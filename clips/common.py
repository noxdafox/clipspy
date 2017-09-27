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
        pass


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
