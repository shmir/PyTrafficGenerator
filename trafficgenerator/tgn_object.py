"""
Base class and utilities for all TGN objects.

@author yoram@ignissoft.com
"""

from collections import OrderedDict
import gc
from abc import ABCMeta, abstractmethod


# Workaround IXN object reference bug. Sometimes IXN return object reference with float sequential
# number instead of integer. For example, endpointset->sources attribute might return:
# vport:1/protocols/bgp/neighborRange:1.0/routeRange:1.
def _WA_norm_obj_ref(obj_ref):
    return obj_ref.replace('.0', '')


class TgnObject(object):
    """ Base class for all TGN classes. """

    _data = {}
    objects = {}
    """ Dictionary of child objects <object reference: object name>. """

    def __init__(self, **data):
        """ Create new TGN object in the API.

        If object does not exist on the chassis, create it on the chassis as well.
        """

        super(TgnObject, self).__init__()
        self._data = {}
        self.objects = OrderedDict()
        self._set_data(**data)
        if 'objRef' not in self._data:
            self._data['objRef'] = self._create()
        if 'name' not in self._data:
            self._data['name'] = self.obj_ref()
        if self._data.get('parent', None):
            # todo: make sure each object has parent and test only for None parents (STC project and IXN root)..
            self._data['parent'].objects[self.obj_ref()] = self

    def __str__(self):
        return self.obj_name()

    def get_subtree(self, types=[], level=1):
        """
        :param types: list of requested types.
        :param level: how many levels to go down the subtree.
        :return: all direct children of the requested types and all their descendants down to the requested level.
        """

        if level == 0:
            return
        for child in self.get_children(*types):
            child.get_subtree(level=level - 1)

    def get_child(self, *types):
        """
        :param types: list of requested types.
        :return: the first (and in most useful cases only) child of specific type(s).
        """
        children = self.get_children(*types)
        return children[0] if any(children) else None

    def get_object_by_ref(self, obj_ref):
        """
        :param obj_ref: requested object reference.
        :return: the first object with the requested object reference in the object branch.
        """
        return self._get_object_by_key('objRef', _WA_norm_obj_ref(obj_ref))

    def get_object_by_name(self, obj_name):
        """
        :param obj_name: requested object name.
        :return: the first object with the requested object name in the object branch.
        """
        return self._get_object_by_key('name', obj_name)

    def _get_object_by_key(self, key, value):
        if self._data[key] == value:
            return self
        else:
            for child in self.objects.values():
                obj = child._get_object_by_key(key, value)
                if obj is not None:
                    return obj

    def get_objects_by_type(self, *types):
        """ Returned objects stored in memory (without re-reading them from the TGN).

        Use this method for fast access to objects in case of static configurations.

        :param types: requested object types.
        :return: all children of the specified types.
        """
        types_l = [o.lower() for o in types]
        return [o for o in self.objects.values() if o.obj_type().lower() in types_l]

    def get_object_by_type(self, *types):

        """
        :param types: requested object types.
        :return: the child of the specified types.
        """
        children = self.get_objects_by_type(*types)
        return children[0] if any(children) else None

    def get_objects_by_type_in_subtree(self, typed_objects=None, *types):
        """
        :param types: requested object types.
        :return: all children of the specified types.
        """

        if not typed_objects:
            typed_objects = []
        typed_objects += self.get_objects_by_type(*types)
        for child in self.objects.values():
            child.get_objects_by_type_in_subtree(typed_objects, *types)
        return typed_objects

    def get_objects_or_children_by_type(self, *types):
        """ Get objects if children already been read or get children.

        Use this method for fast access to objects in case of static configurations.

        :param types: requested object types.
        :return: all children of the specified types.
        """
        objects = self.get_objects_by_type(*types)
        return objects if objects else self.get_children(*types)

    def get_objects_with_object(self, obj_type, *child_types):
        """
        :param obj_type: requested object type.
        :param child_type: requested child types.
        :return: all children of the requested type that have the requested child types.
        """
        return [o for o in self.get_objects_by_type(obj_type) if
                o.get_objects_by_type(*child_types)]

    def get_ancestor_object_by_type(self, obj_type):
        """
        :param obj_type: requested ancestor type.
        :return: the ancestor of the object who's type is obj_type if exists else None.
        """

        if self.obj_type().lower() == obj_type.lower():
            return self
        else:
            if 'parent' not in self._data:
                return None
            return self.obj_parent().get_ancestor_object_by_type(obj_type)

    #
    # Simple utilities to return object _data. Maybe it's not Pythonic (more like Java) but after
    # changing the key name couple of times I decided to go for it.
    #

    def obj_name(self):
        """
        :return: object name.
        """
        return self._data['name']

    def obj_ref(self):
        """
        :return: object reference.
        """
        return self._data['objRef']

    def obj_type(self):
        """
        :return: object type.
        """
        return self._data['objType']

    def obj_parent(self):
        """
        :return: object parent.
        """
        return self._data['parent']

    @classmethod
    def get_objects_of_class(cls):
        """
        :return: all instances of the requested class.
        """
        return list(o for o in gc.get_objects() if isinstance(o, cls))

    def _set_data(self, **data):
        self._data.update(data)

    def _build_children_objs(self, child_type, output):
        children_objs = OrderedDict()
        child_obj_type = self.get_obj_class(child_type)
        for child in filter(None, output):
            child_object = child_obj_type(objRef=child, objType=child_type, parent=self)
            child_object._set_data(name=child_object.get_name())
            children_objs[child_object.obj_ref()] = child_object
        self.objects.update(children_objs)
        return children_objs


class TgnL3(object):
    """ ABC for all L3 objects. """

    __metaclass__ = ABCMeta

    @abstractmethod
    def ip(self):
        """
        :return: IP address.
        """
        pass

    @abstractmethod
    def num_ips(self):
        """
        :return: number of IP addresses.
        """
        pass
