from __future__ import print_function

import logging

from clips._clips import lib, ffi


class Router(object):
    def __init__(self, name, priority):
        self._env = None
        self._name = name
        self._userdata = None
        self._priority = priority

    @property
    def name(self):
        """The Router name."""
        return self._name

    def query(self, _name):
        """This method should return True if the provided logical name
        is handled by the Router.

        """
        return False

    def print(self, _name, _message):
        """If the query method returned True for the given logical name,
        this method will be called with the forwarded message.

        """
        return 0

    def getc(self, _name):
        return 0

    def ungetc(self, _name, _char):
        return 0

    def exit(self, _exitcode):
        return 0

    def activate(self):
        """Activate the Router."""
        if lib.EnvActivateRouter(self._env, self._name.encode()) == 0:
            raise RuntimeError("Unable to activate router %s" % self._name)

    def deactivate(self):
        """Deactivate the Router."""
        if lib.EnvDeactivateRouter(self._env, self._name.encode()) == 0:
            raise RuntimeError("Unable to deactivate router %s" % self._name)

    def delete(self):
        """Delete the Router."""
        if lib.EnvDeleteRouter(self._env, self._name.encode()) == 0:
            raise RuntimeError("Unable to delete router %s" % self._name)

    def add_to_environment(self, environment):
        """Add the router to the given environment."""
        self._env = environment._env
        self._userdata = ffi.new_handle(self)

        lib.EnvAddRouterWithContext(
            self._env, self._name.encode(), self._priority,
            lib.query_function,
            lib.print_function,
            lib.getc_function,
            lib.ungetc_function,
            lib.exit_function,
            self._userdata)


class LoggingRouter(Router):
    """Python logging Router.

    A helper Router to get Python standard logging facilities
    integrated with CLIPS.

    """
    LOGGERS = {'wtrace': logging.debug,
               'stdout': logging.info,
               'wclips': logging.info,
               'wdialog': logging.info,
               'wdisplay': logging.info,
               'wwarning': logging.warning,
               'werror': logging.error}

    def __init__(self):
        super(LoggingRouter, self).__init__('python-logging-router', 30)
        self._message = ''

    def query(self, name):
        return name in self.LOGGERS

    def print(self, name, message):
        if message == '\n':
            self.log_message(name)
        else:
            self._message += message
            if self._message.rstrip(' ').endswith('\n'):
                self.log_message(name)

    def log_message(self, name):
        if self._message:
            self.LOGGERS[name](self._message.lstrip('\n').rstrip('\n'))
            self._message = ''


@ffi.def_extern()
def query_function(env, name):
    router = ffi.from_handle(lib.GetEnvironmentRouterContext(env))

    return int(router.query(ffi.string(name).decode()))


@ffi.def_extern()
def print_function(env, name, message):
    router = ffi.from_handle(lib.GetEnvironmentRouterContext(env))

    try:
        router.print(ffi.string(name).decode(), ffi.string(message).decode())
    except BaseException:
        pass

    return 0


@ffi.def_extern()
def getc_function(env, name):
    router = ffi.from_handle(lib.GetEnvironmentRouterContext(env))

    try:
        return int(router.getc(ffi.string(name).decode()))
    except BaseException:
        pass

    return 0


@ffi.def_extern()
def ungetc_function(env, char, name):
    router = ffi.from_handle(lib.GetEnvironmentRouterContext(env))

    try:
        router.ungetc(ffi.string(name).decode(), char)
    except BaseException:
        pass

    return 0


@ffi.def_extern()
def exit_function(env, exitcode):
    router = ffi.from_handle(lib.GetEnvironmentRouterContext(env))

    try:
        router.exit(exitcode)
    except BaseException:
        pass

    return 0
