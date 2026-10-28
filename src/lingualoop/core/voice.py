"""Provider-neutral speech ports. Audio is transient, outside learning history."""
from typing import Protocol


class SpeechToTextProvider(Protocol):
    async def transcribe(self, audio: bytes) -> str: ...


class TextToSpeechProvider(Protocol):
    async def synthesize(self, text: str) -> bytes: ...
