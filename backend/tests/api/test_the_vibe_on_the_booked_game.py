"""**A booked For-fun game's pairing carries its Social vibe** (#835;
``docs/adr/0207`` §5, §6, §12).

``GET /games/{id}/pairing`` is what the booked game screen and the game at the
court draw their top card from. On a For-fun game — a ``FRIENDLY`` one — it
gains ``vibe {pct, rows[{tag, carried_by}]}``: the table's Social vibe, the
number the card and the details showed, and one row for each of **the
reader's** tags in the vocabulary's order, 💘 included, each naming everybody
on the court who carries it, the reader first. So a For-fun game reads the
same before and after it is booked.

- **Worked out live** from everybody's tags now, read off the player directory
  in one statement, and stored nowhere: a tag edit moves it on the next read.
- **Answered on the same occasions as the pairing today, and no wider**: only
  for somebody on the court, only while the game waits for its entry, and —
  like the forecast — not while a seat is open, since the court that will play
  is not yet known (``docs/adr/0162`` §3).
- **The forecast is still sent on For fun**, for the apps already on phones;
  the new app ignores it.
- **Competitive is unchanged**, the stakes included: no vibe, and no tags read.

Every player is made the way the platform makes one, their tags committed
through the profile and heard by the player directory through the outbox; each
card is made as the proposer makes one and filled by yeses over HTTP.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the games are on
Saturday.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.engines.matchfit.core import SearchMode
from app.modules.games.domain.lineup import GameKind
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
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

#: Counted, 💘 aside: Ola {drink, laughs, meet, new in town}, Ania {drink},
#: Marek {laughs, meet}, Zofia {quiet, home}. Each of Ola's first three is
#: carried by one of the other three, Ania's drink by one, Marek's two by one
#: each, and nothing else by anybody: (1 + ⅓ + ⅔ + 0) over 9 carryings is 22%.
TAGS = {
    "ola": (NEW_IN_TOWN, SOMEONE, MEET, LAUGHS, DRINK),
    "ania": (SOMEONE, DRINK),
    "marek": (LAUGHS, MEET),
    "zofia": (QUIET, HOME),
}
FOUR = ("ola", "ania", "marek", "zofia")


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


async def _the_four(client, session_factory, payments, club, *, intent: str):
    crowd = {
        name: await a_member(
            client, session_factory, payments, name, intent=intent, tags=TAGS[name]
        )
        for name in FOUR
    }
    group = await a_group(
        client, crowd["ola"], club, *(crowd[name] for name in FOUR[1:])
    )
    return crowd, group


def _ola_last(crowd: dict) -> list[dict]:
    """The four in the order they say yes: Ola's yes books it."""

    return [*(crowd[name] for name in FOUR[1:]), crowd["ola"]]


async def _fills(client, proposal_id: UUID, *players: dict) -> dict:
    """Each of ``players`` says yes in turn; the last yes books it."""

    for player in players:
        said = await says_yes(client, player, proposal_id)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    assert booked is not None, said.text
    return booked


async def details_of(client, player: dict, proposal_id: UUID) -> dict:
    read = await client.get(
        f"/api/v1/proposals/{proposal_id}", headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    return read.json()


async def _pairing(client, player: dict, game_id: str):
    return await client.get(
        f"/api/v1/games/{game_id}/pairing", headers=player["headers"]
    )


async def pairing_of(client, player: dict, game_id: str) -> dict:
    read = await _pairing(client, player, game_id)
    assert read.status_code == 200, read.text
    return read.json()


@pytest.fixture
async def a_friendly(client, session_factory, payments, clock, club, mailbox) -> dict:
    """Ola's For-fun card with Ania, Marek and Zofia, read before anybody says
    yes, then filled — its booked game's id beside it."""

    crowd, group = await _the_four(
        client, session_factory, payments, club, intent="FOR_FUN"
    )
    card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        kind=SearchMode.FOR_FUN,
        versions=(tuple(crowd[name] for name in FOUR),),
    )
    await mailbox.drain()
    before = await details_of(client, crowd["ola"], card)
    booked = await _fills(client, card, *_ola_last(crowd))
    await mailbox.drain()
    return {
        "crowd": crowd,
        "card": card,
        "details": before,
        "booking_id": booked["booking_id"],
        "game_id": booked["game_id"],
    }


def _ids(crowd: dict) -> dict[str, str]:
    return {name: str(player["id"]) for name, player in crowd.items()}


async def in_the_readers_direction(client, reader: dict, game_id: str) -> list[str]:
    """The court as the pairing names a row's carriers: the reader, the rest of
    their side, then the other side — each side in the order ``GET /games``
    lists the game's seats in."""

    read = await client.get("/api/v1/games", headers=reader["headers"])
    assert read.status_code == 200, read.text
    [game] = [one for one in read.json()["games"] if one["game_id"] == str(game_id)]
    me = str(reader["id"])
    seats = game["seats"]
    mine = next(seat["side"] for seat in seats if seat["player_id"] == me)
    return [
        me,
        *(s["player_id"] for s in seats if s["side"] == mine and s["player_id"] != me),
        *(s["player_id"] for s in seats if s["side"] != mine),
    ]


def _carried_by(court: list[str], carriers: set[str]) -> list[str]:
    """Who carries a tag, in ``court``'s order — its reader first, always."""

    return [player for player in court if player == court[0] or player in carriers]


# --------------------------------------------------------------------------- #
# For fun: the Social vibe and its rows
# --------------------------------------------------------------------------- #


async def test_a_for_fun_game_s_pairing_carries_the_vibe_and_the_reader_s_rows(
    client, a_friendly
):
    crowd = a_friendly["crowd"]
    ids = _ids(crowd)

    body = await pairing_of(client, crowd["ola"], a_friendly["game_id"])

    vibe = body["vibe"]
    assert vibe["pct"] == 22
    # Her own tags only — none of Zofia's — in the vocabulary's order, 💘 too.
    assert [row["tag"] for row in vibe["rows"]] == [
        DRINK,
        LAUGHS,
        MEET,
        SOMEONE,
        NEW_IN_TOWN,
    ]
    court = await in_the_readers_direction(client, crowd["ola"], a_friendly["game_id"])
    assert [row["carried_by"] for row in vibe["rows"]] == [
        _carried_by(court, {ids["ania"]}),
        _carried_by(court, {ids["marek"]}),
        _carried_by(court, {ids["marek"]}),
        _carried_by(court, {ids["ania"]}),
        [ids["ola"]],
    ]


async def test_each_reader_reads_their_own_rows_and_one_number(client, a_friendly):
    """The number is a fact about the table; the rows are the reader's."""

    crowd = a_friendly["crowd"]
    zofia = _ids(crowd)["zofia"]

    body = await pairing_of(client, crowd["zofia"], a_friendly["game_id"])

    # The vocabulary's order, not the picker's: *Straight home after* first.
    assert body["vibe"] == {
        "pct": 22,
        "rows": [
            {"tag": HOME, "carried_by": [zofia]},
            {"tag": QUIET, "carried_by": [zofia]},
        ],
    }


async def test_a_for_fun_game_reads_the_same_before_and_after_it_is_booked(
    client, a_friendly
):
    """The % and the rows the details showed before the last yes are the
    booked game's — one engine function, one rule for the rows, the carriers
    named in the reader's direction on both. Each of Ola's rows is carried by
    her and at most one other, so here the two read alike to the last id."""

    before = a_friendly["details"]["vibe"]
    after = (
        await pairing_of(client, a_friendly["crowd"]["ola"], a_friendly["game_id"])
    )["vibe"]

    assert after == before


async def test_the_forecast_is_still_sent_on_for_fun_for_older_apps(client, a_friendly):
    """An app already on a phone reads the forecast on every booked game, so it
    keeps coming; the new app draws the vibe in its place. A friendly still
    prices nothing."""

    body = await pairing_of(client, a_friendly["crowd"]["ola"], a_friendly["game_id"])

    assert set(body) == {"read_at", "seats", "forecast", "split", "vibe"}
    assert 0 <= body["forecast"]["pct"] <= 100
    assert len(body["seats"]) == 4


async def test_a_tag_edit_moves_the_vibe_on_the_next_read(client, a_friendly, mailbox):
    """Stored nowhere: Zofia swaps *Straight home after* for Ola's *Stays for a
    drink*, and the drink's row names her on the next read — and the number
    moves: (4/3 + 2/3 + 2/3 + 2/3) over 9 carryings is 37%."""

    crowd = a_friendly["crowd"]
    ids = _ids(crowd)
    changed = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": [DRINK, QUIET]},
        headers=crowd["zofia"]["headers"],
    )
    assert changed.status_code == 200, changed.text
    await mailbox.drain()

    body = await pairing_of(client, crowd["ola"], a_friendly["game_id"])

    assert body["vibe"]["pct"] == 37
    drink = next(row for row in body["vibe"]["rows"] if row["tag"] == DRINK)
    court = await in_the_readers_direction(client, crowd["ola"], a_friendly["game_id"])
    assert drink["carried_by"] == _carried_by(court, {ids["ania"], ids["zofia"]})


async def test_the_tags_are_one_statement_on_the_court(client, a_friendly, statements):
    with statements.counting() as sent:
        await pairing_of(client, a_friendly["crowd"]["ola"], a_friendly["game_id"])

    assert len(sent.naming("discovery_player_tags")) == 1


# --------------------------------------------------------------------------- #
# The same occasions as today, and no wider
# --------------------------------------------------------------------------- #


async def test_no_vibe_while_a_seat_is_open_and_the_leaver_reads_nothing(
    client, a_friendly
):
    """A court somebody has left is not yet the one that will play, so it draws
    its Levels and nothing else — neither a forecast nor a vibe
    (``docs/adr/0162`` §3). The leaver is told what a stranger is told."""

    crowd = a_friendly["crowd"]
    left = await client.post(
        f"/api/v1/bookings/{a_friendly['booking_id']}/departure",
        headers=crowd["marek"]["headers"],
    )
    assert left.status_code == 200, left.text

    body = await pairing_of(client, crowd["ola"], a_friendly["game_id"])

    assert set(body) == {"read_at", "seats"}
    gone = await _pairing(client, crowd["marek"], a_friendly["game_id"])
    assert gone.status_code == 404, gone.text


async def test_nobody_off_the_court_reads_the_vibe(
    client, session_factory, payments, a_friendly
):
    stranger = await a_member(
        client,
        session_factory,
        payments,
        "stranger",
        intent="FOR_FUN",
        tags=TAGS["ola"],
    )

    read = await _pairing(client, stranger, a_friendly["game_id"])

    assert read.status_code == 404, read.text
    assert read.json()["code"] == "game_not_found"


async def test_an_unrated_seat_costs_the_forecast_and_never_the_vibe(
    client, session_factory, mailbox
):
    """The vibe is read beside the pairing and never from it: a seat nobody
    rated leaves the forecast nothing to stand on, and the tags are still the
    tags. Everybody holds the profile commit's own two, so the court shares
    all of them."""

    me, partner, left = [
        await players.a_rated_player(client, name) for name in ("me", "partner", "left")
    ]
    unrated_id, unrated = await players.register(client, "unrated")
    await players.commit_profile(client, unrated)
    booked = await players.a_booked_game(
        session_factory,
        side_a=(me["id"], partner["id"]),
        side_b=(left["id"], unrated_id),
        kind=GameKind.FRIENDLY,
        starts_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    await mailbox.drain()

    read = await client.get(
        f"/api/v1/games/{booked['game_id']}/pairing",
        headers=players.auth(me["token"]),
    )

    assert read.status_code == 200, read.text
    body = read.json()
    assert set(body) == {"read_at", "seats", "vibe"}
    everybody = str(me["id"]), str(partner["id"]), str(left["id"]), str(unrated_id)
    assert body["vibe"]["pct"] == 100
    assert [row["tag"] for row in body["vibe"]["rows"]] == [
        "PLAYS_TO_WIN",
        "HERE_TO_IMPROVE",
    ]
    for row in body["vibe"]["rows"]:
        assert row["carried_by"][0] == str(me["id"])
        assert set(row["carried_by"]) == set(everybody)


# --------------------------------------------------------------------------- #
# Competitive: unchanged
# --------------------------------------------------------------------------- #


async def test_a_competitive_game_s_pairing_is_unchanged_and_reads_no_tags(
    client, session_factory, payments, clock, club, mailbox, statements
):
    """The same four with the same tags, heard by the directory — so the
    absence is the kind's, not the data's: the forecast, the split and what is
    at stake, as today, and no vibe."""

    crowd, group = await _the_four(
        client, session_factory, payments, club, intent="COMPETITIVE"
    )
    card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(crowd[name] for name in FOUR),),
    )
    booked = await _fills(client, card, *_ola_last(crowd))
    await mailbox.drain()

    with statements.counting() as sent:
        body = await pairing_of(client, crowd["ola"], booked["game_id"])

    assert set(body) == {"read_at", "seats", "forecast", "split", "at_stake"}
    assert body["at_stake"]["win_delta"] > 0 > body["at_stake"]["loss_delta"]
    assert len(body["seats"]) == 4
    assert sent.naming("discovery_player_tags") == []
