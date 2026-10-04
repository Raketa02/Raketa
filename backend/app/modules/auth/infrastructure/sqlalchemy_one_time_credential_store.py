from __future__ import annotations

from typing import AbstractSet, Final, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import (
    stored_instant,
    stored_instant_or_none,
)
from app.kernel import Instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.one_time_credential import (
    CredentialPurpose,
    OneTimeCredential,
)
from app.modules.auth.infrastructure.one_time_credential_model import (
    OneTimeCredentialORM,
)

#: The most credentials one claim compares a code against. Each comparison is a
#: password-hasher verify, so the look-back is bounded by count as well as by
#: time; the request throttle keeps an honest address far below it.
_CLAIM_CANDIDATES: Final = 10


def _codes(purposes: AbstractSet[CredentialPurpose]) -> list[str]:
    # Sorted, so the statement a set of purposes renders is the same every time
    # (``docs/adr/0105``).
    return sorted(purpose.value for purpose in purposes)


def _to_domain(row: OneTimeCredentialORM) -> OneTimeCredential:
    return OneTimeCredential(
        id=row.id,
        purpose=CredentialPurpose(row.purpose),
        audience=Audience(row.audience),
        subject_id=row.subject_id,
        email=row.email,
        token_hash=row.token_hash,
        code_hash=row.code_hash,
        issued_at=stored_instant(row.issued_at),
        expires_at=stored_instant(row.expires_at),
        wrong_codes=row.wrong_codes,
        used_at=stored_instant_or_none(row.used_at),
        ticket_hash=row.ticket_hash,
        ticket_expires_at=stored_instant_or_none(row.ticket_expires_at),
    )


class SqlAlchemyOneTimeCredentialStore:
    """``OneTimeCredentialStore`` over ``one_time_credentials``, in the caller's
    transaction.

    **Every read takes the rows it returns ``FOR UPDATE``**, because each is read
    to be changed: a claim counts a wrong code, a use spends the credential, an
    issue retires the older ones. ``save`` writes the counter as an absolute
    value, which is only safe on a row nobody else can be changing — without the
    lock, twenty wrong codes sent at once would each read nought and each write
    one, and the fifth would lock nothing. SQLite renders no ``FOR UPDATE`` and
    runs one connection, so this is a guarantee the suite states and Postgres
    keeps.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, credential: OneTimeCredential) -> None:
        self._session.add(
            OneTimeCredentialORM(
                id=credential.id,
                purpose=credential.purpose.value,
                audience=credential.audience.value,
                subject_id=credential.subject_id,
                email=credential.email,
                token_hash=credential.token_hash,
                code_hash=credential.code_hash,
                issued_at=credential.issued_at,
                expires_at=credential.expires_at,
                wrong_codes=credential.wrong_codes,
                used_at=credential.used_at,
                ticket_hash=credential.ticket_hash,
                ticket_expires_at=credential.ticket_expires_at,
            )
        )
        await self._session.flush()

    async def save(self, credential: OneTimeCredential) -> None:
        row = await self._session.get(OneTimeCredentialORM, credential.id)
        if row is None:
            raise RuntimeError(f"credential {credential.id} has no row to save onto")
        row.expires_at = credential.expires_at
        row.wrong_codes = credential.wrong_codes
        row.used_at = credential.used_at
        row.ticket_hash = credential.ticket_hash
        row.ticket_expires_at = credential.ticket_expires_at
        await self._session.flush()

    async def by_token_hash(self, token_hash: str) -> Optional[OneTimeCredential]:
        return await self._one(OneTimeCredentialORM.token_hash == token_hash)

    async def by_ticket_hash(self, ticket_hash: str) -> Optional[OneTimeCredential]:
        return await self._one(OneTimeCredentialORM.ticket_hash == ticket_hash)

    async def issued_to(
        self,
        email: str,
        *,
        purposes: AbstractSet[CredentialPurpose],
        audience: Audience,
        since: Instant,
    ) -> list[OneTimeCredential]:
        result = await self._session.execute(
            select(OneTimeCredentialORM)
            .where(
                OneTimeCredentialORM.email == email,
                OneTimeCredentialORM.purpose.in_(_codes(purposes)),
                OneTimeCredentialORM.audience == audience.value,
                OneTimeCredentialORM.issued_at > since,
            )
            .order_by(OneTimeCredentialORM.issued_at.desc(), OneTimeCredentialORM.id)
            .limit(_CLAIM_CANDIDATES)
            .with_for_update()
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def live_for(
        self,
        subject_id: UUID,
        *,
        purposes: AbstractSet[CredentialPurpose],
        audience: Audience,
        now: Instant,
    ) -> list[OneTimeCredential]:
        result = await self._session.execute(
            select(OneTimeCredentialORM)
            .where(
                OneTimeCredentialORM.subject_id == subject_id,
                OneTimeCredentialORM.purpose.in_(_codes(purposes)),
                OneTimeCredentialORM.audience == audience.value,
                OneTimeCredentialORM.used_at.is_(None),
                OneTimeCredentialORM.expires_at > now,
            )
            .with_for_update()
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def _one(self, condition) -> Optional[OneTimeCredential]:
        result = await self._session.execute(
            select(OneTimeCredentialORM).where(condition).with_for_update()
        )
        row = result.scalar_one_or_none()
        return None if row is None else _to_domain(row)
