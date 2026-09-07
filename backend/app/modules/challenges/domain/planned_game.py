"""The one thing this context asks somebody else to **do**.

Every seam on ``domain/ports.py`` is a *read* about a fact this context owns or
can fold — the repository, the log queries and the four gates. This is the
exception, and it is in its own module for the reason ``matchmaking``'s
``MutualChallengeMinting`` is: it is a command, and the tables that describe
reads have nothing to say about one.

``settled_game.py`` beside it is the other seam that left ``ports.py``, and for
the neighbouring reason — it is a read, but about a **game**, which is the one
thing here this context does not know the shape of. The two are one arrow
(``challenges -> games``) written twice: this one hands an arrangement over, and
that one asks whether anything more will happen to what came of it.

**It fires exactly once per challenge, at the instant the line-up completes.**
That is the only moment the arrangement is knowable: every seat accepted, nobody
left to answer, and the membership settled for good. Before it there is nothing
to record; after it the sides may still be swapped, but who played may not change.

**Inline, in the transaction of the accept**, and not through the outbox.
``docs/adr/0003`` is this repository's convention for side effects and is right
nearly everywhere; it loses here twice. A subscriber would have to **re-derive
whether this accept completed the line-up** by reading this aggregate again from
outside — a second reader of this log and a second author of what *on* means —
when the use case that just folded it is holding the answer. And the player who
taps the last accept would be told the game is on by a screen that cannot yet
show it, for however long a poller takes.

**This context still does not know what a game is.** It hands over an
arrangement in its own vocabulary — sides as their codes, players as ids — and
learns nothing back but an id.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport


@runtime_checkable
class PlannedGameOpening(Protocol):
    """*Everybody accepted — there is now a game they might play.*

    Signed by an adapter that calls the ``games`` command, wired in the
    composition root with every other choice of implementation. The two contexts
    meet at one sentence and neither learns the other's aggregates.
    """

    async def open_planned_game(
        self,
        *,
        challenge_id: UUID,
        sport: Sport,
        counted: bool,
        window: str | None,
        line_up: Sequence[tuple[str, UUID]],
        occurred_at: Instant,
    ) -> UUID | None:
        """The game now standing for this challenge, or ``None``.

        ``line_up`` is the court in its fixed order — every seat's side code and
        its occupant. The side codes are ``"A"`` and ``"B"``, spelled identically
        in both contexts on purpose, so the mapping at this seam is identity
        rather than a table.

        ``counted`` rather than a kind, because that is the whole of what the
        other side needs and this context has no vocabulary for an evening that
        is or is not evidence.

        **``None`` is an ordinary answer and never an error.** A game already
        opened for this challenge is the expected one: the accept path is
        idempotent under a retry, and there is exactly one game per arrangement.
        A raise here would roll back somebody's acceptance, which is not the
        thing being refused.

        It does **not** commit. The opening and the accept that caused it are one
        transaction, and the boundary stays the use case's.
        """
        ...
