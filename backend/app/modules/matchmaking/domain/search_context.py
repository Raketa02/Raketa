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
from app.modules.matchmaking.domain.areas import area_code_of
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.geography import BoundingBox, Point, bounding_box
from app.modules.matchmaking.domain.ports import PairwiseCounterpart, PlayerScoreReading
from app.modules.matchmaking.domain.searches import SearchInitiation, SearchSurface
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent

#: The terms the deck declines to read, for every pairing (``docs/adr/0169``
#: §2). One today: under one ruler for everybody, a candidate who declared
#: *competitive* would otherwise lose the intent term's whole weight for wanting
#: a different evening than the ruler assumes, and one who declared *for fun*
#: would be paid for agreeing with a vector the viewer never chose. So the term
#: stands down on the deck — its weight renormalises away by the mechanism a term
#: already uses when it has nothing to read — and a declaration moves nobody, up
#: or down. Find a game is untouched: its mode still selects its vector and the
#: term still reads.
#:
#: Declared here rather than in ``deck.py`` because the fact rides on the
#: **context** — ``score_all`` and the reciprocal read both ask it, and each
#: surface's terminal stage calls those without knowing which surface it is.
STOOD_DOWN_ON_THE_DECK: frozenset[Term] = frozenset({Term.INTENT_ALIGNMENT})

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


def is_new_at(profile_created_at: datetime, now: datetime) -> bool:
    """Whether a profile committed then is still inside its newcomer window.

    **A date, never a flag**, and one reading of it: the searcher's side, the
    candidate's side and the level gate's *either side* all ask here, so a change
    to what *new* means cannot land on two of the three.

    **The window has two halves and only one of them is readable today.** *New
    until their first game* is the definition and reads ``matches``, which does
    not exist — there is no counted game anywhere in this backend, so the half is
    **inert** rather than stubbed. *Never longer than fourteen days* is the
    ceiling and reads ``profile_created_at``, which every index row and every
    profile carries, so it is live from build one.

    The ceiling is what makes the window terminate while the definition cannot be
    read, and it is deliberately **not** the definition: a player fourteen days
    in who has played nothing still leaves the window, and falls back on the
    exposure floor, which lifts anybody shown zero times this week
    (``the-newcomer-path.md`` §8). A window that extended while unused would be a
    permanent subsidy for the players the engine knows least about.

    Nothing here stands in for the missing half. A default of *they have played
    nobody* would be true, and would also be the invented measurement this map
    refuses everywhere else — the ceiling already bounds the subsidy, so the
    absent half costs the product nothing until ``matches`` lands and can shorten
    it honestly.
    """

    return now - profile_created_at < NEWCOMER_WINDOW


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
    #: what its 409 checks. **``None`` only on the deck**, which reads no
    #: declaration and refuses nobody for lacking one (``docs/adr/0169`` §2) —
    #: it records the declaration as it stood, and for a viewer who never
    #: declared, as it stood is nothing.
    declared_intent: PlayIntent | None
    profile_created_at: datetime

    def __post_init__(self) -> None:
        invariant(self.radius_km > 0, f"a search radius of {self.radius_km} km")
        invariant(self.sigma >= 0.0, f"a negative Uncertainty: {self.sigma}")

    def is_new_at(self, now: datetime) -> bool:
        """Whether the searcher is still inside their newcomer window."""

        return is_new_at(self.profile_created_at, now)

    @property
    def area_code(self) -> str:
        """This searcher's coarse area, as the code the wire spells areas in.

        Here rather than at the three call sites that record it, because it is
        the same derivation the candidate's own card already makes and one of
        them silently reaching for a different function is how the two codes on
        a card stop being comparable.
        """

        return area_code_of(self.area)


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
    #: Challenge-deep today — who accepted and who declined — because ``matches``
    #: is unwritten, so ``PLAYED`` is empty **by construction** and familiarity
    #: stands down rather than firing at zero strength on every card.
    counterparts: Mapping[UUID, PairwiseCounterpart]
    #: How many seats are waiting on each candidate's answer, across every sport.
    #: Advisory, and a zero is measured: the seats were counted and none of them
    #: was theirs.
    open_challenge_counts: Mapping[UUID, int]
    #: The six reliability strands, for the players who have them. A player with
    #: no record is **absent**, never a zero.
    player_scores: Mapping[UUID, PlayerScoreReading]
    #: How often each candidate has been shown this week, in this sport.
    times_shown: Mapping[UUID, int]
    #: Which of these candidates said *Let's play* to the searcher, and how many
    #: days ago. **Only the ones who did are named**, so absence is *they said
    #: nothing* rather than a zero — a zero here would be a yes sent today.
    #:
    #: It is the one read in this bag that can **admit** somebody: an interest
    #: lift outranks the engine's opinion and may sit below the quality floor
    #: with its reason printed (``docs/adr/0099`` as amended). The other two
    #: lifts reorder. That is also why it is read from a durable row rather than
    #: a ledger with a TTL — the two beside it may be lost, and losing this one
    #: would silently take a person out of a list they were guaranteed.
    interest_days_ago: Mapping[UUID, int]
    #: How often each candidate has been volunteered into a **newcomer's**
    #: shortlist this week, in this sport — ``NEWCOMER_ABSORPTION_CAP``'s tally.
    #:
    #: **Empty on every search a newcomer did not run**, and that is the read not
    #: being taken rather than a bucket that came back quiet: the cap bounds the
    #: ask, so the only search it can bind in is one that is itself adding to
    #: somebody's absorption. :func:`absorption_tally` is where the two are told
    #: apart, once, so no reader has to remember which emptiness it is holding.
    newcomer_appearances: Mapping[UUID, int]
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
    def stood_down_terms(self) -> frozenset[Term]:
        """The terms **this search** does not read, for every pairing.

        A fact about the surface and never about a person or the platform:
        ``absent_terms`` beside it is what the wiring lacks, and a term function
        reports what a pairing lacks. This is the third kind — the search
        declining to ask — and it is derived from the surface so a context
        cannot be built saying one thing about its surface and another about
        which terms it reads.
        """

        if self.surface is SearchSurface.DECK:
            return STOOD_DOWN_ON_THE_DECK
        return frozenset()

    def absorption_tally(self, player_id: UUID) -> int | None:
        """How often this candidate has been volunteered into a newcomer's list.

        ``None`` — *there is nothing to bound* — on every search a newcomer did
        not run, which is where the difference between the cap's two emptinesses
        is drawn. A zero would say *we counted and they have absorbed nothing*,
        and past a cap of one that is a different sentence.

        Read by stage 4 alone. The cap bounds how often an **experienced** player
        is volunteered into newcomers' lists, so it binds the welcoming record —
        the thumb that selects those players — and never the newcomer lift, which
        is a subsidy for the other side of the same pairing.
        """

        if not self.searcher.is_new_at(self.now):
            return None
        return self.terms.newcomer_appearances.get(player_id, 0)

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
