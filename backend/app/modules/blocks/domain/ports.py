"""The seams this context is built on: one to write a block, one to read one, and
one to draw the people on *Blocked players*.

They are here rather than in ``app/application/ports/`` because both are the
Blocks context's own. ``BlockRepository`` is the **aggregate repository** kind —
how a use case reaches an event-sourced ``Block`` without knowing that it is
event-sourced, owning the aggregate-type name, the replay and the
optimistic-concurrency bookkeeping (``docs/adr/0018``). ``BlockQuery`` is the read
kind, and it is the one every other context is going to hold.

**One ``BlockQuery``, and every route onto a court consults it**
(``docs/adr/0193`` §1) — through Proposals' one pair rule, ``PlayerFit``. The
surfaces that only *show* people — Members, the record — no longer ask it
whether two people may see each other (§2). Three questions, because they have
three shapes:

- **The exclusion set** — *whom must this player never share a court with* —
  ``exclusions_for``, one bounded read keyed on the player.
- **The pairwise question** — *are these two blocked, either way round* —
  ``blocked_between``, two keyed reads and no scan, because the pair determines
  both stream ids.
- **The bulk mask** — *which of these people have a block between them* —
  ``blocked_pairs_among``, what a four of six pairs asks (``docs/adr/0116``).

**All three fail closed, and that is a promise about the port rather than a hope
about its callers** (``docs/adr/0095`` §5):

> A term that cannot be evaluated stands down. A gate that cannot be evaluated
> excludes.

An implementation that cannot answer **raises ``BlockStateUnavailable``**. It may
never return an empty set or a ``False`` to mean *could not tell*: those are the
answers *nobody is blocked* and *these two are fine*, and a caller cannot tell
them from the truth. The failure is loud on purpose — it is the sentence that
stops somebody later "fixing" a flaky query by defaulting it to empty.

**None of those three distinguishes the two directions, and none ever will.** The
record is directed so that an unblock is unambiguous; the *effect* is symmetric,
so a reader asking *may these two share a court* is never handed the half that
would let it answer *which way round*.

**The fourth read is directed, and it is the reader's own** (``docs/adr/0193``
§3). ``blocks_made_by`` answers with the blocks one player *made* — whom, and
when — for *Blocked players* and for the record's *you blocked them*. A response
may carry the reader's own blocks and never anyone's block of the reader, so it
is only ever asked with the reader as the blocker; there is no method that
answers *who blocked me*, and that absence is the design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.blocks.domain.block import Block


@final
@dataclass(frozen=True, slots=True)
class OwnBlock:
    """One block a player made and has not lifted: whom, and when.

    **Only ever the reader's own.** It names the person blocked and never the
    blocker, because the blocker is whoever asked.
    """

    blocked_id: UUID
    #: When the standing block was made. A repeat of it does not move this.
    blocked_at: Instant


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
    """*Is either of these two blocked by the other* — the one place it is asked
    — and, for the reader alone, *whom have I blocked*.

    Read-only, and it answers about live state every time. There is no cache and
    no projection behind it by decision, not by omission: ADR-0095 §4 dropped the
    advisory copy the input document proposed, because a block is binary and
    there is nothing for a ranker to lower.
    """

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        """Every player this one must never share a court with, **in either
        direction**.

        The union of *whom they have blocked* and *who has blocked them*, as one
        flat set — the searcher's live block set, resolved at request time and
        carried into generation as an exclusion list. It is deliberately not two
        sets: nothing downstream may branch on which side a block came from, and
        the cheapest way to keep that true is to hand it an answer that cannot.

        Tens of rows, not a scan. Raises ``BlockStateUnavailable`` rather than
        answering with an empty set it cannot stand behind.
        """
        ...

    async def blocked_pairs_among(
        self, player_ids: Collection[UUID]
    ) -> frozenset[frozenset[UUID]]:
        """Every standing block **between two of these people**, as unordered pairs.

        The third question, added by
        [ADR-0116](../../../../docs/adr/0116-in-a-four-every-gate-binds-all-six-pairs.md):
        a four contains six pairs and the searcher is in three of them, so a
        line-up has to know whether `a` blocked `b` — a question no shortlist
        ever asked, because on a shortlist the searcher is one half of every pair
        on the screen.

        **One bulk read over the `K` ids, never `K²` pairwise ones.** A line-up
        enumerates 276 candidate pairs at `K = 24`, and asking
        :meth:`blocked_between` for each would be 276 round trips for a mask that
        is one query. This asks the opposite way round: *which of these people
        have a block standing between them*, which is a single scan bounded by
        how many blocks those `K` people hold rather than by `K²`.

        It answers in **unordered pairs** for the reason the other two answer as
        they do — nothing downstream may learn which way round a block was taken,
        and a ``frozenset`` of two ids is a shape that cannot say.

        Raises ``BlockStateUnavailable`` rather than an empty set it cannot stand
        behind: an empty answer here seats four people together, and *a gate that
        cannot be evaluated excludes*.
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

    async def blocks_made_by(self, blocker_id: UUID) -> tuple[OwnBlock, ...]:
        """Every block this player made and has not lifted, **newest first**.

        **Directed, and the only read here that is**: blocks *made by* this
        player, never one made *of* them (``docs/adr/0193`` §3). Ask it with the
        reader as the blocker and nobody else — what it answers about somebody
        else's id is that person's private list.

        Tens of rows, bounded by how many people this one player blocked. Raises
        ``BlockStateUnavailable`` rather than answering an empty list it cannot
        stand behind: *you have blocked nobody* is an answer a player acts on.
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class BlockedFace:
    """What *Blocked players* draws for one person — a name, a photograph, and
    nothing else.

    ``name`` is the **Name** and never the nickname (``docs/adr/0171`` §4), and
    ``None`` for an id nobody can name. ``photo_id`` and ``photo_url`` are
    present **exactly together**, and neither means the client draws initials.
    """

    player_id: UUID
    name: str | None = None
    photo_id: UUID | None = None
    photo_url: str | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.photo_id is None) == (self.photo_url is None),
            f"a photograph with only half an address: {self!r}",
        )


@runtime_checkable
class BlockedFaces(Protocol):
    """A fifth spelling of the faces read, and the duplication is the decision:
    two contexts needing *what do I draw for this person* is not a reason for one
    to own the other's vocabulary (``groups``' ``GroupFaces`` says the same of the
    four before it)."""

    async def faces_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, BlockedFace]:
        """Each of these players, in **one question about the union**. A player
        absent from the answer, or with no name, is nobody the platform can
        draw."""
        ...
