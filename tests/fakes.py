from pathlib import Path


class FakeStorage:
    """In-memory stand-in for common.storage.ObjectStorage."""

    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}

    def put_bytes(self, bucket, key, data, content_type):
        self.objects[(bucket, key)] = data

    def put_file(self, bucket, key, path, content_type):
        self.objects[(bucket, key)] = Path(path).read_bytes()

    def download_file(self, bucket, key, path):
        Path(path).write_bytes(self.objects[(bucket, key)])
        return Path(path)

    def get_bytes(self, bucket, key):
        return self.objects[(bucket, key)]
