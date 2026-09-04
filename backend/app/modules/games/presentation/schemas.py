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
    """One person, on one side. The court is frozen at the plan."""

    side: GameSide
    player_id: UUID


class StandingProposalSchema(BaseModel):
    """The score waiting on an answer, when exactly one is.

    ``null`` in every other case, and the two are different: nothing has been
    entered, or **both sides have spoken** and neither score is *the* one. The
    second is the disagreement this platform does not resolve, and the client
    reads it off `standing` rather than off an absence here.
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
    standing_proposal: StandingProposalSchema | None = Field(
        default=None,
        description="The score waiting on an answer, when exactly one is.",
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
