"""A population to develop the Play screens against, and what it does not stand for.

**This fixture stands for nothing outside itself.** ``local`` is the only
environment that runs and its named catalog holds a handful of accounts, all at
one address and all in one ring — so every Play screen would be developed against
an empty result. What is here is a **workbench**: a population chosen so that the
states a screen has to render are *reachable*, not a population chosen because it
is what a city looks like. A realistic launch draw reaches a full court only by
luck, and an honestly-modelled 100%-newcomer launch leaves the protagonist's pool
nearly empty — a true fact about launch and a useless screen.

That is why this is **not** ``scripts/ruleset_diff/population.py`` with different
numbers, and why it may exist beside it without disturbing
[ADR-0121](../../../docs/adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md).
That corpus is a **comparator**: it orders two rulesets over one population and
prints on its own report that it cannot tell you what the empty-result rate *is*.
This one's job is to **reach states**. Two fixtures, two questions, and saying so
on the face of each is what keeps them from being confused — so the seed's report
says it too, not only this docstring.

What is borrowed is that generator's **mechanics** and none of its numbers:
seeded draws, ``uuid5``-from-handle ids, and assignment **by rule rather than by
rate**, because a rule survives a population resize where a percentage does not.
Not 2.8 ± 0.6, not twenty per sport per area, not the 100% newcomer share — those
answer a different question.

**Two lists, and they are asymmetric.** What is here is the first: the
*declarations*, which are this generator's own inputs. The second — the
*assertions* — is in ``app/seeds/screens.py``, and every one of them is an
outcome of a **real read path executed as the protagonist**. Nothing is asserted
about a number this file chose: a tightened ``QUALITY_FLOOR`` moves no
distribution at all and still empties every screen, so a check computed from the
population could only ever pass.

**The population is committed as inputs only** — never μ, never σ, never a band.
Those are the engine's answers, and a committed copy of an answer is a second
number nothing keeps honest. What makes the file worth committing is the keying:
every draw is a function of the member's **handle** alone, so adding or removing
one member changes that row and nobody else's and the diff is readable. Under one
global stream, inserting a member rewrites every row after it, the diff is noise,
and committing buys nothing. Accepted knowingly: because draws are keyed off the
handle, **moving a member between rings shows in the diff as a delete plus an
add** — correct, since a member in a different ring is a different member, but
better said than discovered.

Regenerate with ``make gen-cohort`` and commit the result.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Mapping, final
from uuid import NAMESPACE_URL, UUID, uuid5

from app.kernel import Sport
from app.modules.matchmaking.domain.geography import Point, distance_km
from app.modules.player_profile.domain.availability import DAYS_IN_THE_GRID, DayPart
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS
from app.modules.player_profile.domain.social_tags import SocialTag
from app.seeds.clock import NEWCOMER_WINDOW_DAYS
from app.seeds.catalog import (
    BAND_ADVANCED,
    BAND_DEVELOPING,
    BAND_ESTABLISHED,
    BAND_NEW,
    CENTRE_LATITUDE,
    CENTRE_LONGITUDE,
    PROTAGONIST_RADIUS_KM,
    PROTAGONIST_TAGS,
    PROTAGONIST_WEEK,
    SEED_EMAIL_DOMAIN,
    AnswerPolicy,
)

#: Beside the generator, because the image copies ``app/`` and a fixture a
#: container cannot read is a fixture a container cannot check.
ARTIFACT: Final = Path(__file__).resolve().parent / "cohort.json"

#: The seed every draw is *salted* with rather than sequenced from. It is not
#: ``PYTHONHASHSEED``: the draws are keyed strings, hashed with SHA-512 by
#: ``random.Random``, so nothing here depends on the interpreter's hash seed and
#: ``docs/adr/0105``'s question is answered rather than assumed.
COHORT_SEED: Final = 20260830

#: **Two sports, and the second is not decoration.** One sport cannot show Play
#: intent declared *per* sport (``docs/adr/0094``), cannot make
#: *the-one-sport-player* mean anything, and cannot exhibit the one-open-
#: challenge-per-pair-**across-sports** rule at all. A third and a fourth reach
#: no new screen state and cost an assessment each per member.
SPORTS: Final = (Sport.PADEL, Sport.TENNIS)

#: Where the ids come from — ``uuid5`` over the handle, so a member's id is a
#: function of their name alone and unrelated to the order anything was
#: generated in. It is **not** the id the seed writes: ``RegisterUser`` mints
#: that, correctly, because an id chosen by a caller is an id the write path does
#: not own. This is the artifact's stable name for a row, and the file says so.
IDS: Final = uuid5(NAMESPACE_URL, f"https://{SEED_EMAIL_DOMAIN}/cohort")

#: The twenty-one cells of the availability grid, and the served tags.
CELLS: Final = tuple(
    f"{day}:{part.value}" for day in range(1, DAYS_IN_THE_GRID + 1) for part in DayPart
)
TAGS: Final = tuple(tag.value for tag in SocialTag)

#: The protagonist's own week, as cells, so a draw can be made to overlap it.
PROTAGONIST_CELLS: Final = tuple(f"{day}:{part}" for day, part in PROTAGONIST_WEEK)


# ---------------------------------------------------------------------------
# Declarations — every input this generator takes
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class Archetype:
    """One answer set standing for one band. **One per band, and no more.**

    The archetype chooses *answers*; the **engine** chooses the band. That is
    what keeps the histogram a real check rather than the generator grading its
    own work — and it is why the claim below is a range per band and never a μ,
    which would pin the engine.

    ``answers`` carries a **spread**, which is the whole reason ``AnswerPolicy``
    widened: six shared policies would be a population at six values of μ, with
    ``combine_sigma`` constant, predicted balance a function of a handful of Δμ,
    and a pool of near-identical cards ranked arbitrarily.

    **Every archetype here declares zero width on the claims**, and that is a
    decision rather than an oversight. The opening question is a claim, and its
    weakest option puts the engine on its one-question beginner path — so a
    jittered claim would not spread a member around their band, it would move
    them into a different archetype's. Demonstrations are what the engine reads
    for level inside a band, which is exactly the axis a near-twin varies on. The
    width is a *declaration* rather than a branch in ``AnswerPolicy``, so an
    archetype that wanted the other axis could have it.
    """

    name: str
    #: The band this archetype is *for*. Never asserted per member — the claim is
    #: a histogram over the population — but recorded so the file says what each
    #: archetype was aiming at when somebody reads a diff.
    band: str
    answers: AnswerPolicy


#: The beginner path is **one question**, so an archetype here has nothing to
#: spread over: the opening answer ends the run. Stated rather than left at zero
#: silently, because a reader would otherwise take it for an omission.
NEW_TO_THE_SPORT: Final = Archetype(
    name="new-to-the-sport",
    band=BAND_NEW,
    answers=AnswerPolicy(claims=0, demonstrations=0),
)

IMPROVER: Final = Archetype(
    name="improver",
    band=BAND_DEVELOPING,
    answers=AnswerPolicy(claims=1, demonstrations=1, demonstration_spread=1),
)

#: **The bulk of the cohort, and the reason is the level gate.** The tolerance a
#: competitive pairing is gated at is far narrower than a band is wide, so the
#: people a protagonist in the Established band can actually be shown are the
#: people near them — and a cohort spread evenly over four bands would be a
#: cohort where three quarters of everybody is gated out before scoring.
CLUB_PLAYER: Final = Archetype(
    name="club-player",
    band=BAND_ESTABLISHED,
    answers=AnswerPolicy(claims=2, demonstrations=2, demonstration_spread=2),
)

#: The strongest answer set there is, and it is zero-spread for the same reason
#: the beginner is: only the top of the scale reaches this band at all, so a
#: draw downwards is a member in the band below rather than a near-twin.
STRONG_PLAYER: Final = Archetype(
    name="strong-player",
    band=BAND_ADVANCED,
    answers=AnswerPolicy(claims=4, demonstrations=4),
)

ARCHETYPES: Final = (NEW_TO_THE_SPORT, IMPROVER, CLUB_PLAYER, STRONG_PLAYER)


@final
@dataclass(frozen=True, slots=True)
class Ring:
    """One distance band around the protagonist, and who lives in it.

    **The rings are cut by the relaxation ladder's own multipliers**, so each
    rung finds somebody new *by construction* rather than by luck: rung B widens
    the searcher's radius ×1.5 and rung C ×2.0, and there is a ring between each
    pair of those. ``docs/adr/0099``'s bounded single climb is then watchable end
    to end on a screen instead of being a property only a unit test has seen.

    ``latitude`` is stated at two decimal places and the distance it produces is
    **checked** at import, because ``LocationArea`` rounds to 2 dp on the way in:
    ~1.1 km is the floor, and anything thinner is not a ring, it is rounding.
    """

    code: str
    #: What this ring is *for*, printed in the report and in the artifact.
    reason: str
    latitude: float
    #: Inclusive-exclusive kilometres this ring must fall inside, checked at
    #: import against the module's own distance function.
    bounds_km: tuple[float, float]
    #: How many members of each archetype live here.
    members: Mapping[str, int]


#: **How big, and why that big.** The number was found by raising it until the
#: assertions in ``screens.py`` passed and then written down here, which is the
#: only defensible way to choose it: a figure taken from the ruleset-diff corpus
#: would be indefensible the day ``make seed`` starts taking two minutes, and a
#: figure chosen because it felt right is a figure nobody can argue with.
#:
#: What the assertions need, in the order they bind:
#:
#: - the innermost ring must leave **``MIN_SHORTLIST`` rows above the floor**
#:   *after* the level gate, the mutual gender gate and scoring — and only the
#:   Established archetype survives a competitive protagonist's level gate at
#:   all, which is why twelve of that ring's nineteen are club players;
#:  - a **full four** must compose out of the same ring;
#: - each of rungs B and C must **add somebody new**, which is what puts four
#:   club players in each of the two ladder rings rather than one;
#: - the second sport must stay **thin enough to price a ladder at all** — every
#:   third member plays it by rule, so padel is dense and tennis is not.
#:
#: Thirty-six members, three of them past the slider's ceiling. Raising it costs
#: an assessment apiece — the questionnaire is the only door to a level — and
#: buys no screen state that is not already reachable.
RINGS: Final = (
    Ring(
        code="a",
        reason="inside the searcher's own radius — the pool before any widening",
        latitude=51.55,
        bounds_km=(0.0, float(PROTAGONIST_RADIUS_KM)),
        members={
            CLUB_PLAYER.name: 12,
            IMPROVER.name: 3,
            NEW_TO_THE_SPORT.name: 2,
            STRONG_PLAYER.name: 2,
        },
    ),
    Ring(
        code="b",
        reason="reached only by rung B, the ×1.5 widening",
        latitude=51.62,
        bounds_km=(float(PROTAGONIST_RADIUS_KM), PROTAGONIST_RADIUS_KM * 1.5),
        members={CLUB_PLAYER.name: 4, IMPROVER.name: 1},
    ),
    Ring(
        code="c",
        reason="reached only by rung C, the ×2.0 widening",
        latitude=51.67,
        bounds_km=(PROTAGONIST_RADIUS_KM * 1.5, PROTAGONIST_RADIUS_KM * 2.0),
        members={CLUB_PLAYER.name: 4, STRONG_PLAYER.name: 1},
    ),
    Ring(
        code="d",
        reason="past the ladder's furthest rung and inside the slider's ceiling",
        latitude=51.80,
        bounds_km=(PROTAGONIST_RADIUS_KM * 2.0, float(SEARCH_RADIUS_BOUNDS.maximum_km)),
        members={CLUB_PLAYER.name: 3, IMPROVER.name: 1},
    ),
    Ring(
        code="e",
        reason=(
            "past the slider's ceiling — a population `radius_clamp` provably "
            "cannot reach, whatever a player sets and whatever a rung offers"
        ),
        latitude=52.10,
        bounds_km=(float(SEARCH_RADIUS_BOUNDS.maximum_km), 500.0),
        members={CLUB_PLAYER.name: 2, NEW_TO_THE_SPORT.name: 1},
    ),
)

#: **Every rule below is a rule over the member's position, never a rate.** At
#: this size a 25% draw is four people on a good day and one on a bad one, and
#: every one of these exists so that a specific screen state is *reachable* —
#: which a draw cannot promise.
#:
#: **Each rule is offset from the others**, so that the five of them do not all
#: land on position zero and make one member carry every departure at once. A
#: member who was simultaneously the opted-out one, the newcomer, the one the
#: gender gate removes and the one with no shared week would be five rules with
#: one witness — and removing that member would silently empty five assertions.

#: Every n-th member also plays the second sport. Below this, intent-per-sport
#: has nobody to show it on; above it, every member costs a second assessment.
EVERY_NTH_PLAYS_BOTH_SPORTS: Final = 3
PLAYS_BOTH_SPORTS_AT: Final = 0

#: Every n-th member has opted out of proposals. ``gates.py`` gates
#: ``SearchInitiation.ENGINE`` only — *that gate gates the push, not the person*
#: — so these are **full candidates in a search a human ran** and absent from
#: the engine's fill. A unit test proves the gate; only a fixture proves the two
#: screens differ, and somebody who has never seen one reads that as a bug.
EVERY_NTH_HAS_OPTED_OUT: Final = 5
HAS_OPTED_OUT_AT: Final = 1

#: Every n-th member is inside ADR-0113's window. Both sides of the window are
#: present by construction, because a gate with one side present cannot be seen.
EVERY_NTH_IS_A_NEWCOMER: Final = 4
IS_A_NEWCOMER_AT: Final = 2

#: Every n-th member's preference excludes the default protagonist, so the
#: mutual gender gate (``docs/adr/0096``) — invisible to the scorer, and
#: therefore invisible on every screen — has somebody it removes.
EVERY_NTH_EXCLUDES_THE_PROTAGONIST: Final = 6
EXCLUDES_THE_PROTAGONIST_AT: Final = 3

#: Every n-th member is **lopsided**: a week wide enough that the searcher's
#: grid covers little of it, and the tightest radius the slider offers. Both
#: halves point the same way, and that is the point — ``RECIPROCAL_ASYMMETRY``
#: is a **reverse** Fit falling far short of the forward one, and neither
#: availability's denominator nor distance's ring is symmetric between two
#: people. It is the one printable signal a cohort of ordinary members never
#: reaches: everybody drawn alike is everybody who scores each other alike.
EVERY_NTH_IS_LOPSIDED: Final = 9
IS_LOPSIDED_AT: Final = 5

#: Every n-th member's week misses the protagonist's entirely, so the
#: availability term's *no shared slots* dock is reachable rather than
#: structural. Everybody else shares at least this many cells.
EVERY_NTH_SHARES_NO_WEEK: Final = 7
SHARES_NO_WEEK_AT: Final = 4
SHARED_CELLS_FLOOR: Final = 2

#: The Play intent split, as a cycle over position. Weighted toward competitive
#: because the default protagonist searches competitively and an intent term with
#: nothing to agree with is a term that only ever docks.
INTENT_CYCLE: Final = (
    PlayIntent.COMPETITIVE,
    PlayIntent.COMPETITIVE,
    PlayIntent.FOR_FUN,
    PlayIntent.NO_PREFERENCE,
)

#: The gender mix, as a cycle over position. All three values appear, because
#: ``PREFER_NOT_TO_SAY`` is a real answer and a gate that never meets one is a
#: gate whose third branch nobody has watched.
GENDER_CYCLE: Final = (
    Gender.WOMAN,
    Gender.MAN,
    Gender.WOMAN,
    Gender.PREFER_NOT_TO_SAY,
)

#: How long ago a member committed their profile, drawn inside one of two
#: windows. **Both edges clear of the fourteen days**, so a change to
#: ADR-0113's window moves the *fraction* rather than the arithmetic of one edge
#: case — and neither bound is written as fourteen anywhere here.
NEWCOMER_COMMITTED_DAYS_AGO: Final = (2, 11)
SETTLED_COMMITTED_DAYS_AGO: Final = (21, 120)

#: The radius a member sets for themselves. It gates nobody's search but their
#: own; what it moves here is the **reverse** Fit, which is what reciprocal
#: asymmetry is computed from.
MEMBER_RADIUS_KM: Final = (5, SEARCH_RADIUS_BOUNDS.maximum_km)

#: How many tags a member holds, inside the selection's own served bounds.
MEMBER_TAG_COUNT: Final = (2, 5)

#: How many cells a member ticks **beyond** the ones the overlap rule already
#: put there, and how many a member with no shared week ticks instead. Named
#: beside the tag count rather than left inline, because both are the fixture
#: deciding how much of the grid an ordinary player fills — which is the number
#: the availability term's denominator is read against.
MEMBER_EXTRA_CELLS: Final = (1, 4)
MEMBER_CELLS_ELSEWHERE: Final = (2, 5)


# ---------------------------------------------------------------------------
# The population
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class CohortMember:
    """One member, as the artifact spells them. **Inputs only.**

    No μ, no σ, no band: those are the engine's answers to the questionnaire this
    member is about to sit, and committing them would be a second copy of a
    number nothing keeps honest. What is here is everything the run *supplies*,
    and every field is a function of ``handle`` alone.
    """

    handle: str
    ring: str
    archetype: str
    latitude: float
    longitude: float
    radius_km: int
    #: Grid cells, as the boundary spells one.
    slots: tuple[str, ...]
    tags: tuple[str, ...]
    #: One per sport this member plays, in the order the run declares them.
    intents: tuple[tuple[str, str], ...]
    gender: str
    gender_preference: str
    proposals_opt_in: bool
    committed_days_ago: int
    #: The archetype's own draw parameters, written out per member so the file
    #: says what produced this row without a reader having to hold the archetype
    #: table in their head.
    claims: int
    demonstrations: int
    claim_spread: int
    demonstration_spread: int

    @property
    def sports(self) -> tuple[Sport, ...]:
        return tuple(Sport(sport) for sport, _ in self.intents)

    @property
    def email(self) -> str:
        return f"{self.handle}@{SEED_EMAIL_DOMAIN}"

    @property
    def nickname(self) -> str:
        return self.handle

    @property
    def answers(self) -> AnswerPolicy:
        return AnswerPolicy(
            claims=self.claims,
            demonstrations=self.demonstrations,
            claim_spread=self.claim_spread,
            demonstration_spread=self.demonstration_spread,
        )

    @property
    def is_a_newcomer(self) -> bool:
        """Whether this row was declared inside ADR-0113's window.

        A statement about the **declaration**, not about the database: what the
        run then has to prove is that the stored profile still agrees with it,
        which is what the calendar refusal in ``runner.py`` reads.
        """

        return self.committed_days_ago < NEWCOMER_WINDOW_DAYS

    @property
    def stable_id(self) -> UUID:
        """The artifact's name for this row. **Not the id the seed writes.**"""

        return uuid5(IDS, self.handle)

    @property
    def availability(self) -> tuple[tuple[int, str], ...]:
        return tuple(_cell(code) for code in self.slots)


def _cell(code: str) -> tuple[int, str]:
    day, _, part = code.partition(":")
    return int(day), part


@final
@dataclass(frozen=True, slots=True)
class Cohort:
    """The whole population and the seed it was drawn under."""

    seed: int
    members: tuple[CohortMember, ...]

    def by_handle(self, handle: str) -> CohortMember:
        for member in self.members:
            if member.handle == handle:
                return member
        raise KeyError(handle)


def generate(*, seed: int = COHORT_SEED) -> Cohort:
    """Draw the cohort. **Every draw keyed off one handle, nothing off a set.**"""

    members: list[CohortMember] = []
    for ring in RINGS:
        position = 0
        for archetype in ARCHETYPES:
            for _ in range(ring.members.get(archetype.name, 0)):
                members.append(_draw(ring, archetype, position, seed=seed))
                position += 1
    return Cohort(seed=seed, members=tuple(members))


def _draw(
    ring: Ring, archetype: Archetype, position: int, *, seed: int
) -> CohortMember:
    handle = f"cohort-{ring.code}-{position:02d}"
    plays_both = position % EVERY_NTH_PLAYS_BOTH_SPORTS == PLAYS_BOTH_SPORTS_AT
    sports = SPORTS if plays_both else SPORTS[:1]
    newcomer = position % EVERY_NTH_IS_A_NEWCOMER == IS_A_NEWCOMER_AT
    low, high = (
        NEWCOMER_COMMITTED_DAYS_AGO if newcomer else SETTLED_COMMITTED_DAYS_AGO
    )
    return CohortMember(
        handle=handle,
        ring=ring.code,
        archetype=archetype.name,
        latitude=ring.latitude,
        longitude=CENTRE_LONGITUDE,
        radius_km=(
            SEARCH_RADIUS_BOUNDS.minimum_km
            if _is_lopsided(position)
            else _rng(handle, "radius", seed).randint(*MEMBER_RADIUS_KM)
        ),
        slots=_slots(handle, position, seed),
        tags=_tags(handle, position, seed),
        intents=tuple(
            (sport.value, INTENT_CYCLE[(position + index) % len(INTENT_CYCLE)].value)
            for index, sport in enumerate(sports)
        ),
        gender=GENDER_CYCLE[position % len(GENDER_CYCLE)].value,
        gender_preference=_preference(position),
        proposals_opt_in=position % EVERY_NTH_HAS_OPTED_OUT != HAS_OPTED_OUT_AT,
        committed_days_ago=_rng(handle, "committed", seed).randint(low, high),
        claims=archetype.answers.claims,
        demonstrations=archetype.answers.demonstrations,
        claim_spread=archetype.answers.claim_spread,
        demonstration_spread=archetype.answers.demonstration_spread,
    )


def _rng(handle: str, axis: str, seed: int) -> random.Random:
    """One member's draw on one axis. **Keyed, never sequenced.**

    ``random.Random`` seeded with a string hashes it with SHA-512 first, so this
    is stable across processes and unaffected by ``PYTHONHASHSEED`` — which is
    the property ``docs/adr/0105`` asks to be demonstrated rather than assumed.
    """

    return random.Random(f"{seed}|{handle}|{axis}")


def _slots(handle: str, position: int, seed: int) -> tuple[str, ...]:
    """A week that overlaps the protagonist's, unless this member is the n-th.

    The overlap is a **rule** and the rest of the week is a draw: a drawn overlap
    at this size is a fixture where the availability term sometimes has nothing
    to read, and *sometimes* is the one thing a workbench may not be.
    """

    rng = _rng(handle, "slots", seed)
    if _is_lopsided(position):
        return CELLS
    if position % EVERY_NTH_SHARES_NO_WEEK == SHARES_NO_WEEK_AT:
        elsewhere = [cell for cell in CELLS if cell not in PROTAGONIST_CELLS]
        return tuple(
            sorted(rng.sample(elsewhere, rng.randint(*MEMBER_CELLS_ELSEWHERE)))
        )
    shared = rng.sample(PROTAGONIST_CELLS, SHARED_CELLS_FLOOR)
    rest = [cell for cell in CELLS if cell not in shared]
    extra = rng.sample(rest, rng.randint(*MEMBER_EXTRA_CELLS))
    return tuple(sorted(set(shared) | set(extra)))


def _is_lopsided(position: int) -> bool:
    """Whether this member scores the searcher far lower than the searcher does.

    A rule and never a draw, for the reason every coverage rule here is one: at
    this size the arms that fire rarely are the arms a draw misses entirely.
    """

    return position % EVERY_NTH_IS_LOPSIDED == IS_LOPSIDED_AT


def _tags(handle: str, position: int, seed: int) -> tuple[str, ...]:
    """Tags drawn from the served vocabulary, half of them sharing one.

    Sorted, because the order of a tag list is not a fact about the player and an
    unsorted sample would put a draw order into the committed file.
    """

    rng = _rng(handle, "tags", seed)
    drawn = set(rng.sample(TAGS, rng.randint(*MEMBER_TAG_COUNT)))
    if position % 2 == 0:
        drawn.add(rng.choice(PROTAGONIST_TAGS))
    return tuple(sorted(drawn))


def _preference(position: int) -> str:
    """Whose preference excludes the default protagonist, by rule.

    She is a woman, so a member who will only play men is a member the **mutual**
    gate removes from her list without the scorer ever seeing them — which is
    exactly the gate nothing on a screen can show.
    """

    if position % EVERY_NTH_EXCLUDES_THE_PROTAGONIST == EXCLUDES_THE_PROTAGONIST_AT:
        return GenderPreference.MEN_ONLY.value
    return GenderPreference.ANY.value


# ---------------------------------------------------------------------------
# The claim: a histogram, and never a μ
# ---------------------------------------------------------------------------

#: How many members must end in each band, as a **range**. Checked against the
#: **stored** ratings on every run, including one that creates nothing.
#:
#: **A histogram and never a μ.** A μ claim pins the engine: a retune that moved
#: every level by a tenth would fail a fixture whose only complaint is that the
#: engine changed, which is not a defect. What a *band* claim catches is the
#: thing that matters to a screen — a band emptying is a state nobody can reach
#: any more, and a band swallowing the population is a pool of identical cards.
#:
#: The ranges are wide where the arithmetic is near an edge and tight where it is
#: not, and none of them is the number the run happens to produce today: an
#: assertion equal to the observation is an assertion that fails on every change
#: and diagnoses none of them.
BAND_HISTOGRAM: Final[Mapping[str, tuple[int, int]]] = {
    BAND_NEW: (3, 8),
    BAND_DEVELOPING: (5, 12),
    BAND_ESTABLISHED: (26, 40),
    BAND_ADVANCED: (2, 8),
}


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def as_document(cohort: Cohort) -> dict[str, object]:
    """The artifact's shape, with every key in a stated order.

    The header says what the fixture is for **on the artifact itself**, because
    somebody reading a diff a year from now is reading this file and not this
    docstring — and the one thing they must not conclude is that these numbers
    describe a city.
    """

    return {
        "what_this_is": (
            "A development workbench: a population chosen so that every Play "
            "screen state is reachable. It stands for nothing outside itself "
            "and describes no real market. The comparator corpus is "
            "docs/specs/matchmaking/ruleset-diff/, and it answers a different "
            "question."
        ),
        "inputs_only": (
            "No member's level, uncertainty or band is recorded here: those are "
            "the engine's answers to the questionnaire each member sits, and a "
            "committed copy of an answer is a number nothing keeps honest. The "
            "band names that do appear are declarations — which band an "
            "archetype aims at, and the histogram the run checks the engine's "
            "answers against."
        ),
        "seed": cohort.seed,
        "sports": [sport.value for sport in SPORTS],
        "centre": {"latitude": CENTRE_LATITUDE, "longitude": CENTRE_LONGITUDE},
        "rings": [
            {
                "code": ring.code,
                "reason": ring.reason,
                "latitude": ring.latitude,
                "kilometres": round(_distance_of(ring), 2),
                "members": dict(sorted(ring.members.items())),
            }
            for ring in RINGS
        ],
        "archetypes": [
            {
                "name": archetype.name,
                "aims_at_band": archetype.band,
                "claims": archetype.answers.claims,
                "demonstrations": archetype.answers.demonstrations,
                "claim_spread": archetype.answers.claim_spread,
                "demonstration_spread": archetype.answers.demonstration_spread,
            }
            for archetype in ARCHETYPES
        ],
        "band_histogram": {
            band: list(bounds) for band, bounds in BAND_HISTOGRAM.items()
        },
        "members": [_member_document(member) for member in cohort.members],
    }


def _member_document(member: CohortMember) -> dict[str, object]:
    document = asdict(member)
    document["stable_id"] = str(member.stable_id)
    # **A declared input restated, never an engine answer.** ADR-0113's window
    # is what `committed_days_ago` is written against, and a reader following a
    # diff should not have to hold fourteen in their head to see who moved
    # across it.
    document["newcomer"] = member.is_a_newcomer
    document["slots"] = list(member.slots)
    document["tags"] = list(member.tags)
    document["intents"] = [list(pair) for pair in member.intents]
    return document


def write(cohort: Cohort, path: Path = ARTIFACT) -> Path:
    """Write the population as the committed artifact. **Stable bytes.**"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(as_document(cohort), indent=2) + "\n")
    return path


def _distance_of(ring: Ring) -> float:
    return distance_km(
        Point(latitude=CENTRE_LATITUDE, longitude=CENTRE_LONGITUDE),
        Point(latitude=ring.latitude, longitude=CENTRE_LONGITUDE),
    )


# ---------------------------------------------------------------------------
# Refusals, at import
# ---------------------------------------------------------------------------


def _refuse_an_impossible_cohort(cohort: "Cohort") -> None:
    """Fail at import rather than part-way through a run.

    Everything here is a property the *declarations* have to hold before a single
    account is written, and each of them is a way this fixture could stop being a
    workbench while still generating happily: a ring that no longer sits where
    the ladder puts it, an archetype without a band, two members at one handle.
    """

    names = [archetype.name for archetype in ARCHETYPES]
    if len(names) != len(set(names)):
        raise RuntimeError("two cohort archetypes share a name")

    bands = [archetype.band for archetype in ARCHETYPES]
    if len(bands) != len(set(bands)):
        raise RuntimeError(
            "two cohort archetypes aim at one band. An archetype is one per "
            "band: a second is a distribution the histogram cannot read."
        )
    if set(bands) != set(BAND_HISTOGRAM):
        raise RuntimeError(
            "the archetypes and the band histogram disagree about which bands "
            f"exist: {sorted(set(bands))} against {sorted(BAND_HISTOGRAM)}."
        )

    known = {archetype.name for archetype in ARCHETYPES}
    for ring in RINGS:
        distance = _distance_of(ring)
        low, high = ring.bounds_km
        if not low < distance <= high:
            raise RuntimeError(
                f"ring '{ring.code}' sits {distance:.2f} km from the centre and "
                f"is declared for {low:.2f}–{high:.2f} km. The rings are cut by "
                f"the relaxation ladder's own multipliers, so a ring in the "
                f"wrong place is a rung that finds nobody new."
            )
        unknown = set(ring.members) - known
        if unknown:
            raise RuntimeError(
                f"ring '{ring.code}' is populated with archetypes that do not "
                f"exist: {sorted(unknown)}"
            )

    near = NEWCOMER_COMMITTED_DAYS_AGO[1]
    far = SETTLED_COMMITTED_DAYS_AGO[0]
    if not near < NEWCOMER_WINDOW_DAYS < far:
        raise RuntimeError(
            f"the cohort's two commit windows do not straddle ADR-0113's "
            f"{NEWCOMER_WINDOW_DAYS} days: newcomers reach {near} and settled "
            f"members start at {far}. Both edges have to be clear of it, so "
            f"that a change to the window moves the fraction rather than the "
            f"arithmetic of one edge case."
        )

    handles = [member.handle for member in cohort.members]
    if len(handles) != len(set(handles)):
        raise RuntimeError("two cohort members share a handle")
    for member in cohort.members:
        if not SHARED_CELLS_FLOOR <= len(member.slots) <= len(CELLS):
            raise RuntimeError(f"'{member.handle}' has a week of {len(member.slots)}")
        if not SEARCH_RADIUS_BOUNDS.contains(member.radius_km):
            raise RuntimeError(
                f"'{member.handle}' set a radius of {member.radius_km} km, "
                f"which the slider does not offer."
            )


#: The one cohort this system seeds, drawn at import so that the generator, the
#: committed artifact and the run all read one object — and drawn **once**,
#: because the refusal below reads the same draw rather than making its own.
COHORT: Final = generate()

_refuse_an_impossible_cohort(COHORT)
