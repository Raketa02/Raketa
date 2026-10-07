"""What the games test console's tests press and read (#590, #591;
``docs/adr/0194``).

**A press is made the way the page makes it** — a request to the dev surface,
with no token — **and read back the way somebody would read it**: through the
player surface as the protagonist's phone does, or through the club surface as
the desk does. A situation is proven by what she sees, never by the rows it
wrote.
"""

from __future__ import annotations

from uuid import UUID

from app.seeds.catalog import SEED_EMAIL_DOMAIN

#: Where the seed addresses its accounts — an account here is one the console
#: may act as.
SEED = SEED_EMAIL_DOMAIN

PLAYER = "the player's own route"
CLUB = "the club's own route"
CONSOLE = "the console's row"


def code_of(response) -> str:
    return response.json()["code"]


def at(moment) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def ids(people: list[dict]) -> set[str]:
    return {person["player_id"] for person in people}


# --------------------------------------------------------------------------- #
# A person's buttons
# --------------------------------------------------------------------------- #


async def says(client, via: str, verb: str, member: dict, game: UUID):
    """``verb`` — ``yes``, ``no`` or ``withdraw`` — said as ``member``: by their
    own phone, or by the console's row, which holds no token."""

    method, tail = {
        "yes": ("POST", "yes"),
        "no": ("POST", "no"),
        "withdraw": ("DELETE", "yes"),
    }[verb]
    if via == PLAYER:
        return await client.request(
            method,
            f"/api/v1/proposals/{game}/{tail}",
            headers=member["headers"],
        )
    return await client.request(
        method, f"/dev/as/{member['id']}/proposals/{game}/{tail}"
    )


# --------------------------------------------------------------------------- #
# What the phone reads
# --------------------------------------------------------------------------- #


async def deck_of(client, member: dict, group: UUID) -> list[dict]:
    """Their Games tab, as their own phone reads it."""

    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=member["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


async def deck_ids(client, member: dict, group: UUID) -> list[str]:
    return [card["proposal_id"] for card in await deck_of(client, member, group)]


async def home_of(client, member: dict) -> list[dict]:
    """Their Home's games, as their own phone reads it."""

    read = await client.get("/api/v1/home", headers=member["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def receipts_of(client, member: dict) -> list[dict]:
    """You › Payments' receipts, as their own phone reads it."""

    read = await client.get("/api/v1/players/me/receipts", headers=member["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


# --------------------------------------------------------------------------- #
# What the console reads, and its situations
# --------------------------------------------------------------------------- #


async def board_of(client, group: UUID, sport: str = "PADEL") -> dict:
    read = await client.get(f"/dev/groups/{group}", params={"sport": sport})
    assert read.status_code == 200, read.text
    return read.json()


def rows_of(board: dict) -> dict[str, dict]:
    return {row["name"]: row for row in board["people"]}


def pane_of(board: dict, game: UUID) -> dict:
    [pane] = [pane for pane in board["games"] if pane["game_id"] == str(game)]
    return pane


async def presses(client, situation: str, **body):
    return await client.post(
        f"/dev/situations/{situation}",
        json={
            key: value if isinstance(value, int) else str(value)
            for key, value in body.items()
        },
    )
