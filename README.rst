CLIPS Python bindings
=====================

Python CFFI_ bindings for the ‘C’ Language Integrated Production System CLIPS_ 6.31.

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

Linux
+++++

On Linux, CLIPSPy is packaged for `x86_64` architectures as a wheel according to PEP-513_ guidelines.
Most of the distributions should be supported.

.. code:: bash

    $ [sudo] pip install clipspy

Windows
+++++++

CLIPSPy comes as a wheel for most of the Python versions and architectures.

.. code:: batch

    > pip install clipspy

Building from sources
+++++++++++++++++++++

The provided Makefile takes care of retrieving the CLIPS source code and compiling the Python bindings together with it.

.. code:: bash

    $ make
    $ sudo make install

Please check the documentation_ for more information regarding building CLIPSPy from sources.

Example
-------

.. code:: python

    from clips import Environment, Symbol

    environment = Environment()

    # load constructs into the environment
    environment.load('constructs.clp')

    # assert a fact as string
    environment.assert_string('(a-fact)')

    # retrieve a fact template
    template = environment.find_template('a-fact')

    # create a new fact from the template
    fact = template.new_fact()

    # implied (ordered) facts are accessed as lists
    fact.append(42)
    fact.extend(("foo", "bar"))

    # assert the fact within the environment
    fact.assertit()

    # retrieve another fact template
    template = environment.find_template('another-fact')
    fact = template.new_fact()

    # template (unordered) facts are accessed as dictionaries
    fact["slot-name"] = Symbol("foo")

    fact.assertit()

    # execute the activations in the agenda
    environment.run()

.. _CLIPS: http://www.clipsrules.net/
.. _CFFI: https://cffi.readthedocs.io/en/latest/index.html
.. _PEP-513: https://www.python.org/dev/peps/pep-0513/
.. _documentation: https://clipspy.readthedocs.io
