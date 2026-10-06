"""Gender and Gender preference: two closed vocabularies, and never one.

``docs/adr/0096`` settles both. They are separate types because they are
separate facts and their value sets do not even have the same size: a player's
own answer has three values, a preference over other players has three
different ones, and a single enum doing both duty would make *I am a woman* and
*only women* the same word. That is the shape ADR-0094 gives ``SearchMode`` and
``PlayIntent`` for the same reason — two arities cannot be unified even by
somebody hunting duplication.

**Both are asked, and neither is inferred.** ``PREFER_NOT_TO_SAY`` is an
explicit answer and never a null: it is the same shape as Play intent's
``NO_PREFERENCE``, and it must never be confused with *nobody has been asked*.
A profile created before the question existed carries **no** gender at all, and
that absence is a different fact from this answer — the events module is where
that distinction is spelled out, because it is the events that carry it.

The words are plain deliberately. A euphemism would fail the matchmaking
engine's third refusal: it never produces something it cannot explain in one
sentence.

**The gate that reads these is not in this module, and must not move into
it.** ADR-0096 fences it: gender reaches candidate generation and gating, is
*absent* from the type handed to ``app/engines/matchfit/``, and no response ever
carries either value. Writing the comparison **here** would put a matching rule
in the vocabulary the scorer's own context imports, which is the one place the
fence has to hold.

It lives one file over, in ``mutual_preference.py``, and it arrived there when
the send became its third caller: ``matchmaking -> challenges`` and never back,
so a send re-verifying the gate in its own transaction cannot reach the matcher's
copy, and a second implementation of a mutual safety gate is the thing that ends
up satisfied in one place and not the other. The **reading** stayed with each
caller — an index row in a search, live profiles in a send — and only the
judgement moved.

Neither value crosses the wire outward. ``SearchContext`` will carry a
preference *in*; no response shape carries a gender value *out*, and no card
renders one (ADR-0096 §6).
"""

from __future__ import annotations

from enum import Enum
from typing import Final


class Gender(str, Enum):
    """What a player says about themselves — self-declared, freely changed.

    Per person and never per sport, which is what keeps it on ``PlayerProfile``
    rather than beside a rating (ADR-0089's cardinality, unchanged).

    This is **a statement about which games a player wishes to be put in**, not
    a ruling by the platform on who anybody is. A player whose identity is not on
    this list picks the answer that puts them where they want to be, or takes
    ``PREFER_NOT_TO_SAY`` and is paired only with players who asked for anybody.
    The platform adjudicates nothing.
    """

    WOMAN = "WOMAN"
    MAN = "MAN"
    #: Matches only an unconstrained preference and never a narrowed one. It costs
    #: its holder reach, and ADR-0096 records that the honest framing of that
    #: cost is a copy problem — the client's, never this module's.
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class GenderPreference(str, Enum):
    """Who a player is willing to be matched with — durable, never per game.

    **Durable because the gate is mutual.** It has to be evaluated against a
    player when somebody *else's* game is being made and they are not present,
    and a setting made at the moment could not bind that direction at all.
    """

    WOMEN_ONLY = "WOMEN_ONLY"
    MEN_ONLY = "MEN_ONLY"
    ANY = "ANY"


#: What a player holds who has never expressed a preference.
#:
#: The **gender** answer is required at profile creation; the preference is
#: optional and this is its default (ADR-0096 §2). It lives here as a constant
#: rather than as a literal at each call site so that the aggregate's default,
#: the event's default for rows written before the field existed, and the wire
#: schema's default are one number rather than three that can drift.
DEFAULT_GENDER_PREFERENCE: Final = GenderPreference.ANY
