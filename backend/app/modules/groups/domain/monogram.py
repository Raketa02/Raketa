"""A group's monogram: two letters cut from its name, on a colour fixed by its id.

**Served by the backend, because three clients draw the tile** — the player app,
the club website and the public site (``docs/adr/0183`` §5). A rule written three
times drifts three ways: in a digit, an emoji, a leading space or a one-letter
word. So the letters are cut here, once.

It is not presentation (``docs/adr/0022``): the letters are **content cut from
content** a person typed, like the name itself, and the colour crosses as a
**key** that each client maps to its own palette — design systems are not shared
(``docs/adr/0187`` §6).
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from app.modules.groups.domain.value_objects import GroupName

#: How many colour keys there are. A client holds a palette of this many and
#: draws key ``k`` in its ``k``-th colour; the backend never names a colour.
MONOGRAM_COLOURS: Final = 8

_ZERO_WIDTH_JOINER: Final = "‍"


@dataclass(frozen=True, slots=True)
class Monogram:
    """The letters, **as typed**, and the colour key in ``[0, MONOGRAM_COLOURS)``."""

    letters: str
    colour: int


def monogram_of(group_id: UUID, name: GroupName) -> Monogram:
    return Monogram(letters=letters_of(name), colour=colour_of(group_id))


def letters_of(name: GroupName) -> str:
    """The first character of each of the first two words, or the first two
    characters of a one-word name — **as typed**, so *my raketa group* is ``mr``
    and *Ogrody 33 Club* is ``O3``.

    A *character* is what a reader sees as one: a letter with its accents, an
    emoji with its modifiers. A cut by code point would split *é* typed as ``e``
    and a combining mark, or a flag, and draw half of it.
    """

    words = name.value.split()
    if len(words) == 1:
        return "".join(_characters(words[0])[:2])
    return "".join(_characters(word)[0] for word in words[:2])


def colour_of(group_id: UUID) -> int:
    """A key derived from the group's id, so it never changes — not even on a
    rename — and is the same in every process: SHA-256 over the id's bytes and
    never the process hash, which ``docs/adr/0105`` forbids for anything two
    workers must agree on."""

    digest = hashlib.sha256(group_id.bytes).digest()
    return int.from_bytes(digest[:8], "big") % MONOGRAM_COLOURS


def _characters(word: str) -> list[str]:
    """``word`` cut into what a reader sees as characters.

    Not the whole of Unicode's grapheme rules, and deliberately so: a combining
    mark, a variation selector, a skin tone, an emoji tag and whatever follows a
    zero-width joiner stay with the character before them, and two regional
    indicators make one flag. That covers every way a name typed on a phone
    builds one visible character out of several code points.
    """

    clusters: list[str] = []
    joined = False
    for char in word:
        if clusters and (joined or _extends(char, clusters[-1])):
            clusters[-1] += char
        else:
            clusters.append(char)
        joined = char == _ZERO_WIDTH_JOINER
    return clusters


def _extends(char: str, cluster: str) -> bool:
    code = ord(char)
    if unicodedata.combining(char) or unicodedata.category(char) == "Me":
        return True
    if char == _ZERO_WIDTH_JOINER:
        return True
    if 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF:  # variation selectors
        return True
    if 0x1F3FB <= code <= 0x1F3FF:  # skin tones
        return True
    if 0xE0020 <= code <= 0xE007F:  # emoji tags
        return True
    return _is_regional_indicator(char) and _is_lone_regional_indicator(cluster)


def _is_regional_indicator(char: str) -> bool:
    return 0x1F1E6 <= ord(char) <= 0x1F1FF


def _is_lone_regional_indicator(cluster: str) -> bool:
    return len(cluster) == 1 and _is_regional_indicator(cluster)
