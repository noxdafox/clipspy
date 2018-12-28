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

  * Functions namespace class
  * Function class
  * Generic class
  * Method class

"""

import clips

from clips.modules import Module
from clips.error import CLIPSError

from clips._clips import lib, ffi


class Functions:
    """Functions, Generics and Methods namespace class.

    .. note::

       All the Functions methods are accessible through the Environment class.

    """

    __slots__ = '_env'

    def __init__(self, env):
        self._env = env

    def functions(self):
        """Iterates over the defined Globals."""
        deffunction = lib.EnvGetNextDeffunction(self._env, ffi.NULL)

        while deffunction != ffi.NULL:
            yield Function(self._env, deffunction)

            deffunction = lib.EnvGetNextDeffunction(self._env, deffunction)

    def find_function(self, name):
        """Find the Function by its name."""
        deffunction = lib.EnvFindDeffunction(self._env, name.encode())
        if deffunction == ffi.NULL:
            raise LookupError("Function '%s' not found" % name)

        return Function(self._env, deffunction)

    def generics(self):
        """Iterates over the defined Generics."""
        defgeneric = lib.EnvGetNextDefgeneric(self._env, ffi.NULL)

        while defgeneric != ffi.NULL:
            yield Generic(self._env, defgeneric)

            defgeneric = lib.EnvGetNextDefgeneric(self._env, defgeneric)

    def find_generic(self, name):
        """Find the Generic by its name."""
        defgeneric = lib.EnvFindDefgeneric(self._env, name.encode())
        if defgeneric == ffi.NULL:
            raise LookupError("Generic '%s' not found" % name)

        return Generic(self._env, defgeneric)


class Function(object):
    """A CLIPS user defined function.

    In CLIPS, Functions are defined via the (deffunction) statement.

    """

    __slots__ = '_env', '_fnc'

    def __init__(self, env, fnc):
        self._env = env
        self._fnc = fnc

    def __hash__(self):
        return hash(self._fnc)

    def __eq__(self, fnc):
        return self._fnc == fnc._fnc

    def __str__(self):
        string = ffi.string(lib.EnvGetDeffunctionPPForm(self._env, self._fnc))

        return string.decode().rstrip('\n')

    def __repr__(self):
        string = ffi.string(lib.EnvGetDeffunctionPPForm(self._env, self._fnc))

        return "%s: %s" % (self.__class__.__name__,
                           string.decode().rstrip('\n'))

    def __call__(self, arguments=''):
        """Call the CLIPS function.

        Function arguments must be provided as a string.

        """
        data = clips.data.DataObject(self._env)
        name = ffi.string(lib.EnvGetDeffunctionName(self._env, self._fnc))
        args = arguments.encode() if arguments != '' else ffi.NULL

        if lib.EnvFunctionCall(self._env, name, args, data.byref) == 1:
            raise CLIPSError(self._env)

        return data.value

    @property
    def name(self):
        """Function name."""
        return ffi.string(
            lib.EnvGetDeffunctionName(self._env, self._fnc)).decode()

    @property
    def module(self):
        """The module in which the Function is defined.

        Python equivalent of the CLIPS deffunction-module command.

        """
        modname = ffi.string(lib.EnvDeffunctionModule(self._env, self._fnc))
        defmodule = lib.EnvFindDefmodule(self._env, modname)

        return Module(self._env, defmodule)

    @property
    def deletable(self):
        """True if the Function can be deleted."""
        return bool(lib.EnvIsDeffunctionDeletable(self._env, self._fnc))

    @property
    def watch(self):
        """Whether or not the Function is being watched."""
        return bool(lib.EnvGetDeffunctionWatch(self._env, self._fnc))

    @watch.setter
    def watch(self, flag):
        """Whether or not the Function is being watched."""
        lib.EnvSetDeffunctionWatch(self._env, int(flag), self._fnc)

    def undefine(self):
        """Undefine the Function.

        Python equivalent of the CLIPS undeffunction command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndeffunction(self._env, self._fnc) != 1:
            raise CLIPSError(self._env)

        self._env = None


class Generic(object):
    """A CLIPS generic function.

    In CLIPS, Functions are defined via the (defgeneric) statement.

    """

    __slots__ = '_env', '_gnc'

    def __init__(self, env, gnc):
        self._env = env
        self._gnc = gnc

    def __hash__(self):
        return hash(self._gnc)

    def __eq__(self, gnc):
        return self._gnc == gnc._gnc

    def __str__(self):
        string = ffi.string(lib.EnvGetDefgenericPPForm(self._env, self._gnc))

        return string.decode().rstrip('\n')

    def __repr__(self):
        string = ffi.string(lib.EnvGetDefgenericPPForm(self._env, self._gnc))

        return "%s: %s" % (self.__class__.__name__,
                           string.decode().rstrip('\n'))

    def __call__(self, arguments=''):
        """Call the CLIPS generic function.

        Function arguments must be provided as a string.

        """
        data = clips.data.DataObject(self._env)
        name = ffi.string(lib.EnvGetDefgenericName(self._env, self._gnc))
        args = arguments.encode() if arguments != '' else ffi.NULL

        if lib.EnvFunctionCall(self._env, name, args, data.byref) == 1:
            raise CLIPSError(self._env)

        return data.value

    @property
    def name(self):
        return ffi.string(
            lib.EnvGetDefgenericName(self._env, self._gnc)).decode()

    @property
    def module(self):
        modname = ffi.string(lib.EnvDefgenericModule(self._env, self._gnc))
        defmodule = lib.EnvFindDefmodule(self._env, modname)

        return Module(self._env, defmodule)

    @property
    def deletable(self):
        return bool(lib.EnvIsDefgenericDeletable(self._env, self._gnc))

    @property
    def watch(self):
        return bool(lib.EnvGetDefgenericWatch(self._env, self._gnc))

    @watch.setter
    def watch(self, flag):
        lib.EnvSetDefgenericWatch(self._env, int(flag), self._gnc)

    def methods(self):
        index = lib.EnvGetNextDefmethod(self._env, self._gnc, 0)

        while index != 0:
            yield Method(self._env, self._gnc, index)

            index = lib.EnvGetNextDefmethod(self._env, self._gnc, index)

    def undefine(self):
        """Undefine the Generic.

        Python equivalent of the CLIPS undefgeneric command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndefgeneric(self._env, self._gnc) != 1:
            raise CLIPSError(self._env)

        self._env = None


class Method(object):
    """Methods implement the generic logic
    according to the input parameter types.

    """

    __slots__ = '_env', '_gnc', '_idx'

    def __init__(self, env, gnc, idx):
        self._env = env
        self._gnc = gnc
        self._idx = idx

    def __hash__(self):
        return hash(self._gnc) + self._idx

    def __eq__(self, gnc):
        return self._gnc == gnc._gnc and self._idx == gnc._idx

    def __str__(self):
        string = ffi.string(lib.EnvGetDefmethodPPForm(
            self._env, self._gnc, self._idx))

        return string.decode().rstrip('\n')

    def __repr__(self):
        string = ffi.string(lib.EnvGetDefmethodPPForm(
            self._env, self._gnc, self._idx))

        return "%s: %s" % (self.__class__.__name__,
                           string.decode().rstrip('\n'))

    @property
    def watch(self):
        return bool(lib.EnvGetDefmethodWatch(self._env, self._gnc, self._idx))

    @watch.setter
    def watch(self, flag):
        lib.EnvSetDefmethodWatch(self._env, int(flag), self._gnc, self._idx)

    @property
    def deletable(self):
        return bool(lib.EnvIsDefmethodDeletable(
            self._env, self._gnc, self._idx))

    @property
    def restrictions(self):
        data = clips.data.DataObject(self._env)

        lib.EnvGetMethodRestrictions(
            self._env, self._gnc, self._idx, data.byref)

        return data.value

    @property
    def description(self):
        buf = ffi.new('char[1024]')
        lib.EnvGetDefmethodDescription(
            self._env, buf, 1024, self._gnc, self._idx)

        return ffi.string(buf).decode()

    def undefine(self):
        """Undefine the Method.

        Python equivalent of the CLIPS undefmethod command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndefmethod(self._env, self._gnc, self._idx) != 1:
            raise CLIPSError(self._env)

        self._env = None
