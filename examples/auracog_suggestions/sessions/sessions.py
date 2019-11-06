from typing import Any, Dict, Iterable, List, Text

from ..common import FeatureSet


class SessionFeatureSet(FeatureSet):
    """
    This class represents a session's set of features.
    """

    def __init__(self, features: Dict[Text, Any], aura_id_name="AURA_ID", aura_id_global_name="AURA_ID_GLOBAL",
                 session_id_name="SESSION_ID"):
        """
        :param features: dictionary of features.
        :param aura_id_name: the name of the aura_id feature.
        :param aura_id_global_name: the name of the aura_id_global feature.
        :param session_id_name: the name of the session_id feature.
        """
        super().__init__(features)
        self.aura_id_name = aura_id_name
        self.aura_id_global_name = aura_id_global_name
        self.session_id_name = session_id_name

    @property
    def aura_id(self):
        return self.get_feature(self.aura_id_name)

    @property
    def aura_id_global(self):
        return self.get_feature(self.aura_id_global_name)

    @property
    def session_id(self):
        return self.get_feature(self.session_id_name)

    @classmethod
    def build_from_row(cls, values: List[Any], names: List[Text], aura_id_name="AURA_ID",
                       aura_id_global_name="AURA_ID_GLOBAL"):
        """
        Build a SessionFeaturesSet from the contents of a row (composed of a list of values and corresponding names).
        :param values: list of feature values.
        :param names: list of the corresponding names.
        :param aura_id_name: the name of the aura_id feature.
        :param aura_id_global_name: the name of the aura_id_global feature.
        :param session_id_name: the name of the session_id feature.
        """
        return SessionFeatureSet(cls.build_features(values, names), aura_id_name=aura_id_name,
                          aura_id_global_name=aura_id_global_name, session_id_name=aura_id_global_name)


class SessionClusterModel(object):
    """
    This class represents a clustering model for sessions.
    """

    def predict(self, X: Iterable[SessionFeatureSet], **kwargs) -> List[int]:
        """
        Predict the fittest cluster for a list of sessions.

        :param X: List of sessions to cluster.
        :return: List with the ids of the fittest clusters.
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method predict must be implemented!".format(self.__class__))

    def fit(self,  X: Iterable[SessionFeatureSet], **kwargs):
        """
        :param X: List of sessions to cluster.
        :param kwargs:
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method fit must be implemented!".format(self.__class__))
