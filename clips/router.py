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

import logging

import clips

from clips._clips import lib, ffi


class Router:

    __slots__ = '_env', '_name', '_userdata', '_priority'

    def __init__(self, name: str, priority: int):
        self._env = None
        self._name = name
        self._userdata = None
        self._priority = priority

    @property
    def name(self) -> str:
        """The Router name."""
        return self._name

    def query(self, _name: str) -> bool:
        """This method should return True if the provided logical name
        is handled by the Router.

        """
        return False

    def write(self, _name: str, _message: str) -> None:
        """If the query method returns True for the given logical name,
        this method will be called with the forwarded message.

        """
        return None

    def read(self, _name: str) -> int:
        return 0

    def unread(self, _name: str, _char: int) -> int:
        return 0

    def exit(self, _exitcode: int) -> None:
        return None

    def activate(self):
        """Activate the Router."""
        if not lib.ActivateRouter(self._env, self._name.encode()):
            raise RuntimeError("Unable to activate router %s" % self._name)

    def deactivate(self):
        """Deactivate the Router."""
        if not lib.DeactivateRouter(self._env, self._name.encode()):
            raise RuntimeError("Unable to deactivate router %s" % self._name)

    def delete(self):
        """Delete the Router."""
        clips.common.environment_data(self._env, 'routers').pop(self.name, None)

        if not lib.DeleteRouter(self._env, self._name.encode()):
            raise RuntimeError("Unable to delete router %s" % self._name)

    def add_to_environment(self, environment):
        """Add the router to the given environment."""
        self._env = environment._env
        self._userdata = ffi.new_handle(self)

        clips.common.environment_data(self._env, 'routers')[self.name] = self

        lib.AddRouter(
            self._env,
            self._name.encode(),
            self._priority,
            lib.query_function,
            lib.write_function,
            lib.read_function,
            lib.unread_function,
            lib.exit_function,
            self._userdata)


class ErrorRouter(Router):

    __slots__ = '_env', '_name', '_userdata', '_priority', '_last_message'

    def __init__(self):
        super().__init__('python-error-router', 40)
        self._last_message = ''

    @property
    def last_message(self) -> str:
        ret = self._last_message

        self._last_message = ''

        return ret

    def query(self, name: str):
        return True if name == 'stderr' else False

    def write(self, name: str, message: str):
        self._last_message += message


class LoggingRouter(Router):
    """Python logging Router.

    A helper Router to get Python standard logging facilities
    integrated with CLIPS.

    """
    LOGGERS = {'stdout': logging.info,
               'stderr': logging.error,
               'stfwrn': logging.warning}

    def __init__(self):
        super().__init__('python-logging-router', 30)
        self._message = ''

    def query(self, name: str) -> bool:
        return name in self.LOGGERS

    def write(self, name: str, message: str):
        if message == '\n':
            self.log_message(name)
        else:
            self._message += message
            if self._message.rstrip(' ').endswith('\n'):
                self.log_message(name)

    def log_message(self, name: str):
        if self._message:
            self.LOGGERS[name](self._message.lstrip('\n').rstrip('\n'))
            self._message = ''


@ffi.def_extern()
def query_function(env: ffi.CData, name: ffi.CData, context: ffi.CData):
    router = ffi.from_handle(context)

    return bool(router.query(ffi.string(name).decode()))


@ffi.def_extern()
def write_function(env: ffi.CData, name: ffi.CData,
                   message: ffi.CData, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        router.write(ffi.string(name).decode(), ffi.string(message).decode())
    except BaseException:
        pass


@ffi.def_extern()
def read_function(env: ffi.CData, name: ffi.CData, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        return int(router.read(ffi.string(name).decode()))
    except BaseException:
        return 0


@ffi.def_extern()
def unread_function(env: ffi.CData, char: ffi.CData,
                    name: ffi.CData, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        return int(router.unread(ffi.string(name).decode(), char))
    except BaseException:
        return 0


@ffi.def_extern()
def exit_function(env: ffi.CData, exitcode: int, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        router.exit(exitcode)
    except BaseException:
        pass
