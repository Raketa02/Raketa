"""The Administrators context's refusals.

**A field the desk typed is refused under that field** (``details.field``), the
shape every club website form already takes (``docs/adr/0187`` §6): the website
writes the sentence, chosen from the code and never from the message.
"""

from typing import Optional
from uuid import UUID

from app.shared.domain import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


class AdministratorNameInvalid(BadRequestError):
    """The name the club typed is not a Name: 2–64 characters once trimmed and
    collapsed — the rule an Administrator's name follows (``docs/adr/0199``
    §4)."""

    code = "administrator_name_invalid"

    def __init__(self) -> None:
        super().__init__(
            "an administrator's name is 2–64 characters", details={"field": "name"}
        )


class AdministratorAlreadyInvited(ConflictError):
    """That email is already invited at this club — expired included: the desk
    resends rather than inviting the same address twice."""

    code = "administrator_already_invited"

    def __init__(self) -> None:
        super().__init__(
            "that email is already invited here", details={"field": "email"}
        )


class AdministratorAlreadyActive(ConflictError):
    """That email is already an active administrator here — refused as an
    invitation, and as a resend, which has nothing left to open."""

    code = "administrator_already_active"

    def __init__(self) -> None:
        super().__init__(
            "that email is already an administrator here", details={"field": "email"}
        )


class AdministratorNotFound(NotFoundError):
    """No administrator of this club answers to that id — a removed one
    included, because a removed administrator is off the club's list."""

    code = "administrator_not_found"

    def __init__(self) -> None:
        super().__init__("no administrator of this club has that id")


class AdministratorHasNoAccount(ConflictError):
    """*Reset password* for somebody who never set one: there is no account to
    recover. The invitation is what they need, and *Resend* is what sends it."""

    code = "administrator_has_no_account"

    def __init__(self) -> None:
        super().__init__("that administrator has no account yet: resend instead")


class AdministratorAlsoPlays(ConflictError):
    """*Reset password* for an account that also plays (``docs/adr/0184`` §6).

    The club made an administrator-only account and may help recover it. It did
    not make a player's account and may never touch it — a reset would hand
    whoever reads the email that person's games, chats and record. They recover
    through *Forgot password?*, like anybody else."""

    code = "administrator_also_plays"

    def __init__(self) -> None:
        super().__init__(
            "that account also plays: only its owner can reset its password"
        )


class NotAnAdministrator(ForbiddenError):
    """**The administrator guard's refusal** (``docs/adr/0184`` §7): this
    account holds no active administratorship at that club — removed since the
    last request, or never one.

    One code for both, and **distinct from every other refusal**, because the
    app turns it into one message and one move: to the player profile, or a
    sign-out for an account with none."""

    code = "not_an_administrator"

    def __init__(self, club_id: Optional[UUID] = None) -> None:
        super().__init__(
            "this account does not run that club's groups",
            details=None if club_id is None else {"club_id": str(club_id)},
        )


class InvitationNotFound(NotFoundError):
    """No pending invitation addressed to this account answers to that id —
    one answer for somebody else's, a removed one and one that never was."""

    code = "invitation_not_found"

    def __init__(self) -> None:
        super().__init__("no invitation for this account has that id")


class InvitationNotPending(ConflictError):
    """The invitation is no longer waiting to be taken up: the club removed
    it. Raised by the aggregate; each route answers it in its own words."""

    code = "invitation_not_pending"

    def __init__(self) -> None:
        super().__init__("that invitation is no longer open")


class InvitationExpired(ConflictError):
    """Accepted after its 72 hours. *Ask the club to send a new one*, as an
    expired code is told."""

    code = "invitation_expired"

    def __init__(self) -> None:
        super().__init__("that invitation has expired")


class SignInToAccept(ConflictError):
    """A right code or a live link, for an address that has since become an
    account with a password (``docs/adr/0184`` §2): that account accepts the
    invitation from the app, signed in, and no second password is set.

    Said only to somebody holding the right code or the link, so it tells no
    stranger that an address has an account."""

    code = "sign_in_to_accept"

    def __init__(self) -> None:
        super().__init__("this email already has an account: sign in to accept")
