"""
Base classes and utilities for TGN applications classes.
"""
import logging

from trafficgenerator import ApiType


class TgnApp:
    """Base class for all TGN applications classes."""

    def __init__(self, logger: logging.Logger, api_wrapper: ApiType) -> None:
        """Initialize logger and API wrapper."""
        self.logger = logger
        self.api = api_wrapper
