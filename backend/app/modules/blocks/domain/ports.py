"""The two seams this context is built on: one to write a block, one to read one.

They are here rather than in ``app/application/ports/`` because both are the
Blocks context's own. ``BlockRepository`` is the **aggregate repository** kind —
how a use case reaches an event-sourced ``Block`` without knowing that it is
event-sourced, owning the aggregate-type name, the replay and the
optimistic-concurrency bookkeeping (``docs/adr/0018``). ``BlockQuery`` is the read
kind, and it is the one every other context is going to hold.

**One ``BlockQuery``, and every surface that shows one player to another consults
it** (``docs/adr/0095`` §7). Two questions, because ADR-0095 §4 enforces a block
in two places and they ask different things:

- **Generation**, building the searcher's exclusion list — *whom must this
  player never be shown* — ``exclusions_for``.
- **Disposal**, re-verifying a row before the response leaves — *are these two
  blocked, either way round* — ``blocked_between``.

Two methods rather than one, because the two reads have different shapes and
collapsing them would make one of them wrong. The exclusion set is **one bounded
read keyed on the searcher**, resolved once at request entry and carried in the
``SearchContext`` — the index holds no block data at all (``docs/adr/0111``), so
this is where a search learns it. The pairwise question is **two keyed reads and
no scan**, because the pair determines both stream ids; it is what an
asynchronous surface — a deck card, a standing-search notification, a read-back
of a stored search — asks about a single row it is about to render.

**Both fail closed, and that is a promise about the port rather than a hope about
its callers** (``docs/adr/0095`` §5):

> A term that cannot be evaluated stands down. A gate that cannot be evaluated
> excludes.

An implementation that cannot answer **raises ``BlockStateUnavailable``**. It may
never return an empty set or a ``False`` to mean *could not tell*: those are the
answers *nobody is blocked* and *these two are fine*, and a caller cannot tell
them from the truth. The failure is loud on purpose — it is the sentence that
stops somebody later "fixing" a flaky query by defaulting it to empty, and it is
what makes ADR-0095's *the search refuses and returns unavailable* the path of
least resistance rather than a discipline.

**Neither method distinguishes the two directions, and neither ever will.** The
record is directed so that an unblock is unambiguous; the *effect* is symmetric,
so a reader asking *may these two see each other* must never be handed the half
that would let it answer *which way round*. Neither party can discover that, and
the port is where that stays true.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.modules.blocks.domain.block import Block


@runtime_checkable
class BlockRepository(Protocol):
    """Loads and saves ``Block`` aggregates.

    Keyed on the **ordered pair**, because the stream is: there is no block id to
    pass, and a caller cannot ask this port a question that is not scoped to one
    direction between two people. That is the same hazard-closing shape
    ``PlayIntentDeclarationRepository`` has for ``(player, sport)``.
    """

    async def load(self, *, blocker_id: UUID, blocked_id: UUID) -> Block | None:
        """This direction's stream, replayed, or nothing.

        ``None`` rather than a raise: *these two have no history this way round*
        is the ordinary state of every pair on the platform, and it is what tells
        a caller to open the stream rather than append to it. It is **not** the
        same as a block that has been lifted — that one has a stream, a version
        and a sequence worth keeping — and no caller may collapse the two.
        """
        ...

    async def save(self, block: Block) -> None:
        """Append the aggregate's pending events and publish them.

        Appends and publishes; it does **not** commit, for the reason no
        repository in this codebase does — the transaction boundary is a decision
        about the *command*.

        A no-op when nothing is pending, which is what lets an idempotent block
        or a lift of a block that was not standing be saved without growing the
        stream.
        """
        ...


@runtime_checkable
class BlockQuery(Protocol):
    """*Is either of these two blocked by the other* — the one place it is asked.

    Read-only, and it answers about live state every time. There is no cache and
    no projection behind it by decision, not by omission: ADR-0095 §4 dropped the
    advisory copy the input document proposed, because a block is binary and
    there is nothing for a ranker to lower.
    """

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        """Every player this one must not be shown, **in either direction**.

        The union of *whom they have blocked* and *who has blocked them*, as one
        flat set — the searcher's live block set, resolved at request time and
        carried into generation as an exclusion list. It is deliberately not two
        sets: nothing downstream may branch on which side a block came from, and
        the cheapest way to keep that true is to hand it an answer that cannot.

        Tens of rows, not a scan. Raises ``BlockStateUnavailable`` rather than
        answering with an empty set it cannot stand behind.
        """
        ...

    async def blocked_between(self, first: UUID, second: UUID) -> bool:
        """Whether a standing block sits between these two, either way round.

        Symmetric in its arguments — swapping them cannot change the answer —
        which is what makes it safe for a caller to ask without knowing, or
        having to decide, whose row it is rendering.

        Raises ``BlockStateUnavailable`` rather than answering ``False`` it
        cannot stand behind. ``False`` means *these two are verified fine*, and a
        row shown on that basis is the exact failure this port exists to prevent.
        """
        ...
