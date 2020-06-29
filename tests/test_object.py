"""
Tests for basic TGN object operations.
"""
from typing import Type, List, Dict

import pytest

from trafficgenerator.tgn_utils import is_false, is_true, is_local_host, is_ip, flatten, TgnError
from trafficgenerator.tgn_app import TgnApp
from trafficgenerator.tgn_object import TgnObject, TgnObjectsDict, TgnSubStatsDict


@pytest.fixture()
def root():
    """ Yields dummy objects hierarchy. """
    root = TestObject(objRef='root1', objType='root', parent=None)
    root.api = None
    root.logger = None
    root.leaf1 = TestObject(objRef='leaf1', objType='leaf', parent=root)
    root.node1 = TestObject(objRef='node1', objType='node', parent=root, name='name1')
    root.node2 = TestObject(objRef='node2', objType='node', parent=root, name='name2')
    root.node1.node11 = TestObject(objRef='node11', objType='node', parent=root.node1, name='name11')
    root.node1.node12 = TestObject(objRef='node12', objType='node', parent=root.node1, name='name12')
    root.node1.leaf11 = TestObject(objRef='leaf11', objType='leaf', parent=root.node1)
    yield root


class TestObject(TgnObject):
    """ Mock test object. """

    def _create(self, **attributes: Dict[str, object]) -> str:
        pass

    def get_attributes(self) -> Dict[str, str]:
        """ Returns object data as its attributes. """
        return self._data

    def get_attribute(self, attribute: str) -> str:
        """ Returns single data entry as a single attribute. """
        return self._data[attribute]

    def get_children(self, *types: List[str]) -> List[TgnObject]:
        """ Returns all objects as children. """
        return list(self.objects.values())

    def get_objects_from_attribute(self, attribute: str) -> List[TgnObject]:
        """ todo: add implementation and test. """
        pass

    def get_obj_class(self, obj_type: str) -> Type[TgnObject]:
        """ todo: add implementation and test. """
        pass


class TestTgnObject:

    def test_app(self):
        TgnApp(None, None)

    def test_objects_tree(self, root):
        """ Test object search operations. """

        assert root.ref == 'root1'
        assert root.type == 'root'
        assert root.name == 'root1'
        assert root.node1.ref == 'node1'
        assert root.node1.type == 'node'
        assert root.node1.name == 'name1'
        assert root.node1.parent == root

        assert root.get_object_by_name('name2') == root.node2
        assert len(root.get_objects_by_type('node'))== 2
        assert len(root.get_objects_or_children_by_type('node')) == 2
        assert root.get_object_or_child_by_type('node') == root.node1
        assert root.get_object_by_type('node') == root.node1
        assert len(root.get_objects_by_type('no_such_object')) == 0
        assert root.get_object_by_ref('leaf1') == root.leaf1

        assert len(root.get_objects_by_type_in_subtree('node')) == 4
        assert len(root.get_objects_by_type_in_subtree('leaf')) == 2
        assert len(root.node1.node11.get_objects_by_type_in_subtree('node')) == 0

        assert str(root) == root.name

        assert len(root.get_objects_with_attribute(obj_type='node', attribute='name', value='name1')) == 1

        assert len(root.get_children()) == 3
        assert root.get_child() == root.leaf1

    def test_objects_dict(self, root):
        objects_dict = TgnObjectsDict()
        objects_dict[root.node1] = TgnObjectsDict()
        objects_dict[root.node1][root.node1.node11] = 'node 11 entry'
        objects_dict[root.node1][root.node1.node12] = 'node 12 entry'
        objects_dict[root.node1][root.node1.leaf11] = TgnObjectsDict()
        objects_dict[root.node2] = 'node 2 entry'
        with pytest.raises(TgnError) as _:
            objects_dict.__setitem__('invalid key', '')
        assert objects_dict[root.node2] == 'node 2 entry'
        assert objects_dict[root.node2.name] == 'node 2 entry'
        assert objects_dict[root.node2.ref] == 'node 2 entry'
        print(objects_dict.dumps())

    def test_sub_dict(self, root):
        sub_stats_dict = TgnSubStatsDict()
        sub_stats_dict[root.node1] = {'a': 1, 'b': 2}
        assert sub_stats_dict[root.node1]['a'] == 1
        assert sub_stats_dict[root.node1.name]['a'] == 1
        assert sub_stats_dict['a'] == 1
        sub_stats_dict[root.node2] = {'c': 3, 'd': 4}
        assert sub_stats_dict[root.node1]['a'] == 1
        assert sub_stats_dict[root.node2]['c'] == 3
        with pytest.raises(KeyError) as _:
            sub_stats_dict.__getitem__('a')


class TestTgnUtils():

    def test_true_false(self):
        """ Test TGN true and false values. """

        for false_stc in ('False', 'false', '0', 'null', 'NONE', 'none', '::ixnet::obj-null'):
            assert(is_false(false_stc))
            assert(not is_true(false_stc))

        for true_str in ('True', 'TRUE', '1'):
            assert(is_true(true_str))
            assert(not is_false(true_str))

    def test_localhost(self):
        """ Test TGN localhost values. """

        for location in ('127.0.0.1', 'localhost', 'Localhost/1/1', '//(Offline)/1/1', 'null'):
            assert(is_local_host(location))

        for location in ('1.2.3.4', 'hostname', '192.168.1.1/1/2'):
            assert(not is_local_host(location))

    def test_ips(self):
        """ Test TGN IP values. """

        for ip in ('IPV4', 'ipv6', 'ipv4if', 'IPV6IF'):
            assert(is_ip(ip))

        for ip in ('mac', 'bla'):
            assert(not is_ip(ip))

    def test_flatten(self):
        nl = [1, [11, [111]], 2, [22]]
        assert(len(nl) == 4)
        assert(type(nl[1]) == list)
        assert(type(nl[2]) == int)
        assert(len(flatten(nl)) == 5)
        assert(type(flatten(nl)[1]) == int)
        assert(type(flatten(nl)[2]) == int)
