"""Stage 1 — the ten hard exclusions, and the one rule they all obey.

**A gate that cannot be evaluated excludes; a term that cannot be evaluated
stands down** (``docs/adr/0095``). The test for a fact whose provider does not
exist is whether a zero would be **measured** or **invented**: nobody can be held
because nothing can hold anybody, so the hold gate ships true-over-empty and its
zero is real.

**No relaxation reaches a gate, at any rung, ever** (``docs/adr/0099``). There is
no argument to :func:`gate_of` that could carry one, and there is no rung
parameter to add — a rung may relax something the searcher asked for, and a gate
is not an ask.

**The roster is closed and enumerated once.** ``excluded_by_gate`` is a histogram
over exactly these ten codes, and a candidate excluded by two of them is counted
under the **first in declaration order** — stated here rather than discovered,
because a histogram whose keys depend on evaluation order is a histogram nobody
can compare across releases.

**Gender is a gate and never a score.** It is applied in **both directions**, it
fails **closed**, it is explained to its owner and revealed to nobody else, and
nothing on any screen reveals how many people it hid. That last part is why the
pool description the client receives is the **post-gate** count: a pre-gate count
beside a post-gate one is the delta, per searcher, which is precisely what a
mutual gate must never be readable as.

**A blank availability grid is not a gate and never was** (``docs/adr/0102``). It
means *we do not know*, and the availability term stands down.
"""

from __future__ import annotations

from enum import Enum
from typing import final

from app.engines.matchfit.core import SearchMode
from app.modules.matchmaking.domain.candidate_index import CandidateRow
from app.modules.matchmaking.domain.search_context import (
    SearchContext,
    is_new_at,
)
from app.modules.matchmaking.domain.searches import SearchInitiation
from app.modules.player_profile.domain.gender import Gender, GenderPreference


@final
class GateCode(str, Enum):
    """The ten, in the order they are evaluated and counted.

    Eight are the input document's; ``GENDER_PREFERENCE`` and ``LEVEL`` were
    added by ``docs/adr/0096`` and ``docs/adr/0103``. The eleventh exclusion the
    input document had — withholding a player at eight open challenges — is
    **deleted**: it is a Liveness sink now, because when there is nobody else,
    showing the busy person beats showing nobody.
    """

    #: Either direction, live, never the index. Fails **closed**.
    BLOCKED = "BLOCKED"
    #: Both ways. A held *searcher* is refused at the entry point rather than
    #: hidden from others, so what reaches here is the candidate side. Fails
    #: **closed**.
    HELD_ACCOUNT = "HELD_ACCOUNT"
    #: No rating for this sport. Read off the index row.
    NOT_RATED = "NOT_RATED"
    #: Outside the searcher's own ring. Their ask, so a filter — and it is the
    #: **circle**, not the bounding box that admitted the row.
    OUTSIDE_RADIUS = "OUTSIDE_RADIUS"
    #: An open challenge already stands between you. Fails **soft**: the backend
    #: re-verifies the returned rows anyway.
    OPEN_CHALLENGE = "OPEN_CHALLENGE"
    #: Missing or unapproved photo. **Live and inert** — see :func:`_photo`.
    PHOTO = "PHOTO"
    #: Proposals opt-in explicitly ``false``. **Gates the push, not the person**:
    #: it reads ``initiation`` and never ``surface``.
    PROPOSALS_OPT_OUT = "PROPOSALS_OPT_OUT"
    #: ``users`` says this account may not be shown. Candidate-side only, fails
    #: **closed**, and told to nobody.
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    #: The two gender preferences, mutually satisfied. Fails **closed**.
    GENDER_PREFERENCE = "GENDER_PREFERENCE"
    #: ``Δμ < LEVEL_TOL_mode`` — **the same number the curve uses**, so the gate
    #: and the curve cannot drift apart.
    LEVEL = "LEVEL"


#: The roster, as data. The histogram's key set is this and never *the codes
#: somebody remembered*, so a gate added without a column is a red test rather
#: than a silent hole in the denominator.
GATE_ROSTER: tuple[GateCode, ...] = tuple(GateCode)


def gate_of(
    row: CandidateRow, context: SearchContext, *, distance_km: float
) -> GateCode | None:
    """Which gate excludes this candidate, or ``None`` if none does.

    ``distance_km`` is passed in rather than measured here because the caller has
    already measured it to reject against the bounding box, and measuring it
    twice is the kind of duplication that ends with two answers.

    The order below **is** :class:`GateCode`'s declaration order, and the
    telemetry counts the first that fires.
    """

    searcher = context.searcher
    player_id = row.player_id
    if player_id in context.gates.blocked_player_ids:
        return GateCode.BLOCKED
    if player_id in context.gates.held_player_ids:
        return GateCode.HELD_ACCOUNT
    if row.sport != searcher.sport.value or not row.rating_status:
        return GateCode.NOT_RATED
    if distance_km > float(searcher.radius_km):
        return GateCode.OUTSIDE_RADIUS
    if player_id in context.gates.open_challenge_ids:
        return GateCode.OPEN_CHALLENGE
    if _photo(row):
        return GateCode.PHOTO
    if context.initiation is SearchInitiation.ENGINE and row.proposals_opt_in is False:
        return GateCode.PROPOSALS_OPT_OUT
    if player_id in context.gates.unshowable_player_ids:
        return GateCode.ACCOUNT_INACTIVE
    if not _gender_satisfied(row, context):
        return GateCode.GENDER_PREFERENCE
    if not _level_close_enough(row, context):
        return GateCode.LEVEL
    return None


def _photo(row: CandidateRow) -> bool:
    """Whether the photo gate excludes this candidate. **It never does today.**

    Enumerated, counted and inert, which is the state
    [`the-engine.md`](../../../../../docs/specs/matchmaking/the-engine.md) §3
    records for it — and the inertness is structural rather than a stub anybody
    can flip. Neither half of *missing or unapproved* has a search-time provider:

    - **Unapproved** has no producer anywhere in this repository. ``PhotoReview``
      soft-warns and **fails open** (``docs/adr/0129``), and no verdict is stored
      against a player, so nothing here can say a photo was refused.
    - **Missing** is deliberately absent from the index. ``candidate_projection``
      refuses ``player_profile.photos_changed`` by name, and adding a column is a
      change to what ``docs/adr/0111`` lets the index hold — which belongs to
      [#181](https://github.com/Raketa02/Raketa/issues/181), not to a search.

    It is written as a function rather than folded away so that the gate has a
    place to bind on the day it can, and so the roster stays ten rather than
    quietly becoming nine.
    """

    return False


def _gender_satisfied(row: CandidateRow, context: SearchContext) -> bool:
    """Both preferences, both directions. **Closed, and told to nobody.**

    Absence is not a quieter ``PREFER_NOT_TO_SAY``: a preference that *needs* a
    gender and does not have one is a gate that could not be evaluated, and a
    gate that cannot be evaluated excludes. A pair who both ask for anybody never
    reads a gender at all, which is why an unanswered question costs nothing
    until somebody's safety setting depends on it.
    """

    searcher = context.searcher
    theirs = _preference(row.gender_preference)
    if theirs is None:
        return False
    return _satisfies(searcher.gender_preference, _gender(row.gender)) and _satisfies(
        theirs, searcher.gender
    )


def _satisfies(preference: GenderPreference, gender: Gender | None) -> bool:
    if preference is GenderPreference.ANY:
        return True
    if preference is GenderPreference.WOMEN_ONLY:
        return gender is Gender.WOMAN
    return gender is Gender.MAN


def _gender(code: str | None) -> Gender | None:
    """The candidate's answer, or ``None`` for a code this build does not serve.

    An unrecognised code reads as *no answer* rather than raising: the index is a
    fold of a log that outlives this deployment, and a search refusing outright
    because one row holds a value from a later vocabulary would take the whole
    city down for one player's profile.
    """

    return Gender(code) if code in Gender.__members__ else None


def _preference(code: str) -> GenderPreference | None:
    """The candidate's own preference, or ``None`` for a code this build cannot read.

    The asymmetry with :func:`_gender` is deliberate and is the same rule seen
    from the other side. An unreadable *answer* is an absence, and an absence is
    only fatal to a preference that needed it; an unreadable **preference** is a
    safety setting we cannot evaluate at all, and *a gate that cannot be
    evaluated excludes*. So this answers ``None`` rather than guessing a
    restrictive value — a guess would be satisfied by whoever happened to match
    it, which is the failure wearing the shape of a fix.
    """

    return GenderPreference(code) if code in GenderPreference.__members__ else None


def _level_close_enough(row: CandidateRow, context: SearchContext) -> bool:
    """``|Δμ| < LEVEL_TOL``, at the tolerance the curve itself saturates at.

    **Newness changes the gate, never the weights** (``docs/adr/0113``). While
    **either side** of the pairing is inside its newcomer window the tolerance is
    the competitive one in both modes — it binds the *pairing* and not the
    search, because gating only the newcomer's own search leaves the bad first
    game arriving through the veteran's list. No constant is introduced: the
    tighter number is the one the competitive mode already carries.
    """

    ruleset = context.ruleset
    tolerance = ruleset.modes[context.searcher.mode].level_tolerance
    if _either_is_new(row, context):
        tolerance = min(
            tolerance, ruleset.modes[SearchMode.COMPETITIVE].level_tolerance
        )
    return abs(row.mu - context.searcher.mu) < tolerance


def _either_is_new(row: CandidateRow, context: SearchContext) -> bool:
    return is_new_at(row.profile_created_at, context.now) or (
        context.searcher.is_new_at(context.now)
    )
