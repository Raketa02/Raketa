"""``EnrolledMatches`` over five contexts, and the four claims no screen can show.

Everything the enrolled strip *renders* is `tests/unit/test_compose_enrolled.py`'s
subject. What is here is the half a composed screen cannot see:

- the ledger is loaded **once** for the whole strip, not once per card;
- nicknames are read **only** for matches that carry a score, and in one batch;
- the fifteen-minute rule is **not** applied here — the adapter answers *which
  court is reserved* and the composer decides whether it may be printed;
- a player with no matches pays for no club read, no ledger replay and no
  reservation loop at all.

The first three are claims about *cost* and the fourth is a claim about *rules*,
and all four are satisfied by an answer that looks identical on screen. So the
fakes below refuse the read that was not supposed to happen, and count the ones
that were — the shape `test_now_adapters.py` established.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID, uuid4

from decimal import Decimal

from app.kernel import (
    Cover,
    Instant,
    Outcome,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
    shifted,
)
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
    zone_named,
)
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.score import Score, SetScore
from app.modules.money.domain.ledger import Ledger
from app.modules.now.infrastructure.enrolled_matches import EnrolledFromMatches

AT: Instant = instant(datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc))
START: Instant = instant(datetime(2026, 8, 28, 18, 30, tzinfo=timezone.utc))
SHARE = SeatShare(grosze(3800))


# --- the world ------------------------------------------------------------


def a_club(*, courts: int = 2) -> Club:
    club = Club.found(
        club_id=uuid4(),
        name=ClubName("Zabłocie Sport"),
        address=StreetAddress(
            line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
        ),
        point=GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500")),
        timezone=zone_named("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PayoutDestination(
            account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
        ),
        at=AT,
    )
    category = club.add_category(
        category_id=uuid4(),
        name=CategoryName("Padel · indoor"),
        sport=Sport.PADEL,
        cover=Cover.INDOOR,
        rate=grosze(15200),
    )
    for index in range(courts):
        club.add_court(
            court_id=uuid4(),
            category_id=category.id,
            label=CourtLabel(f"Court {index + 1}"),
            at=AT,
        )
    return club


def a_match(
    club: Club,
    *,
    players: Sequence[UUID],
    score: Score | None = None,
    start: Instant = START,
) -> Match:
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=start,
        duration=hours(1),
        share=SHARE,
        policy=ClubPolicy().hold_policy(),
        at=AT,
    )
    for player in players:
        match.take_seat(player, at=AT)
        match.pay_seat(player, at=AT)
    match.score = score
    match.pull_events()
    return match


class Reservation:
    """Just enough of one: which court, and whether it has gone back on sale."""

    def __init__(self, court_id: UUID, released_at: Instant | None = None) -> None:
        self.court_id = court_id
        self.released_at = released_at


# --- the fakes ------------------------------------------------------------


class Matches:
    def __init__(self, *matches: Match) -> None:
        self._matches = list(matches)
        self.asks = 0
        self.queue_asks = 0
        #: Which of these matches the viewer holds a standby place for. Empty
        #: unless a case says otherwise, which is the ordinary player.
        self.queued: set[UUID] = set()
        self.gets: list[UUID] = []

    async def for_player(self, player_id: UUID) -> list[Match]:
        """A seat that names her, or a departure that does — like the real one.

        Filtered rather than answering everything, because the strip's newest
        claim is that a match she is *only queued for* reaches it: a stub that
        answered every match would make that claim pass on the wrong read.
        """

        self.asks += 1
        return [
            match
            for match in self._matches
            if match.seat_of(player_id) is not None
            or match.departure_of(player_id) is not None
        ]

    async def queued_by(self, player_id: UUID) -> list[Match]:
        self.queue_asks += 1
        return [
            match for match in self._matches if match.id in self.queued
        ]

    async def get(self, match_id: UUID) -> Match | None:
        self.gets.append(match_id)
        return next((match for match in self._matches if match.id == match_id), None)


class Clubs:
    """Answers a batch; refuses the one-at-a-time read and the whole table."""

    def __init__(self, *clubs: Club) -> None:
        self._clubs = {club.id: club for club in clubs}
        self.batches: list[tuple[UUID, ...]] = []
        self.gets: list[UUID] = []

    async def find_by_ids(self, club_ids: Sequence[UUID]) -> list[Club]:
        self.batches.append(tuple(club_ids))
        return [self._clubs[one] for one in club_ids if one in self._clubs]

    async def get(self, club_id: UUID):
        """The **one-match** read, and the strip cases assert it never fires.

        A batch of one to answer a question about one match would be the same
        query wearing a loop, so `one()` asks for the club it needs — and every
        case below that composes a *strip* asserts this list stayed empty.
        """

        self.gets.append(club_id)
        return self._clubs.get(club_id)

    async def find_all(self):  # pragma: no cover
        raise AssertionError("the strip never walks every club on the platform")


class Reservations:
    def __init__(self, **held: Reservation) -> None:
        self._held = held
        self.asks: list[UUID] = []

    async def for_match(self, match_id: UUID) -> Reservation | None:
        self.asks.append(match_id)
        return self._held.get(str(match_id))


class Users:
    """Answers a batch, and counts them: a card names a person on two situations."""

    def __init__(self, **nicknames: str) -> None:
        self._nicknames = nicknames
        self.batches: list[tuple[UUID, ...]] = []

    async def find_by_ids(self, user_ids: Sequence[UUID]) -> list:
        self.batches.append(tuple(user_ids))
        return [
            _User(one, self._nicknames[str(one)])
            for one in user_ids
            if str(one) in self._nicknames
        ]

    async def get_by_id(self, user_id: UUID):  # pragma: no cover
        raise AssertionError("a scoreline's names are read in one batch")


class _User:
    def __init__(self, user_id: UUID, nickname: str) -> None:
        self.id = user_id
        self.nickname = _Nickname(nickname)


class _Nickname:
    def __init__(self, value: str) -> None:
        self.value = value


class Ledgers:
    """One stream per player, so one load answers every seat on the strip."""

    def __init__(self) -> None:
        self.loads: list[UUID] = []

    async def load(self, player_id: UUID) -> Ledger:
        self.loads.append(player_id)
        return Ledger.for_player(player_id)


class Standby:
    """The queue, as the set of match ids one player asked about."""

    def __init__(self, *match_ids: UUID) -> None:
        self._held = frozenset(match_ids)
        self.asks: list[UUID] = []

    async def held_by(self, player_id: UUID) -> frozenset[UUID]:
        self.asks.append(player_id)
        return self._held

    async def join(self, **_: object) -> None:  # pragma: no cover
        raise AssertionError("the strip never puts anybody on a queue")

    async def leave(self, **_: object) -> None:  # pragma: no cover
        raise AssertionError("the strip never takes anybody off a queue")


class Claims:
    """The cross-match claim read: one live claim per player, or nothing.

    A match id and never a match, because that is what `SeatClaims` answers —
    the strip loads it back through the repository it already holds, which is
    what the `gets` counter below is watching.
    """

    def __init__(self, match_id: UUID | None = None) -> None:
        self._match_id = match_id
        self.asks: list[tuple[UUID, Instant]] = []

    async def live_for(self, player_id: UUID, *, at: Instant) -> UUID | None:
        self.asks.append((player_id, at))
        return self._match_id


def an_adapter(
    *,
    matches: Matches,
    clubs: Clubs,
    reservations: Reservations | None = None,
    users: Users | None = None,
    ledgers: Ledgers | None = None,
    standby: Standby | None = None,
    claims: Claims | None = None,
) -> EnrolledFromMatches:
    return EnrolledFromMatches(
        matches=matches,
        standby=standby or Standby(),
        claims=claims or Claims(),
        clubs=clubs,
        reservations=reservations or Reservations(),
        users=users or Users(),
        ledgers=ledgers or Ledgers(),
    )


# --- the four claims ------------------------------------------------------


async def test_the_ledger_is_loaded_once_for_the_whole_strip() -> None:
    """A ledger is one stream per player, so every seat's fold comes off one.

    Loading per card would replay a player's whole money history once per match
    on her home screen, which is a cost no card could show.
    """

    player = uuid4()
    club = a_club()
    ledgers = Ledgers()

    rows = await an_adapter(
        matches=Matches(
            a_match(club, players=[player]),
            a_match(club, players=[player]),
            a_match(club, players=[player]),
        ),
        clubs=Clubs(club),
        ledgers=ledgers,
    ).for_player(player_id=player, now=AT)

    assert len(rows) == 3
    assert ledgers.loads == [player]


async def test_the_clubs_are_read_in_one_batch_and_each_one_once() -> None:
    player = uuid4()
    club = a_club()

    await an_adapter(
        matches=Matches(
            a_match(club, players=[player]), a_match(club, players=[player])
        ),
        clubs=(clubs := Clubs(club)),
    ).for_player(player_id=player, now=AT)

    assert clubs.batches == [(club.id,)]
    # And never one at a time. The single read is `one()`'s, and it exists so
    # that a question about one match does not pay a batch to answer.
    assert clubs.gets == []


async def test_no_nickname_is_read_for_a_strip_with_no_score_on_it() -> None:
    """A card names a person on exactly two situations out of thirty-six."""

    player = uuid4()
    club = a_club()

    await an_adapter(
        matches=Matches(a_match(club, players=[player])),
        clubs=Clubs(club),
        users=(users := Users()),
    ).for_player(player_id=player, now=AT)

    assert users.batches == []


async def test_a_scored_match_reads_its_names_once_and_puts_them_on_two_sides() -> None:
    ala, kuba, zofia, piotr = uuid4(), uuid4(), uuid4(), uuid4()
    club = a_club()
    users = Users(
        **{
            str(ala): "ala",
            str(kuba): "kuba",
            str(zofia): "zofia",
            str(piotr): "piotr",
        }
    )

    rows = await an_adapter(
        matches=Matches(
            a_match(
                club,
                players=[ala, kuba, zofia, piotr],
                score=Score(sets=(SetScore(side_a=6, side_b=4),)),
            )
        ),
        clubs=Clubs(club),
        users=users,
    ).for_player(player_id=zofia, now=AT)

    assert len(users.batches) == 1
    score = rows[0].score
    assert score is not None
    assert score.sides == (("ala", "kuba"), ("zofia", "piotr"))
    assert score.sets == ((6, 4),)
    # Seats 0-1 are side A and 2-3 side B, so the third seat is on side B.
    assert score.viewer_side == 1


async def test_the_adapter_names_the_court_whatever_the_clock_says() -> None:
    """The fifteen-minute rule is the **composer's**, and it is asked once.

    An adapter that applied it here would be the second place that rule lives,
    and the two would disagree the day one of them moved — with the symptom
    being a court named on Monday for a Thursday match.
    """

    player = uuid4()
    club = a_club()
    match = a_match(club, players=[player])
    court = club.live_courts[0]

    rows = await an_adapter(
        matches=Matches(match),
        clubs=Clubs(club),
        reservations=Reservations(**{str(match.id): Reservation(court.id)}),
    ).for_player(player_id=player, now=AT)

    # Six days before the start, and the fact is still answered.
    assert rows[0].court == "Court 1"


async def test_a_released_reservation_names_no_court() -> None:
    """The court went back on sale, so there is no court to name."""

    player = uuid4()
    club = a_club()
    match = a_match(club, players=[player])

    rows = await an_adapter(
        matches=Matches(match),
        clubs=Clubs(club),
        reservations=Reservations(
            **{str(match.id): Reservation(club.live_courts[0].id, released_at=AT)}
        ),
    ).for_player(player_id=player, now=AT)

    assert rows[0].court is None


async def test_a_player_with_no_matches_pays_for_nothing_downstream() -> None:
    """The ordinary screen, and the one this must not make expensive."""

    clubs, users, ledgers = Clubs(), Users(), Ledgers()
    reservations = Reservations()

    rows = await an_adapter(
        matches=Matches(),
        clubs=clubs,
        reservations=reservations,
        users=users,
        ledgers=ledgers,
    ).for_player(player_id=uuid4(), now=AT)

    assert rows == ()
    assert (clubs.batches, users.batches, ledgers.loads, reservations.asks) == (
        [],
        [],
        [],
        [],
    )


# --- what the row says about her ------------------------------------------


async def test_the_row_carries_the_share_and_the_whole_court_beside_it() -> None:
    player = uuid4()
    club = a_club()

    rows = await an_adapter(
        matches=Matches(a_match(club, players=[player])), clubs=Clubs(club)
    ).for_player(player_id=player, now=AT)

    assert int(rows[0].share.amount) == 3800
    assert int(rows[0].court_total.amount) == 3800 * 4


async def test_the_roof_is_read_live_off_the_category_the_match_names() -> None:
    """The price was agreed at posting; the roof is about the evening she walks into."""

    player = uuid4()
    club = a_club()

    rows = await an_adapter(
        matches=Matches(a_match(club, players=[player])), clubs=Clubs(club)
    ).for_player(player_id=player, now=AT)

    assert rows[0].where.cover is Cover.INDOOR
    assert rows[0].where.club_name == "Zabłocie Sport"


async def test_a_match_at_a_club_this_read_cannot_see_is_dropped_not_broken() -> None:
    """A card that has to name a venue it does not know is worse than no card."""

    player = uuid4()
    club = a_club()

    rows = await an_adapter(
        matches=Matches(a_match(club, players=[player])), clubs=Clubs()
    ).for_player(player_id=player, now=AT)

    assert rows == ()


# --- one match, for an action off Now ---------------------------------------
#
# `one()` is the read behind the departure route and behind the one card an
# action hands back (ADR-0074, ADR-0086). Its membership is **wider** than the
# strip's by exactly one case, and its cost claim is the mirror of the strip's:
# one club read rather than a batch, and nothing at all for a stranger.


async def test_one_match_answers_a_row_for_a_seat_she_holds() -> None:
    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])
    matches, clubs = Matches(match), Clubs(club)

    row = await an_adapter(matches=matches, clubs=clubs).one(
        player_id=alice, match_id=match.id, now=AT
    )

    assert row is not None
    assert row.match_id == match.id
    assert row.holds_seat is True
    # One match, one club: the batch read is the strip's and never fires here.
    assert clubs.gets == [club.id]
    assert clubs.batches == []


async def test_one_match_answers_a_row_for_a_leaver() -> None:
    """*"A 404 tells a leaver their match never existed"* (ADR-0074).

    She holds no seat, so the membership question is answered by her departure
    — the second of the two sources `for_player` already reads.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])
    match.depart(alice, quote=Outcome.REVERSED, at=AT)

    row = await an_adapter(matches=Matches(match), clubs=Clubs(club)).one(
        player_id=alice, match_id=match.id, now=AT
    )

    assert row is not None
    assert row.holds_seat is False
    assert row.departure is not None


async def test_one_match_answers_a_row_for_a_live_seat_claim() -> None:
    """The case that makes this method's membership wider than the strip's.

    A claim holds no seat yet (ADR-0081) and leaves no departure, so
    `for_player` cannot see her — and her departure route must still open and
    answer *no*.
    """

    club = a_club()
    alice, bob = uuid4(), uuid4()
    match = a_match(club, players=[bob])
    match.open_claim(alice, at=AT)

    row = await an_adapter(matches=Matches(match), clubs=Clubs(club)).one(
        player_id=alice, match_id=match.id, now=AT
    )

    assert row is not None
    assert row.holds_seat is False
    assert row.departure is None
    assert row.claim_expires_at is not None


async def test_a_stranger_gets_nothing_and_pays_for_nothing() -> None:
    """Authorisation, and the read stops the moment it is answered."""

    club = a_club()
    match = a_match(club, players=[uuid4()])
    clubs, ledgers = Clubs(club), Ledgers()

    row = await an_adapter(matches=Matches(match), clubs=clubs, ledgers=ledgers).one(
        player_id=uuid4(), match_id=match.id, now=AT
    )

    assert row is None
    assert clubs.gets == []
    assert ledgers.loads == []


async def test_a_match_that_does_not_exist_answers_nothing() -> None:
    row = await an_adapter(matches=Matches(), clubs=Clubs()).one(
        player_id=uuid4(), match_id=uuid4(), now=AT
    )

    assert row is None


async def test_a_match_at_a_club_this_read_cannot_see_answers_nothing() -> None:
    """The same silence the strip keeps, costing a 404 rather than a missing row.

    A card that would have to name a venue it does not know is worse than no
    card, and on a one-match route *no card* is *no route*.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])

    row = await an_adapter(matches=Matches(match), clubs=Clubs()).one(
        player_id=alice, match_id=match.id, now=AT
    )

    assert row is None


async def test_no_nickname_is_read_for_a_match_with_no_score_on_it() -> None:
    """A card names a person on exactly two situations, and this is neither."""

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])
    users = Users()

    await an_adapter(matches=Matches(match), clubs=Clubs(club), users=users).one(
        player_id=alice, match_id=match.id, now=AT
    )

    assert users.batches == []


# --- the queue: the fourth membership --------------------------------------


async def test_a_queued_match_reaches_the_strip_and_says_so() -> None:
    """A standby place is a fourth membership, and the only one conferring none.

    It is on the strip because `waitlisted` is a card that names an act and this
    is the only region on Now that could hold one — the offers region is seats
    offered to her, and the ranked shelves exclude a match she is queued for by
    rule.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[uuid4()])
    matches = Matches(match)
    matches.queued = {match.id}

    rows = await an_adapter(matches=matches, clubs=Clubs(club)).for_player(
        player_id=alice, now=AT
    )

    assert [row.match_id for row in rows] == [match.id]
    assert rows[0].on_standby is True
    assert rows[0].holds_seat is False


async def test_a_match_she_is_seated_in_is_not_reported_as_queued() -> None:
    """The flag is the queue's answer and never a default."""

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])

    rows = await an_adapter(matches=Matches(match), clubs=Clubs(club)).for_player(
        player_id=alice, now=AT
    )

    assert rows[0].on_standby is False


async def test_a_match_she_both_holds_and_queued_for_appears_once() -> None:
    """The two reads overlap and the strip is a list of matches, not of rows.

    Nothing in the store refuses the pair — a player who queued for a match she
    later joined is an ordinary history — so the merge deduplicates rather than
    drawing her two cards for one match.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])
    matches = Matches(match)
    matches.queued = {match.id}

    rows = await an_adapter(matches=matches, clubs=Clubs(club)).for_player(
        player_id=alice, now=AT
    )

    assert [row.match_id for row in rows] == [match.id]
    assert rows[0].holds_seat is True
    assert rows[0].on_standby is True


async def test_one_match_answers_a_row_for_a_queued_viewer() -> None:
    """She is something to it, so the route opens rather than 404ing.

    The write behind it needs the card that is true *after* the place is gone,
    and a 404 here would make the one act with a surface unable to describe its
    own result.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[uuid4()])

    row = await an_adapter(
        matches=Matches(match), clubs=Clubs(club), standby=Standby(match.id)
    ).one(player_id=alice, match_id=match.id, now=AT)

    assert row is not None
    assert row.on_standby is True


async def test_the_queue_is_asked_about_one_match_and_never_walked() -> None:
    """`held_by` answers a set of ids where `queued_by` assembles whole matches.

    Reading whole matches — every seat, every vacancy, every claim — to compute
    a boolean is the same query wearing a loop, so the single-match read asks
    the cheaper port and the strip pays for the matches because it draws them.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])
    matches = Matches(match)
    standby = Standby()

    await an_adapter(matches=matches, clubs=Clubs(club), standby=standby).one(
        player_id=alice, match_id=match.id, now=AT
    )

    assert standby.asks == [alice]
    assert matches.queue_asks == 0


async def test_the_two_memberships_are_merged_in_one_chronological_order() -> None:
    """The strip is chronological, and it merges two lists to be so.

    Both reads answer soonest-first, so a merge that concatenated them would put
    every queued match after every enrolled one however the clock reads — and a
    chronological region whose order is fixed at composition is the whole point
    of the region (ADR-0073).
    """

    club = a_club()
    alice = uuid4()
    later = a_match(club, players=[alice], start=shifted(START, hours(48)))
    sooner = a_match(club, players=[uuid4()], start=START)
    matches = Matches(later, sooner)
    matches.queued = {sooner.id}

    rows = await an_adapter(matches=matches, clubs=Clubs(club)).for_player(
        player_id=alice, now=AT
    )

    assert [row.match_id for row in rows] == [sooner.id, later.id]


async def test_a_seat_she_is_buying_reaches_the_strip() -> None:
    """The fifth membership, and it arrived with the act that opens one.

    An offer card leaves the offers region the instant the match becomes hers
    (`Raketa02/Raketa#83`), so without this the match she has five minutes to pay
    for would be on no region of her home screen at all.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[uuid4()])
    match.open_claim(alice, at=AT)
    matches = Matches(match)

    rows = await an_adapter(
        matches=matches, clubs=Clubs(club), claims=Claims(match.id)
    ).for_player(player_id=alice, now=AT)

    assert [row.match_id for row in rows] == [match.id]
    assert rows[0].holds_seat is False
    assert rows[0].claim_expires_at is not None


async def test_the_claim_read_is_one_lookup_and_one_get() -> None:
    """One live claim per player across the platform, so it is not a list.

    The read widens the strip by one match rather than by a set, which is what
    lets it be a lookup and a `get` instead of a fourth query to merge.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[uuid4()])
    match.open_claim(alice, at=AT)
    matches = Matches(match)
    claims = Claims(match.id)

    await an_adapter(matches=matches, clubs=Clubs(club), claims=claims).for_player(
        player_id=alice, now=AT
    )

    assert claims.asks == [(alice, AT)]
    assert matches.gets == [match.id]


async def test_a_player_buying_nothing_pays_for_no_match_read() -> None:
    club = a_club()
    matches = Matches(a_match(club, players=[uuid4()]))
    claims = Claims(None)

    rows = await an_adapter(
        matches=matches, clubs=Clubs(club), claims=claims
    ).for_player(player_id=uuid4(), now=AT)

    assert rows == ()
    assert matches.gets == []


async def test_a_claim_on_a_match_she_already_holds_a_seat_in_appears_once() -> None:
    """`open_claim` refuses a second seat, so this can only ever *add* a match.

    The merge keeps the copy the first read produced either way, which is why the
    claim read is passed last: that list is the one carrying her seat and her
    departure.
    """

    club = a_club()
    alice = uuid4()
    match = a_match(club, players=[alice])
    matches = Matches(match)

    rows = await an_adapter(
        matches=matches, clubs=Clubs(club), claims=Claims(match.id)
    ).for_player(player_id=alice, now=AT)

    assert [row.match_id for row in rows] == [match.id]
    assert rows[0].holds_seat is True
