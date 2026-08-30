"""``GET /api/v1/searches/{id}`` — the recorded answer, plus live gate state.

A player opens a shortlist they ran this morning and gets the same answer back.
The record is immutable and never expires, because it *is* the answer's identity;
but the gates that fail closed are **live**, because a stored result that could
resurrect somebody blocked in the meantime is a safety hole dressed as a cache.

**The round trip is asserted over the record's fields**, never over a
byte-identical payload — ``docs/adr/0109`` wrote that down precisely because a
test drafted naively fails on a row that is *supposed* to differ and on a photo
link that is minted per response, and the temptation is to loosen the test rather
than to read the record.

Every assertion here lands on HTTP, through the async client fixture: ASGI
transport over in-memory SQLite, **no MinIO and no sidecar**.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.player_profile.domain.events import GenderPreferenceChanged
from tests.api import matchmaking_world as world

#: The moment a preference is changed in these tests: after every profile was
#: committed, so the projection applies it as the later answer it is.
LATER = world.LONG_AGO + timedelta(days=1)


def _without_the_minted_link(candidate: dict) -> dict:
    """One row, minus the one field on it that is not a recorded fact.

    ``photo_url`` is signed for *this* response over the id the row holds, so it
    is the one thing a round trip may not assert equality on — and dropping it
    here is what keeps the rest of the comparison exact.
    """

    card = candidate.get("player_card")
    if card is None:
        return candidate
    return {
        **candidate,
        "player_card": {
            field: value for field, value in card.items() if field != "photo_url"
        },
    }


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def a_search_of_two(client, session_factory, candidate_source, searcher):
    """One search over two candidates, and the body it answered with."""

    near = await world.a_candidate(
        client, session_factory, "near", mu=searcher["mu"]
    )
    far = await world.a_candidate(
        client, session_factory, "far", mu=searcher["mu"] + 0.2, latitude=51.55
    )
    await world.fold_the_log(session_factory, candidate_source)
    response = await world.search(client, searcher["token"])
    assert response.status_code == 200, response.text
    return response.json(), near, far


async def test_a_search_reads_back_as_the_answer_it_gave(
    client, session_factory, candidate_source, searcher
):
    """**The same schema, and the same answer.**

    Asserted over the record's fields rather than over the bytes: the envelope,
    the order, and every field of every row the record holds. What the record
    does not hold is not compared, which is the whole of ``docs/adr/0109``'s
    narrowing: the photo link is minted per response and is dropped from both
    sides below. This suite's store signs a pure function of the ref, so the two
    links would in fact match here — which is exactly the coincidence a test
    that compared them would come to depend on, and a real signature carries the
    moment it was taken.
    """

    posted, _, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    assert read.status_code == 200, read.text
    body = read.json()
    # **Every recorded fact, and the one thing that is not one.** `prompts` is a
    # statement about *now* — the week you improvised a moment ago, the widening
    # you keep taking, the drift a loop noticed yesterday — so it ships on the
    # search and is omitted here rather than re-asking a month-old question about
    # a value that has since moved. Everything else round-trips.
    assert "prompts" not in body["search"]
    assert body["search"] == {
        field: value
        for field, value in posted["search"].items()
        if field != "prompts"
    }, "the envelope is a recorded fact"
    assert len(body["candidates"]) == len(posted["candidates"])
    for again, first in zip(body["candidates"], posted["candidates"], strict=True):
        assert again["withheld"] is False, "a live row says so, positively"
        recorded = _without_the_minted_link(first)
        assert {key: _without_the_minted_link(again)[key] for key in recorded} == (
            recorded
        ), "the recorded answer came back different"


async def test_the_breakdown_survives_the_round_trip_whole(
    client, session_factory, candidate_source, searcher
):
    """*Why 78?* has to open as fast a month later as it did on the day.

    The terms, their evidence, the concerns, the degraded list and the card are
    on the row rather than re-read from sources that have moved on — so this is
    the assertion that the record is **self-contained**.
    """

    posted, _, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )

    body = (
        await world.read_back(
            client, searcher["token"], posted["search"]["search_id"]
        )
    ).json()

    row = body["candidates"][0]
    assert row["terms"], "a row read back with no working behind its number"
    for term in row["terms"]:
        assert term["evidence"]["kind"]
        assert term["contribution"] == pytest.approx(term["weight"] * term["value"])
    assert row["player_card"]["nickname"]
    assert row["player_card"]["area_code"]
    # The Level **and** how sure of it the platform was, against the answer
    # that was actually given. A range re-read from a rating that has moved
    # since would be a different caveat under the same search id, which is the
    # whole reason the card is recorded — and a bound rather than an equality
    # here would pass on the re-read one.
    assert (
        row["player_card"]["range"]
        == posted["candidates"][0]["player_card"]["range"]
    )
    assert "concerns" in row and "degraded_terms" in row
    assert row["fit"] == posted["candidates"][0]["fit"]


async def test_a_block_since_the_search_withholds_the_row_and_states_it(
    client, session_factory, candidate_source, searcher
):
    """**A shrinking list is a lie.**

    The record is not rewritten and the row is not dropped: it keeps its place
    and says it is withheld. What it does not keep is the person — no id, no
    card, no breakdown to identify them by.
    """

    posted, near, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    assert len(posted["candidates"]) == 2

    blocked = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(near), "surface": "SHORTLIST"},
        headers=world.auth(searcher["token"]),
    )
    assert blocked.status_code == 204, blocked.text

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    body = read.json()
    assert len(body["candidates"]) == 2, "the list got quietly shorter"
    withheld = [row for row in body["candidates"] if row.get("withheld")]
    assert len(withheld) == 1
    assert withheld[0] == {"withheld": True}, "a withheld row carries a person"
    assert str(near) not in read.text
    assert "near" not in read.text


async def test_a_withheld_row_names_no_gate_and_no_reason(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0095``: *neither party is ever notified, and the other side
    sees no trace anywhere in any response.*

    That rule does not weaken because the surface has a longer memory. Naming the
    gate would tell a searcher that this particular person blocked them, was
    suspended, or changed a safety setting — so the four causes are
    indistinguishable and the word *block* does not appear at all.
    """

    posted, near, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    await client.post(
        "/api/v1/blocks",
        json={"player_id": str(near), "surface": "SHORTLIST"},
        headers=world.auth(searcher["token"]),
    )

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    assert "block" not in read.text.lower()
    for gate in ("HELD_ACCOUNT", "ACCOUNT_INACTIVE", "GENDER_PREFERENCE", "BLOCKED"):
        assert gate not in read.text


async def test_re_verifying_changes_nothing_stored(
    client, session_factory, candidate_source, searcher
):
    """**The record is immutable.** Re-verification is a read, and a read-back
    that quietly repaired the row it read would destroy the one denominator this
    engine is judged by."""

    posted, near, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    search_id = posted["search"]["search_id"]
    before = await world.recorded_candidates(session_factory, search_id)
    kept = [(row.band, row.position, row.player_id, row.fit) for row in before]

    await client.post(
        "/api/v1/blocks",
        json={"player_id": str(near), "surface": "SHORTLIST"},
        headers=world.auth(searcher["token"]),
    )
    await world.read_back(client, searcher["token"], search_id)

    after = await world.recorded_candidates(session_factory, search_id)
    assert [
        (row.band, row.position, row.player_id, row.fit) for row in after
    ] == kept
    searches = await world.recorded_searches(session_factory)
    assert len(searches) == 1, "a read-back is not a search"


async def test_a_candidate_who_narrowed_their_preference_is_withheld(
    client, session_factory, candidate_source, searcher
):
    """The mutual gender gate is re-evaluated, and it still fails **closed**.

    The searcher is a woman; the candidate narrows to men only after the search
    ran. Nothing about that reaches the response except that the row is gone —
    a safety setting is its owner's, and revealing it here would publish it to
    exactly the person it was set against (``docs/adr/0096``).
    """

    posted, near, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    await world.append(
        session_factory, GenderPreferenceChanged(near, "MEN_ONLY", LATER)
    )
    await world.fold_the_log(session_factory, candidate_source)

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    body = read.json()
    assert len(body["candidates"]) == 2
    assert [row.get("withheld") for row in body["candidates"]].count(True) == 1
    assert str(near) not in read.text


async def test_a_candidate_the_index_no_longer_holds_cannot_be_verified_so_is_withheld(
    client, session_factory, candidate_source, searcher
):
    """*A gate that cannot be evaluated excludes*, on a read-back too.

    The mutual preference is the one fail-closed gate whose other half lives on
    the index row. A candidate the index no longer holds has no preference to
    read, so there is no way to say the gate passes — and *we could not find out*
    may never be served as *nobody is excluded*.
    """

    from app.modules.matchmaking.presentation.dependencies import get_candidate_source

    posted, _, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    empty = world.an_empty_index(candidate_source)
    world.override(client, get_candidate_source, lambda: empty)

    body = (
        await world.read_back(
            client, searcher["token"], posted["search"]["search_id"]
        )
    ).json()

    assert [row.get("withheld") for row in body["candidates"]] == [True, True]


async def test_a_sort_that_would_now_reorder_nothing_is_no_longer_drawn(
    client, session_factory, candidate_source, searcher
):
    """Offerability is about **the rows in the reader's hand**, and after a
    withholding those are different rows.

    Two candidates at two distances make *Closest* honest; withhold one and
    there is nothing left for it to reorder, so the control is not drawn — a
    visible control that does nothing is the product lying quietly.
    """

    # The better level match is the further one, so the returned order and the
    # distance order genuinely disagree — which is what makes *Closest* honest
    # here rather than a control that reshuffles by player id.
    nearer = await world.a_candidate(
        client, session_factory, "nearer", mu=searcher["mu"] + 0.3
    )
    await world.a_candidate(
        client, session_factory, "further", mu=searcher["mu"], latitude=51.55
    )
    await world.fold_the_log(session_factory, candidate_source)
    posted = (await world.search(client, searcher["token"])).json()
    assert "CLOSEST" in posted["search"]["sorts_available"]

    await client.post(
        "/api/v1/blocks",
        json={"player_id": str(nearer), "surface": "SHORTLIST"},
        headers=world.auth(searcher["token"]),
    )
    body = (
        await world.read_back(
            client, searcher["token"], posted["search"]["search_id"]
        )
    ).json()

    assert body["search"]["sorts_available"] == []


async def test_an_empty_shortlist_reads_back_as_an_empty_shortlist(
    client, session_factory, candidate_source, searcher
):
    """The honest empty state is an answer, and a read-back must not turn a
    search that returned nobody into a search that never happened."""

    await world.fold_the_log(session_factory, candidate_source)
    posted = (await world.search(client, searcher["token"])).json()

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    assert read.status_code == 200, read.text
    assert read.json()["candidates"] == []
    assert read.json()["search"]["pool"]["players_in_range"] == 0


async def test_a_searcher_may_read_their_own_search_and_nobody_elses(
    client, session_factory, candidate_source, searcher
):
    """A stranger's ``search_id`` answers exactly as an unknown one does.

    An answer that separated them would be a directory of other people's
    searches, read one probe at a time.
    """

    posted, _, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    stranger = await world.a_searcher(client, name="stranger")

    theirs = await world.read_back(
        client, stranger["token"], posted["search"]["search_id"]
    )
    unknown = await world.read_back(client, stranger["token"], str(uuid4()))

    assert theirs.status_code == 404, theirs.text
    assert theirs.json()["code"] == "search_not_found"
    assert unknown.status_code == 404, unknown.text
    # Everything but the trace id, which is per request by design and is the one
    # field that must differ between two calls.
    assert {
        key: value for key, value in theirs.json().items() if key != "trace_id"
    } == {
        key: value for key, value in unknown.json().items() if key != "trace_id"
    }, "a stranger's search is distinguishable from one that never existed"


async def test_the_route_requires_a_token(client):
    response = await client.get(f"/api/v1/searches/{uuid4()}")
    assert response.status_code == 401


async def test_a_block_set_that_cannot_be_read_refuses_rather_than_serving(
    client, session_factory, candidate_source, searcher
):
    """**The read-back fails closed too.** A search that cannot be re-verified is
    a `503`, not a degraded render — serving the stored rows while the gate is
    unreadable is exactly the cache the gate exists to refuse."""

    from app.modules.blocks.domain.errors import BlockStateUnavailable
    from app.modules.blocks.presentation.dependencies import get_block_query

    class Unreachable:
        async def exclusions_for(self, player_id):
            raise BlockStateUnavailable("the block store is unreachable")

        async def blocked_between(self, first, second):
            raise BlockStateUnavailable("the block store is unreachable")

    posted, _, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    world.override(client, get_block_query, Unreachable)

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    assert read.status_code == 503, read.text
    assert read.json()["code"] == "gate_data_unavailable"


async def test_a_held_reader_is_refused_their_own_old_answers(
    client, session_factory, candidate_source, searcher
):
    """**The hold points both ways, and it points at old answers too.**

    A held player can still sign in, so refusing them a fresh search while
    handing back this morning's would be the hold ending at the one route that
    remembers.
    """

    posted, _, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    world.hold_everybody(client)

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    assert read.status_code == 403, read.text
    assert read.json()["code"] == "account_held"


async def test_a_candidate_under_a_hold_is_withheld_and_nothing_says_why(
    client, session_factory, candidate_source, searcher
):
    """A hold is a moderation fact about somebody else. The row goes; the reason
    stays inside the building."""

    posted, near, far = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    world.hold_only(client, near)

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    body = read.json()
    assert [row.get("withheld") for row in body["candidates"]].count(True) == 1
    assert str(near) not in read.text
    assert "hold" not in read.text.lower()


async def test_a_candidate_users_may_no_longer_show_is_withheld(
    client, session_factory, candidate_source, searcher
):
    """Account state is live, candidate-side and told to nobody — on this route
    exactly as on the search that produced the row."""

    posted, near, _ = await a_search_of_two(
        client, session_factory, candidate_source, searcher
    )
    world.may_not_show(client, near)

    body = (
        await world.read_back(
            client, searcher["token"], posted["search"]["search_id"]
        )
    ).json()

    assert [row.get("withheld") for row in body["candidates"]].count(True) == 1


async def test_the_read_back_is_on_the_emitted_player_surface():
    """The contract the client generates from is the one this route is on — and
    it is a `GET`, on its own path, beside the `POST` that creates a search."""

    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    spec = build_surface_spec("Raketa Player API", player_api_router)

    assert set(spec["paths"]["/api/v1/searches/{search_id}"]) == {"get"}
    assert set(spec["paths"]["/api/v1/searches"]) == {"post"}


async def test_both_routes_answer_in_the_same_schema():
    """*Not a fuller one, not a slimmer one — the same.* Asserted on the emitted
    document, because two routes drift by growing one field at a time."""

    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    spec = build_surface_spec("Raketa Player API", player_api_router)
    paths = spec["paths"]

    def ok(operation: dict) -> dict:
        return operation["responses"]["200"]["content"]["application/json"]["schema"]

    assert ok(paths["/api/v1/searches"]["post"]) == ok(
        paths["/api/v1/searches/{search_id}"]["get"]
    )


def test_the_moment_the_fixtures_change_a_preference_at_is_after_the_commit():
    """The guard on the fixture: a change stamped before the profile it edits
    would be applied as history and assert nothing."""

    assert LATER > world.LONG_AGO
    assert LATER < datetime.now(timezone.utc)


async def test_the_link_is_minted_again_rather_than_read_off_the_row(
    client, session_factory, candidate_source, photo_storage, searcher
):
    """**A month-old link would be a dead one, so the record never held it.**

    The photo *id* is a recorded fact and comes back unchanged; the address for
    it is signed again, here, for this reader and this window. That is the one
    difference ``docs/adr/0107`` allows the round trip — and it is what lets the
    row be kept for ever without keeping a link that died within the hour.
    """

    photo = uuid4()
    await world.a_candidate(
        client, session_factory, "photographed", mu=searcher["mu"], photo_ids=(photo,)
    )
    await world.fold_the_log(session_factory, candidate_source)
    posted = (await world.search(client, searcher["token"])).json()
    signed_on_the_post = len(photo_storage.signed_windows)

    body = (
        await world.read_back(
            client, searcher["token"], posted["search"]["search_id"]
        )
    ).json()

    card = body["candidates"][0]["player_card"]
    assert card["photo_id"] == str(photo)
    assert card["photo_url"], "a read-back handed back an id with no address"
    assert len(photo_storage.signed_windows) == signed_on_the_post + 1, (
        "the read-back served a link it had not signed"
    )


async def test_a_withheld_rows_photograph_is_signed_for_nobody(
    client, session_factory, candidate_source, photo_storage, searcher
):
    """A withheld row carries no person, so nothing is minted on their behalf.

    The link never reaches the wire either way — the row is rendered as the bare
    withholding — but an address signed for somebody this answer has just agreed
    to stop showing is a credential that should not have been created at all.
    """

    photo = uuid4()
    blocked_player = await world.a_candidate(
        client, session_factory, "photographed", mu=searcher["mu"], photo_ids=(photo,)
    )
    await world.fold_the_log(session_factory, candidate_source)
    posted = (await world.search(client, searcher["token"])).json()
    assert posted["candidates"][0]["player_card"]["photo_url"]
    signed_on_the_post = len(photo_storage.signed_windows)

    blocked = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked_player), "surface": "SHORTLIST"},
        headers=world.auth(searcher["token"]),
    )
    assert blocked.status_code == 204, blocked.text

    read = await world.read_back(
        client, searcher["token"], posted["search"]["search_id"]
    )

    assert read.json()["candidates"] == [{"withheld": True}]
    assert len(photo_storage.signed_windows) == signed_on_the_post, (
        "a withheld row's photograph was signed"
    )
