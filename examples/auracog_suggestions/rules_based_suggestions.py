from collections import Iterable
import logging
import time
from typing import Any, Iterable, List, Text, Tuple

from auracog_rules.rules_engines import RulesEngine, RulesEnginePool, UnorderedFactValue, GenericFactValue
from .context import ContextAdapter
from auracog_suggestions.sessions import IntentSuggestion, IntentSuggestionList, Intent

logger = logging.getLogger(__name__)


class RulesBasedIntentSuggestions(object):
    """
    Rules based suggestions model.
    """

    INTENT_SUGGESTION_NAME = "intent_suggestion"

    def __init__(self, name, rules_file, functions_package_name: Text= None,
                 pool_size: int= -1, initial_pool_size: int= 2, max_reason_cycles: int= 10,
                 max_reasons_per_cycle= 1000, assert_as_multiple: Iterable[Text] = []):
        """

        :param name: The name to be assigned to the reasoner. Usually the conversation domain name.
        :param rules_file: Path to the file containing the rules.
        :param functions_package_name: The name of the package containing the external functions used in the rules.
        :param pool_size: The maximum size of the engines pool that will be used by the reasoner. If -1 it is unlimited.
        :param initial_pool_size: The initial number of preloaded rules engines that will be created at creation time.
        :param max_reason_cycles: The maximum number of reasoning cycles 'reason -> update tracker slots -> check for
               external slot changes -> reason'. When reached a
        :param max_reasons_per_cycle:
        :param assert_as_multiple: List of property names. If a property is contained in this list the corresponding
            property read from the context will be split into multiple values. Therefore, if its value is a list
            of elements, one fact per element will be asserted into the rules engine. Example:
            If the value returned by the context to the property "user" is
            ```
            "user": [
              {
                "id": 191,
                "name": "Alice"
              },
              {
                "id": 192,
                "name": "Bob"
              }
            ]
            ```
            if "user" is contained in assert_as_multiple the following facts will be asserted into the rules engine:
            ```
            (user (id 191) (name "Alice"))
            (user (id 192) (name "Bob"))
            ```
            In this example, if "name" is not contained in assert_as_multiple then a single unordered "user" fact is
            tried to be built and asserted. Since the elements of the list are not primitive Python values teh assertion
            would fail.
        """
        self.name = name
        self.rules_file = rules_file
        self.functions_package_name = functions_package_name
        self.pool_size = pool_size
        self.initial_pool_size = initial_pool_size
        self.max_reason_cycles = max_reason_cycles
        self.max_reasons_per_cycle = max_reasons_per_cycle

        self.assert_as_multiple = set(assert_as_multiple) if assert_as_multiple is not None else set()

        # Instantiate the rules engine pool
        self.rules_engine_pool = RulesEnginePool.get_instance(name, rules_file,
                                                              functions_package_name= functions_package_name,
                                                              pool_size= pool_size,
                                                              initial_pool_size= initial_pool_size)

        # These properties aare used to calculate the performance of the rules engine.
        # It accumulates the time spent in rules engine processing, not taking into account other time components
        # such as response delay of external APIs during persistent slots reading.
        self._current_rules_time = 0
        self._last_rules_time = 0
        self._num_updates = 0
        self._mean_rules_time = 0
        self._max_rules_time = 0

    def _update_rules_time(self):
        self._last_rules_time = self._current_rules_time
        if self._num_updates == 0:
            self._mean_rules_time = self._current_rules_time
            self._max_rules_time = self._current_rules_time
        else:
            self._mean_rules_time = (self._mean_rules_time*self._num_updates + self._current_rules_time) / \
                                    (self._num_updates + 1)
            self._max_rules_time = max(self._max_rules_time, self._current_rules_time)
        self._num_updates += 1
        self._current_rules_time = 0

    def _tic(self):
        self._start_time = time.time()

    def _toc(self):
        self._ent_time = time.time()
        self._current_rules_time = self._ent_time - self._start_time
        self._update_rules_time()

    def get_intent_suggestion(self, user_id: Text, context_adapter: ContextAdapter) -> IntentSuggestionList:
        """
        Apply rules to get a list of suggestions for a user id given the informational elements provided by a context
        adapter.
        :param user_id:
        :param context_adapter:
        :return:
        """
        logger.info("Intents suggestions based on rules for user {} started".format(user_id))
        self._tic()
        engine = self.rules_engine_pool.acquire_rules_engine()

        # 1. Get slots values to reason on
        properties_list = self._format_properties(context_adapter.dump_properties(user_id))

        # 2. Reason
        engine.set_facts(properties_list)
        engine.reason(reason_limit=self.max_reasons_per_cycle)

        # 3. Build results
        # The facts containing the results are expected to have this form: (slot intent_suggestion <intent_id> <score>)
        # in the case of intent suggestions.
        intent_suggestions = engine.collect_fact_values(RulesBasedIntentSuggestions.INTENT_SUGGESTION_NAME)

        # Note: only the intent id is included. No name is added.
        # Sum all teh intent scorings per intent id
        res = self._sum_intent_suggestions(intent_suggestions)
        self._toc()

        logger.info("Intents suggestions based on rules for user {} finished. Spent {:.3f} ms. Mean:  {:.3f} ms, Max:  {:.3f} ms".
                    format(user_id, self._last_rules_time * 1000, self._mean_rules_time * 1000,
                    self._max_rules_time * 1000))
        return res

    def _format_properties(self, properties: Iterable[Tuple[Text, Any]]) -> List[Tuple[Text, GenericFactValue]]:
        """
        Format a list of properties to split those that should be considered as multiple values, according to the content
        of self.assert_as_multiple.

        :param properties: The list of properties (in the form of tuples (name, value)).

        :return: A list with the formatted properties (in the form of tuples (name, value)).
        """
        res = []
        for p_name, p_value in properties:
            if p_name in self.assert_as_multiple:
                if isinstance(p_value, Iterable):
                    for v in p_value:
                        # Split the multiple value
                        res.append((p_name, v))
                else:
                    # The value is not iterable. Return it as single.
                    res.append((p_name, p_value))
            else:
                res.append((p_name, p_value))
        return res

    def _sum_intent_suggestions(self, intent_suggestions: List[Tuple[Text, UnorderedFactValue]]) -> IntentSuggestionList:
        """
        Sum all the scorings for every intent suggestion.
        :param intent_suggestions:
        :return: IntentSuggestionList
        """
        d = {}
        for sug in intent_suggestions:
            intent_id = sug[0]
            score = sug[1]
            if intent_id not in d:
                # TODO: get the intent name from the intent id.
                d[intent_id] = IntentSuggestion(Intent(intent_id, None), 0)
            d[intent_id].score += score
        return IntentSuggestionList(d.values())
