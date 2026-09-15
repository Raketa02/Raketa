"""The loop's own states: a game at every moment of its life, and a court at every end.

**The last layer, and the one that finishes the map.** Everything above it seeds
the *Play* screens — a pool, a deck, a court, eleven relationships — and the two
layers before it reach a game arranged and a plan half agreed. What is left is
everything between *the plan is complete* and *the score moved a Level*, plus the
three challenge endings no other layer arrives at. This is that, and it is written
here rather than spread across the layers it borrows from because the claim is one
claim: **every state the loop's five screens draw is in this database**
(``docs/specs/the-loop/``).

**Three families of state, and each is missing for its own reason.**

- **The Now rail's cards.** ``plans.py`` reaches *planning* and *game on*, and the
  played history reaches *counted* and *uncounted* — but every game it writes was
  played days ago and an ended card leaves the rail after **twenty-four hours**,
  so neither of those two was ever *drawn*. And nothing anywhere reached *needs
  result*, *confirm* or *never played*: the first needs a plan agreed on a
  **backdated** clock, the second a score nobody has answered yet, and the third
  an arrangement old enough to have ghosted. Nor had anything reached the day of
  its own game — a *planning* card whose day row reads *Today* rather than a
  weekday (``docs/adr/0166``), which needs a plan agreed for the day it is read on.
- **The seven challenge standings, on both sides.** Five were somewhere in the
  eleven or the inboxes already; ``LAPSED`` was reachable only by *waiting*, which
  a fixture cannot do, so it is written on a clock three days old; and
  ``CALLED_OFF`` (``docs/adr/0172``) is reached by the one act that records it —
  the departure that leaves one player on a game — on the *called-off* rail game.
- **The room's eight system-line codes.** Four come from the Plan — three slot
  writes and the **lock**, which is an act rather than a slot and comes from the
  one arranged plan declared agreed (``docs/adr/0155``).
  ``GAME_PLAYED`` was written and then **swept**, because a room outlives *we
  played* by forty-eight hours and every played evening here is older than that.
  ``SEAT_ACCEPTED`` and ``SEAT_LEFT`` need a court where somebody accepts after
  the room is already open and somebody else leaves it, and ``SEATS_INVITED``
  needs a **fill** — an act nothing in this fixture performed.

**Written in the past where the state is about a clock, and only there.** A
result is confirmed six hours after the score was proposed, a card leaves the rail
a day after the game, a seat lapses after forty-eight hours and an entry window
closes eight days after the arrangement — so each row below declares how long ago
it happened and is written on its own clock, through the same use cases at that
instant. Nothing is faked forward: the acceptance really is inside its seat's day,
because that day started a moment earlier on the same clock. It is the played
history's rule (``app/seeds/games.py``) at the finer unit ``clock.hours_before``
exists for.

**And it tells the rooms as it goes**, which no other layer does. Every line this
layer seeds depends on an earlier event having been delivered first — a membership
line is written only where a room already existed, a slot line is hung on the room
its challenge opened, and a played line on a room *through its game*. The outbox
orders by a ``created_at``
that is one **second** granular on SQLite, so a send, an acceptance and an entry
written a moment apart tie and the tie-break is a minted uuid: every one of those
lines would be a coin flip on the database that runs the whole seed in CI. So the
barrier is explicit — :func:`_tell_the_rooms` — and two batches are two orders
nobody has to guess.

**Re-running writes nothing twice**, and every probe here is a question about the
**record** rather than about a standing: a standing is a fact about an instant and
the instant a second run folds against is not the first run's. A game is looked
for by its line-up, a court by the pair and the end it reached, and a fill by
whether the court is already bigger than the two people who opened it.

**Nothing here seats the protagonist**, on ``games.py``'s own constraint: a game
with her in it puts that person back in her pool carrying an ``ACCEPTED`` tally,
which is ``PREVIOUS_ACCEPT`` — a code ``screens.py`` asserts is absent from this
cohort by name. The states below are the **population's**, and they are read as
the member whose screen each one is.

**Half a gate, said out loud.** None of the claims here runs in CI: they need a
database with the seed in it. What does run in CI is ``tests/api/test_the_loop.py``,
which walks the same loop over HTTP as two people — the same split the ruleset
diff ships with, and the same one ``screens.py`` states.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Awaitable, Callable, Collection, Mapping, Sequence, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import build_candidate_source
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.challenges.application.commands import (
    AnswerSeatCommand,
    FillSeatsCommand,
    LeaveGameCommand,
    SeatChoice,
)
from app.modules.challenges.application.read_challenge import ReadChallengeCommand
from app.modules.challenges.application.read_challenges import (
    ReadChallengesCommand,
    StandingChallenge,
)
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.seats import SeatAnswer
from app.modules.challenges.domain.seats import Side as CourtSide
from app.modules.challenges.domain.standing import Standing
from app.modules.conversations.domain.entries import SystemLine, SystemLineCode
from app.modules.games.application.commands import (
    AcceptResultCommand,
    StateResultCommand,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import entry_closes_at
from app.modules.matchmaking.application.commands import RunLineupSearchCommand
from app.modules.matchmaking.domain.lineups import LineupSeat
from app.modules.plans.application.commands import ReadPlansCommand
from app.modules.plans.domain.plan import SLOTS, Plan
from app.modules.plans.domain.slots import local_day
from app.seeds.clock import hours_before
from app.seeds.cohort import COHORT, PLAYED_GAMES, Cohort
from app.seeds.games import (
    SCORES,
    arrange_the_court,
    email_of,
    mode_of,
    player_of,
    the_game_already_there,
)
from app.seeds.paths import (
    TRACE_ID,
    ReadPaths,
    read_paths,
    returned_ids,
    run_a_shortlist,
    send_a_court,
    the_ephemeral_store,
    tick_the_tail_to_catch_up,
)
from app.seeds.plans import AGREED_HOUR, ARRANGED_GAMES, agree_up_to
from app.seeds.rooms import (
    deliver_everything_told,
    every_room_in_the_database,
    read_the_entries,
)

#: The barrier this layer calls between writes: *deliver what has been told so
#: far*. A callable rather than a session factory, so the writers below name what
#: they need — a room to write into — rather than the connection it takes to get
#: one.
Told = Callable[[], Awaitable[None]]

#: One day, in hours. Spelled once because three declarations below are ages in
#: days that have to be stated in hours — the unit the loop's clocks work in.
A_DAY = 24


@final
@dataclass(frozen=True, slots=True)
class RailGame:
    """One game at one moment of its life, and the card that moment draws.

    **Handles and never ids**, like every other declaration in this package.
    ``side_a[0]`` organised it, by position rather than in a field of its own, on
    ``PlayedGame``'s own shape — so this satisfies the same ``Arrangement``
    protocol and *send a court and answer every seat* stays written once.

    ``card`` is the name the **client** gives what this row draws
    (``frontend_player/src/features/plans/domain/gameCard.ts``), and it is
    declared rather than derived for one reason: the row exists to reach that card
    and the claim at the bottom of this file re-derives the name from the read
    paths and compares. A row whose declared card and drawn card disagree is
    either a fixture that has drifted or a ladder that has, and both are worth a
    red run.
    """

    card: str
    sport: str
    #: How long before this run's *now* the line-up completed. Hours, because a
    #: card that leaves the rail a day after the game and a result that confirms
    #: six hours after the score cannot be told apart in days.
    arranged_hours_ago: int
    side_a: tuple[str, ...]
    side_b: tuple[str, ...]
    #: How many of the three plan slots are agreed, in ADR-0144's own order.
    slots: int = 0
    #: How many days after the arrangement the agreed day falls. Read only when
    #: ``slots >= 2``, and measured from the **arrangement** rather than from now,
    #: because the write happens on the arrangement's clock and a day before it
    #: is a day the platform refuses.
    day_after_arranging: int = 0
    #: When somebody said *we played*, or ``None`` for a game nobody has entered.
    played_hours_ago: int | None = None
    #: Whether the other side agreed with the score.
    answered: bool = False
    #: When the opponent **left**, or ``None`` for a game nobody has left. In
    #: singles the departure leaves one player on the court, so it ends the
    #: court with its game (``docs/adr/0172`` §1): the challenge reads
    #: ``CALLED_OFF`` naming the leaver, and the game draws *Called off* with
    #: ``called_off_by`` naming them, for a day from that instant.
    left_hours_ago: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.slots <= SLOTS:
            raise ValueError(f"a plan at {self.slots} of {SLOTS} slots")
        if self.left_hours_ago is not None and (
            self.played_hours_ago is not None
            or self.left_hours_ago > self.arranged_hours_ago
            or len(self.side_b) != 1
        ):
            raise ValueError(
                f"'{self.card}' is left {self.left_hours_ago}h ago: a departure "
                f"is admitted only on a game nobody has entered, after it was "
                f"arranged ({self.arranged_hours_ago}h ago), and it ends the "
                f"court only when it leaves one player on it — singles."
            )
        if self.answered and self.played_hours_ago is None:
            raise ValueError(
                f"'{self.card}' agrees a score nobody stated: an acceptance is "
                f"an answer to a proposal, and there is no proposal without an "
                f"entry."
            )
        if (
            self.played_hours_ago is not None
            and self.played_hours_ago > self.arranged_hours_ago
        ):
            raise ValueError(
                f"'{self.card}' was played {self.played_hours_ago}h ago and "
                f"arranged {self.arranged_hours_ago}h ago, which is a game "
                f"played before it was agreed."
            )

    @property
    def organiser(self) -> str:
        return self.side_a[0]

    @property
    def players(self) -> tuple[str, ...]:
        return self.side_a + self.side_b


#: The six games this layer arranges — one per card no other layer draws, and one
#: for the day of the game, which no other layer's plan names.
#:
#: **Tennis singles throughout, organised by the member the played history and the
#: plans already organise with**, which is the cheapest shape that reaches five
#: distinct pairs: a completed line-up releases its pair (``docs/adr/0142`` §1),
#: so nothing here leaves anybody gated. Each opponent is a member who already
#: holds a Tennis rating from their own draw and whom nobody has played — a pair
#: that has already played is a game this layer's probe would mistake for its own,
#: because a game is looked for by its line-up.
#:
#: **None of them declares a second sport**, so ``cohort.json`` does not move:
#: ``SECOND_SPORT_BECAUSE_THEY_PLAYED`` feeds the *draw*, and a row here that
#: needed one would move the committed population for a fixture about cards.
RAIL_GAMES: tuple[RailGame, ...] = (
    # *Planning*, on the day of the game: agreed for today, and the hour
    # deliberately **not** agreed. There is no *Today* card (``docs/adr/0166``) —
    # the day row says it, `Today 14 Sep` where a weekday would be, under the tag
    # the plan has earned — and a plan with a day and no hour on the morning of the
    # game is the case that shows why: it is still *Planning*, with a dim `TIME`
    # bar, and it says so rather than announcing the game as settled.
    RailGame(
        card="planning",
        sport=Sport.TENNIS.value,
        arranged_hours_ago=0,
        side_a=("cohort-d-01",),
        side_b=("cohort-a-15",),
        slots=2,
        day_after_arranging=0,
    ),
    # *Needs result*: the agreed moment has passed and the entry window has not,
    # which is the only rung whose card leads with a duration.
    RailGame(
        card="needs-result",
        sport=Sport.TENNIS.value,
        arranged_hours_ago=4 * A_DAY,
        side_a=("cohort-d-04",),
        side_b=("cohort-d-07",),
        slots=3,
        day_after_arranging=2,
    ),
    # *Confirm the result*: one score on the table and its window still open.
    RailGame(
        card="confirm",
        sport=Sport.TENNIS.value,
        arranged_hours_ago=3,
        side_a=("cohort-d-08",),
        side_b=("cohort-d-02",),
        played_hours_ago=2,
    ),
    # *Counted*, **inside its twenty-four-hour tail** — the one state the played
    # history reaches and never draws. Agreed from across the net rather than
    # confirmed by silence, deliberately: silence confirms one proposal window
    # after the entry, which is almost exactly when the card leaves the rail.
    RailGame(
        card="counted",
        sport=Sport.TENNIS.value,
        arranged_hours_ago=9,
        side_a=("cohort-d-08",),
        side_b=("cohort-d-06",),
        played_hours_ago=8,
        answered=True,
    ),
    # *Never played*: the entry window closed two hours ago, so the game is a
    # ghost and its card is still inside the same tail every ending keeps.
    RailGame(
        card="never-played",
        sport=Sport.TENNIS.value,
        arranged_hours_ago=8 * A_DAY + 2,
        side_a=("cohort-d-01",),
        side_b=("cohort-c-03",),
    ),
    # *Called off*: the opponent said yes and, an hour later, left — which in
    # singles leaves one player on the court, so the court ends with its game
    # (``docs/adr/0172`` §1). The one game here whose ending is an **act** and
    # not a clock, and the one challenge in this database that reads
    # ``CALLED_OFF``: the challenge screen's seventh standing, on both sides —
    # the organiser left alone, and the leaver, who can still open the court
    # they walked out of. A place is agreed so the card has a slot to keep, and
    # no day, so no agreed moment stands in the departure's way.
    RailGame(
        card="called-off",
        sport=Sport.TENNIS.value,
        arranged_hours_ago=3,
        side_a=("cohort-d-01",),
        side_b=("cohort-d-04",),
        slots=1,
        left_hours_ago=2,
    ),
)


@final
@dataclass(frozen=True, slots=True)
class SeededCourt:
    """One court sent for the end it reaches, rather than for the game it becomes.

    ``answers`` is one per invitee, in order, and ``None`` is a seat nobody
    answered — which is *awaiting* and not a fourth :class:`SeatAnswer`, exactly
    as the aggregate spells it.
    """

    sport: str
    #: How long before *now* the court was sent. A seat's window runs from the
    #: send, so this is the only thing that decides whether it has lapsed.
    sent_hours_ago: int
    organiser: str
    invitees: tuple[str, ...]
    answers: tuple[SeatAnswer | None, ...]

    def __post_init__(self) -> None:
        if len(self.answers) != len(self.invitees):
            raise ValueError(
                f"'{self.organiser}' sends {len(self.invitees)} invitation(s) "
                f"and {len(self.answers)} answer(s) are declared."
            )

    @property
    def players(self) -> tuple[str, ...]:
        return (self.organiser,) + self.invitees


#: **The court nobody answered.** ``LAPSED`` is the one standing this database
#: cannot reach by any act: the other five arrive from a send, an acceptance, a
#: no, a decision to end it — and this one arrives from a **clock**, which a
#: fixture reaches by writing in the past and in no other way. Sent three days
#: ago, against an answer window of forty-eight hours.
#:
#: Tennis singles between two members nobody else here uses, so the pair it
#: releases on lapsing was never anybody's fixture.
THE_COURT_NOBODY_ANSWERED = SeededCourt(
    sport=Sport.TENNIS.value,
    sent_hours_ago=3 * A_DAY,
    organiser="cohort-b-03",
    invitees=("cohort-d-01",),
    answers=(None,),
)

#: **The court somebody left**, and the only room in this database that carries
#: both of the two membership lines a room can be told after it opens. A padel
#: four sent to three: the first acceptance opens the room and draws no line, the
#: second draws ``SEAT_ACCEPTED``, and the no draws ``SEAT_LEFT`` — and leaves the
#: court at ``LINE_UP_INCOMPLETE``, because a decline reopens one seat and
#: disturbs nothing else.
#:
#: The person who left is the **reader who has left**: still on the court, still
#: able to open it, drawn no card by it, and told a sentence that is true about
#: *them* rather than *You're in* on a court they have gone from.
#:
#: **Four members of the furthest ring**, and the ring is the choice rather than
#: the members: every member of one ring shares one coordinate, so a send survives
#: the four fail-closed gates over **every pair** of the court — and this court is
#: the one thing here that never ends, so the pairs it holds are held for good. In
#: the nearest ring those would be pairs the protagonist's own screens are read
#: from; out here they are nobody's fixture but this one's.
THE_COURT_SOMEBODY_LEFT = SeededCourt(
    sport=Sport.PADEL.value,
    sent_hours_ago=1,
    organiser="cohort-d-05",
    invitees=("cohort-d-04", "cohort-d-06", "cohort-d-08"),
    answers=(SeatAnswer.ACCEPTED, SeatAnswer.ACCEPTED, SeatAnswer.DECLINED),
)


class LoopStateMissing(RuntimeError):
    """A state the loop's screens draw is not in this database.

    Raised rather than reported, on this fixture's own rule: an assertion here is
    a claim about the **real read path**, so a shape that is missing is a screen a
    developer is about to open and find empty.
    """


@final
@dataclass(frozen=True, slots=True)
class WrittenLoop:
    """What this layer wrote, as lines for the report."""

    games: tuple[str, ...]
    courts: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class SeededLoop:
    """The layer, both halves: what it wrote and what the screens then drew."""

    written: WrittenLoop
    claims: tuple[str, ...]


# ---------------------------------------------------------------------------
# Writing — and telling as it goes, which is what makes the lines deterministic
# ---------------------------------------------------------------------------


async def _tell_the_rooms(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Drain the outbox now, so that the next write has a room to write into.

    **This is the one layer that cannot leave the delivery to the end**, and the
    reason is a rule two layers apart. A membership line is written *only where
    there was already a room to write it in* — the first acceptance **is** the
    opening — and a slot line and a played line are hung on a room **through its
    game**, which the room learns from ``GamePlanned``. So every one of them
    depends on an earlier event having been delivered first.

    The outbox orders by ``(created_at, id)`` and ``created_at`` is
    transaction-start time. On Postgres that is microseconds and the order is the
    order things happened; **on SQLite it is one second**, so a send, an
    acceptance and an entry written a moment apart tie and the tie-break is a
    minted uuid (``docs/adr/0097``) — which makes every line this layer exists to
    seed a coin flip on the database ``tests/unit/test_seed_runner.py`` runs the
    whole seed against.

    Two batches are two orders nobody has to guess, so the barrier is here rather
    than in a comment about luck. It is safe and cheap to repeat for
    ``deliver_everything_told``'s own reason: the batch takes its rows
    ``FOR UPDATE SKIP LOCKED``, and a second call finds nothing left.

    **The writer's own transaction is ended first, and that line is the whole
    difference between a two-minute seed and a fifteen-minute one.** The delivery
    runs on sessions of its own, and SQLite locks the **file**: a second connection
    cannot write while this one is inside a transaction — which a read leaves open
    until it is committed — so every barrier would sit out a busy timeout, twelve
    times, on the database the CI test runs the whole seed against. The commit
    writes nothing (every act here committed through its own unit of work) and
    expires nothing (``expire_on_commit=False``); what it does is let go.
    """

    await session.commit()
    await deliver_everything_told(session_factory)


async def write_the_loop(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Cohort = COHORT,
) -> WrittenLoop:
    """Arrange the six games, send the two courts, and fill the half-built one.

    The tail is ticked first for the reason every layer that runs a search ticks
    it: a search reads the candidate index, and the index has not seen everything
    this run has written. ADR-0110 makes the tick safe and cheap to repeat.

    **Oldest first, and it is legibility rather than a rule** — the same choice
    the played history makes. What the order buys is a report that reads in the
    same direction a life does.
    """

    await tick_the_tail_to_catch_up(session_factory, settings=settings)
    candidates = build_candidate_source(session_factory=session_factory)
    await candidates.refresh()

    games: list[str] = []
    courts: list[str] = []
    async with the_ephemeral_store(settings) as redis:
        async with session_factory() as session:
            # **Looked up once for the whole layer**, exactly as the played
            # history does: every row builds its own paths — one per instant,
            # because the clock is a constructor argument — and the
            # address-to-id map is the one part of that wiring that is a query.
            players: Mapping[str, UUID] | None = None

            async def paths_at(hours_ago: int) -> ReadPaths:
                nonlocal players
                built = await read_paths(
                    session,
                    settings=settings,
                    candidates=candidates,
                    cohort=cohort,
                    now=hours_before(now, hours_ago).now(),
                    redis=redis,
                    players=players,
                )
                players = built.players
                return built

            for declared in sorted(RAIL_GAMES, key=lambda one: -one.arranged_hours_ago):
                games.append(
                    await _write_one_game(
                        session,
                        declared,
                        cohort,
                        arranged=await paths_at(declared.arranged_hours_ago),
                        played=(
                            None
                            if declared.played_hours_ago is None
                            else await paths_at(declared.played_hours_ago)
                        ),
                        left=(
                            None
                            if declared.left_hours_ago is None
                            else await paths_at(declared.left_hours_ago)
                        ),
                        now=now,
                        tell=lambda: _tell_the_rooms(session, session_factory),
                    )
                )
            for court in (THE_COURT_NOBODY_ANSWERED, THE_COURT_SOMEBODY_LEFT):
                courts.append(
                    await _write_one_court(
                        await paths_at(court.sent_hours_ago),
                        court,
                        cohort,
                        tell=lambda: _tell_the_rooms(session, session_factory),
                    )
                )
            courts.append(
                await _fill_a_half_built_court(
                    await paths_at(0),
                    cohort,
                    tell=lambda: _tell_the_rooms(session, session_factory),
                )
            )

    return WrittenLoop(games=tuple(games), courts=tuple(courts))


# ---------------------------------------------------------------------------
# The games
# ---------------------------------------------------------------------------


async def _write_one_game(
    session: AsyncSession,
    declared: RailGame,
    cohort: Cohort,
    *,
    arranged: ReadPaths,
    played: ReadPaths | None,
    left: ReadPaths | None,
    now: Instant,
    tell: Told,
) -> str:
    """One game, arranged at its own instant, planned at it, and entered — or
    left — at another.

    **Two clocks and they are two facts.** The court was sent and answered when it
    was arranged; the score was stated when they had played, or the seat was left
    when somebody walked out. A row that used one for both would be a game whose
    result was entered before the evening.

    The probe comes before the search, exactly as it does for a played game and
    for the lesson ``pairs.py`` paid for: once a court has been sent the pair is
    gated, so a run that searched first would fail its second pass with a message
    about a pool when what actually happened is that the first pass died between
    the send and the last acceptance.
    """

    sport = Sport(declared.sport)
    organiser = cohort.by_handle(declared.organiser)
    standing = await the_game_already_there(arranged, declared, cohort)
    if standing is None:
        standing = await arrange_the_court(arranged, declared, cohort, sport, organiser)
        built = "arranged"
    else:
        built = "already there"
    # **Asked on both paths through this function**, which is why it is here and
    # not inside the send: a game's kind follows the mode of the search its court
    # was built on, which follows the organiser's own declared Play intent — so
    # this is a check that the declaration is coherent, made on the run that
    # creates nothing as well as on the one that creates everything.
    mode_of(arranged, organiser, sport)
    # **The room is told the arrangement before anything is hung on it.** A slot
    # line is found through the room's challenge and a played line *through the
    # game*, which the room learns from ``GamePlanned`` — so the two writes below
    # need this delivery to have happened, and on SQLite they cannot get it by
    # luck.
    await tell()

    # **A called-off game's plan is history**, so the slot its card keeps was
    # written on the run that arranged it and a second run leaves it be: the
    # plan write is the one act here a previous run's ending refuses.
    agreed = (
        "the plan is history, its slot kept"
        if standing.called_off_at is not None
        else await _agree_what_this_card_needs(
            session,
            declared,
            cohort,
            paths=arranged,
            challenge_id=standing.challenge_id,
            at=hours_before(now, declared.arranged_hours_ago).now(),
        )
    )
    entered = (
        "nobody has entered a result"
        if played is None
        else await _enter_what_this_card_needs(played, declared, standing, cohort)
    )
    if left is not None:
        # **After the plan and before the end.** A called-off game's plan is
        # history, so the slot the card keeps has to be written first; and the
        # departure is the ending, so it is the last act on this court.
        entered = await _leave_what_this_card_needs(left, declared, standing, cohort)
    return (
        f"{declared.card} · {sport.value.lower()} · {declared.organiser} against "
        f"{' & '.join(declared.side_b)} · {built} "
        f"{declared.arranged_hours_ago}h ago · {agreed} · {entered}"
    )


async def _agree_what_this_card_needs(
    session: AsyncSession,
    declared: RailGame,
    cohort: Cohort,
    *,
    paths: ReadPaths,
    challenge_id: UUID,
    at: Instant,
) -> str:
    """Write this row's plan, on the clock the arrangement was made on.

    **The day is measured from the arrangement and never from now**, which is what
    lets a plan be agreed for a day that has since passed: the chips a member is
    offered run from *their* today to the horizon, so a day before the write is a
    day the platform refuses — and *needs result* is exactly a plan whose agreed
    moment is now behind us.
    """

    if declared.slots == 0:
        return "nothing is agreed"
    await agree_up_to(
        session,
        challenge_id=challenge_id,
        slots=declared.slots,
        between=(
            player_of(paths, cohort, declared.organiser),
            player_of(paths, cohort, declared.side_b[0]),
        ),
        day=_the_agreed_day(at, declared.day_after_arranging),
        hour=AGREED_HOUR,
        now=at,
    )
    return (
        f"{declared.slots}/{SLOTS} slot(s), agreed for "
        f"{_the_agreed_day(at, declared.day_after_arranging).isoformat()}"
    )


def _the_agreed_day(at: Instant, days_after: int) -> date:
    """The local day this plan names, counted from the day it was agreed on.

    Through the domain's own ``local_day`` — the conversion the plan itself makes,
    written once there rather than spelled again here.
    """

    return local_day(at) + timedelta(days=days_after)


async def _enter_what_this_card_needs(
    paths: ReadPaths, declared: RailGame, standing: Game, cohort: Cohort
) -> str:
    """*We played, here is the score* — and, where the row says so, the answer.

    **Each act is asked for separately, off the record rather than off a
    standing**, exactly as the played history asks: a standing is a fact about an
    instant and the instant a second run folds against is not the first run's,
    while ``played_at`` and the acceptance are the record and say precisely which
    act is still owed.
    """

    speaker = player_of(paths, cohort, declared.side_a[0])
    answerer = player_of(paths, cohort, declared.side_b[0])
    acts: list[str] = []
    if standing.played_at is None:
        await paths.state_result.execute(
            StateResultCommand(
                game_id=standing.id, player_id=speaker, score=SCORES[GameSide.A]
            )
        )
        acts.append(f"score entered {declared.played_hours_ago}h ago")
    if declared.answered and standing.acceptance is None:
        await paths.accept_result.execute(
            AcceptResultCommand(game_id=standing.id, player_id=answerer)
        )
        acts.append("agreed from across the net")
    return ", ".join(acts) if acts else "result already entered"


async def _leave_what_this_card_needs(
    paths: ReadPaths, declared: RailGame, standing: Game, cohort: Cohort
) -> str:
    """*I am out* — the opponent leaves, and in singles that ends the court.

    Asked off the record rather than off a standing, as the entry is: a game
    already called off is one a previous run left, and a second departure would
    meet *the challenge is over*. The departure runs through the use case the
    button behind it runs, so what it writes is what a phone would have written
    — the seat, the court's ending and the game's end in one transaction
    (``docs/adr/0172`` §1) — and the room is destroyed when the outbox is next
    drained.
    """

    if standing.called_off_at is not None:
        return "already called off"
    leaver = player_of(paths, cohort, declared.side_b[0])
    answered = await paths.leave.execute(
        LeaveGameCommand(challenge_id=standing.challenge_id, player_id=leaver)
    )
    if answered.standing is not Standing.CALLED_OFF:
        raise LoopStateMissing(
            f"'{declared.side_b[0]}' left '{declared.card}' and the court reads "
            f"{answered.standing.value} rather than {Standing.CALLED_OFF.value}. "
            f"A departure that leaves one player on a game ends the court with "
            f"it, so a singles court somebody left cannot still be arranging."
        )
    return (
        f"{declared.side_b[0]} left {declared.left_hours_ago}h ago, and the court "
        f"ended with its game"
    )


# ---------------------------------------------------------------------------
# The courts
# ---------------------------------------------------------------------------


async def _write_one_court(
    paths: ReadPaths, declared: SeededCourt, cohort: Cohort, *, tell: Told
) -> str:
    """One court, sent at its own instant and answered as the row declares.

    **The probe is the end this court reached, not a key**, and it has to be:
    ``LAPSED`` and ``LINE_UP_INCOMPLETE`` both leave the seats they were declared
    with, so *has this already been sent* is answerable off the arrangement — the
    pair, the sport and the answers — and off nothing else. A second run that
    could not tell would send a second court, and two courts between two people is
    what ``challenges`` refuses rather than duplicates.
    """

    sport = Sport(declared.sport)
    organiser = cohort.by_handle(declared.organiser)
    already = await _the_court_already_sent(paths, declared, cohort)
    if already is not None:
        return (
            f"already there · {declared.organiser}'s {sport.value.lower()} court "
            f"read {already.standing.value} at the instant it was sent, "
            f"{declared.sent_hours_ago}h ago"
        )

    record = await run_a_shortlist(
        paths, organiser.email, sport, mode_of(paths, organiser, sport)
    )
    shown = returned_ids(record)
    missing = sorted(
        handle
        for handle in declared.invitees
        if player_of(paths, cohort, handle) not in shown
    )
    if missing:
        offered = sorted(
            member.handle
            for member in cohort.members
            if paths.players.get(email_of(cohort, member.handle)) in shown
        )
        raise LoopStateMissing(
            f"'{declared.organiser}' ran their own {sport.value} search and it "
            f"never showed {missing}, over {record.counts.n_generated} generated "
            f"and {record.counts.n_returned} returned — it showed {offered}. A "
            f"send cites the search that showed the person, so this court cannot "
            f"be sent at all. "
            f"Gates: {dict(sorted(record.counts.excluded_by_gate.items()))}. "
            f"The row is a declared court in `app/seeds/loop.py`."
        )

    challenge_id = await send_a_court(
        paths,
        organiser=organiser.email,
        sport=sport,
        record=record,
        invitees=[email_of(cohort, handle) for handle in declared.invitees],
    )
    for handle, answer in zip(declared.invitees, declared.answers, strict=True):
        if answer is None:
            continue
        await _answer_the_seat(
            paths,
            challenge_id=challenge_id,
            player_id=player_of(paths, cohort, handle),
            answer=answer,
        )
        # **After each one, because the first acceptance is the opening.** The
        # second answer's line is written only if the room the first one opened is
        # already there, and two answers in one batch tie on a coarse clock.
        await tell()
    reads = await paths.read_challenge.execute(
        ReadChallengeCommand(
            challenge_id=challenge_id,
            reader_id=player_of(paths, cohort, declared.organiser),
        )
    )
    return (
        f"sent · {declared.organiser}'s {sport.value.lower()} court to "
        f"{' & '.join(declared.invitees)}, "
        f"{[answer.value if answer else 'no answer' for answer in declared.answers]}"
        f" · {declared.sent_hours_ago}h ago it read {reads.standing.value} at the "
        f"instant it was sent"
    )


async def _answer_the_seat(
    paths: ReadPaths, *, challenge_id: UUID, player_id: UUID, answer: SeatAnswer
) -> None:
    """One seat's answer, through the use case the button behind it runs."""

    command = AnswerSeatCommand(challenge_id=challenge_id, player_id=player_id)
    if answer is SeatAnswer.ACCEPTED:
        await paths.accept.execute(command)
    else:
        await paths.decline.execute(command)


async def _the_court_already_sent(
    paths: ReadPaths, declared: SeededCourt, cohort: Cohort
) -> StandingChallenge | None:
    """This declared court, if a previous run already sent it.

    Found by **who is seated on it** rather than by an id, for every other probe
    in this package's reason: an id is minted by the write path and a fresh
    database mints a different one. Read through the organiser's own challenge
    list, which is the screen a player reads their courts on.
    """

    organiser = player_of(paths, cohort, declared.organiser)
    wanted = frozenset(player_of(paths, cohort, handle) for handle in declared.players)
    _, standing = await paths.read_challenges.execute(
        ReadChallengesCommand(reader_id=organiser)
    )
    for row in standing:
        if row.challenge.organiser_id != organiser:
            continue
        seated = frozenset(
            seat.player_id for seat in row.challenge.seats if seat.player_id is not None
        )
        if seated == wanted and row.challenge.sport.value == declared.sport:
            # **The row and not the aggregate**, because the caller wants the
            # standing too and the list has already folded one against the
            # instant these paths read — asking the aggregate again would be a
            # second fold against a second clock.
            return row
    return None


# ---------------------------------------------------------------------------
# The fill — the one act nothing in this fixture performed
# ---------------------------------------------------------------------------


async def _fill_a_half_built_court(
    paths: ReadPaths, cohort: Cohort, *, tell: Told
) -> str:
    """Grow one half-built court, and let the person seated into it accept.

    **``SEATS_INVITED`` has one source and this is it.** A room learns that seats
    were invited from a fill and from nothing else, so a fixture that never
    performed one leaves that line undrawable — which ``app/seeds/rooms.py`` said
    of itself in writing until this layer existed.

    **The court is found by shape and never named**, exactly as ``pairs.py``
    finds the ones it leaves half built: which court is fillable is a question
    about somebody's pool that only a real ⚡ answers, and a fixture that named one
    would go looking for a uuid the day the relationship moved.

    **Any live member may press it**, and the filler here is the first live
    accepted seat on the court — which for a sent court is the organiser and for a
    mutual-born one is whichever of the pair the court seated first. That is the
    rule ``docs/adr/0150`` chose over *only the organiser*, and the mutual-born
    court is the case that decided it.

    **Everybody newly seated then says no, and that is not squeamishness.** The
    court this layer grows is one ``pairs.py`` leaves standing at
    ``LINE_UP_INCOMPLETE`` and asserts is still standing there — so a fill whose
    invitees accepted could complete the line-up, turn the court into a game, and
    take that fixture away for good (a mutual mints again only once the last one it
    minted is finished with, ``docs/adr/0152``). A no leaves the standing exactly
    where it was whatever the pool offered, which makes this layer's effect on
    somebody else's fixture **nothing** rather than *nothing most of the time*.
    What the room keeps is the pair of lines the fill and the departure wrote.

    **The probe is a seat that said no.** A court this layer has already grown
    carries one, and no court this fixture leaves half built does — so *has this
    been grown* is a question about the record rather than a key, and the second run
    stops before the ⚡ rather than asking somebody else.
    """

    for court in await _half_built_courts(paths, cohort):
        if not any(seat.player_id is None for seat in court.seats):
            # A court whose every seat holds somebody has nowhere to seat one
            # more: ``THE_COURT_SOMEBODY_LEFT`` is such a court, and a declined
            # seat keeps its person while reopening the *position*.
            continue
        if any(seat.answer is SeatAnswer.DECLINED for seat in court.seats):
            return (
                f"already grown · challenge {court.id} carries a seat that was "
                f"invited and said no, which is this layer's own footprint"
            )
        already = {seat.player_id for seat in court.seats if seat.player_id is not None}
        member = next(
            seat.player_id
            for seat in court.seats
            if seat.player_id is not None and seat.is_accepted()
        )
        answer = await paths.lineup.execute(
            RunLineupSearchCommand(
                searcher_id=member,
                sport=None,
                mode=None,
                locked_seats=(),
                completing_challenge_id=court.id,
                availability_override=None,
                offered_by_search_id=None,
                rung=None,
                trace_id=TRACE_ID,
            )
        )
        seated = _one_more_from_the_population(answer.seats, already, paths, cohort)
        if seated is None:
            continue
        grown = await paths.fill.execute(
            FillSeatsCommand(
                challenge_id=court.id,
                player_id=member,
                search_id=answer.record.id,
                court=tuple(
                    SeatChoice(
                        # **The two spellings of a side, mapped at the seam.**
                        # The matcher's ``Side`` is *the searcher's side of a
                        # line-up it is ranking* and this one is *a position on a
                        # court somebody was asked to sit in*; the strings are
                        # equal on purpose so the mapping is identity rather than
                        # a table, and the route does exactly this.
                        side=CourtSide(seat.side.value),
                        player_id=_kept(seat.player_id, already, seated),
                    )
                    for seat in answer.seats
                ),
            )
        )
        # The invitation's own line goes in before the answer to it does.
        await tell()
        await _answer_the_seat(
            paths,
            challenge_id=court.id,
            player_id=seated,
            answer=SeatAnswer.DECLINED,
        )
        await tell()
        left = await paths.read_challenge.execute(
            ReadChallengeCommand(challenge_id=court.id, reader_id=member)
        )
        return (
            f"grown · challenge {court.id} was filled by a member's own ⚡ and "
            f"read {grown.standing.value} the moment they were asked; the one "
            f"seat invited said no and it reads {left.standing.value} again, "
            f"with both lines in the room"
        )
    raise LoopStateMissing(
        "no half-built court in this database could be grown: either none "
        "stands — `app/seeds/pairs.py` leaves two — or every ⚡ run from one came "
        "back with nobody new to invite, which is the cohort's own pool and is "
        "held under its own name by `app/seeds/screens.py`. Without a fill, "
        f"{SystemLineCode.SEATS_INVITED.value} is a system line no room in this "
        "database can draw."
    )


def _one_more_from_the_population(
    seats: Sequence[LineupSeat],
    already: Collection[UUID],
    paths: ReadPaths,
    cohort: Cohort,
) -> UUID | None:
    """The **one** cohort member this ⚡ offered who is not already on the court.

    **One, and never every seat it filled.** Two reasons, and each is a state
    somebody else's fixture owns. A fill that took every seat could **complete**
    the line-up, and the court it completed is one ``pairs.py`` asserts is still
    half built; and a court left with no empty seat is one this layer could not
    find again, so the second run would go looking for another court to grow.
    Seating one leaves both facts where they were.

    **From the population and never from the named accounts.** The ⚡ ranks
    whoever is in the pool, and the eleven relationships and the four protagonists
    are in it — each of them named for exactly one state, which a seat on somebody
    else's court is not. So the caller composes the court out of what the search
    offered, which is what a caller does.
    """

    members = {
        paths.player(email_of(cohort, member.handle)) for member in cohort.members
    }
    return next(
        (
            UUID(seat.player_id)
            for seat in seats
            if seat.player_id is not None
            and UUID(seat.player_id) not in already
            and UUID(seat.player_id) in members
        ),
        None,
    )


def _kept(offered: str | None, already: Collection[UUID], seated: UUID) -> UUID | None:
    """Who this seat holds on the court being posted: the court's own, or the one
    newly seated, and **empty for everybody else the ⚡ offered.**

    The fill posts the whole court as it will stand, so the seats this layer is
    not filling have to go back empty rather than carrying whoever the search
    would have put there.
    """

    if offered is None:
        return None
    player_id = UUID(offered)
    return player_id if player_id in already or player_id == seated else None


async def _half_built_courts(paths: ReadPaths, cohort: Cohort) -> tuple[Challenge, ...]:
    """Every ``LINE_UP_INCOMPLETE`` court in this database, read as its members.

    There is no *all the challenges* read and there should not be — the reader is
    the gate on every route this context has — so this reads as each cohort member
    in turn and keeps one copy of each court it is shown. Sorted, because a
    mapping's iteration order is the order the fill would traverse in and a
    fixture's answer may not depend on it (``docs/adr/0105`` §1).
    """

    found: dict[UUID, Challenge] = {}
    for member in cohort.members:
        _, standing = await paths.read_challenges.execute(
            ReadChallengesCommand(
                reader_id=paths.player(email_of(cohort, member.handle))
            )
        )
        for row in standing:
            if row.standing is Standing.LINE_UP_INCOMPLETE:
                found.setdefault(row.challenge.id, row.challenge)
    return tuple(found[key] for key in sorted(found))


# ---------------------------------------------------------------------------
# The claims — after the outbox is drained and the ended rooms are swept
# ---------------------------------------------------------------------------


async def assert_the_loop(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Cohort = COHORT,
) -> tuple[str, ...]:
    """Read every state the loop's screens draw, and refuse a database missing one.

    **After the rooms, and that is the order the claims need.** A room is *told*
    through the outbox and an ended one is destroyed by a sweep, so a claim about
    which lines a standing room carries has to be made on the far side of both —
    exactly as ``screens.py``'s claims are made on the far side of the candidate
    index's tick.

    Returns the lines the report prints. They are the **evidence** rather than a
    decoration: a failure has to name the state, the screen it belongs to and what
    was found instead, and printing the same breakdown on a passing run is what
    makes the green run legible too.
    """

    # **Ticked here as well as before the writes**, on ``screens.py``'s own
    # reason: the detail read is a whole scoring pass and the index has not seen
    # what the delivery and the sweep have since written.
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
            lines = [
                *await _refuse_a_card_the_rail_cannot_draw(paths, cohort),
                *await _refuse_a_standing_only_one_side_can_read(paths),
                await _refuse_a_reader_who_left_and_is_told_they_are_in(paths),
                await _refuse_a_system_line_no_room_carries(
                    session, settings=settings, now=now
                ),
            ]
    return tuple(lines)


#: Every card the Now rail can draw, **and what reaches each one**. The names are
#: the client's own (``features/plans/domain/gameCard.ts``), and the two absences
#: at the bottom are stated here because a fixture that quietly reached seven of
#: nine would read as having reached nine.
#:
#: - ``planning`` and ``game-on`` come from ``app/seeds/plans.py``'s four
#:   arranged games — the slot counts walk the card from empty to complete — and
#:   ``planning`` once more from this layer, on the day of its game;
#: - the five others in :data:`RAIL_GAMES` come from this layer, ``called-off``
#:   among them since ``docs/adr/0172``: the fourth end, an act rather than a
#:   fold, shelved from its own instant;
#: - ``uncounted`` is a **state without a card**, and the arithmetic says so: a
#:   game is unscored only once **both** sides' proposal windows have closed, and
#:   a window is a day long — so the earliest unscored instant is a day after the
#:   entry, which is exactly when an ended game leaves the rail. The state is
#:   reachable and asserted below; its card is not drawable at all, and its
#:   *screen* is, through the conversation's **Details** door, which outlives a
#:   played game by forty-eight hours. Nothing here is a defect: it is
#:   ``the-loop-screens.md`` §4.1's own cost statement — *after 24 h a finished
#:   game and its score are unreachable in this build* — read at the one game
#:   state that can never beat it;
#: - ``unreadable`` is the named gap the client draws for **a standing this build
#:   has no word for**, so it is unreachable by construction: reaching it would
#:   mean the backend serving a sixth ``GameStanding`` the client has not shipped,
#:   and a fixture cannot produce one without inventing an event.
THE_RAIL_DRAWS: tuple[str, ...] = (
    "planning",
    "game-on",
    "needs-result",
    "confirm",
    "counted",
    "never-played",
    "called-off",
)

#: The state whose card the shelf life forbids, and the standing that reaches it.
A_STATE_WITH_NO_CARD = (GameStanding.UNSCORED, "uncounted")

#: How long an ended game keeps its card. **The client's number, and it is the
#: challenge inbox's** ([#335](https://github.com/Raketa02/Raketa/issues/335)),
#: read here so that *inside its tail* means the same thing in both apps.
AN_ENDED_CARD_LASTS = timedelta(hours=24)


async def _refuse_a_card_the_rail_cannot_draw(
    paths: ReadPaths, cohort: Cohort
) -> list[str]:
    """*Every card the Now rail draws is drawn by a game in this database.*

    **Read as the player whose rail it is, which here is not a protagonist, and
    that swap is the fixture's own rule rather than a shortcut.** ``screens.py``
    reads every Play screen as one of the four named protagonists; a game cannot
    be, because *no game seats the protagonist* — one with her in it would put that
    person back in her pool carrying an ``ACCEPTED`` tally, which is
    ``PREVIOUS_ACCEPT``, a code that file asserts is absent from this cohort by
    name. So the reader is the member who organised each game, and the claim is
    the same claim: a **real read path executed as the person whose screen it is**.

    **Folded the way the client folds it**: ``GET /games`` for the standing and the
    instant, ``GET /plans`` for the slots, and the ladder over the two. That fold
    is the client's (``features/plans/domain/gameCard.ts``) and this is a
    transcription of it — which is the point rather than a duplication: a card name
    that stops being reachable fails on a seed run rather than on somebody's phone,
    and the only way to know a name is reachable is to derive it the way the phone
    will.

    **The two reads are two reads on purpose.** ``GET /plans`` carries no instant,
    so Now has one clock by construction (``docs/adr/0148`` §10) — and a claim that
    read a second one could put a rung on one side of a boundary and the standing
    beside it on the other.
    """

    drawn: dict[str, list[str]] = {}
    off_the_rail: dict[str, list[str]] = {}
    for handle in _everybody_who_organises_a_game():
        reader = paths.player(email_of(cohort, handle))
        _, games = await paths.read_games.execute(reader)
        # Keyed by the challenge, which is the plan's own id and the one every
        # game carries (``docs/adr/0164`` §1) — the join the client makes.
        plans = {
            row.plan.challenge_id: row.plan
            for row in await paths.read_plans.execute(
                ReadPlansCommand(reader_id=reader)
            )
        }
        for row in games:
            card = _the_card_this_game_draws(
                row.standing, plans.get(row.game.challenge_id), now=row.read_at
            )
            # **The row's own instant for both questions.** The standing was
            # folded against it and the rail's shelf life is measured from it, so
            # a second clock read here could put a card on the rail beside a
            # standing that says its game ended.
            where = (
                drawn
                if _on_the_rail(row.game, row.standing, row.read_at)
                else off_the_rail
            )
            where.setdefault(card, []).append(handle)

    missing = [card for card in THE_RAIL_DRAWS if card not in drawn]
    if missing:
        raise LoopStateMissing(
            f"the Now rail can draw {len(THE_RAIL_DRAWS)} card(s) and this "
            f"database reaches none of {missing}. Drawn: "
            f"{ {card: sorted(set(who)) for card, who in sorted(drawn.items())} }; "
            f"present but past the rail's own "
            f"{int(AN_ENDED_CARD_LASTS.total_seconds() // 3600)}-hour tail: "
            f"{sorted(off_the_rail)}. The rows that reach them are "
            f"`RAIL_GAMES` in `app/seeds/loop.py` and `ARRANGED_GAMES` in "
            f"`app/seeds/plans.py`."
        )
    standing, uncounted = A_STATE_WITH_NO_CARD
    if uncounted not in off_the_rail and uncounted not in drawn:
        raise LoopStateMissing(
            f"no game in this database reads {standing.value}. Its *card* is "
            f"unreachable by arithmetic and that is stated, but the **state** is "
            f"the game screen's Uncounted arm and is reached by the one game "
            f"nobody scored — `PLAYED_GAMES` in `app/seeds/cohort.py`."
        )
    gone = sorted(set(off_the_rail) - set(drawn))
    return [
        "cards · "
        + ", ".join(f"{card} ({len(drawn[card])})" for card in THE_RAIL_DRAWS)
        + " — every card the rail draws, folded off `GET /games` and `GET /plans`",
        f"cards · {gone} reach the game screen and never the rail, their games "
        f"having ended more than "
        f"{int(AN_ENDED_CARD_LASTS.total_seconds() // 3600)}h ago — `{uncounted}` "
        f"among them by arithmetic rather than by accident, since a game is "
        f"unscored only once both proposal windows have closed; and `unreadable` "
        f"is the client's named gap for a standing it has no word for, "
        f"unreachable here by construction",
    ]


def _everybody_who_organises_a_game() -> tuple[str, ...]:
    """Whose rails hold every game state this database has.

    The organisers of the three layers that arrange one, in declaration order and
    de-duplicated. Reading as **every** cohort member would answer the same
    question at four times the cost; reading as one would answer a narrower one.
    """

    return tuple(
        dict.fromkeys(
            [one.organiser for one in RAIL_GAMES]
            + [one.organiser for one in ARRANGED_GAMES]
            + [one.organiser for one in PLAYED_GAMES]
        )
    )


def _the_card_this_game_draws(
    standing: GameStanding, plan: Plan | None, *, now: Instant
) -> str:
    """The client's own fold: the standing first, and only then the four rungs.

    An ending is an ending whatever the plan says, which is the seam #324 and #329
    kept crossing — a game whose score is being argued about is not *Game on*
    because its plan happens to be whole. **And the day is not a rung**
    (``docs/adr/0166``): a plan agreed for today is *game on* or *planning* by its
    slots, and the calendar is the card's day row's to say.

    **There is a second transcription of this fold and it is deliberate.**
    ``tests/api/test_the_loop.py`` folds the same ladder over the **wire**, which
    is the half a client actually reads; this one folds it over the domain objects
    a seed run holds. Neither can be written in terms of the other without an
    adapter between a dict and an aggregate, and both name the file that owns the
    names.
    """

    if standing is not GameStanding.AWAITING_ENTRY:
        return {
            GameStanding.AWAITING_ANSWER: "confirm",
            GameStanding.CONFIRMED: "counted",
            GameStanding.UNSCORED: "uncounted",
            GameStanding.NEVER_PLAYED: "never-played",
            GameStanding.CALLED_OFF: "called-off",
        }[standing]
    if plan is not None and plan.agreed_point is not None and plan.agreed_point <= now:
        return "needs-result"
    if plan is not None and plan.slot_count == SLOTS:
        return "game-on"
    return "planning"


def _on_the_rail(game: Game, standing: GameStanding, now: Instant) -> bool:
    """Whether this game still has a card at all.

    The client's ``belongsOnTheRail``: a live game always, and an ended one for a
    day after the last instant its own record dates — the act's own instant for
    a game called off, the entry window closing for a ghost, and the entry
    itself for a game somebody played, read in that order because the three are
    exclusive on the record.
    """

    if standing in (GameStanding.AWAITING_ENTRY, GameStanding.AWAITING_ANSWER):
        return True
    ended = game.called_off_at or game.played_at or entry_closes_at(game.planned_at)
    return now - ended < AN_ENDED_CARD_LASTS


# ---------------------------------------------------------------------------
# The challenge screen: seven standings, and a side each
# ---------------------------------------------------------------------------


async def _refuse_a_standing_only_one_side_can_read(
    paths: ReadPaths,
) -> list[str]:
    """*Each of the seven standings has a challenge both of its sides can open.*

    **The screen is keyed on the standing and the side, and the side is derived**
    — from whether the reader holds the organiser's seat, one list, one code, and
    nothing on the wire carrying a side (``the-loop-screens.md`` §2.1). So an arm
    is reachable only if **both** readings of its standing are: fourteen arms over
    seven standings, and a fixture that reached the organiser's half of each would
    leave seven screens undeveloped. ``CALLED_OFF``'s two are the organiser left
    alone and the leaver, who can still open the court they walked out of.

    Both readings are proved through the **detail read**, which is the screen's
    own and the expensive one — a whole scoring pass per open (``docs/adr/0143``).
    That is the right cost here: what an invitee reads is a pairing recomputed in
    their own direction, and a claim made off the list read would prove the row
    rather than the screen.
    """

    found = await _every_challenge_in_the_database(paths)
    lines: list[str] = []
    for standing in Standing:
        lines.append(await _one_standing_from_both_sides(paths, standing, found))
    return lines


async def _one_standing_from_both_sides(
    paths: ReadPaths, standing: Standing, found: Sequence[StandingChallenge]
) -> str:
    """One standing, opened as its organiser and as somebody they asked."""

    for row in found:
        if row.standing is not standing:
            continue
        organiser = row.challenge.organiser_id
        invitee = next(
            (
                seat.player_id
                for seat in row.challenge.seats
                if seat.player_id is not None and seat.player_id != organiser
            ),
            None,
        )
        if invitee is None:
            continue
        sides = {}
        for side, reader in (("organiser", organiser), ("invitee", invitee)):
            opened = await paths.read_challenge.execute(
                ReadChallengeCommand(challenge_id=row.challenge.id, reader_id=reader)
            )
            sides[side] = opened.standing
        if set(sides.values()) != {standing}:
            raise LoopStateMissing(
                f"challenge {row.challenge.id} reads {standing.value} on the list "
                f"and {sides} on the screen. One challenge cannot be two states, "
                f"so a disagreement here is the detail read and the list read "
                f"folding against two different instants."
            )
        return (
            f"standing · {standing.value} · challenge {row.challenge.id} opens as "
            f"both sides, {len(row.challenge.seats)} seat(s)"
        )
    raise LoopStateMissing(
        f"no challenge in this database reads {standing.value} with somebody on "
        f"it besides its organiser, so that arm of the challenge screen cannot be "
        f"opened on either side. The challenges this fixture sends are the eleven "
        f"relationships (`app/seeds/relationships.py`), the two half-built courts "
        f"and the withdrawn one (`app/seeds/pairs.py`), the games "
        f"(`app/seeds/games.py`, `app/seeds/plans.py`, `RAIL_GAMES` — the "
        f"called-off one among them), and the two courts sent for their ends "
        f"(`THE_COURT_NOBODY_ANSWERED`, `THE_COURT_SOMEBODY_LEFT`)."
    )


async def _every_challenge_in_the_database(
    paths: ReadPaths,
) -> tuple[StandingChallenge, ...]:
    """Every challenge, read as somebody on its court. **Never off the table.**

    There is no *all the challenges* read and there should not be — the reader is
    the gate on every route this context has — so the fixture reads as each seeded
    player in turn and keeps one copy of each challenge it is shown. That is more
    reads than a query would be, and it is the right cost: what the claims then
    assert is what a **screen** draws rather than what a table holds.

    Sorted by id, because a mapping's iteration order would otherwise decide which
    challenge a claim names (``docs/adr/0105`` §1).
    """

    found: dict[UUID, StandingChallenge] = {}
    for email in sorted(paths.players):
        _, standing = await paths.read_challenges.execute(
            ReadChallengesCommand(reader_id=paths.player(email))
        )
        for row in standing:
            found.setdefault(row.challenge.id, row)
    return tuple(found[key] for key in sorted(found))


async def _refuse_a_reader_who_left_and_is_told_they_are_in(
    paths: ReadPaths,
) -> str:
    """*Somebody who left a court that is still open can still read it.*

    The arm the spec set gives two sentences of its own
    (``the-loop-screens.md`` §2.5): a challenge that is still
    ``LINE_UP_INCOMPLETE`` for everybody else, read by the one person who is no
    longer in it. Three things have to be true at once for that screen to exist,
    and each of them is a different rule:

    - **the row stays**, so the explanation for why that pair cannot arrange
      anything yet is somewhere they can read it;
    - **the standing is still the court's**, because the challenge did not end
      when they left — which is why the client cannot key its sentence on the
      standing alone and reads *the reader's own seat*;
    - **nobody draws a card for them**, because the pair released the moment they
      left: *that person is a stranger to you once more* (``docs/adr/0143`` §8).
    """

    for row in await _every_challenge_in_the_database(paths):
        if row.standing is not Standing.LINE_UP_INCOMPLETE:
            continue
        gone = next(
            (
                seat
                for seat in row.challenge.seats
                if seat.player_id is not None and seat.answer is SeatAnswer.DECLINED
            ),
            None,
        )
        if gone is None or gone.player_id is None:
            continue
        theirs = await paths.read_challenge.execute(
            ReadChallengeCommand(
                challenge_id=row.challenge.id, reader_id=gone.player_id
            )
        )
        if theirs.standing is not Standing.LINE_UP_INCOMPLETE:
            raise LoopStateMissing(
                f"the person who left challenge {row.challenge.id} opens it and "
                f"reads {theirs.standing.value}; the court they left is still "
                f"being arranged and the standing is the court's, not theirs."
            )
        stayed = next(
            (
                seat.player_id
                for seat in row.challenge.seats
                if seat.player_id is not None and seat.is_accepted()
            ),
            None,
        )
        if stayed is None:
            continue
        others = await paths.read_challenge.execute(
            ReadChallengeCommand(challenge_id=row.challenge.id, reader_id=stayed)
        )
        if others.card_for(gone.player_id) is not None:
            raise LoopStateMissing(
                f"a member of challenge {row.challenge.id} is drawn a card for "
                f"somebody who declined a seat on it. The pair releases the "
                f"moment a seat leaves, and *that person is a stranger to you "
                f"once more* (`docs/adr/0143` §8)."
            )
        return (
            f"left · challenge {row.challenge.id} still reads "
            f"{theirs.standing.value} to the person who declined a seat on it, "
            f"and nobody on it is drawn a card for them"
        )
    raise LoopStateMissing(
        "no still-open court in this database has somebody on it who declined a "
        "seat, so the challenge screen's *reader who has left* arm cannot be "
        "opened at all. The row that reaches it is `THE_COURT_SOMEBODY_LEFT`."
    )


# ---------------------------------------------------------------------------
# The room: every code, and every one of them in a room that still stands
# ---------------------------------------------------------------------------


async def _refuse_a_system_line_no_room_carries(
    session: AsyncSession, *, settings: Settings, now: Instant
) -> str:
    """*Every system-line code is in a room somebody can still open.*

    **In a room that still stands, which is the whole difficulty.** Every code was
    reachable before this layer and three of them were not *drawable*: a room
    outlives *we played* by forty-eight hours and every played evening in the
    played history is older than that, so ``GAME_PLAYED`` had been written and
    swept — and ``SEAT_ACCEPTED``, ``SEATS_INVITED`` and ``SEAT_LEFT`` need a
    court that grew or shrank **after** its room opened, which nothing here did.

    **Read as a member, by paging backward to the beginning** — the way a person
    scrolling reaches it. The one room this fixture fills past a page holds fifty
    messages above the lines that were written before them, so a claim made off the
    newest page alone would be a claim about what a room *opens on*.
    """

    carried: dict[str, list[str]] = {}
    rooms = await every_room_in_the_database(session, settings=settings, now=now)
    for room in rooms:
        for entry in await read_the_entries(
            session, room=room, settings=settings, now=now
        ):
            if isinstance(entry, SystemLine):
                carried.setdefault(entry.code.value, []).append(
                    str(room.conversation_id)
                )
    missing = [code.value for code in SystemLineCode if code.value not in carried]
    if missing:
        raise LoopStateMissing(
            f"{missing} is a system line no standing room in this database "
            f"carries, across {len(rooms)} room(s) whose newest pages hold "
            f"{sorted(carried)}. A code nothing draws is a sentence in "
            f"`the-words.md` §23 that no developer can look at. The rows that "
            f"reach the membership three are `THE_COURT_SOMEBODY_LEFT` and the "
            f"fill in `app/seeds/loop.py`; the Plan's four are "
            f"`app/seeds/plans.py` — and `PLAN_LOCKED` is the one of those four "
            f"that is an act rather than a slot, so it comes from the row "
            f"declared `locked=True` and from nothing else; `GAME_PLAYED` needs "
            f"a game played inside `CONVERSATION_GRACE`, which is `RAIL_GAMES`."
        )
    return (
        f"lines · all {len(carried)} system-line code(s) are carried by a room "
        f"that still stands: "
        + ", ".join(f"{code} ({len(where)})" for code, where in sorted(carried.items()))
    )


# ---------------------------------------------------------------------------
# What it costs, printed rather than hidden
# ---------------------------------------------------------------------------


def costs(seeded: SeededLoop) -> tuple[str, ...]:
    """What this layer costs, said on the report where somebody will meet it.

    The same disclosure every layer here makes about what it spends: a developer
    who meets one of these as a symptom should meet it here as a sentence first.
    """

    return (
        f"{len(seeded.written.games)} more court(s) are arranged, and two of them are "
        f"**played**: `counted_games`, a run of form and a counterpart tally all "
        f"move for the four members named in `RAIL_GAMES`. They are members of "
        f"the two furthest rings on purpose — out there they are nobody's fixture "
        f"but this one's, where in the nearest ring they would be rows the "
        f"protagonist's own screens are read from.",
        "`THE_COURT_SOMEBODY_LEFT` **never ends**, which is the point of it — a "
        "half-built line-up is where ⚡ *Fill the seats* and *Leave the game* are "
        "drawn — so the pairs it holds are held for the life of the database. Its "
        "four members are in the furthest ring for that reason.",
        "the fill invites one member and they say **no**, which leaves that pair "
        "carrying a `PREVIOUS_DECLINE` and the court exactly where `pairs.py` "
        "asserts it is. A yes could have completed the line-up and taken that "
        "fixture away for good (`docs/adr/0152`), so the no is the cost of not "
        "spending somebody else's.",
        "the card names and the rail's twenty-four-hour tail are the **client's** "
        "and are transcribed here, because the two apps may not import each other "
        "and the only contract between them is HTTP. Nothing checks that the two "
        "copies agree: a rung reordered or a shelf life moved in "
        "`features/plans/domain/gameCard.ts` leaves this claim quietly asserting "
        "the old ladder. What it still catches is the half that actually rots — a "
        "**state** becoming unreachable — and the transcription is eight lines with "
        "the owning file named beside it.",
        "two of the eight cards are **stated absences** rather than reached states, "
        "and they are stated here as well as in the docstring: `uncounted` has no "
        "drawable card at all, since a game is unscored only once both proposal "
        "windows have closed and that is a day after the entry — exactly when an "
        "ended card leaves the rail — so it reaches the game screen through "
        "*Details* and never Now; and `unreadable` is the client's gap for a "
        "standing this build has no word for, which a fixture cannot produce "
        "without inventing an event.",
        "the **held** arm is unreachable in every state this layer reaches, and "
        "that is carried forward rather than quietly dropped: nothing on this "
        "platform can open a case, so a hold is a state component tests drive and "
        "no screen here can be developed against one. It is the map's one stated "
        "exception (`app/seeds/plans.py` says the same of the plan's own writes) "
        "and it goes when something can open a case.",
    )
