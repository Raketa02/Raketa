"""The shapes of administrators and invitations, on both surfaces.

**The club's requests declare types and nothing else**, as every club form's do
(``clubs/presentation/schemas.py``): a bound here would refuse first, as a
``422`` naming no field, where the desk needs the refusal under the field.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.administrators.application.administratorship import (
    AdministratorProfile,
)
from app.modules.administrators.application.invitations import OpenedInvitation
from app.modules.administrators.application.profiles import AccountProfiles
from app.modules.administrators.application.views import AdministratorRow
from app.modules.administrators.domain.administrator import AdministratorStanding

# --------------------------------------------------------------------------- #
# The club surface
# --------------------------------------------------------------------------- #


class InviteAdministratorRequest(BaseModel):
    """*+ Add administrator*: a name and an email, and nothing else — the club
    never sets, sees or handles a password or a code."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "Trimmed, runs of whitespace collapsed, then 2–64 characters — "
            "`administrator_name_invalid` otherwise. It becomes the person's "
            "Name if they are new to Raketa."
        )
    )
    email: str = Field(
        description=(
            "Malformed is `email_invalid`. Already invited here — expired "
            "included — is `409 administrator_already_invited`; already active "
            "here is `409 administrator_already_active`."
        )
    )


class AdministratorStatus(StrEnum):
    """What the Administrators table says of somebody, now."""

    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    EXPIRED = "EXPIRED"


class AdministratorGroupSchema(BaseModel):
    id: UUID
    name: str


class AdministratorSchema(BaseModel):
    """One row of the club's Administrators table (``docs/adr/0184`` §1).
    **Every status is derived**, and so is whether *Reset password* is drawn."""

    id: UUID
    name: str = Field(description="As the club typed it: trimmed and collapsed.")
    email: str
    status: AdministratorStatus = Field(
        description=(
            "`ACTIVE` once the invitation was taken up; `INVITED` until then; "
            "`EXPIRED` once its 72 hours have passed unanswered — resendable."
        )
    )
    last_used_at: Optional[datetime] = Field(
        description=(
            "On an `ACTIVE` row: when the administrator profile was last used, "
            "**to the hour** — *today*, *this week*. `null` otherwise."
        )
    )
    expires_at: Optional[datetime] = Field(
        description=(
            "On an `INVITED` row, when it expires; on an `EXPIRED` row, when it "
            "did. `null` on an `ACTIVE` row."
        )
    )
    groups: list[AdministratorGroupSchema] = Field(
        description=(
            "The official groups this administrator runs. Empty until official "
            "groups exist."
        )
    )
    can_reset_password: bool = Field(
        description=(
            "Whether *Reset password* may be pressed: only for an account that "
            "holds nothing but administrator profiles. Pressing it anyway is "
            "`409 administrator_also_plays` or `administrator_has_no_account`."
        )
    )

    @classmethod
    def from_row(cls, row: AdministratorRow) -> "AdministratorSchema":
        if row.standing is AdministratorStanding.REMOVED:
            raise RuntimeError("a removed administrator is on no club's table")
        return cls(
            id=row.id,
            name=row.name,
            email=row.email,
            status=AdministratorStatus(row.standing.value),
            last_used_at=row.last_used_at,
            expires_at=row.expires_at,
            groups=[
                AdministratorGroupSchema(id=group.id, name=group.name)
                for group in row.groups
            ],
            can_reset_password=row.can_reset_password,
        )


class AdministratorListResponse(BaseModel):
    administrators: list[AdministratorSchema] = Field(
        description="Everybody not removed, by name."
    )


# --------------------------------------------------------------------------- #
# The player surface
# --------------------------------------------------------------------------- #


class ClaimInvitationRequest(BaseModel):
    """*Have an invitation code?*: the address and the 8-character code. The
    code is read forgivingly — case, spaces and dashes are ignored — and its
    length is not checked here: a code of the wrong length is simply not the
    right code."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1, max_length=320)
    code: str = Field(min_length=1, max_length=64)


class InvitationPasswordRequest(BaseModel):
    """*Set your password*, and **exactly one** of what opens the way to it:
    the `token` from the email's link, or the `ticket` a claimed code returned.

    The password carries no bound here: the rule every account shares — 8 to
    128 characters with a letter and a digit — is refused as
    `password_too_weak` naming the field. Sending both or neither of `token`
    and `ticket` is the one refusal here that is a `422`.
    """

    model_config = ConfigDict(extra="forbid")

    token: Optional[str] = Field(default=None, min_length=1, max_length=256)
    ticket: Optional[str] = Field(default=None, min_length=1, max_length=256)
    password: str

    @model_validator(mode="after")
    def _exactly_one_way_in(self) -> "InvitationPasswordRequest":
        if (self.token is None) == (self.ticket is None):
            raise ValueError("send exactly one of token and ticket")
        return self


class InvitationByTokenRequest(BaseModel):
    """The token off an invitation's link. In a body rather than a path, so it
    is in no access log."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1, max_length=256)


class InvitationLinkState(StrEnum):
    """Whether an invitation's link still works — the credential's standing,
    under a name of its own on the wire (``Standing`` is a challenge's)."""

    VALID = "valid"
    EXPIRED = "expired"
    USED = "used"
    LOCKED = "locked"


class InvitationByTokenResponse(BaseModel):
    """What a link opens, before anything is set: the email *Set your
    password* locks its field to, whom it greets, and whether it still
    works."""

    email: str
    name: str = Field(description="The name the club typed.")
    club_name: str
    state: InvitationLinkState = Field(
        description=(
            "`valid`, `expired` (ask the club to send a new one), `used`, or "
            "`locked` — five wrong codes."
        )
    )

    @classmethod
    def from_opened(cls, opened: OpenedInvitation) -> "InvitationByTokenResponse":
        return cls(
            email=opened.email,
            name=opened.name,
            club_name=opened.club_name,
            state=InvitationLinkState(opened.standing.value),
        )


class AdministeredClubSchema(BaseModel):
    club_id: UUID
    club_name: str


class PendingInvitationSchema(BaseModel):
    administrator_id: UUID = Field(
        description="What `POST /invitations/{administrator_id}/acceptance` takes."
    )
    club_id: UUID
    club_name: str
    expires_at: datetime


class AccountProfilesSchema(BaseModel):
    """Which profiles this account holds (``docs/adr/0185`` §2) — what the
    entry gate reads first. *Profile* is the switcher's word."""

    acts_as_player: bool = Field(
        description=(
            "Whether this account acts as a player: it has given the Adult "
            "attestation — every sign-up did, and *Start playing* asks it first "
            "— or it holds a Player profile. `false` only for an account an "
            "invitation opened that has not started playing."
        )
    )
    administers: list[AdministeredClubSchema] = Field(
        description="One entry per club whose groups this account runs, by name."
    )
    pending_invitations: list[PendingInvitationSchema] = Field(
        description=(
            "Invitations addressed to this account's email that are still open, "
            "soonest to expire first. One disappears once accepted, removed or "
            "past its 72 hours."
        )
    )

    @classmethod
    def from_profiles(cls, profiles: AccountProfiles) -> "AccountProfilesSchema":
        return cls(
            acts_as_player=profiles.acts_as_player,
            administers=[
                AdministeredClubSchema(club_id=club.club_id, club_name=club.club_name)
                for club in profiles.administers
            ],
            pending_invitations=[
                PendingInvitationSchema(
                    administrator_id=invitation.administrator_id,
                    club_id=invitation.club_id,
                    club_name=invitation.club_name,
                    expires_at=invitation.expires_at,
                )
                for invitation in profiles.pending_invitations
            ],
        )


class AdministratorProfileResponse(BaseModel):
    """*My administrator profile at club X* — the guarded read."""

    club_id: UUID
    club_name: str

    @classmethod
    def from_profile(
        cls, profile: AdministratorProfile
    ) -> "AdministratorProfileResponse":
        return cls(club_id=profile.club_id, club_name=profile.club_name)
