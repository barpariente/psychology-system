import io
from pathlib import Path

from minio import Minio

from common.config import Settings

VIDEOS_BUCKET = "videos"
AUDIO_BUCKET = "audio"
TRANSCRIPTS_BUCKET = "transcripts"


class ObjectStorage:
    def __init__(self, client):
        self._client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "ObjectStorage":
        return cls(Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        ))

    def _ensure_bucket(self, bucket: str) -> None:
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self._ensure_bucket(bucket)
        self._client.put_object(
            bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
        )

    def put_file(self, bucket: str, key: str, path: Path, content_type: str) -> None:
        self._ensure_bucket(bucket)
        self._client.fput_object(bucket, key, str(path), content_type=content_type)

    def download_file(self, bucket: str, key: str, path: Path) -> Path:
        self._client.fget_object(bucket, key, str(path))
        return path

    def get_bytes(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
