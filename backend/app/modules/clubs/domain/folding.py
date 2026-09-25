"""The fold search matches on: lower case, accents stripped (``docs/adr/0182`` §2).

A player types the way they type in WhatsApp — *debniki*, not *Dębniki* — and
finds the club anyway. The search projection keeps a folded copy of a club's
name and district, and a query is folded **by this same function**, so the two
sides of a match cannot disagree about what a letter is.

**Decomposition is not enough for Polish, and the table below is the rest.**
Unicode decomposes *ę* into *e* and a combining ogonek, and dropping the mark
leaves the letter. *Ł* is not a decorated *L* to Unicode — it is its own letter
and decomposes to nothing — so a fold built on decomposition alone would never
find *Błonia* from *blonia*, and nothing would say so: the search would answer
*no club called "blonia"*. ADR-0182 names the one mapping Polish needs; the
table holds it, and a letter found missing later is a row here.
"""

from __future__ import annotations

import unicodedata
from typing import Final

#: Letters Unicode does not decompose into a base letter and a mark, spelled
#: after case folding (so only the lower-case form is needed).
_UNDECOMPOSED: Final = str.maketrans({"ł": "l"})


def fold(text: str) -> str:
    """``text`` as search compares it: case-folded, marks dropped, ``ł`` → ``l``.

    Nothing else changes — spaces, digits and punctuation are kept as typed,
    because *matched anywhere in the field* is a substring test and a fold that
    also rewrote the gaps between words would make ``"ogrody 33"`` and
    ``"ogrody33"`` a question about spacing.
    """

    decomposed = unicodedata.normalize("NFKD", text.casefold())
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return stripped.translate(_UNDECOMPOSED)
