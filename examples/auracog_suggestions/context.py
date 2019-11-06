import json
from typing import Any, Dict, Iterable, List, Text, Tuple


class PropertyNotDefined(Exception):
    pass


class ContextAdapter(object):
    """
    This class encapsulates the operations to access to the Aura Context and other external APIs or databases.:
    - centralizes read/write operations
    - optimizes access to the Aura Context or even to external entities.

    This is an abstract class. Any extending class must implement the read_property and write_property methods.
    This class assumes that the data is organized in the form of name properties, whose values may be of different types, but
    typically:
        - A primitive python type
        - A list
        - A dictionary
        - A plain object

    Property names are thought to be unique. If multiple values are possible for the same property reconsider it as a list of
    values.
    """

    def read_property(self, property_name: Text, user_id: Text) -> Any:
        """
        This method gets the value of a persistent property, reading it from external storage / APIs.
        It must be implemented for every conversation / type of context.
        :param property_name: The path to the context property.
        :param user_id: The user identifier.
        :return: The value of the persistent property and its expiration time: (value, expires)
        """
        raise NotImplemented("The method read_property() is not yet implemented,")

    def write_property(self, property_name: Text, user_id: Text, value: Any):
        """
        Write a value into a persistent property, writing it to external storage / APIs.
        It must be implemented for every conversation / type of context.
        :param property_name: The path to the context property.
        :param user_id: The user identifier.
        :param value: The value of the property to be set
        """
        raise NotImplemented("The method write_property() is not yet implemented!!")

    def get_property_names(self) -> List[Text]:
        """
        :return: The property names defined in the current context adapter.
        """
        raise NotImplemented("The method get_property_names() is not yet implemented.")

    def dump_properties(self, user_id: Text) -> List[Tuple[Text, Any]]:
        """
        :param user_id: The user identifier.

        :return: A list containing all the properties defined in the current context adapter.
        A list with the following structure:
            [[<property_name>, <property_value>]*]
        """
        return [(property_name, self.read_property(property_name, user_id)) for property_name in self.get_property_names()]


class MappingContextAdapter(ContextAdapter):
    """
    This Context Adapter defines a bijective mapping property_name <-> context_path. This makes easier the use of the
    properties of the Aura Context in systems such a as rules engines. Context properties are translated into named
    properties: pairs name - value. These properties can be then easily imported into a rules engine working memory.

    This is an abstract class. Any extending class must implement the _read_property and _write_property methods.
    """

    def __init__(self, context_mapping: Dict[Text, Text]):
        """
        :param context_mapping: Mapping between Context LLocation to property names. Format:
         {<path_in_context>: <property_name>}.
         This mapping must be bijective.
        """
        self.context_mapping = context_mapping
        self.inverse_context_mapping = {v: k for k, v in context_mapping.items()}

    def read_property(self, property_name: Text, aura_id_global: Text) -> Any:
        """
        Get the value of a property.
        :param property_name: The name of the property.
        :param aura_id_global: The global Aura ID.
        :return:
        """
        if property_name not in self.inverse_context_mapping:
            raise PropertyNotDefined("The property {} is not defined in current mapping.".format(property_name))
        return self._read_property(self.inverse_context_mapping[property_name], aura_id_global)

    def _read_property(self, context_path: Text, aura_id_global: Text) -> Any:
        """
        This method gets the value of a persistent property, reading it from external storage / APIs.
        It must be implemented for every conversation / type of context.
        :param context_path: The path to the context property.
        :param aura_id_global: The global Aura ID.
        :return: The value of the persistent property and its expiration time: (value, expires)
        """
        raise NotImplemented("The method _read_property() is not yet implemented.")

    def write_property(self, property_name: Text, aura_id_global: Text, property_value: Any):
        """
        Set the value of a property.
        :param property_name: The name of the property.
        :param aura_id_global: The global Aura ID.
        :param property_value:
        """
        if property_name not in self.inverse_context_mapping:
            raise PropertyNotDefined("The property {} is not defined in current mapping.".format(property_name))
        self._write_property(self.inverse_context_mapping[property_name], aura_id_global, property_value)

    def _write_property(self, context_path: Text, aura_id_global: Text, value: Any):
        """
        Write a value into a persistent property, writing it to external storage / APIs.
        It must be implemented for every conversation / type of context.
        :param context_path: The path to the context property.
        :param aura_id_global: The global Aura ID.
        :param value: The value to be set.
        """
        raise NotImplemented("Te method _write_property is not yet implemented.")

    def get_property_names(self) -> List[Text]:
        """
        :return:
        """
        return list(self.inverse_context_mapping.keys())

    def get_property_paths(self) -> List[Text]:
        """
        :return:
        """
        return list(self.context_mapping.keys())


class ContextManagerContextAdapter(MappingContextAdapter):
    """
    Prototype implementation based on the Context Manager prototype
    (https://github.com/Telefonica/aura-cognitive-containers/tree/master/context_manager).
    """

    def __init__(self, context_mapping: Dict[Text, Text]):
        super().__init__(context_mapping)


class TestJsonContextAdapter(ContextAdapter):
    """
    Context adapter for testing that reads its values from a JSON file.
    The structure of the JSON must be
    {
        <user_id>: {
            <property_name>: <property_value>
        }
    }
    """

    def __init__(self, json_file: Text, properties_to_read: Iterable[Text]):
        """
        :param json_file: JSON file containing the data.
        :param properties_to_read: List of property names to be read.
        """
        with open(json_file) as f:
            self.json_dict = json.load(f)
        self.properties_to_read = properties_to_read

    def read_property(self, property_name: Text, user_id: Text) -> Any:
        return self.json_dict[user_id][property_name]

    def write_property(self, property_name: Text, user_id: Text, value: Any):
        self.json_dict[user_id][property_name] = value

    def get_property_names(self) -> List[Text]:
        return list(self.properties_to_read)

