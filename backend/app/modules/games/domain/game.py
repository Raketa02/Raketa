"""The Game aggregate — one arranged game, its result inside it, event-sourced.

**A game is born from a completed line-up, and a result is the record that it
happened** (``docs/adr/0137``). Four acceptances used to leave no fact behind;
now they leave this. Until somebody says *we played* the game is a plan, and past
its entry window a plan nobody claimed is a **ghost** — the outcome familiarity
must be able to tell from a real one.

**Nothing here stores a standing.** ``standing_at`` folds the record against a
clock the caller supplies, so *is this confirmed* answers the same at every
instant, including the whole gap between a deadline passing and anybody looking.
There is no sweep, because there is nothing for one to correct — and no
``ResultConfirmed`` event, because a derived standing has exactly one place to be
true.

**The line-up is frozen until somebody leaves it** (``docs/adr/0162``). Two
acts move it and both are told by ``challenges`` in the transaction of the act
that caused them: ``vacate`` opens one seat, and ``reseat`` replaces the whole
court once a completed line-up arrives for it. Neither moves ``planned_at`` —
it keeps meaning *when it became a game* — and neither is a standing: a court
with an open seat is still awaiting its entry. What an open seat changes is who
may act, and that a result is refused until the seat is filled.

**And a court with a seat open can be called off** (``docs/adr/0163``). ``call_off``
is the third act told by ``challenges`` — in the transaction of *Call it off*,
or of the departure that left one player on the court (``docs/adr/0165`` §3),
each of which records the court's own ending beside it (``docs/adr/0172`` §1) —
and the only act here that announces an end: ``CALLED_OFF`` is the fourth end, a
decision a person took, folded off ``GameCalledOff`` and read before the clock,
**and it says who** (``called_off_by``, ``docs/adr/0172`` §4). It is neither an
evening nor a ghost, and every read that counts either leaves it out.

**A called-off game's card can be cleared, per player** (``docs/adr/0172`` §5).
``dismiss`` is the reader's own act — the first act here that is not about the
game as a whole — recorded once per player and folded into a set the rail's
read subtracts its reader from. Nothing else folds it.

**One aggregate per game and never one per player.** Whether you won is a
property of the game and of which side you were on; a per-player record would be
four copies of one score, and the day two of them disagreed there would be
nothing to say which lied.

**What it refuses** is in ``errors.py``, and every refusal is one of two rules:
*the people who may act are the people who were on the court*, and *each side
answers once, in front of the other*. Everything else this context knows is
derived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.games.domain.answering import (
    ScorePutToASide,
    score_put_to_a_side,
)
from app.modules.games.domain.errors import (
    AcceptingYourOwnSidesResult,
    AResultMustCarryAScore,
    GameIsNotCalledOff,
    NobodyHasProposedAResult,
    NotAGameToCallOff,
    TheCourtHasAnOpenSeat,
    TheEntryWindowHasClosed,
    TheGameIsNotOpenToSeating,
    TheGameWasCalledOff,
    TheOtherSideHasAnswered,
    TheResultIsAlreadyAccepted,
    TheResultIsSettled,
    YouWereNotOnThisCourt,
    YourSideHasAlreadyAnswered,
)
from app.modules.games.domain.events import (
    GameCalledOff,
    GameDismissed,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
    SeatVacated,
)
from app.modules.games.domain.lineup import GameKind, LineUp, GameSide
from app.modules.games.domain.results import Outcome, Score
from app.modules.games.domain.standing import (
    PLAYED,
    SETTLED,
    Acceptance,
    Proposal,
    GameStanding,
    agreed_score,
    live_acceptance,
    settled_at,
    standing_of,
)
from app.modules.games.domain.windows import entry_closes_at
from app.modules.player_profile.domain.availability import Window
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Game:
    """One arranged game, rebuilt by folding its stream."""

    game_id: UUID
    #: The challenge whose line-up completed into this game. Kept so a support
    #: question about *which ask did this come from* has an answer, and so a
    #: second game can never be opened for one arrangement.
    challenge_id: UUID
    sport: Sport
    kind: GameKind
    #: The window the challenge was sent under, or ``None`` on a mutual-born
    #: one. **The type and not its code**, the way ``Challenge`` holds it: the
    #: code is a storage detail of the event, and a field left as a string is a
    #: field every reader has to remember to widen.
    window: Window | None
    line_up: LineUp
    planned_at: Instant
    #: When somebody said it happened, and ``None`` while nobody has. **This is
    #: the moment**, and there is no other one anywhere in this context.
    played_at: Instant | None
    #: When somebody called it off, or ``None`` because nobody has. **The one
    #: thing about a game that is not a reading of the record and the clock**
    #: (``docs/adr/0163``) — a decision somebody took, folded off
    #: ``GameCalledOff`` and read by ``standing_at`` before anything else, in
    #: the shape of the challenge's recorded conclusion and for its reason: an
    #: instant rather than a flag, because the client shelves the ending card
    #: from it.
    called_off_at: Instant | None
    #: Who called it off, or ``None`` because nobody has — folded off the same
    #: event's ``called_by``, the field ``docs/adr/0163`` §4 kept for the day a
    #: design wanted the name, which is ``docs/adr/0172`` §4. The presser, who
    #: still holds a seat; or the leaver, whose seat is the open one — which is
    #: how a departure is told from a press with no second field.
    called_off_by: UUID | None
    #: Everybody who has cleared this game's card from their own rail
    #: (``docs/adr/0172`` §5), folded off ``GameDismissed``. Read by the rail's
    #: fold, which subtracts its reader, and by nothing else; once per player,
    #: which is what makes a second dismissal write nothing.
    dismissed: frozenset[UUID]
    #: Whose leaving opened the seats that are open now. Folded off
    #: ``SeatVacated`` and emptied by a re-seat — a re-seat is a whole court,
    #: and nobody's departure is still on it. **It exists for one act**: the
    #: departure that leaves one player on the court calls the game off, told by
    #: ``challenges`` in the departure's own transaction, and ``called_by`` is
    #: the leaver (``docs/adr/0165`` §3) — who has, by then, been vacated. *The
    #: people who may act are the people who were on the court*, and somebody
    #: whose seat is the open one was.
    departed: frozenset[UUID]
    #: At most one per side. A ``Mapping`` rather than a list, because the cap is
    #: the shape: there is nowhere here to put a third score.
    proposals: dict[GameSide, Proposal]
    acceptance: Acceptance | None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id. **Minted, and carried on the opening event.**"""

        return self.game_id

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # -- opening ----------------------------------------------------------

    @classmethod
    def planned(
        cls,
        *,
        game_id: UUID,
        challenge_id: UUID,
        sport: Sport,
        kind: GameKind,
        window: Window | None,
        line_up: LineUp,
        occurred_at: Instant,
    ) -> "Game":
        """Open a game from a line-up that has just completed.

        Everything constitutive is chosen here and never recomputed: who played,
        on which side, in which sport, and whether the evening is evidence. The
        clock starts now, because *now* is when the people agreed to play — the
        only date-like fact a challenge produces.
        """

        game = cls._empty()
        game._record_that(
            GamePlanned(
                game_id=game_id,
                challenge_id=challenge_id,
                sport=sport.value,
                kind=kind.value,
                window=None if window is None else window.value,
                seatings=line_up.codes,
                occurred_at=occurred_at,
            )
        )
        return game

    # -- the line-up ------------------------------------------------------

    def vacate(self, player_id: UUID, *, occurred_at: Instant) -> None:
        """Somebody on the court leaves the game. **Their seat opens.**

        Told by ``challenges`` in the transaction of the departure, which has
        already asked the moment guard; what this refuses is the aggregate's
        own half of it — a game that is not awaiting its entry has a line-up
        that is the record of an evening, and nothing on it moves — and somebody
        who is not on the court, which is the one refusal shared with every act
        here.
        """

        self._side_of(player_id)
        if self.standing_at(occurred_at) is not GameStanding.AWAITING_ENTRY:
            raise TheGameIsNotOpenToSeating()
        self._record_that(
            SeatVacated(
                game_id=self.game_id, player_id=player_id, occurred_at=occurred_at
            )
        )

    def reseat(self, line_up: LineUp, *, occurred_at: Instant) -> None:
        """A completed line-up arrived for a court with a seat open. **This is
        the court now.**

        The whole arrangement replaces the whole arrangement: an accepted player
        may have crossed the net as well as a newcomer having sat down. The
        court must be **complete** — a re-seat is what a completed line-up
        hands over — and the game must still be awaiting its entry. Called only
        on a court with a seat open; a court standing whole is answered
        ``None`` one layer up rather than re-seated with itself.
        """

        invariant(line_up.is_complete, "a re-seat with a seat still open")
        invariant(not self.line_up.is_complete, "a re-seat of a court standing whole")
        if self.standing_at(occurred_at) is not GameStanding.AWAITING_ENTRY:
            raise TheGameIsNotOpenToSeating()
        self._record_that(
            LineUpReseated(
                game_id=self.game_id,
                seatings=line_up.codes,
                occurred_at=occurred_at,
            )
        )

    # -- ending it ---------------------------------------------------------

    def call_off(self, *, by: UUID, occurred_at: Instant) -> None:
        """Somebody on the court ends a game that has a seat open. **Its end.**

        Told by ``challenges`` in the transaction of the withdrawal
        (``docs/adr/0163`` §2), which has already decided whose act it is — or
        of the departure that left one player on the court (``docs/adr/0165``
        §3), where ``by`` is the leaver. What this refuses is the aggregate's
        own invariant, kept whether or not the caller already guarantees it:
        **a game awaiting its entry with a seat open**, and nothing else. A
        court standing whole that will not play lets its window lapse into
        *Never played*; a game already ended by its clock is never un-ended,
        because the platform has drawn that card. And the caller **was on the
        court**: on it now, or the one whose leaving opened a seat that is still
        open — the one rule every act here shares, read at the width this act
        needs, since the leaver has been vacated by the time the court is told
        their departure emptied it.
        """

        if by not in self.line_up.players and by not in self.departed:
            raise YouWereNotOnThisCourt()
        if (
            self.standing_at(occurred_at) is not GameStanding.AWAITING_ENTRY
            or self.line_up.is_complete
        ):
            raise NotAGameToCallOff()
        self._record_that(
            GameCalledOff(
                game_id=self.game_id, called_by=by, occurred_at=occurred_at
            )
        )

    def dismiss(self, *, by: UUID, occurred_at: Instant) -> None:
        """One player clears this game's card from their own rail
        (``docs/adr/0172`` §5). **Their act, and nobody else's fact.**

        Admitted for a player the rail would show the card to — on the court,
        which is the one rule every act here shares, and answered as a
        stranger is answered for anybody else: the leaver whose departure
        called it off has been vacated, so the card is not theirs to clear —
        and only on a game that is ``CALLED_OFF``, refused with its own code on
        every other standing, because the other endings' cards are the record
        for the day they stay. **Once per player**: a second dismissal writes
        nothing and answers as done, so a retry is not a second event.
        """

        self._side_of(by)
        if self.standing_at(occurred_at) is not GameStanding.CALLED_OFF:
            raise GameIsNotCalledOff()
        if by in self.dismissed:
            return
        self._record_that(
            GameDismissed(
                game_id=self.game_id, dismissed_by=by, occurred_at=occurred_at
            )
        )

    # -- the result -------------------------------------------------------

    def state_result(
        self,
        *,
        by: UUID,
        score: Score | None,
        occurred_at: Instant,
    ) -> None:
        """*This is the score.* **One act, and the record decides what it means.**

        A player sends the score they believe, and which of the three things they
        are doing follows from what already stands:

        - **nothing stands** — they are saying *we played, here is the score*,
          which is two facts and two events;
        - **their own side's score stands, unanswered** — a correction, free, and
          not a second proposal;
        - **the other side's score stands** — a counter, which is their side's
          one turn.

        The client never has to know which, and cannot get it wrong. A route that
        asked would be a route where a mislabelled correction becomes a proposal
        nobody may make.
        """

        side = self._side_of(by)
        if score is None:
            raise AResultMustCarryAScore()

        if self.played_at is None:
            if self.called_off_at is not None:
                # **Asked before the window**, as the ghost's refusal is asked
                # before the open seat: the end this game met is the answer,
                # and its window stopped mattering the moment it was called off.
                raise TheGameWasCalledOff()
            if occurred_at >= entry_closes_at(self.planned_at):
                raise TheEntryWindowHasClosed()
            if not self.line_up.is_complete:
                # **A score on a court with a seat open is refused**
                # (``docs/adr/0162`` §3): a side the engine cannot price, and
                # a seat with no outcome to give anyone. Asked after the
                # window, so a ghost is told it is a ghost.
                raise TheCourtHasAnOpenSeat()
            self._record_that(
                GamePlayed(game_id=self.game_id, said_by=by, occurred_at=occurred_at)
            )
            self._record_that(
                ResultProposed(
                    game_id=self.game_id,
                    player_id=by,
                    side=side.value,
                    score=score.code,
                    occurred_at=occurred_at,
                )
            )
            return

        if self.standing_at(occurred_at) in SETTLED:
            raise TheResultIsSettled()

        ours = self.proposals.get(side)
        if ours is None:
            self._record_that(
                ResultCountered(
                    game_id=self.game_id,
                    player_id=by,
                    side=side.value,
                    score=score.code,
                    occurred_at=occurred_at,
                )
            )
            return

        if side.other in self.proposals:
            raise YourSideHasAlreadyAnswered()
        if self.standing_acceptance() is not None:
            raise TheOtherSideHasAnswered()
        self._record_that(
            ResultCorrected(
                game_id=self.game_id,
                player_id=by,
                side=side.value,
                score=score.code,
                occurred_at=occurred_at,
            )
        )

    def accept_result(self, *, by: UUID, occurred_at: Instant) -> None:
        """*That is what happened.* **From across the net, and one is enough.**

        It settles nothing on its own. The grace runs from the proposal, so
        inside it a counter still wins — which is the whole reason the grace
        exists: in a four somebody is always slower to their phone, and without
        it a partner's fast tap closes the door on an opponent who has not read
        the score yet.
        """

        side = self._side_of(by)
        if self.standing_at(occurred_at) in SETTLED:
            raise TheResultIsSettled()
        if side in self.proposals and side.other not in self.proposals:
            raise AcceptingYourOwnSidesResult()
        if side.other not in self.proposals:
            raise NobodyHasProposedAResult()
        standing = self.standing_acceptance()
        if standing is not None and standing.side is side:
            raise TheResultIsAlreadyAccepted()

        self._record_that(
            ResultAccepted(
                game_id=self.game_id,
                player_id=by,
                side=side.value,
                occurred_at=occurred_at,
            )
        )

    # -- reading ----------------------------------------------------------

    def standing_at(self, now: Instant) -> GameStanding:
        """What this game is, at this instant. **The only place a standing exists.**"""

        return standing_of(
            planned_at=self.planned_at,
            played_at=self.played_at,
            called_off_at=self.called_off_at,
            proposals=self.proposals,
            acceptance=self.acceptance,
            now=now,
        )

    def was_played_at(self, now: Instant) -> bool:
        """Whether these people were on a court together, as far as we know.

        True from the entry onward and for every ending after it, because *an
        unscored game is an evening, not evidence*: it counts toward how much
        somebody has played and toward who they have played with, and only the
        Level is untouched by it.
        """

        return self.standing_at(now) in PLAYED

    def confirmed_score_at(self, now: Instant) -> Score | None:
        """The agreed score, or ``None`` while nothing has settled on one.

        The two questions — *which score* and *has it settled* — are answered in
        one place here so that nobody publishes a score the standing has not
        reached.
        """

        if self.standing_at(now) is not GameStanding.CONFIRMED:
            return None
        return agreed_score(proposals=self.proposals, acceptance=self.acceptance)

    def confirmed_at(self, now: Instant) -> Instant | None:
        """When this game's result became final, or ``None`` while none has.

        The pair ``settled_at`` deliberately leaves apart, written once here so
        nobody publishes a moment for a game the standing has not reached — the
        same shape as ``confirmed_score_at`` and for the same reason.

        It is what lets the rating context walk confirmed results **in the order
        they became final** without anything announcing one (``docs/adr/0139``).
        """

        if self.standing_at(now) is not GameStanding.CONFIRMED:
            return None
        return settled_at(proposals=self.proposals, acceptance=self.acceptance)

    def score_put_to_a_side_at(self, now: Instant) -> ScorePutToASide | None:
        """The one score this game put to somebody, and what became of it.

        ``None`` while nothing has been asked of anybody yet — nobody has said it
        happened, nobody has put a score up, or the score that is up is still
        inside its window.

        The fold is in ``answering.py`` beside the standing it is read off,
        because *is a counter an answer* is a judgement about what a result is;
        this is where a reader asks the question, on the aggregate, the way
        ``was_played_at`` and ``confirmed_at`` are asked (``docs/adr/0160``).
        """

        return score_put_to_a_side(
            played_at=self.played_at,
            proposals=self.proposals,
            acceptance=self.acceptance,
            now=now,
        )

    def outcome_for(self, player_id: UUID, *, now: Instant) -> Outcome | None:
        """Win or loss for one of the people who played. **Never a draw.**

        ``None`` for anybody who is not on this court — a leaver included — and
        for every standing but ``CONFIRMED``: an unscored game moves nobody's
        Level and has no outcome to give anyone.
        """

        side = self.line_up.side_of(player_id)
        if side is None:
            return None
        score = self.confirmed_score_at(now)
        return None if score is None else score.outcome_for(side)

    def standing_proposals(self) -> tuple[Proposal, ...]:
        """Every score currently on the table. **At most two, side ``A`` first.**

        Empty before anybody has entered one, and two of them is the
        disagreement this platform does not resolve — which is a state a reader
        has to be able to *see*, because either side accepting the other's is its
        only end that is not the game going unscored.

        Ordered by side rather than by arrival, because the order of the two acts
        is a fact about who reached their phone first and nothing here is about
        that. A fold over ``proposals`` would order by insertion, which is the
        stream's order and not a promise anybody made (``docs/adr/0105``).
        """

        return tuple(
            self.proposals[side]
            for side in (GameSide.A, GameSide.B)
            if side in self.proposals
        )

    def standing_acceptance(self) -> Acceptance | None:
        """The agreement that still stands, if one does. **A counter voids it.**

        It does not answer *has this settled* — ``standing_at`` does — and the
        gap between the two answers is the whole point of it: for the length of
        the grace the proposing side has stopped waiting on silence, and nothing
        else on this aggregate says so.
        """

        return live_acceptance(
            proposals=self.proposals, acceptance=self.acceptance
        )

    def accepted_proposal(self) -> Proposal | None:
        """The score a standing agreement agreed with. ``None`` with no agreement.

        The other half of ``standing_acceptance``, and they are ``None``
        together: an agreement is always *of* a score, and the grace it runs out
        is measured from **that score** rather than from the tap — so anybody
        rendering the moment needs both, and neither is answerable alone.

        Asked through ``get`` like the fold's own three readers, and for their
        reason: an agreement whose score is missing is a stream nothing here
        wrote, and the failure mode of a subscript is a crash in a **read**.
        """

        agreement = self.standing_acceptance()
        if agreement is None:
            return None
        return self.proposals.get(agreement.of_side)

    # -- folding ----------------------------------------------------------

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Game":
        """Rebuild from the stream. **The opening event is the constructor.**"""

        game = cls._empty()
        for event in events:
            game._apply(event)
        return game

    @classmethod
    def _empty(cls) -> "Game":
        game = cls.__new__(cls)
        game.version = 0
        game.window = None
        game.played_at = None
        game.called_off_at = None
        game.called_off_by = None
        game.dismissed = frozenset()
        game.departed = frozenset()
        game.proposals = {}
        game.acceptance = None
        game._events = EventRecorder()
        return game

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        """Fold one event. **Every branch is somebody's act**; there are no others."""

        if isinstance(event, GamePlanned):
            self.game_id = event.game_id
            self.challenge_id = event.challenge_id
            self.sport = Sport(event.sport)
            self.kind = GameKind(event.kind)
            self.window = None if event.window is None else Window(event.window)
            self.line_up = LineUp.from_codes(event.seatings)
            self.planned_at = instant(event.occurred_at)
        elif isinstance(event, SeatVacated):
            self.line_up = self.line_up.vacated_by(event.player_id)
            self.departed |= {event.player_id}
        elif isinstance(event, LineUpReseated):
            self.line_up = LineUp.from_codes(event.seatings)
            self.departed = frozenset()
        elif isinstance(event, GameCalledOff):
            self.called_off_at = instant(event.occurred_at)
            self.called_off_by = event.called_by
        elif isinstance(event, GameDismissed):
            self.dismissed |= {event.dismissed_by}
        elif isinstance(event, GamePlayed):
            self.played_at = instant(event.occurred_at)
        elif isinstance(event, (ResultProposed, ResultCorrected, ResultCountered)):
            side = GameSide(event.side)
            self.proposals[side] = Proposal(
                side=side,
                by=event.player_id,
                score=Score.from_code(event.score),
                at=instant(event.occurred_at),
            )
        elif isinstance(event, ResultAccepted):
            accepting = GameSide(event.side)
            self.acceptance = Acceptance(
                by=event.player_id,
                side=accepting,
                of_side=accepting.other,
                at=instant(event.occurred_at),
            )
        else:
            raise TypeError(f"Unsupported game event {event!r}")
        self.version += 1

    # -- internals --------------------------------------------------------

    def _side_of(self, player_id: UUID) -> GameSide:
        side = self.line_up.side_of(player_id)
        if side is None:
            raise YouWereNotOnThisCourt()
        return side
