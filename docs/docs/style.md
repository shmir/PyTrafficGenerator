Style Guide
---

As we all know, python is very stylish language.
So first, we follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and [PEP 257](https://www.python.org/dev/peps/pep-0257/).

Second, to avoid long philosophical debates over style, and minimize style diffs, we use [black formatter](https://github.com/psf/black).
Then we also use [isort](https://pycqa.github.io/isort/) to keep our imports in order.
And finally, we use [sonarlint](https://www.sonarlint.org/), [pylint](https://pylint.org/) and [flake8](https://github.com/pycqa/flake8).

After this, there is not much left :) And yet...

Where this style guide conflicts with the PEPs and tools above - **fix the style guide**.

Imports
=======
Do not use relative imports.

Other than this, just let [isort](https://pycqa.github.io/isort/) order your imports.

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

Docstrings
==========
Do not shout, please use only lowercase and try to refrain from using exclamation marks and ellipses.

Comments
========
The golden rule for comments is - More is less.

The code should be self-explanatory and comments should be used only to explain the `WHY` and `WHAT`, the `HOW` should
be clear from the code.

Try to limit the comment to one line.

Logger
======
Log level matters - please set it carefully.

Do not shout, please use only lowercase and try to refrain from using exclamation marks and ellipses.

Line breaks
===========
Please refrain from using `\\`. Let [black](https://github.com/psf/black) break lines for you.

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
