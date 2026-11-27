"""**A friends game invitation is new in Needs your answer** — over HTTP, with
the fake provider (#815; ``docs/adr/0205`` §3).

The friends card's own world (``test_friends_card.py``): **Tomek** sends
Saturday 10:00 at **Ogrody 33** to **Ewa**, **Magda** and **Ania**, his
friends. Each invitation arrives when its seat was invited into — the send —
and nothing that happens to the game afterwards moves it.
"""

from __future__ import annotations

from datetime import timedelta

from tests.api import test_friends_card as the_friends_card
from tests.api.test_friends_games import a_friends_game, accepts, declines
from tests.api.test_needs_your_answer import closes_the_sheet, home_of, new_for

#: The friends card's own world and clock, as its module builds them.
clock = the_friends_card.clock
world = the_friends_card.world


async def test_each_friend_invited_has_one_new_item(client, world, clock):
    assert await new_for(client, world.ewa) == 0

    await a_friends_game(client, world)

    for friend in (world.ewa, world.magda, world.ania):
        home = await home_of(client, friend)
        assert len(home["friends_games"]) == 1
        assert home["needs_your_answer"]["new_count"] == 1
        # Its arrival is the send: the clock stands still in this world.
        assert home["needs_your_answer"]["watermark"] is not None
    # The sender is invited to nothing.
    assert await new_for(client, world.tomek) == 0


async def test_another_friends_answer_never_makes_a_seen_invitation_new(
    client, world, clock
):
    """Ewa saw the invitation; Magda's accept changes the game, not Ewa's
    seat, so nothing is new for her."""

    booking = await a_friends_game(client, world)
    seen = (await home_of(client, world.ewa))["needs_your_answer"]["watermark"]
    await closes_the_sheet(client, world.ewa, seen)
    clock.move(timedelta(hours=1))

    accepted = await accepts(client, world.magda, booking)

    assert accepted.status_code == 200, accepted.text
    home = await home_of(client, world.ewa)
    assert len(home["friends_games"]) == 1
    assert home["needs_your_answer"] == {"new_count": 0, "watermark": seen}


async def test_not_this_time_drops_the_invitation_from_the_count(client, world, clock):
    booking = await a_friends_game(client, world)

    declined = await declines(client, world.ewa, booking)

    assert declined.status_code == 204, declined.text
    assert (await home_of(client, world.ewa))["needs_your_answer"] == {
        "new_count": 0,
        "watermark": None,
    }


async def test_accepting_drops_the_invitation_from_the_count(client, world, clock):
    booking = await a_friends_game(client, world)

    accepted = await accepts(client, world.ewa, booking)

    assert accepted.status_code == 200, accepted.text
    home = await home_of(client, world.ewa)
    assert home["friends_games"] == []
    assert home["needs_your_answer"]["new_count"] == 0
