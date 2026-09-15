"""The deck-reset ledger: *Show them again*, as a durable row the deal reads.

Three claims run through every test here.

**A reset is a moment, and the deal reads the latest one** (``docs/adr/0169``
§5). Per player, per sport: a padel reset says nothing about tennis, and a
player who has never pressed it has no moment at all — which the deal reads as
*nothing cleared*, the state everybody starts in.

**It is append-only.** A second press is a second row rather than an update of
the first, because every reset is a moment the falsifier ``docs/adr/0128`` §5
protects has to exclude from its sample — a re-show that came from a reset is
not evidence about ``PASS_SUPPRESS``, and only the rows can say which ones did.

**And the ledger has no shape that could answer anything else.** No list, no
count, no *who has reset*: the port declares one write and one read, and the
read answers a moment or ``None``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import Sport, instant
from app.modules.matchmaking.domain.deck_reset import DeckReset, DeckResetLedger
from app.modules.matchmaking.infrastructure.sqlalchemy_deck_reset_ledger import (
    SqlAlchemyDeckResetLedger,
)

NOW = instant(datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc))

ADA = UUID("11111111-1111-1111-1111-111111111111")
BEA = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def ledger(session):
    return SqlAlchemyDeckResetLedger(session)


def test_the_adapter_signs_the_port(ledger):
    assert isinstance(ledger, DeckResetLedger)


def test_the_ledger_offers_one_write_and_one_read_and_nothing_a_route_could_render():
    """No list, no count, no *who*. The read answers a moment or ``None``."""

    methods = {
        name
        for name in vars(DeckResetLedger)
        if callable(getattr(DeckResetLedger, name)) and not name.startswith("_")
    }

    assert methods == {"record", "latest_at"}


async def test_nobody_has_reset_until_somebody_does(ledger):
    assert await ledger.latest_at(player_id=ADA, sport=Sport.PADEL) is None


async def test_a_reset_is_read_back_for_its_player_and_sport_and_no_other(
    ledger, session
):
    await ledger.record(DeckReset(player_id=ADA, sport=Sport.PADEL, at=NOW))

    assert await ledger.latest_at(player_id=ADA, sport=Sport.PADEL) == NOW
    assert await ledger.latest_at(player_id=ADA, sport=Sport.TENNIS) is None, (
        "a padel reset reached the tennis deck"
    )
    assert await ledger.latest_at(player_id=BEA, sport=Sport.PADEL) is None, (
        "one player's reset reached another's deck"
    )


async def test_a_second_reset_is_a_second_row_and_the_latest_is_what_is_read(
    ledger, session
):
    """Append-only, and the deal reads the most recent moment — whichever order
    the rows arrived in."""

    later = NOW + timedelta(hours=3)
    await ledger.record(DeckReset(player_id=ADA, sport=Sport.PADEL, at=later))
    await ledger.record(DeckReset(player_id=ADA, sport=Sport.PADEL, at=NOW))

    assert await ledger.latest_at(player_id=ADA, sport=Sport.PADEL) == later


async def test_the_ledger_does_not_commit_for_its_caller(ledger, session):
    """The transaction boundary is the command's, as it is for every ledger here."""

    await ledger.record(DeckReset(player_id=ADA, sport=Sport.PADEL, at=NOW))
    await session.rollback()

    assert await ledger.latest_at(player_id=ADA, sport=Sport.PADEL) is None
