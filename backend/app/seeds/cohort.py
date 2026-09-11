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

**The population is committed as inputs only** — never μ, never σ, never a band,
and, since the played history arrived, never a Player Score, a counted-game count
or a run of form either. Those are the engine's and the platform's answers, and a
committed copy of an answer is a second number nothing keeps honest. What *is*
committed about a game is who played whom and who won, which is what a player
did. What makes the file worth committing is the keying:
every draw is a function of the member's **handle** alone, so adding or removing
one member changes that row and nobody else's and the diff is readable. The
played history is the one thing that is *also* an input to a row rather than only
a row of its own — a member's second sport and an organiser's radius follow from
the games they are declared to play — and the keying survives it, because a game
names its players by handle: adding one moves the rows of the people in it and
nobody else's. Under one
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
from dataclasses import asdict, dataclass, replace
from math import ceil
from pathlib import Path
from typing import Final, Mapping, Sequence, final
from uuid import NAMESPACE_URL, UUID, uuid5

from app.kernel import Sport
from app.modules.challenges.domain.seats import seats_per_side
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.sportsmanship.domain.window import (
    CARD_OPENS_AFTER,
    CARD_STAYS_OPEN_FOR,
)
from app.modules.matchmaking.domain.geography import Point, distance_km
from app.modules.player_profile.domain.availability import DAYS_IN_THE_GRID, DayPart
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_SELECTION_BOUNDS,
    SocialTag,
)
from app.seeds.clock import NEWCOMER_WINDOW_DAYS
from app.seeds.catalog import (
    COHORT_SURNAMES,
    dealt_name,
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
    THE_POPULATED_PLAYER,
    AnswerPolicy,
)
from app.seeds.photos import DeclaredVerdict

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
        reason=(
            "past the ladder's furthest rung and inside the slider's ceiling — "
            "which is why the played history's opponents live here"
        ),
        latitude=51.80,
        bounds_km=(PROTAGONIST_RADIUS_KM * 2.0, float(SEARCH_RADIUS_BOUNDS.maximum_km)),
        # **Eight club players and not three, and the five extra are the played
        # history's.** A member the cohort plays a *second sport* against holds a
        # rating in it, and a second-sport rating inside the protagonist's
        # furthest rung thickens the very list the ladder is priced on — five
        # rows and the rungs stop being computed at all. This ring is the one
        # place a member can hold a tennis rating without being reachable by any
        # widening she is offered, which is what its own reason line already
        # says. Eight, because the opponents have to be **distinct** and this
        # ring already spends one on the improver, one on the member whose
        # preference excludes the searcher, one on the lopsided witness and one
        # on a newcomer too recent to have played: one open challenge per pair,
        # and nothing ends a challenge every seat accepted.
        members={CLUB_PLAYER.name: 8, IMPROVER.name: 1},
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

#: Every n-th member is a **close match**: the protagonist's whole vocabulary
#: and most of her week, rather than the floor of two cells and the one lucky
#: tag everybody else is drawn with.
#:
#: **The arm this fixture was missing, and the one that makes ⚡ a choice.**
#: Every other rule here widens the population *away* from her; nothing drew
#: anybody *towards* her, so the only rows clearing ``QUALITY_FLOOR`` against
#: her were the named accounts of ``catalog.py`` and ``relationships.py`` —
#: which are her **controls**, and therefore identical to each other and to her
#: on level, week, tags and address. Nine of them in one pool is nine
#: candidates at one μ: the evenest four is a tie between clones, so the engine
#: returned one court and one forecast whatever the search asked for, and a
#: developer reads that as a broken engine rather than as a fixture with no
#: second answer in it.
#:
#: A close match is drawn on level like everybody else — the point is a rival
#: to the clone block that is **not** a copy of it, so the four ⚡ fills differ
#: in strength and the balance forecast has something to say. Half the
#: population, because a court is four people and the arms above remove most of
#: any given member: opted out, gender-gated, no shared week, too far.
EVERY_NTH_IS_A_CLOSE_MATCH: Final = 2
IS_A_CLOSE_MATCH_AT: Final = 1

#: How much of her six-cell week a close match covers. **Five and not six**: a
#: member matching her exactly would be a sixteenth clone, and the availability
#: term would be back to having nothing to separate anybody by.
CLOSE_MATCH_CELLS: Final = 5

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
# What the platform has watched them do — the played history
# ---------------------------------------------------------------------------
#
# **A declaration and never a discovery, and it is committed as inputs only.**
# What is written down here is *who played whom and who won*, which is what a
# player did; the Player Score, the counted-game count and the run of form are
# what the platform makes of it, and a committed copy of one of those would be
# the second number this file exists to refuse.
#
# **A game is a real challenge, really accepted, with a result really entered**
# (``docs/adr/0029``). Nothing here opens a table, so the shape of this
# declaration is the shape the write path forces: a court is the sport's own
# fixed list of sides, a line-up completes only when **every** seat is accepted,
# and the game that follows is counted unless the search behind it was a
# *for fun* one. That is why a padel row seats four and a tennis row seats two —
# a padel court with one invitee is half a game and opens nothing.
#
# **One open challenge per pair, and it releases when they stop arranging.** A
# challenge whose seats were all accepted is `ON`: the arranging is finished, so
# the pair is released and two people who have played can be shown each other
# again (`docs/adr/0142` §1, #343). That was not true when these rows were
# chosen — the rule read *has this ended*, `ON` had not, and a played pair was
# gated for ever — so two of the three consequences below are now **kept rather
# than forced**, and the third has changed its reason:
#
# - **Five counted games still take five distinct opponents**, and the opponents
#   still sit where the fixture can afford them. Neither is forced any more;
#   both are kept, because rewriting them would move `cohort.json` and this
#   fixture's job is to reach states rather than to be minimal.
# - **No game names the protagonist, and the reason has inverted.** It used to be
#   that a game with her in it would take that person *out* of the pool every
#   assertion in ``screens.py`` is read from. Now it would put them back *in* —
#   carrying an `ACCEPTED` tally, which is `PREVIOUS_ACCEPT`, which
#   ``screens.py`` names in ``CANNOT_BE_DRAWN`` as absent from this cohort. Same
#   rule, opposite mechanism, and it is still the rule.


@final
@dataclass(frozen=True, slots=True)
class PlayedGame:
    """One game that really happened, as this fixture declares it.

    **Handles and never ids**, like every other row here: an id is minted by the
    write path and a fresh database mints a different one, so a game keyed on
    handles is a game that means the same thing in every database.

    ``side_a`` and ``side_b`` are the court as it was seated, and **``side_a[0]``
    organised it** — the send is one person's act, and the organiser's own seat
    is accepted from birth, which is why they are named by position rather than
    in a field of their own.

    ``won_by`` is ``None`` for the one game these people never agreed a score
    for. That is not a missing input: it is *an evening, not evidence*
    (``docs/adr/0137``) — the game counts toward how much they have played and
    produces an outcome for nobody, which is a card state a fixture with only
    tidy games could not reach.
    """

    sport: str
    #: How long before this run's own *now* it was played. **An input, and the
    #: only one here a redraw can invalidate**: a game cannot predate the profile
    #: of somebody who played it, and the members' commit dates are drawn. The
    #: refusal below reads both and names the member.
    played_days_ago: int
    side_a: tuple[str, ...]
    side_b: tuple[str, ...]
    #: ``"A"``, ``"B"``, or ``None`` where the two sides never agreed.
    won_by: str | None
    #: Whether anybody ever said *we played*. ``False`` is **a ghost**: the
    #: line-up completed, the evening came and went, nobody entered a score
    #: before the entry window closed, and the arrangement now reads as never
    #: played to everybody who looks at it.
    #:
    #: It is the one ending that is a *bad* outcome on a strand — *shows up* is
    #: played over played-plus-ghosted — and a fixture without one publishes
    #: nothing but full bars, which is a card whose whole point (a penalty you
    #: can look up and watch lift) has never been drawn.
    entered: bool = True
    #: Whether the side that was **asked** replied to the score at all.
    #: ``False`` is the score nobody answered: it confirms by silence anyway, so
    #: the game is scored and the run of form has its square, and the people who
    #: were asked carry an *ignored* against *answers about results*.
    #:
    #: **It is not disagreement.** Two sides who each state a score and neither
    #: accepts is ``won_by=None`` with this left ``True`` — both of them
    #: answered, and what is missing is agreement rather than an answer
    #: (``docs/adr/0137``). The refusal below will not let a row claim both.
    answered: bool = True

    @property
    def organiser(self) -> str:
        return self.side_a[0]

    @property
    def players(self) -> tuple[str, ...]:
        return self.side_a + self.side_b

    @property
    def was_scored(self) -> bool:
        return self.won_by is not None

    @property
    def was_a_ghost(self) -> bool:
        """Nobody claimed the evening, so the platform says it never happened.

        Read off ``entered`` rather than stored beside it, because *a ghost* is
        what the absence of an entry **means** and a second field saying so is a
        second place for the two to disagree.
        """

        return not self.entered

    @property
    def pairs(self) -> tuple[frozenset[str], ...]:
        """Everybody this court makes a pair of. **Sharing a line-up makes one.**

        Every occupied seat but your own is somebody you now have an open game
        with — co-invitees and organiser alike — so a doubles court spends six
        pairs and a singles one spends one. It is a property rather than three
        loops in three files because *what a court costs* is a fact about the
        court, and the three readers are the refusal that will not let two games
        share a pair, the report that prints the price, and the test that says
        so.
        """

        return tuple(
            frozenset({one, other})
            for index, one in enumerate(self.players)
            for other in self.players[index + 1 :]
        )


#: How far apart the played games sit, and why they are not all on one day.
#:
#: *Last 5* is read **oldest to newest**, and the provider orders it on the
#: instant each game was played — so two games on one day would leave the run of
#: form to a tie-break on a uuid, and a fixture whose row of squares reshuffles
#: between databases is a fixture nobody can develop a screen against.
#:
#: The floor is two days rather than one: a result confirmed by **silence** needs
#: its window to have closed, and the game left unscored needs both sides' to
#: have. A game seeded an hour ago would be a game still awaiting an answer,
#: which is a different card.
PLAYED_AT_LEAST_DAYS_AGO: Final = 2

#: How long ago an arrangement has to have been made before **nobody claiming
#: it** reads as a ghost rather than as a game still awaiting its entry.
#:
#: **Derived from the window and never typed.** A plan has an ordinary week to
#: become a game and a day's grace after it, so the honest floor is eight days
#: and one more on top — read off ``games``' own constants, so a horizon that
#: moves takes this with it instead of leaving a fixture quietly declaring a
#: ghost the platform still calls ``AWAITING_ENTRY``. Which is exactly what a
#: typed seven did: the record published *shows up 5 of 5*, the bar was full,
#: and nothing failed.
GHOSTED_AT_LEAST_DAYS_AGO: Final = (PLAN_HORIZON + ENTRY_GRACE).days + 1

#: **The played history, and the states each row is for.** Every one of them is
#: a row on the card of somebody in the protagonist's own padel pool, because a
#: record nobody can be shown is a record no screen renders.
#:
#: - ``cohort-a-12`` plays **five tennis singles**, so *Last 5* is full and the
#:   run of form is a mix rather than five identical squares. Tennis, because a
#:   singles court is two people and five counted games in padel would cost
#:   fifteen distinct partners — every spare pair the nearest ring has, and the
#:   full four ``screens.py`` composes with them.
#: - ``cohort-a-16`` plays **two padel doubles**, so the card draws a count of
#:   two with a run of one and the **gap** rather than a padded row.
#: - The second of those two is the one nobody agreed a score for, which is what
#:   puts ``cohort-a-13`` and ``cohort-a-14`` on a card with a **count and no
#:   run** — the state an unscored evening leaves behind.
#: - ``cohort-a-05``, ``cohort-a-06`` and ``cohort-a-07`` are named nowhere here,
#:   so the blocks are **absent** on their cards and the empty card is proved
#:   correct on a real read rather than assumed.
#:
#: The opponents of the five are **past the ladder's furthest rung**, in ring d,
#: and that is forced rather than chosen. A member who has played tennis holds a
#: tennis rating; the protagonist's tennis list is short *by construction* and
#: the ladder is priced only while it stays under ``MIN_SHORTLIST``; and every
#: rung she is offered widens her radius to at most twice it. So a second-sport
#: opponent anywhere inside that reach would silently take the ladder away —
#: which is the ring's own stated reason for existing, read the other way round.
PLAYED_GAMES: Final[tuple[PlayedGame, ...]] = (
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=7,
        side_a=("cohort-a-12",),
        side_b=("cohort-d-01",),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=6,
        side_a=("cohort-a-12",),
        side_b=("cohort-d-02",),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=5,
        side_a=("cohort-a-12",),
        side_b=("cohort-d-04",),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=4,
        side_a=("cohort-a-12",),
        side_b=("cohort-d-08",),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=3,
        side_a=("cohort-a-12",),
        side_b=("cohort-d-07",),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=4,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-10", "cohort-a-11"),
        won_by="A",
    ),
    # **The one nobody scored.** Both sides put a score on the table, neither
    # side accepted the other's, and both windows have since closed.
    PlayedGame(
        sport=Sport.PADEL.value,
        played_days_ago=2,
        side_a=("cohort-a-16", "cohort-a-12"),
        side_b=("cohort-a-13", "cohort-a-14"),
        won_by=None,
    ),
)

#: Every member the played history names in a sport their draw did not already
#: give them. **You cannot play a sport nobody assessed you in**, so the
#: declaration feeds the draw rather than sitting beside it and being true by
#: luck: a member here sits the questionnaire for that sport like everybody else.
SECOND_SPORT_BECAUSE_THEY_PLAYED: Final[frozenset[str]] = frozenset(
    handle
    for game in PLAYED_GAMES
    if game.sport != SPORTS[0].value
    for handle in game.players
)

# ---------------------------------------------------------------------------
# The protagonist's own played history — the record she reads about herself
# ---------------------------------------------------------------------------
#
# **A second list rather than more rows in the first, because they answer
# different questions.** ``PLAYED_GAMES`` exists so that the *cards in her pool*
# reach every state a card can be in — a full run, a gap, a count with no run, an
# absence. These exist so that **her own record sheet** is not empty: `SH.player`
# opened on your own face is titled *How others see you*, and a sheet that says
# nothing is a sheet nobody can develop against.
#
# Three properties are load-bearing and each is checked below:
#
# - **She is never the organiser**, and is always ``side_b[0]``. The organiser's
#   own seat is accepted at birth, so an organiser answers no invitation and
#   would have no *answers challenges* strand at all; and the side that *states*
#   the score is asked nothing, so a protagonist on side A would have no *answers
#   about results* strand either. Both strands exist because of where she sits.
# - **Every opponent is a cohort member whose own drawn radius already reaches
#   the centre**, so nothing here feeds ``_how_far_they_have_to_see`` and not one
#   member's draw moves. That is the whole reason this list can be added without
#   rewriting ``cohort.json``: the population is untouched and only the events
#   written over it are new.
# - **One sport, and every opponent already holds it.** Nothing here may reach
#   ``SECOND_SPORT_BECAUSE_THEY_PLAYED``, because that feeds the draw and the
#   draw is the artifact — so a row may only name somebody the population
#   already rated in that sport. Her *padel* record staying empty is the same
#   absence the sheet is built to spell, seen from the inside: the record card
#   is one record for the whole player, and only the run of form is per sport.
#
# **A pair may play twice, and this list is the first thing that does.** A
# completed line-up releases its pair (``docs/adr/0142`` §1, #343), so two people
# who have played can be shown each other and challenged again — which is what
# lets three opponents carry five counted games, and therefore what lets
# *opponent variety* print anything but ``100%``. It is also why the writer
# identifies an already-written game **and an already-sent court** by the day as
# well as the line-up: by line-up alone, the second evening with the same person
# is the first one.
#
# **It does not move ``PREVIOUS_ACCEPT``, and the reason is the first bullet
# again.** That signal is *they said yes to you before* — **a price on their
# card, off their own answers, never off the reader's**. She is the invitee on
# every one of these rows, so the accept is hers: the tally it leaves sits on
# **her** card in *their* pool, and their cards in hers carry nothing. Seating
# her on side A would move the tally and cost her two strands, which is the trade
# the first bullet already refuses. So the code stays in ``CANNOT_BE_DRAWN`` in
# ``screens.py``, with a narrower reason than it had.

#: The one account these rows seat besides the cohort. Read off the catalog
#: rather than spelled, so the address and the handle cannot drift apart.
PROTAGONIST_HANDLE: Final = THE_POPULATED_PLAYER.slug

#: Where she sits in the ring geometry: on the **centre** the rings are cut
#: around, which is not one of them. It is a code rather than a ``Ring`` because
#: a ring declares bounds and a membership and the centre has neither — what it
#: has is a latitude, which is all ``_distance_between`` ever reads.
PROTAGONIST_RING: Final = "centre"

#: Who she is declared to play. **Members who hold this sport, who declared it
#: competitively, and whose own drawn radius already reaches the centre** — all
#: three read off the committed population rather than arranged for.
#:
#: The last clause is what keeps this list free: an opponent who could not
#: already see her would have to be *given* a radius, and a member's radius is
#: part of the draw. Four members clear all three bars and only three are here:
#: `cohort-d-07`'s own search never returns her on a fresh database, on the level
#: gate, and that is the one bar a declaration cannot check.
PROTAGONISTS_OPPONENTS: Final = (
    "cohort-a-12",
    "cohort-c-00",
    "cohort-d-08",
)

#: On a singles court the organiser is the **only** other person, so everybody
#: she plays organises. Kept as its own name rather than folded into the one
#: above, because the two say different things — *who may be seated* and *whose
#: search has to find her* — and a doubles row would separate them again.
PROTAGONISTS_ORGANISERS: Final = PROTAGONISTS_OPPONENTS

#: **Her record, as the six evenings behind it.** Read down the endings rather
#: than the scores: they are chosen so that every figure on her sheet is a
#: fraction somebody could *work off* rather than a full bar.
#:
#: - Six arrangements, five of them played: the oldest is **a ghost** — the
#:   line-up completed, nobody ever said it happened, and the entry window closed
#:   over it. *Shows up* reads 5 of 6.
#: - Every invitation answered, so *answers challenges* reads 6 of 6. A lapsed
#:   seat would dock it and there is no way to declare one here: a lapse is a
#:   fact about a **challenge** nobody answered, and this file declares games.
#: - Five scores put to her side and one of them ignored — the three-day-old
#:   row, which confirms by silence anyway and still draws its square. *Answers
#:   about results* reads 4 of 5.
#: - Three distinct people over five counted games, so *opponent variety* prints
#:   ``60% · 3 of 5`` rather than the ``100%`` every card in this fixture printed
#:   while no pair could play twice.
#: - The run of five is **full** and reads ``W L W L W``: mixed, which is the
#:   only row of squares a reader can read a mistake off.
#:
#: **Tennis and singles, and both are forced.** A padel row is a doubles court,
#: so its organiser's one search has to return *three* named people before the
#: shortlist fills — and it does not: an organiser whose radius reaches the
#: centre also reaches the eleven relationship accounts, which are clones of the
#: protagonist and outscore their own ring. A singles court asks the search for
#: one person, which is the difference between a fixture that writes and one that
#: fails half way through with a message about a pool. Tennis, because tennis is
#: this platform's singles sport.
#:
#: **Every organiser here was measured against a *fresh* database**, and that is
#: not a formality: a fourth member passes this list's every declared rule and
#: their search never returns her, because the level gate reads a rating that has
#: not moved yet. On a database where her counted games already exist it does
#: return her, which is a fixture that writes on the second run and fails on the
#: first.
#:
#: **Nothing here moves the draw.** Every opponent already holds tennis, so
#: ``SECOND_SPORT_BECAUSE_THEY_PLAYED`` is unchanged; every one of them was
#: already drawn a radius that reaches the centre, so no member is re-drawn. The
#: committed population is byte-identical with this list added, which is the
#: property that lets it exist beside a fixture every screen assertion is read
#: from.
#:
#: **The two oldest days are derived from the entry window**, so a horizon that
#: moves takes the ghost and the row beside it with it. The rest are typed, and
#: the refusal reads the cohort's own history as well as this one: `cohort-a-12`
#: is already playing on every day from two to seven, and a member on two courts
#: at one instant leaves *Last 5* to a tie-break on a uuid.
PROTAGONIST_GAMES: Final[tuple[PlayedGame, ...]] = (
    # **The ghost.** Nobody claimed the evening and the entry window closed over
    # it, so the platform reads it as never played — which also means there is
    # nobody to rate for it, and the sportsmanship layer skips it by asking the
    # same question the card does. It is also the one row outside the
    # sportsmanship card's own week, which is the same fact from the other side.
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=GHOSTED_AT_LEAST_DAYS_AGO + 1,
        side_a=("cohort-c-00",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by=None,
        entered=False,
    ),
    # **`cohort-a-12` plays her once and it has to be here.** Every day inside
    # the fixture's own window is spent on the cohort's five tennis singles, and
    # this is the first one clear of them. It is outside the sportsmanship card's
    # week as a result, which is why nobody declares what they thought of her.
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=GHOSTED_AT_LEAST_DAYS_AGO,
        side_a=("cohort-a-12",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="B",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=6,
        side_a=("cohort-c-00",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="A",
    ),
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=5,
        side_a=("cohort-d-08",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="B",
    ),
    # **The one she never answered.** The score stands — silence confirms it —
    # so the square is drawn and the dock lands on the strand rather than on the
    # result.
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=3,
        side_a=("cohort-c-00",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="A",
        answered=False,
    ),
    # **The oldest of the played ones, and it is oldest because of a later layer.** It
    # sat two days ago until `pool_history.py` needed her evenings inside the card's
    # week; her tennis history holds every day it can, so the one that moved is the one
    # whose opponent had a free day this far back. It is outside the card's week now,
    # which costs nothing: the rating `cohort-d-08` gives her lands on the five-day-old
    # court they also share.
    PlayedGame(
        sport=Sport.TENNIS.value,
        played_days_ago=11,
        side_a=("cohort-d-08",),
        side_b=(PROTAGONIST_HANDLE,),
        won_by="B",
    ),
)

#: Every arrangement this seed writes, in one tuple, for the readers that do not
#: care whose record it is for: the writer, which walks it oldest first, and the
#: refusals below, which ask *who shared a court with whom* across both lists.
#:
#: The sportsmanship layer is **not** one of them, deliberately — it asks the
#: database which courts a rater actually has rather than re-deriving them from
#: here, so a declaration cannot name an evening the run failed to write.
EVERY_PLAYED_GAME: Final[tuple[PlayedGame, ...]] = PLAYED_GAMES + PROTAGONIST_GAMES


# ---------------------------------------------------------------------------
# What other players said — the one thing on the record people wrote
# ---------------------------------------------------------------------------
#
# **A declaration, like a score is**, and for the same reason: a tap is a thing a
# player did. What is *not* here is the average, the count or the band — those
# are the fold `sportsmanship` takes over these rows, and a committed copy of one
# of them would be the second number this file exists to refuse.
#
# **Keyed by the person it is about, and then by who said it.** That is the order
# the record reads in — *what other players said about them* — and it makes the
# one property that matters legible in the diff: only a rater's **most recent**
# answer about somebody counts, so a subject's figure rests on as many people as
# there are keys under them and never on how often they played.
#
# **Where a card lands is not declared and is read back.** A rater answers a card
# **per court**, and these rows say only what they thought of the person; the
# writer walks their real settled courts and puts the stars on the most recent
# one they shared. So a declaration cannot name a court that does not exist, and
# a game moving a day does not have to be chased through this table.
#
# **Silence is most of it and is deliberate.** Nobody is obliged to answer a
# card, and not answering leaves no record of the omission — so a subject with no
# key here is a subject the record omits the zone for entirely, which is the
# fourth absence `SH.player` has to be able to draw. `cohort-a-10` and
# `cohort-a-11` are named by nobody for exactly that reason.

#: The bounds a tap may fall between, spelled here so a fixture cannot declare
#: something the domain would refuse half way through a run. Not imported from
#: ``sportsmanship``: this file declares inputs and importing a module's domain
#: to validate a fixture is a dependency the fixture does not need — the
#: refusal below is what keeps the two honest, and the use case refuses again.
STARS_ARE_ONE_TO_FIVE: Final = (1, 5)

#: How old the evening behind a declared rating may be. **The card's own week**,
#: read off ``sportsmanship``'s constants rather than typed: the card opens the
#: day after and stays open a week, so an evening older than that is one nobody
#: was ever shown a card for.
#:
#: ``AnswerTheCard`` would accept it — the window decides when somebody is
#: *asked*, and refusing a player who tapped submit a minute after their card
#: lapsed is not a thing this platform does — so nothing would fail and the
#: fixture would quietly be declaring an opinion no player could have given. It
#: is the reason ``cohort-a-12`` plays her and says nothing about it.
RATED_WITHIN_DAYS: Final = (CARD_OPENS_AFTER + CARD_STAYS_OPEN_FOR).days

#: **What each of these people was told about them, out of five.**
#:
#: - The protagonist rests on **two raters at 4,5**. Two rather than three,
#:   because her evening with ``cohort-a-12`` is nine days old and **the card
#:   closes after a week** — a rating written for it would be one nobody was ever
#:   shown the card to give. She never sees the figure anyway: her own sheet is
#:   titled *How others see you* and shows the coarse band instead
#:   (``docs/adr/0158``), so the figure is what a *reader* of her record gets and
#:   the band is what she gets.
#: - ``cohort-a-12`` rests on **three at 4,0** and ``cohort-a-16`` on **two at
#:   3,5** — a middling figure and a small count, because a card that only ever
#:   drew 4,5 over two would never show what a fuller record looks like.
#: - ``cohort-a-08`` rests on **one rater at 5,0**, which is the state the
#:   contract calls out by name: ``5,0 / 5 · 1 player`` is visibly one person's
#:   opinion and reads as one, which is why the count is never separable from
#:   the figure.
#: - Nobody has said anything about ``cohort-a-10``, ``cohort-a-11`` or
#:   ``cohort-a-13``, so their records omit the zone. **That is the state most
#:   players are in** and it is the one an empty fixture would leave unproved.
WHAT_PLAYERS_SAID: Final[Mapping[str, Mapping[str, int]]] = {
    PROTAGONIST_HANDLE: {
        "cohort-c-00": 5,
        "cohort-d-08": 4,
    },
    "cohort-a-12": {
        "cohort-d-01": 4,
        "cohort-d-02": 4,
        "cohort-d-04": 4,
    },
    "cohort-a-16": {
        "cohort-a-13": 3,
        "cohort-a-14": 4,
    },
    "cohort-a-08": {
        "cohort-a-16": 5,
    },
}

#: The three photographs, and the three answers ``docs/adr/0138`` lets a card
#: draw about one. **Three rows and not a rate**, for the reason every coverage
#: rule here is a rule: the third state is an *absence*, and a draw that happened
#: to produce two of the three would leave the shield unprovable on the one
#: reading that matters.
#:
#: The bytes are the seed's own and the verdict is **declared**, which is the
#: same move the run already makes with the clock: the reviewer is a port, a
#: seeded photo is not a photograph of a real court, and a fixture that asked a
#: model what it thought would exhibit whichever states that model happened to
#: reach. What is *not* declared is the metadata: the note is written by the
#: domain's own constructors, so a shield here is a shield ``decision_on_record``
#: agrees to believe rather than a string this file spelled.
#:
#: All three are members of the nearest ring, because a verdict is drawn on a
#: **card** and a card is a row of the protagonist's own pool.
PHOTOGRAPH_VERDICTS: Final[Mapping[str, DeclaredVerdict]] = {
    "cohort-a-05": DeclaredVerdict.ON_A_COURT,
    "cohort-a-07": DeclaredVerdict.NOT_A_COURT,
    "cohort-a-13": DeclaredVerdict.NOBODY_LOOKED,
}


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
    #: Which of ``docs/adr/0138``'s three answers this member's photograph
    #: carries, or ``None`` for the great majority who hold none. An **input**
    #: like every field beside it: what a check concluded about a photograph is
    #: a thing this fixture chooses, and the card the conclusion reaches is what
    #: ``app/seeds/screens.py`` reads back.
    photograph: str | None = None
    #: What every screen draws for this member. ``handle`` stays the identifier
    #: — the address, the answer key and the ring's own numbering are all it —
    #: and this is the only thing a person ever sees. Committed with the rest of
    #: the row, because a name is an input like the week and the tags are.
    name: str = ""

    @property
    def sports(self) -> tuple[Sport, ...]:
        return tuple(Sport(sport) for sport, _ in self.intents)

    @property
    def declared_verdict(self) -> DeclaredVerdict | None:
        """``photograph`` as the type the run declares in.

        The artifact spells it as a string because it is committed JSON; every
        reader here wants the enum, which is the same trade ``intents`` makes one
        field along.
        """

        return None if self.photograph is None else DeclaredVerdict(self.photograph)

    @property
    def email(self) -> str:
        return f"{self.handle}@{SEED_EMAIL_DOMAIN}"

    @property
    def nickname(self) -> str:
        """The name this member is shown under. **The handle is the id, not the
        name** — see ``catalog.FIRST_NAMES``."""

        return self.name

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
    return Cohort(seed=seed, members=_named(members))


def _named(members: Sequence[CohortMember]) -> tuple[CohortMember, ...]:
    """One name each, dealt **by sorted handle** out of the cohort's own pool.

    Sorted rather than drawn, and dealt over the whole population rather than
    per ring, because a name has to be unique across all of them and a keyed
    draw collides: two members under one nickname is a unique-constraint
    violation found half way through a seed run.

    Sorted by handle, so the deal is a function of *which members exist*. A
    member added to a ring renames the members after them **within that ring's
    block of the sorted order** and nobody in an earlier ring — the same
    trade the module note already makes for the draws, and the reason the
    handles are zero-padded.

    The pool is disjoint from the catalog's and the relationships' by surname
    (``catalog.FIRST_NAMES``), so no cohort member can ever collide with a named
    account however either list grows.
    """

    order = sorted(one.handle for one in members)
    return tuple(
        replace(
            one, name=dealt_name(order.index(one.handle), COHORT_SURNAMES)
        )
        for one in members
    )


def _draw(
    ring: Ring, archetype: Archetype, position: int, *, seed: int
) -> CohortMember:
    handle = f"cohort-{ring.code}-{position:02d}"
    plays_both = (
        position % EVERY_NTH_PLAYS_BOTH_SPORTS == PLAYS_BOTH_SPORTS_AT
        # **A member who has played a sport holds a rating in it.** The played
        # history is a declaration and the questionnaire is the only door to a
        # Level, so the declaration has to reach the draw — otherwise the game
        # would be written against a member the level gate removes from their own
        # opponent's search, and the seed would fail naming a pool.
        or handle in SECOND_SPORT_BECAUSE_THEY_PLAYED
    )
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
        radius_km=_radius(handle, position, seed),
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
        photograph=_photograph(handle),
    )


def _photograph(handle: str) -> str | None:
    """Which verdict this member's photograph carries, if they hold one.

    A lookup rather than a draw, and it is the same argument every coverage rule
    on this page makes: the third state is an **absence** on the wire, so a rate
    that happened to produce two of the three would leave *flagged* and *never
    checked* indistinguishable and nothing would say so.
    """

    declared = PHOTOGRAPH_VERDICTS.get(handle)
    return None if declared is None else declared.value


def _radius(handle: str, position: int, seed: int) -> int:
    """The radius this member sets for themselves, and who does not get a draw.

    **An organiser's radius is a rule, and the rule is *your own opponents and
    nobody else*.** A court is built from a search and a search hands back at
    most ``shortlist_max`` rows, so an organiser searching wide fills that list
    with people this fixture never declared — the relationship accounts sit at
    the centre and are clones of the protagonist, and they outscore a member's
    own ring on every term a clone can win. The declared opponent then falls off
    the end of the list, and the send has no origin to cite. So an organiser is
    given the **tightest radius the slider offers that still reaches everybody
    they play**: within a ring every member sits at one coordinate, so a
    same-ring court is searched at the slider's floor and nobody from anywhere
    else is in the way.

    Everybody else keeps what they had: the floor if they are the lopsided one,
    and a keyed draw otherwise.
    """

    reach = _how_far_they_have_to_see(handle)
    if reach is not None:
        return min(
            SEARCH_RADIUS_BOUNDS.maximum_km,
            max(SEARCH_RADIUS_BOUNDS.minimum_km, ceil(reach)),
        )
    if _is_lopsided(position):
        return SEARCH_RADIUS_BOUNDS.minimum_km
    return _rng(handle, "radius", seed).randint(*MEMBER_RADIUS_KM)


def _how_far_they_have_to_see(handle: str) -> float | None:
    """The furthest opponent this member is declared to organise against.

    ``None`` for the great majority, who organise nothing. The ring is read off
    the **handle** rather than looked up, because the handle carries it — that is
    why it is spelled ``cohort-{ring}-{position}`` and why a member's own line is
    readable off any card they appear on.
    """

    organised = [game for game in PLAYED_GAMES if game.organiser == handle]
    if not organised:
        return None
    return max(
        _distance_between(_ring_in(handle), _ring_in(other))
        for game in organised
        for other in game.players[1:]
    )


def _ring_in(handle: str) -> str:
    """Which ring this handle names. ``cohort-a-07`` lives in ring ``a``.

    **The protagonist is the one handle that is not a cohort handle**, and she
    is answered before the split rather than by it: her slug has a hyphen in it
    too, and reading a ring off it would produce a code no ring carries and a
    ``KeyError`` two frames away from the row that caused it.
    """

    if handle == PROTAGONIST_HANDLE:
        return PROTAGONIST_RING
    return handle.split("-")[1]


def _position_in(handle: str) -> int:
    """Which position in its ring this handle names. ``cohort-a-07`` is 7.

    Read off the handle rather than looked up for :func:`_ring_in`'s reason: the
    handle carries both, which is why it is spelled the way it is.
    """

    return int(handle.split("-")[2])


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

    **How much** overlap is a rule too, and the floor is not the ceiling: a close
    match covers five of her six cells where everybody else is guaranteed two.
    Two is enough for the term to *read*; it is not enough for it to ever score
    well, and a fixture whose availability term only ever docks is a fixture
    where nobody outranks the named accounts.
    """

    rng = _rng(handle, "slots", seed)
    if _is_lopsided(position):
        return CELLS
    if position % EVERY_NTH_SHARES_NO_WEEK == SHARES_NO_WEEK_AT:
        elsewhere = [cell for cell in CELLS if cell not in PROTAGONIST_CELLS]
        return tuple(
            sorted(rng.sample(elsewhere, rng.randint(*MEMBER_CELLS_ELSEWHERE)))
        )
    wanted = (
        CLOSE_MATCH_CELLS if _is_a_close_match(position) else SHARED_CELLS_FLOOR
    )
    shared = rng.sample(PROTAGONIST_CELLS, wanted)
    rest = [cell for cell in CELLS if cell not in shared]
    extra = rng.sample(rest, rng.randint(*MEMBER_EXTRA_CELLS))
    return tuple(sorted(set(shared) | set(extra)))


def _is_lopsided(position: int) -> bool:
    """Whether this member scores the searcher far lower than the searcher does.

    A rule and never a draw, for the reason every coverage rule here is one: at
    this size the arms that fire rarely are the arms a draw misses entirely.
    """

    return position % EVERY_NTH_IS_LOPSIDED == IS_LOPSIDED_AT


def _is_a_close_match(position: int) -> bool:
    """Whether this member was drawn **towards** the protagonist rather than away.

    Read by both halves of the draw, because a close match is one member and not
    two: a week that covers hers and a vocabulary that does not would clear no
    floor, and the fixture would have paid for an arm that never fires.

    **The rules above win where they disagree**, which is why this is asked last
    in :func:`_slots`. A member who is *also* the one with no shared week keeps
    the empty week and takes the tags — the two rules stay independent, and the
    one witness the week rule owns is not quietly taken away from it.

    **A lopsided member is never a close match**, and that one is a contradiction
    rather than a precedence: lopsided *means* scoring the searcher far lower
    than she scores them, and the two tag terms are read from both ends. Handing
    that member her whole vocabulary raises the reverse Fit until the asymmetry
    is gone, which is how the seed's own battery caught this — ``RECIPROCAL_
    ASYMMETRY`` is drawn by exactly one member, and drawing them towards her
    silently deleted the only witness a printable signal has.
    """

    if _is_lopsided(position):
        return False
    return position % EVERY_NTH_IS_A_CLOSE_MATCH == IS_A_CLOSE_MATCH_AT


def _tags(handle: str, position: int, seed: int) -> tuple[str, ...]:
    """Tags drawn from the served vocabulary, and how many of hers come with them.

    Three tiers rather than two: a **close match** takes her whole vocabulary,
    every other member takes one of the three, and the rest share whatever the
    draw happened to give them. Before the first tier existed the ceiling was
    one shared tag, so the two tag terms — a quarter of the weight between them
    — could only ever dock a cohort member against the named accounts, who take
    all three by construction.

    Sorted, because the order of a tag list is not a fact about the player and an
    unsorted sample would put a draw order into the committed file.
    """

    rng = _rng(handle, "tags", seed)
    if _is_a_close_match(position):
        # Hers first and the rest of the draw into **what is left of the
        # selection bound**, read off the profile's own value object. Taking
        # three and then drawing the usual two-to-five on top reaches eight,
        # which is not a number of tags a player may hold — and the commit
        # refuses it half way through a run, with the questionnaire already
        # written. The bound is asked rather than copied for the reason the tag
        # ids are: one home, and a literal here drifts the day it moves.
        room = SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags - len(PROTAGONIST_TAGS)
        low, high = MEMBER_TAG_COUNT
        elsewhere = [tag for tag in TAGS if tag not in PROTAGONIST_TAGS]
        drawn = set(PROTAGONIST_TAGS) | set(
            rng.sample(elsewhere, rng.randint(min(low, room), min(high, room)))
        )
        return tuple(sorted(drawn))
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
    # **The upper bound moved when the played history arrived, and the lower one
    # did not.** Ring d grew by five club players — five more padel ratings — and
    # six of that ring took tennis, which is eleven more Established ratings for
    # reasons that have nothing to do with the engine: the observation went from
    # thirty-three to forty-four. The bound keeps the headroom it had, and what a
    # band claim is *for* is the **lower** one — a band that has emptied is a
    # state nobody can reach any more — which is untouched.
    BAND_ESTABLISHED: (26, 52),
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
        "played_games": [_game_document(game) for game in PLAYED_GAMES],
        # **Committed beside the cohort's own and never mixed into it**, because
        # they answer different questions: those rows exist to reach card states
        # in her pool, these to fill the record sheet she reads about herself.
        "protagonist_games": [_game_document(game) for game in PROTAGONIST_GAMES],
        # **Inputs, like a score is.** The average, the count and the band the
        # subject is shown are the fold `sportsmanship` takes over these, and a
        # committed copy of one of them would be a number nothing keeps honest.
        "what_players_said": {
            subject: dict(sorted(said.items()))
            for subject, said in sorted(WHAT_PLAYERS_SAID.items())
        },
        "members": [_member_document(member) for member in cohort.members],
    }


def _game_document(game: PlayedGame) -> dict[str, object]:
    """One declared arrangement, as the artifact spells it. **Inputs only.**

    ``entered`` and ``answered`` are here for the same reason ``won_by`` is:
    each is a thing a player did or did not do, and the ghost, the run of form
    and the strand that reads them are what the platform makes of it.
    """

    return {
        "sport": game.sport,
        "played_days_ago": game.played_days_ago,
        "side_a": list(game.side_a),
        "side_b": list(game.side_b),
        "won_by": game.won_by,
        "entered": game.entered,
        "answered": game.answered,
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

    _refuse_a_played_history_nobody_could_play(cohort)
    _refuse_a_protagonists_history_she_could_not_play(cohort)
    _refuse_an_opinion_nobody_was_on_a_court_to_have(cohort)
    _refuse_a_photograph_set_with_a_state_missing(cohort)
    for member in cohort.members:
        if not SHARED_CELLS_FLOOR <= len(member.slots) <= len(CELLS):
            raise RuntimeError(f"'{member.handle}' has a week of {len(member.slots)}")
        if not SEARCH_RADIUS_BOUNDS.contains(member.radius_km):
            raise RuntimeError(
                f"'{member.handle}' set a radius of {member.radius_km} km, "
                f"which the slider does not offer."
            )


def _refuse_a_played_history_nobody_could_play(cohort: "Cohort") -> None:
    """Every declared game, checked against the population that has to play it.

    **All of it is about the declarations and none of it about a database.** A
    game is written by sending a real challenge and accepting every seat, so each
    of these is a way the run would otherwise fail half way through with a
    message about a pool rather than about a row in this file.
    """

    known = {member.handle: member for member in cohort.members}
    pairs: dict[frozenset[str], int] = {}
    days: dict[str, set[int]] = {}
    for index, game in enumerate(PLAYED_GAMES):
        sport = Sport(game.sport)
        per_side = seats_per_side(sport)
        if len(game.side_a) != per_side or len(game.side_b) != per_side:
            raise RuntimeError(
                f"played game {index} seats {len(game.side_a)} against "
                f"{len(game.side_b)} on a {sport.value} court, which has "
                f"{per_side} a side. A line-up completes only when **every** "
                f"seat is accepted, so a court short of one opens no game at all."
            )
        _refuse_an_ending_no_evening_can_have(index, game)
        if game.won_by not in ("A", "B", None):
            raise RuntimeError(
                f"played game {index} is won by {game.won_by!r}, and a court has "
                f"two sides. `None` is the game nobody agreed a score for."
            )
        if game.played_days_ago < PLAYED_AT_LEAST_DAYS_AGO:
            raise RuntimeError(
                f"played game {index} was played {game.played_days_ago} day(s) "
                f"ago and a seeded result needs {PLAYED_AT_LEAST_DAYS_AGO}: a "
                f"score is confirmed by silence when its window closes, and a "
                f"game younger than that is still awaiting an answer."
            )

        seen = set(game.players)
        if len(seen) != len(game.players):
            raise RuntimeError(f"played game {index} seats somebody twice")
        for handle in game.players:
            member = known.get(handle)
            if member is None:
                raise RuntimeError(
                    f"played game {index} seats '{handle}', who is not in the "
                    f"cohort. A row here names its players by handle, so a "
                    f"member who leaves takes this refusal with them: the game "
                    f"has to go too, and saying so here is what stops it "
                    f"becoming a run that fails naming a pool."
                )
            if sport not in member.sports:
                raise RuntimeError(
                    f"'{handle}' plays {sport.value} in played game {index} and "
                    f"holds no {sport.value} rating. "
                    f"`SECOND_SPORT_BECAUSE_THEY_PLAYED` is what feeds the "
                    f"declaration back into the draw."
                )
            if member.committed_days_ago <= game.played_days_ago:
                raise RuntimeError(
                    f"played game {index} was played "
                    f"{game.played_days_ago} day(s) ago and '{handle}' committed "
                    f"their profile {member.committed_days_ago} day(s) ago — a "
                    f"game before the player existed. The commit dates are "
                    f"drawn and `played_days_ago` is declared, so this is the "
                    f"number to move."
                )
            if game.played_days_ago in days.setdefault(handle, set()):
                raise RuntimeError(
                    f"'{handle}' plays twice on the same day, and *Last 5* is "
                    f"ordered on the instant each game was played — two games "
                    f"at one instant leave the run of form to a tie-break on a "
                    f"uuid, which is a row of squares that reshuffles between "
                    f"databases."
                )
            days[handle].add(game.played_days_ago)

        for pair in game.pairs:
            if pair in pairs:
                raise RuntimeError(
                    f"{sorted(pair)} share a court in played games "
                    f"{pairs[pair]} and {index}. **One open challenge per pair, "
                    f"across sports**, and nothing on this platform ends a "
                    f"challenge every seat accepted — so a pair that has played "
                    f"can never be sent a second court, and the second send "
                    f"would be refused."
                )
            pairs[pair] = index

        organiser = known[game.organiser]
        if _is_lopsided(_position_in(game.organiser)):
            raise RuntimeError(
                f"'{game.organiser}' organises played game {index} and is the "
                f"ring's lopsided member. The two rules disagree about one "
                f"number: lopsidedness *is* the slider's floor — a week wide "
                f"open and a radius that reaches nobody — and an organiser's "
                f"radius has to reach everybody they play. Whichever wins, one "
                f"of the two witnesses is silently gone."
            )
        for handle in game.players[1:]:
            reach = _distance_between(organiser.ring, known[handle].ring)
            if reach > organiser.radius_km:
                raise RuntimeError(
                    f"'{game.organiser}' organises played game {index} and "
                    f"'{handle}' is {reach:.2f} km away, outside the "
                    f"{organiser.radius_km} km they set. A send cites the "
                    f"search that showed the person, so an invitee the "
                    f"organiser's own radius excludes is a court that cannot be "
                    f"built at all. The radius is drawn off the handle."
                )


def _refuse_an_ending_no_evening_can_have(index: int, game: PlayedGame) -> None:
    """The three endings, and the two combinations that are not one of them.

    A game ends **agreed** (a winner, answered), **disagreed** (no winner, both
    sides answered and neither accepted) or **ghosted** (nobody said it
    happened). ``entered`` and ``answered`` are two flags and four combinations,
    so the fourth has to be refused somewhere — here, at import, rather than
    half way through a run where it would surface as a use case declining an act
    the fixture asked for.
    """

    if game.was_a_ghost and game.was_scored:
        raise RuntimeError(
            f"played game {index} is declared a ghost and names a winner. "
            f"Nobody entered a score, so there is no score to have won: a ghost "
            f"is `entered=False` with `won_by=None`."
        )
    if game.was_a_ghost and not game.answered:
        raise RuntimeError(
            f"played game {index} is declared a ghost and declares that nobody "
            f"answered the score. There was no score to answer — an evening the "
            f"platform says did not happen puts nothing in front of anybody."
        )
    if not game.answered and not game.was_scored:
        raise RuntimeError(
            f"played game {index} declares that the asked side never answered "
            f"*and* that nobody agreed a score. Those are two different "
            f"endings: silence **confirms** what was stated, so an unanswered "
            f"score has a winner. What leaves a game unscored is two sides who "
            f"each answered with a score of their own (`docs/adr/0137`)."
        )


def _refuse_a_protagonists_history_she_could_not_play(cohort: "Cohort") -> None:
    """Every row of ``PROTAGONIST_GAMES``, against the world that has to write it.

    **The list's whole value is that it moves no draw**, so most of what is
    checked here is that it stayed inside the population as drawn: an opponent
    the fixture reserved for something else, a sport somebody was never assessed
    in, an organiser whose radius does not reach the centre. Each of those would
    otherwise surface mid-run as a message about an empty pool, blaming the
    search rather than the row.
    """

    known = {member.handle: member for member in cohort.members}
    # **Seeded from the cohort's own history first**, because a member on two
    # courts at one instant is the same defect whichever list put them there —
    # and ``cohort-d-07`` and ``cohort-d-08`` are already playing inside this
    # window.
    days: dict[str, set[int]] = {}
    for game in PLAYED_GAMES:
        for handle in game.players:
            days.setdefault(handle, set()).add(game.played_days_ago)

    for index, game in enumerate(PROTAGONIST_GAMES):
        sport = Sport(game.sport)
        _refuse_an_ending_no_evening_can_have(index, game)

        per_side = seats_per_side(sport)
        if len(game.side_a) != per_side or len(game.side_b) != per_side:
            raise RuntimeError(
                f"protagonist game {index} seats {len(game.side_a)} against "
                f"{len(game.side_b)} on a {sport.value} court, which has "
                f"{per_side} a side."
            )
        if game.side_b[0] != PROTAGONIST_HANDLE:
            raise RuntimeError(
                f"protagonist game {index} does not seat "
                f"'{PROTAGONIST_HANDLE}' first on side B. She sits there in "
                f"every row and it is not a convention: the organiser answers "
                f"no invitation of their own, and the side that *states* the "
                f"score is asked nothing — so a row that moves her costs her a "
                f"strand and the sheet quietly loses a bar."
            )
        if game.players.count(PROTAGONIST_HANDLE) != 1:
            raise RuntimeError(
                f"protagonist game {index} seats '{PROTAGONIST_HANDLE}' "
                f"{game.players.count(PROTAGONIST_HANDLE)} time(s)."
            )
        if game.organiser not in PROTAGONISTS_ORGANISERS:
            raise RuntimeError(
                f"protagonist game {index} is organised by '{game.organiser}', "
                f"who is not in `PROTAGONISTS_ORGANISERS`. A court built on a "
                f"*for fun* search is a friendly and no card counts one, so an "
                f"organiser here has to have declared this sport competitively."
            )
        floor = (
            GHOSTED_AT_LEAST_DAYS_AGO if game.was_a_ghost else PLAYED_AT_LEAST_DAYS_AGO
        )
        if game.played_days_ago < floor:
            raise RuntimeError(
                f"protagonist game {index} was arranged {game.played_days_ago} "
                f"day(s) ago and this ending needs {floor}. A score is confirmed "
                f"by silence when its window closes; **a plan is a ghost only "
                f"once its entry window has**, and that window is a week plus a "
                f"day rather than the day the score's is. A ghost declared "
                f"inside it is a game still awaiting its entry, which the record "
                f"leaves out of both halves of *shows up* — a full bar, and "
                f"nothing failing."
            )

        others = [handle for handle in game.players if handle != PROTAGONIST_HANDLE]
        if len(set(game.players)) != len(game.players):
            raise RuntimeError(f"protagonist game {index} seats somebody twice")
        for handle in others:
            if handle not in PROTAGONISTS_OPPONENTS:
                raise RuntimeError(
                    f"protagonist game {index} seats '{handle}', who is not in "
                    f"`PROTAGONISTS_OPPONENTS`. The rest of the ring is spoken "
                    f"for: three members are the empty cards, two are the "
                    f"evening nobody scored, and the others are gated out of a "
                    f"court of hers by level or by gender."
                )
            member = known[handle]
            if sport not in member.sports:
                raise RuntimeError(
                    f"protagonist game {index} is {sport.value} and "
                    f"'{handle}' holds no {sport.value} rating. **Nothing here "
                    f"may reach `SECOND_SPORT_BECAUSE_THEY_PLAYED`**: that set "
                    f"feeds the draw and the draw is the committed artifact, so "
                    f"a row may only name somebody the population already rated "
                    f"in this sport."
                )
            if member.committed_days_ago <= game.played_days_ago:
                raise RuntimeError(
                    f"protagonist game {index} was played "
                    f"{game.played_days_ago} day(s) ago and '{handle}' "
                    f"committed their profile {member.committed_days_ago} "
                    f"day(s) ago — a game before the player existed."
                )
        for handle in (*others, PROTAGONIST_HANDLE):
            if game.played_days_ago in days.setdefault(handle, set()):
                raise RuntimeError(
                    f"'{handle}' plays twice on the same day, and *Last 5* is "
                    f"ordered on the instant each game was played."
                )
            days[handle].add(game.played_days_ago)

        organiser = known[game.organiser]
        if _is_lopsided(_position_in(game.organiser)):
            raise RuntimeError(
                f"'{game.organiser}' organises protagonist game {index} and is "
                f"the ring's lopsided member, whose radius is the slider's "
                f"floor and reaches nobody."
            )
        to_the_centre = _distance_between(organiser.ring, PROTAGONIST_RING)
        if to_the_centre > organiser.radius_km:
            raise RuntimeError(
                f"'{game.organiser}' organises protagonist game {index} and the "
                f"centre is {to_the_centre:.2f} km away, outside the "
                f"{organiser.radius_km} km they were drawn. **Nothing here may "
                f"widen it**: an organiser's radius is part of the committed "
                f"draw, and giving one to this list would move `cohort.json` "
                f"and every screen assertion read off it. Pick an opponent who "
                f"can already see her."
            )
        for handle in others:
            if handle == game.organiser:
                continue
            reach = _distance_between(organiser.ring, known[handle].ring)
            if reach > organiser.radius_km:
                raise RuntimeError(
                    f"'{game.organiser}' organises protagonist game {index} and "
                    f"'{handle}' is {reach:.2f} km away, outside the "
                    f"{organiser.radius_km} km they set."
                )


def _refuse_an_opinion_nobody_was_on_a_court_to_have(cohort: "Cohort") -> None:
    """Every declared rating, against the courts that would have to carry it.

    **A card may only be answered about somebody you were on a court with**, and
    the court has to be one that is *over*: an evening the platform says never
    happened has nobody to rate. So a row here that no game backs is a card the
    use case would refuse mid-run, with a message about a game id rather than
    about the table it came from.
    """

    lowest, highest = STARS_ARE_ONE_TO_FIVE
    known = {member.handle for member in cohort.members} | {PROTAGONIST_HANDLE}
    #: Who shared a **rateable** court with whom, and how recently. A ghost is
    #: not in it, which is the whole reason this is computed rather than read off
    #: ``pairs``; the day is here because the card has a week and the writer puts
    #: each rating on the **latest** court a pair shared.
    together: dict[str, dict[str, int]] = {}
    for game in EVERY_PLAYED_GAME:
        if game.was_a_ghost:
            continue
        for pair in game.pairs:
            one, other = sorted(pair)
            for who, whom in ((one, other), (other, one)):
                seen = together.setdefault(who, {})
                seen[whom] = min(
                    game.played_days_ago, seen.get(whom, game.played_days_ago)
                )

    for subject, said in WHAT_PLAYERS_SAID.items():
        if subject not in known:
            raise RuntimeError(
                f"'{subject}' is rated by somebody and is in neither population."
            )
        for rater, stars in said.items():
            if rater not in known:
                raise RuntimeError(
                    f"'{rater}' rates '{subject}' and is in neither population."
                )
            if rater == subject:
                raise RuntimeError(
                    f"'{subject}' rates themselves. The rater is not among the "
                    f"others on their own court, so the card has one rule and "
                    f"this is the same one."
                )
            if not lowest <= stars <= highest:
                raise RuntimeError(
                    f"'{rater}' gives '{subject}' {stars} star(s), and a tap is "
                    f"{lowest} to {highest}. **There is no nought**: a rating "
                    f"that reads as *worthless* is a weapon out of proportion "
                    f"to a tap, so a person nobody rated is absent rather than "
                    f"at the bottom of the scale."
                )
            latest = together.get(subject, {}).get(rater)
            if latest is None:
                raise RuntimeError(
                    f"'{rater}' rates '{subject}' and the two of them share no "
                    f"court that is played and over. A card is drawn for an "
                    f"evening, so a rating with no evening behind it cannot be "
                    f"written at all — and a **ghost** is not one: there is "
                    f"nobody to rate for a game the platform says did not "
                    f"happen."
                )
            if latest > RATED_WITHIN_DAYS:
                raise RuntimeError(
                    f"'{rater}' rates '{subject}' and the most recent court "
                    f"they shared was {latest} day(s) ago, past the card's own "
                    f"{RATED_WITHIN_DAYS}-day week. **`AnswerTheCard` would "
                    f"take it** — the window decides when somebody is *asked*, "
                    f"not whether a late tap counts — so nothing would fail and "
                    f"this fixture would be declaring an opinion no player was "
                    f"ever shown a card to give."
                )


def _refuse_a_photograph_set_with_a_state_missing(cohort: "Cohort") -> None:
    """All three of ``docs/adr/0138``'s answers, and every carrier a real member.

    Two of the three are the **same silence** on a card — flagged, and never
    looked at — so a set missing one of them is a set where the two cannot be
    told apart at all, which is the whole reason this fixture holds photographs.
    """

    handles = {member.handle for member in cohort.members}
    unknown = sorted(set(PHOTOGRAPH_VERDICTS) - handles)
    if unknown:
        raise RuntimeError(
            f"{unknown} are declared to hold a photograph and are not in the "
            f"cohort."
        )
    declared = set(PHOTOGRAPH_VERDICTS.values())
    missing = sorted(one.value for one in DeclaredVerdict if one not in declared)
    if missing:
        raise RuntimeError(
            f"no seeded photograph reaches {missing}. A shield's absence has two "
            f"causes and they are indistinguishable on the wire, so a fixture "
            f"holding one of them proves nothing about the other."
        )


def _distance_between(one: str, other: str) -> float:
    """How far apart two rings are. **Both sit on the centre's own meridian**,
    so this is the whole of it — and it is measured with the module's own
    distance function rather than subtracted, because two radii from a centre
    are not a distance between two points in general."""

    latitudes = {ring.code: ring.latitude for ring in RINGS}
    # **The centre is not a ring and is spelled as one here**, because the
    # protagonist sits on it and *how far is she* is the same question about the
    # same meridian. It is a key in this one mapping rather than a fifth `Ring`,
    # which would have to declare bounds and a membership it does not have.
    latitudes[PROTAGONIST_RING] = CENTRE_LATITUDE
    return distance_km(
        Point(latitude=latitudes[one], longitude=CENTRE_LONGITUDE),
        Point(latitude=latitudes[other], longitude=CENTRE_LONGITUDE),
    )


#: The one cohort this system seeds, drawn at import so that the generator, the
#: committed artifact and the run all read one object — and drawn **once**,
#: because the refusal below reads the same draw rather than making its own.
COHORT: Final = generate()

_refuse_an_impossible_cohort(COHORT)
