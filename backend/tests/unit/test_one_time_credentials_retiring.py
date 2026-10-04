"""A newer credential retires the older ones — **of every purpose it is told to**.

The club's reset of an administrator and their invitation open the same page for
the same person (``docs/adr/0186`` §3), so issuing either retires a live one of
the other: the newest email is the only one that opens anything. No HTTP flow
reaches the case on its own — every act that could leave an invitation live
beside a reset retires it first — so it is asserted here, at the mechanism,
against a store that keeps its rows in a list.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import count
from uuid import UUID, uuid4

from app.kernel import Instant, instant
from app.modules.auth.application.one_time_credentials import OneTimeCredentials
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.one_time_credential import (
    CredentialPurpose,
    OneTimeCredential,
    Standing,
)

NOW = instant(datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))
BOTH = frozenset({CredentialPurpose.INVITATION, CredentialPurpose.CLUB_RESET})


class ListStore:
    def __init__(self) -> None:
        self.rows: dict[UUID, OneTimeCredential] = {}

    async def add(self, credential):
        self.rows[credential.id] = replace(credential)

    async def save(self, credential):
        self.rows[credential.id] = replace(credential)

    async def by_token_hash(self, token_hash):
        found = [c for c in self.rows.values() if c.token_hash == token_hash]
        return replace(found[0]) if found else None

    async def by_ticket_hash(self, ticket_hash):
        found = [c for c in self.rows.values() if c.ticket_hash == ticket_hash]
        return replace(found[0]) if found else None

    async def issued_to(self, email, *, purposes, audience, since):
        return [
            replace(c)
            for c in self.rows.values()
            if c.email == email
            and c.purpose in purposes
            and c.audience is audience
            and c.issued_at > since
        ]

    async def live_for(self, subject_id, *, purposes, audience, now):
        return [
            replace(c)
            for c in self.rows.values()
            if c.subject_id == subject_id
            and c.purpose in purposes
            and c.audience is audience
            and c.used_at is None
            and c.expires_at > now
        ]


class CountingSecrets:
    def __init__(self) -> None:
        self._next = count()

    def mint(self) -> str:
        return f"secret-{next(self._next):04d}-" + "x" * 40


class PlainHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


async def issue(credentials, subject, purpose, *, at: Instant, retiring=None):
    prepared = credentials.prepare()
    await credentials.issue(
        prepared,
        purpose=purpose,
        audience=Audience.PLAYER_APP,
        subject_id=subject,
        email="marta@ogrody33.pl",
        now=at,
        retiring=retiring,
    )
    return prepared.token


async def standing_of(credentials, token: str, *, now: Instant) -> Standing:
    opened = await credentials.opened_by(
        token, purposes=BOTH, audience=Audience.PLAYER_APP
    )
    assert opened is not None
    return opened.standing(now=now)


async def test_a_reset_retires_a_live_invitation_it_is_told_to():
    credentials = OneTimeCredentials(
        store=ListStore(), secrets=CountingSecrets(), hasher=PlainHasher()
    )
    marta = uuid4()
    invitation = await issue(credentials, marta, CredentialPurpose.INVITATION, at=NOW)
    later = instant(NOW + timedelta(minutes=5))

    reset = await issue(
        credentials, marta, CredentialPurpose.CLUB_RESET, at=later, retiring=BOTH
    )

    assert await standing_of(credentials, invitation, now=later) is Standing.EXPIRED
    assert await standing_of(credentials, reset, now=later) is Standing.VALID


async def test_without_being_told_a_newer_credential_retires_only_its_own_kind():
    """*Forgot password?* and every caller before this one pass nothing, and
    retire only their own purpose, as they always did."""

    credentials = OneTimeCredentials(
        store=ListStore(), secrets=CountingSecrets(), hasher=PlainHasher()
    )
    marta = uuid4()
    invitation = await issue(credentials, marta, CredentialPurpose.INVITATION, at=NOW)
    later = instant(NOW + timedelta(minutes=5))

    await issue(credentials, marta, CredentialPurpose.CLUB_RESET, at=later)

    assert await standing_of(credentials, invitation, now=later) is Standing.VALID
