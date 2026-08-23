"""The departure screen's table: four rows, four standings, one live quote.

ADR-0086 prints **all four outcomes always**, each with a server-composed marker
of its standing — *"a table that quietly drops forfeited once it is unreachable
is also a table that never showed it while it was"*. The phone derives none of
it, so every claim below is about a value the server sends.

The three claims worth stating before reading the cases:

1. **The table agrees with the quote, always.** The row marked ``searching`` is
   ``live_outcome`` and never a second reading of the same clock — a table that
   could disagree with the quote would be a screen promising one thing and a
   write applying another. Asserted over a grid rather than at four instants.
2. **``stillPossible`` is not ``opens`` with the moment left out.** It exists
   because commitment is an **event**: on a match that has not filled the three
   money outcomes are a *fill* away, not a moment away, and naming a moment
   there would promise a turn that may never come.
3. **``forfeited`` is never spent.** There is nothing past it, and a match
   nobody fills lands there from any distance.
"""

from __future__ import annotations

from itertools import product

import pytest

from app.kernel import (
    HoldPolicy,
    InvariantViolated,
    MatchKind,
    Outcome,
    PayModel,
    Sport,
    deadlines,
    hours,
    live_outcome,
)
from app.modules.now.domain.departure import (
    OutcomeRow,
    commitment_deadline,
    outcome_table,
)
from app.modules.now.domain.vocabulary import (
    OUTCOME_STANDING_COUNT,
    OutcomeStanding,
)

from tests.unit.match_records import a_match, at

#: A minute either side of a threshold, so a boundary is asserted as a boundary.
A_MINUTE = 1

SEARCHING = OutcomeStanding.SEARCHING
OPENS = OutcomeStanding.OPENS
POSSIBLE = OutcomeStanding.STILL_POSSIBLE
SPENT = OutcomeStanding.SPENT


def committed(**facts):
    """A full, committed padel match — the only kind with four outcomes."""

    facts.setdefault("committed_at", at(-2880))
    return a_match(paid=4, **facts)


def forming(**facts):
    """A match that has not filled, so nothing about its money is decided."""

    return a_match(paid=2, **facts)


def converted(*, paid=4, **facts):
    """A private court sold by the share."""

    facts.setdefault("kind", MatchKind.PRIVATE)
    facts.setdefault("pay_model", PayModel.SPLIT)
    return a_match(paid=paid, **facts)


def standings(record, now) -> dict[Outcome, OutcomeRow]:
    return {row.outcome: row for row in outcome_table(record, now)}


# --- the enumeration --------------------------------------------------------


def test_the_enumeration_is_four_and_the_count_is_pinned():
    """A fifth standing is a decision somebody made in a diff."""

    assert len(OutcomeStanding) == OUTCOME_STANDING_COUNT == 4


def test_a_moment_rides_on_opens_and_on_no_other_standing():
    """The shape carries the rule, so a caller cannot get it wrong.

    A moment beside *spent* would be a moment nothing counts to, and a row that
    is *still possible* has none to give — which is precisely what distinguishes
    it from one that opens.
    """

    with pytest.raises(InvariantViolated):
        OutcomeRow(outcome=Outcome.FORFEITED, standing=SPENT, opens_at=at(0))
    with pytest.raises(InvariantViolated):
        OutcomeRow(outcome=Outcome.FORFEITED, standing=OPENS)


# --- the table is the whole set, in the quote's own order --------------------


def test_an_open_match_prints_all_four_in_the_order_they_arrive():
    """Ordered by the quote's timeline, so the table reads past-then-ahead."""

    assert [row.outcome for row in outcome_table(committed(), at(-2000))] == [
        Outcome.REVERSED,
        Outcome.REFUNDED_IN_FULL,
        Outcome.REFUNDED_HALF,
        Outcome.FORFEITED,
    ]


def test_a_private_court_prints_two_rows_and_they_are_the_reachable_two():
    """`CONTEXT.md` fixes that only those two are reachable there.

    The glossary being read, and not a second rule invented for this screen.
    """

    assert [row.outcome for row in outcome_table(converted(), at(-2000))] == [
        Outcome.REFUNDED_IN_FULL,
        Outcome.FORFEITED,
    ]


@pytest.mark.parametrize(
    "record",
    [committed(), forming(), converted(), converted(paid=2)],
    ids=["committed", "forming", "converted-full", "converted-partial"],
)
@pytest.mark.parametrize("offset", [-10_000, -2000, -700, -200, -60, 0, 30])
def test_exactly_one_row_is_ever_searching(record, offset):
    """The screen states one live outcome and never a set.

    A second searching row would make the refuse-if-worse rule ambiguous, and
    none at all would be a screen with no quote on it.
    """

    live = [
        row for row in outcome_table(record, at(offset)) if row.standing is SEARCHING
    ]
    assert len(live) == 1


@pytest.mark.parametrize(
    "record",
    [committed(), forming(), converted(), converted(paid=2)],
    ids=["committed", "forming", "converted-full", "converted-partial"],
)
@pytest.mark.parametrize("offset", [-10_000, -2000, -700, -200, -60, 0, 30])
def test_the_searching_row_is_the_quote_and_never_a_second_reading(record, offset):
    """The one claim the whole screen rests on, asserted over a grid.

    A table that could disagree with `live_outcome` would be a screen promising
    one thing and a write applying another — and the write is the one that wins.
    """

    now = at(offset)
    live = next(row for row in outcome_table(record, now) if row.standing is SEARCHING)
    assert live.outcome is live_outcome(record, now)


# --- an open match, tier by tier --------------------------------------------


def test_before_commitment_the_free_reversal_is_the_quote_and_nothing_is_spent():
    """A match that has not filled has bought nothing, so leaving is free.

    The three money outcomes are a **fill** away rather than a moment away, so
    every one of them is *still possible* and none of them names a moment.
    """

    rows = standings(forming(), at(-2000))

    assert rows[Outcome.REVERSED].standing is SEARCHING
    assert rows[Outcome.REFUNDED_IN_FULL].standing is POSSIBLE
    assert rows[Outcome.REFUNDED_HALF].standing is POSSIBLE
    assert rows[Outcome.FORFEITED].standing is POSSIBLE
    assert all(row.opens_at is None for row in rows.values())


def test_once_committed_the_reversal_is_spent_and_the_two_ahead_name_moments():
    """What she has passed, and what is ahead with the moment it arrives."""

    match = committed()
    when = deadlines(match)
    rows = standings(match, at(-2000))

    assert rows[Outcome.REVERSED].standing is SPENT
    assert rows[Outcome.REFUNDED_IN_FULL].standing is SEARCHING
    assert rows[Outcome.REFUNDED_HALF] == OutcomeRow(
        outcome=Outcome.REFUNDED_HALF, standing=OPENS, opens_at=when.rescue
    )
    assert rows[Outcome.FORFEITED] == OutcomeRow(
        outcome=Outcome.FORFEITED, standing=OPENS, opens_at=when.check
    )


def test_the_reversal_is_spent_the_instant_the_match_commits():
    """Commitment is one-way, so the free window never comes back."""

    match = committed()
    assert standings(match, at(-2000))[Outcome.REVERSED].standing is SPENT
    assert standings(forming(), at(-2000))[Outcome.REVERSED].standing is SEARCHING


def test_from_the_rescue_deadline_the_full_refund_is_spent_and_half_is_the_quote():
    match = committed()
    rows = standings(match, deadlines(match).rescue)

    assert rows[Outcome.REFUNDED_IN_FULL].standing is SPENT
    assert rows[Outcome.REFUNDED_HALF].standing is SEARCHING


def test_from_the_checkpoint_only_the_forfeit_is_left():
    match = committed()
    rows = standings(match, deadlines(match).check)

    assert rows[Outcome.REVERSED].standing is SPENT
    assert rows[Outcome.REFUNDED_IN_FULL].standing is SPENT
    assert rows[Outcome.REFUNDED_HALF].standing is SPENT
    assert rows[Outcome.FORFEITED].standing is SEARCHING


@pytest.mark.parametrize("offset", [-10_000, -2000, -700, -200, -60, 0, 30])
def test_the_forfeit_is_never_spent(offset):
    """There is nothing past it, and a match nobody fills lands there."""

    for record in (committed(), forming(), converted(), converted(paid=2)):
        assert standings(record, at(offset))[Outcome.FORFEITED].standing is not SPENT


def test_the_full_refund_is_spent_on_the_clock_even_if_the_match_never_committed():
    """Its window ends at the rescue deadline whatever the match does.

    A match that fills *after* it commits on the spot, and the leaver's best
    available outcome is then half — so *refunded in full* is genuinely behind
    her, and calling it *still possible* would be an over-promise.
    """

    match = forming()
    rows = standings(match, deadlines(match).rescue)

    assert rows[Outcome.REVERSED].standing is SEARCHING
    assert rows[Outcome.REFUNDED_IN_FULL].standing is SPENT
    assert rows[Outcome.REFUNDED_HALF].standing is POSSIBLE


def test_an_uncommitted_match_past_the_checkpoint_has_only_the_forfeit_ahead():
    match = forming()
    rows = standings(match, deadlines(match).check)

    assert rows[Outcome.REVERSED].standing is SEARCHING
    assert rows[Outcome.REFUNDED_HALF].standing is SPENT
    assert rows[Outcome.FORFEITED].standing is POSSIBLE


def test_a_singles_match_turns_earlier_because_its_rescue_window_opens_earlier():
    """The table reads the kernel's deadlines and holds no threshold of its own.

    A squash match is two seats, so its rescue window opens at a different
    instant from a padel match's — and the table turns there rather than at a
    number transcribed into this module.
    """

    singles = a_match(sport=Sport.SQUASH, paid=2, committed_at=at(-2880))
    assert deadlines(singles).rescue != deadlines(committed()).rescue

    assert (
        standings(singles, deadlines(singles).rescue)[Outcome.REFUNDED_HALF].standing
        is SEARCHING
    )
    assert standings(singles, at(-2000))[Outcome.REFUNDED_HALF] == OutcomeRow(
        outcome=Outcome.REFUNDED_HALF,
        standing=OPENS,
        opens_at=deadlines(singles).rescue,
    )


# --- a private court --------------------------------------------------------


def test_a_private_share_is_refundable_until_match_time_and_forfeits_after():
    court = converted()

    before = standings(court, at(-A_MINUTE))
    assert before[Outcome.REFUNDED_IN_FULL].standing is SEARCHING
    assert before[Outcome.FORFEITED] == OutcomeRow(
        outcome=Outcome.FORFEITED, standing=OPENS, opens_at=court.start
    )

    after = standings(court, at(0))
    assert after[Outcome.REFUNDED_IN_FULL].standing is SPENT
    assert after[Outcome.FORFEITED].standing is SEARCHING


def test_a_private_courts_table_never_mentions_the_rescue_tier():
    """The discount exists to save a court that would otherwise be lost."""

    for offset in (-10_000, -60, 0, 30):
        printed = {row.outcome for row in outcome_table(converted(), at(offset))}
        assert Outcome.REFUNDED_HALF not in printed
        assert Outcome.REVERSED not in printed


# --- the commitment deadline, as a moment -----------------------------------


def test_the_commitment_deadline_is_the_kernels_and_not_a_second_arithmetic():
    assert commitment_deadline(committed()) == deadlines(committed()).commit


def test_a_short_window_club_takes_the_platform_backstop():
    """The deadline is the *earlier* of the two, which is what `deadlines` says."""

    match = committed(policy=HoldPolicy(window=hours(6)))
    assert commitment_deadline(match) == at(-12 * 60)


def test_a_private_court_names_no_commitment_deadline_at_all():
    """The court was bought at booking, so there is no commitment to date.

    Absent rather than far away: *there is no such deadline* is the only thing
    the absence could mean here.
    """

    assert commitment_deadline(converted()) is None


# --- the table is total -----------------------------------------------------


@pytest.mark.parametrize(
    "record,offset",
    list(
        product(
            [committed(), forming(), converted(), converted(paid=2)],
            [-10_000, -2880, -2000, -1440, -700, -200, -60, -1, 0, 30, 200],
        )
    ),
)
def test_every_row_carries_a_standing_and_the_shape_agrees_with_it(record, offset):
    """No state of any match produces a row this table cannot describe."""

    for row in outcome_table(record, at(offset)):
        assert row.standing in OutcomeStanding
        assert (row.opens_at is not None) == (row.standing is OPENS)
