from __future__ import print_function

from clips.router import Router
from clips.common import ENVIRONMENT_DATA

from clips._clips import lib, ffi


class CLIPSError(RuntimeError):
    def __init__(self, env):
        message = ENVIRONMENT_DATA[env].error_router.last_message
        message = message.lstrip('\n').rstrip('\n').replace('\n', ' ')

        super(CLIPSError, self).__init__(message)

        self.code = message[message.find("[") + 1:message.find("]")]


class ErrorRouter(Router):
    def __init__(self, *parameters):
        super(ErrorRouter, self).__init__(*parameters)
        self._last_message = ''

    @property
    def last_message(self):
        ret = self._last_message

        self._last_message = ''

        return ret

    def query(self, name):
        return True if name in 'werror' else False

    def print(self, name, message):
        self._last_message += message
        self.deactivate()
        lib.EnvPrintRouter(self._env, name.encode(), message.encode())
        self.activate()
