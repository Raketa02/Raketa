"""The ranking on the wire (#768, #769; ``docs/adr/0203``; the screens §4–§5).

**Every Level is the two-decimal number the passport prints**, and so is every
gap; the client draws both with the decimal comma. Places are true places: a
row the reader can't see leaves a gap, and `of` still counts it. **The backend
counts the wins and the client draws them**: the count reads the rating
engine's update rule, which nobody else may compute.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport
from app.modules.rankings.application.reads import RankedRow, Ranking
from app.modules.rankings.domain.ranking import (
    FORM_LENGTH,
    GENERAL_ENTRY,
    WINS_COUNTED,
    CardState,
    Chip,
    ChipKind,
    GapLine,
    Outcome,
    PlaceCard,
    PlayerAbove,
    PlayerBelow,
    level_of,
)


class RankingView(StrEnum):
    """Which list the page reads. **General** is everybody in Raketa listed in
    the sport; **Friends** arrives with #771."""

    GENERAL = "GENERAL"


class ChipSchema(BaseModel):
    """**The places moved in the last 7 days**, rolling: the place now against
    where today's same players stood by their Levels exactly 7 days earlier.
    An arrival or a departure moves nobody; an overtake moves both."""

    kind: ChipKind = Field(
        description=(
            "`UP` — *▲ 2*, on the card *▲ 2 up this week*. `DOWN` — *▼ 1*, *▼ 1 "
            "down this week*. `SAME` — *—*, *— no change this week*. `NEW` — "
            "*New*, *New this week*: the 7 days after the 5th result first put "
            "the player on General. A comeback after 90 days is never `NEW`."
        )
    )
    places: int | None = Field(
        ge=1,
        description="With `UP` and `DOWN` only: how many places — the *2* of *▲ 2*.",
    )

    @classmethod
    def of_chip(cls, chip: Chip) -> "ChipSchema":
        return cls(kind=chip.kind, places=chip.places or None)


class PlayerAboveSchema(BaseModel):
    """The nearest player above you that you can see."""

    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    gap: float = Field(
        ge=0,
        description=(
            "How far behind them you are, two decimals — the bold *0,04* of "
            "*0,04 behind Karol*. `0` with `tied`."
        ),
    )
    wins: int | None = Field(
        ge=1,
        le=WINS_COUNTED,
        description=(
            "How many even wins close the gap, each moving your Level as the "
            "rating engine's own rule moves it in a game at your own Level: `1` "
            "reads *one win closes it*, `2`–`5` *about 3 wins close it*. `null` "
            "when more than five would — the count is left out, *0,31 behind "
            "Karol* — when an even win is too small to move your Level at all, "
            "and when `tied`."
        ),
    )
    tied: bool = Field(
        description=(
            "You are level with them, and they are above you on the tie rule: "
            "*Level with Ewa · one win puts you ahead*."
        )
    )

    @classmethod
    def of_above(cls, above: PlayerAbove) -> "PlayerAboveSchema":
        return cls(
            nickname=above.nickname,
            gap=level_of(above.gap),
            wins=above.wins,
            tied=above.tied,
        )


class PlayerBelowSchema(BaseModel):
    """The nearest player below you that you can see."""

    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    gap: float = Field(
        ge=0,
        description=(
            "How far behind you they are, two decimals: *Zofia is 0,02 behind "
            "you*. `0` reads *Zofia is level with you*."
        ),
    )

    @classmethod
    def of_below(cls, below: PlayerBelow) -> "PlayerBelowSchema":
        return cls(nickname=below.nickname, gap=level_of(below.gap))


class GapLineSchema(BaseModel):
    """**The line under the place card**, which turns the place into a target:
    *0,04 behind Karol · about 3 wins close it · Zofia is 0,02 behind you*. It
    names only rows you can see."""

    above: PlayerAboveSchema | None = Field(
        description="The part before the dot; `null` at the top of the list."
    )
    below: PlayerBelowSchema | None = Field(
        description=(
            "The part after it; `null` in last place, where only `above` reads, "
            "and at the top of the list."
        )
    )
    top_of_the_list: bool = Field(
        description=(
            "First place: the whole line reads *Top of the list*, and neither "
            "`above` nor `below` is sent."
        )
    )

    @classmethod
    def of_line(cls, line: GapLine) -> "GapLineSchema":
        above, below = line.above, line.below
        return cls(
            above=None if above is None else PlayerAboveSchema.of_above(above),
            below=None if below is None else PlayerBelowSchema.of_below(below),
            top_of_the_list=line.top_of_the_list,
        )


class PlaceCardSchema(BaseModel):
    """**Your place card**, under the switch — or the card that replaces it
    when there is no place to show."""

    state: CardState = Field(
        description=(
            "`LISTED` — *YOUR PLACE · 7th · of 13* and your Level. "
            "`NEEDS_RESULTS` — fewer than 5 results in the sport: *2 of 5 games — "
            "3 more competitive padel games put you on the list*. `NO_LEVEL` — no "
            "level in the sport, read live: *No squash level yet — get one, then "
            "5 competitive games put you on the list*, with **Get your squash "
            "level**. `OFF_THE_LIST` — no result in the last 90 days: *Off the "
            "list — no competitive padel game in 90 days. Your next one puts you "
            "back.*"
        )
    )
    results: int = Field(
        ge=0,
        description=(
            "Your confirmed competitive results with a winner in the sport — "
            "*2 of 5 games*. `0` with `NO_LEVEL`."
        ),
    )
    results_to_enter: int = Field(
        description=(
            "How many results put a player on General — the *5* of *2 of 5 games*."
        )
    )
    place: int | None = Field(
        ge=1, description="With `LISTED` only: your place — *7th*."
    )
    of: int | None = Field(
        ge=1,
        description="With `LISTED` only: how many are listed — *of 13*.",
    )
    level: float | None = Field(
        description="With `LISTED` only: your Level, two decimals — *2,71*."
    )
    chip: ChipSchema | None = Field(
        description="With `LISTED` only: your places moved this week, under the Level."
    )
    gap_line: GapLineSchema | None = Field(
        description="With `LISTED` only: the line under the fold."
    )

    @classmethod
    def of_card(cls, card: PlaceCard) -> "PlaceCardSchema":
        return cls(
            state=card.state,
            results=card.results,
            results_to_enter=GENERAL_ENTRY,
            place=card.place,
            of=card.of,
            level=None if card.hundredths is None else level_of(card.hundredths),
            chip=None if card.chip is None else ChipSchema.of_chip(card.chip),
            gap_line=(
                None if card.gap_line is None else GapLineSchema.of_line(card.gap_line)
            ),
        )


class RankedRowSchema(BaseModel):
    """One listed player: place, face, form and Level. **A tap opens their
    record.**"""

    place: int = Field(
        ge=1,
        description=(
            "Their true place — coral for 1–3, grey after. A row you can't see "
            "leaves a gap, so places may skip a number."
        ),
    )
    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None
    photo_url: str | None = Field(
        description=(
            "A short-lived link to their first photograph; `null` with "
            "`photo_id` draws initials."
        )
    )
    form: list[Outcome] = Field(
        max_length=FORM_LENGTH,
        description=(
            "Their last results in this sport, **oldest first** — the record's "
            "*Last 5*. Fewer than five is a real answer and is never padded."
        ),
    )
    chip: ChipSchema = Field(
        description="Their places moved this week — no *this week* in a row."
    )
    level: float = Field(description="Their Level, two decimals, right-aligned.")
    is_you: bool = Field(description="Your own row — it reads **You** and is tinted.")

    @classmethod
    def of_row(cls, row: RankedRow) -> "RankedRowSchema":
        return cls(
            place=row.place,
            player_id=row.player_id,
            nickname=row.nickname,
            photo_id=row.photo_id,
            photo_url=row.photo_url,
            form=list(row.form),
            chip=ChipSchema.of_chip(row.chip),
            level=level_of(row.hundredths),
            is_you=row.is_you,
        )


class RankingResponse(BaseModel):
    """**Rankings**, for one sport and view: your card, the podium and the
    list, best first."""

    sport: Sport
    view: RankingView
    card: PlaceCardSchema
    listed: int = Field(
        ge=0,
        description=(
            "How many are listed in the view and sport. `0` reads *Nobody "
            "ranked in badminton yet* where the podium and list would be."
        ),
    )
    podium: list[RankedRowSchema] = Field(
        description=(
            "The first three rows you see, each with its true place — first in "
            "the middle, second left, third right. **Empty with fewer than "
            "three rows**, and the list shows alone."
        )
    )
    rows: list[RankedRowSchema] = Field(
        description=(
            "General's first page of 50, best first: a listed player has at "
            "least 5 confirmed competitive results with a winner in the sport, "
            "the last within 90 days. Ordered by Level, then more results, then "
            "who reached that Level first."
        )
    )

    @classmethod
    def of_ranking(cls, ranking: Ranking, *, view: RankingView) -> "RankingResponse":
        return cls(
            sport=ranking.sport,
            view=view,
            card=PlaceCardSchema.of_card(ranking.card),
            listed=ranking.listed_count,
            podium=[RankedRowSchema.of_row(row) for row in ranking.podium],
            rows=[RankedRowSchema.of_row(row) for row in ranking.rows],
        )
