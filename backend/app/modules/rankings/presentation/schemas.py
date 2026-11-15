"""The ranking on the wire (#768, #769, #770, #771; ``docs/adr/0203``; the
screens §4–§5).

**Every Level is the two-decimal number the passport prints**, and so is every
gap; the client draws both with the decimal comma. **Everybody is on every
list at their true place** (``docs/adr/0204`` §2): no switch and no block hides
a row, and `of` counts everyone. **The backend
counts the wins and the client draws them**: the count reads the rating
engine's update rule, which nobody else may compute.

**A cursor is opaque**: the key a row stood at in the order, written here and
read back only here (``cursor_of``, ``key_of``) — a client hands back what it
was given and never builds one.
"""

from __future__ import annotations

import base64
import binascii
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport
from app.modules.rankings.application.reads import (
    GeneralPage,
    RankedRow,
    Ranking,
    TopTen,
)
from app.modules.rankings.domain.errors import NotAPage
from app.modules.rankings.domain.general_order import (
    OrderKey,
    instant_of_micros,
    micros_of,
)
from app.modules.rankings.domain.ranking import (
    FORM_LENGTH,
    WINS_COUNTED,
    CardState,
    Chip,
    ChipKind,
    GapLine,
    Outcome,
    PlaceCard,
    PlayerAbove,
    PlayerBelow,
    RankingView,
    level_of,
)
from app.modules.rankings.domain.top_ten import TOP_TEN, drawn_chip


def cursor_of(key: OrderKey) -> str:
    """A row's key as a cursor: its four keys, dot-separated, base64url."""

    written = (
        f"{key.hundredths}.{key.results}.{micros_of(key.level_reached_at)}."
        f"{key.player_id.hex}"
    )
    return base64.urlsafe_b64encode(written.encode()).decode().rstrip("=")


def key_of(cursor: str) -> OrderKey:
    """The key a cursor names — :class:`NotAPage` for one this server never
    wrote: unreadable, or naming a key no kept order could hold."""

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        hundredths, results, micros, player = (
            base64.urlsafe_b64decode(padded.encode()).decode().split(".")
        )
        key = OrderKey(
            hundredths=int(hundredths),
            results=int(results),
            level_reached_at=instant_of_micros(int(micros)),
            player_id=UUID(hex=player),
        )
    except (ValueError, OverflowError, UnicodeDecodeError, binascii.Error) as error:
        raise NotAPage("an unreadable cursor") from error
    if not key.can_be_written():
        raise NotAPage("a cursor no row stands at")
    return key


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
        description=(
            "The part before the dot; `null` at the top of the list, and when "
            "nobody above you is a row you can see — then only `below` reads."
        )
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
            "`NEEDS_RESULTS` — fewer results in the sport than the view takes: in "
            "General *2 of 5 games — 3 more competitive padel games put you on "
            "the list*; in Friends, with none, *Not ranked in padel yet — your "
            "first confirmed competitive game puts you on the list*. `NO_LEVEL` — "
            "no level in the sport, read live: *No squash level yet — get one, "
            "then 5 competitive games put you on the list* (in Friends *… then "
            "one competitive game …*), with **Get your squash level**. "
            "`OFF_THE_LIST` — no result in the last 90 days: *Off the list — no "
            "competitive padel game in 90 days. Your next one puts you back.* "
            "**Friends only**: `JUST_YOU` — you are listed and no friend is: *Just "
            "you so far*, with **Add friends**; `NO_FRIEND_LISTED` — neither you "
            "nor any friend is: *None of your friends is ranked in padel yet*, "
            "with **Add friends**, whatever your own state. With either, the card "
            "is the whole page: nothing is drawn below it. In Friends, "
            "`NEEDS_RESULTS`, `NO_LEVEL` and `OFF_THE_LIST` stand above your "
            "friends' podium and table."
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
            "How many results put a player on the view's list — the *5* of *2 "
            "of 5 games* in General, `1` in Friends."
        )
    )
    place: int | None = Field(
        ge=1, description="With `LISTED` only: your place — *7th*."
    )
    of: int | None = Field(
        ge=1,
        description=(
            "With `LISTED` only: how many are listed — *of 13* — everyone, "
            "whoever blocked whom."
        ),
    )
    level: float | None = Field(
        description=("With `LISTED` only: your Level, two decimals — *2,71*.")
    )
    chip: ChipSchema | None = Field(
        description=(
            "With `LISTED` only: your places moved this week, under the Level."
        )
    )
    gap_line: GapLineSchema | None = Field(
        description=(
            "With `LISTED` only: the line under the fold — the true neighbours "
            "above and below you, whoever they are."
        )
    )

    @classmethod
    def of_card(cls, card: PlaceCard, *, view: RankingView) -> "PlaceCardSchema":
        return cls(
            state=card.state,
            results=card.results,
            results_to_enter=view.entry,
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
            "Their true place — coral for 1–3, grey after. A blocked player is "
            "here too; a tap on them reads *This record isn't available*."
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
            "How many are listed in the view and sport, you included. `0` in "
            "General reads *Nobody ranked in badminton yet* where the podium "
            "and list would be."
        ),
    )
    podium: list[RankedRowSchema] = Field(
        description=(
            "The first three rows, each with its true place — first in the "
            "middle, second left, third right. **Empty with fewer than three "
            "listed**, and the list shows alone."
        )
    )
    rows: list[RankedRowSchema] = Field(
        description=(
            "**General**: the first page of 50, best first — a listed player "
            "has at least 5 confirmed competitive results with a winner in the "
            "sport, the last within 90 days. **Friends**: the whole table, "
            "never paged — you and your friends with at least 1 such result, "
            "the last within 90 days, places, chips and the gap line counted "
            "among you alone; empty with `JUST_YOU` and `NO_FRIEND_LISTED`. "
            "Ordered by Level, then more results, then who reached that Level "
            "first."
        )
    )
    next: str | None = Field(
        description=(
            "The cursor the next page is read **after** — "
            "`GET /rankings/{sport}/general/rows?after=…`. `null` when the "
            "first page is the whole list, and always in Friends. Opaque: hand "
            "it back as it came."
        )
    )

    @classmethod
    def of_ranking(cls, ranking: Ranking) -> "RankingResponse":
        return cls(
            sport=ranking.sport,
            view=ranking.view,
            card=PlaceCardSchema.of_card(ranking.card, view=ranking.view),
            listed=ranking.listed_count,
            podium=[RankedRowSchema.of_row(row) for row in ranking.podium],
            rows=[RankedRowSchema.of_row(row) for row in ranking.rows],
            next=None if ranking.next is None else cursor_of(ranking.next),
        )


class TopTenChipSchema(BaseModel):
    """**The week's move on a Top 10 card**, drawn — a triangle and a bold
    italic number, *▲ 2* in volt, *▼ 1* in coral. The Rankings page's chip for
    the same row; a card draws none for no change or *New*."""

    kind: Literal[ChipKind.UP, ChipKind.DOWN] = Field(
        description="`UP` — *▲ 2*. `DOWN` — *▼ 1*."
    )
    places: int = Field(ge=1, description="How many places — the *2* of *▲ 2*.")


class TopTenPlayerSchema(BaseModel):
    """One Top 10 card: the numeral, the portrait, the nickname, the Level and
    the week's move. **A tap opens their record**; across a block it reads
    *This record isn't available*."""

    place: int = Field(
        ge=1,
        le=TOP_TEN,
        description="Their true place in General — the huge numeral, 1 to 10.",
    )
    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None
    photo_url: str | None = Field(
        description=(
            "A short-lived link to their first photograph; `null` with "
            "`photo_id` draws the court picture."
        )
    )
    level: float = Field(description="Their Level, two decimals — *3,40*.")
    chip: TopTenChipSchema | None = Field(
        description=(
            "Their places moved this week, rolling — as the Rankings page's row "
            "reads them. `null` for no change and for *New*: no chip is drawn."
        )
    )
    is_you: bool = Field(
        description=(
            "Your own card — it reads *You*, its numeral volt and the card "
            "ringed in volt."
        )
    )

    @classmethod
    def of_row(cls, row: RankedRow) -> "TopTenPlayerSchema":
        chip = drawn_chip(row.chip)
        return cls(
            place=row.place,
            player_id=row.player_id,
            nickname=row.nickname,
            photo_id=row.photo_id,
            photo_url=row.photo_url,
            level=level_of(row.hundredths),
            chip=(
                None
                if chip is None
                else TopTenChipSchema(
                    kind=ChipKind.UP if chip.kind is ChipKind.UP else ChipKind.DOWN,
                    places=chip.places,
                )
            ),
            is_you=row.is_you,
        )


class TopTenResponse(BaseModel):
    """**Top 10 on Home**: places 1 to 10 of General in one sport, the true
    top of the Rankings page — everybody at their true place, whoever blocked
    whom."""

    sport: Sport = Field(
        description=(
            "The sport the row shows: the one asked for, or the one a "
            "preference fell through to — the pill's chosen sport, and the one "
            "*Rankings ›* opens on."
        )
    )
    anyone_listed: bool = Field(
        description=(
            "Whether anybody is listed in General **in any sport**. While "
            "nobody is, the row is hidden."
        )
    )
    players: list[TopTenPlayerSchema] = Field(
        max_length=TOP_TEN,
        description=(
            "Places 1 to 10 of General in `sport`, best first — fewer while "
            "fewer are listed, one or two included. **Empty while nobody is "
            "ranked in `sport`**: *Nobody ranked in squash yet*."
        ),
    )

    @classmethod
    def of_top_ten(cls, top: TopTen) -> "TopTenResponse":
        return cls(
            sport=top.sport,
            anyone_listed=top.anyone_listed,
            players=[TopTenPlayerSchema.of_row(row) for row in top.rows],
        )


class GeneralPageResponse(BaseModel):
    """**A page of General**: 50 places of the list, the rows of them you see
    and the cursors either side. Scrolling to either end reads the next page
    that way."""

    sport: Sport
    listed: int = Field(
        ge=0,
        description="How many are listed in General in the sport — *of 480*.",
    )
    rows: list[RankedRowSchema] = Field(
        description=(
            "The page's rows, best first, each with its true place — the same "
            "rows the main read draws, 50 places."
        )
    )
    previous: str | None = Field(
        description=(
            "The cursor the page above is read **before** — `?before=…`. "
            "`null` at the top of the list."
        )
    )
    next: str | None = Field(
        description=(
            "The cursor the page below is read **after** — `?after=…`. `null` "
            "at the bottom of the list."
        )
    )

    @classmethod
    def of_page(cls, page: GeneralPage) -> "GeneralPageResponse":
        return cls(
            sport=page.sport,
            listed=page.listed_count,
            rows=[RankedRowSchema.of_row(row) for row in page.rows],
            previous=None if page.previous is None else cursor_of(page.previous),
            next=None if page.next is None else cursor_of(page.next),
        )
