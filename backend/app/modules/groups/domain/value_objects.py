"""What a group is called, who may join it, and the code its link carries.

Each value object normalises what it is given and refuses what it cannot hold.
The name is typed by a person into a form and is refused with the field-level
error the form is shown; the code is minted by the platform, so a code that
breaks its rule is a broken caller and raises through ``invariant()``.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.kernel import Sport, invariant
from app.modules.groups.domain.errors import (
    GroupNameInvalid,
    GroupSportsRequired,
    SportNotOfferedByClub,
    WhatsAppSizeInvalid,
)

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


class GroupKind(StrEnum):
    """The two kinds of Group (``docs/adr/0183`` §1), and every rule that differs
    between them says which it binds rather than reading a null.

    A **player group** has an Owner who created it and plays whatever its
    members are rated in. An **official group** belongs to a club, has **no
    Owner** — one Administrator runs it — and **declares** its sports and the
    size of the WhatsApp group it mirrors (§3).
    """

    PLAYER = "PLAYER"
    OFFICIAL = "OFFICIAL"


#: A WhatsApp group size, whole and from two to 1024 (``docs/adr/0183`` §3):
#: two because a WhatsApp group of one is nobody's crowd, 1024 because that is
#: as many as WhatsApp lets into one group.
WHATSAPP_SIZE_SMALLEST: Final = 2
WHATSAPP_SIZE_LARGEST: Final = 1024


@dataclass(frozen=True, slots=True)
class WhatsAppSize:
    """How many people the WhatsApp group an official group mirrors has. **It
    limits nothing**: it is the denominator of the club's *From WhatsApp*
    figure, and a group may pass it (``docs/adr/0183`` §3).

    A whole number and nothing that merely equals one — ``True`` is not a size
    and neither is ``48.0`` — because a count a form sent as anything else is a
    form that sent the wrong thing.
    """

    value: int

    def __post_init__(self) -> None:
        if (
            type(self.value) is not int
            or not WHATSAPP_SIZE_SMALLEST <= self.value <= WHATSAPP_SIZE_LARGEST
        ):
            raise WhatsAppSizeInvalid()

    def percent_arrived(self, players: int) -> int:
        """The club's *From WhatsApp* figure: how much of the WhatsApp group is
        in the group, as a whole percent **rounded half up** — *11 of 48* is
        23, *1 of 8* is 13 — and **never capped**: *52 of 48* is 108, because
        the club sees the real figure (``docs/adr/0183`` §3). Whole-number
        arithmetic, so no float decides which side of a half a figure lands."""

        return (200 * players + self.value) // (2 * self.value)


@dataclass(frozen=True, slots=True)
class DeclaredSports:
    """What an official group plays, **as its Administrator declared it**: a
    non-empty subset of its club's sports (``docs/adr/0183`` §3), and its sport
    dots (§6). Held as a set — ticking a sport twice is ticking it — and read
    out in the registry's order, as a club's offered sports are.
    """

    sports: frozenset[Sport]

    def __post_init__(self) -> None:
        if not self.sports:
            raise GroupSportsRequired()

    @classmethod
    def of(cls, sports: Iterable[Sport]) -> "DeclaredSports":
        return cls(frozenset(Sport(sport) for sport in sports))

    @classmethod
    def at_club(
        cls, sports: Iterable[Sport], *, offered: Collection[Sport]
    ) -> "DeclaredSports":
        """The sports ticked, refused unless **every one is the club's** — the
        first that is not named in the registry's order, so the refusal is the
        same whichever order they were ticked in. An empty tick is *required*
        before it is anything else."""

        declared = cls.of(sports)
        for sport in declared.in_registry_order():
            if sport not in offered:
                raise SportNotOfferedByClub(sport.value)
        return declared

    @classmethod
    def from_codes(cls, codes: Iterable[str]) -> "DeclaredSports":
        """As an event and the projection spell them: registry codes."""

        return cls.of(Sport(code) for code in codes)

    def in_registry_order(self) -> tuple[Sport, ...]:
        return tuple(sport for sport in Sport if sport in self.sports)

    def codes(self) -> tuple[str, ...]:
        """Registry codes, in the registry's order — how an event and the
        projection hold them."""

        return tuple(sport.value for sport in self.in_registry_order())


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
