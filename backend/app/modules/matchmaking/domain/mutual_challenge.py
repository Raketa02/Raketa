"""The one thing the matcher asks somebody else to **do**.

Every other outward seam in this module is a *read*: ``domain/ports.py`` holds
the five consumer-driven contracts, each answering a question about a fact the
matcher does not own. This is the exception, and it is here rather than there for
three reasons that are all the same reason.

**It is a command, and ``FAIL_POSTURE`` has nothing to say about one.** That
table has two values — *a gate that cannot be evaluated excludes, a term that
cannot be evaluated stands down* — and neither describes an act somebody else
performs. ``MATCHER_DEMANDS`` is exhaustive over it by construction, and the
suite in ``tests/demands/`` builds each implementation over a session and asserts
what it *answers*; there is nothing there for a write to satisfy.

**It exists so the import arrow can stay one-directional.** The arrow runs
``matchmaking -> challenges``, so the matcher could simply call the other
context's use case. It does not, because *what* opens a challenge is a choice
about wiring and belongs in the composition root with every other choice of
implementation — and because a deck deal reaching directly into an aggregate
factory would put a second author on *what a challenge born of a mutual yes is*.

**The alternative was the outbox, and it loses on the promise.** ``docs/adr/0003``
makes the outbox this repository's convention for side effects, and it is the
right one nearly everywhere. Here the product says *that player has left the deck
for good, because you now have an open game together* — and with a poller in the
middle that sentence is false for however long the worker takes. A promise about
what a player will never see again should not depend on a poller. So the mint is
**inline, in the same transaction as the yes**, and the two commit together or
neither does.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Sport


@runtime_checkable
class MutualChallengeMinting(Protocol):
    """*These two just said yes to each other — open their game.*

    Signed by an adapter in ``matchmaking/infrastructure/`` that calls the
    ``challenges`` command. The matcher never learns what a Challenge is, and
    ``challenges`` never learns that a matcher exists.
    """

    async def open_from_mutual_interest(
        self, *, sport: Sport, player_id: UUID, other_player_id: UUID
    ) -> UUID | None:
        """**The game these two have**, or ``None`` when there is none to name.

        Not *what this call minted* (``docs/adr/0154`` §1). A repeat tap on a
        pair whose mutual already minted a game that is not finished with is
        answered with **that** game: the other context is holding them on it and
        has its id in hand, and throwing that away is what left a pair told *you
        both said yes* with nothing behind it.

        **``None`` is an ordinary answer and never an error**, and it covers two
        unrelated things on purpose (§3). The other context re-verifies the same
        safety gates the send does — a *Let's play* may cite a search from a
        month ago, because a search record never expires — and it refuses by
        minting nothing; and a pair with a game still being **arranged**, a send
        or this mutual's own half-built doubles court, is refused too. Either
        way there is nobody to refuse to: the yes was the player's own act and
        stands regardless, and a raise here would roll it back.

        **The fold is why this may be published at all.** An absence that meant
        only *a gate refused* would say something about the other person that
        ``docs/adr/0095`` guarantees leaves no trace anywhere in any response. A
        caller that narrowed it — by giving the still-being-arranged case an id,
        which is one read away — would have to stop publishing it.

        ``player_id`` is the one whose yes arrived **second**. They hold the
        court's first seat, which is what the other context means by *organiser*
        and is not a claim that either of them proposed anything.

        It does **not** commit. The mint and the yes are one transaction, and the
        boundary is the use case's.
        """
        ...
