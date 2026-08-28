"""Everything one search reads, bound once, before a single row is looked at.

``the-two-contracts.md`` §9: *``SearchContext`` is the module's type — the
searcher's own facts as the backend just read them, plus the live gate facts. It
carries gender preference and ``exclude_player_ids``; it does not reach
``matchfit``.*

**Three rules are enforced by this shape rather than by whoever writes a
pipeline.**

*The client sends asks, never facts.* Every field of :class:`SearcherFacts` is
read by the backend at request time, from the profile, the rating and the
declaration. A radius supplied by a phone is a gate evaluated on a lie, so there
is nowhere on the request for one to arrive.

*The snapshot is bound once.* ``CandidateSource.snapshot`` is called at entry and
the container is held here; a refresh mid-search rebinds the source's own pointer
and cannot move this one (``docs/adr/0112``). A search that took the snapshot
twice would be a search the index could move underneath, and there is no method
here that could take a second.

*Live truth travels beside the snapshot.* Blocks, holds, account state, the open
challenges and the ledger reads are **never index columns** — a column for one
would make staleness cost safety rather than quality (``docs/adr/0111``) — so
they are read once per search, as sets, and carried here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import IsoWeekday, Sport, invariant, iso_weekday
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.geography import BoundingBox, Point, bounding_box
from app.modules.matchmaking.domain.ports import PairwiseCounterpart, PlayerScoreReading
from app.modules.matchmaking.domain.searches import SearchInitiation, SearchSurface
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent

#: How long a player is new for. **A date, never a flag** — the window is clocked
#: from the profile commit and computed where it is read, because a stored
#: ``is_newcomer`` boolean goes stale hourly and a date never does
#: (``the-newcomer-path.md`` §1).
#:
#: It lives here rather than in the ruleset because it is not a weight: it says
#: who counts as new, which is a fact about the product's shape, and the ruleset
#: prices what being new is worth. Both halves read it — the level gate tightens
#: while either side is inside it (``docs/adr/0113``), and Liveness lifts a
#: candidate who is.
NEWCOMER_WINDOW = timedelta(days=14)


@final
@dataclass(frozen=True, slots=True)
class SearcherFacts:
    """The searcher, as the backend has just read them. **Never as they sent.**

    This is the one player in a search whose facts do not come from the index.
    The index copy may lag by seconds, and the searcher's own radius, grid and
    preference are what every gate is evaluated against — so they are read live
    from the aggregates, and the lag is spent only on the people being looked at.
    """

    player_id: UUID
    sport: Sport
    mode: SearchMode
    mu: float
    sigma: float
    tags: tuple[str, ...]
    grid: AvailabilityGrid
    radius_km: int
    area: Point
    #: ``None`` is **not** an answer and is never read as ``PREFER_NOT_TO_SAY``
    #: (``docs/adr/0096``): it is a profile committed before anybody was asked.
    #: A preference that needs it and does not have it excludes.
    gender: Gender | None
    gender_preference: GenderPreference
    #: The declaration this search's mode was chosen beside. Recorded rather than
    #: read: a shortlist takes its mode from the request, and the declaration is
    #: what the 409 checks and what the deck will read.
    declared_intent: PlayIntent
    profile_created_at: datetime

    def __post_init__(self) -> None:
        invariant(self.radius_km > 0, f"a search radius of {self.radius_km} km")
        invariant(self.sigma >= 0.0, f"a negative Uncertainty: {self.sigma}")

    def is_new_at(self, now: datetime) -> bool:
        """Whether the searcher is still inside their newcomer window."""

        return now - self.profile_created_at < NEWCOMER_WINDOW


@final
@dataclass(frozen=True, slots=True)
class LiveGateFacts:
    """The facts that must be live, read once per search and never from the index.

    Every set here answers *about the searcher*: who they may not be shown, who
    is under a hold, who is already talking to them. They are separate fields
    rather than one merged exclusion list because the telemetry histogram counts
    **per gate**, and a merged set would make ten reasons into one.

    **The ids are spelled as the index spells them — strings, not ``UUID``.** The
    ports answer in ``UUID`` and the conversion happens once, here, when the
    context is built: gating walks the whole partition, and parsing a UUID per
    row is the one cost that loop cannot absorb. The term facts below stay keyed
    on ``UUID`` because they are read for the survivors only.
    """

    #: Every player the searcher may never be shown, in either direction
    #: (``docs/adr/0095``). Fails **closed**.
    blocked_player_ids: frozenset[str]
    #: Players under a live hold. Fails **closed**, and points both ways — the
    #: searcher's own hold is refused at the entry point, before this is built.
    held_player_ids: frozenset[str]
    #: ``users`` says these may not be shown. Candidate-side only, fails
    #: **closed** (``docs/adr/0124``).
    unshowable_player_ids: frozenset[str]
    #: Whom the searcher already has an open challenge with. Fails **soft** —
    #: the backend re-verifies returned rows anyway, so this is embarrassment
    #: with a backstop rather than a safety failure.
    open_challenge_ids: frozenset[str]


@final
@dataclass(frozen=True, slots=True)
class LiveTermFacts:
    """The reads a term or a Liveness signal stands down without. All **soft**.

    Held apart from :class:`LiveGateFacts` because the postures differ and the
    difference is the module's central rule: *a gate that cannot be evaluated
    excludes; a term that cannot be evaluated stands down.* One bag holding both
    would make the strictest fact's failure mode everybody's.
    """

    #: The searcher's pairwise history, at most 500 counterparts, newest first.
    counterparts: Mapping[UUID, PairwiseCounterpart]
    #: How full each candidate's inbox is. Advisory, and today every count is a
    #: measured zero.
    open_challenge_counts: Mapping[UUID, int]
    #: The six reliability strands, for the players who have them. A player with
    #: no record is **absent**, never a zero.
    player_scores: Mapping[UUID, PlayerScoreReading]
    #: How often each candidate has been shown this week, in this sport.
    times_shown: Mapping[UUID, int]
    #: What *shown more often than most* means this week, or ``None`` when no
    #: roll has published one yet.
    busy_threshold: int | None


@final
@dataclass(frozen=True, slots=True)
class SearchContext:
    """One search's whole world, assembled at entry and never added to."""

    searcher: SearcherFacts
    surface: SearchSurface
    #: Orthogonal to the surface, and the reason there are two columns rather
    #: than one: an engine-pushed deck card is ``DECK`` + ``ENGINE``.
    initiation: SearchInitiation
    now: datetime
    snapshot: CandidateSnapshot
    gates: LiveGateFacts
    terms: LiveTermFacts
    ruleset: Ruleset
    #: The terms whose provider does not exist **on this platform**, as opposed
    #: to for this person. The evidence gate counts person-specific gaps and
    #: never platform-wide absence — a fact nobody has about anybody cannot be
    #: evidence this person failed to produce — and the difference is decided in
    #: the composition root, because *no provider exists* is a fact about the
    #: wiring rather than about the numbers.
    absent_terms: frozenset[Term]

    @property
    def today(self) -> IsoWeekday:
        """Which day of the week this search is running on.

        Derived from ``now`` rather than carried beside it, so a context whose
        weekday disagreed with its instant cannot be built. It is the one time
        fact the engine and the window derivation are both given — neither a date
        nor a timezone, which is what keeps the availability grid's own negative
        space intact.
        """

        return iso_weekday(self.now.isoweekday())

    @property
    def box(self) -> BoundingBox:
        """The rectangle generation reads. Derived from the searcher's own ask.

        Derived rather than stored, so there is no way to hold a context whose
        box disagrees with the radius beside it. Generation reads it **once**,
        into a local, because it is consulted per candidate row.
        """

        return bounding_box(self.searcher.area, float(self.searcher.radius_km))
