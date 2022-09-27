"""
Test server module.
"""
# pylint: disable=redefined-outer-name
from pathlib import Path
from typing import Iterable

import pytest
from invoke.exceptions import UnexpectedExit

from tests import TgnTestSutUtils
from trafficgenerator.tgn_server import Server

pytestmark = pytest.mark.vmware


@pytest.fixture
def server(sut_utils: TgnTestSutUtils, vmware: TgnTestSutUtils) -> Iterable[Server]:
    """Yield Server object for testing."""
    server = sut_utils.server()
    server.power_on()
    yield server
    # Some tests (like negative) change the server object, so re-build it and power on the server.
    sut_utils.server().power_on()


def test_exec_cmd(server: Server) -> None:
    """Test commands that fail."""
    out = server.exec_cmd("pwd")
    assert out.stdout
    assert not out.stderr
    with pytest.raises(UnexpectedExit):
        server.exec_cmd("invalid_command")


def test_put(server: Server) -> None:
    """Test Server put."""
    local_path = Path(__file__)
    server.put(local_path, Path("/tmp"))
    ls = server.exec_cmd("ls /tmp")
    assert local_path.name in ls.stdout


def test_reboot(server: Server) -> None:
    """Test reboot."""
    assert server.is_up()
    server.reboot(timeout=120)
    assert server.is_up()


def test_power(server: Server) -> None:
    """Test VM power operations."""
    assert server.is_up()
    server.shutdown()
    assert not server.is_up()
    server.power_on()
    assert server.is_up()
    server.shutdown()
    server.reboot()
    assert server.is_up()


def test_negative(server: Server) -> None:
    """Negative tests."""
    with pytest.raises(UnexpectedExit):
        server.exec_cmd("false")
    with pytest.raises(TimeoutError):
        server.wait2down(timeout=2)
    server.shutdown()
    with pytest.raises(TimeoutError):
        server.wait2up(timeout=2)
    with pytest.raises(TimeoutError):
        server.wait_reboot(timeout=2)
    server.vmware = None
    with pytest.raises(ValueError):
        server.shutdown()
    with pytest.raises(ValueError):
        server.power_on()
