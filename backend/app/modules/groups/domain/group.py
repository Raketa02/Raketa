"""The Group aggregate — event-sourced, one aggregate for both kinds.

``docs/adr/0183`` §1 rejected two aggregates: the kinds share the link, the
membership, the join policy and its requests, both searches and the whole page,
and two aggregates would be two copies of every shared rule. They differ in
three places, and each rule below says which kind it binds (#509): **who
answers** — a player group's Owner, an official group's Administrator, whom
only the club changes (#510) — **where the sports come from** — an official
group declares them — and **whether the one who runs it can delete or leave
it** — an official group's Administrator can do neither, because running it is
not membership (§7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.kernel import invariant
from app.modules.groups.domain.errors import (
    GroupHasOtherMembers,
    JoinRequestNotFound,
    LoneOwnerCannotLeave,
    NotTheGroupOwner,
)
from app.modules.groups.domain.events import (
    AdministratorAssigned,
    GroupDeleted,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OfficialGroupCreated,
    OwnershipPassed,
    PlayerGroupCreated,
    SportsDeclared,
    WhatsAppSizeSet,
)
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupCode,
    GroupKind,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Group:
    """One group, as its stream leaves it.

    ``members`` maps each Group member to the instant they joined, in the order
    they joined — so its first key is the longest-standing member, who is who a
    leaving Owner passes the group to. Somebody who left and came back is keyed
    again at the end, because their stay starts again.
    ``waiting`` maps each person whose Join request is waiting to the instant
    they asked, in the order they asked.

    ``is_deleted`` is the end of the stream: a deleted group has no members,
    nobody waiting, and is loaded as no group at all.

    **The kind decides which of the rest are present.** A player group has an
    ``owner_id`` and nothing in the last three; an official group has **no
    Owner**, and its ``administrator_id`` — the Administrator who runs it — its
    ``whatsapp_size`` and its ``declared_sports`` (``docs/adr/0183`` §3).
    """

    id: UUID
    name: GroupName
    home_club_id: UUID
    join_policy: JoinPolicy
    owner_id: UUID | None
    code: GroupCode
    members: dict[UUID, datetime]
    waiting: dict[UUID, datetime] = field(default_factory=dict)
    kind: GroupKind = GroupKind.PLAYER
    administrator_id: UUID | None = None
    whatsapp_size: WhatsAppSize | None = None
    declared_sports: DeclaredSports | None = None
    is_deleted: bool = False
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Group":
        group = cls._empty()
        for event in events:
            group._apply(event)
        return group

    @classmethod
    def _empty(cls) -> "Group":
        group = cls.__new__(cls)
        group.version = 0
        group.members = {}
        group.waiting = {}
        group.kind = GroupKind.PLAYER
        group.owner_id = None
        group.administrator_id = None
        group.whatsapp_size = None
        group.declared_sports = None
        group.is_deleted = False
        group._events = EventRecorder()
        return group

    @classmethod
    def create_player_group(
        cls,
        *,
        group_id: UUID,
        name: GroupName,
        home_club_id: UUID,
        join_policy: JoinPolicy,
        owner_id: UUID,
        code: GroupCode,
        occurred_at: datetime,
    ) -> "Group":
        """A player creates a group at a home club and becomes its Owner and
        first member (``docs/adr/0183`` §2). That the home club exists is the
        use case's to have checked — it is a fact about clubs."""

        group = cls._empty()
        group._record_that(
            PlayerGroupCreated(
                group_id=group_id,
                name=name.value,
                home_club_id=home_club_id,
                join_policy=join_policy.value,
                owner_id=owner_id,
                code=code.value,
                occurred_at=occurred_at,
            )
        )
        return group

    @classmethod
    def create_official_group(
        cls,
        *,
        group_id: UUID,
        name: GroupName,
        club_id: UUID,
        join_policy: JoinPolicy,
        administrator_id: UUID,
        created_by: UUID,
        whatsapp_size: WhatsAppSize,
        sports: DeclaredSports,
        code: GroupCode,
        occurred_at: datetime,
    ) -> "Group":
        """An Administrator creates an official group for their club
        (``docs/adr/0183`` §3). **Its home club is their club**, fixed; it has
        **no Owner and nobody in it** — running it is not membership (§7).
        That the Administrator is active at that club, and that its sports are
        the club's, are the use case's to have checked — facts about
        administrators and clubs."""

        group = cls._empty()
        group._record_that(
            OfficialGroupCreated(
                group_id=group_id,
                name=name.value,
                home_club_id=club_id,
                join_policy=join_policy.value,
                administrator_id=administrator_id,
                created_by=created_by,
                whatsapp_size=whatsapp_size.value,
                sports=sports.codes(),
                code=code.value,
                occurred_at=occurred_at,
            )
        )
        return group

    def is_member(self, player_id: UUID) -> bool:
        return player_id in self.members

    def is_waiting(self, player_id: UUID) -> bool:
        return player_id in self.waiting

    def join(
        self, player_id: UUID, *, occurred_at: datetime, runs_it: bool = False
    ) -> None:
        """A player taps *Join* or *Ask to join* (``docs/adr/0183`` §7) — one
        tap, and the policy decides what it was.

        Under *Anyone* they are a member at once. Under *People I approve* their
        tap is a **Join request**, waiting for whoever answers. **Neither is
        recorded twice**: a member tapping again, or somebody asking again while
        their request waits, records nothing and is not refused — the tap asked
        for what they already have.

        **The account that runs an official group joins it directly**, whatever
        its policy (``runs_it``): they would otherwise be asking themselves. One
        who asked as a player before the club made them its Administrator is
        let in by this tap, as the one who answers. Whether the account runs it
        — its Administrator's, and still active — is the use case's to have
        asked; a player group is run by nobody that way.
        """

        invariant(
            not runs_it or self.kind is GroupKind.OFFICIAL,
            "only an official group is run by an Administrator",
        )
        if self.is_member(player_id):
            return
        if runs_it and self.is_waiting(player_id):
            self._record_that(
                JoinRequestApproved(
                    group_id=self.id,
                    player_id=player_id,
                    approved_by=player_id,
                    occurred_at=occurred_at,
                )
            )
            return
        if self.is_waiting(player_id):
            return
        if self.join_policy is JoinPolicy.PEOPLE_I_APPROVE and not runs_it:
            self._record_that(
                JoinRequested(
                    group_id=self.id, player_id=player_id, occurred_at=occurred_at
                )
            )
            return
        self._record_that(
            GroupJoined(group_id=self.id, player_id=player_id, occurred_at=occurred_at)
        )

    def approve(
        self,
        player_id: UUID,
        *,
        by: UUID,
        occurred_at: datetime,
        as_administrator: UUID | None = None,
    ) -> None:
        """Whoever answers approves a Join request, and the person is a member
        **at once** (``docs/adr/0183`` §7).

        Approving somebody already in changes nothing — a second tap, or a tap
        from a second phone, wanted them in and they are. Approving somebody
        with nothing waiting is refused: nobody is admitted who did not ask.
        """

        self._refuse_unless_it_answers(by, as_administrator)
        if self.is_member(player_id):
            return
        if not self.is_waiting(player_id):
            raise JoinRequestNotFound()
        self._record_that(
            JoinRequestApproved(
                group_id=self.id,
                player_id=player_id,
                approved_by=by,
                occurred_at=occurred_at,
            )
        )

    def decline(
        self,
        player_id: UUID,
        *,
        by: UUID,
        occurred_at: datetime,
        as_administrator: UUID | None = None,
    ) -> None:
        """Whoever answers declines a Join request, and it is gone **silently**: the
        person's relation is *none* again and they may ask again
        (``docs/adr/0183`` §7).

        Declining what is not waiting changes nothing — the tap wanted the
        request gone, and it is. It never removes a member: **nobody removes a
        Group member**, and a decline arriving after an approval finds nothing
        to decline.
        """

        self._refuse_unless_it_answers(by, as_administrator)
        if not self.is_waiting(player_id):
            return
        self._record_that(
            JoinRequestDeclined(
                group_id=self.id,
                player_id=player_id,
                declined_by=by,
                occurred_at=occurred_at,
            )
        )

    def leave(self, player_id: UUID, *, occurred_at: datetime) -> None:
        """A Group member taps *Leave the group* (``docs/adr/0183`` §7) — and
        may join again later, under whatever the group's policy is then.

        **An Owner leaving a group other people are in passes it to the member
        who has been in longest**, so the group always keeps somebody who can
        approve people, and the requests waiting on it pass with it. *Longest*
        is this stay: somebody who left and came back counts from their return.
        **An Owner alone cannot leave** — there is nobody to pass it to — and
        deletes the group instead.

        Whether they are in it at all is the caller's to have asked first: a
        stranger is refused as the group's page refuses them.
        """

        if self.kind is GroupKind.PLAYER and player_id == self.owner_id:
            heir = next(
                (member for member in self.members if member != player_id), None
            )
            if heir is None:
                raise LoneOwnerCannotLeave()
            self._record_that(
                OwnershipPassed(
                    group_id=self.id,
                    from_id=player_id,
                    to_id=heir,
                    occurred_at=occurred_at,
                )
            )
        self._record_that(
            GroupLeft(group_id=self.id, player_id=player_id, occurred_at=occurred_at)
        )

    def rename(
        self,
        name: GroupName,
        *,
        by: UUID,
        occurred_at: datetime,
        as_administrator: UUID | None = None,
    ) -> None:
        """Whoever runs the group renames it — the Owner from *Edit group*
        (``docs/adr/0183`` §2), the Administrator from its settings (§3).

        **Its link does not change** — the code is the group's identity and the
        name is not (§4). Saving the name it already has records nothing.
        """

        self._refuse_unless_it_answers(by, as_administrator)
        if name == self.name:
            return
        self._record_that(
            GroupRenamed(
                group_id=self.id,
                name=name.value,
                renamed_by=by,
                occurred_at=occurred_at,
            )
        )

    def change_join_policy(
        self,
        policy: JoinPolicy,
        *,
        by: UUID,
        occurred_at: datetime,
        as_administrator: UUID | None = None,
    ) -> tuple[UUID, ...]:
        """Whoever runs the group changes who can join — the Owner from *Edit
        group*, the Administrator from its settings (``docs/adr/0183`` §7) —
        and learns who it let in.

        **Switching to *Anyone* admits everybody waiting at once**, in the order
        they asked, because nobody should be left waiting under a rule that no
        longer applies. Saving the policy it already has records nothing.

        Returns everybody the switch admitted, in the order they asked — empty
        for every change but that one.
        """

        self._refuse_unless_it_answers(by, as_administrator)
        if policy is self.join_policy:
            return ()
        self._record_that(
            JoinPolicyChanged(
                group_id=self.id,
                join_policy=policy.value,
                changed_by=by,
                occurred_at=occurred_at,
            )
        )
        if policy is not JoinPolicy.ANYONE:
            return ()
        admitted = tuple(self.waiting)
        for player_id in admitted:
            self._record_that(
                JoinRequestApproved(
                    group_id=self.id,
                    player_id=player_id,
                    approved_by=by,
                    occurred_at=occurred_at,
                )
            )
        return admitted

    def set_whatsapp_size(
        self,
        size: WhatsAppSize,
        *,
        by: UUID,
        occurred_at: datetime,
        as_administrator: UUID | None = None,
    ) -> None:
        """Its Administrator changes how many people the WhatsApp group has
        (``docs/adr/0183`` §3). **Official groups only.** Saving the size it
        already has records nothing."""

        self._refuse_unless_it_answers(by, as_administrator)
        invariant(
            self.kind is GroupKind.OFFICIAL, "only an official group has a size"
        )
        if size == self.whatsapp_size:
            return
        self._record_that(
            WhatsAppSizeSet(
                group_id=self.id,
                whatsapp_size=size.value,
                set_by=by,
                occurred_at=occurred_at,
            )
        )

    def declare_sports(
        self,
        sports: DeclaredSports,
        *,
        by: UUID,
        occurred_at: datetime,
        as_administrator: UUID | None = None,
    ) -> None:
        """Its Administrator declares what the group plays, again — the whole
        set (``docs/adr/0183`` §3). **Official groups only.** That they are its
        club's is the use case's to have checked. Declaring the sports it
        already declares records nothing."""

        self._refuse_unless_it_answers(by, as_administrator)
        invariant(
            self.kind is GroupKind.OFFICIAL,
            "only an official group declares its sports",
        )
        if sports == self.declared_sports:
            return
        self._record_that(
            SportsDeclared(
                group_id=self.id,
                sports=sports.codes(),
                declared_by=by,
                occurred_at=occurred_at,
            )
        )

    def assign_administrator(
        self, administrator_id: UUID, *, by: UUID, occurred_at: datetime
    ) -> None:
        """The club hands an official group to one of its Administrators
        (``docs/adr/0183`` §8) — any group, including one whose administrator
        it removed. **Only who answers changes**: the link, the policy, the
        size, the members and the requests waiting all stay, and the new
        Administrator simply finds them; somebody the old one let in as a
        player stays in. ``by`` is the Club account.

        That the new Administrator is an **active** one of this group's club,
        and that it is the club's group, are the use case's to have checked —
        facts about administrators and the club asking. Handing it to whoever
        runs it already records nothing. **Official groups only.**"""

        invariant(
            self.kind is GroupKind.OFFICIAL,
            "only an official group is run by an Administrator",
        )
        if administrator_id == self.administrator_id:
            return
        self._record_that(
            AdministratorAssigned(
                group_id=self.id,
                administrator_id=administrator_id,
                assigned_by=by,
                occurred_at=occurred_at,
            )
        )

    def delete(self, *, by: UUID, occurred_at: datetime) -> None:
        """The Owner taps *Delete the group* (``docs/adr/0183`` §7) — **only
        while they are its only member**, which undoes a group nobody joined and
        can never take a group away from people in it. The requests waiting on
        it go with it.

        **Nobody deletes an official group**: it has no Owner, and its
        Administrator has no way to delete it (§7) — so every member asking is
        refused as a member who is not the Owner is."""

        self._refuse_unless_the_owner(by)
        if any(member != by for member in self.members):
            raise GroupHasOtherMembers()
        self._record_that(
            GroupDeleted(group_id=self.id, deleted_by=by, occurred_at=occurred_at)
        )

    def _refuse_unless_the_owner(self, answerer: UUID) -> None:
        """**Nobody but the Owner** deletes a group (#506) — and an official
        group has none, so nobody deletes one. Whether the person is in the
        group at all is the caller's to have asked first: a stranger is refused
        as the page refuses them, and this is the member's refusal."""

        if self.kind is not GroupKind.PLAYER or answerer != self.owner_id:
            raise NotTheGroupOwner()

    def _refuse_unless_it_answers(
        self, answerer: UUID, as_administrator: UUID | None
    ) -> None:
        """**Nobody but whoever runs the group** answers its Join requests
        (#505) or edits it (#506, #509): a player group's **Owner**, and an
        official group's **Administrator**, acting as that Administrator
        (``as_administrator``) — never as a player, whose account is refused
        here as any member is. That the Administrator is still active at the
        club is the administrator guard's, on the same request."""

        if self.kind is GroupKind.PLAYER:
            self._refuse_unless_the_owner(answerer)
            return
        if as_administrator is None or as_administrator != self.administrator_id:
            raise NotTheGroupOwner()

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, PlayerGroupCreated):
            self.id = event.group_id
            self.name = GroupName(event.name)
            self.home_club_id = event.home_club_id
            self.join_policy = JoinPolicy(event.join_policy)
            self.owner_id = event.owner_id
            self.code = GroupCode(event.code)
            self.members = {event.owner_id: event.occurred_at}
        elif isinstance(event, OfficialGroupCreated):
            self.id = event.group_id
            self.kind = GroupKind.OFFICIAL
            self.name = GroupName(event.name)
            self.home_club_id = event.home_club_id
            self.join_policy = JoinPolicy(event.join_policy)
            self.administrator_id = event.administrator_id
            self.whatsapp_size = WhatsAppSize(event.whatsapp_size)
            self.declared_sports = DeclaredSports.from_codes(event.sports)
            self.code = GroupCode(event.code)
        elif isinstance(event, WhatsAppSizeSet):
            self.whatsapp_size = WhatsAppSize(event.whatsapp_size)
        elif isinstance(event, SportsDeclared):
            self.declared_sports = DeclaredSports.from_codes(event.sports)
        elif isinstance(event, AdministratorAssigned):
            self.administrator_id = event.administrator_id
        elif isinstance(event, GroupJoined):
            self.members[event.player_id] = event.occurred_at
        elif isinstance(event, JoinRequested):
            self.waiting[event.player_id] = event.occurred_at
        elif isinstance(event, JoinRequestApproved):
            del self.waiting[event.player_id]
            self.members[event.player_id] = event.occurred_at
        elif isinstance(event, JoinRequestDeclined):
            del self.waiting[event.player_id]
        elif isinstance(event, GroupLeft):
            del self.members[event.player_id]
        elif isinstance(event, OwnershipPassed):
            self.owner_id = event.to_id
        elif isinstance(event, JoinPolicyChanged):
            self.join_policy = JoinPolicy(event.join_policy)
        elif isinstance(event, GroupRenamed):
            self.name = GroupName(event.name)
        elif isinstance(event, GroupDeleted):
            self.is_deleted = True
            self.members = {}
            self.waiting = {}
        else:
            raise TypeError(f"Unsupported group event {event!r}")
        self.version += 1

