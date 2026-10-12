"""What a game **is** right now, read off the record and the clock.

**Derived, never stored, and never announced** (``docs/adr/0137``). A status
column would be wrong for the whole gap between a deadline passing and anything
noticing, and it would be the copy that gets believed — which is why there is no
status field on the aggregate, no ``ResultConfirmed`` event, and this function is
the only place a standing exists: *nothing announces a conclusion the record
already implies*, applied to a result.

Ten values. Nine of them are what the record and the clock can answer for —
six ends and three waits, the fourth end a booked game's hour coming with a
seat open (#544), the fifth a report of somebody not turning up that stood its
day, and the third wait that day (#547), the sixth two scores naming different
winners when their answer window closed (#654) — and **the tenth is the one
exemption this module holds, and it is written down so it stays one**
(``docs/adr/0163``).
A game called off is a decision — a booking's cut-off, or its club taking the
court back — and there is nothing on the record to fold it out of, so it is the
one standing an event announces — on the rule *an event may announce a
conclusion only when no arrangement of the record could reach it*
(``docs/adr/0142`` §3). ``GameCalledOff`` is not a second place for the fact to
be true; it is the only place, and the fold reads it first.

**The class is ``GameStanding`` and the domain term is *standing*.** It was
named apart from the ``Standing`` component ``challenges`` published on
``openapi.player.json`` until #578, because a second class of that name would
have renamed the first in a contract that is one namespace; the name stays,
since renaming a component is a change to types a shipped app generated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.lineup import GameKind, GameSide
from app.modules.games.domain.results import Score
from app.modules.games.domain.windows import (
    dispute_closes_at,
    entry_closes_at,
    proposal_closes_at,
)


@final
class GameStanding(str, Enum):
    """The ten standings, as codes. A client's words are the client's own."""

    #: Arranged, and nobody has said it happened yet.
    AWAITING_ENTRY = "AWAITING_ENTRY"
    #: The entry window closed and nobody ever said it happened. **A ghost game**
    #: — the pairwise outcome familiarity must be able to tell from a real one.
    NEVER_PLAYED = "NEVER_PLAYED"
    #: They played, a score is on the table, and its window is still open.
    AWAITING_ANSWER = "AWAITING_ANSWER"
    #: They played and a score is agreed — by an acceptance, at once; by
    #: silence; by two scores naming the same winner, with the closer one
    #: (#654); or, For fun, by the score itself, which asks nobody.
    CONFIRMED = "CONFIRMED"
    #: They played and no score is agreed. **An evening, not evidence**: it counts
    #: toward how much these people have played and moves nobody's Level. **Only
    #: a booked game every report of not coming to was disputed reaches it now**
    #: (#547): two scores end confirmed or disputed (#654), and this goes with
    #: the no-show report (``docs/adr/0195`` §3).
    UNSCORED = "UNSCORED"
    #: They played, and the two scores standing when the answer window closed
    #: named **different winners** (#654; ``docs/adr/0195`` §5). No Level
    #: moves — *we will not arbitrate* — and the two players who put the scores
    #: up each have a result left in dispute (``Game.left_in_dispute_by``). An
    #: evening, like ``UNSCORED``: they were on a court together.
    DISPUTED = "DISPUTED"
    #: Somebody ended it while a seat was open, before it happened. **The one
    #: value here that no reading of the record reaches** (``docs/adr/0163``):
    #: nobody said they played and no window closed, so it can reuse none of the
    #: three ends above. It arrives on the fold from ``GameCalledOff`` and from
    #: nowhere else — told by the challenge in the transaction of the act that
    #: called the court off, and it says who (``docs/adr/0172`` §4). **An end,
    #: and neither an evening nor a ghost**: a ghost is silence, this was an
    #: act, and it is in no tally.
    CALLED_OFF = "CALLED_OFF"
    #: A **booked** game whose hour came with a seat open (#544): somebody left
    #: after the club's cut-off and nobody took the seat, so it went ahead
    #: short — *uncounted, a seat was empty*. Read off the record and the clock
    #: — the hour, and a line-up with a seat open — like the three ends above,
    #: and **in no tally**, like a call-off: it is not an evening the people
    #: who stayed had, and not a ghost anybody owes.
    STARTED_SHORT = "STARTED_SHORT"
    #: Somebody who came to a **booked** game reported a player who did not
    #: (#547), and that player's day to dispute it is still running — a wait,
    #: like a score on the table, and neither an evening nor a ghost yet.
    NO_SHOW_REPORTED = "NO_SHOW_REPORTED"
    #: Every report of not turning up that stands has had its day undisputed
    #: (#547): **the game does not count** and nobody's Level moves, and the
    #: player who did not come carries the strongest mark on a record. In no
    #: tally — the people who came were not a four on a court.
    NO_SHOW = "NO_SHOW"


#: The five standings that mean *nothing more will happen to this game*. A
#: settled game refuses every act, which is ADR-0048's *a settled result is
#: final* with no support correction path and no reversal.
#:
#: **``CALLED_OFF`` is the fourth, and it is a fourth *kind* of ending** rather
#: than a spelling of the ghost's (``docs/adr/0163`` §3): a ghost is a window
#: closing on silence and this is a decision somebody took. They are one set here
#: because the readers of this set — the mutual mint's idempotence key, the
#: sportsmanship court, every act on the result — ask *is anything more going to
#: happen*, and for both the answer is no. **``STARTED_SHORT`` is the fifth**
#: (#544): a booked game's hour came with a seat open, and nothing more can.
#: **``NO_SHOW`` is the sixth** (#547): every standing report has had its day.
#: **``DISPUTED`` is the seventh** (#654): two scores named different winners.
SETTLED = frozenset(
    {
        GameStanding.NEVER_PLAYED,
        GameStanding.CONFIRMED,
        GameStanding.UNSCORED,
        GameStanding.DISPUTED,
        GameStanding.CALLED_OFF,
        GameStanding.STARTED_SHORT,
        GameStanding.NO_SHOW,
    }
)

#: The four standings that mean these people were on a court together. Read by
#: the pairwise fold, and by ``counted_games``. ``DISPUTED`` is one (#654): both
#: sides said they played, and disagreed only about who won. **``CALLED_OFF`` is
#: not here**, and neither is it read as a ghost anywhere: the history walk
#: answers ``None`` for it, as it does for a game still inside its window — and
#: nor is ``STARTED_SHORT`` (#544), for the same reason, nor ``NO_SHOW`` (#547):
#: the people who came were not the four the game was, and *shows up* reads it
#: per player instead.
PLAYED = frozenset(
    {
        GameStanding.AWAITING_ANSWER,
        GameStanding.CONFIRMED,
        GameStanding.UNSCORED,
        GameStanding.DISPUTED,
    }
)


@final
@dataclass(frozen=True, slots=True)
class Proposal:
    """One side's score, and the moment its clock started.

    ``at`` is the proposal's own or the correction's that re-dated it — the two
    are one fact here, because what the other side is answering is a score they
    can see.
    """

    side: GameSide
    by: UUID
    score: Score
    at: Instant


@final
@dataclass(frozen=True, slots=True)
class Acceptance:
    """Somebody agreed with the other side's score, and when — **which is when
    it settled** (#654).

    ``of_side`` is the side whose proposal was accepted — always the accepter's
    opposite, because *a teammate agreeing with a teammate proves nothing*.
    """

    by: UUID
    side: GameSide
    of_side: GameSide
    at: Instant


@final
@dataclass(frozen=True, slots=True)
class NoShowReport:
    """A player reported as not turning up to a booked game (#547): by whom,
    when, and whether they disputed it inside their day."""

    reported_by: UUID
    at: Instant
    disputed_at: Instant | None = None

    @property
    def dispute_closes_at(self) -> Instant:
        return dispute_closes_at(self.at)

    def stands_at(self, now: Instant) -> bool:
        """Undisputed, and its day over: the player did not come."""

        return self.disputed_at is None and now >= self.dispute_closes_at


def no_show_standing(
    no_shows: Mapping[UUID, NoShowReport], *, now: Instant
) -> GameStanding | None:
    """What the reports of not turning up make of a game — ``None`` with none.

    **A report has a day, and the game waits for every one** (the mechanics
    §15.3): while any undisputed report's day still runs, the reported player may
    still say they came, so nothing has settled. Then **one report that stood is
    enough**: the game does not count. **Every report disputed is nobody's
    verdict** — the platform does not arbitrate, as it does not arbitrate two
    scores — so it is *unscored*: an evening that proves nothing, on nobody's
    record.
    """

    if not no_shows:
        return None
    undisputed = [one for one in no_shows.values() if one.disputed_at is None]
    if any(now < one.dispute_closes_at for one in undisputed):
        return GameStanding.NO_SHOW_REPORTED
    if undisputed:
        return GameStanding.NO_SHOW
    return GameStanding.UNSCORED


def live_acceptance(
    *,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
) -> Acceptance | None:
    """The acceptance that still stands, if one does.

    **An acceptance settles at once and closes the game** (#654), so nothing is
    put on the table after one. A stream written while an acceptance still ran
    out a six-hour grace may hold a counter made inside it, which beat the
    acceptance then — so an acceptance with a score put on the table *after* it
    is void, and that stream still folds to what it was.
    """

    if acceptance is None:
        return None
    countered = any(
        proposal.at > acceptance.at for proposal in proposals.values()
    )
    return None if countered else acceptance


@final
@dataclass(frozen=True, slots=True)
class Settlement:
    """How the scores on a game's table settle, and when — **off the record
    alone**; whether the clock has reached ``at`` is the caller's question.

    ``score`` is the result, or ``None`` when the two scores named different
    winners, which settles the game **disputed** (#654). ``at`` is the moment it
    settles: the acceptance's own, the answer window closing, or — For fun —
    the score itself.
    """

    score: Score | None
    at: Instant


def settlement_of(
    *,
    kind: GameKind,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
) -> Settlement | None:
    """How the scores on the table settle (#654; ``docs/adr/0195`` §5), or
    ``None`` with none on it. **The one place the rules are**, so the standing,
    the agreed score and the moment it settled are one answer.

    - **For fun asks nothing**: the first score put up is the result, at once.
    - **One *That's right* settles it at once**, with the score it agreed with.
    - **A lone score** settles on silence when its answer window closes.
    - **Two scores** settle when the later one's answer window closes: naming
      the same winner, with the **closer** one — the smaller margin in games,
      and on a tie the first put up; naming different winners, **disputed**.
    """

    if not proposals:
        return None
    # The first put up, by when; the side breaks a tie the aggregate cannot
    # produce, so the answer never rests on mapping order (``docs/adr/0105``).
    first, *rest = sorted(proposals.values(), key=lambda one: (one.at, one.side.value))
    if kind is GameKind.FRIENDLY:
        return Settlement(score=first.score, at=first.at)
    agreed = live_acceptance(proposals=proposals, acceptance=acceptance)
    if agreed is not None:
        accepted = proposals.get(agreed.of_side)
        if accepted is not None:
            return Settlement(score=accepted.score, at=agreed.at)
    if not rest:
        return Settlement(score=first.score, at=proposal_closes_at(first.at))
    (second,) = rest
    closes = proposal_closes_at(second.at)
    if first.score.winner is not second.score.winner:
        return Settlement(score=None, at=closes)
    closer = second if second.score.margin < first.score.margin else first
    return Settlement(score=closer.score, at=closes)


def standing_of(
    *,
    kind: GameKind,
    planned_at: Instant,
    starts_at: Instant | None,
    played_at: Instant | None,
    called_off_at: Instant | None,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
    now: Instant,
    line_up_complete: bool,
    no_shows: Mapping[UUID, NoShowReport],
) -> GameStanding:
    """The game's standing, from its record and this instant.

    The order of the questions is the design, and each rung is a decision:

    **Was it called off?** The one question here that is not a reading of the
    clock, and it is asked first (``docs/adr/0163``): every other answer is
    still what it was — the game is on the record and its window may not have
    closed — so a
    fold that read the clock first would answer with the standing somebody has
    just ended, and would turn a called-off game into a ghost the day its window
    closed. ``called_off_at`` is **stated by every caller and never defaulted**,
    so a second reader of this function has to say which game it is asking about
    rather than inheriting an answer — and so is ``line_up_complete``, for the
    same reason, and ``kind``.

    **Did its booked hour come with a seat open?** (#544) A booked game is
    the one with an hour, and a seat nobody took by then is a game that went
    ahead short: nothing more can happen to it. Asked before the entry,
    because a court with a seat open refuses one.

    **Did somebody not come?** (#547) A report of a booked game's player not
    turning up is the entry for that game — no score stands beside one, and no
    score is taken after one — so its day, and what it came to, is the
    standing (``no_show_standing``).

    **Did it happen at all?** Nothing about a score matters until somebody says
    they played, and after the entry window nothing ever will.

    **Has what is on the table settled?** ``settlement_of`` says how it settles
    and when: once the clock has reached that moment the game is confirmed —
    or, two scores having named different winners, disputed.
    """

    if called_off_at is not None:
        return GameStanding.CALLED_OFF

    if (
        played_at is None
        and starts_at is not None
        and not line_up_complete
        and now >= starts_at
    ):
        return GameStanding.STARTED_SHORT

    reported = no_show_standing(no_shows, now=now)
    if reported is not None:
        return reported

    if played_at is None:
        return (
            GameStanding.AWAITING_ENTRY
            if now < entry_closes_at(planned_at, starts_at=starts_at)
            else GameStanding.NEVER_PLAYED
        )

    settles = settlement_of(kind=kind, proposals=proposals, acceptance=acceptance)
    if settles is None or now < settles.at:
        # ``None`` is unreachable through the aggregate — the entry that records
        # *we played* records a score in the same act — and is stated rather
        # than raised, because a read is a bad place to crash about a stream
        # somebody else wrote: it is still a game nobody has agreed a score for.
        return GameStanding.AWAITING_ANSWER
    if settles.score is None:
        return GameStanding.DISPUTED
    return GameStanding.CONFIRMED


def settled_at(
    *,
    kind: GameKind,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
) -> Instant | None:
    """**When** a result becomes final — ``None`` when the scores on the table
    settle on no result, because they named different winners.

    The third question beside *which score* and *has it settled*, and it is asked
    separately for the same reason those two are: it is answerable off the record
    alone, where *has it settled* needs the clock. A caller checks the standing
    first — ``Game.confirmed_at`` is that pair written once.

    It exists because a confirmation **announces nothing** (``docs/adr/0137``),
    so anybody catching up on results has to walk them in an order, and the only
    honest order is the one they became final in. The instant is derived — an
    acceptance's own moment, or the answer window closing — so it is the same
    answer at every instant and on every reader's clock, which is exactly what a
    cursor needs and what a stored ``confirmed_at`` column could not promise
    (``docs/adr/0139``).
    """

    settles = settlement_of(kind=kind, proposals=proposals, acceptance=acceptance)
    if settles is None or settles.score is None:
        return None
    return settles.at


def agreed_score(
    *,
    kind: GameKind,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
) -> Score | None:
    """**Which** score would settle, if anything has. Never *whether*.

    The two questions are deliberately apart: this one is answerable off the
    proposals alone, and *has it settled* needs the clock. A caller wanting the
    confirmed result asks ``standing_of`` first — ``Game.confirmed_score_at``
    is that pair written once, so nobody publishes a score the standing has not
    reached.

    ``None`` when two scores named different winners, which this platform
    refuses to arbitrate.
    """

    settles = settlement_of(kind=kind, proposals=proposals, acceptance=acceptance)
    return None if settles is None else settles.score
