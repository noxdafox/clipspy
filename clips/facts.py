# Copyright (c) 2016-2017, Matteo Cafasso
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This module contains the definition of:

  * Facts namespace class
  * ImpliedFact class
  * TemplateFact class
  * Template class
  * TemplateSlot class

"""

import os

from itertools import chain

import clips

from clips.modules import Module
from clips.error import CLIPSError
from clips.common import SaveMode, TemplateSlotDefaultType

from clips._clips import lib, ffi


class Facts:
    """Facts and Templates namespace class.

    .. note::

       All the Facts methods are accessible through the Environment class.

    """

    __slots__ = '_env'

    def __init__(self, env):
        self._env = env

    def facts(self):
        """Iterate over the asserted Facts."""
        fact = lib.EnvGetNextFact(self._env, ffi.NULL)

        while fact != ffi.NULL:
            yield new_fact(self._env, fact)

            fact = lib.EnvGetNextFact(self._env, fact)

    def templates(self):
        """Iterate over the defined Templates."""
        template = lib.EnvGetNextDeftemplate(self._env, ffi.NULL)

        while template != ffi.NULL:
            yield Template(self._env, template)

            template = lib.EnvGetNextDeftemplate(self._env, template)

    def find_template(self, name):
        """Find the Template by its name."""
        deftemplate = lib.EnvFindDeftemplate(self._env, name.encode())
        if deftemplate == ffi.NULL:
            raise LookupError("Template '%s' not found" % name)

        return Template(self._env, deftemplate)

    def assert_string(self, string):
        """Assert a fact as string."""
        fact = lib.EnvAssertString(self._env, string.encode())

        if fact == ffi.NULL:
            raise CLIPSError(self._env)

        return new_fact(self._env, fact)

    def load_facts(self, facts):
        """Load a set of facts into the CLIPS data base.

        The C equivalent of the CLIPS load-facts command.

        Facts can be loaded from a string or from a text file.

        """
        facts = facts.encode()

        if os.path.exists(facts):
            ret = lib.EnvLoadFacts(self._env, facts)
            if ret == -1:
                raise CLIPSError(self._env)
        else:
            ret = lib.EnvLoadFactsFromString(self._env, facts, -1)
            if ret == -1:
                raise CLIPSError(self._env)

        return ret

    def save_facts(self, path, mode=SaveMode.LOCAL_SAVE):
        """Save the facts in the system to the specified file.

        The Python equivalent of the CLIPS save-facts command.

        """
        ret = lib.EnvSaveFacts(self._env, path.encode(), mode)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret


class Fact(object):
    """CLIPS Fact base class."""

    __slots__ = '_env', '_fact'

    def __init__(self, env, fact):
        self._env = env
        self._fact = fact
        lib.EnvIncrementFactCount(self._env, self._fact)

    def __del__(self):
        try:
            lib.EnvDecrementFactCount(self._env, self._fact)
        except (AttributeError, TypeError):
            pass  # mostly happening during interpreter shutdown

    def __hash__(self):
        return hash(self._fact)

    def __eq__(self, fact):
        return self._fact == fact._fact

    def __str__(self):
        string = fact_pp_string(self._env, self._fact)

        return string.split('     ', 1)[-1]

    def __repr__(self):
        return "%s: %s" % (
            self.__class__.__name__, fact_pp_string(self._env, self._fact))

    @property
    def index(self):
        """The fact index."""
        return lib.EnvFactIndex(self._env, self._fact)

    @property
    def asserted(self):
        """True if the fact has been asserted within CLIPS."""
        # https://sourceforge.net/p/clipsrules/discussion/776945/thread/4f04bb9e/
        if self.index == 0:
            return False

        return bool(lib.EnvFactExistp(self._env, self._fact))

    @property
    def template(self):
        """The associated Template."""
        return Template(
            self._env, lib.EnvFactDeftemplate(self._env, self._fact))

    def assertit(self):
        """Assert the fact within the CLIPS environment."""
        if self.asserted:
            raise RuntimeError("Fact already asserted")

        lib.EnvAssignFactSlotDefaults(self._env, self._fact)

        if lib.EnvAssert(self._env, self._fact) == ffi.NULL:
            raise CLIPSError(self._env)

    def retract(self):
        """Retract the fact from the CLIPS environment."""
        if lib.EnvRetract(self._env, self._fact) != 1:
            raise CLIPSError(self._env)


class ImpliedFact(Fact):
    """An Implied Fact or Ordered Fact is a list
    where the first element is the fact template name
    followed by the remaining information.

    """

    __slots__ = '_env', '_fact', '_multifield'

    def __init__(self, env, fact):
        super(ImpliedFact, self).__init__(env, fact)
        self._multifield = []

    def __iter__(self):
        slot = slot_value(self._env, self._fact, None)

        return chain((self.template.name, ), slot)

    def __len__(self):
        return len(slot_value(self._env, self._fact, None)) + 1

    def __getitem__(self, item):
        return tuple(self)[item]

    def append(self, value):
        """Append an element to the fact."""
        if self.asserted:
            raise RuntimeError("Fact already asserted")

        self._multifield.append(value)

    def extend(self, values):
        """Append multiple elements to the fact."""
        if self.asserted:
            raise RuntimeError("Fact already asserted")

        self._multifield.extend(values)

    def assertit(self):
        """Assert the fact within CLIPS."""
        data = clips.data.DataObject(self._env)
        data.value = list(self._multifield)

        if lib.EnvPutFactSlot(
                self._env, self._fact, ffi.NULL, data.byref) != 1:
            raise CLIPSError(self._env)

        super(ImpliedFact, self).assertit()


class TemplateFact(Fact):
    """An Template Fact or Unordered Fact is a dictionary
    where each slot name is a key.

    """

    def __iter__(self):
        slots = slot_values(self._env, self._fact, self.template._tpl)

        return chain((('', self.template.name), ), slots)

    def __len__(self):
        slots = slot_values(self._env, self._fact, self.template._tpl)

        return len(tuple(slots)) + 1

    def __getitem__(self, key):
        slot = slot_value(self._env, self._fact, str(key).encode())

        if slot is not None:
            return slot

        raise KeyError(
            "'%s' fact has not slot '%s'" % (self.template.name, key))

    def __setitem__(self, key, value):
        if self.asserted:
            raise RuntimeError("Fact already asserted")

        data = clips.data.DataObject(self._env)
        data.value = value

        ret = lib.EnvPutFactSlot(
            self._env, self._fact, str(key).encode(), data.byref)
        if ret != 1:
            if key not in (s.name for s in self.template.slots()):
                raise KeyError(
                    "'%s' fact has not slot '%s'" % (self.template.name, key))

            raise CLIPSError(self._env)

    def update(self, sequence=None, **mapping):
        """Add multiple elements to the fact."""
        if sequence is not None:
            if isinstance(sequence, dict):
                for slot in sequence:
                    self[slot] = sequence[slot]
            else:
                for slot, value in sequence:
                    self[slot] = value
        if mapping:
            for slot in sequence:
                self[slot] = sequence[slot]


class Template:
    """A Fact Template is a formal representation of the fact data structure.

    In CLIPS, Templates are defined via the (deftemplate) statement.

    Templates allow to create new facts
    to be asserted within the CLIPS environment.

    Implied facts are associated to implied templates. Implied templates
    have a limited set of features. For example, they do not support slots.

    """

    __slots__ = '_env', '_tpl'

    def __init__(self, env, tpl):
        self._env = env
        self._tpl = tpl

    def __hash__(self):
        return hash(self._tpl)

    def __eq__(self, tpl):
        return self._tpl == tpl._tpl

    def __str__(self):
        if self.implied:
            string = self.name
        else:
            string = ffi.string(
                lib.EnvGetDeftemplatePPForm(self._env, self._tpl)).decode()

        return string

    def __repr__(self):
        if self.implied:
            string = self.name
        else:
            string = ffi.string(
                lib.EnvGetDeftemplatePPForm(self._env, self._tpl)).decode()

        return "%s: %s" % (self.__class__.__name__, string)

    @property
    def name(self):
        """Template name."""
        return ffi.string(
            lib.EnvGetDeftemplateName(self._env, self._tpl)).decode()

    @property
    def module(self):
        """The module in which the Template is defined.

        Python equivalent of the CLIPS deftemplate-module command.

        """
        modname = ffi.string(lib.EnvDeftemplateModule(self._env, self._tpl))
        defmodule = lib.EnvFindDefmodule(self._env, modname)

        return Module(self._env, defmodule)

    @property
    def implied(self):
        """True if the Template is implied."""
        return bool(lib.implied_deftemplate(self._tpl))

    @property
    def watch(self):
        """Whether or not the Template is being watched."""
        return bool(lib.EnvGetDeftemplateWatch(self._env, self._tpl))

    @watch.setter
    def watch(self, flag):
        """Whether or not the Template is being watched."""
        lib.EnvSetDeftemplateWatch(self._env, int(flag), self._tpl)

    @property
    def deletable(self):
        """True if the Template can be deleted."""
        return bool(lib.EnvIsDeftemplateDeletable(self._env, self._tpl))

    def slots(self):
        """Iterate over the Slots of the Template."""
        if self.implied:
            return ()

        data = clips.data.DataObject(self._env)

        lib.EnvDeftemplateSlotNames(self._env, self._tpl, data.byref)

        return tuple(
            TemplateSlot(self._env, self._tpl, n.encode()) for n in data.value)

    def new_fact(self):
        """Create a new Fact from this template."""
        fact = lib.EnvCreateFact(self._env, self._tpl)
        if fact == ffi.NULL:
            raise CLIPSError(self._env)

        return new_fact(self._env, fact)

    def undefine(self):
        """Undefine the Template.

        Python equivalent of the CLIPS undeftemplate command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndeftemplate(self._env, self._tpl) != 1:
            raise CLIPSError(self._env)


class TemplateSlot:
    """Template Facts organize the information within Slots.

    Slots might restrict the type or amount of data they store.

    """

    __slots__ = '_env', '_tpl', '_name'

    def __init__(self, env, tpl, name):
        self._env = env
        self._tpl = tpl
        self._name = name

    def __hash__(self):
        return hash(self._tpl) + hash(self._name)

    def __eq__(self, slot):
        return self._tpl == slot._tpl and self._name == slot._name

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    @property
    def name(self):
        """The slot name."""
        return self._name.decode()

    @property
    def multifield(self):
        """True if the slot is a multifield slot."""
        return bool(lib.EnvDeftemplateSlotMultiP(
            self._env, self._tpl, self._name))

    @property
    def types(self):
        """A tuple containing the value types for this Slot.

        The Python equivalent of the CLIPS deftemplate-slot-types function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvDeftemplateSlotTypes(
            self._env, self._tpl, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def range(self):
        """A tuple containing the numeric range for this Slot.

        The Python equivalent of the CLIPS deftemplate-slot-range function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvDeftemplateSlotRange(
            self._env, self._tpl, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def cardinality(self):
        """A tuple containing the cardinality for this Slot.

        The Python equivalent
        of the CLIPS deftemplate-slot-cardinality function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvDeftemplateSlotCardinality(
            self._env, self._tpl, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def default_type(self):
        """The default value type for this Slot.

        The Python equivalent of the CLIPS deftemplate-slot-defaultp function.

        """
        return TemplateSlotDefaultType(
            lib.EnvDeftemplateSlotDefaultP(self._env, self._tpl, self._name))

    @property
    def default_value(self):
        """The default value for this Slot.

        The Python equivalent
        of the CLIPS deftemplate-slot-default-value function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvDeftemplateSlotDefaultValue(
            self._env, self._tpl, self._name, data.byref)

        return data.value

    @property
    def allowed_values(self):
        """A tuple containing the allowed values for this Slot.

        The Python equivalent of the CLIPS slot-allowed-values function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvDeftemplateSlotAllowedValues(
            self._env, self._tpl, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()


def new_fact(env, fact):
    if lib.implied_deftemplate(lib.EnvFactDeftemplate(env, fact)):
        return ImpliedFact(env, fact)
    else:
        return TemplateFact(env, fact)


def slot_value(env, fact, slot):
    data = clips.data.DataObject(env)
    slot = slot if slot is not None else ffi.NULL
    implied = lib.implied_deftemplate(lib.EnvFactDeftemplate(env, fact))

    if not implied and slot == ffi.NULL:
        raise ValueError()

    if bool(lib.EnvGetFactSlot(env, fact, slot, data.byref)):
        return data.value


def slot_values(env, fact, tpl):
    data = clips.data.DataObject(env)
    lib.EnvDeftemplateSlotNames(env, tpl, data.byref)

    return ((s, slot_value(env, fact, s.encode())) for s in data.value)


def fact_pp_string(env, fact):
    buf = ffi.new('char[1024]')
    lib.EnvGetFactPPForm(env, buf, 1024, fact)

    return ffi.string(buf).decode()
