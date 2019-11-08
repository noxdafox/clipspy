from typing import Text, Callable, List

def get_functions_from_module_name(module_name: Text) -> List[Callable]:
    """
    Get the list of functions defined in a python module.

    :param module_name: The name of the module.

    :return: A list with the functions found. The empty list if no function is found. Only functions are returned.
    """
    module = __import__(module_name)
    res = []
    for name in dir(module):
        if is_user_function(module, name):
            res.append(eval("module.{}".format(name)))
    return res

def is_user_function(module, name: Text) -> bool:
    """
    Get whether a
    :param module:
    :param name:
    :return:
    """

    if name.startswith("__") and name.endswith("__"):
        return False
    return callable(eval("module.{}".format(name)))
