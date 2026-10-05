"""Every event the catalog can store has somebody the outbox can deliver it to.

**An event with no subscriber is not a quiet event, it is a stuck one.** The
dispatcher answers a delivery with nobody to receive it as a failure
(``MissingEventHandlerError``), the outbox leaves the row unpublished and fetches
it again on the next poll — oldest first, a batch at a time, with no back-off —
so enough of them fill every batch and **nothing written after them is ever
delivered**: no room is told, no card is released. The Club courts events shipped
without one (#535), and a seeded laptop wrote 102 of them against the API
worker's batch of 100.

Every context therefore subscribes at least a log line to each event it
registers, and this asserts it for the whole runtime rather than trusting each
context to remember.
"""

from __future__ import annotations

from app.bootstrap.events import build_event_runtime


def test_every_registered_event_has_a_subscriber():
    runtime = build_event_runtime()

    registered = runtime.catalog.registered_classes()
    unsubscribed = sorted(
        event_class.__name__
        for event_class in registered
        if not runtime.dispatcher.subscribers_of(event_class)
    )

    assert registered
    assert unsubscribed == []
