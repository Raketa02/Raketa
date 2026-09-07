"""Where one invited seat came from. **Two answers, and never a third.**

**Per seat, never per challenge** (#221). A doubles send draws three invitees
from *one* search at *three* positions, so a challenge-level origin would keep
the search and lose every position — and the position is what
``docs/specs/matchmaking/search-telemetry.md`` §19.2 joins on. There is no
default: a seat that cannot say where it came from cannot be constructed at all,
which is the executable form of *never an optional field*.

**These types are this context's own, and are deliberately a second spelling of
``matchmaking.domain.ports.SentFromSearch`` / ``SentOutsideASearch``.** That pair
is the *reader's* shape — what the matcher is handed back about a challenge it
did not write — and this pair is the *writer's*. ``challenges`` may not import
``matchmaking``, so the alternative to two spellings is the matcher owning the
vocabulary of the context that was built to take it off him. The adapter that
signs the matcher's port is where the two meet, and it is one mapping in one
file.

**A code, never a nested structure.** The event codec coerces scalars only, so a
seat crosses into storage as one string (``seats.py``) and the origin is one
field inside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import invariant

#: What separates a search id from the position inside an origin code. Not a
#: colon: an instant is a neighbouring field in the same seat code and is full of
#: them.
_AT = "@"

#: The whole of ``SentOutsideASearch`` on the wire. A word rather than an empty
#: string, because the empty string already means *this seat was never invited*
#: and the two must not collapse.
_OUTSIDE = "OUTSIDE"


@final
@dataclass(frozen=True, slots=True)
class SentFromSearch:
    """The invitation came from a search, at a known position in it.

    ``position`` resolves against the returned band, so a position below one is
    not a position — the same refusal ``matchmaking``'s ``OriginKey`` makes about
    the same number.
    """

    search_id: UUID
    position: int

    def __post_init__(self) -> None:
        invariant(
            self.position >= 1,
            f"an origin position below one: {self.position}",
        )

    @property
    def code(self) -> str:
        return f"{self.search_id}{_AT}{self.position}"


@final
@dataclass(frozen=True, slots=True)
class SentOutsideASearch:
    """The invitation came from somewhere else, said explicitly.

    Carries nothing: it is a **claim**, not a description. What *somewhere else*
    turns out to contain — a profile visit, a club page, a rematch — is another
    context's vocabulary to name, and inventing a taxonomy for it here would be
    this context taking an opinion about somebody else's states.
    """

    @property
    def code(self) -> str:
        return _OUTSIDE


#: Where an invitation came from. **Two answers, and never a third.**
ChallengeOrigin = SentFromSearch | SentOutsideASearch


def origin_from_code(code: str) -> ChallengeOrigin:
    """The origin a stored code names.

    Raises through ``invariant`` rather than returning a refusal, because this
    reads *history*: a code this cannot parse is a corrupt stream or a codec that
    changed under it, and neither is a state a caller can recover from by asking
    anybody again.
    """

    if code == _OUTSIDE:
        return SentOutsideASearch()
    search_id, separator, position = code.partition(_AT)
    invariant(separator == _AT, f"challenge origin code: {code!r}")
    invariant(position.isdigit(), f"challenge origin code: {code!r}")
    return SentFromSearch(search_id=UUID(search_id), position=int(position))
