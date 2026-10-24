"""Resilient wrapper around PicklePersistence to survive corrupted state files."""

import logging
import pickle
import shutil

from telegram.ext import PicklePersistence

logger = logging.getLogger(__name__)


class ResilientPicklePersistence(PicklePersistence):
    """Keep a backup of the state file and recover from corruption.

    Before every dump the current state file is copied to a sidecar backup
    (``<filepath>.bak``). When the main file turns out to be unreadable at
    startup, the backup is restored; if there is no readable backup the bot
    starts with an empty state instead of crashing in application setup.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._backup_path = self.filepath.with_name(self.filepath.name + ".bak")

    def _dump_singlefile(self) -> None:
        self._copy_current_state_to_backup()
        super()._dump_singlefile()

    def _load_singlefile(self) -> None:
        try:
            super()._load_singlefile()
        except (pickle.UnpicklingError, TypeError) as error:
            logger.warning(
                "The bot state file %s is corrupted: %s", self.filepath, error
            )
            self._recover_or_reset()

    def _copy_current_state_to_backup(self) -> None:
        if not self.filepath.is_file():
            return
        try:
            shutil.copyfile(self.filepath, self._backup_path)
        except OSError as error:
            logger.warning("Could not back up the bot state file: %s", error)

    def _recover_or_reset(self) -> None:
        corrupted_path = self.filepath.with_name(self.filepath.name + ".corrupt")
        try:
            shutil.copyfile(self.filepath, corrupted_path)
            logger.warning("The corrupted state file was parked at %s", corrupted_path)
        except OSError as error:
            logger.warning("Could not park the corrupted state file: %s", error)

        try:
            shutil.copyfile(self._backup_path, self.filepath)
        except OSError as error:
            logger.error(
                "Could not restore the state backup from %s: %s; "
                "starting with an empty state",
                self._backup_path,
                error,
            )
            self._reset_state()
            return

        try:
            super()._load_singlefile()
            logger.warning("Restored the last valid state from %s", self._backup_path)
        except (pickle.UnpicklingError, TypeError) as error:
            logger.error(
                "The state backup %s is also corrupted: %s; "
                "starting with an empty state",
                self._backup_path,
                error,
            )
            self._reset_state()

    def _reset_state(self) -> None:
        self.conversations = {}
        self.user_data = {}
        self.chat_data = {}
        self.bot_data = self.context_types.bot_data()
        self.callback_data = None
