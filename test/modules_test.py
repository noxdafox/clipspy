import unittest

from clips import Environment, Symbol, CLIPSError


DEFGLOBAL = """
(defglobal
  ?*a* = 1
  ?*b* = 2)
"""

DEFMODULE = """(defmodule TEST)"""


class TestModules(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.env.build(DEFGLOBAL)

    def tearDown(self):
        self.env = None

    def test_modules(self):
        """Modules wrapper class test."""
        self.env.build(DEFMODULE)

        # reset MAIN module
        module = self.env.modules.find_module('MAIN')
        self.env.modules.current_module = module

        module = self.env.modules.find_module('TEST')
        self.env.modules.current_module = module

        self.assertEqual(self.env.modules.current_module,
                         self.env.modules.find_module('TEST'))
        self.assertTrue(module in self.env.modules.modules())
        self.assertEqual(self.env.modules.current_module, module)

        with self.assertRaises(LookupError):
            self.env.modules.find_module("NONEXISTING")

    def test_global(self):
        """Defglobal object test."""
        glbl = self.env.modules.find_global("b")

        self.assertTrue(glbl in self.env.modules.globals())
        self.assertEqual(glbl.value, 2)

        glbl.value = 3

        self.assertEqual(glbl.value, 3)
        self.assertTrue(self.env.modules.globals_changed)

        self.assertEqual(glbl.name, "b")
        self.assertEqual(glbl.module.name, "MAIN")
        self.assertTrue('defglobal' in str(glbl))
        self.assertTrue('defglobal' in repr(glbl))
        self.assertTrue(glbl.deletable)
        self.assertFalse(glbl.watch)

        glbl.watch = True

        self.assertTrue(glbl.watch)

        glbl.undefine()

        self.assertTrue(glbl not in self.env.modules.globals())
        with self.assertRaises(LookupError):
            self.env.modules.find_global("b")

    def test_module(self):
        """Module object test."""
        module = self.env.modules.current_module

        self.assertEqual(module.name, 'MAIN')
        self.assertEqual(str(module), 'MAIN')
        self.assertEqual(repr(module), 'Module: MAIN')
