"""Turning what the engine returned into what the record stores.

**Storage stays open where the wire is closed** (``docs/adr/0106``). The
``terms`` blob has to deserialise in five years under a ruleset nobody runs any
more, so it is a plain mapping stamped with ``ruleset_version`` rather than a
schema; the wire type has to be exhaustive *today*, and it is a discriminated
union in ``presentation/evidence.py``. Openness is the right property for the
first and the wrong one for the second, and this module is the seam.

**``liveness_signals`` stores the raw inputs and never the offset.** The offset
is a function of the ruleset's bounds, so storing it would make a bounds change
undiffable — a replay could not re-derive under new bounds what it only has the
old bounds' answer to. For the interest signal the raw input is the **age of the
yes in days**, never the boolean: the ``+14`` is flat, so a boolean would be the
*sufficient* input and the age — the entire x-axis of *acceptance by age of yes*
— would be lost to a Redis TTL within the month.

**``degraded_terms`` is lifted out of the blob** by the caller, so that a
per-term ``NoEvidence`` rate is an array query rather than a blob scan. A term
quietly dying is invisible otherwise.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from app.engines.matchfit.core import LivenessSignal
from app.engines.matchfit.ranking import Liveness, ModifierStack
from app.engines.matchfit.scoring import Fit
from app.modules.matchmaking.domain.shortlist import Scored


def term_rows(fit: Fit) -> tuple[Mapping[str, Any], ...]:
    """Every term that fired, with its weight, value, contribution and evidence.

    The **renormalised** weight, because that is the share of a hundred this term
    actually held in this comparison — and a stored contribution that did not
    reconcile with its own weight and value would be a breakdown nobody could
    check a year later.
    """

    return tuple(
        {
            "term": scored.term.value,
            "weight": scored.weight,
            "value": scored.value,
            "contribution": scored.contribution,
            "evidence": evidence_payload(scored.evidence),
        }
        for scored in fit.terms
    )


def modifier_rows(stack: ModifierStack) -> tuple[Mapping[str, Any], ...]:
    """The budgeted modifiers, and the dock that sits outside the budget.

    The dock is recorded **in the same list** and flagged apart on its own two
    columns, because what a reader of one row wants is *what moved this number*.
    Nothing sums this list: the budget was applied by the type that produced it,
    and ``ModifierStack.applied`` is the only total anybody may read.
    """

    fired = tuple(
        {"code": entry.modifier.value, "points": entry.points}
        for entry in stack.fired
    )
    if stack.floor_breach is None:
        return fired
    return fired + (
        {
            "code": stack.floor_breach.modifier.value,
            "points": stack.floor_breach.points,
        },
    )


def liveness_reason_codes(liveness: Liveness | None) -> tuple[str, ...]:
    """The printable reasons, ranked by how far each moved them.

    A **silent** signal is absent by construction: ``Silent`` carries points and
    no code, so there is no name on the value to print. The full inbox prints its
    coarse rung rather than its own name — *they have a lot on* is the whole of
    what a searcher is owed about a third party's unanswered mail, and the count
    is theirs.
    """

    if liveness is None:
        return ()
    return tuple(_reason_code(move.signal, move.load) for move in liveness.reasons)


def liveness_signal_inputs(row: Scored) -> Mapping[str, Any]:
    """The raw input per signal — **never the offset it produced.**

    Empty for a near-miss row, where stage 6 never ran: an empty mapping says
    *no signal was read*, which is true, where a mapping of nulls would claim ten
    measurements that all came back empty.
    """

    facts = row.liveness_facts
    if facts is None:
        return {}
    inputs: dict[str, Any] = {
        LivenessSignal.INTEREST_RECEIVED.value: facts.interest_days_ago,
        # Two raw inputs, because two produce the lift: the window, and the
        # absorption tally the cap drops it on. Storing only the window would
        # make a cap change undiffable in exactly the way storing the offset
        # would make a bounds change undiffable, and the tally is also the
        # x-axis of the cap's own falsifier.
        #
        # It is the one key whose shape has changed — a bool became a mapping —
        # and the blob is open precisely so that it can (`docs/adr/0106`). The
        # alternative was a second top-level key, which would have made the
        # mapping's key set something other than the signal roster, and that
        # roster is what makes *a signal is never read* a checkable claim.
        LivenessSignal.NEWCOMER_LIFT.value: {
            "newcomer": facts.newcomer,
            "newcomer_appearances": facts.newcomer_appearances,
        },
        LivenessSignal.PREVIOUS_ACCEPT.value: facts.previously_accepted,
        LivenessSignal.PREVIOUS_DECLINE.value: facts.previously_declined,
        LivenessSignal.ANSWER_RATE_AND_SPEED.value: facts.answer_rate,
        LivenessSignal.RECENT_ACTIVITY.value: facts.recent_activity,
        LivenessSignal.OVERLAP_PROXIMITY.value: facts.overlap_proximity,
        LivenessSignal.CHALLENGE_LOAD.value: facts.open_challenges,
        LivenessSignal.EXPOSURE_ADJUSTMENT.value: facts.exposure,
    }
    reciprocal = row.reciprocal
    inputs[LivenessSignal.RECIPROCAL_ASYMMETRY.value] = (
        None
        if reciprocal is None
        else {
            "fit_ab": reciprocal.fit_ab,
            "fit_ba": reciprocal.fit_ba,
            "mode": reciprocal.mode.value,
        }
    )
    return inputs


def _reason_code(signal: LivenessSignal, load: object | None) -> str:
    """One printable signal's code, as the wire spells it.

    The full inbox is the one signal whose code is not its own name: its three
    rungs each name their own code in the ruleset, so a threshold moving does not
    silently re-point a code at a different depth. It is prefixed with the
    signal so the vocabulary stays one flat closed set rather than two that a
    client has to know to merge.
    """

    if load is None:
        return signal.value
    return f"{signal.value}_{getattr(load, 'value', load)}"


def evidence_payload(evidence: Any) -> Mapping[str, Any]:
    """One evidence variant as a mapping, with its ``kind`` first.

    ``asdict`` walks the frozen dataclasses the engine emits, and enums are taken
    down to the machine codes they already are — the stored blob has to be
    readable by something that does not import this build's enums.

    **One serialiser, two consumers.** The record stores this mapping and the
    wire schema validates the same one into its discriminated union, so the
    stored blob and the published shape cannot drift into disagreeing about a
    field name — which is the failure two serialisers of one union always
    eventually produce.
    """

    payload = _plain(evidence)
    if not isinstance(payload, dict):  # pragma: no cover - unreachable by type
        raise TypeError(f"evidence did not serialise to a mapping: {evidence!r}")
    return payload


def _plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        fields = {key: _plain(item) for key, item in asdict(value).items()}
        kind = getattr(type(value), "kind", None)
        if kind is None:
            return fields
        # ``kind`` is a ``ClassVar`` on every evidence variant — *what kind is
        # this* is a property of the type rather than a string a caller passes —
        # so ``asdict`` does not see it. The stored blob carries it anyway,
        # because a reader five years from now has the row and not the class.
        return {"kind": _plain(kind), **fields}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if hasattr(value, "value") and hasattr(value, "name"):
        return value.value
    return value
