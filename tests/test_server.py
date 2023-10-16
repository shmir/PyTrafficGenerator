"""
Test server module.
"""
# pylint: disable=redefined-outer-name, c-extension-no-member
from pathlib import Path
from typing import Iterable

import pytest
from invoke.exceptions import UnexpectedExit
from pyVmomi import vim

from tests import TEST_VM, TgnTestSutUtils
from trafficgenerator.tgn_server import Server
from trafficgenerator.tgn_vmware import VMWare

pytestmark = pytest.mark.vmware


@pytest.fixture(scope="module")
def vm(vmware: VMWare, sut_utils: TgnTestSutUtils) -> Iterable[vim.VirtualMachine]:
    """Yield VM for testing."""
    vm_ware_info = sut_utils.sut["vmware"]
    vm = vmware.get_vm(vm_ware_info["folder"], TEST_VM)
    if not vm:
        vm = vmware.create_from_template(TEST_VM, vm_ware_info["template"], vm_ware_info["folder"], vm_ware_info["datastore"])
    yield vm
    vmware.delete_vm(vm_ware_info["folder"], vm.name)


@pytest.fixture
def server(vmware: VMWare, vm: vim.VirtualMachine, sut_utils: TgnTestSutUtils) -> Iterable[Server]:
    """Yield Server object for testing."""
    server_info = sut_utils.sut["server"]
    server = Server(vm.name, vm.guest.ipAddress, server_info["user"], server_info["password"], vmware)
    server.power_on(wait=False)
    yield server
    # Some tests (like negative) change the server object, so re-build it and power on the server.
    server = sut_utils.sut["server"]
    server.power_on(wait=False)


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
