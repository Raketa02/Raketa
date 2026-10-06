"""Play intent: one stream per (player, sport), and a preference's no-op rule.

Three claims are load-bearing here and none of them is about a route, because
there is not one yet (``docs/adr/0094`` puts the write path in its own build).

**The pair is the identity**, so the stream id is derived rather than minted —
which is a concurrency control and not a naming convenience: two first
declarations for one pair compute the same id and collide on version 1 of one
stream rather than opening two.

**Nothing holds two sports' intent at once**, which is what makes *intent does
not transfer between sports* structural rather than remembered.

**A declaration of the value already held records nothing.** Intent is a
preference, and re-declaring it says nothing the previous answer did not.
"""

from __future__ import annotations

import pytest

from app.application.events.store import EventStreamVersionConflict
from app.kernel import Sport
from app.modules.player_profile.domain.events import PlayIntentDeclared
from app.modules.player_profile.domain.ids import play_intent_declaration_id
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
)
from app.modules.player_profile.infrastructure.event_sourced_play_intent_declaration_repository import (  # noqa: E501
    EventSourcedPlayIntentDeclarationRepository,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import (
    InMemoryEventStore,
    RecordingPublisher,
    utc,
)

PLAYER = new_uuid()
DECLARED_AT = utc(2026, 8, 25)
LATER = utc(2026, 9, 1)


def a_declaration(**overrides) -> PlayIntentDeclaration:
    arguments = dict(
        player_id=PLAYER,
        sport=Sport.PADEL,
        intent=PlayIntent.COMPETITIVE,
        surface=PlayIntentSurface.RATING_TAIL,
        occurred_at=DECLARED_AT,
    )
    arguments.update(overrides)
    return PlayIntentDeclaration.first_declared(**arguments)


def replayed(declaration: PlayIntentDeclaration) -> PlayIntentDeclaration:
    return PlayIntentDeclaration.from_history(declaration.pull_events())


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_the_stream_id_is_a_function_of_the_pair():
    """No lookup table, and no id on the event: the pair *is* the identity."""

    declaration = a_declaration()

    assert declaration.id == play_intent_declaration_id(PLAYER, Sport.PADEL)


def test_the_same_pair_always_computes_the_same_stream():
    """Which is what makes two concurrent first declarations collide on version
    1 of one stream rather than quietly opening a second (#35's trade)."""

    assert a_declaration().id == a_declaration().id


def test_two_sports_are_two_streams():
    """*Levels never transfer between sports, and intent does not either* — and
    here that is structural rather than a rule to remember."""

    padel = a_declaration(sport=Sport.PADEL)
    tennis = a_declaration(sport=Sport.TENNIS)

    assert padel.id != tennis.id


def test_a_declaration_never_shares_a_stream_with_the_rating_for_the_same_pair():
    """Both are keyed ``(player, sport)`` and both derive a uuid5 from it, so
    the namespaces have to differ — otherwise only the aggregate-type column
    keeps two aggregates' histories apart, which is one column too few."""

    assert play_intent_declaration_id(PLAYER, Sport.PADEL) != skill_rating_id(
        PLAYER, Sport.PADEL
    )


# ---------------------------------------------------------------------------
# Declaring
# ---------------------------------------------------------------------------


def test_a_first_declaration_records_one_event_carrying_the_pair():
    declaration = a_declaration()

    (recorded,) = declaration.pull_events()

    assert isinstance(recorded, PlayIntentDeclared)
    assert recorded.player_id == PLAYER
    assert recorded.sport == "PADEL"
    assert recorded.intent == "COMPETITIVE"
    assert recorded.surface == "RATING_TAIL"


def test_no_preference_is_an_answer_like_any_other():
    """The matcher cannot otherwise tell *either suits me* from *I never opened
    that screen*, and those are different facts. Nobody is backfilled to it."""

    declaration = a_declaration(intent=PlayIntent.NO_PREFERENCE)

    assert declaration.pull_events()[0].intent == "NO_PREFERENCE"


def test_changing_the_declared_value_records_it():
    declaration = replayed(a_declaration())

    declaration.declare(
        PlayIntent.FOR_FUN,
        surface=PlayIntentSurface.SEARCH_SWITCH,
        occurred_at=LATER,
    )

    (recorded,) = declaration.pull_events()
    assert recorded.intent == "FOR_FUN"
    assert recorded.surface == "SEARCH_SWITCH"
    assert declaration.intent is PlayIntent.FOR_FUN


def test_a_declaration_made_on_the_deck_names_the_deck():
    """#280, kept for the events that carry it. The deck used to read the
    declaration — ``POST /deck`` has no mode — and drew the same interstitial a
    search does; ``docs/adr/0169`` §2 ended that, and the deck reads no
    declaration now. ``DECK`` stays in the closed five, stored on the events
    that carry it and never emitted again: widening was additive, so every code
    already in a stream still means what it meant, and ``SEARCH_SWITCH`` is
    still left naming the search screen alone.
    """

    declaration = replayed(a_declaration())

    declaration.declare(
        PlayIntent.FOR_FUN,
        surface=PlayIntentSurface.DECK,
        occurred_at=LATER,
    )

    (recorded,) = declaration.pull_events()
    assert recorded.surface == "DECK"
    assert declaration.surface is PlayIntentSurface.DECK


def test_declaring_the_value_already_held_records_nothing():
    """The preference rule. ``PUT /play-intents/{sport}`` is unkeyed precisely
    because of this: the same request twice lands the same state and the second
    appends nothing, so it needs no idempotency key to be safe."""

    declaration = replayed(a_declaration(intent=PlayIntent.COMPETITIVE))

    declaration.declare(
        PlayIntent.COMPETITIVE,
        surface=PlayIntentSurface.PROFILE_SCREEN,
        occurred_at=LATER,
    )

    assert declaration.pull_events() == []


def test_the_surface_is_not_part_of_what_counts_as_a_change():
    """*The same answer, from a different screen* is a fact about where somebody
    was standing, and nothing branches on it — so it must not be able to grow a
    stream on its own. This is the one place this aggregate could quietly have
    become a consent log."""

    declaration = replayed(a_declaration(surface=PlayIntentSurface.RATING_TAIL))

    declaration.declare(
        PlayIntent.COMPETITIVE,
        surface=PlayIntentSurface.DRIFT_PROMPT,
        occurred_at=LATER,
    )

    assert declaration.pull_events() == []
    assert declaration.surface is PlayIntentSurface.RATING_TAIL


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def test_a_declaration_replays_to_itself():
    declaration = a_declaration()
    expected = (
        declaration.player_id,
        declaration.sport,
        declaration.intent,
        declaration.surface,
        declaration.declared_at,
    )

    rebuilt = replayed(declaration)

    assert (
        rebuilt.player_id,
        rebuilt.sport,
        rebuilt.intent,
        rebuilt.surface,
        rebuilt.declared_at,
    ) == expected
    assert rebuilt.version == 1


def test_the_latest_declaration_is_the_state_and_the_first_one_is_the_stamp():
    declaration = a_declaration()
    opening = declaration.pull_events()
    declaration = PlayIntentDeclaration.from_history(opening)
    declaration.declare(
        PlayIntent.FOR_FUN,
        surface=PlayIntentSurface.SEARCH_SWITCH,
        occurred_at=LATER,
    )

    rebuilt = PlayIntentDeclaration.from_history(opening + declaration.pull_events())

    assert rebuilt.intent is PlayIntent.FOR_FUN
    assert rebuilt.declared_at == DECLARED_AT
    assert rebuilt.updated_at == LATER
    assert rebuilt.version == 2


def test_an_event_this_aggregate_does_not_know_is_refused_rather_than_ignored():
    """A fold that silently skipped an event would rebuild a state that never
    existed, and it would do it quietly."""

    class NotOurs:
        occurred_at = DECLARED_AT

    with pytest.raises(TypeError):
        PlayIntentDeclaration.from_history([NotOurs()])


# ---------------------------------------------------------------------------
# The repository, over the real codec
# ---------------------------------------------------------------------------


def a_repository(store):
    return EventSourcedPlayIntentDeclarationRepository(
        event_store=store, events=RecordingPublisher()
    )


async def test_a_saved_declaration_is_found_by_its_pair_and_nothing_else():
    """The point of the derived id: *has this player declared in this sport* is
    one stream read, not a scan of their sports."""

    store = InMemoryEventStore()
    await a_repository(store).save(a_declaration(sport=Sport.TENNIS))

    found = await a_repository(store).load(player_id=PLAYER, sport=Sport.TENNIS)
    other_sport = await a_repository(store).load(player_id=PLAYER, sport=Sport.PADEL)
    other_player = await a_repository(store).load(
        player_id=new_uuid(), sport=Sport.TENNIS
    )

    assert found is not None
    assert found.intent is PlayIntent.COMPETITIVE
    assert other_sport is None, "two sports are two streams"
    assert other_player is None


async def test_a_declaration_that_moved_nothing_never_reaches_the_store():
    """Counted rather than inferred from an empty stream: an empty append is a
    no-op in the real adapter too, so rows alone cannot tell *wrote nothing*
    from *was never asked*."""

    store = InMemoryEventStore()
    await a_repository(store).save(a_declaration())

    repository = a_repository(store)
    declaration = await repository.load(player_id=PLAYER, sport=Sport.PADEL)
    assert declaration is not None
    declaration.declare(
        PlayIntent.COMPETITIVE,
        surface=PlayIntentSurface.SEARCH_SWITCH,
        occurred_at=LATER,
    )
    appends_before = store.appends
    await repository.save(declaration)

    assert store.appends == appends_before


async def test_a_second_first_declaration_for_one_pair_is_refused_by_the_store():
    """Two requests that both read an empty stream compute the same id, collide
    on version 1, and the store rejects the loser — which is what the derived id
    is *for*, and it is the reason a first declaration needs no idempotency key.
    """

    store = InMemoryEventStore()
    await a_repository(store).save(a_declaration())

    with pytest.raises(EventStreamVersionConflict):
        # A fresh repository, so it has read nothing and expects version zero —
        # exactly the state a second concurrent request would be in.
        await a_repository(store).save(a_declaration(intent=PlayIntent.FOR_FUN))


async def test_a_change_appends_to_the_stream_the_first_declaration_opened():
    store = InMemoryEventStore()
    await a_repository(store).save(a_declaration())

    repository = a_repository(store)
    declaration = await repository.load(player_id=PLAYER, sport=Sport.PADEL)
    assert declaration is not None
    declaration.declare(
        PlayIntent.FOR_FUN,
        surface=PlayIntentSurface.SEARCH_SWITCH,
        occurred_at=LATER,
    )
    await repository.save(declaration)

    reloaded = await a_repository(store).load(player_id=PLAYER, sport=Sport.PADEL)
    assert reloaded is not None
    assert reloaded.intent is PlayIntent.FOR_FUN
    assert reloaded.version == 2
