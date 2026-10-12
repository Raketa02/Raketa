"""The Game aggregate — one arranged game, its result inside it, event-sourced.

**A game is born from a booking, and a result is the record that it happened**
(``docs/adr/0137``, #541). Until somebody says *we played* the game is a plan,
and past its entry window a plan nobody claimed is a **ghost** — the outcome
familiarity must be able to tell from a real one.

**Nothing here stores a standing.** ``standing_at`` folds the record against a
clock the caller supplies, so *is this confirmed* answers the same at every
instant, including the whole gap between a deadline passing and anybody looking.
There is no sweep, because there is nothing for one to correct — and no
``ResultConfirmed`` event, because a derived standing has exactly one place to be
true.

**The line-up is frozen until somebody leaves it** (``docs/adr/0162``). Two
acts move it and both are told by ``bookings`` in the transaction of the act
that caused them: ``vacate`` opens one seat (#544), and ``take_seat`` fills one
from a rescue (#545). Neither moves ``planned_at`` — it keeps meaning *when it
became a game* — and neither is a standing: a court with an open seat is still
awaiting its entry. What an open seat changes is who may act, and that a result
is refused until the seat is filled.

**And a court with a seat open can be called off** (``docs/adr/0163``). ``call_off``
is the third act told by ``bookings`` — at the club's cut-off, when a seat is
still open (#544) — and the only act here that announces an end: ``CALLED_OFF``
is the fourth end, a decision rather than a reading of the clock, folded off
``GameCalledOff`` and read before the clock, **and it says who**
(``called_off_by``, ``docs/adr/0172`` §4) — nobody, when it is the cut-off. It
is neither an evening nor a ghost, and every read that counts either leaves it
out.

**A booked game can say somebody did not come** (#547; the mechanics §15.3).
The players who came report them where they would enter the result, and the
reported player has a day to dispute it. A report is the entry for that game —
no score stands beside one — and whatever it comes to, **the game does not
count**. And **a booked game is called off whole** when its club takes the
court back before its hour, with a seat open or none (``call_off_whole``).

**A score is asked for once, and settled by one tap or by silence** (#654;
``docs/adr/0195`` §5). None is taken before the hour, and corrections end with
the entry window. *That's right* from across the net settles it at once and
closes the game; silence settles it a day after it went up; two scores nobody
gave way on settle when the later one's day is up — with the closer, naming the
same winner, or **disputed**, naming different ones. A For fun game asks
nobody: its score is the result the moment it is put up.

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
    ANoShowIsReported,
    AResultIsAlreadyEntered,
    AResultMustCarryAScore,
    CorrectionsHaveClosed,
    NobodyHasProposedAResult,
    NobodyReportedYou,
    NoShowsAreForBookedGames,
    NotAGameToCallOff,
    NotOnThisCourt,
    TheCourtHasAnOpenSeat,
    TheDisputeWindowHasClosed,
    TheEntryWindowHasClosed,
    TheGameHasNotStarted,
    TheGameIsNotOpenToSeating,
    TheGameStartedShort,
    TheGameWasCalledOff,
    TheResultIsSettled,
    YouCannotReportYourself,
    YouWereNotOnThisCourt,
    YouWereReportedAsANoShow,
    YourSideHasAlreadyAnswered,
)
from app.modules.games.domain.events import (
    GameCalledOff,
    GameDismissed,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    NoShowDisputed,
    NoShowReported,
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
    NoShowReport,
    Proposal,
    GameStanding,
    agreed_score,
    live_acceptance,
    settled_at,
    standing_of,
)
from app.modules.games.domain.windows import entry_closes_at
from app.modules.player_profile.domain.weekly_hours import Window
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Game:
    """One arranged game, rebuilt by folding its stream."""

    game_id: UUID
    #: The booking this game was opened for — its id, under the name the field
    #: was born with when a challenge's line-up opened games (#541). Kept so a
    #: support question about *which booking did this come from* has an answer,
    #: and so a second game can never be opened for one arrangement.
    challenge_id: UUID
    sport: Sport
    kind: GameKind
    #: The window the game was arranged under — ``None`` on every booked game,
    #: which has an hour instead. **The type and not its code**: the code is a
    #: storage detail of the event, and a field left as a string is a field
    #: every reader has to remember to widen.
    window: Window | None
    line_up: LineUp
    planned_at: Instant
    #: The hour a **booking** opened this game for (#541), or ``None`` on a game
    #: opened with none. Its entry window runs from the hour when there is one
    #: (``windows.entry_closes_at``).
    starts_at: Instant | None
    #: When somebody said it happened, and ``None`` while nobody has. **This is
    #: the moment**, and there is no other one anywhere in this context.
    played_at: Instant | None
    #: When somebody called it off, or ``None`` because nobody has. **The one
    #: thing about a game that is not a reading of the record and the clock**
    #: (``docs/adr/0163``) — a decision, folded off ``GameCalledOff`` and read
    #: by ``standing_at`` before anything else: an instant rather than a flag,
    #: because the client shelves the ending card from it.
    called_off_at: Instant | None
    #: Who called it off, or ``None`` because nobody has — folded off the same
    #: event's ``called_by`` (``docs/adr/0172`` §4). A booking's cut-off and
    #: its club's cancel name nobody.
    called_off_by: UUID | None
    #: Whose leaving opened the seats that are open now. Folded off
    #: ``SeatVacated`` and emptied once the court is whole again — nobody's
    #: departure is still on a whole court. *The people who may act are the
    #: people who were on the court*, and somebody whose seat is the open one
    #: was: a call-off may name its leaver.
    departed: frozenset[UUID]
    #: At most one per side. A ``Mapping`` rather than a list, because the cap is
    #: the shape: there is nowhere here to put a third score.
    proposals: dict[GameSide, Proposal]
    acceptance: Acceptance | None
    #: Everybody reported as not turning up to this booked game, and what became
    #: of each report (#547). Folded off ``NoShowReported`` and
    #: ``NoShowDisputed``; empty on every game that has no such report.
    no_shows: dict[UUID, NoShowReport]
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
        starts_at: Instant | None = None,
    ) -> "Game":
        """Open a game for a line-up that has just been booked.

        Everything constitutive is chosen here and never recomputed: who played,
        on which side, in which sport, and whether the evening is evidence. The
        clock starts now, because *now* is when the people agreed to play.
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
                starts_at=starts_at,
            )
        )
        return game

    # -- the line-up ------------------------------------------------------

    def vacate(self, player_id: UUID, *, occurred_at: Instant) -> None:
        """Somebody on the court leaves the game. **Their seat opens.**

        Told by ``bookings`` in the transaction of the departure (#544), which
        has already asked whether the booking may still be left; what this
        refuses is the aggregate's own half of it — a game that is not awaiting
        its entry has a line-up that is the record of an evening, and nothing
        on it moves — and somebody who is not on the court, which is the one
        refusal shared with every act here.
        """

        self._side_of(player_id)
        if self.standing_at(occurred_at) is not GameStanding.AWAITING_ENTRY:
            raise TheGameIsNotOpenToSeating()
        self._record_that(
            SeatVacated(
                game_id=self.game_id, player_id=player_id, occurred_at=occurred_at
            )
        )

    def take_seat(
        self, player_id: UUID, *, side: GameSide, occurred_at: Instant
    ) -> None:
        """A booking's rescue took an open seat on ``side`` (#545). **This is
        the court now** — recorded as the re-seat it is, so the room, whose
        members are the line-up, takes them in and the stream reads find them
        on the court — but one seat at a time: a court that lost two players
        is still short of one after the first rescue.

        Told by ``bookings`` in the transaction of the rescue, which has
        already asked whether the seat is there to take. What this refuses is
        the aggregate's own half: a game no longer awaiting its entry — its
        hour has come — and a side with no seat open.
        """

        line_up = self.line_up.seated(player_id, side=side)
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

    def call_off(self, *, by: UUID | None, occurred_at: Instant) -> None:
        """A game that has a seat open is ended. **Its end.**

        Told by ``bookings`` in the transaction of the cut-off that found a
        seat still open (#544), where ``by`` is nobody. What this refuses is
        the aggregate's own invariant, kept whether or not the caller already
        guarantees it: **a game awaiting its entry with a seat open**, and
        nothing else. A court standing whole that will not play lets its window
        lapse into *Never played*; a game already ended by its clock is never
        un-ended, because the platform has drawn that card. And a named caller
        **was on the court**: on it now, or the one whose leaving opened a seat
        that is still open — the one rule every act here shares, read at the
        width this act needs.
        """

        on_the_court = by is None or by in self.line_up.players or by in self.departed
        if not on_the_court:
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

    def call_off_whole(self, *, occurred_at: Instant) -> None:
        """The club took back the court this booked game was on (#547; the
        mechanics §16.9). **Its end**, called off by nobody — as the hour calls
        off a court left short — **whole or with a seat open**: the one end of
        a game standing whole that is somebody's act, because the court itself
        is gone.

        Told by ``bookings`` in the transaction of the club's act, which has
        already asked whether the booking may still be called off; so everything this
        refuses is a broken precondition — a game with no hour, one no longer
        awaiting its entry, or one whose hour has come.
        """

        invariant(
            self.starts_at is not None,
            f"{self.game_id} is called off whole as a booked game, with no hour",
        )
        assert self.starts_at is not None
        invariant(
            occurred_at < self.starts_at
            and self.standing_at(occurred_at) is GameStanding.AWAITING_ENTRY,
            f"{self.game_id} is called off whole at {occurred_at}: "
            f"{self.standing_at(occurred_at)}, its hour {self.starts_at}",
        )
        self._record_that(
            GameCalledOff(
                game_id=self.game_id, called_by=None, occurred_at=occurred_at
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
          which is two facts and two events; never before the hour (#654);
        - **their own side's score stands, unanswered** — a correction, free, and
          not a second proposal, until the entry window closes (#654);
        - **the other side's score stands** — a counter, which is their side's
          one turn.

        The client never has to know which, and cannot get it wrong. A route that
        asked would be a route where a mislabelled correction becomes a proposal
        nobody may make.
        """

        side = self._side_of(by)
        if score is None:
            raise AResultMustCarryAScore()
        if self.no_shows:
            # A report is this game's entry, and no score stands beside one.
            if self.standing_at(occurred_at) in SETTLED:
                raise TheResultIsSettled()
            raise ANoShowIsReported()

        if self.played_at is None:
            if self.called_off_at is not None:
                # **Asked before the window**, as the ghost's refusal is asked
                # before the open seat: the end this game met is the answer,
                # and its window stopped mattering the moment it was called off.
                raise TheGameWasCalledOff()
            if self.standing_at(occurred_at) is GameStanding.STARTED_SHORT:
                raise TheGameStartedShort()
            if self.starts_at is not None and occurred_at < self.starts_at:
                # **No score before the hour** (#654): nothing can have
                # happened at a game that has not begun.
                raise TheGameHasNotStarted()
            if occurred_at >= self.entry_closes_at:
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
        if occurred_at >= self.entry_closes_at:
            # **Corrections end with the entry window** (#654): a correction
            # re-dates its side's score, and a side that kept correcting would
            # keep the game waiting for ever.
            raise CorrectionsHaveClosed()
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
        """*That's right.* **From across the net, and one is enough** — and it
        **settles the result at once and closes the game** (#654;
        ``docs/adr/0195`` §5). No different score is taken after it, so in
        doubles the first agreement from the other side is the one that counts.
        The six-hour grace that once let a counter beat it is retired: a score
        is asked for once, and an agreement is its answer.
        """

        side = self._side_of(by)
        if self.standing_at(occurred_at) in SETTLED:
            raise TheResultIsSettled()
        if side in self.proposals and side.other not in self.proposals:
            raise AcceptingYourOwnSidesResult()
        if side.other not in self.proposals:
            raise NobodyHasProposedAResult()

        self._record_that(
            ResultAccepted(
                game_id=self.game_id,
                player_id=by,
                side=side.value,
                occurred_at=occurred_at,
            )
        )

    # -- somebody did not come ----------------------------------------------

    def report_no_show(
        self,
        *,
        by: UUID,
        absent: UUID,
        occurred_at: Instant,
    ) -> None:
        """*Kuba didn't come* — said by somebody who came to a **booked** game,
        where they would enter its result (#547; the mechanics §15.3).

        **What it refuses, in order**: somebody off the court, a game with no
        hour, a report of yourself or of somebody who was not on it; a game
        called off, started short, not started yet, scored, settled, or past
        its entry window; and a reporter reported themselves, whose answer is
        the dispute. A player already reported is reported: a second report
        writes nothing.
        """

        self._side_of(by)
        if self.starts_at is None:
            raise NoShowsAreForBookedGames()
        if absent == by:
            raise YouCannotReportYourself()
        if self.line_up.side_of(absent) is None:
            raise NotOnThisCourt()
        if self.called_off_at is not None:
            raise TheGameWasCalledOff()
        standing = self.standing_at(occurred_at)
        if standing is GameStanding.STARTED_SHORT:
            raise TheGameStartedShort()
        if occurred_at < self.starts_at:
            raise TheGameHasNotStarted()
        if self.played_at is not None:
            raise AResultIsAlreadyEntered()
        if standing in SETTLED and standing is not GameStanding.NEVER_PLAYED:
            raise TheResultIsSettled()
        if occurred_at >= self.entry_closes_at:
            raise TheEntryWindowHasClosed()
        if by in self.no_shows:
            raise YouWereReportedAsANoShow()
        if absent in self.no_shows:
            return
        self._record_that(
            NoShowReported(
                game_id=self.game_id,
                player_id=absent,
                reported_by=by,
                occurred_at=occurred_at,
            )
        )

    def dispute_no_show(self, *, by: UUID, occurred_at: Instant) -> None:
        """*I was there* — the reported player, inside their day (#547). The
        report falls; a second dispute writes nothing."""

        report = self.no_shows.get(by)
        if report is None:
            raise NobodyReportedYou()
        if report.disputed_at is not None:
            return
        if not self.may_dispute(by, now=occurred_at):
            raise TheDisputeWindowHasClosed()
        self._record_that(
            NoShowDisputed(game_id=self.game_id, player_id=by, occurred_at=occurred_at)
        )

    def may_dispute(self, player_id: UUID, *, now: Instant) -> bool:
        """Whether a report of this player not coming waits on their dispute at
        ``now`` — undisputed, and inside its own day (#547)."""

        report = self.no_shows.get(player_id)
        return (
            report is not None
            and report.disputed_at is None
            and now < report.dispute_closes_at
        )

    def confirmed_no_shows_at(self, now: Instant) -> frozenset[UUID]:
        """Everybody who did not come to this game, as it stands at ``now`` —
        **only once the game is a no-show**, every report having had its day:
        a report still inside its day is not a verdict yet (#547)."""

        if self.standing_at(now) is not GameStanding.NO_SHOW:
            return frozenset()
        return frozenset(
            player for player, report in self.no_shows.items() if report.stands_at(now)
        )

    # -- reading ----------------------------------------------------------

    @property
    def entry_closes_at(self) -> Instant:
        """When *we played* stops being sayable — from the booked hour's end
        when a booking opened this game, from its week otherwise."""

        return entry_closes_at(self.planned_at, starts_at=self.starts_at)

    def standing_at(self, now: Instant) -> GameStanding:
        """What this game is, at this instant. **The only place a standing exists.**"""

        return standing_of(
            kind=self.kind,
            planned_at=self.planned_at,
            starts_at=self.starts_at,
            played_at=self.played_at,
            called_off_at=self.called_off_at,
            proposals=self.proposals,
            acceptance=self.acceptance,
            now=now,
            line_up_complete=self.line_up.is_complete,
            no_shows=self.no_shows,
        )

    def was_played_at(self, now: Instant) -> bool:
        """Whether these people were on a court together, as far as we know.

        True from the entry onward and for every ending after it, because *an
        unscored game is an evening, not evidence*: it counts toward how much
        somebody has played and toward who they have played with, and only the
        Level is untouched by it.
        """

        return self.standing_at(now) in PLAYED

    def became_history_at(self, now: Instant) -> Instant | None:
        """When this game stopped being ahead of the people on it, or ``None``.

        **The one moment ``GAME_IS_HISTORY`` is dated from**, folded here so a
        seat change, a chat exit, a pairwise record and a deck's cool-off cannot
        come to four dates for one game. Three endings and one clock: the entry
        that said *we played*, whatever was agreed about the score afterwards;
        the window closing on silence, which is a ghost; and the call-off, which
        is an act and is dated from nothing but itself. ``None`` is *awaiting
        its entry* — the game is still ahead, whether or not its agreed moment
        has passed, because a plan whose moment has passed can still be moved.
        """

        standing = self.standing_at(now)
        if standing is GameStanding.CALLED_OFF:
            # ``called_off_at`` is set for exactly this standing, which is folded
            # from nothing else; the fallback is unreachable and stated rather
            # than asserted, because a read is a bad place to raise about a
            # stream somebody else wrote.
            return self.called_off_at or now
        if standing is GameStanding.NEVER_PLAYED:
            return self.entry_closes_at
        if standing is GameStanding.STARTED_SHORT:
            # Set for exactly this standing, which only a booked game reaches.
            return self.starts_at or now
        if self.no_shows:
            # A report is the entry of a game somebody did not come to: it is
            # history from the first one, whatever the reports come to (#547).
            return min(report.at for report in self.no_shows.values())
        if standing in PLAYED:
            # ``played_at`` is set for every standing in ``PLAYED`` — the entry
            # that records *we played* is the only thing that can set it.
            return self.played_at or self.planned_at
        return None

    def confirmed_score_at(self, now: Instant) -> Score | None:
        """The agreed score, or ``None`` while nothing has settled on one.

        The two questions — *which score* and *has it settled* — are answered in
        one place here so that nobody publishes a score the standing has not
        reached.
        """

        if self.standing_at(now) is not GameStanding.CONFIRMED:
            return None
        return agreed_score(
            kind=self.kind, proposals=self.proposals, acceptance=self.acceptance
        )

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
        return settled_at(
            kind=self.kind, proposals=self.proposals, acceptance=self.acceptance
        )

    def settled_by_agreement_at(self, now: Instant) -> Acceptance | None:
        """The *That's right* that settled this game, or ``None`` — on every
        game not confirmed at ``now``, and on one silence or the closer of two
        scores settled (#654)."""

        if self.standing_at(now) is not GameStanding.CONFIRMED:
            return None
        return live_acceptance(proposals=self.proposals, acceptance=self.acceptance)

    def left_in_dispute_by(self, now: Instant) -> frozenset[UUID]:
        """Whoever put up the two scores that named different winners — **a
        result left in dispute** on each of their records (#654;
        ``docs/adr/0195`` §5) — once the answer window has closed on them.
        Empty on every other standing.

        **The people who put the standing scores up**, read off the record: a
        side's score is its last correction's, so whoever corrected it is the
        one who put it there. It costs nobody points; it is information.
        """

        if self.standing_at(now) is not GameStanding.DISPUTED:
            return frozenset()
        return frozenset(proposal.by for proposal in self.proposals.values())

    def score_put_to_a_side_at(self, now: Instant) -> ScorePutToASide | None:
        """The one score this game put to somebody, and what became of it.

        ``None`` while nothing has been asked of anybody yet — nobody has said it
        happened, nobody has put a score up, or the score that is up is still
        inside its window.

        The fold is in ``answering.py`` beside the standing it is read off,
        because *is a counter an answer* is a judgement about what a result is;
        this is where a reader asks the question, on the aggregate, the way
        ``was_played_at`` and ``confirmed_at`` are asked (``docs/adr/0160``).

        **A For fun game puts its score to nobody** (#654): it asks nothing, so
        nobody can have stayed silent about it.
        """

        if self.kind is GameKind.FRIENDLY:
            return None
        return score_put_to_a_side(
            played_at=self.played_at,
            proposals=self.proposals,
            acceptance=self.acceptance,
            now=now,
        )

    def awaits_agreement_from(self, player_id: UUID, *, now: Instant) -> bool:
        """Whether a score on the table waits on this player's agreement — the
        *result to confirm* that is theirs to clear (#542; the mechanics §3).

        **The other side's score is up**: a score of their own side's waits on
        the other side. An agreement settles the game at once (#654), so there
        is none still to wait out. Never true off the court, and never outside
        ``AWAITING_ANSWER`` — which a For fun game never reaches.
        """

        side = self.line_up.side_of(player_id)
        if side is None or self.standing_at(now) is not GameStanding.AWAITING_ANSWER:
            return False
        return any(proposal.side is not side for proposal in self.standing_proposals())

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
        disagreement this platform does not arbitrate — which is a state a reader
        has to be able to *see*, because either side may still accept the
        other's, before the later score's day settles it with the closer score
        or **disputed** (#654).

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
        game.departed = frozenset()
        game.proposals = {}
        game.acceptance = None
        game.no_shows = {}
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
            self.starts_at = (
                None if event.starts_at is None else instant(event.starts_at)
            )
        elif isinstance(event, SeatVacated):
            self.line_up = self.line_up.vacated_by(event.player_id)
            self.departed |= {event.player_id}
        elif isinstance(event, LineUpReseated):
            self.line_up = LineUp.from_codes(event.seatings)
            # A whole court has nobody's departure on it; a rescue that leaves a
            # seat still open keeps its leavers, as the court is not whole (#545).
            if self.line_up.is_complete:
                self.departed = frozenset()
        elif isinstance(event, GameCalledOff):
            self.called_off_at = instant(event.occurred_at)
            self.called_off_by = event.called_by
        elif isinstance(event, GameDismissed):
            # Retired (#578): a stored dismissal is read and changes nothing —
            # nothing reads who cleared a card any more.
            pass
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
        elif isinstance(event, NoShowReported):
            self.no_shows = {
                **self.no_shows,
                event.player_id: NoShowReport(
                    reported_by=event.reported_by, at=instant(event.occurred_at)
                ),
            }
        elif isinstance(event, NoShowDisputed):
            report = self.no_shows[event.player_id]
            self.no_shows = {
                **self.no_shows,
                event.player_id: NoShowReport(
                    reported_by=report.reported_by,
                    at=report.at,
                    disputed_at=instant(event.occurred_at),
                ),
            }
        else:
            raise TypeError(f"Unsupported game event {event!r}")
        self.version += 1

    # -- internals --------------------------------------------------------

    def _side_of(self, player_id: UUID) -> GameSide:
        side = self.line_up.side_of(player_id)
        if side is None:
            raise YouWereNotOnThisCourt()
        return side
