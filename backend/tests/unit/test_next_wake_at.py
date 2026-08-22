"""The wake function agrees with the ladder, and it is checked rather than paired.

**A threshold cannot exist in the ladder and be missing from the schedule** is
the claim ADR-0076 makes and the timekeeper (``Raketa02/Raketa#72``) depends on:
it stores the answer as a column and hand-maintains no list of boundaries
anywhere. See
``docs/adr/0076-the-schedule-is-a-column-a-wake-is-a-look-and-there-is-no-list-of-boundaries.md``.

The kernel makes that true by construction — both halves read one list — so the
suite has to attack it from outside. Every probe instant below is computed **in
this file, from the raw thresholds, without calling the kernel's own
``deadlines``, ``hold_boundaries`` or ``_boundaries``**. A test that asked the
kernel where its boundaries were would agree with it about a boundary that was
missing from both.

The property, stated once: *if the situation differs at two instants, a wake
falls between them.* An extra wake is a look that finds nothing and costs a
query; a missing one is a card that stays wrong until somebody pulls to refresh.
"""

from __future__ import annotations

from itertools import islice

import pytest

from app.kernel import (
    HoldPolicy,
    Instant,
    MatchKind,
    MatchRecord,
    Situation,
    Sport,
    Vacancy,
    Viewer,
    hours,
    minutes,
    next_wake_at,
    shifted,
    situation,
)
from tests.unit.match_records import DURATION, START, a_match, at, grid

#: Every threshold this file knows about, spelled from the source rules rather
#: than read off the kernel. Minutes **before** the start, except where an
#: absolute instant is the only way to say it.
_COMMITMENT_BACKSTOP = 12 * 60
_RESCUE_SINGLES = 6 * 60
_RESCUE_DOUBLES = 4 * 60
_CHECKPOINT = 2 * 60
_DOOR_CODE_LEAD = 15
_HOLD_FAR = 12 * 60
_HOLD_NEAR = 4 * 60
_RESULT_WINDOW = 24 * 60
_VACANCY_DECAY = 24 * 60

#: How far either side of a probe the neighbourhood scan looks, in minutes.
_NEIGHBOURHOOD = 3

#: Every 97th record of the grid. A stride rather than a slice, so the sample
#: crosses every axis the generator varies instead of stopping inside the first.
_STRIDE = 97


def _thresholds(record: MatchRecord) -> list[Instant]:
    """Every instant this record's rules could possibly turn on.

    A generous superset: an instant here that no rung reads costs one extra
    comparison, and one missing from here is a change the walk below cannot see.
    """

    singles = record.sport in (Sport.TENNIS, Sport.SQUASH)
    before = [
        min(record.policy.window, _COMMITMENT_BACKSTOP),
        _RESCUE_SINGLES if singles else _RESCUE_DOUBLES,
        _CHECKPOINT,
        record.policy.join_cut,
        0,
        _DOOR_CODE_LEAD,
        _HOLD_FAR,
        _HOLD_NEAR,
        -record.duration,
        -(record.duration + _RESULT_WINDOW),
    ]
    found = [shifted(record.start, minutes(-span)) for span in before]

    found.append(record.created)
    for absolute in (record.committed_at, record.released_at, record.held_since):
        if absolute is not None:
            found.append(absolute)
    if record.held_since is not None and record.policy.max_hold_age is not None:
        found.append(shifted(record.held_since, record.policy.max_hold_age))
    for vacancy in record.open_vacancies:
        found.append(vacancy.vacated_at)
        found.append(shifted(vacancy.vacated_at, minutes(_VACANCY_DECAY)))
    return found


def _probes(record: MatchRecord) -> list[Instant]:
    """The thresholds, their immediate neighbourhoods, and the gaps between them.

    The neighbourhood is what catches a comparison written `>=` where it should
    be `>`; the midpoints are what catch a change that happens somewhere no
    threshold in this file names, which is the failure the whole test is for.
    """

    anchors = sorted(set(_thresholds(record)))
    probes = {
        shifted(anchor, minutes(step))
        for anchor in anchors
        for step in range(-_NEIGHBOURHOOD, _NEIGHBOURHOOD + 1)
    }
    for earlier, later in zip(anchors, anchors[1:], strict=False):
        probes.add(shifted(earlier, minutes((later - earlier).days * 1440 // 2)))
        probes.add(
            shifted(earlier, minutes(int((later - earlier).total_seconds() // 120)))
        )
    return sorted(probes)


def _sampled_records() -> list[MatchRecord]:
    seen: list[MatchRecord] = []
    for index, (record, _) in enumerate(grid()):
        if index % _STRIDE == 0:
            seen.append(record)
    return seen


SAMPLE = _sampled_records()

#: One record per shape whose boundaries are worth walking minute by minute.
#: Every one of them keeps its thresholds inside a few thousand minutes of the
#: start, so an exhaustive scan is affordable.
CURATED = (
    ("forming, nothing paid", a_match(paid=0, created=-1200)),
    ("one seat held and unpaid", a_match(paid=0, held=1, created=-1200)),
    ("two paid, the far tier", a_match(paid=2, created=-1200)),
    ("one short, the near tier", a_match(paid=3, created=-1200)),
    ("complete and uncommitted", a_match(paid=4, created=-1200)),
    (
        "complete and committed",
        a_match(paid=4, created=-1200, committed_at=at(-1440)),
    ),
    (
        "committed and short a seat somebody vacated",
        a_match(
            paid=3,
            created=-1200,
            committed_at=at(-1440),
            open_vacancies=(Vacancy(at(-1300)),),
        ),
    ),
    (
        "a hole left before commitment",
        a_match(paid=2, created=-1200, open_vacancies=(Vacancy(at(-1300)),)),
    ),
    (
        "the court went back on sale",
        a_match(paid=2, created=-1200, released_at=at(-1000)),
    ),
    (
        "a club that caps how long a hold may sit",
        a_match(paid=2, created=-1200, policy=HoldPolicy(max_hold_age=hours(12))),
    ),
    (
        "a club that extends a hold the ladder lapsed",
        a_match(
            paid=2,
            created=-1200,
            policy=HoldPolicy(max_hold_age=hours(48), prob_hold=True),
            club_extended=True,
        ),
    ),
    (
        "a club whose window is the platform backstop",
        a_match(paid=2, created=-1200, policy=HoldPolicy(window=hours(12))),
    ),
    (
        "a club that does not hold speculatively",
        a_match(paid=2, created=-1200, policy=HoldPolicy(max_hold_age=minutes(0))),
    ),
    ("a private court", a_match(paid=2, created=-1200, kind=MatchKind.PRIVATE)),
    (
        "a two-player sport, which has no soft tiers",
        a_match(sport=Sport.TENNIS, paid=1, created=-1200),
    ),
    ("posted after its own deadline", a_match(paid=2, created=-1400)),
)


@pytest.mark.parametrize("why, record", CURATED, ids=[why for why, _ in CURATED])
@pytest.mark.parametrize("viewer", (None, Viewer(on_standby=True)))
def test_every_minute_the_situation_changes_has_a_wake_at_or_before_it(
    why: str,
    record: MatchRecord,
    viewer: Viewer | None,
) -> None:
    """Minute by minute across the record's whole life, exhaustively.

    Exhaustive rather than sampled, because the thing being looked for is a
    boundary nobody thought of: a walk over the instants somebody listed cannot
    find one that is missing from the list.
    """

    first = min(_thresholds(record))
    last = max(_thresholds(record))
    step = minutes(1)

    moment = shifted(first, minutes(-60))
    answer = situation(record, viewer, moment)
    horizon = shifted(last, minutes(60))
    while moment < horizon:
        later = shifted(moment, step)
        after = situation(record, viewer, later)
        if after is not answer:
            wake = next_wake_at(record, moment)
            assert wake is not None, (
                f"{why}: {answer.value} became {after.value} and the record "
                "named no wake at all"
            )
            assert moment < wake <= later, (
                f"{why}: {answer.value} became {after.value} at {later}, and the "
                f"next wake was {wake}"
            )
        moment, answer = later, after


@pytest.mark.parametrize("viewer", (None, Viewer(holds_seat=True)))
def test_no_change_across_the_grid_happens_without_a_wake_before_it(
    viewer: Viewer | None,
) -> None:
    """The same property, over every shape the generator can build.

    Coarser in the clock and far wider in the record, which is the trade the
    exhaustive test above cannot make.
    """

    for record in SAMPLE:
        probes = _probes(record)
        answers = [situation(record, viewer, probe) for probe in probes]
        walked = list(zip(probes, answers, strict=True))
        for (earlier, before), (later, after) in zip(walked, walked[1:], strict=False):
            if before is after:
                continue
            wake = next_wake_at(record, earlier)
            assert wake is not None and earlier < wake <= later, (
                f"{before.value} became {after.value} between {earlier} and "
                f"{later}, and the next wake was {wake}"
            )


def test_the_sample_is_wide_enough_to_be_making_a_claim() -> None:
    assert len(SAMPLE) > 500
    assert len({situation(record, None, START) for record in SAMPLE}) > 5


def test_a_terminal_match_never_wakes_again() -> None:
    """The four cancellations, and nothing else, end the schedule.

    A played match is deliberately not terminal: `needsResult` still moves.
    """

    for fact in (
        "inventory_lost",
        "club_cancelled",
        "weather",
        "form_cancelled",
        "checkpoint_cancelled",
    ):
        cancelled = a_match(paid=2, **{fact: True})
        assert next_wake_at(cancelled, at(-7200)) is None

    played = a_match(paid=4)
    assert next_wake_at(played, at(91)) is not None


def test_a_wake_is_strictly_in_the_future() -> None:
    """A candidate exactly at `now` is not a future wake.

    Without the strict comparison the chain re-arms itself at the same instant
    for ever, and the worker spends the night looking at one match.
    """

    two_paid = a_match(paid=2)
    lapse = shifted(START, minutes(-_HOLD_FAR))

    assert next_wake_at(two_paid, shifted(lapse, minutes(-1))) == lapse
    assert next_wake_at(two_paid, lapse) is not None
    assert next_wake_at(two_paid, lapse) > lapse


def test_the_chain_of_wakes_terminates() -> None:
    """Follow every wake from the beginning; the record runs out of them.

    The published ladder had a recovery rung that never ended, because the fact
    that put a match in it was never cleared. A chain that does not terminate is
    the same defect seen from the schedule's side.
    """

    for _, record in CURATED:
        moment: Instant | None = shifted(min(_thresholds(record)), minutes(-60))
        steps = 0
        while moment is not None:
            later = next_wake_at(record, moment)
            if later is not None:
                assert later > moment
            moment = later
            steps += 1
            assert steps < 40, "the wake chain did not run out"


def test_the_candidate_set_moves_with_the_seat_count() -> None:
    """Which threshold applies depends on how many seats are paid.

    This is why the timekeeper recomputes the column on **every** write rather
    than once when the match is created: the same match wakes at a different
    hour after a third payment.
    """

    two_paid = a_match(paid=2)
    one_short = a_match(paid=3)
    past_the_commitment = at(-1000)

    assert next_wake_at(two_paid, past_the_commitment) == shifted(
        START, minutes(-_HOLD_FAR)
    )
    assert next_wake_at(one_short, past_the_commitment) == shifted(
        START, minutes(-_HOLD_NEAR)
    )


def test_a_late_wake_finds_what_an_on_time_one_would() -> None:
    """A wake is a look, not an instruction.

    The handler re-derives from the record, so arriving an hour after the
    threshold changes *when* we look and never *what we find*.
    """

    one_short = a_match(paid=3)
    lapse = shifted(START, minutes(-_HOLD_NEAR))

    on_time = situation(one_short, None, lapse)
    assert situation(one_short, None, lapse) is on_time
    assert on_time is Situation.FORMING_LATE


def test_the_result_deadline_is_a_boundary_the_schedule_carries() -> None:
    """Twenty-four hours after the last point, not thirty minutes (ADR-0048)."""

    played = a_match(paid=4)
    end = shifted(START, DURATION)

    assert situation(played, None, shifted(end, minutes(30))) is Situation.NEEDS_RESULT
    assert next_wake_at(played, shifted(end, minutes(30))) == shifted(
        end, minutes(_RESULT_WINDOW)
    )
    assert (
        situation(played, None, shifted(end, minutes(_RESULT_WINDOW)))
        is Situation.PLAYED_NO_SCORE
    )


def test_the_grid_the_sample_is_taken_from_is_still_being_walked() -> None:
    """A stride over a generator that yields nothing samples nothing, silently."""

    assert len(list(islice(grid(), 10))) == 10
