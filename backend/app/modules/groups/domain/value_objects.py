"""What a group is called, who may join it, and the code its link carries.

Each value object normalises what it is given and refuses what it cannot hold.
The name is typed by a person into a form and is refused with the field-level
error the form is shown; the code is minted by the platform, so a code that
breaks its rule is a broken caller and raises through ``invariant()``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.kernel import invariant
from app.modules.groups.domain.errors import GroupNameInvalid

#: A group's name, once trimmed: at least one character and at most forty
#: (``docs/adr/0183`` §2). Forty because it matches the WhatsApp group a crowd
#: already has, and a name the group is known by must fit.
GROUP_NAME_SHORTEST: Final = 1
GROUP_NAME_LONGEST: Final = 40


def _collapsed(typed: str) -> str:
    """Text a person typed, trimmed and its runs of whitespace collapsed.

    ``split()`` with no argument splits on any run of whitespace and drops the
    ends, so the trim and the collapse are one step — the way a club's name and
    a player's Name are held.
    """

    return " ".join(typed.split())


@dataclass(frozen=True, slots=True)
class GroupName:
    """What the group is called: trimmed, runs of whitespace collapsed, then
    1–40 characters, and **never unique** — two *Padel Kraków* groups at one
    club are allowed (``docs/adr/0183`` §2).

    ``split()`` with no argument splits on any run of whitespace and drops the
    ends, so the trim and the collapse are one step and the bound is on the name
    as it is recorded.
    """

    value: str

    def __post_init__(self) -> None:
        collapsed = _collapsed(self.value)
        if not GROUP_NAME_SHORTEST <= len(collapsed) <= GROUP_NAME_LONGEST:
            raise GroupNameInvalid()
        object.__setattr__(self, "value", collapsed)


class JoinPolicy(StrEnum):
    """Who gets in (``docs/adr/0183`` §7).

    **Anyone** admits a player the moment they join, and is the default the New
    group form opens on. **People I approve** turns a join into a Join request
    its Owner answers.
    """

    ANYONE = "ANYONE"
    PEOPLE_I_APPROVE = "PEOPLE_I_APPROVE"


class GroupRelation(StrEnum):
    """What a group is to the person reading it (``docs/adr/0183`` §9): they
    are in it, they have asked and their Join request is waiting, or neither.

    **A declined request reads as ``NONE``** — the request is gone, and nothing
    tells them it was declined (``docs/adr/0183`` §7)."""

    MEMBER = "MEMBER"
    REQUESTED = "REQUESTED"
    NONE = "NONE"


#: Eight characters from an alphabet with **no look-alikes**
#: (``docs/adr/0183`` §4): no ``0`` beside ``o``, no ``1`` beside ``l`` or
#: ``i``. Lower case, because a code is read inside a link and typed from one,
#: and one case is half the characters to confuse. Thirty-one letters to the
#: eighth power is about 8.5 × 10¹¹ codes.
GROUP_CODE_ALPHABET: Final = "abcdefghjkmnpqrstuvwxyz23456789"
GROUP_CODE_LENGTH: Final = 8


@dataclass(frozen=True, slots=True)
class GroupCode:
    """The part of a group's link that is the group: unique, and **never
    changing** — not on a rename, a policy change or a handover
    (``docs/adr/0183`` §4). Every WhatsApp post of the link depends on it."""

    value: str

    def __post_init__(self) -> None:
        invariant(
            _is_a_code(self.value),
            f"a group code outside its alphabet or length: {self.value!r}",
        )

    @classmethod
    def read(cls, typed: str) -> "GroupCode | None":
        """The code in something a person pasted, or ``None`` when it could be
        no group's code. **Read lower-cased**: every code is minted lower case,
        so an app that capitalised a link cannot have made it name a different
        group. Minted codes are constructed directly and a bad one is a broken
        caller; a pasted one is only ever a guess, and this is where it is
        checked."""

        lowered = typed.lower()
        return cls(lowered) if _is_a_code(lowered) else None


def _is_a_code(text: str) -> bool:
    return len(text) == GROUP_CODE_LENGTH and all(
        char in GROUP_CODE_ALPHABET for char in text
    )


@dataclass(frozen=True, slots=True)
class SearchText:
    """What a player typed into a search field: trimmed, runs of whitespace
    collapsed — the shape a stored name and district were given, so a gap typed
    twice still finds the name it sits in.

    **A blank field is not a search**: the form says *start typing* there, and a
    list of every club in Raketa is not what an empty field asked for.
    """

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _collapsed(self.value))

    @property
    def is_blank(self) -> bool:
        return not self.value
