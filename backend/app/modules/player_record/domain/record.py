"""What a record says about a person, in this context's own words.

**The header identity, the sport pills, the skill card, opponent variety, the
metered rows and what other players said.** The last of those arrives in two
shapes rather than one, and the second shape is the only place on this sheet
where *who is reading* changes what is said rather than only what it is titled
(``docs/adr/0154``).

**Every one of these fields is spelled here rather than imported**, and the
duplication is the decision (``docs/adr/0155``). ``matchmaking`` already holds a
``CardIdentity`` with three of them on it, and a record that reused it would
inherit a *card's* closed list — the list ``docs/adr/0107`` keeps short because it
is attached over the twenty rows of a search and frozen into a record kept for
ever. A record is one person, live, and read at most a handful of times a day.
Two surfaces with two lists, and the day one of them grows a field is the day the
other one is asked whether it wants one.

**``ReliabilityStrand`` is the one name here that is imported, and the rule is
unbroken.** What ADR-0155 §6 refuses is borrowing another *context's* domain
types; that enum is not one — it lives in ``app/engines/``, the pure layer every
context reads and none of them owns, exactly as ``Sport`` lives in the kernel. It
is also the argument ``player_score`` already made about the same five names: a
locally-declared copy would satisfy every protocol in the suite while being free
to drift, and the strand codes are on the player contract today under that enum's
own spelling. A second one would put two words for one strand in front of a
client reading a Fit breakdown and a record.

**A photograph's three facts travel together and are meaningless apart.** The id
is what the platform stores, the link is minted for this response and written
down nowhere (``docs/adr/0107``), and the verdict is what the on-court check
concluded about *that* photograph rather than about the player
(``docs/adr/0138``). A player with no photograph has none of the three, and the
client draws the generated court poster rather than a placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Sport, invariant


class OnCourtVerdict(StrEnum):
    """What the on-court check concluded about a photograph. **Two values.**

    The third state — *nobody looked* — is the **absence** of one of these and
    never a third value, which is ``docs/adr/0138``'s rule: a shield saying
    *checked and passed* cannot be drawn on a photograph nothing examined, and a
    value meaning *unknown* is a value somebody eventually draws a tick for.

    **The words are the ones a card already carries, and they are checked
    against it.** This is a second spelling of ``player_profile``'s
    ``PhotoReviewDecision`` on purpose — this context imports no other context's
    domain types — and a second spelling that drifts is worse than an import: a
    client reading a search card and a record would get two words for one fact.
    ``tests/unit/test_player_record_identity.py`` fails the build if the two
    vocabularies stop agreeing.
    """

    ALLOWED = "allowed"
    FLAGGED = "flagged"


@final
@dataclass(frozen=True, slots=True)
class SubjectIdentity:
    """Who this person is, as the platform can describe them to a stranger.

    **The whole handle and nothing that shortens it.** ``users`` holds a nickname
    and no real name; every sentence naming somebody uses the handle they gave or
    names nobody.

    **The area is a code and never a sentence.** Nothing in this repository can
    turn a coordinate into the name of a neighbourhood, and a code is what
    licenses the one comparison a client may make — *are we in the same square*
    (``docs/adr/0021``).
    """

    nickname: str
    #: The **first** photo, because order is meaning in a player's photo list.
    #: ``None`` when they have none.
    photo_id: UUID | None
    #: What the check concluded about ``photo_id``, or ``None`` for *nobody
    #: looked*. Meaningless without a photo id, and never present without one.
    review: OnCourtVerdict | None
    #: Their coarse area, as a machine code.
    area_code: str
    #: The Social tag ids they hold, in the vocabulary's own order.
    social_tags: tuple[str, ...]


#: How many results a run of form draws. **This context's own spelling of a
#: number ``games`` also holds**, because a record may not import a provider's
#: constant into its domain any more than it may import its types. What is
#: avoidable about two spellings is them being *silent*: the adapter that reads
#: ``games`` refuses to import when they disagree, which is the seam
#: ``matchmaking`` already puts the same pair of numbers through.
LAST_FIVE: Final = 5


class GameOutcome(StrEnum):
    """How one counted game went for the person the record is about. **Two.**

    *Unscored* is not a third value: a game nobody agreed a score for produced no
    outcome for anybody, and the absence is spelled by not being in the run at
    all (``docs/adr/0137``).

    **A second spelling of ``games``' own ``Outcome``**, mapped at the adapter
    that reads it — which is the shape ``matchmaking``'s ``GameResult`` already
    takes for the same two words, and this context's standing rule about
    borrowing another context's domain types (``docs/adr/0155``). The risk is the
    same one ``OnCourtVerdict`` carries and it is answered the same way:
    ``tests/unit/test_player_record_skill.py`` fails the build if the two
    vocabularies stop agreeing.
    """

    WIN = "WIN"
    LOSS = "LOSS"


@final
@dataclass(frozen=True, slots=True)
class LikelyRange:
    """The band a Level probably sits in — μ ± σ, clamped to the scale.

    **One value with two edges**, nested rather than two loose floats beside the
    Level, which is the shape the rating routes and the player card already
    spell it in. The client computes nothing: the rounding lives in the engine,
    and a range derived anywhere else is a second set of drawing constants.
    """

    low: float
    high: float


@final
@dataclass(frozen=True, slots=True)
class SubjectRating:
    """What this platform holds about one person in one sport.

    **Read and never held.** It is a projection of a ``SkillRating`` and not the
    aggregate: a reader that could hold one could save it, and this context
    stores nothing at all.

    ``counted_games`` is **the games this Level was moved by** and not every
    counted game they have played — the two differ, and the difference is the
    point. A player card's ``counted_games`` is *how much have they played*, over
    every sport, and an unscored evening is in it. This one is *what does this
    certainty rest on*: confirmed counted results in **this** sport that the
    rating actually folded (``docs/adr/0139``). It moves in step with the Level
    beside it, which the other number could not promise.
    """

    sport: Sport
    level: float
    band: str
    #: How sure the platform is, as ``rating`` published it — a whole percentage.
    confidence: int
    counted_games: int
    likely_range: LikelyRange


@final
@dataclass(frozen=True, slots=True)
class SportPill:
    """One sport this person is rated in: the dot, the abbreviation, the Level.

    **Narrower than the rating it is drawn from, deliberately.** A pill answers
    *what else do they play*, and a confidence and a counted-games count on every
    one of them would be four skill cards drawn as jewellery — the panel below is
    where those belong, for the one sport the sheet is about.
    """

    sport: Sport
    level: float
    band: str


@final
@dataclass(frozen=True, slots=True)
class SkillPanel:
    """The skill card, for the one sport this sheet is about.

    **The three headline figures travel together and are never separable.** A
    Level with no certainty beside it and no count under it is the claim
    ``docs/adr/0107``'s range amendment exists to stop: two people both showing
    2,75 are told apart by how sure the platform is about each, and a
    confident-looking number built on three games must not read like one built on
    forty.

    ``last_five`` is **oldest to newest and never padded** — the run of form a
    reader takes left to right — and it is this sport's, which is the defect this
    panel fixes by construction: a run built across every sport and drawn beneath
    a single sport's Level was drawing squash results under a padel number.
    """

    sport: Sport
    level: float
    band: str
    confidence: int
    counted_games: int
    likely_range: LikelyRange
    last_five: tuple[GameOutcome, ...]


@final
@dataclass(frozen=True, slots=True)
class OpponentVariety:
    """How many different people this person's counted games were against.

    **The pair, and the sheet divides it.** The card two rows above argues that a
    perfect record over nine games and one over forty are different claims and
    that a bar alone hides which — so a bare percentage here would break the rule
    the card had just made about itself. What crosses is the fraction; *70 %* is
    what a client draws from it.

    **It is a career statistic and never a window.** The fold behind it is
    unbounded, which is what the number means: *how widely do they spread their
    games*, not *how widely this season*. A second window here would be a figure
    that must not disagree with the matcher's horizon, and eventually would.

    **This is not a strand and it prices no promise.** It neither raises nor
    lowers a Player Score; it is context for a Level — a low figure is somebody
    playing the same few faces every week, whose rating may be narrow but
    untested.

    **A second spelling of a pair ``games`` publishes**, like every fact on this
    sheet (``docs/adr/0155``). There ``distinct_counterparts`` says what was
    measured — everybody who was on a court with them, partner included; here
    ``distinct_opponents`` says what the row is called on screen. The translation
    is one adapter, and there is no third place for either word.
    """

    distinct_opponents: int
    games_played: int

    def __post_init__(self) -> None:
        invariant(
            self.games_played >= 1,
            "a variety over no counted game is an absence, not a nought — this "
            "sheet omits the row rather than drawing a habit nobody has",
        )
        invariant(
            self.distinct_opponents >= 1,
            "a counted game played against nobody: "
            f"{self.distinct_opponents} people over {self.games_played} games",
        )


#: The scale a published star average sits on. **This context's own spelling of
#: two numbers ``sportsmanship`` also holds**, like ``LAST_FIVE`` beside
#: ``games``' own: a record may not import a provider's constant into its domain
#: any more than it may import its types. What is avoidable about two spellings
#: is them being *silent* — a scale that grew a nought over there and not here
#: would answer a published figure with a 500 rather than a red build — so the
#: adapter that reads across refuses to import when they disagree.
LOWEST_AVERAGE: Final = 1.0
HIGHEST_AVERAGE: Final = 5.0

#: How many **people** a published figure may rest on — the same window, spelled
#: a second time for the same reason and checked at the same seam. It is here
#: rather than only over there because the wire *documents* it to clients: a
#: bound a contract states and nothing enforces is a bound that stops being true
#: quietly.
RATER_WINDOW: Final = 50


class OpinionBand(StrEnum):
    """How somebody is coming across, in the three steps **they** may be told.

    **The subject's whole answer, and the coarseness is the safety.** A figure
    plus a count in front of the person they are about is a subtraction: an
    average moving from 4,80 over ten to 4,73 over eleven names the new rating as
    a 4, and they know who they played, so every answer would be identifiable by
    the one person who must never see it. Three steps across the whole scale tell
    them *something is going wrong*, which is the useful half.

    **A second spelling of ``sportsmanship``'s ``SportsmanshipBand``**, and it
    takes a **different name** for the reason ``OnCourtVerdict`` does beside
    ``PhotoReviewDecision`` and ``GameOutcome`` does beside ``Outcome``. That is
    two rules meeting: this context borrows no other context's domain types
    (``docs/adr/0155``), and the emitted contract is **one namespace** — a class
    of the same name in two modules does not shadow the other, it *renames both*,
    and every generated type a shipped app already holds moves. It is
    ``RecordLikelyRangeSchema``'s argument, applied one layer down, because this
    enum reaches the wire as itself rather than through a schema class.

    The risk a second spelling carries is answered the way those two answer it —
    ``tests/unit/test_player_record_sportsmanship.py`` fails the build if the two
    vocabularies stop agreeing.

    **There is no fourth value for *nobody has said anything*.** That is the
    field's absence, on the rule every zone on this sheet takes.
    """

    GOOD = "GOOD"
    MIXED = "MIXED"
    POOR = "POOR"


@final
@dataclass(frozen=True, slots=True)
class WhatPlayersSaid:
    """The one thing on this sheet the platform did not count for itself.

    **Its own heading, and that is the card splitting where the authority
    splits.** The record card below is headed *counted by the system, not written
    by people*, which is the promise every metered row under it rests on; a
    number people typed sitting beneath that title would make the title false.

    **The figure and the count travel together and are never separable.** It
    publishes from the very first rating with no minimum, and the count is what
    makes that safe: ``3,0 / 5 · 1 player`` is visibly one person's opinion and
    reads as one — the same discipline the metered rows take by printing their
    raw pairs.

    **``raters`` is people, and that is what a reader wants to know.** One
    standing answer per person is the store's shape over there, so a high count
    is evidence of *breadth* rather than of repetition, and a weekly partner
    cannot inflate it.

    **It never reaches the person it is about.** The subject is answered with
    :class:`OpinionBand`, off a different method on a different port, so
    the figure has no path to them rather than a rule against printing it.

    **Unlike the pair above it, the division is not the client's.** Opponent
    variety withholds its share because nothing rounds it and it prices no
    promise; this is already a mean, taken and rounded once on the other side of
    the seam, and there is nothing here to divide.
    """

    average: float
    raters: int

    def __post_init__(self) -> None:
        invariant(
            self.raters >= 1,
            "a figure over nobody is an absence, not a nought — this sheet omits "
            "the zone rather than publishing a verdict nobody gave",
        )
        invariant(
            self.raters <= RATER_WINDOW,
            "a figure over more people than the window admits: "
            f"{self.raters} over a window of {RATER_WINDOW}",
        )
        invariant(
            LOWEST_AVERAGE <= self.average <= HIGHEST_AVERAGE,
            f"a mean of one-to-five stars that is not one of them: {self.average}",
        )


@final
@dataclass(frozen=True, slots=True)
class StrandRow:
    """One metered row: what fell due, what came of it, and the figure shown.

    **The raw pair travels, and it is the same honesty the row below it keeps.**
    A perfect record over nine opportunities and one over forty are different
    claims and a bar alone hides which — so the two counts cross and a client
    that wants to print *9 of 9* has them.

    **``pct`` crosses too, and that is where this row parts company with opponent
    variety.** There, the share is deliberately withheld and the division is the
    client's, because the figure prices no promise and nothing rounds it. Here it
    is the number the platform *acts* on: ``StrandRatio.value`` is derived in one
    place so that a card, a profile and the matcher's evidence cannot print three
    roundings of one record, and a client dividing ``good`` by ``opportunities``
    itself would be the fourth. It rounds halves **up**, which JavaScript's
    ``Math.round`` does too — until the day somebody computes it over a negative,
    or in a language that rounds to even, and the two disagree by a point on
    exactly the values a player notices.

    **No weight is on this row and none crosses the seam behind it.** The blend
    is taken on ``player_score``'s side and arrives already taken; a weight here
    would let a reader re-derive the pill, and would invite a sheet drawing one
    strand as worth more than another — a claim no screen on this platform makes.

    ``pct`` is not called ``value`` deliberately: the Fit breakdown already
    publishes a ``StrandReading.value`` for the same five names, and that one is
    the matcher's own reading between nought and one. Two scales under one word
    on one contract is the cost the second arrival pays (``docs/adr/0137``). The
    word itself is the contract's own for a whole percentage — the forecast and
    the predicted-balance evidence both spell it that way already.

    **There is deliberately no invariant tying ``pct`` to the pair beside it**,
    and the asymmetry with the three below is the decision rather than an
    omission. Checking it would mean dividing here, and a second derivation of
    this figure is precisely what the row exists to avoid: it is copied so that a
    card, a profile and the matcher's evidence print one rounding of one record.
    The three checks below are about a row being *well formed*; agreement with
    the ratio is the provider's promise and is asserted at the seam that copies
    it.
    """

    strand: ReliabilityStrand
    good: int
    opportunities: int
    #: The figure out of a hundred the player is shown for this strand —
    #: ``StrandRatio.value``, copied and never re-derived.
    pct: int

    def __post_init__(self) -> None:
        invariant(
            self.opportunities >= 1,
            "a strand with no opportunity behind it is an absence, not a row: "
            f"{self.strand} over {self.opportunities}",
        )
        invariant(
            0 <= self.good <= self.opportunities,
            "a row claiming more good outcomes than opportunities: "
            f"{self.good}/{self.opportunities}",
        )
        invariant(
            0 <= self.pct <= 100,
            f"a figure that is not out of a hundred: {self.pct}",
        )


@final
@dataclass(frozen=True, slots=True)
class ReliabilityPanel:
    """What the platform watched: the pill, and the rows it is the mean of.

    **Counted by the system, not written by people** — the promise the card is
    headed with, and the reason every row under it is a ratio the platform
    observed rather than an opinion somebody typed. What opponents said gets its
    own heading (#382), because a number people typed would make that title
    false.

    **The pill is exactly the number the matcher acts on**, which is what makes
    the screen worth having: a player who works their record back up must be able
    to watch the penalty lift, and a figure that existed nowhere they could look
    would be the unexplainable kind of penalty the reliability floor's own rule
    forbids.

    **A strand with nothing behind it is not a row.** Three of the five names
    stand down platform-wide, and a player may have no opportunity under one that
    does not — both are spelled by absence from ``strands``, never by a nought,
    because *we have not seen enough* and *they are bad at this* are different
    facts. A panel with no row at all is not a panel: the whole zone is omitted,
    and ``PlayerRecord.reliability`` is ``None``.
    """

    player_score: int
    strands: tuple[StrandRow, ...]

    def __post_init__(self) -> None:
        invariant(
            bool(self.strands),
            "a reliability panel with no row on it is an absence, and an "
            "absence is spelled by the whole zone not being there",
        )
        invariant(
            len({row.strand for row in self.strands}) == len(self.strands),
            "a strand printed twice would draw one fact as two and double its "
            f"weight in any mean taken from the rows: {self.strands}",
        )
        invariant(
            0 <= self.player_score <= 100,
            f"a Player Score that is not out of a hundred: {self.player_score}",
        )


@final
@dataclass(frozen=True, slots=True)
class PlayerRecord:
    """One player's record, as of the moment somebody opened it.

    **``is_self`` is the server's answer and not the client's.** A sheet titled
    *How others see you* draws a different screen from one about a stranger — no
    distance, a coarse band where a figure would be — and a client deciding that
    by comparing the id it asked about against the one in its session is a client
    that gets it wrong exactly once, on the screen where being wrong is most
    visible. So the subject's id is deliberately **not** on this type: there is
    nothing here to compare.
    """

    is_self: bool
    identity: SubjectIdentity
    #: A short-lived signed URL for ``identity.photo_id``, minted for this
    #: response and stored nowhere. **Present exactly when the photo id is**:
    #: signing is a signature over a request that is never sent, so there is no
    #: outage that produces an id without an address for it.
    photo_url: str | None
    #: One per sport they hold a rating in, **in the sport registry's own
    #: order**. Empty for somebody rated in nothing, which is an ordinary state
    #: during onboarding rather than an error.
    sports: tuple[SportPill, ...]
    #: The sport the sheet is *about*, or ``None`` where no sport resolves —
    #: which is exactly when ``sports`` is empty, and the client draws the poster
    #: with no Level on it. An omission and never a panel full of noughts.
    skill: SkillPanel | None
    #: The pill and the metered rows behind it. ``None`` for somebody the
    #: platform has watched nothing of — the whole zone is omitted rather than
    #: drawn empty, because nobody has failed to turn up who was never due to.
    #: **A third absence, and it asks a third question.** It is not ``skill``'s:
    #: somebody rated in four sports may have had nothing at all fall due. It is
    #: not ``variety``'s either, and the two do not move together — a plan that
    #: dissolved and a seat that ran out are opportunities and neither is a game
    #: anybody played.
    reliability: ReliabilityPanel | None
    #: How widely they spread their games, over the **whole** record. ``None``
    #: for somebody no counted game has been watched for — which is not the same
    #: absence as ``skill``'s: a player rated in nothing may well have played,
    #: and somebody rated in four sports may never have had a game counted.
    variety: OpponentVariety | None
    #: What other players said, **for a reader who is not the subject.** ``None``
    #: for somebody nobody has rated, and ``None`` on every record somebody is
    #: reading about themselves — the two absences are one field being empty and
    #: the invariant below says which is which.
    sportsmanship: WhatPlayersSaid | None
    #: The coarse band, **for the subject and nobody else.** ``None`` on a record
    #: about somebody else, and ``None`` for a subject nobody has rated.
    sportsmanship_band: OpinionBand | None

    def __post_init__(self) -> None:
        """**The one rule on this type, and it is the privacy rule.**

        Two fields where at most one is ever filled, and which one is decided by
        ``is_self`` rather than by whoever assembled the record. It is checked
        here because the failure is silent everywhere else: a figure and a count
        drawn on the sheet titled *How others see you* is a subtraction the
        subject can perform against their own record, and nothing about the
        response would look wrong (``docs/adr/0154``).

        A broken precondition and not a refusal — nobody typed this, and there is
        no state of the platform in which it is a legitimate answer.
        """

        invariant(
            not (self.is_self and self.sportsmanship is not None),
            "a figure and a count on the subject's own record: they can subtract "
            "each new rating out of it and they know who they played",
        )
        invariant(
            not (self.sportsmanship_band is not None and not self.is_self),
            "a band on a stranger's record: the coarse reading exists for the one "
            "person the figure is withheld from, and nobody else",
        )


__all__ = [
    "HIGHEST_AVERAGE",
    "LAST_FIVE",
    "LOWEST_AVERAGE",
    "RATER_WINDOW",
    "GameOutcome",
    "LikelyRange",
    "OnCourtVerdict",
    "OpponentVariety",
    "PlayerRecord",
    "ReliabilityPanel",
    "SkillPanel",
    "SportPill",
    "OpinionBand",
    "StrandRow",
    "SubjectIdentity",
    "SubjectRating",
    "WhatPlayersSaid",
]
