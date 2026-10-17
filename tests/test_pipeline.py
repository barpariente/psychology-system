import pytest
from common.messaging import PermanentError
from common.pipeline import StageDecision, claim_stage, mark_failed_on_dead_letter
from common.sessions import SessionStatus

EXPECTED, PRODUCES = SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED


def test_process_when_at_expected_status(repo):
    session_id = repo.create("a.mp4")
    assert claim_stage(repo, {"session_id": session_id}, EXPECTED, PRODUCES) == (
        session_id,
        StageDecision.PROCESS,
    )


def test_republish_when_output_already_exists(repo):
    session_id = repo.create("a.mp4")
    repo.advance(session_id, EXPECTED, PRODUCES)
    assert claim_stage(repo, {"session_id": session_id}, EXPECTED, PRODUCES)[1] is (
        StageDecision.REPUBLISH
    )


def test_skip_when_session_moved_further_or_failed(repo):
    session_id = repo.create("a.mp4")
    repo.mark_failed(session_id, "boom")
    assert claim_stage(repo, {"session_id": session_id}, EXPECTED, PRODUCES)[1] is (
        StageDecision.SKIP
    )


@pytest.mark.parametrize("payload", [{}, {"session_id": 5}, {"session_id": "unknown"}])
def test_bad_payload_is_permanent(repo, payload):
    with pytest.raises(PermanentError):
        claim_stage(repo, payload, EXPECTED, PRODUCES)


def test_dead_letter_marks_session_failed(repo):
    session_id = repo.create("a.mp4")
    mark_failed_on_dead_letter(repo)({"session_id": session_id}, "gave up")
    assert repo.get(session_id)["status"] == "FAILED"
    assert repo.get(session_id)["error"] == "gave up"


def test_dead_letter_without_session_id_is_ignored(repo):
    mark_failed_on_dead_letter(repo)({}, "gave up")
