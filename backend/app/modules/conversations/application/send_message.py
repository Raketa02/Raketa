"""*Say something in the room.*

Three things happen here and each has a record behind it.

**Membership is the gate**, and a non-member gets ``conversation_not_found`` —
the same code a room that does not exist gets, so this route cannot be used to
find out whether two people are arranging a game.

**A hold refuses the send and refuses no read** (``docs/adr/0148`` §9). The hold's
own argument is about **reach**, and a message is reach; but a hold must not erase
an arrangement other people are already inside, so they keep reading the room and
reaching the people in it is what stops.

**A repeat records nothing and answers the same message and the same ``seq``.**
The aggregate owns that (``docs/adr/0148`` §5) because ``client_message_id`` is
folded from the stream, not looked up in a table beside it.

**The row is locked before the sequence is minted.** ``load_for_append`` is the
read that takes it, which is what makes ``last_seq + 1`` gapless under two people
typing at once (``docs/adr/0147`` §2).
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import SendMessageCommand
from app.modules.conversations.domain.entries import Message
from app.modules.conversations.domain.ports import (
    AccountHoldQuery,
    ConversationRepository,
)
from app.shared.domain.errors import AccountHeld


@final
class SendMessage:
    """One player's own words, into a room they are in."""

    def __init__(
        self,
        *,
        rooms: ARoomOfYours,
        conversations: ConversationRepository,
        holds: AccountHoldQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._rooms = rooms
        self._conversations = conversations
        self._holds = holds
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SendMessageCommand) -> Message:
        room = (
            await self._rooms.to_append(command.conversation_id, command.author_id)
        ).conversation
        # **After membership, and never before it.** A stranger is told there is
        # no such room; telling them their account is held would be an answer
        # about a room they may not know exists.
        if command.author_id in await self._holds.held_among((command.author_id,)):
            raise AccountHeld("This account is under a live hold.")

        message = room.say(
            author_id=command.author_id,
            client_message_id=command.client_message_id,
            text=command.text,
            occurred_at=self._clock.now(),
        )
        # A repeat pulls no events, so the save is a no-op and the commit closes
        # a transaction that wrote nothing — which is what *recording nothing*
        # means here rather than a branch this use case takes.
        await self._conversations.save(room)
        await self._uow.commit()
        return message
