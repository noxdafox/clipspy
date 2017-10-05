CLIPS Python bindings
=====================

.. image:: https://travis-ci.org/noxdafox/clipspy.svg?branch=master
   :target: https://travis-ci.org/noxdafox/clipspy

Python CFFI bindings for CLIPS_ 6.30.

Installation
------------

The CLIPS shared library and headers must be installed within the system.

If library and headers are not in the system default locations, they can be specified to the installer via the ``CFLAGS`` and ``LDFLAGS`` environment variables.

::

    # CFLAGS="-I<headers path>" LDFLAGS="-L<library path>" pip install pyclips

.. _CLIPS: http://www.clipsrules.net/
