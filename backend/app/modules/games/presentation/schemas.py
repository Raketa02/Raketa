"""The game wire shapes — **a record of an evening, and never a verdict.**

Three rules decide everything below.

**The standing is derived and travels as a code.** ``GameStanding`` is five values and
the words for them are the client's (``docs/adr/0022``). It is on the response
because it is a fold of the record against the moment the list was read — and it
is **not** on the aggregate, in the store, or anywhere a second copy could go
stale.

**Every deadline is a moment the backend computed**, never a duration and never a
rule the client applies. A phone renders *how long you have* by subtracting from
its own clock, which is ``docs/adr/0021``'s split exactly: a countdown toward a
supplied instant is the client's, and the rule that produced the instant is not.

**Nothing here says who is at fault.** There is no field for *whose turn it is*
and none for *who has not answered*: a result nobody agreed on is a fact about a
pair, and the two people who were there can read the two scores and see it. The
platform does not arbitrate, and a wire shape that named a side would be it
starting to.

That last sentence is why ``proposals`` is a **list and not one standing score**.
The field used to carry a proposal *when exactly one stood*, which made the
disagreement the one state whose two scores never crossed — the client was told
there was an argument and shown nothing being argued about, and could not offer
the acceptance that ends it. Both scores and one acceptance are what the four
people on the court can see between them, and none of the three names anybody.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport
from app.modules.games.domain.lineup import GameKind, GameSide
from app.modules.games.domain.results import (
    MAX_POINTS,
    MAX_SETS,
    MIN_SETS,
    Outcome,
)
from app.modules.games.domain.standing import GameStanding
from app.modules.player_profile.domain.availability import Window


class SetScoreSchema(BaseModel):
    """One set, **absolute**: what side A took, and what side B took.

    Never relative to the reader. A score stored from one point of view has to be
    flipped by whoever reads it next, and the first reader to forget publishes a
    loss as a win.
    """

    a: int = Field(
        ..., ge=0, le=MAX_POINTS, description="GameSide A's games in this set"
    )
    b: int = Field(
        ..., ge=0, le=MAX_POINTS, description="GameSide B's games in this set"
    )


class ScoreSchema(BaseModel):
    """The sets, in the order they were played.

    **A score names a winner**, and a level score is refused: none of the four
    sports produces a draw, and *Last 5* is win or loss with no third column to
    put one in. A *set* here is whatever the sport calls its unit — a set in
    tennis and padel, a game in squash and badminton.
    """

    sets: list[SetScoreSchema] = Field(
        ..., min_length=MIN_SETS, max_length=MAX_SETS
    )


class StateResultRequest(BaseModel):
    """*This is the score.*

    **One request for three acts**, and the record decides which: the first score
    entered, a correction of your own side's while nobody has answered it, or
    your side's disagreement with the other's. A client that named which would be
    a client that could name it wrongly, and a mislabelled correction is a
    proposal nobody may make.

    **There is no rejection here and there is no body without a score.** An
    objection carrying nothing would be free and always optimal for the loser.
    """

    score: ScoreSchema = Field(..., description="The score you say was played")


class SeatingSchema(BaseModel):
    """One person, on one side. The court is frozen at the plan.

    **A handle, and nothing else about them** (``docs/adr/0141``). A Level, a
    band, an area and a run of form are what a *searcher* reads to decide about a
    game that might happen, and a gate decided they may see them; this is the
    record of a game that did, and it re-publishes nobody's profile off the back
    of it. The court is the whole of the permission — ``GET /games`` answers
    about games you were on the court of — so nothing here is re-gated against
    who is reading.
    """

    side: GameSide
    player_id: UUID
    nickname: str | None = Field(
        default=None,
        description=(
            "The whole handle, and **nothing may derive a familiar form from "
            "it** — every sentence naming somebody uses all of it or names "
            "nobody (``docs/adr/0107``).\n\n"
            "``null`` where ``users`` no longer has this account. The seat "
            "stays: dropping it would publish a three-person doubles game, and "
            "the screen has a side to name instead."
        ),
    )


class StandingProposalSchema(BaseModel):
    """One side's score, on the table and not yet settled on.

    **At most one per side**, which is what bounds an argument to two rounds. Two
    of them is the disagreement this platform does not resolve — and it does not
    resolve it by *arbitrating*, not by hiding it: both scores travel, either
    side may agree with the other's, and that is the only end short of the game
    going unscored.
    """

    side: GameSide = Field(..., description="Which side put this score on the table")
    proposed_by: UUID
    score: ScoreSchema
    proposed_at: datetime
    answer_by: datetime = Field(
        ...,
        description=(
            "When the other side's silence becomes agreement. **Nothing happens "
            "at this moment** — no job runs and nothing is written; the game "
            "simply reads as confirmed from here on."
        ),
    )
    settles_at: datetime = Field(
        ...,
        description=(
            "When an acceptance of this score would become final. Earlier than "
            "`answer_by`, and it is the grace an opponent who has not read the "
            "score yet is given: inside it a disagreement still wins."
        ),
    )


class AcceptanceSchema(BaseModel):
    """Somebody agreed with the other side's score, and it has not settled yet.

    **Present only while the grace runs.** Once it has passed the game is
    confirmed and the agreed score is on `score`; inside it nothing has settled,
    a disagreement still wins, and the proposing side is no longer waiting on
    silence — which is a different sentence on their screen and a correction the
    aggregate will now refuse.
    """

    agreed_by: UUID
    of_side: GameSide = Field(
        ...,
        description=(
            "Whose score was agreed with. **Always the accepter's opposite** — a "
            "teammate agreeing with a teammate proves nothing — so this names the "
            "score and, with it, which of the two people this is news for."
        ),
    )
    agreed_at: datetime = Field(
        ...,
        description=(
            "When they agreed. On the wire because *a second ago* and *five hours "
            "ago* are the same refusal to a client that cannot see it, and the "
            "sentence a player reads has to be able to say which."
        ),
    )
    settles_at: datetime = Field(
        ...,
        description=(
            "When this agreement becomes final. Measured from the **score**, not "
            "from the tap: the person the grace protects is the opponent who has "
            "not read the score yet, and their clock started when it was put in "
            "front of them."
        ),
    )


class GameSchema(BaseModel):
    """One game, its court, and what it is right now."""

    game_id: UUID
    challenge_id: UUID = Field(
        ..., description="The ask whose line-up completed into this game"
    )
    sport: Sport
    kind: GameKind = Field(
        ...,
        description=(
            "Whether this evening is evidence. **Chosen when the game was "
            "arranged and never derived at the end** — a game nobody scored "
            "stays counted, because a friendly is a thing people choose."
        ),
    )
    window: Window | None = Field(
        default=None,
        description=(
            "How soon the week this was arranged for came round. ``null`` on a "
            "game born of a mutual yes: no grid was proposed from."
        ),
    )
    standing: GameStanding = Field(
        ...,
        description=(
            "What this game is at the instant it was read. **Derived from the "
            "record and the clock, never stored**, so it is right for the whole "
            "gap between a deadline and anything noticing."
        ),
    )
    planned_at: datetime = Field(
        ..., description="When the last seat accepted and this became a game"
    )
    played_at: datetime | None = Field(
        default=None,
        description=(
            "When somebody said it happened. **The entry carries the moment** — "
            "there is no booking and no calendar, so this is the moment of the "
            "entry itself. ``null`` while nobody has said so."
        ),
    )
    entry_closes_at: datetime | None = Field(
        default=None,
        description=(
            "When *we played* stops being sayable and the game becomes a game "
            "that never happened. ``null`` once somebody has said it happened."
        ),
    )
    seats: list[SeatingSchema] = Field(
        ..., description="The court, in the order the challenge handed it over"
    )
    score: ScoreSchema | None = Field(
        default=None,
        description=(
            "The agreed score. ``null`` until something settles on one — "
            "including while a lone score is still waiting, because a score "
            "nobody has answered yet is not the result."
        ),
    )
    outcome: Outcome | None = Field(
        default=None,
        description=(
            "Win or loss **for you**. ``null`` for every standing but a "
            "confirmed one: a game nobody scored moves nobody's Level and has "
            "no outcome to give anybody."
        ),
    )
    proposals: list[StandingProposalSchema] = Field(
        ...,
        description=(
            "The scores on the table, **side A's first and never in the order "
            "they arrived**. Empty unless the game is awaiting an answer: before "
            "that nobody has entered one, and after it the ending is on "
            "`standing` — a confirmed score is `score` and an unscored game is an "
            "evening, not a transcript of the argument. Two entries **is** the "
            "disagreement, and either side may agree with the other's."
        ),
    )
    acceptance: AcceptanceSchema | None = Field(
        default=None,
        description=(
            "The agreement that is waiting out its grace, and `null` when none "
            "is. **A counter voids one**, so this is what still stands rather "
            "than what was once recorded."
        ),
    )


class GameListResponse(BaseModel):
    """Your games, newest arrangement first.

    **One list and not several.** A game awaiting an entry, one awaiting an
    answer and one that never happened are one thing at three moments of its
    life, and splitting them would make the client's shelves the platform's
    opinion about which of them matters.

    ``read_at`` is the instant every standing and deadline here was folded
    against. It travels so a client's countdowns and the standings beside them
    cannot come from two different readings of the clock.
    """

    read_at: datetime
    games: list[GameSchema]
