"""The ledger's two promises, over a real database.

Both are things the route walk cannot reach. The **collapse** is visible there
only as *the row that is left*, and this asserts the shape that produces it; the
**race** is unreachable at all, because the use case's own check refuses a second
card long before the key ever sees one.

The third thing here is the read both callers share — *which of these cards are
closed* — asserted at the two arities it is actually asked at: one game, when a
card is about to be answered, and a page of them, when the list route joins.

They are here rather than in ``tests/demands/`` because there is one
implementation and nothing outside this context reads it: the demand registers
are for ports somebody *else* executes, and a register of one row nobody consumes
would be a claim about a kind of claim this context has not made yet.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.kernel import instant
from app.modules.sportsmanship.domain.card import (
    SettledCourt,
    SportsmanshipCard,
    StarsGiven,
)
from app.modules.sportsmanship.domain.errors import YouHaveAlreadyRatedThisGame
from app.modules.sportsmanship.infrastructure.card_model import (
    SportsmanshipRatingORM,
)
from app.modules.sportsmanship.infrastructure.sqlalchemy_sportsmanship_ledger import (
    SqlAlchemySportsmanshipLedger,
)

MONDAY = instant(datetime(2026, 9, 7, 20, 0, tzinfo=timezone.utc))
FRIDAY = instant(datetime(2026, 9, 11, 20, 0, tzinfo=timezone.utc))


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


@pytest_asyncio.fixture
async def ledger(session):
    return SqlAlchemySportsmanshipLedger(session)


def a_card(*, rater, others, given, at):
    return SportsmanshipCard.answered(
        court=SettledCourt(
            game_id=uuid4(),
            rater_id=rater,
            others=tuple(others),
            played_at=MONDAY,
        ),
        given=[StarsGiven(subject_id=who, stars=stars) for who, stars in given],
        at=at,
    )


async def _ratings(session) -> list[SportsmanshipRatingORM]:
    found = await session.execute(select(SportsmanshipRatingORM))
    return list(found.scalars())


async def test_a_later_card_replaces_what_this_rater_last_said_about_somebody(
    session, ledger
):
    """**The collapse is the primary key.** Two evenings with the same partner
    leave one answer, and it is Friday's."""

    rater, partner = uuid4(), uuid4()
    await ledger.record(
        a_card(rater=rater, others=[partner], given=[(partner, 5)], at=MONDAY)
    )
    await ledger.record(
        a_card(rater=rater, others=[partner], given=[(partner, 2)], at=FRIDAY)
    )
    await session.commit()

    (only,) = await _ratings(session)
    assert only.stars == 2
    assert only.rated_at.replace(tzinfo=timezone.utc) == FRIDAY


async def test_two_raters_about_one_person_are_two_answers(session, ledger):
    """The collapse is per **pair**, not per subject — which is what makes the
    count beside the published figure mean *how many different people*."""

    subject = uuid4()
    for stars in (5, 2):
        rater = uuid4()
        await ledger.record(
            a_card(
                rater=rater, others=[subject], given=[(subject, stars)], at=MONDAY
            )
        )
    await session.commit()

    assert sorted(one.stars for one in await _ratings(session)) == [2, 5]


async def test_a_blank_does_not_withdraw_an_earlier_answer(session, ledger):
    """The delete is scoped to the pairs a card actually answers. Leaving
    somebody out is the absence of an opinion, never the withdrawal of one."""

    rater, partner, opponent = uuid4(), uuid4(), uuid4()
    await ledger.record(
        a_card(
            rater=rater,
            others=[partner, opponent],
            given=[(partner, 5)],
            at=MONDAY,
        )
    )
    await ledger.record(
        a_card(
            rater=rater,
            others=[partner, opponent],
            given=[(opponent, 3)],
            at=FRIDAY,
        )
    )
    await session.commit()

    assert {one.subject_id: one.stars for one in await _ratings(session)} == {
        partner: 5,
        opponent: 3,
    }


async def test_an_all_blank_card_is_stored_and_closes_the_card(session, ledger):
    rater, partner = uuid4(), uuid4()
    card = a_card(rater=rater, others=[partner], given=[], at=MONDAY)

    await ledger.record(card)
    await session.commit()

    assert await _ratings(session) == []
    assert await ledger.answered_among(
        rater_id=card.rater_id, game_ids=(card.game_id,)
    ) == {card.game_id}


async def test_two_cards_racing_for_one_court_meet_the_key_as_a_refusal(
    session, ledger
):
    """**The branch the use case's own check can never reach.**

    Two taps in flight together both find the card open and both insert. The
    loser meets the primary key, and it comes back as the refusal it is rather
    than as an integrity error — because the alternative answers one of two
    identical taps with a 500, and the card is closed either way.
    """

    rater, partner = uuid4(), uuid4()
    court = SettledCourt(
        game_id=uuid4(), rater_id=rater, others=(partner,), played_at=MONDAY
    )
    first = SportsmanshipCard.answered(
        court=court, given=[StarsGiven(subject_id=partner, stars=5)], at=MONDAY
    )
    second = SportsmanshipCard.answered(
        court=court, given=[StarsGiven(subject_id=partner, stars=1)], at=FRIDAY
    )

    await ledger.record(first)
    with pytest.raises(YouHaveAlreadyRatedThisGame):
        await ledger.record(second)


async def test_a_card_nobody_answered_is_not_closed(session, ledger):
    assert (
        await ledger.answered_among(rater_id=uuid4(), game_ids=(uuid4(),))
        == frozenset()
    )


async def test_asking_about_nothing_answers_nothing(ledger):
    """The common case on the list route — a player with no open card — and it
    is answered without a statement, because ``IN ()`` is a thing two dialects
    disagree about for an answer known before either sees it."""

    assert await ledger.answered_among(rater_id=uuid4(), game_ids=()) == frozenset()


async def test_only_the_closed_ones_among_a_list_come_back(session, ledger):
    """The list read's whole join: many courts, one question, and the answer is
    which of them are shut."""

    rater, partner = uuid4(), uuid4()
    closed = a_card(rater=rater, others=[partner], given=[(partner, 4)], at=MONDAY)
    await ledger.record(closed)
    await session.commit()
    still_open, somebody_elses = uuid4(), uuid4()

    assert await ledger.answered_among(
        rater_id=rater, game_ids=(closed.game_id, still_open, somebody_elses)
    ) == {closed.game_id}


async def test_one_rater_answering_does_not_close_the_card_for_the_others(
    session, ledger
):
    """A card belongs to a rater and not to a game, which is why the key carries
    both."""

    game_id = uuid4()
    mine, theirs = uuid4(), uuid4()
    await ledger.record(
        SportsmanshipCard.answered(
            court=SettledCourt(
                game_id=game_id,
                rater_id=mine,
                others=(theirs,),
                played_at=MONDAY,
            ),
            given=[StarsGiven(subject_id=theirs, stars=4)],
            at=MONDAY,
        )
    )
    await session.commit()

    assert await ledger.answered_among(rater_id=mine, game_ids=(game_id,)) == {
        game_id
    }
    assert (
        await ledger.answered_among(rater_id=theirs, game_ids=(game_id,))
        == frozenset()
    )


async def test_a_rating_carries_the_card_it_came_from(session, ledger):
    """``game_id`` is a column and not a key: the answer belongs to the pair, and
    the game says which evening produced the one that stands."""

    rater, partner = uuid4(), uuid4()
    monday = a_card(rater=rater, others=[partner], given=[(partner, 5)], at=MONDAY)
    friday = a_card(rater=rater, others=[partner], given=[(partner, 2)], at=FRIDAY)
    await ledger.record(monday)
    await ledger.record(friday)
    await session.commit()

    (only,) = await _ratings(session)
    assert only.game_id == friday.game_id
    assert only.game_id != monday.game_id
    assert FRIDAY - MONDAY == timedelta(days=4)
