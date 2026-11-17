"""The Groups context's refusals.

**A field a player typed is refused under that field** (``details.field``), the
shape the club website's forms and the player sign-up already take: the New
group form writes its sentence under the control the code names, chosen from the
code and never from the message (``docs/adr/0187`` §6). So the bounds live in the
value objects and are refused from here, and the request schema declares types
and nothing else — a bound restated there would refuse first, as a ``422`` naming
no field.
"""

from app.shared.domain import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


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


class WhatsAppSizeInvalid(BadRequestError):
    """An official group records how many people its WhatsApp group has: a
    **whole number from 2 to 1024**, required (``docs/adr/0183`` §3). Two,
    because a WhatsApp group of one is nobody's crowd; 1024, because that is as
    many as WhatsApp lets into one."""

    code = "whatsapp_size_invalid"

    def __init__(self) -> None:
        super().__init__(
            "a WhatsApp group size is a whole number from 2 to 1024",
            details={"field": "whatsapp_size"},
        )


class GroupSportsRequired(BadRequestError):
    """An official group **declares** what it plays, and declares at least one
    sport (``docs/adr/0183`` §3) — its dots are what it declares, and a group
    with none would be a crowd with nothing to play."""

    code = "group_sports_required"

    def __init__(self) -> None:
        super().__init__(
            "an official group plays at least one sport", details={"field": "sports"}
        )


class SportNotOfferedByClub(BadRequestError):
    """An official group declares a sport **its club offers**, and nothing else
    (``docs/adr/0183`` §3): a group left playing a sport its club does not have
    is what the club's own refusal to untick one exists to prevent
    (``docs/adr/0182`` §5). ``details.sport`` names the first such sport, in the
    registry's order."""

    code = "sport_not_offered_by_club"

    def __init__(self, sport: str) -> None:
        super().__init__(
            "an official group plays only sports its club offers",
            details={"field": "sports", "sport": sport},
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
    """A Group member who is not its Owner asked to do what only the Owner
    does: see or answer its Join requests (#505), rename it, change who can
    join, or delete it (#506).

    **An official group has no Owner** (``docs/adr/0183`` §3), so every member
    asking this of one is refused the same way — its Administrator included,
    when they ask as a player: their group is answered and edited from the
    administrator surface, and nobody deletes it at all (#509).

    **Nobody but the Owner**: a request is a person asking the one who
    answers, and the rest of the group has no business reading who asked to be
    let in; and a group's name and door are the Owner's to change
    (``docs/adr/0183`` §2). Refused as a ``403`` rather than as
    ``group_not_found``, because a member already knows the group exists — the
    stranger's refusal is for the stranger."""

    code = "not_the_group_owner"

    def __init__(self) -> None:
        super().__init__("only the group's owner may do that")


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


class LoneOwnerCannotLeave(ConflictError):
    """The Owner asked to leave a group nobody else is in.

    **The group always keeps somebody who can approve people**
    (``docs/adr/0183`` §7): an Owner leaving passes the group to the member
    who has been in longest, and alone there is nobody to pass it to. What
    undoes a group nobody joined is *Delete the group*, which is the remedy
    this refusal points at."""

    code = "lone_owner_cannot_leave"

    def __init__(self) -> None:
        super().__init__("the group's only member deletes it rather than leaving it")


class GroupHasOtherMembers(ConflictError):
    """The Owner asked to delete a group other people are in.

    **A player group is deleted only while its Owner is its only member**
    (``docs/adr/0183`` §7): that undoes a group nobody joined, and it can never
    take a group away from the people in it. An Owner who wants out of a group
    with people in it leaves, and the group passes on."""

    code = "group_has_other_members"

    def __init__(self) -> None:
        super().__init__("a group other people are in cannot be deleted")


class AdministratorNotActive(ConflictError):
    """The club handed a group to somebody who is not an **active**
    Administrator of the club (``docs/adr/0183`` §8): still invited, expired,
    removed, another club's, or nobody at all.

    **One refusal for all five**, because the Hand over page offers only the
    club's active Administrators and every one of them has one remedy — choose
    again from the list as it stands now. Reached by a list that went stale
    between drawing and the tap: the person was removed, or their password
    reset, in the meantime. Nothing was recorded."""

    code = "administrator_not_active"

    def __init__(self) -> None:
        super().__init__(
            "a group is handed only to an active administrator of the club"
        )


class NotAHottestGroupsPage(BadRequestError):
    """A page of *Groups heating up* asked after a cursor this server never
    wrote (#813). A client's own bug, said so."""

    code = "not_a_hottest_groups_page"

    def __init__(self) -> None:
        super().__init__("Not a page of Hottest groups: an unreadable cursor.")
