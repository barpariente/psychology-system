from common.sessions import SessionStatus


def test_create_starts_uploaded(repo):
    session_id = repo.create("a.mp4")
    session = repo.get(session_id)
    assert session["session_id"] == session_id
    assert session["filename"] == "a.mp4"
    assert session["status"] == "UPLOADED"
    assert session["error"] is None


def test_same_filename_gets_different_ids(repo):
    assert repo.create("a.mp4") != repo.create("a.mp4")


def test_get_unknown_returns_none(repo):
    assert repo.get("missing") is None


def test_advance_only_from_expected_status(repo):
    session_id = repo.create("a.mp4")
    assert repo.advance(session_id, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED)
    assert not repo.advance(session_id, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED)
    assert repo.get(session_id)["status"] == "AUDIO_EXTRACTED"


def test_mark_failed_records_error(repo):
    session_id = repo.create("a.mp4")
    repo.mark_failed(session_id, "ffmpeg failed")
    session = repo.get(session_id)
    assert session["status"] == "FAILED"
    assert session["error"] == "ffmpeg failed"


def test_save_analysis_overwrites(repo):
    repo.save_analysis("s1", {"utterances": [{"topic": "work"}]})
    repo.save_analysis("s1", {"utterances": [{"topic": "family"}]})
    assert repo.get_analysis("s1") == {"utterances": [{"topic": "family"}]}
    assert repo.count_by("topic") == [{"topic": "family", "count": 1}]


def test_count_by_aggregates_across_sessions(repo):
    repo.save_analysis("s1", {"utterances": [{"topic": "family"}, {"topic": "work"}]})
    repo.save_analysis("s2", {"utterances": [{"topic": "family"}]})
    assert repo.count_by("topic") == [
        {"topic": "family", "count": 2},
        {"topic": "work", "count": 1},
    ]
