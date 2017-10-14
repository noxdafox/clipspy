CLIPS Python bindings
=====================

.. image:: https://travis-ci.org/noxdafox/clipspy.svg?branch=master
   :target: https://travis-ci.org/noxdafox/clipspy
   :alt: Build Status
.. image:: https://readthedocs.org/projects/clipspy/badge/?version=latest
   :target: http://clipspy.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Python CFFI_ bindings for CLIPS_ 6.30

Installation
------------

The CLIPS shared library and headers must be installed within the system.

If library and headers are not in the system default locations, they can be specified to the installer via the ``CFLAGS`` and ``LDFLAGS`` environment variables.

.. code:: bash

    # CFLAGS="-I<headers path>" LDFLAGS="-L<library path>" pip install pyclips

Documentation
-------------

Documentation available on `Read The Docs`_.

Example
-------

.. code:: python

    from clips import Environment, Symbol

    environment = Environment()

    # load constructs into the environment
    environment.load('constructs.clp')

    # assert a fact as string
    environment.facts.assert_string('(a-fact)')

    # retrieve a fact template
    template = environment.facts.find_template('a-fact')

    # create a new fact from the template
    fact = template.new_fact()

    # implied (ordered) facts are accessed as lists
    fact.append(42)
    fact.extend(("foo", "bar"))

    # assert the fact within the environment
    fact.assertit()

    # retrieve another fact template
    template = environment.facts.find_template('another-fact')
    fact = template.new_fact()

    # template (unordered) facts are accessed as dictionaries
    fact["slot-name"] = Symbol("foo")

    fact.assertit()

    # execute the activations in the agenda
    environment.agenda.run()

.. _CLIPS: http://www.clipsrules.net/
.. _CFFI: https://cffi.readthedocs.io/en/latest/index.html
.. _`Read The Docs`: http://clipspy.readthedocs.io
