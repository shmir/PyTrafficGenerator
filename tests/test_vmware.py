"""
Test VMWare operations.
"""
# pylint: disable=redefined-outer-name
from typing import Iterable, Optional

import pytest
from vmwc import VMWareClient

from trafficgenerator.server import Server
from trafficgenerator.vmware import TgnVMWareClientException, VMWare


@pytest.fixture
def machine(sut_utils: SutUtils) -> Iterable[Server]:
    """Yield Server object for testing."""
    client_dict = sut_utils.client_dict("linkedin")
    name, ip = list(client_dict["master"].values())
    user, password = sut_utils.client_ssh_info("linkedin")
    server = Server(name, ip, user, password, vmware=sut_utils.vmware("linkedin"))
    server.power_on()
    yield server
    server.power_on()


@pytest.fixture
def vmware(machine: Server, sut_utils: SutUtils) -> Optional[VMWare]:
    """Yield VMWare object for testing."""
    return sut_utils.vmware("linkedin")


def test_power(vmware: VMWare, machine: Server) -> None:
    """Test power on and off operations."""
    assert machine.host in vmware.ips_to_vm.keys()
    assert machine.name in vmware.ips_to_vm.values()
    vmware.power_off(machine.host)
    vmware.power_on(machine.name, wait_ip=False)
    vmware.map_vms()
    assert machine.host not in vmware.ips_to_vm.keys()


# pylint: disable=protected-access
def test_negative(vmware: VMWare, machine: Server) -> None:
    """Negative tests."""
    assert "invalid host" not in vmware.ips_to_vm
    with pytest.raises(TgnVMWareClientException):
        vmware.power_on("invalid host")
    with VMWareClient(vmware.host, vmware.username, vmware.password) as client:
        vm = vmware._get_vm(client, machine.name)
        with pytest.raises(TgnVMWareClientException):
            vmware._power_off(vm, wait_off=False)
            vmware._wait_off(vm, timeout=0)
        vmware._power_off(vm)
        with pytest.raises(TgnVMWareClientException):
            vmware._power_on(vm, wait_on=False)
            vmware._wait_on(vm, timeout=0)
        vmware._wait_on(vm)
        with pytest.raises(TgnVMWareClientException):
            vmware._wait_ip(vm, timeout=0)
