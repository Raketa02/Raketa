"""The Friend link — event-sourced, **one stream per player** (``docs/adr/0202``
§1; the mechanics §4.1; #748).

``<public site>/f/<code>``. **The code is random**, so nobody can guess
somebody's link from their nickname, and a rename never breaks it. **It is made
the first time its owner reads it**, and **New link** replaces it at once: the
old code then reads as not found, in the app and on the public site. **A code
is never reused** — not by its owner and not by anybody else — so a link pasted
into a chat a year ago can only ever lead to the person who shared it, or
nowhere.

**Shaped like a group's code** (``docs/adr/0183`` §4): eight characters from an
alphabet with no look-alikes, lower case. The two alphabets are spelled twice
because Friends imports no group (``.importlinter``'s
*friends-knows-none-of-its-readers*); ``tests/unit/test_friend_link_code.py``
holds them equal.

**A Friend link is not a Group link.** One joins a group; the other asks a
person. Opening one never makes friends by itself: it puts the owner's request
on the opener's Home (``application/link.py``).

**The code is in the events**, as a group's code is in its own (``groups.created``):
a link is posted to chats on purpose, so it is an address and no secret — what
it opens is a request the opener still has to accept. ADR-0184 §4's rule is
about what signs somebody in or proves an email, which this does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Iterable
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.friends.domain.events import FriendLinkMade, FriendLinkReplaced
from app.modules.friends.domain.ids import friend_link_id
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: A group code's alphabet and length (``groups/domain/value_objects.py``), held
#: equal by a test: no ``0`` beside ``o``, no ``1`` beside ``l`` or ``i``.
FRIEND_LINK_CODE_ALPHABET: Final = "abcdefghjkmnpqrstuvwxyz23456789"
FRIEND_LINK_CODE_LENGTH: Final = 8


@dataclass(frozen=True, slots=True)
class FriendLinkCode:
    """What follows ``/f/`` in a friend link."""

    value: str

    def __post_init__(self) -> None:
        invariant(
            _is_a_code(self.value),
            f"a friend link code outside its alphabet or length: {self.value!r}",
        )

    @classmethod
    def read(cls, typed: str) -> "FriendLinkCode | None":
        """The code in a link somebody opened, or ``None`` when it could be no
        link's. **Read lower-cased**, as a group's is: every code is minted lower
        case, so a link an app capitalised still names the same person. A minted
        code is constructed directly; a code from a path is only ever a guess,
        and this is where it is checked."""

        lowered = typed.lower()
        return cls(lowered) if _is_a_code(lowered) else None


def _is_a_code(text: str) -> bool:
    return len(text) == FRIEND_LINK_CODE_LENGTH and all(
        char in FRIEND_LINK_CODE_ALPHABET for char in text
    )


def friend_link_url(public_site: str, code: FriendLinkCode) -> str:
    """``<public site>/f/<code>`` — one slash between the two however the
    address was written. **The address is configuration and the shape is not**,
    as for a group's ``/join/``."""

    return f"{public_site.rstrip('/')}/f/{code.value}"


@dataclass
class FriendLink:
    """A player's link, as their stream leaves it: the code it carries now, or
    none until its owner first reads it."""

    owner_id: UUID
    code: FriendLinkCode | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def from_history(cls, owner: UUID, events: Iterable[DomainEvent]) -> "FriendLink":
        link = cls(owner_id=owner)
        for event in events:
            link._apply(event)
        return link

    @property
    def id(self) -> UUID:
        return friend_link_id(self.owner_id)

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def make(self, *, code: FriendLinkCode, at: Instant) -> FriendLinkCode:
        """The code the link carries — ``code``, freshly minted, the first time;
        **the one it already carries after that**, so a second first read
        records nothing."""

        if self.code is not None:
            return self.code
        self._record_that(
            FriendLinkMade(owner_id=self.owner_id, code=code.value, occurred_at=at)
        )
        return code

    def replace(self, *, code: FriendLinkCode, at: Instant) -> FriendLinkCode:
        """**New link**: ``code`` from now on, and the old one dead at once. A
        link never read is simply made."""

        if self.code is None:
            return self.make(code=code, at=at)
        invariant(code != self.code, f"a link replaced by its own code: {code!r}")
        self._record_that(
            FriendLinkReplaced(
                owner_id=self.owner_id,
                code=code.value,
                replaced_code=self.code.value,
                occurred_at=at,
            )
        )
        return code

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, FriendLinkMade | FriendLinkReplaced):
            self.code = FriendLinkCode(event.code)
        else:
            raise TypeError(f"Unsupported friend link event {event!r}")
        self.version += 1
