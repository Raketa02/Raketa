"""Her played history: past booked games, filled, played, scored and rated (#573).

**The protagonist's record is written on the path the product makes games on.**
Each evening is a game the way the Games deck makes one — ``MakeProposal`` at an
hour Ogrody 33 sells tennis, then ``SayYes`` from her opponent and from her, hers
last, so the last yes **books** it: the seats charged through the run's own fake
provider, a Booking on a free court and the ordinary Game it opens. Then the
result is stated and answered through ``games``' own two acts, and the people she
played rate her through ``AnswerTheCard``. Nothing here opens a table, and
nothing here imports the challenge loop.

**Every act runs on a backdated clock**, at the instant a player would have
taken it: the game made and filled two days before its hour, the score stated
ten minutes after the hour ends and answered ten minutes later, and the card
answered the day after — inside the week it is open for. **Her Level moves
through the rating catch-up**, as every result's does: the API's job folds the
confirmed results on its next run, and this layer only checks that there is
something for it to fold.

**Her week stays as the layers below leave it.** Every evening is played
**before this week began** and long enough ago for every window on it to have
closed. A booked game counts toward its week's *games per week*, so an evening
in this week would hold her deck, her Fill in and her posts to a smaller week
than the layers after this one seat.

**Tennis singles against the three people her history has always been with**
(``cohort-a-12``, ``cohort-c-00``, ``cohort-d-08``). They are already on her
record, so writing her evenings here moves nobody into or out of anybody's
pool. The game is *competitive*, so it is counted. They play in *Tenis na
Ogrodach*, a group she runs at Ogrody 33, because a game is always made in a
group.

**Re-running writes nothing twice.** Once the group holds as many past games of
hers as there are evenings, those are her evenings. Otherwise each evening is
looked for by its hour, and each act is asked for separately off the Game's
record, so a run that died half way picks up where it stopped — on the same
day; a later day places the evenings on later days, beside the ones written.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_confirmed_result_ledger,
    build_court_hours,
    build_domain_event_store,
    build_event_publisher,
    build_fake_payments,
    build_game_repository,
    build_group_code_minter,
    build_home_clubs,
    build_player_bookings,
    build_player_names,
    build_published_sportsmanship,
    build_rated_player_query,
    build_read_home,
    build_settled_courts,
    build_sportsmanship_ledger,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE, hour_start, local_day
from app.modules.games.application.answer_result import AcceptResult, StateResult
from app.modules.games.application.commands import (
    AcceptResultCommand,
    StateResultCommand,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.results import Score, SetScore
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.domain.value_objects import JoinPolicy
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.proposals.domain.deck import GAME_LENGTH, week_of
from app.modules.proposals.domain.home import HomeStatus
from app.modules.sportsmanship.application.answer_the_card import AnswerTheCard
from app.modules.sportsmanship.application.commands import AnswerTheCardCommand
from app.modules.sportsmanship.domain.card import StarsGiven
from app.seeds.bookings import all_say_yes, club_id_of
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS
from app.seeds.cohort import COHORT, PROTAGONIST_HANDLE, STARS_ARE_ONE_TO_FIVE
from app.seeds.groups import group_repository, group_run_by, join_group

#: Where her evenings were played: a club that sells tennis and takes a full
#: game at once, half a kilometre from her.
HISTORY_CLUB: Final = next(club for club in SEED_CLUBS if club.name == "Ogrody 33")
HISTORY_GROUP: Final = "Tenis na Ogrodach"
HISTORY_SPORT: Final = Sport.TENNIS
#: Competitive, so every game is counted.
HISTORY_KIND: Final = SearchMode.COMPETITIVE

#: How far ahead of its hour each game was made and filled.
MADE_AHEAD: Final = timedelta(days=2)
#: When the score is stated, after the hour ends, and when it is answered.
STATED_AFTER: Final = timedelta(minutes=10)
ANSWERED_AFTER: Final = timedelta(minutes=20)
#: How long before the run the latest evening ended: past the score's day for
#: an answer and the entry window's day for a game nobody claimed, so every
#: evening has met its ending by the time anybody reads it.
SETTLED_FOR: Final = timedelta(days=2)
#: How far back the layer looks for a day with a tennis hour before it gives
#: up — a club that sells nothing for a fortnight is a broken fixture.
LOOKS_BACK: Final = timedelta(days=14)
#: When a card is answered: the day after the evening, when it opens, and an
#: hour past the day a silence takes to confirm a score — so the court it is
#: drawn for is settled.
RATED_AFTER: Final = timedelta(days=1, hours=1)
#: The furthest back anything here is written: the latest evening can end up to
#: a week before the run, the oldest is ``LOOKS_BACK`` before that, and its game
#: and the group were made before it. Everybody on an evening has to have
#: committed their profile before then.
WRITTEN_AT_MOST_DAYS_AGO: Final = 7 + LOOKS_BACK.days + MADE_AHEAD.days + 1

#: The two scores an evening is entered with, by the side that won. Absolute,
#: as ``SetScore`` is.
SCORES: Final[Mapping[GameSide, Score]] = {
    GameSide.A: Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
    GameSide.B: Score.of((SetScore(a=4, b=6), SetScore(a=3, b=6))),
}


@final
@dataclass(frozen=True, slots=True)
class Evening:
    """One game she played, as this fixture declares it.

    **The opponent states the score and she answers it**, which is why only the
    opponent is named: the side that states is asked nothing, so she carries an
    *answers about results* strand only because the score is put to her.
    """

    #: A cohort handle.
    opponent: str
    #: ``True`` she won, ``False`` they did, ``None`` they each stated a score
    #: and neither accepted the other's — an evening, not evidence.
    she_won: bool | None
    #: ``False`` is a game nobody said was played: its entry window closed over
    #: it and it reads as never played.
    entered: bool = True
    #: ``False`` is the score she never answered. Silence confirms it anyway.
    answered: bool = True

    @property
    def was_scored(self) -> bool:
        return self.she_won is not None


#: **Her evenings, oldest first, one a day.** Read down the endings rather than
#: the scores, because they are what her record draws:
#:
#: - six games, five of them played — the second is the one nobody claimed, so
#:   *shows up* reads 5 of 6;
#: - five scores put to her and the newest of them unanswered, so *answers about
#:   results* reads 4 of 5;
#: - three people over five counted games, so *opponent variety* reads 3 of 5;
#: - a run of five that mixes wins and losses.
HER_EVENINGS: Final[tuple[Evening, ...]] = (
    Evening(opponent="cohort-d-08", she_won=True),
    Evening(opponent="cohort-c-00", she_won=None, entered=False),
    Evening(opponent="cohort-a-12", she_won=True),
    Evening(opponent="cohort-c-00", she_won=False),
    Evening(opponent="cohort-d-08", she_won=True),
    Evening(opponent="cohort-c-00", she_won=False, answered=False),
)

#: **What her opponents said about her, out of five** — each on the newest
#: evening they shared with her, since only a rater's latest answer stands.
WHAT_THEY_SAID_ABOUT_HER: Final[Mapping[str, int]] = {
    "cohort-c-00": 5,
    "cohort-d-08": 4,
}


class HistoryRefused(RuntimeError):
    """An evening the run could not write, with what the platform said."""


class HistoryIsEmpty(RuntimeError):
    """Her record is missing what this layer promises: a played game, a Level
    the rating catch-up moves, or what somebody said about her."""


@final
@dataclass(frozen=True, slots=True)
class WrittenEvening:
    evening: Evening
    start: Instant
    #: Whether this run booked it, or found it booked already.
    made: bool
    #: What this run did to its result, in the report's words.
    acts: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class SeededHistory:
    group_id: UUID
    created_group: bool
    evenings: tuple[WrittenEvening, ...]
    #: One line per rater: the card answered, or found answered.
    cards: tuple[str, ...]


def _refuse_evenings_she_could_not_have_played() -> None:
    """The declarations against the population, **on import**, so a row that
    could not be written fails before a database is touched."""

    lowest, highest = STARS_ARE_ONE_TO_FIVE
    if SPORT_SPECS[HISTORY_SPORT].players != 2:
        raise RuntimeError(f"{HISTORY_SPORT.value} is not singles: one opponent each")
    her_profile = THE_POPULATED_PLAYER.profile
    if (
        her_profile is None
        or her_profile.committed_days_ago <= WRITTEN_AT_MOST_DAYS_AGO
    ):
        raise RuntimeError(
            f"'{PROTAGONIST_HANDLE}' has to have committed her profile more than "
            f"{WRITTEN_AT_MOST_DAYS_AGO} days ago to have played her evenings"
        )
    played = [evening for evening in HER_EVENINGS if evening.entered]
    for index, evening in enumerate(HER_EVENINGS):
        member = COHORT.by_handle(evening.opponent)
        if member.committed_days_ago <= WRITTEN_AT_MOST_DAYS_AGO:
            raise RuntimeError(
                f"evening {index} can be played up to {WRITTEN_AT_MOST_DAYS_AGO} "
                f"days ago and '{evening.opponent}' committed their profile "
                f"{member.committed_days_ago} day(s) ago — a game before the "
                f"player existed"
            )
        if HISTORY_SPORT not in member.sports:
            raise RuntimeError(
                f"evening {index} is {HISTORY_SPORT.value} against "
                f"'{evening.opponent}', who holds no {HISTORY_SPORT.value} rating"
            )
        if (HISTORY_SPORT.value, PlayIntent.COMPETITIVE.value) not in member.intents:
            raise RuntimeError(
                f"evening {index} is a counted game and '{evening.opponent}' does "
                f"not play {HISTORY_SPORT.value} competitively"
            )
        if not evening.entered and evening.was_scored:
            raise RuntimeError(f"evening {index} was never claimed and has a winner")
        if not evening.answered and not evening.was_scored:
            raise RuntimeError(
                f"evening {index} was left unanswered and has no winner: silence "
                f"confirms a score, so an unanswered one has a winner"
            )
    for rater, stars in WHAT_THEY_SAID_ABOUT_HER.items():
        if not lowest <= stars <= highest:
            raise RuntimeError(f"'{rater}' gives her {stars} stars")
        if all(evening.opponent != rater for evening in played):
            raise RuntimeError(
                f"'{rater}' rates her and played her on no evening that happened"
            )


_refuse_evenings_she_could_not_have_played()


async def write_her_history(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> SeededHistory:
    """Write every evening, oldest first, then what her opponents said.

    **After the cohort, the cards, the clubs and their courts**, which it reads
    and never writes."""

    async with session_factory() as session:
        her = await _player_id(session, THE_POPULATED_PLAYER.email)
        opponents = {
            handle: await _player_id(session, COHORT.by_handle(handle).email)
            for handle in {evening.opponent for evening in HER_EVENINGS}
        }
        club_id = await club_id_of(session, HISTORY_CLUB)
        group_id = await _history_group_of(session, her, club_id)
        played = (
            {}
            if group_id is None
            else await _her_past_games(session, settings, her, group_id, now=now)
        )
        # **Written already, so the evenings are the ones on the record** rather
        # than this run's: a later day would place them on later days.
        written_already = group_id is not None and len(played) >= len(HER_EVENINGS)
        starts = (
            sorted(played)[-len(HER_EVENINGS) :]
            if written_already
            else await evening_starts(session, club_id, now=now)
        )
        created = group_id is None
        if group_id is None:
            group_id = await _the_group(
                session, settings, her, club_id, opponents.values(), at=starts[0]
            )
        written = []
        for evening, start in zip(HER_EVENINGS, starts, strict=True):
            made = start not in played
            if made:
                played[start] = await _book(
                    session,
                    settings,
                    group_id=group_id,
                    club_id=club_id,
                    start=start,
                    players=(opponents[evening.opponent], her),
                )
            acts = await _play(
                session,
                game_id=played[start],
                evening=evening,
                stater=opponents[evening.opponent],
                her=her,
                start=start,
            )
            written.append(WrittenEvening(evening, start, made=made, acts=acts))
        cards = await _rate_her(session, her, opponents, set(played.values()), now=now)
    return SeededHistory(
        group_id=group_id,
        created_group=created,
        evenings=tuple(written),
        cards=cards,
    )


def latest_evening_ends_by(now: Instant) -> Instant:
    """The latest instant an evening may end: before this week began, and long
    enough ago that every ending it can have has been reached."""

    return min(hour_start(week_of(now), 0), instant(now - SETTLED_FOR))


async def evening_starts(
    session: AsyncSession, club_id: UUID, *, now: Instant
) -> list[Instant]:
    """One hour a day, oldest first, walking back from the latest day an evening
    may end on: the first tennis hour the club sold that day, read as it was on
    sale when the game was made."""

    latest = latest_evening_ends_by(now)
    court_hours = build_court_hours(session)
    starts: list[Instant] = []
    day = local_day(latest)
    while len(starts) < len(HER_EVENINGS):
        day_start = hour_start(day, 0)
        if latest - day_start > LOOKS_BACK:
            raise HistoryRefused(
                f"{HISTORY_CLUB.name} sold {len(starts)} day(s) of "
                f"{HISTORY_SPORT.value} in the {LOOKS_BACK.days} days before "
                f"{latest.astimezone(CLUB_ZONE):%a %d %b %H:%M}, and her history "
                f"needs {len(HER_EVENINGS)}"
            )
        on_sale = await court_hours.on_sale(
            [club_id],
            start=day_start,
            end=day_start + timedelta(days=1),
            now=instant(day_start - MADE_AHEAD),
        )
        hour = min(
            (
                one.start
                for one in on_sale
                if one.sport is HISTORY_SPORT
                and one.taking_new_cards
                and one.start + GAME_LENGTH <= latest
            ),
            default=None,
        )
        if hour is not None:
            starts.append(hour)
        day -= timedelta(days=1)
    return sorted(starts)


async def _book(
    session: AsyncSession,
    settings: Settings,
    *,
    group_id: UUID,
    club_id: UUID,
    start: Instant,
    players: tuple[UUID, ...],
) -> UUID:
    """The game made and every yes said, hers last, two days before its hour —
    the fill books it. The Game it opened."""

    answer = await all_say_yes(
        session,
        settings=settings,
        clock=FixedClock(at=instant(start - MADE_AHEAD)),
        provider=build_fake_payments(),
        pool_id=group_id,
        club_id=club_id,
        start=start,
        players=players,
        sport=HISTORY_SPORT,
        kind=HISTORY_KIND,
    )
    if answer is None or answer.booked is None:
        raise HistoryRefused(
            f"her evening at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} filled "
            f"and did not book: {answer!r}"
        )
    booked = {
        game.start: game.game_id
        for game in await build_player_bookings(session, settings=settings).of_player(
            players[-1]
        )
        if game.club_id == club_id and game.game_id is not None
    }
    if start not in booked:
        raise HistoryRefused(
            f"her evening at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} booked "
            f"and opened no Game she can read"
        )
    return booked[start]


async def _play(
    session: AsyncSession,
    *,
    game_id: UUID,
    evening: Evening,
    stater: UUID,
    her: UUID,
    start: Instant,
) -> tuple[str, ...]:
    """*We played, here is the score* — and whatever she did with it. **Each
    act is asked for off the Game's record**, so a resumed run takes only the
    ones still owed. A game nobody claimed is written by writing nothing, and so
    is the answer she never gave."""

    if not evening.entered:
        return ()
    games = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    game = await _loaded(games, game_id)
    winner = stater if evening.she_won is False else her
    winning_side = game.line_up.side_of(winner)
    her_side = game.line_up.side_of(her)
    if winning_side is None or her_side is None:
        raise HistoryRefused(f"game {game_id} does not seat both of them")
    ends = instant(start + GAME_LENGTH)
    acts: list[str] = []
    if game.played_at is None:
        await _state(session, games, ends + STATED_AFTER).execute(
            StateResultCommand(
                game_id=game_id, player_id=stater, score=SCORES[winning_side]
            )
        )
        acts.append("score entered")
        game = await _loaded(games, game_id)
    answered_at = ends + ANSWERED_AFTER
    if not evening.was_scored:
        if her_side not in game.proposals:
            # The counter names the other winner: two sides who disagree.
            await _state(session, games, answered_at).execute(
                StateResultCommand(
                    game_id=game_id, player_id=her, score=SCORES[her_side]
                )
            )
            acts.append("countered")
    elif evening.answered and game.acceptance is None:
        await AcceptResult(
            games=games,
            names=build_player_names(session),
            uow=build_unit_of_work(session),
            clock=FixedClock(at=answered_at),
        ).execute(AcceptResultCommand(game_id=game_id, player_id=her))
        acts.append("accepted")
    return tuple(acts)


def _state(session: AsyncSession, games: GameRepository, at: Instant) -> StateResult:
    return StateResult(
        games=games,
        names=build_player_names(session),
        uow=build_unit_of_work(session),
        clock=FixedClock(at=at),
    )


async def _loaded(games: GameRepository, game_id: UUID) -> Game:
    game = await games.load(game_id)
    if game is None:
        raise HistoryRefused(f"game {game_id} was booked and has no stream")
    return game


async def _rate_her(
    session: AsyncSession,
    her: UUID,
    opponents: Mapping[str, UUID],
    history: set[UUID],
    *,
    now: Instant,
) -> tuple[str, ...]:
    """Each rater's card on the newest of her evenings they shared and played —
    answered the day after it, inside the week the card is open for."""

    courts = build_settled_courts(session)
    ledger = build_sportsmanship_ledger(session)
    lines: list[str] = []
    for rater, stars in sorted(WHAT_THEY_SAID_ABOUT_HER.items()):
        rater_id = opponents[rater]
        shared = [
            court
            for court in await courts.courts_of(rater_id, now=now)
            if court.game_id in history and her in court.others
        ]
        if not shared:
            raise HistoryRefused(
                f"'{rater}' rates her and holds no settled evening of hers"
            )
        latest = max(shared, key=lambda court: court.played_at)
        if await ledger.answered_among(rater_id=rater_id, game_ids=(latest.game_id,)):
            lines.append(f"{rater} · {stars}★ · already answered")
            continue
        await AnswerTheCard(
            clock=FixedClock(at=instant(latest.played_at + RATED_AFTER)),
            courts=courts,
            ledger=ledger,
            unit_of_work=build_unit_of_work(session),
        ).execute(
            AnswerTheCardCommand(
                game_id=latest.game_id,
                rater_id=rater_id,
                given=(StarsGiven(subject_id=her, stars=stars),),
            )
        )
        lines.append(f"{rater} · {stars}★")
    return tuple(lines)


async def _the_group(
    session: AsyncSession,
    settings: Settings,
    her: UUID,
    club_id: UUID,
    opponents: Iterable[UUID],
    *,
    at: Instant,
) -> UUID:
    """Her group at the club, created and joined a day before her first
    evening was made."""

    clock = FixedClock(at=instant(at - MADE_AHEAD - timedelta(days=1)))
    group_id = await CreatePlayerGroup(
        groups=group_repository(session),
        clubs=build_home_clubs(session),
        codes=build_group_code_minter(session),
        uow=build_unit_of_work(session),
        clock=clock,
    ).execute(
        CreatePlayerGroupCommand(
            creator_id=her,
            name=HISTORY_GROUP,
            home_club_id=club_id,
            join_policy=JoinPolicy.ANYONE,
        )
    )
    for opponent in opponents:
        await join_group(session, settings, group_id, opponent, clock)
    return group_id


async def _history_group_of(
    session: AsyncSession, her: UUID, club_id: UUID
) -> UUID | None:
    return await group_run_by(session, her, club_id=club_id, name=HISTORY_GROUP)


async def _her_past_games(
    session: AsyncSession,
    settings: Settings,
    her: UUID,
    group_id: UUID,
    *,
    now: Instant,
) -> dict[Instant, UUID]:
    """Her booked games in the group that ended before this week, by hour."""

    latest = latest_evening_ends_by(now)
    return {
        game.start: game.game_id
        for game in await build_player_bookings(session, settings=settings).of_player(
            her
        )
        if game.pool_id == group_id
        and game.game_id is not None
        and game.start + GAME_LENGTH <= latest
    }


async def _player_id(session: AsyncSession, email: str) -> UUID:
    user = await build_user_repository(session).get_by_email(email)
    if user is None:
        raise RuntimeError(f"{email} is not registered — the accounts run first")
    return user.id


async def assert_her_history(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> str:
    """*Her record has played games, a Level that moves, and stars* — each read
    off her booked evenings through the paths that read them.

    - **played**: her Home, folded as the phone reads it, draws her evenings
      *counted*;
    - **her Level moves**: the confirmed counted results the rating catch-up
      folds hold her evenings, in a sport she is rated in;
    - **stars**: somebody she played has answered a card about her on one of
      them, and her record publishes a figure.

    Any of the three missing fails the run by name."""

    async with session_factory() as session:
        her = await _player_id(session, THE_POPULATED_PLAYER.email)
        club_id = await club_id_of(session, HISTORY_CLUB)
        group_id = await _history_group_of(session, her, club_id)
        where = f"her record · {PROTAGONIST_HANDLE} · {HISTORY_GROUP}"
        if group_id is None:
            raise HistoryIsEmpty(f"{where}: no group, so no evening was written")
        home = await build_read_home(
            session, settings=settings, clock=FixedClock(at=now)
        ).execute(her)
        evenings = [
            card
            for card in home.games
            if card.game.pool_id == group_id and card.game.game_id is not None
        ]
        counted = [card for card in evenings if card.state.status is HomeStatus.COUNTED]
        if not counted:
            raise HistoryIsEmpty(
                f"{where} draws no played game: her evenings read "
                f"{sorted(card.state.status.value for card in evenings)}"
            )
        history = {
            card.game.game_id for card in evenings if card.game.game_id is not None
        }
        moving = [
            game
            for game in await build_confirmed_result_ledger(
                session
            ).confirmed_counted_results(now=now)
            if game.game_id in history and her in (*game.winners, *game.losers)
        ]
        rated = await build_rated_player_query(session).estimates_for(
            [her], sport=HISTORY_SPORT
        )
        if not moving or her not in rated:
            raise HistoryIsEmpty(
                f"{where}: her Level does not move — {len(moving)} confirmed "
                f"counted result(s) of hers for the rating catch-up to fold, and "
                f"she is {'' if her in rated else 'not '}rated in "
                f"{HISTORY_SPORT.value}"
            )
        ledger = build_sportsmanship_ledger(session)
        raters = [
            rater
            for rater, _ in sorted(WHAT_THEY_SAID_ABOUT_HER.items())
            if await ledger.answered_among(
                rater_id=await _player_id(session, COHORT.by_handle(rater).email),
                game_ids=tuple(history),
            )
        ]
        published = await build_published_sportsmanship(session).published_for(her)
        if not raters or published is None:
            raise HistoryIsEmpty(
                f"{where} has no stars: {len(raters)} card(s) answered about her "
                f"on her evenings, and her record publishes "
                f"{'nothing' if published is None else 'a figure'}"
            )
    return (
        f"{where}: {len(counted)} of {len(evenings)} evening(s) counted, "
        f"{len(moving)} result(s) for the rating catch-up to move her Level on, "
        f"{len(raters)} rater(s) on them — {published.average:.1f} / 5 over "
        f"{published.raters}"
    )


def history_lines(seeded: SeededHistory) -> list[str]:
    """The report's section: her evenings, and what was said about her."""

    lines = [
        f"Her played history — booked {HISTORY_SPORT.value.lower()} at "
        f"{HISTORY_CLUB.name} in {HISTORY_GROUP} "
        f"({'created' if seeded.created_group else 'already there'}):"
    ]
    for written in seeded.evenings:
        evening = written.evening
        ending = (
            "never claimed"
            if not evening.entered
            else "nobody agreed a score"
            if evening.she_won is None
            else ("she won" if evening.she_won else "she lost")
            + ("" if evening.answered else ", unanswered and confirmed by silence")
        )
        state = "booked" if written.made else "already booked"
        acts = f", {', '.join(written.acts)}" if written.acts else ""
        lines.append(
            f"  {written.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · against "
            f"{evening.opponent} · {state}{acts} · {ending}"
        )
    lines.extend(f"  {line}" for line in seeded.cards)
    return lines
