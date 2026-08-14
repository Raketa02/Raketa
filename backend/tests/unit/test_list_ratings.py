"""Reading back the ratings a player holds, through the rating repository.

The read is one call now, so what is worth asserting is what the repository does
underneath it: which streams the encoded lookup key finds, that a player sees only
their own, and that a rated sport yields exactly one rating carrying the numbers
the player was shown.

Nothing here fakes the repository. Faking it would leave the encoded key and the
replay — everything this slice introduced — exercised by nothing, and the key's
failure mode is silence: a renamed field returns no streams, which is
indistinguishable from an unrated player, the ordinary answer for a new account.
"""

from __future__ import annotations

from app.kernel import Sport
from app.modules.rating.application.commands import ListRatingsQuery
from app.shared.ids import new_uuid
from tests.unit.assessment_requests import request, result_of, run_to_result, start
from tests.unit.fake_event_store import InMemoryEventStore


async def test_an_unrated_player_holds_no_ratings() -> None:
    # The state of every new account, and never an error.
    store = InMemoryEventStore()

    held = await request(store).list_ratings.execute(
        ListRatingsQuery(player_id=new_uuid())
    )

    assert held == []


async def test_a_rated_sport_yields_one_rating() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    final, _ = await run_to_result(store, player_id, Sport.PADEL)

    held = await request(store).list_ratings.execute(
        ListRatingsQuery(player_id=player_id)
    )

    assert [rating.sport for rating in held] == [Sport.PADEL]
    result = result_of(final)
    rating = held[0]
    assert rating.mu == result.mu
    assert rating.sigma == result.sigma
    assert rating.confidence == result.confidence
    assert rating.range_low == result.range_low
    assert rating.range_high == result.range_high
    # The band travels as the engine computed it — its boundaries are uneven and
    # were wrong once already, so nothing downstream may restate them.
    assert rating.band_name == result.band.name
    assert rating.band_lower == result.band.lower
    assert rating.band_upper == result.band.upper
    assert rating.status == result.status
    assert rating.engine_version == result.engine_version


async def test_each_rated_sport_is_listed_once_and_the_others_are_absent() -> None:
    store = InMemoryEventStore()
    player_id = new_uuid()
    await run_to_result(store, player_id, Sport.PADEL)
    await run_to_result(store, player_id, Sport.TENNIS)

    held = await request(store).list_ratings.execute(
        ListRatingsQuery(player_id=player_id)
    )

    assert sorted(rating.sport.value for rating in held) == sorted(
        [Sport.PADEL.value, Sport.TENNIS.value]
    )
    assert len(held) == 2


async def test_a_started_but_unfinished_run_produces_no_rating() -> None:
    # A rating exists because a run completed, not because one was opened.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await start(store, player_id, Sport.PADEL)

    held = await request(store).list_ratings.execute(
        ListRatingsQuery(player_id=player_id)
    )

    assert held == []


async def test_a_player_reads_only_their_own_ratings() -> None:
    store = InMemoryEventStore()
    mine = new_uuid()
    theirs = new_uuid()
    await run_to_result(store, mine, Sport.PADEL)
    await run_to_result(store, theirs, Sport.TENNIS)

    held = await request(store).list_ratings.execute(ListRatingsQuery(player_id=mine))

    assert [rating.sport for rating in held] == [Sport.PADEL]


async def test_a_replayed_rating_is_at_the_version_its_stream_holds() -> None:
    # Replay, not reconstruction: one initialisation event is one version, which
    # is what a later transition's append would expect.
    store = InMemoryEventStore()
    player_id = new_uuid()
    await run_to_result(store, player_id, Sport.PADEL)

    held = await request(store).list_ratings.execute(
        ListRatingsQuery(player_id=player_id)
    )

    assert held[0].version == 1
    # Replaying records nothing: a read can never write through.
    assert held[0].pull_events() == []


async def test_saving_a_rating_that_decided_nothing_writes_nothing() -> None:
    # The same no-op the assessment's ``save`` has, and the reason neither caller
    # checks first. The store counts calls rather than rows, because an empty
    # append writes nothing in both stores and counting rows cannot tell "wrote
    # nothing" from "never asked".
    store = InMemoryEventStore()
    player_id = new_uuid()
    await run_to_result(store, player_id, Sport.PADEL)

    call = request(store)
    held = await call.list_ratings.execute(ListRatingsQuery(player_id=player_id))
    store.appends = 0
    await call.ratings_repository.save(held[0])

    assert store.appends == 0
    assert call.events.published == []
