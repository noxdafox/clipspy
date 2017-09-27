import unittest
from tempfile import NamedTemporaryFile

from clips import Environment, Symbol
from clips import CLIPSError, ClassDefaultMode, LoggingRouter


DEFCLASSES = [
    """
    (defclass AbstractClass (is-a USER)
      (role abstract))
    """,
    """(defclass InheritClass (is-a AbstractClass))""",
    """
    (defclass ConcreteClass (is-a USER)
      (slot Slot))
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
            self.env.classes.default_mode, ClassDefaultMode.CONVENIENCE_MODE)
        self.env.classes.default_mode = ClassDefaultMode.CONSERVATION_MODE
        self.assertEqual(
            self.env.classes.default_mode, ClassDefaultMode.CONSERVATION_MODE)

        defclass = self.env.classes.find_class('USER')
        self.assertTrue(defclass in self.env.classes.classes())

        with self.assertRaises(LookupError):
            self.env.classes.find_class('NonExisting')

        defclass = self.env.classes.find_class('ConcreteClass')

        defclass.new_instance('some-instance')
        defclass.new_instance('test-instance')

        instance = self.env.classes.find_instance('test-instance')
        self.assertTrue(instance in self.env.classes.instances())

        with self.assertRaises(LookupError):
            self.env.classes.find_instance('NonExisting')

        self.assertTrue(self.env.classes.instances_changed)
        self.assertFalse(self.env.classes.instances_changed)

        # See: https://sourceforge.net/p/clipsrules/tickets/33/
        # with NamedTemporaryFile(buffering=0, delete=False) as tmp:
        #     saved = self.env.classes.save_instances(tmp.name)
        #     self.env.reset()
        #     loaded = self.env.classes.load_instances(tmp.name)
        #     self.assertEqual(saved, loaded)

        with NamedTemporaryFile() as tmp:
            saved = self.env.classes.save_instances(tmp.name)
            self.env.reset()
            loaded = self.env.classes.restore_instances(tmp.name)
            self.assertEqual(saved, loaded)

        with NamedTemporaryFile() as tmp:
            saved = self.env.classes.save_instances(tmp.name, binary=True)
            self.env.reset()
            loaded = self.env.classes.load_instances(tmp.name)
            self.assertEqual(saved, loaded)

    def test_abstract_class(self):
        """Abstract class test."""
        superclass = self.env.classes.find_class('USER')
        subclass = self.env.classes.find_class('InheritClass')
        defclass = self.env.classes.find_class('AbstractClass')

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
            defclass.new_instance('foobar')

        defclass.undefine()

    def test_concrete_class(self):
        """Concrete class test."""
        defclass = self.env.classes.find_class('ConcreteClass')

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
        defclass = self.env.classes.find_class('ConcreteClass')

        slot = tuple(defclass.slots())[0]

        self.assertFalse(slot.public)
        self.assertTrue(slot.writable)
        self.assertTrue(slot.accessible)
        self.assertTrue(slot.initializable)
        self.assertEqual(slot.name, 'Slot')
        self.assertEqual(slot.types, ('FLOAT', 'INTEGER', 'SYMBOL', 'STRING',
                                      'EXTERNAL-ADDRESS', 'FACT-ADDRESS',
                                      'INSTANCE-ADDRESS', 'INSTANCE-NAME'))
        self.assertEqual(slot.sources, (defclass.name, ))
        self.assertEqual(slot.range, ('-oo', '+oo'))
        self.assertEqual(slot.facets, ('SGL', 'STC', 'INH', 'RW', 'LCL', 'RCT',
                                       'EXC', 'PRV', 'RW', 'put-Slot'))
        self.assertEqual(slot.cardinality, ())
        self.assertEqual(slot.default_value, Symbol('nil'))
        self.assertEqual(slot.allowed_values, ())
        self.assertEqual(tuple(slot.allowed_classes()), ())

    def test_instance(self):
        """Instance test."""
        defclass = self.env.classes.find_class('ConcreteClass')

        defclass.new_instance('some-instance')
        instance = defclass.new_instance('test-instance')
        instance['Slot'] = Symbol('value')

        self.assertTrue(instance in defclass.instances())
        self.assertEqual(instance.name, 'test-instance')
        self.assertEqual(instance.instance_class, defclass)
        self.assertEqual(instance['Slot'], Symbol('value'))
        self.assertEqual(
            str(instance), '[test-instance] of ConcreteClass (Slot value)')
        self.assertEqual(
            repr(instance),
            'Instance: [test-instance] of ConcreteClass (Slot value)')

        instance.delete()

        instance = defclass.new_instance('test-instance')

        instance.unmake()

    def test_message_handler(self):
        """MessageHandler test."""
        defclass = self.env.classes.find_class('MessageHandlerClass')

        handler = defclass.find_message_handler('test-handler')

        expected_str = """(defmessage-handler MAIN::MessageHandlerClass test-handler
   ()
   (+ ?self:One ?self:Two))"""

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
        defclass = self.env.classes.find_class('MessageHandlerClass')

        instance = defclass.new_instance('test-instance')
        instance['One'] = 1
        instance['Two'] = 2

        self.assertEqual(instance.send('test-handler'), 3)
