"""
Test VMWare operations.
"""
from typing import Iterable

import pytest
from pyVmomi import vim

from tests import TEST_VM
from tests.test_server import TgnTestSutUtils
from trafficgenerator.tgn_vmware import VMWare

pytestmark = pytest.mark.vmware


@pytest.fixture
def vm(vmware: VMWare, sut_utils: TgnTestSutUtils) -> Iterable[vim.VirtualMachine]:
    """Yield VM for testing."""
    vm_ware_info = sut_utils.sut["vmware"]
    vm_ = vmware.create_from_template(TEST_VM, vm_ware_info["template"], vm_ware_info["folder"], vm_ware_info["datastore"])
    yield vm_
    vmware.delete_vm(vm_ware_info["folder"], vm_.name)


@pytest.fixture
def clean_vm(vmware: VMWare, sut_utils: TgnTestSutUtils) -> Iterable[None]:
    """Clean VM after testing."""
    vm_ware_info = sut_utils.sut["vmware"]
    vmware.delete_vm(vm_ware_info["folder"], TEST_VM)
    yield
    vmware.delete_vm(vm_ware_info["folder"], TEST_VM)


def test_get_vms(vmware: VMWare, vm: vim.VirtualMachine, sut_utils: TgnTestSutUtils) -> None:
    """Test get VMs and events."""
    vm_ware_info = sut_utils.sut["vmware"]
    vms = vmware.get_vms(vm_ware_info["folder"])
    assert vms
    assert vmware.get_vm(vm_ware_info["folder"], vm.name).name == TEST_VM


@pytest.mark.usefixtures("clean_vm")
def test_create_delete(vmware: VMWare, sut_utils: TgnTestSutUtils) -> None:
    """Test Create and delete VM."""
    vm_ware_info = sut_utils.sut["vmware"]
    vm_ = vmware.create_from_template(TEST_VM, vm_ware_info["template"], vm_ware_info["folder"], vm_ware_info["datastore"])
    assert vm_
    vmware.delete_vm(vm_ware_info["folder"], vm_.name)
