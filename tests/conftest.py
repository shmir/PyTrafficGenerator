"""
Standard pytest fixtures and hooks definition file.
"""
# pylint: disable=redefined-outer-name
from typing import Iterable, Optional

import pytest
from pyVmomi import vim

from tests import TEST_VM
from tests.test_server import TgnTestSutUtils
from trafficgenerator.tgn_conftest import log_level, pytest_addoption, sut  # pylint: disable=unused-import
from trafficgenerator.tgn_vmware import VMWare


@pytest.fixture(scope="session")
def sut_utils(sut: dict) -> TgnTestSutUtils:
    """Yield the sut dictionary from the sut file."""
    return TgnTestSutUtils(sut)


@pytest.fixture
def vmware(sut_utils: TgnTestSutUtils) -> Optional[VMWare]:
    """Yield VMWare object for testing."""
    return sut_utils.vmware()


@pytest.fixture
def vm(vmware: VMWare, sut_utils: TgnTestSutUtils) -> Iterable[vim.VirtualMachine]:
    """Yield VM for testing."""
    vm_ware_info = sut_utils.sut["vmware"]
    vm = vmware.create_from_template(TEST_VM, vm_ware_info["template"], vm_ware_info["folder"], vm_ware_info["datastore"])
    yield vm
    vmware.delete_vm(vm_ware_info["folder"], vm.name)
