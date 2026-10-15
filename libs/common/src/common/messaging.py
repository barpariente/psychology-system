"""RabbitMQ topology, publishing, and a consumer loop with delayed retries and dead-lettering."""

import json
import logging
import time
from collections.abc import Callable

import pika
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)

EXCHANGE = "sessions"
DEAD_LETTER_EXCHANGE = "sessions.dlx"
RETRY_HEADER = "x-retry-count"
RETRY_DELAY_MS = 5000

EVENT_UPLOADED = "session.uploaded"
EVENT_AUDIO_EXTRACTED = "session.audio_extracted"
EVENT_TRANSCRIBED = "session.transcribed"
EVENT_ANALYZED = "session.analyzed"

AUDIO_EXTRACTION_QUEUE = "audio_extraction"
TRANSCRIPTION_QUEUE = "transcription"
ANALYSIS_QUEUE = "analysis"

# queue -> routing key it consumes
QUEUE_BINDINGS = {
    AUDIO_EXTRACTION_QUEUE: EVENT_UPLOADED,
    TRANSCRIPTION_QUEUE: EVENT_AUDIO_EXTRACTED,
    ANALYSIS_QUEUE: EVENT_TRANSCRIBED,
}

PublishFn = Callable[[str, dict], None]
Handler = Callable[[dict, PublishFn], None]
DeadLetterFn = Callable[[dict, str], None]


class PermanentError(Exception):
    """Raised by a handler when retrying cannot help (bad input). Skips straight to the DLQ."""


def retry_queue(queue: str) -> str:
    return f"{queue}.retry"


def dead_letter_queue(queue: str) -> str:
    return f"{queue}.dlq"


def declare_topology(channel) -> None:
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=DEAD_LETTER_EXCHANGE, exchange_type="direct", durable=True)
    for queue, routing_key in QUEUE_BINDINGS.items():
        channel.queue_declare(queue=queue, durable=True, arguments={
            "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
            "x-dead-letter-routing-key": queue,
        })
        channel.queue_bind(queue=queue, exchange=EXCHANGE, routing_key=routing_key)
        # Messages wait here for RETRY_DELAY_MS, then expire back into the work queue.
        channel.queue_declare(queue=retry_queue(queue), durable=True, arguments={
            "x-message-ttl": RETRY_DELAY_MS,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": queue,
        })
        channel.queue_declare(queue=dead_letter_queue(queue), durable=True)
        channel.queue_bind(
            queue=dead_letter_queue(queue), exchange=DEAD_LETTER_EXCHANGE, routing_key=queue
        )


def _properties(retry_count: int) -> pika.BasicProperties:
    return pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2,  # persistent
        headers={RETRY_HEADER: retry_count},
    )


def publish(channel, routing_key: str, payload: dict) -> None:
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(payload),
        properties=_properties(0),
    )


def _dead_letter(channel, method, payload: dict, error: Exception, on_dead_letter) -> None:
    logger.error("Dead-lettering %s: %s", payload, error)
    try:
        on_dead_letter(payload, str(error))
    except Exception:
        logger.exception("on_dead_letter callback failed for %s", payload)
    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)


def handle_delivery(
    channel,
    method,
    properties,
    body: bytes,
    *,
    queue: str,
    handler: Handler,
    max_retries: int,
    on_dead_letter: DeadLetterFn,
) -> None:
    retries = int((properties.headers or {}).get(RETRY_HEADER, 0))
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = None
    if not isinstance(payload, dict):
        logger.error("Malformed message on %s, dead-lettering: %r", queue, body[:200])
        channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        return

    def publish_next(routing_key: str, next_payload: dict) -> None:
        publish(channel, routing_key, next_payload)

    try:
        handler(payload, publish_next)
    except PermanentError as exc:
        _dead_letter(channel, method, payload, exc, on_dead_letter)
    except Exception as exc:
        if retries < max_retries:
            logger.warning(
                "Attempt %d/%d on %s failed for %s: %s",
                retries + 1, max_retries + 1, queue, payload, exc,
            )
            channel.basic_publish(
                exchange="",
                routing_key=retry_queue(queue),
                body=body,
                properties=_properties(retries + 1),
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
        else:
            _dead_letter(channel, method, payload, exc, on_dead_letter)
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)


def connect(url: str, attempts: int = 20, delay_seconds: float = 3.0) -> pika.BlockingConnection:
    for attempt in range(1, attempts + 1):
        try:
            return pika.BlockingConnection(pika.URLParameters(url))
        except AMQPConnectionError:
            if attempt == attempts:
                raise
            logger.info("RabbitMQ not ready (attempt %d/%d), retrying", attempt, attempts)
            time.sleep(delay_seconds)
    raise RuntimeError("unreachable")


def run_consumer(
    url: str, queue: str, handler: Handler, *, max_retries: int, on_dead_letter: DeadLetterFn
) -> None:
    connection = connect(url)
    channel = connection.channel()
    declare_topology(channel)
    channel.basic_qos(prefetch_count=1)

    def on_message(ch, method, properties, body):
        handle_delivery(
            ch, method, properties, body,
            queue=queue, handler=handler,
            max_retries=max_retries, on_dead_letter=on_dead_letter,
        )

    channel.basic_consume(queue=queue, on_message_callback=on_message)
    logger.info("Consuming from %s", queue)
    channel.start_consuming()


class RabbitPublisher:
    """Publishes one event per call on a short-lived connection (fine for an upload API)."""

    def __init__(self, url: str):
        self._url = url

    def publish(self, routing_key: str, payload: dict) -> None:
        connection = connect(self._url, attempts=3, delay_seconds=1.0)
        try:
            channel = connection.channel()
            declare_topology(channel)
            publish(channel, routing_key, payload)
        finally:
            connection.close()
