import unittest

from clips import Environment, Symbol


DEFFUNCTION1 = """(deffunction function-sum (?a ?b) (+ ?a ?b))"""
DEFFUNCTION2 = """(deffunction function-sub (?a ?b) (- ?a ?b))"""
DEFGENERIC1 = """(defgeneric generic-sum)"""
DEFGENERIC2 = """(defgeneric generic-sub)"""
DEFMETHOD = """
(defmethod generic-sum ((?a INTEGER) (?b INTEGER)) (+ ?a ?b))
"""


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.env.build(DEFMETHOD)
        self.env.build(DEFGENERIC1)
        self.env.build(DEFGENERIC2)
        self.env.build(DEFFUNCTION1)
        self.env.build(DEFFUNCTION2)

    def test_function_call(self):
        """Test function call."""
        function = self.env.find_function('function-sum')
        self.assertEqual(function(1, 2), 3)

        function = self.env.find_generic('generic-sum')
        self.assertEqual(function(1, 2), 3)

        self.assertEqual(self.env.call('function-sum', 1, 2), 3)
        self.assertEqual(self.env.call('generic-sum', 1, 2), 3)

        self.assertEqual(
            self.env.call('create$', 1, 2.0, "three", Symbol('four')),
            (1, 2.0, 'three', 'four'))

    def test_function(self):
        """Deffunction object test."""
        func = self.env.find_function("function-sub")

        self.assertTrue(func in self.env.functions())

        self.assertEqual(func.name, "function-sub")
        self.assertEqual(func.module.name, "MAIN")
        self.assertTrue('deffunction' in str(func))
        self.assertTrue('deffunction' in repr(func))
        self.assertTrue(func.deletable)
        self.assertFalse(func.watch)

        func.watch = True

        self.assertTrue(func.watch)

        func.undefine()

        self.assertTrue(func not in self.env.functions())
        with self.assertRaises(LookupError):
            self.env.find_function("function-sub")

    def test_generic(self):
        """Defgeneric object test."""
        func = self.env.find_generic("generic-sum")

        self.assertTrue(func in self.env.generics())

        self.assertEqual(func.name, "generic-sum")
        self.assertEqual(func.module.name, "MAIN")
        self.assertTrue('defgeneric' in str(func))
        self.assertTrue('defgeneric' in repr(func))
        self.assertTrue(func.deletable)
        self.assertFalse(func.watch)

        func.watch = True

        self.assertTrue(func.watch)

        func.undefine()

        self.assertTrue(func not in self.env.generics())
        with self.assertRaises(LookupError):
            self.env.find_function("generic-sum")

    def test_method(self):
        """Defgeneric object test."""
        restr = (2, 2, 2, 6, 9, Symbol('FALSE'), 1, Symbol('INTEGER'),
                 Symbol('FALSE'), 1, Symbol('INTEGER'))
        func = self.env.find_generic("generic-sum")

        method = tuple(func.methods())[0]
        self.assertTrue('defmethod' in str(method))
        self.assertTrue('defmethod' in repr(method))
        self.assertTrue(method.deletable)
        self.assertFalse(method.watch)
        self.assertEqual(method.description, "1  (INTEGER) (INTEGER)")
        self.assertEqual(method.restrictions, restr)

        method.watch = True

        self.assertTrue(method.watch)

        method.undefine()

        self.assertTrue(method not in func.methods())
