
Base Python OO API for traffic generators (Ixia, Spirent, Xena etc.).

The package provides

- Common utilities.
- Base class for all Python OO traffic generator classes.
- Base Python wrapper over Tcl - the lowest common denominator API for TGNs is Tcl (also the inheriting packages still have some legacy code implemented in Tcl).

Users
-----
To install pycmts for users, just pip install it::

    $ pip install pytrafficgen

Developers
----------
To get pytrafficgen for developers, just clone it::

    $ git clone https://github.com/shmir/PyTrafficGenerator.git

To upload new version to local pypi::

    $ make upload repo=REPO user=USER_NAME password=PASSWORD

Contact
-------
Feel free to contact me with any question or feature request at yoram@ignissoft.com
