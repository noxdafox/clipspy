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

from enum import IntEnum
from collections import namedtuple

from clips.router import ErrorRouter

from clips._clips import lib, ffi


class CLIPSError(RuntimeError):
    """An error occurred within the CLIPS Environment."""

    def __init__(self, env: ffi.CData, code: int = None):
        routers = environment_data(env, 'routers')
        message = routers['python-error-router'].last_message
        message = message.lstrip('\n').rstrip('\n').replace('\n', ' ')

        super(CLIPSError, self).__init__(message)

        self.code = code


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
    VOID = 9


class SaveMode(IntEnum):
    LOCAL_SAVE = lib.LOCAL_SAVE
    VISIBLE_SAVE = lib.VISIBLE_SAVE


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
    WHEN_DEFINED = lib.WHEN_DEFINED
    WHEN_ACTIVATED = lib.WHEN_ACTIVATED
    EVERY_CYCLE = lib.EVERY_CYCLE


class Verbosity(IntEnum):
    VERBOSE = 0
    SUCCINT = 1
    TERSE = 2


class TemplateSlotDefaultType(IntEnum):
    NO_DEFAULT = lib.NO_DEFAULT
    STATIC_DEFAULT = lib.STATIC_DEFAULT
    DYNAMIC_DEFAULT = lib.DYNAMIC_DEFAULT


def initialize_environment_data(environment):
    env = environment._env

    fact = lib.CreateFactBuilder(env, ffi.NULL)
    if fact is ffi.NULL:
        raise CLIPSError(env, code=lib.FBError(env))
    instance = lib.CreateInstanceBuilder(env, ffi.NULL)
    if fact is ffi.NULL:
        raise CLIPSError(env, code=lib.FBError(env))
    function = lib.CreateFunctionCallBuilder(env, 0)
    if fact is ffi.NULL:
        raise CLIPSError(env, code=lib.FBError(env))
    multifield = lib.CreateMultifieldBuilder(env, 0)
    if multifield is ffi.NULL:
        raise CLIPSError(env)
    string = lib.CreateStringBuilder(env, 0)
    if string is ffi.NULL:
        raise CLIPSError(env)
    builders = EnvBuilders(fact, instance, function, string, multifield)

    fact = lib.CreateFactModifier(env, ffi.NULL)
    if fact is ffi.NULL:
        raise CLIPSError(env, code=lib.FMError(env))
    instance = lib.CreateInstanceModifier(env, ffi.NULL)
    if instance is ffi.NULL:
        raise CLIPSError(env, code=lib.FMError(env))
    modifiers = EnvModifiers(fact, instance)

    ENVIRONMENT_DATA[env] = EnvData(builders, modifiers, {}, {})

    error_router = ErrorRouter()
    error_router.add_to_environment(environment)

    lib.DefinePythonFunction(env)

    return ENVIRONMENT_DATA[env]


def delete_environment_data(env):
    data = ENVIRONMENT_DATA.pop(env, None)

    if data is not None:
        fact, instance, function, string, multifield = data.builders

        lib.FBDispose(fact)
        lib.IBDispose(instance)
        lib.FCBDispose(function)
        lib.SBDispose(string)
        lib.MBDispose(multifield)

        fact, instance = data.modifiers
        lib.FMDispose(fact)
        lib.IMDispose(instance)


def environment_data(env, name) -> type:
    return getattr(ENVIRONMENT_DATA[env], name)


def environment_builder(env, name) -> ffi.CData:
    return getattr(ENVIRONMENT_DATA[env].builders, name)


def environment_modifier(env, name) -> ffi.CData:
    return getattr(ENVIRONMENT_DATA[env].modifiers, name)


ENVIRONMENT_DATA = {}
EnvData = namedtuple('EnvData', ('builders',
                                 'modifiers',
                                 'routers',
                                 'user_functions'))
EnvBuilders = namedtuple('EnvData', ('fact',
                                     'instance',
                                     'function',
                                     'string',
                                     'multifield'))
EnvModifiers = namedtuple('EnvData', ('fact',
                                      'instance'))
