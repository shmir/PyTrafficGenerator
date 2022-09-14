"""
trafficgenerator package.
"""
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
