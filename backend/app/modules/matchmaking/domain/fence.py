"""Assembling what crosses the privacy fence — and nothing that may not.

**The fence is the package boundary with no exceptions in it** (``docs/adr/0093``).
Gating and generation happen on this side, where the I/O is; ``matchfit`` receives
an already-gated, already-fenced set and does the arithmetic. This module is the
crossing: every value the scorer will ever see is built here, from an index row
and the facts the search read live, and **the module holds strictly more than it
hands over**.

Three things happen here and nowhere else, each because the fence puts them here:

*The two σs are combined.* ``combine_sigma`` and the confidence transform are
RacketSkill's — *the single place any engine is allowed to combine two standard
deviations* — and ``.importlinter`` forbids one engine to import the other. So
Match Fit reads that rule **through the module that composes the two**, and a
``CombinedUncertainty`` arrives already combined.

*The curves are applied.* Four Liveness signals cross as a reading in ``[0, 1]``
rather than as what was measured, because a curve from *days since a session
refresh* to a reading is a measurement and belongs beside the clock
(``measurements``).

*The vocabularies stay single-spelled.* Social tag ids, parts of the day and Play
intent declarations cross as the machine codes they already are. An engine may
not import the module that owns a vocabulary, and retyping one on the far side
would be a second spelling of a closed set.

**What does not cross is asserted, not documented.**
``tests/unit/test_scorable_candidate_fence.py`` walks the scorer's own types
transitively and fails the build on a name, a photo, a gender, a birthdate or a
precise location. Nothing here can put one there; this module is only where
somebody would try.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.engines.matchfit.scorable import (
    CombinedUncertainty,
    GridCell,
    LevelReading,
    LivenessFacts,
    MeanObservation,
    ModifierFacts,
    RatioObservation,
    ReliabilityRecord,
    ScorableCandidate,
    Searcher,
    SharedHistory,
    StrandObservation,
)
from app.engines.racketskill.core import combine_sigma, confidence_percent
from app.kernel import iso_weekday
from app.modules.matchmaking.domain.areas import area_code_of
from app.modules.matchmaking.domain.candidate_index import CandidateRow
from app.modules.matchmaking.domain.geography import Point
from app.modules.matchmaking.domain.measurements import (
    Overlap,
    exposure_reading,
    overlap_proximity_reading,
    recent_activity_reading,
)
from app.modules.matchmaking.domain.ports import (
    PairwiseCounterpart,
    PairwiseOutcome,
    PlayerScoreReading,
    RatioStrand,
)
from app.modules.matchmaking.domain.ports import (
    StrandObservation as PublishedStrand,
)
from app.modules.matchmaking.domain.search_context import (
    SearchContext,
    is_new_at,
)
from app.modules.player_profile.domain.availability import AvailabilitySlot, DayPart

#: The parts of a day in the order the platform lays them out — **the one
#: vocabulary fact the engine is told rather than allowed to know.** It is
#: supplied once per search so the scorer can say *the soonest cell you both
#: ticked* without ever learning that one of them is called a morning.
DAY_PARTS: tuple[str, ...] = tuple(part.value for part in DayPart)

#: What ``calibration_priority`` says when a rating is **not** clamouring for
#: real games. Read as a binary because the rating aggregate has two values: a
#: 0…+4 ramp over a field with two states is 0 or +4, and the modifier says so.
CALIBRATION_STANDARD = "STANDARD"


def searcher_of(context: SearchContext) -> Searcher:
    """The searcher, as the scorer is allowed to see them.

    Their grid is the availability term's **denominator** — *how much of my week
    does this person cover* — which is what makes that reading asymmetric and a
    fact about the pair rather than about either person.
    """

    facts = context.searcher
    return Searcher(
        level=LevelReading(mu=facts.mu, sigma=facts.sigma),
        mode=facts.mode,
        tags=facts.tags,
        grid=_cells(facts.grid.slots),
        radius_km=float(facts.radius_km),
        today=iso_weekday(context.now.isoweekday()),
        day_parts=DAY_PARTS,
    )


def candidate_of(
    row: CandidateRow,
    context: SearchContext,
    *,
    distance_km: float,
    player_uuid: UUID,
) -> ScorableCandidate:
    """One index row, as the scorer is allowed to see it.

    The candidate's own radius crosses because it is a Liveness dock and **never
    a gate** — somebody who set a small ring is not refusing to be found, so the
    searcher is shown the fact rather than having the person removed.
    """

    return ScorableCandidate(
        player_id=row.player_id,
        level=LevelReading(mu=row.mu, sigma=row.sigma),
        declared_intent=row.declared_intent,
        tags=row.social_tags,
        grid=_cells(slots_of(row)),
        radius_km=float(row.search_radius_km),
        area_code=area_code_of(area_of(row)),
        distance_km=distance_km,
        combined=_combined(context.searcher.sigma, row.sigma),
        reliability=reliability_record_of(
            context.terms.player_scores.get(player_uuid), context.now
        ),
    )


def modifier_facts_of(
    row: CandidateRow, context: SearchContext, player_uuid: UUID
) -> ModifierFacts:
    """What stage 4 reads. **Two of the three cannot fire today.**

    Familiarity and the welcoming record both need ``matches``, which is
    unwritten, and they say so by being absent rather than by arriving as a
    ``False`` or a zero. ``welcomed_settling_opponents`` is ``None`` meaning *no
    answer* and emphatically not *no*.

    The absorption tally crosses even so, and is not waiting on ``matches`` with
    the modifier it bounds: it is counted from searches, which this build runs.
    **Wired, and never binding** while the cap refuses its integer.
    """

    counterpart = context.terms.counterparts.get(player_uuid)
    return ModifierFacts(
        calibration_elevated=row.calibration_priority != CALIBRATION_STANDARD,
        shared_history=_shared_history(counterpart, context.now),
        welcomed_settling_opponents=None,
        newcomer_appearances=context.absorption_tally(player_uuid),
    )


def liveness_facts_of(
    row: CandidateRow,
    context: SearchContext,
    overlap: Overlap,
    player_uuid: UUID,
) -> LivenessFacts:
    """What stage 6 reads: ten facts that move a position and never a number.

    ``interest_days_ago`` is ``None`` on every search this build can run — the
    interest ledger and its ``+14`` land with their own route — and the absence
    is the honest spelling: nobody has said *Let's play* to anybody yet, so there
    is no age to read.

    ``answer_rate`` is ``None`` for the same reason one layer over: how well and
    how fast somebody answers a challenge is a fact about challenges, and nothing
    in this repository has ever sent one.
    """

    counterpart = context.terms.counterparts.get(player_uuid)
    return LivenessFacts(
        interest_days_ago=None,
        newcomer=is_new_at(row.profile_created_at, context.now),
        # The same call stage 4 made, so one cap cannot drop the modifier and
        # leave the reorder standing.
        newcomer_appearances=context.absorption_tally(player_uuid),
        previously_accepted=_has(counterpart, PairwiseOutcome.ACCEPTED),
        previously_declined=_has(counterpart, PairwiseOutcome.DECLINED),
        answer_rate=None,
        recent_activity=recent_activity_reading(row.last_active_at, context.now),
        overlap_proximity=overlap_proximity_reading(overlap.days_away),
        open_challenges=context.terms.open_challenge_counts.get(player_uuid),
        exposure=exposure_reading(
            context.terms.times_shown.get(player_uuid, 0),
            context.terms.busy_threshold,
        ),
    )


def reliability_record_of(
    reading: PlayerScoreReading | None, now: datetime
) -> ReliabilityRecord | None:
    """A Player Score, as the reliability term reads one. ``None`` is an absence.

    The horizon's input — *how long since anything was observed* — is measured
    here because a pure process has no clock, and it is **one** number over the
    whole record rather than six: the strands share one cause, *this player
    stopped playing*, and six ages would be six places for it to disagree with
    itself.
    """

    if reading is None:
        return None
    days = (now - reading.most_recent_observation).days
    return ReliabilityRecord(
        strands={
            strand: _observation(observation)
            for strand, observation in reading.strands.items()
        },
        published_score=reading.published_score,
        days_since_last_observation=max(0, days),
    )


def area_of(row: CandidateRow) -> Point:
    """The one coarse area this row is searched from.

    ``areas`` is a set of size one today and a tuple so that a row reachable from
    two cells costs a pointer rather than a duplicate row; the first is the only
    one until that day arrives.
    """

    return Point(latitude=row.areas[0].latitude, longitude=row.areas[0].longitude)


def slots_of(row: CandidateRow) -> tuple[AvailabilitySlot, ...]:
    """The candidate's grid, as the platform's own slots. Empty is a real answer."""

    return tuple(AvailabilitySlot.from_code(code) for code in row.availability)


def _cells(slots: tuple[AvailabilitySlot, ...]) -> tuple[GridCell, ...]:
    return tuple(GridCell(day=slot.day, part=slot.part.value) for slot in slots)


def _combined(searcher_sigma: float, candidate_sigma: float) -> CombinedUncertainty:
    pair = combine_sigma(searcher_sigma, candidate_sigma)
    return CombinedUncertainty(sigma=pair, confidence=confidence_percent(pair))


def _shared_history(
    counterpart: PairwiseCounterpart | None, now: datetime
) -> SharedHistory | None:
    """What the two of them have played. **Absence has one spelling: none at all.**

    A pair who arranged games and never played one has counterparts but no
    ``SharedHistory``: the type refuses a record of no games, because a zero here
    would be an invented one and would decay from full strength like a game
    somebody actually played.
    """

    if counterpart is None or counterpart.games_played_together < 1:
        return None
    return SharedHistory(
        days_since_last_game=max(0, (now - counterpart.last_at).days),
        games_played_together=counterpart.games_played_together,
    )


def _has(counterpart: PairwiseCounterpart | None, outcome: PairwiseOutcome) -> bool:
    return counterpart is not None and outcome in counterpart.outcomes


def _observation(observation: PublishedStrand) -> StrandObservation:
    """One strand, from the port's shape into the scorer's.

    Two shapes on each side, and the mapping is one-to-one — five ratios and a
    mean. The scorer's ratio carries the **published** figure and the
    *opportunity* behind it, which is the denominator: the matcher's entire
    policy over these facts is standing a strand down below the bar, and one
    no-show out of one game is not thirty-five out of thirty-eight.
    """

    if isinstance(observation, RatioStrand):
        return RatioObservation(
            published_value=observation.value,
            observations=observation.denominator,
        )
    return MeanObservation(
        mean=observation.mean, observations=observation.rating_count
    )
