import json
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


class FakeChannel:
    """Records the pika channel calls made by common.messaging."""

    def __init__(self):
        self.acked = []
        self.rejected = []
        self.published = []
        self.exchanges = {}
        self.queues = {}
        self.bindings = []

    def basic_ack(self, delivery_tag):
        self.acked.append(delivery_tag)

    def basic_reject(self, delivery_tag, requeue):
        self.rejected.append((delivery_tag, requeue))

    def basic_publish(self, exchange, routing_key, body, properties):
        self.published.append({
            "exchange": exchange,
            "routing_key": routing_key,
            "body": json.loads(body),
            "headers": properties.headers,
            "delivery_mode": properties.delivery_mode,
        })

    def exchange_declare(self, exchange, exchange_type, durable):
        self.exchanges[exchange] = exchange_type

    def queue_declare(self, queue, durable, arguments=None):
        self.queues[queue] = arguments or {}

    def queue_bind(self, queue, exchange, routing_key):
        self.bindings.append((queue, exchange, routing_key))
