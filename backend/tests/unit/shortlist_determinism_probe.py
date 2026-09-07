"""One search, run and printed, so a second process can be compared to the first.

**Determinism is a set-iteration problem in Python** (``docs/adr/0105``), and the
failure it produces is invisible from inside one process: a set of ids reorders
*between* processes and never *within* one, so every test is green and two
workers disagree about who came first.

So the assertion has to cross a process boundary, and this module is the thing on
the other side of it. It is a module rather than a string passed to ``-c`` so
that it is lintable, typecheckable and readable — the probe is the load-bearing
half of that test, and a probe nobody can read is a test nobody can trust.

It prints **everything a search decided**, not just the order: the ids, the
number on each card, the hidden key they were sorted by, the renormalisation
basis, the reasons in the order the engine ranked them, and the near-miss band.
A weaker digest would pass while the ordering held and the reasons shuffled.
"""

from __future__ import annotations

import json
import sys

from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.domain.shortlist import Scored, run
from tests.unit import matchmaking_builders as build

#: A population with **ties in it on purpose.** Candidates that score identically
#: are the only ones whose order a hash seed can move, so a population of clearly
#: distinguishable people would make this probe pass by accident.
POPULATION = tuple(
    build.row(
        number,
        # Four groups of five identical pairings, plus one fact that varies
        # inside each group, so both the tie-break and the ordering are exercised.
        mu=build.SEARCHER_MU + 0.02 * (number % 4),
        slots=build.SEARCHER_SLOTS[: 1 + number % 4],
        latitude=round(build.CENTRE.latitude + 0.01 * (number % 3), 2),
        tags=build.TAGS if number % 2 else ("PLAYS_TO_WIN",),
        declared_intent="COMPETITIVE" if number % 3 else "FOR_FUN",
    )
    for number in range(1, 21)
)


def _row(row: Scored) -> dict[str, object]:
    return {
        "player_id": row.player_id,
        "fit": repr(row.modified.points),
        # The rank key never crosses the wire and is printed **here** on purpose:
        # this is the one place it may be looked at, and an order that agreed
        # while the key that produced it differed would be a coincidence.
        "rank_key": repr(row.rank_key),
        "terms": [scored.term.value for scored in row.fit.terms],
        "degraded": [stood.term.value for stood in row.fit.degraded_terms],
        "concerns": [term.value for term in row.fit.concerns],
        "modifiers": [entry.modifier.value for entry in row.modified.modifiers.fired],
        "liveness": [
            move.signal.value for move in (row.liveness.reasons if row.liveness else ())
        ],
        "inclusion": row.inclusion_reason.value if row.inclusion_reason else None,
    }


def answer() -> dict[str, object]:
    """The whole of what one fixed search decided, as plain data."""

    shortlist = run(build.context(POPULATION), MatchFitV1())
    return {
        "returned": [_row(row) for row in shortlist.returned],
        "near_misses": [_row(row) for row in shortlist.near_misses],
        "counts": {
            "n_generated": shortlist.counts.n_generated,
            "n_scored": shortlist.counts.n_scored,
            "n_cleared_floor": shortlist.counts.n_cleared_floor,
            "n_returned": shortlist.counts.n_returned,
            "excluded_by_gate": shortlist.counts.excluded_by_gate,
        },
        "best_withheld_fit": repr(shortlist.best_withheld_fit),
    }


def main() -> int:
    # `sort_keys` on the *containers* only — every list here is an order the
    # engine chose, and sorting one would hide the very thing being asserted.
    sys.stdout.write(json.dumps(answer(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
