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

import sys

from enum import IntEnum
from collections import namedtuple

from clips._clips import lib, ffi


if sys.version_info.major == 3:
    class Symbol(str):
        """Python equivalent of a CLIPS SYMBOL."""
        def __new__(cls, symbol):
            return str.__new__(cls, sys.intern(symbol))
elif sys.version_info.major == 2:
    class Symbol(str):
        """Python equivalent of a CLIPS SYMBOL."""
        def __new__(cls, symbol):
            return str.__new__(cls, intern(str(symbol)))


class CLIPSType(IntEnum):
    FLOAT = 0
    INTEGER = 1
    SYMBOL = 2
    STRING = 3
    MULTIFIELD = 4
    EXTERNAL_ADDRESS = 5
    FACT_ADDRESS = 6
    INSTANCE_ADDRESS = 7
    INSTANCE_NAME = 8


class SaveMode(IntEnum):
    LOCAL_SAVE = 0
    VISIBLE_SAVE = 1


class ClassDefaultMode(IntEnum):
    CONVENIENCE_MODE = 0
    CONSERVATION_MODE = 1


class Strategy(IntEnum):
    DEPTH = 0
    BREADTH = 1
    LEX = 2
    MEA = 3
    COMPLEXITY = 4
    SIMPLICITY = 5
    RANDOM = 6


class SalienceEvaluation(IntEnum):
    WHEN_DEFINED = 0
    WHEN_ACTIVATED = 1
    EVERY_CYCLE = 2


class Verbosity(IntEnum):
    VERBOSE = 0
    SUCCINT = 1
    TERSE = 2


class TemplateSlotDefaultType(IntEnum):
    NO_DEFAULT = 0
    STATIC_DEFAULT = 1
    DYNAMIC_DEFAULT = 2


# Assign functions and error routers per Environment
ENVIRONMENT_DATA = {}
EnvData = namedtuple('EnvData', ('user_functions', 'error_router'))
