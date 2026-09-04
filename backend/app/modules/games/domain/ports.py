"""What this context stores behind, and what it publishes outward.

**Two of these are the module's own** — the repository and the directory — and
one is the platform's. ``GameHistoryQuery`` is the read every other context in
[#302](https://github.com/Raketa02/Raketa/issues/302) was blocked on: the
pairwise history the matcher's familiarity term has been standing down for want
of, the count under `player_card.counted_games`, and the five results *Last 5*
draws. It is contracted in ``tests/demands/`` in ADR-0098's shape, over every
registered implementation, because *a demand nobody executes is a demand
satisfied by accident* — and this one has three consumers arriving in three
different tickets, none of which can read it while it is being written.

**Every count here is measured and none is invented** (``docs/adr/0098``). The
games ledger exists now, so ``counted_games == 0`` means *we looked and this
person has played none*, which is a real answer and the one §9.10's newcomer
predicate has been waiting for. That is the opposite of ``PlayerScoreQuery``,
where a zero would be a claim about a record nobody keeps and the player is
absent from the answer instead.

**Fewer than five results is a real answer and is never padded.** The card draws
a gap; a fifth invented row would be the same mistake in a smaller place.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Minutes, Sport, invariant
from app.modules.games.domain.game import Game
from app.modules.games.domain.results import Outcome

#: How many counterparts travel with one read of the pairwise history.
#:
#: **Spelled to match ``matchmaking``'s ``PAIRWISE_COUNTERPART_BOUND``**, which
#: this context may not import: ``games`` is a provider and does not know a
#: matcher exists. The two spellings meet at the composing adapter, which refuses
#: to import if they ever part company — the seam ``challenges`` already has for
#: the same number.
PLAYED_COUNTERPART_BOUND = 500

#: How many results *Last 5* draws. The card's own number, and the only place it
#: is written on this side of the wire.
RECENT_RESULTS = 5


@final
class PlayedOutcome(str, Enum):
    """How a game between two people ended, as a fact about the pair.

    **A ghost is kept distinguishable from a game**, because familiarity is a
    statement about people who have actually played and the depth term counts
    games rather than arrangements.
    """

    PLAYED = "PLAYED"
    PLANNED_NEVER_PLAYED = "PLANNED_NEVER_PLAYED"


@final
@dataclass(frozen=True, slots=True)
class PlayedTally:
    """How many times one outcome happened between two people, and when it last did.

    The count is the half a latest-outcome row cannot carry: familiarity decays
    on *days since last* and deepens on *games played together*, and a shape with
    one moment and no count feeds the first and never the second.
    """

    count: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.count >= 1,
            f"a tally of something that never happened: count {self.count}",
        )


@final
@dataclass(frozen=True, slots=True)
class GameCounterpart:
    """One person this player has arranged games with, tallied by how they went.

    **One row per person, and both outcomes inside it.** A pair who played four
    times and ghosted once are not a ghost, and collapsing to a latest outcome
    would erase the history the depth term is counting.
    """

    player_id: UUID
    outcomes: Mapping[PlayedOutcome, PlayedTally]

    def __post_init__(self) -> None:
        invariant(
            bool(self.outcomes),
            "a counterpart with nothing between you is not a counterpart — "
            "absence is spelled by not being in the list at all",
        )

    @property
    def last_at(self) -> Instant:
        """The most recent thing that happened between you, of any kind."""

        return max(tally.last_at for tally in self.outcomes.values())

    @property
    def games_played_together(self) -> int:
        """``n``. Zero for a pair who arranged games and never played one."""

        played = self.outcomes.get(PlayedOutcome.PLAYED)
        return played.count if played else 0


@final
@dataclass(frozen=True, slots=True)
class CountedResult:
    """One counted game that produced an agreed score, from one player's side.

    It carries **whether it was counted and whether it was confirmed** by
    existing at all: an unscored game and a friendly are both absent from this
    read, which is what makes it safe for the rating context to move a Level on
    every row it returns.

    ``played_at`` is the moment somebody said *we played* — the only moment this
    platform has about a game, and the one the five are ordered on.
    """

    game_id: UUID
    sport: Sport
    outcome: Outcome
    played_at: Instant


@runtime_checkable
class GameRepository(Protocol):
    """One game's stream, loaded and appended to."""

    async def load(self, game_id: UUID) -> Game | None: ...

    async def save(self, game: Game) -> None: ...

    async def for_challenge(self, challenge_id: UUID) -> Game | None:
        """The game a completed line-up already opened, if one has.

        **One arrangement is one game**, and the opening runs in the transaction
        of an accept — so the read that makes it idempotent belongs beside the
        write rather than in the caller. It is not a lookup by payload the way
        the directory is: it answers about one challenge and returns one game.
        """
        ...


@runtime_checkable
class GameDirectory(Protocol):
    """Every game one player was on the court for. **Aggregates, not rows.**

    The presentation layer needs the standing, the score on the table, whose turn
    it is and when each clock runs out, and every one of those is folded from the
    record and a clock. A projection would be a second place for them to be true
    and would be wrong for the whole gap between a deadline and a sweep.

    It is also where *was this counted or a friendly* and *was its result
    confirmed* are read from by anybody who wants them about one person: both are
    on the aggregate, ``kind`` and ``standing_at``.
    """

    async def playing(self, player_id: UUID) -> tuple[Game, ...]: ...


@runtime_checkable
class GameHistoryQuery(Protocol):
    """The three facts this context owes the rest of the platform, and the fourth
    it owes an honest ``None``."""

    async def played_counterparts(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[GameCounterpart, ...]:
        """Who this player has arranged games with — at most the bound, newest first.

        One row per person, ordered on ``last_at``: this is *who*, not *every
        time*. The order is part of the demand rather than a convenience — it is
        what makes a counterpart cut off by the bound indistinguishable from one
        fully decayed by time.

        **Both outcomes come from the same fold**, which is why they are one
        method: a plan is a ghost only once its entry window has closed, and a
        read that answered about played games alone would leave whoever wanted
        ghosts re-deriving the window somewhere else.
        """
        ...

    async def counted_games_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, int]:
        """How many counted games each of these people has played.

        **Played, not proved.** An unscored game is in this count, because *an
        unscored game is an evening, not evidence*: it says these people were on
        a court and it moves nobody's Level. A friendly is not, because it was
        never evidence about anybody by the choice of the people who arranged it.

        **Every player asked about gets a count, and a zero is measured**: the
        games were counted and none of them was theirs.
        """
        ...

    async def recent_results_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, tuple[CountedResult, ...]]:
        """The last few counted results per player, **oldest to newest**.

        At most ``RECENT_RESULTS``, and fewer is a real answer that is **never
        padded** — the card draws a gap. Oldest first because the row is read
        left to right as a run of form, and a client reversing a list is a client
        that can reverse it wrongly.

        A player with none is **absent from the answer** rather than carrying an
        empty tuple: one spelling for *nothing to show*, so a measured nothing
        and an unasked question cannot start being confused.
        """
        ...

    async def late_change_threshold(self) -> Minutes | None:
        """How close to its moment a change has to be to count as **late**.

        ``None``, and now for a reason this context owns rather than borrows. A
        plan here is a line-up with a window and no time in it: an accepted seat
        cannot be withdrawn, and there is nothing to move. *Late* has no referent,
        so there is no number — absent rather than defaulted, because a number
        nobody measured is a number somebody picked.

        It is demanded of the context that owns plans even though ``player_score``
        computes the strand, and this is that context. If a later product grows a
        plan with a time in it, that is a conversation and it amends
        ``docs/adr/0098`` — it is not a licence to publish a different number
        under the same name.
        """
        ...


__all__ = [
    "PLAYED_COUNTERPART_BOUND",
    "RECENT_RESULTS",
    "CountedResult",
    "GameCounterpart",
    "GameDirectory",
    "GameHistoryQuery",
    "GameRepository",
    "PlayedOutcome",
    "PlayedTally",
]
