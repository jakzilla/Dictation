"""Local Whisper transcription via faster-whisper."""

import numpy as np
from faster_whisper import WhisperModel

from config import COMPUTE_TYPE, SAMPLE_RATE


class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
        self.load_model(model_size)

    def load_model(self, model_size):
        print(f"Loading Whisper model '{model_size}'...")
        self.model_size = model_size
        self.model = WhisperModel(model_size, device="cpu", compute_type=COMPUTE_TYPE)
        # Warm up CTranslate2 JIT
        dummy = np.zeros(SAMPLE_RATE, dtype=np.float32)
        list(self.model.transcribe(dummy, language="en")[0])
        print(f"Model '{model_size}' loaded and ready.")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.3,
                min_silence_duration_ms=500,
                min_speech_duration_ms=100,
            ),
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()
