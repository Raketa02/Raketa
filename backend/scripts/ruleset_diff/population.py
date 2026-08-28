"""The synthetic corpus's population, generated from a seed and committed as a file.

``the-replay-harness.md`` §2.1 and
[ADR-0121](../../../docs/adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md):
**a fixture stands for a comparison, never for a city.** Every number the gate
prints is baseline against candidate over the *same* population, so the corpus
makes no absolute claim about anything — it orders two rulesets, and it says so
on the face of its report.

**The generator is in code and its output is committed.** ``§7``'s second row:
CI regenerates and requires byte-identity, so a generator edit arrives as a
**visible population diff** instead of silently rewriting every past comparison.
It is the repository's generate-commit-diff idiom, third instance.

**Uniform wherever the repository supplies no shape**, and the one departure is
argued in §2.1: ``mu`` is a truncated normal at 2.8 ± 0.6, because a uniform
draw over the scale rarely produces the near-twins where predicted balance is
discriminating. ``sigma`` is ≈ 0.34 for every player, because every rating today
is an *Initial Estimate* — and its stated cost is that the corpus never
exercises the ×32 σ coefficient.

**Two things here are rules rather than draws, and that is deliberate.** The
newcomer fraction and the ledger coverage are assigned by position in a stable
order, because *a rule survives a population resize where a percentage does
not*: at 20 players per sport per area, a 25% draw is five people on a good day
and one on a bad one, and the whole point of the coverage rule is that
``INTEREST_LIFT``, ``NEWCOMER_WINDOW`` and ``ZERO_EXPOSURE`` each fire.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Final, Sequence, final
from uuid import NAMESPACE_URL, UUID, uuid5

from app.engines.racketskill.core import band_for, confidence_percent
from app.kernel import Sport
from app.modules.player_profile.domain.availability import DAYS_IN_THE_GRID, DayPart
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.social_tags import SocialTag

#: The repository root, from ``backend/scripts/ruleset_diff/``.
REPO: Final = Path(__file__).resolve().parents[3]

#: Where the two committed artifacts live, beside the specs that argue for them.
ARTIFACTS: Final = REPO / "docs" / "specs" / "matchmaking" / "ruleset-diff"

#: **A fixed Wednesday instant, stated with its reason** (§2.1). ADR-0100's
#: derived window rides on the response and ``TODAY | TOMORROW | WEEKEND |
#: THIS_WEEK`` are thresholds against *now* — on a Saturday ``TODAY`` and
#: ``WEEKEND`` collapse and two of the four become unreachable. Mid-week is the
#: only position from which all four are reachable and distinct.
NOW: Final = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)

#: The seed the population is drawn under. It is **not** ``PYTHONHASHSEED``: the
#: draws are seeded and reproducible, and the hash seed is what the check varies
#: to prove that nothing downstream of them iterates a set.
SEED: Final = 20260826

#: One doubles sport and one singles — the minimum that exercises both the group
#: objective and a shortlist where ``G`` does not run. All four would quadruple
#: the run to reach no additional branch.
SPORTS: Final = (Sport.PADEL, Sport.TENNIS)

#: One metro, four districts, **spread deliberately wider than the median
#: radius**, so ADR-0099's ×1.5 and ×2.0 rungs have real candidates to count
#: instead of structural zeroes. Coarse to two decimals, because that is the
#: resolution ``LocationArea.around`` rounds to on the way in and a finer figure
#: is refused by the index row itself.
DISTRICTS: Final = (
    ("N", 51.63, -0.13),
    ("E", 51.51, 0.17),
    ("S", 51.39, -0.13),
    ("W", 51.51, -0.43),
)


#: §2.1's two densities, in players per sport per area.
class Density(str, Enum):
    """How many players per sport per area, and what each stands for."""

    #: The launch market — #161's measured figure, where 63% of searches return
    #: under five candidates. **This is the committed corpus**, and the reason is
    #: runtime rather than preference: see ``the-ruleset-gate.md``.
    THIN = "thin"
    #: A plausible year-one single city, 30× below trigger 4. Runnable on
    #: demand, and far too slow to be a build gate.
    DENSE = "dense"

    @property
    def players_per_sport_per_area(self) -> int:
        return 20 if self is Density.THIN else 2_000

    @property
    def newcomer_fraction(self) -> float:
        """**100% for the launch market — what a launch factually is.**"""

        return 1.0 if self is Density.THIN else 0.25


#: ADR-0121's one openly invented number, and the first thing replaced the day
#: the telemetry has a measured rate: roughly one blocked pair per twenty
#: players. A corpus with no blocks over-reports admissible combinations, since
#: ADR-0116 puts every block in the ``K × K`` mask.
CORPUS_BLOCK_RATE: Final = 0.05

#: Every ``n``-th member by id order also runs the three surfaces a shortlist
#: does not. **A rule, never a sample** — a rule survives a resize.
EVERY_NTH_RUNS_EVERY_SURFACE: Final = 5

#: The truncated normal §2.1 argues for, and the σ every rating carries while
#: every rating is an *Initial Estimate*.
MU_CENTRE: Final = 2.8
MU_SPREAD: Final = 0.6
MU_FLOOR: Final = 1.0
MU_CEILING: Final = 5.0
PLAYER_SIGMA: Final = 0.34

#: The twenty-one cells of the availability grid, and the nineteen served tags.
CELLS: Final = tuple(
    f"{day}:{part.value}" for day in range(1, DAYS_IN_THE_GRID + 1) for part in DayPart
)
TAGS: Final = tuple(tag.value for tag in SocialTag)

#: ``search_radius.py``'s own bounds.
RADIUS_MIN: Final = 1
RADIUS_MAX: Final = 50

#: How long ago a newcomer and a settled player committed their profile. Both
#: sit clear of ADR-0113's fourteen days rather than on it, so that a change to
#: the window moves the *fraction* and not the arithmetic of one edge case.
NEWCOMER_COMMITTED_DAYS_AGO: Final = (2, 13)
SETTLED_COMMITTED_DAYS_AGO: Final = (20, 120)

#: Where the ids come from. ``uuid5`` rather than a counter, so a member's id is
#: a function of its handle alone — stable across a resize, and unrelated to the
#: order anything was generated in.
IDS: Final = uuid5(NAMESPACE_URL, "https://raketa.example/ruleset-diff")


@final
@dataclass(frozen=True, slots=True)
class Member:
    """One ``(player, sport)`` row of the corpus, as the artifact spells it.

    A handle rather than a UUID everywhere a human reads: ``padel-N-007`` is a
    diff somebody can follow, and the id is derived from it rather than stored
    beside it.
    """

    handle: str
    sport: str
    district: str
    mu: float
    sigma: float
    tags: tuple[str, ...]
    slots: tuple[str, ...]
    radius_km: int
    declared_intent: str
    gender: str
    gender_preference: str
    latitude: float
    longitude: float
    committed_days_ago: int
    calibration_priority: str
    #: How many times this player was shown this week. Zero is what makes
    #: ``ZERO_EXPOSURE`` reachable, and it is assigned by rule.
    times_shown: int
    #: **The adversarial tail** (§2.1). Uniform draws under-sample the rare arms,
    #: so a small stated tail makes them fire — and it is excluded from every
    #: rate denominator and printed as its own block.
    tail: bool = False

    @property
    def player_id(self) -> UUID:
        return uuid5(IDS, self.handle)

    @property
    def is_newcomer(self) -> bool:
        return self.committed_days_ago < 14

    @property
    def committed_at(self) -> datetime:
        return NOW - timedelta(days=self.committed_days_ago)


@final
@dataclass(frozen=True, slots=True)
class Population:
    """The whole corpus: its members, its blocks and its yeses.

    The three are one artifact because they are one population — a block pair
    naming a handle that no longer exists is the failure a second file invites.
    """

    density: str
    seed: int
    members: tuple[Member, ...]
    #: Directed as recorded, symmetric in effect (``docs/adr/0095``). Sorted, so
    #: the file is a stable diff.
    blocks: tuple[tuple[str, str], ...]
    #: ``(searcher, candidate, days_ago)`` — the candidate said *Let's play* to
    #: the searcher that many days ago. **The age and never a boolean.**
    yeses: tuple[tuple[str, str, int], ...]

    def by_sport(self, sport: str) -> tuple[Member, ...]:
        return tuple(member for member in self.members if member.sport == sport)


def generate(density: Density, *, seed: int = SEED) -> Population:
    """Draw the population. **Deterministic, and nothing here iterates a set.**"""

    rng = random.Random(seed)
    members: list[Member] = []
    for sport in SPORTS:
        for district, latitude, longitude in DISTRICTS:
            members.extend(
                _draw_district(
                    rng,
                    density,
                    sport=sport,
                    district=district,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
    members.extend(_the_tail(latitude=DISTRICTS[0][1], longitude=DISTRICTS[0][2]))
    ordered = tuple(sorted(members, key=lambda member: member.handle))
    return Population(
        density=density.value,
        seed=seed,
        members=ordered,
        blocks=_blocks(rng, ordered),
        yeses=_yeses(ordered),
    )


def _draw_district(
    rng: random.Random,
    density: Density,
    *,
    sport: Sport,
    district: str,
    latitude: float,
    longitude: float,
) -> list[Member]:
    count = density.players_per_sport_per_area
    newcomers = round(count * density.newcomer_fraction)
    drawn: list[Member] = []
    for index in range(count):
        handle = f"{sport.value.lower()}-{district}-{index:04d}"
        # **The newcomer fraction is a rule over the index**, not a draw: at
        # twenty per area a 25% draw is five people on a good day and one on a
        # bad one, and the fraction is a stated property of the corpus.
        newcomer = index < newcomers
        low, high = (
            NEWCOMER_COMMITTED_DAYS_AGO if newcomer else SETTLED_COMMITTED_DAYS_AGO
        )
        drawn.append(
            Member(
                handle=handle,
                sport=sport.value,
                district=district,
                mu=_mu(rng),
                sigma=PLAYER_SIGMA,
                tags=_tags(rng),
                slots=_slots(rng),
                radius_km=rng.randint(RADIUS_MIN, RADIUS_MAX),
                declared_intent=rng.choice([i.value for i in PlayIntent]),
                gender=rng.choice([g.value for g in Gender]),
                gender_preference=rng.choice([p.value for p in GenderPreference]),
                latitude=latitude,
                longitude=longitude,
                committed_days_ago=rng.randint(low, high),
                # Elevated for every fourth member by rule, so the calibration
                # modifier — the one modifier whose input exists — fires.
                calibration_priority="ELEVATED" if index % 4 == 3 else "STANDARD",
                # Zero for every fourth member, so `ZERO_EXPOSURE` is reachable
                # at any population size.
                times_shown=0 if index % 4 == 0 else index % 7,
            )
        )
    return drawn


def _mu(rng: random.Random) -> float:
    """§2.1's one departure from a uniform draw, clamped to the scale."""

    return round(min(MU_CEILING, max(MU_FLOOR, rng.gauss(MU_CENTRE, MU_SPREAD))), 2)


def _tags(rng: random.Random) -> tuple[str, ...]:
    """Uniform over the nineteen ids, count uniform over the served 2–6.

    Sorted, because a tag list's *order* is not a fact about the player and an
    unsorted sample would put a draw order into the committed file.
    """

    return tuple(sorted(rng.sample(TAGS, rng.randint(2, 6))))


def _slots(rng: random.Random) -> tuple[str, ...]:
    """Uniform over the twenty-one cells, at least one (``docs/adr/0102``)."""

    return tuple(sorted(rng.sample(CELLS, rng.randint(1, len(CELLS)))))


def _the_tail(*, latitude: float, longitude: float) -> list[Member]:
    """The adversarial tail: seven constructed rows, and what each one is for.

    Uniform draws under-sample the rare arms — #179's seven clash rows, the ×2.0
    rung, floor crossings in both directions — so these make them fire.
    **Excluded from every rate denominator and printed as its own block**, which
    is what stops six invented people moving a comparison about thousands.
    """

    def one(name: str, **overrides: object) -> Member:
        base = dict(
            handle=f"tail-{name}",
            sport=Sport.PADEL.value,
            district=DISTRICTS[0][0],
            mu=2.80,
            sigma=PLAYER_SIGMA,
            tags=("HERE_TO_IMPROVE", "PLAYS_TO_WIN"),
            slots=("1:EVENING", "3:EVENING", "5:EVENING"),
            radius_km=25,
            declared_intent=PlayIntent.COMPETITIVE.value,
            gender=Gender.WOMAN.value,
            gender_preference=GenderPreference.ANY.value,
            latitude=latitude,
            longitude=longitude,
            committed_days_ago=60,
            calibration_priority="STANDARD",
            times_shown=3,
            tail=True,
        )
        base.update(overrides)
        return Member(**base)  # type: ignore[arg-type]

    return [
        # A pairing as close as the corpus gets: predicted balance is blind past
        # Δμ ≈ 0.34, and the neutral body rarely produces near-twins.
        one("twin", mu=2.80),
        one("near-twin", mu=2.86),
        # Far enough that only ADR-0099's ×2.0 rung reaches them.
        one("far", latitude=round(latitude + 0.30, 2)),
        # Declared the opposite evening: the intent term reads its other cell.
        one("opposed", declared_intent=PlayIntent.FOR_FUN.value),
        # Inside the newcomer window, and never shown: both lifts, on one row.
        one("newcomer", committed_days_ago=3, times_shown=0),
        # **Settled and never shown**, which is the only way `ZERO_EXPOSURE` is
        # reachable at all: `_inclusion_reason` records the most specific
        # reason, so a newcomer who has also never been shown is recorded as a
        # newcomer — and at the launch density every drawn member is a
        # newcomer. Without this row the third of §2.1's three ledger arms
        # never fires, and a ruleset change to the exposure floor would compare
        # two rulesets over a population that cannot tell them apart.
        one("unseen", committed_days_ago=90, times_shown=0),
        # A week wide enough that the searcher's grid covers little of it, which
        # is the reverse-overlap dock rather than a gate.
        one(
            "wide-week",
            slots=tuple(
                f"{day}:{part.value}"
                for day in range(1, DAYS_IN_THE_GRID + 1)
                for part in DayPart
            ),
            radius_km=2,
        ),
    ]


def _blocks(
    rng: random.Random, members: Sequence[Member]
) -> tuple[tuple[str, str], ...]:
    """Roughly one blocked pair per twenty players, within a sport.

    Drawn rather than ruled, because ``CORPUS_BLOCK_RATE`` is a *rate* somebody
    will one day replace with a measured one — and it is the only openly
    invented number in this generator.
    """

    pairs: list[tuple[str, str]] = []
    for sport in SPORTS:
        cohort = [m.handle for m in members if m.sport == sport.value]
        for _ in range(round(len(cohort) * CORPUS_BLOCK_RATE)):
            a, b = rng.sample(cohort, 2)
            pairs.append((a, b) if a < b else (b, a))
    return tuple(sorted(set(pairs)))


def _yeses(members: Sequence[Member]) -> tuple[tuple[str, str, int], ...]:
    """*Let's play*, assigned by rule so ``INTEREST_LIFT`` fires at any size.

    Every tenth member by id order receives a yes from the member three later in
    the same sport, sent two days ago. The age is what is recorded — ADR-0127
    made the lift flat, so a boolean would be the sufficient input and the age
    would be the one that is lost.
    """

    said: list[tuple[str, str, int]] = []
    for sport in SPORTS:
        cohort = [m.handle for m in members if m.sport == sport.value]
        for index in range(0, len(cohort), 10):
            candidate = index + 3
            if candidate < len(cohort):
                said.append((cohort[index], cohort[candidate], 2))
    return tuple(said)


def write(population: Population, path: Path) -> Path:
    """Write the population as the committed artifact. **Stable bytes.**"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(as_document(population), indent=2) + "\n")
    return path


def as_document(population: Population) -> dict[str, object]:
    """The artifact's shape, with every key in a stated order."""

    return {
        "density": population.density,
        "seed": population.seed,
        "generated_at": NOW.isoformat(),
        "sports": [sport.value for sport in SPORTS],
        "districts": [
            {"code": code, "latitude": latitude, "longitude": longitude}
            for code, latitude, longitude in DISTRICTS
        ],
        "members": [_member_document(member) for member in population.members],
        "blocks": [list(pair) for pair in population.blocks],
        "yeses": [list(yes) for yes in population.yeses],
    }


def _member_document(member: Member) -> dict[str, object]:
    document = asdict(member)
    document["player_id"] = str(member.player_id)
    document["band"] = band_for(member.mu).label
    document["confidence"] = confidence_percent(member.sigma)
    document["tags"] = list(member.tags)
    document["slots"] = list(member.slots)
    return document
