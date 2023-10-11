"""
TrafficGenerator VMWare client classes and utilities.
"""
# pylint: disable=c-extension-no-member
import atexit
import logging
import time
from ipaddress import AddressValueError, IPv4Network
from typing import Dict, Optional

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim
from vmwc import Snapshot, VirtualMachine, VMWareClient

from trafficgenerator import TgnError, pchelper

logger = logging.getLogger("tgn.trafficgenerator")


def wait_for_task(task: vim.Task, timeout: int = 60) -> None:
    """Wait for a vCenter task to finish."""
    logger.info(f"Waiting for task {task.info.name}")
    for index in range(timeout):
        logger.debug(f"Task {task.info.name} finished after {index} seconds")
        if task.info.state == "success":
            return
        time.sleep(1)
    raise TgnVMWareClientException(f"Task {task.info.name} not finished after {timeout} seconds")


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
        service_instance = SmartConnect(host=self.host, user=self.username, pwd=self.password, disableSslCertValidation=True)
        atexit.register(Disconnect, service_instance)
        self.content = service_instance.RetrieveContent()

    @staticmethod
    def get_client(host: str, username: str, password: str) -> "VMWare":
        """Return VMWare client for the requested host."""
        if host not in VMWare.clients:
            VMWare.clients[host] = VMWare(host, username, password)
        return VMWare.clients[host]

    # pylint: disable=too-many-locals
    def create_from_template(self, name: str, template_name: str, folder_name: str, datastore_name: str) -> list[str]:
        """Create VM from template."""
        template = pchelper.get_obj(self.content, [vim.VirtualMachine], template_name)
        folder = pchelper.get_obj(self.content, [vim.Folder], folder_name)
        datastore = pchelper.get_obj(self.content, [vim.Datastore], datastore_name)
        resource_pool = pchelper.get_obj(self.content, [vim.ResourcePool], "Resources")

        storagespec = vim.storageDrs.StoragePlacementSpec()
        storagespec.type = "create"
        storagespec.folder = folder
        storagespec.resourcePool = resource_pool

        relo_spec = vim.vm.RelocateSpec()
        relo_spec.datastore = datastore
        relo_spec.pool = resource_pool

        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relo_spec
        clone_spec.powerOn = False

        task = template.Clone(folder=folder, name=name, spec=clone_spec)
        wait_for_task(task)
        self.power_on(name, wait_vmware_tools=True)

        logger.info(f"Waiting for {name} VMWare IPs")
        with VMWareClient(self.host, self.username, self.password) as client:
            vm = [vm for vm in client.get_virtual_machines() if vm.name == name][0]
            timeout = 64
            ips = []
            for index in range(timeout):
                for net in vm._raw_virtual_machine.guest.net:  # pylint: disable=protected-access
                    for vm_ip in net.ipAddress:
                        ips.append(vm_ip)
                    logger.info(f"IPs discovered after {index} seconds")
                    return ips
                time.sleep(1)
        raise TgnVMWareClientException(f"Failed to discover IPs after {timeout} seconds")

    def get_vms(self, folder_name: str = None) -> list[vim.VirtualMachine]:
        """Get VMs list."""
        folder = pchelper.get_obj(self.content, [vim.Folder], folder_name)
        return [vm for vm in folder.childEntity if isinstance(vm, vim.VirtualMachine)]

    def get_vm_events(self, folder_name: str, vm_name: str, events: Optional[list[str]] = None) -> list[vim.event.EventEx]:
        """Get VM events."""
        folder = pchelper.get_obj(self.content, [vim.Folder], folder_name)
        vm = self.content.searchIndex.FindChild(folder, vm_name)

        by_entity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion="self")  # type: ignore
        filter_spec = vim.event.EventFilterSpec(entity=by_entity, eventTypeId=events)  # type: ignore
        return list(self.content.eventManager.QueryEvent(filter_spec))

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

    def delete_vm(self, ip_or_name: str) -> None:
        """Delete the VM from the disk."""
        self.power_off(ip_or_name)
        with VMWareClient(self.host, self.username, self.password) as client:
            vm = self._get_vm(client, ip_or_name)
            vm.delete()

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
