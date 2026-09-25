"""The Groups context's refusals.

**A field a player typed is refused under that field** (``details.field``), the
shape the club website's forms and the player sign-up already take: the New
group form writes its sentence under the control the code names, chosen from the
code and never from the message (``docs/adr/0187`` §6). So the bounds live in the
value objects and are refused from here, and the request schema declares types
and nothing else — a bound restated there would refuse first, as a ``422`` naming
no field.
"""

from app.shared.domain import BadRequestError, ForbiddenError, NotFoundError


class GroupNameInvalid(BadRequestError):
    """A group's name is 1–40 characters once trimmed (``docs/adr/0183`` §2)."""

    code = "group_name_invalid"

    def __init__(self) -> None:
        super().__init__("a group's name is 1–40 characters", details={"field": "name"})


class HomeClubUnknown(BadRequestError):
    """The home club named is no club in Raketa.

    A group's home club is **required** and chosen from every club in Raketa
    (``docs/adr/0183`` §2), so an id that names none is a field to correct — the
    form only offers clubs that exist, and this is reached by a club that stopped
    existing between the search and the tap, or by a client that invented one.
    """

    code = "home_club_unknown"

    def __init__(self) -> None:
        super().__init__(
            "only a club in Raketa can be a home club",
            details={"field": "home_club_id"},
        )


class GroupNotFound(NotFoundError):
    """**One refusal for two cases**: no such group, and a group the reader is
    not a member of.

    Reading a group is for its members only (``docs/adr/0183``, #504). Telling a
    stranger *this group exists but is not yours* would answer a question the
    refusal exists to leave unanswered, and both cases have one remedy — the
    reader is not in it."""

    code = "group_not_found"

    def __init__(self) -> None:
        super().__init__("group not found")


class NotTheGroupOwner(ForbiddenError):
    """A Group member who is not its Owner asked to see or answer its Join
    requests.

    **Nobody but the Owner** (#505): a request is a person asking the one
    who answers, and the rest of the group has no business reading who asked
    to be let in. Refused as a ``403`` rather than as ``group_not_found``,
    because a member already knows the group exists — the stranger's refusal
    is for the stranger."""

    code = "not_the_group_owner"

    def __init__(self) -> None:
        super().__init__("only the group's owner answers its join requests")


class JoinRequestNotFound(NotFoundError):
    """The Owner approved somebody who has no Join request waiting — one that
    was declined, or never made.

    **Nobody is admitted who did not ask**, so approving is refused rather than
    turned into a membership; the person has to ask again. A decline of a
    request that is not waiting is not refused — it wanted the request gone, and
    it is."""

    code = "join_request_not_found"

    def __init__(self) -> None:
        super().__init__("nobody by that id is waiting to join this group")
