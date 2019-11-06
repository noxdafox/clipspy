from typing import Dict, Iterable, List, Text, Union
import logging

from .sessions import SessionFeatureSet
from .users import UserFeatureSet

logger = logging.getLogger(__name__)


class Intent(object):
    """
    This class represents an intent.
    """

    def __init__(self, code: int, name: str):
        """
        :param code:
        :param name:
        """
        self.code = code
        self.name = name

    def __str__(self):
        return "Intent:[code:{}, name:{}]".format(self.code, self.name)

    def __eq__(self, other):
        if isinstance(other, Intent):
            return False
        return other.intent == self.code


class IntentPrediction(object):
    """
    Intent prediction.
    """
    def __init__(self, intent: Intent, score: float):
        self.intent = intent
        self.score = score


class NextIntentsModel(object):

    def predict(self, sessions: Iterable[SessionFeatureSet], num_steps: int= 1,
                **kwargs) -> List[List[IntentPrediction]]:
        """
        Predict the next intents given a session.

        :param sessions: List of sessions to predict.
        :param num_steps: The number of steps to bee predicted.
        :return:
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method predict must be implemented!".format(self.__class__))

    def fit(self, X: Iterable[SessionFeatureSet], **kwargs):
        """
        :param X: List of sessions with the training data.
        :param kwargs:
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method fit must be implemented!".format(self.__class__))

class NextIntentRestrictions(object):
    """
    Abstract class for the restrictions to be applied during the prediction of next intents.
    """

    def __init__(self, forbidden_intent_codes: List[int]):
        """
        :param forbidden_intent_codes: List of forbidden intent codes, i.e. intents that should not predicted as a
        suggestion.
        """
        self.forbidden_intents_codes = forbidden_intent_codes

    def apply(self, intent_prediction: IntentPrediction, session: SessionFeatureSet, user: UserFeatureSet) -> bool:
        """
        Apply the current restrictions to one intent prediction given the current session and user features.
        :param intent_prediction:
        :param session: session features.
        :param user: user features.
        :return: True if restriction must be applied; False otherwise.
        """
        if self.forbidden_intents_codes is not None and intent_prediction.intent.code in self.forbidden_intents_codes:
            return False
        return self._apply(intent_prediction, session, user)

    def _apply(self, intent_prediction: IntentPrediction, session: SessionFeatureSet, user: UserFeatureSet) -> bool:
        """
        Apply the current restrictions to one intent prediction given the current session and user features.
        :param intent_prediction:
        :param session: session features.
        :param user: user features.
        :return: True if restriction must be applied; False otherwise.
        """
        raise NotImplementedError("{} is an abstract class and cannot be directly instantiated. "
                                  "The method _apply must be implemented!".format(self.__class__))

class IntentSuggestion(object):
    """
    This class represents an intent suggestion, including:
    - the intent
    - the score assigned to that intent.
    """

    def __init__(self, intent: Intent, score: float):
        self.intent = intent
        self.score = score
        self.normalized_score = None

    def __str__(self):
        return "Suggestion[intent:{}, score:{}, normalized_score:{}]".format(self.intent, self.score,
                                                                             self.normalized_score)

    def __eq__(self, other):
        if isinstance(other, IntentSuggestion):
            return False
        return other.intent == self.intent


class IntentSuggestionList(object):
    """
    This class represents a list of intent suggestions for one step.
    """

    def __init__(self, intent_suggestions: List[IntentSuggestion] = [], sort=True):
        """
        :param intent_suggestions:
        :param sort: Whether to sort on scores
        """
        self.intent_suggestions = intent_suggestions
        if sort:
            self.sort()
        self._normalize()

    def sort(self):
        """
        Sorts the current list of intent suggestions.
        :return:
        """
        self.intent_suggestions = sorted(self.intent_suggestions, key= lambda sugg: sugg.score, reverse=True)

    def _normalize(self):
        _total = 0
        _min = min([s.score for s in self.intent_suggestions])
        for sugg in self.intent_suggestions:
            sugg.normalized_score = sugg.score + abs(_min)
        for sugg in self.intent_suggestions:
            _total += sugg.normalized_score
        for sugg in self.intent_suggestions:
            sugg.normalized_score = sugg.normalized_score / _total if _total != 0 else 0

    def append(self, intent_suggestion: IntentSuggestion, sort=True):
        """
        Append one IntentSuggestion to the current list.
        :param intent_suggestion:
        :param sort: Whether to sort on scores
        """
        self.intent_suggestions.append(intent_suggestion)
        if sort:
            self.sort()

    def remove(self, intent_suggestion: IntentSuggestion):
        """
        Remove one Intent Suggestion from the current list.
        :param intent_suggestion:
        """
        self.intent_suggestions.remove(intent_suggestion)

    def __str__(self):
        return "SuggestionList[{}]".format(", ".join([str(s) for s in self.intent_suggestions]))


class SuggestNextIntentsModel(object):
    """
    This class is used to generate a suggestion on intents.
    """

    def __init__(self, next_intents_model_dict: Dict[Union[Text, int], NextIntentsModel],
                 next_intent_restrictions: NextIntentRestrictions):
        """
        :param next_intents_model_dict: Dictionary of NextIntentsModels. Key is the user cluster id to which every model
        :param next_intent_restrictions: Restrictions to apply to the generation of suggestions.
        will be applied to.
        """
        self.model_dict = next_intents_model_dict,
        self.restrictions = next_intent_restrictions

    def suggest(self, sessions: List[SessionFeatureSet], users: List[UserFeatureSet], num_steps: int= 1) \
                -> List[List[IntentSuggestionList]]:
        """
        Get a suggestion of next intents on a session.
        :param sessions: List of sessions to be analyzed.
        :param users: List of user features corresponding to the sessions.
        :param num_steps: the number of steps to predict/suggest

        :return: List of suggested next intents. Every suggestion consists of a list of IntentSuggestion elements.
        One suggestion is returned for every step (num_steps). Therefore, the resulting type is list of lists of
        IntentSuggestionLists.
        """
        assert(len(sessions) == len(users))

        res = []
        for i, session in enumerate(sessions):
            user = users[i]
            # Get the next intent prediction model to apply
            intent_pred_model = self.model_dict[user.cluster_id]
            if intent_pred_model is None:
                logger.error("No NextIntentsModel is defined for user cluster {}".format(user.cluster_id))
                res.append(None)
            else:
                res_sugg = []
                next_intents = intent_pred_model.predict(session, num_steps=num_steps)
                for step in next_intents:
                    filtered_intents = [intent for intent in step if not self.restrictions.apply(intent, session,
                                                                                                     user)]
                    sugg_list = [IntentSuggestion(intent.intent, intent.score) for intent in filtered_intents]
                    res_sugg.append(IntentSuggestionList(sugg_list))
                res.append(res_sugg)
        return res
