from enum import Enum

from common.messaging import DeadLetterFn, PermanentError
from common.sessions import SessionRepository, SessionStatus


class StageDecision(Enum):
    PROCESS = "process"      # session is waiting for this stage
    REPUBLISH = "republish"  # this stage already finished; only re-send the next event
    SKIP = "skip"            # session moved on or failed; nothing to do


def claim_stage(
    repo: SessionRepository,
    payload: dict,
    expected: SessionStatus,
    produces: SessionStatus,
) -> tuple[str, StageDecision]:
    session_id = payload.get("session_id")
    if not isinstance(session_id, str):
        raise PermanentError(f"message has no session_id: {payload}")
    session = repo.get(session_id)
    if session is None:
        raise PermanentError(f"unknown session {session_id}")
    if session["status"] == expected.value:
        return session_id, StageDecision.PROCESS
    if session["status"] == produces.value:
        return session_id, StageDecision.REPUBLISH
    return session_id, StageDecision.SKIP


def mark_failed_on_dead_letter(repo: SessionRepository) -> DeadLetterFn:
    def on_dead_letter(payload: dict, error: str) -> None:
        session_id = payload.get("session_id")
        if isinstance(session_id, str):
            repo.mark_failed(session_id, error)

    return on_dead_letter
