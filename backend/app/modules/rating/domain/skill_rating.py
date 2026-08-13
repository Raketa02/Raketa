"""The SkillRating aggregate — event-sourced, keyed by (player, sport).

Initialisation is the only transition today; match, inactivity and status-change
events are reserved for the match-update engine, which the shared uncertainty
core is extracted to serve. The band's own boundaries travel on the rating, so a
screen never reads them from a second source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.engines.assessment import CALIBRATION_PRIORITY_STANDARD, AssessmentResult
from app.kernel import Sport
from app.modules.rating.domain.events import RatingInitialised
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
    # How urgently this rating wants real matches, and why its confidence landed
    # where it did. Both are facts about the rating, so they travel with it into
    # the match-update engine rather than living only on the assessment.
    calibration_priority: str = CALIBRATION_PRIORITY_STANDARD
    confidence_reason_key: str | None = None
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
            self.calibration_priority = event.calibration_priority
            self.confidence_reason_key = event.confidence_reason_key
            self.version += 1
            return
        raise TypeError(f"Unsupported rating event {event!r}")
