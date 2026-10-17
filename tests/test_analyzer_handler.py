import json

import fakeredis
from analyzer.cache import AnalysisCache
from analyzer.handler import make_handler
from analyzer.llm import FakeLLMClient
from common.sessions import SessionStatus
from transcriber.engines import FakeTranscriber


def at_transcribed(repo):
    session_id = repo.create("a.mp4")
    repo.advance(session_id, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED)
    repo.advance(session_id, SessionStatus.AUDIO_EXTRACTED, SessionStatus.TRANSCRIBED)
    return session_id


def handler(repo, storage):
    cache = AnalysisCache(fakeredis.FakeRedis(decode_responses=True))
    return make_handler(repo, storage, FakeLLMClient(), cache)


def test_analyzes_transcript_and_saves_result(repo, storage, published):
    session_id = at_transcribed(repo)
    transcript = {"utterances": FakeTranscriber().transcribe(None)}
    storage.objects[("transcripts", f"{session_id}.json")] = json.dumps(transcript).encode()

    handler(repo, storage)({"session_id": session_id}, published)

    analysis = repo.get_analysis(session_id)
    assert analysis["session_id"] == session_id
    assert analysis["patient_speaker"] == "B"
    assert analysis["topics_summary"] == {"family": 1, "work": 1}
    assert repo.get(session_id)["status"] == "ANALYZED"
    assert published.events == [("session.analyzed", {"session_id": session_id})]


def test_duplicate_after_finish_does_not_reanalyze(repo, storage, published):
    session_id = at_transcribed(repo)
    repo.advance(session_id, SessionStatus.TRANSCRIBED, SessionStatus.ANALYZED)
    handler(repo, storage)({"session_id": session_id}, published)
    assert repo.get_analysis(session_id) is None
    assert published.events == [("session.analyzed", {"session_id": session_id})]
