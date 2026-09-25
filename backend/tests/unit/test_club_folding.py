"""What search will compare: a club's name and district, folded.

``docs/adr/0182`` §2: lower case, accents stripped, matched anywhere — and the
query folded by the same function as the stored copies. Asserted on the function
itself because no route reads the folded copies until search does (#504), and a
fold that misses a letter fails silently there, as *no club called …*.
"""

from __future__ import annotations

import pytest

from app.modules.clubs.domain.folding import fold


@pytest.mark.parametrize(
    ("typed", "folded"),
    [
        ("Dębniki", "debniki"),
        # The one Unicode will not decompose: without the table, *blonia* would
        # never find this club.
        ("Błonia", "blonia"),
        ("ŁOBZÓW", "lobzow"),
        ("Prądnik Czerwony", "pradnik czerwony"),
        ("Zabłocie Sport", "zablocie sport"),
        ("Grzegórzki", "grzegorzki"),
        ("Kraków", "krakow"),
        ("Źródło Żywe", "zrodlo zywe"),
        ("Ogrody 33 Club", "ogrody 33 club"),
    ],
)
def test_a_name_is_folded_to_what_a_player_types(typed, folded):
    assert fold(typed) == folded


def test_a_query_and_the_name_it_should_find_fold_alike():
    assert fold("debniki") in fold("Klub Dębniki Sport")
    assert fold("BLONIA") in fold("Wisła Park · Błonia")


def test_spacing_and_punctuation_are_kept_as_typed():
    assert fold("  Ogrody  33 · Kraków ") == "  ogrody  33 · krakow "
