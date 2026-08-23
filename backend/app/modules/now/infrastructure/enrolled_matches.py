"""``EnrolledMatches`` over Matches, Clubs, Courts, Users and Money.

The one file in Now that knows a player's own matches are seats and departures in
the Matches context, that a club is where the zone and the roof come from, that
the court a match will be played on is a **reservation**, that the names on a
scoreline are user rows, and that what she has actually paid is a fold off her
ledger.

**Five ports and no session**, on the precedent ``ArrivalsFromUsersAndClubs``
set: what backs a match, a club, a reservation, a user or a ledger is those
contexts' business, and the day any of them answers faster only its own adapter
moves.

**It reads facts and decides nothing.** The court is returned whether or not it
may be shown; the score is returned in the order it was stored. Every rule —
which situation, which clock, which counts, when a card dies, whose side goes
first — is in ``ComposeEnrolled``, where it can be exercised without a database.

**The cost is stated rather than hidden.** One read finds her matches; the clubs
and the score's names are batched; her ledger is loaded **once** for all of them,
because a ledger is one stream per player and every seat's fold comes off it. The
reservation is a read per match, which is the one loop here — a strip is a
player's own matches, so it is a handful, and a player who outgrows it wants a
projection behind ``EnrolledMatches``.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Grosze, Instant, Recoverable, grosze

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.matches.domain.departure import Departure
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository
from app.modules.matches.domain.seat import Seat
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.ports import LedgerRepository
from app.modules.now.domain.enrolled import Enrolment, PlayedScore
from app.modules.now.domain.screen import (
    CardDeparture,
    DepartureNothingTaken,
    DepartureRecoverable,
    Money,
    Place,
)
from app.modules.users.domain.ports import UserRepository


class EnrolledFromMatches:
    """Her matches, and everything five contexts have to say about each one."""

    def __init__(
        self,
        *,
        matches: MatchRepository,
        clubs: ClubRepository,
        reservations: ReservationRepository,
        users: UserRepository,
        ledgers: LedgerRepository,
    ) -> None:
        self._matches = matches
        self._clubs = clubs
        self._reservations = reservations
        self._users = users
        self._ledgers = ledgers

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[Enrolment, ...]:
        matches = await self._matches.for_player(player_id)
        if not matches:
            # A player with no matches pays for no club read, no ledger replay
            # and no reservation loop — which is most players on most screens.
            return ()

        clubs = {
            club.id: club
            for club in await self._clubs.find_by_ids(
                sorted({match.club_id for match in matches})
            )
        }
        nicknames = await self._nicknames(matches)
        ledger = await self._ledgers.load(player_id)

        rows: list[Enrolment] = []
        for match in matches:
            club = clubs.get(match.club_id)
            if club is None:
                # A match at a club this read cannot see is a card that would
                # have to name a venue it does not know. Dropped silently, the
                # way `ArrivalRows` is *"silently short on a stranger"* — a
                # broken card is worse than a missing one.
                continue
            rows.append(
                await self._row(
                    match,
                    club=club,
                    nicknames=nicknames,
                    ledger=ledger,
                    player_id=player_id,
                    now=now,
                )
            )
        return tuple(rows)

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> Enrolment | None:
        """One match, for a viewer who is something to it. Four reads, not five.

        **Its membership is wider than ``for_player``'s by exactly one case.**
        That query answers *a seat that names her, or a departure that does*;
        this also resolves for a viewer holding a **live seat claim**, who holds
        no seat yet (ADR-0081) and whose departure route must still open and
        answer *no*. Anybody else is a stranger and gets nothing.

        A match at a club this read cannot see is ``None`` rather than a card
        naming a venue it does not know — the same silence ``for_player`` keeps,
        and here it costs a 404 rather than a missing row.
        """

        match = await self._matches.get(match_id)
        if match is None:
            return None
        seat = match.seat_of(player_id)
        departure = match.departure_of(player_id)
        claim = _claim(match, player_id, now)
        if seat is None and departure is None and claim is None:
            return None

        club = await self._clubs.get(match.club_id)
        if club is None:
            return None
        return await self._row(
            match,
            club=club,
            # A score names people, and nothing else on a card does — so this
            # read is paid on exactly the two situations that print one.
            nicknames=await self._nicknames([match]),
            ledger=await self._ledgers.load(player_id),
            player_id=player_id,
            now=now,
        )

    async def _row(
        self,
        match: Match,
        *,
        club: Club,
        nicknames: dict[UUID, str],
        ledger: Ledger,
        player_id: UUID,
        now: Instant,
    ) -> Enrolment:
        """One match as Now's own row. The one place an ``Enrolment`` is built."""

        seat = match.seat_of(player_id)
        departure = match.departure_of(player_id)
        return Enrolment(
            match_id=match.id,
            record=match.as_record(),
            where=_place(club, match),
            share=Money(amount=grosze(int(match.share))),
            court_total=Money(amount=_court_total(match)),
            closed_at=match.closed_at,
            holds_seat=seat is not None,
            claim_expires_at=_claim(match, player_id, now),
            court=await self._court(club, match),
            score=_score(match, nicknames, player_id),
            departure=None if departure is None else _departure(departure),
            paid_in=_paid_in(ledger, match, seat_index=_seat_index(seat, departure)),
        )

    async def _nicknames(self, matches: list[Match]) -> dict[UUID, str]:
        """Every player named on a scoreline, in one read.

        Only matches that carry a score contribute: a card names a person on
        exactly two situations, and reading four nicknames for every forming
        match on the strip would be four reads for a card that names nobody.
        """

        wanted = {
            seat.player_id
            for match in matches
            if match.score is not None
            for seat in match.seats
            if seat.player_id is not None
        }
        if not wanted:
            return {}
        return {
            user.id: user.nickname.value
            for user in await self._users.find_by_ids(sorted(wanted))
        }

    async def _court(self, club: Club, match: Match) -> str | None:
        """Which court the reservation names, if a court has been assigned.

        **Whether it may be printed is not decided here.** A court is assigned
        and may be reassigned until fifteen minutes before play, and the rule
        that says so is ``kernel.court_named_at``, applied once in the composer.
        """

        reservation = await self._reservations.for_match(match.id)
        if reservation is None or reservation.released_at is not None:
            return None
        label = club.court(reservation.court_id).label
        return None if label is None else label.value


def _place(club: Club, match: Match) -> Place:
    """Where: the club, its clock face, and whether there is a roof.

    The cover is read **live** off the category rather than copied onto the
    match, unlike the rate: the price was agreed when the match was posted, and
    the roof is a fact about the evening she is walking into (ADR-0090). A
    category's cover never changes, so there is no history to resolve as of an
    instant.
    """

    return Place(
        club_id=club.id,
        club_name=club.name.value,
        zone=club.timezone,
        cover=club.category(match.category_id).cover,
        # No distance, and it is the modelled answer rather than a gap: a
        # distance is measured from the glossary's Distance anchor, the anchor
        # is optional, and precision follows it (ADR-0063).
        distance_km=None,
    )


def _court_total(match: Match) -> Grosze:
    """What the whole court cost, which is the share times the seats.

    Exact, and that rests on a law rather than on an observation: a whole-złoty
    court price is a multiple of a hundred grosze and both 100 ÷ 2 and 100 ÷ 4
    are integers, so the split never rounds and multiplying back never drifts.
    """

    return grosze(int(match.share) * len(match.seats))


def _claim(match: Match, player_id: UUID, now: Instant) -> Instant | None:
    claim = match.live_claim_of(player_id, at=now)
    return None if claim is None else claim.expires_at


def _seat_index(seat: Seat | None, departure: Departure | None) -> int | None:
    """Which seat her money was about — the one she holds, or the one she left.

    A leaver's seat may be somebody else's by now, which is exactly why the
    departure remembers the index: her ledger's movements are filed against the
    seat she paid for, and the refill does not move them.
    """

    if seat is not None:
        return seat.index
    return None if departure is None else departure.seat_index


def _paid_in(ledger: Ledger, match: Match, *, seat_index: int | None) -> Money | None:
    """What she has actually put in for this seat, folded off her own ledger.

    ``None`` when there is no seat to ask about. Zero is a real answer and is
    kept as one — a seat taken and never paid for has a fold of nothing, and the
    composer is what turns that into *no refund line* rather than *0,00 zł back*.
    """

    if seat_index is None:
        return None
    fold = ledger.funded_by_the_player_for(SeatRef(match_id=match.id, index=seat_index))
    return Money(amount=fold)


def _score(
    match: Match, nicknames: dict[UUID, str], player_id: UUID
) -> PlayedScore | None:
    """The stored score, with each side's players named, in the match's order.

    Side A is the first half of the seats and side B the second, in the seats'
    fixed order — Matches' own definition, so the score means the same thing
    however a card arranges the names.

    The viewer's side is found from the seat she holds **or the one she left**,
    because a leaver who played and then left after the match is still on one
    side of that net.
    """

    if match.score is None:
        return None
    half = len(match.seats) // 2
    sides = tuple(
        tuple(
            nicknames[seat.player_id]
            for seat in match.seats[start : start + half]
            if seat.player_id is not None and seat.player_id in nicknames
        )
        for start in (0, half)
    )
    index = _seat_index(match.seat_of(player_id), match.departure_of(player_id))
    return PlayedScore(
        sides=(sides[0], sides[1]),
        sets=tuple((one.side_a, one.side_b) for one in match.score.sets),
        viewer_side=None if index is None else (0 if index < half else 1),
    )


def _departure(departure: Departure) -> CardDeparture:
    """Her departure in one of its **two forms**, never one with a blank amount.

    The union is already the aggregate's — ``LeaverMoney`` is ``NothingTaken |
    Recoverable`` — so this is a translation between two spellings of one shape
    rather than a decision, and the reason it exists at all is that a card also
    carries the outcome and the ledger's payload does not.
    """

    money = departure.money
    if not isinstance(money, Recoverable):
        return DepartureNothingTaken()
    return DepartureRecoverable(
        paid=Money(amount=money.amount),
        outcome=departure.outcome,
    )
