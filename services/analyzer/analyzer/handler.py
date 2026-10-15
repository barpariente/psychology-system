import json
import logging

from common.messaging import EVENT_ANALYZED, Handler, PublishFn
from common.pipeline import StageDecision, claim_stage
from common.sessions import SessionStatus
from common.storage import TRANSCRIPTS_BUCKET

from analyzer.analysis import analyze_utterances

logger = logging.getLogger(__name__)


def make_handler(repo, storage, llm, cache) -> Handler:
    def handle(payload: dict, publish_next: PublishFn) -> None:
        session_id, decision = claim_stage(
            repo, payload, SessionStatus.TRANSCRIBED, SessionStatus.ANALYZED
        )
        if decision is StageDecision.SKIP:
            logger.info("Skipping duplicate message for %s", session_id)
            return
        if decision is StageDecision.PROCESS:
            transcript = json.loads(storage.get_bytes(TRANSCRIPTS_BUCKET, f"{session_id}.json"))
            analysis = analyze_utterances(transcript["utterances"], llm, cache)
            repo.save_analysis(session_id, {"session_id": session_id, **analysis})
            repo.advance(session_id, SessionStatus.TRANSCRIBED, SessionStatus.ANALYZED)
            logger.info("Analyzed %s (%d utterances)", session_id, len(analysis["utterances"]))
        publish_next(EVENT_ANALYZED, {"session_id": session_id})

    return handle
