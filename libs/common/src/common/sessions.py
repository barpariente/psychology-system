import uuid
from datetime import datetime, timezone
from enum import Enum

from pymongo import MongoClient

from common.config import Settings


class SessionStatus(str, Enum):
    UPLOADED = "UPLOADED"
    AUDIO_EXTRACTED = "AUDIO_EXTRACTED"
    TRANSCRIBED = "TRANSCRIBED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRepository:
    def __init__(self, db):
        self._sessions = db["sessions"]
        self._analysis = db["analysis"]

    @classmethod
    def from_settings(cls, settings: Settings) -> "SessionRepository":
        return cls(MongoClient(settings.mongo_uri)[settings.mongo_db])

    def create(self, filename: str) -> str:
        session_id = uuid.uuid4().hex
        now = _now()
        self._sessions.insert_one({
            "_id": session_id,
            "filename": filename,
            "status": SessionStatus.UPLOADED.value,
            "error": None,
            "created_at": now,
            "updated_at": now,
        })
        return session_id

    def get(self, session_id: str) -> dict | None:
        doc = self._sessions.find_one({"_id": session_id})
        if doc is None:
            return None
        doc["session_id"] = doc.pop("_id")
        return doc

    def advance(self, session_id: str, expected: SessionStatus, new: SessionStatus) -> bool:
        """Moves a session to `new` only if it is still at `expected`. Returns whether it moved."""
        result = self._sessions.update_one(
            {"_id": session_id, "status": expected.value},
            {"$set": {"status": new.value, "updated_at": _now()}},
        )
        return result.modified_count == 1

    def mark_failed(self, session_id: str, error: str) -> None:
        self._sessions.update_one(
            {"_id": session_id},
            {"$set": {"status": SessionStatus.FAILED.value, "error": error, "updated_at": _now()}},
        )

    def save_analysis(self, session_id: str, analysis: dict) -> None:
        self._analysis.replace_one(
            {"_id": session_id}, {"_id": session_id, **analysis}, upsert=True
        )

    def get_analysis(self, session_id: str) -> dict | None:
        return self._analysis.find_one({"_id": session_id}, {"_id": 0})

    def count_by(self, field: str) -> list[dict]:
        pipeline = [
            {"$unwind": "$utterances"},
            {"$group": {"_id": f"$utterances.{field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
        ]
        return [
            {field: row["_id"], "count": row["count"]}
            for row in self._analysis.aggregate(pipeline)
            if row["_id"] is not None
        ]
