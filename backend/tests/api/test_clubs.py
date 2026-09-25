"""A club signs up, and reads and changes its own details, on the club surface.

The club surface is the club website's and nobody else's (``docs/adr/0182``,
``docs/adr/0187`` §5), so every route here is under ``/api/v1/club``. What a
club is — a name, a district, a city, the sports it offers and a precise point —
is asserted as the desk would see it: the answer to the request, and the details
read back afterwards.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.modules.clubs.infrastructure.club_model import ClubORM

SIGN_UP = "/api/v1/club/sign-up"
SIGN_IN = "/api/v1/club/auth/login"
DETAILS = "/api/v1/club/details"


def ogrody_33(**overrides) -> dict:
    """Ogrody 33's desk signing up, as #522 tells it."""

    return {
        "name": "Ogrody 33",
        "district": "Grzegórzki",
        "city": "Kraków",
        "sports": ["TENNIS", "PADEL"],
        "point": {"latitude": 50.0612345, "longitude": 19.9587654},
        "email": "desk@ogrody33.pl",
        "password": "ogrody-desk-33",
        **overrides,
    }


async def sign_in(client, email="desk@ogrody33.pl", password="ogrody-desk-33"):
    resp = await client.post(SIGN_IN, json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_a_club_signs_up_and_reads_its_details_back(client):
    signed_up = await client.post(SIGN_UP, json=ogrody_33())

    assert signed_up.status_code == 201, signed_up.text
    club = signed_up.json()
    assert club["name"] == "Ogrody 33"
    assert club["district"] == "Grzegórzki"
    assert club["city"] == "Kraków"
    # The registry's order, whatever order the desk ticked them in.
    assert club["sports"] == ["PADEL", "TENNIS"]
    # Stored as the desk dropped it: a club is a public place, so its point is
    # never coarsened the way a player's Location area is.
    assert club["point"] == {"latitude": 50.0612345, "longitude": 19.9587654}

    read = await client.get(DETAILS, headers=bearer(await sign_in(client)))

    assert read.status_code == 200, read.text
    assert read.json() == club


async def test_a_second_club_cannot_sign_up_with_an_email_a_club_already_uses(client):
    assert (await client.post(SIGN_UP, json=ogrody_33())).status_code == 201

    again = await client.post(
        SIGN_UP, json=ogrody_33(name="Ogrody 33 Bis", password="another-desk-1")
    )

    assert again.status_code == 409
    assert again.json()["code"] == "club_email_already_registered"
    assert again.json()["details"] == {"field": "email"}


async def test_a_club_may_sign_up_with_an_email_a_player_already_uses(
    client, valid_signup_payload
):
    """A Club account is a separate identity from every User (``docs/adr/0182``
    §3): the café owner's own address may also be the club's."""

    player = await client.post("/api/v1/users", json=valid_signup_payload)
    assert player.status_code == 201

    club = await client.post(
        SIGN_UP, json=ogrody_33(email=valid_signup_payload["email"])
    )

    assert club.status_code == 201, club.text


@pytest.mark.parametrize(
    ("overrides", "code", "field"),
    [
        ({"name": " O "}, "club_name_invalid", "name"),
        ({"name": "x" * 81}, "club_name_invalid", "name"),
        ({"district": ""}, "club_district_invalid", "district"),
        ({"city": "K"}, "club_city_invalid", "city"),
        ({"sports": []}, "club_sports_required", "sports"),
        (
            {"point": {"latitude": 91.0, "longitude": 19.95}},
            "club_point_invalid",
            "point",
        ),
        (
            {"point": {"latitude": 50.06, "longitude": -180.5}},
            "club_point_invalid",
            "point",
        ),
        ({"email": "desk-at-ogrody"}, "email_invalid", "email"),
        ({"password": "ogrodydesk"}, "password_too_weak", "password"),
        ({"password": "short1"}, "password_too_weak", "password"),
    ],
)
async def test_invalid_input_is_refused_under_the_field_it_is_about(
    client, overrides, code, field
):
    resp = await client.post(SIGN_UP, json=ogrody_33(**overrides))

    assert resp.status_code == 400, resp.text
    assert resp.json()["code"] == code
    assert resp.json()["details"] == {"field": field}
    # Nothing was recorded: the desk can correct the field and sign up.
    assert (await client.post(SIGN_UP, json=ogrody_33())).status_code == 201


async def test_a_sport_outside_the_registry_is_not_a_sport(client):
    resp = await client.post(SIGN_UP, json=ogrody_33(sports=["PADEL", "PICKLEBALL"]))

    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"


async def test_the_names_are_recorded_trimmed_and_a_sport_ticked_twice_once(client):
    signed_up = await client.post(
        SIGN_UP,
        json=ogrody_33(
            name="  Ogrody   33 ",
            district=" Grzegórzki",
            sports=["PADEL", "TENNIS", "PADEL"],
        ),
    )

    assert signed_up.status_code == 201, signed_up.text
    assert signed_up.json()["name"] == "Ogrody 33"
    assert signed_up.json()["district"] == "Grzegórzki"
    assert signed_up.json()["sports"] == ["PADEL", "TENNIS"]


def moved_pin(**overrides) -> dict:
    """Ogrody 33's details after the desk notices the pin is two streets off."""

    details = {
        key: value
        for key, value in ogrody_33().items()
        if key not in {"email", "password"}
    }
    return {
        **details,
        "point": {"latitude": 50.0631, "longitude": 19.9612},
        **overrides,
    }


async def test_the_desk_changes_its_club_s_details(client):
    await client.post(SIGN_UP, json=ogrody_33())
    headers = bearer(await sign_in(client))

    changed = await client.put(
        DETAILS,
        headers=headers,
        json=moved_pin(
            name="Ogrody 33 Tennis & Padel",
            district="Dąbie",
            sports=["SQUASH", "TENNIS"],
        ),
    )

    assert changed.status_code == 200, changed.text
    assert changed.json()["name"] == "Ogrody 33 Tennis & Padel"
    assert changed.json()["district"] == "Dąbie"
    assert changed.json()["sports"] == ["TENNIS", "SQUASH"]
    assert changed.json()["point"] == {"latitude": 50.0631, "longitude": 19.9612}
    assert (await client.get(DETAILS, headers=headers)).json() == changed.json()


async def test_saving_the_details_unchanged_answers_them_as_they_stand(client):
    signed_up = (await client.post(SIGN_UP, json=ogrody_33())).json()
    headers = bearer(await sign_in(client))
    unchanged = {key: signed_up[key] for key in moved_pin()}

    saved = await client.put(DETAILS, headers=headers, json=unchanged)

    assert saved.status_code == 200, saved.text
    assert saved.json() == signed_up


async def test_a_details_change_is_refused_under_the_field_and_changes_nothing(
    client,
):
    signed_up = (await client.post(SIGN_UP, json=ogrody_33())).json()
    headers = bearer(await sign_in(client))

    refused = await client.put(DETAILS, headers=headers, json=moved_pin(sports=[]))

    assert refused.status_code == 400
    assert refused.json()["code"] == "club_sports_required"
    assert refused.json()["details"] == {"field": "sports"}
    assert (await client.get(DETAILS, headers=headers)).json() == signed_up


async def test_each_club_reads_and_changes_only_its_own_details(client):
    await client.post(SIGN_UP, json=ogrody_33())
    await client.post(
        SIGN_UP,
        json=ogrody_33(
            name="Bonarka Arena", district="Podgórze", email="desk@bonarka.pl"
        ),
    )
    ogrody = bearer(await sign_in(client))
    bonarka = bearer(await sign_in(client, email="desk@bonarka.pl"))

    await client.put(DETAILS, headers=bonarka, json=moved_pin(name="Bonarka Arena 2"))

    assert (await client.get(DETAILS, headers=ogrody)).json()["name"] == "Ogrody 33"
    assert (await client.get(DETAILS, headers=bonarka)).json()["name"] == (
        "Bonarka Arena 2"
    )


@pytest.mark.parametrize("method", ["get", "put"])
async def test_the_details_need_a_club_s_token(client, method):
    await client.post(SIGN_UP, json=ogrody_33())
    body = {"json": moved_pin()} if method == "put" else {}

    resp = await getattr(client, method)(DETAILS, **body)

    assert resp.status_code == 401
    assert resp.json()["code"] == "access_token_missing"


async def test_the_search_row_is_written_with_the_act_and_folded_for_search(
    client, session_factory
):
    """What home-club and join search will read (``docs/adr/0182`` §2) — no
    route reads it until they exist (#504), so it is read here: written in the
    sign-up's own transaction, moved by a details change, and folded by the
    function a query will be folded by."""

    club_id = (await client.post(SIGN_UP, json=ogrody_33())).json()["id"]
    headers = bearer(await sign_in(client))

    async def row():
        async with session_factory() as session:
            return await session.get(ClubORM, UUID(club_id))

    signed_up = await row()
    assert (signed_up.name, signed_up.name_folded) == ("Ogrody 33", "ogrody 33")
    assert signed_up.district_folded == "grzegorzki"
    assert signed_up.sports == ["PADEL", "TENNIS"]

    await client.put(
        DETAILS,
        headers=headers,
        json=moved_pin(name="Błonia Tennis", district="Łobzów", sports=["TENNIS"]),
    )

    changed = await row()
    assert (changed.name_folded, changed.district_folded) == (
        "blonia tennis",
        "lobzow",
    )
    assert changed.sports == ["TENNIS"]
    assert (changed.latitude, changed.longitude) == (50.0631, 19.9612)
