"""What the matcher demands of the contexts it does not build.

**Three outward ports, and one provider signs one contract**
(``docs/adr/0098``, ``docs/specs/matchmaking/consumer-driven-contracts.md``). The
split is by *who supplies the fact*, never by how fresh it has to be — a provider
that signed half of two contracts would have signed all of neither.

They live in one file on purpose: it is **the one place a build agent finds every
demand the matcher makes outward**.

| Port | Provider | Read by |
| --- | --- | --- |
| ``AccountHoldQuery`` | ``cases``: ``NoHoldsExist`` | the record's gates |
| ``AccountStatusQuery`` | ``users``: a **real adapter** | the record's gates |
| ``AtStakeQuery`` | ``rating``'s update rule: **real** | a booked game's pairing |

**Four went with the searches** (#579): ``PlayerScoreQuery``,
``MatchHistoryQuery``, ``HalfBuiltCourtQuery`` and ``SharedCourtQuery`` were read
by the shortlist, the line-ups and the deck and by nothing else.

**The rule that decides every shape below:** *a gate may be honestly empty; a
courtesy may never be honestly invented*, and the test is whether a zero would be
**measured** or **invented**. Nobody can be held because nothing can hold
anybody, so the hold gate ships true-over-empty and its zero is real.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Sport, invariant


# ---------------------------------------------------------------------------
# AccountHoldQuery — ``cases``
# ---------------------------------------------------------------------------


@runtime_checkable
class AccountHoldQuery(Protocol):
    """Whether an account is under a live hold. **One boolean per player.**

    Settled by ``docs/adr/0095``: live, **both directions** — a held *reader*
    is refused at the entry point rather than merely hidden from others — and
    **fail-closed**, because a gate that cannot be evaluated excludes.

    **The matcher never reads ``cases`` to score, and this shape is why it
    cannot.** The port answers with player ids and nothing else: no case, no
    opened-at, no severity, no count — there is no number here to weigh. *Settles
    up* is ``player_score``'s to publish from the historical record, and the
    prototype's collapse of the strand to ``0.15`` while a share is unsettled
    conflates the strand with the gate. A held player is both excluded here and
    carrying a low *settles up*; **that double reach is intended** and is not a
    duplication to be tidied away.

    **Not ``AccountStatusQuery``, and never merged with it.** *Held* and
    *disabled* are different truths, from different contexts, with different
    lifecycles and different remedies (``docs/adr/0124``).
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these players are under a live hold, right now.

        A set membership read once per read rather than a query per person,
        which is the block set's shape and for the block set's reason.

        Answers only about ids it was asked about.
        """
        ...


# ---------------------------------------------------------------------------
# AtStakeQuery — ``rating``'s result-update rule
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True)
class AtStake:
    """What a counted win and a counted loss would do to a player's Level.

    The pair a booked game's screen prints beside the forecast — ``+0,07``
    against ``−0,05`` — computed from the two sides' ratings and the player's own
    confidence.

    **Neither delta may be zero**, and the invariant is the contract rather than
    a sanity check: a zero would claim a counted game against this opponent moves
    the player's Level by nothing, which is false about every opponent. When
    there is no answer the port says so by answering nothing at all.
    """

    win_delta: float
    loss_delta: float

    def __post_init__(self) -> None:
        invariant(
            self.win_delta > 0 > self.loss_delta,
            "at stake claims a counted result that changes nothing or moves the "
            f"wrong way: +{self.win_delta} / {self.loss_delta}",
        )


@runtime_checkable
class AtStakeQuery(Protocol):
    """A pair of signed deltas for one player on one court.

    **Nobody but ``rating`` may compute it, and that is why there is a port here
    at all.** The number needs the result-update rule — a K-factor over the
    player's confidence and an expected score over the two μ values. Three
    parties could plausibly do the arithmetic and none of them may: the **client**
    cannot under ``docs/adr/0021``, because this is a rule with constants rather
    than a countdown toward a supplied instant; the **matcher** cannot under its
    own standing rule that it reads what the player is shown and never re-derives
    it, and because a K-factor is the rating engine's opinion about the rating
    engine; and the **contract** cannot specify the maths, for the same reason it
    has no opinion on how ``games`` works internally. It demands the fact and
    stops.

    **The provider ships and so does the rule** (``docs/adr/0139``). ``rating``
    lives at ``app/modules/rating/`` with its engines at
    ``app/engines/racketskill/``, and the result-update rule is ``results.py``
    there — the same function that moves a Level when the game is actually
    played, which is what makes this block a promise rather than an estimate of
    one. ``NoResultUpdateRuleExists`` is gone; the registered implementation is
    ``RatingResultUpdateRule``.

    **The answer is still absent rather than zero** whenever either party holds
    no rating in this sport, and that absence is measured: there is nothing to
    price the pairing against.

    Fails **soft** — the block is simply not drawn.
    """

    async def counted_game_deltas_on_court(
        self,
        *,
        player_id: UUID,
        own_side: Collection[UUID],
        opposing_side: Collection[UUID],
        sport: Sport,
    ) -> AtStake | None:
        """What a **counted** game on this court would be worth to this player.

        **The rule's own reading, for a line-up that is frozen**
        (``docs/adr/0161``). A game knows every seat, and the result will be
        priced **side against side** — every player on a side moves by the same
        amount, on ``one_side``'s rule that a partner is not somebody you are
        rated *against*. A game screen printing a head-to-head reading in a four
        would promise a figure the update then contradicts, which is the one
        thing *at stake* exists not to do. (The head-to-head read a search card
        drew went with the searches, #579.)

        ``player_id`` is on ``own_side``, and the pair is theirs: the Level move
        is the side's, so it is the same pair for everybody on it, and the
        certainty it buys is the player's own and does not cross here.

        ``None`` when this player holds no rating in this sport — there is
        nothing to move — and when a whole side holds none, which is *nothing
        to price against*. An unrated seat beside a rated one is **not** an
        absence: the update folds a side over the people on it who hold a
        rating, and so does this, because a figure that omitted the case the
        rule prices would be a preview and not the rule.
        """
        ...


# ---------------------------------------------------------------------------
# AccountStatusQuery — ``users``
# ---------------------------------------------------------------------------


@runtime_checkable
class AccountStatusQuery(Protocol):
    """The set of account ids that **may not be shown**. A gate, over ``users``.

    The one outward port whose provider ships (``docs/adr/0124``), so the
    contract suite runs against a real adapter rather than a fake standing in for
    a context nobody has written.

    | | |
    | --- | --- |
    | **Direction** | **Candidate-side only** |
    | **On failure** | **Closed** — the read refuses |
    | **Freshness** | Live. **Never a stored copy** |
    | **Told** | **Nobody** — invisible to the reader, like a block |

    **Candidate-side only is a fact, not a leniency.** ``docs/adr/0095`` makes the
    Hold bidirectional because a *held* player can still log in and read. A
    **disabled** one cannot get past ``get_current_user``, so ``auth`` closes the
    reader's side before the matcher is reached, and a second check here would
    assert something the request could not have carried.

    **Never a stored copy.** A stale *active* flag means a disabled account is
    shown to a stranger, which makes staleness cost **safety**. Account state is
    also not a fact a player changes *about themselves*: an administrator may
    change it.

    **What this does not cover.** Account **erasure** — nothing in this repository
    deletes an account, and erasure is a platform-wide obligation rather than a
    matchmaking demand. If it arrives it changes what *may not be shown* means,
    and the gate's name does not change.
    """

    async def may_not_be_shown(
        self, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these candidates the reader may not be shown.

        Resolved live, **once per read, as a set** — never a query per
        candidate. Answers only about ids it was asked about, and invents
        nobody: an id ``users`` has never heard of is not withheld, because a
        typo must not read as a disabled account.
        """
        ...


# ---------------------------------------------------------------------------
# How each demand fails
# ---------------------------------------------------------------------------


class FailPosture(str, Enum):
    """What happens when one of these reads cannot be answered.

    **A gate that cannot be evaluated excludes; a term that cannot be evaluated
    stands down.** The two are not a spectrum and there is no third value: a
    safety control has no degraded reading, and a courtesy has no reason to take
    the whole screen down with it.
    """

    #: The read refuses. *Nobody is held* and *we could not find out* are
    #: different sentences and must not become one.
    CLOSED = "CLOSED"
    #: The read stands down to the answer its caller offered, and proceeds.
    SOFT = "SOFT"


#: Every outward demand, and how it fails. **Exhaustive over ``MATCHER_DEMANDS``.**
#:
#: Classified in one table rather than at each call site, which is what stops the
#: next person having to guess.
#:
#: **Blocks are built and are deliberately not a row here** (#203). Every port
#: below is one the *matcher* declares of a context it does not write, and its
#: posture is the matcher's reading of somebody else's fact. ``BlockQuery`` is
#: the other arrangement: ADR-0095 §7 makes it the Blocks context's **own** port,
#: declared once and consulted by every surface that shows one player to another,
#: and its fail-closed posture is asserted where the port lives
#: (``modules/blocks/domain/ports.py``) rather than restated per consumer.
#:
#: ``AtStakeQuery``'s row is **derived rather than quoted**: an unanswerable
#: at-stake block is simply not drawn, so a failure here costs a block and never
#: the screen.
FAIL_POSTURE: Mapping[type, FailPosture] = {
    AtStakeQuery: FailPosture.SOFT,
    AccountHoldQuery: FailPosture.CLOSED,
    AccountStatusQuery: FailPosture.CLOSED,
}

#: The three outward ports, as the suite in ``tests/demands/`` walks them.
#:
#: Declared as data rather than left to a reader to collect, so that *a port with
#: no registered implementation* is a question something can ask. A demand nobody
#: runs anything against is the failure ``docs/adr/0098`` exists to prevent, and
#: it arrives by omission rather than by anybody deciding it.
#:
#: **Not derived from ``FAIL_POSTURE``'s keys**, though it would be one line. The
#: two are different claims — *this is a demand the matcher makes* and *this is
#: how that demand fails* — and deriving one from the other would make forgetting
#: the posture invisible instead of red. Two lists that check each other is the
#: point, not the duplication.
MATCHER_DEMANDS: tuple[type, ...] = (
    AtStakeQuery,
    AccountHoldQuery,
    AccountStatusQuery,
)
