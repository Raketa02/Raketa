"""What a record says about a person, in this context's own words.

**The header identity, the sport pills, the skill card and opponent variety.**
The metered rows and what opponents said arrive on this type later (#381, #382);
what shipped first was the zone every one of them hangs under, because the route
and its admission rule are what the rest of the sheet was blocked on.

**Every one of these fields is spelled here rather than imported**, and the
duplication is the decision (``docs/adr/0155``). ``matchmaking`` already holds a
``CardIdentity`` with three of them on it, and a record that reused it would
inherit a *card's* closed list — the list ``docs/adr/0107`` keeps short because it
is attached over the twenty rows of a search and frozen into a record kept for
ever. A record is one person, live, and read at most a handful of times a day.
Two surfaces with two lists, and the day one of them grows a field is the day the
other one is asked whether it wants one.

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
    #: How widely they spread their games, over the **whole** record. ``None``
    #: for somebody no counted game has been watched for — which is not the same
    #: absence as ``skill``'s: a player rated in nothing may well have played,
    #: and somebody rated in four sports may never have had a game counted.
    variety: OpponentVariety | None


__all__ = [
    "LAST_FIVE",
    "GameOutcome",
    "LikelyRange",
    "OnCourtVerdict",
    "OpponentVariety",
    "PlayerRecord",
    "SkillPanel",
    "SportPill",
    "SubjectIdentity",
    "SubjectRating",
]
