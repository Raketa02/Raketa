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

from app.kernel import Sport
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

    **It prices no promise.** It is not a reliability strand, it is in no
    weighted score, and it neither raises nor lowers anybody's standing. It is
    context for a Level — a low figure is somebody playing the same few faces
    every week, whose rating may be narrow but untested.
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
    games_played: int = Field(
        ...,
        ge=1,
        description=(
            "How many **counted games** they were on the court for — the "
            "denominator of the pair.\n\n"
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


class PlayerRecordResponse(BaseModel):
    """Everything the platform will say about one person, to this reader.

    **Read through a prior disclosure and never about a person at large.** A
    record opens for somebody a search of yours returned, somebody you share an
    open challenge or a game with, and yourself. Anybody else — and anybody a
    live gate no longer admits — is `404`, in one shape that names nothing.
    """

    is_self: bool = Field(
        ...,
        description=(
            "Whether this is the reader's own record. **The server's answer, "
            "and the client never derives it** by comparing the id it asked "
            "about against its session — the sheet retitles to *How others see "
            "you*, drops the distance and shows a coarse band where a figure "
            "would be, and getting that wrong is most visible on the one screen "
            "it matters on.\n\n"
            "`true` on `/players/me/record` always, and on the parameterised "
            "route when a client asks about itself."
        ),
    )
    nickname: str = Field(
        ...,
        description=(
            "The whole handle. There is no name in this platform and **nothing "
            "may derive a familiar form from it** — every sentence naming "
            "somebody uses the whole handle or names nobody."
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
            "opened without a search behind it draws them untinted and claims "
            "nothing about common ground."
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
        if record.variety is not None:
            fields["variety"] = OpponentVarietySchema(
                distinct_opponents=record.variety.distinct_opponents,
                games_played=record.variety.games_played,
            )
        if identity.photo_id is not None and record.photo_url is not None:
            fields["photo_id"] = identity.photo_id
            fields["photo_url"] = record.photo_url
            if identity.review is not None:
                fields["review"] = identity.review
        return cls.model_validate(fields)


__all__ = [
    "OpponentVarietySchema",
    "RecordLikelyRangeSchema",
    "PlayerRecordResponse",
    "SkillPanelSchema",
    "SportPillSchema",
]
