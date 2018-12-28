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

import clips

from clips._clips import lib, ffi


class DataObject(object):
    """CLIPS DATA_OBJECT structure wrapper."""

    __slots__ = '_env', '_data', '_type'

    def __init__(self, env, data=None, dtype=None):
        self._env = env
        self._type = dtype
        self._data = data if data is not None else ffi.new("DATA_OBJECT *")

    @property
    def byref(self):
        """Return the DATA_OBJECT structure pointer."""
        return self._data

    @property
    def byval(self):
        """Return the DATA_OBJECT structure."""
        return self._data[0]

    @property
    def value(self):
        """Return the DATA_OBJECT stored value."""
        dtype = lib.get_data_type(self._data)
        dvalue = lib.get_data_value(self._data)

        if dvalue == ffi.NULL:
            return None

        return self.python_value(dtype, dvalue)

    @value.setter
    def value(self, value):
        """Sets the DATA_OBJECT stored value."""
        dtype = TYPES[type(value)] if self._type is None else self._type

        lib.set_data_type(self._data, dtype)
        lib.set_data_value(self._data, self.clips_value(value))

    def python_value(self, dtype, dvalue):
        """Convert a CLIPS type into Python."""
        try:
            return CONVERTERS[dtype](dvalue)
        except KeyError:
            if dtype == clips.common.CLIPSType.MULTIFIELD:
                return self.multifield_to_list()
            elif dtype == clips.common.CLIPSType.FACT_ADDRESS:
                return clips.facts.new_fact(self._env, lib.to_pointer(dvalue))
            elif dtype == clips.common.CLIPSType.INSTANCE_ADDRESS:
                return clips.classes.Instance(self._env, lib.to_pointer(dvalue))

        return None

    def clips_value(self, dvalue):
        """Convert a Python type into CLIPS."""
        try:
            return VALUES[type(dvalue)](self._env, dvalue)
        except KeyError:
            if isinstance(dvalue, (list, tuple)):
                return self.list_to_multifield(dvalue)
            if isinstance(dvalue, (clips.facts.Fact)):
                return dvalue._fact
            if isinstance(dvalue, (clips.classes.Instance)):
                return dvalue._ist

        return ffi.NULL

    def multifield_to_list(self):
        end = lib.get_data_end(self._data)
        begin = lib.get_data_begin(self._data)
        multifield = lib.get_data_value(self._data)

        return [self.python_value(lib.get_multifield_type(multifield, i),
                                  lib.get_multifield_value(multifield, i))
                for i in range(begin, end + 1)]

    def list_to_multifield(self, values):
        index = 1
        size = len(values)
        multifield = lib.EnvCreateMultifield(self._env, size)

        for value in values:
            lib.set_multifield_type(multifield, index, TYPES[type(value)])
            lib.set_multifield_value(multifield, index, self.clips_value(value))

            index += 1

        lib.set_data_begin(self._data, 1)
        lib.set_data_end(self._data, size)

        return multifield


def string_to_str(string):
    return ffi.string(lib.to_string(string)).decode()


CONVERTERS = {clips.common.CLIPSType.FLOAT: lib.to_double,
              clips.common.CLIPSType.INTEGER: lib.to_integer,
              clips.common.CLIPSType.STRING: string_to_str,
              clips.common.CLIPSType.EXTERNAL_ADDRESS: lib.to_external_address,
              clips.common.CLIPSType.INSTANCE_NAME: string_to_str,
              clips.common.CLIPSType.SYMBOL:
              lambda v: clips.common.Symbol(string_to_str(v))}

TYPES = {type(None): clips.common.CLIPSType.SYMBOL,
         bool: clips.common.CLIPSType.SYMBOL,
         int: clips.common.CLIPSType.INTEGER,
         float: clips.common.CLIPSType.FLOAT,
         str: clips.common.CLIPSType.STRING,
         list: clips.common.CLIPSType.MULTIFIELD,
         tuple: clips.common.CLIPSType.MULTIFIELD,
         clips.common.Symbol: clips.common.CLIPSType.SYMBOL,
         clips.facts.ImpliedFact: clips.common.CLIPSType.FACT_ADDRESS,
         clips.facts.TemplateFact: clips.common.CLIPSType.FACT_ADDRESS,
         clips.classes.Instance: clips.common.CLIPSType.INSTANCE_ADDRESS}
VALUES = {type(None): lambda e, v: lib.EnvAddSymbol(e, b'nil'),
          bool: lambda e, v: lib.EnvAddSymbol(e, b'TRUE' if v else b'FALSE'),
          int: lib.EnvAddLong,
          float: lib.EnvAddDouble,
          ffi.CData: lambda _, v: v,
          str: lambda e, v: lib.EnvAddSymbol(e, v.encode()),
          clips.common.Symbol: lambda e, v: lib.EnvAddSymbol(e, v.encode())}

if sys.version_info.major == 2:
    # pylint: disable=E0602
    TYPES[unicode] = clips.common.CLIPSType.STRING
    # pylint: disable=E0602
    VALUES[unicode] = lambda e, v: lib.EnvAddSymbol(e, v.encode())
