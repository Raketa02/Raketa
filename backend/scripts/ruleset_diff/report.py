"""The diff, rendered: what this ruleset moves against the one that shipped.

``the-replay-harness.md`` §4's report, for the corpus that can run in CI. **Every
line names which corpus produced it, and nothing is a pass or a fail** — §5 says
who decides, and it is not this file: *a number saying 18% composition change is
acceptable is a product decision smuggled into code.*

**The baseline is the committed artifact.** There is one ruleset embedded in the
binary (ADR-0093), so *baseline against candidate* is *what the last release
answered against what this tree answers* — which is the comparison a release
argument actually makes, and it is why the artifact is committed rather than
computed twice from the same code.

What the report refuses to hide is §6's list, printed on every run: the
classification and which terms moved it, the per-surface counts, the near-miss
saturation, the tail's separate block, and the four approximations this corpus
cannot compute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping, Sequence, final

from scripts.ruleset_diff.answers import Answers, as_document

RULE: Final = "─" * 76

#: The five verdicts, in the order §4 prints them. A search lands in exactly one
#: and the first that applies wins, most-consequential first: emptiness flipping
#: is a different event from a composition change even though it is one too.
VERDICTS: Final = (
    "unchanged",
    "reordered",
    "composition changed",
    "crossed the floor",
    "emptiness flipped",
)


@final
@dataclass(frozen=True, slots=True)
class Diff:
    """Two runs of one corpus, classified. **It counts; it never judges.**"""

    weight_only: bool
    moved_terms: tuple[str, ...]
    verdicts: Mapping[str, int]
    tail_verdicts: Mapping[str, int]
    searches: int
    tail_searches: int
    by_surface: Mapping[str, int]
    top_one_changed: int
    baseline_mean_top_fit: float | None
    candidate_mean_top_fit: float | None
    renormalisation_bases: int
    baseline_empty: int
    candidate_empty: int
    near_miss_saturated: int
    carried_forward: int
    #: How many term readings the whole corpus produced, baseline and candidate.
    #: **The population the terms fired over**, which is what a *gate* change
    #: moves — as opposed to a term reporting a different number about the same
    #: pairing. Both land as ``shape-class`` under ADR-0118 §3's derived
    #: classification, and the report says which of the two happened, because
    #: they have different answers: a moved value voids the recorded corpus, and
    #: a moved gate is **bounded and not computed** on it (ADR-0118 §8).
    baseline_readings: int
    candidate_readings: int


def compare(baseline: Mapping[str, Any], candidate: Answers) -> Diff:
    """Classify every search of the corpus, body and tail apart."""

    Record = Mapping[str, Any]
    was: dict[str, Record] = {
        str(record["key"]): record for record in baseline.get("records", ())
    }
    records: Sequence[Record] = as_document(candidate)["records"]  # type: ignore[assignment]
    is_: dict[str, Record] = {str(record["key"]): record for record in records}

    moved = tuple(
        term
        for term, digest in sorted(candidate.term_values.items())
        if baseline.get("term_values", {}).get(term) not in (None, digest)
    )

    verdicts = {verdict: 0 for verdict in VERDICTS}
    tail_verdicts = {verdict: 0 for verdict in VERDICTS}
    by_surface: dict[str, int] = {}
    top_changed = 0
    baseline_top: list[float] = []
    candidate_top: list[float] = []
    bases: set[tuple[str, ...]] = set()
    baseline_empty = candidate_empty = 0
    saturated = 0
    carried = 0

    for key, record in sorted(is_.items()):
        surface = str(record["surface"])
        by_surface[surface] = by_surface.get(surface, 0) + 1
        returned = _returned(record)
        candidate_empty += not returned
        if returned:
            candidate_top.append(float(returned[0]["fit"]))
        for row in list(returned) + list(record.get("near_miss", ())):
            # The **basis** is which terms stood down; whose gap each was is
            # recorded beside it and is a different count, so it is not folded
            # in here — two rows on the same seven terms are one basis whatever
            # the reasons say about the two people.
            bases.add(
                tuple(entry["term"] for entry in row.get("degraded", ()))
            )
            carried += row.get("reason") is not None
        counts = record.get("counts", {})
        if counts.get("n_near_miss_recorded") and _saturated(record, was.get(key)):
            saturated += 1

        previous = was.get(key)
        if previous is None:
            continue
        before = _returned(previous)
        baseline_empty += not before
        if before:
            baseline_top.append(float(before[0]["fit"]))
        verdict = _verdict(before, returned, previous, record)
        target = tail_verdicts if record.get("tail") else verdicts
        target[verdict] += 1
        if before and returned and before[0]["who"] != returned[0]["who"]:
            top_changed += 1

    body = sum(verdicts.values())
    return Diff(
        baseline_readings=sum(baseline.get("term_readings", {}).values()),
        candidate_readings=sum(candidate.term_readings.values()),
        weight_only=not moved,
        moved_terms=moved,
        verdicts=verdicts,
        tail_verdicts=tail_verdicts,
        searches=body,
        tail_searches=sum(tail_verdicts.values()),
        by_surface=dict(sorted(by_surface.items())),
        top_one_changed=top_changed,
        baseline_mean_top_fit=_mean(baseline_top),
        candidate_mean_top_fit=_mean(candidate_top),
        renormalisation_bases=len(bases),
        baseline_empty=baseline_empty,
        candidate_empty=candidate_empty,
        near_miss_saturated=saturated,
        carried_forward=carried,
    )


def _returned(record: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    return tuple(record.get("returned", ()))


def _saturated(record: Mapping[str, Any], previous: Mapping[str, Any] | None) -> bool:
    """Whether every recorded near miss crossed the floor in the new ruleset.

    **The blindness indicator** (ADR-0118 §4): if a diff's promotions saturate
    the band, the diff **understated the change** and ``NEAR_MISS_RECORDED`` is
    too small. Printed every run, so the blindness announces itself rather than
    being assumed away.
    """

    if previous is None:
        return False
    withheld = {row["who"] for row in previous.get("near_miss", ())}
    if not withheld:
        return False
    return withheld <= {row["who"] for row in record.get("returned", ())}


def _verdict(
    before: Sequence[Mapping[str, Any]],
    after: Sequence[Mapping[str, Any]],
    previous: Mapping[str, Any],
    record: Mapping[str, Any],
) -> str:
    if bool(before) != bool(after):
        return "emptiness flipped"
    was = [row["who"] for row in before]
    now = [row["who"] for row in after]
    if was == now:
        # A shortlist whose order and membership are identical may still have
        # moved somebody across the floor **into the near-miss band**, which is
        # the change ADR-0118 §4 says reading only the returned rows would miss.
        if _floor_crossers(previous, record):
            return "crossed the floor"
        return "unchanged"
    if set(was) == set(now):
        return "reordered"
    if _floor_crossers(previous, record):
        return "crossed the floor"
    return "composition changed"


def _floor_crossers(previous: Mapping[str, Any], record: Mapping[str, Any]) -> bool:
    """Whether anybody moved between the two bands, in either direction.

    **Both directions, and the single most consequential change a ruleset
    makes** — a promotion is somebody the product now says is worth meeting, and
    a demotion is somebody it has stopped saying that about.
    """

    was_shown = {row["who"] for row in previous.get("returned", ())}
    was_withheld = {row["who"] for row in previous.get("near_miss", ())}
    now_shown = {row["who"] for row in record.get("returned", ())}
    now_withheld = {row["who"] for row in record.get("near_miss", ())}
    return bool((was_withheld & now_shown) or (was_shown & now_withheld))


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def render(candidate: Answers, diff: Diff | None) -> str:
    """The report, as §4 prints it. **Nothing here is a pass or a fail.**"""

    lines = [
        "",
        RULE,
        f"  THE RULESET DIFF — synthetic corpus, {candidate.density}",
        RULE,
        "",
        f"  ruleset                        {candidate.ruleset_version}"
        f"   ·   engine {candidate.engine_version}",
        f"  population                     seed {candidate.population_seed}",
        f"  searches                       {len(candidate.records)}",
    ]
    if diff is None:
        lines += [
            "",
            "  no committed baseline — this run establishes it.",
            "  Commit both artifacts; the next run diffs against them.",
            "",
            RULE,
            "",
        ]
        return "\n".join(lines)

    lines += [
        "  by surface                     "
        + ", ".join(f"{surface} {count}" for surface, count in diff.by_surface.items()),
        "",
        f"  classification                 "
        f"{'weight-only' if diff.weight_only else 'shape-class'}"
        f"        (synthetic: {len(diff.moved_terms)} term values moved)",
    ]
    if diff.moved_terms:
        gated = diff.candidate_readings != diff.baseline_readings
        lines += [
            "  terms whose values moved       " + ", ".join(diff.moved_terms),
            f"  term readings                  "
            f"{diff.baseline_readings} → {diff.candidate_readings}"
            + ("        the gate moved too" if gated else ""),
            "",
            "  **The recorded corpus cannot answer this change** (ADR-0118 §3), "
            "and only the",
            "  synthetic diff below says anything about it.",
        ]
        lines += (
            [
                "  The readings moved with the values, so **a gate moved**: "
                "the terms fired over a",
                "  different population. On the recorded corpus that is bounded "
                "and not computed",
                "  (ADR-0118 §8) — the gate's exclusion count and its smallest "
                "admitted Δμ.",
            ]
            if gated
            else [
                "  The readings did not move, so the same pairings were scored "
                "and **a term reported",
                "  a different number about them**. Every historical search is "
                "void for that term.",
            ]
        )
        lines += [
            "  This is also the condition ADR-0119 §3 arms shadow scoring on, "
            "if the owner in §5",
            "  will not sign this corpus.",
        ]
    lines += ["", "  verdicts (body, excluding the adversarial tail)"]
    for verdict in VERDICTS:
        count = diff.verdicts[verdict]
        share = f"{100 * count / diff.searches:5.1f}%" if diff.searches else "    —"
        lines.append(f"      {verdict:<22} {count:6}   {share}")
    lines += [
        "",
        f"  top-1 changed                  {diff.top_one_changed}",
        f"  mean fit of top-1              "
        f"{diff.baseline_mean_top_fit} → {diff.candidate_mean_top_fit}"
        f"        (over {diff.renormalisation_bases} renormalisation bases)",
        f"  empty results                  "
        f"{diff.baseline_empty} → {diff.candidate_empty}",
        "",
        "  adversarial tail (its own block, in no rate above)",
    ]
    for verdict in VERDICTS:
        lines.append(f"      {verdict:<22} {diff.tail_verdicts[verdict]:6}")
    lines += [
        "",
        f"  near-miss band saturated in    {diff.near_miss_saturated} searches",
        f"  rows carrying an inclusion reason  {diff.carried_forward}",
        "",
        "  What this corpus cannot say, printed rather than known:",
        "    · it does not stand for a city and makes no absolute claim — every",
        "      number above is baseline against candidate over one population",
        "      (ADR-0121);",
        "    · σ is near-constant, so predicted balance is effectively a function",
        "      of Δμ and the ×32 σ coefficient is never exercised;",
        "    · reliability has no provider on this platform, so its term stands",
        "      down for everybody and its digest is the empty one;",
        "    · the recorded corpus is not run here and cannot be — there is no",
        "      database in CI, and ADR-0118 §7 restricts it to a restore.",
        "",
        RULE,
        "",
    ]
    return "\n".join(lines)
