from typing import Any, Dict, List, Text


class FeatureSet(object):
    """
    This class represents a generic session.
    """

    def __init__(self, features: Dict[Text, Any]):
        self.features = features

    @classmethod
    def build_from_row(cls, values: List[Any], names: List[Text]):
        """
        Build a FeatureSet from the contents of a row (composed of a list of values and corresponding names).
        :param values: List (iterable) of values
        :param names: List (iterable) of names
        """
        return FeatureSet(cls.build_features(values, names))

    @classmethod
    def build_features(cls, values: List, names: List) -> Dict[Text, Any]:
        """
        Build feature objects from the contents of a vector (row)
        :param values: List (iterable) of values
        :param names: List (iterable) of names
        :return: Dictionary of features.
        """
        features = {}
        assert(len(values) == len(names))
        for i, val in enumerate(values):
            features[names[i]] = val
        return features

    def get_feature(self, name: str, default: Any= None) -> Any:
        return self.features.get(name, default=default)

    def set_feature(self, feature: Any):
        self.features[feature.name] = feature

    def del_feature(self, feature: Any):
        del self.features[feature.name]

    def __str__(self):
        res = "{}:[{}]".format(self.__class__, self.features)
        return res



