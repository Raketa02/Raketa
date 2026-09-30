"""The player surface's shapes for proposals (#538).

**Money crosses as integer grosze**, as every price on this platform does, and
the client renders it (``docs/value-formatting.md``). **No other person crosses
here**: a yes answers only the seats still open, and the live-yeses list is the
reader's own — who else is In is the card's to draw (#539).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.live_yeses import LiveYeses, NamedLiveYes


class YesAnswerResponse(BaseModel):
    """What a yes left on the game."""

    proposal_id: UUID
    open_seats: int = Field(
        description=(
            "Seats nobody is In on yet, this player's yes counted. Nought is a "
            "game every seat said yes to."
        )
    )

    @classmethod
    def from_answer(cls, answer: YesAnswer) -> "YesAnswerResponse":
        return cls(proposal_id=answer.proposal_id, open_seats=answer.open_seats)


class LiveYesClubSchema(BaseModel):
    id: UUID
    name: str | None = Field(
        description="The club's name; `null` for a club that no longer exists."
    )


class LiveYesSchema(BaseModel):
    """One yes on a game that has not filled."""

    proposal_id: UUID
    pool_id: UUID = Field(description="The pool the game was dealt in — a group's id.")
    sport: Sport
    kind: SearchMode = Field(description="Competitive, or for fun (a friendly).")
    starts_at: datetime = Field(
        description="The court hour's start. Every game is one hour."
    )
    club: LiveYesClubSchema
    share_grosze: int = Field(
        description="What this player is charged if the game fills, in grosze."
    )
    book_by: datetime = Field(
        description="The latest moment the game can fill; past it the yes lapses."
    )

    @classmethod
    def from_named(cls, named: NamedLiveYes) -> "LiveYesSchema":
        yes = named.yes
        return cls(
            proposal_id=yes.proposal_id,
            pool_id=yes.pool_id,
            sport=yes.sport,
            kind=yes.kind,
            starts_at=yes.start,
            club=LiveYesClubSchema(id=yes.club_id, name=named.club_name),
            share_grosze=yes.share_grosze,
            book_by=yes.book_by,
        )


class LiveYesesResponse(BaseModel):
    """You › Payments' **LIVE YESES**: every yes of the reader's on a game that
    has not filled, across groups, soonest game first."""

    yeses: list[LiveYesSchema]
    cap_per_sport: int = Field(
        description="How many live yeses a player may have in one sport."
    )

    @classmethod
    def from_live(cls, live: LiveYeses) -> "LiveYesesResponse":
        return cls(
            yeses=[LiveYesSchema.from_named(named) for named in live.yeses],
            cap_per_sport=live.cap_per_sport,
        )
