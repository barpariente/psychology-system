from functools import lru_cache

from common.config import Settings, load_settings
from common.messaging import RabbitPublisher
from common.sessions import SessionRepository
from common.storage import ObjectStorage


@lru_cache
def _settings() -> Settings:
    return load_settings()


@lru_cache
def get_repository() -> SessionRepository:
    return SessionRepository.from_settings(_settings())


@lru_cache
def get_storage() -> ObjectStorage:
    return ObjectStorage.from_settings(_settings())


@lru_cache
def get_publisher() -> RabbitPublisher:
    return RabbitPublisher(_settings().rabbitmq_url)
