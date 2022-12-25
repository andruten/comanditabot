import logging
import os
import tempfile
from typing import Union

from pydub import AudioSegment
from telegram import Voice, Audio
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)


class TelegramAudioManager:

    def __init__(
            self,
            context: CallbackContext,
            file: Union[Voice, Audio],
            file_download_path=None,
    ) -> None:
        if not isinstance(file, Audio) and not isinstance(file, Voice):
            raise RuntimeError('file must be an Audio or Voice instance')
        if file_download_path is None:
            file_download_path = tempfile.gettempdir()
        self.context = context
        self.file = file
        self.ogg_audio_path = os.path.join(file_download_path, f'{file.file_unique_id}.ogg')
        self.mp3_audio_path = f'{self.ogg_audio_path}.mp3'

    def __enter__(self) -> str:
        self._download_voice_message()
        return self.mp3_audio_path

    def __exit__(self, *args, **kwargs):
        self._clean_up_files()
        return True

    def _clean_up_files(self):
        logger.debug(f'Removing temporary file {self.mp3_audio_path}')
        os.remove(self.mp3_audio_path)
        logger.debug(f'Removing temporary file {self.ogg_audio_path}')
        os.remove(self.ogg_audio_path)

    def _download_voice_message(self):
        new_file = self.context.bot.get_file(self.file.file_id)
        new_file.download(custom_path=self.ogg_audio_path)
        self._convert_ogg_to_mp3(self.ogg_audio_path, self.mp3_audio_path)

    def _convert_ogg_to_mp3(self, ogg_file_path, mp3_file_path):
        given_audio = AudioSegment.from_file(ogg_file_path, format="ogg")
        given_audio.export(mp3_file_path, format="mp3")
