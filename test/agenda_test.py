import unittest

from clips import Environment, CLIPSError, Strategy, SalienceEvaluation


DEFTEMPLATE = """(deftemplate template-fact
  (slot template-slot))
"""

DEFRULE = """(defrule MAIN::rule-name
   (declare (salience 10))
   (implied-fact implied-value)
   =>
   (assert (rule-fired)))
"""

DEFTEMPLATERULE = """(defrule MAIN::rule-name
   (implied-fact implied-value)
   (template-fact (template-slot template-value))
   =>
   (assert (rule-fired)))
"""

DEFOTHERRULE = """(defrule MAIN::other-rule-name
   (declare (salience 20))
   (implied-fact implied-value)
   =>
   (assert (rule-fired)))
"""


class TestAgenda(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.env.build(DEFTEMPLATE)
        self.env.build(DEFRULE)

    def test_agenda_strategy(self):
        """Agenda strategy getting/setting."""
        for strategy in Strategy:
            self.env.strategy = strategy
            self.assertEqual(self.env.strategy, strategy)

    def test_agenda_salience_evaluation(self):
        """Agenda salience_evaluation getting/setting."""
        for salience_evaluation in SalienceEvaluation:
            self.env.salience_evaluation = salience_evaluation
            self.assertEqual(
                self.env.salience_evaluation, salience_evaluation)

    def test_agenda_activation(self):
        """Agenda activation test."""
        self.env.assert_string('(implied-fact implied-value)')

        self.assertTrue(self.env.agenda_changed)

        activation = tuple(self.env.activations())[0]

        self.assertEqual(activation.name, 'rule-name')
        self.assertEqual(activation.salience, 10)
        self.assertEqual(str(activation), '10 rule-name: f-1')
        self.assertEqual(repr(activation), 'Activation: 10 rule-name: f-1')

        activation.delete()

        self.assertFalse(activation in self.env.activations())

    def test_agenda_run(self):
        """Agenda rules are fired on run."""
        self.env.assert_string('(implied-fact implied-value)')

        self.env.run()

        fact_names = (f.template.name for f in self.env.facts())
        self.assertTrue('rule-fired' in fact_names)

    def test_agenda_activation_order(self):
        """Agenda activations order change if salience or strategy change."""
        self.env.build(DEFOTHERRULE)
        self.env.assert_string('(implied-fact implied-value)')

        self.assertTrue(self.env.agenda_changed)

        activations = tuple(self.env.activations())

        self.assertEqual(tuple(a.name for a in activations),
                         (u'other-rule-name', u'rule-name'))

        activations[1].salience = 30

        self.assertEqual(activations[1].salience, 30)

        self.assertFalse(self.env.agenda_changed)

        self.env.reorder()

        self.assertTrue(self.env.agenda_changed)

        activations = tuple(self.env.activations())

        self.assertEqual(tuple(a.name for a in activations),
                         (u'rule-name', u'other-rule-name'))

        self.env.refresh()

        self.assertTrue(self.env.agenda_changed)

        self.env.clear()

        activations = tuple(self.env.activations())

        self.assertEqual(len(activations), 0)


class TestRules(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.env.build(DEFTEMPLATE)
        self.env.build(DEFTEMPLATERULE)

    def test_rule_build(self):
        """Simple Rule build."""
        rule = self.env.find_rule('rule-name')

        self.assertTrue(rule in self.env.rules())
        self.assertEqual(rule.module.name, 'MAIN')
        self.assertTrue(rule.deletable)
        self.assertEqual(str(rule), ' '.join(DEFTEMPLATERULE.split()))
        self.assertEqual(repr(rule),
                         "Rule: %s" % ' '.join(DEFTEMPLATERULE.split()))
        self.assertFalse(rule.watch_firings)
        rule.watch_firings = True
        self.assertTrue(rule.watch_firings)
        self.assertFalse(rule.watch_activations)
        rule.watch_activations = True
        self.assertTrue(rule.watch_activations)

        rule.undefine()

        with self.assertRaises(LookupError):
            self.env.find_rule('rule-name')
        with self.assertRaises(TypeError):
            rule.name

    def test_rule_matches(self):
        """Partial rule matches."""
        rule = self.env.find_rule('rule-name')
        self.env.assert_string('(implied-fact implied-value)')

        self.assertEqual(rule.matches(), (1, 0, 0))

        rule.undefine()

    def test_rule_activation(self):
        """Rule activation."""
        rule = self.env.find_rule('rule-name')
        self.env.assert_string('(implied-fact implied-value)')
        self.env.assert_string(
            '(template-fact (template-slot template-value))')

        self.assertEqual(rule.matches(), (2, 1, 1))
        self.env.run()
        rule.refresh()

        fact_names = (f.template.name for f in self.env.facts())
        self.assertTrue('rule-fired' in fact_names)
