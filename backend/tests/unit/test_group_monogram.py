"""The monogram's letters, cut where a reader sees characters.

``docs/adr/0183`` §5 moved the cut to the backend because three clients would
drift three ways — *in a digit, an emoji, a leading space or a one-letter word*.
The ordinary names are asserted over HTTP in ``tests/api/test_groups.py``; this
file holds the names a phone keyboard makes, where a cut by code point would
draw half a character.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.modules.groups.domain.monogram import MONOGRAM_COLOURS, colour_of, letters_of
from app.modules.groups.domain.value_objects import GroupName

FAMILY = "\U0001f468‍\U0001f469‍\U0001f467"  # man ZWJ woman ZWJ girl
POLAND = "\U0001f1f5\U0001f1f1"  # two regional indicators, one flag
WAVE_DARK = "\U0001f44b\U0001f3ff"  # a hand and its skin tone
TENNIS_VS16 = "\U0001f3be️"  # a ball and its emoji presentation
E_ACUTE_DECOMPOSED = "é"  # e and a combining acute


@pytest.mark.parametrize(
    ("name", "letters"),
    [
        ("my rakieta group", "mr"),
        ("Ogrody 33 Club", "O3"),
        ("  padel   kraków ", "pk"),
        ("Padel", "Pa"),
        ("X", "X"),
        ("x y", "xy"),
        (f"{TENNIS_VS16} Club", f"{TENNIS_VS16}C"),
        (f"{FAMILY} padel", f"{FAMILY}p"),
        (f"{POLAND}{POLAND}", f"{POLAND}{POLAND}"),
        (f"{POLAND} squash", f"{POLAND}s"),
        (f"{WAVE_DARK}hej", f"{WAVE_DARK}h"),
        (f"{E_ACUTE_DECOMPOSED}lan vital", f"{E_ACUTE_DECOMPOSED}v"),
        (f"{E_ACUTE_DECOMPOSED}{E_ACUTE_DECOMPOSED}", E_ACUTE_DECOMPOSED * 2),
    ],
)
def test_the_letters_are_whole_characters_as_typed(name, letters):
    assert letters_of(GroupName(name)) == letters


def test_the_colour_is_the_same_for_one_id_every_time():
    group_id = UUID("6f1d2c3b-4a5e-4f60-8a7b-9c0d1e2f3a4b")

    assert colour_of(group_id) == colour_of(UUID(str(group_id)))
    assert 0 <= colour_of(group_id) < MONOGRAM_COLOURS


def test_the_colours_are_spread_across_every_key():
    seen = {colour_of(UUID(int=n * 7919)) for n in range(1, 400)}

    assert seen == set(range(MONOGRAM_COLOURS))
