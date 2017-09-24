import sys

from enum import IntEnum
from collections import namedtuple

import clips

from clips._clips import lib, ffi


class SaveMode(IntEnum):
    LOCAL_SAVE = 0
    VISIBLE_SAVE = 1


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


class Symbol(str):
    def __new__(cls, symbol):
        return str.__new__(cls, sys.intern(symbol))


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
        try:
            return CONVERTERS[dtype](dvalue)
        except KeyError:
            if dtype == CLIPSType.MULTIFIELD:
                return self.multifield_to_list()
            elif dtype == CLIPSType.FACT_ADDRESS:
                return clips.facts.new_fact(self._env, lib.to_pointer(dvalue))
            elif dtype == CLIPSType.INSTANCE_ADDRESS:
                return clips.classes.Instance(self._env, lib.to_pointer(dvalue))

        return None

    def clips_value(self, dvalue):
        try:
            return VALUES[type(dvalue)](self._env, dvalue)
        except KeyError:
            if isinstance(dvalue, (list, tuple)):
                return self.list_to_multifield(dvalue)

        return ffi.NULL

    def multifield_to_list(self):
        end = lib.get_data_end(self._data)
        begin = lib.get_data_begin(self._data)
        multifield = lib.get_data_value(self._data)
        ftype = lambda m, i: lib.get_multifield_type(m, i)
        fvalue = lambda m, i: lib.get_multifield_value(m, i)

        return [self.python_value(ftype(multifield, i), (fvalue(multifield, i)))
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


@ffi.def_extern()
def python_function(env, data_object):
    arguments = []
    temp = DataObject(env)
    data = DataObject(env, data=data_object)
    argnum = lib.EnvRtnArgCount(env)

    if lib.EnvArgTypeCheck(
            env, b'python-function', 1, CLIPSType.SYMBOL, temp.byref) != 1:
        raise RuntimeError()

    funcname = temp.value

    for index in range(2, argnum + 1):
        lib.EnvRtnUnknown(env, index, temp.byref)
        arguments.append(temp.value)

    try:
        ret = ENVIRONMENT_DATA[env].user_functions[funcname](*arguments)
    except Exception as error:
        ret = str("%s: %s" % (error.__class__.__name__, error))

    data.value = ret if ret is not None else Symbol('nil')


EnvData = namedtuple('EnvData', ('user_functions', 'error_router'))

ENVIRONMENT_DATA = {}  # env: EnvData

TYPES = {int: CLIPSType.INTEGER,
         float: CLIPSType.FLOAT,
         str: CLIPSType.STRING,
         list: CLIPSType.MULTIFIELD,
         tuple: CLIPSType.MULTIFIELD,
         Symbol: CLIPSType.SYMBOL}
VALUES = {int: lib.EnvAddLong,
          float: lib.EnvAddDouble,
          ffi.CData: lambda e, v: v,
          str: lambda e, v: lib.EnvAddSymbol(e, v.encode()),
          Symbol: lambda e, v: lib.EnvAddSymbol(e, v.encode())}
CONVERTERS = {CLIPSType.FLOAT: lib.to_double,
              CLIPSType.INTEGER: lib.to_integer,
              CLIPSType.STRING: lambda v: ffi.string(lib.to_string(v)).decode(),
              CLIPSType.EXTERNAL_ADDRESS: lib.to_external_address,
              CLIPSType.SYMBOL:
              lambda v: Symbol(ffi.string(lib.to_string(v)).decode())}
