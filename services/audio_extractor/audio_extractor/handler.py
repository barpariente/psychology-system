import logging
import subprocess
import tempfile
from pathlib import Path

from common.messaging import EVENT_AUDIO_EXTRACTED, Handler, PermanentError, PublishFn
from common.pipeline import StageDecision, claim_stage
from common.sessions import SessionStatus
from common.storage import AUDIO_BUCKET, VIDEOS_BUCKET

from audio_extractor.extractor import extract_audio

logger = logging.getLogger(__name__)


def make_handler(repo, storage, run_ffmpeg=extract_audio) -> Handler:
    def handle(payload: dict, publish_next: PublishFn) -> None:
        session_id, decision = claim_stage(
            repo, payload, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED
        )
        if decision is StageDecision.SKIP:
            logger.info("Skipping duplicate message for %s", session_id)
            return
        if decision is StageDecision.PROCESS:
            with tempfile.TemporaryDirectory() as tmp:
                video = storage.download_file(VIDEOS_BUCKET, session_id, Path(tmp) / "video")
                audio = Path(tmp) / "audio.mp3"
                try:
                    run_ffmpeg(video, audio)
                except subprocess.CalledProcessError as exc:
                    stderr = (exc.stderr or b"").decode(errors="replace").strip()
                    raise PermanentError(f"ffmpeg could not extract audio: {stderr}") from exc
                storage.put_file(AUDIO_BUCKET, f"{session_id}.mp3", audio, "audio/mpeg")
            repo.advance(session_id, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED)
            logger.info("Extracted audio for %s", session_id)
        publish_next(EVENT_AUDIO_EXTRACTED, {"session_id": session_id})

    return handle
