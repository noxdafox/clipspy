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

from __future__ import print_function

from clips.router import Router
from clips.common import ENVIRONMENT_DATA

from clips._clips import lib, ffi


class CLIPSError(RuntimeError):
    """An error occurred within the CLIPS Environment."""

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
