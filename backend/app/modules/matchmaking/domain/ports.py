"""What the matcher demands of the contexts it does not build.

**Five outward ports, and one provider signs one contract**
(``docs/adr/0098``, ``docs/specs/matchmaking/consumer-driven-contracts.md``). The
split is by *who supplies the fact*, never by how fresh it has to be — a provider
that signed half of two contracts would have signed all of neither.

**One of the five has two providers, and the ADR's amendment banner records the
bend.** ``MatchHistoryQuery``'s seam runs *through* ``pairwise_counterparts``:
``ACCEPTED`` and ``DECLINED`` are ``challenges``' facts and ``PLAYED`` is
``games``'. Splitting the port to match would cut
``PAIRWISE_COUNTERPART_BOUND`` in half, and two bounded reads merged by a caller
is not a bounded read — so the port stays whole and ``games`` arrived as a
**composing** adapter rather than as a second signature
(``docs/adr/0137``). The context is called ``games`` and not ``matches``: the
placeholder was retired when it was built, because the wire, the card and the
newcomer path all say *game*.

They live in one file on purpose: it is **the one place a build agent finds every
demand the matcher makes outward**, and splitting them by does-the-provider-exist
would make a reader check two places to be sure they had them all.

| Port | Provider | Day one |
| --- | --- | --- |
| ``PlayerScoreQuery`` | ``player_score`` | a **real adapter** — the provider ships |
| ``MatchHistoryQuery`` | ``challenges`` + ``games`` | a **real** composition of two |
| ``AccountHoldQuery`` | ``cases`` | ``NoHoldsExist`` |
| ``AtStakeQuery`` | ``rating``'s update rule | a **real adapter** — the rule ships |
| ``AccountStatusQuery`` | ``users`` | a **real adapter** — the provider ships |
| ``HalfBuiltCourtQuery`` | ``challenges`` | a **real adapter** — the fill's court |
| ``SharedCourtQuery`` | ``games`` | a **real adapter** — the deck's cool-off |

**The rule that decides every shape below:** *a gate may be honestly empty; a
term may never be honestly neutral*, and the test is whether a zero would be
**measured** or **invented**. Nobody can be held because nothing can hold
anybody, so the hold gate ships true-over-empty and its zero is real. A player
nothing has ever been arranged for has not failed to turn up, so they are
**absent from the ``player_score`` answer** and never a `0` or a `0.5` — which is
now a rule a real provider keeps rather than one a null object could not break
(``docs/adr/0140``).

**The matcher reads what the player is shown and never re-derives it.** A card
explaining a match with a number the player's own profile disagrees with is worse
than a card that says nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import ReliabilityStrand, SearchMode
from app.kernel import Instant, Minutes, Sport, invariant


# ---------------------------------------------------------------------------
# PlayerScoreQuery — ``player_score``
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True)
class RatioStrand:
    """One of the four ratio strands: what was published, and out of what.

    ``value`` is **the number the player is shown on their own Player Score
    screen**, out of a hundred, and the matcher never re-derives it from the
    counts beside it. A card explaining a match with a figure the player's own
    profile disagrees with breaks the explainability promise more thoroughly than
    saying nothing would. The numerator and denominator ride along because the
    matcher's one policy over these facts is *standing a strand down* below
    ``min_observations``, and one no-show out of one game is not thirty-five out
    of thirty-eight.

    The unit of the denominator is named per strand in
    ``docs/specs/matchmaking/consumer-driven-contracts.md`` so that two people
    reading it compute the same one.
    """

    value: int
    numerator: int
    denominator: int
    observed_at: Instant

    def __post_init__(self) -> None:
        invariant(
            0 <= self.value <= 100,
            f"a strand value outside 0..100: {self.value}",
        )
        invariant(
            self.denominator >= 1,
            "a strand with no opportunity behind it is an absence, not a zero: "
            f"denominator {self.denominator}",
        )
        invariant(
            0 <= self.numerator <= self.denominator,
            f"a strand numerator outside its denominator: "
            f"{self.numerator}/{self.denominator}",
        )


@final
@dataclass(frozen=True)
class SportsmanshipStrand:
    """Sportsmanship — **a mean of 1–5, not a ratio.**

    It is the fifth strand and the one with no good outcome to count, so it
    crosses as its mean and the number of ratings behind it. A separate type
    rather than a ratio with a convention, because a mean smuggled through a
    numerator would be a strand nobody could interpret and nothing could refuse.

    **Nothing constructs one yet**, and that is not a gap in this file: the one
    strand shaped differently from the rest is also the one with no surface on
    which anybody could rate anybody (``docs/adr/0140``). Inventing a mean to
    exercise the shape would put a number on a card that nobody said.
    """

    mean: float
    rating_count: int
    observed_at: Instant

    def __post_init__(self) -> None:
        invariant(
            1.0 <= self.mean <= 5.0,
            f"a sportsmanship mean outside 1..5: {self.mean}",
        )
        invariant(
            self.rating_count >= 1,
            "a sportsmanship mean with no ratings behind it is an absence, not a "
            f"zero: rating count {self.rating_count}",
        )


#: What a strand crosses as. Two shapes, because five of the six are ratios and
#: the sixth is a mean, and one shape covering both would be a shape that
#: describes neither.
StrandObservation = RatioStrand | SportsmanshipStrand


@final
@dataclass(frozen=True)
class PlayerScoreReading:
    """One player's Player Score, **as strands and never as one number.**

    The ruleset weighs the strands **per mode** — 25/32, 22/22, 24/4, 14/14,
    10/12, 5/16 — and the two vectors order people oppositely: *answers about
    results* is worth nearly five times sportsmanship for a counted game and a
    quarter of it for a friendly. One blended number cannot express that. The
    Player Score is nonetheless *one number in the UI*, so the obvious thing to
    ship is that number — which is exactly the failure ``docs/adr/0098`` is
    written against, and why there is **nowhere here to put a blend of the
    six**.

    ``published_score`` is not that blend and is the one deliberate exception,
    recorded so it does not later read as an oversight. It is the figure on the
    player's own profile at the player-facing weights (35/20/15/12/10/8,
    renormalised over the strands present), computed by ``player_score`` and read
    here rather than derived. Its consumer **in the matcher** is the reliability
    floor, whose ``published_score_bar`` lives in the ruleset beside it; the card is a
    second reader one layer out and prints the same figure (``docs/adr/0140``). A
    penalty justified by a figure that exists nowhere a human can look is
    unexplainable, and a player working their visible score back up must be able
    to watch the penalty lift. It may never be weighed as a term, and it cannot
    stand in for the strands: a reading with no strand in it is refused below.

    **An empty reading is not a reading.** Absence has one spelling — the player
    is simply not in the answer — because two spellings of *we have nothing* is
    how a measured nothing and an unasked question start being confused.
    """

    strands: Mapping[ReliabilityStrand, StrandObservation]
    published_score: int

    def __post_init__(self) -> None:
        invariant(
            0 <= self.published_score <= 100,
            f"a published Player Score outside 0..100: {self.published_score}",
        )
        invariant(
            bool(self.strands),
            "a Player Score reading with no strands is an absence, and an "
            "absence is spelled by not answering about that player at all",
        )
        for strand, observation in self.strands.items():
            expected = (
                SportsmanshipStrand
                if strand is ReliabilityStrand.SPORTSMANSHIP
                else RatioStrand
            )
            invariant(
                isinstance(observation, expected),
                f"{strand.value} crossed as {type(observation).__name__} rather "
                f"than {expected.__name__}",
            )

    @property
    def most_recent_observation(self) -> Instant:
        """The freshest moment across every strand — what the horizon reads.

        Derived rather than demanded. The horizon is one number over the whole
        score rather than six because the strands share one cause — *this player
        stopped playing* — and a provider asked to publish it separately would be
        a second place for it to disagree with the strands it summarises.
        """

        return max(observation.observed_at for observation in self.strands.values())


@runtime_checkable
class PlayerScoreQuery(Protocol):
    """The six reliability strands, each with the evidence behind it.

    **Three of them have a provider** — *shows up*, out of plans that settled
    either way, *keeps plans*, out of booked games kept or broken (#544, where
    it took *answers challenges*' place), and *answers about results*, out of
    the scores put in front of somebody (``docs/adr/0160``). The other three are
    absent from every reading rather than published at nought, and the term
    renormalises over what arrives (``docs/adr/0140``).

    **The matcher applies no decay of its own.** The score is a memory and fades
    with new evidence on the provider's side; a second decay here would
    double-count. Its entire policy over these facts is the power to stand a
    strand down — below **its own** ``min_observations`` a strand alone, past
    ``horizon_days`` the whole term — and both are ruleset configuration under
    ``docs/adr/0093``, never code and never environment-selected. The first is a
    bar per strand rather than one number over all six (``docs/adr/0160``), so a
    strand that needs more evidence than the rest can ask for it without changing
    what the platform demands of a newcomer.

    **Opponent variety is not here, and was withdrawn rather than deferred.** It
    was demanded on behalf of two consumers and both were struck (#164, #175). *A
    consumer-driven contract with no consumer is withdrawn, not carried* — a
    demand nobody reads is a demand nobody notices going wrong, and a contract
    suite is exactly where an unread row goes quietly stale. It has since come
    back on **somebody else's** register — the player record demands it of
    ``games``, which owns both its inputs (``docs/adr/0098`` as amended, #380) —
    and that changes nothing here: the matcher does not read it, it is not a
    strand, and its fold is unbounded in a way no read on this port may be.

    ***Settles up* will stand down long after the other four are live.** It
    depends on court money, which is out of scope. Expected, not a defect — and
    it is the **historical record**, never the live case: the open case is the
    Hold and does its work at ``AccountHoldQuery``.

    Fails **soft**: the term stands down and the search proceeds.
    """

    async def readings_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, PlayerScoreReading]:
        """Each of these players' Player Score, for those that have one.

        A player with no record is **absent from the answer** — not a zero and
        not a neutral half. Read once per search over the box, never a query per
        row: the provider folds two event logs behind this, and a per-row call
        would be a thousand walks of them inside one request.
        """
        ...


# ---------------------------------------------------------------------------
# MatchHistoryQuery — ``challenges`` and ``games``, composed
# ---------------------------------------------------------------------------

#: How many pairwise counterparts travel with a search, most recent first.
#:
#: A searcher has played tens of people, and an unbounded read is how one
#: long-standing player's search becomes slow for everyone. The bound is also
#: what makes a counterpart cut off by it and one fully decayed by time
#: **indistinguishable by construction**, which is what keeps familiarity's
#: signed decay honest at the tail.
PAIRWISE_COUNTERPART_BOUND = 500


class PairwiseOutcome(str, Enum):
    """How the last thing between these two people ended.

    **A ghost game is two facts and they go to different places.** As a
    per-player reliability signal it is ``player_score``'s input and the matcher
    never sees it separately; as a *pairwise* outcome it is here, and
    ``PLANNED_NEVER_PLAYED`` is kept distinguishable from ``PLAYED`` because
    familiarity must be able to tell them apart.
    """

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    PLAYED = "PLAYED"
    PLANNED_NEVER_PLAYED = "PLANNED_NEVER_PLAYED"


@final
@dataclass(frozen=True)
class OutcomeTally:
    """How many times one outcome happened between two people, and when it last did.

    **The count is the half a latest-outcome row cannot carry.** Familiarity is
    ``0.5 ^ (days_since_last / HALF_LIFE) × (1 − DEPTH_PHI ⁿ)`` where ``n`` is
    games played together (``ranking-weights.md`` §8), so a shape with one moment
    and no count can feed the decay and never the depth.
    """

    count: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.count >= 1,
            f"a tally of something that never happened: count {self.count}",
        )


@final
@dataclass(frozen=True)
class PairwiseCounterpart:
    """One person the searcher has history with, tallied by how it went.

    **One row per person, and everything that happened between you inside it.**
    The bound is 500 *counterparts*, not 500 events, and it is the searcher's own
    set travelling with the search — so the row has to hold the whole pair's
    story rather than its most recent line.

    Keeping the outcomes apart is what lets an accept stay visible under a later
    decline. Collapsed to a latest outcome, a pair who played four times and
    declined once in August reads as a decline, and the previous-decline signal
    and familiarity would both be reading the same erased history.
    """

    player_id: UUID
    outcomes: Mapping[PairwiseOutcome, OutcomeTally]

    def __post_init__(self) -> None:
        invariant(
            bool(self.outcomes),
            "a counterpart with nothing between you is not a counterpart — "
            "absence is spelled by not being in the list at all",
        )

    @property
    def last_at(self) -> Instant:
        """The most recent thing that happened between you, of any kind.

        What the bound orders on, and what *days since last* reads.
        """

        return max(tally.last_at for tally in self.outcomes.values())

    @property
    def games_played_together(self) -> int:
        """``n``. Zero for a pair who arranged games and never played one."""

        played = self.outcomes.get(PairwiseOutcome.PLAYED)
        return played.count if played else 0


@final
@dataclass(frozen=True)
class SentFromSearch:
    """The challenge came from a shortlist, at a known position in it.

    The join ``docs/specs/matchmaking/search-telemetry.md`` §19.2 needs, and the
    half this contract demands of the other end: the search side of the chain
    ships now, and this is what the outcome side carries back to it.
    """

    search_id: UUID
    position: int

    def __post_init__(self) -> None:
        invariant(
            self.position >= 1,
            f"a shortlist position below one: {self.position}",
        )


@final
@dataclass(frozen=True)
class SentOutsideASearch:
    """The challenge came from somewhere else, said explicitly.

    Carries nothing: it is a **claim**, not a description. What *somewhere else*
    turns out to contain — a profile visit, a club page, a rematch — is
    ``games``' vocabulary to name if it ever needs one, and inventing a taxonomy for
    it here would be this context taking an opinion about somebody else's states.

    What matters is that it exists at all. The alternative is a nullable field,
    the first caller in a hurry omits it, and there is no backfill — the loss is
    permanent and silent.
    """


#: Where a challenge came from. **Two answers, and never a third.**
ChallengeOrigin = SentFromSearch | SentOutsideASearch


@final
@dataclass(frozen=True)
class OpenChallenge:
    """A challenge standing between the searcher and one other person.

    ``origin`` has **no default**, so a challenge that does not say where it came
    from cannot be constructed at all — which is the executable form of *never an
    optional field*.
    """

    counterpart_id: UUID
    origin: ChallengeOrigin
    opened_at: Instant
    #: Which challenge stands between the two of them. **The one field here
    #: that is not about the pair**, and the only place *which challenge* could
    #: come from: a counterpart, an origin and an instant cannot name an
    #: aggregate (``docs/adr/0150`` §3, and the published port's growth is the
    #: honest price of it).
    #:
    #: It has exactly one reader and one use — a fill names the challenge it
    #: completes, and the open-challenge gate steps aside for **that one and
    #: nothing else**. It is not an id to fetch anything with: nothing here
    #: reads a challenge by it, and the exemption is a smaller
    #: ``open_challenge_ids`` rather than a gate that fired and was ignored.
    challenge_id: UUID


@runtime_checkable
class MatchHistoryQuery(Protocol):
    """The searcher's pairwise history, the open challenges, and the load count.

    **Every fact here except the count is a fact about a pair**, and the
    candidate index is one row per ``(player, sport)`` with nowhere to put one.
    ``docs/adr/0095`` already answered this for blocks and the answer transfers:
    **the searcher's own set travels with the search; the index holds nothing.**
    One bounded read, keyed on the searcher, at search time.

    **It fails soft, all of it.** Familiarity and the previous-decline signal
    stand down and the search proceeds — losing a game because we could not
    remember who you played in March is a worse outcome than a slightly duller
    list — and the pending-pair set fails soft too, because §7.5's *the matcher
    proposes, the backend disposes* re-verifies on the way out. That is
    embarrassment with a backstop, not a safety failure. These are separate reads
    carried in one context object; bundling them into one would make the
    strictest fact's failure mode everybody's.

    **Two providers sign it, and the seam runs through the first read.**
    ``challenges`` answers the challenge half of ``pairwise_counterparts`` —
    ``ACCEPTED`` and ``DECLINED``, mapped from the answers people actually gave
    — plus the whole of ``open_challenges`` and ``open_challenge_counts``.
    ``games`` brings ``PLAYED``, ``PLANNED_NEVER_PLAYED`` and the threshold, and
    it arrived as an adapter that **composes** with that one rather than
    replacing it (``docs/adr/0137``). The alternative was splitting the port,
    which would cut the 500 bound in half and leave a caller merging two bounded
    reads into an unbounded one.
    """

    async def pairwise_counterparts(
        self, searcher_id: UUID
    ) -> tuple[PairwiseCounterpart, ...]:
        """Who this searcher has history with — at most 500, newest first.

        One row per person, ordered on ``last_at``: this is *who*, not *every
        time*, and everything that happened between the pair is tallied inside
        the row. The order is the bound's meaning, so it is part of the demand
        rather than a convenience — it is what makes a counterpart cut off by the
        bound and one fully decayed by time indistinguishable.
        """
        ...

    async def open_challenges(self, searcher_id: UUID) -> tuple[OpenChallenge, ...]:
        """Every challenge currently open between this searcher and anyone.

        **One row per counterpart, and a counterpart is everybody occupying a
        seat other than your own** — co-invitees included, because if you are
        both in a line-up you have an open game together. Somebody whose seat has
        declined or lapsed is out of it immediately: their seat is open again, so
        they return to the deck rather than losing a candidate they never turned
        down.

        **Open means *being arranged*, and a completed line-up is not.** The
        moment every seat is accepted the two of them have finished arranging a
        game, so they leave this answer and return to each other's deck — free to
        arrange a second one, because nothing here asks whether the first was
        ever played (``docs/adr/0142`` §1).

        Each row carries **that seat's own** origin, so one doubles send from one
        search at three positions comes back as three rows with three positions —
        which is the join ``docs/specs/matchmaking/search-telemetry.md`` §19.2
        needs.

        **Unbounded**, because it is a never-stale fact and small by
        construction — a player has a handful of live challenges, not a history
        of them.
        """
        ...

    async def late_change_threshold(self) -> Minutes | None:
        """How close to the scheduled moment a change has to be to count as **late**.

        The *keeps plans* strand counts plans that reached their moment without a
        **late** change by this player — and that denominator only means
        something if *late* means one thing. The prototype has *"one late change
        in six months"* as prose with no denominator behind it; a per-case
        judgement is not a fact and cannot be contracted, which is why this
        method takes **no pair, no plan and no case**. One published number, or
        none.

        ``None``, and now for a reason its provider owns rather than for the
        absence of one. A plan in ``games`` is a line-up with a window and no
        time in it: an accepted seat cannot be withdrawn and there is nothing to
        move, so *late* has no referent. Absent rather than a default, on the
        same rule as everything else here: a number nobody measured is a number
        somebody picked.

        Demanded of ``games`` even though ``player_score`` computes the strand:
        *late* is a fact about a plan, and the context that owns plans owns what
        the word means. If a later product grows a plan with a time in it, that
        is a conversation and it amends ``docs/adr/0098`` — it is not a licence
        to publish a different number under the same name.
        """
        ...

    async def open_challenge_counts(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, int]:
        """How full each of these players' inboxes is. **Advisory.**

        Not pairwise, and the one fact here the index keeps — it ranks on load
        and is never the last word. A full inbox *sinks* a player rather than
        withholding them (``docs/adr/0125``), and no screen ever shows the number.

        **What is counted is seats awaiting *that player's* answer** — invited,
        unanswered, inside their own window, across every sport. Not the
        challenges they organised: an organiser with eight sends out is
        over-committed but is not slow to answer, and sinking them would dock the
        exact behaviour this signal exists to find. The ruleset's own falsifier
        is what decides it — *answer rate by open-challenge bucket* — and only
        unanswered seats are the denominator of that.

        **Every player asked about gets a count, and a zero here is measured**:
        the seats were counted and none of them was theirs. That is what
        separates this read from ``PlayerScoreQuery``, where a zero would have
        been invented and the player is absent instead.
        """
        ...


# ---------------------------------------------------------------------------
# AccountHoldQuery — ``cases``
# ---------------------------------------------------------------------------


@runtime_checkable
class AccountHoldQuery(Protocol):
    """Whether an account is under a live hold. **One boolean per player.**

    Settled by ``docs/adr/0095``: live, **both directions** — a held *searcher*
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

        A set membership read once per search rather than a query per row, which
        is the block set's shape and for the block set's reason. The searcher's
        own id goes in the collection beside the candidates' — the gate points
        both ways, and asking in one call is what stops one direction being
        forgotten.

        Answers only about ids it was asked about.
        """
        ...


# ---------------------------------------------------------------------------
# AtStakeQuery — ``rating``'s result-update rule
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True)
class AtStake:
    """What a counted win and a counted loss would do to the searcher's Level.

    The pair the competitive candidate card shows up front — ``+0,07`` against
    ``−0,05`` — computed from both ratings and the searcher's own confidence.

    **Neither delta may be zero**, and the invariant is the contract rather than
    a sanity check: a zero would claim a counted game against this opponent moves
    the searcher's Level by nothing, which is false about every opponent. When
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
    """A pair of signed deltas for one ``(searcher, opponent, sport)``.

    **Nobody but ``rating`` may compute it, and that is why there is a port here
    at all.** The number needs the result-update rule — a K-factor over the
    searcher's confidence and an expected score over the two μ values. Three
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

    async def counted_game_deltas(
        self, *, searcher_id: UUID, opponent_id: UUID, sport: Sport
    ) -> AtStake | None:
        """What a **counted** game against this opponent would be worth.

        Named for the counted game rather than for the mode, because *for-fun
        games are never counted*: in a friendly the figure is not
        absent-because-unavailable, it is **meaningless**, and the card renders
        nothing. Asking about a for-fun evening is therefore a category error the
        method's own name refuses, not a mode flag it would have to branch on.

        ``None`` when there is no answer, which now means one thing: one of the
        two holds no rating in this sport.
        """
        ...

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
        (``docs/adr/0161``). The pair read above prices *you against this
        person* because a card is drawn before the other seats are known; a game
        knows all four, and the result will be priced **side against side** —
        every player on a side moves by the same amount, on ``one_side``'s rule
        that a partner is not somebody you are rated *against*. A game screen
        printing the pair reading in a four would promise a figure the update
        then contradicts, which is the one thing *at stake* exists not to do.

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
    """The set of account ids that **may not be shown**. Gate 8, over ``users``.

    The one outward port whose provider ships (``docs/adr/0124``), so the
    contract suite runs against a real adapter rather than a fake standing in for
    a context nobody has written.

    | | |
    | --- | --- |
    | **Direction** | **Candidate-side only** |
    | **On failure** | **Closed** — the search refuses |
    | **Freshness** | Live. **Never an index column** |
    | **Told** | **Nobody** — invisible to the searcher, like a block |

    **Candidate-side only is a fact, not a leniency.** ``docs/adr/0095`` makes the
    Hold bidirectional because a *held* player can still log in and run a search.
    A **disabled** one cannot get past ``get_current_user``, so ``auth`` closes
    the searcher side before the matcher is reached, and a second check here
    would assert something the request could not have carried.

    **Never an index column.** A stale *active* flag means a disabled account is
    shown to a stranger, which makes staleness cost **safety** — the one thing
    ``docs/adr/0111`` exists to prevent. Account state is also not a fact a player
    changes *about themselves*: an administrator may change it.

    **What this does not cover.** Account **erasure** — nothing in this repository
    deletes an account, and erasure is a platform-wide obligation rather than a
    matchmaking demand. If it arrives it changes what *may not be shown* means,
    and the gate's name does not change.
    """

    async def may_not_be_shown(
        self, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these candidates the searcher may not be shown.

        Resolved live, **once per search, as a set** — never a query per
        candidate row. Answers only about ids it was asked about, and invents
        nobody: an id ``users`` has never heard of is not withheld, because a
        typo must not read as a disabled account.
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class HalfBuiltCourt:
    """The challenge a fill names, as the search completing it reads it.

    **Everything a fill may not be told and must know** (``docs/adr/0150`` §2).
    The sport, the kind of evening and who is already sitting down are facts the
    challenge holds, and a request offering any of them would be a second place
    for one of them to be true — which is the failure the request's own boundary
    refuses.

    ``mode`` is ``None`` exactly where the challenge has none: a deck-born send,
    and every mutual-born court. The filler's own declared Play intent resolves
    one then, on the deck's own rule, and **no mode picker appears anywhere**.
    **There is no window on this row and there will not be one** — a window is
    stamped by the send and by nothing else, so a mutual-born challenge stays
    window-less for its whole life and a newly-invited player answers against a
    label somebody else's grid produced (§5).

    ``seated_ids`` is everybody live on that court besides the filler, in the
    court's own order: **the locked seats**, resolved out of this search's own
    pool like any other hand-seated player. They are not a way past the pool —
    a seated player with no scored row is a player the group objective cannot
    optimise around, and ``optimised_for: GROUP`` *is* that optimisation. **It
    may be empty** on a court that has been a game and lost everybody but the
    filler (``docs/adr/0162`` §6).

    ``answered_and_gone`` is everybody who answered this challenge and left it.
    They are back in the deck the moment they declined or lapsed, so without this
    they would be candidates for the very fill they turned down — and the send
    would refuse with ``NobodyIsAskedTwice`` *after* the player chose them (§4).
    """

    challenge_id: UUID
    sport: Sport
    mode: SearchMode | None
    seated_ids: tuple[UUID, ...]
    answered_and_gone: frozenset[UUID]

    def __post_init__(self) -> None:
        """The two claims this shape makes, checked at the crossing.

        **Stated here as well as on the provider's own row, and deliberately.**
        The demand suite parameterises over *every* registered implementation of
        this port, so a second one — or a translation that dropped a filter —
        would otherwise hand the fill a court it could not seat and the failure
        would arrive as ``locked_seat_not_available`` about nobody.
        """

        invariant(
            not (set(self.seated_ids) & self.answered_and_gone),
            f"somebody both seated on {self.challenge_id} and gone from it: "
            f"{sorted(set(self.seated_ids) & self.answered_and_gone)}",
        )
        # **Empty is a court the filler is alone on** (``docs/adr/0162`` §6):
        # a singles opponent who left, or a four three people left. Such a fill
        # locks nobody and is still a fill — it names the challenge, exempts
        # its pair and excludes the departed.


@runtime_checkable
class HalfBuiltCourtQuery(Protocol):
    """*Which court is this, who is on it, and who has already answered it?*

    **A sixth demand rather than a method on ``MatchHistoryQuery``, and the
    posture is the reason.** That port is history and every read on it fails
    **soft**: losing a game because we could not remember who you played in March
    is worse than a duller list. This one fails **closed**, because a fill that
    cannot read the court it is completing has nothing to complete — it would
    silently become an ordinary ⚡ over a pool that still excludes the very people
    it was meant to seat around. One port, one posture, and the table below is
    where that is said.

    **It is asked once per fill and on no other surface.** A shortlist, a deal
    and an ordinary line-up name no challenge and never reach it.
    """

    async def half_built_court(
        self, *, challenge_id: UUID, member_id: UUID
    ) -> HalfBuiltCourt | None:
        """That challenge, if this member is on its court and it is still being
        arranged.

        **``None`` covers three cases on purpose**: no such challenge, the member
        holds no live seat on it, and a court nobody is arranging any more.
        Telling them apart would answer *is this challenge id real* about a
        stranger's evening, one probe at a time — which is the posture
        ``court_origin`` already takes about a search.

        **Any live member, never only the organiser.** Growing a court and ending
        one are different acts and get different permissions (§1): the withdraw
        is the organiser's, and a mutual-born doubles court has an "organiser"
        who is only whoever's yes arrived second.

        **It takes no clock**, exactly as ``open_challenges`` takes none: whether
        a court is still being arranged is a fact about this instant, and a caller
        that could supply the instant could supply a stale one.
        """
        ...


# ---------------------------------------------------------------------------
# SharedCourtQuery — ``games``
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True)
class SharedCourt:
    """One person the searcher has a game with, and whether it is behind them yet.

    **The deck's cool-off reads this and nothing else reads it**
    (``docs/adr/0169`` §6). *Somebody you are already with is not in your deck,
    and stays out for thirty days after* — so what the matcher needs about a
    court is two facts and never the game: who the other person is, and the
    instant the court went behind them, or that it has not.

    ``behind_since`` is the moment ``docs/adr/0168`` lets a member leave the
    chat, read off the game: the entry that said *we played*, the call-off, or
    the entry window closing on silence. It is ``None`` while the court is still
    ahead — planned, on, awaiting its entry — and an ahead court is the answer
    whatever else stands between the two, because a second game arranged before
    the first is settled is a court they are *with* each other on.

    It is not :class:`PairwiseCounterpart`, deliberately. That row dates a ghost
    from its plan and files a call-off nowhere (``docs/adr/0163`` §3), both by
    decisions of their own about what *happened between you*; the cool-off asks
    a different question — *when did this court stop being ahead of you* — and
    a row answering the first cannot be bent to the second without one of the
    two decisions quietly reversing.
    """

    counterpart_id: UUID
    behind_since: Instant | None

    @property
    def ahead(self) -> bool:
        return self.behind_since is None


@runtime_checkable
class SharedCourtQuery(Protocol):
    """Every game between the searcher and anybody, as *ahead* or *behind since*.

    **One row per person, newest first, at most ``PAIRWISE_COUNTERPART_BOUND``**
    — the same bound and the same order the pairwise history keeps, over the
    same people, so a counterpart cut off by it is one with five hundred more
    recent courts ahead of them and outside any window the deck could ask about.
    A person the searcher has more than one game with is one row: an ahead court
    if any is ahead, otherwise the latest ``behind_since``.

    **Read for the deck's exclusions and for nothing else.** Find a game keeps
    ``docs/adr/0142`` §1's release — a search is a question about the city, and
    somebody you played on Saturday is a fine partner for next week's four. The
    deck is for meeting people, and a rematch is arranged in the chat the two
    already have. The radar reads it too, and only for the deck's number on
    its envelope (``docs/adr/0174`` §5): who the radar draws is untouched by
    it, and Karol from Saturday is on the map.

    **It fails soft**, like the history beside it: an outage repeats a card of
    somebody the viewer already knows, which is embarrassment and never danger,
    and standing down is the posture a courtesy takes (``FAIL_POSTURE``).
    """

    async def shared_courts(self, searcher_id: UUID) -> tuple[SharedCourt, ...]:
        """Who this searcher has a game with, and where each stands — bounded.

        The provider reads its own clock for *ahead*: whether a court is behind
        somebody is a fact about this instant, and a caller that could supply
        the instant could supply a stale one — ``open_challenges``' rule.
        """
        ...


# ---------------------------------------------------------------------------
# How each demand fails
# ---------------------------------------------------------------------------


class FailPosture(str, Enum):
    """What happens when one of these reads cannot be answered.

    **A gate that cannot be evaluated excludes; a term that cannot be evaluated
    stands down.** The two are not a spectrum and there is no third value: a
    safety control has no degraded reading, and a term has no reason to take the
    whole search down with it.
    """

    #: The search refuses. *Nobody is held* and *we could not find out* are
    #: different sentences and must not become one.
    CLOSED = "CLOSED"
    #: The term stands down, the weights renormalise, and the search proceeds.
    SOFT = "SOFT"


#: Every outward demand, and how it fails. **Exhaustive over ``MATCHER_DEMANDS``.**
#:
#: Classified in one table rather than at each call site, which is what stops the
#: next person having to guess — and it is not always the obvious guess. The
#: matcher's other reads are classified the same way and land on both sides:
#: blocks fail **closed** beside the two gates here, while the exposure and
#: suppression ledgers fail **soft**, because applying *a gate that cannot be
#: evaluated excludes* to a courtesy would empty the deck rather than protect
#: anybody.
#:
#: **The ledgers are built and are not rows here either** (#204), and the
#: sentence that said they would join this table is withdrawn rather than
#: forgotten. They arrived after ``BlockQuery`` had already made the criterion
#: explicit one paragraph up: every port below is one the matcher declares of a
#: context **it does not write**. The ledgers are the opposite extreme — the
#: matchmaking module's own ephemeral store, declared in
#: ``matchmaking/domain/ledgers.py`` and answered by adapters in the same module
#: — so their posture is asserted where those ports live, in
#: ``LEDGER_FAIL_POSTURE``, and enforced by the wrapper the composition root puts
#: round every one it hands out. A second declaration here would be a second
#: place for that posture to be set, which is the failure this table exists to
#: prevent. The shape of this file also refuses them: the register beside it
#: builds each row's implementation **over a session**, and neither ledger has
#: one.
#:
#: **Blocks are built and are deliberately not a row here** (#203). Every port
#: below is one the *matcher* declares of a context it does not write, and its
#: posture is the matcher's reading of somebody else's fact. ``BlockQuery`` is
#: the other arrangement: ADR-0095 §7 makes it the Blocks context's **own** port,
#: declared once and consulted by every surface that shows one player to another,
#: and its fail-closed posture is asserted where the port lives
#: (``modules/blocks/domain/ports.py``) rather than restated per consumer. A
#: second declaration of it here would be a second place for that posture to be
#: set, which is the failure this table exists to prevent.
#: ``AtStakeQuery``'s row is **derived rather than quoted** — the spec's table
#: predates the port and has no line for it. It follows from what the card does:
#: an unanswerable at-stake block is simply not drawn, which is what the card
#: already does when the rule does not exist, so a failure here costs a block and
#: never the search.
FAIL_POSTURE: Mapping[type, FailPosture] = {
    PlayerScoreQuery: FailPosture.SOFT,
    MatchHistoryQuery: FailPosture.SOFT,
    AtStakeQuery: FailPosture.SOFT,
    AccountHoldQuery: FailPosture.CLOSED,
    AccountStatusQuery: FailPosture.CLOSED,
    # **Closed, and it is not a gate** — which is the one row here that shows
    # the table classifies *what a failure costs* rather than *what kind of
    # fact this is*. A fill that cannot read the court it names has nothing to
    # complete: standing down would run an ordinary ⚡ over a pool still
    # excluding the people it was meant to seat around, and hand the player a
    # court with strangers where their own line-up should have been.
    HalfBuiltCourtQuery: FailPosture.CLOSED,
    # **Soft, and it is not a term either.** The cool-off is a courtesy about
    # the viewer's own deck, and *a gate that cannot be evaluated excludes*
    # applied to it would empty a deal in a city that has people in it — the
    # suppression ledger's argument, one read over. The backstop is the same
    # one the open-challenge gate leans on: a card repeated is a card, never a
    # court somebody is seated on behind their back.
    SharedCourtQuery: FailPosture.SOFT,
}

#: The seven outward ports, as the suite in ``tests/demands/`` walks them.
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
    PlayerScoreQuery,
    MatchHistoryQuery,
    AtStakeQuery,
    AccountHoldQuery,
    AccountStatusQuery,
    HalfBuiltCourtQuery,
    SharedCourtQuery,
)
