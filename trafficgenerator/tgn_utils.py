"""
TGN projects utilities and errors.

@author: yoram.shamir
"""

from enum import Enum


class TgnType(Enum):
    ixexplorer = 1
    ixnetwork = 2
    testcenter = 3


class ApiType(Enum):
    tcl = 1
    python = 2
    rest = 3
    socket = 4


def is_true(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string represents True TGN attribute value else return False.
    """
    return str_value.lower() in ('true', '1', '::ixnet::ok')


def is_false(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string represents TGN attribute False value else return True.
    """
    return str_value.lower() in ('false', '0', 'null', 'none', '::ixnet::obj-null')


def is_local_host(location):
    """
    :param location: Location string in the format ip[/slot[/port]].
    :returns: True if ip represents localhost or offilne else return False.
    """
    return any(x in location.lower() for x in ('localhost', '127.0.0.1', 'offline', 'null'))


def is_ipv4(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string represents IPv4 else return False.
    """
    return str_value.lower() in ('ipv4', 'ipv4if')


def is_ipv6(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string represents IPv6 else return False.
    """
    return str_value.lower() in ('ipv6', 'ipv6if')


def is_ip(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string is IPv4 or IPv6 else return False.
    """
    return is_ipv4(str_value) or is_ipv6(str_value)


class TgnError(Exception):
    """ Base exception for traffic generator exceptions. """
    pass
