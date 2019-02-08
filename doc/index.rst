.. clipspy documentation master file, created by
   sphinx-quickstart on Sat Oct  7 00:14:23 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

CLIPS Python bindings
=====================

.. only:: html

   :Release: |release|
   :Date: |today|

Python CFFI_ bindings for the 'C' Language Integrated Production System (CLIPS_) 6.40


Design principles
-----------------

The clipspy bindings aim to be a "pythonic" thin layer built on top of the CLIPS native C APIs. Most of the functions and the methods directly resolve to the CLIPS functions documented in the `Advanced Programming Guide`_.

Python standard paradigms are preferred such as property getters and setters, generators and magic methods.


Data types
----------

The mapping between CLIPS and Python types is as follows.

+------------------+----------------+
| CLIPS            | Python         |
+==================+================+
| INTEGER          | int            |
+------------------+----------------+
| FLOAT            | float          |
+------------------+----------------+
| STRING           | str            |
+------------------+----------------+
| SYMBOL           | Symbol *       |
+------------------+----------------+
| MULTIFIELD       | list           |
+------------------+----------------+
| FACT_ADDRESS     | Fact **        |
+------------------+----------------+
| INSTANCE_NAME    | InstanceName * |
+------------------+----------------+
| INSTANCE_ADDRESS | Instance       |
+------------------+----------------+
| EXTERNAL_ADDRESS | ffi.CData      |
+------------------+----------------+

\* The Python Symbol and InstanceName objects are `interned string`_.

** `ImpliedFact` and `TemplateFact` are `Fact` subclasses.


Basic Data Abstractions
-----------------------


Facts
+++++

A `fact` is a list of atomic values that are either referenced positionally (ordered or implied facts) or by name (unordered or template facts).


Ordered Facts
*************

Ordered or implied facts represent information as a list of elements. As the order of the data is what matters, implied facts do not have explicit templates. Ordered facts are pretty limited in terms of supported features.

.. code:: python

    import clips

    env = clips.Environment()

    # Ordered facts can only be asserted as strings
    fact = env.assert_string('(ordered-fact 1 2 3)')

    # Ordered facts data can be accessed as list elements
    assert fact[0] == 1
    assert list(fact) == [1, 2, 3]


Template Facts
**************

Template or unordered facts represent data similarly to Python dictionaries. Unordered facts require a template to be defined. Templates are formal descriptions of the data represented by the fact.

Template facts are more flexible as they support features such as constraints for the data types, default values and more. Template facts can also be modified once asserted.

.. code:: python

    import clips

    template_string = """
    (deftemplate person
      (slot name (type STRING))
      (slot surname (type STRING))
      (slot birthdate (type SYMBOL)))
    """

    env = clips.Environment()

    env.build(template_string)

    template = env.find_template('person')

    fact = template.assert_fact(name='John',
                                surname='Doe',
                                birthdate=clips.Symbol('01/01/1970'))

    assert dict(fact) == {'name': 'John',
                          'surname': 'Doe',
                          'birthdate': clips.Symbol('01/01/1970')}

    fact.modify_slots(name='Leeroy',
                      surname='Jenkins',
                      birthdate=clips.Symbol('11/05/2005'))

    for fact in env.facts():
        print(fact)


Objects
+++++++

Objects are instantiations of specific classes. They support more features such as class inheritance and message sending.

.. code:: python

    import clips

    env = clips.Environment()

    class_string = """
    (defclass MyClass (is-a USER)
      (slot One)
      (slot Two))
    """
    handler_string = """
    (defmessage-handler MyClass handler ()
      (+ ?self:One ?self:Two))
    """
    env.build(class_string)
    env.build(handler_string)

    defclass = env.find_class('MyClass')
    instance = defclass.make_instance('instance-name', One=1, Two=2)
    retval = instance.send('handler')

    assert retval == 3

    for instance in env.instances():
        print(instance)


Evaluating CLIPS code
---------------------

It is possible to quickly evaluate CLIPS statements retrieving their results in Python.

Create a `multifield` value.

.. code:: python

    import clips

    env = clips.Environment()

    env.eval("(create$ hammer drill saw screw pliers wrench)")

CLIPS functions can also be called directly without the need of building language specific strings.

.. code:: python

    import clips

    env = clips.Environment()

    env.call('create$', clips.Symbol('hammer'), 'drill', 1, 2.0)

.. note:: None of the above can be used to define CLIPS constructs. Use the `build` or `load` functions instead.


Defining CLIPS constructs
-------------------------

CLIPS constructs must be defined in CLIPS language. Use the `load` or the `build` functions to define the constructs within the engine.

Rule definition example.

.. code:: python

    import clips

    env = clips.Environment()

    rule = """
    (defrule my-rule
      (my-fact first-slot)
      =>
      (printout t "My Rule fired!" crlf))
    """
    env.build(rule)

    for rule in env.rules():
        print(rule)


Embedding Python
----------------

Through the `define_function` method, it is possible to embed Python code within the CLIPS environment.

The Python function will be accessible within CLIPS via its name as if it was defined via the `deffunction` construct.

In this example, Python regular expression support is added within the CLIPS engine.

.. code:: python

    import re
    import clips

    def regex_match(pattern, string):
        """Match pattern against string returning a multifield
        with the first element containing the full match
        followed by all captured groups.

        """
        match = re.match(pattern, string)
        if match is not None:
            return (match.group(),) + match.groups()
        else:
            return []

    env = clips.Environment()
    env.define_function(regex_match)

    env.eval('(regex_match "(www.)(.*)(.com)" "www.example.com")')


Python Objects lifecycle
------------------------

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
