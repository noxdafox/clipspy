import unittest
from tempfile import NamedTemporaryFile

from clips import Environment, Symbol, CLIPSError, TemplateSlotDefaultType


DEFTEMPLATE = """(deftemplate MAIN::template-fact
   (slot int (type INTEGER) (allowed-values 0 1 2 3 4 5 6 7 8 9))
   (slot float (type FLOAT))
   (slot str (type STRING))
   (slot symbol (type SYMBOL))
   (multislot multifield))
"""

IMPL_STR = '(implied-fact 1 2.3 "4" five)'
IMPL_RPR = 'ImpliedFact: f-2     (implied-fact 1 2.3 "4" five)'
TMPL_STR = '(template-fact (int 1) (float 2.2) (str "4") (symbol five) (multifield 1 2))'
TMPL_RPR = 'TemplateFact: f-1     (template-fact (int 1) (float 2.2) (str "4") (symbol five) (multifield 1 2))'


class TestFacts(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.env.build(DEFTEMPLATE)

    def test_facts(self):
        """Facts wrapper test."""
        template = self.env.facts.find_template('template-fact')
        self.assertTrue(template in self.env.facts.templates())
        fact = self.env.facts.assert_string('(implied-fact)')
        self.assertTrue(fact in self.env.facts.facts())

        self.env.facts.load_facts('(one-fact) (two-facts)')
        self.assertTrue('(two-facts)' in (str(f)
                                          for f in self.env.facts.facts()))

        with NamedTemporaryFile(buffering=0) as tmp:
            saved = self.env.facts.save_facts(tmp.name)
            self.env.reset()
            loaded = self.env.facts.load_facts(tmp.name)
            self.assertEqual(saved, loaded)

    def test_implied_fact(self):
        """ImpliedFacts are asserted."""
        self.env.facts.assert_string('(implied-fact)')

        expected = [Symbol('implied-fact'), 1, 2.3, '4', Symbol('five')]
        template = self.env.facts.find_template('implied-fact')
        fact = template.new_fact()

        fact.append(1)
        fact.extend((2.3, '4', Symbol('five')))
        fact.assertit()

        for asserted_fact in self.env.facts.facts():
            if asserted_fact == fact:
                break

        self.assertEqual(asserted_fact[1], 1)
        self.assertEqual(len(asserted_fact), 5)
        self.assertEqual(asserted_fact.index, 2)
        self.assertEqual(list(asserted_fact), expected)
        self.assertEqual(str(asserted_fact), IMPL_STR)
        self.assertEqual(repr(asserted_fact), IMPL_RPR)

    def test_template_fact(self):
        """TemplateFacts are asserted."""
        expected = {'': 'template-fact', 'int': 1, 'float': 2.2,
                    'str': '4', 'symbol': Symbol('five'), 'multifield': [1, 2]}
        template = self.env.facts.find_template('template-fact')
        fact = template.new_fact()

        fact['int'] = 1
        fact.update({'float': 2.2, 'str': '4'})
        fact.update((('symbol', Symbol('five')), ('multifield', [1, 2])))
        fact.assertit()

        self.assertEqual(fact.index, 1)
        for asserted_fact in self.env.facts.facts():
            if asserted_fact == fact:
                break

        self.assertEqual(len(asserted_fact), 6)
        self.assertEqual(asserted_fact.index, 1)
        self.assertEqual(asserted_fact['int'], 1)
        self.assertEqual(dict(asserted_fact), expected)
        self.assertEqual(str(asserted_fact), TMPL_STR)
        self.assertEqual(repr(asserted_fact), TMPL_RPR)

    def test_implied_fact_already_asserted(self):
        """Asserted ImpliedFacts cannot be modified or re-asserted."""
        self.env.facts.assert_string('(implied-fact)')

        template = self.env.facts.find_template('implied-fact')
        fact = template.new_fact()

        fact.extend((1, 2.3, '4', Symbol('five')))
        fact.assertit()

        self.assertTrue(fact.asserted)

        with self.assertRaises(RuntimeError):
            fact.append(42)
        with self.assertRaises(RuntimeError):
            fact.assertit()

    def test_template_fact_already_asserted(self):
        """Asserted TemplateFacts cannot be modified or re-asserted."""
        template = self.env.facts.find_template('template-fact')
        fact = template.new_fact()

        fact.update({'int': 1, 'float': 2.2, 'str': '4',
                     'symbol': Symbol('five'), 'multifield': [1, 2]})
        fact.assertit()

        self.assertTrue(fact.asserted)

        with self.assertRaises(RuntimeError):
            fact['int'] = 42
        with self.assertRaises(RuntimeError):
            fact.assertit()

    def test_retract_fact(self):
        """Retracted fact is not anymore in the fact list."""
        self.env.facts.assert_string('(implied-fact)')

        template = self.env.facts.find_template('implied-fact')
        fact = template.new_fact()

        fact.extend((1, 2.3, '4', Symbol('five')))
        fact.assertit()

        self.assertTrue(fact.asserted)
        self.assertTrue(fact in list(self.env.facts.facts()))

        fact.retract()

        self.assertFalse(fact.asserted)
        self.assertFalse(fact in list(self.env.facts.facts()))

    def test_implied_fact_template(self):
        """ImpliedFact template properties."""
        fact = self.env.facts.assert_string('(implied-fact 1 2.3 "4" five)')
        template = fact.template

        self.assertTrue(template.implied)
        self.assertEqual(template.name, 'implied-fact')
        self.assertEqual(template.module.name, 'MAIN')
        self.assertEqual(template.slots(), ())
        self.assertEqual(str(template), 'implied-fact')
        self.assertEqual(repr(template), 'Template: implied-fact')
        self.assertFalse(template.deletable)
        with self.assertRaises(CLIPSError):
            template.undefine()

    def test_template_fact_template(self):
        """TemplateFact template properties."""
        template = self.env.facts.find_template('template-fact')

        self.assertEqual(template.name, 'template-fact')
        self.assertEqual(template.module.name, 'MAIN')
        self.assertEqual(len(tuple(template.slots())), 5)
        self.assertEqual(str(template), DEFTEMPLATE)
        self.assertEqual(repr(template), 'Template: ' + DEFTEMPLATE)
        self.assertTrue(template.deletable)

        template.undefine()

    def test_template_fact_slot(self):
        """TemplateFact template Slot."""
        template = self.env.facts.find_template('template-fact')

        slots = {s.name: s for s in template.slots()}

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
