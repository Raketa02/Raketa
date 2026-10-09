"""What this context stores behind, what it reads elsewhere, and what it
publishes outward.

**Two of these are the module's own** — the repository and the directory — one
is somebody else's, and three are the platform's. ``GameHistoryQuery`` is the read
every other context in
[#302](https://github.com/Raketa02/Raketa/issues/302) was blocked on. It is
contracted in ``tests/demands/`` in ADR-0098's shape, over every registered
implementation, because *a demand nobody executes is a demand satisfied by
accident*. Its readers today are ``player_score`` (attendance and result
answering) and the player record (a sport's run of form). **Four reads went with
the ranking** (#580): who a player had arranged games with, how many counted
games each of a list had played, the last five results across every sport, and
the threshold a late change would be measured against — read by the matcher and
a search card alone.

**Fewer than five results is a real answer and is never padded.** The card draws
a gap; a fifth invented row would be the same mistake in a smaller place.

**``OpponentVarietyQuery`` is a separate port and not a fourth fact on the history
read**, and the split is a fence rather than a filing decision. The run of form
there is bounded at five; that one is deliberately unbounded, because *how
widely do they spread their games* is a career statistic and a window would be a
second horizon nothing keeps in step with the others. An unbounded fold on a
port a caller already holds is one somebody eventually calls inside a walk, so it
answers about one player, in a type only the surface that opens one person at a
time is handed.

**``PlayerNames`` is the one port here this context consumes rather than
offers**, and it is a single field wide on purpose. A game says who was on the
court, and until it carried a name it said so in ids — which left the screens
naming *sides* and a result agreed with nobody
(``docs/adr/0141``). What it does **not** borrow is a card: a Level, a band, an
area and a run of form are what a searcher reads to decide about a game that
might happen, and this is the record of one that did.

**``CourtPairing`` is the second port consumed here, and it is read *beside* the
game rather than on it** (``docs/adr/0161``). The seat still carries the name
and nothing else; what this port answers — the forecast, the split, what is at
stake, each seat's Level — is computed for the reader when the screen is opened,
for as long as the game has not happened, and is stored nowhere. It is declared
in this context's own words because ``games`` may not import the matcher
(``.importlinter``), and the adapter that signs it lives on the matcher's side of
that arrow. No ``Forecast``, no ``Split`` and no ``Stakes`` is borrowed from the
engines: a provider that reached for the type one directory over would be the
second-spelling trap the contract's own comment names.

**``attendance_for`` and ``result_answering_for`` are the two reads here that
answer about fewer people than they were asked about**, and the exception proves
the rule above rather than bending it (``docs/adr/0140``, ``docs/adr/0160``).
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

from app.kernel import Instant, Sport, invariant
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, LineUp
from app.modules.games.domain.results import Outcome

#: How many results *Last 5* draws. The card's own number, and the only place it
#: is written on this side of the wire.
RECENT_RESULTS = 5


@final
class PlayedOutcome(str, Enum):
    """How an arrangement settled for the people on its court.

    **A ghost is kept distinguishable from a game**, because *shows up* charges
    a ghost and credits a game (``Attendance``).
    """

    PLAYED = "PLAYED"
    PLANNED_NEVER_PLAYED = "PLANNED_NEVER_PLAYED"


@final
@dataclass(frozen=True, slots=True)
class Attendance:
    """What became of the games one player was arranged into. **Per person.**

    The *shows up* strand's whole input (``docs/adr/0140``). ``played`` is games
    somebody on that court said had happened; ``ghosts`` is plans whose entry
    window closed with nobody ever saying so. A game still inside its entry
    window is in **neither**: it is not a ghost until the clock says so, and
    claiming it either way would publish a conclusion nothing has reached.

    **Counted and friendly games are both here.** Turning up is not evidence
    about anybody's Level, so the choice that makes a game a friendly has nothing
    to say about whether the people who arranged it came.

    **This is a per-player read and never a sum over pairs.** A four played once
    is one game and three counterparts, so adding up pairs would charge a doubles
    player three times for one evening and make *shows up* a statement about how
    many people they play with.

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

    The *answers about results* strand's whole input (``docs/adr/0160``).
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
    like — ``bookings``' ``KeepingRecord`` is a third one (#544) — and a shared
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

    **A second port rather than a fourth fact on ``GameHistoryQuery``, and the
    split is the fence.** That port's set reads are asked about lists of people;
    this fold is deliberately **unbounded**, because a career statistic that
    stopped at a window would be a second horizon. An unbounded fold on a port a
    caller already holds for a list is an invitation to call it inside that
    walk. So it is handed only to the consumer that opens one person at a time.

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
class ScoredGames(Protocol):
    """Which of some games had a score put on their table lately — **ids, and
    nothing folded** (#613).

    **The read that exists because a correction re-dates a score.** A score
    waits for its answer a day from when it was last put on the table, and its
    side may correct it again while the other side has not answered, so a game
    played long ago can still be waiting on somebody
    (``windows.scores_still_waiting_since``). A reader that bounds its read by
    the game's hour — Home — asks this about the games it left out, and folds
    only the few named.

    **It answers about the games asked about, by id**, so its cost is the
    reader's own games and never the platform's.
    """

    async def scored_since(
        self, game_ids: Collection[UUID], *, since: Instant
    ) -> frozenset[UUID]:
        """Those of these games a score was proposed, corrected or countered
        on at or after ``since`` — one question about the set; a game that does
        not exist is absent."""
        ...


@runtime_checkable
class ClubCheckIns(Protocol):
    """*Who did the club see arrive?* — this context's demand on whoever keeps
    a booking (#547; the mechanics §15.1, §16.10).

    A player the club's desk checked in **can never be reported as not
    turning up**, and the scan is the booking's fact, recorded where the desk
    made it; so this context asks for it rather than keeping a copy that could
    disagree. **Keyed by the id the game was opened under** — a booked game's
    ``challenge_id`` is its booking's id, the field keeping the name it was
    born with — so the caller asks in a currency it already holds. A game with
    no booking behind it has no desk, and nobody on it was checked in.
    """

    async def checked_in(self, challenge_id: UUID) -> frozenset[UUID]:
        """Everybody the club checked in to the game opened from
        ``challenge_id`` — empty when there is no booking behind it."""
        ...


@runtime_checkable
class GameRepository(Protocol):
    """One game's stream, loaded and appended to."""

    async def load(self, game_id: UUID) -> Game | None: ...

    async def save(self, game: Game) -> None: ...

    async def for_challenge(self, challenge_id: UUID) -> Game | None:
        """The game a booking already opened, if one has — ``challenge_id`` is
        the booking's id, under the name the field was born with.

        **One arrangement is one game**, and the opening runs in the transaction
        of the fill — so the read that makes it idempotent belongs beside the
        write rather than in the caller. It is not a lookup by payload the way
        the directory is: it answers about one booking and returns one game.
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
class PlayerNames(Protocol):
    """What the people on a court are called. **The one thing this context
    borrows about a person, and the whole of it.**

    A game is a record of an evening, and ``docs/adr/0141`` fixes what a record
    may say about the people in it: the **name** they gave, and nothing that
    changes with who is looking or with when you ask. The name and not the
    nickname (``docs/adr/0171`` §4) — the nickname is a handle, drawn on a
    record and their own You tab and said nowhere. So there is one method here
    and there is nowhere on it for a Level, an area or a photograph to arrive
    later — a card is what a *search* attaches, where a gate decided the person
    may be shown at all.

    **One call for a whole list, never one per seat**, which is the shape every
    set read in this codebase takes: reading four games costs one question about
    at most sixteen people rather than sixteen questions.
    """

    async def names_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each of these players' name, as one set read.

        **A player absent from the answer keeps their seat.** A card with no
        name is not a card and the shortlist drops that row; a *seat* with no
        name is still a person who was on the court, and dropping it would
        publish a three-person doubles game. The name goes ``None`` on the
        wire, the screen says the side, and the game is unchanged — which is the
        same fall-back a Play court already draws for a seat whose row the record
        can no longer describe. A null there never means *unnamed*: the gate
        holds an unnamed account at the naming step (``docs/adr/0171`` §4).
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class SeatLevel:
    """One seat's Level, as ``rating`` published it — and nothing else about them.

    The four figures a record's skill panel and a player card already print:
    the Level, the band's published name, the likely range the engine rounded,
    and the certainty as a whole percentage. **This is not a card.** No area, no
    Player Score, no photograph, no distance, no run of form — a card is what a
    searcher reads to decide about a stranger, and these people are on your
    court. Nothing here is derived: a band a consumer worked out from a Level
    would be a second set of drawing constants.
    """

    player_id: UUID
    level: float
    band: str
    range_low: float
    range_high: float
    confidence: int


@final
@dataclass(frozen=True, slots=True)
class CourtForecast:
    """How even this court's game is forecast to be, read in the reader's direction.

    ``provisional`` travels **inside** the forecast, on the engine's own rule:
    the failure guarded against is a screen showing the number without its
    caveat. It is never ``True`` on a game today — a line-up is frozen at the
    plan, so no side is short — and the field is kept because the shape is the
    court's; when a seat can be open, the answer is an **absence** rather than a
    provisional figure (``docs/adr/0161`` §4).
    """

    pct: int
    sigma_group: float
    provisional: bool
    assumption: str | None

    def __post_init__(self) -> None:
        invariant(0 <= self.pct <= 100, f"a forecast of {self.pct}%")


@final
@dataclass(frozen=True, slots=True)
class CourtSplit:
    """The two side strengths the forecast was read from, **in the reader's
    direction**: ``your_side`` is theirs wherever they sit.

    ``gap`` is a property and signed — ``your_side − their_side`` — so two
    readers on opposite sides see the sign flip and nobody can construct a gap
    its own two strengths do not make.
    """

    your_side: float
    their_side: float

    @property
    def gap(self) -> float:
        return self.your_side - self.their_side


@final
@dataclass(frozen=True, slots=True)
class LevelDeltas:
    """What a **counted** game on this court would do to the reader's Level.

    The rule read forward, side against side, so it is the pair the result will
    deliver — including what the rule does about an unrated seat, which is to
    fold a side over the people on it who hold a rating. Never a pair of zeros:
    absent on a friendly, where a counted result is meaningless rather than
    unavailable, and absent where the rule has nothing to move or nothing to
    price against.
    """

    win_delta: float
    loss_delta: float

    def __post_init__(self) -> None:
        invariant(
            self.win_delta > 0 > self.loss_delta,
            "a counted result that changes nothing or moves the wrong way: "
            f"+{self.win_delta} / {self.loss_delta}",
        )


@final
@dataclass(frozen=True, slots=True)
class Pairing:
    """What the matcher makes of this court, for one reader, at one instant.

    **The forecast and the split are present together or absent together**,
    because they are one computation: the percentage and the two strengths it
    was read from. Absent when the pairing cannot be computed — the reader holds
    no rating or no declaration in the sport, a seat cannot be priced — and
    there is deliberately **no reason beside the absence**: the game screen
    draws nothing and says nothing.

    ``seats`` is whoever on the court holds a rating in the sport, in the
    line-up's own order. A court with an unrated member still names the Levels
    of the rated ones.
    """

    seats: tuple[SeatLevel, ...]
    forecast: CourtForecast | None = None
    split: CourtSplit | None = None
    at_stake: LevelDeltas | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.forecast is None) == (self.split is None),
            "a forecast without the split it was read from, or the reverse",
        )


@runtime_checkable
class CourtPairing(Protocol):
    """*What does this platform make of my court?* — for the reader, right now.

    An outward demand on the matcher, signed by an adapter that lives on the
    matcher's side of the arrow (``docs/adr/0161``). The game screen needs a
    forecast and cannot go and get one: ``games`` may not import
    ``matchmaking``, and the balance forecast a Games card prints already
    lives there — this port is how it is reused rather than built a second
    time, read side against side from the people's Levels (#575).

    **Recomputed, never replayed, and nothing is recorded.** A game carries no
    pairing and never will; the answer is as-of-now and means what a card means
    *because this game has not happened*, which is why the caller asks only
    while it has not.

    **A seat with no Level costs the forecast and never the other Levels**,
    because a Level is a fact about a person and not about the pairing that
    could not be computed.

    **Nothing here re-gates.** The court is the whole of the permission
    (``docs/adr/0141``, ``docs/adr/0143`` §2). What makes that safe is the
    recompute: a seat that cannot be priced today has no figure, with no trace.
    """

    async def pairing_for(
        self,
        *,
        sport: Sport,
        kind: GameKind,
        line_up: LineUp,
        reader_id: UUID,
    ) -> Pairing | None:
        """The pairing for this court, computed for this reader, **right now.**

        ``line_up`` is the frozen court — who sits where — and ``reader_id`` is
        on it; which side is *yours* is read off the line-up and never sent.
        There is no instant to pass: nothing here is folded against a clock,
        and the provider reads its own for the one thing that is bounded by
        one (the index's staleness).

        ``kind`` crosses so that a friendly is never priced: asking what a
        counted game is worth on a court that will not be counted is a category
        error, and the port refuses it by not being asked. The caller holds
        the same rule as an invariant, so a provider that priced one anyway is
        loud rather than rendered.

        ``None`` means **the Levels themselves could not be read** and is the
        one answer that carries nothing. A ``Pairing`` with the forecast absent
        means the seats were read and the matcher could not price the court —
        because there was nothing to compute, or because it could not be
        reached. The wire does not tell those apart, by decision; the log does.
        """
        ...


@runtime_checkable
class GameHistoryQuery(Protocol):
    """The three facts this context owes the rest of the platform about what
    became of a player's games."""

    async def recent_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[CountedResult, ...]:
        """One player's last few counted results **in one sport**, oldest first.

        What a record sheet draws beneath a single sport's Level, where a run
        built across every sport would be squash results under a padel number.

        **Filtered before it is trimmed**: a read that answered the last
        ``RECENT_RESULTS`` across every sport and was narrowed afterwards would
        show three results to somebody who has played thirty.

        **One player and never a collection.** A record is one person opened by a
        deliberate tap.

        At most ``RECENT_RESULTS``, and **fewer is a real answer that is never
        padded**. Empty for a player with none — a short tuple already says the
        whole of *there is less to show*.
        """
        ...

    async def attendance_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, Attendance]:
        """What became of each of these people's arrangements — played, or ghosted.

        **A player with none is absent from the answer, because a zero here would
        be invented**: a ``0/0`` would say *this person was due somewhere and did
        not come*, which is a claim about a record nobody keeps
        (``docs/adr/0098``).

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
        (``docs/adr/0160``). A game's own three clocks are in ``windows.py`` and
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


__all__ = [
    "RECENT_RESULTS",
    "Attendance",
    "ConfirmedGame",
    "ConfirmedResultLedger",
    "CountedResult",
    "CourtForecast",
    "CourtPairing",
    "CourtSplit",
    "LevelDeltas",
    "Pairing",
    "SeatLevel",
    "GameDirectory",
    "GameHistoryQuery",
    "GameRepository",
    "OpponentVariety",
    "OpponentVarietyQuery",
    "PlayedOutcome",
    "PlayerNames",
    "ResultAnswering",
]
