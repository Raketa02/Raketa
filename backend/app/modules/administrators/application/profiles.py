"""Which profiles an account holds — what ``/users/me`` says, and what the
entry gate reads first (``docs/adr/0185`` §2–§3).

- **Whether it acts as a player**: it has given the Adult attestation — every
  sign-up did, and *Start playing* asks for it first — or it holds a Player
  profile. False only for an account an Invitation opened that has not started
  playing, which is the account the gate sends to the administrator area.
- **The clubs it administers**, one per active Administrator.
- **Any pending invitation addressed to its email** — invited, and not yet past
  its window — so the app can offer it on launch.
- **Every group the club handed it that it has not been told about**
  (``docs/adr/0192`` §1), so the app can tell it once.

*Profile* is the switcher's word, not a domain term (``docs/adr/0185`` §1).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant
from app.modules.administrators.domain.administrator import AdministratorStanding
from app.modules.administrators.domain.ports import (
    AccountHolders,
    AdministratorDirectory,
    ClubNames,
    OfficialGroupAssignments,
)
from app.modules.users.domain.value_objects import Email


@final
@dataclass(frozen=True, slots=True)
class AdministeredClub:
    club_id: UUID
    club_name: str


@final
@dataclass(frozen=True, slots=True)
class PendingInvitation:
    administrator_id: UUID
    club_id: UUID
    club_name: str
    expires_at: Instant


@final
@dataclass(frozen=True, slots=True)
class Handover:
    """A group a club handed to this account's administratorship there, which
    it has not been told about: the club, the group, and the queue it got."""

    club_id: UUID
    club_name: str
    group_id: UUID
    group_name: str
    waiting_count: int
    handed_over_at: Instant


@final
@dataclass(frozen=True, slots=True)
class AccountProfiles:
    acts_as_player: bool
    administers: Sequence[AdministeredClub]
    pending_invitations: Sequence[PendingInvitation]
    handovers: Sequence[Handover] = ()


class ReadAccountProfiles:
    def __init__(
        self,
        *,
        directory: AdministratorDirectory,
        accounts: AccountHolders,
        clubs: ClubNames,
        groups: OfficialGroupAssignments,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._accounts = accounts
        self._clubs = clubs
        self._groups = groups
        self._clock = clock

    async def execute(self, *, account_id: UUID, email: Email) -> AccountProfiles:
        now = self._clock.now()
        active = await self._directory.active_for(account_id)
        pending = [
            (listing, listing.expires_at)
            for listing in await self._directory.invited_as(email)
            if listing.standing(now=now) is AdministratorStanding.INVITED
            and listing.expires_at is not None
        ]
        names = await self._clubs.names_of(
            {listing.club_id for listing in active}
            | {listing.club_id for listing, _ in pending}
        )
        # Only an active administratorship is told: a removed one runs nothing.
        club_of = {listing.id: listing.club_id for listing in active}
        handed = await self._groups.handed_untold(list(club_of)) if club_of else ()
        return AccountProfiles(
            acts_as_player=await self._accounts.acts_as_player(account_id),
            administers=sorted(
                (
                    AdministeredClub(
                        club_id=listing.club_id, club_name=names[listing.club_id]
                    )
                    for listing in active
                    if listing.club_id in names
                ),
                key=lambda club: (club.club_name.casefold(), club.club_id),
            ),
            pending_invitations=sorted(
                (
                    PendingInvitation(
                        administrator_id=listing.id,
                        club_id=listing.club_id,
                        club_name=names[listing.club_id],
                        expires_at=expires_at,
                    )
                    for listing, expires_at in pending
                    if listing.club_id in names
                ),
                key=lambda invitation: (invitation.expires_at, invitation.club_id),
            ),
            # Oldest handed first, as they happened.
            handovers=sorted(
                (
                    Handover(
                        club_id=club_of[group.administrator_id],
                        club_name=names[club_of[group.administrator_id]],
                        group_id=group.id,
                        group_name=group.name,
                        waiting_count=group.waiting_count,
                        handed_over_at=group.handed_over_at,
                    )
                    for group in handed
                    if club_of[group.administrator_id] in names
                ),
                key=lambda handover: (handover.handed_over_at, handover.group_id),
            ),
        )
