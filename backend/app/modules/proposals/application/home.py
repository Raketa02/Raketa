"""**Home**: the reader's games from the moment they fill, each with its status
and money line, and how many of them need the reader (#542; the mechanics §3,
§14.1; the screens A8).

**A read, recorded nowhere, and the clock is read once.** Every status, money
line and *needs you* here is folded against one instant (``domain/home.py``), and
that instant travels back as ``read_at`` — so a card's cut-off and its status
cannot be read against two clocks: the share is held until the club's cut-off
and taken at it — *free to leave until* then, *Paid* from it on (#637, Q113).

**Set reads, never one per card**: the reader's bookings, then each game's
result in one question about the set, the clubs' names in one, and the people on
every card in one per sport — a person's Level is per sport, and a card draws it.

**Home sends what Home draws, and reads no more** (#613): the bookings are read
only from the earliest hour a game can still ask anything of its players
(``on_home_since``), and of those a card is sent only while it is live, ended
less than a day after its hour, or needs the reader (``on_home``) — so how many
are folded no longer grows with every game played. **A score put on the table
again reaches further back**: a correction re-dates its side's score and may be
made again while the other side has not answered, so an older game is still
read when the Games context says a score may still wait on it
(``GameResults.waiting_among``) — asked about ids alone, and folded only for
the few it names. Every card that needs the reader is sent, so the badge counts
what it counted before.

**The games that need the reader** are the cards that need them and, beside
them, every payment they have to confirm — a game still filling, which is not on
Home, but which the mechanics count among the games that need you (§3): its seat
is the reader's only until somebody else takes it.

**A game waiting for one payment is here too** (#625; Q111): *Waiting for one
payment* on all four's Home while a refused share's time to pay runs. It has
**no booking** until it books — no court is held — so it is read off its
proposal (``without_a_booking``) for everybody In, the payer among them:
waiting, then *Seat open* once the time ran out or somebody else's seat opened
— a full game gone back to filling (Q106) — or *called off*. Nothing else is
on Home before it is booked: no club confirms a game (``docs/adr/0196`` §1).

**A friends game's invitations are a row of their own** (#751;
``docs/adr/0202`` §5): *FRIENDS GAME · n*, at the very top of Home — every
friends game whose invitation still waits on the reader, the soonest to end
first, each its booking as its sender booked it. Not counted in
``needing_you``. Once the reader accepts, the game is among their games; the
sender's is there from the send.

**A friend's ask for a level is a row of its own** (#764; ``docs/adr/0202``
§4's 2026-11-07 amendment): *ASKED FOR A LEVEL · n*, between the friend
requests and the reader's games — one card per sport, Friends' read through
``LevelAsksOnHome``. Not counted in ``needing_you``.

**The trophy is Rankings'** (#768; ``docs/adr/0203`` §5): the sport of the
reader's latest result, in any sport, and their General place there, through
``RankingOnHome`` — ``None`` with no result anywhere.

**What's new in Needs your answer rides on this read** (#815;
``docs/adr/0205`` §3): the four kinds waiting there — the payments to confirm
(gathered for ``needing_you`` already), the friends game invitations, the
friend requests and each level asker — are this read's own, so their arrivals
are compared here with the reader's last visit's watermark, and no other
context is asked anything new. The read's own watermark is the newest arrival
among the four, which the phone sends back when it closes the sheet. **The
payments to confirm are served here too**, as *To confirm* rows identical to
``GET /players/me/payments-to-confirm``'s, so a sheet drawn off this one read
shows exactly what its watermark covers.

**Classic play's games are not here**: a game a challenge's line-up opened has
no booking. Its card is ``GET /games``'.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.proposals.application.booked_people import people_on
from app.modules.proposals.application.friends import with_the_readers_friends
from app.modules.proposals.application.payments_to_confirm import (
    PaymentToConfirm,
    owed_by,
    to_confirm,
)
from app.modules.proposals.domain.home import (
    BookedGame,
    BookedState,
    on_home,
    on_home_since,
    state_of,
    without_a_booking,
)
from app.modules.proposals.domain.needs_your_answer import WhatIsNew, what_is_new
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    HoldingTimes,
    ClubNames,
    DeckPeople,
    DeckPerson,
    FriendRequestsOnHome,
    FriendsGameBookings,
    HomeFriendRequest,
    HomeLevelAsk,
    HomeRanking,
    LevelAsksOnHome,
    NeedsYourAnswerVisits,
    RankingOnHome,
    ReaderRelations,
    GameResults,
    PlayerBookings,
    ProposalDirectory,
    ProposalRepository,
)


@final
@dataclass(frozen=True, slots=True)
class HomeGame:
    """One card on Home."""

    game: BookedGame
    state: BookedState
    #: ``None`` for a club that no longer exists, with the card kept.
    club_name: str | None


@final
@dataclass(frozen=True, slots=True)
class HomeInvitation:
    """One card in *FRIENDS GAME*: a friends game the reader is invited to."""

    game: BookedGame
    club_name: str | None
    #: When the reader's seat was invited into: its arrival in *Needs your
    #: answer* (#815).
    invited_at: Instant


@final
@dataclass(frozen=True, slots=True)
class Home:
    #: The instant every status and money line was folded against.
    read_at: Instant
    #: Soonest game first.
    games: tuple[HomeGame, ...]
    #: The cards that need the reader, and their payments to confirm.
    needing_you: int
    #: Everybody on every card, each in the sport of the card they are on —
    #: the reader's friends marked.
    people: Mapping[tuple[Sport, UUID], DeckPerson]
    #: *FRIEND REQUESTS* — the requests waiting on the reader, newest first
    #: (``docs/adr/0202`` §1). Empty, and the row gone, once all are answered.
    friend_requests: tuple[HomeFriendRequest, ...] = ()
    #: *FRIENDS GAME* — the friends games whose invitation waits on the
    #: reader, the soonest to end first (#751). Their people are in ``people``.
    friends_games: tuple[HomeInvitation, ...] = ()
    #: *ASKED FOR A LEVEL* — one card per sport, the sport with the newest ask
    #: first (#764). Empty, and the row gone, once none waits.
    level_asks: tuple[HomeLevelAsk, ...] = ()
    #: The trophy left of the bell (#768): the sport of the reader's latest
    #: result and their General place in it. ``None`` with no result anywhere.
    ranking: HomeRanking | None = None
    #: *TO CONFIRM* (#815; ``docs/adr/0205`` §3): every payment the reader has
    #: to confirm, soonest game first — the rows ``needing_you`` counts and the
    #: watermark covers, so the sheet can draw all four sections off one read.
    payments_to_confirm: tuple[PaymentToConfirm, ...] = ()
    #: The envelope's badge (#815): what waits in *Needs your answer* that
    #: arrived since the reader last closed it, and this read's watermark.
    needs_your_answer: WhatIsNew = WhatIsNew(count=0, watermark=None)


@final
class ReadHome:
    def __init__(
        self,
        *,
        bookings: PlayerBookings,
        results: GameResults,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        people: DeckPeople,
        clubs: ClubNames,
        games: BookedGameChanges,
        holding_times: HoldingTimes,
        relations: ReaderRelations,
        friend_requests: FriendRequestsOnHome,
        level_asks: LevelAsksOnHome,
        ranking: RankingOnHome,
        friends_games: FriendsGameBookings,
        visits: NeedsYourAnswerVisits,
        clock: Clock,
    ) -> None:
        self._visits = visits
        self._ranking = ranking
        self._level_asks = level_asks
        self._friends_games = friends_games
        self._relations = relations
        self._friend_requests = friend_requests
        self._bookings = bookings
        self._results = results
        self._proposals = proposals
        self._directory = directory
        self._people = people
        self._clubs = clubs
        self._games = games
        self._holding_times = holding_times
        self._clock = clock

    async def execute(self, reader: UUID) -> Home:
        now = instant(self._clock.now())
        since = on_home_since(now)
        booked = [
            *await self._older_still_waiting(since, reader=reader, now=now),
            *await self._bookings.of_player(reader, since=since),
        ]
        booked = sorted(
            [*booked, *await self._without_a_booking(booked, reader, since, now)],
            key=lambda game: (game.start, game.booking_id),
        )
        # A game that waited for a payment and never booked has none.
        results = await self._results.of(
            [game.game_id for game in booked if game.game_id is not None],
            reader=reader,
            now=now,
        )
        owed = await owed_by(
            reader,
            proposals=self._proposals,
            directory=self._directory,
            bookings=self._bookings,
            games=self._games,
            now=now,
        )
        # One question for every club Home names: its games' and its *To
        # confirm* rows'.
        names = await self._clubs.names_of(
            {game.club_id for game in booked} | {one.proposal.club_id for one in owed}
        )
        # The reader's own shares only checked at the fill (#639).
        held_from = await self._holding_times.of(
            reader, [game.booking_id for game in booked]
        )
        cards = [
            card
            for card in (
                HomeGame(
                    game=game,
                    state=state_of(
                        game,
                        None if game.game_id is None else results.get(game.game_id),
                        now=now,
                        held_from=held_from.get(game.booking_id),
                    ),
                    club_name=names.get(game.club_id),
                )
                for game in booked
            )
            if on_home(card.game, card.state, now=now)
        ]
        invitations = await self._invitations(reader, now=now)
        friend_requests = await self._friend_requests.of(reader)
        level_asks = await self._level_asks.of(reader)
        return Home(
            read_at=now,
            games=tuple(cards),
            needing_you=sum(card.state.needs_you for card in cards) + len(owed),
            people=await with_the_readers_friends(
                await people_on(
                    [
                        *(card.game for card in cards),
                        *(invited.game for invited in invitations),
                    ],
                    self._people,
                ),
                reader=reader,
                relations=self._relations,
            ),
            friend_requests=friend_requests,
            friends_games=invitations,
            level_asks=level_asks,
            ranking=await self._ranking.of(reader),
            payments_to_confirm=to_confirm(owed, names=names),
            needs_your_answer=await self._what_is_new(
                reader,
                [
                    *(one.refused_at for one in owed),
                    *(invited.invited_at for invited in invitations),
                    *(request.asked_at for request in friend_requests),
                    # Each asker by their own ask: one card per sport gains
                    # askers.
                    *(asker.asked_at for ask in level_asks for asker in ask.askers),
                ],
            ),
        )

    async def _what_is_new(self, reader: UUID, arrivals: list[Instant]) -> WhatIsNew:
        """The envelope's badge over these arrivals — the reader's last visit
        read only when something waits, since with nothing waiting nothing is
        new whatever they saw."""

        if not arrivals:
            return what_is_new((), seen_through=None)
        visit = await self._visits.load(reader)
        return what_is_new(arrivals, seen_through=visit.watermark)

    async def _invitations(
        self, reader: UUID, *, now: Instant
    ) -> tuple[HomeInvitation, ...]:
        """The friends games whose invitation still waits on the reader."""

        invited = [
            (game, seat)
            for booking_id in await self._friends_games.invitations_of(reader, now=now)
            if (game := await self._bookings.find(booking_id)) is not None
            and (seat := game.invited_now(reader, now=now)) is not None
        ]
        names = await self._clubs.names_of({game.club_id for game, _ in invited})
        return tuple(
            HomeInvitation(
                game=game,
                club_name=names.get(game.club_id),
                invited_at=seat.invited_at,
            )
            for game, seat in invited
        )

    async def _without_a_booking(
        self,
        booked: list[BookedGame],
        reader: UUID,
        since: Instant,
        now: Instant,
    ) -> list[BookedGame]:
        """The reader's games that waited for a payment and have no booking
        (#625)."""

        found: list[BookedGame] = []
        seen = {game.booking_id for game in booked}
        for proposal_id in await self._directory.payment_awaited_of(
            reader, since=since
        ):
            proposal = await self._proposals.load(proposal_id)
            if proposal is None or proposal_id in seen:
                continue
            game = without_a_booking(proposal, now=now)
            if game.has_a_seat_for(reader):
                found.append(game)
        return found

    async def _older_still_waiting(
        self, since: Instant, *, reader: UUID, now: Instant
    ) -> list[BookedGame]:
        """The reader's games whose hour started before ``since`` that a score
        may still wait on — the only older ones that can still ask anything of
        anybody — soonest first, and by id among games at one hour, as every
        one of them starts before the games read from ``since``."""

        older = await self._bookings.games_before(reader, before=since)
        if not older:
            return []
        waiting = await self._results.waiting_among(older, now=now)
        found: list[BookedGame] = []
        for game_id in waiting:
            game = await self._bookings.find(older[game_id])
            if game is not None:
                found.append(game)
        return sorted(found, key=lambda game: (game.start, game.booking_id))


async def the_game(
    booking_id: UUID,
    *,
    bookings: PlayerBookings,
    proposals: ProposalRepository,
    now: Instant,
) -> BookedGame | None:
    """The game under this id as its players read it at ``now``: its booking —
    or, **a game that waited for a payment**, its proposal, since it has no
    booking until it books (#625). ``None`` for neither."""

    found = await bookings.find(booking_id)
    if found is not None:
        return found
    proposal = await proposals.load(booking_id)
    if proposal is None or proposal.payment_awaited_at is None:
        return None
    return without_a_booking(proposal, now=now)
