from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class InviteAdministratorCommand:
    """The club names a person: a name and an email, as the desk typed them.
    Plain strings — the value objects refuse inside the handler, under the
    field each is about."""

    club_id: UUID
    name: str
    email: str


@dataclass(frozen=True)
class ClaimInvitationCommand:
    email: str
    code: str


@dataclass(frozen=True)
class SetInvitationPasswordCommand:
    """Exactly one of ``token`` and ``ticket``: the email's link, or a
    claimed code."""

    password: str
    token: Optional[str] = None
    ticket: Optional[str] = None
