
import logging
import sys

import pytest


@pytest.fixture(scope='session')
def logger():
    logger = logging.getLogger('tgn')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    yield logger
