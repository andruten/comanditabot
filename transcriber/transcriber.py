import logging
import os
import time
from typing import Dict

import whisper

logger = logging.getLogger(__name__)

whisper_model = os.environ.get('WHISPER_MODEL', default='tiny')
device = os.environ.get('WHISPER_DEVICE', default='cpu')

_model = whisper.load_model(whisper_model, device=device)


class AudioTranscriber:

    @property
    def model(self) -> whisper.Whisper:
        return _model

    def transcribe_audio(self, mp3_audio_path: str) -> Dict:
        start_time = time.time()
        audio = whisper.load_audio(mp3_audio_path)
        result = self.model.transcribe(audio)
        final_time = time.time()
        logger.info(f'Audio processed in {final_time - start_time}')
        return result

    def escape_markdown_chars(self, text: str) -> str:
        escaping_chars = ['_', '*', '[', ']', '(', ')', '~', '>', '+', '-', '=', '|', '{', '}', '.', '!']
        temporal = text
        for char in escaping_chars:
            temporal = temporal.replace(char, f"\\{char}")
        return temporal

    def get_as_markdown(self, text: Dict) -> str:
        transcription = text["text"].removeprefix(" ")
        markdown_message = f'''\
```
{transcription}
```
'''
        return self.escape_markdown_chars(markdown_message)


audio_transcriber = AudioTranscriber()
