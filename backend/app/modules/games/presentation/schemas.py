"""The game wire shapes — **a record of an evening, and never a verdict.**

Three rules decide everything below.

**The standing is derived and travels as a code.** ``GameStanding`` is nine values —
``STARTED_SHORT`` arrived with leaving a booked game (#544), ``NO_SHOW_REPORTED`` and
``NO_SHOW`` with reporting a player who did not come to one (#547) — and the words for
them are the client's (``docs/adr/0022``). It is on the response
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
from typing import Any
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
from app.modules.player_profile.domain.weekly_hours import Window


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
    """One position on one side: a person, or a seat somebody has left.

    **The court is frozen until somebody leaves it** (``docs/adr/0162``). An
    open seat is drawn, never dropped — `player_id` is `null` and the seat keeps
    its place — so a four with one seat open is still a four and the client
    folds *Needs a player* from it. Nothing on the wire names that rung.

    **A name, and nothing else about them** (``docs/adr/0141``). A Level, a
    band, an area and a run of form are what a *searcher* reads to decide about a
    game that might happen, and a gate decided they may see them; this is the
    record of a game that did, and it re-publishes nobody's profile off the back
    of it. The court is the whole of the permission — ``GET /games`` answers
    about games you were on the court of — so nothing here is re-gated against
    who is reading.
    """

    side: GameSide
    player_id: UUID | None = Field(
        ...,
        description=(
            "Who holds this seat. ``null`` on a seat somebody has **left** and "
            "nobody has filled yet: the seat stays, drawn empty, and the game "
            "is awaiting a player before it can be recorded as played. "
            "**Always present** — a seat is never dropped."
        ),
    )
    name: str | None = Field(
        default=None,
        description=(
            "The whole name, and **nothing may derive a familiar form from "
            "it** — every sentence naming somebody uses all of it or names "
            "nobody (``docs/adr/0107``, ``docs/adr/0171``). Never the "
            "nickname: a handle is drawn on a record and said nowhere.\n\n"
            "``null`` where ``users`` no longer has this account, and on an "
            "open seat — never for an unnamed player, whom the entry gate holds "
            "at the naming step. The seat stays: dropping it would publish a "
            "three-person doubles game, and the screen has a side to name "
            "instead."
        ),
    )


class CalledOffBySchema(BaseModel):
    """Who called the game off, and what they are called (``docs/adr/0172`` §4).

    **The name is carried because the court cannot supply it**: the leaver whose
    departure called the game off has been **vacated** — their seat is drawn
    `player_id: null` — so the seats alone could not name them. It is the same
    name a seat carries, read in the same set read, and it is `null` for the
    same reason a seat's is: an account `users` no longer answers for.

    **A departure is told from a press by whether this player still holds a
    seat on the game.** The presser does; the leaver's seat is open. No second
    field says which — the record already does.
    """

    player_id: UUID
    name: str | None = Field(
        default=None,
        description=(
            "The whole name, and **nothing may derive a familiar form from "
            "it** (``docs/adr/0107``, ``docs/adr/0171``). ``null`` where "
            "``users`` no longer has the account — never for an unnamed "
            "player, whom the entry gate holds at the naming step."
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


class NoShowSchema(BaseModel):
    """A player reported as not coming to this booked game (#547; the
    mechanics §15.3) — and what became of it. **Who reported them is not
    here**: the report is the game's, said by the people who came, and a name
    on it would be the platform pointing at one of them."""

    player_id: UUID
    name: str | None = Field(
        default=None,
        description=(
            "Their whole name, as a seat carries it. ``null`` where ``users`` "
            "no longer has the account."
        ),
    )
    reported_at: datetime
    dispute_by: datetime = Field(
        ...,
        description=(
            "The end of their day to say they came — 24 hours from the report. "
            "**Nothing happens at this moment**: an undisputed report simply "
            "stands from here on, and the game reads `NO_SHOW` once every "
            "report has had its day."
        ),
    )
    disputed_at: datetime | None = Field(
        default=None,
        description=(
            "When they disputed it. **Nobody arbitrates**: a disputed report "
            "falls and is on nobody's record; a game whose every report was "
            "disputed is `UNSCORED`."
        ),
    )


class GameSchema(BaseModel):
    """One game, its court, and what it is right now."""

    game_id: UUID
    challenge_id: UUID = Field(
        ...,
        description=(
            "The booking this game was opened for — its id, under the name the "
            "field was born with."
        ),
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
            "How soon the week this was arranged for came round. ``null`` on "
            "every booked game, which has an hour instead."
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
        ..., description="When the court was booked and this became a game"
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
            "that never happened. ``null`` once somebody has said it happened, "
            "and ``null`` on a game that was called off — the window no longer "
            "matters, and a card that shelved itself by it would stay for eight "
            "days."
        ),
    )
    called_off_at: datetime | None = Field(
        default=None,
        description=(
            "When it was called off — at the club's cut-off with a seat open, "
            "or by the club taking the court back (``docs/adr/0163``). ``null`` "
            "unless the standing is `CALLED_OFF`; "
            "then the act's own instant, which is what the ending card is "
            "shelved from — a day later, as `played_at` and `entry_closes_at` "
            "already shelve the other endings. Who is `called_off_by`."
        ),
    )
    called_off_by: CalledOffBySchema | None = Field(
        default=None,
        description=(
            "The player who called it off, and their name (``docs/adr/0172`` "
            "§4). ``null`` on every standing but `CALLED_OFF` — and on a booked "
            "game called off by its cut-off or its club, which nobody did."
        ),
    )
    seats: list[SeatingSchema] = Field(
        ..., description="The court, in the order the booking handed it over"
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
    no_shows: list[NoShowSchema] = Field(
        ...,
        description=(
            "Everybody reported as not coming to this **booked** game, in the "
            "court's order (#547). Empty on every other game. A report is the "
            "game's entry: no score is on the table beside one, and **the game "
            "does not count** whatever it comes to."
        ),
    )


class ReportANoShowRequest(BaseModel):
    """*Kuba didn't come.*"""

    player_id: UUID = Field(
        ..., description="Who did not come — somebody else on the game's court."
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


# ---------------------------------------------------------------------------
# The pairing read — ``docs/adr/0161``
# ---------------------------------------------------------------------------

#: The default that spells **omitted** — *this field does not apply here* — the
#: matcher's sentinel spelled again for the matcher's reason, on the one read in
#: this context that needs it.
#:
#: A field carrying it is not in the schema's ``required`` list, so it generates
#: as ``field?: T``, and the pairing route is declared
#: ``response_model_exclude_unset=True`` so it is genuinely absent from the JSON
#: rather than present as ``null``. Every absence on this response is *this does
#: not apply* — a forecast that could not be computed, stakes on a friendly —
#: and none of them is a measured nothing, so nothing here is ever ``null``.
OMITTED: Any = None


class GamePairingRangeSchema(BaseModel):
    """The likely range a seat's Level sits in — μ ± σ as RacketSkill published it.

    Named for its surface rather than reusing the card's ``LikelyRangeSchema``:
    a second class of that name would not shadow the card's in the contract, it
    would rename it (``docs/adr/0159``'s rule, one context over).
    """

    low: float
    high: float


class GamePairingSeatSchema(BaseModel):
    """One seat on the court and the Level of the person in it.

    **This is not a card**, and it is not the seat on `GET /games` either — that
    one carries a name and nothing else (``docs/adr/0141``), and it is
    untouched. What is here is the four figures a record's skill panel and a
    player card already publish, read beside the game for as long as the game
    has not happened.
    """

    player_id: UUID
    level: float = Field(..., description="Their Level, as RacketSkill published it.")
    band: str = Field(
        ...,
        description=(
            "The Level band's published name, as a key — RacketSkill's own "
            "vocabulary, exactly as the player card and the record print it. "
            "The band's numeric edges are **not** here: they are not a second "
            "range to compare `range` against."
        ),
    )
    range: GamePairingRangeSchema = Field(
        ...,
        description=(
            "The likely range their Level sits in, as the play card ships it. "
            "**The client computes nothing** — not this from `confidence`, and "
            "not a band from `level`."
        ),
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "How sure the platform is, as a whole percentage — `rating`'s own "
            "figure and never re-derived here."
        ),
    )


class GamePairingForecastSchema(BaseModel):
    """How even this court's game is forecast to be, **read in your direction**.

    ``provisional`` travels inside the forecast rather than beside it, on the
    engine's own rule: the failure guarded against is a screen showing the
    number without its caveat. **It is never `true` on a game today** — a
    line-up is frozen at the plan, so no side is short — and the field is kept
    because the shape is the court's. When a seat can be open, the answer is
    *omitted*, never provisional.
    """

    pct: int = Field(..., ge=0, le=100)
    sigma_group: float = Field(
        ..., description="The confidence is part of the claim, so it crosses with it."
    )
    provisional: bool
    assumption: str | None = Field(
        ...,
        description=(
            "What the provisional figure assumed, as a code the client renders "
            "in its own words. Null when nothing was assumed — which, on a "
            "game, is always."
        ),
    )


class GamePairingSplitSchema(BaseModel):
    """The two side strengths the forecast was read from, **in your direction**.

    `your_side` is yours wherever you sit, and `gap` is `your_side − their_side`
    — **signed and served**, so two readers on opposite sides see the sign flip
    and neither subtracts two rounded figures the engine subtracted unrounded.
    A side's strength is not the mean of the people on it, which is why these
    are numbers only the engine has.
    """

    your_side: float
    their_side: float
    gap: float


class GamePairingAtStakeSchema(BaseModel):
    """What a **counted** game on this court would do to your Level.

    The rating engine's own update rule read forward, **side against side** —
    the pair the result will deliver if the game is played, and the same pair
    for everybody on your side.
    """

    win_delta: float
    loss_delta: float


class GamePairingResponse(BaseModel):
    """What this platform makes of your court, computed when you asked.

    **Read beside the game and stored nowhere.** Everything here is as-of-now
    and means what a card means *because this game has not happened*; the route
    refuses once it has. Nothing on `GET /games` changes: a seat there still
    carries a name and nothing else.

    **Three blocks, and each is omitted on its own ground.** `forecast` and
    `split` go together — one computation — and are omitted when the pairing
    cannot be computed: somebody on the court holds no rating in the sport, or
    a seat could not be priced. There is no reason beside the absence; draw
    nothing and say nothing. `at_stake` is omitted on a friendly, where a
    counted result is *meaningless rather than unavailable*, and where the rule
    has nothing to move or nothing to price against — you hold no rating in
    the sport, or nobody across the net does. `seats` names the Level of
    everybody the platform holds one for, and a court with an unrated member
    still names the rated ones.
    """

    read_at: datetime = Field(
        ...,
        description=(
            "The instant the game's standing was folded at and the pairing "
            "computed against."
        ),
    )
    forecast: GamePairingForecastSchema = Field(
        OMITTED,
        description=(
            "How even the game is forecast to be, in your direction. **Omitted "
            "when the pairing cannot be computed**, and always together with "
            "`split`."
        ),
    )
    split: GamePairingSplitSchema = Field(
        OMITTED,
        description=(
            "The evidence behind `pct`: between what and what, on the scale you "
            "already read Levels on. **Omitted together with `forecast`.**"
        ),
    )
    at_stake: GamePairingAtStakeSchema = Field(
        OMITTED,
        description=(
            "What a counted result would do to your Level. **Omitted on a "
            "friendly** — meaningless rather than unavailable — and omitted "
            "where you hold no rating in this sport, or nobody on the other "
            "side does. A side with one unrated seat is priced over the "
            "people on it who are rated, because that is what the result will "
            "do. Never a pair of zeros."
        ),
    )
    seats: list[GamePairingSeatSchema] = Field(
        ...,
        description=(
            "One row per seat whose person holds a rating in this sport, in the "
            "court's own order. Somebody unrated is simply not here."
        ),
    )
