CLIPS Python bindings
=====================

.. image:: https://travis-ci.org/noxdafox/clipspy.svg?branch=master
   :target: https://travis-ci.org/noxdafox/clipspy

Python CFFI bindings for CLIPS_ 6.30.

Installation
------------

The CLIPS shared libraries and headers must be installed within the system.

Run the command from the project root folder:

::

    # python setup.py install

If they are not in the system default locations, they can be passed to the installer:

::

    $ python setup.py build_ext --include-dirs <local include dir> --library-dirs <local lib dir>
    # python setup.py install

.. _CLIPS: http://www.clipsrules.net/
