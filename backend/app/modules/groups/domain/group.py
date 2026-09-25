"""The Group aggregate — event-sourced, one aggregate for both kinds.

``docs/adr/0183`` §1 rejected two aggregates: the kinds share the link, the
membership, the join policy and its requests, both searches and the whole page,
and two aggregates would be two copies of every shared rule. This build holds
the player kind only; the official kind arrives with #509 and will say so, rule
by rule, where it differs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.modules.groups.domain.errors import (
    GroupHasOtherMembers,
    JoinRequestNotFound,
    LoneOwnerCannotLeave,
    NotTheGroupOwner,
)
from app.modules.groups.domain.events import (
    GroupDeleted,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OwnershipPassed,
    PlayerGroupCreated,
)
from app.modules.groups.domain.value_objects import GroupCode, GroupName, JoinPolicy
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
    """

    id: UUID
    name: GroupName
    home_club_id: UUID
    join_policy: JoinPolicy
    owner_id: UUID
    code: GroupCode
    members: dict[UUID, datetime]
    waiting: dict[UUID, datetime] = field(default_factory=dict)
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

    def is_member(self, player_id: UUID) -> bool:
        return player_id in self.members

    def is_waiting(self, player_id: UUID) -> bool:
        return player_id in self.waiting

    def join(self, player_id: UUID, *, occurred_at: datetime) -> None:
        """A player taps *Join* or *Ask to join* (``docs/adr/0183`` §7) — one
        tap, and the policy decides what it was.

        Under *Anyone* they are a member at once. Under *People I approve* their
        tap is a **Join request**, waiting for the Owner. **Neither is recorded
        twice**: a member tapping again, or somebody asking again while their
        request waits, records nothing and is not refused — the tap asked for
        what they already have.
        """

        if self.is_member(player_id) or self.is_waiting(player_id):
            return
        if self.join_policy is JoinPolicy.PEOPLE_I_APPROVE:
            self._record_that(
                JoinRequested(
                    group_id=self.id, player_id=player_id, occurred_at=occurred_at
                )
            )
            return
        self._record_that(
            GroupJoined(group_id=self.id, player_id=player_id, occurred_at=occurred_at)
        )

    def approve(self, player_id: UUID, *, by: UUID, occurred_at: datetime) -> None:
        """The Owner approves a Join request, and the person is a member **at
        once** (``docs/adr/0183`` §7).

        Approving somebody already in changes nothing — a second tap, or a tap
        from a second phone, wanted them in and they are. Approving somebody
        with nothing waiting is refused: nobody is admitted who did not ask.
        """

        self._refuse_unless_the_owner(by)
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

    def decline(self, player_id: UUID, *, by: UUID, occurred_at: datetime) -> None:
        """The Owner declines a Join request, and it is gone **silently**: the
        person's relation is *none* again and they may ask again
        (``docs/adr/0183`` §7).

        Declining what is not waiting changes nothing — the tap wanted the
        request gone, and it is. It never removes a member: **nobody removes a
        Group member**, and a decline arriving after an approval finds nothing
        to decline.
        """

        self._refuse_unless_the_owner(by)
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

        if player_id == self.owner_id:
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

    def rename(self, name: GroupName, *, by: UUID, occurred_at: datetime) -> None:
        """The Owner renames the group, from *Edit group* (``docs/adr/0183`` §2).

        **Its link does not change** — the code is the group's identity and the
        name is not (§4). Saving the name it already has records nothing.
        """

        self._refuse_unless_the_owner(by)
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
        self, policy: JoinPolicy, *, by: UUID, occurred_at: datetime
    ) -> tuple[UUID, ...]:
        """The Owner changes who can join, from *Edit group*
        (``docs/adr/0183`` §7), and learns who it let in.

        **Switching to *Anyone* admits everybody waiting at once**, in the order
        they asked, because nobody should be left waiting under a rule that no
        longer applies. Saving the policy it already has records nothing.

        Returns everybody the switch admitted, in the order they asked — empty
        for every change but that one.
        """

        self._refuse_unless_the_owner(by)
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

    def delete(self, *, by: UUID, occurred_at: datetime) -> None:
        """The Owner taps *Delete the group* (``docs/adr/0183`` §7) — **only
        while they are its only member**, which undoes a group nobody joined and
        can never take a group away from people in it. The requests waiting on
        it go with it."""

        self._refuse_unless_the_owner(by)
        if any(member != by for member in self.members):
            raise GroupHasOtherMembers()
        self._record_that(
            GroupDeleted(group_id=self.id, deleted_by=by, occurred_at=occurred_at)
        )

    def _refuse_unless_the_owner(self, answerer: UUID) -> None:
        """**Nobody but the Owner** answers a Join request (#505), edits the
        group or deletes it (#506). Whether the person is in the group at all
        is the caller's to have asked first: a stranger is refused as the page
        refuses them, and this is the member's refusal."""

        if answerer != self.owner_id:
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
