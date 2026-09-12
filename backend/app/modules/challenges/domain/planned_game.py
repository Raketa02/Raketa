"""The one thing this context asks somebody else to **do** — three times over.

Every seam on ``domain/ports.py`` is a *read* about a fact this context owns or
can fold — the repository, the log queries and the four gates. This is the
exception, and it is in its own module for the reason ``matchmaking``'s
``MutualChallengeMinting`` is: it is a command, and the tables that describe
reads have nothing to say about one.

``settled_game.py`` and ``seatable_game.py`` beside it are the other seams that
left ``ports.py``, and for the neighbouring reason — they are reads, but about a
**game**, which is the one thing here this context does not know the shape of.
The three are one arrow (``challenges -> games``) written three times: this one
hands an arrangement over, hands a departure over and hands a withdrawal over,
one asks whether anything more will happen to what came of it, and one asks
whether its seats may still change.

**It fires at the instant a line-up completes, again at the instant somebody
leaves the game it became** (``docs/adr/0162``), **and again at the instant a
court that has been a game is withdrawn** (``docs/adr/0163``). The first
hand-over used to be the only one — *every seat accepted, nobody left to answer,
and the membership settled for good* — and the membership is no longer settled
for good: a player may leave a game that has not happened, the seat opens on
both records, and the **next** completed line-up hands over a re-seat of the same
game rather than the opening of another. Which of the two a completion is, is
the other side's to say: this context hands over the court and learns back an
id, or nothing. And a reopened court's exit is the withdraw, which reaches the
game: it is **called off**, the fourth end, in the withdrawal's own transaction.

**Inline, in the transaction of the act**, and not through the outbox.
``docs/adr/0003`` is this repository's convention for side effects and is right
nearly everywhere; it loses here twice. A subscriber would have to **re-derive
whether this accept completed the line-up** by reading this aggregate again from
outside — a second reader of this log and a second author of what *on* means —
when the use case that just folded it is holding the answer. And the player who
taps the last accept, or *leave*, would be told by a screen that cannot yet show
it, for however long a poller takes.

**This context still does not know what a game is.** It hands over an
arrangement in its own vocabulary — sides as their codes, players as ids — and
learns nothing back but an id.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport


@runtime_checkable
class PlannedGameHandover(Protocol):
    """*Everybody accepted — there is now a game they might play.* And:
    *somebody left — that seat on it is open.* And: *this court is withdrawn —
    the game it became is called off.*

    Signed by an adapter that calls the ``games`` commands, wired in the
    composition root with every other choice of implementation. The two contexts
    meet at two sentences and neither learns the other's aggregates.
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

        **An id is a game opened or a game re-seated, and ``None`` is an
        ordinary answer and never an error.** A game already standing whole for
        this challenge is the expected one: the accept path is idempotent under a
        retry, and there is exactly one game per arrangement. A game standing
        with a seat open is re-seated with this court, keeping its id and its
        ``planned_at``. A raise here would roll back somebody's acceptance,
        which is not the thing being refused.

        It does **not** commit. The hand-over and the accept that caused it are
        one transaction, and the boundary stays the use case's.
        """
        ...

    async def vacate_seat(
        self, *, challenge_id: UUID, player_id: UUID, occurred_at: Instant
    ) -> None:
        """This player has left the game this challenge became. **Their seat
        opens on it.**

        Called after the challenge has asked ``SeatableGameQuery`` whether the
        game's seats may still change, so what the other side refuses is its own
        half — a game that has happened, or never will — and a refusal there
        rolls the departure back with it. It does **not** commit.
        """
        ...

    async def call_off(
        self, *, challenge_id: UUID, by: UUID, occurred_at: Instant
    ) -> None:
        """This challenge has been withdrawn with a seat open, and it had become
        a game. **That game is called off.**

        Called only on a court that has been a game, after the aggregate has
        recorded the withdrawal and decided whose act it is — so ``by`` is the
        organiser, or a remaining player once the organiser has left, and it is
        the one record of the actor: ``ChallengeWithdrawn`` carries no player.
        The other side reads no moment guard for this; what it decides on its
        own is that **a game already ended by its clock stays the end it is**
        (``docs/adr/0163`` §6) — a ghost is not un-ghosted, and the withdraw
        still ends the challenge. It does **not** commit.
        """
        ...
