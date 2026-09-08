"""What every act on one room shares: **finding it, and finding it is yours.**

Three use cases needed the identical five lines — load, refuse if absent, derive
membership, refuse if the reader is not in it — and the third copy is where a
refusal quietly becomes two different refusals.

**One refusal for two cases.** No such room, and a room that is not yours, answer
identically. Separating them would tell a caller whether a stranger's
conversation id is real, one probe at a time — ``challenge_not_found``'s argument
verbatim (``docs/adr/0148`` §9), and the reason there is no 403 anywhere here.

**Two doors, and the difference is the lock.** ``to_read`` serves a response;
``to_append`` takes the conversation row ``FOR UPDATE`` first, because that is
where a gapless sequence is minted (``docs/adr/0147`` §2). Two methods rather
than a flag, because a caller that forgot the flag would mint a duplicate
sequence number under load and nothing would notice until two people saw one
bubble twice.

**Membership travels back with the room**, because the fold has already been paid
for: the detail read draws the members it just gated on, and asking twice would
be two answers to *who is in this* against one instant.

It is a collaborator rather than a base class — unlike ``challenges``' own
``AChallengeOfYours``, whose four collaborators are the same four for every act.
Here they are not: a send needs a hold query and a unit of work, a page needs
neither, and a header needs the faces. What the three share is exactly this, and
nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.modules.conversations.application.membership import Membership
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.errors import ConversationNotFound
from app.modules.conversations.domain.ports import ConversationRepository


@final
@dataclass(frozen=True, slots=True)
class ARoom:
    """One room and who is in it, folded once."""

    conversation: Conversation
    members: frozenset[UUID]


@final
class ARoomOfYours:
    """One room, loaded for somebody who is in it."""

    def __init__(
        self, *, conversations: ConversationRepository, membership: Membership
    ) -> None:
        self._conversations = conversations
        self._membership = membership

    async def to_read(self, conversation_id: UUID, reader_id: UUID) -> ARoom:
        return await self._yours(
            await self._conversations.load(conversation_id), reader_id
        )

    async def to_append(self, conversation_id: UUID, reader_id: UUID) -> ARoom:
        """The same room, with its row locked for a sequence to be minted."""

        return await self._yours(
            await self._conversations.load_for_append(conversation_id), reader_id
        )

    async def _yours(self, room: Conversation | None, reader_id: UUID) -> ARoom:
        if room is None:
            raise ConversationNotFound()
        members = await self._membership.of_one(room)
        if reader_id not in members:
            raise ConversationNotFound()
        return ARoom(conversation=room, members=members)
