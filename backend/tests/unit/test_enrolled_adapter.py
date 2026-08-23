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

from app.kernel import Cover, Instant, SeatShare, Sport, grosze, hours, instant
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
    club: Club, *, players: Sequence[UUID], score: Score | None = None
) -> Match:
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=START,
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

    async def for_player(self, player_id: UUID) -> list[Match]:
        self.asks += 1
        return self._matches


class Clubs:
    """Answers a batch; refuses the one-at-a-time read and the whole table."""

    def __init__(self, *clubs: Club) -> None:
        self._clubs = {club.id: club for club in clubs}
        self.batches: list[tuple[UUID, ...]] = []

    async def find_by_ids(self, club_ids: Sequence[UUID]) -> list[Club]:
        self.batches.append(tuple(club_ids))
        return [self._clubs[one] for one in club_ids if one in self._clubs]

    async def get(self, club_id: UUID):  # pragma: no cover
        raise AssertionError("the strip reads clubs in one batch, never one by one")

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


def an_adapter(
    *,
    matches: Matches,
    clubs: Clubs,
    reservations: Reservations | None = None,
    users: Users | None = None,
    ledgers: Ledgers | None = None,
) -> EnrolledFromMatches:
    return EnrolledFromMatches(
        matches=matches,
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
