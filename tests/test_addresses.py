"""
Tests addresses module.
"""
import logging
import sys

import pytest
from pycnr.addresses import MacUtils

logger = logging.getLogger("pylgi")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


logging.basicConfig(level=logging.DEBUG)


def test_macs():
    """Test valid MACs of all shapes and forms."""
    assert MacUtils("11:22:33:44:55:66").standard == "11:22:33:44:55:66"
    assert MacUtils("11-22-33-44-55-66").standard == "11:22:33:44:55:66"
    assert MacUtils("1122.3344.5566").standard == "11:22:33:44:55:66"
    assert MacUtils("112233445566").standard == "11:22:33:44:55:66"

    assert MacUtils("11:22:33:44:55:66").hyphened == "11-22-33-44-55-66"
    assert MacUtils("11-22-33-44-55-66").hyphened == "11-22-33-44-55-66"
    assert MacUtils("1122.3344.5566").hyphened == "11-22-33-44-55-66"
    assert MacUtils("112233445566").hyphened == "11-22-33-44-55-66"

    assert MacUtils("11:22:33:44:55:66").dotted == "1122.3344.5566"
    assert MacUtils("11-22-33-44-55-66").dotted == "1122.3344.5566"
    assert MacUtils("1122.3344.5566").dotted == "1122.3344.5566"
    assert MacUtils("112233445566").dotted == "1122.3344.5566"

    assert MacUtils("11:22:33:44:55:66").no_delimiter == "112233445566"
    assert MacUtils("11-22-33-44-55-66").no_delimiter == "112233445566"
    assert MacUtils("1122.3344.5566").no_delimiter == "112233445566"
    assert MacUtils("112233445566").no_delimiter == "112233445566"

    assert str(MacUtils("11:22:33:44:55:66")) == "1122.3344.5566"
    assert str(MacUtils("11-22-33-44-55-66")) == "1122.3344.5566"
    assert str(MacUtils("1122.3344.5566")) == "1122.3344.5566"
    assert str(MacUtils("112233445566")) == "1122.3344.5566"

    assert MacUtils("00:01:02:03:04:05").standard == "00:01:02:03:04:05"
    assert MacUtils("00:01:02:03:04:05").hyphened == "00-01-02-03-04-05"
    assert MacUtils("00:01:02:03:04:05").dotted == "0001.0203.0405"
    assert MacUtils("00:01:02:03:04:05").no_delimiter == "000102030405"
    assert MacUtils("00:01:02:03:04:05").no_leading_zeros == "0:1:2:3:4:5"

    assert MacUtils("0:1:2:3:4:5").standard == "00:01:02:03:04:05"
    assert MacUtils("0:1:2:3:4:5").hyphened == "00-01-02-03-04-05"
    assert MacUtils("0:1:2:3:4:5").dotted == "0001.0203.0405"
    assert MacUtils("0:1:2:3:4:5").no_delimiter == "000102030405"
    assert MacUtils("0:1:2:3:4:5").no_leading_zeros == "0:1:2:3:4:5"


def test_invalid_mac():
    """Test invalid MACs."""
    with pytest.raises(ValueError):
        MacUtils("invalid")

    with pytest.raises(ValueError):
        MacUtils("zz:22:33:44:55:66")

    with pytest.raises(ValueError):
        MacUtils(":22:33:44:55:66")

    with pytest.raises(ValueError):
        MacUtils("11-22-33-44-55")

    with pytest.raises(ValueError):
        MacUtils("1122.33.5566")

    with pytest.raises(ValueError):
        MacUtils("11:22:33::55:66")

    with pytest.raises(ValueError):
        MacUtils("11:22:33.44.55:66")
