"""**A game's details follow its kind** (#833; ``docs/adr/0207`` §5, §6, §12).

- **For fun** answers the table's Social vibe — the card's own number — and the
  grid's rows: **the reader's tags**, in the vocabulary's order, 💘 included,
  each with everybody at the table who carries it, the reader first. No
  forecast, and nothing at stake.
- **Competitive** answers the full forecast — each side's level and the signed
  gap beside the % — and **what is at stake for the reader**: priced by the
  very function a booked game's pairing prices its stakes with, on the reader's
  version's evenest sides, so the stakes seen before a yes are the stakes that
  apply once the game is booked. Two values or none, in singles too. No vibe.

Every player is made the way the platform makes one, their tags committed
through the profile and heard by the player directory through the outbox; every
card is made the way the proposer makes one (``MakeProposal``), and answered
and read over HTTP.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_member,
    makes,
    says_yes,
)
from tests.unit.fake_clock import MovableClock

DRINK, LAUGHS, MEET = "STAYS_FOR_A_DRINK", "LAUGHS_OFF_MISTAKES", "HERE_TO_MEET_PLAYERS"
#: 💘 — a row like any other in the grid, and never counted.
SOMEONE = "OPEN_TO_MEET_SOMEONE"
NEW_IN_TOWN = "NEW_IN_TOWN"
QUIET, HOME = "QUIET_AND_FOCUSED", "STRAIGHT_HOME_AFTER"

#: Ola's tags, handed to the picker out of the vocabulary's order.
OLAS_TAGS = (NEW_IN_TOWN, SOMEONE, MEET, LAUGHS, DRINK)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


async def details_of(client, player: dict, proposal_id: UUID) -> dict:
    read = await client.get(
        f"/api/v1/proposals/{proposal_id}", headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    return read.json()


async def card_on_the_deck(client, player: dict, group: UUID, proposal_id: UUID):
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "FOR_FUN"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return next(
        card for card in read.json()["cards"] if card["proposal_id"] == str(proposal_id)
    )


def tile_order(details: dict) -> list[str]:
    """Everybody drawn, in the tiles' order: the reader first, on their side."""

    return [
        tile["player_id"]
        for tile in (*details["sides"]["yours"], *details["sides"]["theirs"])
    ]


async def fills(client, proposal_id: UUID, *players: dict) -> dict:
    """Each of ``players`` says yes in turn; the last yes books it."""

    for player in players:
        said = await says_yes(client, player, proposal_id)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    assert booked is not None, said.text
    return booked


async def pairing_of(client, player: dict, game_id: str) -> dict:
    read = await client.get(
        f"/api/v1/games/{game_id}/pairing", headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    return read.json()


# --------------------------------------------------------------------------- #
# For fun: the Social vibe and its grid
# --------------------------------------------------------------------------- #


@pytest.fixture
async def a_friendly(client, session_factory, payments, clock, club, mailbox) -> dict:
    """Ola's For-fun card with Ania, Marek and Zofia, nobody In yet.

    Counted, 💘 aside: Ola {drink, laughs, meet, new in town}, Ania {drink},
    Marek {laughs, meet}, Zofia {quiet, home}. Each of Ola's first three is
    carried by one of the other three, Ania's drink by one, Marek's two by one
    each, and nothing else by anybody: (1 + ⅓ + ⅔ + 0) over 9 carryings is 22%.
    """

    tags = {
        "ola": OLAS_TAGS,
        "ania": (SOMEONE, DRINK),
        "marek": (LAUGHS, MEET),
        "zofia": (QUIET, HOME),
    }
    crowd = {
        name: await a_member(
            client, session_factory, payments, name, intent="FOR_FUN", tags=held
        )
        for name, held in tags.items()
    }
    group = await a_group(
        client, crowd["ola"], club, *(p for n, p in crowd.items() if n != "ola")
    )
    card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        kind=SearchMode.FOR_FUN,
        versions=(tuple(crowd[n] for n in ("ola", "ania", "marek", "zofia")),),
    )
    await mailbox.drain()
    return {"crowd": crowd, "group": group, "card": card}


async def test_for_fun_details_answer_the_readers_tags_and_who_carries_each(
    client, a_friendly
):
    crowd = a_friendly["crowd"]
    ola = crowd["ola"]

    details = await details_of(client, ola, a_friendly["card"])

    ids = {name: str(player["id"]) for name, player in crowd.items()}
    order = tile_order(details)
    assert order[0] == ids["ola"]

    def carried_by(*names: str) -> list[str]:
        """Who carries a tag, in the tiles' order — the reader first."""

        return [player for player in order if player in {ids[n] for n in names}]

    vibe = details["vibe"]
    # Her own tags only — none of Zofia's — in the vocabulary's order, 💘 too.
    assert [row["tag"] for row in vibe["rows"]] == [
        DRINK,
        LAUGHS,
        MEET,
        SOMEONE,
        NEW_IN_TOWN,
    ]
    assert [row["carried_by"] for row in vibe["rows"]] == [
        carried_by("ola", "ania"),
        carried_by("ola", "marek"),
        carried_by("ola", "marek"),
        carried_by("ola", "ania"),
        [ids["ola"]],
    ]
    assert vibe["pct"] == 22


async def test_the_for_fun_details_vibe_is_the_card_s(client, a_friendly):
    """The % swiped on is the % looked at — on the reader's deck and in the
    details, for the same version."""

    ola = a_friendly["crowd"]["ola"]

    card = await card_on_the_deck(client, ola, a_friendly["group"], a_friendly["card"])
    details = await details_of(client, ola, a_friendly["card"])

    assert details["vibe"]["pct"] == card["vibe"]["pct"] == 22


async def test_for_fun_details_say_no_forecast_and_nothing_at_stake(client, a_friendly):
    details = await details_of(client, a_friendly["crowd"]["ola"], a_friendly["card"])

    assert details["forecast"] is None
    assert details["at_stake"] is None


async def test_the_rows_follow_the_readers_tags_now(client, a_friendly, mailbox):
    """Stored nowhere: Zofia picks up Ola's drink, and the drink's row names
    her on the next read."""

    crowd = a_friendly["crowd"]
    changed = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": [DRINK, QUIET]},
        headers=crowd["zofia"]["headers"],
    )
    assert changed.status_code == 200, changed.text
    await mailbox.drain()

    details = await details_of(client, crowd["ola"], a_friendly["card"])

    drink = next(row for row in details["vibe"]["rows"] if row["tag"] == DRINK)
    assert set(drink["carried_by"]) == {
        str(crowd[name]["id"]) for name in ("ola", "ania", "zofia")
    }


# --------------------------------------------------------------------------- #
# Competitive: the full forecast, and what is at stake
# --------------------------------------------------------------------------- #


@pytest.fixture
async def a_counted_game(client, session_factory, payments, clock, club, mailbox):
    """Ola's competitive card with Kuba, Ewa and Tomek, nobody In — four
    Levels far enough apart that one way of standing is the evenest, and close
    enough that every pair fits."""

    levels = {"ola": 2.2, "kuba": 2.4, "ewa": 2.6, "tomek": 2.7}
    crowd = {
        name: await a_member(client, session_factory, payments, name, mu=mu)
        for name, mu in levels.items()
    }
    group = await a_group(
        client, crowd["ola"], club, *(p for n, p in crowd.items() if n != "ola")
    )
    card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SATURDAY_FIVE,
        versions=(tuple(crowd[n] for n in ("ola", "kuba", "ewa", "tomek")),),
    )
    await mailbox.drain()
    return {"crowd": crowd, "group": group, "card": card}


async def test_competitive_details_answer_each_side_s_level_and_the_signed_gap(
    client, a_counted_game
):
    details = await details_of(
        client, a_counted_game["crowd"]["ola"], a_counted_game["card"]
    )

    forecast = details["forecast"]
    assert set(forecast) >= {"pct", "provisional", "your_side", "their_side", "gap"}
    assert forecast["provisional"] is False
    assert forecast["gap"] == pytest.approx(
        forecast["your_side"] - forecast["their_side"]
    )
    assert forecast["your_side"] != forecast["their_side"]


async def test_the_stakes_seen_before_the_yes_are_the_booked_game_s(
    client, a_counted_game
):
    """**Fill the game and read its pairing: the stakes are equal**, and so are
    the levels and the gap — one function before the yes and after it."""

    crowd = a_counted_game["crowd"]
    ola = crowd["ola"]
    before = await details_of(client, ola, a_counted_game["card"])

    booked = await fills(
        client,
        a_counted_game["card"],
        *(crowd[n] for n in ("kuba", "ewa", "tomek", "ola")),
    )
    pairing = await pairing_of(client, ola, booked["game_id"])

    assert before["at_stake"] == pairing["at_stake"]
    assert before["at_stake"]["win_delta"] > 0 > before["at_stake"]["loss_delta"]
    assert {
        "your_side": before["forecast"]["your_side"],
        "their_side": before["forecast"]["their_side"],
        "gap": before["forecast"]["gap"],
    } == pairing["split"]
    assert before["forecast"]["pct"] == pairing["forecast"]["pct"]


async def test_competitive_details_carry_no_vibe(client, a_counted_game):
    details = await details_of(
        client, a_counted_game["crowd"]["ola"], a_counted_game["card"]
    )

    assert details["vibe"] is None


async def test_nothing_is_at_stake_while_a_seat_is_open(client, a_counted_game):
    """Two values or none, as on a booked game: a reader In on a game still
    two short reads no stakes, since the court that will play is not yet known
    (``docs/adr/0162``)."""

    crowd = a_counted_game["crowd"]
    for player in (crowd["kuba"], crowd["ola"]):
        said = await says_yes(client, player, a_counted_game["card"])
        assert said.status_code == 200, said.text

    details = await details_of(client, crowd["ola"], a_counted_game["card"])

    assert details["at_stake"] is None


async def test_a_reader_who_said_no_reads_nothing_at_stake(client, a_counted_game):
    """Three In and Ola's *Not this time*: her details still seat her beside
    them, but the game is no longer hers to play, so nothing is at stake for
    her — the court that plays will be somebody else's four."""

    crowd = a_counted_game["crowd"]
    for player in (crowd["kuba"], crowd["ewa"], crowd["tomek"]):
        said = await says_yes(client, player, a_counted_game["card"])
        assert said.status_code == 200, said.text
    declined = await client.post(
        f"/api/v1/proposals/{a_counted_game['card']}/no",
        headers=crowd["ola"]["headers"],
    )
    assert declined.status_code in (200, 204), declined.text

    details = await details_of(client, crowd["ola"], a_counted_game["card"])

    assert details["actions"] == []
    assert details["at_stake"] is None


async def test_once_booked_the_stakes_are_the_booking_s_to_say(client, a_counted_game):
    """A filled game's stakes are its pairing's (``GET /games/{id}/pairing``):
    its court can change after the fill — a leaver, a rescue — and the
    proposal's yeses do not follow it."""

    crowd = a_counted_game["crowd"]
    await fills(
        client,
        a_counted_game["card"],
        *(crowd[n] for n in ("kuba", "ewa", "tomek", "ola")),
    )

    details = await details_of(client, crowd["ola"], a_counted_game["card"])

    assert details["status"] == "FILLED"
    assert details["at_stake"] is None


async def test_singles_details_answer_the_stakes_too(
    client, session_factory, payments, clock, club, mailbox
):
    """Tennis, one a side: the version names both players, so the stakes are
    priced — and are the booked game's."""

    ola = await a_member(
        client, session_factory, payments, "ola", mu=2.3, sports=(Sport.TENNIS,)
    )
    kuba = await a_member(
        client, session_factory, payments, "kuba", mu=2.7, sports=(Sport.TENNIS,)
    )
    group = await a_group(client, ola, club, kuba)
    card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        sport=Sport.TENNIS,
        versions=((ola, kuba),),
    )
    await mailbox.drain()

    before = await details_of(client, ola, card)
    booked = await fills(client, card, kuba, ola)
    pairing = await pairing_of(client, ola, booked["game_id"])

    assert before["at_stake"] is not None
    assert before["at_stake"] == pairing["at_stake"]
    assert before["forecast"]["gap"] == pytest.approx(pairing["split"]["gap"])
    assert before["vibe"] is None
