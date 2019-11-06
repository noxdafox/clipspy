from typing import Any, Dict, List, Text, Iterable

from ..common import FeatureSet


class UserFeatureSet(FeatureSet):
    """
    This class represents a user.
    It contains:
      - user identifier: aura_id, aura_global_id
      - list of features
    """
    def __init__(self, features: Dict[Text, Any], aura_id_name: Text="AURA_ID",
                 aura_id_global_name: Text="AURA_ID_GLOBAL", cluster_id_name: Text= "CLUSTER_ID"):
        """
        :param features: Dictionary of features.
        :param aura_id_name: Default "AURA_ID"
        :param aura_id_global_name:  Default "AURA_ID_GLOBAL"
        :param cluster_id_name: Default "CLUSTER_ID"
        """
        super().__init__(features)
        self.aura_id_name = aura_id_name
        self.aura_id_global_name = aura_id_global_name
        self.cluster_id_name = cluster_id_name

    @property
    def aura_id(self):
        return self.get_feature(self.aura_id_name)

    @property
    def aura_id_global(self):
        return self.get_feature(self.aura_id_global_name)

    @property
    def cluster_id(self):
        return self.get_feature(self.cluster_id_name)

    @cluster_id.setter
    def cluster_id(self, cluster_id):
        self.set_feature(self.cluster_id_name, cluster_id)

    @classmethod
    def build_from_row(cls, values: List[Any], names: List[Text], aura_id_name: Text="AURA_ID",
                       aura_id_global_name: Text="AURA_ID_GLOBAL"):
        """
        Build a UserFeaturesSet from the contents of a row (composed of a list of values and corresponding names).
        :param values: List (iterable) of values
        :param names: List (iterable) of names
        :return:  List of features.
        """
        return UserFeatureSet(cls.build_features(values, names), aura_id_name=aura_id_name,
                          aura_id_global_name=aura_id_global_name)


class UserClusterModel(object):
    """
    This class represents a clustering model for users.
    """

    def predict(self, X: Iterable[UserFeatureSet], **kwargs) -> List[int]:
        """
        Predict the fittest cluster for a list of users.

        :param X: List of users to cluster.
        :return: List with the ids of the fittest clusters.
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method predict must be implemented!".format(self.__class__))

    def fit(self,  X: Iterable[UserFeatureSet], **kwargs):
        """
        :param X: List of users to cluster.
        :param kwargs:
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method fit must be implemented!".format(self.__class__))
