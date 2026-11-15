"""The reader's relation to a person on a row, **in this context's own words**.

The same four as Friends' ``FriendRelation`` — the one wire vocabulary every
face carries — spelled here so the domain borrows no other context's type, held
equal to Friends' by ``tests/unit/test_discovery_relation.py`` and put on the
wire as ``FriendRelation`` (the presentation layer's only borrowing).

**Connected** (the mechanics §2) is friends, or a request the reader sent that
is still open. Someone who asked the reader is **not** connected: they are new
to the reader as anybody unconnected is (call 7 of #790).
"""

from __future__ import annotations

from enum import StrEnum


class Relation(StrEnum):
    #: Nothing between them — or a request the reader's own block hides.
    NONE = "NONE"
    #: The reader asked, and the request is open.
    SENT = "SENT"
    #: They asked the reader, and the request is open.
    ASKED_YOU = "ASKED_YOU"
    FRIEND = "FRIEND"

    @property
    def connected(self) -> bool:
        """Friends, or the reader's request still open — never somebody who
        asked the reader."""

        return self in (Relation.SENT, Relation.FRIEND)
