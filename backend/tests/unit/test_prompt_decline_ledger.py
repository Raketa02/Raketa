"""The decline ledger: durable, keyed by the question, and **write-only outward.**

Three claims run through every test here.

**A *not now* lapses; nothing sweeps it.** The window is a cut-off applied in the
read, so *thirty-one days ago* and *never declined* are the same answer at this
seam — and the row stays, because the row is the evidence and only the silence
expires.

**One read answers both families.** A decline keyed on the player and a decline
keyed on a sport come back from one query, which is the shape ``raised_for``
beside it is written to: a search that asked twice could be told two things about
one moment.

**There is no shape here that could answer *how often has this player said no***.
That is asserted over the port's own surface rather than left to a reviewer,
because the promise is not *we do not query for it* but *there is nothing to
query*.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import Sport
from app.modules.matchmaking.domain.declines import (
    PromptDecline,
    PromptDeclineLedger,
    silence_began,
)
from app.modules.matchmaking.domain.prompts import Prompt
from app.modules.matchmaking.infrastructure.sqlalchemy_prompt_decline_ledger import (
    SqlAlchemyPromptDeclineLedger,
)

NOW = datetime(2026, 8, 30, 18, 0, tzinfo=timezone.utc)

ADA = UUID("11111111-1111-1111-1111-111111111111")
BEA = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest.fixture
def ledger(session):
    return SqlAlchemyPromptDeclineLedger(session)


async def a_decline(
    ledger: PromptDeclineLedger,
    session,
    *,
    prompt: Prompt = Prompt.REFRESH_YOUR_TIMES,
    sport: Sport | None = None,
    player_id: UUID = ADA,
    at: datetime = NOW,
) -> None:
    """One row, committed the way the use case commits it."""

    await ledger.record(
        PromptDecline(player_id=player_id, prompt=prompt, sport=sport, at=at)
    )
    await session.commit()


async def test_a_decline_silences_its_question_for_the_player(ledger, session):
    await a_decline(ledger, session)

    assert await ledger.suppressed_for(
        player_id=ADA, sport=Sport.PADEL, since=silence_began(NOW)
    ) == frozenset({Prompt.REFRESH_YOUR_TIMES})


async def test_a_week_declined_on_one_sports_screen_goes_quiet_on_every_screen(
    ledger, session
):
    """The grid is one week and not seven, so its decline has no sport to be
    about — and the row that carries no sport comes back for all of them."""

    await a_decline(ledger, session, prompt=Prompt.KEEP_THIS_RADIUS)

    for sport in Sport:
        assert Prompt.KEEP_THIS_RADIUS in await ledger.suppressed_for(
            player_id=ADA, sport=sport, since=silence_began(NOW)
        )


async def test_a_declaration_declined_for_one_sport_is_still_asked_about_another(
    ledger, session
):
    """ADR-0094's *for that sport*, kept literally. A player who says *not now*
    about their padel intent has said nothing about tennis."""

    await a_decline(
        ledger, session, prompt=Prompt.UPDATE_PLAY_INTENT, sport=Sport.PADEL
    )

    padel = await ledger.suppressed_for(
        player_id=ADA, sport=Sport.PADEL, since=silence_began(NOW)
    )
    tennis = await ledger.suppressed_for(
        player_id=ADA, sport=Sport.TENNIS, since=silence_began(NOW)
    )

    assert padel == frozenset({Prompt.UPDATE_PLAY_INTENT})
    assert tennis == frozenset()


async def test_both_families_come_back_from_one_read(ledger, session):
    """The read a search makes, and it makes it once."""

    await a_decline(ledger, session, prompt=Prompt.KEEP_THIS_RADIUS)
    await a_decline(
        ledger, session, prompt=Prompt.UPDATE_PLAY_INTENT, sport=Sport.PADEL
    )

    assert await ledger.suppressed_for(
        player_id=ADA, sport=Sport.PADEL, since=silence_began(NOW)
    ) == frozenset({Prompt.KEEP_THIS_RADIUS, Prompt.UPDATE_PLAY_INTENT})


async def test_a_month_later_the_question_is_asked_again(ledger, session):
    """What handles the player whose habit genuinely changed. A suppression that
    never lapsed would be a question the platform may never ask again, decided by
    one tap on one evening."""

    await a_decline(ledger, session)
    later = NOW + timedelta(days=31)

    assert (
        await ledger.suppressed_for(
            player_id=ADA, sport=Sport.PADEL, since=silence_began(later)
        )
        == frozenset()
    )


async def test_the_row_outlives_the_silence(ledger, session):
    """**The whole reason this is a table and not a key with a TTL.** The
    suppression stops and the evidence stays: *how often does anybody ever say no
    to this* is the falsifier ``prompts.py``'s two constants are under.
    """

    await a_decline(ledger, session)

    kept = await ledger.suppressed_for(
        player_id=ADA, sport=Sport.PADEL, since=NOW - timedelta(days=365)
    )

    assert kept == frozenset({Prompt.REFRESH_YOUR_TIMES})


async def test_somebody_elses_no_is_not_mine(ledger, session):
    await a_decline(ledger, session, player_id=BEA)

    assert (
        await ledger.suppressed_for(
            player_id=ADA, sport=Sport.PADEL, since=silence_began(NOW)
        )
        == frozenset()
    )


async def test_a_second_no_is_a_second_row_and_buys_the_same_month(ledger, session):
    """Append-only, and nothing counts them: a tally is the shape a penalty grows
    out of, and what a second *not now* buys is exactly the first one's month."""

    await a_decline(ledger, session)
    await a_decline(ledger, session, at=NOW + timedelta(days=2))

    silenced = await ledger.suppressed_for(
        player_id=ADA, sport=Sport.PADEL, since=silence_began(NOW + timedelta(days=2))
    )

    assert silenced == frozenset({Prompt.REFRESH_YOUR_TIMES})


def test_no_shape_on_this_port_can_answer_how_often_somebody_said_no():
    """**Write-only from the outside**, over the port's own surface: two methods,
    one of which writes, and neither of which lists or counts."""

    asked = {
        name
        for name in dir(PromptDeclineLedger)
        if not name.startswith("_") and callable(getattr(PromptDeclineLedger, name))
    }

    assert asked == {"record", "suppressed_for"}
