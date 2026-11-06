"""What this context refuses. Each refusal is a stable code a client branches on."""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError, ConflictError, NotFoundError


class CannotBefriendYourself(BadRequestError):
    """A player named themselves. A refusal rather than a no-op: a stream whose
    two sides are one person is nothing a caller can have meant."""

    code = "cannot_befriend_yourself"

    def __init__(self) -> None:
        super().__init__("A player cannot ask themselves to be friends.")


class NotInYourGroups(NotFoundError):
    """The player shares no group with the requester (the mechanics §3.1: nobody
    outside your groups can be asked except through the link). **One answer
    for an id nobody holds and for a stranger**, so the route is no oracle for
    which ids exist."""

    code = "player_not_in_your_groups"

    def __init__(self) -> None:
        super().__init__("You can ask only people from your groups.")


class AlreadyFriends(ConflictError):
    code = "already_friends"

    def __init__(self) -> None:
        super().__init__("You are friends already.")


class FriendRequestAlreadySent(ConflictError):
    """The requester's own request to this person is open — set aside or not.
    *Nobody can nag* (``docs/adr/0202`` §1)."""

    code = "friend_request_already_sent"

    def __init__(self) -> None:
        super().__init__("You asked already — the request is still open.")


class UnblockThemFirst(ConflictError):
    """The requester blocked this player. A block keeps two people apart, and
    asking would offer friendship across it; somebody you blocked is never
    offered to befriend (the mechanics §3.5). It names only the reader's own
    block, which the reader may always read (``docs/adr/0193`` §3)."""

    code = "unblock_them_first"

    def __init__(self) -> None:
        super().__init__("Unblock them before asking them to be friends.")


class FriendRequestNotFound(NotFoundError):
    """No request from this player to the reader is open — never made, answered,
    cancelled, ended, or hidden by the reader's own block, which reads exactly
    as no request at all."""

    code = "friend_request_not_found"

    def __init__(self) -> None:
        super().__init__("There is no request from them waiting for you.")
