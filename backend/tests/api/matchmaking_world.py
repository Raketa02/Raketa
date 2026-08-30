"""A city to search in, built the way the platform builds one.

Every test in ``test_searches.py`` needs the same four things and varies one of
them, so the four are written once here.

**The searcher goes through the real routes.** Sign-up, sign-in, the profile
commit and a rating from a real assessment run — because the searcher's facts are
read live from the aggregates at request time, and a searcher assembled any other
way would be testing the fixture rather than the read.

**The candidates go in through the log.** They are index rows, and the index is a
fold of the event store — so a candidate is a handful of appended contracts,
tailed exactly as the projection tails them in production. That is also the only
way to give one a chosen Level, a chosen grid or a chosen area: the questionnaire
does not take dictation.

**The searcher's declaration goes through a route too**, now that ADR-0094's
`PUT /api/v1/play-intents/{sport}` exists. It was the one seam here that was not
a route — appended to the log at the stream id the repository derives — and it
was written down as a handoff rather than a shortcut. The handoff has landed, so
the whole searcher is built the way the platform builds one and nothing in this
module fabricates a fact about them.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from app.kernel import Sport
from app.modules.matchmaking.infrastructure.pass_model import PassORM
from app.modules.matchmaking.infrastructure.prompt_decline_model import (
    PromptDeclineORM,
)
from app.modules.matchmaking.infrastructure.search_model import (
    SearchCandidateORM,
    SearchORM,
)
from app.modules.player_profile.domain.events import (
    PlayerProfileCreated,
    PlayIntentDeclared,
    ProposalsOptInAnswered,
)
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
)
from app.modules.rating.domain.events import RatingInitialised
from tests.unit.candidate_index_fixtures import TickingClock, append, build_tail

#: London, at the platform's own coarse precision. Every distance in these tests
#: is measured from here.
CENTRE = (51.51, -0.13)

#: A moment inside every candidate's newcomer window is *not* what these tests
#: want by default — the window tightens the level gate for the whole pairing —
#: so profiles are committed a good while before the searches run.
LONG_AGO = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)

SPORT = Sport.PADEL

#: Two tags the platform actually serves, on opposite sides of the style/vibe
#: split, so a candidate can be made to look competitive or sociable.
COMPETITIVE_TAGS = ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")
SOCIABLE_TAGS = ("HERE_FOR_THE_SOCIAL", "PLAYS_FOR_FUN")

#: A grid that overlaps the searcher's on two cells of the twenty-one.
SHARED_SLOTS = ("2:EVENING", "6:MORNING")


async def register(client, name: str) -> tuple[UUID, str]:
    """Sign one player up and in. Returns their id and a bearer token."""

    signup = await client.post(
        "/api/v1/users",
        json={
            "email": f"{name}@example.com",
            "password1": "hunter22!",
            "password2": "hunter22!",
            "nickname": name,
            "adult_attested": True,
        },
    )
    assert signup.status_code == 201, signup.text
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": "hunter22!"},
    )
    assert login.status_code == 200, login.text
    return UUID(signup.json()["id"]), login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def commit_profile(client, token: str, **overrides) -> None:
    """The searcher's own profile, through the route the client uses."""

    body = {
        "social_tag_ids": list(COMPETITIVE_TAGS),
        "photo_ids": [],
        "availability": [
            {"day": 2, "part": "EVENING"},
            {"day": 6, "part": "MORNING"},
        ],
        "location": {"latitude": CENTRE[0], "longitude": CENTRE[1]},
        "search_radius_km": 10,
        "proposals_opt_in": {"accepted": True, "copy_version": "proposals-2026-08"},
        "gender": "WOMAN",
    }
    body.update(overrides)
    response = await client.post(
        "/api/v1/players/me/profile",
        json=body,
        headers={**auth(token), "Idempotency-Key": f"commit-{token[:12]}"},
    )
    assert response.status_code == 201, response.text


async def rate(client, token: str, sport: Sport = SPORT) -> float:
    """The shortest honest path to a stored rating, and the μ it produced."""

    created = (
        await client.post(
            "/api/v1/assessments", json={"sport": sport.value}, headers=auth(token)
        )
    ).json()
    await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/answers",
        json={"question_id": created["question"]["id"], "option_id": "never-played"},
        headers=auth(token),
    )
    done = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/completion",
        headers=auth(token),
    )
    assert done.status_code == 200, done.text
    return float(done.json()["result"]["mu"])


async def declare_intent(
    client,
    token: str,
    *,
    intent: str = "COMPETITIVE",
    sport: Sport = SPORT,
) -> None:
    """The searcher's declaration, through ADR-0094's own route.

    ``RATING_TAIL`` because that is where a first declaration is made — this is
    called straight after ``rate``, which is the run whose tail asks.
    """

    response = await client.put(
        f"/api/v1/play-intents/{sport.value}",
        json={"intent": intent, "surface": "RATING_TAIL"},
        headers=auth(token),
    )
    assert response.status_code == 200, response.text


async def a_searcher(
    client,
    name: str = "searcher",
    *,
    intent: str = "COMPETITIVE",
) -> dict:
    """One player, ready to search: profile, rating and declaration.

    Every one of the three through the route a person would use, so a searcher
    is the searcher the platform makes rather than the one this file describes.

    ``intent`` is a parameter rather than something a test declares afterwards
    because the deck is the surface that cares: it reads the declaration instead
    of a mode, so *no preference* is a case it wants at birth. Declaring again
    afterwards would work — the route is unkeyed and re-declaring is an edit —
    but it would put a second event on a stream no test meant to give a history.
    """

    player_id, token = await register(client, name)
    await commit_profile(client, token)
    mu = await rate(client, token)
    await declare_intent(client, token, intent=intent)
    return {"id": player_id, "token": token, "mu": mu}


async def a_candidate(client, session_factory, name: str, **facts) -> UUID:
    """One person in the city. **Their id, because that is what a test asserts on.**"""

    player_id, _ = await a_signed_in_candidate(client, session_factory, name, **facts)
    return player_id


async def a_signed_in_candidate(
    client,
    session_factory,
    name: str,
    *,
    mu: float,
    latitude: float = CENTRE[0],
    longitude: float = CENTRE[1],
    tags: tuple[str, ...] = COMPETITIVE_TAGS,
    photo_ids: tuple[UUID, ...] = (),
    availability: tuple[str, ...] = SHARED_SLOTS,
    radius_km: int = 25,
    gender: str = "WOMAN",
    gender_preference: str = "ANY",
    intent: str | None = "COMPETITIVE",
    at: datetime = LONG_AGO,
) -> tuple[UUID, str]:
    """The same person, **and a bearer token for them.**

    They are registered through the route because the card reads a **nickname**
    from ``users``, which the index does not tail — and a candidate with no
    nickname is a row the search drops rather than a row it shows blank. That
    registration produces a token, and it is handed back here for the one thing
    only a candidate can do for themselves: block another candidate, which is a
    pair no shortlist ever gated.
    """

    player_id, token = await register(client, name)
    await append(
        session_factory,
        PlayerProfileCreated(
            player_id=player_id,
            social_tags=tags,
            photo_ids=tuple(str(photo_id) for photo_id in photo_ids),
            availability=availability,
            latitude=latitude,
            longitude=longitude,
            search_radius_km=radius_km,
            idempotency_key=f"key-{player_id}",
            occurred_at=at,
            gender=gender,
            gender_preference=gender_preference,
        ),
        # **A profile's stream id is the player id itself**, and the card is
        # assembled from the profile port rather than from the index — so a
        # profile filed under a random id is one the card source cannot load,
        # and every candidate here would silently have no photograph.
        aggregate_type=PLAYER_PROFILE_AGGREGATE,
        aggregate_id=player_id,
    )
    await append(
        session_factory,
        ProposalsOptInAnswered(player_id, True, "v1", "ONBOARDING", at),
    )
    await append(session_factory, _rating(player_id, mu=mu, at=at))
    if intent is not None:
        await append(
            session_factory,
            PlayIntentDeclared(player_id, SPORT.value, intent, "RATING_TAIL", at),
        )
    return player_id, token


async def block_between(client, token: str, player_id: UUID):
    """One player blocking another, through the route a person would use."""

    return await client.post(
        "/api/v1/blocks",
        json={"player_id": str(player_id), "surface": "SHORTLIST"},
        headers=auth(token),
    )


def _rating(player_id: UUID, *, mu: float, at: datetime) -> RatingInitialised:
    return RatingInitialised(
        rating_id=UUID(int=abs(hash((player_id, mu))) % (1 << 128)),
        player_id=player_id,
        sport=SPORT.value,
        mu=mu,
        sigma=0.34,
        confidence=62,
        range_low=mu - 0.3,
        range_high=mu + 0.3,
        band_name="Improver",
        band_lower=2.5,
        band_upper=3.0,
        status="INITIAL_ESTIMATE",
        engine_version="v3",
        source_assessment_id=UUID(int=abs(hash((mu, player_id))) % (1 << 128)),
        occurred_at=at,
    )


async def fold_the_log(session_factory, candidate_source) -> None:
    """Tail everything appended so far, then publish the container a search binds.

    Two steps because they are two things in production too: the projection
    advances on its own loop, and each worker refreshes its own copy on another.
    A test that skipped the second would search an index that had been built and
    never handed over.

    The reader's clock starts at **now** rather than at the shared fixture's
    fixed morning. ``caught_up_at`` is what the staleness ladder reads, and a
    reader that believed it last caught up yesterday would put every search in
    this module past the twenty-four-hour refusal — which would be the fixture
    testing the ladder rather than the ladder testing itself.
    """

    tail = build_tail(clock=TickingClock(datetime.now(timezone.utc)))
    async with session_factory() as session:
        while (await tail.tick(session)).events_applied:
            pass
    await candidate_source.refresh()


async def recorded_searches(session_factory) -> list[SearchORM]:
    async with session_factory() as session:
        rows = await session.execute(select(SearchORM).order_by(SearchORM.at))
        return list(rows.scalars())


async def recorded_candidates(
    session_factory, search_id: UUID
) -> list[SearchCandidateORM]:
    async with session_factory() as session:
        rows = await session.execute(
            select(SearchCandidateORM)
            .where(SearchCandidateORM.search_id == search_id)
            .order_by(SearchCandidateORM.band, SearchCandidateORM.position)
        )
        return list(rows.scalars())


async def search(
    client,
    token: str,
    mode: str = "COMPETITIVE",
    sport: Sport = SPORT,
    *,
    availability_override: list[dict] | None = None,
    offered_by_search_id: str | None = None,
    rung: str | None = None,
):
    """One tap. The three optional asks are **omitted** unless a test sends one.

    Omitted rather than sent as null, because that is the only spelling the
    contract has: a client says *use my profile's week* by not mentioning one.
    """

    body: dict = {"sport": sport.value, "mode": mode}
    if availability_override is not None:
        body["availability_override"] = availability_override
    if offered_by_search_id is not None:
        body["offered_by_search_id"] = offered_by_search_id
    if rung is not None:
        body["rung"] = rung
    return await client.post("/api/v1/searches", json=body, headers=auth(token))


async def express_interest(
    client,
    token: str,
    *,
    player_id: UUID,
    search_id: str,
    sport: Sport = SPORT,
):
    """One *Let's play* tap, with the origin key the route requires."""

    return await client.post(
        "/api/v1/interest",
        json={
            "sport": sport.value,
            "player_id": str(player_id),
            "search_id": str(search_id),
        },
        headers=auth(token),
    )


async def read_interest(client, token: str):
    return await client.get("/api/v1/interest", headers=auth(token))


async def deck(
    client,
    token: str,
    sport: Sport = SPORT,
    *,
    availability_override: list[dict] | None = None,
):
    """One deal. **There is still no mode to send** — the deck reads a declaration.

    The week is the one ask beside the sport, omitted unless a test sends one,
    for the reason the search's are: a client says *use my profile's week* by not
    mentioning one.
    """

    body: dict = {"sport": sport.value}
    if availability_override is not None:
        body["availability_override"] = availability_override
    return await client.post("/api/v1/deck", json=body, headers=auth(token))


async def pass_on(
    client,
    token: str,
    *,
    player_id: UUID,
    search_id: str,
    sport: Sport = SPORT,
):
    """One *not today*, with the origin key the route requires."""

    return await client.post(
        "/api/v1/passes",
        json={
            "sport": sport.value,
            "player_id": str(player_id),
            "search_id": str(search_id),
        },
        headers=auth(token),
    )


async def recorded_passes(session_factory) -> list[PassORM]:
    """Every pass row, read straight out of the table.

    The only way to see one at all: no route returns a pass, to anybody, which is
    exactly the promise these tests are asserting — so the assertion has to reach
    past the wire, and reaching past it here rather than in each test is what
    keeps that reach deliberate."""

    async with session_factory() as session:
        rows = await session.execute(
            select(PassORM).order_by(PassORM.passed_at)
        )
        return list(rows.scalars())


async def decline_prompt(
    client,
    token: str,
    *,
    prompt: str,
    sport: Sport = SPORT,
):
    """One *not now*. **No origin key and no window to name.**"""

    return await client.post(
        "/api/v1/prompt-declines",
        json={"prompt": prompt, "sport": sport.value},
        headers=auth(token),
    )


async def recorded_declines(session_factory) -> list[PromptDeclineORM]:
    """Every decline row, read straight out of the table.

    The only way to see one at all: no route returns a decline, to anybody — so
    the assertion has to reach past the wire, and reaching past it here rather
    than in each test is what keeps that reach deliberate."""

    async with session_factory() as session:
        rows = await session.execute(
            select(PromptDeclineORM).order_by(PromptDeclineORM.declined_at)
        )
        return list(rows.scalars())


async def a_yes(client, session_factory, candidate_source, *, sender, towards):
    """Everything a yes needs: the sender searches, then says it.

    Written once because three tests need a *Let's play* that already stands and
    vary only what happens next — and because a yes with an origin key made up by
    a test would be testing a route that does not exist.
    """

    found = await search(client, sender["token"])
    assert found.status_code == 200, found.text
    said = await express_interest(
        client,
        sender["token"],
        player_id=towards,
        search_id=found.json()["search"]["search_id"],
    )
    assert said.status_code in (200, 201), said.text
    return said


#: How long after the log's last event a search is taken to run. Comfortably
#: inside the staleness ladder's first rung, so nothing here is testing the
#: refusal by accident.
A_MOMENT_LATER = timedelta(minutes=1)


def override(client, dependency, factory) -> None:
    """Replace one dependency on the running application, for one test.

    The `client` fixture holds the app rather than exposing it, so reaching for
    it is a private access — written **once, here**, with the reason attached,
    rather than three times in a test module. What it buys is the only way to
    drive a refusal that lives behind a provider: the fail-closed reads and the
    index are wired per request, so breaking one on purpose is a dependency
    override and nothing else.
    """

    client._transport.app.dependency_overrides[dependency] = factory  # noqa: SLF001


def rewind_the_index(source, by: timedelta) -> None:
    """Move the index's *caught up at* backwards, without moving the clock.

    The staleness ladder reads the gap between the two, and a test that moved the
    clock instead would also move every newcomer window and every activity
    reading in the same search — so it would be testing four things and
    asserting one.

    It rebinds the container the way a refresh does rather than mutating one,
    because a snapshot is replaced and never edited.
    """

    source._snapshots = {  # noqa: SLF001 — a container has no setter, by design
        partition: replace(snapshot, caught_up_at=snapshot.caught_up_at - by)
        for partition, snapshot in source._snapshots.items()  # noqa: SLF001
    }
    source._caught_up_at = source._caught_up_at - by  # noqa: SLF001


async def read_back(client, token: str, search_id):
    return await client.get(
        f"/api/v1/searches/{search_id}", headers=auth(token)
    )


def an_empty_index(source):
    """The same index, holding nobody. **A source, not a mutated snapshot.**

    A container is replaced and never edited, so this wraps rather than reaching
    into one — and it keeps the partition's own version and *caught up at*, so a
    test using it is testing an index that holds nobody rather than an index that
    is broken or a day behind.
    """

    class Empty:
        def snapshot(self, partition):
            return replace(source.snapshot(partition), rows=())

    return Empty()


class HoldingEverybody:
    """``AccountHoldQuery`` saying yes about whoever it is asked about.

    The hold has no producer in this build — nothing can hold anybody, which is
    why the gate ships true-over-empty — so the only way to drive it over HTTP is
    to replace the query. It answers **only about ids it was asked about**, which
    is the port's own contract and not a shortcut taken here.
    """

    async def held_among(self, player_ids):
        return frozenset(player_ids)


def hold_everybody(client) -> None:
    from app.modules.matchmaking.presentation.dependencies import (
        get_account_hold_query,
    )

    override(client, get_account_hold_query, HoldingEverybody)


def hold_only(client, *player_ids) -> None:
    """A hold on these players and **nobody else** — the reader included out.

    Which is what makes the candidate-side assertion mean something: a stand-in
    that held everybody would refuse the request at the entry point and never
    reach the row.
    """

    from app.modules.matchmaking.presentation.dependencies import (
        get_account_hold_query,
    )

    held = frozenset(player_ids)

    class Holding:
        async def held_among(self, asked):
            return frozenset(asked) & held

    override(client, get_account_hold_query, Holding)


def may_not_show(client, *player_ids) -> None:
    """``users`` refusing to have these candidates shown, and saying so to nobody."""

    from app.modules.matchmaking.presentation.dependencies import (
        get_account_status_query,
    )

    unshowable = frozenset(player_ids)

    class Unshowable:
        async def may_not_be_shown(self, candidate_ids):
            return frozenset(candidate_ids) & unshowable

    override(client, get_account_status_query, Unshowable)


async def _profile(session_factory, player_id: UUID):
    """The searcher's own profile, replayed from the log.

    There is no `GET` for it — onboarding writes one and nothing reads it back
    over HTTP yet — so *the profile is untouched* is asserted where the profile
    actually lives, which is also the only place a silent write would show up.
    """

    from app.bootstrap.composition import (
        build_domain_event_store,
        build_event_publisher,
        build_player_profile_repository,
    )

    async with session_factory() as session:
        repository = build_player_profile_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        return await repository.load(player_id)


async def saved_radius_km(session_factory, player_id: UUID) -> int:
    profile = await _profile(session_factory, player_id)
    assert profile is not None
    return profile.search_radius.kilometres


async def saved_grid(session_factory, player_id: UUID) -> tuple[str, ...]:
    profile = await _profile(session_factory, player_id)
    assert profile is not None
    return profile.availability.codes


async def lineup(
    client,
    token: str,
    mode: str = "COMPETITIVE",
    sport: Sport = SPORT,
    *,
    locked_seats: list[UUID] | None = None,
    availability_override: list[dict] | None = None,
):
    """One ⚡. **`locked_seats` is the whole difference** between the two surfaces.

    Omitted rather than sent empty when a test is not hand-seating anybody, for
    the same reason the search's three optional asks are: a client says *fill
    every seat* by not naming one.
    """

    body: dict = {"sport": sport.value, "mode": mode}
    if locked_seats is not None:
        body["locked_seats"] = [str(one) for one in locked_seats]
    if availability_override is not None:
        body["availability_override"] = availability_override
    return await client.post("/api/v1/lineups", json=body, headers=auth(token))


async def forecast(
    client,
    token: str,
    *,
    search_id: str,
    players: list[UUID],
    mode: str = "COMPETITIVE",
    sport: Sport = SPORT,
):
    """One composed four, priced. **It creates no search**, which is the point."""

    return await client.post(
        "/api/v1/forecasts",
        json={
            "sport": sport.value,
            "mode": mode,
            "search_id": str(search_id),
            "players": [str(one) for one in players],
        },
        headers=auth(token),
    )
