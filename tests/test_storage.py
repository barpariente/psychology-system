from common.storage import ObjectStorage


class FakeMinio:
    def __init__(self):
        self.buckets = set()
        self.puts = []

    def bucket_exists(self, bucket):
        return bucket in self.buckets

    def make_bucket(self, bucket):
        self.buckets.add(bucket)

    def put_object(self, bucket, key, data, length, content_type):
        self.puts.append((bucket, key, data.read(), length, content_type))


def test_put_bytes_creates_missing_bucket():
    client = FakeMinio()
    ObjectStorage(client).put_bytes("videos", "abc", b"data", "video/mp4")
    assert client.buckets == {"videos"}
    assert client.puts == [("videos", "abc", b"data", 4, "video/mp4")]


def test_put_bytes_reuses_existing_bucket():
    client = FakeMinio()
    client.buckets.add("videos")
    ObjectStorage(client).put_bytes("videos", "abc", b"data", "video/mp4")
    assert client.buckets == {"videos"}
