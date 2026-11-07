"""What a caller asks this context to do. Each command names the acting player
explicitly — the boundary is where an identity comes from a token, and a seed
run drives the same use case with an id of its own."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Sport
from app.modules.friends.domain.friendship import Where


@dataclass(frozen=True, slots=True)
class AskCommand:
    """*Be my friend* — and where it was asked."""

    requester_id: UUID
    addressee_id: UUID
    where: Where


@dataclass(frozen=True, slots=True)
class AnswerCommand:
    """The reader answers the request ``requester_id`` made of them: accept it,
    or set it aside."""

    reader_id: UUID
    requester_id: UUID


@dataclass(frozen=True, slots=True)
class TakeBackCommand:
    """The player takes back what stands between them and ``other_id``: their
    own request (cancel), or the friendship (remove)."""

    player_id: UUID
    other_id: UUID


@dataclass(frozen=True, slots=True)
class AskForALevelCommand:
    """**Ask for a level** (#749): the asker asks ``friend_id`` to get a level in
    ``sport``, from the picker of ``group_id`` — one of the asker's groups,
    where the answer opens."""

    asker_id: UUID
    friend_id: UUID
    sport: Sport
    group_id: UUID


@dataclass(frozen=True, slots=True)
class SetAsideTheAsksCommand:
    """**Not now** on Home's ask card (#764): the reader sets aside every ask
    for a level in ``sport`` that their Home lists now."""

    reader_id: UUID
    sport: Sport
