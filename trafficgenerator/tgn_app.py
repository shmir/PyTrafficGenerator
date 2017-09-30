"""
Base classes and utilities for TGN applications classes.

@author yoram@ignissoft.com
"""


class TgnApp(object):
    """ Base class for all TGN applications classes. """

    def __init__(self, logger, api_wrapper):
        self.logger = logger
        self.api = api_wrapper
