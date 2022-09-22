"""
Implements various SUT operations while hiding the internal structure of the SUT.
"""
from pathlib import Path
from typing import Optional

from kioxia import DEFAULT_CERT
from kioxia.access.vmware import VMWare
from kioxia.client.client_cluster import ClientCluster
from kioxia.client.initiator import Initiator
from kioxia.kumoscale.control_cluster import ControlCluster
from kioxia.kumoscale.ks_cluster import KumoScaleCluster
from kioxia.kumoscale.kumoscale import KumoScale
from kioxia.lab.setup import ApplianceSetup, KioxiaSetup, LinkedInSetup, ManagedSetup
from kioxia.peripherals import LicenseGenerator
from kioxia.peripherals.auth_servers import Keycloak
from kioxia.provisioner.provisioner_rest import ProvisionerRest
from kioxia.setup.vsphere_helper.ssl_helper import get_unverified_session
from vmware.vapi.vsphere.client import VsphereClient, create_vsphere_client


# pylint: disable=too-many-public-methods
class SutUtils:
    """Various SUT utilities."""

    def __init__(self, sut: dict) -> None:
        """Save SUT."""
        self.sut = sut

    def ks_cluster(self) -> KumoScaleCluster:
        """Create KumoScale cluster from SUT."""
        return KumoScaleCluster(self.sut["appliance"]["ks_cluster"]["provisioner"]["ip"], *self.storage_ssh_info("appliance"))

    def client_cluster(self, setup: str) -> ClientCluster:
        """Create ClientCluster from SUT for the requested setup."""
        client_dict = self.client_dict(setup)
        return ClientCluster(client_dict["master"]["ip"], *self.client_ssh_info(setup))

    def control_cluster(self) -> ControlCluster:
        """Create control cluster from SUT."""
        return ControlCluster(
            self.sut["managed"]["control_cluster"][0]["ip"],
            self.sut["managed"]["storage"]["ssh"]["user"],
            self.sut["managed"]["storage"]["ssh"]["password"],
        )

    def provisioner_rest(self, setup: str) -> ProvisionerRest:
        """Create ProvisionerRest from SUT for the requested setup."""
        return ProvisionerRest(*self.provisioner_info(setup))

    def initiator(self, setup: str) -> Initiator:
        """Create Initiator object from SUT for the requested setup."""
        client_dict = self.client_dict(setup)
        return Initiator(client_dict["master"]["ip"], *self.client_ssh_info(setup), vmware=self.sut[setup]["vmware"])

    def kumoscale(self, setup: str, index: int) -> KumoScale:
        """Return KumoScale object from SUT for the requested setup and storage node index."""
        host = list(self.storage_nodes(setup).keys())[index]
        return KumoScale(host, *self.storage_ssh_info(setup), vmware=self.sut[setup]["vmware"])

    def storage_nodes(self, setup: str) -> dict:
        """Return a dictionary of all storage nodes entries in SUT for the requested setup."""
        storage_dict = self.storage_dict(setup)
        storage_nodes_dict = storage_dict["kumoscales"] if setup in ("linkedin", "managed") else storage_dict["storage_nodes"]
        return {x["ip"]: x for x in storage_nodes_dict}

    def client_workers(self, setup: str) -> dict:
        """Return a dictionary of all client cluster workers (including the master)."""
        client_dict = self.client_dict(setup)
        master = {client_dict["master"]["ip"]: client_dict["master"]}
        workers = {x["ip"]: x for x in client_dict["workers"]} if "workers" in client_dict else {}
        return master | workers

    def provisioner_info(self, setup: str) -> tuple:
        """Return provisioner for the requested setup."""
        storage_dict = self.storage_dict(setup)
        return storage_dict["provisioner"]["name"], storage_dict["provisioner"]["ip"], storage_dict["provisioner"]["port"]

    def client_ssh_info(self, setup: str) -> tuple:
        """Return client cluster SSH credentials for the requested setup."""
        client_dict = self.client_dict(setup)
        return client_dict["ssh"]["user"], client_dict["ssh"]["password"]

    def storage_ssh_info(self, setup: str) -> tuple:
        """Return storage cluster SSH credentials for the requested setup."""
        storage_dict = self.storage_dict(setup)
        return storage_dict["ssh"]["user"], storage_dict["ssh"]["password"]

    def storage_rbac_info(self, setup: str) -> tuple:
        """Return storage cluster RBAC credentials for the requested setup."""
        storage_dict = self.storage_dict(setup)
        return storage_dict["rbac"]["user"], storage_dict["rbac"]["password"]

    def storage_dict(self, setup: str) -> dict:
        """Return storage sub-dictionary for the requested setup."""
        return self.sut[setup]["storage"] if setup in ("linkedin", "managed") else self.sut[setup]["ks_cluster"]

    def client_dict(self, setup: str) -> dict:
        """Return client sub-dictionary for the requested setup."""
        return self.sut[setup]["client"] if setup == "linkedin" else self.sut[setup]["client_cluster"]

    def control_cluster_dict(self, setup: str) -> dict:
        """Return control_cluster sub-dictionary for the requested setup."""
        return self.sut[setup]["control_cluster"]

    def control_cluster_nodes(self, setup: str) -> dict:
        """Return a dictionary of all control cluster node IPs."""
        managed_cluster_dict = self.control_cluster_dict(setup)
        return {x["ip"]: x for x in managed_cluster_dict}

    def vsphere(self, setup: str) -> VsphereClient:
        """Create vSphere client from SUT."""
        vsphere = self.sut[setup]["vsphere"]
        return create_vsphere_client(
            server=vsphere["ip"], username=vsphere["user"], password=vsphere["password"], session=get_unverified_session()
        )

    def vsphere_dict(self, setup: str) -> dict:
        """Return vSphere sub-dictionary for requested setup."""
        return self.sut[setup]["vsphere"]

    def keycloak_info(self) -> list:
        """Extract all details from keycloak dictionary and get public key."""
        keycloak_info = self.sut["keycloak"]
        public_key = Keycloak(keycloak_info["ip"], keycloak_info["port"], keycloak_info["realm_name"]).get_public_key()
        return [
            public_key["public_key"],
            f"{public_key['token-service']}/token",
            keycloak_info["provisionerClientID"],
            keycloak_info["provisionerResourceID"],
            keycloak_info["provisionerClientSecret"],
            keycloak_info["backendsClientID"],
            keycloak_info["backendsClientSecret"],
            keycloak_info["backendsResourceID"],
        ]

    def pxe_dhcp_info(self, setup: str) -> dict:
        """Return vSphere sub-dictionary for requested setup."""
        return self.sut[setup]["pxe_dhcp"]

    #
    # Setup utils.
    #

    def appliance_setup(self) -> ApplianceSetup:
        """Create ApplianceSetup from SUT."""
        setup = ApplianceSetup(vmware=self.vmware("appliance"))
        setup.add_ks_cluster(self.sut["appliance"]["ks_cluster"]["provisioner"]["ip"], *self.storage_ssh_info("appliance"))
        self.add_storage(setup, "appliance")
        self.add_client(setup, "appliance")
        return setup

    def linkedin_setup(self) -> LinkedInSetup:
        """Create LinkedInSetup from SUT."""
        setup = LinkedInSetup(vmware=self.vmware("linkedin"))
        self.add_storage(setup, "linkedin")
        self.add_client(setup, "linkedin")
        return setup

    def managed_setup(self) -> ManagedSetup:
        """Create ManagedSetup from SUT."""
        setup = ManagedSetup(vmware=self.vmware("managed"))
        setup.add_ks_cluster(self.sut["managed"]["control_cluster"][0]["ip"], *self.storage_ssh_info("managed"))
        self.add_storage(setup, "managed")
        self.add_client(setup, "managed")
        return setup

    def add_storage(self, setup: KioxiaSetup, setup_type: str) -> None:
        """Add Provisioner and KumoScales from SUT to setup."""
        token = self.get_token(setup_type)

        name, ip, rest_port = self.provisioner_info(setup_type)
        user, password = self.storage_ssh_info(setup_type)
        setup.add_provisioner(name, ip, user, password, token, rest_port, DEFAULT_CERT)

        user, password = self.storage_ssh_info(setup_type)
        for ip in self.storage_nodes(setup_type):
            setup.add_kumoscale(ip, user, password, token, 443, DEFAULT_CERT)

    def add_client(self, setup: KioxiaSetup, setup_type: str) -> None:
        """Add ClientCluster and Initiator from SUT to SUT."""
        name = self.client_dict(setup_type)["master"]["ip"]
        ip = self.client_dict(setup_type)["master"]["ip"]
        user, password = self.client_ssh_info(setup_type)
        setup.add_initiator(name, ip, user, password)
        if not isinstance(setup, LinkedInSetup):
            setup.add_client_cluster(ip, *self.client_ssh_info(setup_type))
        for worker in self.client_workers(setup_type).values():
            setup.add_worker(worker["name"], worker["ip"], user, password)

    def vmware(self, setup: str) -> Optional[VMWare]:
        """Create VMWare client from SUT."""
        if "vmware" in self.sut[setup]:
            vmware = self.sut[setup]["vmware"]
            return VMWare.get_client(vmware["ip"], vmware["user"], vmware["password"])
        return None

    def keycloak(self) -> Keycloak:
        """Return KeyCloak object from SUT."""
        keycloak = self.sut["keycloak"]
        return Keycloak(keycloak["ip"], keycloak["port"], keycloak["realm_name"])

    def license_generator_info(self) -> tuple:
        """Return the license generator parameters."""
        license_generator = self.sut["license_generator"]
        return license_generator["ip"], license_generator["user"], license_generator["password"], license_generator["path"]

    def license_generator(self) -> LicenseGenerator:
        """Return LicenseGenerator object from SUT."""
        host, user, password, path = self.license_generator_info()
        return LicenseGenerator(host, user, password, Path(path))

    def ks_license(self) -> str:
        """Generate KS license from SUT."""
        ks_license = self.sut["ks_license"]
        return self.license_generator().generate_license(
            ks_license["file_path"],
            ks_license["license_name"],
            ks_license["licensed_to_company"],
            ks_license["license_type"],
            ks_license["generated_by"],
            ks_license["max_users"],
            ks_license["expiration_date"],
        )

    def get_token(self, setup_type: str) -> str:
        """Add Provisioner from SUT to setup."""
        _, ip, rest_port = self.provisioner_info(setup_type)
        info = ProvisionerRest(ip, rest_port, None, DEFAULT_CERT).get_info()
        if info["authenticationMode"] == "LOCAL":
            return self.sut["token"]
        keycloak = self.keycloak()
        keycloak_info = self.sut["keycloak"]
        token = keycloak.generate_token(keycloak_info["provisionerClientID"], keycloak_info["provisionerClientSecret"])
        return token["access_token"]
