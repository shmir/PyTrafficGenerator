"""
Test VMWare operations.
"""
# pylint: disable=redefined-outer-name
from typing import Iterable

import pytest
from vmwc import VMWareClient

from tests.test_server import TgnTestSutUtils
from trafficgenerator.tgn_server import Server
from trafficgenerator.tgn_vmware import TgnVMWareClientException, VMWare

pytestmark = pytest.mark.vmware


@pytest.fixture
def machine(sut_utils: TgnTestSutUtils, vmware: TgnTestSutUtils) -> Iterable[Server]:
    """Yield Server object for testing."""
    machine = sut_utils.server()
    machine.power_on()
    yield machine
    sut_utils.server().power_on()


# pylint: disable=protected-access
def test_power(vmware: VMWare, machine: Server) -> None:
    """Test power on and off operations."""
    with VMWareClient(vmware.host, vmware.username, vmware.password) as client:
        vmware._get_vm_by_name(client, machine.name)
        vmware._get_vm_by_ip(client, machine.host)
    vmware.power_off(machine.host)
    with VMWareClient(vmware.host, vmware.username, vmware.password) as client:
        vmware._get_vm_by_name(client, machine.name)
        with pytest.raises(TgnVMWareClientException):
            vmware._get_vm_by_ip(client, machine.host)
    vmware.power_on(machine.name, wait_vmware_tools=False)
    with VMWareClient(vmware.host, vmware.username, vmware.password) as client:
        with pytest.raises(TgnVMWareClientException):
            vmware._get_vm_by_ip(client, machine.host)


# pylint: disable=protected-access
def test_negative(vmware: VMWare, machine: Server) -> None:
    """Negative tests."""
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
            vmware._wait_vmware_tools(vm, timeout=0)
