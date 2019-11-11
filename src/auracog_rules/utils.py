from typing import Text, Callable, List
import importlib

def get_functions_from_module_name(module_name: Text) -> List[Callable]:
    """
    Get the list of functions defined in a python module.

    :param module_name: The name of the module.

    :return: A list with the functions found. The empty list if no function is found. Only functions are returned.
    """

    module = importlib.import_module(module_name)
    res = []
    for name in dir(module):
        if not(name.startswith("__") and name.endswith("__")) and callable(eval("module.{}".format(name))):
            res.append(eval("module.{}".format(name)))
    return res
