"""The corpus, run: one record per search, and the term-value digests beside them.

**This is the committed diff artifact** (ADR-0119 §4). CI regenerates it and
fails if it differs, so a ruleset edited without regenerating its diff fails the
build exactly as a contract changed without its client types does — and the
diff CI prints *is* the ruleset diff, because the file on disk is what the
previously released ruleset answered.

**Every number a record carries is one a ruleset can move**, and nothing here is
a timing. There is no wall-clock, no p99 and no rate of this machine in the
artifact, deliberately: a committed file that moved because a runner was busy
would go red for reasons nobody can argue about, which is how a gate gets
switched off.

**The term-value digests are §3's validity test.** Run the population and hash
each term's *values* — never its contributions — so the classification is
derived rather than declared:

```
values identical   → weight-only  → the recorded corpus may be believed too
any value moved    → shape-class  → only this corpus can answer, and it says so
```

A digest rather than the values themselves, and per **term** rather than per
row: it keeps the artifact a few hundred kilobytes instead of tens of megabytes,
and it still names which of the eight moved — which is the half of the answer a
reader acts on. What it gives up is *which pairing* moved, and the corpus is
re-runnable, so that answer is one command away rather than lost.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping, Sequence, final

from app.engines.matchfit.core import Term
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.grouping import Arranged, Seated, Seating
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1.lineup import seat
from app.kernel import Sport
from app.modules.matchmaking.domain.deck import deal
from app.modules.matchmaking.domain.fence import combine_group_sigma, searcher_of
from app.modules.matchmaking.domain.lineups import (
    LineupPool,
    guests_for,
    mask_over,
    pool_for,
    seated_from,
    single_seat,
    unfilled_reason,
)
from app.engines.matchfit.scorable import Searcher
from app.modules.matchmaking.domain.searches import SearchSurface, StagedCounts
from app.modules.matchmaking.domain.shortlist import (
    Scored,
    generate,
    run,
    score_all,
)
from scripts.ruleset_diff.corpus import Search, searches
from scripts.ruleset_diff.population import Population

#: Where a stored figure is compared, and the walkthroughs' own number: six
#: places is far finer than any weight this ruleset moves and far coarser than
#: the last bit two C libraries disagree about. A diff here is a decision and
#: never a platform.
PLACES: Final = 6

#: How much of each digest the artifact prints. Twelve hex characters is 48 bits
#: — a collision needs ~16 million comparisons of eight terms, and the artifact
#: is read by humans.
DIGEST_CHARACTERS: Final = 12


@final
@dataclass(frozen=True, slots=True)
class Answers:
    """What the whole corpus answered, plus the eight digests §3 compares."""

    ruleset_version: str
    engine_version: str
    population_seed: int
    density: str
    #: One record per search, in the corpus's own stable order.
    records: tuple[Mapping[str, object], ...]
    #: One digest per term, over every value that term produced.
    term_values: Mapping[str, str]
    #: How many readings each digest covers. A digest that moved because a term
    #: fired for one more person is a different finding from one that moved
    #: because a value changed, and the count is what tells them apart.
    term_readings: Mapping[str, int]


def derive(population: Population, ruleset: Ruleset, engine: MatchFit) -> Answers:
    """Run every search of the corpus and record what it answered."""

    handles = {str(member.player_id): member.handle for member in population.members}
    digests = {term.value: hashlib.sha256() for term in Term}
    readings = {term.value: 0 for term in Term}
    records: list[Mapping[str, object]] = []

    for search in searches(population, ruleset):
        _, record = _answer(search, engine, handles)
        records.append(record)
        # **The digest reads every scored pairing, not the recorded band.**
        # Which rows a search *records* moves when the floor moves, so hashing
        # the returned and near-miss rows would report a floor change — a pure
        # weight-class change — as `shape-class`, and send its owner to shadow
        # scoring for a number the recorded corpus can answer exactly.
        #
        # Only the shortlist searches are walked: a term's value is a fact about
        # a pairing and a mode, and the other three surfaces score the same
        # pairings under a mode a shortlist already covered.
        if search.surface is not SearchSurface.SHORTLIST:
            continue
        for row in score_all(generate(search.context), search.context, engine):
            for reading in row.fit.terms:
                digests[reading.term.value].update(
                    f"{search.key}|{handles[row.player_id]}|"
                    f"{round(reading.value, 9)}\n".encode()
                )
                readings[reading.term.value] += 1

    return Answers(
        ruleset_version=ruleset.version,
        engine_version=engine.version,
        population_seed=population.seed,
        density=population.density,
        records=tuple(records),
        term_values={
            term: digest.hexdigest()[:DIGEST_CHARACTERS]
            for term, digest in digests.items()
        },
        term_readings=readings,
    )


def _answer(
    search: Search, engine: MatchFit, handles: Mapping[str, str]
) -> tuple[tuple[Scored, ...], Mapping[str, object]]:
    """One search, through the surface's own terminal stage.

    The six shared stages are the same code a request runs — ``run``,
    ``pool_for`` and ``deal`` are the module's own functions, called here
    unchanged. A harness that reimplemented a stage would be a second opinion
    about what moves somebody, and the second one drifts.
    """

    record: dict[str, object] = {
        "key": search.key,
        "surface": search.surface.value,
        "sport": search.sport,
        "mode": search.mode,
        "searcher": search.searcher,
        "tail": search.tail,
    }
    if search.surface is SearchSurface.SHORTLIST:
        shortlist = run(search.context, engine)
        rows = shortlist.returned + shortlist.near_misses
        record.update(
            counts=_counts(shortlist.counts),
            best_withheld_fit=_round(shortlist.best_withheld_fit),
            returned=[_row(row, handles) for row in shortlist.returned],
            near_miss=[_row(row, handles) for row in shortlist.near_misses],
        )
        return rows, record
    if search.surface is SearchSurface.DECK:
        assert search.exclusions is not None
        dealt = deal(
            search.context,
            engine,
            exclusions=search.exclusions,
            re_shows=frozenset(),
        )
        rows = tuple(card.scored for card in dealt.cards) + dealt.near_misses
        record.update(
            counts=_counts(dealt.counts),
            best_withheld_fit=_round(dealt.best_withheld_fit),
            returned=[_row(card.scored, handles) for card in dealt.cards],
            near_miss=[_row(row, handles) for row in dealt.near_misses],
            excluded_by_suppression=dealt.n_excluded_by_suppression,
        )
        return rows, record

    pool = pool_for(search.context, engine)
    guests = guests_for(Sport(search.sport))
    fenced = searcher_of(search.context)
    # **Filling seats is a line-up with the top seat locked**, which is the one
    # difference between the two surfaces (`lineup.py`). Locking the top row by
    # Fit is a rule rather than a choice, and it is what makes `w_minfit`'s
    # exclusion of locked seats reachable in this corpus at all.
    locked = (
        seated_from(pool.rows[:1], locked=True)
        if search.surface is SearchSurface.FILL_SEATS and pool.rows
        else ()
    )
    if guests == 1:
        seating = single_seat(
            fenced,
            seated_from(pool.rows),
            search.context.ruleset,
            combine_group_sigma,
            locked=locked,
        )
    else:
        seating = _seat_a_four(search, pool, fenced, locked)
    record.update(
        counts=_counts(pool.counts),
        best_withheld_fit=_round(pool.best_withheld_fit),
        returned=[
            {"who": handles[one.candidate.player_id], "fit": _round(one.fit)}
            for one in seating.seated
        ],
        near_miss=[_row(row, handles) for row in pool.near_misses],
        arrangement=_arrangement(seating, handles),
        objective=(
            None if seating.winner is None else _round(seating.winner.objective)
        ),
        unfilled=(
            None
            if (reason := unfilled_reason(pool, seating, search.context, guests=guests))
            is None
            else reason.value
        ),
        combinations=seating.counts.combinations,
    )
    return pool.rows + pool.near_misses, record


def _seat_a_four(
    search: Search,
    pool: LineupPool,
    fenced: Searcher,
    locked: Sequence[Seated],
) -> Seating:
    """The doubles path: the ``K × K`` mask, then the argmax over combinations.

    The mask is **positional and has no default** in ``seat`` (ADR-0116), so it
    is built here rather than defaulted — a default that admitted everybody
    would be an accidental way to seat a four with the gate unread, which is the
    exact failure the mask exists to prevent.

    **The corpus has no blocked pair inside a pool, and that is said out loud.**
    The generator's blocks always name the searcher's own cohort, and a block
    involving the searcher removes the row at generation — so the mask is built
    over an empty pair set here, and it is built rather than skipped because the
    day the generator draws a pair between two *candidates*, this is the line
    that has to notice.
    """

    admissible = mask_over(pool.rows, search.context, frozenset())
    return seat(
        fenced,
        seated_from(pool.rows),
        search.context.ruleset,
        combine_group_sigma,
        admissible,
        locked=locked,
    )


def _arrangement(
    seating: Seating, handles: Mapping[str, str]
) -> Mapping[str, object] | None:
    """Who partners the searcher, and who faces them. **Which way round.**"""

    best: Arranged | None = seating.best
    if best is None:
        return None
    arrangement = best.arrangement
    return {
        "partner": (
            None
            if arrangement.partner is None
            else handles[arrangement.partner.candidate.player_id]
        ),
        "opponents": [
            handles[one.candidate.player_id] for one in arrangement.opponents
        ],
        "side_gap": _round(best.side_gap),
    }


def _row(row: Scored, handles: Mapping[str, str]) -> Mapping[str, object]:
    """One candidate, as the artifact spells them.

    ``rank_key`` is **not** here and never will be: it is ``fit +
    liveness_offset`` and it never crosses the wire in any shape. What the
    artifact records is the order — which is what the offset moved — and the Fit,
    which is what the player is shown.
    """

    return {
        "who": handles[row.player_id],
        "fit": _round(row.modified.points),
        "degraded": [term.value for term in row.fit.degraded_terms],
        "reason": (
            None if row.inclusion_reason is None else row.inclusion_reason.value
        ),
        "withheld": (
            None if row.withheld_reason is None else row.withheld_reason.value
        ),
    }


def _counts(counts: StagedCounts) -> Mapping[str, object]:
    """Every stage's count, including the gate histogram's whole closed roster.

    Sorted, so the artifact is a stable diff — and carried in full, because a
    ruleset that moves *which gate* excluded somebody without moving the total
    is exactly the change a bare ``n_generated`` would hide.
    """

    return {
        "n_generated": counts.n_generated,
        "excluded_by_gate": dict(sorted(counts.excluded_by_gate.items())),
        "n_scored": counts.n_scored,
        "n_cleared_floor": counts.n_cleared_floor,
        "n_returned": counts.n_returned,
        "n_near_miss_recorded": counts.n_near_miss_recorded,
    }


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, PLACES)


def write(answers: Answers, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(as_document(answers), indent=2) + "\n")
    return path


def as_document(answers: Answers) -> dict[str, object]:
    return {
        "ruleset_version": answers.ruleset_version,
        "engine_version": answers.engine_version,
        "density": answers.density,
        "population_seed": answers.population_seed,
        "searches": len(answers.records),
        "term_values": dict(sorted(answers.term_values.items())),
        "term_readings": dict(sorted(answers.term_readings.items())),
        "records": list(answers.records),
    }


def read(path: Path) -> dict[str, object] | None:
    """The committed answers — the **baseline** the re-derived run is diffed
    against — or ``None`` the first time, when there is nothing to compare to."""

    if not path.exists():
        return None
    document: dict[str, object] = json.loads(path.read_text())
    return document
