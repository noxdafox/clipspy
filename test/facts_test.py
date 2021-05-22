import os
import unittest
from tempfile import mkstemp

from clips import Environment, Symbol, CLIPSError, TemplateSlotDefaultType


DEFTEMPLATE = """(deftemplate MAIN::template-fact
   (slot int (type INTEGER) (allowed-values 0 1 2 3 4 5 6 7 8 9))
   (slot float (type FLOAT))
   (slot str (type STRING))
   (slot symbol (type SYMBOL))
   (multislot multifield))
"""

IMPL_STR = '(implied-fact 1 2.3 "4" five)'
IMPL_RPR = 'ImpliedFact: (implied-fact 1 2.3 "4" five)'
TMPL_STR = '(template-fact (int 1) (float 2.2) (str "4") (symbol five) ' + \
           '(multifield 1 2))'
TMPL_RPR = 'TemplateFact: (template-fact (int 1) (float 2.2) ' + \
           '(str "4") (symbol five) (multifield 1 2))'


class TempFile:
    """Cross-platform temporary file."""
    name = None

    def __enter__(self):
        fobj, self.name = mkstemp()
        os.close(fobj)

        return self

    def __exit__(self, *_):
        os.remove(self.name)


class TestFacts(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.env.build(DEFTEMPLATE)

    def test_facts(self):
        """Facts wrapper test."""
        template = self.env.find_template('template-fact')
        self.assertTrue(template in self.env.templates())
        fact = self.env.assert_string('(implied-fact)')
        self.assertTrue(fact in self.env.facts())

        self.env.load_facts('(one-fact) (two-facts)')
        self.assertTrue('(two-facts)' in (str(f)
                                          for f in self.env.facts()))

        with TempFile() as tmp:
            saved = self.env.save_facts(tmp.name)
            self.env.reset()
            loaded = self.env.load_facts(tmp.name)
            self.assertEqual(saved, loaded)

    def test_implied_fact(self):
        """ImpliedFacts are asserted."""
        expected = (1, 2.3, '4', Symbol('five'))
        fact = self.env.assert_string('(implied-fact 1 2.3 "4" five)')

        self.assertEqual(fact[0], 1)
        self.assertEqual(len(fact), 4)
        self.assertEqual(fact.index, 1)
        self.assertEqual(tuple(fact), expected)
        self.assertEqual(str(fact), IMPL_STR)
        self.assertEqual(repr(fact), IMPL_RPR)
        self.assertTrue(fact in tuple(self.env.facts()))

    def test_template_fact(self):
        """TemplateFacts are asserted."""
        expected = {'int': 1,
                    'float': 2.2,
                    'str': '4',
                    'symbol': Symbol('five'),
                    'multifield': (1, 2)}
        template = self.env.find_template('template-fact')
        fact = template.assert_fact(**expected)

        self.assertEqual(len(fact), 5)
        self.assertEqual(fact.index, 1)
        self.assertEqual(fact['int'], 1)
        self.assertEqual(dict(fact), expected)
        self.assertEqual(str(fact), TMPL_STR)
        self.assertEqual(repr(fact), TMPL_RPR)
        self.assertTrue(fact in tuple(self.env.facts()))

    def test_template_fact_errors(self):
        """TemplateFacts errors."""
        with self.assertRaises(LookupError):
            self.env.find_template('non-existing-template')

        template = self.env.find_template('template-fact')

        with self.assertRaises(KeyError):
            template.assert_fact(non_existing_slot=1)
        with self.assertRaises(TypeError):
            template.assert_fact(int=1.0)
        with self.assertRaises(ValueError):
            template.assert_fact(int=10)

    def test_fact_duplication(self):
        """Test fact duplication."""
        fact = self.env.assert_string('(implied-fact)')
        new_fact = self.env.assert_string('(implied-fact)')

        self.assertEqual(fact, new_fact)
        self.assertEqual(len(tuple(self.env.facts())), 1)

        self.env.fact_duplication = True

        new_fact = self.env.assert_string('(implied-fact)')

        self.assertNotEqual(fact, new_fact)
        self.assertEqual(len(tuple(self.env.facts())), 2)

    def test_modify_fact(self):
        """Asserted TemplateFacts can be modified."""
        template = self.env.find_template('template-fact')
        fact = template.assert_fact(**{'int': 1,
                                       'float': 2.2,
                                       'str': '4',
                                       'symbol': Symbol('five'),
                                       'multifield': (1, 2)})

        fact.modify_slots(symbol=Symbol('six'))
        self.assertEqual(fact['symbol'], Symbol('six'))

    def test_retract_fact(self):
        """Retracted fact is not anymore in the fact list."""
        fact = self.env.assert_string('(implied-fact)')

        self.assertTrue(fact in list(self.env.facts()))

        fact.retract()

        self.assertFalse(fact in list(self.env.facts()))

    def test_implied_fact_template(self):
        """ImpliedFact template properties."""
        fact = self.env.assert_string('(implied-fact 1 2.3 "4" five)')
        template = fact.template

        self.assertTrue(template.implied)
        self.assertEqual(template.name, 'implied-fact')
        self.assertEqual(template.module.name, 'MAIN')
        self.assertEqual(template.slots, ())
        self.assertEqual(str(template), '')
        self.assertEqual(repr(template), 'Template: ')
        self.assertFalse(template.deletable)
        with self.assertRaises(CLIPSError):
            template.undefine()

    def test_template_fact_template(self):
        """TemplateFact template properties."""
        template = self.env.find_template('template-fact')

        self.assertEqual(template.name, 'template-fact')
        self.assertEqual(template.module.name, 'MAIN')
        self.assertEqual(len(tuple(template.slots)), 5)
        self.assertEqual(str(template), ' '.join(DEFTEMPLATE.split()))
        self.assertEqual(repr(template),
                         'Template: ' + ' '.join(DEFTEMPLATE.split()))
        self.assertTrue(template.deletable)

        template.undefine()

        with self.assertRaises(CLIPSError):
            print(template)

    def test_template_fact_slot(self):
        """TemplateFact template Slot."""
        template = self.env.find_template('template-fact')

        slots = {s.name: s for s in template.slots}

        self.assertEqual(slots['int'].name, 'int')
        self.assertFalse(slots['int'].multifield)
        self.assertTrue(slots['multifield'].multifield)

        self.assertEqual(slots['int'].types, ('INTEGER', ))
        self.assertEqual(slots['float'].types, ('FLOAT', ))
        self.assertEqual(slots['str'].types, ('STRING', ))
        self.assertEqual(slots['symbol'].types, ('SYMBOL', ))

        self.assertEqual(slots['int'].range, ('-oo', '+oo'))
        self.assertEqual(slots['float'].cardinality, ())
        self.assertEqual(slots['str'].default_type,
                         TemplateSlotDefaultType.STATIC_DEFAULT)
        self.assertEqual(slots['str'].default_value, '')
        self.assertEqual(slots['int'].allowed_values,
                         (0, 1, 2, 3, 4, 5, 6, 7, 8, 9))
