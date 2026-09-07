"""A search, built in memory, so a test can vary one fact and nothing else.

A ``SearchContext`` holds a searcher, a snapshot, four live gate sets and six
live term reads. Spelled out at every call site, the fact under test disappears
into the scaffolding — and worse, a defaulted field somebody quietly changes
moves every assertion at once. So the defaults live here and each test names its
own departure from them.

**The clock is fixed and the ruleset is the live one.** Both are inputs to every
number these tests assert, and a golden file computed against a moving clock is a
golden file that fails on Tuesdays.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping
from uuid import UUID

from app.engines.matchfit.core import ReliabilityStrand, SearchMode, Term
from app.engines.racketskill.core import likely_range
from app.engines.matchfit.ruleset import Ruleset
from app.modules.matchmaking.domain.candidate_index import (
    CandidateRow,
    IndexedArea,
    Partition,
)
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.geography import Point
from app.modules.matchmaking.domain.ports import (
    PairwiseCounterpart,
    PlayerScoreReading,
    RatioStrand,
)
from app.modules.matchmaking.domain.search_context import (
    LiveGateFacts,
    LiveTermFacts,
    SearchContext,
    SearcherFacts,
)
from app.modules.matchmaking.domain.searches import SearchInitiation, SearchSurface
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.kernel import Instant, Sport
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent

#: A Wednesday, because on a Saturday *today* and *the weekend* collapse and a
#: window assertion would stop distinguishing two rungs.
NOW = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)

#: Long enough before ``NOW`` that nobody built with the defaults is a newcomer.
SETTLED = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)

SPORT = Sport.PADEL
CENTRE = Point(latitude=51.51, longitude=-0.13)

SEARCHER_ID = UUID("11111111-1111-1111-1111-111111111111")
SEARCHER_MU = 2.80
SEARCHER_SIGMA = 0.34

#: Four cells of the twenty-one — the availability term's denominator.
SEARCHER_SLOTS = ("1:EVENING", "3:EVENING", "5:EVENING", "6:MORNING")

TAGS = ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")


def published_score(score: int, *, days_ago: int = 3) -> PlayerScoreReading:
    """One published Player Score, with the one live strand behind it.

    The strand is here because **an empty reading is not a reading** — absence is
    spelled by not being in the answer at all — and it is otherwise not what any
    caller of this is about. ``days_ago`` is the horizon's only input, and its
    default is recent enough that nothing decays.

    It is here rather than in either test that wants one, because two spellings
    of *somebody with a record* would be two answers to what the reliability term
    is being handed.
    """

    return PlayerScoreReading(
        strands={
            ReliabilityStrand.SHOWS_UP: RatioStrand(
                value=score,
                numerator=4,
                denominator=5,
                observed_at=Instant(NOW - timedelta(days=days_ago)),
            )
        },
        published_score=score,
    )


def player(number: int) -> UUID:
    """A stable, ordered id, so a tie-break on the id is a fact a test can state."""

    return UUID(f"{number:08d}-0000-0000-0000-000000000000")


def searcher(
    *,
    mode: SearchMode = SearchMode.COMPETITIVE,
    mu: float = SEARCHER_MU,
    sigma: float = SEARCHER_SIGMA,
    tags: tuple[str, ...] = TAGS,
    slots: tuple[str, ...] = SEARCHER_SLOTS,
    radius_km: int = 10,
    area: Point = CENTRE,
    gender: Gender | None = Gender.WOMAN,
    gender_preference: GenderPreference = GenderPreference.ANY,
    declared_intent: PlayIntent = PlayIntent.COMPETITIVE,
    profile_created_at: datetime = SETTLED,
) -> SearcherFacts:
    return SearcherFacts(
        player_id=SEARCHER_ID,
        sport=SPORT,
        mode=mode,
        mu=mu,
        sigma=sigma,
        tags=tags,
        grid=AvailabilityGrid.from_codes(slots),
        radius_km=radius_km,
        area=area,
        gender=gender,
        gender_preference=gender_preference,
        declared_intent=declared_intent,
        profile_created_at=profile_created_at,
    )


def row(
    number: int,
    *,
    mu: float = SEARCHER_MU,
    sigma: float = 0.34,
    tags: tuple[str, ...] = TAGS,
    slots: tuple[str, ...] = SEARCHER_SLOTS,
    latitude: float = CENTRE.latitude,
    longitude: float = CENTRE.longitude,
    radius_km: int = 25,
    declared_intent: str | None = "COMPETITIVE",
    gender: str | None = "WOMAN",
    gender_preference: str = "ANY",
    proposals_opt_in: bool | None = True,
    calibration_priority: str = "STANDARD",
    rating_status: str = "INITIAL_ESTIMATE",
    profile_created_at: datetime = SETTLED,
    last_active_at: datetime | None = None,
    sport: str = SPORT.value,
) -> CandidateRow:
    """One index row. ``number`` fixes the player id and orders the ties."""

    return CandidateRow(
        player_id=str(player(number)),
        sport=sport,
        mu=mu,
        sigma=sigma,
        confidence=62,
        # Through the engine's own function, because a builder that spelled
        # `mu - sigma` would be this suite's private opinion about what a likely
        # range is — and it would drift off the scale at the ends, where the
        # real one clamps.
        range_low=round(likely_range(mu, sigma)[0], 2),
        range_high=round(likely_range(mu, sigma)[1], 2),
        band="Improver",
        band_lower=2.5,
        band_upper=3.0,
        rating_status=rating_status,
        calibration_priority=calibration_priority,
        declared_intent=declared_intent,
        social_tags=tags,
        tags_updated_at=SETTLED,
        availability=slots,
        grid_updated_at=SETTLED,
        areas=(IndexedArea(latitude=latitude, longitude=longitude),),
        search_radius_km=radius_km,
        proposals_opt_in=proposals_opt_in,
        gender=gender,
        gender_preference=gender_preference,
        profile_created_at=profile_created_at,
        last_active_at=last_active_at,
        applied_through_sequence_no=1,
    )


def context(
    rows: tuple[CandidateRow, ...] = (),
    *,
    facts: SearcherFacts | None = None,
    now: datetime = NOW,
    blocked: frozenset[str] = frozenset(),
    held: frozenset[str] = frozenset(),
    unshowable: frozenset[str] = frozenset(),
    open_challenges: frozenset[str] = frozenset(),
    counterparts: Mapping[UUID, PairwiseCounterpart] | None = None,
    open_challenge_counts: Mapping[UUID, int] | None = None,
    player_scores: Mapping[UUID, PlayerScoreReading] | None = None,
    times_shown: Mapping[UUID, int] | None = None,
    interest_days_ago: Mapping[UUID, int] | None = None,
    newcomer_appearances: Mapping[UUID, int] | None = None,
    busy_threshold: int | None = None,
    initiation: SearchInitiation = SearchInitiation.HUMAN,
    surface: SearchSurface = SearchSurface.SHORTLIST,
    ruleset: Ruleset = LIVE_RULESET,
    absent_terms: frozenset[Term] = frozenset(),
    snapshot_version: int = 42,
) -> SearchContext:
    """One whole search, bound. ``absent_terms`` defaults to the live platform's.

    **Empty since ``docs/adr/0140``**, when ``player_score`` shipped and
    reliability stopped being the one term with no provider. The evidence gate
    counts person-specific gaps rather than platform-wide absence, so a test
    carrying the old default would be testing a platform that no longer exists —
    and would read a candidate with no record as nobody's gap rather than as
    theirs.
    """

    return SearchContext(
        searcher=facts or searcher(),
        surface=surface,
        initiation=initiation,
        now=now,
        snapshot=CandidateSnapshot(
            partition=Partition.for_sport(SPORT),
            rows=rows,
            snapshot_version=snapshot_version,
            caught_up_at=now,
        ),
        gates=LiveGateFacts(
            blocked_player_ids=blocked,
            held_player_ids=held,
            unshowable_player_ids=unshowable,
            open_challenge_ids=open_challenges,
        ),
        terms=LiveTermFacts(
            counterparts=counterparts or {},
            open_challenge_counts=open_challenge_counts or {},
            player_scores=player_scores or {},
            times_shown=times_shown or {},
            interest_days_ago=interest_days_ago or {},
            newcomer_appearances=newcomer_appearances or {},
            busy_threshold=busy_threshold,
        ),
        ruleset=ruleset,
        absent_terms=absent_terms,
    )
