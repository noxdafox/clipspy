CLIPS
=====

.. only:: html

   :Release: |release|
   :Date: |today|

Namespaces
----------

To keep the design simple and modular, the CLIPS functions are organised into namespaces.

A namespace is a way to group a set of APIs which belong to the same domain into a category.

The User shall not worry about the namespaces themselves as all the APIs are accessible through the Environment class.

Submodules
----------

clips.environment module
------------------------

.. automodule:: clips.environment
    :members:
    :undoc-members:
    :show-inheritance:

clips.facts module
------------------

.. automodule:: clips.facts
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: new_fact, slot_value, slot_values, fact_pp_string

clips.agenda module
-------------------

.. automodule:: clips.agenda
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: fact_pp_string

clips.classes module
--------------------

.. automodule:: clips.classes
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: instance_pp_string, slot_value

clips.functions module
----------------------

.. automodule:: clips.functions
    :members:
    :undoc-members:
    :show-inheritance:

clips.modules module
--------------------

.. automodule:: clips.modules
    :members:
    :undoc-members:
    :show-inheritance:

clips.router module
-------------------

.. automodule:: clips.router
    :members:
    :undoc-members:
    :show-inheritance:

clips.common module
-------------------

.. automodule:: clips.common
    :members:
    :undoc-members:
    :show-inheritance:

Module contents
---------------

.. automodule:: clips
    :members:
    :undoc-members:
    :show-inheritance:
