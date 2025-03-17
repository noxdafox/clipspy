# Copyright (c) 2016-2025, Matteo Cafasso
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
from clips.common import PutSlotError, PUT_SLOT_ERROR
from clips.common import environment_builder, environment_modifier
from clips.common import CLIPSError, SaveMode, TemplateSlotDefaultType

from clips._clips import lib, ffi


class Fact:
    """CLIPS Fact base class."""

    __slots__ = '_env', '_fact'

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
        template = lib.FactDeftemplate(self._fact)
        name = ffi.string(lib.DeftemplateName(template)).decode()
        return Template(self._env, name)

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
            if ret != PutSlotError.PSE_NO_ERROR:
                raise PUT_SLOT_ERROR[ret](slot)

        if lib.FMModify(modifier) is ffi.NULL:
            raise CLIPSError(self._env, code=lib.FBError(self._env))


class Template:
    """A Fact Template is a formal representation of the fact data structure.

    In CLIPS, Templates are defined via the (deftemplate) function.

    Templates allow to assert new facts within the CLIPS environment.

    Implied facts are associated to implied templates. Implied templates
    have a limited set of features.

    """

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, tpl):
        return self._ptr() == tpl._ptr()

    def __str__(self):
        string = lib.DeftemplatePPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DeftemplatePPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        tpl = lib.FindDeftemplate(self._env, self._name)
        if tpl == ffi.NULL:
            raise CLIPSError(self._env, 'Template <%s> not defined' % self.name)

        return tpl

    @property
    def implied(self) -> bool:
        """True if the Template is implied."""
        return lib.ImpliedDeftemplate(self._ptr())

    @property
    def name(self) -> str:
        """Template name."""
        return self._name.decode()

    @property
    def module(self) -> Module:
        """The module in which the Template is defined.

        Python equivalent of the CLIPS deftemplate-module command.

        """
        name = ffi.string(lib.DeftemplateModule(self._ptr())).decode()

        return Module(self._env, name)

    @property
    def deletable(self) -> bool:
        """True if the Template can be undefined."""
        return lib.DeftemplateIsDeletable(self._ptr())

    @property
    def slots(self) -> tuple:
        """The slots of the template."""
        if self.implied:
            return ()

        value = clips.values.clips_value(self._env)

        lib.DeftemplateSlotNames(self._ptr(), value)

        return tuple(TemplateSlot(self._env, self.name, n)
                     for n in clips.values.python_value(self._env, value))

    @property
    def watch(self) -> bool:
        """Whether or not the Template is being watched."""
        return lib.DeftemplateGetWatch(self._ptr())

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Template is being watched."""
        lib.DeftemplateSetWatch(self._ptr(), flag)

    def facts(self) -> iter:
        """Iterate over the asserted Facts belonging to this Template."""
        fact = lib.GetNextFactInTemplate(self._ptr(), ffi.NULL)
        while fact != ffi.NULL:
            yield new_fact(self._env, fact)

            fact = lib.GetNextFactInTemplate(self._ptr(), fact)

    def assert_fact(self, **slots) -> TemplateFact:
        """Assert a new fact with the given slot values.

        Only deftemplates that have been explicitly defined can be asserted
        with this function.

        Equivalent to the CLIPS (assert) function.

        """
        builder = environment_builder(self._env, 'fact')
        ret = lib.FBSetDeftemplate(builder, self._name)
        if ret != lib.FBE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        for slot, slot_val in slots.items():
            value = clips.values.clips_value(self._env, value=slot_val)

            ret = lib.FBPutSlot(builder, str(slot).encode(), value)
            if ret != PutSlotError.PSE_NO_ERROR:
                raise PUT_SLOT_ERROR[ret](slot)

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
        if not lib.Undeftemplate(self._ptr(), self._env):
            raise CLIPSError(self._env)


class TemplateSlot:
    """Template Facts organize the information within Slots.

    Slots might restrict the type or amount of data they store.

    """

    __slots__ = '_env', '_tpl', '_name'

    def __init__(self, env: ffi.CData, tpl: str, name: str):
        self._env = env
        self._tpl = tpl.encode()
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr()) + hash(self._name)

    def __eq__(self, slot):
        return self._ptr() == slot._ptr() and self._name == slot._name

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    def _ptr(self) -> ffi.CData:
        tpl = lib.FindDeftemplate(self._env, self._tpl)
        if tpl == ffi.NULL:
            raise CLIPSError(
                self._env, 'Template <%s> not defined' % self._tpl.decode())

        return tpl

    @property
    def name(self) -> str:
        """The slot name."""
        return self._name.decode()

    @property
    def multifield(self) -> bool:
        """True if the slot is a multifield slot."""
        return bool(lib.DeftemplateSlotMultiP(self._ptr(), self._name))

    @property
    def types(self) -> tuple:
        """A tuple containing the value types for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-types) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotTypes(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)

        raise CLIPSError(self._env)

    @property
    def range(self) -> tuple:
        """A tuple containing the numeric range for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-range) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotRange(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)

        raise CLIPSError(self._env)

    @property
    def cardinality(self) -> tuple:
        """A tuple containing the cardinality for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-cardinality) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotCardinality(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)

        raise CLIPSError(self._env)

    @property
    def default_type(self) -> TemplateSlotDefaultType:
        """The default value type for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-defaultp) function.

        """
        return TemplateSlotDefaultType(
            lib.DeftemplateSlotDefaultP(self._ptr(), self._name))

    @property
    def default_value(self) -> type:
        """The default value for this Slot.

        Equivalent to the CLIPS (deftemplate-slot-default-value) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotDefaultValue(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)

        raise CLIPSError(self._env)

    @property
    def allowed_values(self) -> tuple:
        """A tuple containing the allowed values for this Slot.

        Equivalent to the CLIPS (slot-allowed-values) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.DeftemplateSlotAllowedValues(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)

        raise CLIPSError(self._env)


class DefinedFacts:
    """The DefinedFacts constitute a set of a priori
    or initial knowledge specified as a collection of facts of user
    defined classes.

    When the CLIPS environment is reset, every fact specified
    within a deffacts construct in the CLIPS knowledge base
    is added to the DefinedFacts list.

    """

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, dfc):
        return self._ptr() == dfc._ptr()

    def __str__(self):
        string = lib.DeffactsPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DeffactsPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        dfc = lib.FindDeffacts(self._env, self._name)
        if dfc == ffi.NULL:
            raise CLIPSError(
                self._env, 'DefinedFacts <%s> not defined' % self.name)

        return dfc

    @property
    def name(self) -> str:
        """DefinedFacts name."""
        return self._name.decode()

    @property
    def module(self) -> Module:
        """The module in which the DefinedFacts is defined.

        Python equivalent of the CLIPS (deffacts-module) command.

        """
        name = ffi.string(lib.DeffactsModule(self._ptr())).decode()

        return Module(self._env, name)

    @property
    def deletable(self) -> bool:
        """True if the DefinedFacts can be undefined."""
        return lib.DeffactsIsDeletable(self._ptr())

    def undefine(self):
        """Undefine the DefinedFacts.

        Equivalent to the CLIPS (undeffacts) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undeffacts(self._ptr(), self._env):
            raise CLIPSError(self._env)


class Facts:
    """Facts and Templates namespace class.

    .. note::

       All the Facts methods are accessible through the Environment class.

    """

    __slots__ = ['_env']

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

    def templates(self) -> iter:
        """Iterate over the defined Templates."""
        template = lib.GetNextDeftemplate(self._env, ffi.NULL)
        while template != ffi.NULL:
            name = ffi.string(lib.DeftemplateName(template)).decode()
            yield Template(self._env, name)

            template = lib.GetNextDeftemplate(self._env, template)

    def find_template(self, name: str) -> Template:
        """Find the Template by its name."""
        tpl = lib.FindDeftemplate(self._env, name.encode())
        if tpl == ffi.NULL:
            raise LookupError("Template '%s' not found" % name)

        return Template(self._env, name)

    def defined_facts(self) -> iter:
        """Iterate over the DefinedFacts."""
        deffacts = lib.GetNextDeffacts(self._env, ffi.NULL)
        while deffacts != ffi.NULL:
            name = ffi.string(lib.DeffactsName(deffacts)).decode()
            yield DefinedFacts(self._env, name)

            deffacts = lib.GetNextDeffacts(self._env, deffacts)

    def find_defined_facts(self, name: str) -> DefinedFacts:
        """Find the DefinedFacts by its name."""
        dfs = lib.FindDeffacts(self._env, name.encode())
        if dfs == ffi.NULL:
            raise LookupError("DefinedFacts '%s' not found" % name)

        return DefinedFacts(self._env, name)

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
