from typing import Any, Dict, List, NewType, Text, Tuple, Union, NoReturn
from clips import Environment, ImpliedFact, TemplateFact
from clips.common import Symbol
from .utils import get_functions_from_module_name
#from.rules_engines_persistence import RulesEnginesStore

from collections import deque
from queue import Queue
import logging
import time


logger = logging.getLogger(__name__)

SYMBOL_TRUE = Symbol("True")
SYMBOL_FALSE = Symbol("False")

# Type definitions
SimpleFactValue = NewType("SimpleFactValue", Union[int, float, bool, Text])
UnorderedFactValue = NewType("FactValue", Union[Dict[Text, SimpleFactValue], object])
OrderedFactValue = NewType("FactValue", Union[SimpleFactValue, List[SimpleFactValue]])
GenericFactValue = NewType("GenericFactValue", Union[UnorderedFactValue, OrderedFactValue])


class InvalidSlotF(Exception):
    """
    This exception is raised when an invalid (slot_f) operation is invoked.
    """
    pass

class InvalidUniqueSlot(Exception):
    """
    This exception is raised when an invalid (unique_slot) operation is invoked.
    """
    pass

class InvalidCallF(Exception):
    """
    This exception is raised when an invalid (call_f) operation is invoked.
    """
    pass

class InvalidUniqueSlotF(Exception):
    """
    This exception is raised when an invalid (unique_slot_f) operation is invoked.
    """
    pass

class ReasonLimitReached(Exception):
    """
    This exception is raised when the maximum limit of reasoning cycles is reached.
    """
    pass

class InvalidCallAndAssert(Exception):
    """
    This exception is raised when an invalid (call_and_assert) operation is invoked.
    """

class FuctionsPackageNotSet(Exception):
    """
    This exception is raised when no functions package/module has been configured but a custom function is called.
    """
    pass

class InvalidSlotFormat(Exception):
    """
    This exception is raised when a malformed slot is tried to be asserted into the rules engine working memory.
    """
    pass

class PersistenceError(Exception):
    """
    This exception is raised when an error in writing / reading persistent the state of a rules engine from a persistent
    store occurs.
    """
    pass

class TicToc(object):
    """
    Utility class to measure execution times.
    """
    def __init__(self):
        self._start_time = {}
        self._end_time = {}
        self._lapse_time = {}

    def _tic(self, name:Text):
        self._start_time[name] = time.time()

    def _toc(self, name:Text):
        self._end_time[name] = time.time()
        self._lapse_time[name] = self._end_time.get(name, 0) - self._start_time.get(name, 0)

    def _tictoc(self, name:Text):
        return self._lapse_time.get(name, 0)

class RulesEngine(TicToc):
    """
    Reasoner on RasAura slots.

    The following special facts are used:

    - Slot fact, with format
        (slot <slot_name> <slot_value>)
    - Call function format:
        (call_f <function_name> [<positional_argument>]*)
    - Write into a slot the resulting value of the invocation of a function, with format
        (set_slot_f <slot_name> <function_name> [<positional_argument>]*)
      The result of this will be the assertion of the fact (slot <slot_name> <alot_value>) where <slot_value> is the
      value returned by the call <function_name>([<propositional_argument>]*)
    """

    def __init__(self, rules_files: List[Text], functions_package_name: Text= None):
        """
        :param rules_files: List of files containing the Clips definition of the rules. Files are provided following
            their intended loading order. For instance, if file_2 uses constructs defined in file_1 then the following
            list must be provided [file_1, file_2].
        :param functions_package_name: The name of the package containing the functions that will be used in the rules.
        """
        super().__init__()
        self._tic("__init__")
        self.rules_files = rules_files

        self.env = Environment()

        if functions_package_name is not None:
            self.functions_package_name = functions_package_name
            for f in get_functions_from_module_name(functions_package_name):
                logger.info("Defining function {}".format(f.__name__))
                self.env.define_function(f)

        for rf in rules_files:
            self.env.load(rf)

        # This is the total number of rules fired during the execution of the reason() method.
        self.num_fires = 0

        self._toc("__init__")
        logger.info("Rules engine created in {0:.3f} ms".format(self._tictoc("__init__") * 1000))

    def _import_package(self, package_name: Text):
        pck = __import__(package_name)
        pck_components = package_name.split(".")
        for comp in pck_components[1:]:
            pck = getattr(pck, comp)
        return pck

    def set_slots(self, slots: Union[Dict[Text, OrderedFactValue],
                                     List[Tuple[Text, OrderedFactValue]]]):
        """
        Write the content of a dictionary or a list as unordered facts of type "slot" into the working memory.
        This method asserts the facts as special unordered facts with the following structure:
            ```
            (slot <slot_name> <slot_value>)
            ```
        This way of asserting facts has a limitation: only simple Python types or lists can be asserted.
        If list types are used, the resulting slots has an ordered list of values. E.g.:
            ```
            (slot <slot_name> <value_1> <value_2> ... <value_n>)
            ```

        :param slots: Slots to be set. Slots can be specified in two ways:
            - As a dictionary:
                ```
                {
                    <slot_name_1>: <value_1>,
                    <slot_name_2>: <value_2>,
                    ...
                    <slot_name_n>: <value_n>,
                }
                ```
                Example:
                ```
                {
                    "pizza_size": "big",
                    "pizza_ingredients": ["cheese", "pepperoni", "tomato"]
                    ...
                }
                ```
            - As a list of tuples/lists:
                ```
                [
                    [<slot_name_1>, <value_1>]
                    [<slot_name_2>, <value_2>]
                    ...
                    [<slot_name_n>, <value_n>]
                [
                ```
                Example:
                ```
                [
                    ["pizza_size", "big"],
                    ["pizza_ingredients", ["cheese", "pepperoni", "tomato"]]
                    ...
                ]
                ```
        """
        if isinstance(slots, dict):
            for k, v in slots.items():
                if v is not None:
                    # Only assert non None slots.
                    self.assert_slot(k, v)
        elif isinstance(slots, list):
            for s in slots:
                if not isinstance(s, tuple) or len(s) < 2:
                    raise InvalidSlotFormat("The slot {} has not a valid format".format(s))
                _slot_name = s[0]
                _slot_value = s[1] if len(s) == 2 else s[1:]
                # Only assert non None slots.
                if _slot_value is not None:
                    self.assert_slot((_slot_name, _slot_value))
        else:
            raise InvalidSlotFormat("The slots {} have not a valid format".format(slots))

    def set_facts(self, facts: Union[Dict[Text, GenericFactValue],
                                     List[Tuple[Text, GenericFactValue]]]):
        """
        Write the content of a dictionary or a list as facts into the working memory.
        The type of the fact depends on the type of the values provided:
            - If the type of the value is primitive or list it is asserted as an unordered fact:
              ```
              (<fact_name> <value>+)
              ```
              Example:
              ```
              {"content_name": "startrek"} -> (content_name "star trek")
              {"pizza_ingredients": ["cheese" "tomato" "pepperoni"]} -> (pizza_ingredients "cheese" "tomato" "pepperoni")
              ```
            - If the value is dictionary or a plain python object it is asserted as an ordered fact:
              ```
              (<fact_name> (<property_name|key> <value>))
              ```
              Asserting ordered facts requires the coresponding deftemplate to be defined in the rules engine.
              Additionally, the corresponding types of the slots/multislots defined in the deftempaltes must be
              compatible with the types of the values.
              Example:
              ```
              {"user":
                {
                  "id": "1234asdf56789",
                  "requests": ["1234567", "23456789"]
                }
              }
              ->
              (user (id "1234asdf56789") (requests  "1234567", "23456789"))
              ```
              In this example it should exist a detemplate similar to this one
              ```
              (deftemplate (slot id) (multislot requests))
              ```

        Is important to note that the values of the facts not allowed to be dictionaries or plain objects. For example,
        the following fact specification is not valid:
        ```
          {"user":
            {
              "id": "1234asdf56789",
              "details": {
                 "name": "Spock",
                 "birth_place": "Vulcan"
               }
            }
          }
        ```

        :param facts: Python structures to be asserted as slots.
            - As a dictionary:
                ```
                {
                    <slot_name_1>: <value_1>,
                    <slot_name_2>: <value_2>,
                    ...
                    <slot_name_n>: <value_n>,
                }
                ```
                Example:
                ```
                {
                    "pizza_size": "big",
                    "pizza_ingredients": ["cheese", "pepperoni", "tomato"],
                    "delivery_location": {
                        "city": "Madrid",
                        "address": "Rue del Percebe 13"
                    }
                    ...
                }
                ```
            - As a list of tuples/lists:
                ```
                [
                    [<slot_name_1>, <value_1>]
                    [<slot_name_2>, <value_2>]
                    ...
                    [<slot_name_n>, <value_n>]
                [
                ```
                Example:
                ```
                [
                    ["pizza_size", "big"],
                    ["pizza_ingredients", ["cheese", "pepperoni", "tomato"]]
                    [ "delivery_location",
                      {
                        "city": "Madrid",
                        "address": "Rue del Percebe 13"
                      }
                    ]

                    ...
                ]
                ```
        """
        self._tic("set_facts")
        if isinstance(facts, dict):
            for k, v in facts.items():
                if v is not None:
                    # Only assert non None slots.
                    self.assert_fact(k, v)
        elif isinstance(facts, list):
            for f in facts:
                if not isinstance(f, tuple) or len(f) < 2:
                    raise InvalidSlotFormat("The fact {} has not a valid format".format(f))
                _fact_name = f[0]
                _fact_value = f[1] if len(f) == 2 else f[1:]
                # Only assert non None slots.
                if _fact_value is not None:
                    self.assert_fact(_fact_name, _fact_value)
        self._toc("set_facts")
        logger.debug("Set facts into the rules engine in {:.3f} ms".format(self._tictoc("set_facts")*1000))

    def assert_plain_object(self, template_name: Text, obj: object):
        """
        Assert a plain object into the working memory as an unordered fact.

        :param template_name: The name of the template.
        :param obj: The object to assert. It must be a plain object.
        """
        self.assert_dictionary(template_name, obj.__dict__)

    def assert_dictionary(self, template_name, d: Dict[Text, SimpleFactValue]):
        """
        Assert a dictionary into the working memory as an unordered fact.

        :param template_name: The name of the template.
        :param d: The dictionary to assert.
        """
        template = self.env.find_template(template_name)
        fact = template.new_fact()
        for k, v in d.items():
            fact[k] = v
        fact.assertit()

    def reason(self, reason_limit=1000, mode="BASIC") -> Union[NoReturn, Dict[Text, UnorderedFactValue]]:
        """
        Executes the run command of Clips.

        :param reason_limit: Maximum number of processing cycles allowed. This is a safety limit that never should be
        reached.
        :param mode: Mode of reasoning. The following modes are currently available:
            - "COMPLETE" (default): Additional control logic is used to provide extra functionalities to the CLIPS
              rules engine.. This includes:
              - "Slot mode" for facts: data can be asserted as special facts with this structure:
                    (slot <slot_name> <slot_value>)
                This makes easier working with slot-like fact bases.
              - Assertion of "unique slots". It is possible to force uniqueness of slot facts.
            - "BASIC": Use CLIPS as it is, without any extra enhancement.

        """
        self._tic("reason")
        self.num_fires = 0
        self._reason(reason_limit=reason_limit, mode=mode)
        self._toc("reason")
        logger.debug("Rules engine reason() took {:.3f} ms. Facts asserted: {}. Rules defined: {}. Rules fired: {}".format(self._tictoc("reason")*1000,
                                                                                              self.get_num_facts(),
                                                                                              self.get_num_rules(),
                                                                                              self.num_fires))

    def collect_resulting_slots(self, initial_slots: Dict[Text, UnorderedFactValue]) -> Dict[Text, UnorderedFactValue]:
        """
        Return the slot changes in the current working memory with respect to a dictionary of initial slots.
        Only unordered facts of type "slot" are considered. Therefore, make sure that all the initial_slots are
        really asserted as "slots" using the set_slots method or using the reason method with the corresponding
        dictionary of slots.

        :param initial_slots: Initial slots to compare with.
        :return: A dictionary with the slot values changed (created, retracted or modified).
        """
        self._tic("collect_resulting_slots")
        res = {}
        _num_slots = 0
        _slots_in_working_memory = {}
        for f in self.env.facts():
            template = f.template
            if template.name == "slot":
                _fact_items = [i for i in f]
                _slot_name = _fact_items[0]
                _slot_value = _fact_items[1] if len(_fact_items) == 2 else _fact_items[1:]
                _slots_in_working_memory[_slot_name] = _slot_value
                if initial_slots.get(_slot_name, None) != _slot_value:
                    res[_slot_name] = self._translate_clips_value(_slot_value)
        # Look for retracted slots. Send them as None values.
        for slot_name, slot_value in initial_slots.items():
            if slot_name not in _slots_in_working_memory and slot_value is not None:
                res[slot_name] = None
        # Look for new asserted slots, not defined in initial_slots
        for slot_name, slot_value in _slots_in_working_memory:
            if slot_name not in initial_slots:
                res[slot_name] = slot_value
        self._toc("collect_resulting_slots")
        logger.debug("Rules engine collect_resulting_slots() took {:.3f} ms".format(self._tictoc("collect_resulting_slots")*1000))
        return res

    def collect_fact_values(self, name: Text) -> List[Tuple[Text, UnorderedFactValue]]:
        """
        Return the values of all the facts with a given name.
        For example, if the following facts are asserted into the working memory
          ```
            (intent_suggestion intent_1 0.231)
            (intent_suggestion intent_2 0.327)
            (entity_suggestion intent_1 entity_34 0.98)
          ```
        collect_fact_values("intent_suggestion") would return
          ```
          [
            [intent_1, 0.231],
            [intent_2, 0.327]
          ]
          ```
        and collect_unordered_fact_values("entity_suggestion") would return
          ```
          [
            [intent_1, entity_34, 0.98]
          ]
          ```

        This method works both for ordered and unordered facts. Therefore, if the following facts are asserted
          ```
            (user (id "123456789"))
            (user (id "987654321"))
          ```
        collect_fact_values("user") would return
          ```
          [
            {"id": "123456789"},
            {"id": "987654321"}
          ]
          ```

        :param name: The name of the facts to be collected.

        :return: A list with the values of the found facts.
        """
        self._tic("collect_fact_values")
        res = []
        _num_slots = 0
        _slots_in_working_memory = {}
        for f in self.env.facts():
            template = f.template
            if template.name == name:
                if isinstance(f, ImpliedFact):
                    # Ordered fact
                    _fact_items = [i for i in f]
                    res.append(_fact_items)
                else:
                    # TemplateFact. Unordered fact
                    res.append({k: v for k, v in f})
        self._toc("collect_fact_values")
        logger.debug("Rules engine collect_fact_values() took {:.3f} ms".format(self._tictoc("collect_fact_values")*1000))
        return res


    # def update_slots_and_reason(self, invalidated_slots_dict: Dict[Text, Any],
    #                             slots_snapshot_dict: Dict[Text, Any], reason_limit=1000) -> Dict[Text, Any]:
    #     """
    #
    #     :param invalidated_slots_dict:
    #     :param slots_snapshot_dict:
    #     :param reason_limit:
    #     :return:
    #     """
    #     for slot_name, slot_value in invalidated_slots_dict.items():
    #         self._retract_slots_by_name(slot_name)
    #         self._assert_slot(slot_name, slot_value)
    #     self._reason(reason_limit=reason_limit)
    #     # Collect facts
    #     return self._collect_resulting_slots(slots_snapshot_dict)


    def update_slots_and_reason(self, updated_slots_dict: Dict[Text, OrderedFactValue],
                                reason_limit=1000) -> Dict[Text, OrderedFactValue]:
        """
        This method updates the values of a set of slots and reasons on these changes again (run the rules engine).

        :param updated_slots_dict: Dictionary with the updated slots (key: slot name, value: new slot value).
        :param reason_limit: Maximum number of reasoning cycles allowed.

        :return: The resulting slot values from the current execution.
        """
        for slot_name, slot_value in updated_slots_dict.items():
            self._retract_slots_by_name(slot_name)
            self.assert_fact(slot_name, slot_value)

        # Get a dictionary with the updated slots (key: slot name, value: new slot value)
        slots_snapshot_dict = self.collect_resulting_slots({})

        self._reason(reason_limit=reason_limit)
        # Collect facts
        return self.collect_resulting_slots(slots_snapshot_dict)

    def _translate_clips_value(self, value: Any) -> Any:
        """
        Convert a clips value into its corresponding python type.
        In particular, translate Symbols to booleans / Strings / Integers / Floats.

        :param value: Value to translate.

        :return: The resulting translated value.
        """
        _t = type(value)
        if _t == list or _t == tuple:
            return [self._translate_clips_value(v) for v in value]
        if type(value) == Symbol:
            if value == SYMBOL_TRUE:
                return True
            if value == SYMBOL_FALSE:
                return False
            if value.isnumeric():
                return int(value)
            if self._is_float(value):
                return float(value)
            else:
                return str(value)
        else:
            return value

    def _is_float(self, v: Symbol):
        try:
            float(v)
            return True
        except:
            return False

    def _get_slots_by_name(self, slot_name: Text) -> List[ImpliedFact]:
        """
        This method returns a list with all the unordered facts called 'slot' whose second element is slot_name.

        :param slot_name: The name of the slot.

        :return: List of facts. Empty list none is found.
        """
        res = []
        for f in self.env.facts():
            template = f.template
            if template.name == "slot":
                fact_items = list(f)
                if len(fact_items) > 0 and fact_items[0] == slot_name:
                    res.append(f)
        return res

    def _get_slots(self) -> List[ImpliedFact]:
        """
        This method returns a list with all the unordered facts called 'slot'.

        :return: List of facts. Empty list none is found.
        """
        res = []
        for f in self.env.facts():
            template = f.template
            if template.name == "slot":
                fact_items = list(f)
                res.append(f)
        return res

    def _retract_slots_by_name(self, slot_name: Text):
        """
        Retracts all the unordered facts called 'slot' whose second element is slot_name.

        :param slot_name: The name of the slot.

        :return: The number of retracted slots.
        """
        count = 0
        for f in self._get_slots_by_name(slot_name):
            f.retract()
            count += 1
        return count

    def assert_fact(self, fact_name: Text, fact_value: GenericFactValue):
        """
        Assert a fact into the working memory.
        The result is the assertion of a fact with this form:
        - If fact_value is a primitive Python type or a list: ordered fact.
        - If fact_value is a dictionary or plain object: unordered fact. In this case the corresponding deftemplate to
          fact_name should be defined in the rules engine.

        :param fact_name: The name of the fact.
        :param fact_value: Value or list of values for the slot.
        """
        if type(fact_value) == list or type(fact_value) == tuple:
            self.env.assert_string("(slot {} {})".format(fact_name, " ".join([self._encode_slot_value(v) for v in fact_value])))
        elif type(fact_value) == dict:
            self.assert_dictionary(fact_name, fact_value)
        else:
            self.env.assert_string("(slot {} {})".format(fact_name, self._encode_slot_value(fact_value)))

    def assert_slot(self, slot_name: Text, slot_value: OrderedFactValue):
        """
        Assert a python value as a "slot" fact.
        The result is the assertion of an ordered fact with this form:
        ```
        (slot <slot_name> <slot_value>)
        ```

        :param slot_name: The name of the slot (i.e. the first element of the resulting ordered fact).
        :param slot_value: Primitive python value or list of primitive values for the slot. If it is a list it is
        split into the corresponding ordered fact. e. g.: (slot slot_name slot_value_1 slot_value_2 slot_value_3).
        """
        if type(slot_value) == list or type(slot_value) == tuple:
            self.env.assert_string("(slot {} {})".format(slot_name, " ".join([self._encode_slot_value(v) for v in slot_value])))
        else:
            self.env.assert_string("(slot {} {})".format(slot_name, self._encode_slot_value(slot_value)))

    def _encode_slot_value(self, slot_value: OrderedFactValue):
        if type(slot_value) == str:
            return '"{}"'.format(slot_value)
        return str(slot_value)

    def _get_slot_values_from_list(self, item_list: List[SimpleFactValue]) -> OrderedFactValue:
        """
        # TODO Review

        Return a list of items as a value to be set into a slot fact.

        :param item_list: List of itmes. If it contains only one elment, this is returned. If it contains more than one
        element, return this list. item_list is empty, return None.
        :return:
        """
        if item_list is None:
            return None
        if len(item_list) == 0:
            return None
        elif len(item_list) == 1:
            return item_list[0]
        else:
            return item_list

    def _reason(self, reason_limit=1000, mode="BASIC") -> Dict[Text, Any]:
        """
        :param slots:
        :param reason_limit:
        :param mode: Mode of reasoning. The following modes are currently available:
            - "COMPLETE" (default): Additional control logic is used to provide extra functionalities to the CLIPS
              rules engine.. This includes:
              - "Slot mode" for facts: data can be asserted as special facts with this structure:
                    (slot <slot_name> <slot_value>)
                This makes easier working with slot-like fact bases.
              - Assertion of "unique slots". It is possible to force uniqueness of slot facts.
            - "BASIC": Use CLIPS as it is, without any extra enhancement.
        """
        assert mode in ["BASIC", "COMPLETE"]
        if reason_limit <= 0:
            raise ReasonLimitReached()
        self._tic("_reason.self.env.run")
        self.num_fires += self.env.run()
        self._toc("_reason.self.env.run")
        logger.debug("Rules engine _reason().self.env.run() took {:.3f} ms".format(self._tictoc("_reason.self.env.run")*1000))
        run_again = False

        if mode == "COMPLETE":
            # Look for 'unique_slot', 'unique_slot_f', 'call_and_assert'
            _slots_to_assert = []
            _facts_to_retract = []
            self._tic("_reason.loop_on_facts")
            for f in self.env.facts():
                template = f.template
                #-----------
                # unique_slot
                if template.name == "unique_slot":
                    fact_items = list(f)
                    run_again = True
                    if len(fact_items) == 0:
                        raise InvalidUniqueSlot("No slot name is provided in (unique_slot)")
                    if len(fact_items) == 1:
                        raise InvalidUniqueSlot("No slot value is provided in (unique_slot)")
                    _facts_to_retract.append(f)
                    _slot_name = fact_items[0]
                    _slot_value = self._get_slot_values_from_list(fact_items[1:])
                    # Get the facts to retract and decide whether asserting a new fact is necessary.
                    _new_facts_to_retract, _needs_to_assert = self._get_facts_to_retract_unique(_slot_name, _slot_value)
                    for r_f in _new_facts_to_retract:
                        _facts_to_retract.append(r_f)
                    if _needs_to_assert:
                        # Assert the new fact
                        _slots_to_assert.append((_slot_name, _slot_value))
            self._toc("_reason.loop_on_facts")
            logger.debug("Rules engine _reason().loop_on_facts took {:.3f} ms".format(self._tictoc("_reason.loop_on_facts")*1000))

            for f in _facts_to_retract:
                f.retract()
            for _s in _slots_to_assert:
                # Assert the new fact
                self.assert_fact(_s[0], _s[1])

            if run_again:
                self._reason(reason_limit - 1)

    def _get_facts_to_retract_unique(self, slot_name: Text, slot_value: Any) -> Tuple[List[ImpliedFact], bool]:
        """
        Get which facts need to be retracted from the working memory to ensure that the fact (slot <slot_name> <slot_value>)
        is unique.
        If that fact already exists, keep it to prevent racing conditions due to unlimited rules chaining.
        If more than one facts with same slot name and value, only one of them is left.

        :param slot_name: The slot name
        :param slot_value: The slot value

        :return: List with two elements: a list with the facts to retract and a boolean indicating whether the new fact
        needs to be asserted.
        """
        facts_to_retract = []
        needs_to_assert = True
        for r_f in self._get_slots_by_name(slot_name):
            fact_items = list(r_f)[1:]
            fact_value = fact_items[0] if len(fact_items) == 1 else fact_items
            if needs_to_assert:
                if slot_value == fact_value:
                    # No need to assert the fact, since it already exists in the working memory.
                    needs_to_assert = False
                else:
                    # Retract the fact, since it has some value different from the on that is to be set.
                    facts_to_retract.append(r_f)
            else:
                # This is a repeated fact that must be retracted.
                facts_to_retract.append(r_f)
        return facts_to_retract, needs_to_assert

    # def _call_function(self, function_name: Text, *argv):
    #     """
    #     Calls a function given its name, module and arguments.
    #     Currently only positional arguments are supported.
    #
    #     :param function_name:
    #     :param argv:
    #     """
    #     if self.functions_package is not None:
    #         function_to_call = getattr(self.functions_package, function_name)
    #     elif self.functions_module is not None:
    #         function_to_call = getattr(self.functions_module, function_name)
    #     else:
    #         raise FuctionsPackageNotSet("NO functions package/module has been cpnfigured.")
    #     return function_to_call(*argv)

    def reset(self):
        """
        Reset the working memory.
        """
        self.env.reset()

    def print_facts(self):
        """
        Print the facts present in the working memory.
        """
        for f in self.env.facts():
            print(f)

    def get_num_facts(self):
        return len(list(self.env.facts()))

    def get_num_rules(self):
        return len(list(self.env.rules()))


class RulesEnginePool(object):
    """
    Pool of rules engines.
    The pool also manages persistence of rules engines through a RulesEnginesEstore.
    """

    # Dictionary of rules engines pools.
    pool_dict = {}

    @classmethod
    def get_instance(cls, pool_name: Text, rules_files: List[Text]= None, functions_package_name: Text= None,
                    pool_size: int= -1, initial_pool_size: int= 5, store: 'RulesEnginesStore'= None) -> 'RulesEnginePool':
        """
        This method is used to instantiate rules engines pools.
        Different pools can be instantiated using different pool names. Using this method ensures that only one
        pool instance does exist in a given process for a pool name.

        If the maximum number of engines is reached and there is no idle engine this method blocks until one engine is
        released.

        :param pool_name:
        :param rules_files: List of files containing the Clips definition of the rules. Files are provided following
            their intended loading order. For instance, if file_2 uses constructs defined in file_1 then the following
            list must be provided [file_1, file_2].
        :param functions_package_name: The name of the package containing the functions that will be used in the rules.
          If this parameter is set 'functions_module_name' and 'functions_module_file' will not be used.
        :param pool_size: Number of rules engines in the pool. If -1, the number of engines is not limited.
        :param initial_pool_size: The initial number of pools to be preloaded at instantiation time.
        :param store: A RulesEnginesStore to save persistent states.

        :return: A RuesEnginePool instance.
        """
        if pool_name in cls.pool_dict:
            return RulesEnginePool.pool_dict[pool_name]
        else:
            pool = RulesEnginePool(pool_name, rules_files, functions_package_name=functions_package_name,
                     pool_size=pool_size, initial_pool_size=initial_pool_size, store=store)
            cls.pool_dict[pool_name] = pool
            return pool

    def __init__(self, pool_name: Text, rules_file: Text, functions_package_name: Text= None,
                 pool_size: int= -1, initial_pool_size: int= 5, store: 'RulesEnginesStore'= None):
        """
        :param pool_name: The name of the pool.
        :param rules_file: File with the definition of the rules to be loaded into the engine.
        :param functions_package_name: The name of the package containing the functions that will be used in the rules.
          If this parameter is set 'functions_module_name' and 'functions_module_file' will not be used.
        :param pool_size: Number of rules engines in the pool. If -1, the number of engines is not limited.
        :param initial_pool_size: The initial number of pools to be preloaded at instantiation time.
        :param store: A RulesEnginesStore to save persistent states.
        """
        self.pool_name = pool_name
        self.rules_file = rules_file
        self.functions_package_name = functions_package_name
        self.pool_size = pool_size
        self.initial_pool_size = initial_pool_size
        self.busy_engines = deque()
        self.idle_engines = Queue()
        if initial_pool_size is not None and initial_pool_size > 0:
            self._preload_rules_engines()
        self.store = store

    def _create_and_load_rules_engine(self) -> RulesEngine:
        """
        Creates a new rules engine and loads rules on it.
        :return: The new rules engine.
        """
        return RulesEngine(self.rules_file, self.functions_package_name)

    def _preload_rules_engines(self):
        """
        Creates and loads all the rules engines in the current pool.
        """
        for i in range(self.initial_pool_size):
            self.idle_engines.put(self._create_and_load_rules_engine())

    def _acquire_rules_engine(self) -> RulesEngine:
        """
        Acquires a rules engine from the pool. If there is not any available engine then the current process is blocked
        until one is ready.
        :return: An idle rules engine.
        """
        if self.idle_engines.qsize() == 0 and (self.pool_size == -1 or len(self.busy_engines) < self.pool_size):
            # Instantiate and load a new rules engine (on demand)
            engine = self._create_and_load_rules_engine()
            self.idle_engines.put(engine)
        engine = self.idle_engines.get()
        self.busy_engines.append(engine)
        return engine

    def acquire_rules_engine(self, id: Text= None) -> RulesEngine:
        """
        Acquires a rules engine from the pool. If there is not any available engine then the current process is blocked
        until one is ready.
        If a not None `id` is provided the previously stored persistent state coresponding to this id is tried to be
        loaded into the engine. If no information is found for the id then the rules engine in returned empty.
        The management of the persistence id is made externally to the rules engine pool.

        :param id: The id of the persistent state. If None, no persistent state is loaded.

        :return: An idle rules engine.
        """
        rules_engine = self._acquire_rules_engine()
        if id is not None:
            self.load_persisted_state(rules_engine, id)
        return rules_engine

    def release_rules_engine(self, rules_engine: RulesEngine, id: Text= None):
        """
        Releases a rules engine and marks it as idle. Just after releasing a reset operation is executed on the engine
        to reinitialize it.
        :param rules_engine: The rules engine to release.
        :param id: If not None, persist the current state of the rules engine into this id. Default: None.
        """
        if id is not None:
            self.persist_engine(rules_engine, id)
        self.busy_engines.remove(rules_engine)
        rules_engine.reset()
        self.idle_engines.put(rules_engine)

    def persist_engine(self, rules_engine: RulesEngine, id: Text):
        """
        Save the current state of a rules engine into a persistent storage.

        :param rules_engine:
        :param id:
        """
        if self.store is None:
            raise PersistenceError("No RulesEngineStore has been configured!")
        else:
            logger.debug('Saving persisted state for id="{}"'.format(id))
            self.store.save_persistent_state(rules_engine, id)

    def load_persisted_state(self, rules_engine: RulesEngine, id: Text):
        """
        Load a persisted state into a rules engine.

        :param rules_engine:
        :param id: The id of the persisted state.
        """
        if self.store is None:
            raise PersistenceError("No RulesEngineStore has been configured!")
        else:
            logger.debug('Reading persisted state for id="{}"'.format(id))
            self.store.load_persistent_state(rules_engine, id)

    def clear_persistent_state(self, id: Text):
        """
        Clears the persisted state identified by a given id.

        :param id: The identifier to clear.
        """
        if self.store is None:
            logger.debug('Clearing persisted state for id="{}"'.format(id))
            raise PersistenceError("No RulesEngineStore has been configured!")
        else:
            self.store.clear_persistent_state(id)
