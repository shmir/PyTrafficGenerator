"""
TGN projects utilities and errors.

@author: yoram.shamir
"""


def is_local_host(location):
    """
    :param location: Location string in the format ip[/slot/port].
    :returns: True if ip represents localhost else return False.
    """
    ip = location.split('/')[0]
    return True if (ip == '127.0.0.1' or ip == 'localhost') else False


def is_ipv4(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string is IPv4 else return False.
    """
    return str_value.lower() == 'ipv4'


def is_ipv6(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string is IPv6 else return False.
    """
    return str_value.lower() == 'ipv6'


def is_ip(str_value):
    """
    :param str_value: String to evaluate.
    :returns: True if string is IPv4 or IPv6 else return False.
    """
    return is_ipv4(str_value) or is_ipv6(str_value)


class TgnError(Exception):
    """ Base exception for traffic generator exceptions. """
    pass
