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

import sys

from clips import common
from clips.classes import Instance
from clips.facts import new_fact, ImpliedFact, TemplateFact

from clips._clips import lib, ffi  # pylint: disable=E0611


class Symbol(str):
    """Python equivalent of a CLIPS SYMBOL."""
    def __new__(cls, symbol):
        return str.__new__(cls, sys.intern(symbol))


class InstanceName(Symbol):
    """Python equivalent of a CLIPS INSTANCE_NAME."""


def python_value(env, value: ffi.CData) -> type:
    """Convert a CLIPSValue or UDFValue into Python."""
    return PYTHON_VALUES[value.header.type](env, value)


def clips_value(env: ffi.CData, value: type = ffi.NULL) -> ffi.CData:
    """Convert a Python value into CLIPS.

    If no value is provided, an empty value is returned.

    """
    val = ffi.new("CLIPSValue *")

    if value is not ffi.NULL:
        constructor = CLIPS_VALUES.get(type(value), clips_external_address)
        val.value = constructor(env, value)

    return val


def clips_udf_value(env: ffi.CData, value: type = ffi.NULL,
                    udf_value: ffi.CData = ffi.NULL) -> ffi.CData:
    """Convert a Python value into a CLIPS UDFValue.

    If no value is provided, an empty value is returned.

    """
    if udf_value is ffi.NULL:
        return ffi.new("UDFValue *")

    constructor = CLIPS_VALUES.get(type(value), clips_external_address)
    udf_value.value = constructor(env, value)

    return udf_value


def multifield_value(env: ffi.CData, values: (list, tuple)) -> ffi.CData:
    """Convert a Python list or tuple into a CLIPS multifield."""
    if not values:
        return lib.EmptyMultifield(env)

    builder = common.environment_builder(env, 'multifield')

    lib.MBReset(builder)
    for value in values:
        lib.MBAppend(builder, clips_value(env, value))

    return lib.MBCreate(builder)


def clips_external_address(env: ffi.CData, value: type) -> ffi.CData:
    """Convert a Python object into a CLIPSExternalAddress."""
    handle = ffi.new_handle(value)

    # Hold reference to CData handle
    user_functions = common.environment_data(env, 'user_functions')
    user_functions.external_addresses[handle] = value

    return lib.CreateCExternalAddress(env, handle)


def python_external_address(env: ffi.CData, value: ffi.CData) -> type:
    """Convert a CLIPSExternalAddress into a Python object."""
    obj = ffi.from_handle(value.externalAddressValue.contents)

    # Remove reference to CData handle
    user_functions = common.environment_data(env, 'user_functions')
    del user_functions.external_addresses[value.externalAddressValue.contents]

    return obj


PYTHON_VALUES = {common.CLIPSType.FLOAT:
                 lambda e, v: float(v.floatValue.contents),
                 common.CLIPSType.INTEGER:
                 lambda e, v: int(v.integerValue.contents),
                 common.CLIPSType.SYMBOL:
                 lambda e, v: Symbol(
                     ffi.string(v.lexemeValue.contents).decode()),
                 common.CLIPSType.STRING:
                 lambda e, v: ffi.string(v.lexemeValue.contents).decode(),
                 common.CLIPSType.MULTIFIELD:
                 lambda e, v: tuple(
                     python_value(e, v.multifieldValue.contents + i)
                     for i in range(v.multifieldValue.length)),
                 common.CLIPSType.FACT_ADDRESS:
                 lambda e, v: new_fact(e, v.factValue),
                 common.CLIPSType.INSTANCE_ADDRESS:
                 lambda e, v: Instance(e, v.instanceValue),
                 common.CLIPSType.INSTANCE_NAME:
                 lambda e, v: InstanceName(
                     ffi.string(v.lexemeValue.contents).decode()),
                 common.CLIPSType.EXTERNAL_ADDRESS: python_external_address,
                 common.CLIPSType.VOID: lambda e, v: None}


CLIPS_VALUES = {int: lib.CreateInteger,
                float: lib.CreateFloat,
                list: multifield_value,
                tuple: multifield_value,
                bool: lib.CreateBoolean,
                type(None): lambda e, v: lib.CreateSymbol(e, b'nil'),
                str: lambda e, v: lib.CreateString(e, v.encode()),
                Instance: lambda e, v: v._ist,
                ImpliedFact: lambda e, v: v._fact,
                TemplateFact: lambda e, v: v._fact,
                Symbol: lambda e, v: lib.CreateSymbol(e, v.encode()),
                InstanceName:
                lambda e, v: lib.CreateInstanceName(e, v.encode())}


ANY_TYPE_BITS = (lib.FLOAT_BIT | lib.INTEGER_BIT | lib.SYMBOL_BIT |
                 lib.STRING_BIT | lib.MULTIFIELD_BIT |
                 lib.EXTERNAL_ADDRESS_BIT | lib.FACT_ADDRESS_BIT |
                 lib.INSTANCE_ADDRESS_BIT | lib.INSTANCE_NAME_BIT
                 | lib.VOID_BIT | lib.BOOLEAN_BIT)
