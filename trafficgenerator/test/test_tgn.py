"""
Base class for all traffic generators tests.

@author yoram@ignissoft.com
"""

from os import path
import sys
import unittest
import logging
from configparser import SafeConfigParser

from trafficgenerator.tgn_utils import ApiType


class TgnTest(unittest.TestCase):
    """ Base class for all TGN tests - read ini file and create logger. """

    config_file = path.join(path.dirname(__file__), 'TrafficGenerator.ini')

    config = None
    logger = logging.getLogger('log')

    @classmethod
    def setUpClass(cls):
        TgnTest.config = SafeConfigParser(allow_no_value=True)
        TgnTest.config.read(TgnTest.config_file)

        TgnTest.logger.setLevel(TgnTest.config.get('Logging', 'level'))
        if TgnTest.config.get('Logging', 'file_name'):
            TgnTest.logger.addHandler(logging.FileHandler(TgnTest.config.get('Logging', 'file_name')))
        TgnTest.logger.addHandler(logging.StreamHandler(sys.stdout))

        # To support non pytest runners.
        try:
            TgnTest.api = ApiType[pytest.config.getoption('--api')]  # @UndefinedVariable
        except Exception as _:
            TgnTest.api = ApiType[TgnTest.config.get('Server', 'api')]

    @classmethod
    def tearDownClass(cls):
        pass

    def testHelloWorld(self):
        print(sys.version)
