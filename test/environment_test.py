import os
import unittest
from tempfile import mkstemp

from clips import CLIPSError
from clips import Environment, Symbol, LoggingRouter, ImpliedFact, InstanceName

DEFRULE_FACT = """
(defrule fact-rule
   ?fact <- (test-fact)
   =>
   (python_method ?fact))
"""

DEFRULE_INSTANCE = """
(defrule instance-rule
   ?instance <- (object (is-a TEST)
                        (name ?instance-name))
   =>
   (python_method ?instance)
   (python_method ?instance-name))
"""

DEFFUNCTION = """
(deffunction test-fact-function ()
   (bind ?facts (python_fact_method))
   (python_method ?facts))
"""

DEFCLASS = """(defclass TEST (is-a USER))"""


def python_function(*value):
    return value


def python_types():
    return None, True, False


def python_objects(obj):
    return obj


def python_error():
    raise Exception("BOOM!")


class TempFile:
    """Cross-platform temporary file."""
    name = None

    def __enter__(self):
        fobj, self.name = mkstemp()
        os.close(fobj)

        return self

    def __exit__(self, *_):
        os.remove(self.name)


class ObjectTest:
    def __init__(self, value):
        self.value = value


class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.values = []
        self.env = Environment()
        self.env.add_router(LoggingRouter())
        self.env.define_function(python_function)
        self.env.define_function(python_function,
                                 name='python-function-renamed')
        self.env.define_function(python_error)
        self.env.define_function(python_types)
        self.env.define_function(python_objects)
        self.env.define_function(self.python_method)
        self.env.define_function(self.python_fact_method)
        self.env.build(DEFCLASS)
        self.env.build(DEFFUNCTION)
        self.env.build(DEFRULE_FACT)
        self.env.build(DEFRULE_INSTANCE)

    def tearDown(self):
        for router in tuple(self.env.routers()):
            router.delete()

    def python_method(self, *values):
        self.values += values

    def python_fact_method(self):
        """Returns a list with one fact."""
        return [self.env.assert_string('(test-fact 5)')]

    def test_eval_python_function(self):
        """Python function is evaluated correctly."""
        expected = (0, 1.1, "2", Symbol('three'), InstanceName('four'))
        ret = self.env.eval('(python_function 0 1.1 "2" three [four])')
        self.assertEqual(ret, expected)

        expected = (0, 1.1, "2", Symbol('three'))
        ret = self.env.eval('(python-function-renamed 0 1.1 "2" three)')
        self.assertEqual(ret, expected)

        expected = (Symbol('nil'), Symbol('TRUE'), Symbol('FALSE'))
        ret = self.env.eval('(python_types)')
        self.assertEqual(ret, expected)

    def test_eval_python_error(self):
        """Errors in Python functions are correctly set."""
        self.assertIsNone(self.env.error_state)

        with self.assertRaises(CLIPSError):
            self.env.eval('(python_error)')
        self.assertTrue("[PYCODEFUN1]" in str(self.env.error_state))

        self.env.clear_error_state()
        self.assertIsNone(self.env.error_state)

    def test_eval_python_method(self):
        """Python method is evaluated correctly."""
        expected = [0, 1.1, "2", Symbol('three')]

        ret = self.env.eval('(python_method 0 1.1 "2" three)')

        self.assertEqual(ret, Symbol('nil'))
        self.assertEqual(self.values, expected)

    def test_call_python_object(self):
        """Python objects are correctly marshalled."""
        test_object = ObjectTest(42)

        ret = self.env.call('python_objects', test_object)

        self.assertEqual(ret, test_object)

    def test_call_python_unhashable(self):
        """Unhashable objects are correctly marshalled."""
        from collections.abc import Hashable
        test_dict = {'test': 'passed'}
        self.assertNotIsInstance(test_dict, Hashable)

        ret = self.env.call('python_objects', test_dict)

        self.assertEqual(ret, test_dict)

    def test_rule_python_fact(self):
        """Facts are forwarded to Python """
        fact = self.env.assert_string('(test-fact)')
        self.env.run()

        self.assertEqual(self.values[0], fact)

    def test_rule_python_instance(self):
        """Instances are forwarded to Python """
        defclass = self.env.find_class('TEST')
        inst = defclass.make_instance('test')
        self.env.run()

        self.assertEqual(self.values[0], inst)
        self.assertEqual(self.values[1], inst.name)

    def test_facts_function(self):
        """Python functions can return list of facts"""
        function = self.env.find_function('test-fact-function')
        function()

        self.assertTrue(isinstance(self.values[0], ImpliedFact))

    def test_batch_star(self):
        """Commands are evaluated from file."""
        with TempFile() as tmp:
            with open(tmp.name, 'wb') as tmpfile:
                tmpfile.write(b"(assert (test-fact))\n")

            self.env.batch_star(tmp.name)

        self.assertTrue(
            'test-fact' in (f.template.name for f in self.env.facts()))

    def test_save_load(self):
        """Constructs are saved and loaded."""
        with TempFile() as tmp:
            self.env.save(tmp.name)
            self.env.clear()
            self.env.load(tmp.name)

            self.assertTrue('fact-rule' in
                            (r.name for r in self.env.rules()))

        with TempFile() as tmp:
            self.env.save(tmp.name, binary=True)
            self.env.clear()
            self.env.load(tmp.name, binary=True)

            self.assertTrue('fact-rule' in
                            (r.name for r in self.env.rules()))
