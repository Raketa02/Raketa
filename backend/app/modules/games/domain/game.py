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

from app.kernel import Instant, Sport, instant
from app.modules.games.domain.answering import (
    ScorePutToASide,
    score_put_to_a_side,
)
from app.modules.games.domain.errors import (
    AcceptingYourOwnSidesResult,
    AResultMustCarryAScore,
    NobodyHasProposedAResult,
    TheEntryWindowHasClosed,
    TheOtherSideHasAnswered,
    TheResultIsAlreadyAccepted,
    TheResultIsSettled,
    YouWereNotOnThisCourt,
    YourSideHasAlreadyAnswered,
)
from app.modules.games.domain.events import (
    GamePlanned,
    GamePlayed,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
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
            if occurred_at >= entry_closes_at(self.planned_at):
                raise TheEntryWindowHasClosed()
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
        ``was_played_at`` and ``confirmed_at`` are asked (``docs/adr/0156``).
        """

        return score_put_to_a_side(
            played_at=self.played_at,
            proposals=self.proposals,
            acceptance=self.acceptance,
            now=now,
        )

    def outcome_for(self, player_id: UUID, *, now: Instant) -> Outcome | None:
        """Win or loss for one of the people who played. **Never a draw.**

        ``None`` for anybody who was not on this court, and for every standing
        but ``CONFIRMED`` — an unscored game moves nobody's Level and has no
        outcome to give anyone.
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
