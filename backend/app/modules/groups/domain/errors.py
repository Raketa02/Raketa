"""The Groups context's refusals.

**A field a player typed is refused under that field** (``details.field``), the
shape the club website's forms and the player sign-up already take: the New
group form writes its sentence under the control the code names, chosen from the
code and never from the message (``docs/adr/0187`` §6). So the bounds live in the
value objects and are refused from here, and the request schema declares types
and nothing else — a bound restated there would refuse first, as a ``422`` naming
no field.
"""

from app.shared.domain import BadRequestError, ConflictError, NotFoundError


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


class GroupNeedsApproval(ConflictError):
    """Tapping *Join* on a *People I approve* group admits nobody.

    **Until join requests exist** (#505), which is where asking to join such a
    group becomes a request its Owner answers. Refused rather than quietly
    admitted, because admitting would be the one thing the Owner chose this
    policy to prevent."""

    code = "group_needs_approval"

    def __init__(self) -> None:
        super().__init__("this group admits people its owner approves")
