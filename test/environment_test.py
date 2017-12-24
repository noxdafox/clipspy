import unittest
from tempfile import NamedTemporaryFile

from clips import Environment, Symbol, LoggingRouter, ImpliedFact


DEFRULE_FACT = """
(defrule fact-rule
   ?fact <- (test-fact)
   =>
   (python_method ?fact))
"""

DEFRULE_INSTANCE = """
(defrule instance-rule
   ?instance <- (object (is-a TEST))
   =>
   (python_method ?instance))
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


class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.value = None
        self.env = Environment()
        router = LoggingRouter()
        router.add_to_environment(self.env)
        self.env.define_function(python_function)
        self.env.define_function(python_types)
        self.env.define_function(self.python_method)
        self.env.define_function(self.python_fact_method)
        self.env.build(DEFCLASS)
        self.env.build(DEFFUNCTION)
        self.env.build(DEFRULE_FACT)
        self.env.build(DEFRULE_INSTANCE)

    def python_method(self, *value):
        self.value = value

    def python_fact_method(self):
        """Returns a list with one fact."""
        template = self.env.find_template('test-fact')
        fact = template.new_fact()
        fact.append(5)

        return [fact]

    def test_eval_python_function(self):
        """Python function is evaluated correctly."""
        expected = [0, 1.1, "2", Symbol('three')]
        ret = self.env.eval('(python_function 0 1.1 "2" three)')
        self.assertEqual(ret, expected)

        expected = [Symbol('nil'), Symbol('TRUE'), Symbol('FALSE')]
        ret = self.env.eval('(python_types)')
        self.assertEqual(ret, expected)

    def test_eval_python_method(self):
        """Python method is evaluated correctly."""
        expected = 0, 1.1, "2", Symbol('three')

        ret = self.env.eval('(python_method 0 1.1 "2" three)')

        self.assertEqual(ret, Symbol('nil'))
        self.assertEqual(self.value, expected)

    def test_rule_python_fact(self):
        """Facts are forwarded to Python """
        fact = self.env.assert_string('(test-fact)')
        self.env.run()

        self.assertEqual(self.value[0], fact)

    def test_rule_python_instance(self):
        """Instances are forwarded to Python """
        cl = self.env.find_class('TEST')
        inst = cl.new_instance('test')
        self.env.run()

        self.assertEqual(self.value[0], inst)

    def test_facts_function(self):
        """Python functions can return list of facts"""
        function = self.env.find_function('test-fact-function')
        function()

        self.assertTrue(isinstance(self.value[0], ImpliedFact))

    def test_batch_star(self):
        """Commands are evaluated from file."""
        with NamedTemporaryFile() as tmp:
            tmp.write(b"(assert (test-fact))\n")
            tmp.flush()

            self.env.batch_star(tmp.name)

        self.assertTrue(
            'test-fact' in (f.template.name for f in self.env.facts()))

    def test_save_load(self):
        """Constructs are saved and loaded."""
        with NamedTemporaryFile() as tmp:
            self.env.save(tmp.name)
            self.env.clear()
            self.env.load(tmp.name)

            self.assertTrue('fact-rule' in
                            (r.name for r in self.env.rules()))

        with NamedTemporaryFile() as tmp:
            self.env.save(tmp.name, binary=True)
            self.env.clear()
            self.env.load(tmp.name)

            self.assertTrue('fact-rule' in
                            (r.name for r in self.env.rules()))
