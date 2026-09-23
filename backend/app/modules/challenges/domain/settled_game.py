"""The other half of the sentence ``planned_game.py`` starts.

That module is this context's one outward **command** — *everybody accepted,
there is now a game they might play* — and this is the read that finishes it:
*is anything more going to happen to the game that came of it?* Both run along
the one arrow ``challenges -> games``, which is what made ``docs/adr/0152``
affordable: the port, the direction, the adapter pattern and the use case
holding them all existed already, so releasing the mutual mint's guard cost a
second method on a seam rather than a second seam.

**It is here rather than on ``ports.py`` because it is not this context's
question.** Everything on that table is a fact about challenges, seats or
people; this one is a fact about a *game*, which this context still does not
know the shape of. What crosses is one word — *settled* — and a challenge id it
handed over in the first place.

**Only the mutual mint reads it, and the send deliberately does not**
(``docs/adr/0152`` §5). Two people with an unplayed game may still send each
other a court: a send is somebody choosing a court deliberately, and holding
them on a game nobody played would put back the block
[#343](https://github.com/Raketa02/Raketa/issues/343) argued out one record ago.
The refusal is recorded here as well as there, because the next reader finds a
``challenges -> games`` port and assumes nobody thought to use it on the send.
"""

from __future__ import annotations

from typing import Collection, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant


@runtime_checkable
class SettledGameQuery(Protocol):
    """*Which of these arrangements are finished with?*

    Signed by an adapter that reads the ``games`` context, wired in the
    composition root with every other choice of implementation.
    """

    async def settled_among(
        self, challenge_ids: Collection[UUID], *, now: Instant
    ) -> frozenset[UUID]:
        """Which of these challenges produced a game that has **settled**.

        **Keyed by challenge id in both directions, so that ``games`` never
        learns what a pair is.** The caller's question is about two people; the
        id it asks with is the one it minted and handed over, and the answer
        comes back in the same currency. A pair-shaped read here would put the
        one-open-challenge-per-pair vocabulary inside a context that has no
        opinion about pairs.

        **Bulk, and the shape is what is promised rather than the read count.**
        A pair holds a second mutual-born challenge the moment the first has
        settled and another has been minted, so a caller with two ids has to be
        able to ask once — which is the shape every set read in this codebase
        takes. What an implementation does behind it is its own business, and
        today's adapter walks the ids through the single join ``games`` offers;
        the day that becomes one statement, no caller changes. **A caller may
        never loop instead**, because that is the half a port cannot take back.

        *Settled* is the ``games`` word for *nothing more will happen to this
        game*, and a **ghost counts**: an entry window that closed with nobody
        saying the game happened is as finished as a confirmed score. Reading it
        as *played* would hold two people on the strength of an evening that
        never occurred.

        **An id with no game behind it is simply absent**, exactly like one whose
        game is still live — there is nothing here for a caller to tell apart,
        because both mean *do not release them on this one*.

        The clock is the caller's, for the reason ``OpenPlannedGame``'s is: a
        standing is a fold against an instant, and the mint reads every one of
        its questions against the same one.

        **What it may not do is answer emptily when it could not tell.** A read
        that cannot complete raises, and the mint turns that into a refusal —
        which is the opposite of ``OpenChallengeQuery``'s rule and is written on
        both (``docs/adr/0152`` §6).
        """
        ...


__all__ = ["SettledGameQuery"]
