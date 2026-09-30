"""A club prices a court-hour per sport, with optional bands — weekday or
weekend, between two hours — that cost more or less (#535, the mechanics §16.5,
the screens B3).

**Money crosses as integer grosze**, and a price has to split into whole grosze
among the sport's seats, because the share — the price divided by the seats —
is what a player pays and it is fixed on the card: *140 zł ÷ 4 = 35 zł each*.
"""

from __future__ import annotations

import pytest

from tests.api.club_courts_world import PRICES, a_desk, sets_prices


def padel(price: int = 120_00, bands: list | None = None) -> dict:
    return {"sport": "PADEL", "price_grosze": price, "bands": bands or []}


def band(days: str, opens: int, closes: int, price: int) -> dict:
    return {
        "days": days,
        "from_hour": opens,
        "until_hour": closes,
        "price_grosze": price,
    }


async def test_the_desk_prices_padel_with_dearer_evenings_and_weekends(client):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))

    saved = await sets_prices(
        client,
        desk,
        [
            padel(
                120_00,
                [band("WEEKEND", 7, 23, 140_00), band("WEEKDAYS", 17, 22, 140_00)],
            )
        ],
    )

    # Every sport the club offers, in the registry's order — tennis unpriced.
    # Each price carries its share: the price divided by the sport's seats.
    assert saved == {
        "prices": [
            {
                "sport": "PADEL",
                "seats": 4,
                "price_grosze": 120_00,
                "share_grosze": 30_00,
                "bands": [
                    {
                        "days": "WEEKDAYS",
                        "from_hour": 17,
                        "until_hour": 22,
                        "price_grosze": 140_00,
                        "share_grosze": 35_00,
                    },
                    {
                        "days": "WEEKEND",
                        "from_hour": 7,
                        "until_hour": 23,
                        "price_grosze": 140_00,
                        "share_grosze": 35_00,
                    },
                ],
            },
            {
                "sport": "TENNIS",
                "seats": 2,
                "price_grosze": None,
                "share_grosze": None,
                "bands": [],
            },
        ]
    }
    assert (await client.get(PRICES, headers=desk)).json() == saved


async def test_a_save_replaces_the_whole_table(client):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))
    await sets_prices(
        client,
        desk,
        [padel(), {"sport": "TENNIS", "price_grosze": 80_00, "bands": []}],
    )

    saved = await sets_prices(
        client, desk, [{"sport": "TENNIS", "price_grosze": 90_00, "bands": []}]
    )

    by_sport = {row["sport"]: row for row in saved["prices"]}
    assert by_sport["PADEL"]["price_grosze"] is None
    assert by_sport["TENNIS"]["price_grosze"] == 90_00
    assert by_sport["TENNIS"]["share_grosze"] == 45_00


async def test_a_price_that_splits_into_whole_grosze_is_kept_to_the_grosz(client):
    _, desk = await a_desk(client, sports=("PADEL",))

    saved = await sets_prices(client, desk, [padel(142_52)])

    assert saved["prices"][0]["share_grosze"] == 35_63


@pytest.mark.parametrize(
    ("row", "code", "details"),
    [
        (
            {"sport": "SQUASH", "price_grosze": 60_00, "bands": []},
            "price_sport_not_offered",
            {"field": "prices", "sport": "SQUASH"},
        ),
        (
            padel(9_96),
            "price_out_of_range",
            {"field": "prices", "sport": "PADEL", "least": 10_00, "most": 1000_00},
        ),
        (
            padel(1000_04),
            "price_out_of_range",
            {"field": "prices", "sport": "PADEL", "least": 10_00, "most": 1000_00},
        ),
        (
            padel(120_00, [band("WEEKEND", 9, 14, 8_00)]),
            "price_out_of_range",
            {"field": "prices", "sport": "PADEL", "least": 10_00, "most": 1000_00},
        ),
        (
            padel(142_50),
            "price_does_not_split",
            {"field": "prices", "sport": "PADEL", "seats": 4},
        ),
        (
            padel(120_00, [band("WEEKDAYS", 17, 22, 141_01)]),
            "price_does_not_split",
            {"field": "prices", "sport": "PADEL", "seats": 4},
        ),
        (
            padel(120_00, [band("WEEKDAYS", 22, 17, 140_00)]),
            "price_band_hours_invalid",
            {"field": "prices", "sport": "PADEL"},
        ),
        (
            padel(120_00, [band("WEEKDAYS", 6, 9, 140_00)]),
            "price_band_hours_invalid",
            {"field": "prices", "sport": "PADEL"},
        ),
        (
            padel(120_00, [band("WEEKDAYS", 20, 24, 140_00)]),
            "price_band_hours_invalid",
            {"field": "prices", "sport": "PADEL"},
        ),
        (
            padel(
                120_00,
                [band("WEEKDAYS", 17, 22, 140_00), band("WEEKDAYS", 21, 23, 150_00)],
            ),
            "price_bands_overlap",
            {"field": "prices", "sport": "PADEL"},
        ),
    ],
)
async def test_what_the_desk_has_to_correct_is_refused_naming_the_sport(
    client, row, code, details
):
    _, desk = await a_desk(client, sports=("PADEL", "TENNIS"))
    before = await sets_prices(client, desk, [padel(100_00)])

    refused = await client.put(PRICES, json={"prices": [row]}, headers=desk)

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == code
    assert refused.json()["details"] == details
    assert (await client.get(PRICES, headers=desk)).json() == before


async def test_a_sport_priced_twice_in_one_save_is_refused(client):
    _, desk = await a_desk(client, sports=("PADEL",))

    refused = await client.put(
        PRICES, json={"prices": [padel(120_00), padel(130_00)]}, headers=desk
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "price_sport_repeated"
    assert refused.json()["details"] == {"field": "prices", "sport": "PADEL"}


async def test_weekday_and_weekend_bands_over_the_same_hours_do_not_overlap(client):
    _, desk = await a_desk(client, sports=("PADEL",))

    saved = await sets_prices(
        client,
        desk,
        [
            padel(
                120_00,
                [band("WEEKDAYS", 17, 22, 140_00), band("WEEKEND", 17, 22, 160_00)],
            )
        ],
    )

    assert len(saved["prices"][0]["bands"]) == 2
