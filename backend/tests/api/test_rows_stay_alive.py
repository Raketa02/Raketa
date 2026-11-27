"""Home's rows stay alive: **the on-screen reports and the rest count**, over
HTTP as the player app sends and reads them (#796; ``docs/adr/0204`` §7, §10,
§12; the home-rows mechanics §9).

**Tomek** holds six Social tags and a sure padel 2,71. **Kuba** shares three
of the tags and plays padel 2,75; **Bartek** shares two and plays 2,80 — both
fresh good matches in each row, Kuba first. **Karol**, his friend, shares all
six; **Ola** shares one, a weaker match. Each day Kuba's card comes on screen
without Tomek adding him counts once: on the fifth, Kuba **rests** in that row
— a gap, never hidden — and a fresh match takes his place. Days Tomek's phone
never reports count nothing, and each row keeps its own count.

**Days are moved on the request's clock** (the ``clock`` fixture), one Warsaw
day at a time, and the rows are read after the outbox is drained, as the
worker would have delivered every event.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select, update

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_follow_the_directory,
    build_skill_rating_repository,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    band_for,
    confidence_percent,
)
from app.kernel import Sport, instant
from app.modules.discovery.infrastructure.rest_count_model import (
    DiscoveryRestCountORM,
)
from app.modules.player_profile.domain.social_tags import SocialTag as T
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM
from app.shared.ids import new_uuid
from tests.api import players_world as players

ON_SCREEN = "/api/v1/on-screen"
SAME_LEVEL = "SAME_LEVEL"
SAME_VIBE = "SAME_VIBE"
ROWS = {SAME_LEVEL: "/api/v1/same-level", SAME_VIBE: "/api/v1/same-vibe"}
REQUESTS = "/api/v1/friends/requests"
OPENED = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
#: How sure the app is of a player with results: sure enough for a good match.
SURE = 0.13

#: Tomek's six, in the vocabulary's order.
HIS = (
    T.STAYS_FOR_A_DRINK,
    T.TALKS_THROUGH_THE_MATCH,
    T.PLAYS_TO_WIN,
    T.LAUGHS_OFF_MISTAKES,
    T.HERE_TO_IMPROVE,
    T.HERE_TO_MEET_PLAYERS,
)
#: Tags Tomek doesn't hold.
OTHERS = (
    T.STRAIGHT_HOME_AFTER,
    T.SETTLES_UP_ON_THE_SPOT,
    T.BOOKS_THE_NEXT_ONE,
    T.QUIET_AND_FOCUSED,
    T.OPEN_TO_MEET_SOMEONE,
)


def sharing(n: int, *, besides: int = 0) -> list[str]:
    """``n`` of Tomek's tags, and ``besides`` he doesn't hold."""

    return [tag.value for tag in (*HIS[:n], *OTHERS[:besides])]


async def a_player(client, name: str, social_tag_ids: list[str]) -> dict:
    player_id, token = await players.register(client, name)
    await players.commit_profile(client, token, social_tag_ids=social_tag_ids)
    return {"id": player_id, "token": token, "headers": players.auth(token)}


async def rated(session_factory, player: dict, mu: float) -> None:
    """A sure padel Level opened through the rating's aggregate, on the
    outbox, as Same competitive level's tests open one."""

    band = band_for(mu)
    async with session_factory() as session:
        await build_skill_rating_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(
            SkillRating.initialise(
                rating_id=skill_rating_id(player["id"], Sport.PADEL),
                player_id=player["id"],
                sport=Sport.PADEL,
                result=AssessmentResult(
                    mu=mu,
                    sigma=SURE,
                    confidence=confidence_percent(SURE),
                    range_low=round(mu - SURE, 2),
                    range_high=round(mu + SURE, 2),
                    band=BandView(name=band.label, lower=band.lower, upper=band.upper),
                    status=STATUS_INITIAL_ESTIMATE,
                    questions_asked=7,
                    engine_version="racketskill-fusion-v3",
                    confidence_ceiling=50,
                ),
                source_assessment_id=new_uuid(),
                occurred_at=OPENED,
            )
        )
        await session.commit()


async def row(client, mailbox, reader: dict, which: str) -> list[dict]:
    await mailbox.drain()
    read = await client.get(ROWS[which], headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()["players"]


async def see_all(client, mailbox, reader: dict, which: str) -> list[dict]:
    await mailbox.drain()
    read = await client.get(f"{ROWS[which]}/all", headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()["players"]


def names(cards: list[dict]) -> list[str]:
    return [card["nickname"] for card in cards]


async def on_screen(client, reader: dict, which: str, *player_ids: UUID) -> None:
    """The phone's report: these cards came on screen in this row."""

    told = await client.post(
        ON_SCREEN,
        json={"row": which, "player_ids": [str(one) for one in player_ids]},
        headers=reader["headers"],
    )
    assert told.status_code == 204, told.text


async def on_screen_for(
    client, clock, reader: dict, which: str, player: dict, *, days: int
) -> None:
    """The card on screen once on each of ``days`` days, the clock left on
    the next day."""

    for _ in range(days):
        await on_screen(client, reader, which, player["id"])
        clock.move(timedelta(days=1))


async def asks(client, requester: dict, addressee: dict) -> None:
    asked = await client.post(
        REQUESTS,
        json={"player_id": str(addressee["id"]), "made_from": "RECORD"},
        headers=requester["headers"],
    )
    assert asked.status_code == 200, asked.text


async def friends(client, one: dict, other: dict) -> None:
    await asks(client, one, other)
    accepted = await client.post(
        f"{REQUESTS}/{one['id']}/acceptance", headers=other["headers"]
    )
    assert accepted.status_code == 200, accepted.text


async def rest_rows(session_factory) -> set[tuple[UUID, str, UUID, int]]:
    async with session_factory() as session:
        found = await session.execute(
            select(
                DiscoveryRestCountORM.viewer_id,
                DiscoveryRestCountORM.row,
                DiscoveryRestCountORM.player_id,
                DiscoveryRestCountORM.days,
            )
        )
        return {tuple(one) for one in found.all()}  # type: ignore[misc]


@pytest.fixture
async def tomek(client, session_factory) -> dict:
    tomek = await a_player(client, "tomek", sharing(6))
    await rated(session_factory, tomek, 2.71)
    return tomek


@pytest.fixture
async def crowd(client, mailbox, session_factory, tomek) -> dict[str, dict]:
    """Delivered, as it is by the time any of their cards is on a row: a card
    the directory has not heard of yet is no card a phone could report."""

    kuba = await a_player(client, "kuba", sharing(3))
    await rated(session_factory, kuba, 2.75)
    bartek = await a_player(client, "bartek", sharing(2))
    await rated(session_factory, bartek, 2.80)
    karol = await a_player(client, "karol", sharing(6))
    ola = await a_player(client, "ola", sharing(1, besides=2))
    await friends(client, tomek, karol)
    await mailbox.drain()
    return {"kuba": kuba, "bartek": bartek, "karol": karol, "ola": ola}


# --------------------------------------------------------------------------- #
# Five days on screen, and a fresh match takes his place
# --------------------------------------------------------------------------- #


async def test_four_days_keep_him_fresh_and_the_fifth_rests_him(
    client, mailbox, clock, tomek
):
    """Kuba, the best match, and ten fresh matches behind him: on the fifth day
    he rests, and the eleventh takes his place on the row."""

    kuba = await a_player(client, "kuba", sharing(6))
    for n in range(10):
        await a_player(client, f"fresh{n}", sharing(2, besides=n % 3))
    first = await row(client, mailbox, tomek, SAME_VIBE)
    assert names(first)[0] == "kuba" and len(first) == 10

    await on_screen_for(client, clock, tomek, SAME_VIBE, kuba, days=4)
    assert names(await row(client, mailbox, tomek, SAME_VIBE)) == names(first)

    await on_screen(client, tomek, SAME_VIBE, kuba["id"])
    rested = names(await row(client, mailbox, tomek, SAME_VIBE))

    behind_him = names(await see_all(client, mailbox, tomek, SAME_VIBE))
    assert behind_him[0] == "kuba", "See all is the plain order: nobody rests there"
    assert "kuba" not in rested
    assert rested == behind_him[1:11]
    assert len(rested) == 10


async def test_the_same_day_twice_counts_once(client, mailbox, clock, tomek, crowd):
    kuba = crowd["kuba"]
    for _ in range(4):
        await on_screen(client, tomek, SAME_VIBE, kuba["id"])
        await on_screen(client, tomek, SAME_VIBE, kuba["id"], kuba["id"])
        clock.move(timedelta(days=1))

    assert names(await row(client, mailbox, tomek, SAME_VIBE))[0] == "kuba"

    await on_screen(client, tomek, SAME_VIBE, kuba["id"])
    assert names(await row(client, mailbox, tomek, SAME_VIBE))[0] == "bartek"


async def test_days_never_reported_count_nothing(client, mailbox, clock, tomek, crowd):
    """Tomek opens Home every day and never scrolls to the row: only the days
    his phone reports count."""

    kuba = crowd["kuba"]
    await on_screen_for(client, clock, tomek, SAME_VIBE, kuba, days=2)
    for _ in range(10):
        await row(client, mailbox, tomek, SAME_VIBE)
        clock.move(timedelta(days=1))
    await on_screen_for(client, clock, tomek, SAME_VIBE, kuba, days=2)

    assert names(await row(client, mailbox, tomek, SAME_VIBE))[0] == "kuba"


# --------------------------------------------------------------------------- #
# Each row keeps its own count
# --------------------------------------------------------------------------- #


async def test_each_row_counts_on_its_own(client, mailbox, clock, tomek, crowd):
    kuba = crowd["kuba"]
    assert names(await row(client, mailbox, tomek, SAME_LEVEL)) == ["kuba", "bartek"]
    assert names(await row(client, mailbox, tomek, SAME_VIBE))[:2] == [
        "kuba",
        "bartek",
    ]

    await on_screen_for(client, clock, tomek, SAME_LEVEL, kuba, days=5)

    # Rested in Same competitive level — a gap behind Bartek — and fresh in
    # Same vibe, where his card was never reported.
    assert names(await row(client, mailbox, tomek, SAME_LEVEL)) == ["bartek", "kuba"]
    assert names(await row(client, mailbox, tomek, SAME_VIBE))[:2] == [
        "kuba",
        "bartek",
    ]
    # See all rests nobody.
    assert names(await see_all(client, mailbox, tomek, SAME_LEVEL)) == [
        "kuba",
        "bartek",
    ]

    await on_screen_for(client, clock, tomek, SAME_VIBE, kuba, days=5)
    assert names(await row(client, mailbox, tomek, SAME_VIBE))[:1] == ["bartek"]


# --------------------------------------------------------------------------- #
# A rested player is a gap, never hidden
# --------------------------------------------------------------------------- #


async def test_a_rested_player_returns_in_a_gap_when_no_fresh_match_is_left(
    client, mailbox, clock, tomek, crowd
):
    assert names(await row(client, mailbox, tomek, SAME_VIBE)) == [
        "kuba",
        "bartek",
        "karol",
        "ola",
    ]

    await on_screen_for(client, clock, tomek, SAME_VIBE, crowd["kuba"], days=5)

    # Bartek is the one fresh match left; Kuba waits among the gaps, best
    # first: Karol (six in common, a friend), Kuba (three), Ola (one).
    assert names(await row(client, mailbox, tomek, SAME_VIBE)) == [
        "bartek",
        "karol",
        "kuba",
        "ola",
    ]


async def test_adding_a_rested_player_keeps_him_a_gap_and_the_rest_never_resets(
    client, mailbox, clock, tomek, crowd
):
    kuba = crowd["kuba"]
    await on_screen_for(client, clock, tomek, SAME_VIBE, kuba, days=5)

    await asks(client, tomek, kuba)
    cards = await row(client, mailbox, tomek, SAME_VIBE)
    assert names(cards) == ["bartek", "karol", "kuba", "ola"]
    assert cards[2]["relation"] == "SENT"

    cancelled = await client.delete(
        f"{REQUESTS}/{kuba['id']}", headers=tomek["headers"]
    )
    assert cancelled.status_code == 204, cancelled.text
    cards = await row(client, mailbox, tomek, SAME_VIBE)
    assert names(cards) == ["bartek", "karol", "kuba", "ola"]
    assert cards[2]["relation"] == "NONE"


async def test_somebody_who_asked_the_reader_rests_as_the_unconnected_do(
    client, mailbox, clock, tomek, crowd
):
    kuba = crowd["kuba"]
    await asks(client, kuba, tomek)

    await on_screen_for(client, clock, tomek, SAME_VIBE, kuba, days=5)

    cards = await row(client, mailbox, tomek, SAME_VIBE)
    assert names(cards)[0] == "bartek"
    assert {card["nickname"]: card["relation"] for card in cards}["kuba"] == (
        "ASKED_YOU"
    )


async def test_days_a_connected_card_is_on_screen_count_nothing(
    client, mailbox, clock, tomek, crowd
):
    """Karol, a friend, is a gap whatever is counted; once the friendship ends
    he is fresh, because no day counted while they were connected."""

    karol = crowd["karol"]
    await on_screen_for(client, clock, tomek, SAME_VIBE, karol, days=5)

    removed = await client.delete(
        f"/api/v1/friends/{karol['id']}", headers=tomek["headers"]
    )
    assert removed.status_code == 204, removed.text

    assert names(await row(client, mailbox, tomek, SAME_VIBE))[0] == "karol"


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


async def test_unknown_and_excluded_ids_are_ignored(
    client, mailbox, session_factory, tomek, crowd
):
    blocked = await a_player(client, "blocked", sharing(3))
    turned = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"])},
        headers=tomek["headers"],
    )
    assert turned.status_code == 204, turned.text
    shy = await a_player(client, "shy", sharing(3))
    await players.closed_to_new_people(client, shy["token"])
    halfway_id, _ = await players.register(client, "halfway")
    await mailbox.drain()

    await on_screen(
        client,
        tomek,
        SAME_VIBE,
        new_uuid(),
        tomek["id"],
        blocked["id"],
        shy["id"],
        halfway_id,
        crowd["karol"]["id"],
        crowd["kuba"]["id"],
    )

    # Only Kuba counts: nobody unknown, not Tomek himself, nobody blocked,
    # switched off or not playing, and not Karol, his friend.
    assert await rest_rows(session_factory) == {
        (tomek["id"], SAME_VIBE, crowd["kuba"]["id"], 1)
    }


async def test_a_report_names_a_row_that_rests(client, tomek, crowd):
    for body in (
        {"row": "NEW_IN_RAKIETA", "player_ids": [str(crowd["kuba"]["id"])]},
        {"row": SAME_VIBE, "player_ids": []},
        {"row": SAME_VIBE, "player_ids": ["not-an-id"]},
    ):
        refused = await client.post(ON_SCREEN, json=body, headers=tomek["headers"])
        assert refused.status_code == 422, (body, refused.text)


async def test_a_report_needs_a_session(client, crowd):
    refused = await client.post(
        ON_SCREEN,
        json={"row": SAME_VIBE, "player_ids": [str(crowd["kuba"]["id"])]},
    )
    assert refused.status_code == 401, refused.text


# --------------------------------------------------------------------------- #
# A gone account's rest rows go, on either side
# --------------------------------------------------------------------------- #


async def test_a_gone_accounts_rest_rows_go_on_either_side(
    client, mailbox, session_factory, tomek, crowd
):
    kuba, bartek = crowd["kuba"], crowd["bartek"]
    await on_screen(client, tomek, SAME_VIBE, kuba["id"], bartek["id"])
    await on_screen(client, kuba, SAME_LEVEL, tomek["id"])
    await on_screen(client, bartek, SAME_VIBE, kuba["id"])
    assert len(await rest_rows(session_factory)) == 4

    # Nothing in ``users`` disables an account yet: the row says it is gone,
    # and the directory's follower forgets it, as a delivered
    # ``users.user_disabled`` would have it do.
    async with session_factory() as session:
        await session.execute(
            update(UserORM).where(UserORM.id == kuba["id"]).values(is_active=False)
        )
        await build_follow_the_directory(session).execute(kuba["id"])
        await session.commit()

    assert await rest_rows(session_factory) == {
        (tomek["id"], SAME_VIBE, bartek["id"], 1)
    }
