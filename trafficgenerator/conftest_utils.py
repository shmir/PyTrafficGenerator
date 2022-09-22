"""
conftest utilities. Import this file in conftest.py so pytest can find all fixtures.
"""
# pylint: disable=redefined-outer-name
import logging
import re
from time import sleep
from typing import Callable, Iterable, Union

import pytest
import yaml
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.fixtures import SubRequest
from _pytest.main import Session
from kioxia import KioxiaException
from kioxia.access.kubectl import SERVICES_NAMESPACE
from kioxia.access.kubectl_base import (
    DEFAULT_AUTH_SERVER_SECRET,
    DEFAULT_AUTHORIZATION_SERVER,
    DEFAULT_KS_NAMESPACE,
    DEFAULT_PROVISIONER_NAMESPACE,
    DEFAULT_PROVISIONER_SECRET,
)
from kioxia.client.client_cluster import ClientCluster
from kioxia.client.initiator import Initiator
from kioxia.kumoscale.control_cluster import ControlCluster
from kioxia.kumoscale.ks_cluster import KumoScaleCluster
from kioxia.kumoscale.kumoscale import KumoScale
from kioxia.lab.setup import KioxiaSetup
from kioxia.peripherals import LicenseGenerator
from kioxia.peripherals.auth_servers import Keycloak
from kioxia.provisioner.provisioner import Provisioner
from kioxia.provisioner.provisioner_rest import ProvisionerRest
from kioxia.sut_utils import SutUtils
from kubernetes.client import V1PersistentVolumeClaim, V1StorageClass

logger = logging.getLogger("kioxia")


@pytest.fixture(scope="session")
def sut_utils(sut: dict) -> SutUtils:
    """Yield the sut dictionary from the sut file."""
    return SutUtils(sut)


@pytest.fixture(scope="module")
def authentication_prov(sut_utils: SutUtils) -> dict:
    """Yield authentication provisioner dictionary from SUT."""
    keycloak_info = sut_utils.keycloak_info()
    return {
        "authServerTokenUrl": keycloak_info[1],
        "provisionerClientID": keycloak_info[2],
        "provisionerClientSecret": keycloak_info[4],
        "storagenodeClientID": keycloak_info[5],
        "storagenodeClientSecret": keycloak_info[6],
    }


def provisioner_rest_with_token(setup: str, sut_utils: SutUtils, sut: dict) -> ProvisionerRest:
    """Set token for provisioner.

    :TODO: Fix to use provisioner.rest.set_token.
    """
    provisioner_rest = sut_utils.provisioner_rest(setup)
    info = provisioner_rest.get_info()
    if info["authenticationMode"] == "OPEN_IDC":
        keycloak = sut["keycloak"]
        provisioner_rest.set_token_open_idc(
            keycloak["provisionerClientID"],
            keycloak["provisionerClientSecret"],
            keycloak["path"],
            keycloak["port"],
            keycloak["realm_name"],
            "client_credentials",
        )
    else:
        ks_ip = list(sut_utils.storage_nodes(setup).keys())[0]
        provisioner_rest.set_token_local(ks_ip, *sut_utils.storage_rbac_info(setup))
    return provisioner_rest


def set_local_prov_secrets(sut_utils: SutUtils, sut: dict) -> None:
    """Delete authorization server if exists and reset provisioner secret to Local."""
    logger.info("Setting local provisioner secrets")
    ks_cluster = sut_utils.ks_cluster()
    client_cluster_appliance = sut_utils.client_cluster("appliance")
    if ks_cluster.get_authorization_server(DEFAULT_AUTHORIZATION_SERVER):
        delete_auth_server_and_secret(ks_cluster, sut_utils)
        if client_cluster_appliance.get_secret(DEFAULT_PROVISIONER_SECRET, DEFAULT_PROVISIONER_NAMESPACE):
            client_cluster_appliance.delete_secret(DEFAULT_PROVISIONER_SECRET, DEFAULT_PROVISIONER_NAMESPACE)
            sleep(5)
            client_cluster_appliance.create_provisioner_secret(*sut_utils.provisioner_info("appliance"), sut["token"])
            sleep(5)
    if not ks_cluster.get_secret(DEFAULT_PROVISIONER_SECRET, DEFAULT_PROVISIONER_NAMESPACE):
        ks_cluster.create_provisioner_secret(*sut_utils.provisioner_info("appliance"), sut["token"])
        sleep(5)
    if not client_cluster_appliance.get_secret(DEFAULT_PROVISIONER_SECRET, DEFAULT_PROVISIONER_NAMESPACE):
        client_cluster_appliance.create_provisioner_secret(*sut_utils.provisioner_info("appliance"), sut["token"])
        sleep(5)


def delete_auth_server_and_secret(control_cluster: Union[KumoScaleCluster, ControlCluster], sut_utils: SutUtils) -> None:
    """Delete authorization server and secrets."""
    logger.info("Deleting Authorization server and secrets")
    provisioner_rest = sut_utils.provisioner_rest("appliance")
    auth_server = control_cluster.get_authorization_server(DEFAULT_AUTHORIZATION_SERVER)
    if auth_server:
        logger.info("Authorization is OPEN_IDC")
        control_cluster.delete_authorization_server(auth_server)
        sleep(2)
    if control_cluster.get_secret(DEFAULT_PROVISIONER_SECRET, DEFAULT_PROVISIONER_NAMESPACE):
        control_cluster.delete_secret(DEFAULT_PROVISIONER_SECRET, DEFAULT_PROVISIONER_NAMESPACE)
    if control_cluster.get_secret(DEFAULT_AUTH_SERVER_SECRET, DEFAULT_KS_NAMESPACE):
        control_cluster.delete_secret(DEFAULT_AUTH_SERVER_SECRET, DEFAULT_KS_NAMESPACE)
    sleep(5)
    wait_for_k8s_auth_server_state_local(control_cluster)
    wait_for_prov_auth_server_state(provisioner_rest, "LOCAL")


def wait_for_prov_auth_server_state(provisioner_rest_appliance: ProvisionerRest, state: str) -> None:
    """Wait for authorization server mode to reach the requested state.

    :TODO: Consider moving to Provisioner class.
    """
    for index in range(30):
        logger.debug(f"Retrying - {index} to get prov auth server state {state}")
        if provisioner_rest_appliance.get_info()["authenticationMode"] == state:
            return
        sleep(2)
    assert provisioner_rest_appliance.get_info()["authenticationMode"] == state


def wait_for_k8s_auth_server_state_local(control_cluster: Union[KumoScaleCluster, ControlCluster]) -> None:
    """Wait for authorization server mode to reach local state.

    :TODO: Move to KubeCtl class, maybe rewrite as "wait for state".
    """
    for index in range(30):
        logger.debug(f"Retrying - {index} to get k8s auth server state Local")
        if control_cluster.get_authorization_server(DEFAULT_AUTHORIZATION_SERVER) == {}:
            return
        sleep(2)
    assert control_cluster.get_authorization_server(DEFAULT_AUTHORIZATION_SERVER) == {}


#
# Pytest hooks.
#


def pytest_addoption(parser: Parser) -> None:
    """Aad parser sut parameter to cli."""
    parser.addoption("--kioxia-sut", help="Path to sut file.")


def pytest_collection_finish(session: Session) -> None:
    """Verify setup marker."""
    if not session.config.option.collectonly:
        get_setup_markers(session.config, session.items)


@pytest.fixture(scope="session")
def sut(request: SubRequest) -> dict:
    """Yield the sut dictionary from the sut file."""
    with open(request.config.rootpath.joinpath(request.config.getoption("--kioxia-sut")), "r") as yaml_file:
        return yaml.safe_load(yaml_file)


@pytest.fixture(scope="session")
def setup(pytestconfig: Config, request: SubRequest, sut_utils: SutUtils, sut: dict) -> KioxiaSetup:
    """Yield KioxiaSetup object based on marker.

    Tests that require setup must have one, and only one, setup marker - appliance, linkedin, or managed.
    If no setup marker was provided in the command line (for example during development), get the marker from the tests.
    """
    setup_markers = get_setup_markers(pytestconfig, request.node.items)
    if not setup_markers:
        raise KioxiaException("Missing setup marker in command line and on tests")
    if setup_markers[0] == "appliance":
        setup = sut_utils.appliance_setup()
        setup.set_local(sut["token"])
    elif setup_markers[0] == "linkedin":
        setup = sut_utils.linkedin_setup()
    elif setup_markers[0] == "managed":
        setup = sut_utils.managed_setup()
    else:
        # We should never get here. But get_setup_markers is not fool-proof, so we add this to be extra cautious.
        raise KioxiaException(f"Unknown setup marker - {setup_markers[0]}")
    logger.info(f"Setup is - {setup}")
    return setup


@pytest.fixture(scope="session")
def ks_cluster(setup: KioxiaSetup) -> KumoScaleCluster:
    """Yield KumoScaleCluster object."""
    return setup.ks_cluster


@pytest.fixture
def ks_cluster_wo_services(ks_cluster: KumoScaleCluster) -> Iterable[KumoScaleCluster]:
    """Clean cluster without prometheus and loki service."""
    ks_cluster.delete_services()
    ks_cluster.delete_pvcs(SERVICES_NAMESPACE)
    yield ks_cluster
    ks_cluster.delete_services()
    ks_cluster.delete_pvcs(SERVICES_NAMESPACE)


@pytest.fixture(scope="session")
def provisioner(setup: KioxiaSetup) -> Provisioner:
    """Yield ProvisionerCli object."""
    return setup.provisioner


@pytest.fixture
def clean_provisioner(provisioner: Provisioner) -> Iterable[Provisioner]:
    """Yield clean ProvisionerCli object."""
    provisioner.rest.clean()
    yield provisioner
    provisioner.rest.clean()


@pytest.fixture(scope="session")
def kumoscale(setup: KioxiaSetup) -> KumoScale:
    """Yield KumoScale object."""
    return list(setup.kumoscales.values())[0]


@pytest.fixture
def clean_kumoscale(kumoscale: KumoScale) -> Iterable[KumoScale]:
    """Yield clean KumoScale object."""
    for target in kumoscale.rest.get_targets():
        kumoscale.rest.remove_target(target["alias"])
    for volume in kumoscale.rest.get_volumes():
        kumoscale.rest.delete_volume(volume["persistentId"])
    yield kumoscale
    for target in kumoscale.rest.get_targets():
        kumoscale.rest.remove_target(target["alias"])
    for volume in kumoscale.rest.get_volumes():
        kumoscale.rest.delete_volume(volume["persistentId"])


@pytest.fixture(scope="session")
def initiator(setup: KioxiaSetup) -> Initiator:
    """Yield Initiator object."""
    return setup.initiator


@pytest.fixture
def clean_initiator(initiator: Initiator) -> Iterable[Initiator]:
    """Yield clean Initiator object."""
    initiator.nvme_disconnect_all()
    yield initiator
    initiator.nvme_disconnect_all()


@pytest.fixture(scope="session")
def client_cluster(setup: KioxiaSetup) -> ClientCluster:
    """Yield ClientCluster object."""
    return setup.client_cluster


@pytest.fixture
def clean_client_cluster(client_cluster: ClientCluster) -> Iterable[ClientCluster]:
    """Yield ClientCluster object for appliance setup."""
    client_cluster.delete_jobs_and_pods()
    for vol_snapshot in client_cluster.get_volume_snapshot_list():
        client_cluster.delete_volume_snapshot(vol_snapshot)
    sleep(2)
    for vol_snap_class in client_cluster.get_snapshot_class_list():
        client_cluster.delete_snapshot_class(vol_snap_class)
    client_cluster.cleanup()
    yield client_cluster
    client_cluster.delete_jobs_and_pods()
    for vol_snapshot in client_cluster.get_volume_snapshot_list():
        client_cluster.delete_volume_snapshot(vol_snapshot)
    sleep(2)
    for vol_snap_class in client_cluster.get_snapshot_class_list():
        client_cluster.delete_snapshot_class(vol_snap_class)
    client_cluster.cleanup()


@pytest.fixture(scope="session")
def keycloak(sut_utils: SutUtils) -> Keycloak:
    """Yield Keycloak object."""
    return sut_utils.keycloak()


@pytest.fixture(scope="session")
def license_generator(sut_utils: SutUtils) -> LicenseGenerator:
    """Yield LicenseGenerator object."""
    return sut_utils.license_generator()


@pytest.fixture
def sc_and_pvc_factory(client_cluster: ClientCluster) -> Callable:
    """Create storage class and PVC."""

    def _create_sc_and_pvc(
        storage_size: int = 100, bound: bool = True, **sc_parameters: object
    ) -> tuple[V1StorageClass, V1PersistentVolumeClaim]:
        storage_class_name = "sc1"
        pvc_name = "volume"
        storage_class = client_cluster.create_storage_class(name=storage_class_name, parameters=sc_parameters)
        pvc = client_cluster.create_persistent_volume_claim(
            name=pvc_name, storage_size=storage_size, storage_class=storage_class, bound=bound
        )
        return storage_class, pvc

    return _create_sc_and_pvc


def get_setup_markers(config: Config, items: list) -> list:
    """Return setup markers from command line and test items.

    :TODO: Refine the regular expression to ignore "invalid" setup markers (like *appliance*).
    """
    setup_items = [item for item in items if "setup" in item.fixturenames]
    if not setup_items:
        return []
    setup_markers = re.findall("appliance|linkedin|managed", config.getoption("-m"))
    if len(setup_markers) > 1:
        raise KioxiaException(f"Multiple setup markers {setup_markers} in {setup_items}")
    if not setup_markers:
        if any([item.get_closest_marker("appliance") for item in items]):
            setup_markers.append("appliance")
        if any([item.get_closest_marker("linkedin") for item in items]):
            setup_markers.append("linkedin")
        if any([item.get_closest_marker("managed") for item in items]):
            setup_markers.append("linkedin")
    if len(setup_markers) > 1:
        raise KioxiaException("Tests from multiple setups")
    return setup_markers
