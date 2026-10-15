import fakeredis
from analyzer.cache import AnalysisCache


def test_roundtrip_with_normalized_key_and_ttl():
    client = fakeredis.FakeRedis(decode_responses=True)
    cache = AnalysisCache(client, ttl_seconds=60)
    cache.set("  Hello World ", {"topic": "greeting"})
    assert cache.get("hello world") == {"topic": "greeting"}
    (key,) = client.keys("*")
    assert key.startswith("analysis:v1:")
    assert 0 < client.ttl(key) <= 60


def test_miss_returns_none():
    assert AnalysisCache(fakeredis.FakeRedis(decode_responses=True)).get("nothing") is None
