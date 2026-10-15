import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    rabbitmq_url: str
    mongo_uri: str
    mongo_db: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    redis_url: str
    fake_ai: bool
    max_retries: int
    openai_api_key: str | None
    assemblyai_api_key: str | None


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if env is None else env
    return Settings(
        rabbitmq_url=env.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
        mongo_uri=env.get("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db=env.get("MONGO_DB", "psychology_system"),
        minio_endpoint=env.get("MINIO_ENDPOINT", "localhost:9000"),
        minio_access_key=env.get("MINIO_ACCESS_KEY", "minio"),
        minio_secret_key=env.get("MINIO_SECRET_KEY", "minio123"),
        redis_url=env.get("REDIS_URL", "redis://localhost:6379/0"),
        fake_ai=env.get("FAKE_AI", "false").lower() == "true",
        max_retries=int(env.get("MAX_RETRIES", "3")),
        openai_api_key=env.get("OPENAI_API_KEY") or None,
        assemblyai_api_key=env.get("ASSEMBLYAI_API_KEY") or None,
    )
