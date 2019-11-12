from .rules_engines import RulesEngine

import logging
import os
from typing import Text


logger = logging.getLogger(__name__)


class RulesEnginesStore(object):
    """
    Base class for rules engine stores.
    """

    def load_persistent_state(self, rules_engine: RulesEngine, id: Text):
        """
        Loads a persisted state into a rules engine.

        :param rules_engine: The rules engine.
        :param id: The id of the persisted state.
        """
        raise NotImplementedError("This method should be implemented by subclasses!")

    def save_persistent_state(self, rules_engine: RulesEngine, id: Text):
        """
        Save the current state of a rules engine and associates it to a given id.

        :param rules_engine: The rules engine.
        :param id: The identifier to persist to.
        """
        raise NotImplementedError("This method should be implemented by subclasses!")

    def clear_persistent_state(self, id: Text):
        """
        Clears the persisted state identified by a give id.

        :param id: The identifier to clear.
        """
        raise NotImplementedError("This method should be implemented by subclasses!")


class LocalFileRulesEngineStore(RulesEnginesStore):
    """
    This rules engine stores persistent states into a folder into the local machine.
    Each persistent state is stored as file into this folder. The name of the files follow this format:
    <floder_path>/<id>.persist
    """

    def __init__(self, folder_path: Text, binary: bool= True):
        """
        :param folder_path: The path to the persistence folder.
        :param binary: If True the state is saved as a binary file. Default: True.
        """
        self.folder_path = folder_path
        self.binary = binary

    def _build_path(self, id: Text):
        return os.path.join(self.folder_path, "{}.persist".format(id))

    def load_persistent_state(self, rules_engine: RulesEngine, id: Text):
        _path = self._build_path(id)
        if os.path.exists(_path):
            rules_engine.env.eval("(load-facts {})".format(self._build_path(id)))
        else:
            logger.warn('No persisted state found for id="{}"'.format(id))

    def save_persistent_state(self, rules_engine: RulesEngine, id: Text):
        rules_engine.env.eval("(save-facts {})".format(self._build_path(id)))

    def clear_persistent_state(self, id: Text):
        _path = self._build_path(id)
        if os.path.exists(_path):
            os.remove(self._build_path(id))
        else:
            logger.warn('No persisted state found for id="{}"'.format(id))
