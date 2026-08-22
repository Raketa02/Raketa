"""The ladder, rung by rung, asserted as **names**.

Every case here is a row: a record, a viewer, a clock, and the name the resolver
must answer with. Nothing asserts a sentence, because no sentence exists on this
side of the wire — copy is the client's thirty-six-row table
(``docs/adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md``,
``docs/adr/0075-the-second-table-is-unpaid-and-the-first-ships-in-english.md``),
and a backend test quoting one would be the second place a wording lives.

**The order of the ladder is the specification**
(``docs/adr/0040-one-ladder-resolves-a-situation.md``), so a third of these rows
exist only to pin an ordering: they are records that satisfy *two* rungs, and
they fail the moment the rungs are swapped. The four load-bearing orderings the
state-table research measured against the prototype
(``docs/specs/now/research/state-table.md`` §6.4) are each a row here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pytest

from app.kernel import (
    HoldPolicy,
    Instant,
    InvariantViolated,
    MatchKind,
    MatchRecord,
    OfferKind,
    PayModel,
    Seat,
    Situation,
    Sport,
    Vacancy,
    Viewer,
    court_hold,
    hours,
    instant,
    is_held,
    minutes,
    situation,
)
from tests.unit.match_records import a_match, at, seats

#: A club that caps how long a speculative hold may sit, which is the only way
#: to reach the first of the two amendments.
CAPPING = HoldPolicy(window=hours(48), max_hold_age=hours(48))

#: A club that caps *and* publishes a demand model, which is the only way to
#: reach the second.
EXTENDING = HoldPolicy(max_hold_age=hours(48), prob_hold=True)

IN_THE_MATCH = Viewer(holds_seat=True)
STANDBY = Viewer(on_standby=True)
OFFERED = Viewer(offer=OfferKind.EXCLUSIVE)
OPENED = Viewer(offer=OfferKind.OPEN)


@dataclass(frozen=True)
class Row:
    """One record, one viewer, one clock, one name."""

    why: str
    record: MatchRecord
    viewer: Viewer | None
    now: Instant
    expected: Situation


def row(
    why: str,
    *,
    at_offset: int,
    expected: Situation,
    viewer: Viewer | None = None,
    **facts: object,
) -> Row:
    return Row(why, a_match(**facts), viewer, at(at_offset), expected)  # type: ignore[arg-type]


#: Rungs 1-4. Every cancellation, and the two orderings inside the group that
#: the research measured: inventory loss sets the club cancellation too, and
#: `formCancelled` beats `checkpointCancelled`.
CANCELLED = (
    row(
        "inventory loss is named rather than reported as weather",
        at_offset=-720,
        paid=2,
        inventory_lost=True,
        club_cancelled=True,
        weather=True,
        form_cancelled=True,
        checkpoint_cancelled=True,
        expected=Situation.INVENTORY_LOST,
    ),
    row(
        "the club cancelled",
        at_offset=-720,
        paid=2,
        club_cancelled=True,
        expected=Situation.CANCELLED_CLUB,
    ),
    row(
        "weather is the club's cancellation, told the same way",
        at_offset=-720,
        paid=2,
        weather=True,
        expected=Situation.CANCELLED_CLUB,
    ),
    row(
        "it never filled, and that beats the checkpoint",
        at_offset=-60,
        paid=2,
        form_cancelled=True,
        checkpoint_cancelled=True,
        expected=Situation.CANCELLED_INCOMPLETE,
    ),
    row(
        "the seat was never refilled",
        at_offset=-60,
        paid=3,
        checkpoint_cancelled=True,
        expected=Situation.CANCELLED_CHECKPOINT,
    ),
    row(
        "a club cancelling after the start reads cancelled, because nobody played",
        at_offset=120,
        paid=4,
        club_cancelled=True,
        expected=Situation.CANCELLED_CLUB,
    ),
)

#: Rung 5. Six names off one clock, and the two precedences inside it: a no-show
#: beats an agreed score, and an unscored match closes at the entry deadline.
PLAYED = (
    row(
        "somebody who paid did not turn up, whatever else is on the table",
        at_offset=120,
        paid=4,
        no_show=True,
        score_proposed=True,
        result_agreed=True,
        expected=Situation.PLAYED_NO_SHOW,
    ),
    row(
        "played a player short",
        at_offset=120,
        paid=3,
        expected=Situation.PLAYED_SHORT,
    ),
    row(
        "a score everybody agreed",
        at_offset=120,
        paid=4,
        result_agreed=True,
        expected=Situation.COMPLETED,
    ),
    row(
        "past the entry deadline: an evening, never evidence",
        at_offset=1560,
        paid=4,
        expected=Situation.PLAYED_NO_SCORE,
    ),
    row(
        "a score is on the table and the deadline is still running",
        at_offset=120,
        paid=4,
        score_proposed=True,
        expected=Situation.CONFIRM_RESULT,
    ),
    row(
        "played, and nobody has said what happened",
        at_offset=91,
        paid=4,
        expected=Situation.NEEDS_RESULT,
    ),
    row(
        "a score before the last point is ignored",
        at_offset=-1,
        paid=4,
        score_proposed=True,
        expected=Situation.READY,
    ),
    row(
        "a no-show flag before the match has no effect either",
        at_offset=-1,
        paid=4,
        no_show=True,
        expected=Situation.READY,
    ),
)

#: Rungs 6-7. The three names only a viewer can be in, and the two orderings
#: that make standby worth joining and a seat-holder immune to both.
VIEWER_RUNGS = (
    row(
        "a seat is being held for her",
        at_offset=-720,
        paid=1,
        viewer=OFFERED,
        expected=Situation.SEAT_OFFERED,
    ),
    row(
        "a seat just opened and it is a race",
        at_offset=-720,
        paid=1,
        viewer=OPENED,
        expected=Situation.SEAT_OPENED,
    ),
    row(
        "the offer beats the queue that produced it",
        at_offset=-720,
        paid=1,
        viewer=Viewer(on_standby=True, offer=OfferKind.OPEN),
        expected=Situation.SEAT_OPENED,
    ),
    row(
        "queueing for a seat rather than holding one",
        at_offset=-720,
        paid=1,
        viewer=STANDBY,
        expected=Situation.WAITLISTED,
    ),
    row(
        "a seat she holds beats a queue she is also on",
        at_offset=-7200,
        paid=1,
        viewer=Viewer(holds_seat=True, on_standby=True),
        expected=Situation.FORMING,
    ),
    row(
        "a seat she holds beats an offer somebody sent her too",
        at_offset=-7200,
        paid=1,
        viewer=Viewer(holds_seat=True, offer=OfferKind.OPEN),
        expected=Situation.FORMING,
    ),
    row(
        "the played group is above all three: a standby player is not asked to "
        "enter a score by being moved off the match's own situation",
        at_offset=120,
        paid=4,
        viewer=STANDBY,
        expected=Situation.NEEDS_RESULT,
    ),
)

#: Rung 8. A private court is a different money model, and `privateFull` is the
#: rung ADR-0072 gave it: the moment the owner stops carrying the court.
PRIVATE = (
    row(
        "seats opened to the marketplace",
        at_offset=-720,
        paid=1,
        kind=MatchKind.PRIVATE,
        open_seats=1,
        expected=Situation.PRIVATE_OPEN,
    ),
    row(
        "every share paid, so the guarantee is discharged",
        at_offset=-720,
        paid=4,
        kind=MatchKind.PRIVATE,
        expected=Situation.PRIVATE_FULL,
    ),
    row(
        "shares still outstanding, and the owner carries them",
        at_offset=-720,
        paid=2,
        kind=MatchKind.PRIVATE,
        expected=Situation.PRIVATE_PARTIAL,
    ),
    row(
        "the owner bought the court outright",
        at_offset=-720,
        paid=1,
        kind=MatchKind.PRIVATE,
        pay_model=PayModel.SOLO,
        expected=Situation.PRIVATE_RESERVED,
    ),
    row(
        "a private court is above the full group, so a complete solo booking "
        "still reads as the owner's rather than as a marketplace match",
        at_offset=-720,
        paid=4,
        kind=MatchKind.PRIVATE,
        pay_model=PayModel.SOLO,
        expected=Situation.PRIVATE_RESERVED,
    ),
)

#: Rung 9. A committed match that lost somebody, and the money still moving.
RECOVERY = (
    row(
        "a named person is taking the seat",
        at_offset=-7200,
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-7260)),),
        transferring=True,
        expected=Situation.REPLACEMENT_TRANSFER,
    ),
    row(
        "past the checkpoint and still short",
        at_offset=-60,
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-1000)),),
        expected=Situation.RESCUE_LATE,
    ),
    row(
        "inside the rescue window",
        at_offset=-200,
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-1000)),),
        expected=Situation.RESCUE,
    ),
    row(
        "a replacement is being looked for",
        at_offset=-7200,
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-7260)),),
        expected=Situation.REPLACEMENT,
    ),
    row(
        "a singles court starts looking two hours sooner than a doubles one",
        sport=Sport.TENNIS,
        at_offset=-300,
        paid=1,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-1000)),),
        expected=Situation.RESCUE,
    ),
    row(
        "the same clock on a doubles court is still only a replacement",
        at_offset=-300,
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-1000)),),
        expected=Situation.REPLACEMENT,
    ),
)

#: Rung 10. Somebody left before commitment, and the twenty-four hours that make
#: the rung terminate instead of pinning a match for ever.
UNCOMMITTED_DEPARTURE = (
    row(
        "a court is still held over the hole",
        at_offset=-7200,
        paid=2,
        open_vacancies=(Vacancy(at(-7260)),),
        expected=Situation.PROTECTED_BACK,
    ),
    row(
        "no court is held over it",
        at_offset=-7200,
        paid=1,
        open_vacancies=(Vacancy(at(-7260)),),
        expected=Situation.FORMING_BACK,
    ),
    row(
        "a day later it is an ordinary forming match again",
        at_offset=-7200,
        paid=1,
        open_vacancies=(Vacancy(at(-8700)),),
        expected=Situation.FORMING,
    ),
    row(
        "the newest hole is the one that describes the match, not the oldest",
        at_offset=-7200,
        paid=1,
        open_vacancies=(Vacancy(at(-8700)), Vacancy(at(-7260))),
        expected=Situation.FORMING_BACK,
    ),
)

#: Rung 11. Complete, and the three ways a complete match can be described.
COMPLETE = (
    row(
        "fifteen minutes out, and the door code is worth showing",
        at_offset=-15,
        paid=4,
        expected=Situation.READY,
    ),
    row(
        "it filled after its own deadline and committed on the spot",
        at_offset=-120,
        paid=4,
        policy=CAPPING,
        committed_at=at(-1440),
        expected=Situation.CONFIRMED_ON_FILL,
    ),
    row(
        "it committed at the deadline, as planned",
        at_offset=-120,
        paid=4,
        committed_at=at(-1440),
        expected=Situation.CONFIRMED,
    ),
    row(
        "complete, and not committed yet",
        at_offset=-120,
        paid=4,
        expected=Situation.FULL,
    ),
    row(
        "full beats the court group: a complete group has a better thing to "
        "hear than what the club is doing with the court",
        at_offset=-120,
        paid=4,
        court_locked=True,
        expected=Situation.FULL,
    ),
)

#: Rungs 12-17. The court group, the two halves of `formingLate`, and forming.
FORMING_GROUP = (
    row(
        "posted after its own deadline, with a court held",
        at_offset=-1000,
        paid=2,
        created=-1400,
        expected=Situation.FORMING_LATE_HELD,
    ),
    row(
        "posted after its own deadline, with no court held",
        at_offset=-700,
        paid=2,
        created=-1400,
        expected=Situation.FORMING_LATE,
    ),
    row(
        "the club committed a court by hand",
        at_offset=-7200,
        paid=1,
        court_locked=True,
        expected=Situation.CLUB_HELD,
    ),
    row(
        "two paid seats, and still more than twelve hours out",
        at_offset=-7200,
        paid=2,
        expected=Situation.HELD_SOFT,
    ),
    row(
        "one seat short, and still more than four hours out",
        at_offset=-300,
        paid=3,
        expected=Situation.HELD_SOFT,
    ),
    row(
        "the court went back on sale and there is still a group to tell",
        at_offset=-700,
        paid=2,
        released_at=at(-1000),
        expected=Situation.HELD_RELEASED,
    ),
    row(
        "somebody holds a seat nobody has paid for",
        at_offset=-7200,
        paid=0,
        held=1,
        expected=Situation.FORMING_HELD,
    ),
    row(
        "past the deadline, and nothing else to say",
        at_offset=-700,
        paid=2,
        expected=Situation.FORMING_LATE,
    ),
    row(
        "the club is still selling this slot",
        at_offset=-7200,
        paid=0,
        expected=Situation.FORMING,
    ),
)

#: W1-W2. The club's two amendments, applied after the ladder rather than inside
#: it, so a court state can never relabel a match that is over.
AMENDMENTS = (
    row(
        "the club took back a hold that had stopped earning itself",
        at_offset=-721,
        paid=2,
        policy=CAPPING,
        expected=Situation.HELD_STALE,
    ),
    row(
        "the club held longer than the ladder promised",
        at_offset=-700,
        paid=2,
        policy=EXTENDING,
        club_extended=True,
        expected=Situation.HELD_EXTENDED,
    ),
    row(
        "a stale hold on a cancelled match still reads as a cancellation",
        at_offset=-721,
        paid=2,
        policy=CAPPING,
        club_cancelled=True,
        expected=Situation.CANCELLED_CLUB,
    ),
    row(
        "an extension on a played match still reads as played",
        at_offset=120,
        paid=2,
        policy=EXTENDING,
        club_extended=True,
        expected=Situation.PLAYED_SHORT,
    ),
)

THE_LADDER = (
    *CANCELLED,
    *PLAYED,
    *VIEWER_RUNGS,
    *PRIVATE,
    *RECOVERY,
    *UNCOMMITTED_DEPARTURE,
    *COMPLETE,
    *FORMING_GROUP,
    *AMENDMENTS,
)


@pytest.mark.parametrize("case", THE_LADDER, ids=lambda case: case.why)
def test_the_ladder_resolves_the_name_the_row_claims(case: Row) -> None:
    assert situation(case.record, case.viewer, case.now) is case.expected


def test_every_row_is_a_name_and_never_a_sentence() -> None:
    """The table above may only claim members of the enumeration.

    Cheap, and it is the claim the ACs make about the shape of this suite: a row
    asserting a sentence would be a wording living on the wrong side of the wire.
    """

    assert all(isinstance(case.expected, Situation) for case in THE_LADDER)


def test_the_table_reaches_every_rung_of_the_ladder() -> None:
    """A row per name, so no rung is specified by prose alone.

    The reachability walk proves each name is *producible*; this proves each one
    was **claimed** by hand, from a record a reader can read.
    """

    claimed = {case.expected for case in THE_LADDER}
    assert claimed == set(Situation), sorted(
        item.value for item in set(Situation) - claimed
    )


# ---------------------------------------------------------------------------
# The four defects of the published ladder, asserted rather than documented.
# ---------------------------------------------------------------------------


def test_the_two_impossible_names_are_not_in_the_enumeration() -> None:
    """`protectedCourt` and `protectedLate` produce nothing because they are gone."""

    values = {member.value for member in Situation}
    assert "protectedCourt" not in values
    assert "protectedLate" not in values


def test_the_fact_combination_behind_them_is_refused_rather_than_named() -> None:
    """A committed match that is neither complete nor short a vacated seat.

    No writer produces it — commitment needs a full match, and the only way out
    of one is a departure, which leaves a hole. Reaching it means something
    upstream has lost track of a seat, so it raises instead of resolving to a
    name that would tell four people their court is safe.
    """

    lost_a_seat_without_a_hole = a_match(paid=3, committed_at=at(-1440))
    with pytest.raises(InvariantViolated, match="hard court hold"):
        situation(lost_a_seat_without_a_hole, None, at(-1000))


def test_forming_late_never_means_a_court_is_held() -> None:
    """The half of the split that says *no court*, over every clock it can hold at."""

    late = a_match(paid=2, created=-1400)
    for offset in range(-1440, 0, 7):
        moment = at(offset)
        if situation(late, None, moment) is Situation.FORMING_LATE:
            assert not is_held(court_hold(late, moment))


def test_forming_late_held_always_means_a_court_is_held() -> None:
    late = a_match(paid=2, created=-1400)
    for offset in range(-1440, 0, 7):
        moment = at(offset)
        if situation(late, None, moment) is Situation.FORMING_LATE_HELD:
            assert is_held(court_hold(late, moment))


def test_a_refilled_match_cannot_carry_the_hole_it_no_longer_has() -> None:
    """The recovery rung terminates because the record cannot express the pin.

    The prototype's defect was a flag nothing cleared: a match refilled by an
    ordinary join stayed in the recovery group for ever, and at 4 of 4 told
    everybody a seat was missing. Here more holes than empty seats is refused at
    the door, so *committed, complete, and still recovering* has no spelling.
    """

    with pytest.raises(InvariantViolated, match="open vacancies"):
        MatchRecord(
            sport=Sport.PADEL,
            start=at(0),
            duration=minutes(90),
            created=at(-4320),
            seats=seats(4, paid=4),
            committed_at=at(-1440),
            open_vacancies=(Vacancy(at(-1000)),),
        )


def test_the_recovery_rung_stops_firing_the_moment_the_hole_closes() -> None:
    short = a_match(
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(at(-1000)),),
    )
    refilled = a_match(paid=4, committed_at=at(-1440))

    assert situation(short, None, at(-200)) is Situation.RESCUE
    assert situation(refilled, None, at(-200)) is Situation.CONFIRMED


def test_an_uncommitted_departure_decays_on_its_own_clock() -> None:
    """The twenty-four hours the documents promised and nothing implemented."""

    left = a_match(paid=1, open_vacancies=(Vacancy(at(-8640)),))

    assert situation(left, None, at(-8639)) is Situation.FORMING_BACK
    assert situation(left, None, at(-7201)) is Situation.FORMING_BACK
    assert situation(left, None, at(-7200)) is Situation.FORMING


# ---------------------------------------------------------------------------
# Strictly `>`, and the flap it prevents.
# ---------------------------------------------------------------------------


def test_the_far_tier_lapses_at_its_moment_and_not_a_minute_before() -> None:
    two_paid = a_match(paid=2)

    assert situation(two_paid, None, at(-721)) is Situation.HELD_SOFT
    assert situation(two_paid, None, at(-720)) is Situation.FORMING_LATE


def test_the_near_tier_lapses_at_its_moment_and_not_a_minute_before() -> None:
    one_short = a_match(paid=3)

    assert situation(one_short, None, at(-241)) is Situation.HELD_SOFT
    assert situation(one_short, None, at(-240)) is Situation.FORMING_LATE


def test_a_match_on_the_twelve_hour_boundary_never_flaps() -> None:
    """Second by second across the far tier's lapse, each answer appears once.

    This is the whole of the `>` versus `>=` argument, and it is why every
    threshold in the kernel is an instant. Written against a floored minute
    count instead, ``T-12h-30s`` reads 719 minutes remaining and releases a hold
    that has not lapsed — then the next whole minute puts it back. A run that
    visits `heldSoft`, then `formingLate`, then `heldSoft` again fails here, and
    so does one that disagrees with itself at a single instant.
    """

    two_paid = a_match(paid=2)
    lapse = at(-720)
    seen: list[Situation] = []
    for second in range(-90, 91):
        moment = instant(lapse + timedelta(seconds=second))
        answer = situation(two_paid, None, moment)
        assert answer is situation(two_paid, None, moment)
        if not seen or seen[-1] is not answer:
            seen.append(answer)

    assert seen == [Situation.HELD_SOFT, Situation.FORMING_LATE]
    assert len(seen) == len(set(seen))


# ---------------------------------------------------------------------------
# The viewer, and what the resolver cannot say without one.
# ---------------------------------------------------------------------------


def test_the_seat_holder_and_the_bare_viewer_answer_what_no_viewer_answers() -> None:
    """A viewer with no relationship to the match changes nothing.

    The absolute form is *the same function with the parameter absent*, not a
    second derivation, so there is nothing for a consistency suite to catch.
    """

    for record in (
        a_match(paid=2),
        a_match(paid=4),
        a_match(paid=3, committed_at=at(-1440), open_vacancies=(Vacancy(at(-1000)),)),
        a_match(paid=1, kind=MatchKind.PRIVATE),
    ):
        for offset in (-7200, -700, -100, 120):
            moment = at(offset)
            absolute = situation(record, None, moment)
            assert situation(record, Viewer(), moment) is absolute
            assert situation(record, IN_THE_MATCH, moment) is absolute


def test_a_seat_paid_but_nobody_on_it_is_refused() -> None:
    with pytest.raises(InvariantViolated, match="paid seat"):
        Seat(taken=False, paid=True)
