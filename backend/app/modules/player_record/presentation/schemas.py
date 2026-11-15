"""The player record on the wire. **One shape, both routes.**

Your own record and a stranger's are the same response, and `is_self` is what
separates them — so a client renders one component, retitles it, and drops the
rows that do not apply to a person looking at themselves.

**There is no subject id on this response, deliberately.** The client is told
whether the record is its own rather than being handed the material to work it
out: an id would invite exactly the comparison `is_self` exists to replace, and
the comparison is wrong on the one screen where being wrong is most visible.

**An omitted field is not a null one.** ``OMITTED`` fields are absent from the
JSON, and the difference is the contract's own: *absent* means the field does not
apply to this person, and ``null`` would mean it applies and the answer is a
measured nothing. Nobody here is ever nulled.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import ReliabilityBand
from app.kernel import Sport
from app.modules.friends.domain.relation import FriendRelation
from app.modules.player_record.domain.record import (
    LAST_FIVE,
    GameOutcome,
    OnCourtVerdict,
    PlayerRecord,
)

#: The default that spells **omitted** — the same sentinel the shortlist's schema
#: uses, spelled here rather than imported: this context declares its own
#: presentation vocabulary for the reason it declares its own ports, and the two
#: are one line each.
OMITTED: Any = None


class SportPillSchema(BaseModel):
    """One sport this person is rated in, as a pill: the dot, the Level, the band.

    **Narrower than the panel below it, deliberately.** A pill answers *what else
    do they play*; how sure the platform is and what that rests on belong to the
    one sport the sheet is about, and repeating them four times would be four
    skill cards drawn as jewellery.
    """

    sport: Sport = Field(
        ..., description="Which sport. The client draws its own dot and short form."
    )
    level: float = Field(
        ..., description="Their Level in it, as RacketSkill published it."
    )
    band: str = Field(
        ...,
        description=(
            "The Level band's published name. **A key and never derived from "
            "the Level** — a client mapping a number to a band would be a second "
            "set of drawing constants, and the day the boundaries move the two "
            "would disagree."
        ),
    )


class RecordLikelyRangeSchema(BaseModel):
    """The **likely range** a Level sits in — μ ± σ, clamped to the scale.

    **Named for its surface, because the contract is one namespace and this
    arrived second.** ``matchmaking`` already publishes a ``LikelyRangeSchema``
    on the player card; a second class of that name does not shadow it, it
    *renames* it — the emitted document qualifies both by module and every
    generated type a shipped app already holds moves. It is ``games``' rule for
    ``GameStanding``, applied to the wire: the cost of a shared word is paid by
    whoever arrives second.

    The shape is deliberately identical to the card's. Two edges of one value,
    both rounded by the engine, and a client computes neither.
    """

    low: float
    high: float


class SkillPanelSchema(BaseModel):
    """The skill card, for the one sport this sheet is about.

    **The sport is resolved by the server and stated back.** You asked with
    `?sport=`; what you get is that sport where they are rated in it, and
    otherwise the one they have played most — so read `sport` here rather than
    assuming the answer is what you sent.
    """

    sport: Sport = Field(
        ...,
        description=(
            "Which sport this panel is about — **the resolved one, not the one "
            "asked for.** They differ whenever the subject holds no rating in "
            "the sport you arrived from."
        ),
    )
    level: float = Field(..., description="Their Level, as RacketSkill published it.")
    band: str = Field(
        ...,
        description=(
            "The band's published name, as a key. The band's numeric edges are "
            "**not** here: they are not a second range to compare `likely_range` "
            "against."
        ),
    )
    confidence: int = Field(
        ...,
        description=(
            "How sure the platform is, as a whole percentage — `rating`'s own "
            "figure and never re-derived here.\n\n"
            "**It travels with `counted_games` and is meaningless without it.** "
            "A confident-looking number built on three games must not read like "
            "one built on forty, which is the whole reason both cross."
        ),
    )
    counted_games: int = Field(
        ...,
        ge=0,
        description=(
            "**How many confirmed counted results have moved this Level, in this "
            "sport.** Deliberately not the player card's `counted_games`, which "
            "is how much they have *played*, over every sport, and includes an "
            "evening nobody agreed a score for.\n\n"
            "This one is what the certainty rests on, so it comes off the same "
            "stream as the Level beside it and moves in step with it. **`0` is a "
            "real answer here** and is not an absence: a rating from the "
            "questionnaire that no game has tested yet is exactly what it says."
        ),
    )
    likely_range: RecordLikelyRangeSchema = Field(
        ...,
        description=(
            "The range their Level probably sits in, μ ± σ as the engine "
            "rounded it. Always present: two people both showing 2,75 are told "
            "apart by how wide this is."
        ),
    )
    last_five: list[GameOutcome] = Field(
        ...,
        max_length=LAST_FIVE,
        description=(
            "Their last counted results **in this sport**, oldest to newest — "
            "the run of form drawn left to right.\n\n"
            "**Per sport, which is the fix.** A run built across every sport and "
            "drawn beneath a single sport's Level was squash results under a "
            "padel number.\n\n"
            "**Fewer than five is a real answer and is never padded**: three "
            "entries means three counted results, and the client draws the gap. "
            "An empty list means none of theirs has been counted and agreed.\n\n"
            "**There are no dates here, at any granularity.** A moment beside "
            "one of these would be activity recency, which no surface on this "
            "platform carries in any shape."
        ),
    )


class OpponentVarietySchema(BaseModel):
    """How widely this person spreads their games, over their **whole** record.

    **Two counts and no percentage, deliberately.** The card this sits on argues
    two rows above that a perfect record over nine games and one over forty are
    different claims and that a bar alone hides which — so publishing a bare
    share here would break the rule the card had just made about itself. Draw
    both: `70 % · 14 of 20`.

    **The share is yours to compute and it is one division.** Nothing is rounded
    on this side and there is no banding, no floor and no tone attached — unlike
    a Level's band, which is a key precisely because a client deriving it would
    be a second set of drawing constants.

    **This is a career statistic, not a window.** It is every counted game the
    platform has recorded for them, which is what the number means: *how widely
    do they spread their games*, rather than *how widely this season*. There is
    no decay behind it and no horizon.

    **It prices no promise.** It is no part of Player reliability, and it
    neither raises nor lowers anybody's standing. It is context for a Level — a
    low figure is somebody playing the same few faces every week, whose rating
    may be narrow but untested.
    """

    distinct_opponents: int = Field(
        ...,
        ge=1,
        description=(
            "How many **different people** those games were against.\n\n"
            "**A doubles partner is one of them.** *A pair is anybody you were "
            "on a court with* is the rule this platform already counts "
            "familiarity by, and a figure counting opponents alone would say "
            "that somebody who partners the same person every week spreads "
            "their games as widely as somebody who does not."
        ),
    )
    times_on_court: int = Field(
        ...,
        ge=1,
        description=(
            "How many **times they were on a court with somebody** across their "
            "counted games — the denominator of the pair, and never a count of "
            "games.\n\n"
            "**A doubles evening contributes three.** Games were the denominator "
            "first and are only divisible in singles: one doubles game put three "
            "people on the court, so the pair read `3 of 1` and the share went "
            "over a hundred. Counting the seats opposite makes both halves the "
            "same kind of thing — *five different people across ten times on a "
            "court* — and `distinct_opponents` can never exceed it.\n\n"
            "**It is not `skill.counted_games`, and the two will differ on this "
            "same response.** That one is *what this Level rests on*: confirmed "
            "results, in one sport, that the rating actually folded. This one "
            "is *how much have they played*: every sport, and an evening "
            "nobody agreed a score for is in it. Two honest numbers about the "
            "same person, answering two questions — do not reconcile them.\n\n"
            "**Counted rather than every game**: a friendly was never evidence "
            "about anybody by the choice of the people who arranged it, and it "
            "is out of both halves of this pair rather than only the bottom "
            "one."
        ),
    )


class RecordSportsmanshipSchema(BaseModel):
    """What other players said — **the one thing here nobody counted.**

    **Named for its surface, because the contract is one namespace.** The word
    belongs to ``sportsmanship``, which has a surface of its own; a class simply
    called ``SportsmanshipSchema`` here would not shadow whatever that context
    publishes next, it would *rename both* — and every generated type a shipped
    app already holds would move. It is ``RecordLikelyRangeSchema``'s rule.

    **Its own heading, and never mixed with the rows above.** The record card is
    headed *counted by the system, not written by people*, which is the promise
    every count under it rests on; a number people typed sitting beneath that
    title would make the title false. Draw this under *What opponents said*
    and the two apart.

    **Both numbers, always, from the very first rating.** There is no minimum
    because the count does a minimum's work honestly: `4,7 / 5 · 17 players` and
    `3,0 / 5 · 1 player` are the same field, and the second one visibly reads as
    one person's opinion. Print them together — a figure drawn without its count
    is this field's one way of lying.

    **`raters` is people, not ratings.** Only somebody's most recent stars about
    a person ever count, so a weekly partner is **one** rater however many
    evenings they play. That is what makes a high count evidence of *breadth*.

    **It is the fifty most recent raters and nothing is trimmed.** Somebody can
    recover from a bad patch by playing with fifty other people; nobody's rating
    is discarded for being an outlier, because deciding which raters were wrong
    is a larger claim than publishing the number.

    **Nothing acts on it, and you should say so if you draw it beside Player
    reliability.** A low figure here does not hide anybody, demote anybody or
    keep anybody out of a game — Player reliability is the counted-only number,
    and the reliability filter reads that and never this.

    **On your own record too, at this resolution.** The person it is about
    reads the same figure and the same count a stranger does; the coarse band
    that used to stand in for it on their own sheet is gone from the shape. See
    the field on the response for why.
    """

    average: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description=(
            "The mean of what other players said, **out of five, to one "
            "decimal.** Served rather than derived: there is one mean and one "
            "rounding of this record on the platform, and it rounds halves "
            "up.\n\n"
            "**One to five, and never nought.** There is no zero on the scale a "
            "player taps — a rating that reads as *worthless* is a weapon out of "
            "proportion to a tap — so a person nobody has rated is **absent** "
            "here rather than sitting at the bottom of it."
        ),
    )
    raters: int = Field(
        ...,
        ge=1,
        description=(
            "How many **different people** the figure rests on. Always drawn "
            "beside it.\n\n"
            "**People and not ratings.** Only a rater's most recent stars about "
            "somebody count, so ten evenings with the same partner contribute "
            "one. A high count is therefore evidence of breadth rather than of "
            "repetition, and it cannot be inflated by volume.\n\n"
            "**At most fifty**, which is the window: the fifty most recent "
            "raters, each contributing the one answer that stands."
        ),
    )


class BackWithEveryoneSchema(BaseModel):
    """The figure that deals you with everyone in your groups again (ADR-0195
    §6) — *Some players in your groups play only with High reliability or above.
    At 75 you're dealt with everyone again.* **Names nobody.**"""

    band: ReliabilityBand = Field(
        ...,
        description=(
            "The highest minimum among the filters that keep you off a court — "
            "`HIGH` or `MEDIUM` — the word in *play only with High reliability or "
            "above*. Draw the word from this code."
        ),
    )
    points: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Where that band begins — *at 75 you're dealt with everyone again*. "
            "Reaching it passes every one of those filters at once."
        ),
    )


class ReliabilityFilterSchema(BaseModel):
    """**Your** reliability filter — *Play only with players of at least High
    reliability* — as it stands in your groups, and whether anybody else's keeps
    you off a court (ADR-0195 §6). **On your own record only, and it names
    nobody**: two counts and, where it applies, a band."""

    minimum: ReliabilityBand = Field(
        default=OMITTED,
        description=(
            "`MEDIUM` or `HIGH` — the switch's position. **Omitted while the filter "
            "is off**, which it is until the player switches it on "
            "(`PUT /players/me/reliability-filter`)."
        ),
    )
    hides: int = Field(
        ...,
        ge=0,
        description=(
            "How many of the players in your groups your filter keeps off your "
            "courts — *Your filter hides 2 of the 11 players in your groups*. "
            "Never somebody New, who passes every filter; `0` while it is off."
        ),
    )
    of: int = Field(
        ...,
        ge=0,
        description=(
            "Everybody else in every group you are in, each counted once — the *of 11*."
        ),
    )
    back_with_everyone: BackWithEveryoneSchema = Field(
        default=OMITTED,
        description=(
            "**Present only while somebody in your groups filters you out** — "
            "draw *Some players in your groups play only with High reliability or "
            "above. At 75 you're dealt with everyone again.* Omitted while nobody "
            "does: New players pass every filter."
        ),
    )


class ReliabilitySchema(BaseModel):
    """**Player reliability** — the figure in points, its band, *New*, and the
    four counts the record shows beside it (ADR-0195 §1).

    **Counted by the system, not written by people.** Every number under this
    heading is something the platform observed. What opponents said about
    somebody is not here and will not be: an opinion under this title would make
    the title false.

    **Everyone starts at 100.** A failure takes a fixed price off — *Didn't
    come* −25, *Came late* −10, leaving after the cut-off with the seat left
    empty −15, leaving before it (or a card not fixed in time) when the empty
    seat calls the game off −10 — and every game played through gives 5 back,
    never above 100. Each drops out six months after it happened. Silence on a
    score costs nothing, and a dispute costs nothing.

    **No ledger and no ratio.** The figure is points, and the counts are counts
    over the last six months: draw *turned up 12 of 13*, never a percentage.
    """

    player_score: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Their **Player reliability** in points, 0–100 — the same figure a "
            "group's Members list prints. **Everyone starts at 100**, so a "
            "player nothing has happened to reads `100`."
        ),
    )
    band: ReliabilityBand = Field(
        ...,
        description=(
            "The word under the figure: `VERY_HIGH` 90–100, `HIGH` 75–89, "
            "`MEDIUM` 50–74, `LOW` below 50. **Served, never derived** — draw "
            "the word from this code and hold no thresholds of your own."
        ),
    )
    is_new: bool = Field(
        ...,
        description=(
            "**New** — fewer than 3 games played through, ever, across sports. "
            "Draw *100 · New*. A player who stops for six months does not become "
            "New again."
        ),
    )
    turned_up: int = Field(
        ...,
        ge=0,
        description=(
            "*Shows up*: how many of the games that reached their hour with them "
            "on the court they turned up to, **late counting as turned up** — "
            "over the last six months."
        ),
    )
    turned_up_of: int = Field(
        ...,
        ge=0,
        description=(
            "*Shows up*'s *of*: the games that reached their hour with them on "
            "the court, over the last six months — *turned up 12 of 13*. May be "
            "`0`: nothing has fallen due in six months."
        ),
    )
    late: int = Field(
        ...,
        ge=0,
        description=(
            "*Being late*: how many times they came late — arrived ten to thirty "
            "minutes after the start, or said *I was there* and were confirmed — "
            "over the last six months."
        ),
    )
    kept: int = Field(
        ...,
        ge=0,
        description=(
            "*Keeps plans*: how many of the booked games they held a seat on "
            "they kept — still in when its hour came with every seat held — over "
            "the last six months. A game they Didn't come to is kept here: it is "
            "priced once, on *Shows up*."
        ),
    )
    kept_of: int = Field(
        ...,
        ge=0,
        description=(
            "*Keeps plans*' *of*: the booked games they were in, kept or broken "
            "by leaving so that the game was called off or played short, over "
            "the last six months — *kept 13 of 14*. Leaving when the seat was "
            "taken, or before the cut-off when the game still played, is in "
            "neither."
        ),
    )
    left_in_dispute: int = Field(
        ...,
        ge=0,
        description=(
            "*Results left in dispute*: how many games, over the last six "
            "months, they put up one of two scores that named different winners "
            "and neither side gave way. **Information only — it costs no "
            "points.**"
        ),
    )
    filter: ReliabilityFilterSchema = Field(
        default=OMITTED,
        description=(
            "**Your** reliability filter and how many players in your groups it "
            "hides, and the figure that brings you back where somebody's filter "
            "keeps you off a court (#661).\n\n"
            "**On `/players/me/record` always, and on nobody else's record "
            "ever** — a filter is a preference about other people, and showing it "
            "to them would say who filters whom."
        ),
    )


class RecordPhotoSchema(BaseModel):
    """One of a player's photos on their record (``docs/adr/0204`` §2)."""

    photo_id: UUID
    photo_url: str = Field(
        description=(
            "Short-lived signed URL that draws this photo, minted per response "
            "and stored nowhere."
        )
    )


class PlayerRecordResponse(BaseModel):
    """Everything the platform will say about one person, to this reader.

    **Open to any reader** (``docs/adr/0204`` §2), except somebody who turned
    *Show me to new people* off and shares no group, game or friendship with
    you, nor is in a group you run — and anybody a live gate no longer admits,
    a block either way among them. Those are `404`, in one shape that names
    nothing.
    """

    is_self: bool = Field(
        ...,
        description=(
            "Whether this is the reader's own record. **The server's answer, "
            "and the client never derives it** by comparing the id it asked "
            "about against its session — the sheet retitles to *How others see "
            "you* and drops the distance and the fit pill, and getting that "
            "wrong is most visible on the one screen it matters on. It decides "
            "the title and nothing on the sheet: every zone, what other players "
            "said included, is the same fact whoever is reading.\n\n"
            "`true` on `/players/me/record` always, and on the parameterised "
            "route when a client asks about itself."
        ),
    )
    relation: FriendRelation = Field(
        description=(
            "**Your** relation to this person — the left button of the record's "
            "foot, beside *Block* (`docs/adr/0202` §1): `NONE` — **Add friend** "
            "when `can_add_friend` is `true`, else *Block* stands alone; `SENT` "
            "— **Request sent ▾** (*Cancel request*), for as long as your "
            "request stays open; `ASKED_YOU` — **Accept**; `FRIEND` — **Friend "
            "✓ ▾** (*Remove friend*). `NONE` on your own record, which draws "
            "neither button. Nothing here says who else they are friends "
            "with.\n\n"
            "**There is no Unblock here** (`docs/adr/0203` §8): a record never "
            "opens between two people either of whom blocked the other, so "
            "*Block* is always *Block*. Unblock lives in You › Blocked players."
        )
    )
    can_add_friend: bool = Field(
        description=(
            "Whether to offer **Add friend** (`docs/adr/0204` §2): `relation` is "
            "`NONE` and this is not your own record. A request is admitted by "
            "the rule this record opened by, so a record you can read is "
            "somebody you can ask — as many as you like, with no daily limit. "
            "Send a request made from a record opened on the Rankings page "
            "with `made_from` `RANKING` and that page's sport."
        )
    )
    nickname: str = Field(
        ...,
        description=(
            "Their handle, unique across the platform, and the title of the "
            "sheet — drawn large, with nothing under it, and never with an @. "
            "**Nothing may derive a familiar form from it**: every sentence "
            "naming somebody uses the whole nickname or names nobody "
            "(``docs/adr/0199`` §1)."
        ),
    )
    photos: list[RecordPhotoSchema] = Field(
        ...,
        description=(
            "**Every** photo, in their own order — the first is `photo_id`'s — "
            "each with a short-lived signed URL minted for this response "
            "(`docs/adr/0204` §2). Empty when they have none. Always present."
        ),
    )
    photo_id: UUID = Field(
        default=OMITTED,
        description=(
            "The first photo — order is meaning in a photo list. **Omitted** "
            "when the player has no photograph, and the client draws the "
            "generated court poster rather than a placeholder."
        ),
    )
    photo_url: str = Field(
        default=OMITTED,
        description=(
            "Short-lived signed URL that draws that photo. **Minted per "
            "response and stored nowhere** — this context stores nothing at "
            "all — so two reads of one record carry two links to one "
            "photograph.\n\n"
            "**You cannot sign one yourself.** `GET /photos/{photo_id}` signs "
            "only *your own* photos and refuses a stranger's id deliberately, "
            "so this is the only address this photograph has.\n\n"
            "**Present exactly when `photo_id` is.**"
        ),
    )
    review: OnCourtVerdict = Field(
        default=OMITTED,
        description=(
            "What the on-court check concluded about `photo_id`, or **omitted** "
            "where this photograph has not been checked.\n\n"
            "**Omitted is not `allowed`, and only `allowed` earns a shield.** "
            "Three answers, not two: checked and passed, checked and flagged, "
            "and *nobody looked* — a photo that arrived while the reviewer "
            "could not be reached, or before the check existed at all. A client "
            "that drew a tick on the absence would be claiming a check happened "
            "on every photograph on the platform.\n\n"
            "**A fact about this photograph and not about the player**, present "
            "only beside `photo_id`. `flagged` blocks nothing — the photo is "
            "stored, it is shown, and the check is wrong sometimes. The "
            "evidence behind the verdict never crosses on any route."
        ),
    )
    area_code: str = Field(
        ...,
        description=(
            "Their coarse area, as a machine code. **An identifier and never a "
            "name** — nothing here can turn a coordinate into the name of a "
            "neighbourhood. What it licenses is the one comparison a client "
            "makes for itself: two players in the same square share a code, "
            "which is what *in your area* is drawn from."
        ),
    )
    social_tags: list[str] = Field(
        ...,
        description=(
            "The Social tag ids they hold, in the vocabulary's own order. "
            "**Which of them the reader also holds is the client's own "
            "comparison** — the platform states no overlap here, so a record "
            "draws them untinted and claims nothing about common ground."
        ),
    )
    intro: str = Field(
        default=OMITTED,
        # No `max_length`: the cap binds the write and never the read.
        description=(
            "One line this player wrote about themselves — their **intro** — "
            "verbatim, drawn under the nickname. **Omitted where they wrote "
            "none**, and never an empty string: the intro is optional, and a "
            "player who skipped has no line rather than an empty one.\n\n"
            "Read off the profile as it stands. Fenced at the write "
            "against a phone number, an email, a URL or an `@handle`, so what "
            "arrives is a line about a player and never a way to reach one. "
            "Present on your own record as on anybody else's — it is what "
            "strangers read, shown back to you."
        ),
    )
    sports: list[SportPillSchema] = Field(
        ...,
        description=(
            "One pill per sport they hold a rating in, **in the sport "
            "registry's own order** — the same order every list of sports on "
            "this surface takes, so a client never sorts one.\n\n"
            "**Empty for somebody rated in nothing**, which is an ordinary state "
            "part way through onboarding rather than an error. It is empty "
            "exactly when `skill` is absent."
        ),
    )
    skill: SkillPanelSchema = Field(
        default=OMITTED,
        description=(
            "The skill card, for the one sport this sheet is about.\n\n"
            "**Which sport is resolved here and stated back on the panel.** The "
            "`?sport=` you asked with wins where they are rated in it; otherwise "
            "it falls back to the sport they have played most, ties broken by "
            "the sport registry's own order. A fallback on their *highest* Level "
            "would make the header a boast about a sport nobody asked about.\n\n"
            "**Omitted where no sport resolves** — that is, where they are rated "
            "in nothing at all. The header draws the poster with no Level on it, "
            "and there is no panel of noughts to mistake for a bad record."
        ),
    )

    reliability: ReliabilitySchema = Field(
        ...,
        description=(
            "**Player reliability** — the figure in points, its band, *New* and "
            "the four counts.\n\n"
            "**Always present.** Everyone starts at 100, so somebody nothing has "
            "happened to reads `100`, `VERY_HIGH`, `is_new: true`, every count "
            "`0`.\n\n"
            "It is about **no sport**, like `variety`: `?sport=` does not move "
            "it. Turning up is a habit, not a padel habit."
        ),
    )

    variety: OpponentVarietySchema = Field(
        default=OMITTED,
        description=(
            "How widely they spread their games — **the raw pair, over their "
            "whole record.**\n\n"
            "**Omitted where no counted game has ever been recorded for "
            "them**, which is not a nought and not `0 / 0`: a habit nobody has "
            "been observed having is not a narrow one. It is a **different "
            "absence from `skill`'s** — somebody rated in nothing may have "
            "played all week, and somebody rated in four sports may never have "
            "had a game counted.\n\n"
            "**It is about every sport**, unlike `skill.last_five` above it. "
            "`?sport=` does not move it: a person who plays padel with the same "
            "four faces and squash with twenty has one habit, and a figure "
            "narrowed to one sport would be a different statistic under the "
            "same word."
        ),
    )

    sportsmanship: RecordSportsmanshipSchema = Field(
        default=OMITTED,
        description=(
            "**What other players said** — the average out of five and how many "
            "different people it rests on.\n\n"
            "**Its own zone, deliberately apart from `reliability`.** That card "
            "promises *counted by the system, not written by people*, and this "
            "is the one thing here people wrote. Two headings, no lie.\n\n"
            "**Omitted where nobody has rated them**, which is most people and "
            "is never a nought: rating is a favour, ignoring the card costs "
            "nothing, and nothing anywhere records that somebody did not "
            "answer. It is a **third absence** and asks a third question — not "
            "`skill`'s and not `variety`'s, since a game played is not an "
            "opinion anybody offered.\n\n"
            "**On your own record too, and it is the same figure.** What you "
            "read about yourself under *Sportsmanship, by players* is what a "
            "stranger reads about you — `4,3 / 5 · 12 players` — with nothing "
            "coarsened and no count withheld. The three-step band that used to "
            "stand in for it on your own sheet is gone from this shape; ADR-0179 "
            "§5 decides that and names what it costs.\n\n"
            "**It is about no sport**, like `variety` and `reliability`: "
            "`?sport=` does not move it. How somebody is to play with is not a "
            "padel fact.\n\n"
            "**The matcher never reads it.** A low figure hides nobody and "
            "demotes nobody — Pass and Block are the controls that act, and both "
            "are deliberate."
        ),
    )

    @classmethod
    def of(cls, record: PlayerRecord) -> "PlayerRecordResponse":
        """Render one record, omitting rather than nulling what is absent.

        The photograph's three fields **travel together**: an id with no address
        beside it is a photograph nothing can draw, and a verdict with no picture
        under it is a shield floating over a poster somebody else generated.
        """

        identity = record.identity
        fields: dict[str, Any] = {
            "is_self": record.is_self,
            "nickname": identity.nickname,
            "area_code": identity.area_code,
            "social_tags": list(identity.social_tags),
            "sports": [
                SportPillSchema(sport=one.sport, level=one.level, band=one.band)
                for one in record.sports
            ],
        }
        fields["relation"] = FriendRelation(record.relation.value)
        fields["can_add_friend"] = record.can_add_friend
        if identity.intro is not None:
            # Omitted where nothing was written, never `""` (`docs/adr/0170`).
            fields["intro"] = identity.intro
        if record.skill is not None:
            panel = record.skill
            fields["skill"] = SkillPanelSchema(
                sport=panel.sport,
                level=panel.level,
                band=panel.band,
                confidence=panel.confidence,
                counted_games=panel.counted_games,
                likely_range=RecordLikelyRangeSchema(
                    low=panel.likely_range.low, high=panel.likely_range.high
                ),
                last_five=list(panel.last_five),
            )
        watched = record.reliability
        reliability: dict[str, Any] = {
            "player_score": watched.player_score,
            "band": watched.band,
            "is_new": watched.is_new,
            "turned_up": watched.turned_up,
            "turned_up_of": watched.turned_up_of,
            "late": watched.late,
            "kept": watched.kept,
            "kept_of": watched.kept_of,
            "left_in_dispute": watched.left_in_dispute,
        }
        if watched.filter is not None:
            # Your own record's alone (#661): omitted on everybody else's.
            own = watched.filter
            filtering: dict[str, Any] = {"hides": own.hides, "of": own.of}
            if own.minimum is not None:
                filtering["minimum"] = own.minimum
            if own.back_with_everyone is not None:
                filtering["back_with_everyone"] = BackWithEveryoneSchema(
                    band=own.back_with_everyone.band,
                    points=own.back_with_everyone.points,
                )
            reliability["filter"] = ReliabilityFilterSchema(**filtering)
        fields["reliability"] = ReliabilitySchema(**reliability)
        if record.sportsmanship is not None:
            said = record.sportsmanship
            fields["sportsmanship"] = RecordSportsmanshipSchema(
                average=said.average, raters=said.raters
            )
        if record.variety is not None:
            fields["variety"] = OpponentVarietySchema(
                distinct_opponents=record.variety.distinct_opponents,
                times_on_court=record.variety.times_on_court,
            )
        fields["photos"] = [
            RecordPhotoSchema(photo_id=photo.photo_id, photo_url=photo.photo_url)
            for photo in record.photos
        ]
        if identity.photo_id is not None and record.photo_url is not None:
            fields["photo_id"] = identity.photo_id
            fields["photo_url"] = record.photo_url
            if identity.review is not None:
                fields["review"] = identity.review
        return cls.model_validate(fields)


__all__ = [
    "BackWithEveryoneSchema",
    "OpponentVarietySchema",
    "PlayerRecordResponse",
    "RecordLikelyRangeSchema",
    "ReliabilityFilterSchema",
    "ReliabilitySchema",
    "SkillPanelSchema",
    "SportPillSchema",
    "RecordSportsmanshipSchema",
]
