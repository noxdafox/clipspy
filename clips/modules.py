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

  * Modules namespace class
  * Module class
  * Global class

"""

import clips

from clips.common import CLIPSError

from clips._clips import lib, ffi


class Module:
    """Modules are namespaces restricting the CLIPS constructs scope."""

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, mdl):
        return self._ptr() == mdl._ptr()

    def __str__(self):
        string = lib.DefmodulePPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefmodulePPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        module = lib.FindDefmodule(self._env, self._name)
        if module == ffi.NULL:
            raise CLIPSError(self._env, 'Module <%s> not defined' % self.name)

        return module

    @property
    def name(self) -> str:
        """Module name."""
        return self._name.decode()


class Global:
    """A CLIPS global variable.

    In CLIPS, Globals are defined via the (defglobal) statement.

    """

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, glb):
        return self._ptr() == glb._ptr()

    def __str__(self):
        string = lib.DefglobalPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefglobalPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        glb = lib.FindDefglobal(self._env, self._name)
        if glb == ffi.NULL:
            raise CLIPSError(
                self._env, 'Global <%s> not defined' % self.name)

        return glb

    @property
    def value(self) -> type:
        """Global value."""
        value = clips.values.clips_value(self._env)

        lib.DefglobalGetValue(self._ptr(), value)

        return clips.values.python_value(self._env, value)

    @value.setter
    def value(self, value: type):
        """Global value."""
        value = clips.values.clips_value(self._env, value=value)

        lib.DefglobalSetValue(self._ptr(), value)

    @property
    def name(self) -> str:
        """Global name."""
        return self._name.decode()

    @property
    def module(self) -> Module:
        """The module in which the Global is defined.

        Equivalent to the CLIPS (defglobal-module) function.

        """
        name = ffi.string(lib.DefglobalModule(self._ptr())).decode()

        return Module(self._env, name)

    @property
    def deletable(self) -> bool:
        """True if the Global can be deleted."""
        return lib.DefglobalIsDeletable(self._ptr())

    @property
    def watch(self) -> bool:
        """Whether or not the Global is being watched."""
        return lib.DefglobalGetWatch(self._ptr())

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Global is being watched."""
        lib.DefglobalSetWatch(self._ptr(), flag)

    def undefine(self):
        """Undefine the Global.

        Equivalent to the CLIPS (undefglobal) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefglobal(self._ptr(), self._env):
            raise CLIPSError(self._env)


class Modules:
    """Globals and Modules namespace class.

    .. note::

       All the Modules methods are accessible through the Environment class.

    """

    __slots__ = ['_env']

    def __init__(self, env: ffi.CData):
        self._env = env

    @property
    def current_module(self) -> Module:
        """The current module.

        Equivalent to the CLIPS (get-current-module) function.

        """
        module = lib.GetCurrentModule(self._env)
        name = ffi.string(lib.DefmoduleName(module)).decode()

        return Module(self._env, name)

    @current_module.setter
    def current_module(self, module: Module):
        """The current module.

        Equivalent to the CLIPS (get-current-module) function.

        """
        lib.SetCurrentModule(self._env, module._ptr())

    @property
    def reset_globals(self) -> bool:
        """True if Globals reset behaviour is enabled."""
        return lib.GetResetGlobals(self._env)

    @reset_globals.setter
    def reset_globals(self, value: bool):
        """True if Globals reset behaviour is enabled."""
        lib.SetResetGlobals(self._env, value)

    @property
    def globals_changed(self) -> bool:
        """True if any Global has changed since last check."""
        value = lib.GetGlobalsChanged(self._env)
        lib.SetGlobalsChanged(self._env, False)

        return value

    def globals(self) -> iter:
        """Iterates over the defined Globals."""
        defglobal = lib.GetNextDefglobal(self._env, ffi.NULL)

        while defglobal != ffi.NULL:
            name = ffi.string(lib.DefglobalName(defglobal)).decode()
            yield Global(self._env, name)

            defglobal = lib.GetNextDefglobal(self._env, defglobal)

    def find_global(self, name: str) -> Module:
        """Find the Global by its name."""
        defglobal = lib.FindDefglobal(self._env, name.encode())
        if defglobal == ffi.NULL:
            raise LookupError("Global '%s' not found" % name)

        return Global(self._env, name)

    def modules(self) -> iter:
        """Iterates over the defined Modules."""
        defmodule = lib.GetNextDefmodule(self._env, ffi.NULL)

        while defmodule != ffi.NULL:
            name = ffi.string(lib.DefmoduleName(defmodule)).decode()
            yield Module(self._env, name)

            defmodule = lib.GetNextDefmodule(self._env, defmodule)

    def find_module(self, name: str) -> Module:
        """Find the Module by its name."""
        defmodule = lib.FindDefmodule(self._env, name.encode())
        if defmodule == ffi.NULL:
            raise LookupError("Module '%s' not found" % name)

        return Module(self._env, name)
