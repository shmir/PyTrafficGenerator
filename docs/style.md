Style Guide
---

As we all know, python is very stylish language.
So first, we follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and [PEP 257](https://www.python.org/dev/peps/pep-0257/).

Where this style guide conflicts with the PEPs - **fix the style guide**.

Anyway, this style guide does not try to invent anything, but select one style where several pythonic options are
available.

Imports
=======
Imports should be grouped and ordered, from the general to the specific.
There should be a blank line between groups.
```python
import logging
import os

import requests

import trafficgenerator
```
Do not use relative imports.

Methods ordering
================
Methods with class should be grouped as following:

First, all dundar (operation overloading) starting with __init__.
Then business logic methods.
Then properties.
And private methods at the end.

```python

class MyClass:

    def __init__(self):
        pass

    def __str__(self):
        pass

    def do_something(self):
        pass

    def do_something_else(self):
        pass

    @property
    def property_1(self):
        pass

    @property
    def property_2(self):
        pass

    def _private_1(self):
        pass

    def _private_2(self):
        pass
```

Strings and Docstrings
======================
Use single quotes ('') for strings and double-quotes ("") for docstrings.

The summary line should be in the the same line as the opening quotes. Add one space between the quotes and the line.

Remove the docstring, this is a standard pytest method name, and you do not need to document it, especially when your docstring does not explain much.

Do not shout, please use only lowercase and try to refrain from using exclamation marks and ellipses.

Comments
========
The golden rule for comments is - More is less.

The code should be self-explanatory and comments should be used only the explain the `WHY` and `WHAT`, the `HOW` should
be clear from the code.

Try to limit the comment to one line.

Logger
======
Log level matters - please set it carefully.

Do not shout, please use only lowercase and try to refrain from using exclamation marks and ellipses.

Line breaks
===========
Please refrain from using `\\`. Break long lines on commas, dots, etc.

Type hints
==========
Add type hinting in method definitions.

Type hinting in the code itself is optional.

General
=======
Always prefer positive conditions.

Right:
```python
if True:
    pass
```
Wrong:
```python
if not False:
    pass
```