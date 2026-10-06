"""A game still filling, and a player's three answers to it: **yes**, **no** and
a yes taken back (#538; the mechanics §5–§7, §6.6; the screens A2.4, A3.2, A7.3).

Every answer is given over HTTP as the phone gives it, and every claim is read
where a player would read it — the answer to the request, and their live yeses
— except the three the phone has no window on: that a yes moves no money, that
the pool is a row of its own, and the sweep's record of an expiry.

The rules these hold the routes to:

- **a yes is silent and moves nothing**, and a no is silent and final;
- **yeses are the game's, not a version's** — a yes on any version counts;
- **a replacement must fit everybody already In**, every pair, both when a
  version is dealt and when a yes lands;
- **ten live yeses per sport**, refused with its code;
- **the book-by is derived from the club** and is the only deadline: a
  proposal past it is over at once, and the sweep records it silently.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.api.dependencies import get_clock
from app.engines.matchfit.core import SearchMode
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
from app.modules.proposals.domain.errors import (
    CourtHourNotForSale,
    NotInThePool,
    PaymentMethodRequired,
    PoolNotFound,
    VersionDoesNotFit,
)
from app.modules.proposals.infrastructure.proposal_models import PoolORM, ProposalORM
from tests.api import players_world as players
from tests.unit.fake_clock import MovableClock
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_player,
    deals,
    live_ids,
    live_yeses,
    makes,
    saves_a_card,
    says_no,
    says_yes,
    sweeps,
    warsaw,
    withdraws,
)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card."""

    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club, *four[1:])


async def events_of(session_factory, proposal_id: UUID) -> list[str]:
    async with session_factory() as session:
        return list(
            (
                await session.scalars(
                    select(EventStoreORM.event_type)
                    .where(EventStoreORM.aggregate_id == proposal_id)
                    .order_by(EventStoreORM.version)
                )
            ).all()
        )


# --------------------------------------------------------------------------- #
# A yes
# --------------------------------------------------------------------------- #


async def test_a_yes_lands_on_the_game_and_in_the_player_s_live_yeses(
    client, session_factory, clock, club, four, group
):
    ola = four[0]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )

    said = await says_yes(client, ola, proposal)

    assert said.status_code == 200, said.text
    assert said.json() == {
        "proposal_id": str(proposal),
        "open_seats": 3,
        "booked": None,
        "waiting_for_the_club": False,
        "your_payment": None,
    }
    assert await live_yeses(client, ola) == {
        "yeses": [
            {
                "proposal_id": str(proposal),
                "pool_id": str(group),
                "sport": "PADEL",
                "kind": "COMPETITIVE",
                "starts_at": "2026-10-10T15:00:00Z",
                "club": {"id": club, "name": "Bonarka Arena"},
                "share_grosze": 30_00,
                # Instant: the start less the two hours' minimum notice.
                "book_by": "2026-10-10T13:00:00Z",
            }
        ],
    }


async def test_a_yes_moves_no_money_and_tells_nobody(
    client, session_factory, clock, payments, mailbox, club, four, group
):
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    asked_before = len(payments.calls)

    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200

    assert len(payments.calls) == asked_before
    assert await mailbox.sent() == []


async def test_a_yes_already_said_records_nothing(
    client, session_factory, clock, club, four, group
):
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, four[0], proposal)
    recorded = await events_of(session_factory, proposal)

    again = await says_yes(client, four[0], proposal)

    assert again.status_code == 200
    assert again.json()["open_seats"] == 3
    assert await events_of(session_factory, proposal) == recorded


async def test_a_game_nobody_dealt_you_is_not_found(
    client, session_factory, clock, payments, club, four, group
):
    stranger = await a_player(client, payments, "stranger")
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )

    for answer in (says_yes, says_no, withdraws):
        refused = await answer(client, stranger, proposal)
        assert refused.status_code == 404
        assert refused.json()["code"] == "proposal_not_found"
    missing = await says_yes(client, four[0], uuid4())
    assert missing.status_code == 404


async def test_a_yes_needs_a_method_to_charge(
    client, session_factory, clock, payments, club, four
):
    cardless = await a_player(client, payments, "cardless", card=False)
    group = await a_group(client, four[0], club, cardless, *four[1:3])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((cardless, *four[1:3]),),
    )

    refused = await says_yes(client, cardless, proposal)

    assert refused.status_code == 409
    assert refused.json()["code"] == "payment_method_required"
    await saves_a_card(client, payments, cardless["headers"])
    assert (await says_yes(client, cardless, proposal)).status_code == 200


async def test_leaving_the_group_withdraws_the_leaver_s_yeses_there(
    client, session_factory, clock, club, four, group
):
    """The mechanics §19: *you leave a group — your yeses there are withdrawn*.
    Refused at once, since a yes asks the pool who is in it now; withdrawn
    when the leaving is delivered, as a tap on *Withdraw* would."""

    kuba, ewa, tomek = four[1], four[2], four[3]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, kuba, proposal)
    await says_yes(client, ewa, proposal)
    for leaver in (kuba, ewa, tomek):
        left = await client.delete(
            f"/api/v1/groups/{group}/membership", headers=leaver["headers"]
        )
        assert left.status_code in (200, 204), left.text

    refused = await says_yes(client, tomek, proposal)
    assert refused.status_code == 404
    assert refused.json()["code"] == "proposal_not_found"
    # A yes of one's own can be withdrawn by hand before the leaving lands.
    assert (await withdraws(client, ewa, proposal)).status_code == 204

    await players.deliver_the_outbox(session_factory)

    assert await live_ids(client, kuba) == []
    assert (await events_of(session_factory, proposal)).count(
        "proposals.yes_withdrawn"
    ) == 2


# --------------------------------------------------------------------------- #
# A no, and a yes taken back
# --------------------------------------------------------------------------- #


async def test_a_no_is_silent_and_final(
    client, session_factory, clock, club, four, group
):
    kuba = four[1]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )

    said = await says_no(client, kuba, proposal)

    assert said.status_code == 204
    assert (await says_no(client, kuba, proposal)).status_code == 204
    refused = await says_yes(client, kuba, proposal)
    assert refused.status_code == 409
    assert refused.json()["code"] == "proposal_already_answered"
    assert await events_of(session_factory, proposal) == [
        "proposals.proposal_made",
        "proposals.version_dealt",
        "proposals.no_said",
    ]


async def test_somebody_in_leaves_by_withdrawing_rather_than_by_a_no(
    client, session_factory, clock, club, four, group
):
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, four[0], proposal)

    refused = await says_no(client, four[0], proposal)

    assert refused.status_code == 409
    assert refused.json()["code"] == "proposal_already_answered"


async def test_a_withdrawn_yes_leaves_the_live_list_and_may_be_said_again(
    client, session_factory, clock, club, four, group
):
    ola = four[0]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, proposal)

    withdrawn = await withdraws(client, ola, proposal)

    assert withdrawn.status_code == 204
    assert await live_ids(client, ola) == []
    again = await says_yes(client, ola, proposal)
    assert again.status_code == 200
    assert await live_ids(client, ola) == [str(proposal)]


async def test_withdrawing_a_yes_never_said_records_nothing(
    client, session_factory, clock, club, four, group
):
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    recorded = await events_of(session_factory, proposal)

    assert (await withdraws(client, four[1], proposal)).status_code == 204
    assert await events_of(session_factory, proposal) == recorded


async def test_a_poster_withdrawing_alone_takes_the_post_with_them(
    client, session_factory, clock, club, four, group
):
    ola, kuba = four[0], four[1]
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=ola,
        versions=(tuple(four[1:]),),
    )
    assert await live_ids(client, ola) == [str(post)]

    assert (await withdraws(client, ola, post)).status_code == 204

    refused = await says_yes(client, kuba, post)
    assert refused.status_code == 409
    assert refused.json()["code"] == "proposal_is_over"
    assert refused.json()["details"] == {"standing": "WITHDRAWN"}
    assert (await events_of(session_factory, post))[-2:] == [
        "proposals.yes_withdrawn",
        "proposals.proposal_withdrawn",
    ]


async def test_a_poster_withdrawing_leaves_the_game_to_those_in(
    client, session_factory, clock, club, four, group
):
    ola, kuba, ewa = four[0], four[1], four[2]
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=ola,
        versions=(tuple(four[1:]),),
    )
    await says_yes(client, kuba, post)

    await withdraws(client, ola, post)

    assert await live_ids(client, kuba) == [str(post)]
    assert (await says_yes(client, ewa, post)).json()["open_seats"] == 2


# --------------------------------------------------------------------------- #
# One game, several versions
# --------------------------------------------------------------------------- #


async def test_yeses_on_two_versions_fill_the_one_game(
    client, session_factory, clock, payments, club
):
    """The mechanics §7's example: Marek posts Saturday 17:00, version 1 is
    B, C, D and version 2 is E, F, G. B and C say yes on version 1 and E on
    version 2 — Marek, B, C and E are four."""

    marek, b, c, d, e, f, g = [
        await a_player(client, payments, name)
        for name in ("marek", "bartek", "celina", "dawid", "ela", "filip", "gosia")
    ]
    group = await a_group(client, marek, club, b, c, d, e, f, g)
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=marek,
        versions=((b, c, d), (e, f, g)),
    )

    assert (await says_yes(client, b, post)).json()["open_seats"] == 2
    assert (await says_yes(client, c, post)).json()["open_seats"] == 1
    last = (await says_yes(client, e, post)).json()
    assert last["open_seats"] == 0

    # Marek, B, C and E filled it — across two versions — so it booked (#541).
    assert last["booked"]["booking_id"] == str(post)
    for player in (marek, b, c, e):
        assert await live_ids(client, player) == []
    late = await says_yes(client, f, post)
    assert late.status_code == 409
    assert late.json()["code"] == "proposal_is_over"
    assert late.json()["details"] == {"standing": "FILLED"}


async def test_a_version_dealt_later_counts_toward_the_same_game(
    client, session_factory, clock, payments, club, four, group
):
    ola, kuba, ewa, tomek = four
    late = await a_player(client, payments, "late")
    await client.post(f"/api/v1/groups/{group}/membership", headers=late["headers"])
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, pick)
    await says_no(client, tomek, pick)

    assert await deals(session_factory, clock, pick, late) == 2

    assert (await says_yes(client, late, pick)).json()["open_seats"] == 2


async def test_a_seat_a_no_left_is_dealt_again_into_its_version(
    client, session_factory, clock, payments, club, four, group
):
    """The mechanics §6.2: *your seat is dealt, as a card, to the next best
    fits* — into the version the no was on, which spends no second version."""

    ola, tomek = four[0], four[3]
    late = await a_player(client, payments, "late")
    await client.post(f"/api/v1/groups/{group}/membership", headers=late["headers"])
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, pick)
    await says_no(client, tomek, pick)

    assert await deals(session_factory, clock, pick, late, into=1) == 1

    assert (await says_yes(client, late, pick)).json()["open_seats"] == 2


# --------------------------------------------------------------------------- #
# A replacement must fit everybody already In — every pair
# --------------------------------------------------------------------------- #


async def test_a_yes_from_somebody_who_does_not_fit_a_player_in_is_refused(
    client, session_factory, clock, payments, club
):
    marek, b, c, d, e, f, g = [
        await a_player(client, payments, name)
        for name in ("marek", "bartek", "celina", "dawid", "ela", "filip", "gosia")
    ]
    group = await a_group(client, marek, club, b, c, d, e, f, g)
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=marek,
        versions=((b, c, d), (e, f, g)),
    )
    # Dealt while only Marek was In, and E fitted him; B, In since, blocked E.
    await says_yes(client, b, post)
    assert (await players.block_between(client, b["token"], e["id"])).status_code == 204

    refused = await says_yes(client, e, post)

    assert refused.status_code == 409
    assert refused.json()["code"] == "no_longer_fits"
    # Who is not said.
    assert "details" not in refused.json()
    # Whoever fits everybody In still gets in.
    assert (await says_yes(client, f, post)).status_code == 200


async def test_a_version_naming_somebody_who_does_not_fit_a_player_in_is_not_dealt(
    client, session_factory, clock, payments, club, four, group
):
    ola = four[0]
    blocked = await a_player(client, payments, "blocked")
    await client.post(f"/api/v1/groups/{group}/membership", headers=blocked["headers"])
    await players.block_between(client, ola["token"], blocked["id"])
    pick = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, pick)
    await says_no(client, four[3], pick)

    with pytest.raises(VersionDoesNotFit):
        await deals(session_factory, clock, pick, blocked)


async def test_every_pair_on_a_version_must_fit_each_other(
    client, session_factory, clock, payments, club, four, group
):
    far = await a_player(client, payments, "far", sports=())
    await players.rate_in(
        session_factory, far["id"], Sport.PADEL, mu=4.5
    )  # Levels apart: outside the competitive window of anybody here.
    await client.post(f"/api/v1/groups/{group}/membership", headers=far["headers"])

    with pytest.raises(VersionDoesNotFit):
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            versions=((*four[:3], far),),
        )


async def test_a_gender_preference_is_a_pair_that_does_not_fit(
    client, session_factory, clock, payments, club, four, group
):
    """Every one of the four is a woman; a man who plays with men only fits
    none of them, and nor do they him."""

    only_men = await a_player(
        client, payments, "adam", gender="MAN", gender_preference="MEN_ONLY"
    )
    await client.post(f"/api/v1/groups/{group}/membership", headers=only_men["headers"])

    with pytest.raises(VersionDoesNotFit):
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            versions=((four[0], only_men),),
        )


async def test_nobody_outside_the_pool_is_dealt_a_game_from_it(
    client, session_factory, clock, payments, club, four, group
):
    outsider = await a_player(client, payments, "outsider")

    with pytest.raises(NotInThePool):
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            versions=((*four[:3], outsider),),
        )


# --------------------------------------------------------------------------- #
# No cap on live yeses
# --------------------------------------------------------------------------- #


async def test_a_player_may_be_in_on_any_number_of_games_still_filling(
    client, session_factory, clock, club, four, group
):
    """There is no live-yes cap (removed 2026-10-05): games per week and one
    game per hour already bound what a yes can book."""

    ola = four[0]
    games = [
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            start=warsaw(10, 7 + hour),
            versions=((ola,),),
        )
        for hour in range(11)
    ]

    for game in games:
        said = await says_yes(client, ola, game)
        assert said.status_code == 200, said.text

    assert await live_ids(client, ola) == [str(game) for game in games]


# --------------------------------------------------------------------------- #
# The book-by
# --------------------------------------------------------------------------- #


async def test_at_its_book_by_a_game_is_over_and_the_sweep_records_it_silently(
    client, session_factory, clock, mailbox, club, four, group
):
    ola, kuba = four[0], four[1]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, proposal)

    clock.move(SATURDAY_FIVE - timedelta(hours=2) - clock.now())

    assert await live_ids(client, ola) == []
    refused = await says_yes(client, kuba, proposal)
    assert refused.status_code == 409
    assert refused.json()["details"] == {"standing": "EXPIRED"}
    swept = await sweeps(session_factory, clock)
    assert (swept.proposals, swept.conflicts) == (1, 0)
    assert (await events_of(session_factory, proposal))[-1] == (
        "proposals.proposal_expired"
    )
    assert (await sweeps(session_factory, clock)).proposals == 0
    assert await mailbox.sent() == []


async def test_before_its_book_by_the_sweep_leaves_a_game_alone(
    client, session_factory, clock, club, four, group
):
    await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    clock.move(timedelta(days=5))  # Saturday 08:00, five hours before.

    assert (await sweeps(session_factory, clock)).proposals == 0


async def test_an_only_raketa_club_s_book_by_is_its_release_time(
    client, session_factory, clock, payments, four
):
    club = await a_club_selling(
        client, name="Centrum Ruchu", way="ONLY_RAKETA", release_lead_days=3
    )
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, four[0], proposal)

    [yes] = (await live_yeses(client, four[0]))["yeses"]

    assert yes["book_by"] == "2026-10-07T15:00:00Z"


# --------------------------------------------------------------------------- #
# Making a proposal
# --------------------------------------------------------------------------- #


async def test_the_first_game_in_a_group_opens_its_pool_under_the_group_s_id(
    session_factory, clock, club, four, group
):
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await makes(session_factory, clock, pool_id=group, club_id=club)

    async with session_factory() as session:
        pools = (await session.scalars(select(PoolORM))).all()
        row = await session.get(ProposalORM, proposal)
    assert [(pool.id, pool.kind) for pool in pools] == [(group, "GROUP")]
    assert row is not None and row.pool_id == group


async def test_a_game_is_proposed_only_at_an_hour_the_club_sells(
    client, session_factory, clock, four, group, club
):
    paused = await a_club_selling(client, name="Zablocie Sport", paused=True)
    with pytest.raises(CourtHourNotForSale):
        await makes(session_factory, clock, pool_id=group, club_id=paused)
    with pytest.raises(CourtHourNotForSale):
        # Squash is not sold here at all.
        await makes(
            session_factory, clock, pool_id=group, club_id=club, sport=Sport.SQUASH
        )
    with pytest.raises(CourtHourNotForSale):
        # An hour already past its book-by.
        await makes(
            session_factory, clock, pool_id=group, club_id=club, start=warsaw(5, 9)
        )


async def test_a_game_is_proposed_only_in_a_pool_that_exists(
    session_factory, clock, club, four
):
    with pytest.raises(PoolNotFound):
        await makes(session_factory, clock, pool_id=uuid4(), club_id=club)


async def test_a_post_is_the_poster_s_yes_and_needs_their_card(
    client, session_factory, clock, payments, club, four
):
    cardless = await a_player(client, payments, "cardless", card=False)
    group = await a_group(client, cardless, club, *four)

    with pytest.raises(PaymentMethodRequired):
        await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            poster=cardless,
            kind=SearchMode.FOR_FUN,
        )


# --------------------------------------------------------------------------- #
# Payments asks about live yeses
# --------------------------------------------------------------------------- #


async def test_a_method_with_a_live_yes_on_it_cannot_be_removed(
    client, session_factory, clock, club, four, group
):
    ola = four[0]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    await says_yes(client, ola, proposal)

    refused = await client.delete(
        "/api/v1/players/me/payment-methods/current", headers=ola["headers"]
    )

    assert refused.status_code == 409
    assert refused.json()["details"] == {"live_yeses": 1, "upcoming_games": 0}
    await withdraws(client, ola, proposal)
    removed = await client.delete(
        "/api/v1/players/me/payment-methods/current", headers=ola["headers"]
    )
    assert removed.status_code in (200, 204), removed.text
