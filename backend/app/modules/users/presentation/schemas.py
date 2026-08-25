from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from app.modules.users.domain.user import User


class UserCreateRequest(BaseModel):
    email: EmailStr
    password1: str = Field(..., min_length=8, max_length=128)
    password2: str = Field(..., min_length=8, max_length=128)
    nickname: str = Field(
        ..., min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$"
    )

    @field_validator("password2")
    @classmethod
    def _passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if "password1" in info.data and v != info.data["password1"]:
            raise ValueError("passwords do not match")
        return v


class UserResponse(BaseModel):
    """The account, plus the one fact about it onboarding's entry gate needs.

    ``has_player_profile`` is not a property of a ``User`` and the domain layer
    has no idea it exists — it is answered by the Player profile context and
    joined here, on the response, because the gate reads it on every cold launch
    and a second round trip for one boolean would be a second thing to fail
    (``docs/adr/0090``).

    **It is not an "onboarded" flag.** The rating context's invariant against one
    stands: whether a player has been through onboarding *for a sport* is asked
    by asking whether a rating exists for that sport, and this field cannot
    answer it. This asks a genuinely per-player question, because a profile is
    one per player and has no sport dimension at all.
    """

    id: UUID
    email: EmailStr
    nickname: str
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
        cls, user: User, *, has_player_profile: bool = False
    ) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email.value,
            nickname=user.nickname.value,
            authority=user.authority.value,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            has_player_profile=has_player_profile,
        )
