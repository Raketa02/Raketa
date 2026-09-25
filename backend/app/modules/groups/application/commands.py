"""What a caller asks the Groups context for, in the primitives it asked in.

Plain values rather than value objects, for the reason ``RegisterUserCommand``
gives: a command is what a caller *asked for*, and the boundary must be able to
express the answer that gets refused, or the refusal has nowhere to happen.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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
