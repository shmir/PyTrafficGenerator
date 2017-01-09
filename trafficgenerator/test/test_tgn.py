"""
Tests for basic TGN object operations.

@author yoram@ignissoft.com
"""

from os import path
import sys
import unittest
import logging
from ConfigParser import SafeConfigParser

from trafficgenerator.tgn_utils import is_false, is_true, is_local_host, is_ip
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

    def testObjectsTree(self):
        """ Test object search operations. """

        root = TgnObject(objRef='root1', objType='root')
        assert(root.obj_ref() == 'root1')
        assert(root.obj_type() == 'root')
        assert(root.obj_name() == 'root1')
        node1 = TgnObject(objRef='node1', objType='node', parent=root, name='name1')
        node2 = TgnObject(objRef='node2', objType='node', parent=root, name='name2')
        node12 = TgnObject(objRef='node12', objType='node', parent=node1, name='name12')
        assert(node1.obj_ref() == 'node1')
        assert(node1.obj_type() == 'node')
        assert(node1.obj_name() == 'name1')
        assert(node1.obj_parent() == root)
        leaf1 = TgnObject(objRef='leaf1', objType='leaf', parent=node1)

        assert(root.get_object_by_name('name2') == node2)
        assert(len(root.get_objects_by_type('node')) == 2)
        assert(len(root.get_objects_by_type('no_such_object')) == 0)
        assert(root.get_object_by_ref('leaf1') == leaf1)

        assert(len(root.get_objects_by_type_in_subtree(None, 'node')) == 3)
        assert(len(node12.get_objects_by_type_in_subtree(None, 'node')) == 0)

        assert(str(root) == root.obj_name())

    def testTrueFalse(self):
        """ Test TGN true and false values. """

        for false_stc in ('False', 'false', '0', 'null', 'NONE', 'none', '::ixnet::obj-null'):
            assert(is_false(false_stc))
            assert(not is_true(false_stc))

        for true_str in ('True', 'TRUE', '1'):
            assert(is_true(true_str))
            assert(not is_false(true_str))

    def testLocalhost(self):
        """ Test TGN localhost values. """

        for location in ('127.0.0.1', 'localhost', 'Localhost/1/1'):
            assert(is_local_host(location))

        for location in ('1.2.3.4', 'hostname', '192.168.1.1/1/2'):
            assert(not is_local_host(location))

    def testIps(self):
        """ Test TGN IP values. """

        for ip in ('IPV4', 'ipv6'):
            assert(is_ip(ip))

        for ip in ('mac', 'bla'):
            assert(not is_ip(ip))
