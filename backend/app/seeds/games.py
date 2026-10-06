"""Write the played history: real challenges, really accepted, really scored.

**No longer the runner's** (#573): every declared game is written as a past
booked game by ``app/seeds/booked_history.py``. The plans and loop layers still
borrow its court helpers, and it goes with them.

**A seeded game is not a row and cannot be one** (``docs/adr/0029``). It is a
challenge sent off a search that really showed the people it seats, every seat
answered, the line-up completing — which is what opens the game, inline, in the
transaction of the acceptance that filled the last seat — and then a score
stated and answered. Nothing here opens a table, and nothing here calls
``games`` directly except through the two acts a player performs on a result.

**This is the one layer of the seed that writes in the past, and the reason is
the clock.** A relationship is a thing happening now: a seat's own answer window
has to start when the run starts or the court is over before it is read. A
played game is a thing that *happened* — a score is confirmed when its window
closes and two scores nobody agreed leave the game unscored when both of theirs
do, so a game seeded an hour ago is a game still awaiting an answer, and the
card the fixture exists for would be empty. So each game is written on its own
clock, at the instant ``cohort.py`` declares for it, through the same use cases
at that instant. Nothing is faked forward: the acceptance really is inside its
seat's day, because that day started a moment earlier on the same clock.

**Every game costs a real search run as the organiser**, and the cost is the
check — the rule ``pairs.py`` already runs on. A send cites the search its court
was built on and ``court_origin`` refuses a citation the record does not bear
out, so *these two played* means the organiser could genuinely see them through
gender, level and radius. A fixture that wrote the game would prove that a game
can be written.

**Re-running writes nothing twice.** A game is looked for by its line-up before
anything is sent: one arrangement is one game, ``challenges`` refuses a second
open challenge for a pair, and both of those would surface as an exception half
way through rather than as an idempotent no-op. The probe reads ``played_at``
rather than a standing, because *has the result been entered* is a fact about the
record while a standing is a fact about an instant — and the instant this run
folds against is not the one the first run did.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, Mapping, Protocol, Sequence, final, runtime_checkable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import build_candidate_source
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.challenges.application.commands import AnswerSeatCommand
from app.modules.challenges.application.read_challenges import ReadChallengesCommand
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.standing import ENDED
from app.modules.games.application.commands import (
    AcceptResultCommand,
    StateResultCommand,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide
from app.modules.games.domain.results import Score, SetScore
from app.modules.matchmaking.domain.deck import mode_for_intent
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import PhotoStorage
from app.seeds.clock import days_before
from app.seeds.cohort import (
    COHORT,
    EVERY_PLAYED_GAME,
    Cohort,
    PlayedGame,
)
from app.seeds.pool_history import (
    NAMED_ACCOUNTS,
    THE_POOL_HAS_A_RECORD,
    address_of,
)
from app.seeds.paths import (
    ReadPaths,
    read_paths,
    the_ephemeral_store,
    returned_ids,
    run_a_shortlist,
    send_a_court,
    tick_the_tail_to_catch_up,
)

#: How far apart two moments may be and still be the same declared evening. A
#: day is the declaration's own unit, so half of one either side is the widest
#: window that cannot reach the row before or the row after.
_A_DECLARED_EVENING: Final = timedelta(hours=12)

#: The two scores a seeded game is entered with, one per winning side.
#:
#: **Derived from the declared winner rather than declared beside it.** What
#: ``cohort.json`` commits is *who won*, which is what a player did; the sets are
#: the shape of that win, and a committed set score would be a second input
#: saying the same thing — with the two free to disagree.
#:
#: Absolute and never relative, because :class:`SetScore` is: a score stored from
#: one side's point of view would have to be flipped by whoever read it next.
SCORES: Mapping[GameSide, Score] = {
    GameSide.A: Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
    GameSide.B: Score.of((SetScore(a=4, b=6), SetScore(a=3, b=6))),
}


@runtime_checkable
class Arrangement(Protocol):
    """The half of a declared game that is about **who is on the court**.

    ``PlayedGame`` satisfies it and so does the Plan layer's own declaration, and
    that is the whole reason it exists: *send a court the organiser could really
    see, and answer every seat on it* is one act, and the two layers differ only
    in what they do **after** the line-up completes. A second copy of the send
    would be a second opinion about whether an origin has to resolve.

    It is structural rather than a base class because the two declarations are
    otherwise nothing alike — one carries a moment and a winner, the other a slot
    count — and a shared parent would be a place for the next field to be added
    to both.
    """

    @property
    def sport(self) -> str: ...

    @property
    def side_a(self) -> tuple[str, ...]: ...

    @property
    def side_b(self) -> tuple[str, ...]: ...

    @property
    def organiser(self) -> str: ...

    @property
    def players(self) -> tuple[str, ...]: ...


class Organiser(Protocol):
    """Whoever sends a court — the three things sending one costs.

    Who they are for a message, the address a search is run as, and the
    declaration that decides the mode, which decides whether the game that
    follows is counted at all. A ``CohortMember`` satisfies it, and so does the
    named account the pool's own history is organised by (:class:`_Organiser`);
    structural for :class:`Arrangement`'s reason, so that the two layers that
    declare arrangements hand the send whichever population their organiser
    came out of.
    """

    @property
    def handle(self) -> str: ...

    @property
    def email(self) -> str: ...

    @property
    def intents(self) -> tuple[tuple[str, str], ...]: ...


class GameRefused(RuntimeError):
    """A game the run could not write, with the reason the platform gave.

    A ``RuntimeError`` for ``EdgeRefused``'s reason, and it is raised rather than
    warned for the same one: a played game that silently failed to exist is a
    card block developed against a state nobody produced, and the assertion that
    caught it would name a pool rather than a game.
    """


@final
@dataclass(frozen=True, slots=True)
class WrittenGame:
    """One game after the run, and the line the report prints for it."""

    game: PlayedGame
    line: str


@final
@dataclass(frozen=True, slots=True)
class SeededGames:
    """Everything the played history wrote, and what it cost."""

    games: tuple[WrittenGame, ...]
    costs: tuple[str, ...]


async def write_the_played_history(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Cohort = COHORT,
    photos: PhotoStorage | None = None,
) -> SeededGames:
    """Write every declared game, oldest first, and report what each one cost.

    **Oldest first is legibility and not a rule**, and it is worth saying which:
    the run of form is ordered by the provider on the instant each game was
    played, so writing them in any order produces the same row of squares. What
    the order buys is that the report reads in the same direction the card does,
    and that a reader of this loop does not have to hold *the newest is which*
    in their head.

    The tail is ticked first, because a search reads the candidate index and the
    index has not seen the population this run just wrote. ADR-0110 makes the
    tick safe and cheap to repeat, which is what lets it be a barrier here as
    well as before the relationships and before the assertions.
    """

    await tick_the_tail_to_catch_up(session_factory, settings=settings)
    candidates = build_candidate_source(session_factory=session_factory)
    await candidates.refresh()

    written: list[WrittenGame] = []
    async with the_ephemeral_store(settings) as redis:
        async with session_factory() as session:
            # **Looked up once for the whole layer.** Every game builds its own
            # paths — one per instant, because the clock is a constructor
            # argument — and the address-to-id map is the one part of that
            # wiring that is a query rather than an object.
            players: Mapping[str, UUID] | None = None
            for game in sorted(
                (*EVERY_PLAYED_GAME, *THE_POOL_HAS_A_RECORD),
                key=lambda one: -one.played_days_ago,
            ):
                paths_now = days_before(now, game.played_days_ago).now()
                paths = await read_paths(
                    session,
                    settings=settings,
                    candidates=candidates,
                    cohort=cohort,
                    now=paths_now,
                    redis=redis,
                    players=players,
                    photos=photos,
                )
                players = paths.players
                written.append(
                    WrittenGame(
                        game=game,
                        line=await _write_one(paths, game, cohort, when=paths_now),
                    )
                )

    return SeededGames(games=tuple(written), costs=_costs(written))


def _costs(written: Sequence[WrittenGame]) -> tuple[str, ...]:
    """What the played history costs, said on the report rather than hidden.

    The same disclosure ``pairs.py`` makes about the deal it spends: a developer
    who meets one of these as a symptom should meet it here as a sentence first.
    """

    # **Distinct, because a pair may now share two courts.** A completed
    # line-up releases its pair, so the protagonist's history plays three people
    # five times — and a list that counted the same two names twice would say the
    # released set is larger than it is.
    pairs = sorted(
        {" & ".join(sorted(pair)) for one in written for pair in one.game.pairs}
    )
    return (
        f"a completed line-up releases its pair (`docs/adr/0142` §1), so the "
        f"{len(pairs)} pair(s) that have played are back on each other's "
        f"surfaces — each carrying an ACCEPTED tally, which is what makes "
        f"PREVIOUS_ACCEPT drawable on their cards. `pool_history.py` is what "
        f"gives that code its witness: she **organises** most of its courts, "
        f"so the people in her pool accepted a seat from her and their cards "
        f"carry the tally — which is why `screens.py` promises the code "
        f"rather than naming it in `CANNOT_BE_DRAWN`. Played: "
        + ", ".join(pairs)
        + ".",
    )


async def _write_one(
    paths: ReadPaths, game: PlayedGame, cohort: Cohort, *, when: Instant
) -> str:
    """One game, from whatever state the database is already in."""

    sport = Sport(game.sport)
    organiser = _organiser_of(game, cohort)
    standing = await the_game_already_there(paths, game, cohort, when=when)
    if standing is None:
        standing = await arrange_the_court(
            paths, game, cohort, sport, organiser, when=when
        )
        built = "arranged and played"
    else:
        built = "already played"

    # **The kind is this layer's requirement and not the arrangement's**, which
    # is why it is checked here rather than inside the send. A friendly is a
    # perfectly good arrangement — the Plan layer wants one either way — and what
    # a *played history* needs is a game a card counts. Asked on both paths, so a
    # database whose first run built a friendly is caught on the second.
    if standing.kind is not GameKind.COUNTED:
        raise GameRefused(
            f"the game '{organiser.handle}' arranged is a {standing.kind.value} "
            f"and the played history is for counted games — *a friendly is a "
            f"thing people choose*, and a counted game is what a card counts. "
            f"The kind follows the mode of the search the court was built on, "
            f"which follows the organiser's own declared Play intent."
        )

    # **A ghost is written by not writing anything**, which is the only way to
    # write one: nobody said *we played*, the entry window closed over the
    # arrangement, and the platform now reads it as never played. An act here
    # would be refused — `the_entry_window_has_closed` — so the absence is both
    # the declaration and the mechanism.
    entered = (
        "never claimed"
        if game.was_a_ghost
        else await _enter_the_result(paths, game, standing, cohort)
    )
    return (
        f"{sport.value.lower()} · {' & '.join(game.side_a)} against "
        f"{' & '.join(game.side_b)}, {game.played_days_ago} day(s) ago · "
        f"{built}, {entered} · " + _ending(game)
    )


def _ending(game: PlayedGame) -> str:
    """Which of the three endings this row is, in the words the report prints."""

    if game.was_a_ghost:
        return "a ghost — the entry window closed over it"
    if not game.was_scored:
        return "nobody agreed a score"
    if not game.answered:
        return f"side {game.won_by} won, unanswered and confirmed by silence"
    return f"side {game.won_by} won"


async def the_game_already_there(
    paths: ReadPaths,
    game: Arrangement,
    cohort: Cohort,
    *,
    when: Instant | None = None,
) -> Game | None:
    """This declared game, if a previous run already arranged it.

    Found **by its line-up and its day**, never by an id: the id is minted by the
    write path and a fresh database mints a different one, which is the promise
    every other probe in the seed makes.

    **The day is half the key when the caller supplies one, and the played
    history always does.** The Plan and loop layers declare one arrangement per
    pair and probe by line-up alone; the played history cannot, and the reason
    it cannot was not always there. A completed
    line-up releases its pair (``docs/adr/0142`` §1, #343), so two people may
    play twice — which is what lets three opponents carry five counted games on
    the protagonist's record. By line-up alone, the second evening with the same
    person *is* the first one: the probe finds it, the run writes nothing, and
    the fixture silently declares a game it never wrote.

    A **day** rather than an instant, because the declaration's own granularity
    is ``played_days_ago`` and an equality on a timestamp is a bet on what a
    round trip through Postgres preserves.
    """

    wanted = frozenset(_ids(paths, cohort, game.players))
    organiser = player_of(paths, cohort, game.organiser)
    _, standing = await paths.read_games.execute(organiser)
    for row in standing:
        # **The people who were on the court, the departed included.** A
        # called-off game's leaver has been vacated (``docs/adr/0162`` §3), so
        # its line-up alone is one seat short of the declaration and a second
        # run would arrange the game again; ``departed`` is whose leaving
        # opened the seats that are open now, and a re-seat empties it.
        on_the_court = row.game.line_up.players | row.game.departed
        if (
            row.game.sport.value == game.sport
            and on_the_court == wanted
            and (when is None or _on_the_same_day(row.game.planned_at, when))
        ):
            return row.game
    return None


def _on_the_same_day(one: Instant, other: Instant) -> bool:
    """Whether two moments are the same declared evening.

    Half a day either side rather than a calendar date, because the fixture
    counts backwards in whole days from the run's own *now* — which is a time of
    day, not midnight — so two runs an hour apart put the same declared evening
    on either side of a date boundary.
    """

    return abs(one - other) < _A_DECLARED_EVENING


async def arrange_the_court(
    paths: ReadPaths,
    game: Arrangement,
    cohort: Cohort,
    sport: Sport,
    organiser: Organiser,
    *,
    when: Instant | None = None,
) -> Game:
    """Send the court if nobody has, then answer every seat still outstanding.

    **The probe comes before the search, deliberately** — the lesson
    ``pairs.py`` already paid for. Once a court has been sent the pair is gated,
    so the organiser can no longer see the people they invited: a run that
    searched first would fail its second pass with a message about a pool, when
    what actually happened is that the first pass died between the send and the
    last acceptance.

    **The last acceptance is what opens the game**, and there is no other way to:
    ``challenges`` hands a completed line-up over inline, so this function's last
    act is an accept and its answer is a game it then has to go and find.
    """

    court = await _the_court_already_sent(paths, game, cohort, when=when)
    if court is None:
        court = await _send_the_court(paths, game, cohort, sport, organiser, when=when)
    for seat in court.seats:
        if seat.player_id is not None and seat.is_awaiting():
            await paths.accept.execute(
                AnswerSeatCommand(challenge_id=court.id, player_id=seat.player_id)
            )

    opened = await the_game_already_there(paths, game, cohort, when=when)
    if opened is None:
        raise GameRefused(
            f"every seat on challenge {court.id} was accepted and no game "
            f"stands for it. A completed line-up opens a game inline, in the "
            f"transaction of the acceptance that filled the last seat, so an "
            f"absence here is that hand-over having stopped happening."
        )
    return opened


async def _enter_the_result(
    paths: ReadPaths, game: PlayedGame, standing: Game, cohort: Cohort
) -> str:
    """*We played, here is the score* — and then whatever the other side did.

    Two shapes and they are the two states the card is for. A game these people
    **agreed** is a score from one side and an acceptance from across the net; a
    game they never agreed is two scores and no acceptance, which is the
    disagreement this platform refuses to arbitrate and leaves as *an evening,
    not evidence*.

    The acceptance is made at the same instant as the proposal, and it settles
    nothing then: the grace runs from the **proposal**, so what confirms this
    result is the six hours that have passed since — on the run's own now, days
    later. Advancing a clock is the only way to observe that, which is the whole
    reason a played game is written in the past.

    **Each act is asked for separately, off the record rather than off a
    standing.** A run that died between the score and the answer to it left a
    game whose *standing* at this instant is a fact about a clock, and re-reading
    one would answer a different question every day; ``played_at``, the
    proposals and the acceptance are the record, and they say exactly which of
    the two acts is still owed. That is what makes an interrupted run resumable
    rather than a database to drop.
    """

    speaker = player_of(paths, cohort, game.side_a[0])
    answerer = player_of(paths, cohort, game.side_b[0])
    acts: list[str] = []

    if standing.played_at is None:
        await paths.state_result.execute(
            StateResultCommand(
                game_id=standing.id,
                player_id=speaker,
                score=SCORES[GameSide.A if game.won_by != "B" else GameSide.B],
            )
        )
        acts.append("score entered")

    if game.was_scored:
        # **The silence is written by not writing**, exactly as the ghost is one
        # layer up. A score nobody answers is confirmed by its own window
        # closing, so the game is scored either way and the difference lands
        # where it belongs: on *answers about results*, against everybody who
        # was on the side that was asked.
        if standing.acceptance is None and game.answered:
            await paths.accept_result.execute(
                AcceptResultCommand(game_id=standing.id, player_id=answerer)
            )
            acts.append("accepted from across the net")
        elif not game.answered:
            acts.append("left unanswered across the net")
    elif GameSide.B not in standing.proposals:
        # **The counter, and it has to name the other winner.** A second score
        # agreeing with the first is a correction nobody objected to; what leaves
        # a game unscored is two sides who disagree, and the disagreement is the
        # whole of what this row exists to exhibit.
        await paths.state_result.execute(
            StateResultCommand(
                game_id=standing.id, player_id=answerer, score=SCORES[GameSide.B]
            )
        )
        acts.append("countered from across the net")

    return ", ".join(acts) if acts else "result already settled"


async def _the_court_already_sent(
    paths: ReadPaths,
    game: Arrangement,
    cohort: Cohort,
    *,
    when: Instant | None = None,
) -> Challenge | None:
    """The court this game was sent as, if a run already sent it.

    Found by **who is seated on it, in which sport, and — when the caller
    supplies a day — on which day** rather than by an id, for
    :func:`the_game_already_there`'s reason: an id is minted
    by the write path and a fresh database mints a different one. Read through
    the organiser's own challenge list, which is the screen a player reads their
    courts on.

    **The day is half the key here too, and leaving it out cost a whole
    afternoon.** A completed line-up is not *ended* — the arranging finished, so
    the challenge stands and the pair is released — which means the court a pair
    played on last week still answers *who is seated on it* for the court they
    played on yesterday. The probe returned the older one, its seats were long
    since accepted so nothing was sent, and the run then failed looking for a
    game on a day that court was never played on.
    """

    organiser = player_of(paths, cohort, game.organiser)
    wanted = frozenset(_ids(paths, cohort, game.players))
    _, standing = await paths.read_challenges.execute(
        ReadChallengesCommand(reader_id=organiser)
    )
    for row in standing:
        if row.challenge.organiser_id != organiser or row.standing in ENDED:
            continue
        if row.challenge.sport.value != game.sport:
            continue
        if when is not None and not _on_the_same_day(row.challenge.opened_at, when):
            continue
        seated = frozenset(
            seat.player_id
            for seat in row.challenge.seats
            if seat.player_id is not None
        )
        if seated == wanted:
            return row.challenge
    return None


async def _send_the_court(
    paths: ReadPaths,
    game: Arrangement,
    cohort: Cohort,
    sport: Sport,
    organiser: Organiser,
    *,
    when: Instant | None = None,
) -> Challenge:
    """One real search run as the organiser, and the court it earns.

    **The search and the refusal are one act**, exactly as they are for an edge:
    a send cites the search that surfaced the person and ``court_origin``
    refuses a citation the record does not bear out, so a search that did not
    show them is not an origin — and *these two played* would be a claim about a
    pair the platform says cannot see each other.
    """

    record = await run_a_shortlist(
        paths, organiser.email, sport, mode_of(paths, organiser, sport)
    )
    shown = returned_ids(record)
    missing = sorted(
        handle
        for handle in game.players[1:]
        if player_of(paths, cohort, handle) not in shown
    )
    if missing:
        # **The list it did show is on the message**, because the question a
        # declaration failure actually asks is *who could I have written down
        # instead* — and answering it from a gate histogram alone means running
        # the search again by hand.
        offered = sorted(
            member.handle
            for member in cohort.members
            if paths.players.get(email_of(cohort, member.handle)) in shown
        )
        raise GameRefused(
            f"'{organiser.handle}' ran their own {sport.value} search and it "
            f"never showed {missing}, over {record.counts.n_generated} "
            f"generated and {record.counts.n_returned} returned — it showed "
            f"{offered}. A send cites "
            f"the search that showed the person, so this game cannot be "
            f"arranged at all — and the pair it declares is a pair the platform "
            f"says cannot see each other. "
            f"Gates: {dict(sorted(record.counts.excluded_by_gate.items()))}. "
            f"The row is a declared arrangement — `PLAYED_GAMES` in "
            f"`app/seeds/cohort.py`, `THE_POOL_HAS_A_RECORD` in "
            f"`app/seeds/pool_history.py`, or `ARRANGED_GAMES` in "
            f"`app/seeds/plans.py`."
        )

    await send_a_court(
        paths,
        organiser=organiser.email,
        sport=sport,
        record=record,
        invitees=[email_of(cohort, handle) for handle in game.players[1:]],
    )
    sent = await _the_court_already_sent(paths, game, cohort, when=when)
    if sent is None:
        raise GameRefused(
            f"'{organiser.handle}' sent a {sport.value} court citing search "
            f"{record.id} and their own list does not carry it back. That list "
            f"is the screen a player reads their courts on."
        )
    return sent


@final
@dataclass(frozen=True, slots=True)
class _Organiser:
    """Whoever sent the court, from whichever population they came out of.

    **Three fields, because three are what sending one costs**: who they are for a
    message, the address a search is run as, and the declaration that decides the mode —
    which decides whether the game that follows is counted at all. A ``CohortMember``
    satisfied all three while every organiser was one; the pool's own history is
    organised by the protagonist, who is a named account rather than a row in a
    distribution.
    """

    handle: str
    email: str
    intents: tuple[tuple[str, str], ...]


def _organiser_of(game: PlayedGame, cohort: Cohort) -> _Organiser:
    """The sender of this court, looked up in whichever list holds them."""

    if game.organiser.startswith("cohort-"):
        member = cohort.by_handle(game.organiser)
        return _Organiser(
            handle=member.handle, email=member.email, intents=member.intents
        )
    account = NAMED_ACCOUNTS.get(game.organiser)
    if account is None or account.profile is None:
        raise GameRefused(
            f"'{game.organiser}' organises a game and holds no profile, so there is no "
            f"declaration to run their search under and no court for them to send."
        )
    return _Organiser(
        handle=account.slug,
        email=account.email,
        intents=tuple(
            (sport.value, intent.value) for sport, intent in account.profile.intents
        ),
    )


def mode_of(paths: ReadPaths, member: Organiser, sport: Sport) -> SearchMode:
    """Which weight vector this organiser's own declaration puts them under.

    **Derived and never tabled**, the rule ``pairs.py`` states: a member takes
    whatever the intent cycle gave them, and a search run under a mode they never
    asked for would score them against a tolerance they never chose. It also
    decides whether the game is *counted* — a court built on a for-fun search is
    a friendly, and a friendly was never evidence about anybody.
    """

    for declared, intent in member.intents:
        if declared == sport.value:
            return mode_for_intent(PlayIntent(intent), paths.ruleset.intent)
    raise GameRefused(
        f"'{member.handle}' organises a {sport.value} game and declares "
        f"{[one for one, _ in member.intents]}. Play intent is declared per "
        f"sport (ADR-0094), so there is no mode to run this under."
    )


def email_of(cohort: Cohort, handle: str) -> str:
    """The address behind a handle, from **any** of the three populations.

    ``pool_history`` owns the walk, because it is the only module that can see all
    three: the cohort is a distribution, the catalog is a set of named states and the
    eleven are pair fixtures, and a court seats whoever it seats. This is the one seam
    that needed to stop caring which list a name came from.
    """

    return address_of(handle, cohort)


def player_of(paths: ReadPaths, cohort: Cohort, handle: str) -> UUID:
    """The id the write path minted for the member behind this handle.

    Spelled once because the walk from a handle to an id is two steps and the two
    layers that declare arrangements make it a dozen times: a declaration names
    handles, an address is derived from one, and the id is what the write path
    minted for that address.
    """

    return paths.player(email_of(cohort, handle))


def _ids(
    paths: ReadPaths, cohort: Cohort, handles: Sequence[str]
) -> tuple[UUID, ...]:
    return tuple(player_of(paths, cohort, handle) for handle in handles)
