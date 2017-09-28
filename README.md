CLIPS Python bindings
=====================

Python CFFI bindings for CLIPS 6.30.

[CLIPS Website](http://www.clipsrules.net/)

Installation
------------

Run the command from the project root folder:

```bash
# python setup.py install
```

The CLIPS shared libraries and headers must be installed within the system.

If they are not in the default locations, they can be passed to the compiler:

```bash
$ python setup.py build_ext --include-dirs <local include dir> --libraries <local lib dir>
# python setup.py install
```
