"""A group's **Games** deck, read as the phone reads it (#539; the mechanics §6.6,
§7, §8; the screens A1, A2).

Every card is made the way the engine will make one (``MakeProposal``), answered
over HTTP as the phone answers it, and read back through
``GET /pools/{id}/deck`` as the reader. The claims:

- **a card is the reader's own version** — everybody In, the reader, and the
  rest of their version — drawn with its sides, forecast, overlap, court block
  and deadline;
- **the order** is seats open after the reader's yes, then challenge › pick,
  then the soonest deadline, then the best forecast; **the same people** are
  dealt at their best hour only; **a no is final** and a yes moves the card to
  *You're In*;
- **every filter**: blocks, gender preference and the level gate (the matcher's
  pair rule, read live), the Play intent's segments, *most I'll pay*, a week at
  the games-per-week cap and an hour already taken;
- **the counts, the badge and the capped weeks** around the deck.

The tests that need booked games stand in for them by overriding
``get_booked_games``, so the deck's filters are asserted without filling games —
a fill's effect on the deck is ``test_the_fill.py``'s (#541).

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_clock
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.payments.domain.provider import ClubAccountStatus
from app.modules.proposals.presentation.dependencies import get_booked_games
from app.modules.rating.domain.events import RatingMovedOnResult
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from tests.api import matchmaking_world as world
from tests.api.club_courts_world import (
    PAYMENTS_LINK,
    a_desk,
    adds_a_court,
    chooses,
    confirms_settings,
    connects_payments,
    court_path,
    sets_hours,
    sets_prices,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_member,
    every_hour_of_the_week,
    makes,
    says_no,
    says_yes,
    warsaw,
    withdraws,
)
from tests.unit.candidate_index_fixtures import append
from tests.unit.fake_clock import MovableClock

GAMES_AND_MONEY = "/api/v1/players/me/games-and-money"
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
async def crowd(client, session_factory, payments) -> list[dict]:
    """Ola — the reader — and seven others, all at padel 2,5."""

    return [
        await a_member(client, session_factory, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek", "ania", "marek", "zofia", "piotr")
    ]


@pytest.fixture
async def group(client, club, crowd) -> UUID:
    return await a_group(client, crowd[0], club, *crowd[1:])


async def deck_of(
    client,
    player: dict,
    group: UUID,
    *,
    sport: str = "PADEL",
    kind: str = "COMPETITIVE",
) -> dict:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": sport, "kind": kind},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def dealt_ids(client, player: dict, group: UUID, **query) -> list[str]:
    return [
        card["proposal_id"]
        for card in (await deck_of(client, player, group, **query))["cards"]
    ]


def tiles(card: dict) -> list[dict]:
    return [*card["sides"]["yours"], *card["sides"]["theirs"]]


@dataclass
class BookedFor:
    """``BookedGames`` while nothing can be booked: the games a test says each
    player has."""

    games: dict[UUID, list[datetime]] = field(default_factory=dict)

    async def starts_of(self, player_id, *, start, end):
        return [at for at in self.games.get(player_id, []) if start <= at < end]


@pytest.fixture
def booked(app) -> BookedFor:
    stand_in = BookedFor()
    app.dependency_overrides[get_booked_games] = lambda: stand_in
    return stand_in


# --------------------------------------------------------------------------- #
# The card
# --------------------------------------------------------------------------- #


async def test_a_card_is_my_version_of_the_game_with_everything_it_draws(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    assert (await says_yes(client, ewa, proposal)).status_code == 200

    deck = await deck_of(client, ola, group)

    assert deck["pool_id"] == str(group)
    assert deck["segments"] == [{"kind": "COMPETITIVE", "count": 1}]
    assert deck["games_badge"] == 1
    assert deck["games_per_week"] == 2
    assert deck["capped_weeks"] == []
    [card] = deck["cards"]
    assert card["proposal_id"] == str(proposal)
    assert card["type"] == "PICKED_FOR_YOU"
    assert card["kind"] == "COMPETITIVE"
    assert card["challenger"] is None
    assert card["club"] == {"id": club, "name": "Bonarka Arena"}
    assert card["share_grosze"] == 30_00
    assert datetime.fromisoformat(card["starts_at"]) == SATURDAY_FIVE
    # An Instant club: two hours' minimum notice.
    assert datetime.fromisoformat(card["deadline"]) == warsaw(10, 15)
    assert card["in_count"] == 1
    assert card["version_count"] == 1
    assert card["open_seats_after_your_yes"] == 2
    assert card["court"] == "COURT_AVAILABLE"
    assert card["no_free_cancellation"] is False
    assert card["club_confirms"] is False

    assert len(card["sides"]["yours"]) == len(card["sides"]["theirs"]) == 2
    assert card["sides"]["yours"][0]["player_id"] == str(ola["id"])
    by_name = {tile["name"]: tile for tile in tiles(card)}
    assert set(by_name) == {"ola", "kuba", "ewa", "tomek"}
    assert [name for name, tile in by_name.items() if tile["is_you"]] == ["ola"]
    assert [name for name, tile in by_name.items() if tile["is_in"]] == ["ewa"]
    assert {tile["level"] for tile in by_name.values()} == {2.5}
    assert all(
        tile["photo_id"] is None and tile["photo_url"] is None
        for tile in by_name.values()
    )

    assert card["forecast"]["provisional"] is False
    assert 0 < card["forecast"]["pct"] <= 100
    assert card["overlap"]["grade"] == "HIGH"
    assert len(card["overlap"]["cells"]) == 21
    assert {cell["shade"] for cell in card["overlap"]["cells"]} == {"BRIGHT"}
    assert card["overlap"]["game"] == {"day": 6, "range": "EVENING"}


async def test_my_yes_completing_it_says_book_it_now(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    for player in (kuba, ewa, tomek):
        await says_yes(client, player, proposal)

    [card] = (await deck_of(client, ola, group))["cards"]

    assert card["open_seats_after_your_yes"] == 0
    assert card["court"] == "BOOK_IT_NOW"
    assert card["in_count"] == 3


async def test_the_sides_are_the_evenest_arrangement_with_me_on_mine(
    client, session_factory, payments, clock, club
):
    me = await a_member(client, session_factory, payments, "ola", mu=2.5)
    strong = await a_member(client, session_factory, payments, "kuba", mu=2.9)
    level = await a_member(client, session_factory, payments, "ewa", mu=2.5)
    other_strong = await a_member(client, session_factory, payments, "tomek", mu=2.9)
    group = await a_group(client, me, club, strong, level, other_strong)
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((me, level, other_strong, strong),),
    )

    [card] = (await deck_of(client, me, group))["cards"]

    # Ola beside a 2,9 against 2,5 and 2,9 — never the two 2,5s together.
    mine = {tile["name"] for tile in card["sides"]["yours"]}
    assert "ola" in mine and mine & {"kuba", "tomek"}
    theirs = {tile["name"] for tile in card["sides"]["theirs"]}
    assert "ewa" in theirs


async def test_a_last_minute_card_says_no_free_cancellation(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    # Tomorrow at seven: twenty-three hours away, inside the 24-hour cut-off.
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(6, 7),
        versions=((ola, kuba, ewa, tomek),),
    )

    [card] = (await deck_of(client, ola, group))["cards"]

    assert card["no_free_cancellation"] is True


async def test_a_challenge_names_its_poster_until_they_withdraw(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek, ania = crowd[:5]
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=kuba,
        versions=((ola, ewa, tomek),),
    )

    [card] = (await deck_of(client, ola, group))["cards"]
    assert card["type"] == "CHALLENGE"
    assert card["challenger"] == {"player_id": str(kuba["id"]), "name": "kuba"}
    assert [tile["name"] for tile in tiles(card) if tile["is_in"]] == ["kuba"]

    await says_yes(client, ewa, post)
    await withdraws(client, kuba, post)

    [card] = (await deck_of(client, ola, group))["cards"]
    assert card["type"] == "CHALLENGE"
    assert card["challenger"] is None
    assert "kuba" not in {tile["name"] for tile in tiles(card)}


async def test_a_game_dealt_in_versions_counts_the_yeses_on_every_version(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek, ania, marek, zofia = crowd[:7]
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        poster=kuba,
        versions=((ola, ewa, tomek), (ania, marek, zofia)),
    )
    await says_yes(client, marek, post)

    [card] = (await deck_of(client, ola, group))["cards"]

    assert card["version_count"] == 2
    assert card["in_count"] == 2
    # Marek is In on the other version, so he is on mine; one seat is left
    # beside me, and the first of my version's names takes it.
    assert {tile["name"] for tile in tiles(card)} == {"kuba", "marek", "ola", "ewa"}


async def test_at_an_on_request_club_the_card_says_the_club_confirms(
    client, session_factory, clock, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    asks = await a_club_selling(client, name="Ogrody 33", way="ON_REQUEST")
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=asks,
        versions=((ola, kuba, ewa, tomek),),
    )

    [card] = (await deck_of(client, ola, group))["cards"]

    assert card["club_confirms"] is True
    assert card["club"]["name"] == "Ogrody 33"


# --------------------------------------------------------------------------- #
# The order
# --------------------------------------------------------------------------- #


async def test_the_deck_is_ordered_by_momentum_then_type_then_deadline(
    client, session_factory, clock, club, crowd, group
):
    ola, a, b, c, d, e, f, g = crowd

    async def pick(start, named, *yeses):
        proposal = await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            start=start,
            versions=((ola, *named),),
        )
        for player in yeses:
            assert (await says_yes(client, player, proposal)).status_code == 200
        return str(proposal)

    nothing_in = await pick(warsaw(7, 18), (b, e, g))
    one_in_later = await pick(warsaw(9, 19), (c, d, g), c)
    one_in_sooner = await pick(warsaw(6, 19), (b, d, f), b)
    two_in = await pick(warsaw(8, 19), (a, e, g), a, g)
    three_in = await pick(warsaw(11, 18), (a, b, c), a, b, c)
    challenge = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(10, 12),
        poster=d,
        versions=((ola, e, f),),
    )
    await says_yes(client, e, challenge)

    assert await dealt_ids(client, ola, group) == [
        three_in,
        str(challenge),
        two_in,
        one_in_sooner,
        one_in_later,
        nothing_in,
    ]


async def test_at_the_same_momentum_type_and_deadline_the_evener_game_comes_first(
    client, session_factory, payments, clock, club
):
    me = await a_member(client, session_factory, payments, "ola", mu=2.5)
    level = [
        await a_member(client, session_factory, payments, name, mu=2.5)
        for name in ("kuba", "ewa", "tomek")
    ]
    above = [
        await a_member(client, session_factory, payments, name, mu=mu)
        for name, mu in (("ania", 3.0), ("marek", 3.0), ("zofia", 2.95))
    ]
    group = await a_group(client, me, club, *level, *above)
    uneven = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((me, *above),)
    )
    even = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((me, *level),)
    )

    cards = (await deck_of(client, me, group))["cards"]

    assert [card["proposal_id"] for card in cards] == [str(even), str(uneven)]
    assert cards[0]["forecast"]["pct"] > cards[1]["forecast"]["pct"]


async def test_the_same_people_are_dealt_only_at_their_best_hour(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    four = ((ola, kuba, ewa, tomek),)
    saturday = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=four
    )
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 18),
        versions=four,
    )
    await says_yes(client, kuba, sunday)

    deck = await deck_of(client, ola, group)

    assert [card["proposal_id"] for card in deck["cards"]] == [str(sunday)]
    assert deck["segments"] == [{"kind": "COMPETITIVE", "count": 1}]
    # The batch is each reader's own: Kuba is In on Sunday's, which is in his
    # You're In, so Saturday's is his best hour with the same three.
    assert await dealt_ids(client, kuba, group) == [str(saturday)]


async def test_a_no_is_final_a_yes_leaves_the_deck_and_a_withdrawn_yes_returns(
    client, session_factory, clock, club, crowd, group
):
    ola, a, b, c, d, e, f = crowd[:7]
    refused = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((ola, a, b, c),)
    )
    accepted = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 18),
        versions=((ola, d, e, f),),
    )

    await says_no(client, ola, refused)
    await says_yes(client, ola, accepted)
    assert await dealt_ids(client, ola, group) == []

    await withdraws(client, ola, accepted)
    assert await dealt_ids(client, ola, group) == [str(accepted)]


# --------------------------------------------------------------------------- #
# The filters
# --------------------------------------------------------------------------- #


async def test_a_card_with_somebody_in_i_blocked_is_withheld_and_a_name_is_left_off(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek, ania, marek, zofia = crowd[:7]
    kuba_in = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    await says_yes(client, kuba, kuba_in)
    kuba_named = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 18),
        versions=((ola, kuba, ania, marek),),
    )

    blocked = await world.block_between(client, ola["token"], kuba["id"])
    assert blocked.status_code in (200, 201, 204), blocked.text

    [card] = (await deck_of(client, ola, group))["cards"]
    assert card["proposal_id"] == str(kuba_named)
    assert {tile["name"] for tile in tiles(card)} == {"ola", "ania", "marek"}


async def test_a_name_who_blocked_somebody_in_is_left_off_my_card(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    await says_yes(client, kuba, proposal)
    blocked = await world.block_between(client, tomek["token"], kuba["id"])
    assert blocked.status_code in (200, 201, 204), blocked.text

    [card] = (await deck_of(client, ola, group))["cards"]

    assert {tile["name"] for tile in tiles(card)} == {"kuba", "ola", "ewa"}


async def test_a_card_with_somebody_in_my_gender_preference_excludes_is_withheld(
    client, session_factory, payments, clock, club, crowd, group
):
    ola, ewa, tomek = crowd[0], crowd[2], crowd[3]
    jan = await a_member(client, session_factory, payments, "jan", gender="MAN")
    await client.post(f"/api/v1/groups/{group}/membership", headers=jan["headers"])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, jan, ewa, tomek),),
    )
    await says_yes(client, jan, proposal)
    assert await dealt_ids(client, ola, group) == [str(proposal)]

    narrowed = await client.put(
        "/api/v1/players/me/gender-preference",
        json={"gender_preference": "WOMEN_ONLY"},
        headers=ola["headers"],
    )
    assert narrowed.status_code == 204, narrowed.text

    assert await dealt_ids(client, ola, group) == []


async def test_a_card_with_somebody_in_outside_my_level_window_is_withheld(
    client, session_factory, clock, club, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    await says_yes(client, kuba, proposal)

    # Kuba's Level moves on a result, well past the competitive window.
    await append(
        session_factory,
        _moved(kuba["id"], mu=3.6),
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(kuba["id"], Sport.PADEL),
        version=2,
    )

    assert await dealt_ids(client, ola, group) == []


def _moved(player_id: UUID, *, mu: float) -> RatingMovedOnResult:
    return RatingMovedOnResult(
        rating_id=skill_rating_id(player_id, Sport.PADEL),
        player_id=player_id,
        sport=Sport.PADEL.value,
        game_id=uuid4(),
        won=True,
        opposition_mu=mu,
        opposition_sigma=0.3,
        information_share=0.5,
        win_delta=1.1,
        loss_delta=-0.2,
        mu=mu,
        sigma=0.3,
        confidence=70,
        range_low=mu - 0.3,
        range_high=mu + 0.3,
        band_name="Advanced",
        band_lower=3.5,
        band_upper=4.5,
        status="SETTLING",
        engine_version="v3",
        occurred_at=MONDAY_MORNING,
    )


async def test_the_segments_follow_my_intent_and_nobody_is_dealt_before_i_answer(
    client, session_factory, clock, club, crowd, group
):
    ola, a, b, c, d, e, f = crowd[:7]
    competitive = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((ola, a, b, c),)
    )
    for_fun = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 18),
        kind=SearchMode.FOR_FUN,
        versions=((ola, d, e, f),),
    )
    await says_yes(client, d, for_fun)

    # Competitive: the For fun segment is not shown, and its card not dealt.
    deck = await deck_of(client, ola, group, kind="FOR_FUN")
    assert deck["segments"] == [{"kind": "COMPETITIVE", "count": 1}]
    assert deck["cards"] == []
    assert deck["games_badge"] == 0

    # Either: both segments, and the badge counts across them.
    await world.declare_intent(client, ola["token"], intent="NO_PREFERENCE")
    deck = await deck_of(client, ola, group, kind="FOR_FUN")
    assert deck["segments"] == [
        {"kind": "COMPETITIVE", "count": 1},
        {"kind": "FOR_FUN", "count": 1},
    ]
    assert [card["proposal_id"] for card in deck["cards"]] == [str(for_fun)]
    assert deck["games_badge"] == 1
    assert await dealt_ids(client, ola, group) == [str(competitive)]


async def test_a_player_who_has_declared_no_intent_is_dealt_nothing(
    client, session_factory, payments, clock, club, crowd
):
    undecided = await a_member(client, session_factory, payments, "nowy", intent=None)
    ola, kuba, ewa = crowd[:3]
    group = await a_group(client, ola, club, kuba, ewa, undecided)
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((undecided, ola, kuba, ewa),),
    )

    deck = await deck_of(client, undecided, group)

    assert deck["segments"] == []
    assert deck["cards"] == []
    assert deck["games_badge"] == 0


async def test_a_card_above_most_i_ll_pay_is_never_dealt(
    client, session_factory, clock, club, crowd, group
):
    ola, a, b, c, d, e, f = crowd[:7]
    pricey = await a_club_selling(client, name="Pricey Padel", padel_grosze=200_00)
    cheap_card = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((ola, a, b, c),)
    )
    pricey_card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=pricey,
        start=warsaw(11, 18),
        versions=((ola, d, e, f),),
    )

    saved = await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 2, "most_ill_pay_grosze": 45_00},
        headers=ola["headers"],
    )
    assert saved.status_code == 200, saved.text
    assert await dealt_ids(client, ola, group) == [str(cheap_card)]

    await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 2, "most_ill_pay_grosze": None},
        headers=ola["headers"],
    )
    assert set(await dealt_ids(client, ola, group)) == {
        str(cheap_card),
        str(pricey_card),
    }


async def test_a_week_at_my_games_per_week_is_not_dealt_and_the_read_says_so(
    client, session_factory, clock, club, crowd, group, booked
):
    ola, a, b, c, d, e, f = crowd[:7]
    this_week = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((ola, a, b, c),)
    )
    next_week = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(17, 17),
        versions=((ola, d, e, f),),
    )
    booked.games[ola["id"]] = [warsaw(6, 19), warsaw(7, 19)]

    deck = await deck_of(client, ola, group)

    assert [card["proposal_id"] for card in deck["cards"]] == [str(next_week)]
    assert deck["capped_weeks"] == [{"starts_on": "2026-10-05", "booked": 2}]
    assert deck["segments"] == [{"kind": "COMPETITIVE", "count": 1}]

    await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 3, "most_ill_pay_grosze": None},
        headers=ola["headers"],
    )

    deck = await deck_of(client, ola, group)
    assert deck["capped_weeks"] == []
    assert deck["games_per_week"] == 3
    assert [card["proposal_id"] for card in deck["cards"]] == [
        str(this_week),
        str(next_week),
    ]


async def test_an_hour_i_already_have_a_game_at_is_not_dealt(
    client, session_factory, clock, club, crowd, group, booked
):
    ola, a, b, c, d, e, f = crowd[:7]
    await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=((ola, a, b, c),)
    )
    later = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(10, 19),
        versions=((ola, d, e, f),),
    )
    booked.games[ola["id"]] = [SATURDAY_FIVE]

    assert await dealt_ids(client, ola, group) == [str(later)]


async def test_a_club_that_stops_selling_deals_nothing_more(
    client, session_factory, clock, crowd, group
):
    ola, kuba, ewa, tomek = crowd[:4]
    club_id, desk = await a_desk(
        client, name="Wisla Park", email="desk@wisla.pl", sports=("PADEL",)
    )
    await chooses(client, desk, "INSTANT")
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], every_hour_of_the_week())
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )
    await confirms_settings(client, desk)
    await connects_payments(client, desk)
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club_id,
        versions=((ola, kuba, ewa, tomek),),
    )
    assert len(await dealt_ids(client, ola, group)) == 1

    # Its only court switched off: the club is no longer live.
    switched = await client.put(
        court_path(court["id"]),
        json={"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": False},
        headers=desk,
    )
    assert switched.status_code == 200, switched.text

    assert await dealt_ids(client, ola, group) == []


async def test_a_club_whose_payments_stop_deals_nothing_more(
    client, session_factory, clock, crowd, group, payments
):
    """**Not live, not paused** (#537): a club the provider stops taking
    payments for is off the decks until it answers — its cards still filling
    included, since a fill could charge nobody on its account."""

    ola, kuba, ewa, tomek = crowd[:4]
    club_id, desk = await a_desk(
        client, name="Wisla Park", email="desk@wisla.pl", sports=("PADEL",)
    )
    await chooses(client, desk, "INSTANT")
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], every_hour_of_the_week())
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )
    await confirms_settings(client, desk)
    await connects_payments(client, desk)
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club_id,
        versions=((ola, kuba, ewa, tomek),),
    )
    assert len(await dealt_ids(client, ola, group)) == 1

    # The provider wants more; the desk's *Continue with Stripe* reads it.
    account = payments.account_opened_for(UUID(club_id))
    payments.club_account_is(account, ClubAccountStatus.NEEDS_DETAILS)
    linked = await client.post(PAYMENTS_LINK, headers=desk)
    assert linked.status_code == 200, linked.text

    assert await dealt_ids(client, ola, group) == []


# --------------------------------------------------------------------------- #
# Who may read it
# --------------------------------------------------------------------------- #


async def test_a_stranger_and_a_group_that_does_not_exist_are_one_answer(
    client, session_factory, payments, clock, club, crowd, group
):
    stranger = await a_member(client, session_factory, payments, "obcy")

    not_mine = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=stranger["headers"],
    )
    nowhere = await client.get(
        f"/api/v1/pools/{uuid4()}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=stranger["headers"],
    )

    assert not_mine.status_code == nowhere.status_code == 404
    assert not_mine.json()["code"] == nowhere.json()["code"] == "pool_not_found"


async def test_a_member_with_nothing_dealt_reads_an_empty_deck(
    client, clock, crowd, group
):
    deck = await deck_of(client, crowd[1], group)

    assert deck["cards"] == []
    assert deck["segments"] == [{"kind": "COMPETITIVE", "count": 0}]
    assert deck["games_badge"] == 0


async def test_the_deck_asks_for_a_session(client, group):
    read = await client.get(
        f"/api/v1/pools/{group}/deck", params={"sport": "PADEL", "kind": "COMPETITIVE"}
    )

    assert read.status_code == 401
