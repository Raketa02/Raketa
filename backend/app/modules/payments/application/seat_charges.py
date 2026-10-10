"""Charging a game's seats, **all or nothing** (the mechanics §11–§12.2;
``docs/adr/0189`` §4; the mechanics Appendix A, *The fill*).

**Every seat is held first, on the club's account, off-session** — the player's
saved card cloned onto the seller's account for that one payment, authorised
with manual capture. Only when **every** seat is held does the game book; when
one is not, every hold is let go and **nobody pays**. A hold let go costs
nothing.

**Booked before the club's cut-off, every hold is kept and nothing is taken**
(#637; ADR-0189's 2026-10-10 amendment): each share stays held on its card for
the booked game until the cut-off, which takes it (``proposals``' cut-off job,
through ``TakeTheHeldShares``), and leaving before then lets it go — a
rescue's share too, which follows the seats it joins. **Booked after it, every
share is taken at once**, as before.

**A hold that would not last until the cut-off is a Card check** (#639; Q113):
a hold made without its player lasts days — 4 days 18 hours on a Visa — so a
game booked further ahead lets that seat's hold go at once, all or nothing
with the others, which proves the money was there that day, and the holding
job holds it again at its **Holding time**, four days before the cut-off
(``HoldTheCheckedShares``). A holding the card refuses gives its player their
time to fix the card on the booked game: confirmed in time it is kept
(``KeepTheFixedShare``), and run out it is let go with their seat
(``LetTheUnfixedShareGo``).

**The holds are asked inline, because their answer is the response** — *It's a
game!* or *your payment didn't go through* — and before anything is written
(``docs/adr/0190`` §4). What is written is the verdict: every charge **taken**
with the booking, or the refused ones recorded and the others **released**.
The capture and the cancellation at the provider follow the commit, from the
outbox (``handlers/settle_seat_charges.py``), so a crash between the verdict and
the money leaves a decision a subscriber retries rather than money moved with
nothing written.

**A key is the game, the player, the attempt and the hour.** The attempt is the
caller's — the game's own record of how many times it has tried to fill — so a
request retried after an outage asks for the same holds again and the provider
answers the first ones, while the next attempt after a refusal asks afresh. The
hour bounds an outage the provider stored against a key (``docs/adr/0190`` §4).
A hold made and then orphaned by a transaction that never committed is not
cancelled by anybody: the next attempt in the hour is answered it again, and
otherwise the provider lets it lapse untaken, which costs nothing.

**A hold the player confirmed in the app is taken rather than asked for again**
— their bank may check every payment, and that is the one it gave — when the
fill it confirmed for books. When another seat is refused instead, it is let go
with every other hold: *if any fails, the others are cancelled* — **unless the
refused player is given time to pay** (#625, #626; the mechanics §12.2, Q109):
then every other hold is **kept** on its card, the new ones recorded held, so
that paying in time books the game on them and nobody's bank is asked again.

**Nothing here commits**: the fill's transaction is the caller's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import final
from uuid import UUID

from app.application.ports import MailQueue
from app.kernel import Instant, Sport, invariant
from app.modules.payments.application.seat_charge_emails import (
    confirm_payment_email,
    game_booked_email,
)
from app.modules.payments.application.setup import key_hour
from app.modules.payments.domain.errors import (
    PaymentNotConfirmed,
    SeatChargeNotFound,
)
from app.modules.payments.domain.ports import (
    Payers,
    PaymentMethodRepository,
    SeatChargeRepository,
    Seller,
    Sellers,
)
from app.modules.payments.domain.provider import (
    Payment,
    PaymentProvider,
    PaymentStatus,
)
from app.modules.payments.domain.seat_charge import (
    PAID,
    FailureReason,
    SeatCharge,
    SeatChargeStatus,
    holding_time,
    reaches,
    taken_by,
)
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class GameToCharge:
    """The game whose seats are charged, as the fill knows it."""

    #: The proposal that filled — the id its booking takes.
    game_id: UUID
    club_id: UUID
    sport: Sport
    starts_at: Instant
    share_grosze: int
    #: The court it is booked on, for the confirmation.
    court_name: str
    #: The club's cut-off while it is ahead — every share is **held** for the
    #: booked game until then, and taken at it (#637) — or ``None`` when the
    #: game filled after it, and every share is taken at once.
    free_to_leave_until: Instant | None
    #: A seat a leaver left open on a booked game, taken by one player (#545)
    #: — its holds are keyed apart from the fill's, and a refusal asks them to
    #: confirm the payment to **take** the seat rather than to keep one.
    rescue: bool = False
    #: **Time to pay** (#625, #626): a refused share's seat is held for its
    #: player until then, and every other hold is kept for it — the email
    #: names the time. ``None`` lets every hold go: a rescue's refusal, and one
    #: with no time left before the book-by.
    pay_by: Instant | None = None
    #: The players already given time to pay, and when it ends: refused
    #: again, they keep it — and their email names it.
    paying_until: Mapping[UUID, Instant] = field(default_factory=dict)
    #: The game books on a payment it waited for (#625): the players were told
    #: *It's a game!* when it filled, so the receipt says *booked · you paid*
    #: (Q110) — but to the player whose payment booked it (``filled_by``), who
    #: sees *It's a game!* on their phone.
    booked_on_a_payment: bool = False
    filled_by: UUID | None = None


@final
@dataclass(frozen=True, slots=True)
class RefusedSeat:
    """A seat whose share could not be held, and the charge that says so."""

    charge_id: UUID
    reason: FailureReason


@final
@dataclass(frozen=True, slots=True)
class SeatsCharged:
    """Every seat held for the booked game or taken — ``refused`` is empty —
    or nobody: ``refused`` names whose share could not be held, and nothing
    was taken."""

    #: Each player's charge, when every seat was held for the game or taken.
    taken: Mapping[UUID, UUID]
    refused: Mapping[UUID, RefusedSeat]

    @property
    def all_taken(self) -> bool:
        return not self.refused


def hold_key(
    game_id: UUID, player_id: UUID, *, attempt: int, at: Instant, rescue: bool = False
) -> str:
    """The key a seat's hold is asked under: the game, the player, the attempt
    and the hour — a rescue's apart from the fill's (#545), since the two count
    their attempts on different streams and one game id carries both."""

    kind = "rescue" if rescue else "seat"
    return f"raketa-{kind}-{game_id}-{player_id}-{attempt}-{key_hour(at)}"


def _refusal_of(payment: Payment) -> FailureReason:
    return (
        FailureReason.AUTHENTICATION_REQUIRED
        if payment.status is PaymentStatus.AUTHENTICATION_REQUIRED
        else FailureReason.DECLINED
    )


@final
class ChargeTheSeats:
    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        charges: SeatChargeRepository,
        sellers: Sellers,
        payers: Payers,
        provider: PaymentProvider,
        mail: MailQueue,
        app_link: str,
    ) -> None:
        self._methods = methods
        self._charges = charges
        self._sellers = sellers
        self._payers = payers
        self._provider = provider
        self._mail = mail
        self._app_link = app_link

    async def execute(
        self,
        game: GameToCharge,
        players: Sequence[UUID],
        *,
        attempt: int,
        at: Instant,
    ) -> SeatsCharged:
        invariant(len(set(players)) == len(players), f"a seat twice: {players}")
        seller = (await self._sellers.of([game.club_id])).get(game.club_id)
        invariant(
            seller is not None and seller.account_id is not None,
            f"a game filled at {game.club_id}, which takes no payments",
        )
        assert seller is not None and seller.account_id is not None
        confirmed = {
            charge.player_id: charge
            for charge in await self._charges.of_game(game.game_id)
            if charge.held_now
        }

        held: dict[UUID, Payment] = {}
        refused: dict[UUID, tuple[FailureReason, Payment | None]] = {}
        for player in players:
            if player in confirmed:
                continue
            outcome = await self._hold(
                game, player, seller=seller, attempt=attempt, at=at
            )
            if isinstance(outcome, Payment):
                held[player] = outcome
            else:
                refused[player] = outcome

        if not refused:
            return await self._book_every_seat(
                game, players, held=held, confirmed=confirmed, seller=seller, at=at
            )
        return await self._nobody_pays(
            game,
            held=held,
            confirmed=[confirmed[player] for player in players if player in confirmed],
            refused=refused,
            seller=seller,
            at=at,
        )

    async def _hold(
        self,
        game: GameToCharge,
        player: UUID,
        *,
        seller: Seller,
        attempt: int,
        at: Instant,
    ) -> Payment | tuple[FailureReason, Payment | None]:
        """One seat's hold, or why it could not be made."""

        return await _held_on_the_card(
            player,
            methods=self._methods,
            provider=self._provider,
            seller=seller,
            amount_grosze=game.share_grosze,
            description=f"{game.sport.value.title()} · {seller.name}",
            game_id=game.game_id,
            key=hold_key(
                game.game_id, player, attempt=attempt, at=at, rescue=game.rescue
            ),
        )

    async def _book_every_seat(
        self,
        game: GameToCharge,
        players: Sequence[UUID],
        *,
        held: Mapping[UUID, Payment],
        confirmed: Mapping[UUID, SeatCharge],
        seller: Seller,
        at: Instant,
    ) -> SeatsCharged:
        """Every hold is the game's: kept until the cut-off — a rescue's too,
        like every seat it joins — or, booked after it, taken now. **A hold
        that would not last until the cut-off is checked** (#639): let go at
        once, and held again at its Holding time — unless that time has come,
        when it is kept and taken by its last safe moment (``taken_by``)."""

        until = game.free_to_leave_until
        taken: dict[UUID, UUID] = {}
        checked: dict[UUID, Instant] = {}
        for player in players:
            charge = confirmed.get(player) or _a_hold(
                game, player, held[player], seller=seller, at=at
            )
            if until is None:
                charge.take(booking_id=game.game_id, at=at)
            elif reaches(charge.last_moment, cut_off=until) or at >= holding_time(
                until
            ):
                charge.keep(
                    booking_id=game.game_id,
                    until=taken_by(charge.last_moment, cut_off=until),
                    at=at,
                )
            else:
                checked[player] = holding_time(until)
                charge.check(
                    booking_id=game.game_id,
                    until=until,
                    hold_at=checked[player],
                    at=at,
                )
            await self._charges.save(charge)
            taken[player] = charge.charge_id
        payers = await self._payers.of(players)
        for player in players:
            payer = payers.get(player)
            if payer is None:
                continue
            await self._mail.enqueue(
                game_booked_email(
                    to=payer.email,
                    name=payer.name,
                    club=seller.name,
                    court=game.court_name,
                    sport=game.sport,
                    starts_at=game.starts_at,
                    share_grosze=game.share_grosze,
                    held_until=until,
                    held_from=checked.get(player),
                    app_link=self._app_link,
                    booked_on_a_payment=game.booked_on_a_payment
                    and player != game.filled_by,
                ),
                at=at,
            )
        return SeatsCharged(taken=taken, refused={})

    async def _nobody_pays(
        self,
        game: GameToCharge,
        *,
        held: Mapping[UUID, Payment],
        confirmed: Sequence[SeatCharge],
        refused: Mapping[UUID, tuple[FailureReason, Payment | None]],
        seller: Seller,
        at: Instant,
    ) -> SeatsCharged:
        assert seller.account_id is not None
        made = [
            _a_hold(game, player, payment, seller=seller, at=at)
            for player, payment in held.items()
        ]
        if game.pay_by is None:
            for charge in [*made, *confirmed]:
                charge.release(at=at)
                await self._charges.save(charge)
        else:
            # Time to pay: every hold waits on its card for the payment in
            # time, and the game books on them (Q109).
            for charge in made:
                await self._charges.save(charge)
        seats: dict[UUID, RefusedSeat] = {}
        for player, (reason, answer) in refused.items():
            charge = SeatCharge.refused(
                charge_id=new_uuid(),
                player_id=player,
                game_id=game.game_id,
                club_id=game.club_id,
                account_id=seller.account_id,
                amount_grosze=game.share_grosze,
                sport=game.sport,
                starts_at=game.starts_at,
                reason=reason,
                payment=answer,
                at=at,
            )
            await self._charges.save(charge)
            seats[player] = RefusedSeat(charge_id=charge.charge_id, reason=reason)
        if game.pay_by is None and not game.rescue:
            # No time is left to pay — the book-by had come at the club's yes:
            # the game is called off, and told so; there is nothing to confirm.
            return SeatsCharged(taken={}, refused=seats)
        payers = await self._payers.of(list(refused))
        for player, seat in seats.items():
            payer = payers.get(player)
            if payer is None:
                continue
            await self._mail.enqueue(
                confirm_payment_email(
                    to=payer.email,
                    club=seller.name,
                    sport=game.sport,
                    starts_at=game.starts_at,
                    amount_grosze=game.share_grosze,
                    reason=seat.reason,
                    app_link=self._app_link,
                    rescue=game.rescue,
                    pay_by=game.paying_until.get(player, game.pay_by),
                    # Refused before the cut-off, where the share would only be
                    # held: their time is to fix the card (#638).
                    cut_off=game.free_to_leave_until,
                ),
                at=at,
            )
        return SeatsCharged(taken={}, refused=seats)


async def _held_on_the_card(
    player: UUID,
    *,
    methods: PaymentMethodRepository,
    provider: PaymentProvider,
    seller: Seller,
    amount_grosze: int,
    description: str,
    game_id: UUID,
    key: str,
) -> Payment | tuple[FailureReason, Payment | None]:
    """One share held on a player's saved card, cloned onto the club's account
    for that one payment — or why it could not be: a player with no method, or
    whose card the terms in force were not accepted for, is refused **without
    asking the provider** (the mechanics §19)."""

    assert seller.account_id is not None
    method = await methods.load(player)
    if method.method is None or method.customer_id is None:
        return FailureReason.NO_METHOD, None
    if method.terms_needed:
        # A brand the terms were not accepted for cannot be charged off-session
        # until its holder agrees again.
        return FailureReason.TERMS_NEEDED, None
    clone = await provider.clone_method(
        customer_id=method.customer_id,
        method_id=method.method.method_id,
        account_id=seller.account_id,
        idempotency_key=f"{key}-clone",
    )
    payment = await provider.authorise(
        account_id=seller.account_id,
        method_id=clone,
        amount_grosze=amount_grosze,
        description=description,
        metadata={"game_id": str(game_id), "player_id": str(player)},
        idempotency_key=key,
    )
    if payment.status is PaymentStatus.AUTHORISED:
        return payment
    return _refusal_of(payment), payment


def _a_hold(
    game: GameToCharge, player: UUID, payment: Payment, *, seller: Seller, at: Instant
) -> SeatCharge:
    """A hold the provider just made, as the charge it is born."""

    assert seller.account_id is not None
    return SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player,
        game_id=game.game_id,
        club_id=game.club_id,
        account_id=seller.account_id,
        payment=payment,
        sport=game.sport,
        starts_at=game.starts_at,
        at=at,
    )


@final
class TakeTheHeldShares:
    """**The club's cut-off takes the shares held for its booked game** (#637;
    ADR-0189's 2026-10-10 amendment): each one is taken in the caller's
    transaction, and captured at the provider from the outbox after the
    commit, which records the real fee kept on it. **No commit.**"""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def due(self, *, at: Instant) -> Sequence[UUID]:
        """Every game with a share still held whose cut-off has come."""

        return await self._charges.games_held_until(at)

    async def execute(self, game_id: UUID, *, at: Instant) -> int:
        """Take every share held for this game whose moment has come — the
        cut-off, or a holding's last safe moment (#639). Answers how many."""

        taken = 0
        for charge in await self._charges.of_game(game_id):
            if (
                charge.held_until is not None
                and charge.held_until <= at
                and charge.take_at_the_cut_off(at=at)
            ):
                await self._charges.save(charge)
                taken += 1
        return taken


def holding_key(charge: SeatCharge, *, at: Instant) -> str:
    """The key a checked share's holding is asked under: the charge, the
    attempt — its stream version, so a holding asked again after the terms
    were fixed asks afresh — and the hour (#639)."""

    return f"raketa-holding-{charge.charge_id}-{charge.version}-{key_hour(at)}"


@final
@dataclass(frozen=True, slots=True)
class HoldingDone:
    """What one game's holding did: whose shares were held again, and whose
    were refused — each player's charge and why."""

    held: frozenset[UUID]
    refused: Mapping[UUID, RefusedSeat]


@final
class HoldTheCheckedShares:
    """**The Holding time** (#639; the mechanics Q113): every share checked at
    its game's fill is held again, four days before the cut-off, to stay until
    it — **inline**, as the fill's holds are, because whether it holds decides
    what the booked game asks of its player. A holding that still would not
    reach the cut-off is taken by its last safe moment (``taken_by``). **A
    refused holding** is recorded, and its player emailed to fix their card
    by ``fix_by`` — whose seat is theirs until then is the booked game's to
    say. A share refused for want of terms or a method is asked again on each
    run once its player fixed them, and records nothing until then. **No
    commit.**"""

    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        charges: SeatChargeRepository,
        sellers: Sellers,
        payers: Payers,
        provider: PaymentProvider,
        mail: MailQueue,
        app_link: str,
    ) -> None:
        self._methods = methods
        self._charges = charges
        self._sellers = sellers
        self._payers = payers
        self._provider = provider
        self._mail = mail
        self._app_link = app_link

    async def due(self, *, at: Instant) -> Sequence[UUID]:
        """Every game with a share checked whose Holding time has come — the
        earliest first."""

        return await self._charges.games_to_hold_by(at)

    async def execute(
        self,
        game_id: UUID,
        *,
        fix_by: Instant,
        at: Instant,
        fixing_until: Mapping[UUID, Instant] | None = None,
    ) -> HoldingDone:
        """``fixing_until`` names the players already given their time to fix
        the card, and when it ends: refused again, they keep it."""

        due = [
            charge
            for charge in await self._charges.of_game(game_id)
            if charge.hold_at is not None
            and charge.hold_at <= at
            and (
                charge.status is SeatChargeStatus.CHECKED
                or (charge.refused_at_its_holding and charge.payment_id is None)
            )
        ]
        if not due:
            return HoldingDone(held=frozenset(), refused={})
        seller = (await self._sellers.of([due[0].club_id])).get(due[0].club_id)
        invariant(
            seller is not None and seller.account_id is not None,
            f"{game_id} held at {due[0].club_id}, which takes no payments",
        )
        assert seller is not None
        held: set[UUID] = set()
        refused: dict[UUID, RefusedSeat] = {}
        for charge in due:
            assert charge.held_until is not None
            outcome = await _held_on_the_card(
                charge.player_id,
                methods=self._methods,
                provider=self._provider,
                seller=seller,
                amount_grosze=charge.amount_grosze,
                description=f"{charge.sport.value.title()} · {seller.name}",
                game_id=game_id,
                key=holding_key(charge, at=at),
            )
            if isinstance(outcome, Payment):
                charge.hold_again(
                    outcome,
                    until=taken_by(outcome.last_moment, cut_off=charge.held_until),
                    at=at,
                )
                held.add(charge.player_id)
            else:
                reason, answer = outcome
                if charge.holding_refused(reason, payment=answer, at=at):
                    refused[charge.player_id] = RefusedSeat(
                        charge_id=charge.charge_id, reason=reason
                    )
            await self._charges.save(charge)
        await self._ask_to_fix(
            [charge for charge in due if charge.player_id in refused],
            seller=seller,
            fix_by=fix_by,
            fixing_until=fixing_until or {},
            at=at,
        )
        return HoldingDone(held=frozenset(held), refused=refused)

    async def _ask_to_fix(
        self,
        refused: Sequence[SeatCharge],
        *,
        seller: Seller,
        fix_by: Instant,
        fixing_until: Mapping[UUID, Instant],
        at: Instant,
    ) -> None:
        """*Fix your card by 19:30 to keep your seat* — to each player whose
        holding was refused, by the time they have."""

        payers = await self._payers.of([charge.player_id for charge in refused])
        for charge in refused:
            payer = payers.get(charge.player_id)
            if payer is None or charge.failure is None:
                continue
            assert charge.held_until is not None
            await self._mail.enqueue(
                confirm_payment_email(
                    to=payer.email,
                    club=seller.name,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    amount_grosze=charge.amount_grosze,
                    reason=charge.failure,
                    app_link=self._app_link,
                    pay_by=fixing_until.get(charge.player_id, fix_by),
                    cut_off=charge.held_until,
                    at_the_holding=True,
                ),
                at=at,
            )


@final
class KeepTheFixedShare:
    """**Fixed in time** (#639): a share refused at its Holding time that its
    player confirmed — the payment the provider holds now — is kept for the
    booked game until the cut-off, as a holding's is. Answers whether it was:
    nothing for a charge that is no refused holding confirmed. **No
    commit.**"""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(self, charge_id: UUID, *, at: Instant) -> bool:
        charge = await self._charges.load(charge_id)
        if (
            charge is None
            or charge.status is not SeatChargeStatus.AUTHORISED
            or charge.booking_id is None
            or charge.held_until is None
        ):
            return False
        charge.keep(
            booking_id=charge.booking_id,
            until=taken_by(charge.last_moment, cut_off=charge.held_until),
            at=at,
            fixed=True,
        )
        await self._charges.save(charge)
        return True


@final
class LetTheUnfixedShareGo:
    """**Not fixed in time** (#639): the share refused at its Holding time is
    let go with its player's seat — its payment cancelled from the outbox — and
    they owe nothing. **No commit.**"""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(self, game_id: UUID, player_id: UUID, *, at: Instant) -> int:
        """Answers how many were let go."""

        let_go = 0
        for charge in await self._charges.of_game(game_id):
            if charge.player_id == player_id and charge.to_fix and charge.let_go(at=at):
                await self._charges.save(charge)
                let_go += 1
        return let_go


@final
class ReleaseCharges:
    """Let go of every charge on a game that it will not be paid with — a
    refused payment the seat was taken from, or a hold confirmed for a game
    that filled without it or never filled. **No commit.**"""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(
        self,
        game_id: UUID,
        *,
        keeping: Collection[UUID],
        of_player: UUID | None = None,
        at: Instant,
    ) -> int:
        """Release every undecided charge on ``game_id`` that is not one of
        ``keeping`` — only ``of_player``'s, when one is named. Answers how many
        were released."""

        released = 0
        for charge in await self._charges.of_game(game_id):
            if charge.charge_id in keeping:
                continue
            if of_player is not None and charge.player_id != of_player:
                continue
            if charge.release(at=at):
                await self._charges.save(charge)
                released += 1
        return released


@final
class PaymentToConfirmOn:
    """This player's refused payment for this game still waiting for them —
    what a rescue's second *I'm in* is told to confirm rather than asking the
    bank the same question again (#545)."""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(self, game_id: UUID, *, player_id: UUID) -> UUID | None:
        for charge in reversed(await self._charges.of_game(game_id)):
            if charge.player_id == player_id and charge.awaits_its_player:
                return charge.charge_id
        return None


@final
@dataclass(frozen=True, slots=True)
class ConfirmedCharge:
    """A refused charge its player confirmed: held now, for this game."""

    charge_id: UUID
    game_id: UUID


@final
class ConfirmSeatCharge:
    """*I confirmed my payment in the app.* **Asked of the provider, never
    taken on the phone's word**: the payment is read as it stands, and only a
    payment it holds is recorded as confirmed. No commit — the yes it stands for
    is the caller's, in the same transaction."""

    def __init__(
        self, *, charges: SeatChargeRepository, provider: PaymentProvider
    ) -> None:
        self._charges = charges
        self._provider = provider

    async def execute(
        self, charge_id: UUID, *, player_id: UUID, at: Instant
    ) -> ConfirmedCharge:
        charge = await self._charges.load(charge_id)
        if charge is None or charge.player_id != player_id:
            raise SeatChargeNotFound()
        if charge.status is SeatChargeStatus.AUTHORISED:
            # Confirmed already — by an earlier request, or by the provider's
            # notice that arrived first.
            return ConfirmedCharge(charge_id=charge_id, game_id=charge.game_id)
        if charge.status is not SeatChargeStatus.FAILED or charge.payment_id is None:
            raise PaymentNotConfirmed(
                status=charge.status.value
                if charge.status is not SeatChargeStatus.FAILED
                else "NOTHING_TO_CONFIRM"
            )
        payment = await self._provider.read_payment(
            account_id=charge.account_id, payment_id=charge.payment_id
        )
        if payment.status is not PaymentStatus.AUTHORISED:
            raise PaymentNotConfirmed(status=payment.status.value)
        charge.confirm(at=at, last_moment=payment.last_moment)
        await self._charges.save(charge)
        return ConfirmedCharge(charge_id=charge_id, game_id=charge.game_id)


@final
@dataclass(frozen=True, slots=True)
class ChargeToConfirm:
    """What the phone needs to confirm a refused payment on the club's
    account: the payment's secret and the seller's account, asked of the
    provider now and never recorded."""

    client_secret: str
    account_id: str
    publishable_key: str


@final
@dataclass(frozen=True, slots=True)
class SeatChargeReading:
    charge: SeatCharge
    club_name: str | None
    #: Present exactly while the payment waits for its player.
    to_confirm: ChargeToConfirm | None


@final
class ReadSeatCharge:
    """One of the reader's own charges — and, while its payment waits for them,
    what the phone confirms it with."""

    def __init__(
        self,
        *,
        charges: SeatChargeRepository,
        sellers: Sellers,
        provider: PaymentProvider,
    ) -> None:
        self._charges = charges
        self._sellers = sellers
        self._provider = provider

    async def execute(self, charge_id: UUID, *, player_id: UUID) -> SeatChargeReading:
        charge = await self._charges.load(charge_id)
        if charge is None or charge.player_id != player_id:
            raise SeatChargeNotFound()
        seller = (await self._sellers.of([charge.club_id])).get(charge.club_id)
        to_confirm = None
        if charge.awaits_its_player:
            assert charge.payment_id is not None
            payment = await self._provider.read_payment(
                account_id=charge.account_id, payment_id=charge.payment_id
            )
            if payment.client_secret is not None:
                to_confirm = ChargeToConfirm(
                    client_secret=payment.client_secret,
                    account_id=charge.account_id,
                    publishable_key=self._provider.publishable_key(),
                )
        return SeatChargeReading(
            charge=charge,
            club_name=None if seller is None else seller.name,
            to_confirm=to_confirm,
        )


class ReceiptKind(StrEnum):
    """Which way the money went — or that it never moved."""

    #: A share paid.
    CHARGE = "CHARGE"
    #: A share given back (#544).
    REFUND = "REFUND"
    #: A share held for a booked game and let go untaken (#641): *40 zł held ·
    #: released*, so the hold the bank app showed is explained.
    RELEASED = "RELEASED"


@final
@dataclass(frozen=True, slots=True)
class Receipt:
    """Money that moved for the player, or was held and let go: to whom, for
    which game, how much, which way, when."""

    charge: SeatCharge
    club_name: str | None
    kind: ReceiptKind = ReceiptKind.CHARGE

    @property
    def amount_grosze(self) -> int:
        """What was paid, what came back, or what was held — always
        positive."""

        if self.kind is ReceiptKind.REFUND:
            assert self.charge.refund_given is not None
            return self.charge.refund_given.amount_grosze
        return self.charge.amount_grosze

    @property
    def card_fee_grosze(self) -> int | None:
        """Exactly what was kept on the payment, on a refund — nought on one in
        full; ``None`` on a charge and on a hold let go."""

        if self.kind is ReceiptKind.REFUND:
            assert self.charge.refund_given is not None
            return self.charge.refund_given.fee_withheld_grosze
        return None

    @property
    def at(self) -> Instant:
        """When the money moved: taken, or given back — the act that decided
        the refund, a leaving or a call-off, rather than the provider's answer
        moments later — or when the hold was let go."""

        if self.kind is ReceiptKind.REFUND:
            assert self.charge.refund_decided_at is not None
            return self.charge.refund_decided_at
        if self.kind is ReceiptKind.RELEASED:
            assert self.charge.released_at is not None
            return self.charge.released_at
        return self.charge.taken_at or self.charge.opened_at


@final
class ReadReceipts:
    """You › Payments' *RECEIPTS*: every share the reader paid and every share
    given back (#544), **the club named as the seller**, the latest first — a
    refund once the provider has given it, with exactly what was kept on the
    payment — and every share held for a booked game and let go untaken, *held
    · released* (#641): a leave, a call-off or the club's cancel before the
    cut-off. A hold the fill released because the game did not book on it is
    not here: it never held anything for a game."""

    def __init__(self, *, charges: SeatChargeRepository, sellers: Sellers) -> None:
        self._charges = charges
        self._sellers = sellers

    async def execute(self, player_id: UUID) -> tuple[Receipt, ...]:
        charges = [
            charge
            for charge in await self._charges.receipts_of(player_id)
            if charge.status in PAID or charge.released_at is not None
        ]
        sellers = await self._sellers.of({charge.club_id for charge in charges})
        receipts: list[Receipt] = []
        for charge in charges:
            club_name = (
                sellers[charge.club_id].name if charge.club_id in sellers else None
            )
            if charge.status not in PAID:
                receipts.append(
                    Receipt(
                        charge=charge, club_name=club_name, kind=ReceiptKind.RELEASED
                    )
                )
                continue
            receipts.append(Receipt(charge=charge, club_name=club_name))
            if charge.refund_given is not None:
                receipts.append(
                    Receipt(
                        charge=charge, club_name=club_name, kind=ReceiptKind.REFUND
                    )
                )
        # Latest first; a refund given at the moment of its charge after it.
        return tuple(
            sorted(
                receipts,
                key=lambda receipt: (receipt.at, receipt.kind is ReceiptKind.REFUND),
                reverse=True,
            )
        )
