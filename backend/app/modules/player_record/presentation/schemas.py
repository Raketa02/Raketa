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

from app.modules.player_record.domain.record import OnCourtVerdict, PlayerRecord

#: The default that spells **omitted** — the same sentinel the shortlist's schema
#: uses, spelled here rather than imported: this context declares its own
#: presentation vocabulary for the reason it declares its own ports, and the two
#: are one line each.
OMITTED: Any = None


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
        }
        if identity.photo_id is not None and record.photo_url is not None:
            fields["photo_id"] = identity.photo_id
            fields["photo_url"] = record.photo_url
            if identity.review is not None:
                fields["review"] = identity.review
        return cls.model_validate(fields)


__all__ = ["PlayerRecordResponse"]
