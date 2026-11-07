"""What a notice says, read off the contexts that own it — every adapter
**signed here**, so the arrows run ``notifications → proposals``, ``→ bookings``,
``→ games``, ``→ payments``, ``→ users``, ``→ groups`` and ``→ rating`` (a club's
name is read through Proposals' own ``ClubNames``), and none of them knows a
notice exists (#549).

``BookedAndProposedGames`` is a game as it stands: the proposal's stream folded,
and its booking's when it has one — one id for both. ``GameStreamCourts`` is the
court of the game a booking opened, asked of the Game itself — who is awaited,
whose agreement a score waits on, whose *I was there* waits (#663) — and
``BookedHours`` the booked games whose hour has just ended, off the bookings'
own projection. ``ProposalsDecks`` asks
**the deck itself** whether it shows a card to a reader
(``ReadGroupDeck.shows``), and ``RescueSeatOffers`` asks the Fill in board's
own ``RescueOffers`` who a seat is offered to — never a second reading of
either rule. ``SeatChargeShares`` is what a refund gives back — the provider's
own figures, never an estimate (#641). ``PlatformNames`` is a person's nickname
(``docs/adr/0199`` §1) and a club's name. ``DirectoryGroupJoiners`` is when each
account first joined a group it is in now, asked of the groups' own published
directory, and ``RatingsRatedAccounts`` who holds a rating, asked of rating's
published read — *Get your level*'s two questions (#727).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import Booking
from app.modules.bookings.domain.ports import BookingDirectory, BookingRepository
from app.modules.games.domain.attendance import NOT_HERE_STATES, AttendanceState
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.standing import GameStanding, settlement_of
from app.modules.groups.domain.ports import GroupDirectory
from app.modules.games.domain.windows import (
    A_BOOKED_GAME,
    hour_ends_at,
    late_claim_closes_at,
)
from app.modules.friends.application.reads import ReadRelations, ReadRequestsWaiting
from app.modules.notifications.domain.ports import (
    CourtBrief,
    GameBrief,
    PaidShare,
    WaitingRequest,
)
from app.modules.payments.domain.ports import SeatChargeRepository
from app.modules.payments.domain.seat_charge import PAID, RefundReason, SeatCharge
from app.modules.proposals.application.group_deck import ReadGroupDeck
from app.modules.proposals.application.rescues import RescueOffers
from app.modules.proposals.domain.ports import (
    ClubNames,
    PlayerBookings,
    Pools,
    ProposalRepository,
)
from app.modules.proposals.domain.proposal import Standing
from app.modules.proposals.domain.rescues import rescuable
from app.modules.rating.domain.ports import RatedPlayerQuery
from app.modules.users.domain.ports import UserRepository


@final
class BookedAndProposedGames:
    def __init__(
        self, *, proposals: ProposalRepository, bookings: BookingRepository
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings

    async def about(self, game_id: UUID, *, at: Instant) -> GameBrief | None:
        proposal = await self._proposals.load(game_id)
        if proposal is None:
            # No proposal stands for a friends game (#751): its booking is
            # the whole of it.
            sent = await self._bookings.load(game_id)
            return None if sent is None else _a_friends_game(sent, at=at)
        booking = await self._bookings.load(game_id)
        answered = {
            *proposal.yeses,
            *proposal.declined,
            *proposal.withdrawn,
            *proposal.reopened,
            *proposal.paused,
        }
        filling = proposal.standing_at(at) is Standing.FILLING
        return GameBrief(
            game_id=proposal.proposal_id,
            pool_id=proposal.pool.id,
            sport=proposal.sport,
            game_kind=proposal.kind.value,
            club_id=proposal.club_id,
            starts_at=proposal.start,
            share_grosze=proposal.share_grosze,
            made_at=proposal.made_at,
            posted_by=proposal.poster_id,
            filling=filling,
            open_seats=proposal.open_seats,
            in_=proposal.yeses,
            withdrawn=proposal.withdrawn,
            undecided=tuple(
                player
                for version in proposal.versions
                for player in version.players
                if player not in answered
            ),
            named=tuple(
                player
                for version in proposal.versions
                for player in version.players[: version.first_named]
                if player not in answered
            ),
            booked=booking is not None and booking.is_booked,
            seated=() if booking is None else booking.players,
            seats_taken={}
            if booking is None
            else {
                left.player_id: left.rescued_by
                for left in booking.departures
                if left.rescued_by is not None
            },
            cancel_reason=None
            if booking is None or booking.cancel_reason is None
            else booking.cancel_reason.value,
            filled_by=proposal.filled_by,
            book_by=proposal.book_by,
            fell_back_at=proposal.fell_back_at,
            left_it_short=()
            if booking is None
            else tuple(
                left.player_id
                for left in booking.departures
                if left.is_open and left.at < booking.cut_off
            ),
            # And a booked game's: a holding refused, its card to fix (#639) —
            # and a seat kept for a refused rescuer (#640).
            paying={
                **proposal.payments_due,
                **({} if booking is None else booking.fixing_until),
                **({} if booking is None else booking.kept_until),
            },
            fixing=proposal.fixing
            | (frozenset() if booking is None else frozenset(booking.cards_to_fix))
            | (
                frozenset()
                if booking is None
                else frozenset(
                    player
                    for player, kept in booking.kept.items()
                    if kept.to_fix_the_card
                )
            ),
            waiting_for_a_payment=filling and proposal.waiting_for_a_payment,
            booked_on_a_payment=proposal.booked_on_a_payment,
        )


def _a_friends_game(booking: Booking, *, at: Instant) -> GameBrief:
    """A friends game as a notice tells it (#751): booked at send, so never
    filling, its people the ones In and the friends still invited."""

    return GameBrief(
        game_id=booking.booking_id,
        pool_id=booking.pool_id,
        sport=booking.sport,
        game_kind=booking.kind.value,
        club_id=booking.club_id,
        starts_at=booking.start,
        share_grosze=booking.share_grosze,
        made_at=booking.booked_at,
        posted_by=None,
        filling=False,
        open_seats=booking.open_seats,
        in_=(),
        withdrawn=(),
        undecided=(),
        named=(),
        booked=booking.is_booked,
        seated=booking.players,
        seats_taken={
            left.player_id: left.rescued_by
            for left in booking.departures
            if left.rescued_by is not None
        },
        cancel_reason=None
        if booking.cancel_reason is None
        else booking.cancel_reason.value,
        filled_by=None,
        book_by=booking.start,
        fell_back_at=None,
        left_it_short=tuple(
            left.player_id
            for left in booking.departures
            if left.is_open and left.at < booking.cut_off
        ),
        paying={**booking.fixing_until, **booking.kept_until},
        fixing=frozenset(booking.cards_to_fix)
        | frozenset(
            player for player, kept in booking.kept.items() if kept.to_fix_the_card
        ),
        sender=booking.sender,
        invited=tuple(seat.player_id for seat in booking.waiting_at(at)),
        whole=booking.is_whole,
    )


@final
class GameStreamCourts:
    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def of_game(self, game_id: UUID, *, at: Instant) -> CourtBrief | None:
        return _court(await self._games.load(game_id), at=at)

    async def of_booking(self, booking_id: UUID, *, at: Instant) -> CourtBrief | None:
        return _court(await self._games.for_challenge(booking_id), at=at)


def _court(game: Game | None, *, at: Instant) -> CourtBrief | None:
    # A game with no hour was opened by no booking: nothing is asked of it.
    if game is None or game.starts_at is None:
        return None
    starts_at = game.starts_at
    states = game.attendance_at(at)
    players = game.line_up.players
    to_agree = frozenset(
        player for player in players if game.awaits_agreement_from(player, now=at)
    )
    # When what is on the table settles if nobody answers — the games' own
    # rule: a lone score when its day is up, two when the later one's is.
    settles = settlement_of(
        kind=game.kind, proposals=game.proposals, acceptance=game.acceptance
    )
    return CourtBrief(
        booking_id=game.challenge_id,
        competitive=game.kind is GameKind.COUNTED,
        sides={
            player: side.value
            for player in players
            if (side := game.line_up.side_of(player)) is not None
        },
        hour_ends_at=hour_ends_at(starts_at),
        awaiting_a_score=game.standing_at(at) is GameStanding.AWAITING_ENTRY,
        noted_by={
            player: absence.noted_by for player, absence in game.attendance.items()
        },
        awaited=frozenset(
            player
            for player, state in states.items()
            if state is AttendanceState.WAITING
        ),
        to_agree=to_agree,
        settles_at=settles.at if to_agree and settles is not None else None,
        claimed=frozenset(
            player
            for player, state in states.items()
            if state is AttendanceState.CLAIMED
        ),
        vouching=frozenset(
            player for player in players if states.get(player) not in NOT_HERE_STATES
        ),
        claims_close_at=late_claim_closes_at(starts_at),
    )


@final
class BookedHours:
    def __init__(self, directory: BookingDirectory) -> None:
        self._directory = directory

    async def ended(self, *, after: Instant, by: Instant) -> Sequence[UUID]:
        # The hour ends one booked game's length after it starts.
        return await self._directory.booked_starting(
            after=instant(after - A_BOOKED_GAME), by=instant(by - A_BOOKED_GAME)
        )


@final
class ProposalsDecks:
    def __init__(self, *, proposals: ProposalRepository, deck: ReadGroupDeck) -> None:
        self._proposals = proposals
        self._deck = deck

    async def showing(
        self, game_id: UUID, players: Collection[UUID], *, at: Instant
    ) -> tuple[UUID, ...]:
        proposal = None if not players else await self._proposals.load(game_id)
        if proposal is None:
            return ()
        shown: list[UUID] = []
        for player in players:
            if await self._deck.shows(player, proposal, now=at):
                shown.append(player)
        return tuple(shown)

    async def kind_of_court(self, game_id: UUID) -> bool | None:
        proposal = await self._proposals.load(game_id)
        return None if proposal is None else await self._deck.kind_of_court(proposal)


@final
class RescueSeatOffers:
    def __init__(
        self, *, pools: Pools, bookings: PlayerBookings, offers: RescueOffers
    ) -> None:
        self._pools = pools
        self._bookings = bookings
        self._offers = offers

    async def pool_of(self, game_id: UUID) -> tuple[UUID, ...]:
        game = await self._bookings.find(game_id)
        pool = None if game is None else await self._pools.find(game.pool_id)
        if pool is None:
            return ()
        return await self._pools.members_of(pool)

    async def offered_among(
        self, game_id: UUID, players: Collection[UUID], *, at: Instant
    ) -> tuple[UUID, ...]:
        game = await self._bookings.find(game_id)
        if game is None or not players or not rescuable(game, now=at):
            return ()
        candidates = await self._offers.candidates(
            sorted(players, key=str), sport=game.sport, games=[game], now=at
        )
        offered = await self._offers.offered(
            [game], candidates, sport=game.sport, now=at
        )
        return tuple(
            player for player in offered[game.booking_id] if player not in game.said_no
        )


@final
class SeatChargeShares:
    def __init__(self, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def of(self, charge_id: UUID) -> PaidShare | None:
        charge = await self._charges.load(charge_id)
        return None if charge is None else _share(charge)

    async def of_player(self, game_id: UUID, player_id: UUID) -> PaidShare | None:
        paid = [
            charge
            for charge in await self._charges.of_game(game_id)
            if charge.player_id == player_id and charge.status in PAID
        ]
        # A share given back is the one that was paid; there is one at most.
        return _share(paid[-1]) if paid else None

    async def has_a_charge(self, game_id: UUID, player_id: UUID) -> bool:
        return any(
            charge.player_id == player_id
            for charge in await self._charges.of_game(game_id)
        )


def _share(charge: SeatCharge) -> PaidShare:
    given = charge.refund_given
    return PaidShare(
        game_id=charge.game_id,
        refunded_grosze=(
            charge.given_back_grosze
            if charge.refund_withholds_fee is not None
            # No refund decided: giving it back would give the share.
            else charge.amount_grosze
        ),
        kept_grosze=None if given is None else given.fee_withheld_grosze,
        seat_taken=charge.refund_reason is RefundReason.SEAT_TAKEN,
    )


@final
class PlatformNames:
    def __init__(
        self, *, users: UserRepository, clubs: ClubNames, groups: GroupDirectory
    ) -> None:
        self._users = users
        self._clubs = clubs
        self._groups = groups

    async def of_people(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not player_ids:
            return {}
        return await self._users.find_nicknames_of(player_ids)

    async def of_clubs(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not club_ids:
            return {}
        return await self._clubs.names_of(club_ids)

    async def of_groups(self, group_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not group_ids:
            return {}
        listings = await self._groups.listings(group_ids)
        return {group_id: listing.name.value for group_id, listing in listings.items()}


@final
class FriendsOfTheReader:
    """``Friendships`` over Friends' own reads — the requests on the reader's
    Home, and the reader's friends — so a request is told and listed only while
    its card stands, and *friends made* only while they are (#745)."""

    def __init__(
        self, *, waiting: ReadRequestsWaiting, relations: ReadRelations
    ) -> None:
        self._waiting = waiting
        self._relations = relations

    async def waiting_on(self, reader: UUID) -> frozenset[WaitingRequest]:
        return frozenset(
            WaitingRequest(
                requester_id=request.requester_id, asked_at=request.asked_at
            )
            for request in await self._waiting.waiting(reader)
        )

    async def are_friends(self, one: UUID, other: UUID) -> bool:
        return other in await self._relations.friends_among(one, [other])


@final
class DirectoryGroupJoiners:
    """``GroupJoiners`` over the groups' own published directory — never their
    table, whose shape is that context's business."""

    def __init__(self, groups: GroupDirectory) -> None:
        self._groups = groups

    async def first_joined(
        self, *, after: Instant, by: Instant
    ) -> Mapping[UUID, Instant]:
        return await self._groups.first_joined(after=after, by=by)


@final
class RatingsRatedAccounts:
    """``RatedAccounts`` over rating's published read, which replays and holds
    nothing — so asking cannot move a Level. One batch per sport, and a player
    found rated is not asked about again."""

    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings

    async def rated_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        unknown = set(player_ids)
        rated: set[UUID] = set()
        for sport in Sport:
            if not unknown:
                break
            found = set(await self._ratings.estimates_for(unknown, sport=sport))
            rated |= found
            unknown -= found
        return frozenset(rated)
