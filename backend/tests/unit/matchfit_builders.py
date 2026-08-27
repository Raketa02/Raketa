"""Builders for the fenced scorer inputs, so a test states only what it varies.

A ``ScorableCandidate`` has thirteen fields and a comparison is about one of
them. Spelled out at every call site, the fact under test disappears into the
scaffolding — and worse, a defaulted field somebody quietly changes moves every
assertion at once. So the defaults live here, in one place, and each test names
its own departure from them.

The defaults are **judged case 1's**: the median good pairing from
``docs/specs/matchmaking/judged-pairings.json``, which is also the set the
acceptance test below re-derives.
"""

from __future__ import annotations

from app.engines.matchfit.core import ReliabilityStrand, SearchMode
from app.engines.matchfit.scorable import (
    CombinedUncertainty,
    GridCell,
    LevelReading,
    MeanObservation,
    RatioObservation,
    ReliabilityRecord,
    ScorableCandidate,
    Searcher,
    StrandObservation,
)
from app.engines.racketskill.core import combine_sigma, confidence_percent
from app.kernel import IsoWeekday, iso_weekday
from app.modules.player_profile.domain.availability import DayPart

#: The parts of a day, in the order the platform lays them out — the one
#: vocabulary fact the engine is told rather than allowed to know.
DAY_PARTS = tuple(part.value for part in DayPart)

#: Judged case 1's searcher: four cells of twenty-one, a ten kilometre ring, and
#: a Wednesday, because on a Saturday *today* and *the weekend* collapse.
SEARCHER_MU = 2.80
SEARCHER_SIGMA = 0.34
WEDNESDAY = iso_weekday(3)


def cells(*specs: tuple[int, DayPart]) -> tuple[GridCell, ...]:
    return tuple(GridCell(day=iso_weekday(day), part=part.value) for day, part in specs)


FOUR_CELLS = cells(
    (1, DayPart.EVENING),
    (3, DayPart.EVENING),
    (5, DayPart.EVENING),
    (6, DayPart.MORNING),
)


def searcher(
    *,
    mu: float = SEARCHER_MU,
    sigma: float = SEARCHER_SIGMA,
    mode: SearchMode = SearchMode.COMPETITIVE,
    tags: tuple[str, ...] = (),
    grid: tuple[GridCell, ...] = FOUR_CELLS,
    radius_km: float = 10.0,
    today: IsoWeekday = WEDNESDAY,
) -> Searcher:
    return Searcher(
        level=LevelReading(mu=mu, sigma=sigma),
        mode=mode,
        tags=tags,
        grid=grid,
        radius_km=radius_km,
        today=today,
        day_parts=DAY_PARTS,
    )


def candidate(
    *,
    player_id: str = "candidate",
    mu: float = SEARCHER_MU,
    sigma: float = SEARCHER_SIGMA,
    against_sigma: float = SEARCHER_SIGMA,
    declared_intent: str | None = None,
    tags: tuple[str, ...] = (),
    grid: tuple[GridCell, ...] = FOUR_CELLS,
    radius_km: float = 10.0,
    area_code: str = "PL-WAW-C",
    distance_km: float = 2.0,
    reliability: ReliabilityRecord | None = None,
) -> ScorableCandidate:
    """One candidate, with the pair's uncertainty combined the way the module does.

    ``against_sigma`` is the searcher's σ, and it is a parameter rather than a
    constant because the combination is **RacketSkill's** and is done on the
    module's side of the fence: a test that hard-coded the combined figure would
    be asserting arithmetic nobody runs.
    """

    return ScorableCandidate(
        player_id=player_id,
        level=LevelReading(mu=mu, sigma=sigma),
        declared_intent=declared_intent,
        tags=tags,
        grid=grid,
        radius_km=radius_km,
        area_code=area_code,
        distance_km=distance_km,
        combined=combined(against_sigma, sigma),
        reliability=reliability,
    )


def combined(mine: float, theirs: float) -> CombinedUncertainty:
    pair = combine_sigma(mine, theirs)
    return CombinedUncertainty(sigma=pair, confidence=confidence_percent(pair))


def record(
    *,
    published_score: int = 80,
    days_since_last_observation: int = 7,
    ratios: dict[ReliabilityStrand, tuple[int, int]] | None = None,
    sportsmanship: tuple[float, int] | None = None,
) -> ReliabilityRecord:
    """A Player Score record, as the strands and never as one number."""

    strands: dict[ReliabilityStrand, StrandObservation] = {
        strand: RatioObservation(published_value=value, observations=count)
        for strand, (value, count) in (ratios or {}).items()
    }
    if sportsmanship is not None:
        mean, count = sportsmanship
        strands[ReliabilityStrand.SPORTSMANSHIP] = MeanObservation(
            mean=mean, observations=count
        )
    return ReliabilityRecord(
        strands=strands,
        published_score=published_score,
        days_since_last_observation=days_since_last_observation,
    )


def sigma_pair(a: float, b: float) -> float:
    """RacketSkill's combination, for a test asserting the fixture's own σ.

    Through ``combine_sigma`` and never written out: ``√(σ² + σ²)`` spelled here
    would be a second definition of an identity that already has an owner, which
    is the thing the engine-to-engine fence exists to prevent — and a test
    carrying its own copy would agree with the engine right up until the day the
    rule changed.
    """

    return combine_sigma(a, b)
