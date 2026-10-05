"""One row of the candidate index, and the partition it is searched in.

**The invariant that governs every column here, and every column anybody adds
later** (``docs/adr/0111``):

> **The index holds only facts a player changes about themselves. Every fact
> that must be live is never in it.**

It is the read-side counterpart of *a gate may be honestly empty; a term may
never be honestly neutral*, and the test a future column is put to is not *is
this expensive to project* but *would being two seconds wrong about this hurt
somebody*. Blocks, holds, pairwise history, the open-challenge set and account
status are therefore not columns and never will be — they travel in the search
context and the backend re-verifies what comes back (``docs/adr/0095``,
``docs/adr/0098``, ``docs/adr/0109``, ``docs/adr/0124``).

**Identity is ``(player_id, sport)``** — never ``(player, sport, area)``
(``docs/adr/0101``). The row holds a *set* of area references, size one today, so
a row reachable from two cells at trigger 4 costs a pointer rather than a
duplicate row.

**Three properties are asserted by a walk rather than by this docstring**, in
``tests/unit/test_candidate_row_fence.py``:

1. **No shard-key field.** The partition is *derived* (``partition_of`` below), so
   there is no field for a future matching conjunct to attach itself to.
2. **No name, photo, email, date of birth, nationality or precise location.**
   Gender **is** here and is fenced one layer out: it reaches candidate
   generation and the mutual gate and is absent from the type handed to
   ``app/engines/matchfit/`` (``docs/adr/0096``). The area is coarse *by
   construction* — ``IndexedArea`` refuses a fix finer than the platform keeps —
   rather than by a word nobody may spell.
3. **No reference cycles.** ``slots=True``, primitive fields, no back-pointer to
   the container. That is what makes ``gc.freeze()`` safe (``docs/adr/0112``):
   one automatic gen-2 collection over a live index cost **57.9 ms
   stop-the-world**, ~30× the search it interrupted, and freezing is only safe if
   the frozen objects cannot become unreachable garbage. Refcounting frees an
   outgoing row the moment the last container drops it — a property, not a hope.

Measured at **2 016 bytes a row** as ``__slots__`` objects, held once per gunicorn
worker — ``docs/research/bench/matcher-scale/candidate_row_bench.py``, which
measures *this* type by importing it. The 782 that stood here until #276 was a
real measurement of ``matchmaking-engine.md`` §7.2's row, which packs the grid
and the tags into two ``int`` bitmasks and keeps the area as three scalars; this
row holds two tuples of strings and a tuple of ``IndexedArea``, and it has never
had the other shape. #276 measured it at 1 991; the 25 on top is the intro
(``docs/adr/0170``), a slot on every row and a line on the cohort's share of
them. Half of it is vocabulary strings the projection copies per row rather than
shares — which is a fact about the projection, and is argued where the
projection is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import final

from app.kernel import Sport, invariant
from app.modules.player_profile.domain.location import LOCATION_PRECISION_DP


@final
@dataclass(frozen=True, slots=True)
class IndexedArea:
    """A coarse place, and the **only** place this index is able to hold.

    The two degrees are the area's centroid at the platform's own precision —
    ``LocationArea.around`` discards the precise fix at the boundary, and there is
    no version of any stream from which one could be recovered. The refusal below
    is what makes *no precise location on an index row* a property of the type
    rather than a word on a forbidden list: a caller that has a device fix cannot
    put it here, whatever they call the field.

    There is no area **code** on it, and its absence is deliberate. The coarse
    centroid is what the bounding box reads and it is the only spatial truth the
    index has; the human-readable area a player card prints is assembled outside
    the engine (``docs/adr/0107``) and has no producer in this repository yet.
    Deriving one here would be inventing a naming scheme nobody has calibrated —
    the mistake ``the-candidate-index.md`` §8 refuses for the geo cell, for the
    same reason.
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        for axis, degrees in (
            ("latitude", self.latitude),
            ("longitude", self.longitude),
        ):
            invariant(
                round(degrees, LOCATION_PRECISION_DP) == degrees,
                f"a {axis} finer than the coarse area this platform keeps: {degrees}",
            )


@final
@dataclass(frozen=True, slots=True)
class CandidateRow:
    """One ``(player, sport)`` pair, as the index holds it.

    Every field is a fact the player changes about themselves, or the stamp that
    says how far the log has been folded into it. Read the module docstring
    before adding one.

    **A player id is a string here and not a ``UUID``.** It becomes the engine's
    ``player_id`` unchanged, ties break on it ascending (``docs/adr/0105``), and a
    string compares in a stable order with no clock and no hash seed behind it.
    """

    player_id: str
    #: The sport, as ``Sport.value``. A machine code rather than the enum member,
    #: because an enum member holds a reference to its own class and its class
    #: holds its members — a cycle, on the one type whose freedom from cycles is
    #: what makes ``gc.freeze()`` safe.
    sport: str

    # --- what `rating` published (`rating.rating_initialised`)
    mu: float
    sigma: float
    confidence: int
    #: The **likely range** — μ ± σ clamped to the scale — as ``rating``
    #: published it, and the pair a card prints beside the Level so that a
    #: reader can see how sure the platform is and not only what it thinks.
    #:
    #: **Projected, never derived.** ``likely_range()`` returns *unrounded*
    #: values and the rounding lives in the engine, so a consumer that computed
    #: μ ± σ here would own a rounding rule for a number somebody else
    #: publishes — the second-source-of-truth defect ``band_lower`` /
    #: ``band_upper`` being projected rather than derived already settled once.
    range_low: float
    range_high: float
    #: The Level band's published name. Spelled ``band`` rather than
    #: ``band_name`` so that no field on this row names a *name* — see the fence.
    band: str
    band_lower: float
    band_upper: float
    rating_status: str
    calibration_priority: str

    # --- what the player declared about this sport
    #: ``None`` when they have not declared. Not declaring stands the intent term
    #: down; it is not a third value of the intent vocabulary.
    declared_intent: str | None

    # --- what the player declared about themselves
    social_tags: tuple[str, ...]
    tags_updated_at: datetime
    #: The line they wrote about themselves, or ``None`` where they wrote none
    #: (``docs/adr/0170``). **The one text field on this row, and it reaches
    #: the card and never the scorer**: ``fence.py`` does not copy it onto a
    #: ``ScorableCandidate``, and the scorer's fence refuses the word. Held here
    #: for the reason the tags are — a fact a player changes about themselves,
    #: read on the one surface that shows one person at a time.
    intro: str | None
    #: The player's weekly hours, as ``WeeklyHour.code`` writes them —
    #: ``"2:19"``. The column keeps its older name, ``availability``, because it
    #: is a projection rebuilt from the log and a rename would be a migration
    #: bought for a word. Empty is *we do not know when they play* — absent,
    #: never a zero (ADR-0102).
    availability: tuple[str, ...]
    grid_updated_at: datetime
    #: Size one today. A *set*, so a row reachable from two cells at trigger 4
    #: costs a pointer rather than a duplicate row (``docs/adr/0101``).
    areas: tuple[IndexedArea, ...]
    search_radius_km: int
    #: ``None`` for a profile committed before the question existed.
    proposals_opt_in: bool | None
    #: ``None`` is *nobody was asked* and is emphatically not a quieter
    #: ``PREFER_NOT_TO_SAY`` (``docs/adr/0096``).
    gender: str | None
    gender_preference: str
    #: The moment onboarding ended. The newcomer window is ``now −
    #: profile_created_at < 14 d``, computed where it is read: **a date, never a
    #: flag**, because a stored ``is_newcomer`` boolean goes stale hourly and a
    #: date never does (``the-newcomer-path.md`` §1).
    profile_created_at: datetime
    #: *Last session refresh*, projected from ``auth.refresh_token_issued`` and
    #: ``auth.refresh_token_rotated`` against a 24-hour token lifetime — so it
    #: **resolves days, not hours**, and Liveness reads it as *this week* …
    #: *dormant* rather than *active now* (``docs/adr/0111``). ``None`` for a
    #: player who has never refreshed a session.
    last_active_at: datetime | None

    #: How far the log has been folded into this row. It is what a delta refresh
    #: reads to know the row moved (``docs/adr/0112``), and what makes an
    #: out-of-order repair provably safe.
    applied_through_sequence_no: int

    def __post_init__(self) -> None:
        invariant(bool(self.player_id), "a candidate row with no player")
        invariant(bool(self.sport), "a candidate row with no sport")
        invariant(self.sigma >= 0.0, f"a negative Uncertainty: {self.sigma}")
        invariant(
            self.range_low <= self.range_high,
            f"a likely range that runs backwards: {self.range_low}–{self.range_high}",
        )
        invariant(
            self.search_radius_km > 0,
            f"a search radius of {self.search_radius_km} km",
        )
        invariant(bool(self.areas), "a candidate row reachable from nowhere")
        invariant(
            len(set(self.areas)) == len(self.areas),
            "a candidate row holding one area twice",
        )


@final
@dataclass(frozen=True, slots=True)
class Partition:
    """Which container a row is searched in. **Derived, never stored.**

    ``(sport)`` today and ``(sport, cell)`` at trigger 4 (``docs/adr/0101``), so
    the shape survives that day without a rewrite — generation is
    ``sport ∧ box ∧ gates`` and a search never spans two sports, so the split
    costs nothing.

    It is a *type*, and there is deliberately no partition **column**. A stored
    key is a field a future matching conjunct can attach itself to, and the day it
    does, *who you are shown* starts depending on how the data happens to be
    laid out. The cell size is not chosen here either: it is calibrated against a
    real population's clustering and trigger 4 is ~25 000 players away.
    """

    sport: str

    @classmethod
    def for_sport(cls, sport: Sport) -> "Partition":
        return cls(sport=sport.value)


def partition_of(row: CandidateRow) -> Partition:
    """The partition this row belongs to, computed from the row itself."""

    return Partition(sport=row.sport)
