"""Home's *Same vibe players* row and its See all — over HTTP, as the player
app calls them (#795; the home-rows mechanics §8, §9, §12; ``docs/adr/0204``
§6, §7, §9, §10).

**Tomek** holds six Social tags. **Karol**, his friend, holds the same six
(98%); **Bartek** three of them (88%), **Kuba** two (75%), **Ola** one (50%);
**Nobody** none of them. Karol waits in a gap while the fresh matches with two
or more shared tags lead; Ola, with one, is a gap however fresh. Skill plays no
part, and nobody here holds a level unless a test gives them one.

**Tags are the profile's**, committed and changed through the player's own
routes; the directory hears them through the outbox, so each read follows a
delivery, as the worker would have made it.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_skill_rating_repository,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    band_for,
    confidence_percent,
)
from app.kernel import Sport, instant
from app.modules.player_profile.domain.social_tags import SocialTag as T
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.ids import new_uuid
from tests.api import players_world as players
from tests.api.discovery_world import a_crowd

ROW = "/api/v1/same-vibe"
ALL = "/api/v1/same-vibe/all"
REQUESTS = "/api/v1/friends/requests"
NOTICES = "/api/v1/players/me/notices"
OPENED = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))

#: Tomek's six, in the vocabulary's order — the order every chip comes in.
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


def tags(*held: T) -> list[str]:
    return [tag.value for tag in held]


def sharing(n: int, *, besides: int = 0) -> list[str]:
    """``n`` of Tomek's tags, and ``besides`` he doesn't hold."""

    return tags(*HIS[:n], *OTHERS[:besides])


async def a_player(client, name: str, social_tag_ids: list[str]) -> dict:
    player_id, token = await players.register(client, name)
    await players.commit_profile(client, token, social_tag_ids=social_tag_ids)
    return {"id": player_id, "token": token, "headers": players.auth(token)}


async def retags(client, player: dict, social_tags: list[str]) -> None:
    changed = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": social_tags},
        headers=player["headers"],
    )
    assert changed.status_code == 200, changed.text


async def rated(session_factory, player: dict, sport: Sport, mu: float) -> None:
    """A Level opened through the rating's aggregate, on the outbox — what a
    sport filter reads."""

    band = band_for(mu)
    async with session_factory() as session:
        await build_skill_rating_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(
            SkillRating.initialise(
                rating_id=skill_rating_id(player["id"], sport),
                player_id=player["id"],
                sport=sport,
                result=AssessmentResult(
                    mu=mu,
                    sigma=0.8,
                    confidence=confidence_percent(0.8),
                    range_low=round(mu - 0.8, 2),
                    range_high=round(mu + 0.8, 2),
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


async def row(client, mailbox, reader: dict) -> list[dict]:
    return (await whole_row(client, mailbox, reader))["players"]


async def whole_row(client, mailbox, reader: dict) -> dict:
    await mailbox.drain()
    read = await client.get(ROW, headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def see_all(client, mailbox, reader: dict, **params) -> dict:
    await mailbox.drain()
    read = await client.get(ALL, params=params, headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()


def names(cards: list[dict]) -> list[str]:
    return [card["nickname"] for card in cards]


async def asks(client, requester: dict, addressee: dict, **body) -> None:
    asked = await client.post(
        REQUESTS,
        json={"player_id": str(addressee["id"]), "made_from": "RECORD"} | body,
        headers=requester["headers"],
    )
    assert asked.status_code == 200, asked.text


async def friends(client, one: dict, other: dict) -> None:
    await asks(client, one, other)
    accepted = await client.post(
        f"{REQUESTS}/{one['id']}/acceptance", headers=other["headers"]
    )
    assert accepted.status_code == 200, accepted.text


async def the_request_on_home(client, mailbox, addressee: dict) -> tuple[dict, dict]:
    await mailbox.drain()
    [request] = (await client.get("/api/v1/home", headers=addressee["headers"])).json()[
        "friend_requests"
    ]
    [notice] = (await client.get(NOTICES, headers=addressee["headers"])).json()[
        "notices"
    ]
    return request, notice


@pytest.fixture
async def tomek(client) -> dict:
    return await a_player(client, "tomek", tags(*HIS))


@pytest.fixture
async def crowd(client, tomek) -> dict[str, dict]:
    karol = await a_player(client, "karol", sharing(6))
    bartek = await a_player(client, "bartek", sharing(3, besides=2))
    kuba = await a_player(client, "kuba", sharing(2, besides=1))
    ola = await a_player(client, "ola", sharing(1, besides=2))
    nobody = await a_player(client, "nobody", tags(*OTHERS[:2]))
    await friends(client, tomek, karol)
    return {
        "karol": karol,
        "bartek": bartek,
        "kuba": kuba,
        "ola": ola,
        "nobody": nobody,
    }


# --------------------------------------------------------------------------- #
# The vibe % and what a card carries
# --------------------------------------------------------------------------- #


async def test_the_vibe_percent_rises_with_each_shared_tag(client, mailbox, tomek):
    for n in range(1, 7):
        # Every player holds at least two tags: one shared needs one besides.
        await a_player(client, f"shares{n}", sharing(n, besides=1 if n == 1 else 0))

    page = await see_all(client, mailbox, tomek)

    assert [
        (card["nickname"], card["in_common"], card["vibe_percent"])
        for card in page["players"]
    ] == [
        ("shares6", 6, 98),
        ("shares5", 5, 97),
        ("shares4", 4, 94),
        ("shares3", 3, 88),
        ("shares2", 2, 75),
        ("shares1", 1, 50),
    ]


async def test_a_card_carries_the_shared_tags_in_the_vocabulary_s_order(
    client, mailbox, tomek, crowd
):
    [bartek] = [
        card
        for card in (await see_all(client, mailbox, tomek))["players"]
        if card["nickname"] == "bartek"
    ]

    assert bartek["player_id"] == str(crowd["bartek"]["id"])
    assert bartek["shared_tags"] == tags(*HIS[:3])
    assert bartek["in_common"] == 3
    assert bartek["vibe_percent"] == 88
    assert bartek["relation"] == "NONE"
    assert bartek["photo_id"] is None and bartek["photo_url"] is None


async def test_a_tie_goes_to_fewer_tags_not_shared_then_the_player_id(
    client, mailbox, tomek
):
    lena = await a_player(client, "lena", sharing(2, besides=3))
    kuba = await a_player(client, "kuba", sharing(2, besides=1))
    twins = sorted(
        [
            await a_player(client, "twin1", sharing(2)),
            await a_player(client, "twin2", sharing(2)),
        ],
        key=lambda one: one["id"].int,
    )

    page = await see_all(client, mailbox, tomek)

    assert [card["player_id"] for card in page["players"]] == [
        str(one["id"]) for one in (*twins, kuba, lena)
    ]


# --------------------------------------------------------------------------- #
# The row: fresh good matches first, then the gaps
# --------------------------------------------------------------------------- #


async def test_fresh_matches_lead_and_karol_waits_in_a_gap(
    client, mailbox, tomek, crowd
):
    cards = await row(client, mailbox, tomek)

    assert names(cards) == ["bartek", "kuba", "karol", "ola"]
    assert [card["relation"] for card in cards] == ["NONE", "NONE", "FRIEND", "NONE"]


async def test_the_row_reads_for_a_player_with_no_level(client, mailbox, tomek, crowd):
    # Nobody here holds a level, Tomek least of all: skill plays no part.
    assert len(await row(client, mailbox, tomek)) == 4


async def test_somebody_tomek_asked_is_a_gap_and_somebody_who_asked_him_is_fresh(
    client, mailbox, tomek, crowd
):
    await asks(client, tomek, crowd["bartek"], made_from="SAME_VIBE")
    await asks(client, crowd["kuba"], tomek)

    cards = await row(client, mailbox, tomek)

    assert names(cards) == ["kuba", "karol", "bartek", "ola"]
    assert [card["relation"] for card in cards] == [
        "ASKED_YOU",
        "FRIEND",
        "SENT",
        "NONE",
    ]


async def test_a_new_fresh_match_takes_the_weakest_gap(client, mailbox, tomek):
    gaps = [await a_player(client, f"one{n}", sharing(1, besides=1)) for n in range(10)]
    weakest = max(gaps, key=lambda one: one["id"].int)

    before = await row(client, mailbox, tomek)
    await a_player(client, "fresh", sharing(2))
    after = await row(client, mailbox, tomek)

    assert len(before) == 10 and len(after) == 10
    assert names(after)[0] == "fresh"
    assert str(weakest["id"]) in {card["player_id"] for card in before}
    assert str(weakest["id"]) not in {card["player_id"] for card in after}


async def test_ten_fresh_fill_the_row_and_push_the_friend_off(client, mailbox, tomek):
    karol = await a_player(client, "karol", sharing(6))
    await friends(client, tomek, karol)
    for n in range(10):
        await a_player(client, f"fresh{n}", sharing(2))

    cards = await row(client, mailbox, tomek)

    assert len(cards) == 10
    assert "karol" not in names(cards)
    page = await see_all(client, mailbox, tomek)
    # See all rests nobody and holds no gaps: the friend leads it.
    assert names(page["players"])[0] == "karol"


async def test_a_tag_change_is_read_into_the_next_read(client, mailbox, tomek, crowd):
    await retags(client, crowd["ola"], sharing(4))
    await retags(client, crowd["bartek"], tags(*OTHERS[:3]))

    cards = await row(client, mailbox, tomek)

    assert names(cards) == ["ola", "kuba", "karol"]
    assert cards[0]["in_common"] == 4

    # And the reader's own: Tomek drops all but two of his, so all three share
    # two, and the tie goes to fewer of theirs he doesn't hold — Kuba one, Ola
    # two; Karol, a friend, still a gap.
    await retags(client, tomek, tags(*HIS[:2]))
    cards = await row(client, mailbox, tomek)
    assert names(cards) == ["kuba", "ola", "karol"]
    assert {card["in_common"] for card in cards} == {2}


# --------------------------------------------------------------------------- #
# Who is never on it
# --------------------------------------------------------------------------- #


async def test_nobody_sharing_none_blocked_switched_off_or_not_playing_is_on_it(
    client, mailbox, tomek, crowd
):
    blocked = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(crowd["kuba"]["id"])},
        headers=tomek["headers"],
    )
    assert blocked.status_code == 204, blocked.text
    blocker = await a_player(client, "blocker", sharing(6))
    blocks_tomek = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(tomek["id"])},
        headers=blocker["headers"],
    )
    assert blocks_tomek.status_code == 204, blocks_tomek.text
    shy = await a_player(client, "shy", sharing(6))
    await players.closed_to_new_people(client, shy["token"])
    await players.register(client, "halfway")

    read = await whole_row(client, mailbox, tomek)
    everyone = names(read["players"])
    page = await see_all(client, mailbox, tomek)

    assert set(everyone) == {"karol", "bartek", "ola"}
    assert set(names(page["players"])) == {"karol", "bartek", "ola"}
    assert "tomek" not in everyone
    # The total under the same exclusions: nobody, Kuba, the blocker, the shy
    # one and the one who never finished sign-up are not counted.
    assert read["total"] == 3


async def test_nobody_else_sharing_a_tag_hides_the_row(client, mailbox, tomek):
    await a_player(client, "nobody", tags(*OTHERS[:2]))

    assert await whole_row(client, mailbox, tomek) == {"players": [], "total": 0}
    assert await see_all(client, mailbox, tomek) == {
        "players": [],
        "next": None,
        "sports": [],
    }


# --------------------------------------------------------------------------- #
# The total: everybody sharing a tag, counted up to 100 (#812)
# --------------------------------------------------------------------------- #


async def test_the_total_counts_each_player_once_however_many_tags_they_share(
    client, mailbox, tomek, crowd
):
    # Karol shares six, Bartek three, Kuba two and Ola one: four people, the
    # friend among them. Nobody shares none.
    assert (await whole_row(client, mailbox, tomek))["total"] == 4


async def test_the_total_stops_at_100_and_the_row_and_see_all_stand(
    client, mailbox, session_factory, tomek
):
    await a_crowd(session_factory, 99, tags=sharing(2))
    assert (await whole_row(client, mailbox, tomek))["total"] == 99

    await a_crowd(session_factory, 2, tags=sharing(1, besides=1), named="one")
    read = await whole_row(client, mailbox, tomek)
    page = await see_all(client, mailbox, tomek)

    assert read["total"] == 100
    assert len(read["players"]) == 10
    assert all(card["in_common"] == 2 for card in read["players"])
    assert len(page["players"]) == 20 and page["next"] is not None


async def test_the_total_is_counted_in_the_one_pass_over_the_tag_rows(
    client, mailbox, session_factory, statements, tomek
):
    """**No statement more** than the row read before its total: the count is
    a window over the pass the row already makes, so the tag rows are read
    once for the reader's own and once a batch — never a second pass."""

    await a_crowd(session_factory, 25, tags=sharing(2))
    await mailbox.drain()
    with statements.counting() as sent:
        read = (await client.get(ROW, headers=tomek["headers"])).json()

    assert read["total"] == 25 and len(read["players"]) == 10
    his_tags, the_pass = sent.naming("discovery_player_tags")
    assert sent.naming("discovery_players") == [the_pass]
    assert "over ()" in the_pass.lower()
    assert "discovery_players" not in his_tags

    # See all carries no total, and its pass counts nothing.
    with statements.counting() as page:
        await client.get(ALL, headers=tomek["headers"])
    assert not any("over ()" in one.lower() for one in page)


# --------------------------------------------------------------------------- #
# See all
# --------------------------------------------------------------------------- #


async def test_see_all_is_everybody_most_in_common_first_friends_where_they_fall(
    client, mailbox, tomek, crowd
):
    page = await see_all(client, mailbox, tomek)

    assert names(page["players"]) == ["karol", "bartek", "kuba", "ola"]
    assert page["next"] is None


async def test_a_sport_keeps_the_players_holding_a_level_in_it(
    client, mailbox, session_factory, tomek, crowd
):
    await rated(session_factory, crowd["bartek"], Sport.PADEL, 2.40)
    await rated(session_factory, crowd["ola"], Sport.PADEL, 3.10)
    await rated(session_factory, crowd["kuba"], Sport.TENNIS, 3.35)
    await rated(session_factory, crowd["nobody"], Sport.SQUASH, 2.50)

    padel = await see_all(client, mailbox, tomek, sport="PADEL")
    everyone = await see_all(client, mailbox, tomek)

    assert names(padel["players"]) == ["bartek", "ola"]
    # The pill: every sport somebody listed holds a level in, whatever the
    # filter — Nobody's squash isn't one, since Nobody isn't listed.
    assert padel["sports"] == ["PADEL", "TENNIS"]
    assert everyone["sports"] == ["PADEL", "TENNIS"]
    assert (
        names((await see_all(client, mailbox, tomek, sport="BADMINTON"))["players"])
        == []
    )


async def test_see_all_comes_in_pages_of_twenty(client, mailbox, tomek):
    for n in range(22):
        await a_player(client, f"p{n:02}", sharing(1 + n % 3, besides=1))

    first = await see_all(client, mailbox, tomek)
    second = await see_all(client, mailbox, tomek, after=first["next"])

    assert len(first["players"]) == 20 and first["next"] is not None
    assert len(second["players"]) == 2 and second["next"] is None
    listed = [card["player_id"] for card in first["players"] + second["players"]]
    assert len(set(listed)) == 22
    shared = [card["in_common"] for card in first["players"] + second["players"]]
    assert shared == sorted(shared, reverse=True)


async def test_a_cursor_this_server_never_wrote_is_refused(client, tomek):
    for cursor in ("not-a-page", "MDoxOmFiYw"):
        read = await client.get(ALL, params={"after": cursor}, headers=tomek["headers"])

        assert read.status_code == 400
        assert read.json()["code"] == "not_a_same_vibe_page"


# --------------------------------------------------------------------------- #
# A request from the row
# --------------------------------------------------------------------------- #


async def test_a_request_from_the_row_counts_today_s_tags_in_common(
    client, mailbox, tomek, crowd
):
    await asks(client, tomek, crowd["bartek"], made_from="SAME_VIBE")

    request, notice = await the_request_on_home(client, mailbox, crowd["bartek"])

    assert request["from_same_vibe"] is True
    assert request["in_common"] == 3
    assert request["group"] is None and request["sport"] is None
    assert notice["body"] == "3 things in common"


async def test_one_tag_in_common_is_one_thing(client, mailbox, tomek, crowd):
    await asks(client, tomek, crowd["ola"], made_from="SAME_VIBE")

    request, notice = await the_request_on_home(client, mailbox, crowd["ola"])

    assert request["in_common"] == 1
    assert notice["body"] == "1 thing in common"


async def test_the_count_is_today_s_and_falls_back_once_none_is_shared(
    client, mailbox, tomek, crowd
):
    kuba = crowd["kuba"]
    await asks(client, tomek, kuba, made_from="SAME_VIBE")
    await retags(client, kuba, sharing(5))

    request, notice = await the_request_on_home(client, mailbox, kuba)
    assert request["in_common"] == 5
    assert notice["body"] == "5 things in common"

    await retags(client, kuba, tags(*OTHERS[:3]))

    request, notice = await the_request_on_home(client, mailbox, kuba)
    assert request["in_common"] == 0
    assert notice["body"] == "Found you through your tags"


async def test_a_request_from_the_row_names_no_group_and_no_sport(
    client, mailbox, tomek, crowd
):
    await asks(
        client,
        tomek,
        crowd["kuba"],
        made_from="SAME_VIBE",
        sport="PADEL",
        group_id=str(new_uuid()),
    )

    request, _ = await the_request_on_home(client, mailbox, crowd["kuba"])

    assert request["from_same_vibe"] is True
    assert request["sport"] is None and request["group"] is None


async def test_a_request_from_anywhere_else_is_not_from_the_row(
    client, mailbox, tomek, crowd
):
    await asks(client, tomek, crowd["kuba"])

    request, notice = await the_request_on_home(client, mailbox, crowd["kuba"])

    assert request["from_same_vibe"] is False
    assert request["in_common"] is None
    assert notice["body"] == "Answer it on Home."
