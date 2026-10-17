import pytest
from api import deps
from api.main import create_app
from fastapi.testclient import TestClient


class RecordingPublisher:
    def __init__(self):
        self.events = []

    def publish(self, routing_key, payload):
        self.events.append((routing_key, payload))


class BrokenStorage:
    def put_bytes(self, *args, **kwargs):
        raise ConnectionError("minio down")


def make_client(repo, storage):
    app = create_app()
    publisher = RecordingPublisher()
    app.dependency_overrides[deps.get_repository] = lambda: repo
    app.dependency_overrides[deps.get_storage] = lambda: storage
    app.dependency_overrides[deps.get_publisher] = lambda: publisher
    client = TestClient(app)
    client.publisher = publisher
    return client


@pytest.fixture
def client(repo, storage):
    return make_client(repo, storage)


def upload(client, name="session.mp4", data=b"video-bytes", content_type="video/mp4"):
    return client.post("/sessions", files={"file": (name, data, content_type)})


def test_upload_stores_video_under_session_id_and_publishes(client, repo, storage):
    response = upload(client, name="../evil.mp4")
    assert response.status_code == 202
    session_id = response.json()["session_id"]
    assert storage.objects == {("videos", session_id): b"video-bytes"}
    assert client.publisher.events == [("session.uploaded", {"session_id": session_id})]
    assert repo.get(session_id)["filename"] == "../evil.mp4"


def test_same_filename_twice_creates_two_sessions(client, storage):
    first = upload(client).json()["session_id"]
    second = upload(client).json()["session_id"]
    assert first != second
    assert len(storage.objects) == 2


def test_rejects_non_video(client):
    response = upload(client, name="notes.txt", content_type="text/plain")
    assert response.status_code == 400
    assert client.publisher.events == []


def test_rejects_empty_file(client):
    assert upload(client, data=b"").status_code == 400


def test_storage_failure_returns_503_and_publishes_nothing(repo):
    client = make_client(repo, BrokenStorage())
    assert upload(client).status_code == 503
    assert client.publisher.events == []


def test_status(client):
    session_id = upload(client).json()["session_id"]
    body = client.get(f"/sessions/{session_id}").json()
    assert body["status"] == "UPLOADED"
    assert client.get("/sessions/unknown").status_code == 404


def test_analysis_404_until_ready_then_returned(client, repo):
    session_id = upload(client).json()["session_id"]
    assert client.get(f"/sessions/{session_id}/analysis").status_code == 404
    repo.save_analysis(session_id, {"session_id": session_id, "utterances": []})
    assert client.get(f"/sessions/{session_id}/analysis").json()["session_id"] == session_id


def test_stats(client, repo):
    repo.save_analysis("s1", {"utterances": [
        {"topic": "family", "emotion": "anxiety"},
        {"topic": "work", "emotion": "pride"},
    ]})
    repo.save_analysis("s2", {"utterances": [{"topic": "family", "emotion": "anxiety"}]})
    assert client.get("/stats/topics").json() == {"topics": [
        {"topic": "family", "count": 2},
        {"topic": "work", "count": 1},
    ]}
    assert client.get("/stats/emotions").json()["emotions"][0] == {"emotion": "anxiety", "count": 2}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
