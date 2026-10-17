import logging

from common.messaging import EVENT_UPLOADED
from common.storage import VIDEOS_BUCKET
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api import deps

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])

MAX_UPLOAD_BYTES = 200 * 1024 * 1024


@router.post("", status_code=202, summary="Upload a session video and start processing")
def upload_session(
    file: UploadFile = File(...),
    repo=Depends(deps.get_repository),
    storage=Depends(deps.get_storage),
    publisher=Depends(deps.get_publisher),
):
    content_type = file.content_type or ""
    if not content_type.startswith("video/"):
        raise HTTPException(400, "Only video files are accepted")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(400, "File is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 200 MB")

    session_id = repo.create(file.filename or "upload")
    try:
        storage.put_bytes(VIDEOS_BUCKET, session_id, data, content_type)
        publisher.publish(EVENT_UPLOADED, {"session_id": session_id})
    except Exception as exc:
        logger.exception("Could not start processing for %s", session_id)
        repo.mark_failed(session_id, f"upload failed: {exc}")
        raise HTTPException(503, "Storage or message broker unavailable") from exc
    return {"session_id": session_id, "status": "UPLOADED"}


@router.get("/{session_id}", summary="Get processing status of a session")
def get_session(session_id: str, repo=Depends(deps.get_repository)):
    session = repo.get(session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    return session


@router.get("/{session_id}/analysis", summary="Get the analysis of a processed session")
def get_analysis(session_id: str, repo=Depends(deps.get_repository)):
    analysis = repo.get_analysis(session_id)
    if analysis is None:
        raise HTTPException(404, "Analysis not found or not ready yet")
    return analysis
