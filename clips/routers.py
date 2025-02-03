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

  * Router class
  * LoggingRouter class
  * Routers namespace class

"""

import logging
import traceback

import clips
from clips import common

from clips._clips import lib, ffi


class Router:

    __slots__ = '_env', '_name', '_userdata', '_priority'

    def __init__(self, name: str, priority: int):
        self._env = None
        self._name = name
        self._priority = priority
        self._userdata = ffi.new_handle(self)

    @property
    def name(self) -> str:
        """The Router name."""
        return self._name

    @property
    def priority(self) -> int:
        """The Router priority."""
        return self._priority

    def query(self, _name: str) -> bool:
        """This method should return True if the provided logical name
        is handled by the Router.

        """
        return False

    def write(self, _name: str, _message: str):
        """If the query method returns True for the given logical name,
        this method will be called with the forwarded message.

        """
        return None

    def read(self, _name: str) -> int:
        """Callback implementation for the `Environment.read_router`
        function.

        """
        return 0

    def unread(self, _name: str, _char: int) -> int:
        """Callback implementation for the `Environment.unread_router`
        function.

        """
        return 0

    def exit(self, _exitcode: int):
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

    def share_message(self, name: str, message: str):
        """Share the captured message with other Routers."""
        self.deactivate()
        lib.WriteString(self._env, name.encode(), message.encode())
        self.activate()


class ErrorRouter(Router):
    """Router capturing error messages for CLIPSError exceptions."""

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
        self.share_message(name, message)


class LoggingRouter(Router):
    """Python logging Router.

    A helper Router to get Python standard logging facilities
    integrated with CLIPS.

    It captures CLIPS output and re-directs it to Python logging library.

    """

    __slots__ = '_env', '_name', '_userdata', '_priority', '_message'

    LOGGERS = {'stdout': logging.info,
               'stderr': logging.error,
               'stdwrn': logging.warning}

    def __init__(self):
        super().__init__('python-logging-router', 30)
        self._message = ''

    def query(self, name: str) -> bool:
        """Capture log from CLIPS output routers."""
        return name in self.LOGGERS

    def write(self, name: str, message: str):
        """If the message is a new-line terminate sentence,
        log it at according to the mapped level.

        Otherwise, append it to the message string.

        """
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


class Routers:
    """Routers namespace class.

    .. note::

       All the Routers methods are accessible through the Environment class.

    """

    __slots__ = ['_env']

    def __init__(self, env):
        self._env = env

    def routers(self) -> iter:
        """The User defined routers installed within the Environment."""
        return common.environment_data(self._env, 'routers').values()

    def read_router(self, router_name: str) -> int:
        """Query the Router by the given name calling its `read` callback."""
        return lib.ReadRouter(self._env, router_name.encode())

    def unread_router(self, router_name: str, characters: int) -> int:
        """Query the Router by the given name calling its `unread` callback."""
        return lib.UnReadRouter(self._env, router_name.encode(), characters)

    def write_router(self, router_name: str, *args):
        """Send the given arguments to the given Router for writing."""
        for arg in args:
            if type(arg) == str:
                lib.WriteString(self._env, router_name.encode(), arg.encode())
            else:
                value = clips.values.clips_value(self._env, arg)
                lib.WriteCLIPSValue(self._env, router_name.encode(), value)

    def add_router(self, router: Router):
        """Add the given Router to the Environment."""
        name = router.name
        router._env = self._env

        common.environment_data(self._env, 'routers')[name] = router

        lib.AddRouter(self._env,
                      name.encode(),
                      router.priority,
                      lib.query_function,
                      lib.write_function,
                      lib.read_function,
                      lib.unread_function,
                      lib.exit_function,
                      router._userdata)


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
    except BaseException as error:
        message = "[ROUTER2] Router callback error: %r" % error
        string = "\n".join((message, traceback.format_exc()))

        lib.WriteString(env, 'stderr'.encode(), string.encode())


@ffi.def_extern()
def read_function(env: ffi.CData, name: ffi.CData, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        return int(router.read(ffi.string(name).decode()))
    except BaseException as error:
        message = "[ROUTER2] Router callback error: %r" % error
        string = "\n".join((message, traceback.format_exc()))

        lib.WriteString(env, 'stderr'.encode(), string.encode())

        return 0


@ffi.def_extern()
def unread_function(env: ffi.CData, char: ffi.CData,
                    name: ffi.CData, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        return int(router.unread(ffi.string(name).decode(), char))
    except BaseException as error:
        message = "[ROUTER2] Router callback error: %r" % error
        string = "\n".join((message, traceback.format_exc()))

        lib.WriteString(env, 'stderr'.encode(), string.encode())

        return 0


@ffi.def_extern()
def exit_function(env: ffi.CData, exitcode: int, context: ffi.CData):
    router = ffi.from_handle(context)

    try:
        router.exit(exitcode)
    except BaseException as error:
        message = "[ROUTER2] Router callback error: %r" % error
        string = "\n".join((message, traceback.format_exc()))

        lib.WriteString(env, 'stderr'.encode(), string.encode())
