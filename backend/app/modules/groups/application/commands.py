"""What a caller asks the Groups context for, in the primitives it asked in.

Plain values rather than value objects, for the reason ``RegisterUserCommand``
gives: a command is what a caller *asked for*, and the boundary must be able to
express the answer that gets refused, or the refusal has nowhere to happen.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.kernel import Sport
from app.modules.groups.domain.value_objects import JoinPolicy


@dataclass(frozen=True)
class CreatePlayerGroupCommand:
    """A player creates a group. ``creator_id`` comes from the session, never
    from the body."""

    creator_id: UUID
    name: str
    home_club_id: UUID
    join_policy: JoinPolicy


@dataclass(frozen=True)
class JoinGroupCommand:
    group_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class SearchHomeClubsCommand:
    """What the player typed into the home club field, and which page of the
    answer they have scrolled to — from one."""

    reader_id: UUID
    text: str
    page: int


@dataclass(frozen=True)
class SearchGroupsToJoinCommand:
    """What the player typed or pasted into *Join a group*'s one field, and
    which page of the answer they have scrolled to — from one."""

    reader_id: UUID
    text: str
    page: int


@dataclass(frozen=True)
class AnswerJoinRequestCommand:
    """Somebody approves or declines a Join request — the Owner, or a refusal.
    ``answered_by`` comes from the session, never from the body; ``player_id``
    is who asked."""

    group_id: UUID
    player_id: UUID
    answered_by: UUID


@dataclass(frozen=True)
class LeaveGroupCommand:
    """A member taps *Leave the group*. ``player_id`` comes from the session."""

    group_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class DeleteGroupCommand:
    """The Owner taps *Delete the group*. ``deleted_by`` comes from the
    session."""

    group_id: UUID
    deleted_by: UUID


@dataclass(frozen=True)
class EditGroupCommand:
    """The Owner saves *Edit group*: the name and who can join, both as the
    form holds them. ``editor_id`` comes from the session."""

    group_id: UUID
    editor_id: UUID
    name: str
    join_policy: JoinPolicy


@dataclass(frozen=True)
class Administering:
    """Somebody acting as an Administrator — **the administratorship the
    administrator guard just read as active** at the club the path names
    (``docs/adr/0184`` §7), and the account behind it. Every field comes from
    the guard, never from a body."""

    club_id: UUID
    administrator_id: UUID
    account_id: UUID


@dataclass(frozen=True)
class CreateOfficialGroupCommand:
    """An Administrator creates an official group for their club: its name, who
    can join, the size of the WhatsApp group it mirrors and the sports it plays
    (``docs/adr/0183`` §3). The home club is theirs, and not asked."""

    administering: Administering
    name: str
    join_policy: JoinPolicy
    whatsapp_size: int
    sports: Sequence[Sport]


@dataclass(frozen=True)
class ChangeOfficialGroupSettingsCommand:
    """Its Administrator saves an official group's settings — all four, as the
    settings screen holds them (``docs/adr/0184`` §8)."""

    administering: Administering
    group_id: UUID
    name: str
    join_policy: JoinPolicy
    whatsapp_size: int
    sports: Sequence[Sport]


@dataclass(frozen=True)
class AnswerAsAdministratorCommand:
    """An Administrator approves or declines a Join request waiting on an
    official group they run. ``player_id`` is who asked."""

    administering: Administering
    group_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class NoteHandoversSeenCommand:
    """The Administrator was told the club handed them these groups
    (``docs/adr/0192`` §1) — the sheet's groups, closed or followed."""

    administering: Administering
    group_ids: Sequence[UUID]


@dataclass(frozen=True)
class HandOverCommand:
    """The club hands one of its official groups to one of its Administrators.
    ``club_id`` and ``assigned_by`` come from the club's session, never from
    the body; ``administrator_id`` is who they chose."""

    club_id: UUID
    assigned_by: UUID
    group_id: UUID
    administrator_id: UUID


@dataclass(frozen=True)
class AnswerAsClubCommand:
    """The club approves or declines a Join request waiting on one of its
    official groups (``docs/adr/0191`` §1). ``club_id`` and ``answered_by``
    come from the club's session; ``player_id`` is who asked."""

    club_id: UUID
    answered_by: UUID
    group_id: UUID
    player_id: UUID
