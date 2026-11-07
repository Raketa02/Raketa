"""The ranking on the wire (#768; ``docs/adr/0203``; the screens §4–§5).

**Every Level is the two-decimal number the passport prints**, and the client
draws it with the decimal comma. Places are true places: a row the reader
can't see leaves a gap, and `of` still counts it.
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
    CardState,
    Outcome,
    PlaceCard,
    level_of,
)


class RankingView(StrEnum):
    """Which list the page reads. **General** is everybody in Raketa listed in
    the sport; **Friends** arrives with #771."""

    GENERAL = "GENERAL"


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

    @classmethod
    def of_card(cls, card: PlaceCard) -> "PlaceCardSchema":
        return cls(
            state=card.state,
            results=card.results,
            results_to_enter=GENERAL_ENTRY,
            place=card.place,
            of=card.of,
            level=None if card.hundredths is None else level_of(card.hundredths),
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
