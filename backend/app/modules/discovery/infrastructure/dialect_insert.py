"""An ``INSERT`` in the dialect a session is bound to — Postgres in every
environment, SQLite in the suite — for the ``ON CONFLICT`` clause both speak,
SQLite since 3.24. The directory's two tables write through it, as Rankings'
do through its own."""

from __future__ import annotations

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.base import Base


def insert_into(
    session: AsyncSession, model: type[Base]
) -> postgresql.Insert | sqlite.Insert:
    if session.get_bind().dialect.name == "postgresql":
        return postgresql.insert(model)
    return sqlite.insert(model)
