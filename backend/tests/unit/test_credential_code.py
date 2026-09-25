"""The 8-character code: readable, typed forgivingly, and recomputed from its link.

``docs/adr/0184`` §3 and ``docs/adr/0186`` §3: a code is read off an email and
typed elsewhere, and the public invitation page shows the code to whoever holds
the link — which, with both stored only as hashes, is possible only because the
code is a function of the token.
"""

from __future__ import annotations

import pytest

from app.modules.auth.domain.credential_code import (
    CODE_ALPHABET,
    CODE_LENGTH,
    TypedCode,
    code_for,
)


def test_the_alphabet_has_no_look_alikes() -> None:
    for look_alike in "01OIL":
        assert look_alike not in CODE_ALPHABET
    assert len(set(CODE_ALPHABET)) == len(CODE_ALPHABET) == 31


def test_a_code_is_eight_characters_of_that_alphabet() -> None:
    code = code_for("a-link-token")

    assert len(code) == CODE_LENGTH == 8
    assert set(code) <= set(CODE_ALPHABET)


def test_the_link_recomputes_its_code_and_another_link_does_not() -> None:
    assert code_for("a-link-token") == code_for("a-link-token")
    assert code_for("a-link-token") != code_for("another-link-token")


def test_codes_spread_over_the_whole_alphabet() -> None:
    """A derivation that reached only part of the alphabet would be a shorter
    code than it looks, and five tries would buy a guesser more."""

    seen = set("".join(code_for(f"token-{n}") for n in range(500)))

    assert seen == set(CODE_ALPHABET)


@pytest.mark.parametrize(
    "typed", ["K7M4QX2P", "k7m4qx2p", " K7M4 QX2P ", "K7M4-QX2P", "k7m4\tqx2p"]
)
def test_a_typed_code_is_read_the_way_it_was_written(typed: str) -> None:
    assert TypedCode(typed).value == "K7M4QX2P"
