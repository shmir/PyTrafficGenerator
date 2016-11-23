"""
Tests for basic TGN object operations.

@author yoram@ignissoft.com
"""

from os import path
import sys
import unittest
import logging
from ConfigParser import SafeConfigParser

from trafficgenerator.tgn_object import TgnObject


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
        TgnTest.logger.addHandler(logging.FileHandler(TgnTest.config.get('Logging', 'file_name')))
        TgnTest.logger.addHandler(logging.StreamHandler(sys.stdout))

    @classmethod
    def tearDownClass(cls):
        pass

    def testHelloWorld(self):
        print sys.version


class TgnObjectTest(TgnTest):

    def createObject(self):
        root = TgnObject(objRef='root1', objType='root')
        assert(root.obj_ref() == 'root1')
        assert(root.obj_type() == 'root')
        assert(root.obj_name() == 'root1')
        node1 = TgnObject(objRef='node1', objType='node', parent=root, name='name1')
        node2 = TgnObject(objRef='node2', objType='node', parent=root, name='name2')
        assert(node1.obj_ref() == 'node1')
        assert(node1.obj_type() == 'node')
        assert(node1.obj_name() == 'name1')
        assert(node1.obj_parent() == root)
        leaf1 = TgnObject(objRef='leaf1', objType='leaf', parent=node1)

        assert(root.get_object_by_name('name2') == node2)
        assert(len(root.get_objects_by_type('node')) == 2)
        assert(len(root.get_objects_by_type('no_such_object')) == 0)
        assert(root.get_object_by_ref('leaf1') == leaf1)
