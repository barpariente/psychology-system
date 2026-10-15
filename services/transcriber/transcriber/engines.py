from pathlib import Path
from typing import Protocol

from common.config import Settings


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> list[dict]: ...


class AssemblyAITranscriber:
    """Speaker-labelled transcription through AssemblyAI. `transcribe` blocks until done."""

    def __init__(self, api_key: str):
        import assemblyai as aai

        aai.settings.api_key = api_key
        self._aai = aai

    def transcribe(self, audio_path: Path) -> list[dict]:
        config = self._aai.TranscriptionConfig(speaker_labels=True)
        transcript = self._aai.Transcriber().transcribe(str(audio_path), config=config)
        if transcript.status == self._aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI error: {transcript.error}")
        return [
            {"speaker": u.speaker, "text": u.text, "start_ms": u.start, "end_ms": u.end}
            for u in transcript.utterances or []
        ]


class FakeTranscriber:
    """Deterministic transcript for local demos and CI (FAKE_AI=true)."""

    def transcribe(self, audio_path: Path) -> list[dict]:
        return [
            {"speaker": "A", "text": "How have you been feeling this week?",
             "start_ms": 0, "end_ms": 2000},
            {"speaker": "B", "text": "I keep arguing with my mother and it makes me anxious.",
             "start_ms": 2000, "end_ms": 6000},
            {"speaker": "A", "text": "What usually happens during those arguments?",
             "start_ms": 6000, "end_ms": 8500},
            {"speaker": "B", "text": "Work has been better though, I got really good feedback.",
             "start_ms": 8500, "end_ms": 12000},
        ]


def build_transcriber(settings: Settings) -> Transcriber:
    if settings.fake_ai:
        return FakeTranscriber()
    if not settings.assemblyai_api_key:
        raise RuntimeError("ASSEMBLYAI_API_KEY is required when FAKE_AI is false")
    return AssemblyAITranscriber(settings.assemblyai_api_key)
