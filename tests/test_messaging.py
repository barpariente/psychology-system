import json
from types import SimpleNamespace

from common.messaging import (
    DEAD_LETTER_EXCHANGE,
    EXCHANGE,
    PermanentError,
    declare_topology,
    handle_delivery,
)
from fakes import FakeChannel

QUEUE = "audio_extraction"
METHOD = SimpleNamespace(delivery_tag=7, routing_key="session.uploaded")


def deliver(channel, handler, body=b'{"session_id": "s1"}', retries=0, max_retries=3):
    dead_letters = []
    handle_delivery(
        channel,
        METHOD,
        SimpleNamespace(headers={"x-retry-count": retries}),
        body,
        queue=QUEUE,
        handler=handler,
        max_retries=max_retries,
        on_dead_letter=lambda payload, error: dead_letters.append((payload, error)),
    )
    return dead_letters


def test_success_acks_and_passes_payload():
    channel, seen = FakeChannel(), []
    deliver(channel, lambda payload, publish_next: seen.append(payload))
    assert seen == [{"session_id": "s1"}]
    assert channel.acked == [7]
    assert channel.rejected == []


def test_handler_can_publish_next_event():
    channel = FakeChannel()
    deliver(channel, lambda payload, publish_next: publish_next("session.audio_extracted", payload))
    assert channel.published == [{
        "exchange": EXCHANGE,
        "routing_key": "session.audio_extracted",
        "body": {"session_id": "s1"},
        "headers": {"x-retry-count": 0},
        "delivery_mode": 2,
    }]


def test_transient_error_goes_to_retry_queue_with_incremented_count():
    channel = FakeChannel()

    def boom(payload, publish_next):
        raise RuntimeError("network blip")

    dead_letters = deliver(channel, boom, retries=1)
    assert channel.published[0]["exchange"] == ""
    assert channel.published[0]["routing_key"] == "audio_extraction.retry"
    assert channel.published[0]["headers"] == {"x-retry-count": 2}
    assert channel.acked == [7]
    assert dead_letters == []


def test_last_attempt_dead_letters():
    channel = FakeChannel()

    def boom(payload, publish_next):
        raise RuntimeError("still broken")

    dead_letters = deliver(channel, boom, retries=3, max_retries=3)
    assert channel.published == []
    assert channel.rejected == [(7, False)]
    assert dead_letters == [({"session_id": "s1"}, "still broken")]


def test_permanent_error_skips_retries():
    channel = FakeChannel()

    def bad_input(payload, publish_next):
        raise PermanentError("no audio stream")

    dead_letters = deliver(channel, bad_input, retries=0)
    assert channel.published == []
    assert channel.rejected == [(7, False)]
    assert dead_letters == [({"session_id": "s1"}, "no audio stream")]


def test_malformed_body_is_rejected_without_calling_handler():
    channel, seen = FakeChannel(), []
    for body in (b"not json", json.dumps([1, 2]).encode()):
        deliver(channel, lambda payload, publish_next: seen.append(payload), body=body)
    assert seen == []
    assert channel.rejected == [(7, False), (7, False)]


def test_dead_letter_callback_failure_still_rejects():
    channel = FakeChannel()

    def bad_input(payload, publish_next):
        raise PermanentError("bad")

    def broken_callback(payload, error):
        raise RuntimeError("mongo down")

    handle_delivery(
        channel, METHOD, SimpleNamespace(headers={}), b'{"session_id": "s1"}',
        queue=QUEUE, handler=bad_input, max_retries=3, on_dead_letter=broken_callback,
    )
    assert channel.rejected == [(7, False)]


def test_topology_wires_retry_and_dead_letter_queues():
    channel = FakeChannel()
    declare_topology(channel)
    assert channel.exchanges == {EXCHANGE: "topic", DEAD_LETTER_EXCHANGE: "direct"}
    assert channel.queues["audio_extraction"] == {
        "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
        "x-dead-letter-routing-key": "audio_extraction",
    }
    assert channel.queues["audio_extraction.retry"] == {
        "x-message-ttl": 5000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "audio_extraction",
    }
    assert "audio_extraction.dlq" in channel.queues
    assert ("audio_extraction", EXCHANGE, "session.uploaded") in channel.bindings
    assert ("audio_extraction.dlq", DEAD_LETTER_EXCHANGE, "audio_extraction") in channel.bindings
    assert ("analysis", EXCHANGE, "session.transcribed") in channel.bindings
