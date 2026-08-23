"""A departure is its own record, and its outcome only ever moves upward.

Six claims, and five of them are the ticket's acceptance criteria.

1. **A departure is its own record.** Not a flag on a seat, not an amount beside
   a hole — its own thing with its own id, its own clock and its own answer.
2. **A vacancy and a departure are independent.** Refilling the seat closes the
   hole and does not touch the departure that opened it; the filler settles the
   **oldest unsettled** departure, which ADR-0033's own worked example proves is
   not always the same one.
3. **Her money has two forms**, distinct payloads rather than one with a
   sometimes-absent amount (ADR-0072).
4. **Forfeit ranks equal to a zero refund**, so a forfeit quoted against a
   reversal applies rather than being refused (ADR-0033).
5. **Two concurrent leaves resolve by quote-and-confirm on the label.** The
   sharp case is the one the ADR names: the first leave drops the match below
   its checkpoint threshold and the second player's free reversal becomes a
   forfeit between the tap and the apply.
6. **A leaver still resolves against the match**, and her card does not vanish
   when somebody takes her seat.

The monotonic guarantee is asserted as a property of the **type**: ``Departure``
has no operation that lowers an outcome, so the grid below is exhaustive over
all sixteen moves rather than a sample of the ones somebody thought of.
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import product
from uuid import uuid4

import pytest

from app.kernel import (
    HoldPolicy,
    MatchKind,
    NothingTaken,
    Outcome,
    PayModel,
    Recoverable,
    SeatShare,
    Situation,
    Sport,
    Viewer,
    deadlines,
    grosze,
    hours,
    instant,
    live_outcome,
    minutes,
    outcome_rank,
    situation,
)
from app.modules.matches.domain.departure import Departure, oldest_unsettled
from app.modules.matches.domain.errors import (
    DepartureLocked,
    DepartureOutcomeWorsened,
    MatchAlreadyStarted,
    SeatNotTaken,
)
from app.modules.matches.domain.events import (
    DepartureOutcomeImproved,
    DepartureSettled,
    PlayerDeparted,
    SeatVacated,
)
from app.modules.matches.domain.match import Match

CLUB = uuid4()
CATEGORY = uuid4()
SHARE = SeatShare(grosze(3800))
POLICY = HoldPolicy(window=hours(24), join_cut=minutes(30))


def at(day: int, hour: int = 12, minute: int = 0):
    return instant(datetime(2026, 9, day, hour, minute, tzinfo=timezone.utc))


POSTED = at(1)
START = at(8, 18)


def a_match(**overrides):
    kwargs = dict(
        match_id=uuid4(),
        club_id=CLUB,
        category_id=CATEGORY,
        sport=Sport.PADEL,
        start=START,
        duration=hours(1),
        share=SHARE,
        policy=POLICY,
        at=POSTED,
    )
    kwargs.update(overrides)
    match = Match.post(**kwargs)
    match.pull_events()
    return match


def a_committed_match(*, when=at(7, 20), **overrides):
    """Four players, all paid, past the deadline — so it is genuinely bound.

    ``when`` is after `start - 24h`, which is what makes the fourth payment
    commit it on the spot rather than leaving it merely full.
    """

    match = a_match(**overrides)
    match.players = [uuid4() for _ in range(4)]
    for player in match.players:
        match.take_seat(player, at=when)
        match.pay_seat(player, at=when)
    assert match.committed_at is not None
    match.pull_events()
    return match


def leaves(match, player, *, when, quote=None):
    """Depart at the live outcome unless a stale quote is the point."""

    if quote is None:
        quote = live_outcome(match.as_record(), when)
    return match.depart(player, quote=quote, at=when)


def announced(match, kind):
    return [event for event in match.pull_events() if isinstance(event, kind)]


# --- 1 · a departure is its own record --------------------------------------


def test_leaving_writes_a_departure_and_a_vacancy_and_they_are_two_records():
    match = a_committed_match()
    leaver = match.players[0]

    departure = leaves(match, leaver, when=at(7, 21))

    assert len(match.departures) == 1
    assert len(match.vacancies) == 1
    assert departure.id != match.vacancies[0].id
    assert departure.seat_index == match.vacancies[0].seat_index


def test_the_departure_remembers_the_player_and_the_hole_does_not():
    match = a_committed_match()
    leaver = match.players[0]

    departure = leaves(match, leaver, when=at(7, 21))

    assert departure.player_id == leaver
    assert not hasattr(match.vacancies[0], "player_id")


def test_leaving_announces_the_hole_and_the_departure_separately():
    """Two facts, two names. A support agent asks about them separately."""

    match = a_committed_match()

    leaves(match, match.players[0], when=at(7, 21))

    events = match.pull_events()
    assert [type(one) for one in events] == [SeatVacated, PlayerDeparted]


def test_the_announcement_carries_the_label_she_acted_on():
    match = a_committed_match()

    leaves(match, match.players[0], when=at(7, 21))

    (departed,) = announced(match, PlayerDeparted)
    assert departed.quoted == Outcome.REFUNDED_IN_FULL.value
    assert departed.amount_grosze == 3800


def test_leaving_a_seat_nobody_holds_is_refused():
    """One of ADR-0033's two absolute refusals, and it is not quote-driven."""

    match = a_committed_match()

    with pytest.raises(SeatNotTaken):
        leaves(match, uuid4(), when=at(7, 21))


def test_a_leaver_cannot_leave_twice():
    """The same refusal, reached the other way: she holds no seat any more."""

    match = a_committed_match()
    leaver = match.players[0]
    leaves(match, leaver, when=at(7, 21))

    with pytest.raises(SeatNotTaken):
        leaves(match, leaver, when=at(7, 22))


# --- 2 · the two axes -------------------------------------------------------


def test_refilling_the_seat_does_not_touch_the_departure_that_opened_it():
    """The hole closes; the settlement is a separate write with its own moment.

    Asserted on identity as well as on the fields: a departure replaced by an
    equal-looking one would pass a field comparison and lose the record.
    """

    match = a_committed_match()
    departure = leaves(match, match.players[0], when=at(7, 21))
    before = (departure.id, departure.player_id, departure.money, departure.quoted)

    match.take_seat(uuid4(), at=at(7, 22))

    assert match.open_vacancies == []
    assert match.departures == [departure]
    assert (
        departure.id,
        departure.player_id,
        departure.money,
        departure.quoted,
    ) == before


def test_a_filler_settles_the_oldest_unsettled_departure_and_not_the_oldest_hole():
    """ADR-0033's worked example, and the defect it was written against.

    A transfer is **born settled** and still leaves a hole; an ordinary leave
    after it is unsettled. One sorted pass stopping at the first match hands the
    filler to the departure with nothing to settle, and *"Ola stays owed while a
    seat gets filled."* The symptom is one player never refunded, months later,
    and never an error.

    Here the born-settled departure is an unpaid seat-holder rather than a
    transfer, because transfers have no v1 surface — the shape is identical:
    settled departure first, unsettled departure second, one filler.
    """

    match = a_committed_match()
    settled_leaver, owed_leaver = match.players[0], match.players[1]

    # Somebody takes the first seat back and does not pay, then leaves: born
    # settled, hole open.
    leaves(match, settled_leaver, when=at(7, 21))
    stand_in = uuid4()
    match.take_seat(stand_in, at=at(7, 21, 30))
    born_settled = leaves(match, stand_in, when=at(7, 22))
    # And now somebody who *had* paid leaves: unsettled, hole open.
    owed = leaves(match, owed_leaver, when=at(7, 23))
    match.pull_events()

    assert born_settled.is_settled
    assert not owed.is_settled

    match.take_seat(uuid4(), at=at(8, 1))

    assert owed.is_settled, "the filler skipped the only person who was owed"
    assert owed.outcome is Outcome.REFUNDED_IN_FULL
    assert born_settled.outcome is Outcome.REVERSED


def test_the_filler_closes_the_oldest_hole_while_settling_a_different_departure():
    """The two FIFO queues, asserted as two: same list, different filters."""

    match = a_committed_match()
    first_hole = leaves(match, match.players[0], when=at(7, 21))
    stand_in = uuid4()
    match.take_seat(stand_in, at=at(7, 21, 30))  # closes the first hole, settles it
    leaves(match, stand_in, when=at(7, 22))  # born settled, second hole
    owed = leaves(match, match.players[1], when=at(7, 23))  # unsettled, third hole

    match.take_seat(uuid4(), at=at(8, 1))

    assert first_hole.is_settled
    assert owed.is_settled
    # The hole that closed is the second one — the oldest open — while the
    # departure that settled is the third.
    assert [one.vacated_at for one in match.open_vacancies] == [at(7, 23)]


def test_the_older_of_two_unsettled_departures_is_the_one_a_filler_settles():
    """FIFO, and it is a queue over **waiting**: the seat somebody takes is not
    the seat anybody vacated, so the only thing that can order the two is how
    long each has been owed."""

    match = a_committed_match()
    older = leaves(match, match.players[0], when=at(7, 21))
    newer = leaves(match, match.players[1], when=at(7, 22))

    match.take_seat(uuid4(), at=at(7, 23))

    assert older.is_settled
    assert not newer.is_settled


def test_the_queue_is_ordered_by_waiting_and_not_by_seat():
    """The same claim with the two orders pulled apart: the player who has been
    waiting longest holds the **higher** seat number here, so a queue keyed on
    the seat settles the wrong person."""

    match = a_committed_match()
    older = leaves(match, match.players[2], when=at(7, 21))
    newer = leaves(match, match.players[0], when=at(7, 22))

    match.take_seat(uuid4(), at=at(7, 23))

    assert older.is_settled
    assert not newer.is_settled


def test_a_filler_with_nobody_owed_closes_a_hole_and_settles_nothing():
    """*"A filler arriving when every departure is already settled closes a
    vacancy and settles nothing, which is correct."*"""

    match = a_match()
    holder = uuid4()
    match.take_seat(holder, at=POSTED)
    departure = leaves(match, holder, when=at(2))
    match.pull_events()

    match.take_seat(uuid4(), at=at(3))

    assert match.open_vacancies == []
    assert departure.outcome is Outcome.REVERSED
    assert announced(match, DepartureSettled) == []


def test_oldest_unsettled_is_total_and_skips_the_born_settled():
    """The helper on its own, because it is one of two traversals that differ
    only in their filter — the shape ADR-0033 calls a real hazard."""

    settled = Departure(
        id=uuid4(),
        seat_index=0,
        player_id=uuid4(),
        departed_at=at(2),
        quoted=Outcome.REVERSED,
        money=NothingTaken(),
        outcome=Outcome.REVERSED,
        settled_at=at(2),
    )
    owed = Departure(
        id=uuid4(),
        seat_index=1,
        player_id=uuid4(),
        departed_at=at(3),
        quoted=Outcome.REFUNDED_IN_FULL,
        money=Recoverable(amount=grosze(3800)),
    )

    assert oldest_unsettled([settled, owed]) is owed
    assert oldest_unsettled([settled]) is None
    assert oldest_unsettled([]) is None


# --- 3 · the two money forms ------------------------------------------------


def test_a_leaver_before_commitment_names_no_amount():
    """*"The seat is cleared and unpaid, so there is nothing left to derive from
    and the card can name no amount at all"* (ADR-0030)."""

    match = a_match()
    holder = uuid4()
    match.take_seat(holder, at=POSTED)
    match.pay_seat(holder, at=POSTED)

    departure = leaves(match, holder, when=at(2))

    assert departure.money == NothingTaken()
    assert departure.took_nothing


def test_a_leaver_after_commitment_names_what_she_paid():
    match = a_committed_match()

    departure = leaves(match, match.players[0], when=at(7, 21))

    assert departure.money == Recoverable(amount=grosze(3800))


def test_somebody_who_never_paid_names_no_amount_however_close_it_is():
    """A seat held and never paid for has nothing to return, at any distance."""

    match = a_committed_match()
    leaves(match, match.players[0], when=at(7, 21))
    stand_in = uuid4()
    match.take_seat(stand_in, at=at(7, 22))

    departure = leaves(match, stand_in, when=at(8, 15))

    assert departure.money == NothingTaken()
    assert departure.outcome is Outcome.REVERSED


def test_a_departure_that_took_nothing_is_born_settled():
    match = a_match()
    holder = uuid4()
    match.take_seat(holder, at=POSTED)

    departure = leaves(match, holder, when=at(2))

    assert departure.is_settled
    assert departure.settled_at == at(2)


def test_a_departure_with_money_at_stake_is_born_unsettled():
    match = a_committed_match()

    departure = leaves(match, match.players[0], when=at(7, 21))

    assert not departure.is_settled
    assert departure.outcome is None
    assert departure.settled_at is None


def test_the_two_forms_cannot_be_mixed_up_with_the_outcome():
    """*Nothing taken* is *reversed*, in both directions and for life."""

    with pytest.raises(ValueError):
        Departure(
            id=uuid4(),
            seat_index=0,
            player_id=uuid4(),
            departed_at=at(2),
            quoted=Outcome.REVERSED,
            money=NothingTaken(),
            outcome=Outcome.REFUNDED_IN_FULL,
            settled_at=at(2),
        )

    with pytest.raises(ValueError):
        Departure(
            id=uuid4(),
            seat_index=0,
            player_id=uuid4(),
            departed_at=at(2),
            quoted=Outcome.REVERSED,
            money=Recoverable(amount=grosze(3800)),
            outcome=Outcome.REVERSED,
            settled_at=at(2),
        )


def test_a_settlement_is_an_outcome_and_a_moment_or_neither():
    with pytest.raises(ValueError):
        Departure(
            id=uuid4(),
            seat_index=0,
            player_id=uuid4(),
            departed_at=at(2),
            quoted=Outcome.REFUNDED_IN_FULL,
            money=Recoverable(amount=grosze(3800)),
            outcome=Outcome.REFUNDED_HALF,
            settled_at=None,
        )


# --- 4 · monotonic upward, as a property of the type ------------------------


def an_unsettled_departure():
    return Departure(
        id=uuid4(),
        seat_index=0,
        player_id=uuid4(),
        departed_at=at(2),
        quoted=Outcome.REFUNDED_IN_FULL,
        money=Recoverable(amount=grosze(3800)),
    )


#: Every outcome a departure with money at stake can reach. `REVERSED` is not
#: one: it means nothing was taken, and such a departure is born settled.
SETTLEABLE = [one for one in Outcome if one is not Outcome.REVERSED]


@pytest.mark.parametrize("outcome", SETTLEABLE)
def test_an_unsettled_departure_settles_at_whatever_it_is_given(outcome):
    departure = an_unsettled_departure()

    assert departure.raise_to(outcome, at=at(3)) is True
    assert departure.outcome is outcome
    assert departure.settled_at == at(3)


@pytest.mark.parametrize(
    "settled_at_outcome, target", list(product(SETTLEABLE, SETTLEABLE))
)
def test_an_outcome_moves_only_upward(settled_at_outcome, target):
    """The whole grid, so the guarantee is not a sample of remembered cases."""

    departure = an_unsettled_departure()
    departure.raise_to(settled_at_outcome, at=at(3))

    moved = departure.raise_to(target, at=at(4))

    if outcome_rank(target) > outcome_rank(settled_at_outcome):
        assert moved is True
        assert departure.outcome is target
        assert departure.settled_at == at(4)
    else:
        assert moved is False
        assert departure.outcome is settled_at_outcome
        assert departure.settled_at == at(3)


def test_a_departure_that_took_nothing_never_moves():
    """There is no money to return, so an improvement would announce a refund
    that cannot happen."""

    departure = Departure(
        id=uuid4(),
        seat_index=0,
        player_id=uuid4(),
        departed_at=at(2),
        quoted=Outcome.REVERSED,
        money=NothingTaken(),
        outcome=Outcome.REVERSED,
        settled_at=at(2),
    )

    assert departure.raise_to(Outcome.REFUNDED_IN_FULL, at=at(3)) is False
    assert departure.outcome is Outcome.REVERSED


def test_the_only_way_to_move_an_outcome_is_upward_by_construction():
    """No setter, no lowering method — asserted so that adding one is loud."""

    movers = {
        name
        for name in dir(Departure)
        if not name.startswith("_") and callable(getattr(Departure, name, None))
    }

    assert movers == {"raise_to"}


# --- the club-side failure that reopens a settlement ------------------------


def test_a_club_cancellation_improves_a_settled_half_to_a_full_refund():
    """ADR-0030's own example, and the reason `settlementReopened` is a cause."""

    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(8, 16, 30))
    match.take_seat(uuid4(), at=at(8, 16, 45))
    assert owed.outcome is Outcome.REFUNDED_HALF
    match.pull_events()

    match.cancel_by_club(at=at(8, 17))

    assert owed.outcome is Outcome.REFUNDED_IN_FULL
    (improved,) = announced(match, DepartureOutcomeImproved)
    assert improved.improved_from == Outcome.REFUNDED_HALF.value
    assert improved.improved_to == Outcome.REFUNDED_IN_FULL.value


def test_a_club_cancellation_settles_a_departure_that_had_not_settled():
    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))
    match.pull_events()

    match.cancel_by_club(at=at(7, 22))

    assert owed.outcome is Outcome.REFUNDED_IN_FULL
    (settled,) = announced(match, DepartureSettled)
    assert settled.outcome == Outcome.REFUNDED_IN_FULL.value


def test_a_club_cancellation_leaves_a_full_refund_exactly_where_it_is():
    """Silently — *"you are still refunded in full"* is not a change."""

    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))
    match.take_seat(uuid4(), at=at(7, 22))
    assert owed.outcome is Outcome.REFUNDED_IN_FULL
    settled_at = owed.settled_at
    match.pull_events()

    match.cancel_by_club(at=at(7, 23))

    assert owed.settled_at == settled_at
    assert announced(match, DepartureOutcomeImproved) == []


def test_the_checkpoint_cancellation_forfeits_whatever_is_still_open():
    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))

    match.settle_checkpoint_cancellation(at=at(8, 16))

    assert owed.outcome is Outcome.FORFEITED


def test_the_checkpoint_cancellation_does_not_take_back_a_settled_refund():
    """Forfeited ranks at the bottom, so it can only ever settle, never lower."""

    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))
    match.take_seat(uuid4(), at=at(7, 22))

    match.settle_checkpoint_cancellation(at=at(8, 16))

    assert owed.outcome is Outcome.REFUNDED_IN_FULL


# --- 5 · quote-and-confirm --------------------------------------------------


def test_a_quote_that_has_become_worse_is_refused_and_names_what_is_true_now():
    match = a_committed_match()

    with pytest.raises(DepartureOutcomeWorsened) as refused:
        leaves(
            match,
            match.players[0],
            when=at(8, 15),
            quote=Outcome.REFUNDED_IN_FULL,
        )

    assert refused.value.outcome is Outcome.REFUNDED_HALF
    assert match.departures == []
    assert match.vacancies == []


def test_a_refusal_leaves_the_seat_exactly_where_it_was():
    """She is re-presented, not half-removed."""

    match = a_committed_match()
    leaver = match.players[0]

    with pytest.raises(DepartureOutcomeWorsened):
        leaves(match, leaver, when=at(8, 16, 30), quote=Outcome.REFUNDED_IN_FULL)

    assert match.seat_of(leaver) is not None
    assert match.seat_of(leaver).paid
    assert match.pull_events() == []


def test_an_equal_quote_applies():
    match = a_committed_match()

    departure = leaves(
        match, match.players[0], when=at(7, 21), quote=Outcome.REFUNDED_IN_FULL
    )

    assert departure.quoted is Outcome.REFUNDED_IN_FULL


def test_a_better_outcome_than_quoted_applies():
    """Equal **or better** applies — she is never refused for good news."""

    match = a_committed_match()

    departure = leaves(
        match, match.players[0], when=at(7, 21), quote=Outcome.FORFEITED
    )

    assert departure.quoted is Outcome.REFUNDED_IN_FULL


def test_a_forfeit_quoted_against_a_reversal_applies():
    """The tie, at the behaviour rather than at the ranking: *"a confirmation
    dialog that says 'still zero' is friction bought for no protection."*"""

    match = a_match()
    holder = uuid4()
    match.take_seat(holder, at=POSTED)
    match.pay_seat(holder, at=POSTED)

    departure = leaves(match, holder, when=at(2), quote=Outcome.FORFEITED)

    assert departure.quoted is Outcome.REVERSED


def test_two_concurrent_leaves_resolve_by_the_label_and_not_by_the_amount():
    """The sharp case ADR-0033 names: the first leave changes the second one's
    position between the tap and the apply.

    Ola and Kuba are both shown *refunded in full* while the full-price search
    would run. Ola leaves; the clock reaches Rescue; Kuba's tap lands carrying
    the label he was shown, and it is refused with the one that is now true.
    """

    match = a_committed_match()
    ola, kuba = match.players[0], match.players[1]
    both_shown = live_outcome(match.as_record(), at(7, 21))
    assert both_shown is Outcome.REFUNDED_IN_FULL

    leaves(match, ola, when=at(7, 21), quote=both_shown)

    with pytest.raises(DepartureOutcomeWorsened) as refused:
        leaves(match, kuba, when=at(8, 15), quote=both_shown)

    assert refused.value.outcome is Outcome.REFUNDED_HALF

    # Re-presented, and the second tap carrying the corrected label goes through.
    second = leaves(
        match, kuba, when=at(8, 15), quote=refused.value.outcome
    )
    assert second.quoted is Outcome.REFUNDED_HALF
    assert len(match.departures) == 2


# --- 6 · a leaver still resolves against the match --------------------------


def test_a_leavers_card_is_the_matchs_own_situation():
    """ADR-0030: *"the leaver's card is the match's card rendered for somebody
    who used to hold a seat."* The ladder takes no leaver — she resolves as
    somebody looking in, and the audience is a rendering downstream."""

    match = a_committed_match()
    leaver = match.players[0]
    leaves(match, leaver, when=at(7, 21))

    record = match.as_record()
    assert situation(record, Viewer(holds_seat=False), at(7, 22)) is (
        situation(record, None, at(7, 22))
    )
    assert situation(record, None, at(7, 22)) is Situation.REPLACEMENT


def test_a_leaver_keeps_her_record_when_the_seat_refills():
    """*"Nothing vanishes."* The hole closes and the match goes back to
    describing an ordinary complete match — and her departure is still there,
    still findable by her."""

    match = a_committed_match()
    leaver = match.players[0]
    leaves(match, leaver, when=at(7, 21))

    match.take_seat(uuid4(), at=at(7, 22))
    match.pay_seat(match.seats[0].player_id, at=at(7, 22))

    assert match.departure_of(leaver) is not None
    # Back to describing a complete match — `confirmedOnFill` rather than
    # `confirmed` because this one filled past its own deadline — with no
    # trace of the recovery it went through, and her record still standing.
    assert situation(match.as_record(), None, at(7, 23)) is (
        Situation.CONFIRMED_ON_FILL
    )


def test_a_leaver_is_found_by_herself_and_not_by_the_seat_she_left():
    """The seat may be somebody else's by now, which is the whole point."""

    match = a_committed_match()
    leaver = match.players[0]
    departure = leaves(match, leaver, when=at(7, 21))
    filler = uuid4()
    match.take_seat(filler, at=at(7, 22))

    assert match.departure_of(leaver) is departure
    assert match.departure_of(filler) is None


def test_the_newest_departure_is_the_one_a_returning_leaver_gets():
    match = a_committed_match()
    player = match.players[0]
    leaves(match, player, when=at(7, 21))
    match.take_seat(player, at=at(7, 22))
    again = leaves(match, player, when=at(7, 23))

    assert match.departure_of(player) is again


# --- settlement once the roster can no longer change ------------------------


def test_nothing_settles_while_a_seat_event_is_still_possible():
    """Including past the **join cutoff**, which is where ADR-0030's example
    puts it and where ADR-0081 later made it wrong: a claim already running when
    the cutoff passes is honoured to completion, so money can still arrive."""

    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))
    when = deadlines(match.as_record())

    assert match.settle_departures_if_closed(at=when.join_cut) == 0
    assert match.settle_departures_if_closed(at=_a_minute_before(when.play)) == 0
    assert not owed.is_settled


def test_the_start_forfeits_a_seat_nobody_took():
    """*"An outcome settles when no further seat event can change it."* The
    aggregate refuses every seat move from the start, so the start is derivably
    that moment rather than a claim about a rule kept somewhere else."""

    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))
    when = deadlines(match.as_record()).play

    assert match.settle_departures_if_closed(at=when) == 1
    assert owed.outcome is Outcome.FORFEITED
    (settled,) = announced(match, DepartureSettled)
    assert settled.outcome == Outcome.FORFEITED.value


def test_the_moment_it_settles_at_is_the_moment_no_seat_can_move():
    """The two halves of the argument, asserted together: the aggregate refuses
    a seat move from exactly the instant the settlement fires."""

    match = a_committed_match()
    leaves(match, match.players[0], when=at(7, 21))
    play = deadlines(match.as_record()).play

    with pytest.raises(MatchAlreadyStarted):
        match.take_seat(uuid4(), at=play)
    assert match.settle_departures_if_closed(at=play) == 1


def test_settling_twice_moves_nothing_and_announces_nothing():
    match = a_committed_match()
    leaves(match, match.players[0], when=at(7, 21))
    when = deadlines(match.as_record()).play
    match.settle_departures_if_closed(at=when)
    match.pull_events()

    assert match.settle_departures_if_closed(at=when) == 0
    assert match.pull_events() == []


def test_a_claim_that_pays_past_the_join_cutoff_still_settles_in_full():
    """The case that decided the moment. A claim started before ``joinCut`` is
    honoured to completion (``Raketa02/Raketa#68``), so its payment lands after
    the cutoff — and finds the departure still open, rather than a forfeit that
    had already taken her money."""

    match = a_committed_match()
    owed = leaves(match, match.players[0], when=at(7, 21))
    past_the_cutoff = at(8, 17, 45)
    assert past_the_cutoff > deadlines(match.as_record()).join_cut

    match.take_seat(uuid4(), at=past_the_cutoff)

    assert owed.outcome is Outcome.REFUNDED_HALF


# --- 7 · the one departure the model refuses --------------------------------


def _converted(**overrides):
    """A private court sold by the share, full: ADR-0046's *converted* court."""

    match = a_committed_match(**overrides)
    match.kind = MatchKind.PRIVATE
    match.pay_model = PayModel.SPLIT
    return match


def test_nobody_leaves_a_converted_court_that_is_bought_and_full():
    """ADR-0046's lock, refused **by the aggregate** and not only by the route.

    `kernel.may_depart` answers false in the same place, so no control is ever
    drawn — but a boolean the write does not enforce is a rule held only on the
    phone, and this is the half that keeps it on the server. It survived a
    mutation pass before this case existed: deleting the refusal left the whole
    aggregate suite green.
    """

    match = _converted()
    # The default club's cancellation window is twenty-four hours, and the
    # match starts at 18:00 on the eighth.
    past_the_deadline = at(7, 20)

    with pytest.raises(DepartureLocked):
        match.depart(match.players[0], quote=Outcome.REFUNDED_IN_FULL,
                     at=past_the_deadline)

    assert match.departures == []
    assert match.vacancies == []


def test_a_converted_court_is_free_to_leave_until_that_deadline():
    """A minute either side, because a region asserted is not a boundary.

    The match starts at 18:00 on the eighth and the default club's cancellation
    window is twenty-four hours, so the lock closes at 18:00 on the seventh.
    """

    free = _converted()
    departure = free.depart(
        free.players[0], quote=Outcome.REFUNDED_IN_FULL, at=at(7, 17, 59)
    )
    assert departure.quoted is Outcome.REFUNDED_IN_FULL

    locked = _converted()
    with pytest.raises(DepartureLocked):
        locked.depart(locked.players[0], quote=Outcome.REFUNDED_IN_FULL, at=at(7, 18))


def test_a_converted_court_short_of_full_never_locks():
    """A stranger has not yet bought a court that definitely exists."""

    match = _converted()
    match.depart(match.players[0], quote=Outcome.REFUNDED_IN_FULL, at=at(7, 17))

    # One seat short now, and the deadline has passed — still free to leave.
    second = match.depart(
        match.players[1], quote=Outcome.REFUNDED_IN_FULL, at=at(7, 20)
    )

    assert second.quoted is Outcome.REFUNDED_IN_FULL


def test_an_open_match_never_locks_however_full_and_however_late():
    """The lock is a private-court rule, and an open match is not one."""

    match = a_committed_match()

    departure = leaves(match, match.players[0], when=at(8, 17))

    assert departure.quoted is Outcome.FORFEITED


def _a_minute_before(moment):
    from app.kernel import shifted

    return shifted(moment, minutes(-1))
