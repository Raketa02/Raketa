"""What a caller asks this context for. **Four, and every one carries a reader.**

Membership is the gate on every route, so the reader is not context a use case
picks up from somewhere — it is an argument, and a command with no reader on it
would be a route that could be called for somebody else.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReadConversationsCommand:
    """Every room this player is a member of."""

    reader_id: UUID


@dataclass(frozen=True, slots=True)
class ReadConversationCommand:
    """One room's header and its newest page, in one fold."""

    conversation_id: UUID
    reader_id: UUID


@dataclass(frozen=True, slots=True)
class ReadEntriesCommand:
    """One page backward, by a cursor over ``seq``.

    ``before_seq`` is **exclusive**, and ``None`` asks for the newest page — the
    same code path serves history and catch-up, which is the property
    ``docs/adr/0147`` bought by making the cursor a sequence rather than an
    offset.
    """

    conversation_id: UUID
    reader_id: UUID
    before_seq: int | None
    limit: int


@dataclass(frozen=True, slots=True)
class SendMessageCommand:
    """One player's own words.

    ``client_message_id`` is the client's, in the body rather than a header,
    because it does two jobs (``docs/adr/0148`` §5).
    """

    conversation_id: UUID
    author_id: UUID
    client_message_id: UUID
    text: str
