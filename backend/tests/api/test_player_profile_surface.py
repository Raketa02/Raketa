"""The profile surface Play reads and writes: one read, one `PUT` per fact.

The Play screen edits three facts — the week, the radius and the per-sport Play
intent — and until these routes existed it could read none of them and write
none of them. What is asserted here is the shape #226 settled: **one read
carrying all three**, and **one unkeyed `PUT` per changeable fact**, because a
blank grid is a legal value and a `PATCH` field that may be `null` would mean
both *leave my week alone* and *clear my week*.

The fourth fact a screen needs — *which sports am I rated in* — is
`GET /api/v1/ratings` and is not re-served here.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
from app.modules.player_profile.domain.ids import play_intent_declaration_id
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS

PROFILE_URL = "/api/v1/players/me/profile"
AVAILABILITY_URL = "/api/v1/players/me/availability"
RADIUS_URL = "/api/v1/players/me/search-radius"


def intents_url(sport: Sport | str) -> str:
    value = sport.value if isinstance(sport, Sport) else sport
    return f"/api/v1/play-intents/{value}"


async def a_player(client, name: str = "surface") -> tuple[UUID, dict[str, str]]:
    """One signed-in player with a committed profile, through the real routes."""

    signup = await client.post(
        "/api/v1/users",
        json={
            "email": f"{name}@example.com",
            "password1": "hunter22!",
            "password2": "hunter22!",
            "adult_attested": True,
        },
    )
    assert signup.status_code == 201, signup.text
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": "hunter22!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    commit = await client.post(
        PROFILE_URL,
        json={
            "social_tag_ids": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
            "photo_ids": [],
            "availability": [
                {"day": 2, "part": "EVENING"},
                {"day": 6, "part": "MORNING"},
            ],
            "location": {"latitude": 51.5073509, "longitude": -0.1277583},
            "search_radius_km": SEARCH_RADIUS_BOUNDS.default_km,
            "proposals_opt_in": {
                "accepted": True,
                "copy_version": "proposals-2026-08",
            },
            "gender": "WOMAN",
        },
        headers={**headers, "Idempotency-Key": f"commit-{name}"},
    )
    assert commit.status_code == 201, commit.text
    return UUID(signup.json()["id"]), headers


async def a_signed_in_player(client, name: str) -> dict[str, str]:
    """A player with no profile — every account before onboarding's second part."""

    await client.post(
        "/api/v1/users",
        json={
            "email": f"{name}@example.com",
            "password1": "hunter22!",
            "password2": "hunter22!",
            "adult_attested": True,
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": "hunter22!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def stream_length(session_factory, aggregate_id: UUID) -> int:
    async with session_factory() as session:
        return (
            await session.execute(
                select(func.count()).where(EventStoreORM.aggregate_id == aggregate_id)
            )
        ).scalar_one()


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------


async def test_the_read_carries_the_week_the_radius_and_the_declaration(client):
    _, headers = await a_player(client)
    await client.put(
        intents_url(Sport.PADEL),
        json={"intent": "COMPETITIVE", "surface": "RATING_TAIL"},
        headers=headers,
    )

    response = await client.get(PROFILE_URL, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["availability"] == [
        {"day": 2, "part": "EVENING"},
        {"day": 6, "part": "MORNING"},
    ]
    assert body["search_radius_km"] == SEARCH_RADIUS_BOUNDS.default_km
    assert body["play_intents"] == {"PADEL": "COMPETITIVE"}


async def test_a_sport_with_no_declaration_is_absent_rather_than_null(client):
    """ADR-0094 forbids a nullable intent, and an encoding must not walk that
    back in: the map holds what was declared, and *rated but undeclared* is the
    client's own set difference against `GET /ratings`."""

    _, headers = await a_player(client)
    await client.put(
        intents_url(Sport.TENNIS),
        json={"intent": "FOR_FUN", "surface": "RATING_TAIL"},
        headers=headers,
    )

    body = (await client.get(PROFILE_URL, headers=headers)).json()

    assert body["play_intents"] == {"TENNIS": "FOR_FUN"}
    assert "PADEL" not in body["play_intents"]


async def test_the_read_serves_neither_the_refused_fields_nor_the_deferred_ones(
    client,
):
    """Decision 12's scope, and ADR-0096's standing refusal, in one assertion.

    `gender` never comes back out of this API. Tags, photos and location are
    **not served yet** and land here when You is built — which is why the route
    description names photos, the one absence a client could otherwise read as
    *you have none*.
    """

    _, headers = await a_player(client)

    body = (await client.get(PROFILE_URL, headers=headers)).json()

    for absent in (
        "gender",
        "gender_preference",
        "social_tag_ids",
        "photo_ids",
        "location",
    ):
        assert absent not in body


async def test_the_read_answers_the_profile_that_is_not_there(client):
    headers = await a_signed_in_player(client, "unonboarded")

    response = await client.get(PROFILE_URL, headers=headers)

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "player_profile_not_found"


async def test_the_read_needs_a_token(client):
    assert (await client.get(PROFILE_URL)).status_code == 401


# ---------------------------------------------------------------------------
# The week
# ---------------------------------------------------------------------------


async def test_the_week_is_replaced_whole(client):
    _, headers = await a_player(client)

    response = await client.put(
        AVAILABILITY_URL,
        json={"availability": [{"day": 1, "part": "MORNING"}]},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["availability"] == [{"day": 1, "part": "MORNING"}]
    read = (await client.get(PROFILE_URL, headers=headers)).json()
    assert read["availability"] == [{"day": 1, "part": "MORNING"}]


async def test_a_cleared_week_is_a_legal_value_on_the_write(client):
    """The floor binds the commit and not every later edit, and this is the
    route that finally says so: `AvailabilityGrid.edited` is what the boundary
    builds through, so nothing ticked is recorded rather than refused."""

    _, headers = await a_player(client)

    response = await client.put(
        AVAILABILITY_URL, json={"availability": []}, headers=headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["availability"] == []
    assert (await client.get(PROFILE_URL, headers=headers)).json()["availability"] == []


async def test_the_week_comes_back_folded_and_in_reading_order(client):
    """Why the write answers with the grid rather than with no content: a
    repeated cell is collapsed and the order is the platform's, so a client that
    kept what it sent would hold a week the profile does not."""

    _, headers = await a_player(client)

    response = await client.put(
        AVAILABILITY_URL,
        json={
            "availability": [
                {"day": 3, "part": "EVENING"},
                {"day": 1, "part": "MORNING"},
                {"day": 3, "part": "EVENING"},
            ]
        },
        headers=headers,
    )

    assert response.json()["availability"] == [
        {"day": 1, "part": "MORNING"},
        {"day": 3, "part": "EVENING"},
    ]


async def test_the_same_week_twice_lands_the_same_state(client, session_factory):
    """Unkeyed and idempotent, which is what makes an idempotency key pointless
    here: the second request lands the state the first did and the aggregate's
    no-op rule means it appends nothing."""

    player_id, headers = await a_player(client)
    week = {"availability": [{"day": 4, "part": "AFTERNOON"}]}

    first = await client.put(AVAILABILITY_URL, json=week, headers=headers)
    after_first = await stream_length(session_factory, player_id)
    second = await client.put(AVAILABILITY_URL, json=week, headers=headers)

    assert first.json() == second.json()
    assert await stream_length(session_factory, player_id) == after_first


async def test_there_is_no_patch_for_the_week(client):
    """`null` versus absent is fatal on this field specifically: a blank grid is
    a legal value, so `{"availability": null}` would mean both *leave it alone*
    and *clear my week*."""

    _, headers = await a_player(client)

    response = await client.patch(
        AVAILABILITY_URL, json={"availability": []}, headers=headers
    )

    assert response.status_code == 405


async def test_the_week_cannot_be_written_without_a_profile(client):
    headers = await a_signed_in_player(client, "weekless")

    response = await client.put(
        AVAILABILITY_URL, json={"availability": []}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["code"] == "player_profile_not_found"


# ---------------------------------------------------------------------------
# The radius
# ---------------------------------------------------------------------------


async def test_the_radius_is_replaced_whole(client):
    _, headers = await a_player(client)

    response = await client.put(
        RADIUS_URL, json={"search_radius_km": 22}, headers=headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["search_radius_km"] == 22
    assert (await client.get(PROFILE_URL, headers=headers)).json()[
        "search_radius_km"
    ] == 22


async def test_a_radius_outside_the_served_bounds_is_refused_by_its_own_code(client):
    """The bounds are served so a client can build a slider that cannot produce
    an illegal value — and a control is not a validation (ADR-0089)."""

    _, headers = await a_player(client)

    response = await client.put(
        RADIUS_URL,
        json={"search_radius_km": SEARCH_RADIUS_BOUNDS.maximum_km + 1},
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "search_radius_out_of_bounds"


async def test_there_is_no_patch_for_the_radius(client):
    _, headers = await a_player(client)

    response = await client.patch(
        RADIUS_URL, json={"search_radius_km": 22}, headers=headers
    )

    assert response.status_code == 405


async def test_the_radius_cannot_be_written_without_a_profile(client):
    headers = await a_signed_in_player(client, "radiusless")

    response = await client.put(
        RADIUS_URL, json={"search_radius_km": 22}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["code"] == "player_profile_not_found"


# ---------------------------------------------------------------------------
# The declaration
# ---------------------------------------------------------------------------


async def test_a_declaration_is_opened_and_then_changed_through_one_route(client):
    _, headers = await a_player(client)

    opened = await client.put(
        intents_url(Sport.SQUASH),
        json={"intent": "FOR_FUN", "surface": "RATING_TAIL"},
        headers=headers,
    )
    changed = await client.put(
        intents_url(Sport.SQUASH),
        json={"intent": "COMPETITIVE", "surface": "SEARCH_SWITCH"},
        headers=headers,
    )

    assert opened.status_code == 200, opened.text
    assert opened.json() == {"sport": "SQUASH", "intent": "FOR_FUN"}
    assert changed.json() == {"sport": "SQUASH", "intent": "COMPETITIVE"}


async def test_the_deck_is_a_surface_the_route_accepts(client):
    """#280. The deck draws ADR-0094's interstitial for the same reason the
    search screen does, so ``DECK`` has to cross the boundary as itself rather
    than as the nearest of four — this is the assertion that the widened enum
    reached the schema and not only the domain."""

    _, headers = await a_player(client)

    response = await client.put(
        intents_url(Sport.TENNIS),
        json={"intent": "COMPETITIVE", "surface": "DECK"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"sport": "TENNIS", "intent": "COMPETITIVE"}


async def test_declaring_the_value_already_held_records_nothing(
    client, session_factory
):
    """A preference, not a consent: re-declaring `COMPETITIVE` over
    `COMPETITIVE` from a different surface is the same answer, and a stream that
    grew an event for it would record that a player did not do anything."""

    player_id, headers = await a_player(client)
    stream = play_intent_declaration_id(player_id, Sport.PADEL)

    await client.put(
        intents_url(Sport.PADEL),
        json={"intent": "COMPETITIVE", "surface": "RATING_TAIL"},
        headers=headers,
    )
    after_first = await stream_length(session_factory, stream)
    again = await client.put(
        intents_url(Sport.PADEL),
        json={"intent": "COMPETITIVE", "surface": "SEARCH_SWITCH"},
        headers=headers,
    )

    assert again.status_code == 200, again.text
    assert again.json() == {"sport": "PADEL", "intent": "COMPETITIVE"}
    assert await stream_length(session_factory, stream) == after_first


async def test_no_preference_is_a_declaration_like_any_other(client):
    """Nobody is ever backfilled to it, and it is not the absent case: the
    matcher must be able to tell *either suits me* from *I never answered*."""

    _, headers = await a_player(client)

    await client.put(
        intents_url(Sport.BADMINTON),
        json={"intent": "NO_PREFERENCE", "surface": "PROFILE_SCREEN"},
        headers=headers,
    )

    body = (await client.get(PROFILE_URL, headers=headers)).json()
    assert body["play_intents"]["BADMINTON"] == "NO_PREFERENCE"


async def test_a_declaration_does_not_wait_on_a_profile(client):
    """The rating tail is the first surface and it comes before onboarding's
    second part, so a declaration with no profile behind it is the ordinary
    first case rather than an error."""

    headers = await a_signed_in_player(client, "rated-only")

    response = await client.put(
        intents_url(Sport.TENNIS),
        json={"intent": "FOR_FUN", "surface": "RATING_TAIL"},
        headers=headers,
    )

    assert response.status_code == 200, response.text


async def test_a_sport_this_platform_does_not_rate_is_refused(client):
    _, headers = await a_player(client)

    response = await client.put(
        intents_url("CHESS"),
        json={"intent": "FOR_FUN", "surface": "RATING_TAIL"},
        headers=headers,
    )

    assert response.status_code == 422


async def test_a_declaration_is_the_declaring_players_own(client):
    _, headers = await a_player(client, "mine")
    _, other = await a_player(client, "theirs")

    await client.put(
        intents_url(Sport.PADEL),
        json={"intent": "COMPETITIVE", "surface": "RATING_TAIL"},
        headers=headers,
    )

    assert (await client.get(PROFILE_URL, headers=other)).json()["play_intents"] == {}


async def test_the_declaration_needs_a_token(client):
    response = await client.put(
        intents_url(Sport.PADEL),
        json={"intent": "COMPETITIVE", "surface": "RATING_TAIL"},
    )

    assert response.status_code == 401


def test_the_surface_is_a_read_a_week_and_a_radius_and_nothing_else():
    """Map Decision 12, asserted against the routes rather than against prose.

    Tags, photos, gender, gender preference and location all have aggregate
    methods and **no route**, deliberately: they belong to You, which is not
    built. A sixth route appearing under this prefix without that ticket is what
    this test is here to catch.
    """

    from app.modules.player_profile.presentation.profile_surface_routes import router

    assert {(route.path, tuple(sorted(route.methods))) for route in router.routes} == {
        ("/players/me/profile", ("GET",)),
        ("/players/me/availability", ("PUT",)),
        ("/players/me/search-radius", ("PUT",)),
    }


def test_nothing_on_this_surface_takes_an_idempotency_key():
    """The key stays on the creating commit. A `PUT` that lands the same state
    twice has nothing to deduplicate — which is the whole argument for the
    shape, and it would be undone by adding one here out of symmetry."""

    from app.modules.player_profile.presentation import (
        play_intent_routes,
        profile_surface_routes,
    )

    for module in (profile_surface_routes, play_intent_routes):
        for route in module.router.routes:
            names = {
                dependant.alias or dependant.name
                for dependant in route.dependant.header_params
            }
            assert "Idempotency-Key" not in names, route.path
