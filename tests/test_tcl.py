"""
Tests for TGN Tcl wrapper - the default wrapper.
"""
import pytest

from trafficgenerator.tgn_tcl import TgnTclWrapper, TgnTkThread, py_list_to_tcl_list, tcl_file_name, tcl_list_2_py_list


@pytest.fixture
def tcl(logger):
    yield TgnTclWrapper(logger)


@pytest.fixture
def multi_thread_tcl(logger):
    tcl_interp = TgnTkThread()
    tcl_interp.start()
    yield TgnTclWrapper(logger, tcl_interp)
    tcl_interp.stop()


def test_list(tcl):
    """ Test Python->Tcl and Tcl->Python list conversion. """

    py_list = ["a", "b b"]
    tcl_list_length = tcl.eval("llength " + py_list_to_tcl_list(py_list))
    assert int(tcl_list_length) == 2

    tcl_list = "{a} {b b}"
    python_list = tcl_list_2_py_list(tcl_list)
    assert len(python_list) == 2
    assert type(python_list[0]) is str
    assert type(python_list[1]) is str

    tcl_list = "{{a} {b b}}"
    python_list = tcl_list_2_py_list(tcl_list)
    assert len(python_list) == 2
    assert type(python_list[0]) is str
    assert type(python_list[1]) is str

    tcl_list = ""
    assert len(tcl_list_2_py_list(tcl_list)) == 0

    tcl_list = "{}"
    assert len(tcl_list_2_py_list(tcl_list)) == 0

    tcl_list = '[["a"], ["b", "b"]]'
    assert len(tcl_list_2_py_list(tcl_list)) == 2


def test_file_name():
    """ Test Tcl file names normalization. """
    assert tcl_file_name("a\\b/c").strip() == "{a/b/c}"


@pytest.mark.skip("Throws Tcl_AsyncDelete: async handler deleted by the wrong thread which fails tox.")
def test_puts(multi_thread_tcl):
    """ Test multi threaded Tcl """
    assert multi_thread_tcl.eval('set dummy "hello world"') == "hello world"
