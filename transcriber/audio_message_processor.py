from telegram import Update
from telegram.ext import CallbackContext

from transcriber.telegram_file_manager import TelegramAudioManager
from transcriber.transcriber import audio_transcriber


class AudioMessageTranscriberMixin:

    def transcribe(self, context: CallbackContext, audio) -> str:
        with TelegramAudioManager(context, audio) as mp3_audio_path:
            try:
                result = audio_transcriber.transcribe_audio(mp3_audio_path)
                text = audio_transcriber.get_as_markdown(result)
            except Exception as e:
                text = f'Error converting video to audio. Exception={e}'
        return text
