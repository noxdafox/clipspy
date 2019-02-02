# Copyright (c) 2016-2018, Matteo Cafasso
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

  * ImpliedFact class
  * TemplateFact class
  * Template class
  * TemplateSlot class
  * DefinedFacts class
  * Facts namespace class

"""

import os

from itertools import chain

import clips

from clips.modules import Module
from clips.common import environment_builder, environment_modifier
from clips.common import CLIPSError, SaveMode, TemplateSlotDefaultType

from clips._clips import lib, ffi


class Fact:
    """CLIPS Fact base class."""

    __slots__ = '_env', '_tpl', '_fact'

    def __init__(self, env: ffi.CData, fact: ffi.CData):
        self._env = env
        self._fact = fact
        lib.RetainFact(self._fact)

    def __del__(self):
        try:
            lib.ReleaseFact(self._env, self._fact)
        except (AttributeError, TypeError):
            pass  # mostly happening during interpreter shutdown

    def __hash__(self):
        return hash(self._fact)

    def __eq__(self, fact):
        return self._fact == fact._fact

    def __str__(self):
        return ' '.join(fact_pp_string(self._env, self._fact).split())

    def __repr__(self):
        string = ' '.join(fact_pp_string(self._env, self._fact).split())

        return "%s: %s" % (self.__class__.__name__, string)

    @property
    def index(self) -> int:
        """The fact index."""
        return lib.FactIndex(self._fact)

    @property
    def exists(self) -> bool:
        """True if the fact has been asserted within CLIPS.

        Equivalent to the CLIPS (fact-existp) function.

        """
        return lib.FactExistp(self._fact)

    @property
    def template(self) -> 'Template':
        """The associated Template."""
        return Template(self._env, lib.FactDeftemplate(self._fact))

    def retract(self):
        """Retract the fact from the CLIPS environment."""
        ret = lib.Retract(self._fact)
        if ret != lib.RE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)


class ImpliedFact(Fact):
    """An Implied Fact or Ordered Fact represents its data as a list
    of elements similarly as for a Multifield.

    Implied Fact cannot be build or modified.
    They can be asserted via the Environment.assert_string() method.

    """

    def __iter__(self):
        return chain(slot_value(self._env, self._fact))

    def __len__(self):
        return len(slot_value(self._env, self._fact))

    def __getitem__(self, index):
        return slot_value(self._env, self._fact)[index]


class TemplateFact(Fact):
    """A Template or Unordered Fact represents its data as a dictionary
    where each slot name is a key.

    TemplateFact slot values can be modified.
    The Fact will be re-evaluated against the rule network once modified.

    """

    __slots__ = '_env', '_fact'

    def __init__(self, env: ffi.CData, fact: ffi.CData):
        super().__init__(env, fact)

    def __iter__(self):
        return chain(slot_values(self._env, self._fact))

    def __len__(self):
        slots = slot_values(self._env, self._fact)

        return len(tuple(slots))

    def __getitem__(self, key):
        try:
            return slot_value(self._env, self._fact, slot=str(key))
        except CLIPSError as error:
            if error.code == lib.GSE_SLOT_NOT_FOUND_ERROR:
                raise KeyError("'%s'" % key)
            else:
                raise error

    def modify_slots(self, **slots):
        """Modify one or more slot values of the Fact.

        Fact must be asserted within the CLIPS engine.

        Equivalent to the CLIPS (modify) function.

        """
        modifier = environment_modifier(self._env, 'fact')
        ret = lib.FMSetFact(modifier, self._fact)
        if ret != lib.FME_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        for slot, slot_val in slots.items():
            value = clips.values.clips_value(self._env, value=slot_val)

            ret = lib.FMPutSlot(modifier, str(slot).encode(), value)
            if ret != lib.PSE_NO_ERROR:
                if ret == lib.PSE_SLOT_NOT_FOUND_ERROR:
                    raise KeyError("'%s'" % slot)
                else:
                    raise CLIPSError(self._env, code=ret)

        if lib.FMModify(modifier) is ffi.NULL:
            raise CLIPSError(self._env, code=lib.FBError(self._env))


class Template:
    """A Fact Template is a formal representation of the fact data structure.

    In CLIPS, Templates are defined via the (deftemplate) function.

    Templates allow to assert new facts within the CLIPS environment.

    Implied facts are associated to implied templates. Implied templates
    have a limited set of features.

    """

    __slots__ = '_env', '_tpl'

    def __init__(self, env: ffi.CData, tpl: ffi.CData):
        self._env = env
        self._tpl = tpl

    def __hash__(self):
        return hash(self._tpl)

    def __eq__(self, tpl):
        return self._tpl == tpl._tpl

    def __str__(self):
        string = lib.DeftemplatePPForm(self._tpl)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DeftemplatePPForm(self._tpl)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    @property
    def implied(self) -> bool:
        """True if the Template is implied."""
        return lib.ImpliedDeftemplate(self._tpl)

    @property
    def name(self) -> str:
        """Template name."""
        return ffi.string(lib.DeftemplateName(self._tpl)).decode()

    @property
    def module(self) -> Module:
        """The module in which the Template is defined.

        Python equivalent of the CLIPS deftemplate-module command.

        """
        modname = ffi.string(lib.DeftemplateModule(self._tpl))

        return Module(self._env, lib.FindDefmodule(self._env, modname))

    @property
    def deletable(self) -> bool:
        """True if the Template can be undefined."""
        return lib.DeftemplateIsDeletable(self._tpl)

    @property
    def slots(self) -> tuple:
        """The slots of the template."""
        if self.implied:
            return ()

        value = clips.values.clips_value(self._env)

        lib.DeftemplateSlotNames(self._tpl, value)

        return tuple(TemplateSlot(self._env, self._tpl, n.encode())
                     for n in clips.values.python_value(self._env, value))

    @property
    def watch(self) -> bool:
        """Whether or not the Template is being watched."""
        return lib.GetDeftemplateWatch(self._tpl)

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Template is being watched."""
        lib.EnvSetDeftemplateWatch(self._tpl, flag)

    def facts(self) -> iter:
        """Iterate over the asserted Facts belonging to this Template."""
        fact = lib.GetNextFactInTemplate(self._tpl, ffi.NULL)
        while fact != ffi.NULL:
            yield new_fact(self._tpl, fact)

            fact = lib.GetNextFactInTemplate(self._tpl, fact)

    def assert_fact(self, **slots) -> TemplateFact:
        """Assert a new fact with the given slot values.

        Only deftemplates that have been explicitly defined can be asserted
        with this function.

        Equivalent to the CLIPS (assert) function.

        """
        builder = environment_builder(self._env, 'fact')
        ret = lib.FBSetDeftemplate(builder, lib.DeftemplateName(self._tpl))
        if ret != lib.FBE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        for slot, slot_val in slots.items():
            value = clips.values.clips_value(self._env, value=slot_val)

            ret = lib.FBPutSlot(builder, str(slot).encode(), value)
            if ret != lib.PSE_NO_ERROR:
                if ret == lib.PSE_SLOT_NOT_FOUND_ERROR:
                    raise KeyError("'%s'" % slot)
                else:
                    raise CLIPSError(self._env, code=ret)

        fact = lib.FBAssert(builder)
        if fact != ffi.NULL:
            return TemplateFact(self._env, fact)
        else:
            raise CLIPSError(self._env, code=lib.FBError(self._env))

    def undefine(self):
        """Undefine the Template.

        Equivalent to the CLIPS (undeftemplate) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undeftemplate(self._tpl, self._env):
            raise CLIPSError(self._env)

        self._env = self._tpl = None


class TemplateSlot:
    """Template Facts organize the information within Slots.

    Slots might restrict the type or amount of data they store.

    """

    __slots__ = '_env', '_tpl', '_name'

    def __init__(self, env: ffi.CData, tpl: ffi.CData, name: str):
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
    def name(self) -> str:
        """The slot name."""
        return self._name.decode()

    @property
    def multifield(self) -> bool:
        """True if the slot is a multifield slot."""
        return bool(lib.DeftemplateSlotMultiP(self._tpl, self._name))

    @property
    def types(self) -> tuple:
        """A tuple containing the value types for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-types) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotTypes(self._tpl, self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def range(self) -> tuple:
        """A tuple containing the numeric range for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-range) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotRange(self._tpl, self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def cardinality(self) -> tuple:
        """A tuple containing the cardinality for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-cardinality) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotCardinality(
                self._tpl, self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def default_type(self) -> TemplateSlotDefaultType:
        """The default value type for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-defaultp) function.

        """
        return TemplateSlotDefaultType(
            lib.DeftemplateSlotDefaultP(self._tpl, self._name))

    @property
    def default_value(self) -> type:
        """The default value for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-default-value) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotDefaultValue(
                self._tpl, self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def allowed_values(self) -> tuple:
        """A tuple containing the allowed values for this Slot.

        Equivalent to the CLIPS (slot-allowed-values) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotAllowedValues(
                self._tpl, self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)


class DefinedFacts:
    """The DefinedFacts constitute a set of a priori
    or initial knowledge specified as a collection of facts of user
    defined classes.

    When the CLIPS environment is reset, every fact specified
    within a deffacts construct in the CLIPS knowledge base
    is added to the DefinedFacts list.

    """

    __slots__ = '_env', '_dfc'

    def __init__(self, env: ffi.CData, dfc: ffi.CData):
        self._env = env
        self._dfc = dfc

    def __hash__(self):
        return hash(self._dfc)

    def __eq__(self, dfc):
        return self._dfc == dfc._dfc

    def __str__(self):
        string = lib.DeffactsPPForm(self._dfc)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DeffactsPPForm(self._dfc)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    @property
    def name(self) -> str:
        """The DefinedFacts name."""
        return ffi.string(lib.DeffactsName(self._dfc)).decode()

    @property
    def module(self) -> Module:
        """The module in which the DefinedFacts is defined.

        Python equivalent of the CLIPS (deffacts-module) command.

        """
        modname = ffi.string(lib.DeffactsModule(self._dfc))

        return Module(self._env, lib.FindDefmodule(self._env, modname))

    @property
    def deletable(self) -> bool:
        """True if the DefinedFacts can be undefined."""
        return lib.DeffactsIsDeletable(self._dfc)

    def undefine(self):
        """Undefine the DefinedFacts.

        Equivalent to the CLIPS (undeffacts) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undeffacts(self._dfc, self._env):
            raise CLIPSError(self._env)

        self._env = self._dfc = None


class Facts:
    """Facts and Templates namespace class.

    .. note::

       All the Facts methods are accessible through the Environment class.

    """

    __slots__ = '_env'

    def __init__(self, env):
        self._env = env

    @property
    def fact_duplication(self) -> bool:
        """Whether or not duplicate facts are allowed."""
        return lib.GetFactDuplication(self._env)

    @fact_duplication.setter
    def fact_duplication(self, duplication: bool) -> bool:
        return lib.SetFactDuplication(self._env, duplication)

    def facts(self) -> iter:
        """Iterate over the asserted Facts."""
        fact = lib.GetNextFact(self._env, ffi.NULL)
        while fact != ffi.NULL:
            yield new_fact(self._env, fact)

            fact = lib.GetNextFact(self._env, fact)

    def templates(self):
        """Iterate over the defined Templates."""
        template = lib.GetNextDeftemplate(self._env, ffi.NULL)
        while template != ffi.NULL:
            yield Template(self._env, template)

            template = lib.GetNextDeftemplate(self._env, template)

    def find_template(self, name: str) -> Template:
        """Find the Template by its name."""
        tpl = lib.FindDeftemplate(self._env, name.encode())
        if tpl == ffi.NULL:
            raise LookupError("Template '%s' not found" % name)

        return Template(self._env, tpl)

    def assert_string(self, string: str) -> (ImpliedFact, TemplateFact):
        """Assert a fact as string."""
        fact = lib.AssertString(self._env, string.encode())

        if fact == ffi.NULL:
            raise CLIPSError(
                self._env, code=lib.GetAssertStringError(self._env))

        return new_fact(self._env, fact)

    def load_facts(self, facts: str):
        """Load a set of facts into the CLIPS data base.

        Equivalent to the CLIPS (load-facts) function.

        Facts can be loaded from a string or from a text file.

        """
        facts = facts.encode()

        if os.path.exists(facts):
            if not lib.LoadFacts(self._env, facts):
                raise CLIPSError(self._env)
        else:
            if not lib.LoadFactsFromString(self._env, facts, len(facts)):
                raise CLIPSError(self._env)

    def save_facts(self, path, mode=SaveMode.LOCAL_SAVE):
        """Save the facts in the system to the specified file.

        Equivalent to the CLIPS (save-facts) function.

        """
        if not lib.SaveFacts(self._env, path.encode(), mode):
            raise CLIPSError(self._env)


def new_fact(env: ffi.CData, fact: ffi.CData) -> (ImpliedFact, TemplateFact):
    if lib.ImpliedDeftemplate(lib.FactDeftemplate(fact)):
        return ImpliedFact(env, fact)
    else:
        return TemplateFact(env, fact)


def slot_value(env: ffi.CData, fact: ffi.CData, slot: str = None) -> type:
    value = clips.values.clips_value(env)
    slot = slot.encode() if slot is not None else ffi.NULL
    implied = lib.ImpliedDeftemplate(lib.FactDeftemplate(fact))

    if not implied and slot == ffi.NULL:
        raise ValueError()

    ret = lib.GetFactSlot(fact, slot, value)
    if ret != lib.GSE_NO_ERROR:
        raise CLIPSError(env, code=ret)

    return clips.values.python_value(env, value)


def slot_values(env: ffi.CData, fact: ffi.CData) -> iter:
    value = clips.values.clips_value(env)
    lib.FactSlotNames(fact, value)

    return ((s, slot_value(env, fact, slot=s))
            for s in clips.values.python_value(env, value))


def fact_pp_string(env: ffi.CData, fact: ffi.CData) -> str:
    builder = environment_builder(env, 'string')
    lib.SBReset(builder)
    lib.FactPPForm(fact, builder, False)

    return ffi.string(builder.contents).decode()
