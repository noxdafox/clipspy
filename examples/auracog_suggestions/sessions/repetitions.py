from .sessions import SessionFeatureSet

from typing import Iterable, List


class SessionRepetitionsModel(object):
    """
    This is the base cass for Session Repetition Models.
    Their goal is to predict whether a given session can be considered as a "Repetition", i.e. a sequence of actions
    repeatedly requested by a given user.
    Repetitions trend to indicate that the user requests could not be successfully attended.
    """

    def fit(self, X:Iterable[SessionFeatureSet], Y:Iterable[float], **kwargs):
        """
        Train the current model instance.

        :param X: List of training sessions.
        :param Y: List of expected results. List of floats in the interval [0.0, 1.0]
        :param kwargs: Additional optional parameters to be used by specific implementations.
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method fit must be implemented!".format(self.__class__))

    def predict(self, X:Iterable[SessionFeatureSet]) -> List[float]:
        """
        Predict whether a given session can be considered as a Repetition.
        :param X: List of sessions to predict.
        :return:
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method fit must be implemented!".format(self.__class__))


class ThresholdBasedSessionRepetitionModel(SessionRepetitionsModel):
    """
    Simple model based on a threshold over a given feature.
    """

    def __init__(self, feature_name: str, threshold: float):
        self.feature_name = feature_name
        self.threshold = threshold

    def fit(self, X:Iterable[SessionFeatureSet], Y:Iterable[float], **kwargs):
        pass

    def predict(self, X:Iterable[SessionFeatureSet]):
        return [1.0 if s.get_feature(self.feature_name) >= self.threshold else 0 for s in X]
