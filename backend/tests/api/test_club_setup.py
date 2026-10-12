"""The setup checklist on the club's Overview: four steps, and whether the club
is live (#535, #537, #670, the mechanics §16.2, the screens B2).

A step is **done**, **to do** or **locked** behind the one it needs — hours and
prices behind a court. The club is live when all four are done, payments
included: how the payments step moves is ``test_club_payments.py``'s. *Choose
how you work with Raketa* was the second of five until Only Raketa became the
one way (#670; ``docs/adr/0196`` §1).
"""

from __future__ import annotations

from tests.api.club_courts_world import (
    SETUP,
    a_desk,
    adds_a_court,
    confirms_settings,
    connects_payments,
    court_path,
    sets_hours,
    sets_prices,
)

STEPS = ["CONNECT_PAYMENTS", "COURTS", "HOURS_AND_PRICES", "SETTINGS"]


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
            "CONNECT_PAYMENTS": "TO_DO",
            "COURTS": "TO_DO",
            "HOURS_AND_PRICES": "LOCKED",
            "SETTINGS": "TO_DO",
        },
        False,
    )


async def test_the_desk_walks_the_four_steps_and_the_club_goes_live(client):
    _, desk = await a_desk(client, sports=("PADEL",))

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
    assert (steps["SETTINGS"], steps["CONNECT_PAYMENTS"], live) == (
        "DONE",
        "TO_DO",
        False,
    )

    await connects_payments(client, desk)
    steps, live = await checklist(client, desk)

    assert steps == {
        "CONNECT_PAYMENTS": "DONE",
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
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(6, 9)])
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )
    await confirms_settings(client, desk)
    await connects_payments(client, desk)
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
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(6, 9)])
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )

    await confirms_settings(client, desk, paused=True)
    await connects_payments(client, desk)

    assert (await checklist(client, desk))[1] is True
