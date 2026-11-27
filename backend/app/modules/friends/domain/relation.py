"""The words this context publishes: a reader's relation to a player, where a
request was made, and how a friendship began and ended.

**``FriendRelation`` is the one vocabulary every face reads** (``docs/adr/0202``
§2) — Members, the record, the deck, the details, Home, Fill in and the result
all carry it under this spelling, so a client is handed one word for one fact.
It is always **the reader's** relation: *sent* is a request the reader made,
*asked you* one made of the reader.
"""

from __future__ import annotations

from enum import StrEnum


class FriendRelation(StrEnum):
    """Where the reader stands with one player."""

    #: Nothing between them: the **+ Add** pill. Also what the reader reads of a
    #: player whose request is hidden by the reader's own block.
    NONE = "NONE"
    #: The reader asked, and the request is open — set aside or not. *request
    #: sent*, for as long as it stays open: it never expires.
    SENT = "SENT"
    #: They asked the reader, and the request is open — the **Accept** pill.
    ASKED_YOU = "ASKED_YOU"
    #: Friends.
    FRIEND = "FRIEND"


class RequestOrigin(StrEnum):
    """Where a friend request was made (``docs/adr/0202`` §1)."""

    #: A group's Members, or a game's faces in that group.
    MEMBERS = "MEMBERS"
    #: The player record, opened from a face.
    RECORD = "RECORD"
    #: The result screen's *PLAYED WITH* card.
    RESULT = "RESULT"
    #: The requester's Friend link, opened by the person asked (#748) — *Invited
    #: you to Raketa* on their Home.
    LINK = "LINK"
    #: A record opened from the Rankings page, with that page's sport (#773;
    #: ``docs/adr/0203`` §9) — *Found you in the padel ranking* on their Home.
    RANKING = "RANKING"
    #: Home's *New in Rakieta* row, or a record opened from it (#793;
    #: ``docs/adr/0204`` §9) — *Found you among new players* on their Home.
    #: Names no group and no sport: the line is the whole line.
    NEW_PLAYERS = "NEW_PLAYERS"
    #: Home's *Same competitive level players* row, or a record opened from it
    #: (#794; ``docs/adr/0204`` §9), with the card's sport — *Your level in
    #: padel · 91% even* on their Home, worked out when it is read. Names no
    #: group.
    SAME_LEVEL = "SAME_LEVEL"
    #: Home's *Same vibe players* row, or a record opened from it (#795;
    #: ``docs/adr/0204`` §9) — *6 things in common* on their Home, counted when
    #: it is read. Names no group and no sport.
    SAME_VIBE = "SAME_VIBE"


class HowFriendsWereMade(StrEnum):
    #: The person asked said yes.
    ACCEPTED = "ACCEPTED"
    #: Each asked the other before either answered: nobody had to say yes.
    CROSSED = "CROSSED"


class HowItEnded(StrEnum):
    #: One of them removed the other.
    REMOVED = "REMOVED"
    #: One of them blocked the other: the friendship and any open request end.
    BLOCKED = "BLOCKED"
