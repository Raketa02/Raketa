"""The Game aggregate — one arranged game, its result inside it, event-sourced.

**A game is born from a booking, and a result is the record that it happened**
(``docs/adr/0137``, #541). Until somebody says *we played* the game is a plan,
and past its entry window a full court nobody recorded was **played all the
same** — *Played · no score*, with no Level moving (#655; ``docs/adr/0195``
§2): it was booked and paid for, and nothing is charged to anybody for the
silence.

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
is not an evening, and every read that counts one leaves it out.

**A booked game catches a real absence at the court, while it happens** (#657;
``docs/adr/0195`` §3, the mechanics §15.1). In the first thirty minutes a player
at the club taps *Oscar isn't here yet*; Oscar's arrival — his own *I'm here*,
or a courtmate's *they're here*, each from the club — decides on time or Came
late, and none by then is **Didn't come**: the game takes no score and never
counts. *I was there* within a day, confirmed by somebody else on the court,
makes it Came late. Everybody who arrives on time does nothing at all
(``attendance.py``). And **a booked game is called off whole** when its club
takes the court back before its hour, with a seat open or none
(``call_off_whole``).

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

from dataclasses import dataclass, field, replace
from typing import Any, Iterable
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.games.domain.attendance import (
    CAME_LATE_STATES,
    NOT_HERE_STATES,
    Absence,
    AttendanceState,
    ClubVerdict,
    Turnout,
    is_final,
    state_of,
)
from app.modules.games.domain.errors import (
    AcceptingYourOwnSidesResult,
    AlreadyArrived,
    AResultMustCarryAScore,
    AttendanceIsForBookedGames,
    CorrectionsHaveClosed,
    NobodyHasProposedAResult,
    NobodySaidTheyWereNotHere,
    NotAboutYourself,
    NotAGameToCallOff,
    NotAtTheClub,
    NothingToConfirm,
    NotOnThisCourt,
    SomebodyDidntCome,
    SomebodyIsNotHereYet,
    TheCourtHasAnOpenSeat,
    TheEntryWindowHasClosed,
    TheGameHasNotStarted,
    TheGameIsNotOpenToSeating,
    TheGameStartedShort,
    TheGameWasCalledOff,
    TheLateClaimHasClosed,
    TheResultIsSettled,
    TheTapWindowHasClosed,
    TheTapWindowIsOpen,
    YouAreNotHereYourself,
    YouWereNotOnThisCourt,
    YourSideHasAlreadyAnswered,
)
from app.modules.games.domain.events import (
    AbsenceNoted,
    ArrivalNoted,
    GameCalledOff,
    GameDismissed,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    NoShowDisputed,
    NoShowReported,
    PresenceClaimed,
    PresenceConfirmed,
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
from app.modules.games.domain.windows import (
    entry_closes_at,
    late_claim_closes_at,
    tap_window_closes_at,
)
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
    #: Everybody somebody on the court said was not here yet, and what has been
    #: said about each since (#657) — folded off the four attendance events;
    #: empty on every game where everybody arrived on time, which is every
    #: ordinary game. What each **is** is ``attendance_at``'s, never stored.
    attendance: dict[UUID, Absence]
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
        nothing else. A court standing whole that nobody records lapses into
        *Played · no score* (#655); a game already ended by its clock is never
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
        standing = self.standing_at(occurred_at)
        if standing is GameStanding.NOT_HERE_YET:
            # If they never come the game takes no score (#657).
            raise SomebodyIsNotHereYet()
        if standing is GameStanding.DIDNT_COME:
            raise SomebodyDidntCome()

        if self.played_at is None:
            if self.called_off_at is not None:
                # **Asked before the window**, as the window's refusal is asked
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
                # window, so a score too late is told it is too late.
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
        standing = self.standing_at(occurred_at)
        if standing is GameStanding.NOT_HERE_YET:
            # An agreement settles a score, and none settles beside an absence
            # (#657): if they never come the game takes no score.
            raise SomebodyIsNotHereYet()
        if standing is GameStanding.DIDNT_COME:
            raise SomebodyDidntCome()
        if standing in SETTLED:
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

    # -- who turned up (#657) -----------------------------------------------

    def note_absent(
        self,
        *,
        by: UUID,
        absent: UUID,
        where: ClubVerdict,
        occurred_at: Instant,
    ) -> None:
        """*Oscar isn't here yet* — from a player on a **booked** game's court,
        at the club, in the tap window (``docs/adr/0195`` §3). It costs its
        maker nothing, and a partner may be tapped as well as an opponent.

        **What it refuses, in order**: somebody off the court; a game with no
        hour; yourself, or somebody not on the court; a game called off or
        started short; before the hour, or after the tap window; a result
        already **settled**, which is final; a maker who is themselves awaited;
        a player already arrived; and, last, a maker not at the club — so the
        sentence a player reads is about the game before it is about where they
        stand. A player already awaited is awaited: a second tap writes nothing.

        **A score still waiting for its answer does not stop it**: the entry
        window opens at the hour's start and a score carries no location, so
        an absent player — or their partner — could otherwise post one from
        home at 17:00 and never be caught. The score stays on the table and is
        nobody's while anybody is awaited or Didn't come; an arrival, or a
        confirmed *I was there*, gives it back its game.
        """

        self._side_of(by)
        starts_at = self._booked_hour()
        if absent == by:
            raise NotAboutYourself()
        if self.line_up.side_of(absent) is None:
            raise NotOnThisCourt()
        self._in_the_tap_window(occurred_at, starts_at=starts_at)
        if self.standing_at(occurred_at) in SETTLED:
            raise TheResultIsSettled()
        if self._not_here(by, now=occurred_at):
            raise YouAreNotHereYourself()
        noted = self.attendance.get(absent)
        if noted is not None and noted.arrived_at is not None:
            raise AlreadyArrived()
        if not where.at_the_club:
            raise NotAtTheClub(where.club_name)
        if noted is not None:
            return
        self._record_that(
            AbsenceNoted(
                game_id=self.game_id,
                player_id=absent,
                noted_by=by,
                occurred_at=occurred_at,
            )
        )

    def note_arrival(
        self,
        *,
        by: UUID,
        arrived: UUID,
        where: ClubVerdict,
        occurred_at: Instant,
    ) -> None:
        """**The arrival** — *I'm here* when ``by`` is ``arrived``, *they're
        here* from anybody else on the court; at the club, in the tap window
        (#657). The first is the one that counts, and its moment decides on
        time or Came late.

        **What it refuses, in order**: somebody off the court; a game with no
        hour; somebody not on the court; a game called off or started short;
        before the hour, or after the tap window — a player still awaited then
        Didn't come, and has *I was there*; a player nobody tapped, since
        everybody who arrives on time does nothing; a player already arrived;
        a courtmate who is themselves awaited; and, last, a maker not at the
        club — *they're here* is checked too (a call, ``docs/adr/0195`` §10.4).
        """

        self._side_of(by)
        starts_at = self._booked_hour()
        if self.line_up.side_of(arrived) is None:
            raise NotOnThisCourt()
        self._in_the_tap_window(occurred_at, starts_at=starts_at)
        noted = self.attendance.get(arrived)
        if noted is None:
            raise NobodySaidTheyWereNotHere()
        if noted.arrived_at is not None:
            raise AlreadyArrived()
        if by != arrived and self._not_here(by, now=occurred_at):
            raise YouAreNotHereYourself()
        if not where.at_the_club:
            raise NotAtTheClub(where.club_name)
        self._record_that(
            ArrivalNoted(
                game_id=self.game_id,
                player_id=arrived,
                noted_by=by,
                occurred_at=occurred_at,
            )
        )

    def claim_presence(self, *, by: UUID, occurred_at: Instant) -> None:
        """*I was there* — the player who Didn't come, within a day of the tap
        window closing, for a phone that died at the court (#657). **No fix is
        asked**: it is made a day later from wherever they are, and what proves
        it is somebody else on the court confirming it. A second claim writes
        nothing.

        **What it refuses, in order**: somebody off the court; a game with no
        hour; a player nobody tapped; a player who arrived; the tap window still
        running — *I'm here* is the answer then — and the late claim's day over.
        """

        self._side_of(by)
        starts_at = self._booked_hour()
        noted = self.attendance.get(by)
        if noted is None:
            raise NobodySaidTheyWereNotHere()
        if noted.arrived_at is not None:
            raise AlreadyArrived()
        if occurred_at < tap_window_closes_at(starts_at):
            raise TheTapWindowIsOpen()
        if occurred_at >= late_claim_closes_at(starts_at):
            raise TheLateClaimHasClosed()
        if noted.claimed_at is not None:
            return
        self._record_that(
            PresenceClaimed(game_id=self.game_id, player_id=by, occurred_at=occurred_at)
        )

    def confirm_presence(
        self, *, by: UUID, claimant: UUID, occurred_at: Instant
    ) -> None:
        """*Yes, they were here* — anybody else on the court, agreeing with an
        *I was there* inside the same day (#657). **It turns Didn't come into
        Came late**, because the tap still proves they were not there when it
        was made, and the game carries on as usual — score and Level included.
        In singles the one who can confirm is the opponent who tapped
        (``docs/adr/0195``'s accepted cost). A second confirmation writes
        nothing.

        **What it refuses, in order**: somebody off the court; a game with no
        hour; yourself, or somebody not on the court; a player who has not said
        *I was there*; the late claim's day over; and a confirmer who Didn't
        come themselves — two absentees cannot vouch for each other (a call
        beside ``docs/adr/0195`` §3's *never while yourself absent*).
        """

        self._side_of(by)
        starts_at = self._booked_hour()
        if claimant == by:
            raise NotAboutYourself()
        if self.line_up.side_of(claimant) is None:
            raise NotOnThisCourt()
        noted = self.attendance.get(claimant)
        if noted is None or noted.claimed_at is None:
            raise NothingToConfirm()
        if occurred_at >= late_claim_closes_at(starts_at):
            raise TheLateClaimHasClosed()
        if self._not_here(by, now=occurred_at):
            raise YouAreNotHereYourself()
        if noted.confirmed_at is not None:
            return
        self._record_that(
            PresenceConfirmed(
                game_id=self.game_id,
                player_id=claimant,
                confirmed_by=by,
                occurred_at=occurred_at,
            )
        )

    def attendance_at(self, now: Instant) -> dict[UUID, AttendanceState]:
        """What became of everybody somebody said was not here yet, at ``now``
        — **folded on every read**, never stored. Empty on every game where
        nobody was tapped, which is every ordinary game."""

        if self.starts_at is None:
            return {}
        return {
            player: state_of(absence, starts_at=self.starts_at, now=now)
            for player, absence in self.attendance.items()
        }

    def didnt_come_at(self, now: Instant) -> frozenset[UUID]:
        """Everybody who **Didn't come** to this game, for good, at ``now`` —
        only once their late claim's day is over unconfirmed: a provisional
        *Didn't come* is not a verdict yet (#657)."""

        if self.starts_at is None:
            return frozenset()
        starts_at = self.starts_at
        return frozenset(
            player
            for player, state in self.attendance_at(now).items()
            if state is AttendanceState.DIDNT_COME
            and is_final(state, starts_at=starts_at, now=now)
        )

    def turnout_of(self, player_id: UUID, *, now: Instant) -> Turnout | None:
        """What this game says about this player on their record at ``now``
        (#659), or ``None`` while it says nothing — off the court, inside the
        entry window, a *Didn't come* still provisional, and for good on a game
        called off or started short.

        **Came late first**, because it is final at the arrival and the game it
        was carries on as usual; then a final *Didn't come*; then a game played
        — on time, played through; then, beside somebody else's final *Didn't
        come*, on time to a game that never counted.
        """

        if player_id not in self.line_up.players:
            return None
        if self.attendance_at(now).get(player_id) in CAME_LATE_STATES:
            return Turnout.CAME_LATE
        absent = self.didnt_come_at(now)
        if player_id in absent:
            return Turnout.DIDNT_COME
        if self.was_played_at(now):
            return Turnout.PLAYED_THROUGH
        if absent:
            return Turnout.TURNED_UP_UNCOUNTED
        return None

    def attendance_waits_on(self, player_id: UUID, *, now: Instant) -> bool:
        """Whether attendance waits on this player at ``now`` (#657): their own
        *I'm here* while they are awaited, their own *I was there* while they
        Didn't come and have not said it, or somebody else's *I was there* to
        confirm. Never true off the court, and never once the late claim's day
        is over."""

        if self.line_up.side_of(player_id) is None or self.starts_at is None:
            return False
        if now >= late_claim_closes_at(self.starts_at):
            return False
        states = self.attendance_at(now)
        own = states.get(player_id)
        if own in (AttendanceState.WAITING, AttendanceState.DIDNT_COME):
            return True
        if own is AttendanceState.CLAIMED:
            # Said; it waits on somebody else now.
            return False
        return any(
            state is AttendanceState.CLAIMED and player != player_id
            for player, state in states.items()
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
            attendance=self.attendance,
        )

    def was_played_at(self, now: Instant) -> bool:
        """Whether these people were on a court together, as far as we know.

        True from the entry onward and for every ending after it, because *an
        unscored game is an evening, not evidence*: it counts toward how much
        somebody has played and toward who they have played with, and only the
        Level is untouched by it. **And true of a full court nobody recorded**
        once its window has closed (#655): *Played · no score*.
        """

        return self.standing_at(now) in PLAYED

    def became_history_at(self, now: Instant) -> Instant | None:
        """When this game stopped being ahead of the people on it, or ``None``.

        **The one moment ``GAME_IS_HISTORY`` is dated from**, folded here so a
        seat change, a chat exit, a pairwise record and a deck's cool-off cannot
        come to four dates for one game. Three endings and one clock: the entry
        that said *we played*, whatever was agreed about the score afterwards;
        the window closing on silence, which is *Played · no score* on a full
        court (#655); and the call-off, which is an act and is dated from
        nothing but itself. ``None`` is *awaiting its entry* — the game is
        still ahead, whether or not its agreed moment has passed, because a
        plan whose moment has passed can still be moved.
        """

        standing = self.standing_at(now)
        if standing is GameStanding.CALLED_OFF:
            # ``called_off_at`` is set for exactly this standing, which is folded
            # from nothing else; the fallback is unreachable and stated rather
            # than asserted, because a read is a bad place to raise about a
            # stream somebody else wrote.
            return self.called_off_at or now
        if standing is GameStanding.PLAYED_NO_SCORE:
            return self.entry_closes_at
        if standing is GameStanding.STARTED_SHORT:
            # A booked game started short at its hour; a stream with no hour
            # reaches it only when its window closes on a seat still open.
            return self.starts_at or self.entry_closes_at
        if standing is GameStanding.DIDNT_COME and self.starts_at is not None:
            # Somebody Didn't come once the tap window closed on them (#657).
            return tap_window_closes_at(self.starts_at)
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
        game.attendance = {}
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
        elif isinstance(event, AbsenceNoted):
            self.attendance = {
                **self.attendance,
                event.player_id: Absence(
                    noted_by=event.noted_by, noted_at=instant(event.occurred_at)
                ),
            }
        elif isinstance(event, ArrivalNoted):
            self._absence_changed(
                event.player_id,
                arrived_at=instant(event.occurred_at),
                arrival_noted_by=event.noted_by,
            )
        elif isinstance(event, PresenceClaimed):
            self._absence_changed(
                event.player_id, claimed_at=instant(event.occurred_at)
            )
        elif isinstance(event, PresenceConfirmed):
            self._absence_changed(
                event.player_id,
                confirmed_at=instant(event.occurred_at),
                confirmed_by=event.confirmed_by,
            )
        elif isinstance(event, (NoShowReported, NoShowDisputed)):
            # Retired (#657; ``docs/adr/0195`` §9): a stored report and its
            # dispute decode and change nothing — the game reads as if nobody
            # had made one, so a full court nobody recorded is *Played · no
            # score*.
            pass
        else:
            raise TypeError(f"Unsupported game event {event!r}")
        self.version += 1

    # -- internals --------------------------------------------------------

    def _side_of(self, player_id: UUID) -> GameSide:
        side = self.line_up.side_of(player_id)
        if side is None:
            raise YouWereNotOnThisCourt()
        return side

    def _absence_changed(self, player_id: UUID, **said: Any) -> None:
        """Fold what was said since about a player noted absent."""

        self.attendance = {
            **self.attendance,
            player_id: replace(self.attendance[player_id], **said),
        }

    def _booked_hour(self) -> Instant:
        """The hour a booking opened this game for — the one every attendance
        clock runs from. A game with none has no hour to turn up to."""

        if self.starts_at is None:
            raise AttendanceIsForBookedGames()
        return self.starts_at

    def _in_the_tap_window(self, occurred_at: Instant, *, starts_at: Instant) -> None:
        """Refuse a tap outside the first thirty minutes of a game that is
        being played: one called off, one that started short, one whose hour
        has not come, one whose tap window has closed."""

        if self.called_off_at is not None:
            raise TheGameWasCalledOff()
        if self.standing_at(occurred_at) is GameStanding.STARTED_SHORT:
            raise TheGameStartedShort()
        if occurred_at < starts_at:
            raise TheGameHasNotStarted()
        if occurred_at >= tap_window_closes_at(starts_at):
            raise TheTapWindowHasClosed()

    def _not_here(self, player_id: UUID, *, now: Instant) -> bool:
        """Whether this player is, at ``now``, somebody the court is still
        waiting for or who Didn't come — who may not say who else is here, nor
        vouch for anybody."""

        return self.attendance_at(now).get(player_id) in NOT_HERE_STATES
