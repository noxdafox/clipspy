.. clipspy documentation master file, created by
   sphinx-quickstart on Sat Oct  7 00:14:23 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

CLIPS Python bindings
=====================

Python CFFI_ bindings for the 'C' Language Integrated Production System (CLIPS_) 6.30

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

Python native types returned by functions defined within an Environment are mapped to the following CLIPS symbols.

+------------------+------------+
| CLIPS            | Python     |
+==================+============+
| nil              | None       |
+------------------+------------+
| TRUE             | True       |
+------------------+------------+
| FALSE            | False      |
+------------------+------------+

\* The Python Symbol object is a `interned string`_

** `ImpliedFact` and `TemplateFact` are `Fact` subclasses


Objects lifecycle
-----------------

All clipspy objects are simple wrappers of CLIPS data structures. This means every object lifecycle is bound to the CLIPS data structure it refers to.

In most of the cases, deleting or undefining an object makes it unusable.

Example:

.. code:: python

    template = env.find_template('some-fact')

    # remove the Template from the CLIPS Environment
    template.undefine()  # from here on, the template object is unusable

    # this will cause an error
    print(template)

If the previous example is pretty straightforward, there are more subtle scenarios.

.. code:: python

    templates = tuple(env.templates())

    # remove all CLIPS constructs from the environment
    env.clear()  # from here on, all the previously created objects are unusable

    # this will cause an error
    for template in templates:
        print(template)


API documentation
-----------------

.. toctree::
   :maxdepth: 2

   clips

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _CLIPS: http://www.clipsrules.net/
.. _CFFI: https://cffi.readthedocs.io/en/latest/index.html
.. _`Advanced Programming Guide`: http://clipsrules.sourceforge.net/documentation/v630/apg.pdf
.. _`interned string`: https://docs.python.org/3/library/sys.html?highlight=sys%20intern#sys.intern
