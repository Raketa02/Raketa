"""Two friends games sent to the protagonist (#751; ``docs/adr/0202`` §5–§6): a
**Split the cost** game waiting on her alone, and a **Whole court** game waiting
on all three friends.

**Through the use cases a phone runs** — the friendships its line-ups need made
by the friends layer's own acts (``FriendActs``), the court read off *Find a
court* (``ReadFriendsCourts``), the game sent by ``SendAFriendsGame`` over the
run's own provider, and each accept by ``AcceptAFriendsGame`` — all in
*Czwartkowy padel*, her group at Centrum Ruchu, in padel. Nothing here opens a
table.

- **Split**: ``rating-well-established`` sent it to her, ``the-one-sport-player``
  and ``rating-barely-established``; both of them accepted, each 25 zł held, so
  her Home's *FRIENDS GAME* card reads *2 of 3 friends in* with **Accept and
  pay**, and his Your games *waiting for* her.
- **Whole court**: ``the-one-sport-player`` sent it to her,
  ``rating-well-established`` and ``rating-barely-established``, the whole court
  held on his card; nobody has answered.

**At an hour that moves nothing she is dealt**: the first row *Find a court*
lists where most of the four are free, more than two days out, at which none of
them has a live yes, and in a week the sender and each friend who accepts still has
room in after it — so no yes is withdrawn or paused, and her deck, Fill in and
post read as before. The two games are at different hours.

**After the friends layer and before the screens**, its outbox drained so the
invitations are told and each game's chat is open. **Re-running sends nothing
twice**: each sender's friends game in the group is read first, and only a
missing accept is made.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_accept_a_friends_game,
    build_group_directory,
    build_player_bookings,
    build_proposal_directory,
    build_read_friends_courts,
    build_general_orders_kept_here,
    build_read_home,
    build_send_a_friends_game,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.friends.domain.relation import FriendRelation
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.proposals.application.commands import (
    FriendsGameCommand,
    FriendsLineUpCommand,
    SendAFriendsGameCommand,
)
from app.modules.proposals.application.friends_card import FriendsLineUpRead
from app.modules.proposals.domain.deck import week_of
from app.modules.proposals.domain.friends_card import CourtForFriends
from app.modules.proposals.domain.home import PayMode, SeatState
from app.seeds.catalog import (
    RATING_BARELY_ESTABLISHED,
    RATING_WELL_ESTABLISHED,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.clock import FixedClock, hours_before
from app.seeds.friends import CZWARTKOWY, FriendActs
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.rooms import deliver_everything_told

#: How far out a seeded friends game is, at least: its invitations' 24 hours
#: end well before its cut-off.
AT_LEAST: Final = timedelta(days=2)


@final
@dataclass(frozen=True, slots=True)
class FriendsGameSpec:
    """One friends game the layer promises: who sends it, to whom, how it is
    paid, and who has accepted."""

    sender: SeedAccount
    friends: tuple[SeedAccount, ...]
    pay_mode: PayMode
    accepted: tuple[SeedAccount, ...]


#: The two games, in the order they are sent.
FRIENDS_GAMES: Final[tuple[FriendsGameSpec, ...]] = (
    FriendsGameSpec(
        sender=RATING_WELL_ESTABLISHED,
        friends=(THE_POPULATED_PLAYER, THE_ONE_SPORT_PLAYER, RATING_BARELY_ESTABLISHED),
        pay_mode=PayMode.SPLIT_THE_COST,
        accepted=(THE_ONE_SPORT_PLAYER, RATING_BARELY_ESTABLISHED),
    ),
    FriendsGameSpec(
        sender=THE_ONE_SPORT_PLAYER,
        friends=(
            THE_POPULATED_PLAYER,
            RATING_WELL_ESTABLISHED,
            RATING_BARELY_ESTABLISHED,
        ),
        pay_mode=PayMode.WHOLE_COURT,
        accepted=(),
    ),
)

#: The friendships the two line-ups need beyond the friends layer's.
_PAIRS: Final = (
    (RATING_WELL_ESTABLISHED, THE_ONE_SPORT_PLAYER),
    (RATING_WELL_ESTABLISHED, RATING_BARELY_ESTABLISHED),
    (THE_ONE_SPORT_PLAYER, RATING_BARELY_ESTABLISHED),
)


@final
@dataclass(frozen=True, slots=True)
class SeededFriendsGame:
    booking_id: UUID
    sender: str
    pay_mode: PayMode
    starts_at: Instant
    club_id: UUID
    #: Who is In beside the sender, by slug.
    friends_in: tuple[str, ...]
    #: Whose invitation still waits, by slug.
    waiting: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class SeededFriendsGames:
    games: tuple[SeededFriendsGame, ...]


async def write_the_friends_games(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    money: SeedMoney = THE_FAKE,
) -> SeededFriendsGames:
    accounts = (
        THE_POPULATED_PLAYER,
        RATING_WELL_ESTABLISHED,
        THE_ONE_SPORT_PLAYER,
        RATING_BARELY_ESTABLISHED,
    )
    async with session_factory() as session:
        ids = await _ids(session, accounts)
        group = await _the_group(session, ids[THE_POPULATED_PLAYER.slug])
    acts = FriendActs(session_factory, ids=ids, groups={CZWARTKOWY: group}, now=now)
    for one, other in _PAIRS:
        if await acts.relation(one, other) is FriendRelation.NONE:
            await acts.ask(one, other, group=CZWARTKOWY, hours=30)
        if await acts.relation(one, other) is FriendRelation.SENT:
            await acts.accept(other, one, hours=29)

    provider = money.provider()
    sent_at = instant(now - timedelta(hours=2))
    taken: list[Instant] = []
    for spec in FRIENDS_GAMES:
        booking_id = await _sent_already(session_factory, spec, ids, group, now=now)
        if booking_id is None:
            booking_id = await _send(
                session_factory,
                spec,
                ids,
                group,
                settings=settings,
                provider=provider,
                at=sent_at,
                not_at=taken,
            )
        for friend in spec.accepted:
            async with session_factory() as session:
                await build_accept_a_friends_game(
                    session,
                    clock=hours_before(now, 1),
                    provider=provider,
                    settings=settings,
                ).execute(
                    FriendsGameCommand(
                        player_id=ids[friend.slug], booking_id=booking_id
                    )
                )
        async with session_factory() as session:
            game = await build_player_bookings(session).find(booking_id)
        assert game is not None
        taken.append(game.start)
    await deliver_everything_told(session_factory, money=money)
    seeded = await _read_back(session_factory, ids, settings=settings, now=now)
    _refuse_a_seed_that_lies(seeded)
    return seeded


async def _sent_already(
    session_factory: async_sessionmaker[AsyncSession],
    spec: FriendsGameSpec,
    ids: dict[str, UUID],
    group: UUID,
    *,
    now: Instant,
) -> UUID | None:
    """The sender's friends game of this pay mode in the group, from an earlier
    run."""

    sender = ids[spec.sender.slug]
    async with session_factory() as session:
        games = await build_player_bookings(session).of_player(sender, since=now)
    found = next(
        (
            game.booking_id
            for game in games
            if game.sender == sender
            and game.pool_id == group
            and game.pay_mode is spec.pay_mode
            and game.called_off_reason(now) is None
        ),
        None,
    )
    return found


async def _send(
    session_factory: async_sessionmaker[AsyncSession],
    spec: FriendsGameSpec,
    ids: dict[str, UUID],
    group: UUID,
    *,
    settings: Settings,
    provider: PaymentProvider,
    at: Instant,
    not_at: Sequence[Instant],
) -> UUID:
    line_up = FriendsLineUpCommand(
        player_id=ids[spec.sender.slug],
        pool_id=group,
        sport=Sport.PADEL,
        friend_ids=[ids[friend.slug] for friend in spec.friends],
    )
    async with session_factory() as session:
        courts = await build_read_friends_courts(
            session, clock=FixedClock(at=at)
        ).execute(line_up)
        yeses = {
            player: {
                yes.start
                for yes in await build_proposal_directory(session).live_yeses_of(
                    player, now=at
                )
            }
            for player in line_up_players(line_up)
        }
    in_it = {ids[spec.sender.slug], *(ids[friend.slug] for friend in spec.accepted)}
    court = _the_court(courts.read, yeses, in_it=in_it, not_at=not_at, at=at)
    if court is None:
        raise RuntimeError(
            f"the friends games layer found no hour for {spec.sender.slug}'s "
            f"{spec.pay_mode.value} game in {CZWARTKOWY}: every row of Find a "
            "court is too soon, at a live yes, or in a full week"
        )
    async with session_factory() as session:
        sent = await build_send_a_friends_game(
            session, clock=FixedClock(at=at), provider=provider, settings=settings
        ).execute(
            SendAFriendsGameCommand(
                line_up=line_up,
                kind=SearchMode.COMPETITIVE,
                court_id=court.court.court_id,
                starts_at=court.start,
                pay_mode=spec.pay_mode,
            )
        )
    if sent.booked is None:
        raise RuntimeError(
            f"{spec.sender.slug}'s friends game was refused a payment: "
            f"{[payment.refusal.value for payment in sent.your_payments]}"
        )
    return sent.booking_id


def line_up_players(line_up: FriendsLineUpCommand) -> tuple[UUID, ...]:
    return (line_up.player_id, *line_up.friend_ids)


def _the_court(
    read: FriendsLineUpRead,
    yeses: dict[UUID, set[Instant]],
    *,
    in_it: set[UUID],
    not_at: Sequence[Instant],
    at: Instant,
) -> CourtForFriends | None:
    """Of the rows far enough out, clear of every live yes and of the other
    game, and in a week everybody In keeps room in, the first where most of
    the four are free — as the card proposes one: every row can be picked."""

    def room_after(start: Instant) -> bool:
        week = week_of(start)
        return all(
            sum(1 for booked in person.booked if week_of(booked) == week) + 1
            < person.limits.games_per_week
            for person in read.people
            if person.player_id in in_it
        )

    # ``max`` keeps the first among equals, which is the soonest.
    return max(
        (
            row
            for row in read.courts
            if row.start - at >= AT_LEAST
            and row.start not in not_at
            and all(row.start not in starts for starts in yeses.values())
            and room_after(row.start)
        ),
        key=lambda row: len(row.free),
        default=None,
    )


async def _read_back(
    session_factory: async_sessionmaker[AsyncSession],
    ids: dict[str, UUID],
    *,
    settings: Settings,
    now: Instant,
) -> SeededFriendsGames:
    """Her Home's *FRIENDS GAME* row, read as the app reads it."""

    slug_of = {player: slug for slug, player in ids.items()}
    async with session_factory() as session:
        home = await build_read_home(
            session,
            settings=settings,
            clock=FixedClock(at=now),
            orders=build_general_orders_kept_here(),
        ).execute(ids[THE_POPULATED_PLAYER.slug])
    games = []
    for invitation in home.friends_games:
        game = invitation.game
        assert game.sender is not None and game.pay_mode is not None
        seats = game.seat_states(now=now)
        games.append(
            SeededFriendsGame(
                booking_id=game.booking_id,
                sender=slug_of.get(game.sender, str(game.sender)),
                pay_mode=game.pay_mode,
                starts_at=game.start,
                club_id=game.club_id,
                friends_in=tuple(
                    slug_of.get(seat.player_id, str(seat.player_id))
                    for seat in seats
                    if seat.state is SeatState.IN and seat.player_id != game.sender
                ),
                waiting=tuple(
                    slug_of.get(seat.player_id, str(seat.player_id))
                    for seat in seats
                    if seat.state is SeatState.WAITING
                ),
            )
        )
    return SeededFriendsGames(games=tuple(games))


def _refuse_a_seed_that_lies(seeded: SeededFriendsGames) -> None:
    """Both games on her Home, as promised — or the run fails by name."""

    found = {(game.sender, game.pay_mode): game for game in seeded.games}
    wrong = []
    for spec in FRIENDS_GAMES:
        game = found.get((spec.sender.slug, spec.pay_mode))
        if game is None:
            wrong.append(
                f"{spec.sender.slug}'s {spec.pay_mode.value} game is not on her Home"
            )
            continue
        if sorted(game.friends_in) != sorted(friend.slug for friend in spec.accepted):
            wrong.append(
                f"{spec.sender.slug}'s game has {game.friends_in} In, not "
                f"{[friend.slug for friend in spec.accepted]}"
            )
        if THE_POPULATED_PLAYER.slug not in game.waiting:
            wrong.append(f"{spec.sender.slug}'s game is not waiting on her")
    if wrong:
        raise RuntimeError(f"the friends games layer did not reach its states: {wrong}")


async def _ids(
    session: AsyncSession, accounts: Sequence[SeedAccount]
) -> dict[str, UUID]:
    users = build_user_repository(session)
    ids: dict[str, UUID] = {}
    for account in accounts:
        user = await users.get_by_email(account.email)
        if user is None:
            raise RuntimeError(
                f"{account.slug} is not registered — the accounts layer runs first"
            )
        ids[account.slug] = user.id
    return ids


async def _the_group(session: AsyncSession, owner: UUID) -> UUID:
    directory = build_group_directory(session)
    listings = await directory.listings(await directory.groups_of(owner))
    group = next(
        (
            listing.id
            for listing in listings.values()
            if listing.name.value == CZWARTKOWY
        ),
        None,
    )
    if group is None:
        raise RuntimeError(f"{CZWARTKOWY} is not seeded — the groups layer runs first")
    return group


def friends_game_lines(seeded: SeededFriendsGames) -> list[str]:
    """The report's section."""

    return [
        f"Friends games — {THE_POPULATED_PLAYER.email}'s Home, FRIENDS GAME:",
        *(
            f"  {game.sender}'s {game.pay_mode.value.lower().replace('_', ' ')} "
            f"game {game.starts_at.isoformat()}: in "
            f"{', '.join(game.friends_in) or 'nobody'}, "
            f"waiting on {', '.join(game.waiting)}"
            for game in seeded.games
        ),
    ]
