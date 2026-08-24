"""``OfferedSeats`` over the offers table, Matches, Clubs and Courts.

The one file in Now that knows an offered seat is a row the cascade wrote, that
the match behind it is the Matches context's, that a club is where the zone and
the roof come from, and that the court is a reservation.

**Four ports and no session**, on the precedent ``EnrolledFromMatches`` set — and
the first of the four is a port of Now's own. ``Offers`` is the store the cascade
writes and this reads it rather than the table, so ``offer_of`` stays the one
place a stored rung becomes a ``Rung``: two mappings of that integer would be two
answers to *which rung was she on*, which is the one thing a seeded offer's check
exists to catch.

**It reads facts and decides nothing.** Every offer she has ever been made comes
back, alive or not — *"whether the seat is still there is a question about the
match, asked at the instant the screen is composed"* — and so does the court,
whether or not it may yet be named. The rules are ``ComposeOffers``'s, where they
can be exercised without a database.

**The cost is stated rather than hidden.** One read finds her offers; the matches
behind them are loaded one apiece and **deduplicated first**, because a match that
lost two players has two holes and one card; the clubs are batched. What is not
bounded is the offer list itself: it grows with how often seats free in her band,
which is a fact about the platform rather than about her, and `#125` is where the
projection lands. What keeps it honest today is that the seeded and launch-volume
answer is a handful of rows.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Grosze, Instant, grosze

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository
from app.modules.now.domain.cascade import Offer
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.ports import Offers
from app.modules.now.domain.screen import Money, Place


class OfferedFromTheCascade:
    """Her offers, and everything three contexts have to say about each match."""

    def __init__(
        self,
        *,
        offers: Offers,
        matches: MatchRepository,
        clubs: ClubRepository,
        reservations: ReservationRepository,
    ) -> None:
        self._offers = offers
        self._matches = matches
        self._clubs = clubs
        self._reservations = reservations

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[OfferedSeat, ...]:
        """Every seat put in front of her, whether or not it is still there."""

        offers = await self._offers.held_by(player_id)
        if not offers:
            # A player who has never been told about a seat pays for no match
            # read, no club read and no reservation loop — which is most players
            # on most screens.
            return ()

        # **The newest offer per match wins**, and the read is ordered newest
        # first, so the first one seen is the one kept. A match that lost two
        # players has two holes and therefore two offers to the same person, and
        # a card is about the match: two cards for one match would be the same
        # seat offered twice.
        newest: dict[UUID, Offer] = {}
        for offer in offers:
            newest.setdefault(offer.match_id, offer)

        matches = await self._load(sorted(newest, key=str))
        if not matches:
            return ()
        clubs = {
            club.id: club
            for club in await self._clubs.find_by_ids(
                sorted({match.club_id for match in matches.values()})
            )
        }

        rows: list[OfferedSeat] = []
        for match_id, offer in newest.items():
            match = matches.get(match_id)
            if match is None:
                continue
            club = clubs.get(match.club_id)
            if club is None:
                # A match at a club this read cannot see is a card that would
                # have to name a venue it does not know. Dropped silently, the
                # way the strip's own missing club is: a broken card is worse
                # than a missing one.
                continue
            rows.append(
                await self._row(
                    match, offer=offer, club=club, player_id=player_id, now=now
                )
            )
        return tuple(rows)

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> OfferedSeat | None:
        """The newest offer she holds on this one match, if she holds one.

        A second method rather than the caller filtering ``for_player``, on
        ``EnrolledMatches.one``'s rule: on a write path, filtering would load
        every match she has ever been told about to answer a question about one.
        """

        offer = next(
            (
                one
                for one in await self._offers.held_by(player_id)
                if one.match_id == match_id
            ),
            None,
        )
        if offer is None:
            return None
        match = await self._matches.get(match_id)
        if match is None:
            return None
        club = await self._clubs.get(match.club_id)
        if club is None:
            return None
        return await self._row(
            match, offer=offer, club=club, player_id=player_id, now=now
        )

    async def _load(self, match_ids: list[UUID]) -> dict[UUID, Match]:
        """The matches behind her offers, one read apiece.

        The one loop here, and it is the shape the strip already carries: there
        is no batch read on ``MatchRepository`` and adding one for this would be
        widening another context's port from inside Now. Deduplication happens
        **before** the loop rather than after it, so two holes in one match cost
        one read.
        """

        loaded: dict[UUID, Match] = {}
        for match_id in match_ids:
            match = await self._matches.get(match_id)
            if match is not None:
                loaded[match_id] = match
        return loaded

    async def _row(
        self,
        match: Match,
        *,
        offer: Offer,
        club: Club,
        player_id: UUID,
        now: Instant,
    ) -> OfferedSeat:
        """One offer as Now's own row. The one place an ``OfferedSeat`` is built."""

        return OfferedSeat(
            match_id=match.id,
            vacancy_id=offer.vacancy_id,
            record=match.as_record(),
            where=_place(club, match),
            kind=offer.kind,
            rung=offer.player_rung,
            # The seat's own share, **not** the amount stored on the offer: the
            # composer applies `kernel.seat_price` to it at the composing instant,
            # so a card quotes the rescue tier that is running now rather than the
            # one that was running when she was told.
            share=Money(amount=grosze(int(match.share))),
            court_total=Money(amount=_court_total(match)),
            offered_at=offer.offered_at,
            already_mine=_already_mine(match, player_id, now),
            court=await self._court(club, match),
        )

    async def _court(self, club: Club, match: Match) -> str | None:
        """Which court the reservation names, if a court has been assigned.

        **Whether it may be printed is not decided here**, exactly as it is not
        in the strip's adapter: a court is assigned and may be reassigned until
        fifteen minutes before play, and ``kernel.court_named_at`` is the rule,
        applied once in the composer.
        """

        reservation = await self._reservations.for_match(match.id)
        if reservation is None or reservation.released_at is not None:
            return None
        label = club.court(reservation.court_id).label
        return None if label is None else label.value


def _already_mine(match: Match, player_id: UUID, at: Instant) -> bool:
    """Whether this match is hers already, in the three senses the pool means.

    A seat, a live seat claim, or a departure she made herself — read here
    because they are facts about the pair and answered by the aggregate, and
    judged in ``ComposeOffers`` because *what that means for the card* is a rule.

    The claim is composed against the **composing instant**, so it stops counting
    at the moment her five minutes run out rather than when a reaper writes the
    receipt — which is ADR-0081's *"live is composed, never latched"* read from
    the reading end. A player who let a claim lapse is nothing to the match
    again, and if the seat is still free her offer is live again: that is the
    correct answer rather than a lenient one, since the seat genuinely went back
    on the market and somebody has to be told.
    """

    return (
        match.seat_of(player_id) is not None
        or match.departure_of(player_id) is not None
        or match.live_claim_of(player_id, at=at) is not None
    )


def _place(club: Club, match: Match) -> Place:
    """Where: the club, its clock face, and whether there is a roof.

    The cover is read **live** off the category rather than copied onto the
    match, exactly as the strip reads it (ADR-0090): the price was agreed when
    the match was posted, and the roof is a fact about the evening she would be
    walking into.
    """

    return Place(
        club_id=club.id,
        club_name=club.name.value,
        zone=club.timezone,
        cover=club.category(match.category_id).cover,
        # No distance, and it is the modelled answer rather than a gap: a
        # distance is measured from the glossary's Distance anchor, the anchor is
        # optional, and precision follows it (ADR-0063).
        distance_km=None,
    )


def _court_total(match: Match) -> Grosze:
    """What the whole court cost, which is the share times the seats."""

    return grosze(int(match.share) * len(match.seats))
