"""The Players deal — the deck, over HTTP.

Every assertion lands on the real route through the async client fixture: ASGI
transport over in-memory SQLite, **no MinIO, no sidecar and no Redis**.

What is asserted is the product's promises rather than the plumbing. That no mode
crosses the wire in either direction, and that the week the player just edited is
the one the deal runs on. That **every viewer is dealt under the fun ruler**,
declared or not, and that the intent term stands down on every card
(``docs/adr/0169`` §2). That the order is the deck's own two bands. That **a
spent deal deals again**, and that only a fresh deal coming back empty is the
honest empty state. That somebody the viewer has a court with is **cooling off**
and absent from the deal while present on the shortlist (§6). That the envelope
says how many people are beyond the hand and how many are waiting (§4, §5). And
that the two facts nobody can see from any screen — how many cards a
suppression removed, and whether a card is a re-show — are on the record where
an analyst can find them.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.kernel import Sport, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.matchmaking.domain.searches import SearchSurface
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


@pytest.fixture
async def a_city(client, session_factory, candidate_source, searcher):
    """One searcher and three findable candidates, at three Levels.

    Three rather than one, because most of what the deck promises is about
    *order* and *what a second deal does*, and neither is observable with a pool
    of one.
    """

    others = [
        await world.a_candidate(
            client, session_factory, name, mu=searcher["mu"] + offset
        )
        for name, offset in (("bea", 0.0), ("cara", 0.02), ("dee", -0.02))
    ]
    await world.fold_the_log(session_factory, candidate_source)
    return others


# ---------------------------------------------------------------------------
# One deal
# ---------------------------------------------------------------------------


async def test_a_deal_names_no_mode_in_either_direction(client, searcher, a_city):
    """**No mode crosses the wire, in either direction.**

    The deck reads the viewer's own declaration instead — which is why the
    envelope's `mode` comes back null rather than echoing something the request
    never sent, and why there is no field for one to arrive through.
    """

    dealt = await world.deck(client, searcher["token"])

    assert dealt.status_code == 200, dealt.text
    body = dealt.json()
    assert body["search"]["surface"] == SearchSurface.DECK.value
    assert body["search"]["mode"] is None, "the deck has no mode"
    assert body["search"]["search_id"], "one deal, one search id"
    assert body["candidates"], "three findable people and an empty deal"


async def test_a_deal_runs_on_the_week_the_player_just_edited(
    client, session_factory, searcher, a_city
):
    """**Match me reads the improvised week, and offers to keep it.**

    The alternative was a deck that silently ranks on a week the player has just
    replaced. The three refusals this body is written under are a mode, a
    widening and a pass window; a grid is none of them.
    """

    dealt = await world.deck(
        client, searcher["token"], availability_override=[{"day": 4, "part": "EVENING"}]
    )

    assert dealt.status_code == 200, dealt.text
    prompts = {
        prompt["prompt"]: prompt for prompt in dealt.json()["search"]["prompts"]
    }
    assert prompts["KEEP_THESE_TIMES"]["slots"] == [{"day": 4, "part": "EVENING"}]

    recorded = (await world.recorded_searches(session_factory))[-1]
    assert list(recorded.searcher_grid) == ["4:EVENING"]
    # The area is recorded beside the week and on the same terms — a deal is a
    # search, and its envelope carries both halves of the card's one comparison.
    assert recorded.searcher_area_code
    assert dealt.json()["search"]["my_area_code"] == recorded.searcher_area_code
    assert await world.saved_grid(session_factory, searcher["id"]) == (
        "2:EVENING",
        "6:MORNING",
    ), "the profile is untouched"


async def test_a_deal_on_the_profiles_own_week_asks_nothing(
    client, searcher, a_city
):
    """A prompt is raised by something having happened, and an empty list is the
    honest way to say nothing did — the deck runs them now rather than not
    having them."""

    dealt = await world.deck(client, searcher["token"])

    assert dealt.json()["search"]["prompts"] == []


async def test_a_cleared_week_deals_a_deck(client, searcher, a_city):
    """The same bug, on the third surface: unticking every cell is an edit."""

    dealt = await world.deck(client, searcher["token"], availability_override=[])

    assert dealt.status_code == 200, dealt.text
    prompts = {
        prompt["prompt"]: prompt for prompt in dealt.json()["search"]["prompts"]
    }
    assert prompts["KEEP_THESE_TIMES"]["slots"] == []


async def test_the_declaration_is_recorded_and_the_vector_is_not(
    client, session_factory, searcher, a_city
):
    """`intent_read` records **the declaration as it stood** — for history, and
    for nothing the deal does with it (``docs/adr/0169`` §2)."""

    await world.deck(client, searcher["token"])

    recorded = await world.recorded_searches(session_factory)
    deal = recorded[-1]
    assert deal.surface == SearchSurface.DECK.value
    assert deal.mode is None
    assert deal.intent_read == "COMPETITIVE", "the declaration, not a vector"


async def test_a_player_with_no_preference_still_gets_a_working_deck(
    client, session_factory, candidate_source
):
    """**Indecision is not a blocked state**, and the declaration is what is
    recorded — so the row says `NO_PREFERENCE` while the deal ran on the ruler
    every deal runs on."""

    undecided = await world.a_searcher(client, "undecided", intent="NO_PREFERENCE")
    await world.a_candidate(
        client, session_factory, "eve", mu=undecided["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)

    dealt = await world.deck(client, undecided["token"])

    assert dealt.status_code == 200, dealt.text
    assert dealt.json()["candidates"], "no preference is an answer, not a refusal"
    recorded = await world.recorded_searches(session_factory)
    assert recorded[-1].intent_read == "NO_PREFERENCE"


# ---------------------------------------------------------------------------
# The fun ruler for everyone, and the term that stands down
# ---------------------------------------------------------------------------


async def test_the_deck_reads_no_declaration_and_deals_a_viewer_who_never_made_one(
    client, session_factory, candidate_source
):
    """**Never a `409`** (``docs/adr/0169`` §2): a player who never declared is
    dealt without being asked to, and the row records that nothing stood."""

    player_id, token = await world.register(client, "undeclared")
    await world.commit_profile(client, token)
    mu = await world.rate(client, token)
    await world.a_candidate(client, session_factory, "fay", mu=mu)
    await world.fold_the_log(session_factory, candidate_source)

    dealt = await world.deck(client, token)

    assert dealt.status_code == 200, dealt.text
    assert dealt.json()["candidates"], "a working deck, with no declaration read"
    recorded = await world.recorded_searches(session_factory)
    assert recorded[-1].surface == SearchSurface.DECK.value
    assert recorded[-1].intent_read is None, "the declaration as it stood: none"


async def test_two_viewers_who_declared_differently_are_dealt_the_same_deck(
    client, session_factory, candidate_source
):
    """A viewer declared *competitive* and one declared *for fun*, otherwise
    alike, asking the same padel deck get the same order **and the same Fit per
    card** — every deal scores under the fun ruler, so what either declared
    moves nothing."""

    competitive = await world.a_searcher(client, "keen", intent="COMPETITIVE")
    for_fun = await world.a_searcher(client, "easy", intent="FOR_FUN")
    others = [
        await world.a_candidate(
            client, session_factory, name, mu=competitive["mu"] + offset, intent=intent
        )
        for name, offset, intent in (
            ("gia", 0.0, "COMPETITIVE"),
            ("hal", 0.02, "FOR_FUN"),
            ("ivy", -0.02, "NO_PREFERENCE"),
        )
    ]
    await world.fold_the_log(session_factory, candidate_source)

    keen = (await world.deck(client, competitive["token"])).json()
    easy = (await world.deck(client, for_fun["token"])).json()

    def dealt(body):
        return [
            (row["player_id"], row["fit"])
            for row in body["candidates"]
            if UUID(row["player_id"]) in set(others)
        ]

    assert len(dealt(keen)) == 3
    assert dealt(keen) == dealt(easy)


async def test_the_intent_term_stands_down_on_every_card_and_reads_on_a_shortlist(
    client, searcher, a_city
):
    """On a deal `INTENT_ALIGNMENT` is in `degraded_terms` for every card under
    a code that is neither side's gap, and never in `terms`; on a shortlist over
    the same people it still reads (``docs/adr/0169`` §2)."""

    dealt = (await world.deck(client, searcher["token"])).json()
    listed = (await world.search(client, searcher["token"])).json()

    assert dealt["candidates"] and listed["candidates"]
    for row in dealt["candidates"]:
        assert "INTENT_ALIGNMENT" not in {term["term"] for term in row["terms"]}
        assert {"term": "INTENT_ALIGNMENT", "reason": "NOT_READ_ON_THIS_SURFACE"} in [
            {"term": stood["term"], "reason": stood["reason"]}
            for stood in row["degraded_terms"]
        ]
    for row in listed["candidates"]:
        assert "INTENT_ALIGNMENT" in {term["term"] for term in row["terms"]}


async def test_a_deal_is_capped_and_the_cap_is_not_a_target(
    client, session_factory, candidate_source, searcher
):
    """At most `DECK_DEAL_MAX` cards, which is **10**.

    The number is ruleset data and never crosses the wire — a client renders the
    cards it is given — so this asserts the bound rather than reading it from
    anywhere.
    """

    for number in range(12):
        await world.a_candidate(
            client, session_factory, f"p{number}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    dealt = (await world.deck(client, searcher["token"])).json()

    assert len(dealt["candidates"]) == 10


# ---------------------------------------------------------------------------
# A spent deal deals again
# ---------------------------------------------------------------------------


async def test_a_spent_deal_deals_again_with_nobody_repeated(
    client, session_factory, candidate_source, searcher
):
    """**Running out of cards is not running out of people.**

    A second deal is a new search with a new id and the same exclusions plus
    everybody already dealt — so the next request answers with the *next* people
    rather than the same ten in the same order.
    """

    for number in range(12):
        await world.a_candidate(
            client, session_factory, f"q{number}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    first = (await world.deck(client, searcher["token"])).json()
    second = (await world.deck(client, searcher["token"])).json()

    assert first["search"]["search_id"] != second["search"]["search_id"]
    dealt_first = {row["player_id"] for row in first["candidates"]}
    dealt_again = {row["player_id"] for row in second["candidates"]}
    assert dealt_first, "the first deal was empty and proves nothing"
    assert not (dealt_first & dealt_again), "a spent deal dealt the same cards"


async def test_an_exhausted_pool_says_so_honestly(client, searcher, a_city):
    """A fresh deal that comes back with nothing is the honest empty state.

    It is a `200` with the pool described, exactly like any other deal, and it is
    recorded exactly like any other search — the absence of a row is never how
    emptiness is expressed.
    """

    while (dealt := (await world.deck(client, searcher["token"])).json())[
        "candidates"
    ]:
        pass

    assert dealt["candidates"] == []
    assert dealt["search"]["pool"]["players_in_range"] >= 1, (
        "the pool is described even when the deal is empty — a thin pool and "
        "your own exhausted deck must be tellable apart"
    )


# ---------------------------------------------------------------------------
# The two counts on the envelope
# ---------------------------------------------------------------------------


async def test_remaining_is_the_eligible_beyond_the_hand_and_drops_as_hands_are_dealt(
    client, session_factory, candidate_source, searcher
):
    """`pool.remaining` (``docs/adr/0169`` §5) is the count of people eligible
    after every deck exclusion who are not in this hand, and the next hand
    remembers this one."""

    for number in range(14):
        await world.a_candidate(
            client, session_factory, f"r{number}", mu=searcher["mu"]
        )
    await world.fold_the_log(session_factory, candidate_source)

    first = (await world.deck(client, searcher["token"])).json()
    second = (await world.deck(client, searcher["token"])).json()

    assert len(first["candidates"]) == 10
    assert first["search"]["pool"]["remaining"] == 4
    assert len(second["candidates"]) == 4
    assert second["search"]["pool"]["remaining"] == 0


async def test_want_to_play_you_counts_the_yeses_waiting_and_is_nought_when_nobody_is(
    client, session_factory, candidate_source, searcher
):
    """`pool.want_to_play_you` (``docs/adr/0169`` §4): present as `0` when
    nobody is waiting, `1` once somebody's live yes would be dealt, still `1`
    after they were dealt this morning — the dealt memory is not applied — and
    `0` again once the viewer has passed on them."""

    bea = await world.a_searcher(client, "bea")
    await world.a_candidate(client, session_factory, "cara", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    # Nobody has said yes to bea: her own deal counts and finds nought.
    quiet = (await world.deck(client, bea["token"])).json()
    assert quiet["search"]["pool"]["want_to_play_you"] == 0

    await world.a_yes(
        client, session_factory, candidate_source, sender=bea, towards=searcher["id"]
    )
    waiting = (await world.deck(client, searcher["token"])).json()
    assert waiting["search"]["pool"]["want_to_play_you"] == 1
    dealt_bea = next(
        row for row in waiting["candidates"] if row["player_id"] == str(bea["id"])
    )
    assert dealt_bea["inclusion_reason"] == "INTEREST_LIFT"
    # **Unmarked beyond that**: the same fields every other card carries, and
    # no sentence, tag or flag saying they said yes.
    other = next(
        row for row in waiting["candidates"] if row["player_id"] != str(bea["id"])
    )
    assert set(dealt_bea) - set(other) <= {"inclusion_reason"}

    still_waiting = (await world.deck(client, searcher["token"])).json()
    assert str(bea["id"]) not in {
        row["player_id"] for row in still_waiting["candidates"]
    }, "dealt this morning, so remembered for a day"
    assert still_waiting["search"]["pool"]["want_to_play_you"] == 1, (
        "dealt this morning and unanswered is still waiting"
    )

    passed = await world.pass_on(
        client,
        searcher["token"],
        player_id=bea["id"],
        search_id=waiting["search"]["search_id"],
    )
    assert passed.status_code == 204, passed.text
    answered = (await world.deck(client, searcher["token"])).json()
    assert answered["search"]["pool"]["want_to_play_you"] == 0


async def test_the_two_counts_are_a_deals_and_cross_on_no_other_envelope(
    client, searcher, a_city
):
    """Present on a deal, omitted on a shortlist and on a read-back: the counts
    are as fresh as the hand, and a month-old count would be a number about a
    pool that has moved on."""

    dealt = (await world.deck(client, searcher["token"])).json()
    listed = (await world.search(client, searcher["token"])).json()
    read = (
        await world.read_back(client, searcher["token"], dealt["search"]["search_id"])
    ).json()

    assert {"remaining", "want_to_play_you"} <= set(dealt["search"]["pool"])
    assert not {"remaining", "want_to_play_you"} & set(listed["search"]["pool"])
    assert not {"remaining", "want_to_play_you"} & set(read["search"]["pool"])


# ---------------------------------------------------------------------------
# The cool-off
# ---------------------------------------------------------------------------


async def _a_game_between(
    session_factory, one: UUID, other: UUID, *, planned_at: datetime, played_at=None
) -> None:
    """A real game on the record, through the aggregate — ahead, or played at a
    moment."""

    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=one),
                Seating(side=GameSide.B, player_id=other),
            )
        ),
        occurred_at=instant(planned_at),
    )
    if played_at is not None:
        game.state_result(
            by=one,
            score=Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
            occurred_at=instant(played_at),
        )
    async with session_factory() as session:
        await build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(game)
        await session.commit()


@pytest.mark.parametrize(
    "days_ago,dealt",
    [
        pytest.param(None, False, id="a game still ahead"),
        pytest.param(10, False, id="played ten days ago"),
        pytest.param(40, True, id="played forty days ago"),
    ],
)
async def test_somebody_the_viewer_has_a_court_with_is_absent_from_the_deal_only(
    client, session_factory, candidate_source, searcher, a_city, days_ago, dealt
):
    """**Deck only, thirty days** (``docs/adr/0169`` §6). A live game holds its
    counterpart out of the deal for as long as it stands, and a game behind
    them for thirty days after; Find a game keeps ``docs/adr/0142`` §1's
    release and lists them throughout."""

    bea = a_city[0]
    now = datetime.now(timezone.utc)
    if days_ago is None:
        await _a_game_between(
            session_factory, searcher["id"], bea, planned_at=now - timedelta(hours=1)
        )
    else:
        await _a_game_between(
            session_factory,
            searcher["id"],
            bea,
            planned_at=now - timedelta(days=days_ago, hours=2),
            played_at=now - timedelta(days=days_ago),
        )

    deal = (await world.deck(client, searcher["token"])).json()
    listed = (await world.search(client, searcher["token"])).json()

    assert (str(bea) in {row["player_id"] for row in deal["candidates"]}) is dealt
    assert str(bea) in {row["player_id"] for row in listed["candidates"]}
    assert deal["search"]["pool"]["players_in_range"] == 3, (
        "the cool-off is not a gate: the pool is a fact about the city"
    )


# ---------------------------------------------------------------------------
# Show them again
# ---------------------------------------------------------------------------


def _dealt(deal: dict) -> set[str]:
    return {row["player_id"] for row in deal["candidates"]}


async def test_show_them_again_deals_the_passed_the_dealt_and_the_cooling_off_again(
    client, session_factory, searcher, a_city
):
    """**One request, and the deck is whole again** (``docs/adr/0169`` §5).

    Bea is cooling off after a game ten days ago, Cara was passed on, and Dee
    was dealt this morning — so the next deal is honestly empty: everybody in
    range is excluded, which is the *You have seen everybody* ending. *Show them
    again* clears all three at once for this sport, and the deal after it deals
    all three. The pass record is untouched — a re-shown card is still a
    re-show — and the deal no longer counts a suppression it does not apply.
    """

    bea, cara, dee = a_city
    now = datetime.now(timezone.utc)
    await _a_game_between(
        session_factory,
        searcher["id"],
        bea,
        planned_at=now - timedelta(days=10, hours=2),
        played_at=now - timedelta(days=10),
    )
    first = (await world.deck(client, searcher["token"])).json()
    assert _dealt(first) == {str(cara), str(dee)}
    passed = await world.pass_on(
        client,
        searcher["token"],
        player_id=cara,
        search_id=first["search"]["search_id"],
    )
    assert passed.status_code == 204, passed.text
    spent = (await world.deck(client, searcher["token"])).json()
    assert spent["candidates"] == [], "somebody was dealt with everybody excluded"

    reset = await world.show_them_again(client, searcher["token"])
    whole = (await world.deck(client, searcher["token"])).json()

    assert reset.status_code == 204, reset.text
    assert reset.content == b"", "a reset never carries a body"
    assert _dealt(whole) == {str(bea), str(cara), str(dee)}
    rows = await world.recorded_passes(session_factory)
    assert [str(row.passed_id) for row in rows] == [str(cara)], (
        "the reset touched the pass record"
    )
    recorded = await world.recorded_searches(session_factory)
    assert recorded[-1].n_excluded_by_suppression == 0, (
        "the deal counted a suppression the reset had cleared"
    )
    re_shown = await world.recorded_candidates(session_factory, recorded[-1].id)
    assert {str(row.player_id): row.suppression_lapsed for row in re_shown} == {
        str(bea): False,
        str(cara): False,
        str(dee): False,
    }, (
        "a reset re-show is not a lapsed suppression: the flag says the window "
        "ran out, and it has not — the reset ledger is what names these"
    )


async def test_show_them_again_leaves_a_live_yes_and_another_sports_passes_alone(
    client, session_factory, candidate_source, searcher, a_city
):
    """**What the reset does not clear.** The people the viewer has a live yes
    on are still theirs to wait on, and a reset is one sport's: resetting
    tennis lifts no padel pass."""

    bea, cara, dee = a_city
    await world.rate(client, searcher["token"], Sport.TENNIS)
    first = (await world.deck(client, searcher["token"])).json()
    await world.pass_on(
        client,
        searcher["token"],
        player_id=cara,
        search_id=first["search"]["search_id"],
    )
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=dee
    )

    other_sport = await world.show_them_again(
        client, searcher["token"], Sport.TENNIS
    )
    assert other_sport.status_code == 204, other_sport.text
    after_tennis = (await world.deck(client, searcher["token"])).json()
    this_sport = await world.show_them_again(client, searcher["token"])
    assert this_sport.status_code == 204, this_sport.text
    after_padel = (await world.deck(client, searcher["token"])).json()

    assert str(cara) not in _dealt(after_tennis), "a tennis reset lifted a padel pass"
    assert str(cara) in _dealt(after_padel)
    assert str(dee) not in _dealt(after_padel), "a live yes was dealt again"
    mine = (await world.read_interest(client, searcher["token"])).json()
    assert [row["player_id"] for row in mine["outgoing"]] == [str(dee)]


async def test_another_sports_passes_still_suppress_after_a_reset(
    client, session_factory, candidate_source, searcher, a_city
):
    """A reset is one sport's, seen from the other sport's own deck: Cara is
    passed on in tennis, padel is reset, and the tennis deck still holds her
    out."""

    bea, cara, dee = a_city
    await world.rate(client, searcher["token"], Sport.TENNIS)
    await world.rate_in(session_factory, cara, Sport.TENNIS, mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    tennis = (await world.deck(client, searcher["token"], Sport.TENNIS)).json()
    assert _dealt(tennis) == {str(cara)}, "the tennis deck has nobody to pass on"
    passed = await world.pass_on(
        client,
        searcher["token"],
        player_id=cara,
        search_id=tennis["search"]["search_id"],
        sport=Sport.TENNIS,
    )
    assert passed.status_code == 204, passed.text

    reset = await world.show_them_again(client, searcher["token"], Sport.PADEL)
    tennis_again = (await world.deck(client, searcher["token"], Sport.TENNIS)).json()

    assert reset.status_code == 204, reset.text
    assert tennis_again["candidates"] == [], "a padel reset lifted a tennis pass"


async def test_a_second_reset_is_a_204_and_changes_nothing(
    client, session_factory, searcher, a_city
):
    """Idempotent: pressing it twice in a row is one press. The record of the
    press is kept either way, and nothing else is written."""

    bea, cara, dee = a_city
    first = (await world.deck(client, searcher["token"])).json()
    await world.pass_on(
        client,
        searcher["token"],
        player_id=bea,
        search_id=first["search"]["search_id"],
    )

    once = await world.show_them_again(client, searcher["token"])
    twice = await world.show_them_again(client, searcher["token"])
    dealt = (await world.deck(client, searcher["token"])).json()

    assert once.status_code == twice.status_code == 204
    assert _dealt(dealt) == {str(bea), str(cara), str(dee)}
    assert len(await world.recorded_passes(session_factory)) == 1


async def test_a_reset_is_refused_under_a_hold_and_for_a_sport_you_are_not_rated_in(
    client, searcher, a_city
):
    """The deal's two refusals about *you*, one code each: nothing is written
    for a deck that cannot be dealt."""

    unrated = await world.show_them_again(client, searcher["token"], Sport.TENNIS)
    assert unrated.status_code == 409, unrated.text
    assert unrated.json()["code"] == "sport_not_rated"

    world.hold_everybody(client)
    held = await world.show_them_again(client, searcher["token"])
    assert held.status_code == 403, held.text
    assert held.json()["code"] == "account_held"


# ---------------------------------------------------------------------------
# What the deck is not
# ---------------------------------------------------------------------------


async def test_the_relaxation_ladder_does_not_reach_the_deck(
    client, session_factory, candidate_source
):
    """No rung offers on a deal, ever — **null, not an empty list.**

    `null` is *the offers were not computed at all*, which is the truth here: a
    ladder that ran and found nothing would be an empty list, and that would be a
    different claim.
    """

    lonely = await world.a_searcher(client, "lonely")
    await world.fold_the_log(session_factory, candidate_source)

    dealt = (await world.deck(client, lonely["token"])).json()

    assert dealt["candidates"] == []
    assert dealt["search"]["rung_offers"] is None


async def test_a_deal_draws_no_re_sorts(client, searcher, a_city):
    """A deck is one card at a time, so there is no list to reorder.

    Its order **is** its variety, and a control that resorted a deal would offer
    to undo the one thing the surface does.
    """

    dealt = (await world.deck(client, searcher["token"])).json()

    assert dealt["search"]["sorts_available"] == []


async def test_the_re_show_flag_is_written_on_a_dealt_card_and_nowhere_else(
    client, session_factory, searcher, a_city
):
    """`suppression_lapsed` is set exactly where a card was dealt.

    `false` on a card nobody was ever passed on, and **null** on a shortlist row
    — a biconditional rather than a default, because *not a re-show* and *not a
    card* are different sentences and only one of them is a measurement.
    """

    dealt = (await world.deck(client, searcher["token"])).json()
    await world.search(client, searcher["token"])

    recorded = await world.recorded_searches(session_factory)
    cards = await world.recorded_candidates(
        session_factory, dealt["search"]["search_id"]
    )
    assert cards, "the deal was empty and proves nothing"
    assert all(
        row.suppression_lapsed is False
        for row in cards
        if row.band == "RETURNED"
    )
    shortlist = next(row for row in recorded if row.surface == "SHORTLIST")
    listed = await world.recorded_candidates(session_factory, shortlist.id)
    assert all(row.suppression_lapsed is None for row in listed)


async def test_a_deal_reads_back_in_the_same_shape(client, searcher, a_city):
    """`GET /searches/{id}` returns the same schema the `POST` did.

    The same rule for all four surfaces — which is why a deal crosses in the
    envelope a shortlist crosses in rather than a shape of its own.
    """

    dealt = (await world.deck(client, searcher["token"])).json()

    read = await world.read_back(
        client, searcher["token"], dealt["search"]["search_id"]
    )

    assert read.status_code == 200, read.text
    body = read.json()
    assert body["search"]["surface"] == SearchSurface.DECK.value
    assert body["search"]["mode"] is None
    assert [row["player_id"] for row in body["candidates"]] == [
        row["player_id"] for row in dealt["candidates"]
    ]


async def test_a_dealt_card_quotes_the_line_its_player_wrote_and_closes_up_otherwise(
    client, session_factory, candidate_source, searcher
):
    """**The one field ADR-0107 §2's closed list gains** (``docs/adr/0170`` §3).

    Karol wrote a line and it is on his card, verbatim; Ola skipped and her card
    has no key at all — omitted, never an empty string — so the layout closes up
    rather than drawing a blank quotation. And the read-back quotes the line as
    it stood at the deal, because the card is attached to the search record when
    it is served (``docs/adr/0104``).
    """

    karol = await world.a_candidate(
        client,
        session_factory,
        "karol",
        mu=searcher["mu"],
        intro="Moved from Wrocław in May. Needs opponents.",
    )
    ola = await world.a_candidate(client, session_factory, "ola", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    dealt = await world.deck(client, searcher["token"])

    assert dealt.status_code == 200, dealt.text
    cards = {
        UUID(candidate["player_id"]): candidate["player_card"]
        for candidate in dealt.json()["candidates"]
    }
    assert cards[karol]["intro"] == "Moved from Wrocław in May. Needs opponents."
    assert "intro" not in cards[ola], "an absent line was drawn as something"

    read_back = await world.read_back(
        client, searcher["token"], dealt.json()["search"]["search_id"]
    )
    assert read_back.status_code == 200, read_back.text
    quoted = {
        UUID(candidate["player_id"]): candidate["player_card"]
        for candidate in read_back.json()["candidates"]
    }
    assert quoted[karol]["intro"] == "Moved from Wrocław in May. Needs opponents."
    assert "intro" not in quoted[ola]


async def test_a_dealt_card_carries_the_photograph_it_is_mostly_made_of(
    client, session_factory, candidate_source, searcher
):
    """**The deck's whole card is a photograph.**

    A deal that handed back an id the client cannot sign for would draw the
    generated poster on every card, which would quietly make the poster the
    product rather than the fallback it argued itself into being.
    """

    photo = uuid4()
    dealt_to = await world.a_candidate(
        client, session_factory, "bea", mu=searcher["mu"], photo_ids=(photo,)
    )
    await world.fold_the_log(session_factory, candidate_source)

    card = (await world.deck(client, searcher["token"])).json()["candidates"][0][
        "player_card"
    ]

    assert card["photo_id"] == str(photo)
    assert card["photo_url"].endswith(f"{dealt_to}/{photo}")
