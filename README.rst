CLIPS Python bindings
=====================

Python CFFI_ bindings for the 'C' Language Integrated Production System CLIPS_ 6.41.

:Source: https://github.com/noxdafox/clipspy
:Documentation: https://clipspy.readthedocs.io
:Download: https://pypi.python.org/pypi/clipspy

|build badge| |docs badge|

.. |build badge| image:: https://github.com/noxdafox/clipspy/actions/workflows/action.yml/badge.svg
   :target: https://github.com/noxdafox/clipspy/actions/workflows/action.yml
   :alt: Build Status
.. |docs badge| image:: https://readthedocs.org/projects/clipspy/badge/?version=latest
   :target: http://clipspy.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status


Initially developed at NASA's Johnson Space Center, CLIPS is a rule-based programming language useful for creating expert and production systems where a heuristic solution is easier to implement and maintain than an imperative one. CLIPS is designed to facilitate the development of software to model human knowledge or expertise.

CLIPSPy brings CLIPS capabilities within the Python ecosystem.

Installation
------------

Linux
+++++

On Linux CLIPSPy is packaged for `x86_64` architecture as a wheel according to PEP-513_ guidelines.
Most of the distributions should be supported.

.. code:: bash

    $ pip install clipspy

MacOsx
++++++

Apple Silicon is supported for Python versions greater than 3.11.

.. code:: bash

    $ pip install clipspy

Windows
+++++++

CLIPSPy comes as a wheel for most of the Python versions and architectures.

.. code:: batch

    > pip install clipspy

Building from sources
+++++++++++++++++++++

The provided Makefiles take care of retrieving the CLIPS source code and compiling the Python bindings together with it.

.. code:: bash

    $ make
    # make install

Please check the documentation_ for more information regarding building CLIPSPy from sources.

Example
-------

.. code:: python

    import clips

    DEFTEMPLATE_STRING = """
    (deftemplate person
      (slot name (type STRING))
      (slot surname (type STRING))
      (slot birthdate (type SYMBOL)))
    """

    DEFRULE_STRING = """
    (defrule hello-world
      "Greet a new person."
      (person (name ?name) (surname ?surname))
      =>
      (println "Hello " ?name " " ?surname))
    """

    environment = clips.Environment()

    # define constructs
    environment.build(DEFTEMPLATE_STRING)
    environment.build(DEFRULE_STRING)

    # retrieve the fact template
    template = environment.find_template('person')

    # assert a new fact through its template
    fact = template.assert_fact(name='John',
                                surname='Doe',
                                birthdate=clips.Symbol('01/01/1970'))

    # fact slots can be accessed as dictionary elements
    assert fact['name'] == 'John'

    # execute the activations in the agenda
    environment.run()

.. _CLIPS: http://www.clipsrules.net/
.. _CFFI: https://cffi.readthedocs.io/en/latest/index.html
.. _PEP-513: https://www.python.org/dev/peps/pep-0513/
.. _documentation: https://clipspy.readthedocs.io
