"""What this context refuses. Each refusal is a stable code a client branches on."""

from __future__ import annotations

from http import HTTPStatus

from app.shared.domain.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class CannotBefriendYourself(BadRequestError):
    """A player named themselves. A refusal rather than a no-op: a stream whose
    two sides are one person is nothing a caller can have meant."""

    code = "cannot_befriend_yourself"

    def __init__(self) -> None:
        super().__init__("A player cannot ask themselves to be friends.")


class NotInYourGroups(NotFoundError):
    """The player shares no group with the requester **and isn't listed on
    General, or is hidden from it** (the friends mechanics §3.1, widened by
    ``docs/adr/0203`` §9, #773: nobody else can be asked except through the
    link). **One answer for an id nobody holds, a stranger off the list and a
    hidden one**, so the route is no oracle for which ids exist or who turned
    *Show me in General* off. The code predates the widening and is kept: a
    shipped client branches on it."""

    code = "player_not_in_your_groups"

    def __init__(self) -> None:
        super().__init__("You can ask only people from your groups or on the ranking.")


class DailyRequestLimit(AppError):
    """The requester has sent ten requests this Warsaw day to people they share
    no group with (#773; ``docs/adr/0203`` §9, Q21): *You've sent 10 requests to
    new people today. Try again tomorrow.* Nothing was recorded. A request to a
    group-mate still goes through, and the count resets at Warsaw midnight.

    A 429, as the card-testing guard's ``payment_setups_exhausted`` is: the
    same request succeeds tomorrow, unchanged."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "daily_request_limit"

    def __init__(self) -> None:
        super().__init__(
            "You've sent 10 requests to new people today. Try again tomorrow."
        )


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


class FriendLinkNotFound(NotFoundError):
    """A link that leads nowhere: a code replaced by **New link**, one nobody's
    link ever carried, or one that could be no link's code — one answer,
    *Nothing at that link*, so the route is no oracle for which codes were ever
    made (the mechanics §4.2). The public read gives it too for an owner nobody
    can name."""

    code = "friend_link_not_found"

    def __init__(self) -> None:
        super().__init__("Nothing at that link.")


class FriendNotFound(NotFoundError):
    """The player is not the reader's friend — never was, removed, ended by a
    block, or the reader themselves. **One answer for all of them**, given before
    anything else is read, so asking about a stranger tells nothing about them
    (#749)."""

    code = "friend_not_found"

    def __init__(self) -> None:
        super().__init__("They are not your friend.")


class AlreadyHasALevel(ConflictError):
    """The friend already has a level in the sport: there is nothing to ask
    them, and they can be seated now (#749)."""

    code = "already_has_a_level"

    def __init__(self) -> None:
        super().__init__("They have a level in that sport already.")


class LevelAlreadyAsked(ConflictError):
    """The reader asked this friend for a level in this sport before — **once
    per friend per sport, ever** (the mechanics §5), answered or not, and after a
    friendship removed and made again too."""

    code = "level_already_asked"

    def __init__(self) -> None:
        super().__init__("You asked them for a level in that sport already.")


class NotOneOfYourGroups(NotFoundError):
    """An ask for a level names the group whose picker it was asked from, and
    that group must be the asker's now: its picker is where the answer opens
    (#749). One answer for a group that does not exist and one the asker is not
    in, as a group's own read gives (``groups.md``)."""

    code = "not_one_of_your_groups"

    def __init__(self) -> None:
        super().__init__("Ask from the picker of one of your groups.")
