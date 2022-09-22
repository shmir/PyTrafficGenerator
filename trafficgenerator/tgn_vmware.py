"""
TrafficGenerator VMWare client classes and utilities.
"""
import logging
import time
from ipaddress import AddressValueError, IPv4Network
from typing import Dict

from vmwc import Snapshot, VirtualMachine, VMWareClient

from trafficgenerator import TgnError

logger = logging.getLogger("tgn.trafficgenerator")


class TgnVMWareClientException(TgnError):
    """Base (default) class for all TrafficGenerator VMWare client exceptions."""


class VMWare(VMWareClient):
    """TrafficGenerator VMWare client."""

    clients: Dict[str, "VMWare"] = {}

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize variables and get all user VMs from VMWare.

        :param host: ESXi/VCenter IP.
        :param username: ESXi/VCenter username.
        :param password: ESXi/VCenter password.
        """
        super().__init__(host, username, password)
        self.host = host
        self.username = username
        self.password = password

    @staticmethod
    def get_client(host: str, username: str, password: str) -> "VMWare":
        """Return VMWare client for the requested host."""
        if host not in VMWare.clients:
            VMWare.clients[host] = VMWare(host, username, password)
        return VMWare.clients[host]

    def power_on(self, ip_or_name: str, wait_on: bool = True, wait_vmware_tools: bool = False) -> None:
        """Power on specific machine."""
        with VMWareClient(self.host, self.username, self.password) as client:
            vm = self._get_vm(client, ip_or_name)
            self._power_on(vm, wait_on)
            if wait_vmware_tools:
                self._wait_vmware_tools(vm)

    def power_off(self, ip_or_name: str, wait_off: bool = True) -> None:
        """Power off specific machine."""
        with VMWareClient(self.host, self.username, self.password) as client:
            vm = self._get_vm(client, ip_or_name)
            self._power_off(vm, wait_off)

    #
    # Private methods that assume VMWareClient is initialized (run within "with VMWareClient" clause).
    #

    def _get_vm(self, client: VMWareClient, ip_or_name: str) -> VirtualMachine:
        """Get VM by IP or name."""
        try:
            IPv4Network(ip_or_name)
            return self._get_vm_by_ip(client, ip_or_name)
        except AddressValueError:
            return self._get_vm_by_name(client, ip_or_name)

    @staticmethod
    def _get_vm_by_ip(client: VMWareClient, ip: str) -> VirtualMachine:
        for vm in client.get_virtual_machines():
            if vm.get_tools_status():
                for net in vm._raw_virtual_machine.guest.net:  # pylint: disable=protected-access
                    if ip in net.ipAddress:
                        return vm
        raise TgnVMWareClientException(f"VM with IP {ip} not found")

    @staticmethod
    def _get_vm_by_name(client: VMWareClient, name: str) -> VirtualMachine:
        for vm in client.get_virtual_machines():
            if vm.name == name:
                return vm
        raise TgnVMWareClientException(f"VM with name {name} not found")

    @staticmethod
    def _get_snapshot(vm: VirtualMachine, name: str) -> Snapshot:
        for snapshot in vm.get_snapshots():
            if snapshot.name == name:
                return snapshot
        raise TgnVMWareClientException(f"VM '{vm.name}' has no snapshot {name}")

    def _power_on(self, vm: VirtualMachine, wait_on: bool = True, timeout: int = 30) -> None:
        logger.info(f"Powering on VM {vm.name}")
        vm.power_on()
        if wait_on:
            self._wait_on(vm, timeout)

    def _power_off(self, vm: VirtualMachine, wait_off: bool = True) -> None:
        logger.info(f"Powering off VM {vm.name}")
        vm.power_off()
        if wait_off:
            self._wait_off(vm)

    @staticmethod
    def _wait_on(vm: VirtualMachine, timeout: int = 30) -> None:
        """Wait for VM to power on."""
        logger.info(f"Waiting for {vm.name} to power on")
        for _ in range(timeout):
            if vm.is_powered_on():
                return
            time.sleep(1)
        raise TgnVMWareClientException(f"VM {vm.name} not on after {timeout} seconds")

    @staticmethod
    def _wait_off(vm: VirtualMachine, timeout: int = 30) -> None:
        """Wait for VM to power off."""
        logger.info(f"Waiting for {vm.name} to power off")
        for _ in range(timeout):
            if not vm.is_powered_on():
                return
            time.sleep(1)
        raise TgnVMWareClientException(f"VM {vm.name} not off after {timeout} seconds")

    @staticmethod
    def _wait_vmware_tools(vm: VirtualMachine, timeout: int = 30) -> None:
        """Wait for VM IP to be discovered by VMWare."""
        logger.info(f"Waiting for {vm.name} VMWare tools to be discovered")
        for _ in range(timeout):
            if vm.get_tools_status():
                return
            time.sleep(1)
        raise TgnVMWareClientException(f"Can't find {vm.name} VMWare tools after {timeout} seconds")
