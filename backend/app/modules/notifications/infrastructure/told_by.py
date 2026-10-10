"""What a notice says, read off the contexts that own it — every adapter
**signed here**, so the arrows run ``notifications → proposals``, ``→ bookings``,
``→ payments`` and ``→ users`` (a club's name is read through Proposals' own
``ClubNames``), and none of them knows a notice exists (#549).

``BookedAndProposedGames`` is a game as it stands: the proposal's stream folded,
and its booking's when it has one — one id for both. ``ProposalsDecks`` asks
**the deck itself** whether it shows a card to a reader
(``ReadGroupDeck.shows``), and ``RescueSeatOffers`` asks the Fill in board's
own ``RescueOffers`` who a seat is offered to — never a second reading of
either rule. ``SeatChargeShares`` is what a refund gives back — the provider's
own figures, never an estimate (#641). ``PlatformNames`` is a person's Name and
a club's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.bookings.domain.ports import BookingRepository
from app.modules.notifications.domain.ports import GameBrief, PaidShare
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
            return None
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
            waiting_for_the_club=filling and proposal.waiting_for_the_club,
            answer_by=booking.answer_by
            if booking is not None and booking.is_waiting
            else None,
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
            asked_the_club=booking is not None and booking.answer_by is not None,
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
            fell_back_at=(
                booking.taken_back_at
                if booking is not None and booking.taken_back_at is not None
                else proposal.fell_back_at
            ),
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
    def __init__(self, *, users: UserRepository, clubs: ClubNames) -> None:
        self._users = users
        self._clubs = clubs

    async def of_people(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not player_ids:
            return {}
        namings = await self._users.find_namings_of(player_ids)
        return {player_id: naming.name for player_id, naming in namings.items()}

    async def of_clubs(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        if not club_ids:
            return {}
        return await self._clubs.names_of(club_ids)
