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

from datetime import datetime
from enum import Enum
from typing import final

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset
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
    """The mutual gate, over an index row inside a running search."""

    return gender_satisfied(
        searcher_gender=context.searcher.gender,
        searcher_preference=context.searcher.gender_preference,
        theirs=row,
    )


def gender_satisfied(
    *,
    searcher_gender: Gender | None,
    searcher_preference: GenderPreference,
    theirs: CandidateRow | None,
) -> bool:
    """Both preferences, both directions. **Closed, and told to nobody.**

    Absence is not a quieter ``PREFER_NOT_TO_SAY``: a preference that *needs* a
    gender and does not have one is a gate that could not be evaluated, and a
    gate that cannot be evaluated excludes. A pair who both ask for anybody never
    reads a gender at all, which is why an unanswered question costs nothing
    until somebody's safety setting depends on it.

    It takes the searcher's two facts and the other side's **row** rather than a
    whole ``SearchContext``, because the same gate is evaluated in two places —
    inside a search, and again when a stored search is read back an hour later
    (``docs/adr/0109``) — and a second implementation of a mutual safety gate is
    exactly the thing that ends up satisfied in one place and not the other.

    ``theirs`` is ``None`` when the index holds no row for that player at all,
    which is a gate that **cannot be evaluated** and therefore excludes.
    """

    if theirs is None:
        return False
    preference = _preference(theirs.gender_preference)
    if preference is None:
        return False
    return _satisfies(searcher_preference, _gender(theirs.gender)) and _satisfies(
        preference, searcher_gender
    )


def gender_satisfied_between(one: CandidateRow, other: CandidateRow) -> bool:
    """The mutual gate over **two candidates** — the pairs no searcher is in.

    ``docs/adr/0116``: a four contains six pairs and the searcher is in three of
    them, so the other three are gated against nobody unless this exists.
    ADR-0096 chose mutuality precisely so a one-directional filter would not
    *"leave a woman open to every man who searched ``ANY``"*, and under a
    searcher-only gate she is open to every man a **third party** seats beside
    her.

    It reads the same two fields through the same two readers as
    :func:`gender_satisfied` and applies the same asymmetry between them — an
    unreadable *answer* is an absence, an unreadable **preference** is a safety
    setting that cannot be evaluated, and *a gate that cannot be evaluated
    excludes*. Written as its own function rather than by feeding one row in
    where a searcher goes, because the searcher's own gender arrives live from
    the profile and a candidate's arrives off an index row, and a signature that
    accepted either would be one a caller could pass the wrong one to.
    """

    mine = _preference(one.gender_preference)
    theirs = _preference(other.gender_preference)
    if mine is None or theirs is None:
        return False
    return _satisfies(mine, _gender(other.gender)) and _satisfies(
        theirs, _gender(one.gender)
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
    """The level gate for the one pair a shortlist is about: searcher, candidate."""

    return level_close_enough(
        mu_a=context.searcher.mu,
        mu_b=row.mu,
        a_created_at=context.searcher.profile_created_at,
        b_created_at=row.profile_created_at,
        mode=context.searcher.mode,
        ruleset=context.ruleset,
        now=context.now,
    )


def level_close_enough(
    *,
    mu_a: float,
    mu_b: float,
    a_created_at: datetime,
    b_created_at: datetime,
    mode: SearchMode,
    ruleset: Ruleset,
    now: datetime,
) -> bool:
    """``|Δμ| < LEVEL_TOL``, at the tolerance the curve itself saturates at.

    **Newness changes the gate, never the weights** (``docs/adr/0113``). While
    **either side** of the pairing is inside its newcomer window the tolerance is
    the competitive one in both modes — it binds the *pairing* and not the
    search, because gating only the newcomer's own search leaves the bad first
    game arriving through the veteran's list. No constant is introduced: the
    tighter number is the one the competitive mode already carries.

    **It takes two people and not a searcher and a row**, which is what makes
    the rule survive into a four. ``docs/adr/0116`` binds every gate across all
    **six** pairs of a line-up, and carries this tolerance with it — *every pair
    containing a newcomer takes ``LEVEL_TOL_COMP``, whoever ran the search* —
    and the three cross pairs contain no searcher at all. A gate written against
    a ``SearchContext`` could only ever answer for the three pairs the searcher
    is in, which is precisely the hole ADR-0113 was written to close, reopened
    one enumeration later. So the pair is the argument, here, before there is a
    line-up to get it wrong.
    """

    tolerance = ruleset.modes[mode].level_tolerance
    if is_new_at(a_created_at, now) or is_new_at(b_created_at, now):
        tolerance = min(
            tolerance, ruleset.modes[SearchMode.COMPETITIVE].level_tolerance
        )
    return abs(mu_a - mu_b) < tolerance
