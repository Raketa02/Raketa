"""No response shape on this API can carry an inbox. Asserted, and **narrowed once**.

``docs/adr/0109`` §2 banked a one-sided yes under a promise of silence: *"incoming
and not mutual never crosses, on any route, in any shape — not as a list, not as
a count, not as a badge."* ``docs/adr/0169`` §4 reverses exactly one clause of
that sentence, knowingly: **one count, on one envelope**. Ania learns that
*somebody* wants her, never who. The list and the badge stay refused, and this
file is the schema test that sentence said would be narrowed — it enforces the
rest of it.

So the check walks the **emitted contract**, not the source: every schema
reachable from a *response* on the player surface, transitively, and no property
on any of them may name incoming interest — except ``PoolSchema.want_to_play_you``,
which must be an integer and nothing else, and must live on exactly that schema.
A rule like this is broken by addition, months later, by somebody adding a
helpful field to a candidate row, and nothing about the diff would look wrong.

**Matching is on the words of a property name.** ``want_to_play_you`` is the one
admitted spelling; ``wants_to_play_you`` on a card, ``incoming`` anywhere,
``inbox``, ``likers``, ``said_yes`` and ``liked_by`` are the spellings a leak would
plausibly reuse, and each is driven against a deliberately broken document
below, because a gate that has never been observed to fail is indistinguishable
from one that does not work.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router
from tests.unit.test_no_response_carries_a_forbidden_fact import (
    offends as names_a_signal,
    schemas_reachable_from_responses,
)

#: Anything a client could read as *these people said yes to me*. A signal is
#: either a word, or a tuple of words that must **all** appear.
INBOX_SIGNALS: tuple[object, ...] = (
    "inbox",
    "incoming",
    "likers",
    "liker",
    ("liked", "by"),
    ("said", "yes"),
    ("want", "to", "play", "you"),
    ("wants", "to", "play", "you"),
    ("waiting", "for", "you"),
    ("interest", "received"),
)

#: The one field admitted against the rule, with the reason it is not the thing
#: the rule was written about — and the shape it must keep to stay admitted.
THE_COUNT = ("PoolSchema", "want_to_play_you")


def offends(field: str, signals: Iterable[object] = INBOX_SIGNALS) -> bool:
    """The forbidden-fact walk's own word matching, over this file's signals."""

    return names_a_signal(field, signals)


def _spec() -> dict:
    return build_surface_spec("Raketa Player API", player_api_router)


def _properties(spec: dict) -> list[tuple[str, str, dict]]:
    return [
        (name, field, schema)
        for name, owner in schemas_reachable_from_responses(spec).items()
        for field, schema in owner.get("properties", {}).items()
    ]


def test_the_walk_reaches_the_deal_and_the_count_is_on_it():
    """The guard on the guard: a walk that did not reach the deal's envelope
    would admit nothing and refuse nothing, and pass for ever."""

    reached = schemas_reachable_from_responses(_spec())

    assert "PoolSchema" in reached, "the deal's pool is not in the walk"
    assert "want_to_play_you" in reached["PoolSchema"]["properties"]


def test_no_response_schema_carries_an_inbox_beyond_the_one_count():
    """**One count, on one envelope** (``docs/adr/0169`` §4), and nothing else
    that faces that direction — not on a card, not on the interest read, not on
    a record sheet."""

    offenders = {
        f"{owner}.{field}"
        for owner, field, _ in _properties(_spec())
        if offends(field) and (owner, field) != THE_COUNT
    }

    assert offenders == set(), (
        f"incoming interest reaches a response: {sorted(offenders)}"
    )


def test_the_one_count_is_an_integer_and_never_a_list_or_a_person():
    """The narrowing is to a **count**. An array, an object or a reference here
    would be the list ADR-0109 refused wearing the count's name."""

    owner, field = THE_COUNT
    reached = schemas_reachable_from_responses(_spec())
    declared = reached[owner]["properties"][field]

    assert declared.get("type") == "integer", declared
    assert "$ref" not in declared and "items" not in declared
    assert declared.get("minimum", 0) >= 0


@pytest.mark.parametrize(
    "field",
    [
        "wants_to_play_you",
        "want_to_play_you",
        "incoming",
        "incoming_interest",
        "inbox",
        "likers",
        "liked_by",
        "said_yes_to_you",
        "waiting_for_you",
        "interest_received",
        "interestReceived",
    ],
)
def test_the_walk_refuses_the_fields_it_exists_to_refuse(field: str):
    """Driven against deliberately broken names: each is a spelling a leak would
    plausibly reuse, including the admitted one **on any other schema**."""

    assert offends(field)


def test_a_list_of_incoming_yeses_anywhere_goes_red():
    """The acceptance the record asks for, driven against a broken document:
    the same word on a candidate row, and the count re-declared as a list."""

    broken = _spec()
    schemas = broken["components"]["schemas"]
    schemas["CandidateSchema"]["properties"]["wants_to_play_you"] = {"type": "boolean"}
    schemas["OutstandingSchema"]["properties"]["incoming"] = {
        "type": "array",
        "items": {"type": "string"},
    }

    offenders = {
        f"{owner}.{field}"
        for owner, field, _ in _properties(broken)
        if offends(field) and (owner, field) != THE_COUNT
    }

    assert offenders == {
        "CandidateSchema.wants_to_play_you",
        "OutstandingSchema.incoming",
    }


@pytest.mark.parametrize(
    "field",
    ["outgoing", "mutual", "outstanding", "inclusion_reason", "players_in_range"],
)
def test_the_walk_admits_what_the_contract_actually_carries(field: str):
    """The other half of the judgement: your own yeses, the ones that came back
    and the count in flight are yours to read, and ``inclusion_reason`` names
    a lift without facing anybody's inbox."""

    assert not offends(field)
