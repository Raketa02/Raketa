"""What a game's details say about it, by kind — the pure rules (#833;
``docs/adr/0207`` §6).

**For fun**: the table's Social vibe — the card's own number — and a row for
each tag **the reader** holds, in the vocabulary's order, 💘 too, each carried
by the reader and then by whoever else at the table holds it, in the order the
table is handed over. **Competitive**: what is at stake is priced only while
the game is still the reader's to play, and once every seat is named.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.kernel import InvariantViolated
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.proposals.domain.deck import Sides
from app.modules.proposals.domain.details import ReaderAction, stakes_are_priced
from app.modules.proposals.domain.vibe import (
    VibeRow,
    social_vibe_of,
    table_vibe_of,
)

ME, KUBA, EWA, TOMEK = (uuid4() for _ in range(4))

DRINK = SocialTag.STAYS_FOR_A_DRINK
LAUGHS = SocialTag.LAUGHS_OFF_MISTAKES
SOMEONE = SocialTag.OPEN_TO_MEET_SOMEONE
NEW_IN_TOWN = SocialTag.NEW_IN_TOWN
QUIET = SocialTag.QUIET_AND_FOCUSED


def test_the_rows_are_the_reader_s_tags_in_the_vocabulary_s_order():
    tags = {
        ME: frozenset({NEW_IN_TOWN, SOMEONE, LAUGHS, DRINK}),
        KUBA: frozenset({DRINK, SOMEONE, QUIET}),
        EWA: frozenset({LAUGHS}),
    }

    vibe = table_vibe_of(ME, (KUBA, ME, EWA), tags)

    assert vibe is not None
    assert vibe.rows == (
        VibeRow(tag=DRINK, carried_by=(ME, KUBA)),
        VibeRow(tag=LAUGHS, carried_by=(ME, EWA)),
        VibeRow(tag=SOMEONE, carried_by=(ME, KUBA)),
        VibeRow(tag=NEW_IN_TOWN, carried_by=(ME,)),
    )


def test_the_number_is_the_card_s_whatever_order_the_table_comes_in():
    tags = {
        ME: frozenset({DRINK, LAUGHS, SOMEONE}),
        KUBA: frozenset({DRINK, SOMEONE}),
        EWA: frozenset({QUIET, LAUGHS}),
        TOMEK: frozenset({QUIET, NEW_IN_TOWN}),
    }

    vibe = table_vibe_of(ME, (ME, TOMEK, EWA, KUBA), tags)

    assert vibe is not None
    assert vibe.pct == social_vibe_of((KUBA, EWA, ME, TOMEK), tags)


def test_no_grid_where_the_card_draws_no_vibe():
    """Alone at the table, or nobody there holding a tag that counts."""

    assert table_vibe_of(ME, (ME,), {ME: frozenset({DRINK, LAUGHS})}) is None
    assert (
        table_vibe_of(ME, (ME, KUBA), {ME: frozenset({SOMEONE}), KUBA: frozenset()})
        is None
    )


def test_a_reader_whose_tags_are_not_known_reads_no_rows():
    vibe = table_vibe_of(ME, (ME, KUBA, EWA), {KUBA: frozenset({DRINK}), EWA: {DRINK}})

    assert vibe is not None and vibe.rows == ()


def test_a_grid_is_never_drawn_for_somebody_not_at_the_table():
    with pytest.raises(InvariantViolated):
        table_vibe_of(ME, (KUBA, EWA), {KUBA: frozenset({DRINK})})


FOUR = Sides(yours=(ME, KUBA), theirs=(EWA, TOMEK))
TO_ANSWER = (ReaderAction.YES, ReaderAction.NO)


@pytest.mark.parametrize(
    ("sides", "seats_per_side", "named"),
    [
        (FOUR, 2, True),
        (Sides(yours=(ME,), theirs=(KUBA,)), 1, True),
        (Sides(yours=(ME, KUBA), theirs=(EWA,)), 2, False),
        (Sides(yours=(ME,), theirs=(KUBA,)), 2, False),
    ],
)
def test_stakes_are_priced_only_once_every_seat_is_named(sides, seats_per_side, named):
    priced = stakes_are_priced(sides, seats_per_side=seats_per_side, actions=TO_ANSWER)

    assert priced is named


@pytest.mark.parametrize(
    ("actions", "priced"),
    [
        (TO_ANSWER, True),
        ((ReaderAction.WITHDRAW,), True),
        ((ReaderAction.CONFIRM_PAYMENT, ReaderAction.LEAVE), True),
        ((ReaderAction.CONFIRM_PAYMENT,), True),
        # A no, no longer fitting, a paused yes, a game over or booked.
        ((), False),
    ],
)
def test_stakes_are_priced_only_on_a_game_still_the_reader_s_to_play(actions, priced):
    assert stakes_are_priced(FOUR, seats_per_side=2, actions=actions) is priced
