
+++ WORK IN PROGRESS - fully tested and functional, documentation under construction. +++

TGN - Traffic Generator

This package implements base Python OO API for traffic generators (IxNetwork, TestCenter etc.).

The package provides:
- Common utilities.
- Base class for all Python OO traffic generator classes.
- Base Python wrapper over Tcl - the lowest common denominator API for TGNs is Tcl (also the inheriting packages still
	have some legacy code implemented in Tcl).    

The Python wrapper over Tcl can work on top of any Python Tcl interpreter as long as it supports some common API.
The default Python Tcl interpreter used is Tk package but in the package there is also a sample of implementation of
Python Tcl interpreter over console (Telnet).

Logging:
- general messages + calls to underlining API + return values are logged to the logger provided by the application.
	API calls are logged at debug level 
- calls to underlining Tcl API are also logged to a separate file to create a native Tcl script that can be run as is.

Installation:
stable - pip instsll pytrafficgen

Contact:
Feel free to contact me with any question or feature request at yoram@ignissoft.com
