# Copyright (c) 2016-2019, Matteo Cafasso
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

  * Function class
  * Generic class
  * Method class
  * Functions namespace class

"""

import traceback

import clips

from clips.modules import Module
from clips.common import CLIPSError, environment_builder, environment_data

from clips._clips import lib, ffi


class Function:
    """A CLIPS user defined Function.

    In CLIPS, Functions are defined via the (deffunction) statement.

    """

    __slots__ = '_env', '_fnc'

    def __init__(self, env: ffi.CData, fnc: ffi.CData):
        self._env = env
        self._fnc = fnc

    def __hash__(self):
        return hash(self._fnc)

    def __eq__(self, fnc):
        return self._fnc == fnc._fnc

    def __str__(self):
        string = lib.DeffunctionPPForm(self._fnc)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DeffunctionPPForm(self._fnc)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def __call__(self, *arguments):
        """Call the CLIPS function with the given arguments."""
        value = clips.values.clips_value(self._env)
        builder = environment_builder(self._env, 'function')

        lib.FCBReset(builder)
        for argument in arguments:
            lib.FCBAppend(
                builder, clips.values.clips_value(self._env, value=argument))

        ret = lib.FCBCall(builder, lib.DeffunctionName(self._fnc), value)
        if ret != lib.FCBE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        return clips.values.python_value(self._env, value)

    @property
    def name(self) -> str:
        """Function name."""
        return ffi.string(lib.DeffunctionName(self._fnc)).decode()

    @property
    def module(self) -> Module:
        """The module in which the Function is defined.

        Equivalent to the CLIPS (deffunction-module) functions.

        """
        modname = ffi.string(lib.DeffunctionModule(self._fnc))

        return Module(self._env, lib.FindDefmodule(self._env, modname))

    @property
    def deletable(self) -> bool:
        """True if the Function can be deleted."""
        return lib.DeffunctionIsDeletable(self._fnc)

    @property
    def watch(self) -> bool:
        """Whether or not the Function is being watched."""
        return lib.DeffunctionGetWatch(self._fnc)

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Function is being watched."""
        lib.DeffunctionSetWatch(self._fnc, flag)

    def undefine(self):
        """Undefine the Function.

        Equivalent to the CLIPS (undeffunction) command.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undeffunction(self._fnc, self._env):
            raise CLIPSError(self._env)

        self._env = self._fnc = None


class Generic:
    """A CLIPS Generic Function.

    In CLIPS, Generic Functions are defined via the (defgeneric) statement.

    """

    __slots__ = '_env', '_gnc'

    def __init__(self, env: ffi.CData, gnc: ffi.CData):
        self._env = env
        self._gnc = gnc

    def __hash__(self):
        return hash(self._gnc)

    def __eq__(self, gnc):
        return self._gnc == gnc._gnc

    def __str__(self):
        string = lib.DefgenericPPForm(self._gnc)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefgenericPPForm(self._gnc)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def __call__(self, *arguments):
        """Call the CLIPS Generic function with the given arguments."""
        value = clips.values.clips_value(self._env)
        builder = environment_builder(self._env, 'function')

        lib.FCBReset(builder)
        for argument in arguments:
            lib.FCBAppend(
                builder, clips.values.clips_value(self._env, value=argument))

        ret = lib.FCBCall(builder, lib.DefgenericName(self._gnc), value)
        if ret != lib.FCBE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        return clips.values.python_value(self._env, value)

    @property
    def name(self) -> str:
        """Generic name."""
        return ffi.string(lib.DefgenericName(self._gnc)).decode()

    @property
    def module(self) -> Module:
        """The module in which the Generic is defined.

        Equivalent to the CLIPS (defgeneric-module) generics.

        """
        modname = ffi.string(lib.DefgenericModule(self._gnc))

        return Module(self._env, lib.FindDefmodule(self._env, modname))

    @property
    def deletable(self) -> bool:
        """True if the Generic can be deleted."""
        return lib.DefgenericIsDeletable(self._gnc)

    @property
    def watch(self) -> bool:
        """Whether or not the Generic is being watched."""
        return lib.DefgenericGetWatch(self._gnc)

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Generic is being watched."""
        lib.DefgenericSetWatch(self._gnc, flag)

    def methods(self) -> iter:
        """Iterates over the defined Methods."""
        index = lib.GetNextDefmethod(self._gnc, 0)

        while index != 0:
            yield Method(self._env, self._gnc, index)

            index = lib.GetNextDefmethod(self._gnc, index)

    def undefine(self):
        """Undefine the Generic.

        Equivalent to the CLIPS (undefgeneric) command.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefgeneric(self._gnc, self._env):
            raise CLIPSError(self._env)

        self._env = self._gnc = None


class Method(object):
    """Methods implement the generic logic
    according to the input parameter types.

    """

    __slots__ = '_env', '_gnc', '_idx'

    def __init__(self, env: ffi.CData, gnc: ffi.CData, idx: int):
        self._env = env
        self._gnc = gnc
        self._idx = idx

    def __hash__(self):
        return hash(self._gnc) + self._idx

    def __eq__(self, gnc):
        return self._gnc == gnc._gnc and self._idx == gnc._idx

    def __str__(self):
        string = lib.DefmethodPPForm(self._gnc, self._idx)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefmethodPPForm(self._gnc, self._idx)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    @property
    def watch(self) -> bool:
        """Whether or not the Method is being watched."""
        return lib.DefmethodGetWatch(self._gnc, self._idx)

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Method is being watched."""
        lib.DefmethodSetWatch(self._gnc, self._idx, flag)

    @property
    def deletable(self):
        """True if the Template can be undefined."""
        return lib.DefmethodIsDeletable(self._gnc, self._idx)

    @property
    def restrictions(self) -> tuple:
        value = clips.values.clips_value(self._env)

        lib.GetMethodRestrictions(self._gnc, self._idx, value)

        return clips.values.python_value(self._env, value)

    @property
    def description(self) -> str:
        builder = environment_builder(self._env, 'string')
        lib.SBReset(builder)
        lib.DefmethodDescription(self._gnc, self._idx, builder)

        return ffi.string(builder.contents).decode()

    def undefine(self):
        """Undefine the Method.

        Equivalent to the CLIPS (undefmethod) command.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefmethod(self._gnc, self._idx, self._env):
            raise CLIPSError(self._env)

        self._env = self._gnc = self._idx = None


class Functions:
    """Functions, Generics and Methods namespace class.

    .. note::

       All the Functions methods are accessible through the Environment class.

    """

    __slots__ = '_env'

    def __init__(self, env: ffi.CData):
        self._env = env

    def call(self, function: str, *arguments) -> type:
        """Call the CLIPS function with the given arguments."""
        value = clips.values.clips_value(self._env)
        builder = environment_builder(self._env, 'function')

        lib.FCBReset(builder)
        for argument in arguments:
            lib.FCBAppend(
                builder, clips.values.clips_value(self._env, value=argument))

        ret = lib.FCBCall(builder, function.encode(), value)
        if ret != lib.FCBE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        return clips.values.python_value(self._env, value)

    def functions(self):
        """Iterates over the defined Globals."""
        deffunction = lib.GetNextDeffunction(self._env, ffi.NULL)

        while deffunction != ffi.NULL:
            yield Function(self._env, deffunction)

            deffunction = lib.GetNextDeffunction(self._env, deffunction)

    def find_function(self, name: str) -> Function:
        """Find the Function by its name."""
        deffunction = lib.FindDeffunction(self._env, name.encode())
        if deffunction == ffi.NULL:
            raise LookupError("Function '%s' not found" % name)

        return Function(self._env, deffunction)

    def generics(self) -> iter:
        """Iterates over the defined Generics."""
        defgeneric = lib.GetNextDefgeneric(self._env, ffi.NULL)

        while defgeneric != ffi.NULL:
            yield Generic(self._env, defgeneric)

            defgeneric = lib.GetNextDefgeneric(self._env, defgeneric)

    def find_generic(self, name: str) -> Generic:
        """Find the Generic by its name."""
        defgeneric = lib.FindDefgeneric(self._env, name.encode())
        if defgeneric == ffi.NULL:
            raise LookupError("Generic '%s' not found" % name)

        return Generic(self._env, defgeneric)

    def define_function(self, function: callable, name: str = None):
        """Define the Python function within the CLIPS environment.

        If a name is given, it will be the function name within CLIPS.
        Otherwise, the name of the Python function will be used.

        The Python function will be accessible within CLIPS via its name
        as if it was defined via the `deffunction` construct.

        """
        name = name if name is not None else function.__name__

        environment_data(self._env, 'user_functions')[name] = function

        ret = lib.Build(self._env, DEFFUNCTION.format(name).encode())
        if ret != lib.BE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)


@ffi.def_extern()
def python_function(env: ffi.CData, context: ffi.CData, output: ffi.CData):
    arguments = []
    value = clips.values.clips_udf_value(env)

    if lib.UDFFirstArgument(context, lib.SYMBOL_BIT, value):
        funcname = clips.values.python_value(env, value)
    else:
        lib.UDFThrowError(context)
        return

    while lib.UDFHasNextArgument(context):
        if lib.UDFNextArgument(context, clips.values.ANY_TYPE_BITS, value):
            arguments.append(clips.values.python_value(env, value))
        else:
            lib.UDFThrowError(context)
            return

    try:
        ret = environment_data(env, 'user_functions')[funcname](*arguments)
    except Exception as error:
        clips.values.clips_udf_value(env, traceback.format_exc(), value)
        lib.SetErrorValue(env, value.header)
        lib.UDFThrowError(context)
    else:
        clips.values.clips_udf_value(env, ret, output)


DEFFUNCTION = """
(deffunction {0} ($?args)
  (python-function {0} (expand$ ?args)))
"""
