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

**What the corpus deliberately does not carry** (§2.1): held accounts. They are
binary, never relaxed and carry no constant, so **no ruleset release can change
what they do** — a corpus that included them would spend runtime to hold one
answer fixed.

**Pairwise history and open challenges used to be on that list and are not any
more** (#253). Their exclusion was justified by the provider being
``NoMatchHistoryExists``, and ``challenges`` signing the port killed the
justification: ``PREVIOUS_ACCEPT``, ``PREVIOUS_DECLINE`` and ``CHALLENGE_LOAD``'s
three rungs are **priced** and would otherwise be releasable behaviour the
offline diff could not see. The gate — one pair with an open game between them —
comes in for the reason blocks did: a corpus with none over-reports how many
candidates a search returns.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
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
from app.modules.matchmaking.domain.deck import (
    INHERITED_ON_THE_DECK,
    DeckExclusions,
)
from app.modules.matchmaking.domain.geography import Point
from app.modules.matchmaking.domain.search_context import (
    LiveGateFacts,
    LiveTermFacts,
    SearchContext,
    SearcherFacts,
)
from app.modules.matchmaking.domain.searches import SearchInitiation, SearchSurface
from app.engines.racketskill.core import band_for, confidence_percent, likely_range
from app.kernel import Instant, Sport
from app.modules.matchmaking.domain.ports import (
    OutcomeTally,
    PairwiseCounterpart,
    PairwiseOutcome,
)
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from scripts.ruleset_diff.population import (
    EVERY_NTH_RUNS_EVERY_SURFACE,
    NOW,
    Member,
    Population,
)

#: The terms with no provider on this platform. **Empty since ``docs/adr/0140``**,
#: when ``player_score`` shipped and reliability stopped being the last one.
#:
#: The evidence gate counts person-specific gaps and never platform-wide absence,
#: so this has to be what the composition root says rather than what the corpus
#: finds convenient — and it moved the gate's basis from seven live terms to
#: eight, which is a real change to the artefact below rather than a comment.
#:
#: **Nobody in this population has a Player Score**, which is a different fact and
#: is spelled the way the provider spells it: ``player_scores`` is empty, so every
#: member's reliability stands down as **their own** gap. Arranging a synthetic
#: record would mean inventing games and challenges that never happened, and a
#: corpus that scored an invented history would be answering about a platform
#: that does not exist — which is exactly what this constant exists to prevent.
ABSENT_TERMS: Final[frozenset[Term]] = frozenset()

#: The snapshot version every container claims. A constant, because the corpus
#: has no log to be a prefix of — and a moving number would put a value in the
#: committed artifact that says nothing about the ruleset.
SNAPSHOT_VERSION: Final = 1


@final
@dataclass(frozen=True, slots=True)
class Relations:
    """The population's five relations, resolved once and carried as one thing.

    They are read per search and computed per run, so threading them one
    parameter at a time made the signature grow every time the corpus learned
    about another ledger. What they have in common is exactly what makes them a
    type: each is *the whole population's* answer to one of the reads a live
    search takes, indexed the way that read is keyed.
    """

    #: Handle -> the ids that player may not be shown, either direction.
    blocks: Mapping[str, frozenset[str]]
    #: Handle -> who said *Let's play* to them, and how many days ago.
    yeses: Mapping[str, Mapping[UUID, int]]
    #: Handle -> their pairwise history, one row per counterpart.
    answered: Mapping[str, Mapping[UUID, PairwiseCounterpart]]
    #: Handle -> the ids they already have an open game with.
    gated: Mapping[str, frozenset[str]]
    #: Id -> how many seats are waiting on that player's answer. **Everybody is
    #: in it**, because every player asked about gets a count.
    loads: Mapping[UUID, int]
    #: Id -> how many times that player was shown this week.
    shown: Mapping[UUID, int]


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

    relations = Relations(
        blocks=_blocks_by_player(population),
        yeses=_yeses_by_searcher(population),
        answered=_answers_by_searcher(population),
        gated=_open_challenges_by_player(population),
        loads=_loads_by_player(population),
        shown={member.player_id: member.times_shown for member in population.members},
    )
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
                relations=relations,
            )
        if index % EVERY_NTH_RUNS_EVERY_SURFACE:
            continue
        for surface in (
            SearchSurface.LINEUP,
            SearchSurface.FILL_SEATS,
            SearchSurface.DECK,
        ):
            # **The deck has no mode and reads no declaration**: every deal
            # scores under the fun ruler (`docs/adr/0169` §2), which is the
            # whole reason `search.mode` is null exactly when the surface is a
            # deck. The intent term stands down there too — the context knows
            # its surface, so `deal` needs telling nothing.
            mode = (
                INHERITED_ON_THE_DECK
                if surface is SearchSurface.DECK
                else SearchMode.COMPETITIVE
            )
            yield _search(
                member,
                rows,
                ruleset,
                surface=surface,
                mode=mode,
                relations=relations,
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
    relations: Relations,
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
            blocked_player_ids=relations.blocks.get(member.handle, frozenset()),
            held_player_ids=frozenset(),
            unshowable_player_ids=frozenset(),
            open_challenge_ids=relations.gated.get(member.handle, frozenset()),
        ),
        terms=LiveTermFacts(
            counterparts=relations.answered.get(member.handle, {}),
            open_challenge_counts=dict(relations.loads),
            player_scores={},
            times_shown=dict(relations.shown),
            interest_days_ago=dict(relations.yeses.get(member.handle, {})),
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
    # The corpus stands in for `rating.rating_initialised`, so it publishes the
    # range the way the engine does — through the engine's own function, rounded
    # where the engine rounds. Nothing scores it; it is here because a row with
    # a Level and no range is a row this platform does not produce.
    low, high = likely_range(member.mu, member.sigma)
    return CandidateRow(
        player_id=str(member.player_id),
        sport=member.sport,
        mu=member.mu,
        sigma=member.sigma,
        confidence=confidence_percent(member.sigma),
        range_low=round(low, 2),
        range_high=round(high, 2),
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
            suppressed=frozenset(),
            already_asked=frozenset(),
            already_dealt=frozenset(),
            cooling_off=frozenset(),
        )
    return DeckExclusions(
        suppressed=frozenset({UUID(others[0].player_id)}),
        already_asked=frozenset(),
        already_dealt=frozenset(),
        # Nobody in the corpus has a game with anybody: the population is
        # inputs only, and a court is an outcome. The cool-off is exercised
        # at its own seam (`tests/unit/test_deck_deal.py`), not here.
        cooling_off=frozenset(),
    )


def _blocks_by_player(population: Population) -> Mapping[str, frozenset[str]]:
    """A block is directed as recorded and **symmetric in effect** (ADR-0095)."""

    ids = {member.handle: str(member.player_id) for member in population.members}
    both: dict[str, set[str]] = {}
    for a, b in population.blocks:
        both.setdefault(a, set()).add(ids[b])
        both.setdefault(b, set()).add(ids[a])
    return {handle: frozenset(blocked) for handle, blocked in both.items()}


def _answers_by_searcher(
    population: Population,
) -> Mapping[str, Mapping[UUID, PairwiseCounterpart]]:
    """The searcher's pairwise history, as the fence reads it: one row per person.

    ``PLAYED`` and ``PLANNED_NEVER_PLAYED`` are absent from every row, which is
    what the live provider answers too — a challenge accepted is not a game
    played, and ``matches`` is unwritten. That is load-bearing rather than
    incidental: familiarity needs ``games_played_together >= 1``, so a
    challenge-only pair leaves the modifier **absent** rather than firing at zero
    strength on every card.

    **Every tally is a count of one, and that is a stated limit rather than an
    oversight.** Both signals downstream are flags — *has this ever happened* —
    so a second accept between the same pair moves nothing the diff could see,
    and ``last_at`` is the only field the bound reads. A corpus that carried
    repeat counterparts would spend runtime to hold one answer fixed, which is
    the same argument §2.1 makes about held accounts.
    """

    ids = {member.handle: member.player_id for member in population.members}
    tallies: dict[str, dict[UUID, dict[PairwiseOutcome, OutcomeTally]]] = {}
    for searcher, counterpart, outcome, days in population.answers:
        tallies.setdefault(searcher, {}).setdefault(ids[counterpart], {})[
            PairwiseOutcome(outcome)
        ] = OutcomeTally(count=1, last_at=Instant(NOW - timedelta(days=days)))
    return {
        searcher: {
            player_id: PairwiseCounterpart(player_id=player_id, outcomes=outcomes)
            for player_id, outcomes in rows.items()
        }
        for searcher, rows in tallies.items()
    }


def _open_challenges_by_player(population: Population) -> Mapping[str, frozenset[str]]:
    """The gate, **symmetric in effect** — two people are arranging a game or not.

    Recorded as one direction and applied in both, exactly as a block is: the
    matcher's ``OpenChallenge`` carries no organiser and no sport, because
    sharing a line-up makes a pair regardless of who sent it.
    """

    ids = {member.handle: str(member.player_id) for member in population.members}
    both: dict[str, set[str]] = {}
    for a, b in population.open_challenges:
        both.setdefault(a, set()).add(ids[b])
        both.setdefault(b, set()).add(ids[a])
    return {handle: frozenset(others) for handle, others in both.items()}


def _loads_by_player(population: Population) -> Mapping[UUID, int]:
    """How full each candidate's inbox is. **Everybody gets a count.**

    Absence from ``population.inboxes`` is an empty inbox and crosses as a
    measured ``0``, which is the shape the port answers with — every player asked
    about gets a count, and only a Player Score spells absence by silence.
    """

    depths = dict(population.inboxes)
    return {
        member.player_id: depths.get(member.handle, 0)
        for member in population.members
    }


def _yeses_by_searcher(
    population: Population,
) -> Mapping[str, Mapping[UUID, int]]:
    ids = {member.handle: member.player_id for member in population.members}
    said: dict[str, dict[UUID, int]] = {}
    for searcher, candidate, days in population.yeses:
        said.setdefault(searcher, {})[ids[candidate]] = days
    return said
