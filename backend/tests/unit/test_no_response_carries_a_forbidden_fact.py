"""No forbidden fact reaches any response type. Asserted **centrally**.

A test per route passes for ever and then somebody adds a route. So this walks
the **emitted contract** — every schema reachable from a response on the player
surface, transitively, however it got there — and refuses a property that names
one of the facts this product has decided it does not publish.

The list below is not a style guide. Every row is a decision somebody argued for,
and every one of them is broken the same way: months later, by a helpful field
added to a candidate row, in a diff where nothing looks wrong.

- **gender** — a protected characteristic may **gate**; it may never be shown
  to anybody but its owner, or scored. The owner's own profile read is the one
  shape that carries it (``docs/adr/0179`` §4), named in ``PERMITTED_ON`` — and
  the rule is asserted from both sides below: refused everywhere else, and
  **present** there, so the admission cannot quietly widen into a second shape
  or quietly lapse from the first.
- **a bio, or any player-authored free text** — the platform's first moderation
  surface. ``docs/adr/0170`` admitted exactly one line, ``intro``, fenced at the
  write; the words this rule catches are the ones a *paragraph* would arrive
  under, and ``intro`` is deliberately not among them.
- **activity recency, at any granularity** — *last seen* is a presence indicator
  and this product does not have one.
- **a decline, a pass** — a refusal is not a notification, and a pass is
  write-only.
- **a withheld or near-miss row** — *a player may ask why somebody was shown;
  nobody may ask who was withheld.* The one field once admitted against it, the
  search read-back's own ``withheld``, went with the searches (#579).
- **a birthdate or an age** — nothing in this backend collects one, and no gate
  may reopen it here.
- **a first, last, full or given name** — the platform holds the **Name** a
  player typed, whole (``docs/adr/0171``), and nothing may derive a familiar
  form from it: a ``first_name`` field would be the product addressing somebody
  by a word they never gave it.
- **a shard key** — the partition is derived, so there is no field for a future
  conjunct to attach to.
- **an unsettled case** — the matcher never reads `cases`; the hold does its
  work at the gate.
- **an individual sportsmanship rating** — *no individual rating is returned to
  anybody, on any route, in any shape.* What may be published about a person is
  an **average** beside how many different people it rests on, and to the subject
  a coarse **band** with no count at all; a published average plus a count lets a
  subject subtract, name each new rating exactly, and go and find the one person
  who could have given it. ``stars`` is the word this rule can catch, and the
  scope of that is worth being honest about: it is the word the write route uses
  and the only one a leak would plausibly reuse, and it catches nothing about a
  figure published under an honest name. The rest of the rule is structural —
  ``SportsmanshipLedger`` has no method that answers *what did somebody say about
  me*, so a route wanting to leak one has to grow a read first.

**Matching is on the words of a property name, never on a substring.** So
``gender`` catches ``gender_preference`` and ``threshold`` is not a hold. Both
halves are load-bearing, and both are driven against deliberately broken
documents below.

Two neighbours assert the same shape over the same document and are kept apart
because each needs a judgement this one does not:
``test_matchmaking_liveness_never_crosses`` refuses the word beside a **number**
where ``liveness_reasons`` is exactly what the contract does carry, and
``test_no_response_carries_a_block`` covers the block vocabulary.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router

#: One entry per decision, so a failure names the rule rather than a regex. A
#: signal is either a word, or a tuple of words that must **all** appear — which
#: is what lets *last name* be refused while *last* alone is ordinary.
FORBIDDEN: dict[str, tuple[object, ...]] = {
    "gender": ("gender",),
    "free text about a player": ("bio", "biography", "blurb", ("about", "me")),
    "activity recency": (
        "recency",
        "online",
        ("last", "seen"),
        ("last", "active"),
        ("seen", "at"),
        ("active", "at"),
    ),
    "a decline": ("decline", "declined", "declines"),
    "a pass": ("passed", "passes"),
    "a withheld row": ("withheld", ("near", "miss")),
    "a birthdate": ("birth", "birthdate", "birthday", "age", ("date", "of", "birth")),
    "a real name": (
        ("first", "name"),
        ("last", "name"),
        ("full", "name"),
        ("given", "name"),
    ),
    "a shard key": ("shard",),
    "an unsettled case": ("unsettled", "hold", ("case", "id")),
    "an individual sportsmanship rating": ("stars",),
}

#: Fields that trip a rule above and are published **on purpose, on every shape
#: they appear on**, each with the reason it is not the thing the rule was
#: written about. Kept as a named list rather than by loosening a rule, so
#: admitting one is a decision somebody writes down instead of a signal quietly
#: getting weaker.
PERMITTED: dict[str, str] = {}

#: Fields that trip a rule above and are published **on one named shape and no
#: other** — the narrower admission, keyed by the shape as well as the word.
#: ``PERMITTED`` admits a word wherever it appears; this admits it in one place,
#: and `test_a_shape_scoped_admission_reaches_exactly_the_shapes_it_names`
#: asserts the word is *there*, so the admission is a claim about the contract
#: rather than a hole in the walk.
PERMITTED_ON: dict[tuple[str, str], str] = {
    ("PlayerProfileReadResponse", "gender"): (
        "The owner's own answer, on the route scoped to `me` (ADR-0179 §4). "
        "ADR-0096 §6 — *no response shape carries a gender value out* — is "
        "about responses that describe one player to another, and every one "
        "of those is still refused. What this admits is a player reading the "
        "fact they set, so the screen that asks the question can open on the "
        "answer already given."
    ),
    ("PlayerProfileReadResponse", "gender_preference"): (
        "The owner's own setting, on the same route and for the same reason: "
        "*did I set women only, or not?* is the exact fact the reach sentence "
        "exists to make legible, and a stranger's card still carries no trace "
        "of it — a withheld row names no gate (ADR-0130)."
    ),
}


def words(name: str) -> set[str]:
    """The identifier words in a property name, lowercased.

    Both spellings the contract could arrive in — a generated document may carry
    ``last_seen`` or ``lastSeen`` depending on how somebody declares an alias —
    so camelCase is split as well as snake_case.
    """

    found: list[str] = []
    word: list[str] = []
    for character in name:
        if character.isalnum():
            if character.isupper() and word:
                found.append("".join(word))
                word = []
            word.append(character.lower())
        elif word:
            found.append("".join(word))
            word = []
    if word:
        found.append("".join(word))
    return set(found)


def names(signal: object, present: set[str]) -> bool:
    if isinstance(signal, tuple):
        return set(signal) <= present
    return signal in present


def offends(field: str, signals: Iterable[object]) -> bool:
    present = words(field)
    return any(names(signal, present) for signal in signals)


def _refs(node: object) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.add(value.rsplit("/", 1)[-1])
            else:
                found |= _refs(value)
    elif isinstance(node, list):
        for item in node:
            found |= _refs(item)
    return found


def schemas_reachable_from_responses(spec: dict) -> dict[str, dict]:
    """Every schema a client could ever be handed, transitively.

    Requests are deliberately outside the walk: what a player *sends* is not what
    the platform *publishes*, and a search request carrying a sport is not the
    platform telling anybody anything.
    """

    components = spec.get("components", {}).get("schemas", {})
    frontier: set[str] = set()
    for path in spec["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                frontier |= _refs(operation.get("responses", {}))

    reached: dict[str, dict] = {}
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        schema = components.get(name, {})
        reached[name] = schema
        frontier |= _refs(schema) - set(reached)
    return reached


def _spec() -> dict:
    return build_surface_spec("Raketa Player API", player_api_router)


def _properties(spec: dict | None = None) -> list[tuple[str, str]]:
    return [
        (name, field)
        for name, schema in schemas_reachable_from_responses(spec or _spec()).items()
        for field in schema.get("properties", {})
    ]


def test_the_walk_reaches_the_record_and_not_only_the_error_envelope():
    """The guard on the guard: a walk that reached nothing would pass for ever,
    and would go on passing the day the surface grew the field it guards."""

    reached = schemas_reachable_from_responses(_spec())

    assert "ErrorResponse" in reached
    # The one shape admitted to carry a gender value out. A walk that did not
    # reach it would pass the refusal for ever and prove nothing about it.
    assert "PlayerProfileReadResponse" in reached, "the profile read is not in the walk"
    # The player record describes **one person** rather than a pairing, which
    # makes it the surface every forbidden fact is most plausibly added to next:
    # a gender, an age or a *last seen* would each look like a helpful field on
    # a sheet whose whole job is answering *who is this*.
    assert "PlayerRecordResponse" in reached, "the record route is not in the walk"
    assert len(_properties()) > 50


def _offenders(rule: str, spec: dict | None = None) -> set[str]:
    """Every ``Schema.field`` in the document that trips `rule` and is admitted
    by neither list."""

    return {
        f"{owner}.{field}"
        for owner, field in _properties(spec)
        if offends(field, FORBIDDEN[rule])
        and field not in PERMITTED
        and (owner, field) not in PERMITTED_ON
    }


@pytest.mark.parametrize("rule", sorted(FORBIDDEN))
def test_no_response_schema_publishes_a_forbidden_fact(rule: str):
    offenders = _offenders(rule)

    assert offenders == set(), f"{rule} reaches a response: {sorted(offenders)}"


def test_the_admission_is_for_one_shape_and_a_second_is_still_refused():
    """Driven against a deliberately broken document: the owner's read carries
    `gender` and so does a card. The admission must cover the first and the
    walk must still name the second — otherwise ``PERMITTED_ON`` would have
    been ``PERMITTED`` with extra steps."""

    document = {
        "paths": {
            "/profile": {
                "get": {
                    "responses": {
                        "200": {
                            "$ref": "#/components/schemas/PlayerProfileReadResponse"
                        }
                    }
                }
            },
            "/searches": {
                "post": {
                    "responses": {
                        "200": {"$ref": "#/components/schemas/PlayerCardSchema"}
                    }
                }
            },
        },
        "components": {
            "schemas": {
                "PlayerProfileReadResponse": {
                    "properties": {"gender": {}, "gender_preference": {}}
                },
                "PlayerCardSchema": {"properties": {"gender": {}, "name": {}}},
            }
        },
    }

    assert _offenders("gender", document) == {"PlayerCardSchema.gender"}


def test_a_shape_scoped_admission_reaches_exactly_the_shapes_it_names():
    """The other half of ``PERMITTED_ON``: the admitted word is **on** the shape
    it names. Without this, deleting `gender` from the profile read would leave
    the refusal green and the You tab's *Who you play with* opening on nothing
    — and adding it to a second shape is caught by the refusal above, so the
    two tests together pin the word to exactly one place.
    """

    admitted_words = {field for _, field in PERMITTED_ON}
    reached = {
        (owner, field) for owner, field in _properties() if field in admitted_words
    }

    assert reached == set(PERMITTED_ON), (
        f"the shape-scoped admissions and the contract disagree: "
        f"admitted {sorted(PERMITTED_ON)}, found {sorted(reached)}"
    )


@pytest.mark.parametrize(
    "field",
    [
        "gender",
        "gender_preference",
        "bio",
        "last_seen_at",
        "lastActiveAt",
        "declined_at",
        "shard_key",
        "withheld_reason",
        "near_miss_count",
        "date_of_birth",
        "first_name",
    ],
)
def test_the_walk_refuses_the_fields_it_exists_to_refuse(field: str):
    """Driven against a deliberately broken document, because a gate that has
    never been observed to fail is indistinguishable from one that does not
    work — and these are fields somebody will add with a good reason."""

    assert any(offends(field, signals) for signals in FORBIDDEN.values())


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "nickname",
        "area_code",
        "fit",
        "liveness_reasons",
        "degraded_terms",
        "concerns",
        "threshold",
        "password_changed_at",
        "page",
        "last_position",
    ],
)
def test_the_walk_admits_what_the_contract_actually_carries(field: str):
    """The other half of the judgement, and the one a substring check fails.

    ``threshold`` is not a hold, ``page`` is not an age, and ``last_position`` is
    not a name — a rule that caught any of them would be loosened within the
    month, and a loosened rule catches nothing.
    """

    assert not any(offends(field, signals) for signals in FORBIDDEN.values())
