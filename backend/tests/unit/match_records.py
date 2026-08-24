"""Match records for the ladder suite, and the grid the reachability walk runs.

Records are built from **offsets against one fixed start**, so a case reads as
*three seats paid, twenty hours out* rather than as two timestamps a reader has
to subtract. Every offset is a whole number of minutes and every stored instant
lands on a minute boundary, which is what lets the wake property scan minute by
minute and still be exact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import product
from typing import Any, Iterator

from app.kernel import (
    HoldPolicy,
    Instant,
    MatchKind,
    MatchRecord,
    OfferKind,
    PayModel,
    Seat,
    Sport,
    Vacancy,
    Viewer,
    hours,
    instant,
    minutes,
    shifted,
)

#: One fixed start every offset in this module is measured against.
START = instant(datetime(2026, 8, 22, 18, 30, tzinfo=timezone.utc))

#: Ninety minutes of padel, which is what the seeded world sells.
DURATION = minutes(90)


def at(offset: int) -> Instant:
    """An instant `offset` minutes from `START`; negative is before it."""

    return shifted(START, minutes(offset))


def seats(count: int, paid: int = 0, held: int = 0) -> tuple[Seat, ...]:
    """`count` seats of which `paid` are paid for and `held` are taken unpaid."""

    return tuple(
        Seat(taken=index < paid + held, paid=index < paid) for index in range(count)
    )


def a_match(
    *,
    sport: Sport = Sport.PADEL,
    paid: int = 0,
    held: int = 0,
    created: int = -4320,
    **facts: Any,
) -> MatchRecord:
    """A match at `START`, with `paid` seats paid and `held` taken but unpaid.

    `held_since` defaults to the creation moment whenever the seat count could
    have earned a speculative hold, because a soft hold with nothing to age from
    is a record the hold ladder refuses — deliberately, since reading it as *no
    age* would silently disable a club's cap.
    """

    players = 4 if sport in (Sport.PADEL, Sport.BADMINTON) else 2
    facts.setdefault("held_since", at(created) if paid >= 2 else None)
    return MatchRecord(
        sport=sport,
        start=START,
        duration=DURATION,
        created=at(created),
        seats=seats(players, paid, held),
        **facts,
    )


#: Five clubs' worth of policy, chosen for what each one changes: the default,
#: one whose window coincides with the platform backstop, one that caps a hold,
#: one that caps *and* publishes a demand model, and one that does not hold
#: speculatively at all.
POLICIES = (
    HoldPolicy(),
    HoldPolicy(window=hours(12)),
    HoldPolicy(window=hours(48), max_hold_age=hours(48)),
    HoldPolicy(max_hold_age=hours(48), prob_hold=True),
    HoldPolicy(max_hold_age=minutes(0)),
)

#: Clock positions, each one a minute either side of a threshold or squarely
#: between two: five days out, the twenty-four-hour commitment, the twelve-hour
#: backstop and far-tier lapse, the four-hour near-tier lapse and rescue, the
#: two-hour checkpoint, the door code, the start, mid-match, the end, past the
#: result window and past the day a card is kept.
OFFSETS = (
    -7200,
    -1441,
    -1440,
    -721,
    -720,
    -241,
    -240,
    -121,
    -120,
    -16,
    -15,
    -1,
    45,
    91,
    120,
    1560,
)

#: The four facts that decide what is happening to the **court**, one at a time.
COURT_FACTS: tuple[dict[str, Any], ...] = (
    {},
    {"court_locked": True},
    {"club_extended": True},
    {"released_at": at(-1000)},
)

#: The ten facts that decide what happened to the **match**, one at a time.
#: Inventory loss sets the club cancellation too, which is exactly why it has to
#: be tested above it.
#:
#: The two proposal rows are one axis and not two spellings of one: ADR-0048
#: settles them in **opposite** directions once silence answers — a lone proposal
#: stands and the match counts, two proposals leave it uncounted — so a grid
#: carrying only the first would never reach the second's name at all.
OUTCOMES: tuple[dict[str, Any], ...] = (
    {"inventory_lost": True, "club_cancelled": True},
    {"club_cancelled": True},
    {"weather": True},
    {"form_cancelled": True},
    {"checkpoint_cancelled": True},
    {"no_show": True},
    {"proposed_at": at(91), "proposals": 1},
    {"proposed_at": at(91), "proposals": 2},
    {"result_agreed": True},
    {"transferring": True},
)

#: The four shapes a court is bought in.
KINDS = (
    (MatchKind.OPEN, PayModel.SPLIT, 0),
    (MatchKind.PRIVATE, PayModel.SPLIT, 0),
    (MatchKind.PRIVATE, PayModel.SOLO, 0),
    (MatchKind.PRIVATE, PayModel.SPLIT, 1),
)

#: Every relationship a viewer can have to a match, including none at all.
VIEWERS = (
    None,
    Viewer(),
    Viewer(holds_seat=True),
    Viewer(on_standby=True),
    Viewer(offer=OfferKind.EXCLUSIVE),
    Viewer(offer=OfferKind.OPEN),
)


def _occupancies(players: int) -> list[tuple[int, int]]:
    """Every way `players` seats can be paid for and held unpaid."""

    return [
        (paid, held)
        for paid in range(players + 1)
        for held in range(players + 1 - paid)
    ]


def _custody(
    players: int, paid: int, held: int, offset: int
) -> list[tuple[Instant | None, tuple[Vacancy, ...]]]:
    """The commitment and vacancy combinations a writer can actually produce.

    Two consistency rules, honoured here rather than filtered afterwards:

    * a hole is a seat nobody is on, so a full match has no open vacancy;
    * **a committed match is either complete or short a seat somebody vacated**,
      since commitment needs a full match and the only way out of one is a
      departure.

    The second is the whole argument for deleting ``protectedCourt`` and
    ``protectedLate``. The ladder refuses that combination outright, so a
    generator that produced it would be asserting somebody else's bug.
    """

    empty = players - paid - held
    complete = paid == players
    vacancies: list[tuple[Vacancy, ...]] = (
        [()]
        if not empty
        else [(), (Vacancy(at(offset - 60)),), (Vacancy(at(offset - 1900)),)]
    )
    out: list[tuple[Instant | None, tuple[Vacancy, ...]]] = []
    for open_vacancies in vacancies:
        out.append((None, open_vacancies))
        if complete or open_vacancies:
            out.append((at(-1440), open_vacancies))
    return out


def _build(
    sport: Sport,
    players: int,
    paid: int,
    held: int,
    offset: int,
    created: int,
    policy: HoldPolicy,
    kind: tuple[MatchKind, PayModel, int],
    committed: Instant | None,
    open_vacancies: tuple[Vacancy, ...],
    facts: dict[str, Any],
) -> tuple[MatchRecord, Instant]:
    match_kind, pay_model, open_seats = kind
    return (
        MatchRecord(
            sport=sport,
            start=START,
            duration=DURATION,
            created=at(created),
            seats=seats(players, paid, held),
            policy=policy,
            kind=match_kind,
            pay_model=pay_model,
            open_seats=open_seats,
            held_since=at(created) if paid >= 2 else None,
            committed_at=committed,
            open_vacancies=open_vacancies,
            **facts,
        ),
        at(offset),
    )


def grid() -> Iterator[tuple[MatchRecord, Instant]]:
    """Fresh records over club × occupancy × clock × court × custody, with a now.

    Three passes rather than one product, because the axes do not interact:
    what is happening to a **court** is crossed against everything, what a
    **private** court is doing needs no clubs and no flags, and what has
    happened to a **match** short-circuits the ladder in its first five rungs and
    needs neither.
    """

    for sport in (Sport.PADEL, Sport.TENNIS):
        players = 4 if sport is Sport.PADEL else 2
        for policy, offset, (paid, held), created, facts in product(
            POLICIES, OFFSETS, _occupancies(players), (-4320, -1200), COURT_FACTS
        ):
            for committed, vacancies in _custody(players, paid, held, offset):
                yield _build(
                    sport,
                    players,
                    paid,
                    held,
                    offset,
                    created,
                    policy,
                    KINDS[0],
                    committed,
                    vacancies,
                    facts,
                )

        for kind, offset, (paid, held) in product(
            KINDS[1:], OFFSETS, _occupancies(players)
        ):
            yield _build(
                sport,
                players,
                paid,
                held,
                offset,
                -4320,
                POLICIES[0],
                kind,
                None,
                (),
                {},
            )

        for facts, offset, (paid, held) in product(
            OUTCOMES, OFFSETS, _occupancies(players)
        ):
            for committed, vacancies in _custody(players, paid, held, offset):
                yield _build(
                    sport,
                    players,
                    paid,
                    held,
                    offset,
                    -4320,
                    POLICIES[0],
                    KINDS[0],
                    committed,
                    vacancies,
                    facts,
                )
