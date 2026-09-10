"""What this context stores behind, what it reads elsewhere, and what it
publishes outward.

**Two of these are the module's own** — the repository and the directory — one
is somebody else's, and three are the platform's. ``GameHistoryQuery`` is the read
every other context in
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

**``OpponentVarietyQuery`` is a separate port and not a sixth fact on the history
read**, and the split is a fence rather than a filing decision. Every read there
is bounded — five results, five hundred counterparts — because its caller holds
twenty rows and asks once; that one is deliberately unbounded, because *how
widely do they spread their games* is a career statistic and a window would be a
second horizon nothing keeps in step with the matcher's. An unbounded fold on the
port a search already holds is one somebody eventually calls inside that walk, so
it answers about one player, in a type only the surface that opens one person at
a time is handed.

**``PlayerHandles`` is the one port here this context consumes rather than
offers**, and it is a single field wide on purpose. A game says who was on the
court, and until it carried a handle it said so in ids — which left the screens
naming *sides* and a result agreed with nobody
(``docs/adr/0141``). What it does **not** borrow is a card: a Level, a band, an
area and a run of form are what a searcher reads to decide about a game that
might happen, and this is the record of one that did.

**``attendance_for`` and ``result_answering_for`` are the two reads here that
answer about fewer people than they were asked about**, and the exception proves
the rule above rather than bending it (``docs/adr/0140``, ``docs/adr/0156``).
Both are ``player_score``'s inputs — *shows up* and *answers about results* —
where a ``0/0`` would say *this person was due somewhere and did not come* about
somebody nothing was ever arranged for, and *this person ignored a score* about
somebody nobody ever sent one to. The two rules live in one class deliberately,
so that a reader meets the difference instead of rediscovering it.
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
class Attendance:
    """What became of the games one player was arranged into. **Per person.**

    The *shows up* strand's whole input (``docs/adr/0140``). ``played`` is games
    somebody on that court said had happened; ``ghosts`` is plans whose entry
    window closed with nobody ever saying so. A game still inside its entry
    window is in **neither**, for the reason the pairwise fold gives: it is not a
    ghost until the clock says so, and claiming it either way would publish a
    conclusion nothing has reached.

    **Counted and friendly games are both here.** Turning up is not evidence
    about anybody's Level, so the choice that makes a game a friendly has nothing
    to say about whether the people who arranged it came.

    **This is a per-player read and never a sum of the pairwise one.** A four
    played once is one game and three counterparts, so adding up
    ``played_counterparts`` would charge a doubles player three times for one
    evening and make *shows up* a statement about how many people they play with.

    ``last_at`` is when the most recent of those opportunities **closed** — the
    moment a game was played, or the moment a plan's entry window shut on
    silence. It is the strand's observation moment, and dating a ghost from the
    plan instead would age a record faster than the record aged.
    """

    played: int
    ghosts: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.played >= 0 and self.ghosts >= 0,
            f"a negative arrangement count: {self.played} played, "
            f"{self.ghosts} ghosts",
        )
        invariant(
            self.played + self.ghosts >= 1,
            "an attendance record with no settled arrangement behind it is an "
            "absence, not a zero — absence is spelled by not being in the answer",
        )


@final
@dataclass(frozen=True, slots=True)
class ResultAnswering:
    """What one player did about the scores put in front of them. **Per person.**

    The *answers about results* strand's whole input (``docs/adr/0156``).
    ``answered`` is scores they accepted or countered inside the window;
    ``ignored`` is scores whose window ran out with nothing said. A score still
    inside its window is in **neither** — the answer is still wanted, and filing
    it either way would publish a conclusion the clock has not reached.

    **The denominator is scores put in front of *them*, and never games.** The
    side that entered the score is asked nothing, and once both sides have put a
    score up the argument is capped — so a counter is the asked side's answer and
    never a second question put back to the opener. That is the whole difference
    from the strand ``docs/adr/0137`` struck: **nobody is docked for
    disagreeing**, because there is no state a person reaches by holding their
    position that this read files as a miss.

    **A counter is a good outcome**, which makes this the second strand on this
    platform where saying *no* scores, after *answers challenges*. What is priced
    is silence, not judgement — and here the judgement being protected is
    ADR-0049's: *no player is penalised for not agreeing a result.*

    **Counted and friendly games are both here.** A score put in front of you is a
    question whether or not the evening was evidence about anybody's Level.

    ``last_at`` is the most recent moment one of those opportunities closed — the
    instant something was said, or the deadline that passed in silence.

    **It is the same shape as ``Attendance`` above and is deliberately not the
    same type.** Three counts and a moment is what an opportunity record looks
    like — ``challenges``' ``AnsweringRecord`` is a third one — and a shared
    ``Opportunity(good, missed, last_at)`` would be a type whose field names could
    not say *played* or *ghosted* or *ignored*. The words are the whole content of
    these rows: a reader of the fold has to know that a ghost is charged to a
    whole court and an ignored score only to the side it faced, and a generic pair
    is exactly where that stops being visible. The cost is two invariants spelled
    twice, and it is smaller than the cost of the alternative.
    """

    answered: int
    ignored: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.answered >= 0 and self.ignored >= 0,
            f"a negative score count: {self.answered} answered, "
            f"{self.ignored} ignored",
        )
        invariant(
            self.answered + self.ignored >= 1,
            "an answering record with no closed score behind it is an absence, "
            "not a zero — absence is spelled by not being in the answer",
        )


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


@final
@dataclass(frozen=True, slots=True)
class ConfirmedGame:
    """One **counted** game whose result is final, from nobody's point of view.

    The shape the rating context reads forward (``docs/adr/0139``). It carries the
    two sides rather than an outcome per player, because a result is a fact about
    a game and which side you were on — four per-player rows would be four copies
    of one score, and the day two of them disagreed there would be nothing to say
    which lied.

    ``confirmed_at`` is **when the result became final**, not when it was entered:
    an acceptance's grace, or a proposal window closing on silence. Derived, so it
    is the same instant on every reader's clock — which is what makes it safe to
    order a catch-up on.

    **Tuples and not sets.** The order is the line-up's own, so a walk over this
    is the same walk on every process and under every ``PYTHONHASHSEED``
    (``docs/adr/0105``).
    """

    game_id: UUID
    sport: Sport
    winners: tuple[UUID, ...]
    losers: tuple[UUID, ...]
    played_at: Instant
    confirmed_at: Instant

    def __post_init__(self) -> None:
        invariant(
            bool(self.winners) and bool(self.losers),
            "a confirmed result with an empty side: a score names a winner and "
            f"somebody it was won against ({len(self.winners)}/{len(self.losers)})",
        )


@final
@dataclass(frozen=True, slots=True)
class OpponentVariety:
    """How many different people one player's counted games were played against.

    **A pair and never a share.** The division is a drawing decision and the two
    counts are the fact: *fourteen of twenty* and *seven of ten* are the same
    percentage and different claims, and a reader told only the percentage cannot
    tell which one they are looking at.

    ``distinct_counterparts`` counts **everybody who was on a court with them**,
    partner included, on ``LineUp.counterparts_of``'s own rule that *a pair is
    anybody you were on a court with*. A figure counting opponents alone would
    say that somebody who partners the same person every week spreads their games
    as widely as somebody who does not.

    **The denominator is people met and never games played**, and that is the
    correction rather than a preference. A game was the denominator first, and it
    is only divisible in singles: a doubles evening puts three people on the
    court, so one game produced ``3 of 1`` — a fraction whose numerator exceeds
    its denominator, which a client could only render by clamping the share at a
    hundred and printing a pair that reads as nonsense. Counting the **seats
    opposite** instead makes the two halves the same kind of thing: *five
    different people across ten times on a court* is the sentence, and the share
    is a share.

    **Both halves are read off the same games**, which is what keeps the pair
    coherent: a friendly and a ghost are in neither, so a player with forty
    friendlies and two counted games cannot be described as playing twenty
    different people an evening.
    """

    distinct_counterparts: int
    times_on_court: int

    def __post_init__(self) -> None:
        invariant(
            self.times_on_court >= 1,
            "a variety over no counted game is an absence, not a nought — "
            "absence is spelled by not being in the answer at all",
        )
        invariant(
            self.distinct_counterparts >= 1,
            "a counted game somebody played alone: "
            f"{self.distinct_counterparts} people over "
            f"{self.times_on_court} times",
        )
        invariant(
            self.distinct_counterparts <= self.times_on_court,
            "more different people than seats they sat opposite: "
            f"{self.distinct_counterparts} over {self.times_on_court}. It is "
            "what the denominator being a count of **games** could not say, "
            "and a doubles evening broke it every time",
        )


@runtime_checkable
class OpponentVarietyQuery(Protocol):
    """*How widely does this person spread their games?* — over the whole record.

    **A second port rather than a sixth fact on ``GameHistoryQuery``, and the
    split is the fence.** That port is held by a caller that walks twenty rows
    and, for the pairwise read, five hundred counterparts; this fold is
    deliberately **unbounded**, because a career statistic that stopped at a
    window would be a second horizon that must not disagree with the matcher's.
    An unbounded fold on the same port a search already holds is an invitation to
    call it inside that walk. So it is handed only to the consumer that opens one
    person at a time.

    **One player and never a collection**, stated in the signature and asserted
    there. There is no set-shaped version of this to reach for.

    **Cost.** Bounded by how many games this player has ever been seated in — the
    same profile as every other read in this context, because the fold *is* the
    answer.
    """

    async def variety_of(
        self, player_id: UUID, *, now: Instant
    ) -> OpponentVariety | None:
        """Their different faces and their counted games, or **nothing at all**.

        ``None`` for a player no counted game has been recorded for, which is
        this platform's one spelling for *we watched nothing*. A ``0`` would be a
        habit nobody has, and a ``0 / 0`` would be arithmetic nobody can draw.

        ``now`` is taken rather than read for the reason every fold here takes
        it: whether a game was played is folded from the record against a clock,
        and one response's facts are folded against one instant.
        """
        ...


@runtime_checkable
class ConfirmedResultLedger(Protocol):
    """Every counted game that has reached an agreed score, **oldest first.**

    **The read that exists because nothing announces a confirmation.** ADR-0137
    refused a ``ResultConfirmed`` event on the grounds that a derived standing has
    exactly one place to be true, and recorded the cost: the rating context has
    nothing to subscribe to and must read results forward instead. This is that
    read.

    **Oldest first is the contract, not a convenience.** A Level is moved against
    the Levels as they stood, so applying Tuesday's result after Thursday's would
    produce a different rating for the same history — and nothing would ever say
    so.

    **It takes no cursor, and the rating's own stream is the cursor.** Each move a
    rating records carries the game that caused it, so *have I applied this* is
    answerable by replaying the aggregate that would be changed — which is one
    fewer thing to be stale, one fewer table, and immune to a catch-up that dies
    half way. A cursor column would be a second record of progress, and the first
    one to be wrong would be the one nothing could check.

    **Cost.** Bounded by how many games the platform has ever recorded, like every
    other read in this context and for the same reason: the fold *is* the answer.
    The index that fixes it belongs with the first query that measures it.
    """

    async def confirmed_counted_results(
        self, *, now: Instant
    ) -> tuple[ConfirmedGame, ...]:
        """Every counted game confirmed by this instant, in settlement order.

        **Counted only, and confirmed only.** A friendly is absent because it was
        never evidence about anybody by the choice of the people who arranged it;
        an unscored game is absent because *an evening is not evidence*. Both
        absences are the same absence a caller needs — everything returned here
        may move a Level, and nothing else may.
        """
        ...


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
class PlayerHandles(Protocol):
    """What the people on a court are called. **The one thing this context
    borrows about a person, and the whole of it.**

    A game is a record of an evening, and ``docs/adr/0141`` fixes what a record
    may say about the people in it: the handle they chose, and nothing that
    changes with who is looking or with when you ask. So there is one method here
    and there is nowhere on it for a Level, an area or a photograph to arrive
    later — a card is what a *search* attaches, where a gate decided the person
    may be shown at all.

    **One call for a whole list, never one per seat**, which is the shape every
    set read in this codebase takes: reading four games costs one question about
    at most sixteen people rather than sixteen questions.
    """

    async def handles_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each of these players' handle, as one set read.

        **A player absent from the answer keeps their seat.** A card with no
        nickname is not a card and the shortlist drops that row; a *seat* with no
        nickname is still a person who was on the court, and dropping it would
        publish a three-person doubles game. The handle goes ``None`` on the
        wire, the screen says the side, and the game is unchanged — which is the
        same fall-back a Play court already draws for a seat whose row the record
        can no longer describe.
        """
        ...


@runtime_checkable
class GameHistoryQuery(Protocol):
    """The six facts this context owes the rest of the platform, and the seventh
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

    async def recent_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[CountedResult, ...]:
        """One player's last few counted results **in one sport**, oldest first.

        **A second read and not a parameter on the one above**, because the two
        answer for different callers and one of them must not move. The set read
        is what a *search* attaches to twenty rows and freezes into a record kept
        for ever; narrowing it to a sport would make the same person's card read
        differently before and after, which is a change worth making deliberately
        rather than as a side effect. This one is what a record sheet draws
        beneath a single sport's Level, where a run built across every sport is
        squash results under a padel number.

        **Filtered before it is trimmed**, which is the whole reason a caller
        cannot build this from the set read: that one answers at most
        ``RECENT_RESULTS`` across every sport, so a consumer filtering afterwards
        would show three results to somebody who has played thirty.

        **One player and never a collection.** A record is one person opened by a
        deliberate tap; a set-shaped version of this would be an invitation to
        call it inside a walk over five hundred candidates.

        At most ``RECENT_RESULTS``, and **fewer is a real answer that is never
        padded**. Empty for a player with none — which needs no second spelling
        here, unlike the mapping above, because a short tuple already says the
        whole of *there is less to show*.
        """
        ...

    async def attendance_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, Attendance]:
        """What became of each of these people's arrangements — played, or ghosted.

        **A player with none is absent from the answer, and this is the one read
        here whose zero would be invented.** ``counted_games_for`` beside it
        answers ``0`` for everybody it was asked about, because the games were
        counted and none of them was theirs; here a ``0/0`` would say *this
        person was due somewhere and did not come*, which is a claim about a
        record nobody keeps. The two rules sit in one class deliberately, so the
        difference is read rather than rediscovered (``docs/adr/0098``).

        Its reader is ``player_score``, which turns it into the *shows up*
        strand. The strand's arithmetic is not here: this context knows what
        happened to its own games and has no opinion about what that says about a
        person.
        """
        ...

    async def result_answering_for(
        self, player_ids: Collection[UUID], *, since: Instant, now: Instant
    ) -> Mapping[UUID, ResultAnswering]:
        """What each of these people did about the scores put in front of them.

        **A player with none is absent from the answer**, the second read here
        whose zero would be invented: somebody nobody has ever put a score to has
        not ignored one.

        **``since`` is the caller's window and never this context's**
        (``docs/adr/0156``). A game's own three clocks are in ``windows.py`` and
        are what a player is promised; *how far back a strand remembers* is a
        judgement about what a record is worth, and it belongs to the context
        that publishes the strand. This read answers about opportunities that
        closed at or after that instant, and holds no opinion about which instant
        it should be.

        Its reader is ``player_score``. The arithmetic is not here: this context
        knows what happened to its own games and has no opinion about what that
        says about a person.
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
    "Attendance",
    "ConfirmedGame",
    "ConfirmedResultLedger",
    "CountedResult",
    "GameCounterpart",
    "GameDirectory",
    "GameHistoryQuery",
    "GameRepository",
    "OpponentVariety",
    "OpponentVarietyQuery",
    "PlayedOutcome",
    "PlayerHandles",
    "PlayedTally",
    "ResultAnswering",
]
