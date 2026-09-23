"""A fact edited on the You tab, and everything that reads it follows.

``docs/adr/0179`` §8, end to end: Tomek changes his tags, rewrites his intro
and switches his preference to *Women only*; his card reads the new tags and the
new line on the next deal anybody runs, and Marek — who searched for anybody —
no longer finds him. Every write here is the tab's own route, and every read is
a search or a deal by somebody else, so what is asserted is the projection
following the aggregate rather than the aggregate alone.

**The two directions of a narrowed preference live in two places**, which is
the reason the preference gets its own test. The *searcher's* own preference is
read live off the aggregate at request time, so Tomek's next search stops
finding Marek the instant the write commits. Everybody *else* reads Tomek off
the candidate index, which tails the log — so Marek stops finding Tomek only
once the projection has followed, and the fold is run in-process here exactly
as ``matchmaking_world`` runs it for every other test.

**Why the reads before an edit are shortlists and not deals.** A deal remembers
whom it dealt for a day (``docs/adr/0131``), so a searcher who had already been
dealt Tomek would be shown him again by nothing — and a deal after the edit
would pass for the wrong reason. The shortlist has no dealt memory, so a card
is compared before and after through it, and the deal after an edit is the
first one that searcher makes.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.modules.player_profile.domain.photos import PhotoRef
from tests.api import matchmaking_world as world

TAGS_URL = "/api/v1/players/me/social-tags"
PHOTOS_URL = "/api/v1/players/me/photos"
INTRO_URL = "/api/v1/players/me/intro"
PREFERENCE_URL = "/api/v1/players/me/gender-preference"


def a_photo_held(photo_storage, owner: UUID) -> UUID:
    """One photograph already in the store under this player."""

    photo_id = uuid4()
    photo_storage.already_holding(PhotoRef(owner_id=owner, photo_id=photo_id), {})
    return photo_id


def cards_on(response) -> dict[str, dict]:
    assert response.status_code == 200, response.text
    return {
        row["player_id"]: row["player_card"] for row in response.json()["candidates"]
    }


async def test_a_deal_after_the_tag_change_reads_the_new_tags(
    client, session_factory, candidate_source
):
    tomek = await world.a_searcher(client, "tomek")
    marek = await world.a_searcher(client, "marek")
    await world.fold_the_log(session_factory, candidate_source)
    before = cards_on(await world.search(client, marek["token"]))
    assert set(before[str(tomek["id"])]["social_tags"]) == set(world.COMPETITIVE_TAGS)

    changed = await client.put(
        TAGS_URL,
        json={"social_tags": ["PLAYS_TO_WIN", "QUIET_AND_FOCUSED"]},
        headers=world.auth(tomek["token"]),
    )
    assert changed.status_code == 200, changed.text
    await world.fold_the_log(session_factory, candidate_source)

    dealt = cards_on(await world.deck(client, marek["token"]))
    assert set(dealt[str(tomek["id"])]["social_tags"]) == {
        "PLAYS_TO_WIN",
        "QUIET_AND_FOCUSED",
    }


async def test_a_promoted_photograph_is_the_face_on_the_next_card(
    client, session_factory, candidate_source, photo_storage
):
    """The face is the first photograph, and the card reads the profile's
    order live (``docs/adr/0107``) — so the deal after Tomek promotes his
    second photograph draws it, with nothing folded in between."""

    tomek_id, tomek_token = await world.register(client, "tomek")
    first, second = (
        a_photo_held(photo_storage, tomek_id),
        a_photo_held(photo_storage, tomek_id),
    )
    await world.commit_profile(client, tomek_token, photo_ids=[str(first), str(second)])
    await world.rate(client, tomek_token)
    await world.declare_intent(client, tomek_token)
    marek = await world.a_searcher(client, "marek")
    await world.fold_the_log(session_factory, candidate_source)
    before = cards_on(await world.search(client, marek["token"]))
    assert before[str(tomek_id)]["photo_id"] == str(first)

    promoted = await client.put(
        PHOTOS_URL,
        json={"photo_ids": [str(second), str(first)]},
        headers=world.auth(tomek_token),
    )
    assert promoted.status_code == 200, promoted.text

    dealt = cards_on(await world.deck(client, marek["token"]))
    assert dealt[str(tomek_id)]["photo_id"] == str(second)


async def test_a_rewritten_intro_reaches_the_card_and_a_withdrawal_clears_it(
    client, session_factory, candidate_source
):
    """The one text fact the index holds follows its edit into the same column
    (``docs/adr/0179`` §6): a rewritten line is what the next card says, and a
    withdrawn one leaves the card with **no line** — never the old one, and
    never an empty string."""

    tomek = await world.a_searcher(client, "tomek", intro="Moved from Wrocław in May.")
    marek = await world.a_searcher(client, "marek")
    await world.fold_the_log(session_factory, candidate_source)
    before = cards_on(await world.search(client, marek["token"]))
    assert before[str(tomek["id"])]["intro"] == "Moved from Wrocław in May."

    rewritten = await client.put(
        INTRO_URL,
        json={"intro": "Will travel for a hard game."},
        headers=world.auth(tomek["token"]),
    )
    assert rewritten.status_code == 204, rewritten.text
    await world.fold_the_log(session_factory, candidate_source)
    after = cards_on(await world.search(client, marek["token"]))
    assert after[str(tomek["id"])]["intro"] == "Will travel for a hard game."

    withdrawn = await client.put(
        INTRO_URL, json={"intro": None}, headers=world.auth(tomek["token"])
    )
    assert withdrawn.status_code == 204, withdrawn.text
    await world.fold_the_log(session_factory, candidate_source)
    cleared = cards_on(await world.deck(client, marek["token"]))
    assert "intro" not in cleared[str(tomek["id"])]


async def test_a_narrowed_preference_gates_the_next_search_in_both_directions(
    client, session_factory, candidate_source
):
    """Tomek, a man who had asked for anybody, switches to *Women only*. Marek
    — a man who asked for anybody — no longer finds him, because the mutual
    gate reads Tomek's index row; and Tomek no longer finds Marek, because his
    own search reads his preference live — while Ania is found by both, as
    before. Nothing about the refusal reaches Marek except that the row is
    gone (``docs/adr/0096`` §3)."""

    tomek = await world.a_searcher(client, "tomek", gender="MAN")
    marek = await world.a_searcher(client, "marek", gender="MAN")
    ania = await world.a_searcher(client, "ania", gender="WOMAN")
    await world.fold_the_log(session_factory, candidate_source)
    assert str(tomek["id"]) in cards_on(await world.search(client, marek["token"]))
    tomeks_view = cards_on(await world.search(client, tomek["token"]))
    assert {str(marek["id"]), str(ania["id"])} <= set(tomeks_view)

    narrowed = await client.put(
        PREFERENCE_URL,
        json={"gender_preference": "WOMEN_ONLY"},
        headers=world.auth(tomek["token"]),
    )
    assert narrowed.status_code == 204, narrowed.text

    # The searcher's own side follows the write at once: read live.
    tomeks_view = cards_on(await world.search(client, tomek["token"]))
    assert str(marek["id"]) not in tomeks_view
    assert str(ania["id"]) in tomeks_view

    # Everybody else's follows the projection.
    await world.fold_the_log(session_factory, candidate_source)
    mareks_view = cards_on(await world.search(client, marek["token"]))
    assert str(tomek["id"]) not in mareks_view
    assert str(ania["id"]) in mareks_view
    anias_view = cards_on(await world.search(client, ania["token"]))
    assert str(tomek["id"]) in anias_view, "a woman asking for anybody still finds him"
