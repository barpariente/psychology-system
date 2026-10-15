import hashlib
import json
import logging

import redis

logger = logging.getLogger(__name__)


class AnalysisCache:
    """Caches per-sentence LLM results. Redis problems never fail the pipeline."""

    PREFIX = "analysis:v1:"

    def __init__(self, client, ttl_seconds: int = 7 * 24 * 3600):
        self._client = client
        self._ttl = ttl_seconds

    @classmethod
    def from_url(cls, url: str) -> "AnalysisCache":
        return cls(redis.Redis.from_url(url, decode_responses=True))

    def _key(self, text: str) -> str:
        normalized = " ".join(text.lower().split())
        return self.PREFIX + hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, text: str) -> dict | None:
        try:
            raw = self._client.get(self._key(text))
        except redis.RedisError as exc:
            logger.warning("Cache read failed, continuing without cache: %s", exc)
            return None
        return json.loads(raw) if raw else None

    def set(self, text: str, result: dict) -> None:
        try:
            self._client.set(self._key(text), json.dumps(result), ex=self._ttl)
        except redis.RedisError as exc:
            logger.warning("Cache write failed: %s", exc)
