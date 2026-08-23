"""``RatedSports`` and ``ParkedRuns`` over the rating context's own repositories.

The two adapters the door reads through, and the two claims their docstrings make
that no behavioural test can reach — because both are claims about **cost**, and a
cheaper read and a dearer one give the same answer.

`RatedSports.holds` promises *one lookup, never a replay of every rating she
holds*, and `ParkedRuns` promises *a boolean, never the run*. Swapping either for
the expensive spelling leaves every screen in the suite identical; what goes red
is here, where the fakes refuse the read that was not supposed to happen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.kernel import Instant, Sport, instant
from app.modules.now.infrastructure.parked_runs import ParkedRunsFromAssessments
from app.modules.now.infrastructure.rating_sports import RatedSportsFromSkillRatings
from app.modules.rating.domain.skill_rating import SkillRating

AT: Instant = instant(datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc))


class RatingsRefusingTheReplay:
    """``exists_for`` answers; ``find_all_for`` is the read this must not make."""

    def __init__(self, *held: tuple[UUID, Sport]) -> None:
        self._held = set(held)
        self.pair_asks: list[tuple[UUID, Sport]] = []

    async def save(self, rating: SkillRating) -> None:  # pragma: no cover
        raise AssertionError("the door writes nothing")

    async def exists_for(self, *, player_id: UUID, sport: Sport) -> bool:
        self.pair_asks.append((player_id, sport))
        return (player_id, sport) in self._held

    async def find_for(
        self, *, player_id: UUID, sport: Sport
    ) -> Optional[SkillRating]:  # pragma: no cover
        raise AssertionError("`holds` is a question, never an aggregate")

    async def find_all_for(
        self, *, player_id: UUID
    ) -> list[SkillRating]:  # pragma: no cover
        raise AssertionError(
            "`holds` asked for every rating she holds to answer about one sport"
        )


class AssessmentsRefusingTheTranscript:
    """``find_open`` answers; loading an aggregate is the read this must not make."""

    def __init__(self, *open_runs: tuple[UUID, Sport]) -> None:
        self._open = set(open_runs)
        self.pair_asks: list[tuple[UUID, Sport]] = []

    async def load(self, assessment_id: UUID, *, for_player: UUID):  # pragma: no cover
        raise AssertionError("the door does not read a transcript")

    async def save(self, assessment) -> None:  # pragma: no cover
        raise AssertionError("the door writes nothing")

    async def next_identity(self, *, player_id: UUID, sport: Sport) -> UUID:
        raise AssertionError("the door starts nothing")  # pragma: no cover

    async def find_open(self, *, player_id: UUID, sport: Sport):
        self.pair_asks.append((player_id, sport))
        # The adapter reads *whether there is one*, so the run itself never has to
        # be a real aggregate for this question to be answerable.
        return object() if (player_id, sport) in self._open else None

    async def find_all_open(self, *, player_id: UUID) -> list:  # pragma: no cover
        raise AssertionError(
            "the door asked for every unfinished run to answer about one sport"
        )


async def test_holds_asks_by_pair_and_never_replays_the_whole_set() -> None:
    player = uuid4()
    ratings = RatingsRefusingTheReplay((player, Sport.PADEL))
    rated = RatedSportsFromSkillRatings(ratings=ratings)

    assert await rated.holds(player_id=player, sport=Sport.PADEL) is True
    assert ratings.pair_asks == [(player, Sport.PADEL)]


async def test_holds_is_false_at_a_sport_she_was_never_rated_at() -> None:
    player = uuid4()
    rated = RatedSportsFromSkillRatings(
        ratings=RatingsRefusingTheReplay((player, Sport.PADEL))
    )

    assert await rated.holds(player_id=player, sport=Sport.SQUASH) is False


async def test_holds_never_answers_for_another_player() -> None:
    # The stream id *is* the pair, so a rating cannot be reached without saying
    # whose it is — and this is the read that decides whether she is owed a door.
    somebody = uuid4()
    rated = RatedSportsFromSkillRatings(
        ratings=RatingsRefusingTheReplay((somebody, Sport.PADEL))
    )

    assert await rated.holds(player_id=uuid4(), sport=Sport.PADEL) is False


async def test_a_parked_run_is_a_boolean_read_by_pair() -> None:
    player = uuid4()
    assessments = AssessmentsRefusingTheTranscript((player, Sport.SQUASH))
    parked = ParkedRunsFromAssessments(assessments=assessments)

    answer = await parked.parked_at(player_id=player, sport=Sport.SQUASH)

    assert answer is True
    assert assessments.pair_asks == [(player, Sport.SQUASH)]


async def test_no_run_at_this_sport_is_false_rather_than_an_error() -> None:
    # The ordinary state of a player meeting a sport for the first time, which is
    # the state the door exists for.
    player = uuid4()
    parked = ParkedRunsFromAssessments(
        assessments=AssessmentsRefusingTheTranscript((player, Sport.TENNIS))
    )

    assert await parked.parked_at(player_id=player, sport=Sport.SQUASH) is False


async def test_the_adapter_answers_with_a_boolean_and_never_the_run() -> None:
    # `ParkedRuns` returning an `Assessment` would invite a later session to read
    # a transcript on the home screen's path.
    player = uuid4()
    parked = ParkedRunsFromAssessments(
        assessments=AssessmentsRefusingTheTranscript((player, Sport.SQUASH))
    )

    assert await parked.parked_at(player_id=player, sport=Sport.SQUASH) is True
