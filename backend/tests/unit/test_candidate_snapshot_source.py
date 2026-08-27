"""What a search reads, and the two properties that make it safe to read.

**Bound once** — a search takes the container at entry and a refresh cannot move
it underneath — and **refreshed by delta**, sharing row references with the
container it replaces so the steady state never holds two copies of a row. The
second is what took the ``× 2`` out of trigger 4, and it is asserted here on
object identity rather than on equality, because equality would pass for a
container that had faithfully re-decoded all fifty thousand rows.
"""

from __future__ import annotations

import gc
from datetime import timedelta
from uuid import uuid4

from app.kernel import Instant, Sport
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.index_staleness import IndexFreshness
from app.modules.matchmaking.infrastructure.candidate_snapshot_source import (
    DatabaseCandidateSource,
)
from tests.unit.candidate_index_fixtures import (
    START,
    append,
    build_tail,
    intent_declared,
    opt_in,
    profile_created,
    rating_initialised,
)

PADEL = Partition.for_sport(Sport.PADEL)
TENNIS = Partition.for_sport(Sport.TENNIS)


def _source(session_factory) -> DatabaseCandidateSource:
    return DatabaseCandidateSource(
        session_factory=session_factory, empty_at=Instant(START)
    )


async def _onboard(session_factory, *, sport: str = "PADEL"):
    player = uuid4()
    await append(session_factory, profile_created(player))
    await append(session_factory, opt_in(player))
    await append(session_factory, rating_initialised(player, sport=sport))
    await append(session_factory, intent_declared(player, sport=sport))
    return player


async def _tail(session_factory) -> None:
    async with session_factory() as session:
        await build_tail().tick(session)


async def test_a_loaded_partition_holds_the_rows_the_projection_wrote(
    session_factory,
) -> None:
    player = await _onboard(session_factory)
    await _tail(session_factory)

    source = _source(session_factory)
    await source.refresh()

    rows = source.snapshot(PADEL).rows
    assert [row.player_id for row in rows] == [str(player)]
    assert rows[0].declared_intent == "COMPETITIVE"
    assert rows[0].areas[0].latitude == 52.23


async def test_the_snapshot_version_is_the_cursors_own_value(
    session_factory,
) -> None:
    """*Everything up to and including this is applied* — by construction.

    It is what makes ``docs/adr/0104``'s unexpiring search record reproducible,
    and it is the input the replay harness was missing.
    """

    await _onboard(session_factory)
    await _tail(session_factory)

    source = _source(session_factory)
    report = await source.refresh()

    assert report.snapshot_version == 4
    assert source.snapshot(PADEL).snapshot_version == 4


async def test_a_search_that_bound_a_container_keeps_it_across_a_refresh(
    session_factory,
) -> None:
    """§13, in one binding: the index cannot move underneath a running search.

    The refresh rebinds an attribute while the running search keeps its own
    container alive by reference. There is no lock, no copy and no coordination.
    """

    await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()

    bound = source.snapshot(PADEL)

    await _onboard(session_factory)
    await _tail(session_factory)
    await source.refresh()

    assert len(bound.rows) == 1
    assert len(source.snapshot(PADEL).rows) == 2
    assert source.snapshot(PADEL) is not bound


async def test_a_refresh_copies_the_reference_of_a_row_that_did_not_move(
    session_factory,
) -> None:
    """Identity, not equality — equality would pass for a full re-decode.

    This is the property trigger 4's arithmetic now rests on: the steady state
    never holds two copies of a row, so the peak is the index rather than twice
    it.
    """

    await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()
    unmoved = source.snapshot(PADEL).rows[0]

    await _onboard(session_factory)
    await _tail(session_factory)
    report = await source.refresh()

    carried = [row for row in source.snapshot(PADEL).rows if row is unmoved]
    assert carried == [unmoved]
    assert report.rows_decoded == 1
    assert report.rows_held == 2


async def test_a_refresh_that_found_nothing_decodes_nothing(
    session_factory,
) -> None:
    await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()

    assert (await source.refresh()).rows_decoded == 0


async def test_a_profile_edit_moves_the_row_even_though_no_level_changed(
    session_factory,
) -> None:
    """The stamp is on the index row, so the delta read is one question.

    An edit to a fact the row copies from the player's facts has to re-decode the
    row, or the container would keep serving the tags the player has just
    changed.
    """

    from app.modules.player_profile.domain.events import SocialTagsChanged

    player = await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()

    await append(session_factory, SocialTagsChanged(player, ("social_first",), START))
    await _tail(session_factory)
    report = await source.refresh()

    assert report.rows_decoded == 1
    assert source.snapshot(PADEL).rows[0].social_tags == ("social_first",)


async def test_the_gc_is_frozen_after_a_refresh_that_decoded_rows(
    session_factory, monkeypatch
) -> None:
    """One automatic gen-2 collection over a live index cost 57.9 ms.

    Safe because a ``CandidateRow`` has no reference cycles — asserted in
    ``test_candidate_row_fence.py``, which is the other half of this claim.
    """

    freezes = _count_freezes(monkeypatch)
    await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)

    await source.refresh()

    assert freezes() == 1


async def test_a_refresh_that_decoded_nothing_does_not_freeze(
    session_factory, monkeypatch
) -> None:
    """``gc.freeze()`` promotes **everything tracked**, not only the new rows.

    A refresh with nothing to protect would therefore promote whatever requests
    happened to be in flight, every two seconds, for ever — a slow leak bought
    for nothing, since there is no newly decoded row for the collection to
    interrupt. The freeze is paid where there is something to buy.
    """

    freezes = _count_freezes(monkeypatch)
    source = _source(session_factory)

    await source.refresh()
    await source.refresh()

    assert freezes() == 0


def _count_freezes(monkeypatch):
    frozen = 0

    def counting_freeze() -> None:
        nonlocal frozen
        frozen += 1

    monkeypatch.setattr(gc, "freeze", counting_freeze)
    return lambda: frozen


async def test_a_container_never_holds_a_row_from_past_its_own_version(
    session_factory,
) -> None:
    """The cursor and the rows are two statements, and the tail commits between.

    A container that claimed version N while holding a row reflecting N+5 would
    still be right that everything up to N was applied, and would no longer *be*
    the index at N — which is what makes a recorded search interpretable later
    (``docs/adr/0104``). The load is bounded at both ends for that reason, and
    this drives the race directly by advancing the log between the two reads.
    """

    from app.modules.player_profile.domain.events import SocialTagsChanged

    player = await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()
    version = source.snapshot(PADEL).snapshot_version

    # The tail moves on while the container built above is still bound. A refresh
    # that read rows without an upper bound would pick this up under the *old*
    # version the moment the two statements straddled the commit.
    await append(session_factory, SocialTagsChanged(player, ("social_first",), START))
    await _tail(session_factory)

    stale = source.snapshot(PADEL)
    assert stale.snapshot_version == version
    assert stale.rows[0].applied_through_sequence_no <= version
    assert stale.rows[0].social_tags == ("competitive_edge",)


async def test_a_row_with_no_profile_behind_it_is_not_a_candidate(
    session_factory,
) -> None:
    """It has no grid and no area, so it could not be generated for.

    Said with a join rather than with columns full of nulls that a term would
    eventually read as a measured zero.
    """

    player = uuid4()
    await append(session_factory, rating_initialised(player))
    await _tail(session_factory)

    source = _source(session_factory)
    await source.refresh()

    assert source.snapshot(PADEL).rows == ()


async def test_a_partition_nobody_has_rated_answers_with_an_empty_container(
    session_factory,
) -> None:
    """*No padel players near you* is an answer; a sport nobody rated is not an error.

    The empty container still carries the version and the freshness, so a search
    over an empty sport is recorded and refused on exactly the same terms as any
    other.
    """

    await _onboard(session_factory, sport="PADEL")
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()

    empty = source.snapshot(TENNIS)
    assert empty.rows == ()
    assert empty.snapshot_version == source.snapshot(PADEL).snapshot_version


async def test_a_container_reports_its_own_lag_and_the_rung_it_lands_on(
    session_factory,
) -> None:
    await _onboard(session_factory)
    await _tail(session_factory)
    source = _source(session_factory)
    await source.refresh()

    snapshot = source.snapshot(PADEL)
    fresh = snapshot.caught_up_at + timedelta(seconds=3)
    day_old = snapshot.caught_up_at + timedelta(hours=25)

    assert snapshot.freshness_at(fresh) is IndexFreshness.FRESH
    assert snapshot.freshness_at(day_old) is IndexFreshness.REFUSED
    assert snapshot.lag_at(fresh) == timedelta(seconds=3)
