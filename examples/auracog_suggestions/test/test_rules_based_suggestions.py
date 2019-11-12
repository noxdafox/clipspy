from auracog_suggestions import RulesBasedIntentSuggestions
from auracog_suggestions import TestJsonContextAdapter

import logging
from logging.config import dictConfig
import yaml

from memory_profiler import profile

CONFIG_LOGGING = "../examples/config/logging.yml"


#@profile  # Uncoment this line for memory profiling
def main():
    # Configure logging
    #    with open(CONFIG_LOGGING, 'r') as f:
    #        log_cfg = yaml.safe_load(f.read())
    #    dictConfig(log_cfg)
    ##    logger = logging.getLogger("rules")
    #     logger = logging.getLogger(__name__)

    logging.basicConfig(format="[%(levelname)s] %(asctime)s.%(msecs)03d - %(name)s: %(message)s",
                        datefmt="%d-%m-%Y %H:%M:%S",
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    name = "rules_based_suggestions"
    rules_files = ["../examples/auracog_suggestions/exploratory_intent_suggestions_rules.clp"]
    functions_package_name = "auracog_suggestions.custom_functions"
    pool_size = -1
    initial_pool_size = 2
    max_reason_cycles = 10
    max_reasons_per_cycle = 1000
    assert_as_multiple = ["intent"]

    logger.debug("Instantiating suggestions model")
    sug = RulesBasedIntentSuggestions(name, rules_files, functions_package_name=functions_package_name,
                                      pool_size=pool_size, initial_pool_size=initial_pool_size,
                                      max_reason_cycles=max_reason_cycles,
                                      max_reasons_per_cycle=max_reasons_per_cycle,
                                      assert_as_multiple=assert_as_multiple)

    context_json_file = "../examples/auracog_suggestions/context_data.json"
    context_adapter = TestJsonContextAdapter(context_json_file, ["user", "general", "intent", "current_session"])
    user_id = "user1"

    intent_suggestion = sug.get_intent_suggestion(user_id, context_adapter)

    print(intent_suggestion)


if __name__ == "__main__":
    main()
