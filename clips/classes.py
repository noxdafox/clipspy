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

"""This module contains the definition of:

  * Classes namespace class
  * Class class
  * Instance class
  * ClassSlot class
  * MessageHandler class

"""

import os

import clips

from clips.modules import Module
from clips.error import CLIPSError
from clips.common import SaveMode, ClassDefaultMode, CLIPSType

from clips._clips import lib, ffi


class Classes:
    """Classes and Instances namespace class.

    .. note::

       All the Classes methods are accessible through the Environment class.

    """

    __slots__ = '_env'

    def __init__(self, env):
        self._env = env

    @property
    def default_mode(self):
        """Return the current class defaults mode.

        The Python equivalent of the CLIPS get-class-defaults-mode command.

        """
        return ClassDefaultMode(lib.EnvGetClassDefaultsMode(self._env))

    @default_mode.setter
    def default_mode(self, value):
        """Return the current class defaults mode.

        The Python equivalent of the CLIPS get-class-defaults-mode command.

        """
        lib.EnvSetClassDefaultsMode(self._env, value)

    @property
    def instances_changed(self):
        """True if any instance has changed."""
        value = bool(lib.EnvGetInstancesChanged(self._env))
        lib.EnvSetInstancesChanged(self._env, int(False))

        return value

    def classes(self):
        """Iterate over the defined Classes."""
        defclass = lib.EnvGetNextDefclass(self._env, ffi.NULL)

        while defclass != ffi.NULL:
            yield Class(self._env, defclass)

            defclass = lib.EnvGetNextDefclass(self._env, defclass)

    def find_class(self, name):
        """Find the Class by its name."""
        defclass = lib.EnvFindDefclass(self._env, name.encode())
        if defclass == ffi.NULL:
            raise LookupError("Class '%s' not found" % name)

        return Class(self._env, defclass)

    def instances(self):
        """Iterate over the defined Instancees."""
        definstance = lib.EnvGetNextInstance(self._env, ffi.NULL)

        while definstance != ffi.NULL:
            yield Instance(self._env, definstance)

            definstance = lib.EnvGetNextInstance(self._env, definstance)

    def find_instance(self, name, module=None):
        """Find the Instance by its name."""
        module = module if module is not None else ffi.NULL
        definstance = lib.EnvFindInstance(self._env, module, name.encode(), 1)
        if definstance == ffi.NULL:
            raise LookupError("Instance '%s' not found" % name)

        return Instance(self._env, definstance)

    def load_instances(self, instances):
        """Load a set of instances into the CLIPS data base.

        The C equivalent of the CLIPS load-instances command.

        Instances can be loaded from a string,
        from a file or from a binary file.

        """
        instances = instances.encode()

        if os.path.exists(instances):
            try:
                return self._load_instances_binary(instances)
            except CLIPSError:
                return self._load_instances_text(instances)
        else:
            return self._load_instances_string(instances)

    def _load_instances_binary(self, instances):
        ret = lib.EnvBinaryLoadInstances(self._env, instances)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret

    def _load_instances_text(self, instances):
        ret = lib.EnvLoadInstances(self._env, instances)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret

    def _load_instances_string(self, instances):
        ret = lib.EnvLoadInstancesFromString(self._env, instances, -1)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret

    def restore_instances(self, instances):
        """Restore a set of instances into the CLIPS data base.

        The Python equivalent of the CLIPS restore-instances command.

        Instances can be passed as a set of strings or as a file.

        """
        instances = instances.encode()

        if os.path.exists(instances):
            ret = lib.EnvRestoreInstances(self._env, instances)
            if ret == -1:
                raise CLIPSError(self._env)
        else:
            ret = lib.EnvRestoreInstancesFromString(self._env, instances, -1)
            if ret == -1:
                raise CLIPSError(self._env)

        return ret

    def save_instances(self, path, binary=False, mode=SaveMode.LOCAL_SAVE):
        """Save the instances in the system to the specified file.

        If binary is True, the instances will be saved in binary format.

        The Python equivalent of the CLIPS save-instances command.

        """
        if binary:
            ret = lib.EnvBinarySaveInstances(self._env, path.encode(), mode)
        else:
            ret = lib.EnvSaveInstances(self._env, path.encode(), mode)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret


class Class:
    """A Class is a template for creating instances of objects.

    In CLIPS, Classes are defined via the (defclass) statement.

    Classes allow to create new instances
    to be added within the CLIPS environment.

    """

    __slots__ = '_env', '_cls'

    def __init__(self, env, cls):
        self._env = env
        self._cls = cls

    def __hash__(self):
        return hash(self._cls)

    def __eq__(self, cls):
        return self._cls == cls._cls

    def __str__(self):
        strn = lib.EnvGetDefclassPPForm(self._env, self._cls)
        strn = ffi.string(strn).decode() if strn != ffi.NULL else self.name

        return strn.rstrip('\n')

    def __repr__(self):
        strn = lib.EnvGetDefclassPPForm(self._env, self._cls)
        strn = ffi.string(strn).decode() if strn != ffi.NULL else self.name

        return "%s: %s" % (self.__class__.__name__, strn.rstrip('\n'))

    @property
    def abstract(self):
        """True if the class is abstract."""
        return bool(lib.EnvClassAbstractP(self._env, self._cls))

    @property
    def reactive(self):
        """True if the class is reactive."""
        return bool(lib.EnvClassReactiveP(self._env, self._cls))

    @property
    def name(self):
        """Class name."""
        return ffi.string(lib.EnvGetDefclassName(self._env, self._cls)).decode()

    @property
    def module(self):
        """The module in which the Class is defined.

        Python equivalent of the CLIPS defglobal-module command.

        """
        modname = ffi.string(lib.EnvDefclassModule(self._env, self._cls))
        defmodule = lib.EnvFindDefmodule(self._env, modname)

        return Module(self._env, defmodule)

    @property
    def deletable(self):
        """True if the Class can be deleted."""
        return bool(lib.EnvIsDefclassDeletable(self._env, self._cls))

    @property
    def watch_instances(self):
        """Whether or not the Class Instances are being watched."""
        return bool(lib.EnvGetDefclassWatchInstances(self._env, self._cls))

    @watch_instances.setter
    def watch_instances(self, flag):
        """Whether or not the Class Instances are being watched."""
        lib.EnvSetDefclassWatchInstances(self._env, int(flag), self._cls)

    @property
    def watch_slots(self):
        """Whether or not the Class Slots are being watched."""
        return bool(lib.EnvGetDefclassWatchSlots(self._env, self._cls))

    @watch_slots.setter
    def watch_slots(self, flag):
        """Whether or not the Class Slots are being watched."""
        lib.EnvSetDefclassWatchSlots(self._env, int(flag), self._cls)

    def new_instance(self, name):
        """Create a new raw instance from this Class."""
        ist = lib.EnvCreateRawInstance(self._env, self._cls, name.encode())
        if ist == ffi.NULL:
            raise CLIPSError(self._env)

        return Instance(self._env, ist)

    def find_message_handler(self, handler_name, handler_type='primary'):
        """Returns the MessageHandler given its name and type for this class."""
        ret = lib.EnvFindDefmessageHandler(
            self._env, self._cls, handler_name.encode(), handler_type.encode())
        if ret == 0:
            raise CLIPSError(self._env)

        return MessageHandler(self._env, self._cls, ret)

    def subclass(self, klass):
        """True if the Class is a subclass of the given one."""
        return bool(lib.EnvSubclassP(self._env, self._cls, klass._cls))

    def superclass(self, klass):
        """True if the Class is a superclass of the given one."""
        return bool(lib.EnvSuperclassP(self._env, self._cls, klass._cls))

    def slots(self, inherited=False):
        """Iterate over the Slots of the class."""
        data = clips.data.DataObject(self._env)

        lib.EnvClassSlots(self._env, self._cls, data.byref, int(inherited))

        return (ClassSlot(self._env, self._cls, n.encode()) for n in data.value)

    def instances(self):
        """Iterate over the instances of the class."""
        ist = lib.EnvGetNextInstanceInClass(self._env, self._cls, ffi.NULL)

        while ist != ffi.NULL:
            yield Instance(self._env, ist)

            ist = lib.EnvGetNextInstanceInClass(self._env, self._cls, ist)

    def subclasses(self, inherited=False):
        """Iterate over the subclasses of the class.

        This function is the Python equivalent
        of the CLIPS class-subclasses command.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvClassSubclasses(self._env, self._cls, data.byref, int(inherited))

        for klass in classes(self._env, data.value):
            yield klass

    def superclasses(self, inherited=False):
        """Iterate over the superclasses of the class.

        This function is the Python equivalent
        of the CLIPS class-superclasses command.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvClassSuperclasses(
            self._env, self._cls, data.byref, int(inherited))

        for klass in classes(self._env, data.value):
            yield klass

    def message_handlers(self):
        """Iterate over the message handlers of the class."""
        index = lib.EnvGetNextDefmessageHandler(self._env, self._cls, 0)

        while index != 0:
            yield MessageHandler(self._env, self._cls, index)

            index = lib.EnvGetNextDefmessageHandler(self._env, self._cls, index)

    def undefine(self):
        """Undefine the Class.

        Python equivalent of the CLIPS undefclass command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndefclass(self._env, self._cls) != 1:
            raise CLIPSError(self._env)

        self._env = None


class ClassSlot:
    """A Class Instances organize the information within Slots.

    Slots might restrict the type or amount of data they store.

    """

    __slots__ = '_env', '_cls', '_name'

    def __init__(self, env, cls, name):
        self._env = env
        self._cls = cls
        self._name = name

    def __hash__(self):
        return hash(self._cls) + hash(self._name)

    def __eq__(self, cls):
        return self._cls == cls._cls and self._name == cls._name

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    @property
    def name(self):
        """The Slot name."""
        return self._name.decode()

    @property
    def public(self):
        """True if the Slot is public."""
        return bool(lib.EnvSlotPublicP(self._env, self._cls, self._name))

    @property
    def initializable(self):
        """True if the Slot is initializable."""
        return bool(lib.EnvSlotInitableP(self._env, self._cls, self._name))

    @property
    def writable(self):
        """True if the Slot is writable."""
        return bool(lib.EnvSlotWritableP(self._env, self._cls, self._name))

    @property
    def accessible(self):
        """True if the Slot is directly accessible."""
        return bool(lib.EnvSlotDirectAccessP(self._env, self._cls, self._name))

    @property
    def types(self):
        """A tuple containing the value types for this Slot.

        The Python equivalent of the CLIPS slot-types function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotTypes(self._env, self._cls, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def sources(self):
        """A tuple containing the names of the Class sources for this Slot.

        The Python equivalent of the CLIPS slot-sources function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotSources(self._env, self._cls, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def range(self):
        """A tuple containing the numeric range for this Slot.

        The Python equivalent of the CLIPS slot-range function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotRange(self._env, self._cls, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def facets(self):
        """A tuple containing the facets for this Slot.

        The Python equivalent of the CLIPS slot-facets function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotFacets(self._env, self._cls, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def cardinality(self):
        """A tuple containing the cardinality for this Slot.

        The Python equivalent of the CLIPS slot-cardinality function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotCardinality(
            self._env, self._cls, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    @property
    def default_value(self):
        """The default value for this Slot.

        The Python equivalent of the CLIPS slot-default-value function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotDefaultValue(
            self._env, self._cls, self._name, data.byref)

        return data.value

    @property
    def allowed_values(self):
        """A tuple containing the allowed values for this Slot.

        The Python equivalent of the CLIPS slot-allowed-values function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotAllowedValues(
            self._env, self._cls, self._name, data.byref)

        return tuple(data.value) if isinstance(data.value, list) else ()

    def allowed_classes(self):
        """Iterate over the allowed classes for this slot.

        The Python equivalent of the CLIPS slot-allowed-classes function.

        """
        data = clips.data.DataObject(self._env)

        lib.EnvSlotAllowedClasses(
            self._env, self._cls, self._name, data.byref)

        if isinstance(data.value, list):
            for klass in classes(self._env, data.value):
                yield klass


class Instance:
    """A Class Instance is an occurrence of an object.

    Instances are dictionaries where each slot name is a key.

    """

    __slots__ = '_env', '_ist'

    def __init__(self, env, ist):
        self._env = env
        self._ist = ist
        lib.EnvIncrementInstanceCount(self._env, self._ist)

    def __del__(self):
        try:
            lib.EnvDecrementInstanceCount(self._env, self._ist)
        except (AttributeError, TypeError):
            pass  # mostly happening during interpreter shutdown

    def __hash__(self):
        return hash(self._ist)

    def __eq__(self, ist):
        return self._ist == ist._ist

    def __str__(self):
        return instance_pp_string(self._env, self._ist)

    def __repr__(self):
        return "%s: %s" % (
            self.__class__.__name__, instance_pp_string(self._env, self._ist))

    def __getitem__(self, slot):
        data = clips.data.DataObject(self._env)

        lib.EnvDirectGetSlot(self._env, self._ist, slot.encode(), data.byref)

        return data.value

    def __setitem__(self, slot, value):
        data = clips.data.DataObject(self._env)
        data.value = value

        if lib.EnvDirectPutSlot(
                self._env, self._ist, slot.encode(), data.byref) == 0:
            raise CLIPSError(self._env)

    @property
    def name(self):
        """Instance name."""
        return ffi.string(lib.EnvGetInstanceName(self._env, self._ist)).decode()

    @property
    def instance_class(self):
        """Instance class."""
        return Class(self._env, lib.EnvGetInstanceClass(self._env, self._ist))

    def send(self, message, arguments=None):
        """Send a message to the Instance.

        Message arguments must be provided as a string.

        """
        output = clips.data.DataObject(self._env)
        instance = clips.data.DataObject(
            self._env, dtype=CLIPSType.INSTANCE_ADDRESS)
        instance.value = self._ist

        args = arguments.encode() if arguments is not None else ffi.NULL

        lib.EnvSend(
            self._env, instance.byref, message.encode(), args, output.byref)

        return output.value

    def delete(self):
        """Delete the instance."""
        if lib.EnvDeleteInstance(self._env, self._ist) != 1:
            raise CLIPSError(self._env)

    def unmake(self):
        """This method is equivalent to delete except that it uses
        message-passing instead of directly deleting the instance.

        """
        if lib.EnvUnmakeInstance(self._env, self._ist) != 1:
            raise CLIPSError(self._env)


class MessageHandler:
    """MessageHandlers are the CLIPS equivalent of instance methods in Python.

    """

    __slots__ = '_env', '_cls', '_idx'

    def __init__(self, env, cls, idx):
        self._env = env
        self._cls = cls
        self._idx = idx

    def __hash__(self):
        return hash(self._cls) + self._idx

    def __eq__(self, cls):
        return self._cls == cls._cls and self._idx == cls._idx

    def __str__(self):
        string = ffi.string(lib.EnvGetDefmessageHandlerPPForm(
            self._env, self._cls, self._idx))

        return string.decode().rstrip('\n')

    def __repr__(self):
        string = ffi.string(lib.EnvGetDefmessageHandlerPPForm(
            self._env, self._cls, self._idx))

        return "%s: %s" % (self.__class__.__name__,
                           string.decode().rstrip('\n'))

    @property
    def name(self):
        """MessageHandler name."""
        return ffi.string(lib.EnvGetDefmessageHandlerName(
            self._env, self._cls, self._idx)).decode()

    @property
    def type(self):
        """MessageHandler type."""
        return ffi.string(lib.EnvGetDefmessageHandlerType(
            self._env, self._cls, self._idx)).decode()

    @property
    def watch(self):
        """True if the MessageHandler is being watched."""
        return bool(lib.EnvGetDefmessageHandlerWatch(
            self._env, self._cls, self._idx))

    @watch.setter
    def watch(self, flag):
        """True if the MessageHandler is being watched."""
        lib.EnvSetDefmessageHandlerWatch(
            self._env, int(flag), self._cls, self._idx)

    @property
    def deletable(self):
        """True if the MessageHandler can be deleted."""
        return bool(lib.EnvIsDefmessageHandlerDeletable(
            self._env, self._cls, self._idx))

    def undefine(self):
        """Undefine the MessageHandler.

        Python equivalent of the CLIPS undefmessage-handler command.

        The object becomes unusable after this method has been called.

        """
        if lib.EnvUndefmessageHandler(self._env, self._cls, self._idx) != 1:
            raise CLIPSError(self._env)

        self._env = None


def classes(env, names):
    for name in names:
        defclass = lib.EnvFindDefclass(env, name.encode())
        if defclass == ffi.NULL:
            raise CLIPSError(env)

        yield Class(env, defclass)


def instance_pp_string(env, ist):
    buf = ffi.new('char[1024]')
    lib.EnvGetInstancePPForm(env, buf, 1024, ist)

    return ffi.string(buf).decode()
