"""Every read of a one-time credential is a claim on it.

*Five wrong codes lock the credential* and *usable once* are both a
read-then-write: a claim reads the counter and writes it back one higher, a use
reads the credential and marks it spent. Without a row lock, twenty wrong codes
sent at once would each read nought and write one. The suite runs on SQLite,
which renders no ``FOR UPDATE`` and has one connection, so the race cannot be
driven here — what can be asserted is that every read the store makes asks
Postgres for the lock.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.kernel import instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.one_time_credential import CredentialPurpose
from app.modules.auth.infrastructure.sqlalchemy_one_time_credential_store import (
    SqlAlchemyOneTimeCredentialStore,
)

NOW = instant(datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))


class _NoRows:
    def scalar_one_or_none(self):
        return None

    def scalars(self):
        return self

    def all(self):
        return []


class RecordingSession:
    """Keeps every statement it is asked to run, and finds nothing."""

    def __init__(self) -> None:
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _NoRows()


READS = {
    "by_token_hash": lambda store: store.by_token_hash("digest"),
    "by_ticket_hash": lambda store: store.by_ticket_hash("digest"),
    "issued_to": lambda store: store.issued_to(
        "tomek@example.com",
        purpose=CredentialPurpose.FORGOT_PASSWORD,
        audience=Audience.PLAYER_APP,
        since=NOW,
    ),
    "live_for": lambda store: store.live_for(
        uuid4(),
        purpose=CredentialPurpose.FORGOT_PASSWORD,
        audience=Audience.PLAYER_APP,
        now=NOW,
    ),
}


@pytest.mark.parametrize("read", READS.values(), ids=READS.keys())
async def test_every_read_locks_the_rows_it_returns(read) -> None:
    session = RecordingSession()

    await read(SqlAlchemyOneTimeCredentialStore(session))

    (statement,) = session.statements
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert compiled.rstrip().endswith("FOR UPDATE"), compiled
