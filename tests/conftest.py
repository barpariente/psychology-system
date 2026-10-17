import mongomock
import pytest
from common.sessions import SessionRepository
from fakes import FakeStorage


@pytest.fixture
def repo():
    return SessionRepository(mongomock.MongoClient()["test"])


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def published():
    """A publish_next function that records (routing_key, payload) in .events."""
    events = []

    def publish_next(routing_key, payload):
        events.append((routing_key, payload))

    publish_next.events = events
    return publish_next
