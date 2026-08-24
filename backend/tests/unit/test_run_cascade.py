"""One dispatch: which store answers which rung, and what gets written.

`test_cascade_ladder.py` owns the rules — the pool, the wall, the floor, the
order, the quiet hours. This owns the **reach**: that a dark rung reads no store
at all, that a candidate the record already refuses never costs a rating replay,
that a live claim leaves the row due, and that an empty first wave stops the
second waiting for it.

Two claims are asserted against the **real** engines rather than a double, and
both are about the engines: that ADR-0061's wall is the pairing engine's
`TargetBand`, and that the stand-in observer `analyse` needs cannot move it.
Everything else uses `FakeScorer`, because a fixture that had to produce a fit of
71 through ten weighted terms is a fixture nobody can read.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.bootstrap.composition import build_match_scorer
from app.engines.matchmaking import PlayerRef, PlayerSkill, level, uncertainty
from app.kernel import (
    Instant,
    OfferKind,
    Sport,
    apply_fraction,
    deadlines,
    grosze,
    minutes,
    seat_price,
    shifted,
)

from app.modules.now.application.cascade import (
    POOL_LIMIT,
    CascadeBatch,
    CascadeOutcome,
    OpenCascade,
    RunCascade,
    _band_from,
)
from app.modules.now.domain.cascade import (
    CASCADE_FLOOR,
    Band,
    PendingWave,
    Rung,
    Wave,
    delivery_at,
    wave_due,
)
from tests.unit.cascade_doubles import (
    FakeCascadeWaves,
    FakeClubRegulars,
    FakeContexts,
    FakeDiaries,
    FakeOffers,
    FakeRatedPlayers,
    FakeRatings,
    FakeScorer,
    FakeStandbyQueue,
    FixedClock,
    SpyUnitOfWork,
)
from app.modules.now.application.compose_offers import ComposeOffers
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.screen import Place
from tests.unit.match_records import at
from tests.unit.shelf_doubles import a_context, a_match, rated

#: Two days out, so the fit floor is in force unless a case moves the clock.
FAR = 2880
NOW: Instant = at(0)
BAND = Band(low=level(250), high=level(350))


def a_player(hundredths: int = 300) -> tuple[UUID, PlayerSkill]:
    who = uuid4()
    return who, PlayerSkill(
        player=PlayerRef(str(who)),
        level=level(hundredths),
        uncertainty=uncertainty(60),
        confidence=50,
    )


class Fixture:
    """One dispatch, wired from doubles, with everything it wrote visible."""

    def __init__(self, **overrides: object) -> None:
        self.context = overrides.pop(
            "context", a_context(record=a_match(paid=1, starts=FAR))
        )
        self.waves = FakeCascadeWaves()
        self.offers = overrides.pop("offers", FakeOffers())
        self.contexts = FakeContexts(self.context)
        self.players = overrides.pop("players", FakeRatedPlayers())
        self.regulars = overrides.pop("regulars", FakeClubRegulars())
        self.standby = overrides.pop("standby", FakeStandbyQueue())
        self.diaries = overrides.pop("diaries", FakeDiaries())
        self.ratings = overrides.pop("ratings", FakeRatings())
        self.scorer = overrides.pop("scorer", FakeScorer(band=BAND))
        self.uow = SpyUnitOfWork()
        self.now = overrides.pop("now", NOW)
        assert not overrides, overrides
        self.vacancy = uuid4()

    def rung_one(self, *who: UUID) -> "Fixture":
        self.standby = FakeStandbyQueue(*who)
        return self

    def in_the_band(self, *who: UUID) -> "Fixture":
        self.players = FakeRatedPlayers(*who)
        return self

    def regular_at_the_club(self, *who: UUID) -> "Fixture":
        self.regulars = FakeClubRegulars(*who)
        return self

    def rate(self, who: UUID, skill: PlayerSkill | None) -> "Fixture":
        self.ratings.give(who, skill)
        return self

    def build(self) -> RunCascade:
        return RunCascade(
            waves=self.waves,
            offers=self.offers,
            contexts=self.contexts,
            players=self.players,
            regulars=self.regulars,
            commitments=self.diaries,
            ratings=self.ratings,
            standby=self.standby,
            scorer=self.scorer,
            uow=self.uow,
            clock=FixedClock(self.now),
        )

    def wave(self, which: Wave = Wave.SECOND) -> PendingWave:
        return PendingWave(
            match_id=self.context.match_id,
            vacancy_id=self.vacancy,
            wave=which,
            due_at=self.now,
        )

    async def run(self, which: Wave = Wave.SECOND) -> CascadeOutcome:
        return await self.build().execute(self.wave(which))

    @property
    def told(self) -> list[UUID]:
        return [offer.player_id for offer in self.offers.written]


# ---------------------------------------------------------------------------
# Which store answers which rung
# ---------------------------------------------------------------------------


async def test_the_first_dispatch_reads_the_queue_and_nothing_else() -> None:
    """Rung 1 alone, and the three stores below it are not even asked.

    Asserted on the **asking**, because a wave that read every store and then
    filtered by rung would produce the same offers and cost forty rating
    replays.
    """

    who, skill = a_player()
    fixture = Fixture().rung_one(who).in_the_band(uuid4()).regular_at_the_club(uuid4())
    fixture.rate(who, skill)

    assert await fixture.run(Wave.FIRST) is CascadeOutcome.DISPATCHED

    assert fixture.told == [who]
    assert fixture.standby.asked == [fixture.context.match_id]
    assert fixture.players.asked == []
    assert fixture.regulars.asked == []
    assert fixture.offers.asked_on_match == []


async def test_the_second_dispatch_reads_the_three_stores_that_have_one() -> None:
    """Rungs 3, 5 and 6 have sources; 2, 4 and 7 are dark and read nothing.

    There is no store to assert *not* asked for the dark rungs, which is the
    point: `_members` answers them the empty set without reaching for anything,
    so the evidence is that the queue — rung 1's store, in the other wave — is
    also untouched here.
    """

    fixture = Fixture()

    assert await fixture.run(Wave.SECOND) is CascadeOutcome.NOBODY

    assert fixture.offers.asked_on_match == [fixture.context.match_id]
    assert fixture.regulars.asked == [(fixture.context.club.club_id, NOW)]
    assert fixture.players.asked == [Sport.PADEL]
    assert fixture.standby.asked == []


async def test_somebody_on_two_rungs_stands_on_the_higher_one() -> None:
    """The ladder is an ordering over **people**; standing twice is told twice."""

    who, skill = a_player()
    fixture = Fixture().regular_at_the_club(who).in_the_band(who)
    fixture.rate(who, skill)

    assert await fixture.run() is CascadeOutcome.DISPATCHED

    assert [offer.player_rung for offer in fixture.offers.written] == [
        Rung.CLUB_REGULAR
    ]


async def test_a_dark_rung_contributes_nobody_even_when_a_store_could() -> None:
    """The negative control for the three that ship dark.

    Every store this dispatch reads is loaded with the same person, and she
    arrives on rung 3, 5 or 6 — never on 2, 4 or 7, which have no source to be
    loaded from at all.
    """

    who, skill = a_player()
    fixture = Fixture(offers=FakeOffers(on_match=frozenset({who})))
    fixture.rate(who, skill)

    await fixture.run()

    assert [offer.player_rung for offer in fixture.offers.written] == [
        Rung.ASKED_BEFORE
    ]


# ---------------------------------------------------------------------------
# What is written
# ---------------------------------------------------------------------------


async def test_an_offer_carries_the_rung_the_fit_the_price_and_the_kind() -> None:
    who, skill = a_player()
    fixture = Fixture(scorer=FakeScorer(band=BAND, fits={who: 84}))
    fixture.in_the_band(who).rate(who, skill)

    await fixture.run()

    offer = fixture.offers.written[0]
    assert offer.match_id == fixture.context.match_id
    assert offer.vacancy_id == fixture.vacancy
    assert offer.player_id == who
    assert offer.player_rung is Rung.IN_THE_BAND
    assert offer.fit == 84
    assert offer.kind is OfferKind.OPEN
    assert offer.offered_at == NOW


async def test_the_price_is_the_kernels_and_full_before_the_rescue_deadline() -> None:
    who, skill = a_player()
    fixture = Fixture()
    fixture.in_the_band(who).rate(who, skill)

    await fixture.run()

    assert fixture.offers.written[0].price == seat_price(
        fixture.context.record, grosze(int(fixture.context.share.amount)), NOW
    )
    assert int(fixture.offers.written[0].price) == int(fixture.context.share.amount)


async def test_the_price_halves_from_the_rescue_deadline() -> None:
    """The other half of ADR-0061's *"50 % from the rescue deadline"*.

    The match is committed and the clock is past its rescue window, which is the
    only state in which a filler pays the discount.
    """

    record = a_match(paid=1, starts=FAR, committed_at=at(-4320))
    when = deadlines(record)
    context = a_context(record=record)
    who, skill = a_player()
    fixture = Fixture(context=context, now=when.rescue)
    fixture.contexts = FakeContexts(context)
    fixture.in_the_band(who).rate(who, skill)

    await fixture.run()

    from app.kernel import RESCUE_FRACTION

    assert int(fixture.offers.written[0].price) == int(
        apply_fraction(grosze(int(context.share.amount)), RESCUE_FRACTION)
    )


async def test_everybody_in_one_dispatch_is_quoted_the_same_price() -> None:
    """One read of the clock per dispatch, and not one per row.

    Two people told in the same wave were told the same thing; reading the
    kernel per offer would let a wave straddling the rescue deadline quote two
    of them differently for no reason a player could see.
    """

    people = [a_player() for _ in range(4)]
    fixture = Fixture().in_the_band(*(who for who, _ in people))
    for who, skill in people:
        fixture.rate(who, skill)

    await fixture.run()

    assert len({offer.price for offer in fixture.offers.written}) == 1


async def test_the_offers_are_written_in_ladder_order() -> None:
    """The order the store is handed, which is what a later reader inherits."""

    queued, queued_skill = a_player()
    regular, regular_skill = a_player()
    stranger, stranger_skill = a_player()
    fixture = Fixture(
        scorer=FakeScorer(
            band=BAND, fits={queued: 71, regular: 80, stranger: 99}
        )
    )
    fixture.regular_at_the_club(regular).in_the_band(stranger, queued)
    for who, skill in (
        (queued, queued_skill),
        (regular, regular_skill),
        (stranger, stranger_skill),
    ):
        fixture.rate(who, skill)

    await fixture.run()

    assert fixture.told == [regular, stranger, queued]


async def test_a_dispatch_commits() -> None:
    """The offers and the queue row close together or they do not close at all."""

    who, skill = a_player()
    fixture = Fixture()
    fixture.in_the_band(who).rate(who, skill)

    await fixture.run()

    assert fixture.uow.commits == 1
    assert fixture.waves.done == [(fixture.vacancy, Wave.SECOND, NOW)]


# ---------------------------------------------------------------------------
# Who is left out, and what that costs
# ---------------------------------------------------------------------------


async def test_an_unrated_candidate_is_dropped_and_never_scored() -> None:
    """`RATED_AT_SPORT` fires before anything expensive.

    Asserted on the scorer's own log, because dropping her *after* scoring
    produces the identical offers and pays the whole cost.
    """

    who = uuid4()
    fixture = Fixture()
    fixture.in_the_band(who).rate(who, None)

    assert await fixture.run() is CascadeOutcome.NOBODY

    assert fixture.told == []
    assert fixture.scorer.scored == []


async def test_somebody_the_match_is_already_hers_is_dropped_on_its_identity() -> None:
    """A seat, or a departure — `Commitments` answers both as *hers*.

    The **leaver** is the case worth having: she is on no seat and her evening
    is otherwise free, so nothing else in the pool would stop the cascade
    offering her back the seat she left minutes ago.

    Her diary row deliberately names this match at hours that **do not clash**
    with it, which no real adapter would produce — and that is the point. In
    life the two rules fire together, because `Commitments` answers this match
    with this match's own window; a case that let them is a case that passes
    when the identity rule is deleted, which is exactly what a mutation found
    here. Naming the hours apart is what isolates *she is already in this one*
    from *she is busy then*.
    """

    leaver, skill = a_player()
    fixture = Fixture()
    fixture.in_the_band(leaver).rate(leaver, skill)
    elsewhere = shifted(fixture.context.record.start, minutes(600))
    fixture.diaries.give(
        leaver, (fixture.context.match_id, elsewhere, shifted(elsewhere, minutes(90)))
    )

    assert await fixture.run() is CascadeOutcome.NOBODY
    assert fixture.told == []


async def test_somebody_playing_elsewhere_that_evening_is_dropped() -> None:
    """The other half of the pair, isolated the same way.

    A **different** match, overlapping these hours. Nothing about identity can
    reach her, so this is the clash rule and only the clash rule — and the two
    cases together are what make deleting either one visible.
    """

    busy, skill = a_player()
    fixture = Fixture()
    fixture.in_the_band(busy).rate(busy, skill)
    fixture.diaries.give(
        busy,
        (
            uuid4(),
            shifted(fixture.context.record.start, minutes(-30)),
            shifted(fixture.context.record.start, minutes(30)),
        ),
    )

    assert await fixture.run() is CascadeOutcome.NOBODY
    assert fixture.told == []


async def test_somebody_playing_that_afternoon_is_not_dropped() -> None:
    """The negative control for the clash: a free evening is a free evening."""

    free, skill = a_player()
    fixture = Fixture()
    fixture.in_the_band(free).rate(free, skill)
    earlier = shifted(fixture.context.record.start, minutes(-300))
    fixture.diaries.give(free, (uuid4(), earlier, shifted(earlier, minutes(90))))

    assert await fixture.run() is CascadeOutcome.DISPATCHED
    assert fixture.told == [free]


async def test_a_candidate_outside_the_band_is_dropped() -> None:
    inside, inside_skill = a_player(300)
    outside, outside_skill = a_player(480)
    fixture = Fixture()
    fixture.in_the_band(inside, outside)
    fixture.rate(inside, inside_skill).rate(outside, outside_skill)

    await fixture.run()

    assert fixture.told == [inside]


async def test_the_floor_drops_a_candidate_above_a_day_and_keeps_her_below() -> None:
    """One person, two clocks, and only the distance to the match differs."""

    who, skill = a_player()
    below = CASCADE_FLOOR - 1

    far = Fixture(scorer=FakeScorer(band=BAND, fits={who: below}))
    far.in_the_band(who).rate(who, skill)
    assert await far.run() is CascadeOutcome.NOBODY

    record = a_match(paid=1, starts=FAR)
    inside_a_day = shifted(record.start, minutes(-60))
    near = Fixture(
        context=a_context(record=record),
        now=inside_a_day,
        scorer=FakeScorer(band=BAND, fits={who: below}),
    )
    near.contexts = FakeContexts(near.context)
    near.in_the_band(who).rate(who, skill)

    assert await near.run() is CascadeOutcome.DISPATCHED
    assert near.told == [who]


async def test_nobody_already_told_about_this_hole_is_told_again() -> None:
    """ADR-0061's *"a lapse resumes them and nobody is told twice"*.

    Checked **before** the expensive half, so a resumed wave does not pay a
    rating replay and a score for everybody it is about to skip.
    """

    told, told_skill = a_player()
    fresh, fresh_skill = a_player()
    fixture = Fixture(offers=FakeOffers(for_vacancy=frozenset({told})))
    fixture.in_the_band(told, fresh)
    fixture.rate(told, told_skill).rate(fresh, fresh_skill)

    await fixture.run()

    assert fixture.told == [fresh]
    assert fixture.scorer.scored == [fresh]


async def test_one_candidate_who_cannot_be_scored_does_not_drop_the_rest() -> None:
    """The opposite of the shelves' rule, and the opposite for a reason.

    A shelf ordered from a half-run scoring pass is a shelf whose order means
    nothing. Here the order is over *people*, and one player whose stream will
    not replay is one person not told.
    """

    broken, broken_skill = a_player()
    fine, fine_skill = a_player()
    fixture = Fixture(scorer=FakeScorer(band=BAND, unscorable=frozenset({broken})))
    fixture.in_the_band(broken, fine)
    fixture.rate(broken, broken_skill).rate(fine, fine_skill)

    await fixture.run()

    assert fixture.told == [fine]


async def test_a_match_with_no_band_tells_everybody_the_pool_allows() -> None:
    """No band is **no wall**, never a wall nobody clears.

    A dispatch whose analysis will not run has no band either, and it degrades
    the same way — refusing everybody on a missing fact is the dead seat this
    module exists to prevent.
    """

    far_off, skill = a_player(480)
    fixture = Fixture(scorer=FakeScorer(band=None, band_raises=True))
    fixture.in_the_band(far_off).rate(far_off, skill)

    assert await fixture.run() is CascadeOutcome.DISPATCHED
    assert fixture.told == [far_off]


# ---------------------------------------------------------------------------
# The claim, the empty rung, and the match that went away
# ---------------------------------------------------------------------------


async def test_a_live_seat_claim_suppresses_a_dispatch_and_leaves_it_due() -> None:
    """*"A live seat claim silences pending waves; a lapse resumes them."*

    The row is **not** marked dispatched, which is the whole of *resumes*: the
    first tick after the claim ends is the one that runs it. Nothing is written
    and nothing is committed.
    """

    from app.kernel import SeatClaim

    who, skill = a_player()
    record = a_match(
        paid=1,
        starts=FAR,
        claims=(SeatClaim(seat_index=2, expires_at=shifted(NOW, minutes(3))),),
    )
    fixture = Fixture(context=a_context(record=record))
    fixture.contexts = FakeContexts(fixture.context)
    fixture.in_the_band(who).rate(who, skill)

    assert await fixture.run() is CascadeOutcome.SUPPRESSED

    assert fixture.told == []
    assert fixture.waves.done == []
    assert fixture.uow.commits == 0


async def test_a_lapsed_claim_no_longer_suppresses() -> None:
    """Liveness is composed, not latched, so no reaper has to have been round."""

    from app.kernel import SeatClaim

    who, skill = a_player()
    record = a_match(
        paid=1,
        starts=FAR,
        claims=(SeatClaim(seat_index=2, expires_at=shifted(NOW, minutes(-1))),),
    )
    fixture = Fixture(context=a_context(record=record))
    fixture.contexts = FakeContexts(fixture.context)
    fixture.in_the_band(who).rate(who, skill)

    assert await fixture.run() is CascadeOutcome.DISPATCHED
    assert fixture.told == [who]


async def test_an_empty_first_dispatch_brings_the_second_forward() -> None:
    """*"An empty rung is skipped instantly."*

    The head start is what joining a queue buys; an **empty** queue has bought
    nothing, and making strangers wait ten minutes for it is ten minutes of a
    seat's life spent on nobody.
    """

    fixture = Fixture()

    assert await fixture.run(Wave.FIRST) is CascadeOutcome.NOBODY

    assert fixture.waves.brought_forward == [(fixture.vacancy, Wave.SECOND, NOW)]
    assert fixture.waves.done == [(fixture.vacancy, Wave.FIRST, NOW)]


async def test_a_first_dispatch_that_reached_somebody_leaves_the_second_alone() -> None:
    """The negative control: the head start is paid for exactly when it is earned."""

    who, skill = a_player()
    fixture = Fixture().rung_one(who)
    fixture.rate(who, skill)

    assert await fixture.run(Wave.FIRST) is CascadeOutcome.DISPATCHED
    assert fixture.waves.brought_forward == []


async def test_an_empty_second_dispatch_brings_nothing_forward() -> None:
    """There is nothing behind the second wave to move."""

    fixture = Fixture()

    assert await fixture.run(Wave.SECOND) is CascadeOutcome.NOBODY
    assert fixture.waves.brought_forward == []


async def test_a_match_that_cannot_be_read_retires_its_row() -> None:
    """Otherwise the queue grows a dispatch that can never run.

    Left due, the tick picks it up every second for ever — which is the same
    defect a wake that finds nothing and does not re-arm has.
    """

    fixture = Fixture()
    gone = PendingWave(
        match_id=uuid4(), vacancy_id=fixture.vacancy, wave=Wave.SECOND, due_at=NOW
    )

    assert await fixture.build().execute(gone) is CascadeOutcome.GONE

    assert fixture.waves.done == [(fixture.vacancy, Wave.SECOND, NOW)]
    assert fixture.uow.commits == 1


# ---------------------------------------------------------------------------
# Opening the two dispatches
# ---------------------------------------------------------------------------


async def test_opening_a_cascade_writes_exactly_two_rows() -> None:
    context = a_context(record=a_match(paid=1, starts=FAR))
    waves = FakeCascadeWaves()
    vacancy = uuid4()

    await OpenCascade(waves=waves, contexts=FakeContexts(context)).execute(
        match_id=context.match_id, vacancy_id=vacancy, vacated_at=NOW
    )

    assert [one.wave for one in waves.opened] == [Wave.FIRST, Wave.SECOND]
    assert {one.vacancy_id for one in waves.opened} == {vacancy}
    assert {one.match_id for one in waves.opened} == {context.match_id}


async def test_the_two_rows_carry_the_head_start_and_the_quiet_hours() -> None:
    """The due moments are `wave_due` with `delivery_at` applied, not either alone.

    Composed from the two functions rather than from literals, so a change to
    either one is a change this case follows rather than a change it fights.
    """

    context = a_context(record=a_match(paid=1, starts=FAR))
    waves = FakeCascadeWaves()

    await OpenCascade(waves=waves, contexts=FakeContexts(context)).execute(
        match_id=context.match_id, vacancy_id=uuid4(), vacated_at=NOW
    )

    assert [one.due_at for one in waves.opened] == [
        delivery_at(wave_due(NOW, wave), context.record, zone=context.club.zone)
        for wave in (Wave.FIRST, Wave.SECOND)
    ]


async def test_a_match_with_no_context_opens_no_cascade_and_does_not_raise() -> None:
    """A departure must not fail because the club table is short a row.

    Her money is the thing being applied; the cascade is what happens next, and
    the safe direction is a seat nobody hears about rather than a leave that
    will not go through.
    """

    waves = FakeCascadeWaves()

    await OpenCascade(waves=waves, contexts=FakeContexts()).execute(
        match_id=uuid4(), vacancy_id=uuid4(), vacated_at=NOW
    )

    assert waves.opened == []


async def test_the_pool_valve_bites_and_it_bites_at_the_tail_of_the_ladder() -> None:
    """`POOL_LIMIT` bounds the work, and never at the expense of a higher rung.

    Rung 6 is *everyone else in the band*, so without a valve a sport's whole
    population is replayed and scored on one background job. It is applied
    **before** anything expensive, in ladder order, so what a truncation loses
    is the tail ADR-0061 already calls *"everyone in the band anywhere"*.

    Asserted on the rating replays, because a valve applied after scoring
    produces a shelf of the same length and pays the whole cost.
    """

    regulars = [a_player() for _ in range(POOL_LIMIT)]
    crowd = [a_player() for _ in range(20)]
    fixture = Fixture()
    fixture.regular_at_the_club(*(who for who, _ in regulars))
    fixture.in_the_band(*(who for who, _ in crowd))
    for who, skill in regulars + crowd:
        fixture.rate(who, skill)

    await fixture.run()

    # Exactly the higher rung, and **none** of the lower one — asserted as an
    # equality rather than as a membership, so a valve that truncated in id
    # order (which keeps most of rung 5 by luck) disagrees rather than passing
    # most of the time.
    assert {who for who, _ in fixture.ratings.asked} == {who for who, _ in regulars}
    assert len(fixture.offers.written) == POOL_LIMIT
    assert {offer.player_rung for offer in fixture.offers.written} == {
        Rung.CLUB_REGULAR
    }


# ---------------------------------------------------------------------------
# The batch
# ---------------------------------------------------------------------------


async def test_the_batch_runs_every_dispatch_that_is_due() -> None:
    fixture = Fixture()
    due = [
        PendingWave(
            match_id=fixture.context.match_id,
            vacancy_id=uuid4(),
            wave=wave,
            due_at=NOW,
        )
        for wave in (Wave.FIRST, Wave.SECOND)
    ]
    fixture.waves.pending.extend(due)

    taken = await CascadeBatch(
        waves=fixture.waves,
        run=fixture.build(),
        uow=fixture.uow,
        clock=FixedClock(NOW),
    ).execute(worker_id="worker-1")

    assert taken == 2


async def test_a_dispatch_that_is_not_due_yet_is_not_taken() -> None:
    fixture = Fixture()
    fixture.waves.pending.append(
        PendingWave(
            match_id=fixture.context.match_id,
            vacancy_id=uuid4(),
            wave=Wave.SECOND,
            due_at=shifted(NOW, minutes(1)),
        )
    )

    taken = await CascadeBatch(
        waves=fixture.waves,
        run=fixture.build(),
        uow=fixture.uow,
        clock=FixedClock(NOW),
    ).execute(worker_id="worker-1")

    assert taken == 0


async def test_one_failing_dispatch_does_not_stop_the_tick() -> None:
    """Two holes at two clubs have nothing to do with each other.

    The rollback is what makes *the rest are run* true rather than hopeful: a
    session left holding a failed statement fails every dispatch after it.
    """

    fixture = Fixture()
    first = PendingWave(
        match_id=fixture.context.match_id,
        vacancy_id=uuid4(),
        wave=Wave.SECOND,
        due_at=NOW,
    )
    second = PendingWave(
        match_id=fixture.context.match_id,
        vacancy_id=uuid4(),
        wave=Wave.FIRST,
        due_at=NOW,
    )
    fixture.waves.pending.extend([first, second])

    exploding = fixture.build()
    seen: list[UUID] = []

    async def blow_up_on_the_first(wave: PendingWave) -> CascadeOutcome:
        seen.append(wave.vacancy_id)
        if wave.vacancy_id == first.vacancy_id:
            raise RuntimeError("one bad hole")
        return CascadeOutcome.NOBODY

    exploding.execute = blow_up_on_the_first  # type: ignore[method-assign]

    taken = await CascadeBatch(
        waves=fixture.waves, run=exploding, uow=fixture.uow, clock=FixedClock(NOW)
    ).execute(worker_id="worker-1")

    assert seen == [first.vacancy_id, second.vacancy_id]
    assert taken == 1
    assert fixture.uow.rollbacks == 1


# ---------------------------------------------------------------------------
# The wall is the engine's, and no observer moves it
# ---------------------------------------------------------------------------


def test_the_band_is_the_seated_mean_and_the_engines_are_what_compute_it() -> None:
    """ADR-0061's wall, against the **real** pairing engine.

    *"Everyone inside the band the players who stayed signed up for"* has no
    field behind it and needs none: the band is `TargetBand`, which the engine
    already computes as the mean of the seated Levels. Asserted by moving the
    roster and watching the band move with it — which is what makes it *the
    stayers'* band rather than a constant.
    """

    scorer = build_match_scorer()
    low = a_context(
        record=a_match(paid=2, starts=FAR),
        occupants=(rated(200), rated(200), None, None),
    )
    high = a_context(
        record=a_match(paid=2, starts=FAR),
        occupants=(rated(400), rated(400), None, None),
    )

    low_band = _band_from(scorer.analyse(low, now=NOW))
    high_band = _band_from(scorer.analyse(high, now=NOW))

    assert low_band is not None and high_band is not None
    assert low_band.low < low_band.high
    assert low_band.high < high_band.low


def test_the_stand_in_observer_cannot_move_the_band() -> None:
    """The property that makes `analyse`'s observer safe, not the reasoning.

    `_target_band` reads `snapshot.occupants` — everybody on a seat — and never
    `current_player`, so the band a dispatch computes with a stand-in is the
    band a real candidate's own analysis would have produced. The day that stops
    being true, this goes red, which is the day the stand-in stops being safe.
    """

    scorer = build_match_scorer()
    context = a_context(
        record=a_match(paid=2, starts=FAR),
        occupants=(rated(280), rated(320), None, None),
    )

    through_the_stand_in = _band_from(scorer.analyse(context, now=NOW))
    for hundredths in (120, 300, 495):
        _, viewer = a_player(hundredths)
        _, analysis = scorer.score(context, viewer=viewer, now=NOW)
        assert _band_from(analysis) == through_the_stand_in


def test_a_match_nobody_is_seated_at_has_no_band_at_all() -> None:
    """*"The mean of no Levels is not a wide band — it is no band."*"""

    scorer = build_match_scorer()
    empty = a_context(
        record=a_match(paid=0, starts=FAR), occupants=(None, None, None, None)
    )

    assert _band_from(scorer.analyse(empty, now=NOW)) is None


@pytest.mark.parametrize("hundredths", [250, 300, 350])
def test_the_wall_admits_the_levels_the_engines_band_contains(hundredths) -> None:
    """The two halves joined: the engine's band, the ladder's `admits`.

    Neither function is interesting alone — this is the seam, and it is where a
    unit swap between hundredths and a ratio would show up.
    """

    scorer = build_match_scorer()
    context = a_context(
        record=a_match(paid=2, starts=FAR),
        occupants=(rated(300), rated(300), None, None),
    )
    band = _band_from(scorer.analyse(context, now=NOW))

    assert band is not None
    her = level(hundredths)
    assert band.admits(her) == (band.low <= her <= band.high)


# ---------------------------------------------------------------------------
# What the offers region can therefore draw
# ---------------------------------------------------------------------------


class _OfferedFromWhatWasWritten:
    """`OfferedSeats` over exactly what a dispatch wrote, for one match.

    The join between the cascade and the region, and the only thing this file
    stands up beyond the ladder. Everything about the read itself —
    deduplication, batching, *already mine* — is
    `tests/unit/test_offered_adapter.py`'s; what this needs is a port that
    invents nothing, so that a card appearing is a claim about the **dispatch**
    rather than about a fixture.
    """

    def __init__(self, offers: FakeOffers, context) -> None:
        self._offers = offers
        self._context = context

    async def for_player(self, *, player_id, now):
        return tuple(
            OfferedSeat(
                match_id=offer.match_id,
                vacancy_id=offer.vacancy_id,
                record=self._context.record,
                where=Place(
                    club_id=self._context.club.club_id,
                    club_name=self._context.club.name,
                    zone=self._context.club.zone,
                    cover=self._context.club.cover,
                ),
                kind=offer.kind,
                share=self._context.share,
                court_total=self._context.court_total,
                offered_at=offer.offered_at,
            )
            for offer in self._offers.written
            if offer.player_id == player_id
        )

    async def one(self, *, player_id, match_id, now):  # pragma: no cover
        raise AssertionError("this file composes a region, never one card")


async def _region_for(fixture: Fixture, player_id: UUID):
    return await ComposeOffers(
        offered=_OfferedFromWhatWasWritten(fixture.offers, fixture.context)
    ).compose(viewer=player_id, sport=None, now=fixture.now, stamp=1)


async def test_a_player_the_pool_admitted_gets_a_card() -> None:
    """The negative controls below are worth nothing without this one.

    A region that drew nothing for everybody would satisfy both of them, so the
    positive case is what makes them assertions rather than tautologies.
    """

    who, skill = a_player(300)
    fixture = Fixture()
    fixture.in_the_band(who).rate(who, skill)
    await fixture.run()

    region = await _region_for(fixture, who)

    assert [card.match_id for card in region.cards] == [fixture.context.match_id]


async def test_no_card_reaches_a_sport_the_viewer_holds_no_rating_at() -> None:
    """`RATED_AT_SPORT` is the pool's, and the region inherits it by having
    nothing to draw.

    The region asks ``cascade.seat_exclusions`` — the four facts about the *seat*
    — and never the three about the candidate, deliberately: re-deciding *is she
    still the right person for this* on a card she is already looking at would
    withdraw a seat by a rule she cannot see, which is what ADR-0061 replaced
    retraction with wording to avoid. So this rule has to hold where the offer is
    **written**, and this is the assertion that it does.
    """

    who = uuid4()
    fixture = Fixture()
    fixture.in_the_band(who).rate(who, None)
    await fixture.run()

    region = await _region_for(fixture, who)

    assert region.cards == ()


async def test_no_card_reaches_a_player_outside_the_matchs_band() -> None:
    """The wall, read from the screen's end. ADR-0061: *"everyone inside the band
    the players who stayed signed up for."*"""

    inside, inside_skill = a_player(300)
    outside, outside_skill = a_player(480)
    fixture = Fixture()
    fixture.in_the_band(inside, outside)
    fixture.rate(inside, inside_skill).rate(outside, outside_skill)
    await fixture.run()

    assert (await _region_for(fixture, inside)).cards != ()
    assert (await _region_for(fixture, outside)).cards == ()
