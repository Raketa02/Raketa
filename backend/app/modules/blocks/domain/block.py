"""The Block aggregate — event-sourced, keyed by the **ordered** pair.

One stream per ``(blocker, blocked)`` (``docs/adr/0095`` §1), rebuilt by folding
it. The whole state is one boolean — *is this block standing* — and that is not
an argument for a table: what is worth keeping is the **sequence**. *Blocked,
unblocked, blocked again* is safety evidence, and it is the one thing in this
design a human would miss if it silently vanished (``docs/adr/0095``, Context).

**Directed record, symmetric effect.** This aggregate knows only its own
direction. That ``A → B`` standing also removes A from B's view is the *reader's*
rule — ``BlockQuery`` asks about both streams — and deliberately not a fact this
object holds, because an aggregate that tried to hold both directions would be
one stream with two versions contending on it, and lifting one side would have to
decide what the other side meant.

**Idempotent, in the shape of ``users``' ``disable()``.** Blocking somebody
already blocked appends nothing: a second block is not a new fact, and a stream
that grew a row for it would be recording that a player did not do anything.
Unblocking somebody who is not blocked is the same no-op, and it is what lets the
route answer identically either way — a distinct answer for *there was nothing to
lift* would be the response shape telling one player about the other's state.

**Blocking yourself raises** rather than no-ops, which is the one asymmetry in
the paragraph above and the reason it is stated separately: a no-op would accept
a request whose only possible meaning is a caller's bug.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, instant
from app.modules.blocks.domain.errors import CannotBlockYourself
from app.modules.blocks.domain.events import PlayerBlocked, PlayerUnblocked
from app.modules.blocks.domain.ids import block_id
from app.modules.blocks.domain.surface import BlockSurface
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Block:
    """One player's block of another, in one direction, as its stream leaves it."""

    blocker_id: UUID
    blocked_id: UUID
    #: Whether the block is standing *right now*. The history of it is the
    #: stream; nothing accumulates a list here.
    is_standing: bool
    #: Where the **standing** block was made from, or where the last one was if
    #: it has since been lifted. Context, never a thing a rule reads.
    surface: BlockSurface
    updated_at: Instant
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id, derived from the ordered pair rather than carried.

        The pair **is** the identity (``ids.py``), so the id is a function of it
        and there is nothing to store. An id on the event would be a second copy
        of one fact and a second place for it to disagree — and it is the copy
        that would be believed, because it is the one the row holds.
        """

        return block_id(self.blocker_id, self.blocked_id)

    def counterpart_of(self, player_id: UUID) -> UUID:
        """The other side of this pair, whichever side `player_id` is on.

        Here rather than at the reader, because *who is the other one* is a
        question about a Block and the answer needs both of its fields. It is
        what an exclusion set is built from, and putting the conditional at the
        call site is how one reader eventually gets it the wrong way round and
        excludes the searcher from their own search.

        Raises for somebody who is not in the pair: an id that reached this from
        a stream it does not appear in is a caller bug, and returning either side
        would hide it behind a plausible answer.
        """

        if player_id == self.blocker_id:
            return self.blocked_id
        if player_id == self.blocked_id:
            return self.blocker_id
        raise ValueError(f"{player_id} is not a side of this block")

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Block":
        block = cls._empty()
        for event in events:
            block._apply(event)
        return block

    @classmethod
    def _empty(cls) -> "Block":
        block = cls.__new__(cls)
        block.version = 0
        block.is_standing = False
        block._events = EventRecorder()
        return block

    @classmethod
    def first_blocked(
        cls,
        *,
        blocker_id: UUID,
        blocked_id: UUID,
        surface: BlockSurface,
        occurred_at: Instant,
    ) -> "Block":
        """Open the stream for a pair that has never been blocked this way round.

        The self-block refusal is here rather than only in the use case because
        it is a rule about what a Block *is*, and a second write path — a seed
        run, a later admin tool — must not be able to route around it.

        Two of these racing compute the same stream id and collide on version 1,
        and the store rejects the loser (``ids.py``).
        """

        _refuse_self_block(blocker_id, blocked_id)
        block = cls._empty()
        block._record_that(
            _blocked(
                blocker_id=blocker_id,
                blocked_id=blocked_id,
                surface=surface,
                occurred_at=occurred_at,
            )
        )
        return block

    def block(self, *, surface: BlockSurface, occurred_at: Instant) -> None:
        """Re-block after an unblock. **A no-op while the block is standing.**

        The surface is deliberately not part of that comparison, for the reason
        it is not part of a re-declared Play intent's: *the same decision, made
        again, from a different screen* is not a new fact about these two people.
        """

        if self.is_standing:
            return
        self._record_that(
            _blocked(
                blocker_id=self.blocker_id,
                blocked_id=self.blocked_id,
                surface=surface,
                occurred_at=occurred_at,
            )
        )

    def unblock(self, *, occurred_at: Instant) -> None:
        """Lift this block. **A no-op when it is not standing.**

        It lifts **this direction only.** If the other party has blocked back,
        their stream is untouched and they stay invisible to each other — which
        is what the directed record buys and why neither party can discover which
        way it went.
        """

        if not self.is_standing:
            return
        self._record_that(
            PlayerUnblocked(
                blocker_id=self.blocker_id,
                blocked_id=self.blocked_id,
                occurred_at=occurred_at,
            )
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, PlayerBlocked):
            self.blocker_id = event.blocker_id
            self.blocked_id = event.blocked_id
            self.surface = BlockSurface(event.surface)
            self.is_standing = True
            self._touch(event.occurred_at)
            return
        if isinstance(event, PlayerUnblocked):
            self.blocker_id = event.blocker_id
            self.blocked_id = event.blocked_id
            self.is_standing = False
            self._touch(event.occurred_at)
            return
        raise TypeError(f"Unsupported block event {event!r}")

    def _touch(self, occurred_at: datetime) -> None:
        self.updated_at = instant(occurred_at)
        self.version += 1


def _blocked(
    *,
    blocker_id: UUID,
    blocked_id: UUID,
    surface: BlockSurface,
    occurred_at: Instant,
) -> PlayerBlocked:
    """The one place a ``PlayerBlocked`` is constructed.

    Opening the stream and re-blocking after a lift record the *same* fact, and
    the two call sites above differ only in where the pair comes from. One
    constructor is what keeps the surface's ``.value`` conversion from being
    remembered twice.
    """

    return PlayerBlocked(
        blocker_id=blocker_id,
        blocked_id=blocked_id,
        surface=surface.value,
        occurred_at=occurred_at,
    )


def _refuse_self_block(blocker_id: UUID, blocked_id: UUID) -> None:
    if blocker_id == blocked_id:
        raise CannotBlockYourself()
