"""Reading a run: pure replay, scoped to the player who owns it.

The ownership guard has one implementation now — the repository's ``load`` will
not hand an aggregate back without being told whose it is — so what these assert
is that reading goes through it, and that an absent run and somebody else's are
the same answer.
"""

from __future__ import annotations

import pytest

from app.modules.rating.domain.errors import AssessmentNotFound
from app.shared.ids import new_uuid
from tests.unit.assessment_requests import answer, read, request, run_to_result, start
from tests.unit.fake_event_store import InMemoryEventStore, utc

NOW = utc(2026, 8, 14)


async def test_reading_returns_the_outstanding_question() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step
    after = await answer(store, player_id, opening)
    assert after.question is not None

    step = await read(store, player_id, opening.assessment_id)

    assert step.question is not None
    assert step.question.id == after.question.id
    assert step.questions_asked == 1
    assert step.result is None


async def test_reading_a_finished_run_returns_its_result() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id)

    step = await read(store, player_id, final.assessment_id)

    assert step.status == "completed"
    assert step.question is None
    assert step.result is not None and final.result is not None
    assert step.result.mu == final.result.mu


async def test_reading_an_abandoned_run_returns_neither() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    opening = (await start(store, player_id)).step

    ending = request(store)
    run = await ending.repository.load(opening.assessment_id, for_player=player_id)
    run.abandon(occurred_at=NOW)
    await ending.repository.save(run)

    step = await read(store, player_id, opening.assessment_id)

    assert step.status == "abandoned"
    assert step.question is None
    assert step.result is None


async def test_another_players_assessment_is_not_found() -> None:
    store = InMemoryEventStore()
    opening = (await start(store, new_uuid())).step

    with pytest.raises(AssessmentNotFound):
        await read(store, new_uuid(), opening.assessment_id)


async def test_an_absent_assessment_is_not_found() -> None:
    store = InMemoryEventStore()

    with pytest.raises(AssessmentNotFound):
        await read(store, new_uuid(), new_uuid())
