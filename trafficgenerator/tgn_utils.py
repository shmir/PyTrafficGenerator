"""
TGN projects utilities and errors.

@author: yoram.shamir
"""

import logging
from os import path
from enum import Enum
import collections


class TgnType(Enum):
    ixexplorer = 1
    ixnetwork = 2
    testcenter = 3


class ApiType(Enum):
    tcl = 1
    python = 2
    rest = 3
    socket = 4


def flatten(x):
    if isinstance(x, collections.Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


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


def new_log_file(logger, suffix, file_type='tcl'):
    """ Create new logger and log file from existing logger.

    The new logger will be create in the same directory as the existing logger file and will be named
    as the existing log file with the requested suffix.

    :param logger: existing logger
    :param suffix: string to add to the existing log file name to create the new log file name.
    :param file_type: logger file type (tcl. txt. etc.)
    :return: the newly created logger
    """

    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
    new_logger = logging.getLogger(file_type + suffix)
    if file_handler:
        logger_file_name = path.splitext(file_handler.baseFilename)[0]
        tcl_logger_file_name = logger_file_name + '-' + suffix + '.' + file_type
        new_logger.addHandler(logging.FileHandler(tcl_logger_file_name, 'w'))
        new_logger.setLevel(logger.getEffectiveLevel())

    return new_logger


class TgnError(Exception):
    """ Base exception for traffic generator exceptions. """
    pass
