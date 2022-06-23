"""
Tests for TGN Tcl wrapper - the default wrapper.
"""
# pylint: disable=redefined-outer-name
import logging
import sys

import pytest

from trafficgenerator.tgn_tcl import TgnTclWrapper, py_list_to_tcl_list, tcl_file_name, tcl_list_2_py_list


@pytest.fixture(scope="session")
def logger() -> logging.Logger:
    """Yield logger for package regression testing."""
    logger = logging.getLogger("tgn")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


@pytest.fixture
def tcl(logger: logging.Logger) -> TgnTclWrapper:
    """Yield TgnTclWrapper."""
    return TgnTclWrapper(logger)


def test_list(tcl: TgnTclWrapper) -> None:
    """Test Python->Tcl and Tcl->Python list conversion."""
    py_list = ["a", "b b"]
    tcl_list_length = tcl.eval("llength " + py_list_to_tcl_list(py_list))
    assert int(tcl_list_length) == 2

    tcl_list = "{a} {b b}"
    python_list = tcl_list_2_py_list(tcl_list)
    assert len(python_list) == 2
    assert isinstance(python_list[0], str)
    assert isinstance(python_list[1], str)

    tcl_list = "{{a} {b b}}"
    python_list = tcl_list_2_py_list(tcl_list)
    assert len(python_list) == 2
    assert isinstance(python_list[0], str)
    assert isinstance(python_list[1], str)

    tcl_list = '{{"a" "b b"}}'
    python_list = tcl_list_2_py_list(tcl_list)
    assert len(python_list) == 1

    tcl_list = ""
    assert len(tcl_list_2_py_list(tcl_list)) == 0

    tcl_list = "{}"
    assert len(tcl_list_2_py_list(tcl_list)) == 0

    tcl_list = '[["a"], ["b", "b"]]'
    assert len(tcl_list_2_py_list(tcl_list)) == 2


def test_file_name() -> None:
    """Test Tcl file names normalization."""
    assert tcl_file_name("a\\b/c").strip() == "{a/b/c}"
