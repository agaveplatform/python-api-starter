# agaveflask #

## Overview ##

A common set of Python modules for writing flask services for the Agave Platform. The package officially requires Python
3.4+, though some functionality may work with Python 2.


## Installation ##
pip install agaveflask

Requires Python header files and a C++ compiler on top of gcc. On Debian/Ubuntu systems:
apt-get install python3-dev g++


## Usage ##
agaveflask provides the following modules:

* auth.py - configurable authentication/authorization routines.
* config.py - config parsing.
* errors.py - exception classes raised by agaveflask.
* store.py - python bindings for persistence.
* utils.py - general request/response utilities.
