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

  * Modules namespace class
  * Module class
  * Global class

"""

import clips

from clips.common import CLIPSError

from clips._clips import lib, ffi


class Module:
    """Modules are namespaces restricting the CLIPS constructs scope."""

    __slots__ = '_env', '_mdl'

    def __init__(self, env: ffi.CData, mdl: ffi.CData):
        self._env = env
        self._mdl = mdl

    def __hash__(self):
        return hash(self._mdl)

    def __eq__(self, mdl):
        return self._mdl == mdl._mdl

    def __str__(self):
        string = lib.DefmodulePPForm(self._mdl)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefmodulePPForm(self._mdl)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    @property
    def name(self):
        """Module name."""
        return ffi.string(lib.DefmoduleName(self._mdl)).decode()


class Global(object):
    """A CLIPS global variable.

    In CLIPS, Globals are defined via the (defglobal) statement.

    """

    __slots__ = '_env', '_glb'

    def __init__(self, env: ffi.CData, glb: ffi.CData):
        self._env = env
        self._glb = glb

    def __hash__(self):
        return hash(self._glb)

    def __eq__(self, glb):
        return self._glb == glb._glb

    def __str__(self):
        string = lib.DefglobalPPForm(self._glb)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefglobalPPForm(self._glb)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    @property
    def value(self) -> type:
        """Global value."""
        value = clips.values.clips_value(self._env)

        lib.DefglobalGetValue(self._glb, value)

        return clips.values.python_value(self._env, value)

    @value.setter
    def value(self, value: type):
        """Global value."""
        value = clips.values.clips_value(self._env, value=value)

        lib.DefglobalSetValue(self._glb, value)

    @property
    def name(self) -> str:
        """Global name."""
        return ffi.string(lib.DefglobalName(self._glb)).decode()

    @property
    def module(self) -> Module:
        """The module in which the Global is defined.

        Equivalent to the CLIPS (defglobal-module) function.

        """
        modname = ffi.string(lib.DefglobalModule(self._glb))

        return Module(self._env, lib.FindDefmodule(self._env, modname))

    @property
    def deletable(self) -> bool:
        """True if the Global can be deleted."""
        return lib.DefglobalIsDeletable(self._glb)

    @property
    def watch(self) -> bool:
        """Whether or not the Global is being watched."""
        return lib.DefglobalGetWatch(self._glb)

    @watch.setter
    def watch(self, flag: bool):
        """Whether or not the Global is being watched."""
        lib.DefglobalSetWatch(self._glb, flag)

    def undefine(self):
        """Undefine the Global.

        Equivalent to the CLIPS (undefglobal) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefglobal(self._glb, self._env):
            raise CLIPSError(self._env)

        self._env = self._glb = None


class Modules:
    """Globals and Modules namespace class.

    .. note::

       All the Modules methods are accessible through the Environment class.

    """

    __slots__ = '_env'

    def __init__(self, env: ffi.CData):
        self._env = env

    @property
    def current_module(self) -> Module:
        """The current module.

        Equivalent to the CLIPS (get-current-module) function.

        """
        return Module(self._env, lib.GetCurrentModule(self._env))

    @current_module.setter
    def current_module(self, module: Module):
        """The current module.

        Equivalent to the CLIPS (get-current-module) function.

        """
        lib.SetCurrentModule(self._env, module._mdl)

    @property
    def reset_globals(self) -> bool:
        """True if Globals reset behaviour is enabled."""
        return lib.GetResetGlobals(self._env)

    @reset_globals.setter
    def reset_globals(self, value: bool):
        """True if Globals reset behaviour is enabled."""
        return lib.SetResetGlobals(self._env, value)

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
            yield Global(self._env, defglobal)

            defglobal = lib.GetNextDefglobal(self._env, defglobal)

    def find_global(self, name: str) -> Module:
        """Find the Global by its name."""
        defglobal = lib.FindDefglobal(self._env, name.encode())
        if defglobal == ffi.NULL:
            raise LookupError("Global '%s' not found" % name)

        return Global(self._env, defglobal)

    def modules(self) -> iter:
        """Iterates over the defined Modules."""
        defmodule = lib.GetNextDefmodule(self._env, ffi.NULL)

        while defmodule != ffi.NULL:
            yield Module(self._env, defmodule)

            defmodule = lib.GetNextDefmodule(self._env, defmodule)

    def find_module(self, name: str) -> Module:
        """Find the Module by its name."""
        defmodule = lib.FindDefmodule(self._env, name.encode())
        if defmodule == ffi.NULL:
            raise LookupError("Module '%s' not found" % name)

        return Module(self._env, defmodule)
