"""
conftest utilities. Import this file in conftest.py so pytest can find all fixtures.
"""
import logging

# pylint: disable=redefined-outer-name
import pytest
import yaml
from _pytest.config.argparsing import Parser
from _pytest.fixtures import SubRequest

from trafficgenerator import ApiType


def pytest_addoption(parser: Parser) -> None:
    """Aad tgn parameters to pytest CLI."""
    parser.addoption("--tgn-sut", help="Path to sut file.")
    parser.addoption("--tgn-api", choices=["rest", "tcl"], default="rest", help="api options: rest or tcl, where applicable")
    parser.addoption(
        "--tgn-log-level",
        type=int,
        choices=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR],
        default=logging.INFO,
        help="tgn logger log level",
    )


@pytest.fixture(scope="session")
def api(request: SubRequest) -> ApiType:
    """Yield API type - generate tests will generate API types based on the api option."""
    return ApiType[request.config.getoption("--tgn-api")]


@pytest.fixture(scope="session")
def sut(request: SubRequest) -> dict:
    """Yield the sut dictionary from the sut file."""
    with open(request.config.rootpath.joinpath(request.config.getoption("--tgn-sut")), "r") as yaml_file:
        return yaml.safe_load(yaml_file)


@pytest.fixture(scope="session", autouse=True)
def log_level(request: SubRequest) -> None:
    """Yield API type - generate tests will generate API types based on the api option."""
    logging.getLogger("tgn").setLevel(request.config.getoption("--tgn-log-level"))
