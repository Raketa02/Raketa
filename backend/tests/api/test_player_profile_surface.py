"""The profile surface reads and writes: one read, one `PUT` per fact.

The Play screen edits three facts — the week, the radius and the per-sport Play
intent — and until these routes existed it could read none of them and write
none of them. What is asserted here is the shape #226 settled: **one read
carrying all three**, and **one unkeyed `PUT` per changeable fact**, because a
blank grid is a legal value and a `PATCH` field that may be `null` would mean
both *leave my week alone* and *clear my week*.

The fourth `PUT` is the **cold start's** and no screen's: the location
(``docs/adr/0174`` §6), put silently on every launch, which is why the
same-cell case answering `204` with nothing appended is the assertion that
matters most.

The fourth fact a screen needs — *which sports am I rated in* — is
`GET /api/v1/ratings` and is not re-served here.

**The read is the You tab's too** (``docs/adr/0179`` §8): it grew by the tags,
the photos with their verdicts, the intro, the standing opt-in answer, and the
owner's own gender and preference — the one shape those two may cross on (§4).
What is asserted about it here is each field's spelling of absence, because
that is what a client branches on: an empty ``photos`` list is served, an
unwritten intro is omitted, a photograph nobody looked at carries no verdict,
a pre-question profile carries no gender, and the location is still not there.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select

from app.bootstrap.events import build_event_runtime
from app.infrastructure.events.event_store_model import EventStoreORM
from app.infrastructure.events.sqlalchemy_domain_event_store import (
    SqlAlchemyEventStore,
)
from app.kernel import Sport
from app.modules.player_profile.domain.events import (
    PlayerProfileCreated,
    ProposalsOptInAnswered,
)
from app.modules.player_profile.domain.ids import play_intent_declaration_id
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
)
from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewUnavailability,
    review_metadata,
    verdict_from_similarities,
    verdict_when_unreviewable,
)
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS

PROFILE_URL = "/api/v1/players/me/profile"
AVAILABILITY_URL = "/api/v1/players/me/availability"
RADIUS_URL = "/api/v1/players/me/search-radius"
LOCATION_URL = "/api/v1/players/me/location"

#: The fix `a_player` commits with.
HOME_FIX = {"latitude": 51.5073509, "longitude": -0.1277583}
#: A fix in another cell entirely, and its cell.
AWAY_FIX = {"latitude": 52.2297, "longitude": 21.0122}
AWAY_CELL = (52.23, 21.01)


def intents_url(sport: Sport | str) -> str:
    value = sport.value if isinstance(sport, Sport) else sport
    return f"/api/v1/play-intents/{value}"


async def an_account(client, name: str) -> tuple[UUID, dict[str, str]]:
    """One signed-in account with no profile yet, through the real routes."""

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
    return UUID(signup.json()["id"]), headers


async def a_committed_profile(
    client, headers: dict[str, str], name: str, **overrides
) -> None:
    """The commit, with the answers every test here gives unless it says otherwise."""

    body = {
        "social_tag_ids": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
        "photo_ids": [],
        "availability": [
            {"day": 2, "part": "EVENING"},
            {"day": 6, "part": "MORNING"},
        ],
        "location": HOME_FIX,
        "search_radius_km": SEARCH_RADIUS_BOUNDS.default_km,
        "proposals_opt_in": {
            "accepted": True,
            "copy_version": "proposals-2026-08",
        },
        "gender": "WOMAN",
    }
    body.update(overrides)
    commit = await client.post(
        PROFILE_URL,
        json=body,
        headers={**headers, "Idempotency-Key": f"commit-{name}"},
    )
    assert commit.status_code == 201, commit.text


async def a_player(client, name: str = "surface") -> tuple[UUID, dict[str, str]]:
    """One signed-in player with a committed profile, through the real routes."""

    player_id, headers = await an_account(client, name)
    await a_committed_profile(client, headers, name)
    return player_id, headers


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


async def stream_of(session_factory, aggregate_id: UUID) -> list[EventStoreORM]:
    async with session_factory() as session:
        rows = await session.execute(
            select(EventStoreORM)
            .where(EventStoreORM.aggregate_id == aggregate_id)
            .order_by(EventStoreORM.version)
        )
        return list(rows.scalars())


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


#: The reviewer a stored verdict names, and the two similarity vectors that
#: decide it one way and the other. What the numbers mean is the domain's.
MODEL = "openai/clip-vit-base-patch32"
ON_COURT = [0.9] * 5 + [0.1] * 8
OFF_COURT = [0.1] * 5 + [0.9] * 8


def a_photo_held(photo_storage, owner: UUID, metadata: dict[str, str]) -> UUID:
    """One photograph already in the store under this owner, carrying what a
    verdict writes — the fixture a *reader* of the verdict wants, not an upload."""

    photo_id = uuid4()
    photo_storage.already_holding(PhotoRef(owner_id=owner, photo_id=photo_id), metadata)
    return photo_id


async def test_the_read_carries_every_fact_the_you_tab_draws(client, photo_storage):
    """``docs/adr/0179`` §8: the read grows by the tags, the photos with their
    verdicts, the intro, the standing opt-in answer, and the owner's own gender
    and preference (§4). Every row on the tab draws its live line from this one
    response, and *Who you play with* opens with the right radio pre-selected.
    """

    player_id, headers = await an_account(client, "you")
    passed = a_photo_held(
        photo_storage,
        player_id,
        review_metadata(verdict_from_similarities(model=MODEL, similarities=ON_COURT)),
    )
    flagged = a_photo_held(
        photo_storage,
        player_id,
        review_metadata(verdict_from_similarities(model=MODEL, similarities=OFF_COURT)),
    )
    await a_committed_profile(
        client,
        headers,
        "you",
        social_tag_ids=["HERE_TO_IMPROVE", "PLAYS_TO_WIN"],
        photo_ids=[str(passed), str(flagged)],
        intro="Will travel for a hard game.",
        gender="MAN",
        gender_preference="ANY",
    )

    response = await client.get(PROFILE_URL, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    # The vocabulary's order, whatever order the picker sent them in.
    assert body["social_tags"] == ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"]
    assert body["photos"] == [
        {"photo_id": str(passed), "review": "allowed"},
        {"photo_id": str(flagged), "review": "flagged"},
    ]
    assert body["intro"] == "Will travel for a hard game."
    assert body["proposals_opt_in"]["accepted"] is True
    assert body["proposals_opt_in"]["copy_version"] == "proposals-2026-08"
    assert body["proposals_opt_in"]["answered_at"]
    assert body["gender"] == "MAN"
    assert body["gender_preference"] == "ANY"


async def test_a_photograph_nobody_looked_at_carries_no_verdict(client, photo_storage):
    """The uploader's third reading is an **absence** (``docs/adr/0138``): the
    photograph is listed, in its place, and nothing is claimed about it — never
    ``allowed``, and never ``null`` either, which would generate a type that
    says neither thing."""

    player_id, headers = await an_account(client, "outage")
    unlooked_at = a_photo_held(
        photo_storage,
        player_id,
        review_metadata(verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT)),
    )
    await a_committed_profile(client, headers, "outage", photo_ids=[str(unlooked_at)])

    body = (await client.get(PROFILE_URL, headers=headers)).json()

    assert body["photos"] == [{"photo_id": str(unlooked_at)}]


async def test_no_photographs_is_an_empty_list_and_no_intro_is_no_field(client):
    """Two absences with two spellings. A profile may legally hold no photo, so
    the list is **served empty** rather than omitted — the deferral this route
    used to name as the one a client could read as *you have none*. An intro
    that was never written is **omitted**, never ``""`` (``docs/adr/0170``)."""

    _, headers = await a_player(client, "bare")

    body = (await client.get(PROFILE_URL, headers=headers)).json()

    assert body["photos"] == []
    assert "intro" not in body


async def test_a_profile_from_before_the_gender_question_omits_the_answer(
    client, session_factory
):
    """Never ``PREFER_NOT_TO_SAY``, which is an answer a player gives
    (``docs/adr/0179`` §4). No route can commit such a profile any more, so the
    stream is written as it was then — the field simply unset, no upcaster —
    and the assertion is on the wire, because *omitted* is a property of the
    route and not of the model behind it."""

    player_id, headers = await an_account(client, "before-the-question")
    then = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    async with session_factory() as session:
        await SqlAlchemyEventStore(session, build_event_runtime().codec).append(
            aggregate_type=PLAYER_PROFILE_AGGREGATE,
            aggregate_id=player_id,
            expected_version=0,
            events=[
                PlayerProfileCreated(
                    player_id=player_id,
                    social_tags=("PLAYS_TO_WIN", "HERE_TO_IMPROVE"),
                    photo_ids=(),
                    availability=("2:EVENING",),
                    latitude=51.51,
                    longitude=-0.13,
                    search_radius_km=SEARCH_RADIUS_BOUNDS.default_km,
                    idempotency_key="commit-before-the-question",
                    occurred_at=then,
                ),
                ProposalsOptInAnswered(
                    player_id=player_id,
                    accepted=True,
                    copy_version="proposals-2026-08",
                    surface="ONBOARDING",
                    occurred_at=then,
                ),
            ],
        )
        await session.commit()

    response = await client.get(PROFILE_URL, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "gender" not in body
    assert body["gender_preference"] == "ANY"


async def test_the_read_serves_no_location_and_no_flag_for_one(client):
    """The area is still not served, and neither is a ``has_location``: a
    profile cannot be committed without an area, so the flag could never be
    false, and a branch nobody can take is a branch nobody tests
    (``docs/adr/0179`` §8)."""

    _, headers = await a_player(client)

    body = (await client.get(PROFILE_URL, headers=headers)).json()

    assert "location" not in body
    assert "has_location" not in body


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
# The location
# ---------------------------------------------------------------------------


async def test_a_fix_in_a_new_cell_moves_the_area_and_records_one_event(
    client, session_factory
):
    """Filip moved from Podgórze to Nowa Huta; the next launch puts the phone's
    position. `204` with no body: no route on this surface serves the area yet,
    and a write made silently on every launch is not the one to start
    (``docs/adr/0174`` §6)."""

    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(LOCATION_URL, json=AWAY_FIX, headers=headers)

    assert response.status_code == 204, response.text
    assert response.content == b""
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 1
    moved = stream[-1]
    assert moved.event_type == "player_profile.location_changed"
    assert (moved.payload["latitude"], moved.payload["longitude"]) == AWAY_CELL


async def test_a_fix_rounding_to_the_stored_cell_answers_204_and_records_nothing(
    client, session_factory
):
    """The time after that: a different reading in the same cell. The aggregate's
    no-op rule is what makes a write on every launch cost nothing, and the
    route answers as if it had moved — a client cannot tell and need not."""

    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        LOCATION_URL,
        json={"latitude": 51.5099, "longitude": -0.1310},
        headers=headers,
    )

    assert response.status_code == 204, response.text
    assert await stream_length(session_factory, player_id) == before


async def test_the_precise_fix_is_nowhere_in_the_stream(client, session_factory):
    """*The precise fix that produced it is never a shareable value* — asserted
    against every row of the stream rather than the one event, because the
    commit and the move are two writers and the rule is the value object's."""

    player_id, headers = await a_player(client)
    await client.put(LOCATION_URL, json=AWAY_FIX, headers=headers)

    for row in await stream_of(session_factory, player_id):
        for precise in (*HOME_FIX.values(), *AWAY_FIX.values()):
            assert precise not in row.payload.values(), (row.event_type, precise)


async def test_a_fix_outside_the_world_is_refused_at_the_boundary(client):
    _, headers = await a_player(client)

    response = await client.put(
        LOCATION_URL, json={"latitude": 91.0, "longitude": 0.0}, headers=headers
    )

    assert response.status_code == 422


async def test_there_is_no_patch_for_the_location(client):
    _, headers = await a_player(client)

    response = await client.patch(LOCATION_URL, json=AWAY_FIX, headers=headers)

    assert response.status_code == 405


async def test_the_location_cannot_be_written_without_a_profile(client):
    """A cold start before onboarding's second part: the entry gate is still
    sending this player into it, and there is no cell to move."""

    headers = await a_signed_in_player(client, "unplaced")

    response = await client.put(LOCATION_URL, json=AWAY_FIX, headers=headers)

    assert response.status_code == 404
    assert response.json()["code"] == "player_profile_not_found"


async def test_the_location_needs_a_token(client):
    assert (await client.put(LOCATION_URL, json=AWAY_FIX)).status_code == 401


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


def test_the_surface_is_a_read_a_week_a_radius_a_location_and_nothing_else():
    """Map Decision 12, asserted against the routes rather than against prose.

    Tags, photos, gender and gender preference all have aggregate methods and
    **no route**, deliberately: they belong to You, which is not built. The
    location is the exception and it is not You's — it is the cold start's
    (``docs/adr/0174`` §6). A fifth route appearing on this router without its
    ticket is what this test is here to catch.
    """

    from app.modules.player_profile.presentation.profile_surface_routes import router

    assert {(route.path, tuple(sorted(route.methods))) for route in router.routes} == {
        ("/players/me/profile", ("GET",)),
        ("/players/me/availability", ("PUT",)),
        ("/players/me/search-radius", ("PUT",)),
        ("/players/me/location", ("PUT",)),
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
