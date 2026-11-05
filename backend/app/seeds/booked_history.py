"""The played history: past booked games, filled, played, scored and rated (#573).

**Every game the seed says somebody played is written on the path the product
makes games on.** That is the protagonist's own evenings, which fill the record
she reads about herself, and every declared game the runner hands in: the
cohort's own (``PLAYED_GAMES``). Each is a game the way the Games deck makes
one — ``MakeProposal`` at an hour Ogrody 33 sells, then ``SayYes`` from
everybody on it, so the last yes **books** it: the seats held through the
run's own provider, a Booking on a free court and the ordinary Game it
opens — and **the cut-off job runs at the club's cut-off**, as the API's would
have, so every past game's shares are taken and settled (#637). Then the result
is stated and answered through ``games``' own two acts. Nothing here opens a
table, and nothing here imports the challenge loop.

**A game is always made in a group**, so she runs one per sport at Ogrody 33 —
*Tenis na Ogrodach* and *Padel na Ogrodach* — and everybody a game seats joins
the one for its sport. **The fill draws the sides** for the most even game, so a
declared doubles partnership is a declaration of who was on the court and who
won, never of who stood beside whom.

**Every act runs on a backdated clock**, at the instant a player would have
taken it: the game made and filled two days before its hour — or an hour after
the last of its players committed, where that is later — the score stated ten
minutes after the hour ends and answered ten minutes later. **Her Level moves
through the rating catch-up**, as every result's does: the API's job folds the
confirmed results on its next run, and this layer only checks that there is
something for it to fold.

**Her week stays as the layers below leave it.** A booked game counts toward its
week's *games per week*, so every game is played **before this week began** and
long enough ago for every window on it to have closed. The one exception is a
game somebody on it could not have played before the week, because they
committed their profile inside it: that game is played this week, on the day it
was declared, and the report says so.

**Her evenings** are tennis singles against the three people her history has
always been with (``cohort-a-12``, ``cohort-c-00``, ``cohort-d-08``), one a day
walking back from the last day before her week, and the people she played rate
her through ``AnswerTheCard`` the day after. **The declared games** keep the day
they were declared for wherever that is before her week; the ones declared
inside it are played on the last day before it instead.

**Re-running writes nothing twice.** A game is looked for by who was on it in its
group — the n-th declared game for the same people is the n-th booking they
share — and each act is asked for separately off the Game's record, so a run that
died half way picks up where it stopped. A later day places a fresh game only
where none was written.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_confirmed_result_ledger,
    build_court_hours,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_group_code_minter,
    build_home_clubs,
    build_player_bookings,
    build_play_intent_declaration_repository,
    build_player_names,
    build_published_sportsmanship,
    build_rated_player_query,
    build_read_booking_details,
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
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.domain.value_objects import GroupName, JoinPolicy
from app.modules.player_profile.application.commands import (
    DeclarePlayIntentCommand,
)
from app.modules.player_profile.application.declare_play_intent import (
    DeclarePlayIntent,
)
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.proposals.domain.deck import GAME_LENGTH, week_of
from app.modules.proposals.domain.home import HomeStatus
from app.modules.sportsmanship.application.answer_the_card import AnswerTheCard
from app.modules.sportsmanship.application.commands import AnswerTheCardCommand
from app.modules.sportsmanship.domain.card import StarsGiven
from app.seeds.bookings import all_say_yes, club_id_of, the_cut_off_came
from app.seeds.catalog import THE_POPULATED_PLAYER, SeedAccount
from app.seeds.clock import FixedClock, days_before
from app.seeds.clubs import SEED_CLUBS
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.cohort import (
    COHORT,
    PROTAGONIST_HANDLE,
    STARS_ARE_ONE_TO_FIVE,
    PlayedGame,
)
from app.seeds.groups import group_repository, group_run_by, join_group
from app.seeds.sportsmanship import RATED_AFTER

#: Where every game was played: a club that sells padel and tennis and takes a
#: full game at once, half a kilometre from her.
HISTORY_CLUB: Final = next(club for club in SEED_CLUBS if club.name == "Ogrody 33")
#: The group each sport's games are made in, run by her.
HISTORY_GROUPS: Final[Mapping[Sport, str]] = {
    Sport.TENNIS: "Tenis na Ogrodach",
    Sport.PADEL: "Padel na Ogrodach",
}
#: Her evenings' sport.
HISTORY_SPORT: Final = Sport.TENNIS
# Refused on import, through the domain's own value object, as ``groups.py``'s
# names are.
for _name in HISTORY_GROUPS.values():
    GroupName(_name)
#: Competitive, so every game is counted.
HISTORY_KIND: Final = SearchMode.COMPETITIVE
#: **A counted game was played competitively by everybody on it**, and since
#: Q127 a yes is held to the kind its player's intent wants. Somebody on one
#: whose own intent in the sport is For fun — hers in tennis — played it
#: competitively and switched after: their intent is declared competitive
#: before the games are made and their own declared again once every game is
#: written, both at the run's instant and on the You tab. A declaration that
#: changes nothing records nothing, so a second run records neither.
HISTORY_INTENT: Final = PlayIntent.COMPETITIVE
#: The one intent that does not want ``HISTORY_KIND``.
PLAYED_FOR_FUN: Final = PlayIntent.FOR_FUN

#: How far ahead of its hour each game was made and filled.
MADE_AHEAD: Final = timedelta(days=2)
#: How soon after the last of its players committed a game could be made.
AFTER_THE_LAST_COMMIT: Final = timedelta(hours=1)
#: When the score is stated, after the hour ends, and when it is answered.
STATED_AFTER: Final = timedelta(minutes=10)
ANSWERED_AFTER: Final = timedelta(minutes=20)
#: How long before the run the latest game ended: past the score's day for an
#: answer and the entry window's day for a game nobody claimed, so every game
#: has met its ending by the time anybody reads it.
SETTLED_FOR: Final = timedelta(days=2)
#: How far back the layer walks for a free hour before it gives up — a club
#: that sells nothing for a fortnight is a broken fixture.
LOOKS_BACK: Final = timedelta(days=14)
#: The furthest back one of her evenings is written: the latest can end up to a
#: week before the run, the oldest is ``LOOKS_BACK`` before that, and its game
#: was made before it. Everybody on one has to have committed before then.
WRITTEN_AT_MOST_DAYS_AGO: Final = 7 + LOOKS_BACK.days + MADE_AHEAD.days

#: The two scores a game is entered with, by the side that won. Absolute, as
#: ``SetScore`` is.
SCORES: Final[Mapping[GameSide, Score]] = {
    GameSide.A: Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
    GameSide.B: Score.of((SetScore(a=4, b=6), SetScore(a=3, b=6))),
}


@final
@dataclass(frozen=True, slots=True)
class Evening:
    """One game she played, as this fixture declares it.

    **The opponent states the score and she answers it**, which is why only the
    opponent is named: the side that states is asked nothing, and her silence on
    the last one costs her nothing (#659).
    """

    #: A cohort handle.
    opponent: str
    #: ``True`` she won, ``False`` they did, ``None`` they each stated a score
    #: naming a different winner and neither accepted the other's — **disputed**
    #: (#654): an evening, not evidence.
    she_won: bool | None
    #: ``False`` is a game nobody recorded: its entry window closed over a full
    #: court and it reads **Played · no score** (#655) — played, for both of
    #: them, with no Level moving.
    entered: bool = True
    #: ``False`` is the score she never answered. Silence confirms it anyway.
    answered: bool = True

    @property
    def was_scored(self) -> bool:
        return self.she_won is not None

    def as_a_game(self) -> PlayedGame:
        """This evening in the shape every declared game takes: the opponent on
        side A, who states, and her on side B, who answers."""

        return PlayedGame(
            sport=HISTORY_SPORT.value,
            played_days_ago=0,
            side_a=(self.opponent,),
            side_b=(PROTAGONIST_HANDLE,),
            won_by=None if self.she_won is None else "B" if self.she_won else "A",
            entered=self.entered,
            answered=self.answered,
        )


#: **Her evenings, oldest first, one a day.** Read down the endings rather than
#: the scores, because they are what her record draws:
#:
#: - six games, all six played through — the second is the one nobody
#:   recorded, which reads *Played · no score* (#655) and earns its 5 like the
#:   rest — so her Player reliability reads **100 · Very high**, no longer New,
#:   *turned up 6 of 6* and *kept 6 of 6* (#659);
#: - five scores put to her and the newest of them unanswered, which costs her
#:   nothing: silence on a score is free;
#: - three people over six counted games, the unrecorded one among them, so
#:   *opponent variety* reads 3 of 6;
#: - a run of five that mixes wins and losses — the unrecorded evening has no
#:   result to put in it.
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
    """A game the run could not write, with what the platform said."""


class HistoryIsEmpty(RuntimeError):
    """Her record is missing what this layer promises: a played game, a Level
    the rating catch-up moves, or what somebody said about her."""


@final
@dataclass(frozen=True, slots=True)
class WrittenGame:
    game: PlayedGame
    start: Instant
    #: Whether this run booked it, or found it booked already.
    made: bool
    #: What this run did to its result, in the report's words.
    acts: tuple[str, ...]
    #: Played this week, because somebody on it committed inside it.
    this_week: bool = False


@final
@dataclass(frozen=True, slots=True)
class SeededHistory:
    #: Her evenings, oldest first.
    evenings: tuple[WrittenGame, ...]
    #: Every declared game handed in, oldest first.
    played: tuple[WrittenGame, ...]
    #: Each group, by sport, and whether this run created it.
    groups: tuple[tuple[Sport, UUID, bool], ...]
    #: One line per rater of hers: the card answered, or found answered.
    cards: tuple[str, ...]

    @property
    def this_week(self) -> tuple[WrittenGame, ...]:
        return tuple(game for game in self.played if game.this_week)


def _refuse_evenings_she_could_not_have_played() -> None:
    """Her declarations against the population, **on import**, so a row that
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
            raise RuntimeError(f"evening {index} was never recorded and has a winner")
        if not evening.answered and not evening.was_scored:
            raise RuntimeError(
                f"evening {index} was left unanswered and has no winner: silence "
                f"confirms a score, so an unanswered one has a winner"
            )
    for rater, stars in WHAT_THEY_SAID_ABOUT_HER.items():
        if not lowest <= stars <= highest:
            raise RuntimeError(f"'{rater}' gives her {stars} stars")
        if all(evening.opponent != rater for evening in HER_EVENINGS):
            # Every evening was played — an unrecorded one too (#655) — so
            # every one of them draws a card.
            raise RuntimeError(f"'{rater}' rates her and played her on no evening")


_refuse_evenings_she_could_not_have_played()


# ---------------------------------------------------------------------------
# Who is on a game
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class _Person:
    handle: str
    player_id: UUID
    #: The latest instant their profile could have been committed at.
    committed_at: Instant
    #: Their own Play intent per sport, as the fixture declares it.
    intents: Mapping[Sport, PlayIntent]


async def _people(
    session: AsyncSession,
    handles: Iterable[str],
    *,
    named: Sequence[SeedAccount],
    now: Instant,
) -> dict[str, _Person]:
    """Everybody the games name: a cohort member by handle, anybody else by the
    slug of a named account."""

    accounts = {account.slug: account for account in (THE_POPULATED_PLAYER, *named)}
    users = build_user_repository(session)
    people: dict[str, _Person] = {}
    for handle in sorted(set(handles)):
        if handle.startswith("cohort-"):
            member = COHORT.by_handle(handle)
            email, days = member.email, member.committed_days_ago
            intents = {
                Sport(sport): PlayIntent(intent) for sport, intent in member.intents
            }
        else:
            account = accounts.get(handle)
            if account is None or account.profile is None:
                raise HistoryRefused(
                    f"'{handle}' is on a game and is neither a cohort member nor a "
                    f"named account with a profile"
                )
            email, days = account.email, account.profile.committed_days_ago
            intents = dict(account.profile.intents)
        user = await users.get_by_email(email)
        if user is None:
            raise RuntimeError(f"{email} is not registered — the accounts run first")
        people[handle] = _Person(
            handle=handle,
            player_id=user.id,
            committed_at=days_before(now, days).now(),
            intents=intents,
        )
    return people


async def _declare(
    session: AsyncSession,
    switched: Iterable[tuple[_Person, Sport]],
    *,
    intent_of: Callable[[_Person, Sport], PlayIntent],
    now: Instant,
) -> None:
    """Each of these people's Play intent in the sport declared, as they would
    change it on the You tab — a declaration that changes nothing recording
    nothing."""

    store = build_domain_event_store(session)
    declare = DeclarePlayIntent(
        declarations=build_play_intent_declaration_repository(
            event_store=store, events=build_event_publisher(session)
        ),
        uow=build_unit_of_work(session),
        clock=FixedClock(at=now),
    )
    for person, sport in switched:
        await declare.execute(
            DeclarePlayIntentCommand(
                player_id=person.player_id,
                sport=sport,
                intent=intent_of(person, sport),
                surface=PlayIntentSurface.PROFILE_SCREEN,
            )
        )


# ---------------------------------------------------------------------------
# Writing every game
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class _Planned:
    game: PlayedGame
    #: The day the placement starts from, walking back.
    day: date
    #: The day it was declared for: where a game nobody on it could have played
    #: before her week is played instead.
    declared: date
    #: Her evening, which is placed before her week or not at all.
    hers: bool
    #: The order games for the same people are told apart by: oldest first.
    order: int


def _plan(games: Sequence[PlayedGame], *, now: Instant) -> list[_Planned]:
    """Every game and where its placement starts: a declared game on its own
    day, or the last day before her week where it was declared inside it; her
    evenings one a day back from that day."""

    # The day the latest game may end on — the last day before her week, or
    # earlier still where the run is early in it.
    anchor = local_day(instant(latest_evening_ends_by(now) - timedelta(minutes=1)))
    planned: list[_Planned] = []
    for game in sorted(games, key=lambda one: -one.played_days_ago):
        declared = local_day(days_before(now, game.played_days_ago).now())
        planned.append(
            _Planned(
                game,
                day=min(declared, anchor),
                declared=declared,
                hers=False,
                order=len(planned),
            )
        )
    for index, evening in enumerate(HER_EVENINGS):
        day = anchor - timedelta(days=len(HER_EVENINGS) - 1 - index)
        planned.append(
            _Planned(
                evening.as_a_game(),
                day=day,
                declared=day,
                hers=True,
                order=len(planned),
            )
        )
    return planned


async def write_the_played_history(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    games: Sequence[PlayedGame] = (),
    named: Sequence[SeedAccount] = (),
    money: SeedMoney = THE_FAKE,
) -> SeededHistory:
    """Write every declared game and her evenings, oldest first, then what her
    opponents said about her.

    ``games`` are the declared games the runner hands in; ``named`` are the
    accounts besides the cohort they may name; every seat is held through
    ``money``'s provider. **After the cohort, the cards, the clubs and their
    courts**, which it reads and never writes."""

    planned = _plan(games, now=now)
    async with session_factory() as session:
        people = await _people(
            session,
            (handle for one in planned for handle in one.game.players),
            named=named,
            now=now,
        )
        her = people[PROTAGONIST_HANDLE]
        club_id = await club_id_of(session, HISTORY_CLUB)
        groups: dict[Sport, tuple[UUID, bool]] = {}
        for sport in Sport:
            members = [
                people[handle]
                for one in planned
                if one.game.sport == sport.value
                for handle in one.game.players
            ]
            if members:
                groups[sport] = await _the_group(
                    session, settings, her, club_id, sport, members
                )
        booked = await _past_bookings(
            session, [person.player_id for person in people.values()]
        )
        busy: dict[UUID, list[Instant]] = {}
        for _, players, start, _ in booked:
            for player in players:
                busy.setdefault(player, []).append(start)
        found = _already_booked(planned, booked, groups, people)
        # Who plays a game still to be made in a sport they now play for fun.
        switched = [
            (people[handle], Sport(sport))
            for handle, sport in sorted(
                {
                    (handle, one.game.sport)
                    for one in planned
                    if one.order not in found
                    for handle in one.game.players
                    if people[handle].intents.get(Sport(one.game.sport))
                    is PLAYED_FOR_FUN
                }
            )
        ]
        await _declare(
            session,
            switched,
            intent_of=lambda person, sport: HISTORY_INTENT,
            now=now,
        )

        written: dict[int, WrittenGame] = {}
        game_ids: dict[int, UUID] = {}
        for one in sorted(planned, key=lambda one: (one.day, one.order)):
            on_it = [people[handle] for handle in one.game.players]
            sport = Sport(one.game.sport)
            if one.order in found:
                start, game_ids[one.order] = found[one.order]
                made = False
            else:
                start, made_at = await _a_free_hour(
                    session, club_id, sport, one, on_it, busy, now=now
                )
                game_ids[one.order] = await _book(
                    session,
                    settings,
                    provider=money.provider(),
                    group_id=groups[sport][0],
                    club_id=club_id,
                    sport=sport,
                    start=start,
                    made_at=made_at,
                    players=tuple(person.player_id for person in on_it),
                )
                made = True
                for person in on_it:
                    busy.setdefault(person.player_id, []).append(start)
            acts = await _play(
                session,
                game_id=game_ids[one.order],
                game=one.game,
                people=people,
                start=start,
            )
            written[one.order] = WrittenGame(
                one.game,
                start,
                made=made,
                acts=acts,
                this_week=start >= hour_start(week_of(now), 0),
            )
        await _declare(
            session,
            switched,
            intent_of=lambda person, sport: person.intents[sport],
            now=now,
        )

        cards = await _rate_her(
            session,
            her.player_id,
            {handle: people[handle].player_id for handle in WHAT_THEY_SAID_ABOUT_HER},
            {game_ids[one.order] for one in planned if one.hers},
            now=now,
        )
    return SeededHistory(
        evenings=tuple(written[one.order] for one in planned if one.hers),
        played=tuple(
            sorted(
                (written[one.order] for one in planned if not one.hers),
                key=lambda game: game.start,
            )
        ),
        groups=tuple(
            (sport, group_id, created) for sport, (group_id, created) in groups.items()
        ),
        cards=cards,
    )


def latest_evening_ends_by(now: Instant) -> Instant:
    """The latest instant a game may end: before this week began, and long
    enough ago that every ending it can have has been reached."""

    return min(hour_start(week_of(now), 0), instant(now - SETTLED_FOR))


async def _a_free_hour(
    session: AsyncSession,
    club_id: UUID,
    sport: Sport,
    one: _Planned,
    on_it: Sequence[_Person],
    busy: Mapping[UUID, Sequence[Instant]],
    *,
    now: Instant,
) -> tuple[Instant, Instant]:
    """The first hour the club sold on the game's day — walking back a day at a
    time — that ends before her week, that nobody on it is already playing at,
    and that could have been made after the last of them committed. Where none
    could, a declared game is played inside her week instead, on its declared
    day or before. The hour, and when the game was made."""

    latest = latest_evening_ends_by(now)
    earliest_made = instant(
        max(person.committed_at for person in on_it) + AFTER_THE_LAST_COMMIT
    )
    attempts = [(one.day, latest)]
    if not one.hers and one.declared > one.day:
        attempts.append((one.declared, instant(now - SETTLED_FOR)))
    for first, bound in attempts:
        day = first
        while day >= local_day(earliest_made) and first - day <= LOOKS_BACK:
            hour = await _an_hour(
                session,
                club_id,
                sport,
                day,
                on_it,
                busy,
                bound=bound,
                earliest_made=earliest_made,
            )
            if hour is not None:
                return hour
            day -= timedelta(days=1)
    names = ", ".join(person.handle for person in on_it)
    raise HistoryRefused(
        f"{HISTORY_CLUB.name} sold no {sport.value} hour {names} could all play "
        f"between {earliest_made.astimezone(CLUB_ZONE):%a %d %b %H:%M} and "
        f"{one.declared:%a %d %b}"
    )


async def _an_hour(
    session: AsyncSession,
    club_id: UUID,
    sport: Sport,
    day: date,
    on_it: Sequence[_Person],
    busy: Mapping[UUID, Sequence[Instant]],
    *,
    bound: Instant,
    earliest_made: Instant,
) -> tuple[Instant, Instant] | None:
    court_hours = build_court_hours(session)
    day_start = hour_start(day, 0)
    on_sale = await court_hours.on_sale(
        [club_id],
        start=day_start,
        end=day_start + timedelta(days=1),
        now=max(instant(day_start - MADE_AHEAD), earliest_made),
    )
    for start in sorted(
        hour.start for hour in on_sale if hour.sport is sport and hour.taking_new_cards
    ):
        if start + GAME_LENGTH > bound or any(
            abs(start - taken) < GAME_LENGTH
            for person in on_it
            for taken in busy.get(person.player_id, ())
        ):
            continue
        made_at = max(instant(start - MADE_AHEAD), earliest_made)
        if made_at < start and await court_hours.offered(
            club_id, sport=sport, start=start, now=made_at
        ):
            return start, made_at
    return None


async def _book(
    session: AsyncSession,
    settings: Settings,
    *,
    provider: PaymentProvider,
    group_id: UUID,
    club_id: UUID,
    sport: Sport,
    start: Instant,
    made_at: Instant,
    players: tuple[UUID, ...],
) -> UUID:
    """The game made and every yes said, in the order the game names them — the
    last books it. The Game it opened."""

    answer = await all_say_yes(
        session,
        settings=settings,
        clock=FixedClock(at=made_at),
        provider=provider,
        pool_id=group_id,
        club_id=club_id,
        start=start,
        players=players,
        sport=sport,
        kind=HISTORY_KIND,
    )
    if answer is None or answer.booked is None:
        raise HistoryRefused(
            f"the {sport.value} game at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} "
            f"filled and did not book: {answer!r}"
        )
    # Held until the club's cut-off, which takes the shares (#637): the cut-off
    # job runs at that moment, as the API's would have.
    booked = await build_player_bookings(session).find(answer.booked.booking_id)
    if booked is not None and made_at < booked.cut_off:
        await the_cut_off_came(session, settings=settings, at=booked.cut_off)
    return answer.booked.game_id


async def _play(
    session: AsyncSession,
    *,
    game_id: UUID,
    game: PlayedGame,
    people: Mapping[str, _Person],
    start: Instant,
) -> tuple[str, ...]:
    """*We played, here is the score* — and whatever the other side did with it.

    **The first person declared on side A states**, and the score is put to the
    first declared person the fill seated across the net from them. **Each act is
    asked for off the Game's record**, so a resumed run takes only the ones still
    owed. A game nobody claimed is written by writing nothing, and so is the
    answer nobody gave."""

    if not game.entered:
        return ()
    games = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    played = await _loaded(games, game_id)
    stater = people[game.side_a[0]].player_id
    stater_side = played.line_up.side_of(stater)
    if stater_side is None:
        raise HistoryRefused(f"game {game_id} does not seat '{game.side_a[0]}'")
    answerer = next(
        (
            people[handle].player_id
            for handle in (*game.side_b, *game.side_a[1:])
            if played.line_up.side_of(people[handle].player_id) is stater_side.other
        ),
        None,
    )
    if answerer is None:
        raise HistoryRefused(f"game {game_id} seats nobody across the net")
    # A game nobody agreed is the stater's side claiming it and the other side
    # claiming it back.
    winner = game.side_b[0] if game.won_by == "B" else game.side_a[0]
    winning_side = played.line_up.side_of(people[winner].player_id) or stater_side
    ends = instant(start + GAME_LENGTH)
    acts: list[str] = []
    if played.played_at is None:
        await _state(session, games, instant(ends + STATED_AFTER)).execute(
            StateResultCommand(
                game_id=game_id,
                player_id=stater,
                score=SCORES[winning_side],
            )
        )
        acts.append("score entered")
        played = await _loaded(games, game_id)
    answered_at = instant(ends + ANSWERED_AFTER)
    if not game.was_scored:
        if stater_side.other not in played.proposals:
            # The counter names the other winner: two sides who disagree.
            await _state(session, games, answered_at).execute(
                StateResultCommand(
                    game_id=game_id,
                    player_id=answerer,
                    score=SCORES[stater_side.other],
                )
            )
            acts.append("countered")
    elif game.answered and played.acceptance is None:
        await AcceptResult(
            games=games,
            names=build_player_names(session),
            uow=build_unit_of_work(session),
            clock=FixedClock(at=answered_at),
        ).execute(AcceptResultCommand(game_id=game_id, player_id=answerer))
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
    raters: Mapping[str, UUID],
    evenings: set[UUID],
    *,
    now: Instant,
) -> tuple[str, ...]:
    """Each rater's card on the newest of her evenings they shared and played —
    answered the day after it, inside the week the card is open for."""

    courts = build_settled_courts(session)
    ledger = build_sportsmanship_ledger(session)
    lines: list[str] = []
    for rater, stars in sorted(WHAT_THEY_SAID_ABOUT_HER.items()):
        rater_id = raters[rater]
        shared = [
            court
            for court in await courts.courts_of(rater_id, now=now)
            if court.game_id in evenings and her in court.others
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
    her: _Person,
    club_id: UUID,
    sport: Sport,
    members: Iterable[_Person],
) -> tuple[UUID, bool]:
    """Her group for the sport at the club — created half an hour after she
    committed, and joined by everybody its games seat, each half an hour after
    they did. Joining again records nothing."""

    name = HISTORY_GROUPS[sport]
    opened = instant(her.committed_at + timedelta(minutes=30))
    group_id = await group_run_by(session, her.player_id, club_id=club_id, name=name)
    created = group_id is None
    if group_id is None:
        group_id = await CreatePlayerGroup(
            groups=group_repository(session),
            clubs=build_home_clubs(session),
            codes=build_group_code_minter(session),
            uow=build_unit_of_work(session),
            clock=FixedClock(at=opened),
        ).execute(
            CreatePlayerGroupCommand(
                creator_id=her.player_id,
                name=name,
                home_club_id=club_id,
                join_policy=JoinPolicy.ANYONE,
            )
        )
    for member in {person.handle: person for person in members}.values():
        if member.player_id == her.player_id:
            continue
        joined = max(opened, instant(member.committed_at + timedelta(minutes=30)))
        await join_group(
            session, settings, group_id, member.player_id, FixedClock(at=joined)
        )
    return group_id, created


async def _past_bookings(
    session: AsyncSession, players: Iterable[UUID]
) -> list[tuple[UUID, frozenset[UUID], Instant, UUID]]:
    """Every booked game these players have, once each — its group, who is on
    it, its hour and its Game."""

    bookings = build_player_bookings(session)
    seen: dict[UUID, tuple[UUID, frozenset[UUID], Instant, UUID]] = {}
    for player in sorted(set(players), key=str):
        for game in await bookings.of_player(player, since=None):
            if game.game_id is not None:
                seen[game.booking_id] = (
                    game.pool_id,
                    frozenset((*game.first_side, *game.second_side)),
                    game.start,
                    game.game_id,
                )
    return list(seen.values())


def _already_booked(
    planned: Sequence[_Planned],
    booked: Sequence[tuple[UUID, frozenset[UUID], Instant, UUID]],
    groups: Mapping[Sport, tuple[UUID, bool]],
    people: Mapping[str, _Person],
) -> dict[int, tuple[Instant, UUID]]:
    """The games an earlier run wrote: the n-th declared game for the same
    people in its group is the n-th booking they share there, oldest first."""

    def key_of(one: _Planned) -> tuple[UUID, frozenset[UUID]]:
        return (
            groups[Sport(one.game.sport)][0],
            frozenset(people[handle].player_id for handle in one.game.players),
        )

    existing: dict[tuple[UUID, frozenset[UUID]], list[tuple[Instant, UUID]]] = {}
    for pool_id, players, start, game_id in booked:
        existing.setdefault((pool_id, players), []).append((start, game_id))
    found: dict[int, tuple[Instant, UUID]] = {}
    seen: dict[tuple[UUID, frozenset[UUID]], int] = {}
    for one in sorted(planned, key=lambda one: one.order):
        key = key_of(one)
        index = seen.get(key, 0)
        seen[key] = index + 1
        mine = sorted(existing.get(key, []))
        if index < len(mine):
            found[one.order] = mine[index]
    return found


async def assert_her_history(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> str:
    """*Her record has played games, a Level that moves, and stars* — each read
    off her evenings through the paths that read them.

    - **played**: each of her evenings' details reads it *counted* — her
      details, not her Home, which sends only what it draws (#613), and every
      evening ended days before the run;
    - **her Level moves**: the confirmed counted results the rating catch-up
      folds hold her evenings, in a sport she is rated in;
    - **stars**: somebody she played has answered a card about her on one of
      them, and her record publishes a figure.

    Any of the three missing fails the run by name."""

    async with session_factory() as session:
        her = (await _people(session, [PROTAGONIST_HANDLE], named=(), now=now))[
            PROTAGONIST_HANDLE
        ].player_id
        club_id = await club_id_of(session, HISTORY_CLUB)
        group_id = await group_run_by(
            session, her, club_id=club_id, name=HISTORY_GROUPS[HISTORY_SPORT]
        )
        where = f"her record · {PROTAGONIST_HANDLE} · {HISTORY_GROUPS[HISTORY_SPORT]}"
        if group_id is None:
            raise HistoryIsEmpty(f"{where}: no group, so no evening was written")
        details = build_read_booking_details(
            session, settings=settings, clock=FixedClock(at=now)
        )
        evenings = [
            await details.execute(game.booking_id, her)
            for game in await build_player_bookings(session).of_player(her, since=None)
            if game.pool_id == group_id and game.game_id is not None
        ]
        counted = [one for one in evenings if one.state.status is HomeStatus.COUNTED]
        if not counted:
            raise HistoryIsEmpty(
                f"{where} draws no played game: her evenings read "
                f"{sorted(one.state.status.value for one in evenings)}"
            )
        history = {one.game.game_id for one in evenings if one.game.game_id is not None}
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
        raters = await _people(session, WHAT_THEY_SAID_ABOUT_HER, named=(), now=now)
        ledger = build_sportsmanship_ledger(session)
        answered = [
            handle
            for handle, rater in sorted(raters.items())
            if await ledger.answered_among(
                rater_id=rater.player_id, game_ids=tuple(history)
            )
        ]
        published = await build_published_sportsmanship(session).published_for(her)
        if not answered or published is None:
            raise HistoryIsEmpty(
                f"{where} has no stars: {len(answered)} card(s) answered about her "
                f"on her evenings, and her record publishes "
                f"{'nothing' if published is None else 'a figure'}"
            )
    return (
        f"{where}: {len(counted)} of {len(evenings)} game(s) counted, "
        f"{len(moving)} result(s) for the rating catch-up to move her Level on, "
        f"{len(answered)} rater(s) on them — {published.average:.1f} / 5 over "
        f"{published.raters}"
    )


def _ending(game: PlayedGame, *, hers: bool) -> str:
    if not game.entered:
        return "nobody recorded it — played, no score"
    if game.won_by is None:
        return "nobody agreed a score"
    won = (
        ("she won" if game.won_by == "B" else "she lost")
        if hers
        else f"side {game.won_by} won"
    )
    return won if game.answered else f"{won}, unanswered and confirmed by silence"


def _line(written: WrittenGame, *, hers: bool = False) -> str:
    game = written.game
    state = "booked" if written.made else "already booked"
    acts = f", {', '.join(written.acts)}" if written.acts else ""
    week = (
        " · this week: somebody on it committed inside it" if written.this_week else ""
    )
    who = (
        f"against {game.side_a[0]}"
        if hers
        else f"{' & '.join(game.side_a)} against {' & '.join(game.side_b)}"
    )
    return (
        f"  {written.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · "
        f"{game.sport.lower()} · {who} · {state}{acts} · "
        f"{_ending(game, hers=hers)}{week}"
    )


def history_lines(seeded: SeededHistory) -> list[str]:
    """The report's section: the groups, her evenings, what was said about her,
    and every declared game."""

    groups = ", ".join(
        f"{HISTORY_GROUPS[sport]} ({'created' if created else 'already there'})"
        for sport, _, created in seeded.groups
    )
    lines = [
        f"The played history — booked at {HISTORY_CLUB.name}, in {groups}",
        "Her evenings:",
        *(_line(written, hers=True) for written in seeded.evenings),
        *(f"  {line}" for line in seeded.cards),
        f"Every declared game ({len(seeded.played)}, "
        f"{len(seeded.this_week)} played this week):",
        *(_line(written) for written in seeded.played),
    ]
    return lines
