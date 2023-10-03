"""
Create VMWare VMs for appliance and managed mode setup.
"""
import logging
import tempfile
from pathlib import Path
from typing import Optional

from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (
    Boot,
    Cpu,
    Disk,
    Ethernet,
    Memory,
    NvmeAddressSpec,
    SataAddressSpec,
    ScsiAddressSpec,
)
from com.vmware.vcenter.vm_client import GuestOS, Hardware, Power
from com.vmware.vcenter_client import VM, Network
from kioxia.access.server import SshShell
from vmware.vapi.vsphere.client import VsphereClient, create_vsphere_client

from kioxia_lab.sut_utils import SutUtils
from kioxia_lab.vsphere_helper import datastore_helper, folder_helper, network_helper
from kioxia_lab.vsphere_helper.ssl_helper import get_unverified_session
from kioxia_lab.vsphere_helper.vm_helper import get_vm

logger = logging.getLogger("kioxia")

GB = 1024 * 1024 * 1024
GB_MEMORY = 1024

SETUP_PATH = "lab/grub/grub_{}.cfg"
GRUB_PATH = "/var/lib/tftpboot/auto_{}/grub.cfg"
GRUB_VIP_PATH = "/var/lib/tftpboot/auto_{}_vip/grub.cfg"
INSTALL_REPO = "http://{}}/oses/centos-{}/"
INSTALL_KS = "http://{}/ksfiles/centos-{}-efi.ks"
KUMOSCALE_ROOT = "live:http://{}/kumoscale/NVMf-{}/{}/kumoscale-{}-img.raw"
INITRDEFI = "images/centos-{}/initrd.img"
INITRDEFI_KS = "efi/initrd-{}.img"


def vsphere(vsphere_info: dict) -> VsphereClient:
    """Create vSphere client from SUT."""
    return create_vsphere_client(
        server=vsphere_info["ip"],
        username=vsphere_info["user"],
        password=vsphere_info["password"],
        session=get_unverified_session(),
    )


def create_managed_vms(sut: dict) -> None:
    """Create VMs which are required for managed setup."""
    sut_utils = SutUtils(sut)
    initiators = sut_utils.client_info("managed")
    kumoscales = sut_utils.storage_nodes_info("managed")
    control_cluster_nodes = sut_utils.control_nodes_info()
    logger.info("Creating VMs required for managed setup.")

    for kumoscale in kumoscales:
        create_kumoscale_vm(kumoscales[kumoscale]["name"], sut, "managed")

    for initiator in initiators:
        create_initiator_vm(initiators[initiator]["name"], sut, "managed")

    for control_node in control_cluster_nodes:
        create_initiator_vm(control_cluster_nodes[control_node]["name"], sut, "managed")


def delete_managed_vms(sut: dict) -> None:
    """Delete VMs which are used for managed setup."""
    sut_utils = SutUtils(sut)
    initiators = sut_utils.client_info("managed")
    kumoscales = sut_utils.storage_nodes_info("managed")
    control_cluster_nodes = sut_utils.control_nodes_info()
    logger.info("Deleting VMs used for managed setup.")

    for kumoscale in kumoscales:
        delete_vm(kumoscales[kumoscale]["name"], sut, "managed")

    for initiator in initiators:
        delete_vm(initiators[initiator]["name"], sut, "managed")

    for control_node in control_cluster_nodes:
        delete_vm(control_cluster_nodes[control_node]["name"], sut, "managed")


def create_appliance_vms(sut: dict) -> None:
    """Create VMs which are required for appliance setup."""
    sut_utils = SutUtils(sut)
    initiators = sut_utils.client_info("appliance")
    kumoscales = sut_utils.storage_nodes_info("appliance")
    logger.info("Creating VMs required for appliance setup.")

    for kumoscale in kumoscales:
        storage_dict = sut_utils.storage_dict("appliance")
        create_grub(
            sut_utils.pxe_dhcp_info("appliance"),
            storage_dict["os"],
            storage_dict["version"],
            storage_dict["provisioner"]["ip"],
        )
        create_kumoscale_vm(kumoscales[kumoscale], sut, "appliance")

    for initiator in initiators:
        client_dict = sut_utils.client_dict("appliance")
        create_grub(sut_utils.pxe_dhcp_info("appliance"), client_dict["os"], client_dict["version"])
        create_initiator_vm(initiators[initiator], sut, "appliance")


def delete_appliance_vms(sut: dict) -> None:
    """Delete VMs which are used for appliance setup."""
    sut_utils = SutUtils(sut)
    initiators = sut_utils.client_info("appliance")
    kumoscales = sut_utils.storage_nodes_info("appliance")
    logger.info("Deleting VMs used for appliance setup.")

    for kumoscale in kumoscales:
        delete_vm(kumoscales[kumoscale]["name"], sut, "appliance")

    for initiator in initiators:
        delete_vm(initiators[initiator]["name"], sut, "appliance")


def create_kumoscale_vm(vm_dict: dict, sut: dict, mode: str) -> None:
    """Create Kumoscale VM."""
    sut_utils = SutUtils(sut)
    vsphere_info = sut_utils.vsphere_dict(mode)
    vsphere_client = vsphere(vsphere_info)

    # Creating placement spec
    folder = folder_helper.get_folder(vsphere_client, vsphere_info["datacenter"]["name"], vsphere_info["datacenter"]["folder"])

    datastore = datastore_helper.get_datastore(
        vsphere_client, vsphere_info["datacenter"]["name"], vsphere_info["host"]["datastore"]
    )

    # Create the vm placement spec with the datastore, host and vm folder
    host = [host.host for host in vsphere_client.vcenter.Host.list() if host.name == vsphere_info["host"]["ip"]][0]
    placement_spec = VM.PlacementSpec(folder=folder, host=host, datastore=datastore)
    logger.info(f"placement_spec: {placement_spec}")

    # Get a standard network backing
    standard_network = network_helper.get_network_backing(
        vsphere_client, vsphere_info["host"]["vm_network"], vsphere_info["datacenter"]["name"], Network.Type.STANDARD_PORTGROUP
    )

    # Get a standard network backing
    standard_network1 = network_helper.get_network_backing(
        vsphere_client,
        vsphere_info["host"]["private_network"],
        vsphere_info["datacenter"]["name"],
        Network.Type.STANDARD_PORTGROUP,
    )

    vm_create_spec = VM.CreateSpec(
        guest_os=GuestOS.CENTOS_8_64,
        name=vm_dict["name"],
        placement=placement_spec,
        hardware_version=Hardware.Version.VMX_19,
        cpu=Cpu.UpdateSpec(count=8, cores_per_socket=2, hot_add_enabled=False, hot_remove_enabled=False),
        memory=Memory.UpdateSpec(size_mib=16 * GB_MEMORY, hot_add_enabled=False),
        disks=[
            Disk.CreateSpec(
                type=Disk.HostBusAdapterType.SATA,
                sata=SataAddressSpec(bus=0, unit=0),
                new_vmdk=Disk.VmdkCreateSpec(name="boot", capacity=80 * GB),
            ),
            Disk.CreateSpec(
                type=Disk.HostBusAdapterType.NVME,
                nvme=NvmeAddressSpec(bus=0, unit=0),
                new_vmdk=Disk.VmdkCreateSpec(capacity=100 * GB),
            ),
            Disk.CreateSpec(
                type=Disk.HostBusAdapterType.NVME,
                nvme=NvmeAddressSpec(bus=1, unit=0),
                new_vmdk=Disk.VmdkCreateSpec(capacity=100 * GB),
            ),
        ],
        nics=[
            Ethernet.CreateSpec(
                type=Ethernet.EmulationType.VMXNET3,
                start_connected=True,
                upt_compatibility_enabled=True,
                allow_guest_control=True,
                wake_on_lan_enabled=True,
                mac_type=Ethernet.MacAddressType.GENERATED,
                backing=Ethernet.BackingSpec(type=Ethernet.BackingType.STANDARD_PORTGROUP, network=standard_network),
            ),
            Ethernet.CreateSpec(
                type=Ethernet.EmulationType.VMXNET3,
                start_connected=True,
                upt_compatibility_enabled=True,
                mac_type=Ethernet.MacAddressType.MANUAL if "mac" in vm_dict else Ethernet.MacAddressType.GENERATED,
                mac_address=vm_dict["mac"] if "mac" in vm_dict else None,
                allow_guest_control=True,
                wake_on_lan_enabled=True,
                backing=Ethernet.BackingSpec(type=Ethernet.BackingType.STANDARD_PORTGROUP, network=standard_network1),
            ),
        ],
        boot=Boot.CreateSpec(
            type=Boot.Type.EFI, network_protocol=Boot.NetworkProtocol.IPV4, delay=10000, retry_delay=10, enter_setup_mode=False
        ),
        boot_devices=[
            BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET),
            BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
        ],
    )
    logger.info(f"VM Spec: {vm_create_spec}")
    vm = vsphere_client.vcenter.VM.create(vm_create_spec)
    logger.info(f"Created VM '{vm_dict['name']}' ({vm})")

    vm_info = vsphere_client.vcenter.VM.get(vm)
    logger.info(f"vm.get({vm}) -> {vm_info}")
    vm = get_vm(vsphere_client, vm_dict["name"])

    # Power on the vm
    logger.info("Power on the vm")
    vsphere_client.vcenter.vm.Power.start(vm)
    logger.info(f"vm.Power.start({vm})")


def create_initiator_vm(vm_dict: dict, sut: dict, mode: str) -> None:
    """Create VM required for initiator and control cluster node."""
    sut_utils = SutUtils(sut)
    vsphere_info = sut_utils.vsphere_dict(mode)
    vsphere_client = vsphere(vsphere_info)

    # Creating placement spec
    folder = folder_helper.get_folder(vsphere_client, vsphere_info["datacenter"]["name"], vsphere_info["datacenter"]["folder"])

    datastore = datastore_helper.get_datastore(
        vsphere_client, vsphere_info["datacenter"]["name"], vsphere_info["host"]["datastore"]
    )

    # Create the vm placement spec with the datastore, host and vm folder
    host = [host.host for host in vsphere_client.vcenter.Host.list() if host.name == vsphere_info["host"]["ip"]][0]
    placement_spec = VM.PlacementSpec(folder=folder, host=host, datastore=datastore)
    logger.info(f"placement_spec: {placement_spec}")

    # Get a standard network backing
    standard_network = network_helper.get_network_backing(
        vsphere_client, vsphere_info["host"]["vm_network"], vsphere_info["datacenter"]["name"], Network.Type.STANDARD_PORTGROUP
    )

    # Get a standard network backing
    standard_network1 = network_helper.get_network_backing(
        vsphere_client,
        vsphere_info["host"]["private_network"],
        vsphere_info["datacenter"]["name"],
        Network.Type.STANDARD_PORTGROUP,
    )

    vm_create_spec = VM.CreateSpec(
        guest_os=GuestOS.CENTOS_8_64,
        name=vm_dict["name"],
        placement=placement_spec,
        hardware_version=Hardware.Version.VMX_19,
        cpu=Cpu.UpdateSpec(count=2, cores_per_socket=2, hot_add_enabled=False, hot_remove_enabled=False),
        memory=Memory.UpdateSpec(size_mib=4 * GB_MEMORY, hot_add_enabled=False),
        disks=[
            Disk.CreateSpec(
                type=Disk.HostBusAdapterType.SCSI,
                scsi=ScsiAddressSpec(bus=0, unit=0),
                new_vmdk=Disk.VmdkCreateSpec(capacity=64 * GB),
            ),
        ],
        nics=[
            Ethernet.CreateSpec(
                type=Ethernet.EmulationType.VMXNET3,
                start_connected=True,
                upt_compatibility_enabled=True,
                mac_type=Ethernet.MacAddressType.GENERATED,
                allow_guest_control=True,
                wake_on_lan_enabled=True,
                backing=Ethernet.BackingSpec(type=Ethernet.BackingType.STANDARD_PORTGROUP, network=standard_network),
            ),
            Ethernet.CreateSpec(
                type=Ethernet.EmulationType.VMXNET3,
                start_connected=True,
                upt_compatibility_enabled=True,
                allow_guest_control=True,
                wake_on_lan_enabled=True,
                mac_type=Ethernet.MacAddressType.MANUAL if "mac" in vm_dict else Ethernet.MacAddressType.GENERATED,
                mac_address=vm_dict["mac"] if "mac" in vm_dict else None,
                backing=Ethernet.BackingSpec(type=Ethernet.BackingType.STANDARD_PORTGROUP, network=standard_network1),
            ),
        ],
        boot=Boot.CreateSpec(
            type=Boot.Type.EFI, network_protocol=Boot.NetworkProtocol.IPV4, delay=10000, retry_delay=10, enter_setup_mode=False
        ),
        boot_devices=[
            BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET),
            BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
        ],
    )
    logger.info(f"VM Spec: {vm_create_spec}")
    vm = vsphere_client.vcenter.VM.create(vm_create_spec)
    logger.info(f"Created VM '{vm_dict['name']}' ({vm})")

    vm_info = vsphere_client.vcenter.VM.get(vm)
    logger.info(f"vm.get({vm}) -> {vm_info}")
    vm = get_vm(vsphere_client, vm_dict["name"])

    # Power on the vm
    logger.info("Power on the vm")
    vsphere_client.vcenter.vm.Power.start(vm)
    logger.info(f"vm.Power.start({vm})")


def delete_vm(vm_name: str, sut: dict, mode: str) -> None:
    """Delete VM."""
    sut_utils = SutUtils(sut)
    vsphere_client = vsphere(sut_utils.vsphere_dict(mode))

    vm = get_vm(vsphere_client, vm_name)
    if vm:
        state = vsphere_client.vcenter.vm.Power.get(vm)
        if state == Power.Info(state=Power.State.POWERED_ON):
            vsphere_client.vcenter.vm.Power.stop(vm)
        elif state == Power.Info(state=Power.State.SUSPENDED):
            vsphere_client.vcenter.vm.Power.start(vm)
            vsphere_client.vcenter.vm.Power.stop(vm)
        logger.info(f"Deleting VM '{vm_name}' ({vm})")
        vsphere_client.vcenter.VM.delete(vm)


def create_grub(
    dhcp: dict,
    os: str,
    version: str,
    vip: Optional[str] = None,
) -> None:
    """Create grub files on the dhcp pxe server."""
    dhcp_server = SshShell(dhcp["ip"], dhcp["user"], dhcp["password"])
    if vip:
        with open(Path(__file__).parent.parent.joinpath(SETUP_PATH.format(os)), "r") as grub:
            grub_text = grub.read()
        grub_text = grub_text.replace("[VERSION]", version)
        grub_text = grub_text.replace("[VIP]", vip)
        grub_text = grub_text.replace(
            "[KUMOSCALE_ROOT]", KUMOSCALE_ROOT.format(dhcp["internal_ip"], version.split("-")[0], version)
        )
        grub_text = grub_text.replace("[INITRDEFI_KS]", KUMOSCALE_ROOT.format(version))

        with tempfile.TemporaryFile("w+") as grub_file:
            grub_file.write(grub_text)
            grub_file.flush()
            dhcp_server.put(grub_file, GRUB_VIP_PATH.format(os))

    with open(Path(__file__).parent.parent.joinpath(SETUP_PATH.format(os)), "r") as grub:
        grub_text = grub.read()
    grub_text = grub_text.replace("[VERSION]", version)
    grub_text = grub_text.replace("[INSTALL_REPO]", INSTALL_REPO.format(dhcp["internal_ip"], version))
    grub_text = grub_text.replace("[INSTALL_KS]", INSTALL_KS.format(dhcp["internal_ip"], version))
    grub_text = grub_text.replace("[KUMOSCALE_ROOT]", KUMOSCALE_ROOT.format(dhcp["internal_ip"], version))
    grub_text = grub_text.replace("[INITRDEFI_KS]", KUMOSCALE_ROOT.format(version))
    grub_text = grub_text.replace("[INITRDEFI]", KUMOSCALE_ROOT.format(version))

    with tempfile.TemporaryFile("w+") as grub_file:
        grub_file.write(grub_text)
        grub_file.flush()
        dhcp_server.put(grub_file, GRUB_PATH.format(os))
