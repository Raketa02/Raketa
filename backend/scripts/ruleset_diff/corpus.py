"""The searches the corpus runs, built from the population and a fixed clock.

§2.1's *the searches*: **every player runs ``SHORTLIST`` in both modes**, and
every *n*-th player by id order also runs ``LINEUP``, ``FILL_SEATS`` and
``DECK`` — *a rule, never a sample, because a rule survives a resize.* The
collision is real and stated: a shortlist is 1.00 µs per surviving candidate and
a line-up enumerates thousands of combinations at ``K = 24``, so per-surface
counts are printed on the face of the report.

**Everything here is the pure seam.** ``run``, ``pool_for``, ``seat`` and
``deal`` take a bound context and an engine and do no I/O, so a corpus run needs
no database, no Redis, no clock and no network — which is what lets the gate be
hermetic and live in CI (ADR-0118 §7).

**What the corpus deliberately does not carry** (§2.1): held accounts, pairwise
history and open challenges. All three are binary, never relaxed and carry no
constant, so **no ruleset release can change what they do** — a corpus that
included them would spend runtime to hold three answers fixed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterator, Mapping, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.modules.matchmaking.domain.candidate_index import (
    CandidateRow,
    IndexedArea,
    Partition,
)
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.deck import DeckExclusions, mode_for_intent
from app.modules.matchmaking.domain.geography import Point
from app.modules.matchmaking.domain.search_context import (
    LiveGateFacts,
    LiveTermFacts,
    SearchContext,
    SearcherFacts,
)
from app.modules.matchmaking.domain.searches import SearchInitiation, SearchSurface
from app.engines.racketskill.core import band_for, confidence_percent
from app.kernel import Instant, Sport
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from scripts.ruleset_diff.population import (
    EVERY_NTH_RUNS_EVERY_SURFACE,
    NOW,
    Member,
    Population,
)

#: The one term with no provider on this platform. The evidence gate counts
#: person-specific gaps and never platform-wide absence, so a corpus that left
#: this out would be scoring a platform that does not exist.
ABSENT_TERMS: Final = frozenset({Term.RELIABILITY})

#: The snapshot version every container claims. A constant, because the corpus
#: has no log to be a prefix of — and a moving number would put a value in the
#: committed artifact that says nothing about the ruleset.
SNAPSHOT_VERSION: Final = 1


@final
@dataclass(frozen=True, slots=True)
class Search:
    """One search of the corpus: what it is, and the context that answers it."""

    #: ``padel-N-0007 · SHORTLIST · COMPETITIVE`` — the key the answers file is
    #: sorted and diffed on, and the one a human reads in a report.
    key: str
    #: **The enum, never its spelling.** Four surfaces are four different
    #: terminal stages and every reader here branches on which — a string would
    #: put that branch one typo away from silently running a shortlist's
    #: recording over a deal.
    surface: SearchSurface
    sport: str
    mode: str
    searcher: str
    tail: bool
    context: SearchContext
    #: The deck's own exclusions, ``None`` on every other surface.
    exclusions: DeckExclusions | None = None


def rows_for(population: Population, sport: str) -> tuple[CandidateRow, ...]:
    """One sport's whole partition, in the order ties break on (``docs/adr/0105``)."""

    return tuple(
        sorted(
            (_row(member) for member in population.by_sport(sport)),
            key=lambda row: row.player_id,
        )
    )


def searches(population: Population, ruleset: Ruleset) -> Iterator[Search]:
    """Every search the corpus runs, in a stable order."""

    blocks = _blocks_by_player(population)
    yeses = _yeses_by_searcher(population)
    shown = {member.player_id: member.times_shown for member in population.members}
    partitions = {
        sport: rows_for(population, sport)
        for sport in sorted({member.sport for member in population.members})
    }
    for index, member in enumerate(population.members):
        rows = partitions[member.sport]
        for mode in (SearchMode.COMPETITIVE, SearchMode.FOR_FUN):
            yield _search(
                member,
                rows,
                ruleset,
                surface=SearchSurface.SHORTLIST,
                mode=mode,
                blocks=blocks,
                yeses=yeses,
                shown=shown,
            )
        if index % EVERY_NTH_RUNS_EVERY_SURFACE:
            continue
        for surface in (
            SearchSurface.LINEUP,
            SearchSurface.FILL_SEATS,
            SearchSurface.DECK,
        ):
            # **The deck has no mode**: it reads the player's own declaration and
            # scores against that (`the-engine.md` §9.11), which is the whole
            # reason `search.mode` is null exactly when the surface is a deck.
            mode = (
                mode_for_intent(PlayIntent(member.declared_intent), ruleset.intent)
                if surface is SearchSurface.DECK
                else SearchMode.COMPETITIVE
            )
            yield _search(
                member,
                rows,
                ruleset,
                surface=surface,
                mode=mode,
                blocks=blocks,
                yeses=yeses,
                shown=shown,
                exclusions=(
                    _exclusions(member, rows) if surface is SearchSurface.DECK else None
                ),
            )


def _search(
    member: Member,
    rows: tuple[CandidateRow, ...],
    ruleset: Ruleset,
    *,
    surface: SearchSurface,
    mode: SearchMode,
    blocks: Mapping[str, frozenset[str]],
    yeses: Mapping[str, Mapping[UUID, int]],
    shown: Mapping[UUID, int],
    exclusions: DeckExclusions | None = None,
) -> Search:
    searcher = _searcher(member, mode)
    context = SearchContext(
        searcher=searcher,
        surface=surface,
        initiation=SearchInitiation.HUMAN,
        now=NOW,
        snapshot=CandidateSnapshot(
            partition=Partition.for_sport(Sport(member.sport)),
            # The searcher's own row is not a candidate for their own search.
            rows=tuple(row for row in rows if row.player_id != str(member.player_id)),
            snapshot_version=SNAPSHOT_VERSION,
            caught_up_at=Instant(NOW),
        ),
        gates=LiveGateFacts(
            blocked_player_ids=blocks.get(member.handle, frozenset()),
            held_player_ids=frozenset(),
            unshowable_player_ids=frozenset(),
            open_challenge_ids=frozenset(),
        ),
        terms=LiveTermFacts(
            counterparts={},
            open_challenge_counts={},
            player_scores={},
            times_shown=dict(shown),
            interest_days_ago=dict(yeses.get(member.handle, {})),
            newcomer_appearances={},
            busy_threshold=None,
        ),
        ruleset=ruleset,
        absent_terms=ABSENT_TERMS,
    )
    return Search(
        key=f"{member.handle} · {surface.value} · {mode.value}",
        surface=surface,
        sport=member.sport,
        mode=mode.value,
        searcher=member.handle,
        tail=member.tail,
        context=context,
        exclusions=exclusions,
    )


def _searcher(member: Member, mode: SearchMode) -> SearcherFacts:
    return SearcherFacts(
        player_id=member.player_id,
        sport=Sport(member.sport),
        mode=mode,
        mu=member.mu,
        sigma=member.sigma,
        tags=member.tags,
        grid=AvailabilityGrid.from_codes(member.slots),
        radius_km=member.radius_km,
        area=Point(latitude=member.latitude, longitude=member.longitude),
        gender=Gender(member.gender),
        gender_preference=GenderPreference(member.gender_preference),
        declared_intent=PlayIntent(member.declared_intent),
        profile_created_at=member.committed_at,
    )


def _row(member: Member) -> CandidateRow:
    band = band_for(member.mu)
    return CandidateRow(
        player_id=str(member.player_id),
        sport=member.sport,
        mu=member.mu,
        sigma=member.sigma,
        confidence=confidence_percent(member.sigma),
        band=band.label,
        band_lower=band.lower,
        band_upper=band.upper,
        rating_status="INITIAL_ESTIMATE",
        calibration_priority=member.calibration_priority,
        declared_intent=member.declared_intent,
        social_tags=member.tags,
        tags_updated_at=member.committed_at,
        availability=member.slots,
        grid_updated_at=member.committed_at,
        areas=(IndexedArea(latitude=member.latitude, longitude=member.longitude),),
        search_radius_km=member.radius_km,
        proposals_opt_in=True,
        gender=member.gender,
        gender_preference=member.gender_preference,
        profile_created_at=member.committed_at,
        # **Never read as a clock.** Liveness reads *last active* at day
        # resolution, and the corpus states it as a fact about the fixed instant
        # the whole run is stamped with.
        last_active_at=member.committed_at,
        applied_through_sequence_no=SNAPSHOT_VERSION,
    )


def _exclusions(member: Member, rows: tuple[CandidateRow, ...]) -> DeckExclusions:
    """One live suppression per deal, so ``PASS_SUPPRESS``'s counter is exercised.

    §2.1's coverage rule, one ledger over: the suppression ledger fires for at
    least one row per density, by rule rather than by rate. It is the searcher's
    own first candidate by id order, which is a rule that survives a resize.
    """

    others = [row for row in rows if row.player_id != str(member.player_id)]
    if not others:
        return DeckExclusions(
            suppressed=frozenset(), already_asked=frozenset(), already_dealt=frozenset()
        )
    return DeckExclusions(
        suppressed=frozenset({UUID(others[0].player_id)}),
        already_asked=frozenset(),
        already_dealt=frozenset(),
    )


def _blocks_by_player(population: Population) -> Mapping[str, frozenset[str]]:
    """A block is directed as recorded and **symmetric in effect** (ADR-0095)."""

    ids = {member.handle: str(member.player_id) for member in population.members}
    both: dict[str, set[str]] = {}
    for a, b in population.blocks:
        both.setdefault(a, set()).add(ids[b])
        both.setdefault(b, set()).add(ids[a])
    return {handle: frozenset(blocked) for handle, blocked in both.items()}


def _yeses_by_searcher(
    population: Population,
) -> Mapping[str, Mapping[UUID, int]]:
    ids = {member.handle: member.player_id for member in population.members}
    said: dict[str, dict[UUID, int]] = {}
    for searcher, candidate, days in population.yeses:
        said.setdefault(searcher, {})[ids[candidate]] = days
    return said
