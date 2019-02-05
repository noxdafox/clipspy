CLIPS Python bindings
=====================

Python CFFI_ bindings for the ‘C’ Language Integrated Production System CLIPS_ 6.40.

:Source: https://github.com/noxdafox/clipspy
:Documentation: https://clipspy.readthedocs.io
:Download: https://pypi.python.org/pypi/clipspy

|travis badge| |docs badge|

.. |travis badge| image:: https://travis-ci.org/noxdafox/clipspy.svg?branch=master
   :target: https://travis-ci.org/noxdafox/clipspy
   :alt: Build Status
.. |docs badge| image:: https://readthedocs.org/projects/clipspy/badge/?version=latest
   :target: http://clipspy.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status


Initially developed at NASA’s Johnson Space Center, CLIPS is a rule-based programming language useful for creating expert and production systems where a heuristic solution is easier to implement and maintain than an imperative one. CLIPS is designed to facilitate the development of software to model human knowledge or expertise.

CLIPSPy brings CLIPS capabilities within the Python ecosystem.

Installation
------------

Windows
+++++++

CLIPSPy comes as a wheel for most of the Python versions and architectures. Therefore, it can be installed from Pip.

.. code:: batch

    > pip install clipspy

Linux
+++++

Building from sources
*********************

The provided Makefile takes care of retrieving the CLIPS source code and compiling the Python bindings together with it.

.. code:: bash

    $ make
    # make install

The following tools are required to build the sources.

 - gcc
 - make
 - wget
 - unzip
 - python
 - python-cffi

The following conditional variables are accepted by the Makefile.

 - PYTHON: Python interpreter to use, default `python`
 - CLIPS_SOURCE_URL: Location from where to retrieve CLIPS source code archive.
 - SHARED_LIBRARY_DIR: Path where to install CLIPS shared library, default `/usr/lib`

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

    environment = clips.Environment()

    # load constructs into the environment from a file
    environment.load('constructs.clp')

    # define a fact template
    environment.build(DEFTEMPLATE_STRING)

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
