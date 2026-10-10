"""A group at a live club, its players, and the games proposed to them — the
few moves every proposals test makes (#538; the mechanics §5–§7).

**Every player is made the way the platform makes one**: signed up and named,
a profile committed, rated through an assessment, and — unless a test says
otherwise — a card saved through the three steps of the setup against the fake
provider. **Every answer is given over HTTP**, as the phone gives it.

**No route makes a proposal** — the engine will (#540) — so a test makes one the
way a seed does, through ``MakeProposal`` and ``DealVersion`` built by the
composition root over the test's database and clock.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**, so every hour is
a literal the calendar can check: the sixth is a Tuesday, the tenth a Saturday.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.bootstrap.composition import (
    build_deal_version,
    build_expire_proposals,
    build_make_proposal,
    build_run_out_the_time_to_pay,
)
from app.core.config import get_settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    CardBehaviour,
    EnteredCard,
)
from app.modules.proposals.application.commands import (
    DealVersionCommand,
    MakeProposalCommand,
)
from app.modules.proposals.domain.post import PostedFor
from app.modules.proposals.domain.proposal import Origin
from tests.api import players_world as players
from tests.api.club_courts_world import (
    a_desk,
    adds_a_court,
    chooses,
    confirms_settings,
    connects_payments,
    sets_hours,
    sets_prices,
)

WARSAW = ZoneInfo("Europe/Warsaw")

GROUPS = "/api/v1/groups"
LIVE_YESES = "/api/v1/players/me/live-yeses"
PAYMENT_METHODS = "/api/v1/players/me/payment-methods"
TERMS_IN_FORCE = "2026-09-29"


def warsaw(day: int, hour: int, month: int = 10) -> datetime:
    """An hour in Kraków in 2026, as an instant."""

    return instant(datetime(2026, month, day, hour, tzinfo=WARSAW))


MONDAY_MORNING = warsaw(5, 8)
#: Saturday 17:00 — a padel hour at 120 zł, so 30 zł a seat.
SATURDAY_FIVE = warsaw(10, 17)


def every_hour_of_the_week() -> list[tuple[int, int]]:
    return [(day, hour) for day in range(1, 8) for hour in range(7, 23)]


async def a_club_selling(client, **kwargs) -> str:
    """A live club selling one padel and one tennis court at every hour of the
    week — padel at 120 zł (30 zł a seat) unless told otherwise, tennis at 80 zł
    (40 zł a seat). Its id."""

    club_id, _ = await a_club_and_its_desk(client, **kwargs)
    return club_id


async def a_club_and_its_desk(
    client,
    *,
    name: str = "Bonarka Arena",
    email: str | None = None,
    way: str = "INSTANT",
    point: tuple[float, float] = (50.06, 19.95),
    paused: bool = False,
    hours: list[tuple[int, int]] | None = None,
    padel_grosze: int = 120_00,
    **settings,
) -> tuple[str, dict]:
    """``a_club_selling``'s club, and its desk's session — for a test that
    changes what the club sells afterwards. The desk signs in at ``email``, or
    at an address made of the club's name."""

    club_id, desk = await a_desk(
        client,
        name=name,
        email=email or f"desk@{name.split()[0].lower()}.pl",
        sports=("PADEL", "TENNIS"),
        point=point,
    )
    await chooses(client, desk, way)
    padel = await adds_a_court(client, desk, name="Court 1", sport="PADEL")
    tennis = await adds_a_court(client, desk, name="Court 2", sport="TENNIS")
    await sets_hours(
        client,
        desk,
        [padel["id"], tennis["id"]],
        hours if hours is not None else every_hour_of_the_week(),
    )
    await sets_prices(
        client,
        desk,
        [
            {"sport": "PADEL", "price_grosze": padel_grosze, "bands": []},
            {"sport": "TENNIS", "price_grosze": 80_00, "bands": []},
        ],
    )
    await confirms_settings(client, desk, paused=paused, **settings)
    await connects_payments(client, desk)
    return club_id, desk


async def saves_a_card(
    client, payments, headers: dict, card: EnteredCard = A_CARD
) -> None:
    """The whole setup, in its order: start, the phone types the card, the
    terms, the bank — whose one-time check the phone passes for a card it
    checks."""

    started = await client.post(f"{PAYMENT_METHODS}/setup", headers=headers)
    assert started.status_code == 201, started.text
    setup_id = started.json()["setup_id"]
    payments.phone_enters(setup_id, card)
    if card.behaviour in (
        CardBehaviour.CHECKED_AT_SETUP,
        CardBehaviour.CHECKED_EVERY_TIME,
    ):
        payments.phone_authenticates(setup_id)
    accepted = await client.post(
        f"{PAYMENT_METHODS}/terms",
        json={"terms_version": TERMS_IN_FORCE},
        headers=headers,
    )
    assert accepted.status_code == 200, accepted.text
    confirmed = await client.post(f"{PAYMENT_METHODS}/confirmation", headers=headers)
    assert confirmed.status_code == 200, confirmed.text


async def a_player(
    client,
    payments,
    name: str,
    *,
    sports: tuple[Sport, ...] = (Sport.PADEL,),
    card: bool = True,
    entered: EnteredCard = A_CARD,
    gender: str = "WOMAN",
    gender_preference: str | None = None,
    location: tuple[float, float] | None = None,
) -> dict:
    """One player, rated in ``sports`` and — unless told otherwise — with a
    saved card, living where the world's profiles live unless ``location``
    says otherwise. Their id and headers."""

    player_id, token = await players.register(client, name)
    profile: dict = {"gender": gender}
    if gender_preference is not None:
        profile["gender_preference"] = gender_preference
    if location is not None:
        profile["location"] = {"latitude": location[0], "longitude": location[1]}
    await players.commit_profile(client, token, **profile)
    for sport in sports:
        await players.rate(client, token, sport)
    headers = players.auth(token)
    if card:
        await saves_a_card(client, payments, headers, entered)
    return {"id": player_id, "token": token, "headers": headers}


EVERY_HOUR = [
    {"day": day, "hour": hour} for day in range(1, 8) for hour in range(7, 23)
]


async def a_member(
    client,
    session_factory,
    payments,
    name: str,
    *,
    mu: float = 2.5,
    sports: tuple[Sport, ...] = (Sport.PADEL,),
    intent: str | None = "COMPETITIVE",
    week: list[dict] = EVERY_HOUR,
    gender: str = "WOMAN",
    gender_preference: str | None = None,
    card: bool = True,
    domain: str = "example.com",
) -> dict:
    """A member rated at ``mu`` in ``sports``, free every hour of the week
    unless told otherwise, with a declared intent and — unless told otherwise
    — a saved card, addressed at ``domain``."""

    player_id, token = await players.register(client, name, domain=domain)
    profile: dict = {"weekly_hours": week, "gender": gender}
    if gender_preference is not None:
        profile["gender_preference"] = gender_preference
    await players.commit_profile(client, token, **profile)
    for sport in sports:
        await players.rate_in(session_factory, player_id, sport, mu=mu)
        if intent is not None:
            await players.declare_intent(client, token, intent=intent, sport=sport)
    headers = players.auth(token)
    if card:
        await saves_a_card(client, payments, headers)
    return {"id": player_id, "token": token, "headers": headers, "name": name}


async def a_group(client, owner: dict, club_id: str, *members: dict) -> UUID:
    """An *Anyone* group at the club, every member joined. Its id — which is
    also its pool's."""

    created = await client.post(
        GROUPS,
        json={
            "name": "Sobotni padel",
            "home_club_id": club_id,
            "join_policy": "ANYONE",
        },
        headers=owner["headers"],
    )
    assert created.status_code == 201, created.text
    group_id = created.json()["id"]
    for member in members:
        joined = await client.post(
            f"{GROUPS}/{group_id}/membership", headers=member["headers"]
        )
        assert joined.status_code in (200, 201), joined.text
    return UUID(group_id)


async def makes(
    session_factory,
    clock,
    *,
    pool_id: UUID,
    club_id: str,
    start: datetime = SATURDAY_FIVE,
    sport: Sport = Sport.PADEL,
    kind: SearchMode = SearchMode.COMPETITIVE,
    poster: dict | None = None,
    versions: tuple[tuple[dict, ...], ...] = (),
    posted_for: PostedFor | None = None,
) -> UUID:
    """A game proposed the way the engine will propose one. A pick unless a
    poster is named — for anybody, unless it says whom (#546)."""

    async with session_factory() as session:
        return await build_make_proposal(session, clock=clock).execute(
            MakeProposalCommand(
                pool_id=pool_id,
                origin=Origin.POST if poster is not None else Origin.PICK,
                poster_id=poster["id"] if poster is not None else None,
                sport=sport,
                kind=kind,
                club_id=UUID(club_id),
                start=instant(start),
                versions=[[player["id"] for player in version] for version in versions],
                posted_for=posted_for,
            )
        )


async def deals(
    session_factory, clock, proposal_id: UUID, *players: dict, into: int | None = None
) -> int:
    async with session_factory() as session:
        return await build_deal_version(session, clock=clock).execute(
            DealVersionCommand(
                proposal_id=proposal_id,
                player_ids=[player["id"] for player in players],
                into_version=into,
            )
        )


async def sweeps(session_factory, clock):
    async with session_factory() as session:
        return await build_expire_proposals(session, clock=clock).execute()


async def runs_out(session_factory, clock):
    """The time-to-pay job: every refused share's time to pay that is up runs
    out (#625, #626)."""

    async with session_factory() as session:
        return await build_run_out_the_time_to_pay(
            session, clock=clock, settings=get_settings()
        ).execute()


def yes_path(proposal_id: UUID) -> str:
    return f"/api/v1/proposals/{proposal_id}/yes"


async def says_yes(client, player: dict, proposal_id: UUID):
    return await client.post(yes_path(proposal_id), headers=player["headers"])


async def says_no(client, player: dict, proposal_id: UUID):
    return await client.post(
        f"/api/v1/proposals/{proposal_id}/no", headers=player["headers"]
    )


async def withdraws(client, player: dict, proposal_id: UUID):
    return await client.delete(yes_path(proposal_id), headers=player["headers"])


async def live_yeses(client, player: dict) -> dict:
    read = await client.get(LIVE_YESES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def live_ids(client, player: dict) -> list[str]:
    return [row["proposal_id"] for row in (await live_yeses(client, player))["yeses"]]
