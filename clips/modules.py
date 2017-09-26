import clips

from clips.error import CLIPSError

from clips._clips import lib, ffi


class Modules:
    """Globals and Modules wrapper class."""

    __slots__ = '_env'

    def __init__(self, env):
        self._env = env

    @property
    def current_module(self):
        """The current module.

        The Python equivalent of the CLIPS get-current-module function.

        """
        return Module(self._env, lib.EnvGetCurrentModule(self._env))

    @current_module.setter
    def current_module(self, module):
        """The current module.

        The Python equivalent of the CLIPS get-current-module function.

        """
        lib.EnvSetCurrentModule(self._env, module._mdl)

    @property
    def globals_changed(self):
        """True if any Global has changed."""
        value = bool(lib.EnvGetGlobalsChanged(self._env))
        lib.EnvSetGlobalsChanged(self._env, int(False))

        return value

    def globals(self):
        """Iterates over the defined Globals."""
        defglobal = lib.EnvGetNextDefglobal(self._env, ffi.NULL)

        while defglobal != ffi.NULL:
            yield Global(self._env, defglobal)

            defglobal = lib.EnvGetNextDefglobal(self._env, defglobal)

    def find_global(self, name):
        """Find the Global by its name."""
        defglobal = lib.EnvFindDefglobal(self._env, name.encode())
        if defglobal == ffi.NULL:
            raise LookupError("Global '%s' not found" % name)

        return Global(self._env, defglobal)

    def modules(self):
        """Iterates over the defined Modules."""
        defmodule = lib.EnvGetNextDefmodule(self._env, ffi.NULL)

        while defmodule != ffi.NULL:
            yield Module(self._env, defmodule)

            defmodule = lib.EnvGetNextDefmodule(self._env, defmodule)

    def find_module(self, name):
        """Find the Module by its name."""
        defmodule = lib.EnvFindDefmodule(self._env, name.encode())
        if defmodule == ffi.NULL:
            raise LookupError("Module '%s' not found" % name)

        return Module(self._env, defmodule)



class Global:
    """This class encapsulates the CLIPS Defglobal data structure."""

    __slots__ = '_env', '_glb'

    def __init__(self, env, glb):
        self._env = env
        self._glb = glb

    def __hash__(self):
        return hash(self._glb)

    def __eq__(self, glb):
        return self._glb == glb._glb

    def __str__(self):
        string = ffi.string(lib.EnvGetDefglobalPPForm(self._env, self._glb))

        return string.decode().rstrip('\n')

    def __repr__(self):
        string = ffi.string(lib.EnvGetDefglobalPPForm(self._env, self._glb))

        return "%s: %s" % (self.__class__.__name__,
                           string.decode().rstrip('\n'))

    @property
    def value(self):
        """Global value."""
        data = clips.data.DataObject(self._env)

        if lib.EnvGetDefglobalValue(
                self._env, self.name.encode(), data.byref) != 1:
            raise CLIPSError(self._env)

        return data.value

    @value.setter
    def value(self, value):
        """Global value."""
        data = clips.data.DataObject(self._env)
        data.value = value

        if lib.EnvSetDefglobalValue(
                self._env, self.name.encode(), data.byref) != 1:
            raise CLIPSError(self._env)

    @property
    def name(self):
        """Global name."""
        return ffi.string(
            lib.EnvGetDefglobalName(self._env, self._glb)).decode()

    @property
    def module(self):
        """The module in which the Global is defined.

        Python equivalent of the CLIPS defglobal-module command.

        """
        modname = ffi.string(lib.EnvDefglobalModule(self._env, self._glb))
        defmodule = lib.EnvFindDefmodule(self._env, modname)

        return Module(self._env, defmodule)

    @property
    def deletable(self):
        """True if the Global can be deleted."""
        return bool(lib.EnvIsDefglobalDeletable(self._env, self._glb))

    @property
    def watch(self):
        """Whether or not the Global is being watched."""
        return bool(lib.EnvGetDefglobalWatch(self._env, self._glb))

    @watch.setter
    def watch(self, flag):
        """Whether or not the Global is being watched."""
        lib.EnvSetDefglobalWatch(self._env, int(flag), self._glb)

    def undefine(self):
        """Undefine the Global.

        Python equivalent of the CLIPS undefglobal command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndefglobal(self._env, self._glb) != 1:
            raise CLIPSError(self._env)

        self._env = None


class Module:
    __slots__ = '_env', '_mdl'

    def __init__(self, env, mdl):
        self._env = env
        self._mdl = mdl

    def __hash__(self):
        return hash(self._mdl)

    def __eq__(self, mdl):
        return self._mdl == mdl._mdl

    def __str__(self):
        module = lib.EnvGetDefmodulePPForm(self._env, self._mdl)

        return ffi.string(module).decode() if module != ffi.NULL else self.name

    def __repr__(self):
        module = lib.EnvGetDefmodulePPForm(self._env, self._mdl)
        strn = ffi.string(module).decode() if module != ffi.NULL else self.name

        return "%s: %s" % (self.__class__.__name__, strn)

    @property
    def name(self):
        """Global name."""
        return ffi.string(
            lib.EnvGetDefmoduleName(self._env, self._mdl)).decode()
