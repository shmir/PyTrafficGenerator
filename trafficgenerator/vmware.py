"""
Kioxia VMWare client classes and utilities.
"""
import logging
import time
from ipaddress import AddressValueError, IPv4Network

from vmwc import Snapshot, VirtualMachine, VMWareClient

from kioxia import KioxiaException

logger = logging.getLogger("kioxia")


class KioxiaVMWareClientException(KioxiaException):
    """Base (default) class for all Kioxia VMWare client exceptions."""


class VMWare(VMWareClient):
    """Kioxia VMWare client. Mainly to run operations on list of VM IPs (rather than names)."""

    clients: dict[str, "VMWare"] = {}

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
        self.ips_to_vm: dict[str, str] = {}
        self.macs_to_vm: dict[str, str] = {}
        self.managed_machines: list[str] = []
        self.map_vms()

    @staticmethod
    def get_client(host: str, username: str, password: str) -> "VMWare":
        """Return VMWare client for the requested host."""
        if host not in VMWare.clients:
            VMWare.clients[host] = VMWare(host, username, password)
        return VMWare.clients[host]

    def map_vms(self) -> None:
        """Create mapping of VM IPs/MACs to names."""
        logger.info("Mapping VMs")
        self.ips_to_vm = {}
        self.macs_to_vm = {}
        with VMWareClient(self.host, self.username, self.password) as client:
            for vm in client.get_virtual_machines():
                if vm.get_tools_status():
                    for net in vm._raw_virtual_machine.guest.net:  # pylint: disable=protected-access
                        for vm_ip in net.ipAddress:
                            self.ips_to_vm[vm_ip] = vm.name
                        self.macs_to_vm[net.macAddress] = vm.name

    def create_snapshot(self, snapshot_name: str) -> None:
        """Create snapshot for all managed VMs."""
        with VMWareClient(self.host, self.username, self.password) as client:
            for machine in self.managed_machines:
                vm = self._get_vm(client, machine)
                powered_on = vm.is_powered_on()
                self._power_off(vm)
                logger.info(f"Taking snapshot of VM '{vm.name}'.")
                vm.take_snapshot(snapshot_name)
                if powered_on:
                    self._power_on(vm)

    def revert_snapshot(self, name: str) -> None:
        """Revert all managed machines to the requested snapshot."""
        logger.info(f"Reverting all VMs to snapshot {name}")
        with VMWareClient(self.host, self.username, self.password) as client:
            vm_power_status = {}
            for machine in self.managed_machines:
                vm = self._get_vm(client, machine)
                powered_on = vm.is_powered_on()
                vm_power_status[vm] = powered_on
                self._power_off(vm)
                snapshot = self._get_snapshot(vm, name)
                logger.info(f"Reverting VM '{vm.name}' to snapshot '{name}'.")
                snapshot.revert()
                if powered_on:
                    self._power_on(vm, wait_on=False)
            for vm, power_status in vm_power_status.items():
                if power_status:
                    self._wait_on(vm)

    def remove_all_snapshots(self) -> None:
        """Remove all snapshots for all managed machines."""
        with VMWareClient(self.host, self.username, self.password) as client:
            for machine in self.managed_machines:
                vm = self._get_vm(client, machine)
                logger.info(f"Removing all snapshots of VM '{vm.name}'.")
                vm.remove_all_snapshots()

    def power_on(self, ip_or_name: str, wait_on: bool = True, wait_ip: bool = False) -> None:
        """Power on specific machine."""
        with VMWareClient(self.host, self.username, self.password) as client:
            vm = self._get_vm(client, ip_or_name)
            if not vm.is_powered_on():
                self._power_on(vm, wait_on)
                if wait_ip:
                    self._wait_ip(vm)

    def power_off(self, ip_or_name: str, wait_off: bool = True) -> None:
        """Power off specific machine."""
        with VMWareClient(self.host, self.username, self.password) as client:
            vm = self._get_vm(client, ip_or_name)
            self._power_off(vm, wait_off)

    #
    # Private methods that assume VMWareClient is initialized (run within "with VMWareClient" clause.
    #

    def _get_vm(self, client: VMWareClient, ip_or_name: str) -> VirtualMachine:
        try:
            IPv4Network(ip_or_name)
            name = self.ips_to_vm.get(ip_or_name)
        except AddressValueError:
            name = ip_or_name
        for vm in client.get_virtual_machines():
            if vm.name == name:
                return vm
        raise KioxiaVMWareClientException(f"VM with IP/name {ip_or_name} not found")

    @staticmethod
    def _get_snapshot(vm: VirtualMachine, name: str) -> Snapshot:
        for snapshot in vm.get_snapshots():
            if snapshot.name == name:
                return snapshot
        raise KioxiaVMWareClientException(f"VM '{vm.name}' has no snapshot {name}")

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

    def _wait_ip(self, vm: VirtualMachine, timeout: int = 30) -> None:
        """Wait for VM Ip to be discovered by VMWare."""
        logger.info(f"Waiting for {vm.name} IP to be discovered")
        for _ in range(timeout):
            self.map_vms()
            if vm.name in self.ips_to_vm.values():
                return
            time.sleep(1)
        raise KioxiaVMWareClientException(f"Can't find VM {vm.name} IP after {timeout} seconds")

    @staticmethod
    def _wait_on(vm: VirtualMachine, timeout: int = 30) -> None:
        """Wait for VM to power on."""
        logger.info(f"Waiting for {vm.name} to power on")
        for _ in range(timeout):
            if vm.is_powered_on():
                return
            time.sleep(1)
        raise KioxiaVMWareClientException(f"VM {vm.name} not on after {timeout} seconds")

    @staticmethod
    def _wait_off(vm: VirtualMachine, timeout: int = 30) -> None:
        """Wait for VM to power off."""
        logger.info(f"Waiting for {vm.name} to power off")
        for _ in range(timeout):
            if not vm.is_powered_on():
                return
            time.sleep(1)
        raise KioxiaVMWareClientException(f"VM {vm.name} not off after {timeout} seconds")
