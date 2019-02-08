import os
import unittest
from tempfile import mkstemp

from clips import Environment, Symbol, InstanceName
from clips import CLIPSError, ClassDefaultMode, LoggingRouter


DEFCLASSES = [
    """
    (defclass AbstractClass (is-a USER)
      (role abstract))
    """,
    """(defclass InheritClass (is-a AbstractClass))""",
    """
    (defclass ConcreteClass (is-a USER)
      (slot Slot (type SYMBOL) (allowed-values value another-value)))
    """,
    """
    (defclass MessageHandlerClass (is-a USER)
      (slot One)
      (slot Two))
    """,
    """
    (defmessage-handler MessageHandlerClass test-handler ()
      (+ ?self:One ?self:Two))
    """
]


class TempFile:
    """Cross-platform temporary file."""
    name = None

    def __enter__(self):
        fobj, self.name = mkstemp()
        os.close(fobj)

        return self

    def __exit__(self, *_):
        os.remove(self.name)


class TestClasses(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        router = LoggingRouter()
        router.add_to_environment(self.env)
        for defclass in DEFCLASSES:
            self.env.build(defclass)

    def test_classes(self):
        """Classes wrapper test."""
        self.assertEqual(
            self.env.default_mode, ClassDefaultMode.CONVENIENCE_MODE)
        self.env.default_mode = ClassDefaultMode.CONSERVATION_MODE
        self.assertEqual(
            self.env.default_mode, ClassDefaultMode.CONSERVATION_MODE)

        defclass = self.env.find_class('USER')
        self.assertTrue(defclass in self.env.classes())

        with self.assertRaises(LookupError):
            self.env.find_class('NonExisting')

        defclass = self.env.find_class('ConcreteClass')

        defclass.make_instance('some-instance')
        defclass.make_instance('test-instance')

        instance = self.env.find_instance('test-instance')
        self.assertTrue(instance in self.env.instances())

        with self.assertRaises(LookupError):
            self.env.find_instance('non-existing-instance')

        self.assertTrue(self.env.instances_changed)
        self.assertFalse(self.env.instances_changed)

        with TempFile() as tmp:
            saved = self.env.save_instances(tmp.name)
            self.env.reset()
            loaded = self.env.load_instances(tmp.name)
            self.assertEqual(saved, loaded)

        with TempFile() as tmp:
            saved = self.env.save_instances(tmp.name)
            self.env.reset()
            loaded = self.env.restore_instances(tmp.name)
            self.assertEqual(saved, loaded)

        with TempFile() as tmp:
            saved = self.env.save_instances(tmp.name, binary=True)
            self.env.reset()
            loaded = self.env.load_instances(tmp.name)
            self.assertEqual(saved, loaded)

    def test_abstract_class(self):
        """Abstract class test."""
        superclass = self.env.find_class('USER')
        subclass = self.env.find_class('InheritClass')
        defclass = self.env.find_class('AbstractClass')

        self.assertTrue(defclass.abstract)
        self.assertFalse(defclass.reactive)
        self.assertEqual(defclass.name, 'AbstractClass')
        self.assertEqual(defclass.module.name, 'MAIN')
        self.assertTrue(defclass.deletable)
        self.assertTrue(defclass.subclass(superclass))
        self.assertTrue(defclass.superclass(subclass))
        self.assertEqual(tuple(defclass.subclasses()), (subclass, ))
        self.assertEqual(tuple(defclass.superclasses()), (superclass, ))

        with self.assertRaises(CLIPSError):
            defclass.make_instance('foobar')

        defclass.undefine()

    def test_concrete_class(self):
        """Concrete class test."""
        defclass = self.env.find_class('ConcreteClass')

        self.assertFalse(defclass.abstract)
        self.assertTrue(defclass.reactive)
        self.assertEqual(defclass.name, 'ConcreteClass')
        self.assertEqual(defclass.module.name, 'MAIN')
        self.assertTrue(defclass.deletable)

        self.assertFalse(defclass.watch_instances)
        defclass.watch_instances = True
        self.assertTrue(defclass.watch_instances)

        self.assertFalse(defclass.watch_slots)
        defclass.watch_slots = True
        self.assertTrue(defclass.watch_slots)

        defclass.undefine()

    def test_slot(self):
        """Slot test."""
        defclass = self.env.find_class('ConcreteClass')

        slot = tuple(defclass.slots())[0]

        self.assertFalse(slot.public)
        self.assertTrue(slot.writable)
        self.assertTrue(slot.accessible)
        self.assertTrue(slot.initializable)
        self.assertEqual(slot.name, 'Slot')
        self.assertEqual(slot.types, ('SYMBOL', ))
        self.assertEqual(slot.sources, (defclass.name, ))
        self.assertEqual(slot.range, Symbol('FALSE'))
        self.assertEqual(slot.facets, ('SGL', 'STC', 'INH', 'RW', 'LCL', 'RCT',
                                       'EXC', 'PRV', 'RW', 'put-Slot'))
        self.assertEqual(slot.cardinality, ())
        self.assertEqual(slot.default_value, Symbol('value'))
        self.assertEqual(slot.allowed_values, ('value', 'another-value'))
        self.assertEqual(tuple(slot.allowed_classes()), ())

    def test_make_instance(self):
        """Instance test."""
        defclass = self.env.find_class('ConcreteClass')

        instance_name = self.env.eval(
            '(make-instance test-name-instance of ConcreteClass)')
        self.assertEqual(instance_name, 'test-name-instance')
        self.assertTrue(isinstance(instance_name, InstanceName))

        defclass.make_instance('some-instance')
        instance = defclass.make_instance('test-instance', Slot=Symbol('value'))

        self.assertTrue(instance in defclass.instances())
        self.assertEqual(instance.name, 'test-instance')
        self.assertEqual(instance.instance_class, defclass)
        self.assertEqual(instance['Slot'], Symbol('value'))
        self.assertEqual(
            str(instance), '[test-instance] of ConcreteClass (Slot value)')
        self.assertEqual(
            repr(instance),
            'Instance: [test-instance] of ConcreteClass (Slot value)')
        self.assertEqual(dict(instance), {'Slot': Symbol('value')})

        instance.delete()

        with self.assertRaises(LookupError):
            self.env.find_instance('test-instance')

        instance = defclass.make_instance('test-instance')

        instance.unmake()

        with self.assertRaises(LookupError):
            self.env.find_instance('test-instance')

    def test_make_instance_errors(self):
        """Instance errors."""
        defclass = self.env.find_class('ConcreteClass')

        with self.assertRaises(KeyError):
            defclass.make_instance('some-instance', NonExistingSlot=1)
        with self.assertRaises(TypeError):
            defclass.make_instance('some-instance', Slot="wrong type")
        with self.assertRaises(ValueError):
            defclass.make_instance('some-instance', Slot=Symbol('wrong-value'))

    def test_modify_instance(self):
        """Instance slot modification test."""
        defclass = self.env.find_class('ConcreteClass')

        defclass.make_instance('some-instance')
        instance = defclass.make_instance('test-instance', Slot=Symbol('value'))
        instance.modify_slots(Slot=Symbol('another-value'))

        self.assertEqual(instance['Slot'], Symbol('another-value'))

        instance.delete()

    def test_message_handler(self):
        """MessageHandler test."""
        defclass = self.env.find_class('MessageHandlerClass')

        handler = defclass.find_message_handler('test-handler')

        expected_str = "(defmessage-handler MAIN::MessageHandlerClass " + \
            "test-handler () (+ ?self:One ?self:Two))"

        self.assertTrue(handler.deletable)
        self.assertEqual(handler.type, 'primary')
        self.assertEqual(handler.name, 'test-handler')
        self.assertTrue(handler in defclass.message_handlers())

        self.assertEqual(str(handler), expected_str)
        self.assertEqual(repr(handler), 'MessageHandler: ' + expected_str)

        self.assertFalse(handler.watch)
        handler.watch = True
        self.assertTrue(handler.watch)

        handler.undefine()

    def test_message_handler_instance(self):
        """MessageHandler instance test."""
        defclass = self.env.find_class('MessageHandlerClass')

        instance = defclass.make_instance('test-instance', One=1, Two=2)

        self.assertEqual(instance.send('test-handler'), 3)
