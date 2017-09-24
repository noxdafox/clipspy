CLIPS Python bindings
=====================

Python CFFI bindings for CLIPS 6.30.

[CLIPS Website](http://www.clipsrules.net/)

Installation
------------

Currently, only Python 3 is supported. Python2 and PyPy will be added soon.

Run the command from the project root folder:

```bash
# sudo python3 setup.py install
```

The CLIPS shared libraries and headers must be installed within the system.

If they are not in the default locations, they can be passed to the installer via the compiler

```bash
# sudo python3 setup.py build_ext --include-dirs <local include dir> --libraries <local lib dir>
# sudo python3 setup.py install
```
