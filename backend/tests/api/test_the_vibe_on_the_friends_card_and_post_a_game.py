"""**The Friends card and Post a game's best fits say their kind's own number**
(#834; ``docs/adr/0207`` §5, §12).

- **The Friends card** on For fun answers the Social vibe of the line-up as it
  would stand — the reader and the friends seated — and no forecast; on
  Competitive the forecast, as before, and no vibe. Its sides are the evenest
  either way: the forecast still arranges a friendly, it is only not said.
- **Post a game's best fits** on a For-fun post each carry the Social vibe of
  **the poster and that player**, and are **ranked by it**, highest first, a tie
  falling to today's order — the forecast, then the pool's; no forecast is
  sent. A competitive post's fits are unchanged: the forecast, most even first,
  and no vibe.

Every player is made the way the platform makes one, their tags committed
through the profile and heard by the player directory through the outbox
(``mailbox.drain()``), and every read is the phone's, over HTTP.

**Ola** (2,50) is in a group at Bonarka Arena with **Zofia** (2,50), **Kuba**
(2,60), **Marek** (2,90) and **Ania** (3,00), all four her friends and every one
of them happy with either kind of game. Counted, 💘 aside:

- Ola {drink, laughs, meet, new in town}, 💘 too;
- Ania {drink, laughs, meet}, 💘 too — three shared with Ola: 6/7, **86%**;
- Kuba {drink, straight home} — one shared: 2/6, **33%**;
- Marek {drink, quiet} — one shared: 2/6, **33%**;
- Zofia {quiet, straight home} — nothing shared with Ola: **0%**.

So the order her fits' vibes put them in runs against the order their levels
do: Ania is the best company and the least even game. Ola and Ania play tennis
too, where a friends card seats one friend.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the tenth is a
Saturday.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.api.dependencies import get_clock
from app.kernel import Sport
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
)
from tests.api.test_friends_on_every_face import befriend
from tests.unit.fake_clock import MovableClock

DRINK, LAUGHS, MEET = "STAYS_FOR_A_DRINK", "LAUGHS_OFF_MISTAKES", "HERE_TO_MEET_PLAYERS"
NEW_IN_TOWN, QUIET, HOME = "NEW_IN_TOWN", "QUIET_AND_FOCUSED", "STRAIGHT_HOME_AFTER"
#: 💘 — held by Ola and Ania, and never counted.
SOMEONE = "OPEN_TO_MEET_SOMEONE"

SATURDAY = date(2026, 10, 10)

#: Each player's Level and tags, in the order they join the group.
CROWD = {
    "ola": (2.5, (NEW_IN_TOWN, SOMEONE, MEET, LAUGHS, DRINK)),
    "marek": (2.9, (DRINK, QUIET)),
    "zofia": (2.5, (QUIET, HOME)),
    "ania": (3.0, (SOMEONE, DRINK, LAUGHS, MEET)),
    "kuba": (2.6, (DRINK, HOME)),
}

#: The Social vibe of Ola and each of them.
WITH_OLA = {"ania": 86, "kuba": 33, "marek": 33, "zofia": 0}

#: Ola and Ania play tennis too, which seats one friend.
SINGLES_TOO = (Sport.PADEL, Sport.TENNIS)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def crowd(client, session_factory, payments, clock, mailbox) -> dict:
    """Ola's group, everybody in it her friend and their tags in the
    directory."""

    club = await a_club_selling(client)
    people = {
        name: await a_member(
            client,
            session_factory,
            payments,
            name,
            mu=mu,
            sports=SINGLES_TOO if name in ("ola", "ania") else (Sport.PADEL,),
            intent="NO_PREFERENCE",
            tags=tags,
        )
        for name, (mu, tags) in CROWD.items()
    }
    ola = people["ola"]
    group = await a_group(
        client, ola, club, *(people[name] for name in CROWD if name != "ola")
    )
    for name in CROWD:
        if name != "ola":
            await befriend(client, group, people[name], ola)
    await mailbox.drain()
    return {**people, "group": group}


def ids(*people: dict) -> list[str]:
    return [str(person["id"]) for person in people]


# --------------------------------------------------------------------------- #
# The Friends card
# --------------------------------------------------------------------------- #


async def the_card(
    client, crowd, *seated: str, kind: str, sport: str = "PADEL", **more
) -> dict:
    read = await client.get(
        f"/api/v1/pools/{crowd['group']}/friends-card",
        params={
            "sport": sport,
            "kind": kind,
            "friend_ids": ids(*(crowd[name] for name in seated)),
            **more,
        },
        headers=crowd["ola"]["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def test_a_for_fun_friends_card_says_the_line_up_s_vibe_and_no_forecast(
    client, crowd
):
    card = await the_card(client, crowd, "ania", "marek", "zofia", kind="FOR_FUN")

    # The four at the table, 💘 aside: drink carried by three of them, laughs
    # and meet by two, quiet by two, new in town and straight home by one —
    # (⁴⁄₃ + ⁴⁄₃ + 1 + ⅓) over 11 carryings is 36%.
    assert card["kind"] == "FOR_FUN"
    assert card["vibe"] == {"pct": 36}
    assert card["forecast"] is None


async def test_a_competitive_friends_card_says_the_forecast_and_no_vibe(client, crowd):
    card = await the_card(client, crowd, "ania", "marek", "zofia", kind="COMPETITIVE")

    assert card["kind"] == "COMPETITIVE"
    assert card["forecast"] is not None
    assert card["vibe"] is None


async def test_flipping_the_switch_flips_the_number_and_nothing_else(client, crowd):
    competitive = await the_card(
        client, crowd, "ania", "marek", "zofia", kind="COMPETITIVE"
    )
    for_fun = await the_card(client, crowd, "ania", "marek", "zofia", kind="FOR_FUN")

    # The friendly still stands the evenest way, on the same court.
    unchanged = ("sides", "court", "overlap", "cut_off", "home_club")
    assert {key: for_fun[key] for key in unchanged} == {
        key: competitive[key] for key in unchanged
    }


async def test_the_vibe_is_the_line_up_s_however_it_stands(client, crowd):
    evenest = await the_card(client, crowd, "ania", "marek", "zofia", kind="FOR_FUN")
    swapped = await the_card(
        client,
        crowd,
        "ania",
        "marek",
        "zofia",
        kind="FOR_FUN",
        partner_id=str(crowd["zofia"]["id"]),
    )

    assert swapped["sides"] != evenest["sides"]
    assert swapped["vibe"] == evenest["vibe"] == {"pct": 36}


async def test_a_for_fun_singles_card_is_the_vibe_of_the_two_of_them(client, crowd):
    card = await the_card(client, crowd, "ania", kind="FOR_FUN", sport="TENNIS")

    assert card["vibe"] == {"pct": WITH_OLA["ania"]}
    assert card["forecast"] is None


# --------------------------------------------------------------------------- #
# Post a game's best fits
# --------------------------------------------------------------------------- #


async def the_sheet(client, crowd, *, kind: str) -> dict:
    read = await client.get(
        f"/api/v1/pools/{crowd['group']}/posting-grid/slot",
        params={
            "sport": "PADEL",
            "kind": kind,
            "who": "ANYONE",
            "day": SATURDAY.isoformat(),
            "range": "EVENING",
        },
        headers=crowd["ola"]["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


def names(sheet: dict) -> list[str]:
    return [fit["nickname"] for fit in sheet["fits"]]


async def test_a_for_fun_post_s_fits_each_carry_the_vibe_of_the_two_of_you(
    client, crowd
):
    sheet = await the_sheet(client, crowd, kind="FOR_FUN")

    assert {fit["nickname"]: fit["vibe"] for fit in sheet["fits"]} == {
        name: {"pct": pct} for name, pct in WITH_OLA.items()
    }
    assert all(fit["forecast"] is None for fit in sheet["fits"])


async def test_a_for_fun_post_s_fits_are_ranked_by_it_a_tie_falling_to_today_s_order(
    client, crowd
):
    for_fun = await the_sheet(client, crowd, kind="FOR_FUN")
    today = names(await the_sheet(client, crowd, kind="COMPETITIVE"))

    vibes = [fit["vibe"]["pct"] for fit in for_fun["fits"]]
    assert vibes == sorted(vibes, reverse=True)
    # Kuba and Marek both share one tag with her: the more even game of the two
    # comes first, as it does on a competitive post.
    assert names(for_fun) == sorted(
        WITH_OLA, key=lambda name: (-WITH_OLA[name], today.index(name))
    )
    # Ania, the best company, is the least even game of them all.
    assert names(for_fun)[0] == "ania" == today[-1]


async def test_a_competitive_post_s_fits_are_unchanged(client, crowd):
    sheet = await the_sheet(client, crowd, kind="COMPETITIVE")

    assert all(fit["vibe"] is None for fit in sheet["fits"])
    evenness = [fit["forecast"]["pct"] for fit in sheet["fits"]]
    assert evenness == sorted(evenness, reverse=True)
    assert [fit["level"] for fit in sheet["fits"]][-1] == pytest.approx(3.0)
    assert set(names(sheet)) == set(WITH_OLA)
