"""The two reads the cascade asks in the opposite direction to everything else.

Now composes *matches for a player*; the cascade composes *players for a match*,
and neither of the two stores it needs was ever asked that way round. What is
under test here is that the reach is right — that the rating streams answer
*who*, and that a club's history answers *who has been*.

`RatedPlayers` is driven against the **real** rating repository writing into the
in-memory event store, and that is the point: the lookup keys on
`RatingInitialised`'s field names as the codec writes them, so a stub answering
whatever a case set up would assert the query against itself. A rename there
returns nothing and reads as *nobody plays this sport* — which is the ordinary
answer for a quiet city and therefore the failure no behavioural test upstream
could see.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.kernel import Instant, Sport, minutes, shifted

from app.modules.now.infrastructure.pool_sources import (
    ClubRegularsFromMatches,
    RatedPlayersFromRatingStreams,
)
from app.engines.assessment import AssessmentResult, BandView
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    EventSourcedSkillRatingRepository,
)
from tests.unit.fake_event_store import InMemoryEventStore, RecordingPublisher, utc
from tests.unit.match_records import a_match, at

RATED_AT = utc(2026, 8, 14)


# ---------------------------------------------------------------------------
# Who holds a rating at a sport
# ---------------------------------------------------------------------------


async def _rate(repository, player_id: UUID, sport: Sport) -> None:
    """One player rated at one sport, **through the aggregate that owns the event**.

    Not by writing a row: the lookup below keys on `RatingInitialised`'s field
    names as the codec writes them, so a fixture that assembled the payload by
    hand would assert the query against its own spelling rather than against the
    one the product produces.
    """

    rating = SkillRating.initialise(
        rating_id=skill_rating_id(player_id, sport),
        player_id=player_id,
        sport=sport,
        result=AssessmentResult(
            mu=2.85,
            sigma=0.42,
            confidence=27,
            range_low=2.01,
            range_high=3.69,
            band=BandView(name="Intermediate", lower=2.5, upper=3.4),
            status="provisional",
            questions_asked=7,
            engine_version="racketskill-v3",
        ),
        source_assessment_id=uuid4(),
        occurred_at=RATED_AT,
    )
    await repository.save(rating)


def _repository(store: InMemoryEventStore) -> EventSourcedSkillRatingRepository:
    return EventSourcedSkillRatingRepository(
        event_store=store, events=RecordingPublisher()
    )


async def test_it_answers_everybody_rated_at_the_sport() -> None:
    store = InMemoryEventStore()
    repository = _repository(store)
    padel = [uuid4() for _ in range(3)]
    for who in padel:
        await _rate(repository, who, Sport.PADEL)

    found = await RatedPlayersFromRatingStreams(store).at(Sport.PADEL)

    assert set(found) == set(padel)


async def test_a_rating_at_another_sport_is_not_this_sports() -> None:
    """ADR-0061's whole reason for the rule: *"a badminton rating does not
    qualify anyone for squash cancellations."*"""

    store = InMemoryEventStore()
    repository = _repository(store)
    padel_player, squash_player = uuid4(), uuid4()
    await _rate(repository, padel_player, Sport.PADEL)
    await _rate(repository, squash_player, Sport.SQUASH)

    assert await RatedPlayersFromRatingStreams(store).at(Sport.PADEL) == (
        padel_player,
    )
    assert await RatedPlayersFromRatingStreams(store).at(Sport.SQUASH) == (
        squash_player,
    )


async def test_one_player_rated_at_two_sports_answers_for_both() -> None:
    """A stream per pair, so she is on two lists and neither knows about the other."""

    store = InMemoryEventStore()
    repository = _repository(store)
    who = uuid4()
    await _rate(repository, who, Sport.PADEL)
    await _rate(repository, who, Sport.TENNIS)

    assert await RatedPlayersFromRatingStreams(store).at(Sport.PADEL) == (who,)
    assert await RatedPlayersFromRatingStreams(store).at(Sport.TENNIS) == (who,)


async def test_a_sport_nobody_holds_a_rating_at_answers_nothing() -> None:
    """The ordinary answer for a quiet city, and never an error."""

    store = InMemoryEventStore()
    await _rate(_repository(store), uuid4(), Sport.PADEL)

    assert await RatedPlayersFromRatingStreams(store).at(Sport.BADMINTON) == ()


async def test_it_answers_the_player_and_never_the_stream() -> None:
    """The stream id is `uuid5(player, sport)`, and a caller needs the player.

    This is the whole reason the port answers ids rather than being folded into
    `Ratings`: the index read answers *which streams*, and only the payload
    answers *whose*. Handing the stream id back would be a set of identifiers
    nothing else in the product could use — and it would look exactly right.
    """

    store = InMemoryEventStore()
    who = uuid4()
    await _rate(_repository(store), who, Sport.PADEL)

    found = await RatedPlayersFromRatingStreams(store).at(Sport.PADEL)

    assert found == (who,)
    assert skill_rating_id(who, Sport.PADEL) not in found


async def test_the_population_is_one_query_and_not_one_per_player() -> None:
    """**The cost claim, asserted where the answer cannot show it.**

    The first draft read the matched stream ids and then loaded each stream to
    find out whose it was — an N+1 over a sport's whole population, producing
    the *identical* answer. So this counts the reads rather than checking the
    result: a rating stream's id is `uuid5(player, sport)` and cannot be
    reversed, which is exactly why the temptation to load each one back is
    there.
    """

    store = InMemoryEventStore()
    repository = _repository(store)
    for _ in range(8):
        await _rate(repository, uuid4(), Sport.PADEL)
    before = store.stream_loads

    found = await RatedPlayersFromRatingStreams(store).at(Sport.PADEL)

    assert len(found) == 8
    assert store.index_reads == 1
    assert store.stream_loads == before


# ---------------------------------------------------------------------------
# Who plays at a club
# ---------------------------------------------------------------------------


class StubMatches:
    """`MatchRepository` narrowed to the one read rung 5 makes."""

    def __init__(self, *matches: object) -> None:
        self._matches = matches
        self.asked: list[UUID] = []

    async def for_club(self, club_id: UUID) -> list[object]:
        self.asked.append(club_id)
        return list(self._matches)


class _Seat:
    def __init__(self, player_id: UUID | None) -> None:
        self.player_id = player_id


class _Match:
    def __init__(self, *, start: Instant, players: list[UUID | None]) -> None:
        self.start = start
        self.seats = [_Seat(who) for who in players]


async def test_a_past_match_at_the_club_puts_its_players_on_the_rung() -> None:
    played, other = uuid4(), uuid4()
    matches = StubMatches(
        _Match(start=at(-10_000), players=[played, other, None, None])
    )
    club = uuid4()

    assert await ClubRegularsFromMatches(matches).at(club_id=club, before=at(0)) == {
        played,
        other,
    }
    assert matches.asked == [club]


async def test_a_match_still_ahead_is_not_history_yet() -> None:
    """`before` is the freeing match's **start**, not its end.

    A match being played this evening is not history, and counting it would put
    the people on tonight's other court on the rung for a seat freeing in it.
    Asserted a minute either side, because a region is not a boundary.
    """

    ahead, behind = uuid4(), uuid4()
    matches = StubMatches(
        _Match(start=at(1), players=[ahead, None, None, None]),
        _Match(start=at(-1), players=[behind, None, None, None]),
    )

    assert await ClubRegularsFromMatches(matches).at(
        club_id=uuid4(), before=at(0)
    ) == {behind}


async def test_a_match_starting_exactly_now_is_not_history() -> None:
    who = uuid4()
    matches = StubMatches(_Match(start=at(0), players=[who, None, None, None]))

    assert (
        await ClubRegularsFromMatches(matches).at(club_id=uuid4(), before=at(0))
        == frozenset()
    )


async def test_an_empty_seat_names_nobody() -> None:
    """Every seat of a padel match is read, and three of four are usually empty."""

    who = uuid4()
    matches = StubMatches(_Match(start=at(-100), players=[who, None, None, None]))

    assert await ClubRegularsFromMatches(matches).at(
        club_id=uuid4(), before=at(0)
    ) == {who}


async def test_a_club_with_no_history_answers_nothing() -> None:
    assert (
        await ClubRegularsFromMatches(StubMatches()).at(
            club_id=uuid4(), before=at(0)
        )
        == frozenset()
    )


async def test_somebody_who_played_twice_is_named_once() -> None:
    """A set, because the rung is a membership and never a count.

    *Often* is deliberately not a threshold — the rung is an **ordering** and
    not a claim — so two matches and one match put her in the same place, and a
    count here would be the first half of a cut-off nobody wrote down.
    """

    who = uuid4()
    matches = StubMatches(
        _Match(start=at(-100), players=[who, None, None, None]),
        _Match(start=at(-200), players=[who, None, None, None]),
    )

    assert await ClubRegularsFromMatches(matches).at(
        club_id=uuid4(), before=at(0)
    ) == {who}


def test_the_seat_stub_matches_the_shape_the_adapter_reads() -> None:
    """A guard on the fixture rather than on the product.

    The adapter reads `match.start` and `seat.player_id`; a stub that drifted
    from the aggregate would make every case above pass against a shape nothing
    produces.
    """

    real = a_match(paid=1)
    assert hasattr(real, "start")
    assert all(hasattr(seat, "taken") for seat in real.seats)
    assert shifted(real.start, minutes(1)) > real.start
