"""
trafficgenerator package.
"""
import logging
import sys
from enum import Enum


class ApiType(Enum):
    """List TGN API types."""

    # pylint: disable=invalid-name
    tcl = 1
    python = 2
    rest = 3
    socket = 4


class TgnError(Exception):
    """Base exception for traffic generator exceptions."""


class TgnApp:
    """Base class for all TGN applications classes."""

    def __init__(self, logger: logging.Logger, api_wrapper: ApiType) -> None:
        """Initialize logger and API wrapper."""
        self.logger = logger
        self.api = api_wrapper


class TgnSutUtils:
    """Base class for SUT utilities."""

    def __init__(self, sut: dict) -> None:
        """Save SUT."""
        self.sut = sut


def set_logger() -> None:
    """Create and set tgn logger.

    Log level is set by the tgn-log-level pytest option.
    """
    logger = logging.getLogger("tgn")
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)8s] {%(filename)s:%(lineno)d} %(message)s", datefmt="%Y-%B-%d:%H:%M:%S"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
