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

from app.modules.groups.domain.errors import GroupNeedsApproval
from app.modules.groups.domain.events import GroupJoined, PlayerGroupCreated
from app.modules.groups.domain.value_objects import GroupCode, GroupName, JoinPolicy
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Group:
    """One group, as its stream leaves it.

    ``members`` maps each Group member to the instant they joined, in the order
    they joined — the Owner first, because creating the group is joining it.
    """

    id: UUID
    name: GroupName
    home_club_id: UUID
    join_policy: JoinPolicy
    owner_id: UUID
    code: GroupCode
    members: dict[UUID, datetime]
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

    def join(self, player_id: UUID, *, occurred_at: datetime) -> None:
        """A player taps *Join* (``docs/adr/0183`` §7).

        **Joining twice changes nothing**: a member joining again records
        nothing and is not refused, whatever the policy — the tap asked to be
        in, and they are. Anyone else is admitted at once under *Anyone*, and
        under *People I approve* is refused until their tap can become a Join
        request (#505).
        """

        if self.is_member(player_id):
            return
        if self.join_policy is JoinPolicy.PEOPLE_I_APPROVE:
            raise GroupNeedsApproval()
        self._record_that(
            GroupJoined(group_id=self.id, player_id=player_id, occurred_at=occurred_at)
        )

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
        else:
            raise TypeError(f"Unsupported group event {event!r}")
        self.version += 1
