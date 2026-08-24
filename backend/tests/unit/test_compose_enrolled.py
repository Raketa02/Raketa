"""The enrolled strip: eleven claims about a player's own matches.

The region she is **committed** to. Four of the claims are *one rule* rather than
a table of thirty-six judgements (ADR-0073) — the order, the counting, the clock
and the twenty-four-hour tail — and the rest are facts that ride beside the
situation exactly when they exist.

The composer is driven through its port with a hand-written stub, so everything
below is about the *rules* and nothing about a database. What the adapter reads
is `tests/unit/test_now_adapters.py`'s.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import (
    Cause,
    Cover,
    Instant,
    MatchKind,
    MatchRecord,
    Outcome,
    PayModel,
    Situation,
    Sport,
    Vacancy,
    grosze,
    hours,
    instant,
    minutes,
    shifted,
)
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.domain.enrolled import Enrolment, PlayedScore
from app.modules.now.domain.ports import EnrolledMatches
from app.modules.now.domain.screen import (
    DepartureNothingTaken,
    DepartureRecoverable,
    Money,
    Place,
)
from app.modules.now.domain.vocabulary import (
    ACT_OF,
    ActCode,
    CardHoldReason,
    DepartureForm,
    RefundDestination,
)

from tests.unit.match_records import DURATION, START, a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
STAMP = 1_771_000_000_000
SHARE = grosze(3800)
COURT = grosze(15200)


class StubEnrolled(EnrolledMatches):
    """The port, hand-written, answering whatever a case set up."""

    def __init__(self, *rows: Enrolment) -> None:
        self._rows = rows
        self.asked: list[tuple[UUID, Instant]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[Enrolment, ...]:
        self.asked.append((player_id, now))
        return self._rows


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Kraków",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def enrolled(record: MatchRecord | None = None, **kwargs) -> Enrolment:
    return Enrolment(
        **{
            "match_id": uuid4(),
            "record": record if record is not None else a_match(paid=1),
            "where": a_place(),
            "share": Money(amount=SHARE),
            "court_total": Money(amount=COURT),
            "holds_seat": True,
            **kwargs,
        }
    )


async def compose(*rows: Enrolment, now: Instant, sport: Sport | None = None):
    region = await ComposeEnrolled(enrolled=StubEnrolled(*rows)).compose(
        viewer=uuid4(), sport=sport, now=now, stamp=STAMP
    )
    return region


async def one_card(row: Enrolment, *, now: Instant):
    region = await compose(row, now=now)
    assert len(region.cards) == 1
    return region.cards[0]


# --- 1 · chronological, and fixed at composition ---------------------------


async def test_the_region_keeps_the_order_it_was_given() -> None:
    """Never ordered by quality, and never re-sorted here.

    The port answers soonest-first and the composer does not sort again: two
    orderings of one list is how the region a player is committed to comes to
    disagree with itself between a compose and an update.
    """

    first = enrolled(a_match(paid=1))
    second = enrolled(a_match(paid=2))
    third = enrolled(a_match(paid=3))

    region = await compose(first, second, third, now=at(-3000))

    assert [card.match_id for card in region.cards] == [
        first.match_id,
        second.match_id,
        third.match_id,
    ]


async def test_every_card_carries_the_composes_one_stamp() -> None:
    region = await compose(enrolled(), enrolled(), now=at(-3000))

    assert {card.stamp for card in region.cards} == {STAMP}
    assert region.stamp == STAMP


async def test_a_player_with_no_matches_gets_a_region_that_is_present_and_empty() -> (
    None
):
    """A *region* makes no claim, so nothing in it is present and empty."""

    region = await compose(now=at(-3000))

    assert region.cards == ()
    assert region.stamp == STAMP


# --- the sport bar reaches the strip too -----------------------------------


async def test_a_named_chip_hides_the_other_sports() -> None:
    padel = enrolled(a_match(sport=Sport.PADEL, paid=1))
    squash = enrolled(a_match(sport=Sport.SQUASH, paid=1))

    region = await compose(padel, squash, now=at(-3000), sport=Sport.SQUASH)

    assert [card.match_id for card in region.cards] == [squash.match_id]


async def test_all_hides_nothing_at_all() -> None:
    """`all` is *no chip chosen*, and it must not hide a match she has paid for.

    Resolving it to *the sports she holds a rating at* is an argument about
    *Best fit for you* being a claim about her; applied here it would drop the
    squash match she is playing tomorrow because nobody has rated her yet.
    """

    padel = enrolled(a_match(sport=Sport.PADEL, paid=1))
    squash = enrolled(a_match(sport=Sport.SQUASH, paid=1))

    region = await compose(padel, squash, now=at(-3000), sport=None)

    assert len(region.cards) == 2


# --- 2 · counting is by money ----------------------------------------------


async def test_seats_paid_and_seats_held_are_two_numbers() -> None:
    """Counting people would say *3 of 4* while a seat may still lapse."""

    card = await one_card(enrolled(a_match(paid=2, held=1)), now=at(-3000))

    counts = card.situation.facts.counts
    assert (counts.seats, counts.paid, counts.held) == (4, 2, 1)


async def test_nobody_has_played_before_the_match_so_no_number_says_they_have() -> None:
    card = await one_card(enrolled(a_match(paid=4)), now=at(-3000))

    assert card.situation.facts.counts.turned_up is None


async def test_a_played_match_says_how_many_turned_up() -> None:
    card = await one_card(enrolled(a_match(paid=4)), now=at(120))

    assert card.situation.facts.counts.turned_up == 4


async def test_a_no_show_sends_three_and_four_rather_than_four_take_one_off() -> None:
    record = a_match(paid=4, no_show=True)

    card = await one_card(enrolled(record), now=at(120))

    counts = card.situation.facts.counts
    assert (counts.turned_up, counts.seats) == (3, 4)
    assert card.situation.situation is Situation.PLAYED_NO_SHOW


async def test_a_match_played_two_short_counts_the_two_who_paid() -> None:
    """The case that breaks *n − 1* on a phone: two played, not three."""

    card = await one_card(enrolled(a_match(paid=2)), now=at(120))

    counts = card.situation.facts.counts
    assert (counts.turned_up, counts.seats) == (2, 4)


# --- 3 · a hold is a reason and its facts ----------------------------------


async def test_a_held_court_names_one_of_five_reasons() -> None:
    card = await one_card(enrolled(a_match(paid=2)), now=at(-1000))

    assert card.situation.situation is Situation.HELD_SOFT
    hold = card.situation.facts.hold
    assert hold is not None
    assert hold.reason is CardHoldReason.FAR
    assert hold.age_minutes is None


async def test_a_stale_hold_carries_the_holds_real_age() -> None:
    """`now - heldSince`, and never the club's threshold."""

    record = a_match(
        paid=2,
        policy=_capped_at(hours(48)),
        held_since=at(-7200),
    )

    card = await one_card(enrolled(record), now=at(-1440))

    assert card.situation.situation is Situation.HELD_STALE
    hold = card.situation.facts.hold
    assert hold is not None
    assert hold.reason is CardHoldReason.STALE
    assert hold.age_minutes == 7200 - 1440


async def test_a_card_that_is_not_describing_a_court_names_no_hold() -> None:
    """The eight diagnostic reasons reach no card at all."""

    card = await one_card(enrolled(a_match(paid=0)), now=at(-3000))

    assert card.situation.facts.hold is None


# --- 4 · one clock -----------------------------------------------------------


async def test_a_card_has_one_clock_and_it_is_the_next_thing_that_happens() -> None:
    record = a_match(paid=1)

    card = await one_card(enrolled(record), now=at(-3000))

    assert card.clock == shifted(START, minutes(-1440))


async def test_a_cancelled_card_counts_to_nothing() -> None:
    record = a_match(paid=2, club_cancelled=True)

    card = await one_card(enrolled(record, closed_at=at(-2000)), now=at(-1999))

    assert card.clock is None


async def test_a_live_claim_of_her_own_takes_the_clock_and_shows_on_the_card() -> None:
    lapses = at(-2995)

    card = await one_card(
        enrolled(a_match(paid=1), holds_seat=False, claim_expires_at=lapses),
        now=at(-3000),
    )

    assert card.clock == lapses
    assert card.seat_claim is not None
    assert card.seat_claim.expires_at == lapses


async def test_a_claim_that_has_lapsed_is_not_on_the_card() -> None:
    card = await one_card(
        enrolled(a_match(paid=1), holds_seat=False, claim_expires_at=at(-3001)),
        now=at(-3000),
    )

    assert card.seat_claim is None


# --- 5 · where, and the court's name ---------------------------------------


async def test_every_card_says_whether_there_is_a_roof_and_whose_clock_face() -> None:
    card = await one_card(enrolled(where=a_place(cover=Cover.OUTDOOR)), now=at(-3000))

    assert card.where.cover is Cover.OUTDOOR
    assert card.where.zone == WARSAW


async def test_the_court_is_not_named_on_monday_for_a_thursday_match() -> None:
    """A court is assigned and may be reassigned; naming one early is a promise."""

    card = await one_card(enrolled(a_match(paid=4), court="Court 3"), now=at(-16))

    assert card.situation.facts.court is None


async def test_the_court_is_named_once_it_is_hers_to_know() -> None:
    row = enrolled(a_match(paid=4, committed_at=at(-1440)), court="Court 3")

    card = await one_card(row, now=at(-15))

    assert card.situation.situation is Situation.READY
    assert card.situation.facts.court == "Court 3"


async def test_a_match_with_no_court_assigned_names_none_even_at_the_door() -> None:
    card = await one_card(enrolled(a_match(paid=4), court=None), now=at(-15))

    assert card.situation.facts.court is None


# --- 6 · a card lives 24 hours from the moment it closed --------------------


async def test_a_cancelled_card_is_gone_twenty_four_hours_after_the_cancellation() -> (
    None
):
    """Cancelled Thursday 09:00, gone Friday 09:00 — not Sunday.

    The match starts days later, so `matchEnd + 24 h` would keep its corpse on
    her home screen long after everybody had moved on.
    """

    record = a_match(paid=2, club_cancelled=True)
    row = enrolled(record, closed_at=at(-2000))

    assert (await compose(row, now=at(-2000 + 1439))).cards != ()
    assert (await compose(row, now=at(-2000 + 1440))).cards == ()


async def test_a_played_card_is_gone_twenty_four_hours_after_the_last_point() -> None:
    played = int(DURATION)

    assert (await compose(enrolled(a_match(paid=4)), now=at(played + 1439))).cards != ()
    assert (await compose(enrolled(a_match(paid=4)), now=at(played + 1440))).cards == ()


async def test_a_match_that_has_not_closed_has_no_tail_however_far_off_it_is() -> None:
    assert (await compose(enrolled(a_match(paid=1)), now=at(-100_000))).cards != ()


async def test_a_terminal_row_with_no_closing_recorded_falls_back_and_still_dies() -> (
    None
):
    """The one row this column cannot date, and it must not live for ever.

    ADR-0048's original `matchEnd + 24 h` is what such a card would have expired
    under before the narrowing — which is a worse answer than the truth and a far
    better one than *never*.
    """

    row = enrolled(a_match(paid=2, club_cancelled=True), closed_at=None)
    played = int(DURATION)

    assert (await compose(row, now=at(played + 1439))).cards != ()
    assert (await compose(row, now=at(played + 1440))).cards == ()


# --- 7 · a cancellation names the amount and where it went ------------------


@pytest.mark.parametrize(
    "ending, cause, destination",
    [
        (
            {"inventory_lost": True, "club_cancelled": True},
            Cause.INVENTORY_LOST,
            RefundDestination.CARD,
        ),
        ({"club_cancelled": True}, Cause.CLUB_CANCELLED, RefundDestination.CARD),
        ({"weather": True}, Cause.CLUB_CANCELLED, RefundDestination.CARD),
        ({"form_cancelled": True}, Cause.FORM_CANCELLED, RefundDestination.CARD),
        (
            {"checkpoint_cancelled": True},
            Cause.CHECKPOINT_CANCELLED,
            RefundDestination.CLUB_CREDIT,
        ),
    ],
)
async def test_each_cancellation_names_its_cause_and_where_the_money_went(
    ending, cause, destination
) -> None:
    row = enrolled(
        a_match(paid=2, **ending),
        closed_at=at(-2000),
        paid_in=Money(amount=SHARE),
    )

    card = await one_card(row, now=at(-1999))

    assert card.situation.facts.cause is cause
    refund = card.situation.facts.refund
    assert refund is not None
    assert refund.amount == Money(amount=SHARE)
    assert refund.destination is destination


async def test_a_card_refund_carries_no_claim_that_the_money_landed() -> None:
    """A card lives 24 hours and a refund rarely arrives inside one.

    The payload is an amount and a destination and there is no *arrived* field
    for a branch that would ship on every cancellation card and never render.
    """

    row = enrolled(
        a_match(paid=2, club_cancelled=True),
        closed_at=at(-2000),
        paid_in=Money(amount=SHARE),
    )

    card = await one_card(row, now=at(-1999))

    assert set(vars(card.situation.facts.refund)) == {"amount", "destination"}


async def test_a_match_that_is_still_a_game_names_no_cause_and_no_refund() -> None:
    card = await one_card(
        enrolled(a_match(paid=2), paid_in=Money(amount=SHARE)), now=at(-3000)
    )

    assert card.situation.facts.cause is None
    assert card.situation.facts.refund is None


async def test_a_cancellation_she_never_paid_into_names_no_refund() -> None:
    """A card telling somebody money is coming back when none went in."""

    row = enrolled(
        a_match(paid=1, held=1, club_cancelled=True),
        closed_at=at(-2000),
        paid_in=Money(amount=grosze(0)),
    )

    card = await one_card(row, now=at(-1999))

    assert card.situation.facts.refund is None


# --- 8 · a private owner's two figures --------------------------------------


async def test_a_private_court_carries_what_is_recovered_and_the_whole_court() -> None:
    """Two figures that disagree on purpose, and the gap is the product fact."""

    record = a_match(paid=3, kind=MatchKind.PRIVATE, open_seats=2)

    card = await one_card(enrolled(record), now=at(-3000))

    owner = card.situation.facts.owner
    assert owner is not None
    # Two of four are on the marketplace and one of them has paid.
    assert owner.recovered == Money(amount=grosze(3800))
    # And the guarantee has not moved at all.
    assert owner.guaranteed == Money(amount=COURT)


async def test_the_guarantee_never_shrinks_as_shares_arrive() -> None:
    thin = a_match(paid=2, kind=MatchKind.PRIVATE, open_seats=2)
    full = a_match(paid=4, kind=MatchKind.PRIVATE, open_seats=2)

    lean = await one_card(enrolled(thin), now=at(-3000))
    fat = await one_card(enrolled(full), now=at(-3000))

    assert lean.situation.facts.owner.guaranteed == Money(amount=COURT)
    assert fat.situation.facts.owner.guaranteed == Money(amount=COURT)
    assert fat.situation.facts.owner.recovered == Money(amount=grosze(7600))


async def test_a_solo_private_court_has_recovered_nothing() -> None:
    record = a_match(
        paid=2, kind=MatchKind.PRIVATE, pay_model=PayModel.SOLO, open_seats=0
    )

    card = await one_card(enrolled(record), now=at(-3000))

    assert card.situation.situation is Situation.PRIVATE_RESERVED
    assert card.situation.facts.owner.recovered == Money(amount=grosze(0))


async def test_an_open_match_carries_no_owner_exposure_at_all() -> None:
    card = await one_card(enrolled(a_match(paid=2)), now=at(-3000))

    assert card.situation.facts.owner is None


# --- 9 · the court's total has no audience ----------------------------------


async def test_the_court_total_is_on_every_card_beside_her_own_share() -> None:
    """`{price} settled to the club` is the **court's** total, for everybody.

    Her own share answers a question she did not ask and answers it worse: her
    money left days ago, so *your 38 zł has gone* is stale news dressed as an
    update.
    """

    card = await one_card(
        enrolled(a_match(paid=4, committed_at=at(-1440))), now=at(-100)
    )

    assert card.price == Money(amount=SHARE)
    assert card.situation.facts.court_total == Money(amount=COURT)


# --- 10 · the leaver, and her two payload forms -----------------------------


async def test_a_leaver_keeps_a_card_and_it_keeps_the_matchs_own_progress() -> None:
    """Whether her money comes back depends entirely on the seat refilling."""

    record = a_match(
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(vacated_at=at(-1400)),),
    )
    row = enrolled(
        record,
        holds_seat=False,
        departure=DepartureRecoverable(paid=Money(amount=SHARE)),
    )

    card = await one_card(row, now=at(-1000))

    assert card.situation.situation is Situation.REPLACEMENT
    assert card.situation.facts.counts.paid == 3
    assert card.situation.facts.departure.paid == Money(amount=SHARE)
    assert card.situation.facts.departure.outcome is None


async def test_a_leaver_who_paid_nothing_carries_a_payload_with_no_amount() -> None:
    """*Nothing was taken* and *nothing has come back yet* are opposite sentences.

    An optional amount would be a field whose absence the phone has to
    interpret, and the phone interprets nothing.
    """

    row = enrolled(a_match(paid=1), holds_seat=False, departure=DepartureNothingTaken())

    card = await one_card(row, now=at(-3000))

    departure = card.situation.facts.departure
    assert departure.form is DepartureForm.NOTHING_TAKEN
    assert not hasattr(departure, "paid")


async def test_a_settled_departure_still_names_what_she_paid() -> None:
    """*You paid 38,00 zł and got none of it back* is the sentence."""

    row = enrolled(
        a_match(paid=4, checkpoint_cancelled=True),
        holds_seat=False,
        closed_at=at(-2000),
        departure=DepartureRecoverable(
            paid=Money(amount=SHARE), outcome=Outcome.FORFEITED
        ),
    )

    card = await one_card(row, now=at(-1999))

    assert card.situation.facts.departure.paid == Money(amount=SHARE)
    assert card.situation.facts.departure.outcome is Outcome.FORFEITED


async def test_a_player_still_on_the_match_carries_no_departure() -> None:
    card = await one_card(enrolled(a_match(paid=2)), now=at(-3000))

    assert card.situation.facts.departure is None


# --- 11 · a finished card prints the score ----------------------------------


async def test_a_settled_result_prints_both_sides_with_the_viewers_first() -> None:
    row = enrolled(
        a_match(paid=4, result_agreed=True),
        score=PlayedScore(
            sides=(("ala", "kuba"), ("zofia", "piotr")),
            sets=((6, 4), (3, 6), (6, 2)),
            viewer_side=1,
        ),
    )

    card = await one_card(row, now=at(120))

    score = card.situation.situation, card.situation.facts.score
    assert score[0] is Situation.COMPLETED
    assert [side.players for side in score[1].sides] == [
        ("zofia", "piotr"),
        ("ala", "kuba"),
    ]
    assert [(one.first, one.second) for one in score[1].sets] == [
        (4, 6),
        (6, 3),
        (2, 6),
    ]


async def test_a_viewer_on_side_a_gets_the_stored_order_unchanged() -> None:
    row = enrolled(
        a_match(paid=4, result_agreed=True),
        score=PlayedScore(
            sides=(("ala", "kuba"), ("zofia", "piotr")),
            sets=((6, 4),),
            viewer_side=0,
        ),
    )

    card = await one_card(row, now=at(120))

    assert [(one.first, one.second) for one in card.situation.facts.score.sets] == [
        (6, 4)
    ]


async def test_a_viewer_who_did_not_play_gets_the_matchs_own_order() -> None:
    """Nothing is invented for her — the stored score already means side A first."""

    row = enrolled(
        a_match(paid=4, result_agreed=True),
        holds_seat=False,
        score=PlayedScore(
            sides=(("ala", "kuba"), ("zofia", "piotr")),
            sets=((6, 4),),
            viewer_side=None,
        ),
    )

    card = await one_card(row, now=at(120))

    assert card.situation.facts.score.sides[0].players == ("ala", "kuba")


async def test_a_score_carries_no_level_movement_and_no_tiebreak() -> None:
    """No engine produces a level movement, and a card must not invent one."""

    row = enrolled(
        a_match(paid=4, result_agreed=True),
        score=PlayedScore(
            sides=(("ala", "kuba"), ("zofia", "piotr")),
            sets=((7, 6),),
            viewer_side=0,
        ),
    )

    card = await one_card(row, now=at(120))

    assert set(vars(card.situation.facts.score)) == {"sides", "sets"}
    assert set(vars(card.situation.facts.score.sets[0])) == {"first", "second"}


async def test_a_match_with_no_score_prints_none() -> None:
    card = await one_card(enrolled(a_match(paid=4)), now=at(120))

    assert card.situation.situation is Situation.NEEDS_RESULT
    assert card.situation.facts.score is None


# --- what a card deliberately does not carry --------------------------------


async def test_no_seated_card_names_an_act_while_no_surface_can_receive_one() -> None:
    """A door offered that will not open is worse than the gap (ADR-0083).

    The departure route landed and its control is a **spine boolean**, not a
    seventh act code — leaving is not the card's act, and putting it in `cta`
    would give one card two of them. Nine of the ten situations that name an act
    have a destination belonging to a ticket that has not landed, so `act` stays
    absent on all of them and this goes red the day one arrives without its
    surface.
    """

    region = await compose(
        enrolled(a_match(paid=4)),
        enrolled(a_match(paid=2)),
        now=at(-2000),
    )

    assert all(card.act is None for card in region.cards)


# --- the queue: the fourth membership, and the one act that has a surface ----


async def test_a_queue_place_puts_the_match_on_the_strip_as_waitlisted() -> None:
    """`waitlisted` is the one situation only a viewer can be in (ADR-0040).

    It is composed here because this is the only region on Now that could hold
    it: the offers region is seats offered to her, and the ranked shelves
    exclude a match she is queued for by rule. A card nowhere on the screen
    cannot carry a button.
    """

    card = await one_card(
        enrolled(a_match(paid=2), holds_seat=False, on_standby=True), now=at(-2000)
    )

    assert card.situation.situation is Situation.WAITLISTED


async def test_a_queued_card_names_the_act_whose_surface_this_ticket_built() -> None:
    """ADR-0087 exercised ADR-0083's growth rule: the act came **with** the write.

    That is the only way the enumeration was ever allowed to grow, and it is why
    this is the one act composed anywhere in the product today.
    """

    card = await one_card(
        enrolled(a_match(paid=2), holds_seat=False, on_standby=True), now=at(-2000)
    )

    assert card.act is ActCode.LEAVE_STANDBY


async def test_a_queue_place_beside_a_seat_changes_nothing() -> None:
    """Rung 7 tests *not seated*, so the seat wins and so does its silence.

    Nothing in the store refuses the pair, and nothing should: a player who
    queued for a match she later joined is an ordinary history, and the ladder
    already answers it.
    """

    card = await one_card(
        enrolled(a_match(paid=4), holds_seat=True, on_standby=True), now=at(-2000)
    )

    assert card.situation.situation is not Situation.WAITLISTED
    assert card.act is None


async def test_a_queued_card_offers_no_exit() -> None:
    """She holds no seat, so there is nothing to depart from.

    The two controls never appear together, which is ADR-0087's own reason for
    refusing to fold this act into the departure route.
    """

    card = await one_card(
        enrolled(a_match(paid=2), holds_seat=False, on_standby=True), now=at(-2000)
    )

    assert card.may_depart is False


async def test_a_queued_card_on_a_cancelled_match_says_the_cancellation() -> None:
    """The queue rung is the seventh, and four cancellations sit above it.

    A player queued for a match the club called off is told the match is off —
    not that she is still queueing for it — and her card dies on the same
    twenty-four-hour tail every other closed card does.
    """

    card = await one_card(
        enrolled(
            a_match(paid=2, club_cancelled=True),
            holds_seat=False,
            on_standby=True,
            closed_at=at(-2100),
        ),
        now=at(-2000),
    )

    assert card.situation.situation is Situation.CANCELLED_CLUB
    assert card.act is None


async def test_a_queued_card_leaves_the_screen_on_the_same_tail() -> None:
    """One rule for the region, and a queue place does not extend it."""

    region = await compose(
        enrolled(
            a_match(paid=2, club_cancelled=True),
            holds_seat=False,
            on_standby=True,
            closed_at=at(-2000),
        ),
        now=at(-2000 + 24 * 60 + 1),
    )

    assert region.cards == ()


async def test_the_act_table_names_only_acts_this_build_can_receive() -> None:
    """Read off the table itself, so a tenth row is a decision in a diff.

    ADR-0083's rule is *a card names an act when the viewer can take it now and
    a v1 surface can receive it*, and nine of the ten situations that would name
    one have no destination: the result route, the offers region, Find and the
    Getting-in sheet are all unbuilt. A row added ahead of its surface is a door
    that will not open, and this is where it is noticed.
    """

    assert dict(ACT_OF) == {Situation.WAITLISTED: ActCode.LEAVE_STANDBY}


async def test_a_card_offers_the_exit_exactly_where_the_write_would_take_it() -> None:
    """`may_depart` is `kernel.may_depart`, which is what `depart` refuses on.

    Driven **before** the start, because after it every answer is false and the
    claim would hold for the wrong reason — which is what the first version of
    this case did.
    """

    card = await one_card(enrolled(a_match(paid=4)), now=at(-2000))

    assert card.may_depart is True


@pytest.mark.parametrize(
    "row,now",
    [
        (enrolled(a_match(paid=4)), at(120)),
        (enrolled(a_match(paid=4, club_cancelled=True)), at(-2000)),
        (enrolled(a_match(paid=4), holds_seat=False), at(-2000)),
        # Her seat is held, so the **claim** is the only thing refusing — the
        # combination `holds_seat=False` would have been answered a line earlier
        # and proved nothing about the clause.
        (
            enrolled(a_match(paid=4), claim_expires_at=at(-1990)),
            at(-2000),
        ),
        (
            enrolled(a_match(paid=4, kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT)),
            at(-1440),
        ),
    ],
    ids=["started", "cancelled", "already-left", "live-claim", "private-lock"],
)
async def test_a_card_offers_no_exit_wherever_the_write_would_refuse(row, now) -> None:
    """The five falsities, on the card rather than on the route.

    One expression answers both, so a control cannot be drawn where the write
    would raise — and the day a sixth arrives it arrives on both at once.
    """

    card = await one_card(row, now=now)

    assert card.may_depart is False


async def test_a_card_in_this_region_carries_no_badge_and_never_shouts() -> None:
    """Both are judgements about a *suggestion*, and she is already in this one."""

    card = await one_card(enrolled(a_match(paid=2)), now=at(-3000))

    assert card.fit is None
    assert card.emphasis is False


def _capped_at(cap):
    from app.kernel import HoldPolicy

    return HoldPolicy(max_hold_age=cap)


def test_the_fixtures_agree_with_the_court_they_claim() -> None:
    """The share times the seats *is* the court, or every money case is fiction."""

    assert int(SHARE) * 4 == int(COURT)


def test_the_start_is_where_the_offsets_are_measured_from() -> None:
    assert START == instant(datetime(2026, 8, 22, 18, 30, tzinfo=timezone.utc))
    assert at(-1440) == START - timedelta(days=1)
