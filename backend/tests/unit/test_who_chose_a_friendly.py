"""``FriendlyChoiceQuery``, answered by ``player_profile``'s own declarations.

The mint decides *counted unless either declared for fun* (``docs/adr/0169``
§8) over a port that answers one word — *chose a friendly* — and this file is
the translation behind that word, run against the real declaration repository
on a real (SQLite) session, because what is under test is precisely what a
double would have to invent: which of the three declarations, and the absence
of one, reads as a friendly.

Four claims. **``FOR_FUN`` is the only yes.** **``COMPETITIVE`` is a no.**
**``NO_PREFERENCE`` is a no** — indifference about the kind of evening is not a
wish for a friendly, and the matcher's own mapping of it to the fun ruler is a
fact about weight vectors that must not leak into what somebody's game is.
**Never declared is a no.** And the read is **per sport**: a padel *for fun*
does not make a tennis mutual between the same two a friendly.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_friendly_choice_query,
    build_play_intent_declaration_repository,
)
from app.kernel import Sport, instant
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
)
from app.shared.ids import new_uuid

DECLARED_AT = instant(datetime(2026, 9, 1, 9, tzinfo=timezone.utc))


async def _declare(session_factory, player_id, sport: Sport, intent: PlayIntent):
    async with session_factory() as session:
        declarations = build_play_intent_declaration_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        await declarations.save(
            PlayIntentDeclaration.first_declared(
                player_id=player_id,
                sport=sport,
                intent=intent,
                surface=PlayIntentSurface.RATING_TAIL,
                occurred_at=DECLARED_AT,
            )
        )
        await session.commit()


async def _chose_a_friendly(session_factory, player_ids, *, sport: Sport):
    async with session_factory() as session:
        return await build_friendly_choice_query(session).chose_a_friendly_among(
            player_ids, sport=sport
        )


@pytest.mark.parametrize(
    ("intent", "chose"),
    [
        (PlayIntent.FOR_FUN, True),
        (PlayIntent.COMPETITIVE, False),
        (PlayIntent.NO_PREFERENCE, False),
    ],
    ids=lambda value: value.value if isinstance(value, PlayIntent) else str(value),
)
async def test_only_a_for_fun_declaration_is_a_friendly_chosen(
    session_factory, intent, chose
):
    ania, marek = new_uuid(), new_uuid()
    await _declare(session_factory, ania, Sport.TENNIS, intent)
    await _declare(session_factory, marek, Sport.TENNIS, PlayIntent.COMPETITIVE)

    answer = await _chose_a_friendly(session_factory, {ania, marek}, sport=Sport.TENNIS)

    assert answer == (frozenset({ania}) if chose else frozenset())


async def test_somebody_who_never_declared_chose_nothing(session_factory):
    """*Rated but not yet declared* is the ordinary state between finishing a
    rating run and answering the tail (``docs/adr/0094``), and it is an absence
    here like the other two — not a refusal, and not a friendly."""

    ania, marek = new_uuid(), new_uuid()
    await _declare(session_factory, ania, Sport.TENNIS, PlayIntent.FOR_FUN)

    answer = await _chose_a_friendly(session_factory, {ania, marek}, sport=Sport.TENNIS)

    assert answer == frozenset({ania})


async def test_the_answer_is_for_the_sport_asked_and_no_other(session_factory):
    ania, marek = new_uuid(), new_uuid()
    await _declare(session_factory, ania, Sport.PADEL, PlayIntent.FOR_FUN)
    await _declare(session_factory, ania, Sport.TENNIS, PlayIntent.COMPETITIVE)
    await _declare(session_factory, marek, Sport.TENNIS, PlayIntent.COMPETITIVE)

    assert (
        await _chose_a_friendly(session_factory, {ania, marek}, sport=Sport.TENNIS)
        == frozenset()
    )
    assert await _chose_a_friendly(
        session_factory, {ania, marek}, sport=Sport.PADEL
    ) == frozenset({ania})


async def test_both_choosing_a_friendly_are_both_named(session_factory):
    """The mint only asks *did either*, but the port answers who — a set rather
    than a bool, because a set is what every read here takes and a bool would
    have folded the rule into the adapter."""

    ania, marek = new_uuid(), new_uuid()
    await _declare(session_factory, ania, Sport.SQUASH, PlayIntent.FOR_FUN)
    await _declare(session_factory, marek, Sport.SQUASH, PlayIntent.FOR_FUN)

    assert await _chose_a_friendly(
        session_factory, {ania, marek}, sport=Sport.SQUASH
    ) == frozenset({ania, marek})
