from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)

from app.modules.administrators.presentation.schemas import AccountProfilesSchema
from app.modules.users.application.read_own_account import OwnAccount
from app.modules.users.domain.user import User


class UserCreateRequest(BaseModel):
    """Sign-up: credentials and the attestation, and nothing about who you are.

    The nickname is not in this payload (``docs/adr/0199`` §3) — it is asked in
    onboarding, with :class:`NameRequest`. **Extra fields are
    refused** rather than ignored, so a client still sending one meets the
    validation envelope instead of a sign-up that quietly dropped what it said.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password1: str = Field(..., min_length=8, max_length=128)
    password2: str = Field(..., min_length=8, max_length=128)
    adult_attested: bool = Field(
        ...,
        description=(
            "The player's own claim that they are an adult. Required, and "
            "required to be `true`: the platform is adults only and that is a "
            "precondition of holding an account. `false` is refused with "
            "`adult_attestation_required`, and the client writes the sentence. "
            "**Not a date of birth and not age verification** — this records "
            "that the question was asked and answered, and nothing more."
        ),
    )

    @field_validator("password2")
    @classmethod
    def _passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if "password1" in info.data and v != info.data["password1"]:
            raise ValueError("passwords do not match")
        return v


class NameRequest(BaseModel):
    """The naming — *How should people see you?* (``docs/adr/0199`` §3).

    **A nickname and nothing else.** The shape rule here is the value object's
    own, restated so the generated client type carries it. A body still
    carrying a ``name`` — or anything else — is refused with the validation
    envelope rather than quietly dropped, so a client that kept the field
    cannot believe it was recorded.
    """

    model_config = ConfigDict(extra="forbid")

    nickname: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description=(
            "A handle: letters, digits and `. _ -`, no spaces, 2–64 characters, "
            "**unique across the platform** — refused with "
            "`nickname_already_taken` when another player holds it, admitted "
            "when it is already yours. **What every screen says about you**, "
            "never with an @."
        ),
    )


class NamingResponse(BaseModel):
    """What the naming recorded: the nickname as it now stands.

    Not a ``UserResponse``, deliberately — that shape carries
    ``has_player_profile``, a fact of another context's this write never asks
    about, and ``false`` there would be a claim. The client re-reads ``/me``
    before moving on; this is what lets it show the nickname back at once.
    """

    nickname: str = Field(..., description="The handle, as recorded.")


class UserResponse(BaseModel):
    """The account, plus the one fact about it onboarding's entry gate needs.

    ``has_player_profile`` is not a property of a ``User`` and the domain layer
    has no idea it exists — it is answered by the Player profile context and
    joined here, on the response, because the gate reads it on every cold launch
    and a second round trip for one boolean would be a second thing to fail
    (``docs/adr/0090``).

    ``nickname`` is **null until the naming**, an account an Invitation opened
    included, and this is the one read where it may be null
    (``docs/adr/0199`` §3): a player on any surface that names another player
    has necessarily picked one, because the gate holds an account with none at
    the naming step. **There is no ``name``**: no account holds a player name.
    On ``/me`` the nickname is read from the player's own stream, as
    ``has_player_profile`` is, so it is right the instant after the commit the
    gate reads it after.

    **It is not an "onboarded" flag.** The rating context's invariant against one
    stands: whether a player has been through onboarding *for a sport* is asked
    by asking whether a rating exists for that sport, and this field cannot
    answer it. This asks a genuinely per-player question, because a profile is
    one per player and has no sport dimension at all.
    """

    id: UUID
    email: EmailStr
    nickname: Optional[str] = Field(
        default=None,
        description=(
            "The handle, unique across the platform, and what every screen says "
            "about this player — never with an @. `null` until the naming, an "
            "account an invitation opened included: the entry gate's first "
            "destination is **no nickname**."
        ),
    )
    authority: str
    is_admin: bool
    is_active: bool
    created_at: Optional[datetime] = None
    has_player_profile: bool = Field(
        default=False,
        description=(
            "Whether this player has committed a Player profile — the fourth "
            "branch of the entry gate. Read from the profile's own event stream "
            "rather than from a projection, so it is correct immediately after "
            "the commit that creates one. False on a response that is not about "
            "the authenticated player, such as the one registration returns."
        ),
    )

    @classmethod
    def from_domain(
        cls,
        user: User,
        *,
        has_player_profile: bool = False,
        own: OwnAccount | None = None,
    ) -> "UserResponse":
        """``own`` is the stream's answer, and the only source of the nickname:
        ``/me`` passes what :class:`ReadOwnAccount` folded, and the
        registration passes nothing because a fresh account has none. There is
        deliberately no fallback to the aggregate's own ``nickname`` — the row
        it was loaded from is a projection, and the gate's field is read from
        the stream and never from one."""

        return cls(
            id=user.id,
            email=user.email.value,
            nickname=None if own is None else own.nickname,
            authority=user.authority.value,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            has_player_profile=has_player_profile,
        )


class MeResponse(UserResponse):
    """``/me``: the account, and **which profiles it holds**
    (``docs/adr/0185`` §2) — what the entry gate reads ahead of every
    onboarding destination.

    Its own shape rather than more fields on :class:`UserResponse`, because the
    registration's answer is about an account one line old and has no honest
    value for either: it holds no profile yet, and ``/me`` is where the gate
    reads them.
    """

    adult_attested: bool = Field(
        ...,
        description=(
            "Whether this account has given the Adult attestation. Every "
            "sign-up has; an account an invitation opened has not, and *Start "
            "playing* asks it first — `POST /users/me/adult-attestation`."
        ),
    )
    profiles: AccountProfilesSchema

    @classmethod
    def from_parts(
        cls,
        user: User,
        *,
        has_player_profile: bool,
        own: OwnAccount,
        profiles: AccountProfilesSchema,
    ) -> "MeResponse":
        base = UserResponse.from_domain(
            user, has_player_profile=has_player_profile, own=own
        )
        return cls(
            **base.model_dump(),
            adult_attested=own.adult_attested,
            profiles=profiles,
        )


class AdultAttestationRequest(BaseModel):
    """The Adult attestation, given by an account that already exists — what
    *Start playing* asks first (``docs/adr/0185`` §5)."""

    model_config = ConfigDict(extra="forbid")

    adult_attested: bool = Field(
        ...,
        description=(
            "Required to be `true`, exactly as at sign-up: `false` is refused "
            "with `adult_attestation_required`. **Not a date of birth and not "
            "age verification.**"
        ),
    )
