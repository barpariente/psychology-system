import json
import logging
import tempfile
from pathlib import Path

from common.messaging import EVENT_TRANSCRIBED, Handler, PublishFn
from common.pipeline import StageDecision, claim_stage
from common.sessions import SessionStatus
from common.storage import AUDIO_BUCKET, TRANSCRIPTS_BUCKET

logger = logging.getLogger(__name__)


def make_handler(repo, storage, engine) -> Handler:
    def handle(payload: dict, publish_next: PublishFn) -> None:
        session_id, decision = claim_stage(
            repo, payload, SessionStatus.AUDIO_EXTRACTED, SessionStatus.TRANSCRIBED
        )
        if decision is StageDecision.SKIP:
            logger.info("Skipping duplicate message for %s", session_id)
            return
        if decision is StageDecision.PROCESS:
            with tempfile.TemporaryDirectory() as tmp:
                audio = storage.download_file(
                    AUDIO_BUCKET, f"{session_id}.mp3", Path(tmp) / "audio.mp3"
                )
                utterances = engine.transcribe(audio)
            body = json.dumps({"utterances": utterances}).encode()
            storage.put_bytes(TRANSCRIPTS_BUCKET, f"{session_id}.json", body, "application/json")
            repo.advance(session_id, SessionStatus.AUDIO_EXTRACTED, SessionStatus.TRANSCRIBED)
            logger.info("Transcribed %s (%d utterances)", session_id, len(utterances))
        publish_next(EVENT_TRANSCRIBED, {"session_id": session_id})

    return handle
