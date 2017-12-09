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

  * Agenda class
  * Rule class
  * Activation class

"""

import clips

from clips.modules import Module
from clips.error import CLIPSError
from clips.common import Strategy, SalienceEvaluation, Verbosity

from clips._clips import lib, ffi


class Agenda(object):
    """In CLIPS, when all the conditions to activate a rule are met,
    The Rule action is placed on the Agenda.

    The CLIPS Agenda is responsible of sorting the Rule Activations
    according to their salience and the conflict resolution strategy.

    .. note::

       All the Agenda methods are accessible through the Environment class.

    """

    def __init__(self, env):
        self._env = env

    @property
    def agenda_changed(self):
        """True if any rule activation changes have occurred."""
        value = bool(lib.EnvGetAgendaChanged(self._env))
        lib.EnvSetAgendaChanged(self._env, int(False))

        return value

    @property
    def focus(self):
        """The module associated with the current focus.

        The Python equivalent of the CLIPS get-focus function.

        """
        return Module(self._env, lib.EnvGetFocus(self._env))

    @focus.setter
    def focus(self, module):
        """The module associated with the current focus.

        The Python equivalent of the CLIPS get-focus function.

        """
        return lib.EnvFocus(self._env, module._mdl)

    @property
    def strategy(self):
        """The current conflict resolution strategy.

        The Python equivalent of the CLIPS get-strategy function.

        """
        return Strategy(lib.EnvGetStrategy(self._env))

    @strategy.setter
    def strategy(self, value):
        """The current conflict resolution strategy.

        The Python equivalent of the CLIPS get-strategy function.

        """
        lib.EnvSetStrategy(self._env, Strategy(value))

    @property
    def salience_evaluation(self):
        """The salience evaluation behavior.

        The Python equivalent of the CLIPS get-salience-evaluation command.

        """
        return SalienceEvaluation(lib.EnvGetSalienceEvaluation(self._env))

    @salience_evaluation.setter
    def salience_evaluation(self, value):
        """The salience evaluation behavior.

        The Python equivalent of the CLIPS get-salience-evaluation command.

        """
        lib.EnvSetSalienceEvaluation(self._env, SalienceEvaluation(value))

    def rules(self):
        """Iterate over the defined Rules."""
        rule = lib.EnvGetNextDefrule(self._env, ffi.NULL)

        while rule != ffi.NULL:
            yield Rule(self._env, rule)

            rule = lib.EnvGetNextDefrule(self._env, rule)

    def find_rule(self, rule):
        """Find a Rule by name."""
        defrule = lib.EnvFindDefrule(self._env, rule.encode())
        if defrule == ffi.NULL:
            raise LookupError("Rule '%s' not found" % defrule)

        return Rule(self._env, defrule)

    def reorder(self, module=None):
        """Reorder the Activations in the Agenda.

        If no Module is specified, the current one is used.

        To be called after changing the conflict resolution strategy.

        """
        module = module._mdl if module is not None else ffi.NULL

        lib.EnvReorderAgenda(self._env, module)

    def refresh(self, module=None):
        """Recompute the salience values of the Activations on the Agenda
        and then reorder the agenda.

        The Python equivalent of the CLIPS refresh-agenda command.

        If no Module is specified, the current one is used.
        """
        module = module._mdl if module is not None else ffi.NULL

        lib.EnvRefreshAgenda(self._env, module)

    def activations(self):
        """Iterate over the Activations in the Agenda."""
        activation = lib.EnvGetNextActivation(self._env, ffi.NULL)

        while activation != ffi.NULL:
            yield Activation(self._env, activation)

            activation = lib.EnvGetNextActivation(self._env, activation)

    def clear(self):
        """Deletes all activations in the agenda."""
        if lib.EnvDeleteActivation(self._env, ffi.NULL) != 1:
            raise CLIPSError(self._env)

    def clear_focus(self):
        """Remove all modules from the focus stack.

        The Python equivalent of the CLIPS clear-focus-stack command.

        """
        lib.EnvClearFocusStack(self._env)

    def run(self, limit=None):
        """Runs the activations in the agenda.

        If limit is not None, the first activations up to limit will be run.

        Returns the number of activation which were run.

        """
        return lib.EnvRun(self._env, limit if limit is not None else -1)


class Rule:
    """A CLIPS rule.

    In CLIPS, Rules are defined via the (defrule) statement.

    """

    __slots__ = '_env', '_rule'

    def __init__(self, env, rule):
        self._env = env
        self._rule = rule

    def __hash__(self):
        return hash(self._rule)

    def __eq__(self, rule):
        return self._rule == rule._rule

    def __str__(self):
        return ffi.string(
            lib.EnvGetDefrulePPForm(self._env, self._rule)).decode()

    def __repr__(self):
        string = lib.EnvGetDefrulePPForm(self._env, self._rule)

        return "%s: %s" % (self.__class__.__name__, ffi.string(string).decode())

    @property
    def name(self):
        """Rule name."""
        return ffi.string(lib.EnvGetDefruleName(self._env, self._rule)).decode()

    @property
    def module(self):
        """The module in which the Rule is defined.

        Python equivalent of the CLIPS defrule-module command.

        """
        modname = ffi.string(lib.EnvDefruleModule(self._env, self._rule))
        defmodule = lib.EnvFindDefmodule(self._env, modname)

        return Module(self._env, defmodule)

    @property
    def deletable(self):
        """True if the Rule can be deleted."""
        return bool(lib.EnvIsDefruleDeletable(self._env, self._rule))

    @property
    def watch_firings(self):
        """Whether or not the Rule firings are being watched."""
        return bool(lib.EnvGetDefruleWatchFirings(self._env, self._rule))

    @watch_firings.setter
    def watch_firings(self, flag):
        """Whether or not the Rule firings are being watched."""
        lib.EnvSetDefruleWatchFirings(self._env, int(flag), self._rule)

    @property
    def watch_activations(self):
        """Whether or not the Rule Activations are being watched."""
        return bool(lib.EnvGetDefruleWatchActivations(self._env, self._rule))

    @watch_activations.setter
    def watch_activations(self, flag):
        """Whether or not the Rule Activations are being watched."""
        lib.EnvSetDefruleWatchActivations(self._env, int(flag), self._rule)

    def matches(self, verbosity=Verbosity.TERSE):
        """Shows partial matches and activations.

        Returns a tuple containing the combined sum of the matches
        for each pattern, the combined sum of partial matches
        and the number of activations.

        The verbosity parameter controls how much to output:

          * Verbosity.VERBOSE: detailed matches are printed to stdout
          * Verbosity.SUCCINT: a brief description is printed to stdout
          * Verbosity.TERSE: (default) nothing is printed to stdout

        """
        data = clips.data.DataObject(self._env)

        lib.EnvMatches(self._env, self._rule, verbosity, data.byref)

        return tuple(data.value)

    def refresh(self):
        """Refresh the Rule.

        The Python equivalent of the CLIPS refresh command.

        """
        if lib.EnvRefresh(self._env, self._rule) != 1:
            raise CLIPSError(self._env)

    def add_breakpoint(self):
        """Add a breakpoint for the Rule.

        The Python equivalent of the CLIPS add-break command.

        """
        lib.EnvSetBreak(self._env, self._rule)

    def remove_breakpoint(self):
        """Remove a breakpoint for the Rule.

        The Python equivalent of the CLIPS remove-break command.

        """
        if lib.EnvRemoveBreak(self._env, self._rule) != 1:
            raise CLIPSError("No breakpoint set")

    def undefine(self):
        """Undefine the Rule.

        Python equivalent of the CLIPS undefrule command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndefrule(self._env, self._rule) != 1:
            raise CLIPSError(self._env)

        self._env = None


class Activation(object):
    """When all the constraints of a Rule are satisfied,
    the Rule becomes active.

    Activations are organized within the CLIPS Agenda.

    """

    def __init__(self, env, act):
        self._env = env
        self._act = act

    def __hash__(self):
        return hash(self._act)

    def __eq__(self, act):
        return self._act == act._act

    def __str__(self):
        return activation_pp_string(self._env, self._act)

    def __repr__(self):
        return "%s: %s" % (
            self.__class__.__name__, activation_pp_string(self._env, self._act))

    @property
    def name(self):
        """Activation Rule name."""
        return ffi.string(
            lib.EnvGetActivationName(self._env, self._act)).decode()

    @property
    def salience(self):
        """Activation salience value."""
        return lib.EnvGetActivationSalience(self._env, self._act)

    @salience.setter
    def salience(self, salience):
        """Activation salience value."""
        lib.EnvSetActivationSalience(self._env, self._act, salience)

    def delete(self):
        """Remove the activation from the agenda."""
        if lib.EnvDeleteActivation(self._env, self._act) != 1:
            raise CLIPSError(self._env)

        self._env = None


def activation_pp_string(env, activation):
    buf = ffi.new('char[1024]')
    lib.EnvGetActivationPPForm(env, buf, 1024, activation)

    return ffi.string(buf).decode()
