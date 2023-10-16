[![Python 3.7|3.8|3.9|3.10](https://img.shields.io/badge/python-3.7%7C3.8%7C.3.9%7C.3.10-blue.svg)](https://www.python.org/downloads/release/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Base Python OO API for traffic generators (Ixia, Spirent, Xena, TRex etc.).

The package provides

- Common utilities.
- Base class for all Python OO traffic generator classes.
- Base Python wrapper over Tcl - the lowest common denominator API for TGNs is Tcl (also the inheriting packages still have some legacy code implemented in Tcl).
- Base classes for server management and VMWare.

Users
---
To install pytrafficgen for users, just pip install it
```bash
pip install pytrafficgen
pip install git+https://github.com/vmware/vsphere-automation-sdk-python.git
```

Developers
----------
To get pytrafficgen for developers, just clone it
```bash
$ git clone https://github.com/shmir/PyTrafficGenerator.git
$ make install
```

Testing
----------
For basic testing without testing VMware and Server. 
```bash
$ pytest -m "not vmware" 
```
For basic testing without testing VMWare and Server.
First edit/copy the SUT configuration file under `tests/test_sut.yaml`, and then run: 
```bash
$ pytest -s --tgn-sut=/path/to/yaml/file 
```

To upload a new version to local pypi:
```bash
$ make upload repo=REPO user=USER_NAME password=PASSWORD
```

Publishing to pypi is performed by GitHub workflow.

Documentation
-------------
http://pytrafficgenerator.readthedocs.io/en/latest/

Contact
-------
Feel free to contact me with any question or feature request at [yoram@ignissoft.com](mailto:yoram@ignissoft.com).
