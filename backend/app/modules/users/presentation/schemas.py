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

from app.modules.users.domain.ports import Naming
from app.modules.users.domain.user import User


class UserCreateRequest(BaseModel):
    """Sign-up: credentials and the attestation, and nothing about who you are.

    The nickname left this payload with ``docs/adr/0171`` §2 — it is asked in
    onboarding, beside the name, with :class:`NameRequest`. **Extra fields are
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
    """The naming — *How should people see you?* (``docs/adr/0171`` §1–2).

    Both fields, always: the naming is one act carrying both, and there is no
    event for one without the other. The shape rules here are the value
    objects' own, restated so the generated client type carries them; the trim
    and the collapse happen in the domain, so ``"  Ania   Kowalska "`` is
    admitted and recorded as ``Ania Kowalska``.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description=(
            "What you are called — free text, spaces allowed, **never unique**: "
            "two players may share one. Trimmed, runs of whitespace collapsed to "
            "one space, 2–64 characters after that. This is what every screen "
            "says about you."
        ),
    )
    nickname: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description=(
            "A handle: letters, digits and `. _ -`, no spaces, 2–64 characters, "
            "**unique across the platform** — refused with "
            "`nickname_already_taken` when another player holds it, admitted "
            "when it is already yours. Shown as `@nickname` under your name on "
            "your own You tab and on your record, and said nowhere else."
        ),
    )


class NamingResponse(BaseModel):
    """What the naming recorded: the name as it now stands and the nickname.

    Not a ``UserResponse``, deliberately — that shape carries
    ``has_player_profile``, a fact of another context's this write never asks
    about, and ``false`` there would be a claim. The client re-reads ``/me``
    before moving on (``docs/adr/0171`` §3); this is what lets it show the
    normalised name back at once.
    """

    name: str = Field(..., description="The name as recorded: trimmed, collapsed.")
    nickname: str = Field(..., description="The handle, as recorded.")


class UserResponse(BaseModel):
    """The account, plus the one fact about it onboarding's entry gate needs.

    ``has_player_profile`` is not a property of a ``User`` and the domain layer
    has no idea it exists — it is answered by the Player profile context and
    joined here, on the response, because the gate reads it on every cold launch
    and a second round trip for one boolean would be a second thing to fail
    (``docs/adr/0090``).

    ``name`` and ``nickname`` are **null until the naming**, and this is the one
    read where either may be null (``docs/adr/0171`` §2): a player on any
    surface that names another player has necessarily been named, because the
    gate holds an unnamed account at the naming step. On ``/me`` they are read
    from the player's own stream, as ``has_player_profile`` is, so they are
    right the instant after the commit the gate reads them after.

    **It is not an "onboarded" flag.** The rating context's invariant against one
    stands: whether a player has been through onboarding *for a sport* is asked
    by asking whether a rating exists for that sport, and this field cannot
    answer it. This asks a genuinely per-player question, because a profile is
    one per player and has no sport dimension at all.
    """

    id: UUID
    email: EmailStr
    name: Optional[str] = Field(
        default=None,
        description=(
            "What this player is called — what every screen says. `null` until "
            "the naming, and **the entry gate's first destination**: a player "
            "with no name is sent to the naming step before anything else."
        ),
    )
    nickname: Optional[str] = Field(
        default=None,
        description=(
            "The handle, unique across the platform, drawn as `@nickname` under "
            "the name on the You tab and nowhere else. `null` until the naming."
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
        naming: Naming | None = None,
    ) -> "UserResponse":
        """``naming`` is the stream's answer where the route has one (``/me``);
        elsewhere the response reads the aggregate it was handed, and a fresh
        registration is unnamed."""

        if naming is None and user.name is not None and user.nickname is not None:
            naming = Naming(name=user.name.value, nickname=user.nickname.value)
        return cls(
            id=user.id,
            email=user.email.value,
            name=None if naming is None else naming.name,
            nickname=None if naming is None else naming.nickname,
            authority=user.authority.value,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            has_player_profile=has_player_profile,
        )
