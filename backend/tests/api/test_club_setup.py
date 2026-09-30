"""The setup checklist on the club's Overview: five steps, and whether the club
is live (#535, the mechanics §16.2, the screens B2).

A step is **done**, **to do**, **locked** behind the one it needs — hours and
prices behind a court, the settings behind a way of working — or, for
payments, **pending**: connecting a Stripe account arrives with its own ticket
(#537), and until then the step reads pending and the club is live on the
other four.
"""

from __future__ import annotations

from tests.api.club_courts_world import (
    SETUP,
    a_desk,
    adds_a_court,
    chooses,
    confirms_settings,
    court_path,
    sets_hours,
    sets_prices,
)

STEPS = ["CONNECT_PAYMENTS", "WAY_OF_WORKING", "COURTS", "HOURS_AND_PRICES", "SETTINGS"]


async def checklist(client, desk) -> tuple[dict[str, str], bool]:
    read = await client.get(SETUP, headers=desk)
    assert read.status_code == 200, read.text
    body = read.json()
    assert [row["step"] for row in body["steps"]] == STEPS
    return {row["step"]: row["state"] for row in body["steps"]}, body["live"]


async def test_a_club_that_has_done_nothing_has_its_first_steps_to_do(client):
    _, desk = await a_desk(client)

    assert await checklist(client, desk) == (
        {
            "CONNECT_PAYMENTS": "PENDING",
            "WAY_OF_WORKING": "TO_DO",
            "COURTS": "TO_DO",
            "HOURS_AND_PRICES": "LOCKED",
            "SETTINGS": "LOCKED",
        },
        False,
    )


async def test_the_desk_walks_the_checklist_and_the_club_goes_live(client):
    _, desk = await a_desk(client, sports=("PADEL",))

    await chooses(client, desk, "INSTANT")
    steps, live = await checklist(client, desk)
    assert (steps["WAY_OF_WORKING"], steps["SETTINGS"], live) == (
        "DONE",
        "TO_DO",
        False,
    )

    court = await adds_a_court(client, desk, name="Court 1")
    steps, _ = await checklist(client, desk)
    assert (steps["COURTS"], steps["HOURS_AND_PRICES"]) == ("DONE", "TO_DO")

    await sets_hours(client, desk, [court["id"]], [(1, 17), (1, 18)])
    steps, _ = await checklist(client, desk)
    assert steps["HOURS_AND_PRICES"] == "TO_DO"  # hours, and no price yet

    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )
    steps, live = await checklist(client, desk)
    assert (steps["HOURS_AND_PRICES"], live) == ("DONE", False)

    await confirms_settings(client, desk)
    steps, live = await checklist(client, desk)

    assert steps == {
        "CONNECT_PAYMENTS": "PENDING",
        "WAY_OF_WORKING": "DONE",
        "COURTS": "DONE",
        "HOURS_AND_PRICES": "DONE",
        "SETTINGS": "DONE",
    }
    assert live is True


async def test_prices_before_hours_leave_the_step_to_do(client):
    _, desk = await a_desk(client, sports=("PADEL",))
    await adds_a_court(client, desk, name="Court 1")

    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )

    steps, _ = await checklist(client, desk)
    assert steps["HOURS_AND_PRICES"] == "TO_DO"


async def test_every_court_selling_hours_needs_its_sport_priced(client):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))
    padel = await adds_a_court(client, desk, name="Court 1", sport="PADEL")
    tennis = await adds_a_court(client, desk, name="Kort centralny", sport="TENNIS")
    await sets_hours(client, desk, [padel["id"], tennis["id"]], [(6, 9)])
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )

    steps, _ = await checklist(client, desk)
    assert steps["HOURS_AND_PRICES"] == "TO_DO"

    # Switched off, the tennis court sells nothing, so nothing is left unpriced.
    await client.put(
        court_path(tennis["id"]),
        json={
            "name": "Kort centralny",
            "sport": "TENNIS",
            "indoor": True,
            "offered": False,
        },
        headers=desk,
    )

    steps, _ = await checklist(client, desk)
    assert steps["HOURS_AND_PRICES"] == "DONE"


async def test_a_club_with_every_court_switched_off_is_not_live(client):
    _, desk = await a_desk(client, sports=("PADEL",))
    await chooses(client, desk, "ONLY_RAKETA")
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(6, 9)])
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )
    await confirms_settings(client, desk)
    assert (await checklist(client, desk))[1] is True

    await client.put(
        court_path(court["id"]),
        json={"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": False},
        headers=desk,
    )

    steps, live = await checklist(client, desk)
    assert (steps["COURTS"], steps["HOURS_AND_PRICES"], live) == (
        "TO_DO",
        "LOCKED",
        False,
    )


async def test_a_paused_club_is_still_live(client):
    """Live is the checklist's word; pausing stops new cards and is a setting
    (the mechanics §16.15), not a step undone."""

    _, desk = await a_desk(client, sports=("PADEL",))
    await chooses(client, desk, "ON_REQUEST")
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(6, 9)])
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )

    await confirms_settings(client, desk, paused=True)

    assert (await checklist(client, desk))[1] is True
