"""
Tests for basic TGN object operations.
"""
# pylint: disable=redefined-outer-name
import logging
import typing
from typing import Dict, Iterable, List, Type

import pytest

from trafficgenerator import ApiType, TgnError
from trafficgenerator.tgn_app import TgnApp
from trafficgenerator.tgn_object import TgnObject, TgnObjectsDict, TgnSubStatsDict
from trafficgenerator.tgn_utils import flatten, is_false, is_ip, is_local_host, is_true


class TgnTestObject(TgnObject):
    """Mock test object."""

    def get_attributes(self) -> Dict[str, str]:
        """Return object data as its attributes."""
        return self._data

    def get_attribute(self, attribute: str) -> str:
        """Return single data entry as a single attribute."""
        return self._data[attribute]

    def get_children(self, *types: str) -> List[TgnObject]:
        """Return all objects as children."""
        return list(self.objects.values())

    def _create(self, **attributes: object) -> str:
        """todo: add implementation and test."""

    def get_name(self) -> str:
        """todo: add implementation and test."""

    def get_objects_from_attribute(self, attribute: str) -> List[TgnObject]:
        """todo: add implementation and test."""

    def get_obj_class(self, obj_type: str) -> Type[TgnObject]:
        """todo: add implementation and test."""


@typing.no_type_check
@pytest.fixture
def tgn_object() -> Iterable[TgnTestObject]:
    """Yield dummy objects hierarchy."""
    # pylint: disable=attribute-defined-outside-init
    tgn_object = TgnTestObject(parent=None, objRef="root1", objType="root")
    tgn_object.api = None
    tgn_object.logger = None
    tgn_object.leaf1 = TgnTestObject(objRef="leaf1", objType="leaf", parent=tgn_object)
    tgn_object.node1 = TgnTestObject(objRef="node1", objType="node", parent=tgn_object, name="name1")
    tgn_object.node2 = TgnTestObject(objRef="node2", objType="node", parent=tgn_object, name="name2")
    tgn_object.node1.node11 = TgnTestObject(objRef="node11", objType="node", parent=tgn_object.node1, name="name11")
    tgn_object.node1.node12 = TgnTestObject(objRef="node12", objType="node", parent=tgn_object.node1, name="name12")
    tgn_object.node1.leaf11 = TgnTestObject(objRef="leaf11", objType="leaf", parent=tgn_object.node1)
    yield tgn_object


def test_app() -> None:
    """Test TgnApp class."""
    tgn_app = TgnApp(logging.getLogger(), ApiType.tcl)
    assert tgn_app.logger == logging.getLogger()
    assert tgn_app.api == ApiType.tcl


@typing.no_type_check
def test_objects_tree(tgn_object: TgnTestObject) -> None:
    """Test object search operations."""
    assert tgn_object.ref == "root1"
    assert tgn_object.type == "root"
    assert tgn_object.name == "root1"
    assert tgn_object.node1.ref == "node1"
    assert tgn_object.node1.type == "node"
    assert tgn_object.node1.name == "name1"
    assert tgn_object.node1.parent == tgn_object

    assert tgn_object.get_object_by_name("name2") == tgn_object.node2
    assert len(tgn_object.get_objects_by_type("node")) == 2
    assert len(tgn_object.get_objects_or_children_by_type("node")) == 2
    assert tgn_object.get_object_or_child_by_type("node") == tgn_object.node1
    assert tgn_object.get_object_by_type("node") == tgn_object.node1
    assert len(tgn_object.get_objects_by_type("no_such_object")) == 0
    assert tgn_object.get_object_by_ref("leaf1") == tgn_object.leaf1

    assert len(tgn_object.get_objects_by_type_in_subtree("node")) == 4
    assert len(tgn_object.get_objects_by_type_in_subtree("leaf")) == 2
    assert len(tgn_object.node1.node11.get_objects_by_type_in_subtree("node")) == 0

    assert str(tgn_object) == tgn_object.name

    assert len(tgn_object.get_objects_with_attribute(obj_type="node", attribute="name", value="name1")) == 1

    assert len(tgn_object.get_children()) == 3
    assert tgn_object.get_child() == tgn_object.leaf1


@typing.no_type_check
def test_objects_dict(tgn_object: TgnTestObject) -> None:
    """Test TgnObjectsDict class."""
    objects_dict = TgnObjectsDict()
    objects_dict[tgn_object.node1] = TgnObjectsDict()
    objects_dict[tgn_object.node1][tgn_object.node1.node11] = "node 11 entry"
    objects_dict[tgn_object.node1][tgn_object.node1.node12] = "node 12 entry"
    objects_dict[tgn_object.node1][tgn_object.node1.leaf11] = TgnObjectsDict()
    objects_dict[tgn_object.node2] = "node 2 entry"
    with pytest.raises(TgnError) as _:
        objects_dict["invalid key"] = ""
    assert objects_dict[tgn_object.node2] == "node 2 entry"
    assert objects_dict[tgn_object.node2.name] == "node 2 entry"
    assert objects_dict[tgn_object.node2.ref] == "node 2 entry"
    assert objects_dict.get(tgn_object.node2.ref) == "node 2 entry"
    assert objects_dict.get(tgn_object.node2.name) == "node 2 entry"
    assert objects_dict.get(tgn_object.node2.ref) == "node 2 entry"
    assert not objects_dict.get("invalid key")
    assert objects_dict.get("invalid key", "value") == "value"
    with pytest.raises(KeyError):
        objects_dict["invalid key"]  # pylint: disable=pointless-statement


@typing.no_type_check
def test_sub_dict(tgn_object: TgnTestObject) -> None:
    """Test TgnSubStatsDict class."""
    sub_stats_dict = TgnSubStatsDict()
    sub_stats_dict[tgn_object.node1] = {"a": 1, "b": 2}
    assert sub_stats_dict[tgn_object.node1]["a"] == 1
    assert sub_stats_dict.get(tgn_object.node1)["a"] == 1
    assert sub_stats_dict[tgn_object.node1.name]["a"] == 1
    assert sub_stats_dict.get(tgn_object.node1.name)["a"] == 1
    assert sub_stats_dict["a"] == 1
    assert sub_stats_dict.get("a") == 1
    sub_stats_dict[tgn_object.node2] = {"c": 3, "d": 4}
    assert sub_stats_dict[tgn_object.node1]["a"] == 1
    assert sub_stats_dict.get(tgn_object.node1)["a"] == 1
    assert sub_stats_dict[tgn_object.node2]["c"] == 3
    assert sub_stats_dict.get(tgn_object.node2)["c"] == 3
    with pytest.raises(KeyError):
        sub_stats_dict["a"]  # pylint: disable=pointless-statement
    assert not sub_stats_dict.get("a")


def test_true_false() -> None:
    """Test TGN true and false values."""
    for false_stc in ("False", "false", "0", "null", "NONE", "none", "::ixnet::obj-null"):
        assert is_false(false_stc)
        assert not is_true(false_stc)
    for true_str in ("True", "TRUE", "1"):
        assert is_true(true_str)
        assert not is_false(true_str)


def test_localhost() -> None:
    """Test TGN localhost values."""
    for location in ("127.0.0.1", "localhost", "Localhost/1/1", "//(Offline)/1/1", "null"):
        assert is_local_host(location)
    for location in ("1.2.3.4", "hostname", "192.168.1.1/1/2"):
        assert not is_local_host(location)


def test_ips() -> None:
    """Test TGN IP values."""
    for ip in ("IPV4", "ipv6", "ipv4if", "IPV6IF"):
        assert is_ip(ip)
    for ip in ("mac", "bla"):
        assert not is_ip(ip)


def test_flatten() -> None:
    """Test flatten utility."""
    ml_list = [1, [11, [111]], 2, [22]]
    assert len(ml_list) == 4
    assert isinstance(ml_list[1], list)
    assert isinstance(ml_list[2], int)
    assert len(flatten(ml_list)) == 5
    assert isinstance(flatten(ml_list)[1], int)
    assert isinstance(flatten(ml_list)[2], int)
