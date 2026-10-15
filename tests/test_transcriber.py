import json

import pytest
from common.config import load_settings
from common.sessions import SessionStatus
from transcriber.engines import FakeTranscriber, build_transcriber
from transcriber.handler import make_handler


class ExplodingTranscriber:
    def transcribe(self, audio_path):
        raise AssertionError("should not transcribe")


def at_audio_extracted(repo):
    session_id = repo.create("a.mp4")
    repo.advance(session_id, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED)
    return session_id


def test_transcribes_and_stores_json(repo, storage, published):
    session_id = at_audio_extracted(repo)
    storage.objects[("audio", f"{session_id}.mp3")] = b"mp3"
    make_handler(repo, storage, FakeTranscriber())({"session_id": session_id}, published)

    stored = json.loads(storage.objects[("transcripts", f"{session_id}.json")])
    assert stored["utterances"] == FakeTranscriber().transcribe(None)
    assert repo.get(session_id)["status"] == "TRANSCRIBED"
    assert published.events == [("session.transcribed", {"session_id": session_id})]


def test_duplicate_after_finish_republishes_without_work(repo, storage, published):
    session_id = at_audio_extracted(repo)
    repo.advance(session_id, SessionStatus.AUDIO_EXTRACTED, SessionStatus.TRANSCRIBED)
    make_handler(repo, storage, ExplodingTranscriber())({"session_id": session_id}, published)
    assert published.events == [("session.transcribed", {"session_id": session_id})]


def test_fake_transcript_has_two_speakers():
    speakers = {u["speaker"] for u in FakeTranscriber().transcribe(None)}
    assert speakers == {"A", "B"}


def test_build_transcriber_uses_fake_in_fake_mode():
    assert isinstance(build_transcriber(load_settings({"FAKE_AI": "true"})), FakeTranscriber)


def test_build_transcriber_requires_key_in_real_mode():
    with pytest.raises(RuntimeError, match="ASSEMBLYAI_API_KEY"):
        build_transcriber(load_settings({}))
