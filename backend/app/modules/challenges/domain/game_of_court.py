"""The fourth seam this context has onto a **game**: which game did this court
become?

``planned_game.py`` hands an arrangement, a departure and a call-off over;
``settled_game.py`` asks whether anything more will happen to the game that
came of it; ``seatable_game.py`` asks whether its seats may still change. This
asks the one thing the challenge read lacked (``docs/adr/0172`` §4): **which of
these courts stand for which game**, so that a Chats row and the leaver's sheet
can tell a court that has been a game from one that has not without a join on
the client.

**Read, not recorded.** The hand-over already learns the id back and discards
it; recording it would put a challenge event on the stream announcing what the
completing acceptance already says, with a foreign id on it — two places for
*has this court been a game*, one of them the fold's ``game_opened``. So the id
is asked of ``games`` at the read, on the arrow that already carries three
reads, and asked **only about the courts the fold says have been a game**: a
list with none costs nothing, and ``null`` is the fold's answer rather than the
other context's.

**And one second question, the reader's own** (``docs/adr/0173``): which of
these courts has *this reader* cleared? A called-off court is one fact drawn on
two of the reader's lists — the row on Chats and the card on Now — and the
dismissal ADR-0172 §5 recorded on the game is the act that clears it. The row
goes with the card because they are one court, so the inbox subtracts its reader
off the same set the rail does, and asks about it here rather than folding a
second copy. It is a question about the reader and never about the game: what
crosses is *yes or no for you*, not who else has cleared it, and not the game's
standing, its court or its ending, which the challenge's own fold answers.
"""

from __future__ import annotations

from typing import Collection, Mapping, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class GameOfCourtQuery(Protocol):
    """*Which of these courts have a game, and which game?*

    Signed by an adapter that reads the ``games`` context, wired in the
    composition root with every other choice of implementation.
    """

    async def games_of(self, challenge_ids: Collection[UUID]) -> Mapping[UUID, UUID]:
        """The game standing for each of these challenges, keyed by challenge.

        **Keyed by challenge id in both directions**, on ``SettledGameQuery``'s
        argument: the caller's question is about a court it minted and handed
        over, and the answer comes back in the same currency. **Bulk, and the
        shape is what is promised rather than the read count** — a list of
        twenty been-a-game courts is one question, and what an implementation
        does behind it is its own business. A caller may never loop instead.

        **An id with no game behind it is simply absent.** The caller asks only
        about courts whose fold says a line-up completed, so an absence there
        is a broken store rather than a state, and it is the caller's to refuse.
        A read that cannot complete raises, and the read that holds it decides
        what that costs.
        """
        ...

    async def dismissed_of(
        self, challenge_ids: Collection[UUID], *, by: UUID
    ) -> frozenset[UUID]:
        """Which of these courts' games this player has dismissed, keyed by
        challenge id — the reader's own act, read for the reader's own inbox
        (``docs/adr/0173``).

        **Bulk, keyed by challenge, and about one person**, on ``games_of``'s
        argument for the first two: the caller's question is about courts it
        minted, and the answer comes back in the same currency. About one person
        because a dismissal is *their act, and nobody else's fact*
        (``docs/adr/0172`` §5): the inbox is one reader's, and who else has
        cleared a card is nothing it may act on. A court with no game behind it,
        or whose game this player has not cleared, is simply absent; the caller
        asks only about courts whose fold says ``CALLED_OFF``, the one standing
        a dismissal is admitted on, so a list with none costs nothing.
        """
        ...


__all__ = ["GameOfCourtQuery"]
