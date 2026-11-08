"""The General ranking, read the way the player app reads it (#768;
``docs/adr/0203``; the rankings mechanics §3–§5, §8).

Tomek, Karol, Zofia and Inés play padel together — every game a booked game,
its score stated and accepted through the player routes, and the outbox
delivered as the worker delivers it: the agreement moves the four Levels, and
each move folds its player's row. Every claim is read off
``GET /rankings/padel`` and ``GET /home``.

**Where a test needs exact Levels** — a tie, or who reached a Level first — the
Level is moved through the rating's own aggregate (``move_on_result``), which
records the same ``rating.moved_on_result`` a settled game does, on the same
outbox: no route takes dictation for a chosen Level.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import delete

from app.application.events import DeliveryContext
from app.bootstrap.composition import (
    build_domain_event_store,
    build_move_the_ranking,
    build_ranking_rows,
    build_rating_histories,
    build_rebuild_the_rankings,
)
from app.kernel import Sport
from app.modules.games.domain.lineup import GameKind
from app.modules.rankings.domain.ranking import row_of
from app.modules.rankings.infrastructure.ranking_model import RankingRowORM
from app.modules.rating.domain.events import RatingMovedOnResult
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from tests.api import players_world as players
from tests.api.rankings_world import (
    home_ranking,
    level_of,
    plays,
    ranking,
    results_at,
    stored_points,
    stored_rows,
    the_catch_up_runs,
)
from tests.unit.kept_orders import kept_orders_of


@pytest.fixture
async def four(client) -> dict[str, dict]:
    """Four padel players, each rated through a real questionnaire."""

    return {
        name: await players.a_rated_player(client, name)
        for name in ("tomek", "karol", "zofia", "ines")
    }


# --------------------------------------------------------------------------- #
# Who is listed
# --------------------------------------------------------------------------- #


async def test_four_results_need_one_more_and_the_fifth_lists_the_player(
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    for _ in range(4):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))

    before = await ranking(client, tomek)

    assert before["card"] == {
        "state": "NEEDS_RESULTS",
        "results": 4,
        "results_to_enter": 5,
        "place": None,
        "of": None,
        "level": None,
        "chip": None,
        "gap_line": None,
    }
    assert (before["listed"], before["rows"], before["podium"]) == (0, [], [])

    await plays(client, session_factory, clock, (zofia, ines), (tomek, karol))
    after = await ranking(client, tomek)

    assert after["view"] == "GENERAL"
    assert after["card"]["state"] == "LISTED"
    assert after["card"]["of"] == after["listed"] == 4
    assert after["card"]["level"] == await level_of(client, tomek)
    assert [row["nickname"] for row in after["rows"]][:2] in (
        ["karol", "tomek"],
        ["tomek", "karol"],
    )
    [mine] = [row for row in after["rows"] if row["is_you"]]
    assert mine["nickname"] == "tomek"
    assert mine["place"] == after["card"]["place"]
    assert mine["form"] == ["WIN", "WIN", "WIN", "WIN", "LOSS"]
    assert [row["place"] for row in after["rows"]] == [1, 2, 3, 4]
    assert [row["place"] for row in after["podium"]] == [1, 2, 3]


async def test_for_fun_games_no_score_and_disputes_never_count(
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    await plays(
        client,
        session_factory,
        clock,
        (tomek, karol),
        (zofia, ines),
        kind=GameKind.FRIENDLY,
    )
    await plays(
        client, session_factory, clock, (tomek, karol), (zofia, ines), ending="disputed"
    )
    await plays(
        client,
        session_factory,
        clock,
        (tomek, karol),
        (zofia, ines),
        ending="unrecorded",
    )
    # Every window on those games closes, and the catch-up folds whatever a
    # closing window settled.
    clock.move(timedelta(days=3))
    await the_catch_up_runs(session_factory, clock)

    card = (await ranking(client, tomek))["card"]

    assert (card["state"], card["results"]) == ("NEEDS_RESULTS", 1)


# --------------------------------------------------------------------------- #
# The order
# --------------------------------------------------------------------------- #


async def test_the_order_is_the_level_then_more_results_then_who_got_there_first(
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    # Inés leads on the Level alone.
    await results_at(session_factory, ines, [3.0, 3.1, 3.2, 3.3, 3.4], clock)
    # Karol reaches 2,75 first; Tomek reaches it later, with the same count.
    await results_at(session_factory, karol, [2.6, 2.65, 2.7, 2.72, 2.75], clock)
    await results_at(session_factory, tomek, [2.6, 2.65, 2.7, 2.72, 2.75], clock)
    # Zofia reaches 2,75 last of all, but has played one more.
    await results_at(session_factory, zofia, [2.6, 2.65, 2.7, 2.72, 2.73, 2.75], clock)

    rows = (await ranking(client, tomek))["rows"]

    assert [(row["place"], row["nickname"], row["level"]) for row in rows] == [
        (1, "ines", 3.4),
        (2, "zofia", 2.75),
        (3, "karol", 2.75),
        (4, "tomek", 2.75),
    ]


async def test_two_partners_moved_by_one_result_are_told_apart_by_their_id(
    client, session_factory, clock, four
):
    """The same Level, the same count, reached on the same result: every place
    is still unique, and the player id decides."""

    tomek, karol, zofia, ines = four.values()
    for _ in range(5):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))

    rows = (await ranking(client, tomek))["rows"]

    winners = sorted([tomek, karol], key=lambda player: str(player["id"]))
    assert [row["player_id"] for row in rows[:2]] == [str(one["id"]) for one in winners]
    assert rows[0]["level"] == rows[1]["level"]


# --------------------------------------------------------------------------- #
# 90 days
# --------------------------------------------------------------------------- #


async def test_ninety_one_days_on_the_player_is_off_the_list_and_the_next_result_brings_them_back(  # noqa: E501
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    for _ in range(5):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    assert (await ranking(client, tomek))["card"]["state"] == "LISTED"

    clock.move(timedelta(days=91))
    gone = await ranking(client, tomek)

    assert gone["card"] == {
        "state": "OFF_THE_LIST",
        "results": 5,
        "results_to_enter": 5,
        "place": None,
        "of": None,
        "level": None,
        "chip": None,
        "gap_line": None,
    }
    assert (gone["listed"], gone["rows"]) == (0, [])
    assert await home_ranking(client, tomek) == {
        "sport": "PADEL",
        "general_place": None,
        "friends_place": None,
    }

    await plays(client, session_factory, clock, (tomek, zofia), (karol, ines))
    back = await ranking(client, tomek)

    assert back["card"]["state"] == "LISTED"
    assert back["card"]["of"] == 4
    assert back["card"]["place"] == next(
        row["place"] for row in back["rows"] if row["is_you"]
    )


# --------------------------------------------------------------------------- #
# No level
# --------------------------------------------------------------------------- #


async def test_a_reader_with_no_level_in_the_sport_is_told_so(
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    for _ in range(5):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    ola = await players.a_rated_player(client, "ola", sport=Sport.TENNIS)

    read = await ranking(client, ola)

    assert read["card"]["state"] == "NO_LEVEL"
    assert read["card"]["results"] == 0
    assert read["listed"] == 4
    assert not any(row["is_you"] for row in read["rows"])


async def test_a_reader_with_a_level_and_no_result_needs_five(client, four):
    read = await ranking(client, four["tomek"])

    assert (read["card"]["state"], read["card"]["results"]) == ("NEEDS_RESULTS", 0)
    assert (read["listed"], read["podium"], read["rows"]) == (0, [], [])


async def test_an_unknown_sport_is_refused(client, four):
    read = await client.get(
        "/api/v1/rankings/PICKLEBALL", headers=players.auth(four["tomek"]["token"])
    )

    assert read.status_code == 422


# --------------------------------------------------------------------------- #
# The podium
# --------------------------------------------------------------------------- #


async def test_the_podium_shows_only_with_three_rows(
    client, session_factory, clock, four
):
    tomek, karol, zofia, _ = four.values()
    await results_at(session_factory, tomek, [2.6, 2.7, 2.8, 2.9, 3.0], clock)
    await results_at(session_factory, karol, [2.6, 2.7, 2.8, 2.9, 2.95], clock)

    two = await ranking(client, tomek)
    assert (len(two["rows"]), two["podium"]) == (2, [])

    await results_at(session_factory, zofia, [2.5, 2.5, 2.5, 2.5, 2.5], clock)
    three = await ranking(client, tomek)

    assert [(row["place"], row["nickname"]) for row in three["podium"]] == [
        (1, "tomek"),
        (2, "karol"),
        (3, "zofia"),
    ]
    assert three["podium"] == three["rows"][:3]


# --------------------------------------------------------------------------- #
# Home's trophy
# --------------------------------------------------------------------------- #


async def test_home_has_no_ranking_with_no_result_anywhere(client, four):
    assert await home_ranking(client, four["tomek"]) is None


async def test_home_carries_the_sport_of_the_latest_result_and_the_general_place(
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    assert await home_ranking(client, tomek) == {
        "sport": "PADEL",
        "general_place": None,
        "friends_place": None,
    }

    for _ in range(4):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    place = (await ranking(client, tomek))["card"]["place"]
    assert await home_ranking(client, tomek) == {
        "sport": "PADEL",
        "general_place": place,
        "friends_place": None,
    }

    # A tennis result after it: the trophy follows the latest result's sport,
    # where Tomek isn't listed yet.
    for player in (tomek, karol):
        await players.rate(client, player["token"], Sport.TENNIS)
        await players.declare_intent(client, player["token"], sport=Sport.TENNIS)
    await plays(client, session_factory, clock, (tomek,), (karol,), sport=Sport.TENNIS)

    assert await home_ranking(client, tomek) == {
        "sport": "TENNIS",
        "general_place": None,
        "friends_place": None,
    }


# --------------------------------------------------------------------------- #
# The projection
# --------------------------------------------------------------------------- #


async def test_the_rebuild_matches_live_delivery_and_running_it_twice_changes_nothing(
    client, session_factory, clock, four
):
    tomek, karol, zofia, ines = four.values()
    for _ in range(3):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    await plays(client, session_factory, clock, (tomek, zofia), (karol, ines))
    await plays(client, session_factory, clock, (zofia, ines), (tomek, karol))
    await plays(client, session_factory, clock, (tomek, ines), (karol, zofia))
    live = await stored_rows(session_factory)
    live_read = await ranking(client, tomek)

    # Today's players, before the ranking shipped: no row at all.
    async with session_factory() as session:
        await session.execute(delete(RankingRowORM))
        await session.commit()
    assert (await ranking(client, tomek))["listed"] == 0

    for _ in range(2):
        async with session_factory() as session:
            rebuilt = await build_rebuild_the_rankings(
                session, orders=kept_orders_of(session_factory)
            ).execute()
        assert (rebuilt.ratings, rebuilt.rows) == (4, 4)
        assert await stored_rows(session_factory) == live

    assert await ranking(client, tomek) == live_read


async def test_a_redelivered_move_changes_nothing(client, session_factory, clock, four):
    """Every move Tomek's stream holds, delivered a second time — each folds
    the whole stream again, the oldest first, and the row is the row. The level
    history is keyed by the event, so it gains nothing either (#769)."""

    tomek, karol, zofia, ines = four.values()
    for _ in range(5):
        await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))
    before = await stored_rows(session_factory)
    points = await stored_points(session_factory)
    assert len(points) == 4 * 6

    async with session_factory() as session:
        stream = await build_domain_event_store(session).load_stream(
            aggregate_type=RATING_AGGREGATE,
            aggregate_id=skill_rating_id(tomek["id"], Sport.PADEL),
        )
        mover = build_move_the_ranking(session, orders=kept_orders_of(session_factory))
        for record in stream:
            if isinstance(record.event, RatingMovedOnResult):
                await mover(
                    record.event,
                    DeliveryContext(
                        event_id=record.id, attempt=2, occurred_at=record.occurred_at
                    ),
                )
        await session.commit()

    assert await stored_rows(session_factory) == before
    assert await stored_points(session_factory) == points


async def test_a_fold_with_fewer_results_never_replaces_the_stored_row(
    client, session_factory, clock, four
):
    """A delivery that read the stream before another's move committed folds an
    older row; saved after the newer one, it takes nothing back."""

    tomek = four["tomek"]
    await results_at(session_factory, tomek, [2.6, 2.7], clock)
    async with session_factory() as session:
        history = await build_rating_histories(session).history_of(
            tomek["id"], Sport.PADEL
        )
    assert history is not None
    older = row_of(replace(history, moves=history.moves[:1]))
    newer = await stored_rows(session_factory)
    assert older is not None

    async with session_factory() as session:
        await build_ranking_rows(session).save(older)
        await session.commit()

    assert await stored_rows(session_factory) == newer
    assert (await ranking(client, tomek))["card"]["results"] == 2
