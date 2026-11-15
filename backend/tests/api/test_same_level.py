"""Home's *Same competitive level players* row and its See all — over HTTP, as
the player app calls them (#794; the home-rows mechanics §6, §9, §12;
``docs/adr/0204`` §4, §7, §9, §10).

**Tomek** reads his Home: padel 2,71 and tennis 3,10, both sure. **Zofia**, his
friend, plays padel 2,69 and squash 2,55; **Kuba**, a stranger, padel 2,80 and
tennis 3,35; **Bartek** signed up with padel 2,35 from the questionnaire alone,
so the app is unsure of it. Kuba leads the row — a fresh good match — and Zofia,
91% even, waits in a gap at the right.

**Levels are opened and moved through the rating's own aggregate**, on the
outbox, as a questionnaire and a settled result record them: no route takes
dictation for a chosen Level and its Uncertainty. The current-level projection
hears them through the outbox, so each read follows a delivery, as the worker
would have made it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import delete, select

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_player_levels,
    build_rebuild_the_levels,
    build_ruleset,
    build_skill_rating_repository,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    SkillEstimate,
    band_for,
    confidence_percent,
)
from app.engines.racketskill.update_v1 import MovedRating, Stakes
from app.kernel import Sport, instant
from app.modules.discovery.domain.levels import Band, CurrentLevel
from app.modules.discovery.infrastructure.levels_model import DiscoveryLevelORM
from app.modules.matchmaking.domain.balance import forecast_the_sides
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.ids import new_uuid
from tests.api import players_world as players

ROW = "/api/v1/same-level"
ALL = "/api/v1/same-level/all"
REQUESTS = "/api/v1/friends/requests"
NOTICES = "/api/v1/players/me/notices"
OPENED = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
#: How sure the app is of a player with results; a questionnaire alone is
#: far less sure.
SURE = 0.13
UNSURE = 0.8


async def a_player(client, name: str, **profile) -> dict:
    player_id, token = await players.register(client, name)
    await players.commit_profile(client, token, **profile)
    return {"id": player_id, "token": token, "headers": players.auth(token)}


async def rated(
    session_factory, player: dict, sport: Sport, mu: float, sigma: float = SURE
) -> None:
    """A Level opened through the rating's aggregate — the questionnaire's
    record — on the outbox."""

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
                    sigma=sigma,
                    confidence=confidence_percent(sigma),
                    range_low=round(mu - sigma, 2),
                    range_high=round(mu + sigma, 2),
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


async def moved(
    session_factory, player: dict, sport: Sport, mu: float, sigma: float = SURE
) -> None:
    """A settled result moving the Level, as the rating records one."""

    band = band_for(mu)
    async with session_factory() as session:
        ratings = build_skill_rating_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        rating = await ratings.find_for(player_id=player["id"], sport=sport)
        assert rating is not None
        rating.move_on_result(
            game_id=new_uuid(),
            moved=MovedRating(
                mu=mu,
                sigma=sigma,
                confidence=confidence_percent(sigma),
                range_low=round(mu - sigma, 2),
                range_high=round(mu + sigma, 2),
                band=BandView(name=band.label, lower=band.lower, upper=band.upper),
                status="Calibrating",
                stakes=Stakes(win=0.03, loss=-0.03),
            ),
            won=True,
            opposition=SkillEstimate(mu=mu, sigma=0.3),
            information_share=0.5,
            occurred_at=OPENED,
        )
        await ratings.save(rating)
        await session.commit()


def forecast(sport: Sport, yours: tuple[float, float], theirs: tuple[float, float]):
    """The matcher's own forecast with one player a side — what the row must
    print, read straight off the function."""

    you, them = UUID(int=1), UUID(int=2)
    sides = forecast_the_sides(
        (you,),
        (them,),
        {you: SkillEstimate(*yours), them: SkillEstimate(*theirs)},
        sport=sport,
        rules=build_ruleset().balance,
    )
    assert sides is not None
    return sides[0].pct


async def row(client, mailbox, reader: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(ROW, headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()["players"]


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


async def accepts(client, reader: dict, requester: dict) -> None:
    accepted = await client.post(
        f"{REQUESTS}/{requester['id']}/acceptance", headers=reader["headers"]
    )
    assert accepted.status_code == 200, accepted.text


async def friends(client, one: dict, other: dict) -> None:
    await asks(client, one, other)
    await accepts(client, other, one)


@pytest.fixture
async def tomek(client, session_factory) -> dict:
    tomek = await a_player(client, "tomek")
    await rated(session_factory, tomek, Sport.PADEL, 2.71)
    await rated(session_factory, tomek, Sport.TENNIS, 3.10)
    return tomek


@pytest.fixture
async def crowd(client, session_factory, tomek) -> dict[str, dict]:
    """Zofia (his friend), Kuba and Bartek, as the mechanics' examples have
    them."""

    zofia = await a_player(client, "zofia")
    await rated(session_factory, zofia, Sport.PADEL, 2.69)
    await rated(session_factory, zofia, Sport.SQUASH, 2.55)
    kuba = await a_player(client, "kuba")
    await rated(session_factory, kuba, Sport.PADEL, 2.80)
    await rated(session_factory, kuba, Sport.TENNIS, 3.35)
    bartek = await a_player(client, "bartek")
    await rated(session_factory, bartek, Sport.PADEL, 2.35, sigma=UNSURE)
    await friends(client, tomek, zofia)
    return {"zofia": zofia, "kuba": kuba, "bartek": bartek}


# --------------------------------------------------------------------------- #
# Who: once the reader has a level, everybody sharing a sport
# --------------------------------------------------------------------------- #


async def test_the_row_is_hidden_while_the_reader_has_no_level(
    client, mailbox, session_factory
):
    ola = await a_player(client, "ola")
    kuba = await a_player(client, "kuba")
    await rated(session_factory, kuba, Sport.PADEL, 2.80)

    assert await row(client, mailbox, ola) == []
    assert await see_all(client, mailbox, ola) == {
        "players": [],
        "next": None,
        "sports": [],
    }

    await rated(session_factory, ola, Sport.PADEL, 2.75, sigma=UNSURE)
    assert names(await row(client, mailbox, ola)) == ["kuba"]


async def test_only_players_who_share_a_sport_with_the_reader(
    client, mailbox, session_factory, tomek, crowd
):
    ewa = await a_player(client, "ewa")
    await rated(session_factory, ewa, Sport.BADMINTON, 2.70)
    await a_player(client, "nobody")

    cards = await row(client, mailbox, tomek)

    assert "ewa" not in names(cards) and "nobody" not in names(cards)
    assert set(names(cards)) == {"zofia", "kuba", "bartek"}


async def test_each_player_is_in_the_sport_where_the_two_are_evenest(
    client, mailbox, tomek, crowd
):
    cards = {card["nickname"]: card for card in await row(client, mailbox, tomek)}

    kuba = cards["kuba"]
    padel = forecast(Sport.PADEL, (2.71, SURE), (2.80, SURE))
    tennis = forecast(Sport.TENNIS, (3.10, SURE), (3.35, SURE))
    assert padel > tennis
    assert kuba["shown"] == {
        "sport": "PADEL",
        "your_level": 2.71,
        "their_level": 2.80,
        "percent_even": padel,
        "level_gap": 0.09,
        "your_band": {"name": "Established", "lower": 2.7, "upper": 3.8},
    }
    # The comparison sheet's blocks: every shared sport, most even first.
    assert [(one["sport"], one["percent_even"]) for one in kuba["sports"]] == [
        ("PADEL", padel),
        ("TENNIS", tennis),
    ]
    assert kuba["sports"][1]["level_gap"] == 0.25
    assert kuba["sports"][1]["your_band"]["name"] == "Established"
    # Zofia's squash is not Tomek's: one block, no *N sports ›*.
    zofia = cards["zofia"]
    assert zofia["shown"]["level_gap"] == -0.02
    assert [one["sport"] for one in zofia["sports"]] == ["PADEL"]


async def test_the_percent_is_the_forecast_for_sure_and_unsure_levels(
    client, mailbox, session_factory, tomek, crowd
):
    """Zofia, sure and 0,02 away, reads 91% — not 99 — and Bartek's
    questionnaire-only level reads lower than a sure one at his gap."""

    sure_at_bartek = await a_player(client, "ania")
    await rated(session_factory, sure_at_bartek, Sport.PADEL, 2.35)

    cards = {card["nickname"]: card for card in await row(client, mailbox, tomek)}

    assert cards["zofia"]["shown"]["percent_even"] == 91
    assert cards["zofia"]["shown"]["percent_even"] == forecast(
        Sport.PADEL, (2.71, SURE), (2.69, SURE)
    )
    assert cards["bartek"]["shown"]["percent_even"] == forecast(
        Sport.PADEL, (2.71, SURE), (2.35, UNSURE)
    )
    assert cards["ania"]["shown"]["percent_even"] == forecast(
        Sport.PADEL, (2.71, SURE), (2.35, SURE)
    )
    assert (
        cards["bartek"]["shown"]["percent_even"]
        <= cards["ania"]["shown"]["percent_even"]
    )


async def test_a_moved_level_is_compared_where_it_stands(
    client, mailbox, session_factory, tomek, crowd
):
    await moved(session_factory, crowd["kuba"], Sport.PADEL, 2.72)

    [kuba] = [
        card for card in await row(client, mailbox, tomek) if card["nickname"] == "kuba"
    ]

    assert kuba["shown"]["their_level"] == 2.72
    assert kuba["shown"]["percent_even"] == forecast(
        Sport.PADEL, (2.71, SURE), (2.72, SURE)
    )


# --------------------------------------------------------------------------- #
# The row of 10: fresh good matches first, then the gaps
# --------------------------------------------------------------------------- #


async def test_kuba_leads_as_a_fresh_match_and_zofia_waits_in_a_gap(
    client, mailbox, session_factory, tomek, crowd
):
    ania = await a_player(client, "ania")
    await rated(session_factory, ania, Sport.PADEL, 2.70)
    await asks(client, tomek, ania)

    cards = await row(client, mailbox, tomek)

    # Kuba (81%) is the only fresh good match; Ania (93%, asked by Tomek) and
    # Zofia (91%, a friend) are gaps, best % first, then Bartek, a weaker one.
    assert names(cards) == ["kuba", "ania", "zofia", "bartek"]
    assert [card["relation"] for card in cards] == ["NONE", "SENT", "FRIEND", "NONE"]


async def test_somebody_who_asked_the_reader_counts_as_fresh(
    client, mailbox, session_factory, tomek, crowd
):
    ania = await a_player(client, "ania")
    await rated(session_factory, ania, Sport.PADEL, 2.70)
    await asks(client, ania, tomek)

    cards = await row(client, mailbox, tomek)

    assert names(cards)[:2] == ["ania", "kuba"]
    assert cards[0]["relation"] == "ASKED_YOU"


async def test_a_new_good_match_takes_the_weakest_gap(
    client, mailbox, session_factory, tomek, crowd
):
    """Eight fresh matches, Zofia and Bartek fill the ten; Marta starts
    playing at a good match and Bartek leaves; one more, and Zofia does."""

    for n in range(7):
        stranger = await a_player(client, f"fresh{n}")
        await rated(session_factory, stranger, Sport.PADEL, round(2.72 + n / 100, 2))
    first = names(await row(client, mailbox, tomek))
    assert len(first) == 10
    assert first[-2:] == ["zofia", "bartek"]

    marta = await a_player(client, "marta")
    await rated(session_factory, marta, Sport.PADEL, 2.73)
    with_marta = names(await row(client, mailbox, tomek))
    assert "marta" in with_marta and "bartek" not in with_marta
    assert with_marta[-1] == "zofia"

    piotr = await a_player(client, "piotr")
    await rated(session_factory, piotr, Sport.PADEL, 2.74)
    full = names(await row(client, mailbox, tomek))
    assert "zofia" not in full and len(full) == 10


# --------------------------------------------------------------------------- #
# Who is never on it
# --------------------------------------------------------------------------- #


async def test_nobody_blocked_switched_off_or_not_playing_is_on_it(
    client, mailbox, session_factory, tomek, crowd
):
    blocked = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(crowd["kuba"]["id"])},
        headers=tomek["headers"],
    )
    assert blocked.status_code == 204, blocked.text
    blocker = await a_player(client, "blocker")
    await rated(session_factory, blocker, Sport.PADEL, 2.71)
    blocks_tomek = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(tomek["id"])},
        headers=blocker["headers"],
    )
    assert blocks_tomek.status_code == 204, blocks_tomek.text
    shy = await a_player(client, "shy")
    await rated(session_factory, shy, Sport.PADEL, 2.71)
    await players.closed_to_new_people(client, shy["token"])
    halfway_id, _ = await players.register(client, "halfway")
    await rated(session_factory, {"id": halfway_id}, Sport.PADEL, 2.71)

    everyone = names(await row(client, mailbox, tomek))
    page = await see_all(client, mailbox, tomek)

    assert set(everyone) == {"zofia", "bartek"}
    assert set(names(page["players"])) == {"zofia", "bartek"}


# --------------------------------------------------------------------------- #
# See all
# --------------------------------------------------------------------------- #


async def test_see_all_is_everybody_best_first_friends_where_they_fall(
    client, mailbox, tomek, crowd
):
    page = await see_all(client, mailbox, tomek)

    # Zofia, a friend at 91%, stands first: See all rests nobody and holds no
    # gaps.
    assert names(page["players"]) == ["zofia", "kuba", "bartek"]
    assert page["next"] is None
    assert page["sports"] == ["PADEL", "TENNIS"]
    assert page["players"][1]["sports"][1]["sport"] == "TENNIS"


async def test_a_sport_re_compares_everybody_in_it(
    client, mailbox, session_factory, tomek, crowd
):
    ola = await a_player(client, "ola")
    await rated(session_factory, ola, Sport.TENNIS, 3.12, sigma=UNSURE)

    tennis = await see_all(client, mailbox, tomek, sport="TENNIS")

    # Ola, 0,02 away but unsure, reads 71%; Kuba, sure and 0,25 away, 58%.
    assert names(tennis["players"]) == ["ola", "kuba"]
    kuba = tennis["players"][1]
    assert kuba["shown"]["sport"] == "TENNIS"
    assert kuba["shown"]["percent_even"] == forecast(
        Sport.TENNIS, (3.10, SURE), (3.35, SURE)
    )
    # Every card keeps every shared sport for the sheet.
    assert [one["sport"] for one in kuba["sports"]] == ["PADEL", "TENNIS"]
    assert tennis["sports"] == ["PADEL", "TENNIS"]
    assert (await see_all(client, mailbox, tomek, sport="SQUASH"))["players"] == []


async def test_see_all_comes_in_pages_of_twenty(
    client, mailbox, session_factory, tomek
):
    for n in range(22):
        player = await a_player(client, f"p{n:02d}")
        await rated(session_factory, player, Sport.PADEL, round(2.71 + n / 50, 2))

    first = await see_all(client, mailbox, tomek)
    second = await see_all(client, mailbox, tomek, after=first["next"])

    assert names(first["players"]) == [f"p{n:02d}" for n in range(20)]
    assert names(second["players"]) == ["p20", "p21"]
    assert second["next"] is None
    percents = [card["shown"]["percent_even"] for card in first["players"]]
    assert percents == sorted(percents, reverse=True)


async def test_a_cursor_this_server_never_wrote_is_refused(client, tomek):
    read = await client.get(
        ALL, params={"after": "not-a-page"}, headers=tomek["headers"]
    )

    assert read.status_code == 400
    assert read.json()["code"] == "not_a_same_level_page"


# --------------------------------------------------------------------------- #
# A request from the row
# --------------------------------------------------------------------------- #


async def test_a_request_from_the_row_reads_todays_percent(
    client, mailbox, tomek, crowd
):
    kuba = crowd["kuba"]
    await asks(client, tomek, kuba, made_from="SAME_LEVEL", sport="PADEL")
    await mailbox.drain()

    [request] = (await client.get("/api/v1/home", headers=kuba["headers"])).json()[
        "friend_requests"
    ]
    [notice] = (await client.get(NOTICES, headers=kuba["headers"])).json()["notices"]

    pct = forecast(Sport.PADEL, (2.80, SURE), (2.71, SURE))
    assert request["from_same_level"] is True
    assert request["sport"] == "PADEL"
    assert request["group"] is None
    assert request["percent_even"] == pct
    assert notice["body"] == f"Your level in padel · {pct}% even"


async def test_a_request_falls_back_when_either_holds_no_level_there(
    client, mailbox, tomek, crowd
):
    kuba = crowd["kuba"]
    # Neither holds a squash level: the line can't be worked out.
    await asks(client, tomek, kuba, made_from="SAME_LEVEL", sport="SQUASH")
    await mailbox.drain()

    [request] = (await client.get("/api/v1/home", headers=kuba["headers"])).json()[
        "friend_requests"
    ]
    [notice] = (await client.get(NOTICES, headers=kuba["headers"])).json()["notices"]

    assert request["from_same_level"] is True
    assert request["percent_even"] is None
    assert notice["body"] == "Found you at your squash level"


async def test_a_request_from_the_row_names_its_sport_and_no_group(
    client, tomek, crowd
):
    refused = await client.post(
        REQUESTS,
        json={"player_id": str(crowd["kuba"]["id"]), "made_from": "SAME_LEVEL"},
        headers=tomek["headers"],
    )

    assert refused.status_code == 422


async def test_a_request_from_anywhere_else_is_not_from_the_row(
    client, mailbox, tomek, crowd
):
    await asks(client, tomek, crowd["kuba"], sport="PADEL")
    await mailbox.drain()

    [request] = (
        await client.get("/api/v1/home", headers=crowd["kuba"]["headers"])
    ).json()["friend_requests"]

    assert request["from_same_level"] is False
    assert request["percent_even"] is None


# --------------------------------------------------------------------------- #
# The current-level projection
# --------------------------------------------------------------------------- #


async def stored_levels(session_factory) -> list[tuple]:
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(DiscoveryLevelORM).order_by(
                    DiscoveryLevelORM.player_id, DiscoveryLevelORM.sport
                )
            )
        ).scalars()
        return [
            (
                row.player_id,
                row.sport,
                row.mu,
                row.sigma,
                row.band_name,
                row.band_lower,
                row.band_upper,
                row.results,
            )
            for row in rows
        ]


async def test_the_rebuild_writes_what_live_delivery_wrote_and_twice_changes_nothing(
    client, mailbox, session_factory, tomek, crowd
):
    await moved(session_factory, crowd["kuba"], Sport.PADEL, 2.74)
    await moved(session_factory, crowd["kuba"], Sport.PADEL, 2.77, sigma=0.12)
    await mailbox.drain()
    live = await stored_levels(session_factory)
    live_row = await row(client, mailbox, tomek)
    assert len(live) == 7  # tomek 2, zofia 2, kuba 2, bartek 1

    # Today's ratings, before the projection shipped: nobody compared.
    async with session_factory() as session:
        await session.execute(delete(DiscoveryLevelORM))
        await session.commit()
    assert await row(client, mailbox, tomek) == []

    for _ in range(2):
        async with session_factory() as session:
            rebuilt = await build_rebuild_the_levels(session).execute()
        assert rebuilt.levels == 7
        assert await stored_levels(session_factory) == live

    assert await row(client, mailbox, tomek) == live_row


async def test_a_fold_with_fewer_results_never_replaces_the_stored_one(
    session_factory, tomek
):
    """Two deliveries at once: the one that read the stream before the other's
    move committed writes last, and the move stands."""

    def level(mu: float, results: int) -> CurrentLevel:
        return CurrentLevel(
            player_id=tomek["id"],
            sport=Sport.SQUASH,
            mu=mu,
            sigma=SURE,
            band=Band(name="Established", lower=2.7, upper=3.8),
            results=results,
        )

    async with session_factory() as session:
        levels = build_player_levels(session)
        await levels.save(level(2.80, results=2))
        await levels.save(level(2.75, results=1))
        await session.commit()
        stored = await levels.of_player(tomek["id"])

    assert stored[Sport.SQUASH].mu == 2.80
    assert stored[Sport.SQUASH].results == 2
