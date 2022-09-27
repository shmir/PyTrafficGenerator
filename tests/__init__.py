"""
Tests for pytrafficgen.
"""
from trafficgenerator import TgnSutUtils, set_logger
from trafficgenerator.tgn_server import Server
from trafficgenerator.tgn_vmware import VMWare


class TgnTestSutUtils(TgnSutUtils):
    """SUT utilities for trafficgenerator testing."""

    def server(self) -> Server:
        """Create Server from SUT."""
        server = self.sut["server"]
        return Server(server["name"], server["ip"], server["user"], server["password"], self.vmware())

    def vmware(self) -> VMWare:
        """Create VMWare from SUT."""
        vmware = self.sut["vmware"]
        return VMWare(vmware["ip"], vmware["user"], vmware["password"])


set_logger()
