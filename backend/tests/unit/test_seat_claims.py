"""Five minutes of exclusive right to buy one seat, and every way it ends.

ADR-0081 and ``Raketa02/Raketa#68``. The seven claims below are the ticket's
acceptance criteria, and the last one is the one the whole design is arranged
around.

1. **Five minutes from the tap**, and the expiry is a **match wake** rather than
   anything sent to anybody.
2. **One live claim per player.** The half inside one match is asserted here;
   the half across matches is a port, and it is asserted in
   ``test_claim_seat_use_case.py`` where a second match exists.
3. **Thirty seconds** before the same player may re-claim the **same seat**.
4. **A running claim is honoured past ``joinCut``** — a deadline and not a
   trapdoor.
5. **No claim may be started after ``joinCut``.**
6. **A live claim silences the offer's pending waves**, and a lapse resumes them
   with nobody told twice — which needs no write at all, and that is the point.
7. **A claim never appears as a seat state.** Occupancy still reads *paid* or
   *unpaid* and nothing else, which is what keeps the fill count, the forecast
   and the hold ladder honest without any of them learning a new word.

Every threshold below is written out in this file. A test that asked the kernel
how long five minutes was would agree with it about four.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import (
    HoldPolicy,
    MatchKind,
    PayModel,
    SeatShare,
    Situation,
    Sport,
    Viewer,
    filled,
    grosze,
    held_unpaid,
    court_hold,
    hours,
    instant,
    is_full,
    live_outcome,
    minutes,
    next_wake,
    situation,
)
from app.modules.matches.domain.errors import (
    ClaimCoolingDown,
    JoiningClosed,
    MatchAlreadySettled,
    MatchAlreadyStarted,
    MatchIsFull,
    NoLiveSeatClaim,
    PlayerAlreadyClaiming,
    PlayerAlreadyHoldsASeat,
    SeatAlreadyClaimed,
    SeatClaimAlreadyEnded,
)
from app.modules.matches.domain.events import (
    SeatClaimLapsed,
    SeatClaimOpened,
    SeatClaimRedeemed,
    SeatPaid,
    SeatTaken,
)
from app.modules.matches.domain.match import Match

CLUB = uuid4()
CATEGORY = uuid4()
SHARE = SeatShare(grosze(3800))
POLICY = HoldPolicy(window=hours(24), join_cut=minutes(30))

#: The two thresholds, spelled out here rather than imported.
FIVE_MINUTES = timedelta(minutes=5)
THIRTY_SECONDS = timedelta(seconds=30)


def at(day: int, hour: int = 12, minute: int = 0, second: int = 0):
    return instant(
        datetime(2026, 9, day, hour, minute, second, tzinfo=timezone.utc)
    )


POSTED = at(1)
START = at(8, 18)
#: The join cutoff: thirty minutes before the start.
JOIN_CUT = at(8, 17, 30)


def a_match(**overrides) -> Match:
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


def kinds(match: Match) -> list[type]:
    return [type(event) for event in match.pull_events()]


# --- 1 · five minutes, and the expiry is a wake -----------------------------


def test_a_claim_runs_for_five_minutes_from_the_tap() -> None:
    match = a_match()
    tapped = at(7, 20)

    claim = match.open_claim(uuid4(), at=tapped)

    assert claim.claimed_at == tapped
    assert claim.expires_at == tapped + FIVE_MINUTES


def test_the_claim_is_live_right_up_to_its_deadline_and_not_at_it() -> None:
    match = a_match()
    buyer = uuid4()
    match.open_claim(buyer, at=at(7, 20))

    assert match.live_claim_of(buyer, at(7, 20, 4, 59)) is not None
    assert match.live_claim_of(buyer, at(7, 20, 5)) is None


def test_the_expiry_is_the_match_s_own_next_wake() -> None:
    """*"An expiry is a match wake, not a channel send"* (ADR-0081).

    A fortnight out there is nothing else within five minutes of anything, so
    the schedule pointing at the claim is unambiguous — and it is the match's
    schedule, which is what makes the claim reachable by a look at all.
    """

    match = a_match()
    tapped = at(7, 20)
    claim = match.open_claim(uuid4(), at=tapped)

    wake = next_wake(match.as_record(), tapped)

    assert wake is not None
    assert wake.at == claim.expires_at
    assert wake.reason.value == "claimLapse"


def test_reaping_writes_the_receipt_and_dates_it_at_the_expiry() -> None:
    """A worker that was down for an hour must not extend anybody's thirty
    seconds by an hour, so the receipt is dated when the claim actually ended."""

    match = a_match()
    buyer = uuid4()
    claim = match.open_claim(buyer, at=at(7, 20))
    match.pull_events()

    reaped = match.reap_lapsed_claims(at=at(8, 9))

    assert reaped == 1
    assert claim.ended_at == claim.expires_at == at(7, 20, 5)
    assert kinds(match) == [SeatClaimLapsed]


def test_reaping_twice_writes_nothing_the_second_time() -> None:
    """A wake taken twice is looking twice, which is why ADR-0076 needs no table
    of handled keys."""

    match = a_match()
    match.open_claim(uuid4(), at=at(7, 20))
    match.reap_lapsed_claims(at=at(7, 20, 6))
    match.pull_events()

    assert match.reap_lapsed_claims(at=at(7, 20, 7)) == 0
    assert kinds(match) == []


def test_a_live_claim_is_not_reaped() -> None:
    match = a_match()
    match.open_claim(uuid4(), at=at(7, 20))
    match.pull_events()

    assert match.reap_lapsed_claims(at=at(7, 20, 4)) == 0
    assert kinds(match) == []


def test_a_claim_ended_twice_is_refused_rather_than_moved() -> None:
    """Moving the instant a claim closed would move the cooldown measured from
    it — history rewritten rather than recorded."""

    match = a_match()
    claim = match.open_claim(uuid4(), at=at(7, 20))
    claim.end(at=at(7, 20, 2))

    with pytest.raises(SeatClaimAlreadyEnded):
        claim.end(at=at(7, 23))


def test_a_claim_ended_before_its_deadline_is_over_at_once() -> None:
    """**Ended and expired are two different endings, and liveness reads both.**

    A redeemed claim — or one a cancellation closed — still has minutes left on
    its own clock, so a liveness that asked only the clock would go on calling a
    spent claim live. The seat under it would read as *spoken for* by the player
    who is already sitting on it: she could not be seated by anybody, the
    cascade would not offer it, and the card would draw no exit. It is the same
    rule the cross-match query needs one layer down, which is why both are
    asserted rather than one standing in for the other.
    """

    match = a_match()
    buyer = uuid4()
    claim = match.open_claim(buyer, at=at(7, 20))

    claim.end(at=at(7, 20, 1))

    assert claim.expires_at > claim.ended_at, "ended with time still on its clock"
    assert not claim.is_live(at(7, 20, 2))
    assert match.live_claim_of(buyer, at(7, 20, 2)) is None
    assert match.seats_under_claim(at(7, 20, 2)) == frozenset()


# --- 2 · one live claim per player, inside one match ------------------------


def test_a_second_claim_by_the_same_player_is_refused() -> None:
    match = a_match()
    buyer = uuid4()
    match.open_claim(buyer, at=at(7, 20))

    with pytest.raises(PlayerAlreadyClaiming):
        match.open_claim(buyer, at=at(7, 20, 2))


def test_a_player_already_on_the_match_cannot_claim_a_second_seat() -> None:
    match = a_match()
    player = uuid4()
    match.take_seat(player, at=at(7, 20))

    with pytest.raises(PlayerAlreadyHoldsASeat):
        match.open_claim(player, at=at(7, 20, 1))


def test_she_may_claim_again_once_her_five_minutes_and_the_cooldown_are_up(
) -> None:
    """Her own lapse is reaped by her own second tap, and the seat is hers again."""

    match = a_match()
    buyer = uuid4()
    first = match.open_claim(buyer, at=at(7, 20))

    second = match.open_claim(buyer, at=at(7, 20, 6))

    assert first.ended_at == first.expires_at
    assert second.seat_index == first.seat_index


def test_inside_the_cooldown_she_is_given_a_different_free_seat() -> None:
    """The cooldown is per seat, so a match with room simply moves her along
    rather than telling her to wait — which is the difference between breaking a
    tap-loop and charging her for one."""

    match = a_match()
    buyer = uuid4()
    first = match.open_claim(buyer, at=at(7, 20))

    second = match.open_claim(buyer, at=at(7, 20, 5, 10))

    assert second.seat_index != first.seat_index


# --- 3 · thirty seconds on the same seat ------------------------------------


def test_the_same_seat_is_closed_to_her_for_thirty_seconds() -> None:
    """A padel court with one seat free, so there is nowhere else for her to go."""

    match = a_match()
    buyer = uuid4()
    for other in (uuid4(), uuid4(), uuid4()):
        match.take_seat(other, at=at(7, 19))
        match.pay_seat(other, at=at(7, 19))
    match.open_claim(buyer, at=at(7, 20))

    with pytest.raises(ClaimCoolingDown):
        match.open_claim(buyer, at=at(7, 20, 5, 29))


def test_the_same_seat_reopens_to_her_after_thirty_seconds() -> None:
    match = a_match()
    buyer = uuid4()
    for other in (uuid4(), uuid4(), uuid4()):
        match.take_seat(other, at=at(7, 19))
        match.pay_seat(other, at=at(7, 19))
    first = match.open_claim(buyer, at=at(7, 20))

    again = match.open_claim(buyer, at=first.expires_at + THIRTY_SECONDS)

    assert again.seat_index == first.seat_index


def test_the_cooldown_binds_only_the_player_who_let_the_seat_go() -> None:
    """Somebody else may take it the instant it frees. The thirty seconds break
    a tap-loop; they are not a penalty on the seat."""

    match = a_match()
    dawdler = uuid4()
    for other in (uuid4(), uuid4(), uuid4()):
        match.take_seat(other, at=at(7, 19))
        match.pay_seat(other, at=at(7, 19))
    first = match.open_claim(dawdler, at=at(7, 20))

    somebody_else = match.open_claim(uuid4(), at=first.expires_at)

    assert somebody_else.seat_index == first.seat_index


def test_a_claim_she_redeemed_leaves_no_cooldown_anybody_can_hit() -> None:
    """She is on the seat, so the question cannot arise for her — and the seat
    is taken, so it cannot arise for anybody else either."""

    match = a_match()
    buyer = uuid4()
    match.open_claim(buyer, at=at(7, 20))
    match.redeem_claim(buyer, at=at(7, 20, 1))

    with pytest.raises(PlayerAlreadyHoldsASeat):
        match.open_claim(buyer, at=at(7, 20, 1, 10))


# --- 4 and 5 · the cutoff is a deadline and not a trapdoor ------------------


def test_no_claim_may_be_started_after_the_join_cutoff() -> None:
    match = a_match()

    with pytest.raises(JoiningClosed):
        match.open_claim(uuid4(), at=JOIN_CUT)


def test_a_claim_may_be_started_up_to_the_instant_of_the_cutoff() -> None:
    match = a_match()

    claim = match.open_claim(uuid4(), at=JOIN_CUT - timedelta(seconds=1))

    assert claim.expires_at > JOIN_CUT


def test_a_running_claim_is_honoured_past_the_cutoff() -> None:
    """She tapped at 17:29 against a 17:30 cutoff and pays at 17:33.

    One comparison is the whole of the distinction between a deadline and a
    trapdoor, and this is it: ``redeem_claim`` does not read the cutoff at all.
    """

    match = a_match()
    buyer = uuid4()
    match.open_claim(buyer, at=at(8, 17, 29))

    seat = match.redeem_claim(buyer, at=at(8, 17, 33))

    assert seat.paid
    assert filled(match.as_record()) == 1


def test_a_claim_cannot_be_redeemed_after_its_own_five_minutes() -> None:
    match = a_match()
    buyer = uuid4()
    match.open_claim(buyer, at=at(8, 17, 29))

    with pytest.raises(NoLiveSeatClaim):
        match.redeem_claim(buyer, at=at(8, 17, 35))


def test_a_claim_cannot_be_redeemed_after_the_match_starts() -> None:
    """Past the start the aggregate refuses every seat move, and a claim is not
    an exception to that — it is honoured past a *cutoff*, not past a game."""

    match = a_match()
    buyer = uuid4()
    match.open_claim(buyer, at=at(8, 17, 29))

    with pytest.raises(MatchAlreadyStarted):
        match.redeem_claim(buyer, at=at(8, 18, 1))


def test_a_settled_match_takes_no_new_claims() -> None:
    match = a_match()
    match.cancel_by_club(at=at(7, 20))

    with pytest.raises(MatchAlreadySettled):
        match.open_claim(uuid4(), at=at(7, 20, 1))


# --- 6 · exclusivity, and the waves it silences -----------------------------


def test_a_seat_under_a_live_claim_is_spoken_for() -> None:
    match = a_match()
    claim = match.open_claim(uuid4(), at=at(7, 20))

    assert match.seats_under_claim(at(7, 20, 2)) == frozenset({claim.seat_index})


def test_a_lapse_puts_the_seat_back_with_no_write_at_all() -> None:
    """**This is *"a lapse resumes them"*, and the reason it needs no write.**

    The cascade asks whether a seat may be offered and gets a different answer
    five minutes later without anybody having touched the row. Nobody is told
    twice by that, because nothing was retracted and nothing is re-sent — the
    cascade keeps its own record of who it has already reached
    (``Raketa02/Raketa#82``).
    """

    match = a_match()
    claim = match.open_claim(uuid4(), at=at(7, 20))
    match.pull_events()

    assert match.seats_under_claim(claim.expires_at) == frozenset()
    assert kinds(match) == [], "the seat came back without a write"


def test_somebody_else_cannot_claim_a_seat_that_is_being_bought() -> None:
    match = a_match()
    for other in (uuid4(), uuid4(), uuid4()):
        match.take_seat(other, at=at(7, 19))
        match.pay_seat(other, at=at(7, 19))
    match.open_claim(uuid4(), at=at(7, 20))

    with pytest.raises(SeatAlreadyClaimed):
        match.open_claim(uuid4(), at=at(7, 20, 1))


def test_somebody_else_cannot_be_seated_on_a_seat_that_is_being_bought() -> None:
    """The invitation door is closed too, or the exclusivity is a promise the
    record does not keep. *Taken* and *being bought* are two different words."""

    match = a_match()
    for other in (uuid4(), uuid4(), uuid4()):
        match.take_seat(other, at=at(7, 19))
        match.pay_seat(other, at=at(7, 19))
    match.open_claim(uuid4(), at=at(7, 20))

    with pytest.raises(SeatAlreadyClaimed):
        match.take_seat(uuid4(), at=at(7, 20, 1))


def test_two_players_may_buy_two_different_seats_at_once() -> None:
    """Exclusivity is per seat and not per match, which is the whole reason a
    five-minute window is affordable at all."""

    match = a_match()
    first = match.open_claim(uuid4(), at=at(7, 20))
    second = match.open_claim(uuid4(), at=at(7, 20))

    assert first.seat_index != second.seat_index
    assert match.seats_under_claim(at(7, 20, 1)) == frozenset(
        {first.seat_index, second.seat_index}
    )


def test_a_match_whose_seats_are_all_spoken_for_says_so_and_is_not_full() -> None:
    match = a_match()
    for _ in range(4):
        match.open_claim(uuid4(), at=at(7, 20))

    with pytest.raises(SeatAlreadyClaimed):
        match.open_claim(uuid4(), at=at(7, 20, 1))
    assert not is_full(match.as_record())


def test_a_match_with_no_free_seat_says_full_rather_than_claimed() -> None:
    """Four different sentences for four different refusals — a card that said
    *somebody is buying that seat* about a full match would be a lie."""

    match = a_match()
    for player in (uuid4(), uuid4(), uuid4(), uuid4()):
        match.take_seat(player, at=at(7, 19))

    with pytest.raises(MatchIsFull):
        match.open_claim(uuid4(), at=at(7, 20))


def test_a_stale_claim_is_reaped_by_the_tap_it_would_otherwise_block() -> None:
    """**The write that would be blocked is the write that clears it.**

    A claim's five minutes are over at their own instant, but the row stays
    unended until somebody writes the receipt — and the record refuses two
    unended claims on one seat. So ``open_claim`` reaps first, and a player
    never waits on a scheduled look to be allowed to tap.
    """

    match = a_match()
    for other in (uuid4(), uuid4(), uuid4()):
        match.take_seat(other, at=at(7, 19))
        match.pay_seat(other, at=at(7, 19))
    dawdler = uuid4()
    lapsing = match.open_claim(dawdler, at=at(7, 20))
    match.pull_events()

    match.open_claim(uuid4(), at=at(7, 20, 6))

    assert lapsing.ended_at == lapsing.expires_at
    assert kinds(match) == [SeatClaimLapsed, SeatClaimOpened]


# --- 7 · a claim is never a seat state --------------------------------------


def test_a_claimed_seat_is_still_empty_in_every_count() -> None:
    """The glossary sentence, kept word for word: *there is no window in which a
    seat is taken and unpaid by the taker*. Nobody has taken a seat — they have
    taken the place in the queue in front of it."""

    match = a_match()
    match.open_claim(uuid4(), at=at(7, 20))
    record = match.as_record()

    assert filled(record) == 0
    assert held_unpaid(record) == 0
    assert not is_full(record)
    assert all(not seat.taken and not seat.paid for seat in record.seats)


def test_a_claim_moves_no_situation_for_anybody() -> None:
    """ADR-0081 refuses a thirty-seventh situation: a claim is about the viewer,
    and ADR-0040 fixes that ``waitlisted`` is the one situation only a viewer
    can be in. The kernel suite asserts this over the whole grid; here it is
    asserted through the aggregate, for the claimant herself."""

    match = a_match()
    buyer = uuid4()
    # Days out, so the match is plainly `forming` and the claim has the whole
    # of the ladder above it to move and does not.
    looked_at = at(5, 12)
    before = situation(match.as_record(), Viewer(), looked_at)

    match.open_claim(buyer, at=at(5, 11))

    assert situation(match.as_record(), Viewer(), looked_at) is before
    assert before is Situation.FORMING


def test_a_claimed_seat_earns_the_match_no_court() -> None:
    """A claim does nothing for the hold ladder, because the ladder counts money
    and a claim is the absence of it. Two paid seats earn a speculative hold;
    one paid and one being bought earn nothing."""

    match = a_match()
    payer = uuid4()
    match.take_seat(payer, at=at(7, 19))
    match.pay_seat(payer, at=at(7, 19))
    match.open_claim(uuid4(), at=at(7, 20))

    assert court_hold(match.as_record(), at(7, 20, 1)).kind.value == "none"


def test_redeeming_takes_and_pays_the_seat_in_one_move() -> None:
    """Never taken-and-then-paid: the held-and-unpaid state is an *invitation*,
    hours long and given by a person, and reaching it from here would be the
    collision ADR-0081 refuses."""

    match = a_match()
    buyer = uuid4()
    claim = match.open_claim(buyer, at=at(7, 20))
    match.pull_events()

    seat = match.redeem_claim(buyer, at=at(7, 20, 2))

    assert seat.index == claim.seat_index
    assert seat.player_id == buyer and seat.paid
    assert filled(match.as_record()) == 1
    assert held_unpaid(match.as_record()) == 0
    assert kinds(match) == [SeatClaimRedeemed, SeatTaken, SeatPaid]


def test_redeeming_takes_the_seat_she_was_promised() -> None:
    """Not *the first free one*: the seat she has been alone with for five
    minutes is hers, and handing her a different one would make the exclusivity
    meaningless the moment two people are paying at once."""

    match = a_match()
    first, second = uuid4(), uuid4()
    match.open_claim(first, at=at(7, 20))
    hers = match.open_claim(second, at=at(7, 20))

    seat = match.redeem_claim(second, at=at(7, 20, 1))

    assert seat.index == hers.seat_index


def test_redeeming_seats_her_where_she_claimed_and_not_on_the_first_free_seat() -> None:
    """The same rule where *the first free seat* and *hers* genuinely differ.

    In the test above the seat she did not claim is held out of reach by
    somebody else's live claim, so *the first free one* and *hers* are the same
    seat and the assertion passes either way. Here the seat she skipped is free
    and spoken for by nobody — she let it go herself, seconds ago, and only the
    cooldown moved her along. `take_seat` does not read the cooldown, so a
    redemption that asked for *the first free seat* would seat her back on the
    one she just abandoned.
    """

    match = a_match()
    buyer = uuid4()
    first = match.open_claim(buyer, at=at(7, 20))
    match.reap_lapsed_claims(at=at(7, 20, 5))
    hers = match.open_claim(buyer, at=at(7, 20, 5, 10))
    assert hers.seat_index != first.seat_index, "the cooldown moved her along"
    assert match.seat_at(first.seat_index).is_free, "and left that seat free"

    seat = match.redeem_claim(buyer, at=at(7, 20, 6))

    assert seat.index == hers.seat_index
    assert match.seat_at(first.seat_index).is_free


def test_a_player_with_no_claim_cannot_redeem_one() -> None:
    match = a_match()

    with pytest.raises(NoLiveSeatClaim):
        match.redeem_claim(uuid4(), at=at(7, 20, 1))


def test_a_claim_and_the_hole_it_could_fill_have_different_ids() -> None:
    """Three records can be named by one match, one seat and one instant — a
    vacancy, a departure and a claim — and each derives its id from a different
    prefix over the same three facts. Two of them colliding would be one row
    silently standing in for another."""

    match = a_match()
    leaver = uuid4()
    for player in (leaver, uuid4(), uuid4(), uuid4()):
        match.take_seat(player, at=at(7, 19))
        match.pay_seat(player, at=at(7, 19))
    quote = live_outcome(match.as_record(), at(7, 20))
    match.depart(leaver, quote=quote, at=at(7, 20))

    claim = match.open_claim(uuid4(), at=at(7, 20))
    [vacancy] = match.vacancies
    [departure] = match.departures

    assert vacancy.seat_index == departure.seat_index == claim.seat_index
    assert len({vacancy.id, departure.id, claim.id}) == 3


# --- the match ending underneath it -----------------------------------------


@pytest.mark.parametrize(
    "ending",
    [
        "cancel_by_club",
        "cancel_for_weather",
        "settle_incomplete_cancellation",
        "settle_checkpoint_cancellation",
        "lose_inventory",
    ],
)
def test_every_ending_closes_the_claims_it_leaves_behind(ending: str) -> None:
    """**A terminal match never wakes again**, so a claim on one would be a row
    nobody ever writes a receipt for — ADR-0081 asks for a record that *"must be
    reaped, must not leak"*, and this is the half a schedule cannot reach.

    It is announced under the same name as an ordinary expiry, because *"one
    rule ends a claim, whatever ended it"*: downstream both are refunded with
    cause ``claimLapsed``, and which one happened is answered by the
    cancellation announcing itself in the same breath.
    """

    match = a_match()
    claim = match.open_claim(uuid4(), at=at(7, 20))
    match.pull_events()

    getattr(match, ending)(at=at(7, 20, 2))

    assert claim.ended_at == at(7, 20, 2)
    announced = set(kinds(match))
    assert SeatClaimLapsed in announced
    assert announced != {SeatClaimLapsed}, "the ending announces itself too"


def test_an_ending_after_the_five_minutes_dates_the_lapse_at_the_expiry() -> None:
    """`min(at, expires_at)` — one rule, and it never post-dates a lapse."""

    match = a_match()
    claim = match.open_claim(uuid4(), at=at(7, 20))

    match.cancel_by_club(at=at(7, 20, 40))

    assert claim.ended_at == claim.expires_at == at(7, 20, 5)


# --- a private court is not a special case ----------------------------------


def test_a_private_court_s_opened_seat_is_bought_the_same_way() -> None:
    """*One rule for both doors* (ADR-0081): a seat offered to you and a seat you
    found yourself are the same race when it is the last one."""

    match = a_match(kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT)
    match.open_seats_to_the_marketplace(2, at=POSTED)
    buyer = uuid4()

    match.open_claim(buyer, at=at(7, 20))
    seat = match.redeem_claim(buyer, at=at(7, 20, 1))

    assert seat.paid
