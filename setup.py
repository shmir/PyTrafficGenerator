from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import io
import os
import sys

import trafficgenerator

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.txt')


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='tgnooapi',
    version=trafficgenerator.__version__,
    url='https://github.com/shmir/PyTrafficGenerator/',
    license='Apache Software License',
    author='Yoram Shamir',
    tests_require=['pytest'],
    install_requires=[],
    cmdclass={'test': PyTest},
    author_email='yoram@ignissoft.com',
    description='Base Python OO API package to automate traffic generators (Spirent TestCenter, Ixia IxNetwork etc.)',
    long_description=long_description,
    packages=['trafficgenerator', 'trafficgenerator.test'],
    include_package_data=True,
    platforms='any',
    test_suite='trafficgenerator.test.test_tcl',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing :: Traffic Generation'],
    extras_require={
        'testing': ['pytest'],
    }
)
