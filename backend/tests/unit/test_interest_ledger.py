"""The interest ledger: durable, expiring, and **structurally unable to be an inbox.**

Two claims run through every test here.

**A yes lapses; it never quietly decays** (``docs/adr/0127``). Every read is
bounded by ``now``, so *lapsed* and *never sent* are the same answer at this seam —
and the sweep that removes the row is a tidy-up rather than the thing that makes
expiry true.

**There is no shape here that could answer *who has said yes to me***. That is
asserted over the port's own surface rather than left to a reviewer, because the
promise ``docs/adr/0109`` makes is not *we do not query for it* but *there is
nothing to query*.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.domain.interest import (
    Interest,
    InterestLedger,
    OriginKey,
    expires_at,
)
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    InclusionReason,
    PoolDescription,
    RecordedCard,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    StagedCounts,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_interest_ledger import (
    SqlAlchemyInterestLedger,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_search_store import (
    SqlAlchemySearchStore,
)
from app.kernel import InvariantViolated
from app.modules.player_profile.domain.availability import Window

NOW = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)
TTL = 21

ADA = UUID("11111111-1111-1111-1111-111111111111")
BEA = UUID("22222222-2222-2222-2222-222222222222")
CAI = UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def ledger(session):
    return SqlAlchemyInterestLedger(session)


async def _a_search(
    session,
    *,
    searcher_id: UUID,
    shown: tuple[UUID, ...],
    at: datetime = NOW,
    sport: Sport = Sport.PADEL,
    lifted: tuple[UUID, ...] = (),
) -> UUID:
    """One recorded search, so an origin key has something true to point at.

    ``lifted`` marks the rows the pipeline recorded as ``INTEREST_LIFT``, which is
    what the expiry loop joins against to decide whether a yes ever fired.
    """

    search_id = uuid4()
    await SqlAlchemySearchStore(session).record(
        SearchRecord(
            id=search_id,
            searcher_id=searcher_id,
            sport=sport,
            mode=SearchMode.COMPETITIVE,
            intent_read=None,
            surface=SearchSurface.SHORTLIST,
            initiation=SearchInitiation.HUMAN,
            at=at,
            engine_version="matchfit-v1",
            ruleset_version="r2026-08-26-a",
            snapshot_version=42,
            trace_id="trace-1",
            index_stale=False,
            counts=StagedCounts(
                n_generated=len(shown),
                excluded_by_gate={},
                n_scored=len(shown),
                n_cleared_floor=len(shown),
                n_returned=len(shown),
                n_near_miss_recorded=0,
            ),
            best_withheld_fit=None,
            pool_description=PoolDescription(
                sport=sport,
                radius_km_used=10,
                players_in_range=len(shown),
                window=Window.THIS_WEEK,
            ),
            searcher_grid=("1:EVENING",),
            searcher_slot_count=1,
            radius_clamp_bit=False,
            rung_offers=None,
            offered_by_search_id=None,
            rung_taken=None,
            latency_ms_by_stage={"pipeline": 1},
            candidates=tuple(
                SearchCandidateRecord(
                    band=CandidateBand.RETURNED,
                    position=position,
                    player_id=player_id,
                    fit=70.0,
                    terms=(),
                    degraded_terms=(),
                    degraded_reasons=(),
                    modifiers=(),
                    liveness_reasons=(),
                    liveness_signals={},
                    shared_count=1,
                    their_slot_count=1,
                    days_away=0,
                    inclusion_reason=(
                        InclusionReason.INTEREST_LIFT
                        if player_id in lifted
                        else None
                    ),
                    withheld_reason=None,
                    missing_terms=(),
                    reliability_penalty_applied=False,
                    reliability_penalty_decisive=False,
                    concerns=(),
                    distance_km=3,
                    card=RecordedCard(
                        nickname="someone",
                        photo_id=None,
                        area_code="LDN-CENTRAL",
                        social_tags=(),
                        level=2.7,
                        band="Improver",
                        range_low=2.36,
                        range_high=3.04,
                    ),
                    at_stake=None,
                )
                for position, player_id in enumerate(shown, start=1)
            ),
        )
    )
    return search_id


async def _yes(
    ledger,
    session,
    *,
    sender: UUID,
    recipient: UUID,
    at: datetime = NOW,
    sport: Sport = Sport.PADEL,
    lifted: tuple[UUID, ...] = (),
) -> Interest:
    search_id = await _a_search(
        session,
        searcher_id=sender,
        shown=(recipient,),
        at=at,
        sport=sport,
        lifted=lifted,
    )
    interest = Interest(
        from_player_id=sender,
        to_player_id=recipient,
        sport=sport,
        at=at,
        expires_at=expires_at(at, TTL),
        origin=OriginKey(search_id=search_id, position=1),
    )
    await ledger.record(interest)
    return interest


# ---------------------------------------------------------------------------
# The shape of the port
# ---------------------------------------------------------------------------


def test_the_ledger_offers_no_shape_that_could_answer_who_said_yes_to_me():
    """**An inbox is not a query this port can express** (``docs/adr/0109``).

    The one method that reads incoming yeses takes the population it may answer
    about, so asking it about the whole city would mean already holding a list of
    the whole city — and there is nothing else here that faces that direction.
    """

    reads_towards_me = [
        name
        for name in dir(InterestLedger)
        if not name.startswith("_") and name not in {"record", "lapse"}
    ]
    assert sorted(reads_towards_me) == [
        "days_ago_towards",
        "find",
        "mutual",
        "outgoing",
        "outstanding",
    ]
    annotations = InterestLedger.days_ago_towards.__annotations__
    assert "senders" in annotations, (
        "the only read of incoming yeses stopped being bounded by a population, "
        "which is the one thing keeping it from being an inbox"
    )


def test_a_yes_to_yourself_is_not_a_state_this_product_has():
    with pytest.raises(InvariantViolated):
        Interest(
            from_player_id=ADA,
            to_player_id=ADA,
            sport=Sport.PADEL,
            at=NOW,
            expires_at=expires_at(NOW, TTL),
            origin=OriginKey(search_id=uuid4(), position=1),
        )


def test_the_expiry_is_dated_at_birth_and_reads_flat():
    """**Twenty-one days, then absent** — no taper, and the age is carried whole.

    ``days_ago_at`` is the lift's recorded input and never a boolean, because the
    ``+14`` is flat: a boolean would be the *sufficient* input and the age — the
    entire x-axis of *acceptance by age of yes* — would be lost within the month.
    """

    yes = Interest(
        from_player_id=ADA,
        to_player_id=BEA,
        sport=Sport.PADEL,
        at=NOW,
        expires_at=expires_at(NOW, TTL),
        origin=OriginKey(search_id=uuid4(), position=1),
    )

    assert yes.expires_at == NOW + timedelta(days=TTL)
    assert yes.is_live_at(NOW + timedelta(days=20, hours=23))
    assert not yes.is_live_at(NOW + timedelta(days=21))
    assert yes.days_ago_at(NOW + timedelta(days=18)) == 18


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------


async def test_a_yes_round_trips_with_the_origin_key_on_its_own_row(
    ledger, session
):
    """**Two columns, never a third table** (``search-telemetry.md`` §4)."""

    written = await _yes(ledger, session, sender=ADA, recipient=BEA)

    found = await ledger.find(
        from_player_id=ADA, to_player_id=BEA, sport=Sport.PADEL, now=NOW
    )

    assert found == written
    assert found.origin == written.origin


async def test_a_lapsed_yes_is_invisible_to_every_read(ledger, session):
    """*Lapsed* and *never sent* are deliberately the same answer here.

    Nothing has swept the row: expiry is a date, and the sweep is a tidy-up.
    """

    await _yes(ledger, session, sender=ADA, recipient=BEA)
    later = NOW + timedelta(days=TTL, minutes=1)

    assert (
        await ledger.find(
            from_player_id=ADA, to_player_id=BEA, sport=Sport.PADEL, now=later
        )
        is None
    )
    assert await ledger.outgoing(player_id=ADA, now=later) == ()
    assert await ledger.outstanding(player_id=ADA, now=later) == {}
    assert (
        await ledger.days_ago_towards(
            player_id=BEA, sport=Sport.PADEL, senders=[ADA], now=later
        )
        == {}
    )


async def test_outstanding_counts_what_is_in_flight_and_not_what_came_back(
    ledger, session
):
    """**Outstanding means sent, unexpired and not yet mutual** (ADR-0127 §3).

    A mutual has been answered and is no longer in flight, which is the one way
    room at the cap opens up other than waiting.
    """

    await _yes(ledger, session, sender=ADA, recipient=BEA)
    await _yes(ledger, session, sender=ADA, recipient=CAI)
    await _yes(ledger, session, sender=ADA, recipient=BEA, sport=Sport.TENNIS)
    assert await ledger.outstanding(player_id=ADA, now=NOW) == {
        Sport.PADEL: 2,
        Sport.TENNIS: 1,
    }, "the cap is per sport, and one read answers for every one of them"

    await _yes(ledger, session, sender=BEA, recipient=ADA)

    assert await ledger.outstanding(player_id=ADA, now=NOW) == {
        Sport.PADEL: 1,
        Sport.TENNIS: 1,
    }


async def test_a_mutual_answers_in_this_players_own_rows(ledger, session):
    """The one shape in which somebody else's yes reaches its recipient.

    Every row that comes back is one this player wrote; the other person's row is
    read only to decide whether this one is returned at all.
    """

    await _yes(ledger, session, sender=ADA, recipient=BEA)
    await _yes(ledger, session, sender=ADA, recipient=CAI)
    await _yes(ledger, session, sender=CAI, recipient=ADA)

    mutual = await ledger.mutual(player_id=ADA, now=NOW)

    assert [row.to_player_id for row in mutual] == [CAI]
    assert all(row.from_player_id == ADA for row in mutual)


async def test_the_lift_read_answers_only_about_the_people_it_was_asked_about(
    ledger, session
):
    """One keyed read over the candidate set, and never a query per row."""

    await _yes(
        ledger, session, sender=BEA, recipient=ADA, at=NOW - timedelta(days=3)
    )
    await _yes(ledger, session, sender=CAI, recipient=ADA)

    ages = await ledger.days_ago_towards(
        player_id=ADA, sport=Sport.PADEL, senders=[BEA], now=NOW
    )

    assert ages == {BEA: 3}, "a sender nobody asked about was named anyway"
    assert (
        await ledger.days_ago_towards(
            player_id=ADA, sport=Sport.PADEL, senders=[], now=NOW
        )
        == {}
    )


async def test_the_lift_read_is_sport_scoped(ledger, session):
    await _yes(ledger, session, sender=BEA, recipient=ADA, sport=Sport.TENNIS)

    assert (
        await ledger.days_ago_towards(
            player_id=ADA, sport=Sport.PADEL, senders=[BEA], now=NOW
        )
        == {}
    )


async def test_expiry_removes_the_row_and_counts_the_yeses_that_lifted_nobody(
    ledger, session
):
    """The falsifier is counted **as the rows go**, because that is the last moment.

    *Yeses that expired having never lifted anybody* is ``INTEREST_TTL``'s one
    day-one falsifier (``the-five-numbers.md`` §8). A lapsed row leaves no trace
    by design, so a figure computed a day later would have nothing to count.
    """

    fired = await _yes(ledger, session, sender=BEA, recipient=ADA)
    await _yes(ledger, session, sender=CAI, recipient=ADA)
    # ADA ran a search a week later that lifted BEA with the reason recorded.
    await _a_search(
        session,
        searcher_id=ADA,
        shown=(BEA,),
        at=NOW + timedelta(days=7),
        lifted=(BEA,),
    )
    assert fired.from_player_id == BEA

    lapsed = await ledger.lapse(now=NOW + timedelta(days=TTL, minutes=1))

    assert lapsed.removed == 2
    assert lapsed.never_lifted == 1, (
        "the yes that was never fired is the whole of the falsifier"
    )
    assert await ledger.outgoing(player_id=BEA, now=NOW) == ()


async def test_expiry_leaves_a_live_yes_alone(ledger, session):
    """**Nothing of the player's is quietly shortened.**"""

    await _yes(ledger, session, sender=ADA, recipient=BEA)

    lapsed = await ledger.lapse(now=NOW + timedelta(days=20))

    assert lapsed.removed == 0
    assert len(await ledger.outgoing(player_id=ADA, now=NOW + timedelta(days=20))) == 1


async def test_the_ledger_does_not_commit_for_its_caller(ledger, session):
    """The transaction boundary is the command's, exactly as the record's is."""

    await _yes(ledger, session, sender=ADA, recipient=BEA)
    await session.rollback()

    assert (
        await ledger.find(
            from_player_id=ADA, to_player_id=BEA, sport=Sport.PADEL, now=NOW
        )
        is None
    )


async def test_a_lapsed_yes_may_be_sent_again_before_anything_has_swept_it(
    ledger, session
):
    """**The sweep is a tidy-up and is never load-bearing for a write.**

    A lapsed row still occupies its key until the loop gets to it, and the key
    *is* ``(from, to, sport)``. If the write collided with it, saying *Let's
    play* again to somebody whose earlier yes expired would fail for up to an
    hour — and for ever with the loop switched off, which every docstring in
    this feature says is a safe thing to do.
    """

    first = await _yes(ledger, session, sender=ADA, recipient=BEA)
    later = NOW + timedelta(days=TTL + 3)

    again = Interest(
        from_player_id=ADA,
        to_player_id=BEA,
        sport=Sport.PADEL,
        at=later,
        expires_at=expires_at(later, TTL),
        origin=first.origin,
    )
    await ledger.record(again)

    standing = await ledger.find(
        from_player_id=ADA, to_player_id=BEA, sport=Sport.PADEL, now=later
    )
    assert standing == again
    assert standing.expires_at > first.expires_at, "the fresh yes kept the old expiry"
    assert len(await ledger.outgoing(player_id=ADA, now=later)) == 1


async def test_a_live_yes_is_never_replaced_by_the_write_path(ledger, session):
    """The replacement above is scoped to a row that is **already lapsed**.

    Stated as its own case because the delete is the dangerous half: a predicate
    one character wider would silently re-date a yes on every tap, which is the
    unbounded life ``docs/adr/0127`` refused.
    """

    first = await _yes(ledger, session, sender=ADA, recipient=BEA)

    with pytest.raises(IntegrityError):
        await ledger.record(
            Interest(
                from_player_id=ADA,
                to_player_id=BEA,
                sport=Sport.PADEL,
                at=NOW + timedelta(days=1),
                expires_at=expires_at(NOW + timedelta(days=1), TTL),
                origin=first.origin,
            )
        )
