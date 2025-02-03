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

  * Agenda class
  * Rule class
  * Activation class

"""

import clips

from clips.modules import Module
from clips.common import environment_builder
from clips.common import CLIPSError, Strategy, SalienceEvaluation, Verbosity

from clips._clips import lib, ffi


class Rule:
    """A CLIPS rule.

    In CLIPS, Rules are defined via the (defrule) statement.

    """

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, rule):
        return self._ptr() == rule._ptr()

    def __str__(self):
        string = lib.DefrulePPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefrulePPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        rule = lib.FindDefrule(self._env, self._name)
        if rule == ffi.NULL:
            raise CLIPSError(self._env, 'Rule <%s> not defined' % self.name)

        return rule

    @property
    def name(self) -> str:
        """Rule name."""
        return self._name.decode()

    @property
    def module(self) -> Module:
        """The module in which the Rule is defined.

        Equivalent to the CLIPS (defrule-module) function.

        """
        name = ffi.string(lib.DefruleModule(self._ptr())).decode()

        return Module(self._env, name)

    @property
    def deletable(self) -> bool:
        """True if the Rule can be deleted."""
        return lib.DefruleIsDeletable(self._ptr())

    @property
    def watch_firings(self) -> bool:
        """Whether or not the Rule firings are being watched."""
        return lib.DefruleGetWatchFirings(self._ptr())

    @watch_firings.setter
    def watch_firings(self, flag: bool):
        """Whether or not the Rule firings are being watched."""
        lib.DefruleSetWatchFirings(self._ptr(), flag)

    @property
    def watch_activations(self) -> bool:
        """Whether or not the Rule Activations are being watched."""
        return lib.DefruleGetWatchActivations(self._ptr())

    @watch_activations.setter
    def watch_activations(self, flag: bool):
        """Whether or not the Rule Activations are being watched."""
        lib.DefruleSetWatchActivations(self._ptr(), flag)

    def matches(self, verbosity: Verbosity = Verbosity.TERSE):
        """Shows partial matches and activations.

        Returns a tuple containing the combined sum of the matches
        for each pattern, the combined sum of partial matches
        and the number of activations.

        The verbosity parameter controls how much to output:

          * Verbosity.VERBOSE: detailed matches are printed to stdout
          * Verbosity.SUCCINT: a brief description is printed to stdout
          * Verbosity.TERSE: (default) nothing is printed to stdout

        """
        value = clips.values.clips_value(self._env)

        lib.Matches(self._ptr(), verbosity, value)

        return clips.values.python_value(self._env, value)

    def refresh(self):
        """Refresh the Rule.

        Equivalent to the CLIPS (refresh) function.

        """
        lib.Refresh(self._ptr())

    def add_breakpoint(self):
        """Add a breakpoint for the Rule.

        Equivalent to the CLIPS (add-break) function.

        """
        lib.SetBreak(self._ptr())

    def remove_breakpoint(self):
        """Remove a breakpoint for the Rule.

        Equivalent to the CLIPS (remove-break) function.

        """
        if not lib.RemoveBreak(self._env, self._ptr()):
            raise CLIPSError("No breakpoint set")

    def undefine(self):
        """Undefine the Rule.

        Equivalent to the CLIPS (undefrule) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefrule(self._ptr(), self._env):
            raise CLIPSError(self._env)


class Activation:
    """When all the constraints of a Rule are satisfied,
    the Rule becomes active.

    Activations are organized within the CLIPS Agenda.

    """

    def __init__(self, env: ffi.CData, act: ffi.CData):
        self._env = env
        self._act = act
        self._pp = activation_pp_string(self._env, self._act)
        self._rule_name = ffi.string(lib.ActivationRuleName(self._act))

    def __hash__(self):
        return hash(self._act)

    def __eq__(self, act):
        return self._act == act._act

    def __str__(self):
        return ' '.join(self._pp.split())

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, ' '.join(self._pp.split()))

    def _assert_is_active(self):
        """As the engine does not provide means to find activations,
        the existence of the pointer in the activations list is tested instead.

        """
        activations = []
        activation = lib.GetNextActivation(self._env, ffi.NULL)

        while activation != ffi.NULL:
            activations.append(activation)
            activation = lib.GetNextActivation(self._env, activation)

        if self._act not in activations:
            raise CLIPSError(
                self._env, "Activation %s not in the agenda" % self.name)

    @property
    def name(self) -> str:
        """Activation Rule name."""
        return self._rule_name.decode()

    @property
    def salience(self) -> int:
        """Activation salience value."""
        self._assert_is_active()
        return lib.ActivationGetSalience(self._act)

    @salience.setter
    def salience(self, salience: int):
        """Activation salience value."""
        self._assert_is_active()
        lib.ActivationSetSalience(self._act, salience)

    def delete(self):
        """Remove the activation from the agenda."""
        self._assert_is_active()
        lib.DeleteActivation(self._act)


class Agenda:
    """In CLIPS, when all the conditions to activate a rule are met,
    The Rule action is placed within the Agenda.

    The CLIPS Agenda is responsible of sorting the Rule Activations
    according to their salience and the conflict resolution strategy.

    .. note::

       All the Agenda methods are accessible through the Environment class.

    """

    def __init__(self, env: ffi.CData):
        self._env = env

    @property
    def agenda_changed(self) -> bool:
        """True if any rule activation changes have occurred."""
        value = lib.GetAgendaChanged(self._env)
        lib.SetAgendaChanged(self._env, False)

        return value

    @property
    def focus(self) -> Module:
        """The module associated with the current focus.

        Equivalent to the CLIPS (get-focus) function.

        """
        current_focus = lib.GetFocus(self._env)
        if current_focus != ffi.NULL:
            name = ffi.string(lib.DefmoduleName(current_focus)).decode()

            return Module(self._env, name)

        return None

    @focus.setter
    def focus(self, module: Module):
        """The module associated with the current focus.

        Equivalent to the CLIPS (get-focus) function.

        """
        return lib.Focus(module._ptr())

    @property
    def strategy(self) -> Strategy:
        """The current conflict resolution strategy.

        Equivalent to the CLIPS (get-strategy) function.

        """
        return Strategy(lib.GetStrategy(self._env))

    @strategy.setter
    def strategy(self, value: Strategy):
        """The current conflict resolution strategy.

        Equivalent to the CLIPS (get-strategy) function.

        """
        lib.SetStrategy(self._env, Strategy(value))

    @property
    def salience_evaluation(self) -> SalienceEvaluation:
        """The salience evaluation behavior.

        Equivalent to the CLIPS (get-salience-evaluation) command.

        """
        return SalienceEvaluation(lib.GetSalienceEvaluation(self._env))

    @salience_evaluation.setter
    def salience_evaluation(self, value: SalienceEvaluation):
        """The salience evaluation behavior.

        Equivalent to the CLIPS (get-salience-evaluation) command.

        """
        lib.SetSalienceEvaluation(self._env, SalienceEvaluation(value))

    def rules(self) -> iter:
        """Iterate over the defined Rules."""
        rule = lib.GetNextDefrule(self._env, ffi.NULL)

        while rule != ffi.NULL:
            name = ffi.string(lib.DefruleName(rule)).decode()
            yield Rule(self._env, name)

            rule = lib.GetNextDefrule(self._env, rule)

    def find_rule(self, name: str) -> Rule:
        """Find a Rule by name."""
        defrule = lib.FindDefrule(self._env, name.encode())
        if defrule == ffi.NULL:
            raise LookupError("Rule '%s' not found" % name)

        return Rule(self._env, name)

    def reorder(self, module: Module = None):
        """Reorder the Activations in the Agenda.

        If no Module is specified, the agendas of all modules are reordered.

        To be called after changing the conflict resolution strategy.

        """
        if module is not None:
            lib.ReorderAgenda(module._ptr())
        else:
            lib.ReorderAllAgendas(self._env)

    def refresh(self, module: Module = None):
        """Recompute the salience values of the Activations on the Agenda
        and then reorder the agenda.

        Equivalent to the CLIPS (refresh-agenda) function.

        If no Module is specified, the agendas of all modules are refreshed.

        """
        if module is not None:
            lib.RefreshAgenda(module._ptr())
        else:
            lib.RefreshAllAgendas(self._env)

    def activations(self) -> iter:
        """Iterate over the Activations in the Agenda."""
        activation = lib.GetNextActivation(self._env, ffi.NULL)

        while activation != ffi.NULL:
            yield Activation(self._env, activation)

            activation = lib.GetNextActivation(self._env, activation)

    def delete_activations(self):
        """Delete all activations in the agenda."""
        if not lib.DeleteActivation(self._env, ffi.NULL):
            raise CLIPSError(self._env)

    def clear_focus(self):
        """Remove all modules from the focus stack.

        Equivalent to the CLIPS (clear-focus-stack) function.

        """
        lib.ClearFocusStack(self._env)

    def run(self, limit: int = None) -> int:
        """Runs the activations in the agenda.

        If limit is not None, the first activations up to limit will be run.

        Returns the number of activation which were run.

        """
        return lib.Run(self._env, limit if limit is not None else -1)


def activation_pp_string(env: ffi.CData, ist: ffi.CData) -> str:
    builder = environment_builder(env, 'string')
    lib.SBReset(builder)
    lib.ActivationPPForm(ist, builder)

    return ffi.string(builder.contents).decode()
