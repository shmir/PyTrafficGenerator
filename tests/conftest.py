"""
Standard pytest fixtures and hooks definition file.
"""
# pylint: disable=redefined-outer-name
from typing import Optional

import pytest

from tests.test_server import TgnTestSutUtils
from trafficgenerator.tgn_vmware import VMWare


@pytest.fixture(scope="session")
def sut_utils(sut: dict) -> TgnTestSutUtils:
    """Yield the sut dictionary from the sut file."""
    return TgnTestSutUtils(sut)


@pytest.fixture(scope="session")
def vmware(sut_utils: TgnTestSutUtils) -> Optional[VMWare]:
    """Yield VMWare object for testing."""
    return sut_utils.vmware()
