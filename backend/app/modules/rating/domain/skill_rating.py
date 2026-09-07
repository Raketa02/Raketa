"""The SkillRating aggregate — event-sourced, keyed by (player, sport).

**Two transitions.** Onboarding opens the rating with a hypothesis, and every
confirmed counted result tests it (``docs/adr/0139``). Inactivity is still
reserved; there is no status-change transition, because a status is authored by
whichever rule moved the rating and a second author would be a second answer.
The band's own boundaries travel on the rating, so a screen never reads them from
a second source.

**Applying the same game twice is a no-op and not a refusal.** The catch-up that
drives this is at-least-once by construction — nothing announces a confirmation,
so results are read forward and re-read — and a second sighting of a game already
on the stream is the ordinary case rather than an error. The aggregate answers it
by recording nothing, which is what makes the run safe to interrupt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.engines.assessment import CALIBRATION_PRIORITY_STANDARD, AssessmentResult
from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import MovedRating
from app.kernel import Sport
from app.modules.rating.domain.events import RatingInitialised, RatingMovedOnResult
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class SkillRating:
    id: UUID
    player_id: UUID
    sport: Sport
    mu: float
    sigma: float
    confidence: int
    range_low: float
    range_high: float
    band_name: str
    band_lower: float
    band_upper: float
    status: str
    engine_version: str
    # When this rating last moved. Every transition sets it, so once the
    # match-update engine appends to this stream the field keeps meaning the same
    # thing without anyone remembering to maintain it.
    updated_at: datetime
    # How urgently this rating wants real matches, and why its confidence landed
    # where it did. Both are facts about the rating, so they travel with it into
    # the match-update engine rather than living only on the assessment.
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD
    confidence_reason_key: str | None = None
    #: The counted results already folded into this rating, in the order they
    #: were applied. **The cursor**, and the whole of the catch-up's idempotency
    #: (``docs/adr/0139``): a game on this list has already moved this Level, and
    #: no second record of progress exists to disagree with it.
    applied_games: tuple[UUID, ...] = ()
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "SkillRating":
        rating = cls._empty()
        for event in events:
            rating._apply(event)
        return rating

    @classmethod
    def _empty(cls) -> "SkillRating":
        rating = cls.__new__(cls)
        rating.version = 0
        rating.applied_games = ()
        rating._events = EventRecorder()
        return rating

    @classmethod
    def initialise(
        cls,
        *,
        rating_id: UUID,
        player_id: UUID,
        sport: Sport,
        result: AssessmentResult,
        source_assessment_id: UUID,
        occurred_at: datetime,
    ) -> "SkillRating":
        rating = cls._empty()
        rating._record_that(
            RatingInitialised(
                rating_id=rating_id,
                player_id=player_id,
                sport=sport.value,
                mu=result.mu,
                sigma=result.sigma,
                confidence=result.confidence,
                range_low=result.range_low,
                range_high=result.range_high,
                band_name=result.band.name,
                band_lower=result.band.lower,
                band_upper=result.band.upper,
                status=result.status,
                engine_version=result.engine_version,
                source_assessment_id=source_assessment_id,
                occurred_at=occurred_at,
                calibration_priority=result.calibration_priority,
                confidence_reason_key=(
                    result.confidence_reason.key
                    if result.confidence_reason is not None
                    else None
                ),
            )
        )
        return rating

    @property
    def counted_results(self) -> int:
        """How many confirmed counted results have moved this rating.

        Derived from the stream rather than counted into a column, so it cannot
        disagree with the list it is the length of. What ``status`` reads to tell
        *nothing has ever tested this* from *this has been tested and is still
        moving*.
        """

        return len(self.applied_games)

    @property
    def estimate(self) -> SkillEstimate:
        """This rating as the engine's currency: a Level and an uncertainty."""

        return SkillEstimate(mu=self.mu, sigma=self.sigma)

    def has_applied(self, game_id: UUID) -> bool:
        """Whether this game has already moved this Level."""

        return game_id in self.applied_games

    def move_on_result(
        self,
        *,
        game_id: UUID,
        moved: MovedRating,
        won: bool,
        opposition: SkillEstimate,
        information_share: float,
        occurred_at: datetime,
    ) -> None:
        """Apply one confirmed counted result. **Silent about a game already applied.**

        ``moved`` arrives from the engine rather than being computed here, exactly
        as ``initialise`` takes an ``AssessmentResult``: the arithmetic is the
        rating engine's and the aggregate's job is to record what it said. That is
        also the whole of *only the rating context writes μ, σ and status* — the
        rule lives in one pure module and reaches a stream through this method.
        """

        if self.has_applied(game_id):
            return
        self._record_that(
            RatingMovedOnResult(
                rating_id=self.id,
                player_id=self.player_id,
                sport=self.sport.value,
                game_id=game_id,
                won=won,
                opposition_mu=opposition.mu,
                opposition_sigma=opposition.sigma,
                information_share=information_share,
                win_delta=moved.stakes.win,
                loss_delta=moved.stakes.loss,
                mu=moved.mu,
                sigma=moved.sigma,
                confidence=moved.confidence,
                range_low=moved.range_low,
                range_high=moved.range_high,
                band_name=moved.band.name,
                band_lower=moved.band.lower,
                band_upper=moved.band.upper,
                status=moved.status,
                engine_version=moved.engine_version,
                occurred_at=occurred_at,
            )
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, RatingInitialised):
            self.id = event.rating_id
            self.player_id = event.player_id
            self.sport = Sport(event.sport)
            self.mu = event.mu
            self.sigma = event.sigma
            self.confidence = event.confidence
            self.range_low = event.range_low
            self.range_high = event.range_high
            self.band_name = event.band_name
            self.band_lower = event.band_lower
            self.band_upper = event.band_upper
            self.status = event.status
            self.engine_version = event.engine_version
            self.updated_at = event.occurred_at
            self.calibration_priority = event.calibration_priority
            self.confidence_reason_key = event.confidence_reason_key
            self.applied_games = ()
            self.version += 1
            return
        if isinstance(event, RatingMovedOnResult):
            self.mu = event.mu
            self.sigma = event.sigma
            self.confidence = event.confidence
            self.range_low = event.range_low
            self.range_high = event.range_high
            self.band_name = event.band_name
            self.band_lower = event.band_lower
            self.band_upper = event.band_upper
            self.status = event.status
            # **The engine version moves with the number it produced.** A Level
            # that has been tested by results was last written by the
            # result-update rule, and attributing it to the questionnaire would
            # make the one thing a retune has to be traceable through a lie.
            self.engine_version = event.engine_version
            self.updated_at = event.occurred_at
            self.applied_games = (*self.applied_games, event.game_id)
            self.version += 1
            return
        raise TypeError(f"Unsupported rating event {event!r}")
