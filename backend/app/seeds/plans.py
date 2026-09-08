"""Arrange four games nobody has played, and plan them nought to three slots.

**A plan cannot be written into a database; it has to be agreed.** ADR-0029's
rule as every other layer here keeps it — the four plans below are written
through the three routes a player presses, into games opened by line-ups that
really completed, on courts built from searches that really showed the people
seated on them. **Four seeded plans, never four fixtures.**

**These are the first games this fixture arranges and does not play**, and that
is the whole reason the layer exists. Every game the played history writes
carries a moment somebody said they played, so every one of them is past its
entry window as far as a plan is concerned: *the game leaving ``AWAITING_ENTRY``
is the only thing that freezes the slots*, and a database made only of played
games can draw a plan card in exactly one state — frozen. So this layer sends
four more courts, answers every seat, and stops.

**Nought, one, two, three — and *nought* is a game with no plan at all.** A plan
is born by being used, so the empty state is not an empty record: it is a game
that appears in ``GET /games`` and nowhere in ``GET /plans``. It is seeded by
arranging a game and then deliberately writing nothing on it, which is the only
way that state exists.

**It writes in the present, unlike the played history.** A game arranged an hour
ago is a game with eight days left to be played in, which is what makes its slots
writable and its day row non-empty. The played history is the one layer that
writes in the past, and this is deliberately not it.

**Everything it costs is a tennis singles court, and the members were chosen so
that costs nothing else.** The four opponents already hold a Tennis rating from
their own draw — this layer declares no second sport and therefore does not feed
``SECOND_SPORT_BECAUSE_THEY_PLAYED``, so ``cohort.json`` does not move. And the
four games are **counted toward nothing**: a game still inside its entry window
is neither played nor a ghost, so no counterpart tally, no ``counted_games`` and
no run of form changes because these exist.

**Re-running writes nothing twice.** Every act here is idempotent for its own
reason: a game is looked for by its line-up before anything is sent, and a slot
write of the value already there records nothing by the platform's own rule —
which makes the second run of this layer the one that proves that rule end to
end.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from datetime import time as wall_time
from typing import final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_candidate_source,
    build_domain_event_store,
    build_event_publisher,
    build_plan_hold_query,
    build_plan_repository,
    build_planning_court,
    build_read_plans,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.plans.application.commands import (
    ReadPlansCommand,
    SetDayCommand,
    SetHourCommand,
    SetPlaceCommand,
)
from app.modules.plans.application.record_a_slot import SetDay, SetHour, SetPlace
from app.modules.plans.domain.plan import SLOTS, Plan
from app.modules.plans.domain.slots import PLATFORM_ZONE
from app.seeds.clock import FixedClock
from app.seeds.cohort import COHORT, Cohort
from app.seeds.games import (
    arrange_the_court,
    email_of,
    mode_of,
    player_of,
    the_game_already_there,
)
from app.seeds.paths import (
    ReadPaths,
    read_paths,
    the_ephemeral_store,
    tick_the_tail_to_catch_up,
)

#: How far ahead a seeded plan puts its day. **Two days**, which is inside the
#: horizon with room to spare and far enough that the agreed moment is still
#: ahead however long the run takes.
DAYS_AHEAD = 2

#: The hour a seeded plan agrees on, on the grid the platform offers.
AGREED_HOUR = wall_time(18, 0)

#: What a seeded plan writes in its *where* slot. **A note and never a court** —
#: it is a string this platform will never look up, geocode or reuse, and the
#: seed writes it the way a person would.
THE_PLACE = "Zabłocie Sport"


@final
@dataclass(frozen=True, slots=True)
class ArrangedGame:
    """One game this fixture arranges and nobody plays, and how far its plan got.

    **Handles and never ids**, like every other declaration here: an id is minted
    by the write path and a fresh database mints a different one.

    ``side_a[0]`` organised it, by position rather than in a field of its own,
    because the send is one person's act and the organiser's own seat is accepted
    from birth. That is ``PlayedGame``'s shape, and the two satisfy one
    ``Arrangement`` protocol so that *send a court and answer every seat* is
    written once.

    ``slots`` is **how many of the three this plan holds**, filled in ADR-0144's
    own order — *where · day · hour* — so the four rows walk the plan card from
    empty to complete. It is a count rather than three optional values because
    the order is the record's and a fixture must not be able to choose a
    different one.
    """

    sport: str
    side_a: tuple[str, ...]
    side_b: tuple[str, ...]
    slots: int

    def __post_init__(self) -> None:
        if not 0 <= self.slots <= SLOTS:
            raise ValueError(
                f"a plan at {self.slots} of {SLOTS} slots: there are three, and "
                f"filling the third is the whole of the completion."
            )

    @property
    def organiser(self) -> str:
        return self.side_a[0]

    @property
    def players(self) -> tuple[str, ...]:
        return self.side_a + self.side_b


#: The four games, and the four plans they carry.
#:
#: **Tennis singles, organised by the member the played history already
#: organises with**, which is the cheapest shape that reaches four distinct
#: pairs: a completed line-up releases its pair (``docs/adr/0142`` §1), so these
#: four courts leave nothing gated behind them.
#:
#: **The opponents are ring-a members who already hold a Tennis rating**, drawn
#: that way rather than declared into it. That is what keeps this layer out of
#: ``cohort.json``: ``SECOND_SPORT_BECAUSE_THEY_PLAYED`` feeds the *draw*, and a
#: row here that needed a second sport would move the committed population for a
#: fixture about slots.
ARRANGED_GAMES: tuple[ArrangedGame, ...] = (
    ArrangedGame(
        sport=Sport.TENNIS.value,
        side_a=("cohort-a-12",),
        side_b=("cohort-c-00",),
        slots=0,
    ),
    ArrangedGame(
        sport=Sport.TENNIS.value,
        side_a=("cohort-a-12",),
        side_b=("cohort-d-06",),
        slots=1,
    ),
    ArrangedGame(
        sport=Sport.TENNIS.value,
        side_a=("cohort-a-12",),
        side_b=("cohort-a-06",),
        slots=2,
    ),
    ArrangedGame(
        sport=Sport.TENNIS.value,
        side_a=("cohort-a-06",),
        side_b=("cohort-c-00",),
        slots=3,
    ),
)


class SeedPlanMissing(RuntimeError):
    """A plan state a screen has to draw is not in this database.

    Raised rather than reported, on this fixture's own rule: an assertion here is
    a claim about the **real read path**, so a shape that is missing is a card a
    developer is about to open and find empty.
    """


@final
@dataclass(frozen=True, slots=True)
class SeededPlans:
    """What this layer arranged and agreed, as lines for the report."""

    arranged: int
    plans: tuple[str, ...]


async def write_the_plans(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Cohort = COHORT,
) -> SeededPlans:
    """Arrange the four courts, fill their slots, and read every claim back.

    The tail is ticked first for the reason every layer that runs a search ticks
    it: a search reads the candidate index, and the index has not seen everything
    this run has written. ADR-0110 makes the tick safe and cheap to repeat.
    """

    await tick_the_tail_to_catch_up(session_factory, settings=settings)
    candidates = build_candidate_source(session_factory=session_factory)
    await candidates.refresh()

    async with the_ephemeral_store(settings) as redis:
        async with session_factory() as session:
            paths = await read_paths(
                session,
                settings=settings,
                candidates=candidates,
                cohort=cohort,
                now=now,
                redis=redis,
            )
            games = {
                declared: await _arrange(paths, declared, cohort)
                for declared in ARRANGED_GAMES
            }
            await _fill_the_slots(session, games, cohort, paths=paths, now=now)

    # **Re-read after the writes**, because what is asserted is what a screen
    # would draw and not what this function believes it wrote.
    async with session_factory() as session:
        drawn = await _every_plan_drawn(session, now=now, cohort=cohort)
    return SeededPlans(
        arranged=len(games),
        plans=_refuse_a_card_state_nobody_can_draw(drawn, games),
    )


# ---------------------------------------------------------------------------
# Arranging
# ---------------------------------------------------------------------------


async def _arrange(
    paths: ReadPaths, declared: ArrangedGame, cohort: Cohort
) -> UUID:
    """One game, sent and fully accepted, and **never entered**.

    The probe comes before the search, exactly as it does for a played game and
    for the lesson ``pairs.py`` paid for: once a court has been sent the pair is
    gated, so a run that searched first would fail its second pass with a message
    about a pool when what actually happened is that the first pass died between
    the send and the last acceptance.
    """

    sport = Sport(declared.sport)
    organiser = cohort.by_handle(declared.organiser)
    standing = await the_game_already_there(paths, declared, cohort)
    if standing is None:
        standing = await arrange_the_court(
            paths, declared, cohort, sport, organiser
        )
    if standing.played_at is not None:
        raise SeedPlanMissing(
            f"the game '{declared.organiser}' arranged against "
            f"{declared.side_b[0]} has been entered as played, so its slots are "
            f"frozen and the plan states this layer exists for are unreachable. "
            f"Nothing here enters a result; a run that found one has met a "
            f"database somebody else wrote in."
        )
    # The mode is read here rather than only inside the send, because it is what
    # decides whether the game is counted — and a friendly plan is the same plan,
    # so this is a check that the declaration is coherent rather than a rule.
    mode_of(paths, organiser, sport)
    return standing.id


# ---------------------------------------------------------------------------
# Agreeing
# ---------------------------------------------------------------------------


async def _fill_the_slots(
    session: AsyncSession,
    games: dict[ArrangedGame, UUID],
    cohort: Cohort,
    *,
    paths: ReadPaths,
    now: Instant,
) -> None:
    """Write each plan up to its declared slot count, in ADR-0144's own order.

    **Through the three use cases a request runs**, so a seeded plan has the
    event stream and the outbox rows a real one has — which is what puts the
    three system lines in the room the acceptances already opened.

    **The writer alternates between the two people on the court**, because *any
    member may fill or change any slot* is the rule the card is built on and a
    plan every slot of which was written by the organiser would draw one side of
    it.
    """

    clock = FixedClock(at=now)
    plans = build_plan_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    court = build_planning_court(session)
    holds = build_plan_hold_query(session)
    uow = build_unit_of_work(session)
    # **One repository for all three writes**, because it remembers the stream
    # versions it has loaded: three over one session would be three answers to
    # *what version have I seen*, and the second append would expect version 0 of
    # a stream it had never read.
    place = SetPlace(plans=plans, court=court, holds=holds, uow=uow, clock=clock)
    day = SetDay(plans=plans, court=court, holds=holds, uow=uow, clock=clock)
    hour = SetHour(plans=plans, court=court, holds=holds, uow=uow, clock=clock)
    agreed_day = _the_agreed_day(now)

    for declared, game_id in games.items():
        organiser = player_of(paths, cohort, declared.organiser)
        opponent = player_of(paths, cohort, declared.side_b[0])
        if declared.slots >= 1:
            await place.execute(
                SetPlaceCommand(
                    game_id=game_id, player_id=organiser, place=THE_PLACE
                )
            )
        if declared.slots >= 2:
            await day.execute(
                SetDayCommand(
                    game_id=game_id, player_id=opponent, day=agreed_day
                )
            )
        if declared.slots >= 3:
            await hour.execute(
                SetHourCommand(
                    game_id=game_id, player_id=organiser, hour=AGREED_HOUR
                )
            )


def _the_agreed_day(now: Instant) -> date:
    """The local day a seeded plan names.

    Read in the platform zone, because that is the zone the plan itself converts
    through — a day computed off the UTC date would be the wrong day for two
    hours of every evening.
    """

    return now.astimezone(PLATFORM_ZONE).date() + timedelta(days=DAYS_AHEAD)


# ---------------------------------------------------------------------------
# The claims, read off the real path
# ---------------------------------------------------------------------------


async def _every_plan_drawn(
    session: AsyncSession, *, now: Instant, cohort: Cohort
) -> dict[UUID, Plan]:
    """Every plan these games carry, read through ``GET /plans``' own use case.

    **Read as a player and never off the table.** The read is scoped to the games
    the reader is on the court of, so a fixture that queried the store would be
    asserting something no screen can draw — and reading as *each* organiser is
    what makes that scoping the thing under test rather than a detail routed
    around.
    """

    reader = build_read_plans(session, clock=FixedClock(at=now))
    drawn: dict[UUID, Plan] = {}
    for handle in sorted({declared.organiser for declared in ARRANGED_GAMES}):
        found = await reader.execute(
            ReadPlansCommand(reader_id=await _player_id(session, cohort, handle))
        )
        drawn.update({plan.game_id: plan for plan in found})
    return drawn


async def _player_id(
    session: AsyncSession, cohort: Cohort, handle: str
) -> UUID:
    """The id the write path minted for this member. Looked up by address."""

    email = email_of(cohort, handle)
    found = await build_user_repository(session).get_by_email(email)
    if found is None:
        raise SeedPlanMissing(
            f"'{email}' organises an arranged game and is not in this "
            f"database. The assertions read the same database the run wrote."
        )
    return found.id


def _refuse_a_card_state_nobody_can_draw(
    drawn: dict[UUID, Plan], games: dict[ArrangedGame, UUID]
) -> tuple[str, ...]:
    """*Nought, one, two and three slots are all in this database.*

    **The absence is asserted as hard as the presence**, and that is the point of
    the nought row: a plan at no slots is a game with **no plan**, so the claim it
    makes is that the game is arranged, readable, and missing from the plan list.
    A layer that quietly reached three of the four states would read as having
    reached four, and the person it misled would be the one about to build the
    card.
    """

    lines: list[str] = []
    for declared, game_id in games.items():
        plan = drawn.get(game_id)
        reached = 0 if plan is None else plan.slot_count
        if reached != declared.slots:
            raise SeedPlanMissing(
                f"the game against '{declared.side_b[0]}' was declared at "
                f"{declared.slots} slot(s) and its plan draws {reached}. "
                + (
                    "A plan is born by being used, so nought slots means the "
                    "game carries no plan at all and must be absent from "
                    "`GET /plans` — a row of three nulls is a state this "
                    "platform cannot produce."
                    if declared.slots == 0
                    else "The three slot writes go through the routes a player "
                    "presses, so a count that has moved is a refusal one of them "
                    "answered with."
                )
            )
        lines.append(_line_for(declared, plan))
    _refuse_a_run_that_reached_the_same_state_four_times(games)
    return tuple(lines)


def _refuse_a_run_that_reached_the_same_state_four_times(
    games: dict[ArrangedGame, UUID],
) -> None:
    """The four are four **states**, not four rows.

    Declared here rather than assumed, because the failure it catches is a
    copy-paste in the table above and the symptom is a card state nobody can
    reach with a green seed.
    """

    reached = sorted(declared.slots for declared in games)
    if reached != list(range(SLOTS + 1)):
        raise SeedPlanMissing(
            f"the arranged games reach slot counts {reached}; the plan card has "
            f"{SLOTS + 1} states and every one of them has to be openable."
        )


def _line_for(declared: ArrangedGame, plan: Plan | None) -> str:
    """One row of the report, in the words a developer needs."""

    against = " & ".join(declared.side_b)
    if plan is None:
        return (
            f"{declared.sport.lower()} · {declared.organiser} against {against} "
            f"· no plan — the game is arranged and nothing is agreed"
        )
    return (
        f"{declared.sport.lower()} · {declared.organiser} against {against} · "
        f"{plan.slot_count}/{SLOTS} slot(s)"
        + (f" · where {plan.place.value}" if plan.place else "")
        + (f" · {plan.day.isoformat()}" if plan.day else "")
        + (f" · agreed {plan.agreed_point.isoformat()}" if plan.agreed_point else "")
    )


def costs(seeded: SeededPlans) -> tuple[str, ...]:
    """What this layer costs, printed rather than hidden.

    The same disclosure the two layers above it make about the pairs they spend:
    a developer who meets one of these as a symptom should meet it here as a
    sentence first.
    """

    return (
        f"{seeded.arranged} tennis court(s) are arranged and **never played**, "
        f"which is a state no other layer reaches and the only one a plan can be "
        f"written on. They count toward nothing — a game inside its entry window "
        f"is neither played nor a ghost — so no counterpart tally, no "
        f"`counted_games` and no run of form moves because they exist. What does "
        f"move is `answers challenges`: four more invitations were answered.",
        "the **held** arm of the three slot writes is unreachable here, and that "
        "is named rather than missed: nothing on this platform can open a case, "
        "so the hold query's only registered implementation is the null object "
        "and `account_held` is a state component tests drive.",
    )
