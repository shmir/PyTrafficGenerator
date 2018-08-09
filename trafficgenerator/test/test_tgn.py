"""
Base class for all traffic generators tests.

@author yoram@ignissoft.com
"""

from os import path
import sys
import logging
from configparser import ConfigParser


class TestTgnBase():
    """ Base class for all TGN tests - read ini file and create logger. """

    config_file = path.join(path.dirname(__file__), 'TrafficGenerator.ini')

    config = None
    logger = logging.getLogger('log')

    @classmethod
    def setupclass(cls):
        TestTgnBase.config = ConfigParser(allow_no_value=True)
        TestTgnBase.config.read(TestTgnBase.config_file)

        TestTgnBase.logger.setLevel(TestTgnBase.config.get('Logging', 'level'))
        if TestTgnBase.config.get('Logging', 'file_name'):
            TestTgnBase.logger.addHandler(logging.FileHandler(TestTgnBase.config.get('Logging', 'file_name')))
        TestTgnBase.logger.addHandler(logging.StreamHandler(sys.stdout))

    @classmethod
    def teardownclass(cls):
        pass

    def test_hello_world(self):
        print(sys.version)
