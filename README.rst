CLIPS Python bindings
=====================

.. image:: https://travis-ci.org/noxdafox/clipspy.svg?branch=master
   :target: https://travis-ci.org/noxdafox/clipspy
   :alt: Build Status

Python CFFI_ bindings for CLIPS_ 6.30

Installation
------------

The CLIPS shared library and headers must be installed within the system.

If library and headers are not in the system default locations, they can be specified to the installer via the ``CFLAGS`` and ``LDFLAGS`` environment variables.

.. code:: bash

    # CFLAGS="-I<headers path>" LDFLAGS="-L<library path>" pip install pyclips

Design principles
-----------------

The clipspy bindings aim to be a "pythonic" thin layer built on top of the CLIPS native C APIs. Most of the functions and the methods directly resolve to the CLIPS functions documented in the `Advanced Programming Guide`_.

Python standard paradigms are preferred such as property getters and setters, generators and magic methods.

Data types
----------

The mapping between CLIPS and Python types is as follows.

+------------------+------------+
| CLIPS            | Python     |
+==================+============+
| INTEGER          | int        |
+------------------+------------+
| FLOAT            | float      |
+------------------+------------+
| STRING           | str        |
+------------------+------------+
| SYMBOL           | Symbol *   |
+------------------+------------+
| MULTIFIELD       | list       |
+------------------+------------+
| FACT_ADDRESS     | Fact **    |
+------------------+------------+
| INSTANCE_ADDRESS | Instance   |
+------------------+------------+
| EXTERNAL_ADDRESS | ffi.CData  |
+------------------+------------+

\* The Python Symbol object is a `interned string`_

** `ImpliedFact` and `TemplateFact` are `Fact` subclasses

Namespaces
----------

To keep the ``Environment`` interface simple, the CLIPS functions have been grouped into five different namespaces. Each namespace is accessible via an ``Environment`` specific attribute.

* ``Environment.facts``: facts and templates
* ``Environment.agenda``: rules and activations
* ``Environment.classes``: classes and instances
* ``Environment.modules``: modules and global variables
* ``Environment.functions``: functions, generics and methods


Objects lifecycle
-----------------

All clipspy objects are simple wrappers of CLIPS data structures. This means every object lifecycle is bound to the CLIPS data structure it refers to.

In most of the cases, deleting or undefining an object makes it unusable.

Example:

.. code:: python

    template = env.facts.find_template('some-fact')

    # remove the Template from the CLIPS Environment
    template.undefine()  # from here on, the template object is unusable

    # this will cause an error
    print(template)

If the previous example is pretty straightforward, there are more subtle scenarios.

.. code:: python

    templates = tuple(env.facts.templates())

    # remove all CLIPS constructs from the environment
    env.clear()  # from here on, all the previously created objects are unusable

    # this will cause an error
    for template in templates:
        print(template)

API Documentation
-----------------

The ``doc`` folder contains the sources to generate the documentation via ``sphinx``.

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
.. _`Advanced Programming Guide`: http://clipsrules.sourceforge.net/documentation/v630/apg.pdf
.. _`interned string`: https://docs.python.org/3/library/sys.html?highlight=sys%20intern#sys.intern
