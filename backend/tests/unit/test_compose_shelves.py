"""The ranked funnel's reach: what it asks, in what order, and what it degrades to.

``test_shelf_funnel.py`` owns the rules, which are pure functions over values.
This owns the *composition* — the window retrieval is asked for, the cache key,
which shelves appear at all, the badge, and what happens when the scorer cannot
answer. Everything here runs the **real** engines behind the real
``MatchScorer``: an engine mocked out of a scoring test is a test of the mock.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.engines.matchfit.v1 import MatchFitEngineV1
from app.engines.pairing.v1 import PairingEngineV1
from app.kernel import Instant, Sport, elapsed_minutes

from app.modules.now.application.compose_shelves import ComposeShelves
from app.modules.now.application.scoring import MatchScorer
from app.modules.now.domain.funnel import (
    BEST_FIT_CAP,
    CANDIDATE_HORIZON_DAYS,
    FULL_CAP,
    MatchScoringContext,
)
from app.modules.now.domain.screen import MatchCard, Shelf
from app.modules.now.domain.vocabulary import ShelfCode
from tests.unit.match_records import at
from tests.unit.shelf_doubles import (
    STAMP,
    FakeCityMatches,
    FakeCommitments,
    FakeRatings,
    FakeStandbyPlaces,
    a_club,
    a_context,
    a_match,
    a_viewer_rated_at,
    rated,
)

PADEL = frozenset({Sport.PADEL})
NOW = at(-2880)


class BrokenFitEngine(MatchFitEngineV1):
    """The Match Fit engine, out. What §5.5's kill switch actually models.

    The **engine** is what fails, not the scorer around it, so a degraded case
    goes through the real ``MatchScorer.score`` and proves the whole path: an
    arbitrary engine exception becomes ``Unscorable``, and ``Unscorable``
    becomes a degraded shelf. A fake that raised ``Unscorable`` itself would
    skip the half that turns one into the other, which is the half a narrower
    ``except`` clause would break.
    """

    def score(self, **kwargs):  # type: ignore[no-untyped-def, override]
        raise RuntimeError("the scorer is out")


def ExplodingScorer() -> MatchScorer:
    return MatchScorer(pairing=PairingEngineV1(), matchfit=BrokenFitEngine())


def _shelves(
    *contexts: MatchScoringContext,
    ratings: FakeRatings | None = None,
    commitments: FakeCommitments | None = None,
    standby: FakeStandbyPlaces | None = None,
    city: FakeCityMatches | None = None,
    scorer: MatchScorer | None = None,
) -> ComposeShelves:
    return ComposeShelves(
        city=city or FakeCityMatches(*contexts),
        commitments=commitments or FakeCommitments(),
        standby=standby or FakeStandbyPlaces(),
        ratings=ratings or a_viewer_rated_at(),
        scorer=scorer
        or MatchScorer(pairing=PairingEngineV1(), matchfit=MatchFitEngineV1()),
    )


async def compose(
    *contexts: MatchScoringContext,
    viewer: UUID | None = None,
    sports: frozenset[Sport] = PADEL,
    now: Instant = NOW,
    **kwargs,
) -> tuple[Shelf, ...]:
    return await _shelves(*contexts, **kwargs).compose(
        viewer=viewer or uuid4(), sports=sports, now=now, stamp=STAMP
    )


def _by_code(shelves: tuple[Shelf, ...]) -> dict[ShelfCode, Shelf]:
    return {shelf.code: shelf for shelf in shelves}


# --- 1 · which shelves appear ----------------------------------------------


async def test_an_open_match_and_a_full_one_compose_two_shelves() -> None:
    shelves = await compose(
        a_context(record=a_match(paid=1)),
        a_context(record=a_match(paid=4)),
    )

    codes = {shelf.code for shelf in shelves}
    assert ShelfCode.FULL_WORTH_WAITING in codes
    assert codes & {ShelfCode.BEST_FIT, ShelfCode.SAME_LEVEL}


async def test_the_ranked_pair_is_emitted_in_the_servers_order() -> None:
    """Shelf 1 before shelf 2, always, whatever either one scored."""

    shelves = await compose(
        a_context(record=a_match(paid=4)),
        a_context(record=a_match(paid=1)),
    )

    assert [shelf.code for shelf in shelves][-1] is ShelfCode.FULL_WORTH_WAITING


async def test_shelf_one_is_never_absent_for_a_viewer_with_an_eligible_match() -> None:
    """The retitle is what buys this: it drops the floor rather than the shelf.

    A shelf that could go silent would leave a player with matches in her city
    looking at a screen that says nothing is happening.
    """

    shelves = await compose(a_context(record=a_match(paid=1)))

    codes = {shelf.code for shelf in shelves}
    assert codes & {ShelfCode.BEST_FIT, ShelfCode.SAME_LEVEL}


async def test_the_waitlist_shelf_is_absent_when_nothing_clears_eighty() -> None:
    """No retitle, no fallback: *wait for this* is a claim that cannot be softened.

    The match below is full and playable and aimed far above the viewer, so it
    scores under 80 — and the shelf goes rather than appearing with the one card
    it could find. Asking somebody to wait is ADR-0051's bigger ask.
    """

    others = (rated(490), rated(480), rated(470), rated(495))
    shelves = await compose(
        a_context(record=a_match(paid=4), occupants=others),
        ratings=FakeRatings(PADEL=rated(100)),
    )

    assert ShelfCode.FULL_WORTH_WAITING not in {shelf.code for shelf in shelves}


async def test_the_ranked_shelf_retitles_rather_than_going_silent() -> None:
    """The same viewer, the same mismatch, on the shelf that may not disappear.

    Nothing clears 70, so shelf 1 keeps its cards, drops its floor and changes
    its claim. That is what buys the floor: an unfillable shelf is *absent*
    rather than empty, so no card claims the city is empty.
    """

    shelves = await compose(
        a_context(record=a_match(paid=1), occupants=(rated(490), None, None, None)),
        ratings=FakeRatings(PADEL=rated(100)),
    )

    assert [shelf.code for shelf in shelves] == [ShelfCode.SAME_LEVEL]
    assert shelves[0].cards


async def test_nothing_composes_when_the_city_is_empty() -> None:
    assert await compose() == ()


async def test_nothing_composes_for_a_viewer_the_platform_cannot_place() -> None:
    """A player with no rating is owed a **door**, not a ranked shelf.

    Composing one would print an order computed from a Level nobody holds, and
    ADR-0084 puts the door in these two shelves' position precisely because
    there is nothing for them to hold.
    """

    shelves = await compose(a_context(record=a_match(paid=1)), ratings=FakeRatings())

    assert shelves == ()


async def test_an_unrankable_viewer_costs_no_retrieval_at_all() -> None:
    city = FakeCityMatches(a_context(record=a_match(paid=1)))

    await compose(city=city, ratings=FakeRatings())

    assert city.asked == []


# --- 2 · eligibility reaches the composer ----------------------------------


async def test_a_match_she_is_already_in_reaches_no_shelf() -> None:
    hers = uuid4()
    shelves = await compose(
        a_context(match_id=hers, record=a_match(paid=1)),
        commitments=FakeCommitments((hers, at(0), at(90))),
    )

    assert shelves == ()


async def test_a_match_she_is_queued_for_reaches_no_shelf() -> None:
    queued = uuid4()
    shelves = await compose(
        a_context(match_id=queued, record=a_match(paid=1)),
        standby=FakeStandbyPlaces(queued),
    )

    assert shelves == ()


async def test_a_match_in_another_sport_reaches_no_shelf() -> None:
    shelves = await compose(a_context(record=a_match(sport=Sport.TENNIS, paid=1)))

    assert shelves == ()


async def test_the_standby_and_commitment_reads_happen_once_for_the_screen() -> None:
    """Both shelves run over one viewer, so both reads are asked once.

    Two lanes asking the same two questions twice would double the cost of the
    busiest read in the product for an answer that cannot differ between them.
    """

    commitments = FakeCommitments()
    standby = FakeStandbyPlaces()
    viewer = uuid4()

    await compose(
        a_context(record=a_match(paid=1)),
        a_context(record=a_match(paid=4)),
        viewer=viewer,
        commitments=commitments,
        standby=standby,
    )

    assert commitments.asked == [viewer]
    assert standby.asked == [viewer]


# --- 3 · retrieval -----------------------------------------------------------


async def test_retrieval_is_asked_for_the_horizon_and_nothing_wider() -> None:
    city = FakeCityMatches()

    await compose(city=city)

    (sports, window_from, window_to) = city.asked[0]
    assert sports == PADEL
    assert window_from == NOW
    assert elapsed_minutes(window_from, window_to) == CANDIDATE_HORIZON_DAYS * 24 * 60


async def test_the_floor_is_applied_before_the_cap_and_not_after_it() -> None:
    """A shelf keeps its **best** six, not the six retrieval happened to answer.

    Nine candidates, three of which are aimed at her and six wildly above. If the
    cap ran first, the shelf would keep whichever six came back and then drop the
    good ones for not being in that slice — a shelf of near-misses on a screen
    with three real suggestions in it.
    """

    hers = [
        a_context(
            record=a_match(paid=1, starts=n * 30),
            occupants=(rated(300), None, None, None),
        )
        for n in range(3)
    ]
    strangers = [
        a_context(
            record=a_match(paid=1, starts=200 + n * 30),
            occupants=(rated(490), None, None, None),
        )
        for n in range(6)
    ]

    shelves = _by_code(
        await compose(*strangers, *hers, ratings=FakeRatings(PADEL=rated(300)))
    )
    ranked = shelves.get(ShelfCode.BEST_FIT)

    assert ranked is not None, "nothing cleared 70, so the case is not testing it"
    assert {card.match_id for card in ranked.cards} >= {one.match_id for one in hers}


async def test_the_waitlist_shelf_has_no_variety_rule() -> None:
    """Shelf 2 has no diversity policy, and that is the delta's own table.

    Its cards are full matches, so *two from one club in one hour* is not a
    variety problem she can act on — every one of them is something to wait for
    rather than something to choose between.

    Four at one club and one at another, all in the same hour and ordered by
    start. With a variety rule the fifth would be promoted over the third and the
    shelf would hold two clubs; without one it holds the three soonest.
    """

    busy, elsewhere = a_club(), a_club()
    seated = tuple(rated(300) for _ in range(4))
    theirs = [
        a_context(record=a_match(paid=4, starts=n), club=busy, occupants=seated)
        for n in range(4)
    ]
    other = a_context(
        record=a_match(paid=4, starts=4), club=elsewhere, occupants=seated
    )

    shelves = _by_code(
        await compose(*theirs, other, ratings=FakeRatings(PADEL=rated(300)))
    )
    waiting = shelves.get(ShelfCode.FULL_WORTH_WAITING)

    assert waiting is not None
    assert len(waiting.cards) == FULL_CAP
    assert {card.where.club_id for card in waiting.cards} == {busy.club_id}


async def test_diversity_runs_after_the_order_and_before_the_cap() -> None:
    """The pass order, seen as the only thing it changes: who is on the shelf.

    Eight at one club and one at another, all in one hour. Diversity promotes the
    ninth over the third, so the capped shelf holds **two** clubs. Applying the
    cap first would diversify a slice that is already all one club, and the pass
    would have nothing left to do.
    """

    busy, elsewhere = a_club(), a_club()
    seated = (rated(300), None, None, None)
    theirs = [
        a_context(record=a_match(paid=1, starts=n), club=busy, occupants=seated)
        for n in range(8)
    ]
    other = a_context(
        record=a_match(paid=1, starts=8), club=elsewhere, occupants=seated
    )

    shelves = await compose(*theirs, other, ratings=FakeRatings(PADEL=rated(300)))
    ranked = next(
        shelf
        for shelf in shelves
        if shelf.code in {ShelfCode.BEST_FIT, ShelfCode.SAME_LEVEL}
    )

    assert len(ranked.cards) == BEST_FIT_CAP
    assert {card.where.club_id for card in ranked.cards} == {
        busy.club_id,
        elsewhere.club_id,
    }
    # And it is promoted rather than appended: the other club's card sits third,
    # where the busy club's third would otherwise have been.
    assert ranked.cards[2].match_id == other.match_id


# --- 4 · the badge ----------------------------------------------------------


async def _one_card(*contexts, **kwargs) -> MatchCard:
    shelves = await compose(*contexts, **kwargs)
    cards = [card for shelf in shelves for card in shelf.cards]
    assert len(cards) == 1
    card = cards[0]
    assert isinstance(card, MatchCard)
    return card


async def test_a_shelf_card_always_carries_a_number_in_the_pill_range() -> None:
    card = await _one_card(a_context(record=a_match(paid=1)))

    assert card.fit is not None
    assert 20 <= card.fit.score <= 99


async def test_a_card_carries_at_most_three_reasons_each_with_its_facts() -> None:
    """Reasons are the engine's own term objects, not copies of them.

    A card showing a reason computed from anything but the score beside it would
    be two readings of a match that only has one.
    """

    card = await _one_card(a_context(record=a_match(paid=1)))

    assert card.fit is not None
    assert 0 < len(card.fit.reasons) <= 3
    assert all(reason.fact is not None for reason in card.fit.reasons)


async def test_the_aim_crosses_only_when_exactly_one_seat_is_open() -> None:
    """The seat target is precise; a target band is her own band restated."""

    one_open = await _one_card(
        a_context(
            record=a_match(paid=3),
            occupants=(rated(300), rated(300), rated(300), None),
        )
    )
    two_open = await _one_card(
        a_context(
            record=a_match(paid=2),
            occupants=(rated(300), rated(300), None, None),
        )
    )

    assert one_open.fit is not None and one_open.fit.target is not None
    assert two_open.fit is not None and two_open.fit.target is None


async def test_a_shelf_card_names_no_act_and_offers_no_exit() -> None:
    """ADR-0083's rule: *and a v1 surface can receive it*.

    The seat claim a suggestion's *take a seat* would open is #89. A door that
    will not open is worse than the gap, and this goes red the day one lands.
    """

    card = await _one_card(a_context(record=a_match(paid=1)))

    assert card.act is None
    assert card.may_depart is False
    assert card.seat_claim is None


async def test_a_shelf_card_carries_no_emphasis() -> None:
    """At most one card on the **whole screen** is emphatic, so it is not here.

    Emphasis depends on the other cards, which makes it a property of the
    composed screen rather than of a shelf (ADR-0032, ADR-0037).
    """

    card = await _one_card(a_context(record=a_match(paid=1)))

    assert card.emphasis is False


async def test_a_shelf_card_counts_in_money_and_names_the_courts_total() -> None:
    card = await _one_card(a_context(record=a_match(paid=1, held=1)))

    counts = card.situation.facts.counts
    assert (counts.paid, counts.held) == (1, 1)
    assert counts.seats == 4
    assert counts.turned_up is None
    assert card.situation.facts.court_total.amount == 15200


# --- 5 · degrade ------------------------------------------------------------


async def test_a_failed_scorer_leaves_shelf_one_standing_with_no_badge() -> None:
    """*Soonest-first, no badge*, retitled — a screen players have seen before.

    Reusing the thin-week fallback means the degraded path is exercised by
    ordinary testing rather than only by an incident.
    """

    shelves = await compose(
        a_context(record=a_match(paid=1, starts=600)),
        a_context(record=a_match(paid=1, starts=120)),
        scorer=ExplodingScorer(),
    )

    assert [shelf.code for shelf in shelves] == [ShelfCode.SAME_LEVEL]
    assert all(card.fit is None for card in shelves[0].cards)


async def test_a_failed_scorer_drops_the_waitlist_shelf_entirely() -> None:
    """An 80 floor with no scorer is not a claim we can make."""

    shelves = await compose(a_context(record=a_match(paid=4)), scorer=ExplodingScorer())

    assert shelves == ()


async def test_the_degraded_shelf_is_ordered_soonest_first() -> None:
    late = a_context(record=a_match(paid=1, starts=600))
    early = a_context(record=a_match(paid=1, starts=120))

    shelves = await compose(late, early, scorer=ExplodingScorer())

    assert [card.match_id for card in shelves[0].cards] == [
        early.match_id,
        late.match_id,
    ]


async def test_the_degraded_shelf_still_respects_its_cap() -> None:
    shelves = await compose(
        *[a_context(record=a_match(paid=1, starts=n * 30)) for n in range(9)],
        scorer=ExplodingScorer(),
    )

    assert len(shelves[0].cards) == BEST_FIT_CAP


async def test_no_degrade_marker_crosses_anywhere() -> None:
    """A degrade flag would be a fact about our infrastructure on her home screen.

    What the client sees is a shelf with no badges, which is what an unrated
    viewer's shelf also looks like — and that is the whole of it.
    """

    degraded = await compose(
        a_context(record=a_match(paid=1)), scorer=ExplodingScorer()
    )

    assert degraded[0].caption is None
    assert not hasattr(degraded[0], "degraded")


# --- 6 · caps ---------------------------------------------------------------


async def test_each_shelf_is_capped_at_its_own_number() -> None:
    opens = [a_context(record=a_match(paid=1, starts=n * 30)) for n in range(9)]
    fulls = [a_context(record=a_match(paid=4, starts=n * 30)) for n in range(9)]

    shelves = _by_code(await compose(*opens, *fulls))

    ranked = shelves.get(ShelfCode.BEST_FIT) or shelves[ShelfCode.SAME_LEVEL]
    assert len(ranked.cards) <= BEST_FIT_CAP
    assert len(shelves[ShelfCode.FULL_WORTH_WAITING].cards) <= FULL_CAP
