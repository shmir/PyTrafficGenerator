"""
Tests for basic TGN object operations.

@author yoram@ignissoft.com
"""

import unittest
from mock import MagicMock

from trafficgenerator.tgn_utils import is_false, is_true, is_local_host, is_ip, flatten, TgnError
from trafficgenerator.tgn_object import TgnObject, TgnObjectsDict, TgnSubStatsDict


class TgnObjectTest(unittest.TestCase):

    def setUp(self):
        self.root = TgnObject(objRef='root1', objType='root', parent=None)
        self.root.api = None
        self.root.logger = None
        self.leaf1 = TgnObject(objRef='leaf1', objType='leaf', parent=self.root)
        self.node1 = TgnObject(objRef='node1', objType='node', parent=self.root, name='name1')
        self.node2 = TgnObject(objRef='node2', objType='node', parent=self.root, name='name2')
        self.node11 = TgnObject(objRef='node11', objType='node', parent=self.node1, name='name11')
        self.node12 = TgnObject(objRef='node12', objType='node', parent=self.node1, name='name12')
        self.leaf11 = TgnObject(objRef='leaf11', objType='leaf', parent=self.node1)
        for o in self.__dict__.values():
            if type(o) == TgnObject:
                self._mock_object(o)

    def tearDown(self):
        pass

    def testHelloWorld(self):
        pass

    def testObjectsTree(self):
        """ Test object search operations. """

        assert(self.root.obj_ref() == 'root1')
        assert(self.root.obj_type() == 'root')
        assert(self.root.obj_name() == 'root1')
        assert(self.node1.obj_ref() == 'node1')
        assert(self.node1.obj_type() == 'node')
        assert(self.node1.obj_name() == 'name1')
        assert(self.node1.obj_parent() == self.root)

        assert(self.root.get_object_by_name('name2') == self.node2)
        assert(len(self.root.get_objects_by_type('node')) == 2)
        assert(len(self.root.get_objects_by_type('no_such_object')) == 0)
        assert(self.root.get_object_by_ref('leaf1') == self.leaf1)

        assert(len(self.root.get_objects_by_type_in_subtree('node')) == 4)
        assert(len(self.root.get_objects_by_type_in_subtree('leaf')) == 2)
        assert(len(self.node11.get_objects_by_type_in_subtree('node')) == 0)

        assert(str(self.root) == self.root.obj_name())

        assert(len(self.root.get_objects_with_attribute('node', 'attr_name', 'node1')) == 1)

    def _mock_object(self, o):
        o.get_attribute = MagicMock(name='get_attribute')
        o.get_attribute('attr_name')
        o.get_attribute.return_value = o.obj_ref()

    def test_objects_dict(self):
        objects_dict = TgnObjectsDict()
        objects_dict[self.node1] = TgnObjectsDict()
        objects_dict[self.node1][self.node11] = 'node 11 entry'
        objects_dict[self.node1][self.node12] = 'node 12 entry'
        objects_dict[self.node2] = 'node 2 entry'
        self.assertRaises(TgnError, objects_dict.__setitem__, 'invalid key', '')
        assert(objects_dict[self.node2] == 'node 2 entry')
        assert(objects_dict[self.node2.name] == 'node 2 entry')
        assert(objects_dict[self.node2.ref] == 'node 2 entry')
        print(objects_dict.dumps())

    def test_sub_dict(self):
        sub_stats_dict = TgnSubStatsDict()
        sub_stats_dict[self.node1] = {'a': 1, 'b': 2}
        assert(sub_stats_dict[self.node1]['a'] == 1)
        assert(sub_stats_dict[self.node1.name]['a'] == 1)
        assert(sub_stats_dict['a'] == 1)
        sub_stats_dict[self.node2] = {'c': 3, 'd': 4}
        assert(sub_stats_dict[self.node1]['a'] == 1)
        assert(sub_stats_dict[self.node2]['c'] == 3)
        self.assertRaises(KeyError, sub_stats_dict.__getitem__, 'a')


class TgnUtilsTest(unittest.TestCase):

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

        for location in ('127.0.0.1', 'localhost', 'Localhost/1/1', '//(Offline)/1/1', 'null'):
            assert(is_local_host(location))

        for location in ('1.2.3.4', 'hostname', '192.168.1.1/1/2'):
            assert(not is_local_host(location))

    def testIps(self):
        """ Test TGN IP values. """

        for ip in ('IPV4', 'ipv6', 'ipv4if', 'IPV6IF'):
            assert(is_ip(ip))

        for ip in ('mac', 'bla'):
            assert(not is_ip(ip))

    def testFlatten(self):
        nl = [1, [11, [111]], 2, [22]]
        assert(len(nl) == 4)
        assert(type(nl[1]) == list)
        assert(type(nl[2]) == int)
        assert(len(flatten(nl)) == 5)
        assert(type(flatten(nl)[1]) == int)
        assert(type(flatten(nl)[2]) == int)
