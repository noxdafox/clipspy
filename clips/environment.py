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

import clips

from clips.facts import Facts
from clips.agenda import Agenda
from clips.classes import Classes
from clips.modules import Modules
from clips.functions import Functions
from clips.routers import Routers, ErrorRouter
from clips.common import CLIPSError
from clips.common import initialize_environment_data, delete_environment_data

from clips._clips import lib


class Environment:
    """The environment class encapsulates an independent CLIPS engine
    with its own data structures.

    """

    __slots__ = ('_env', '_facts', '_agenda', '_classes',
                 '_modules', '_functions', '_routers', '_namespaces')

    def __init__(self):
        self._env = lib.CreateEnvironment()

        initialize_environment_data(self._env)

        self._facts = Facts(self._env)
        self._agenda = Agenda(self._env)
        self._classes = Classes(self._env)
        self._modules = Modules(self._env)
        self._functions = Functions(self._env)
        self._routers = Routers(self._env)

        self._routers.add_router(ErrorRouter())

        # mapping between the namespace and the methods it exposes
        self._namespaces = {m: n for n in (self._facts,
                                           self._agenda,
                                           self._classes,
                                           self._modules,
                                           self._functions,
                                           self._routers)
                            for m in dir(n) if not m.startswith('_')}

    def __del__(self):
        try:
            delete_environment_data(self._env)
            lib.DestroyEnvironment(self._env)
        except (AttributeError, KeyError, TypeError):
            pass  # mostly happening during interpreter shutdown

    def __getattr__(self, attr):
        try:
            return getattr(self._namespaces[attr], attr)
        except (KeyError, AttributeError):
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

    def __setattr__(self, attr, value):
        if attr in self.__slots__:
            super(Environment, self).__setattr__(attr, value)
            return

        try:
            setattr(self._namespaces[attr], attr, value)
        except (KeyError, AttributeError):
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

    def __dir__(self):
        return dir(self.__class__) + list(self._namespaces.keys())

    def load(self, path: str, binary: bool = False):
        """Load a set of constructs into the CLIPS data base.

        If constructs were saved in binary format,
        the binary parameter should be set to True.

        Equivalent to the CLIPS (load) function.

        """
        if binary:
            if not lib.Bload(self._env, path.encode()):
                raise CLIPSError(self._env)
        else:
            ret = lib.Load(self._env, path.encode())
            if ret != lib.LE_NO_ERROR:
                raise CLIPSError(self._env, code=ret)

    def save(self, path: str, binary=False):
        """Save a set of constructs into the CLIPS data base.

        If binary is True, the constructs will be saved in binary format.

        Equivalent to the CLIPS (load) function.

        """
        if binary:
            ret = lib.Bsave(self._env, path.encode())
        else:
            ret = lib.Save(self._env, path.encode())
        if ret == 0:
            raise CLIPSError(self._env)

    def batch_star(self, path: str):
        """Evaluate the commands contained in the specific path.

        Equivalent to the CLIPS (batch*) function.

        """
        if lib.BatchStar(self._env, path.encode()) != 1:
            raise CLIPSError(self._env)

    def build(self, construct: str):
        """Build a single construct in CLIPS.

        Equivalent to the CLIPS (build) function.

        """
        ret = lib.Build(self._env, construct.encode())
        if ret != lib.BE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

    def eval(self, expression: str) -> type:
        """Evaluate an expression returning its value.

        Equivalent to the CLIPS (eval) function.

        """
        value = clips.values.clips_value(self._env)

        ret = lib.Eval(self._env, expression.encode(), value)
        if ret != lib.EE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        return clips.values.python_value(self._env, value)

    def reset(self):
        """Reset the CLIPS environment.

        Equivalent to the CLIPS (reset) function.

        """
        if lib.Reset(self._env):
            raise CLIPSError(self._env)

    def clear(self):
        """Clear the CLIPS environment.

        Equivalent to the CLIPS (clear) function.

        """
        if not lib.Clear(self._env):
            raise CLIPSError(self._env)
