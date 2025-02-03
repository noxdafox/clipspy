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

"""This module contains the definition of:

  * Classes namespace class
  * Class class
  * Instance class
  * ClassSlot class
  * MessageHandler class
  * DefinedInstances class

"""

import os

import clips

from clips.modules import Module
from clips.common import PutSlotError, PUT_SLOT_ERROR
from clips.common import CLIPSError, SaveMode, ClassDefaultMode
from clips.common import environment_builder, environment_modifier

from clips._clips import lib, ffi


class Instance:
    """A Class Instance is an occurrence of an object.

    A Class Instance represents its data as a dictionary
    where each slot name is a key.

    Class Instance slot values can be modified.
    The Instance will be re-evaluated against the rule network once modified.

    """

    __slots__ = '_env', '_ist'

    def __init__(self, env: ffi.CData, ist: ffi.CData):
        self._env = env
        self._ist = ist
        lib.RetainInstance(self._ist)

    def __del__(self):
        try:
            lib.ReleaseInstance(self._ist)
        except (AttributeError, TypeError):
            pass  # mostly happening during interpreter shutdown

    def __hash__(self):
        return hash(self._ist)

    def __eq__(self, ist):
        return self._ist == ist._ist

    def __str__(self):
        return ' '.join(instance_pp_string(self._env, self._ist).split())

    def __repr__(self):
        string = ' '.join(instance_pp_string(self._env, self._ist).split())

        return "%s: %s" % (self.__class__.__name__, string)

    def __iter__(self):
        slot_names = (s.name for s in self.instance_class.slots())

        return ((n, slot_value(self._env, self._ist, n)) for n in slot_names)

    def __getitem__(self, slot):
        return slot_value(self._env, self._ist, slot)

    @property
    def name(self) -> str:
        """Instance name."""
        return ffi.string(lib.InstanceName(self._ist)).decode()

    @property
    def instance_class(self) -> 'Class':
        """Instance class."""
        defclass = lib.InstanceClass(self._ist)
        name = ffi.string(lib.DefclassName(defclass)).decode()

        return Class(self._env, name)

    def modify_slots(self, **slots):
        """Modify one or more slot values of the Instance.

        Instance must exist within the CLIPS engine.

        Equivalent to the CLIPS (modify-instance) function.

        """
        modifier = environment_modifier(self._env, 'instance')
        ret = lib.IMSetInstance(modifier, self._ist)
        if ret != lib.IME_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        for slot, slot_val in slots.items():
            value = clips.values.clips_value(self._env, value=slot_val)

            ret = lib.IMPutSlot(modifier, str(slot).encode(), value)
            if ret != PutSlotError.PSE_NO_ERROR:
                raise PUT_SLOT_ERROR[ret](slot)

        if lib.IMModify(modifier) is ffi.NULL:
            raise CLIPSError(self._env, code=lib.IMError(self._env))

    def send(self, message: str, arguments: str = None) -> type:
        """Send a message to the Instance.

        The output value of the message handler is returned.

        Equivalent to the CLIPS (send) function.

        """
        output = clips.values.clips_value(self._env)
        instance = clips.values.clips_value(self._env, value=self)

        args = arguments.encode() if arguments is not None else ffi.NULL
        lib.Send(self._env, instance, message.encode(), args, output)

        return clips.values.python_value(self._env, output)

    def delete(self):
        """Directly delete the instance."""
        ret = lib.DeleteInstance(self._ist)
        if ret != lib.UIE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

    def unmake(self):
        """This method is equivalent to delete except that it uses
        message-passing instead of directly deleting the instance.

        """
        ret = lib.UnmakeInstance(self._ist)
        if ret != lib.UIE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)


class Class:
    """A Class is a template for creating instances of objects.

    In CLIPS, Classes are defined via the (defclass) statement.

    Classes allow to create new instances
    to be added within the CLIPS environment.

    """

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, cls):
        return self._ptr() == cls._ptr()

    def __str__(self):
        string = lib.DefclassPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefclassPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        cls = lib.FindDefclass(self._env, self._name)
        if cls == ffi.NULL:
            raise CLIPSError(self._env, 'Class <%s> not defined' % self.name)

        return cls

    @property
    def abstract(self) -> bool:
        """True if the class is abstract."""
        return lib.ClassAbstractP(self._ptr())

    @property
    def reactive(self) -> bool:
        """True if the class is reactive."""
        return lib.ClassReactiveP(self._ptr())

    @property
    def name(self) -> str:
        """Class name."""
        return ffi.string(lib.DefclassName(self._ptr())).decode()

    @property
    def module(self) -> Module:
        """The module in which the Class is defined.

        Equivalent to the CLIPS (defclass-module) function.

        """
        name = ffi.string(lib.DefclassModule(self._ptr())).decode()

        return Module(self._env, name)

    @property
    def deletable(self) -> bool:
        """True if the Class can be deleted."""
        return lib.DefclassIsDeletable(self._ptr())

    @property
    def watch_instances(self) -> bool:
        """Whether or not the Class Instances are being watched."""
        return lib.DefclassGetWatchInstances(self._ptr())

    @watch_instances.setter
    def watch_instances(self, flag: bool):
        """Whether or not the Class Instances are being watched."""
        lib.DefclassSetWatchInstances(self._ptr(), flag)

    @property
    def watch_slots(self) -> bool:
        """Whether or not the Class Slots are being watched."""
        return lib.DefclassGetWatchSlots(self._ptr())

    @watch_slots.setter
    def watch_slots(self, flag: bool):
        """Whether or not the Class Slots are being watched."""
        lib.DefclassSetWatchSlots(self._ptr(), flag)

    def make_instance(self, instance_name: str = None, **slots) -> Instance:
        """Make a new Instance from this Class.

        Equivalent to the CLIPS (make-instance) function.

        """
        builder = environment_builder(self._env, 'instance')
        ret = lib.IBSetDefclass(builder, lib.DefclassName(self._ptr()))
        if ret != lib.IBE_NO_ERROR:
            raise CLIPSError(self._env, code=ret)

        for slot, slot_val in slots.items():
            value = clips.values.clips_value(self._env, value=slot_val)

            ret = lib.IBPutSlot(builder, str(slot).encode(), value)
            if ret != PutSlotError.PSE_NO_ERROR:
                raise PUT_SLOT_ERROR[ret](slot)

        instance = lib.IBMake(
            builder, instance_name.encode()
            if instance_name is not None else ffi.NULL)
        if instance != ffi.NULL:
            return Instance(self._env, instance)
        else:
            raise CLIPSError(self._env, code=lib.FBError(self._env))

    def subclass(self, defclass: 'Class') -> bool:
        """True if the Class is a subclass of the given one."""
        return lib.SubclassP(self._ptr(), defclass._ptr())

    def superclass(self, defclass: 'Class') -> bool:
        """True if the Class is a superclass of the given one."""
        return lib.SuperclassP(self._ptr(), defclass._ptr())

    def slots(self, inherited: bool = False) -> iter:
        """Iterate over the Slots of the class."""
        value = clips.values.clips_value(self._env)

        lib.ClassSlots(self._ptr(), value, inherited)

        return (ClassSlot(self._env, self.name, n)
                for n in clips.values.python_value(self._env, value))

    def instances(self) -> iter:
        """Iterate over the instances of the class."""
        ist = lib.GetNextInstanceInClass(self._ptr(), ffi.NULL)

        while ist != ffi.NULL:
            yield Instance(self._env, ist)

            ist = lib.GetNextInstanceInClass(self._ptr(), ist)

    def subclasses(self, inherited: bool = False) -> iter:
        """Iterate over the subclasses of the class.

        Equivalent to the CLIPS (class-subclasses) function.

        """
        value = clips.values.clips_value(self._env)

        lib.ClassSubclasses(self._ptr(), value, inherited)

        for defclass in classes(
                self._env, clips.values.python_value(self._env, value)):
            yield defclass

    def superclasses(self, inherited=False) -> iter:
        """Iterate over the superclasses of the class.

        Equivalent to the CLIPS class-superclasses command.

        """
        value = clips.values.clips_value(self._env)

        lib.ClassSuperclasses(self._ptr(), value, int(inherited))

        for defclass in classes(
                self._env, clips.values.python_value(self._env, value)):
            yield defclass

    def message_handlers(self) -> iter:
        """Iterate over the message handlers of the class."""
        index = lib.GetNextDefmessageHandler(self._ptr(), 0)

        while index != 0:
            yield MessageHandler(self._env, self.name, index)

            index = lib.GetNextDefmessageHandler(self._ptr(), index)

    def find_message_handler(
            self, name: str, handler_type: str = 'primary') -> 'MessageHandler':
        """Returns the MessageHandler given its name and type."""
        ident = lib.FindDefmessageHandler(
            self._ptr(), name.encode(), handler_type.encode())
        if ident == 0:
            raise CLIPSError(self._env)

        return MessageHandler(self._env, self.name, ident)

    def undefine(self):
        """Undefine the Class.

        Equivalent to the CLIPS (undefclass) command.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefclass(self._ptr(), self._env):
            raise CLIPSError(self._env)


class ClassSlot:
    """A Class Instances organize the information within Slots.

    Slots might restrict the type or amount of data they store.

    """

    __slots__ = '_env', '_cls', '_name'

    def __init__(self, env: ffi.CData, cls: str, name: str):
        self._env = env
        self._cls = cls.encode()
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr()) + hash(self._name)

    def __eq__(self, cls):
        return self._ptr() == cls._ptr() and self._name == cls._name

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    def _ptr(self) -> ffi.CData:
        cls = lib.FindDefclass(self._env, self._cls)
        if cls == ffi.NULL:
            raise CLIPSError(
                self._env, 'Class <%s> not defined' % self._cls.decode())

        return cls

    @property
    def name(self):
        """The Slot name."""
        return self._name.decode()

    @property
    def public(self) -> bool:
        """True if the Slot is public."""
        return lib.SlotPublicP(self._ptr(), self._name)

    @property
    def initializable(self) -> bool:
        """True if the Slot is initializable."""
        return lib.SlotInitableP(self._ptr(), self._name)

    @property
    def writable(self) -> bool:
        """True if the Slot is writable."""
        return lib.SlotWritableP(self._ptr(), self._name)

    @property
    def accessible(self) -> bool:
        """True if the Slot is directly accessible."""
        return lib.SlotDirectAccessP(self._ptr(), self._name)

    @property
    def types(self) -> tuple:
        """A tuple containing the value types for this Slot.

        Equivalent to the CLIPS (slot-types) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotTypes(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def sources(self) -> tuple:
        """A tuple containing the names of the Class sources for this Slot.

        Equivalent to the CLIPS (slot-sources) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotSources(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def range(self) -> tuple:
        """A tuple containing the numeric range for this Slot.

        Equivalent to the CLIPS (slot-range) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotRange(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def facets(self) -> tuple:
        """A tuple containing the facets for this Slot.

        Equivalent to the CLIPS (slot-facets) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotFacets(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def cardinality(self) -> tuple:
        """A tuple containing the cardinality for this Slot.

        Equivalent to the CLIPS slot-cardinality function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotCardinality(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def default_value(self) -> type:
        """The default value for this Slot.

        Equivalent to the CLIPS (slot-default-value) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotDefaultValue(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    @property
    def allowed_values(self) -> tuple:
        """A tuple containing the allowed values for this Slot.

        Equivalent to the CLIPS (slot-allowed-values) function.

        """
        value = clips.values.clips_value(self._env)

        if lib.SlotAllowedValues(self._ptr(), self._name, value):
            return clips.values.python_value(self._env, value)
        else:
            raise CLIPSError(self._env)

    def allowed_classes(self) -> iter:
        """Iterate over the allowed classes for this slot.

        Equivalent to the CLIPS (slot-allowed-classes) function.

        """
        value = clips.values.clips_value(self._env)

        lib.SlotAllowedClasses(self._ptr(), self._name, value)

        if isinstance(value, tuple):
            for defclass in classes(self._env, value):
                yield defclass


class MessageHandler:
    """MessageHandlers are the CLIPS equivalent of instance methods in Python.

    """

    __slots__ = '_env', '_cls', '_idx'

    def __init__(self, env: ffi.CData, cls: str, idx: int):
        self._env = env
        self._cls = cls.encode()
        self._idx = idx

    def __hash__(self):
        return hash(self._ptr()) + self._idx

    def __eq__(self, cls):
        return self._ptr() == cls._ptr() and self._idx == cls._idx

    def __str__(self):
        string = lib.DefmessageHandlerPPForm(self._ptr(), self._idx)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefmessageHandlerPPForm(self._ptr(), self._idx)
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        cls = lib.FindDefclass(self._env, self._cls)
        if cls == ffi.NULL:
            raise CLIPSError(
                self._env, 'Class <%s> not defined' % self._cls.decode())

        return cls

    @property
    def name(self) -> str:
        """MessageHandler name."""
        return ffi.string(lib.DefmessageHandlerName(
            self._ptr(), self._idx)).decode()

    @property
    def type(self) -> str:
        """MessageHandler type."""
        return ffi.string(lib.DefmessageHandlerType(
            self._ptr(), self._idx)).decode()

    @property
    def watch(self) -> bool:
        """True if the MessageHandler is being watched."""
        return lib.DefmessageHandlerGetWatch(self._ptr(), self._idx)

    @watch.setter
    def watch(self, flag: bool):
        """True if the MessageHandler is being watched."""
        lib.DefmessageHandlerSetWatch(self._ptr(), self._idx, flag)

    @property
    def deletable(self) -> bool:
        """True if the MessageHandler can be deleted."""
        return lib.DefmessageHandlerIsDeletable(self._ptr(), self._idx)

    def undefine(self):
        """Undefine the MessageHandler.

        Equivalent to the CLIPS (undefmessage-handler) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.UndefmessageHandler(self._ptr(), self._idx, self._env):
            raise CLIPSError(self._env)


class DefinedInstances:
    """The DefinedInstances constitute a set of a priori
    or initial knowledge specified as a collection of instances of user
    defined classes.

    When the CLIPS environment is reset, every instance specified
    within a definstances construct in the CLIPS knowledge base
    is added to the DefinedInstances list.

    """

    __slots__ = '_env', '_name'

    def __init__(self, env: ffi.CData, name: str):
        self._env = env
        self._name = name.encode()

    def __hash__(self):
        return hash(self._ptr())

    def __eq__(self, dis):
        return self._ptr() == dis._ptr()

    def __str__(self):
        string = lib.DefinstancesPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return ' '.join(string.split())

    def __repr__(self):
        string = lib.DefinstancesPPForm(self._ptr())
        string = ffi.string(string).decode() if string != ffi.NULL else ''

        return "%s: %s" % (self.__class__.__name__, ' '.join(string.split()))

    def _ptr(self) -> ffi.CData:
        dfc = lib.FindDefinstances(self._env, self._name)
        if dfc == ffi.NULL:
            raise CLIPSError(
                self._env, 'DefinedInstances <%s> not defined' % self.name)

        return dfc

    @property
    def name(self) -> str:
        """The DefinedInstances name."""
        return self._name.decode()

    @property
    def module(self) -> Module:
        """The module in which the DefinedInstances is defined.

        Python equivalent of the CLIPS (definstances-module) command.

        """
        name = ffi.string(lib.DefinstancesModule(self._ptr())).decode()

        return Module(self._env, name)

    @property
    def deletable(self) -> bool:
        """True if the DefinedInstances can be undefined."""
        return lib.DefinstancesIsDeletable(self._ptr())

    def undefine(self):
        """Undefine the DefinedInstances.

        Equivalent to the CLIPS (undefinstances) function.

        The object becomes unusable after this method has been called.

        """
        if not lib.Undefinstances(self._ptr(), self._env):
            raise CLIPSError(self._env)


class Classes:
    """Classes and Instances namespace class.

    .. note::

       All the Classes methods are accessible through the Environment class.

    """

    __slots__ = ['_env']

    def __init__(self, env: ffi.CData):
        self._env = env

    @property
    def default_mode(self) -> ClassDefaultMode:
        """Return the current class defaults mode.

        Equivalent to the CLIPS (get-class-defaults-mode) function.

        """
        return ClassDefaultMode(lib.GetClassDefaultsMode(self._env))

    @default_mode.setter
    def default_mode(self, value: ClassDefaultMode):
        """Return the current class defaults mode.

        Equivalent to the CLIPS (get-class-defaults-mode) command.

        """
        lib.SetClassDefaultsMode(self._env, value)

    @property
    def instances_changed(self) -> bool:
        """True if any instance has changed since last check."""
        value = lib.GetInstancesChanged(self._env)
        lib.SetInstancesChanged(self._env, False)

        return value

    def classes(self) -> iter:
        """Iterate over the defined Classes."""
        defclass = lib.GetNextDefclass(self._env, ffi.NULL)

        while defclass != ffi.NULL:
            name = ffi.string(lib.DefclassName(defclass)).decode()
            yield Class(self._env, name)

            defclass = lib.GetNextDefclass(self._env, defclass)

    def find_class(self, name: str) -> Class:
        """Find the Class by the given name."""
        defclass = lib.FindDefclass(self._env, name.encode())
        if defclass == ffi.NULL:
            raise LookupError("Class '%s' not found" % name)

        return Class(self._env, name)

    def defined_instances(self) -> iter:
        """Iterate over the DefinedInstances."""
        definstances = lib.GetNextDefinstances(self._env, ffi.NULL)
        while definstances != ffi.NULL:
            name = ffi.string(lib.DefinstancesName(definstances)).decode()
            yield DefinedInstances(self._env, name)

            definstances = lib.GetNextDefinstances(self._env, definstances)

    def find_defined_instances(self, name: str) -> DefinedInstances:
        """Find the DefinedInstances by its name."""
        dfs = lib.FindDefinstances(self._env, name.encode())
        if dfs == ffi.NULL:
            raise LookupError("DefinedInstances '%s' not found" % name)

        return DefinedInstances(self._env, name)

    def instances(self) -> iter:
        """Iterate over the defined Instancees."""
        definstance = lib.GetNextInstance(self._env, ffi.NULL)

        while definstance != ffi.NULL:
            yield Instance(self._env, definstance)

            definstance = lib.GetNextInstance(self._env, definstance)

    def find_instance(self, name: str, module: Module = None) -> Instance:
        """Find the Instance by the given name."""
        module = module._mdl if module is not None else ffi.NULL
        definstance = lib.FindInstance(self._env, module, name.encode(),
                                       ClassDefaultMode.CONSERVATION_MODE)
        if definstance == ffi.NULL:
            raise LookupError("Instance '%s' not found" % name)

        return Instance(self._env, definstance)

    def load_instances(self, instances: str) -> int:
        """Load a set of instances into the CLIPS data base.

        Equivalent to the CLIPS (load-instances) function.

        Instances can be loaded from a string, a file or a binary file.

        """
        instances = instances.encode()

        if os.path.exists(instances):
            try:
                return self._load_instances_binary(instances)
            except CLIPSError:
                return self._load_instances_text(instances)
        else:
            return self._load_instances_string(instances)

    def _load_instances_binary(self, instances: str) -> int:
        ret = lib.BinaryLoadInstances(self._env, instances)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret

    def _load_instances_text(self, instances: str) -> int:
        ret = lib.LoadInstances(self._env, instances)
        if ret == -1:
            raise CLIPSError(self._env)

        return ret

    def _load_instances_string(self, instances: str) -> int:
        ret = lib.LoadInstancesFromString(self._env, instances, len(instances))
        if ret == -1:
            raise CLIPSError(self._env)

        return ret

    def restore_instances(self, instances: str) -> int:
        """Restore a set of instances into the CLIPS data base.

        Equivalent to the CLIPS (restore-instances) function.

        Instances can be passed as a set of strings or as a file.

        """
        instances = instances.encode()

        if os.path.exists(instances):
            ret = lib.RestoreInstances(self._env, instances)
            if ret == -1:
                raise CLIPSError(self._env)
        else:
            ret = lib.RestoreInstancesFromString(
                self._env, instances, len(instances))
            if ret == -1:
                raise CLIPSError(self._env)

        return ret

    def save_instances(self, path: str, binary: bool = False,
                       mode: SaveMode = SaveMode.LOCAL_SAVE) -> int:
        """Save the instances in the system to the specified file.

        If binary is True, the instances will be saved in binary format.

        Equivalent to the CLIPS (save-instances) function.

        """
        if binary:
            ret = lib.BinarySaveInstances(self._env, path.encode(), mode)
        else:
            ret = lib.SaveInstances(self._env, path.encode(), mode)
        if ret == 0:
            raise CLIPSError(self._env)

        return ret


def slot_value(env: ffi.CData, ist: ffi.CData, slot: str) -> type:
    value = clips.values.clips_value(env)

    ret = lib.DirectGetSlot(ist, slot.encode(), value)
    if ret != lib.GSE_NO_ERROR:
        raise CLIPSError(env, code=ret)

    return clips.values.python_value(env, value)


def classes(env: ffi.CData, names: (list, tuple)) -> iter:
    for name in names:
        defclass = lib.FindDefclass(env, name.encode())
        if defclass == ffi.NULL:
            raise CLIPSError(env)

        yield Class(env, name)


def instance_pp_string(env: ffi.CData, ist: ffi.CData) -> str:
    builder = environment_builder(env, 'string')
    lib.SBReset(builder)
    lib.InstancePPForm(ist, builder)

    return ffi.string(builder.contents).decode()
