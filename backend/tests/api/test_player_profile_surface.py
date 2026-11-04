"""The profile surface reads and writes: one read, one `PUT` per fact.

The Play screen edited two facts here — the week and the per-sport Play intent —
and until these routes existed it could read neither and write neither. What is
asserted here is the shape #226 settled: **one read carrying both**, and **one
unkeyed `PUT` per changeable fact**, because a blank grid is a legal value and a
`PATCH` field that may be `null` would mean both *leave my week alone* and
*clear my week*. The search radius was a third, and went with the ranking that
read it (#581).

One `PUT` is the **cold start's** and no screen's: the location
(``docs/adr/0174`` §6), put silently on every launch, which is why the
same-cell case answering `204` with nothing appended is the assertion that
matters most.

The fact a screen needs from elsewhere — *which sports am I rated in* — is
`GET /api/v1/ratings` and is not re-served here.

**The read is the You tab's too** (``docs/adr/0179`` §8): it grew by the tags,
the photos with their verdicts, the intro, and the owner's own gender and
preference — the one shape those two may cross on (§4).
What is asserted about it here is each field's spelling of absence, because
that is what a client branches on: an empty ``photos`` list is served, an
unwritten intro is omitted, a photograph nobody looked at carries no verdict,
a pre-question profile carries no gender, and the location is still not there.

**And the five writes the tab needs land on the same surface** (§8): the tags,
the photos, the intro, the gender and the preference. The opt-in answered again
from ``PROFILE`` was a sixth, and went with the radius (#581). Each is the
aggregate's own transition behind one unkeyed ``PUT``, and what is asserted is
what a client branches on — the fact as stored coming back, the refusals the
commit already makes arriving under the same codes, and the stream growing by
exactly one event or by none. The two
gender writes and the intro's answer ``204``, because *served on one route and
no other* (§4) and *the card, the record and its author* (ADR-0170 §3) have to
stay literally true of the response shapes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.bootstrap.events import build_event_runtime
from app.infrastructure.events.event_store_model import EventStoreORM
from app.infrastructure.events.sqlalchemy_domain_event_store import (
    SqlAlchemyEventStore,
)
from app.kernel import Sport, Zone, instant
from app.modules.player_profile.domain.events import (
    PlayerProfileCreated,
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
from app.modules.player_profile.domain.weekly_hours import free_for_the_hour
from tests.api.administration_world import club_signs_up

PROFILE_URL = "/api/v1/players/me/profile"
WEEKLY_HOURS_URL = "/api/v1/players/me/weekly-hours"
WARSAW = Zone("Europe/Warsaw")
RADIUS_URL = "/api/v1/players/me/search-radius"
LOCATION_URL = "/api/v1/players/me/location"
TAGS_URL = "/api/v1/players/me/social-tags"
PHOTOS_URL = "/api/v1/players/me/photos"
INTRO_URL = "/api/v1/players/me/intro"
GENDER_URL = "/api/v1/players/me/gender"
PREFERENCE_URL = "/api/v1/players/me/gender-preference"
RELIABILITY_FILTER_URL = "/api/v1/players/me/reliability-filter"
OPT_IN_URL = "/api/v1/players/me/proposals-opt-in"

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
        "weekly_hours": [
            {"day": 2, "hour": 19},
            {"day": 6, "hour": 10},
        ],
        "location": HOME_FIX,
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


async def test_the_read_carries_the_week_and_the_declaration(client):
    _, headers = await a_player(client)
    await client.put(
        intents_url(Sport.PADEL),
        json={"intent": "COMPETITIVE", "surface": "RATING_TAIL"},
        headers=headers,
    )

    response = await client.get(PROFILE_URL, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["weekly_hours"] == [
        {"day": 2, "hour": 19},
        {"day": 6, "hour": 10},
    ]
    assert body["play_intents"] == {"PADEL": "COMPETITIVE"}
    # Neither a radius nor a suggestions answer: both went with the ranking
    # that read them (#581).
    assert "search_radius_km" not in body
    assert "proposals_opt_in" not in body


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
    verdicts, the intro, and the owner's own gender and preference (§4). Every
    row on the tab draws its live line from this one response, and *Who you
    play with* opens with the right radio pre-selected.
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
                    weekly_hours=("2:19",),
                    latitude=51.51,
                    longitude=-0.13,
                    idempotency_key="commit-before-the-question",
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
        WEEKLY_HOURS_URL,
        json={"weekly_hours": [{"day": 1, "hour": 10}]},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["weekly_hours"] == [{"day": 1, "hour": 10}]
    read = (await client.get(PROFILE_URL, headers=headers)).json()
    assert read["weekly_hours"] == [{"day": 1, "hour": 10}]


async def test_the_week_saved_is_the_week_a_court_hour_is_read_against(
    client, session_factory
):
    """*Free for the whole hour*, read off the week this route stored.

    The rule is one function in the Player profile's domain that the proposer,
    posting and the rescue board will each ask (ADR-0189 §5); what this pins is
    that the week it reads is the week a player saved here. Tuesday 19:00 and
    20:00 cover 19:00–20:00 and 19:30–20:30 — never 18:30, whose first half is
    unticked, nor 20:30, whose second half is.
    """

    from app.bootstrap.composition import (
        build_domain_event_store,
        build_event_publisher,
        build_player_profile_repository,
    )

    player_id, headers = await a_player(client)
    saved = await client.put(
        WEEKLY_HOURS_URL,
        json={"weekly_hours": [{"day": 2, "hour": 19}, {"day": 2, "hour": 20}]},
        headers=headers,
    )
    assert saved.status_code == 200, saved.text
    async with session_factory() as session:
        profile = await build_player_profile_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).load(player_id)
    assert profile is not None

    def free_from(utc: str) -> bool:
        # 2026-09-29 is a Tuesday, and Warsaw is two hours ahead of UTC then.
        start = instant(datetime.fromisoformat(utc).replace(tzinfo=timezone.utc))
        return free_for_the_hour(profile.weekly_hours, start=start, zone=WARSAW)

    assert free_from("2026-09-29T17:00:00")
    assert free_from("2026-09-29T17:30:00")
    assert not free_from("2026-09-29T16:30:00")
    assert not free_from("2026-09-29T18:30:00")


async def test_a_cleared_week_is_a_legal_value_on_the_write(client):
    """The floor binds the commit and not every later edit, and this is the
    route that finally says so: `WeeklyHours.edited` is what the boundary
    builds through, so nothing ticked is recorded rather than refused."""

    _, headers = await a_player(client)

    response = await client.put(
        WEEKLY_HOURS_URL, json={"weekly_hours": []}, headers=headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["weekly_hours"] == []
    assert (await client.get(PROFILE_URL, headers=headers)).json()["weekly_hours"] == []


async def test_the_week_comes_back_folded_and_in_reading_order(client):
    """Why the write answers with the week rather than with no content: a
    repeated hour is collapsed and the order is the platform's — day, then hour,
    nine before ten — so a client that kept what it sent would hold a week the
    profile does not."""

    _, headers = await a_player(client)

    response = await client.put(
        WEEKLY_HOURS_URL,
        json={
            "weekly_hours": [
                {"day": 3, "hour": 19},
                {"day": 1, "hour": 10},
                {"day": 3, "hour": 19},
                {"day": 1, "hour": 9},
            ]
        },
        headers=headers,
    )

    assert response.json()["weekly_hours"] == [
        {"day": 1, "hour": 9},
        {"day": 1, "hour": 10},
        {"day": 3, "hour": 19},
    ]


@pytest.mark.parametrize(
    "cell",
    [{"day": 1, "hour": 6}, {"day": 1, "hour": 23}, {"day": 1, "part": "MORNING"}],
    ids=["before-seven", "the-hour-after-the-grid", "a-part-of-the-day"],
)
async def test_a_cell_that_is_not_an_hour_of_the_week_is_refused(client, cell):
    """Sixteen cells a day, 07:00 to 23:00 — and a part of the day is not a cell
    any more (ADR-0189 §5)."""

    _, headers = await a_player(client)

    response = await client.put(
        WEEKLY_HOURS_URL, json={"weekly_hours": [cell]}, headers=headers
    )

    assert response.status_code == 422, response.text


async def test_the_old_part_of_day_write_is_gone(client):
    """``PUT /players/me/availability`` was replaced, not kept beside it: two
    writes for one week would be two answers to *which one is the week*."""

    _, headers = await a_player(client)

    response = await client.put(
        "/api/v1/players/me/availability",
        json={"availability": [{"day": 1, "part": "MORNING"}]},
        headers=headers,
    )

    assert response.status_code in (404, 405)


async def test_the_same_week_twice_lands_the_same_state(client, session_factory):
    """Unkeyed and idempotent, which is what makes an idempotency key pointless
    here: the second request lands the state the first did and the aggregate's
    no-op rule means it appends nothing."""

    player_id, headers = await a_player(client)
    week = {"weekly_hours": [{"day": 4, "hour": 15}]}

    first = await client.put(WEEKLY_HOURS_URL, json=week, headers=headers)
    after_first = await stream_length(session_factory, player_id)
    second = await client.put(WEEKLY_HOURS_URL, json=week, headers=headers)

    assert first.json() == second.json()
    assert await stream_length(session_factory, player_id) == after_first


async def test_there_is_no_patch_for_the_week(client):
    """`null` versus absent is fatal on this field specifically: a blank week is
    a legal value, so `{"weekly_hours": null}` would mean both *leave it alone*
    and *clear my week*."""

    _, headers = await a_player(client)

    response = await client.patch(
        WEEKLY_HOURS_URL, json={"weekly_hours": []}, headers=headers
    )

    assert response.status_code == 405


async def test_the_week_cannot_be_written_without_a_profile(client):
    headers = await a_signed_in_player(client, "weekless")

    response = await client.put(
        WEEKLY_HOURS_URL, json={"weekly_hours": []}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["code"] == "player_profile_not_found"


# ---------------------------------------------------------------------------
# The radius and the opt-in, gone (#581)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "body"),
    [
        (RADIUS_URL, {"search_radius_km": 22}),
        (OPT_IN_URL, {"accepted": True, "copy_version": "proposals-opt-in.v3"}),
    ],
    ids=["radius", "opt-in"],
)
async def test_the_radius_and_the_opt_in_are_no_longer_written(client, url, body):
    """Only the "who fits whom" ranking read either answer, and it is gone —
    so the two writes the You tab and the old search screen used are too."""

    _, headers = await a_player(client)

    response = await client.put(url, json=body, headers=headers)

    assert response.status_code == 404, response.text


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
# A club in place of a reading (docs/adr/0200 §10)
# ---------------------------------------------------------------------------


async def test_a_picked_club_moves_the_area_to_the_club_s_cell(client, session_factory):
    """Filip turned the phone's location off and picks a club in Warsaw near
    where he plays now, from *You › Where you play*: his area is that club's
    point rounded to the cell, and the club's precise point is nowhere in his
    stream."""

    club_id, _ = await club_signs_up(client, point=tuple(AWAY_FIX.values()))
    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        LOCATION_URL, json={"club_id": club_id}, headers=headers
    )

    assert response.status_code == 204, response.text
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 1
    moved = stream[-1]
    assert moved.event_type == "player_profile.location_changed"
    assert (moved.payload["latitude"], moved.payload["longitude"]) == AWAY_CELL
    for row in stream:
        for precise in AWAY_FIX.values():
            assert precise not in row.payload.values(), (row.event_type, precise)


async def test_the_next_reading_in_another_cell_replaces_a_picked_club(
    client, session_factory
):
    """The cold start is unchanged (``docs/adr/0174`` §6): once Ania allows
    location, the phone's reading replaces the club she picked at sign-up."""

    club_id, _ = await club_signs_up(client, point=tuple(AWAY_FIX.values()))
    player_id, headers = await an_account(client, "picked")
    await a_committed_profile(client, headers, "picked", location={"club_id": club_id})

    response = await client.put(LOCATION_URL, json=HOME_FIX, headers=headers)

    assert response.status_code == 204, response.text
    moved = (await stream_of(session_factory, player_id))[-1]
    assert moved.event_type == "player_profile.location_changed"
    assert (moved.payload["latitude"], moved.payload["longitude"]) == (51.51, -0.13)


async def test_a_club_that_is_not_in_raketa_moves_nothing(client, session_factory):
    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        LOCATION_URL, json={"club_id": str(uuid4())}, headers=headers
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "location_club_unknown"
    assert response.json()["details"] == {"field": "club_id"}
    assert await stream_length(session_factory, player_id) == before


@pytest.mark.parametrize(
    "body",
    [
        {**AWAY_FIX, "club_id": str(uuid4())},
        {"longitude": 21.0122, "club_id": str(uuid4())},
        {"latitude": 52.2297},
        {},
    ],
    ids=["both forms", "half a reading and a club", "half a reading", "neither"],
)
async def test_a_move_is_a_reading_or_a_club_and_exactly_one(client, body):
    _, headers = await a_player(client)

    response = await client.put(LOCATION_URL, json=body, headers=headers)

    assert response.status_code == 422, response.text


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
    """A preference: re-declaring `COMPETITIVE` over
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


# ---------------------------------------------------------------------------
# The You tab's six writes (docs/adr/0179 §6, §8)
# ---------------------------------------------------------------------------


async def test_the_tags_are_replaced_whole_and_come_back_in_the_vocabularys_order(
    client, session_factory
):
    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        TAGS_URL,
        json={"social_tags": ["QUIET_AND_FOCUSED", "HERE_TO_COMPETE"]},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    served = response.json()["social_tags"]
    assert set(served) == {"HERE_TO_COMPETE", "QUIET_AND_FOCUSED"}
    read = (await client.get(PROFILE_URL, headers=headers)).json()
    assert read["social_tags"] == served, "the write answers what the read serves"
    assert await stream_length(session_factory, player_id) == before + 1


async def test_the_same_selection_twice_appends_no_event(client, session_factory):
    player_id, headers = await a_player(client)
    selection = {"social_tags": ["HERE_TO_IMPROVE", "PLAYS_TO_WIN"]}

    first = await client.put(TAGS_URL, json=selection, headers=headers)
    after_first = await stream_length(session_factory, player_id)
    second = await client.put(TAGS_URL, json=selection, headers=headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert await stream_length(session_factory, player_id) == after_first


async def test_tags_are_refused_as_the_commit_refuses_them(client):
    """An id outside the served vocabulary, a count outside the served bounds,
    and the same id twice — each under the commit's own code, because the
    picker on the tab is the onboarding step reused and a control is not a
    validation."""

    _, headers = await a_player(client)

    unknown = await client.put(
        TAGS_URL, json={"social_tags": ["PLAYS_TO_WIN", "NOT_A_TAG"]}, headers=headers
    )
    too_few = await client.put(TAGS_URL, json={"social_tags": []}, headers=headers)
    twice = await client.put(
        TAGS_URL,
        json={"social_tags": ["PLAYS_TO_WIN", "PLAYS_TO_WIN"]},
        headers=headers,
    )

    assert (unknown.status_code, unknown.json()["code"]) == (400, "unknown_social_tag")
    assert (too_few.status_code, too_few.json()["code"]) == (
        400,
        "social_tag_selection_out_of_bounds",
    )
    assert (twice.status_code, twice.json()["code"]) == (400, "duplicate_social_tag")


async def test_the_photos_are_replaced_in_order_and_an_empty_list_clears(
    client, session_factory, photo_storage
):
    """Tomek promotes his second photograph, then lets both go: the first is
    the one a card shows, so the reorder is a change; the empty list is a real
    answer and the poster returns."""

    player_id, headers = await an_account(client, "photos")
    first = a_photo_held(photo_storage, player_id, {})
    second = a_photo_held(photo_storage, player_id, {})
    await a_committed_profile(
        client, headers, "photos", photo_ids=[str(first), str(second)]
    )
    before = await stream_length(session_factory, player_id)

    promoted = await client.put(
        PHOTOS_URL, json={"photo_ids": [str(second), str(first)]}, headers=headers
    )
    assert promoted.status_code == 200, promoted.text
    assert promoted.json() == {"photo_ids": [str(second), str(first)]}
    read = (await client.get(PROFILE_URL, headers=headers)).json()
    assert [photo["photo_id"] for photo in read["photos"]] == [str(second), str(first)]

    cleared = await client.put(PHOTOS_URL, json={"photo_ids": []}, headers=headers)
    assert cleared.status_code == 200, cleared.text
    assert cleared.json() == {"photo_ids": []}
    assert (await client.get(PROFILE_URL, headers=headers)).json()["photos"] == []
    assert await stream_length(session_factory, player_id) == before + 2


async def test_the_same_order_twice_appends_no_event(
    client, session_factory, photo_storage
):
    player_id, headers = await an_account(client, "same-photos")
    photo = a_photo_held(photo_storage, player_id, {})
    await a_committed_profile(client, headers, "same-photos", photo_ids=[str(photo)])
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        PHOTOS_URL, json={"photo_ids": [str(photo)]}, headers=headers
    )

    assert response.status_code == 200, response.text
    assert await stream_length(session_factory, player_id) == before


async def test_a_photograph_that_is_not_the_callers_is_refused(
    client, session_factory, photo_storage
):
    """The commit's check: another player's photo id and an imaginary one
    answer the same way, and nothing is recorded."""

    player_id, headers = await a_player(client, "mine")
    stranger, _ = await a_player(client, "theirs")
    theirs = a_photo_held(photo_storage, stranger, {})
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        PHOTOS_URL, json={"photo_ids": [str(theirs)]}, headers=headers
    )
    imaginary = await client.put(
        PHOTOS_URL, json={"photo_ids": [str(uuid4())]}, headers=headers
    )

    assert response.status_code == imaginary.status_code == 404, response.text
    assert response.json()["code"] == imaginary.json()["code"] == "photo_not_found"
    assert await stream_length(session_factory, player_id) == before


async def test_the_intro_is_replaced_trimmed_and_read_back(client, session_factory):
    player_id, headers = await an_account(client, "intro")
    await a_committed_profile(client, headers, "intro", intro="Moved from Wrocław.")
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        INTRO_URL, json={"intro": "  Will travel for a hard game.  "}, headers=headers
    )

    assert response.status_code == 204, response.text
    assert response.content == b""
    read = (await client.get(PROFILE_URL, headers=headers)).json()
    assert read["intro"] == "Will travel for a hard game.", "trimmed, read back"
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 1
    assert stream[-1].event_type == "player_profile.intro_changed"


async def test_null_withdraws_the_intro_and_the_read_omits_it(client, session_factory):
    """A removal is a write of **no intro** (``docs/adr/0179`` §6): recorded on
    the stream, and the read spells the absence the way it spells a line never
    written — omitted, never ``null`` and never ``""``."""

    player_id, headers = await an_account(client, "withdrawn")
    await a_committed_profile(client, headers, "withdrawn", intro="Moved from Wrocław.")
    before = await stream_length(session_factory, player_id)

    response = await client.put(INTRO_URL, json={"intro": None}, headers=headers)

    assert response.status_code == 204, response.text
    assert "intro" not in (await client.get(PROFILE_URL, headers=headers)).json()
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 1
    assert stream[-1].payload["intro"] is None


async def test_the_same_line_twice_appends_no_event(client, session_factory):
    player_id, headers = await an_account(client, "same-line")
    await a_committed_profile(client, headers, "same-line", intro="Moved from Wrocław.")
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        INTRO_URL, json={"intro": "Moved from Wrocław."}, headers=headers
    )

    assert response.status_code == 204, response.text
    assert await stream_length(session_factory, player_id) == before


async def test_a_line_with_contact_is_refused_with_its_reason(client):
    _, headers = await a_player(client)

    response = await client.put(
        INTRO_URL, json={"intro": "WhatsApp me on 600 123 456"}, headers=headers
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "intro_not_admitted"
    assert response.json()["details"] == {"reason": "contains_contact"}


async def test_the_intro_field_is_required_so_that_null_is_said_and_not_forgotten(
    client,
):
    """``{}`` is a 422: *withdraw the line* has to be sent as ``null``, never
    arrived at by leaving the field out, or a client that forgot the field
    would be clearing lines."""

    _, headers = await a_player(client)

    assert (await client.put(INTRO_URL, json={}, headers=headers)).status_code == 422


async def test_the_gender_is_corrected_with_a_204_and_reads_back(
    client, session_factory
):
    """``204`` and no body, deliberately: the owner's read is the one shape
    that carries a gender value out (``docs/adr/0179`` §4), and the write does
    not become a second one."""

    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(GENDER_URL, json={"gender": "MAN"}, headers=headers)

    assert response.status_code == 204, response.text
    assert response.content == b""
    assert (await client.get(PROFILE_URL, headers=headers)).json()["gender"] == "MAN"
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 1
    assert stream[-1].event_type == "player_profile.gender_changed"


async def test_an_unchanged_gender_appends_no_event(client, session_factory):
    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(GENDER_URL, json={"gender": "WOMAN"}, headers=headers)

    assert response.status_code == 204, response.text
    assert await stream_length(session_factory, player_id) == before


async def test_a_gender_outside_the_closed_set_is_refused_at_the_boundary(client):
    _, headers = await a_player(client)

    response = await client.put(GENDER_URL, json={"gender": "OTHER"}, headers=headers)

    assert response.status_code == 422


async def test_the_preference_is_narrowed_with_a_204_and_reads_back(
    client, session_factory
):
    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        PREFERENCE_URL, json={"gender_preference": "WOMEN_ONLY"}, headers=headers
    )

    assert response.status_code == 204, response.text
    assert response.content == b""
    read = (await client.get(PROFILE_URL, headers=headers)).json()
    assert read["gender_preference"] == "WOMEN_ONLY"
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 1
    assert stream[-1].event_type == "player_profile.gender_preference_changed"


async def test_an_unchanged_preference_appends_no_event(client, session_factory):
    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        PREFERENCE_URL, json={"gender_preference": "ANY"}, headers=headers
    )

    assert response.status_code == 204, response.text
    assert await stream_length(session_factory, player_id) == before


async def test_the_reliability_filter_is_switched_on_and_off_with_a_204(
    client, session_factory
):
    """*Play only with players of at least High reliability*, then off — each
    its own event; the same value again records nothing (#661)."""

    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    on = await client.put(
        RELIABILITY_FILTER_URL, json={"minimum": "HIGH"}, headers=headers
    )
    again = await client.put(
        RELIABILITY_FILTER_URL, json={"minimum": "HIGH"}, headers=headers
    )
    off = await client.put(
        RELIABILITY_FILTER_URL, json={"minimum": None}, headers=headers
    )

    assert [on.status_code, again.status_code, off.status_code] == [204, 204, 204]
    assert on.content == b""
    stream = await stream_of(session_factory, player_id)
    assert len(stream) == before + 2
    assert [row.event_type for row in stream[-2:]] == [
        "player_profile.reliability_minimum_set",
        "player_profile.reliability_minimum_set",
    ]


@pytest.mark.parametrize("minimum", ["VERY_HIGH", "LOW", "RELIABLE"])
async def test_a_filter_the_switch_does_not_offer_is_refused_at_the_boundary(
    client, session_factory, minimum
):
    """*At least Medium*, *at least High* or off — the contract names the two
    bands and no other, so *at least Very high* never reaches the profile."""

    player_id, headers = await a_player(client)
    before = await stream_length(session_factory, player_id)

    response = await client.put(
        RELIABILITY_FILTER_URL, json={"minimum": minimum}, headers=headers
    )

    assert response.status_code == 422, response.text
    assert await stream_length(session_factory, player_id) == before


async def test_a_filter_left_out_is_refused_at_the_boundary(client):
    _, headers = await a_player(client)

    missing = await client.put(RELIABILITY_FILTER_URL, json={}, headers=headers)

    assert missing.status_code == 422


@pytest.mark.parametrize(
    ("url", "body"),
    [
        (TAGS_URL, {"social_tags": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"]}),
        (PHOTOS_URL, {"photo_ids": []}),
        (INTRO_URL, {"intro": "Late to the game."}),
        (GENDER_URL, {"gender": "MAN"}),
        (PREFERENCE_URL, {"gender_preference": "ANY"}),
        (RELIABILITY_FILTER_URL, {"minimum": "HIGH"}),
    ],
    ids=["tags", "photos", "intro", "gender", "preference", "reliability-filter"],
)
async def test_each_of_the_six_refuses_an_uncommitted_profile_and_needs_a_token(
    client, url, body
):
    """As the existing writes refuse: the recovery is onboarding's second
    part, which ``GET /users/me`` already sends a cold launch into."""

    headers = await a_signed_in_player(client, f"unonboarded-{url.rsplit('/', 1)[1]}")

    without_profile = await client.put(url, json=body, headers=headers)
    without_token = await client.put(url, json=body)

    assert without_profile.status_code == 404, without_profile.text
    assert without_profile.json()["code"] == "player_profile_not_found"
    assert without_token.status_code == 401


def test_the_surface_is_a_read_and_the_eight_writes_and_nothing_else():
    """Asserted against the routes rather than against prose.

    One read; the two writes the Play screens and the cold start had; the
    five the You tab needed (``docs/adr/0179`` §8) — every one of the
    aggregate's transitions under *Later changes, from the profile screen* has
    its route — and the reliability filter (#661). The radius and the opt-in had
    one each until #581. A tenth appearing on this router without its ticket is
    what this test is here to catch.
    """

    from app.modules.player_profile.presentation.profile_surface_routes import router

    assert {(route.path, tuple(sorted(route.methods))) for route in router.routes} == {
        ("/players/me/profile", ("GET",)),
        ("/players/me/weekly-hours", ("PUT",)),
        ("/players/me/location", ("PUT",)),
        ("/players/me/social-tags", ("PUT",)),
        ("/players/me/photos", ("PUT",)),
        ("/players/me/intro", ("PUT",)),
        ("/players/me/gender", ("PUT",)),
        ("/players/me/gender-preference", ("PUT",)),
        ("/players/me/reliability-filter", ("PUT",)),
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
