"""
Tests for TGN Tcl multithreading interpreter.

@author yoram@ignissoft.com
"""

import sys
from os import path
import unittest
import logging
from configparser import SafeConfigParser

from trafficgenerator.tgn_tcl import TgnTkMultithread, TgnTclWrapper

config_file = path.join(path.dirname(__file__), 'TrafficGenerator.ini')


class TclTest(unittest.TestCase):

    def setUp(self):
        global tcl

        config = SafeConfigParser(allow_no_value=True)
        config.read(config_file)

        logger = logging.getLogger('log')
        logger.setLevel(config.get('Logging', 'level'))
        logger.addHandler(logging.FileHandler(config.get('Logging', 'file_name')))
        logger.addHandler(logging.StreamHandler(sys.stdout))

        self.tcl_interp = TgnTkMultithread()
        self.tcl_interp.start()
        self.tcl = TgnTclWrapper(logger, self.tcl_interp)

    def tearDown(self):
        self.tcl_interp.stop()

    def testPuts(self):
        print(self.tcl.eval('set dummy "hello world"'))
