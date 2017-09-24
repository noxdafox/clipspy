from clips.facts import Facts
from clips.agenda import Agenda
from clips.classes import Classes
from clips.modules import Modules
from clips.functions import Functions
from clips.error import CLIPSError, ErrorRouter
from clips.common import DataObject, EnvData, ENVIRONMENT_DATA

from clips._clips import lib, ffi


class Environment(object):
    __slots__ = ('_env', '_facts', '_agenda',
                 '_classes', '_modules', '_functions')

    def __init__(self):
        self._env = lib.CreateEnvironment()
        self._facts = Facts(self._env)
        self._agenda = Agenda(self._env)
        self._classes = Classes(self._env)
        self._modules = Modules(self._env)
        self._functions = Functions(self._env)

        lib.define_function(self._env)

        error_router = ErrorRouter('python-error-router', 40)
        error_router.add_to_environment(self)

        ENVIRONMENT_DATA[self._env] = EnvData({}, error_router)

    def __del__(self):
        try:
            lib.DestroyEnvironment(self._env)
            del ENVIRONMENT_DATA[self._env]
        except (AttributeError, KeyError):
            pass

    @property
    def facts(self):
        """Environment Facts namespace.

        Fact and Template functions are grouped under this namespace.

        """
        return self._facts

    @property
    def agenda(self):
        """Environment Agenda namespace.

        The Agenda and the Rule functions are grouped under this namespace.

        """
        return self._agenda

    @property
    def classes(self):
        """Environment Classes namespace.

        Classe and Instance functions are grouped under this namespace.

        """
        return self._classes

    @property
    def modules(self):
        """Environment Modules namespace.

        Module and Global functions are grouped under this namespace.

        """
        return self._modules

    @property
    def functions(self):
        """Environment Functions namespace.

        Function and Generic functions are grouped under this namespace.

        """
        return self._functions

    def load(self, path):
        """Load a set of constructs into the CLIPS data base.

        The Python equivalent of the CLIPS load command.

        """
        ret = lib.EnvBload(self._env, path.encode())
        if ret != 1:
            ret = lib.EnvLoad(self._env, path.encode())
            if ret != 1:
                raise CLIPSError(self._env)

    def save(self, path, binary=False):
        """Save a set of constructs into the CLIPS data base.

        If binary is True, the constructs will be saved in binary format.

        The Python equivalent of the CLIPS load command.

        """
        if binary:
            ret = lib.EnvBsave(self._env, path.encode())
        else:
            ret = lib.EnvSave(self._env, path.encode())
        if ret == 0:
            raise CLIPSError(self._env)

    def build(self, construct):
        """Build a single construct in CLIPS.

        The Python equivalent of the CLIPS build command.

        """
        if lib.EnvBuild(self._env, construct.encode()) != 1:
            raise CLIPSError(self._env)

    def eval(self, construct):
        """Evaluate an expression returning its value.

        The Python equivalent of the CLIPS eval command.

        """
        data = DataObject(self._env)

        if lib.EnvEval(self._env, construct.encode(), data.byref) != 1:
            raise CLIPSError(self._env)

        return data.value

    def reset(self):
        """Reset the CLIPS environment.

        The Python equivalent of the CLIPS reset command.

        """
        lib.EnvReset(self._env)

    def clear(self):
        """Clear the CLIPS environment.

        The Python equivalent of the CLIPS clear command.

        """
        lib.EnvClear(self._env)

    def define_function(self, function):
        """Define the Python function within the CLIPS environment.

        Functions defined in this way can be called within CLIPS
        via the 'python-function' symbol.

        (python-function function_name arg1 arg2)

        """
        ENVIRONMENT_DATA[self._env].user_functions[function.__name__] = function
