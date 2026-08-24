"""The result screen: four facts, two clocks, and three things she may do.

ADR-0074's route in values, and it is ADR-0086's shape read the other way round
— that one carried a quote and a table of outcomes, this one carries a score and
a conversation. What both share is everything above the middle: the same spine,
the same situation half off the same ladder, and **not a card** — no fit badge,
no emphasis flag, no card stamp, because all three are judgements the
*composition* made about a card's place on Now and none of them means anything on
a screen with one thing on it.

**Five renderings, one reader.** Entry, both audience renderings of a live
proposal, the counter, the settled result and the unscored ending are the ladder
answering ``needsResult``, ``confirmResult``, ``completed`` and ``playedNoScore``
for the viewer who asked — ADR-0060's *render by situation, not by a screen
identifier*. Nothing here names a rendering, and there is no screen id anywhere
on the wire.

**The result block is four facts and nothing more** (ADR-0034, ADR-0074): the
score on the table, which side put it there, whether it has settled, and how many
sides have spoken. **No history** — a counter *replaces* what was on the table,
and printing the score it beat invites arguing with a number that is no longer
live. It is **always present and empty when nothing is on the table**, which is
the asymmetry ADR-0070 draws: a region makes no claim and is present and empty, a
shelf makes one and is absent. This block makes none.

**Two clocks, both named.** A card gets one slot because a thirty-six-row rule
about *which fact is the clock* must not live on the phone; that argument does
not bind a screen resolving one situation, and this one has two live deadlines at
once. The settlement deadline is the hero (ADR-0060); the acceptance grace is the
quieter line and is **present only while it runs** — hiding it would produce the
outcome ADR-0048 built it to prevent, inverted: a player taps accept, the screen
says *settled*, and thirty minutes later it is not.

**No ``phase`` field and no version.** The situation says which of the five
renderings this is, and ADR-0074 refused a client-held version outright: it would
make the phone hold a rule about its own staleness and buy a distinction the
player cannot act on differently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import (
    SIDES,
    Instant,
    MatchRecord,
    Situation,
    match_end,
    minutes,
    result_window,
    settlement_deadline,
    shifted,
)

from app.modules.now.domain.enrolled import PlayedScore
from app.modules.now.domain.screen import (
    Money,
    Place,
    ScoreLine,
    ScoreSide,
    SeatCounts,
    SetScore,
    SituationHalf,
)

#: How long after a proposal an acceptance still loses to a counter (ADR-0048).
#: *"In a four-player match somebody is always slower to their phone, and without
#: this a partner's fast tap closes the door on an opponent who was still in the
#: shower."*
#:
#: It lives here and **not in the kernel**, because no rung reads it: it changes
#: nothing about what the match is doing and everything about what the screen may
#: say, which is this module's business and not the ladder's. A boundary in the
#: kernel is a moment the ladder compares a clock against, and putting a purely
#: editorial one there would arm a wake for a look with nothing to find.
ACCEPTANCE_GRACE_MINUTES = 30


@final
@dataclass(frozen=True)
class ResultBlock:
    """What is on the table, and who has spoken. Four facts and no history.

    Empty rather than absent when nothing has been entered: an empty score and a
    zero count on ``needsResult``, so *not there* and *there and empty* cannot be
    handled in one place and not the other.

    ``proposed_by`` indexes into ``score.sides``, which the composer has already
    put the **viewer's side first** in — so index 0 is always *your side* and the
    phone subtracts nothing to know whose score it is looking at. It is a side
    and never a player: ADR-0048 caps proposals per side, and naming the
    teammate who typed it would put a person in an argument the model holds
    between two halves of a net.
    """

    agreed: bool
    proposals: int
    score: ScoreLine | None = None
    proposed_by: int | None = None

    def __post_init__(self) -> None:
        if (self.score is None) != (self.proposed_by is None):
            raise ValueError(
                f"a table holding {self.score!r} proposed by {self.proposed_by!r}"
            )


@final
@dataclass(frozen=True)
class ResultScreen:
    """The result conversation, for one viewer, at one instant.

    The first four fields are the card's spine, composed by the **same** function
    that composes the strip's card, so the screen she arrives on cannot describe
    the match differently from the card she tapped.

    ``counts`` rides here rather than only inside the situation half for the
    reason the departure screen's does: that half is the one a phone reads only
    when it knows the name, and a fact the screen always draws cannot live only
    in the half that may be skipped.
    """

    match_id: UUID
    where: Place
    price: Money
    situation: SituationHalf

    result: ResultBlock
    counts: SeatCounts

    may_enter: bool = False
    may_accept: bool = False
    may_counter: bool = False

    #: The hero clock: when this conversation ends by itself. It is the live
    #: proposal's own deadline once there is one and the entry deadline before
    #: that, which is *"the remaining time is the largest figure on the screen,
    #: next to the sentence that says nobody has to do anything"* (ADR-0060) in
    #: both renderings — the thing that happens without her is the same kind of
    #: thing in each. `None` once the answer has arrived: a settled result and an
    #: unscored evening count to nothing rather than to zero.
    settlement_deadline: Instant | None = None

    #: The second, quieter line, present **only while it runs**: inside it a
    #: counter beats a pending acceptance, so the screen must not say *settled*
    #: half an hour early.
    acceptance_grace: Instant | None = None


def result_block(record: MatchRecord, score: PlayedScore | None) -> ResultBlock:
    """The four facts, with the viewer's side put first.

    The flip is the composer's and happens once, here and in ``card_of``, for the
    reason ``PlayedScore`` states: doing it in the adapter would make what comes
    out of the database depend on who asked.

    A score that has **settled** is still on the table and still printed — the
    settled rendering is one of ADR-0060's five, and it is the one that prints a
    scoreline on a card.
    """

    if score is None:
        return ResultBlock(agreed=record.result_agreed, proposals=record.proposals)
    mine = 0 if score.viewer_side is None else score.viewer_side
    theirs = 1 - mine
    return ResultBlock(
        agreed=record.result_agreed,
        proposals=record.proposals,
        score=ScoreLine(
            sides=(
                ScoreSide(players=score.sides[mine]),
                ScoreSide(players=score.sides[theirs]),
            ),
            sets=tuple(
                SetScore(first=games[mine], second=games[theirs])
                for games in score.sets
            ),
        ),
        proposed_by=(
            None
            if score.proposed_side is None
            else (0 if score.proposed_side == mine else 1)
        ),
    )


def hero_clock(record: MatchRecord, now: Instant) -> Instant | None:
    """When this conversation ends on its own, or `None` once it has.

    Two deadlines and one slot, and which one is live is a fact about the record
    rather than a choice: before anybody speaks the clock is the **entry**
    deadline, and from the first proposal it is that proposal's own. They are the
    same kind of promise — *this is what happens if nobody does anything* — which
    is why ADR-0060 could call one of them the hero without naming which.

    Empty once the answer is in. A settled result and an unscored evening are
    both over, and a card that is over counts to nothing rather than to zero —
    the same rule ``kernel.card_clock`` applies one ring out.
    """

    if now < match_end(record) or record.result_agreed:
        return None
    settles = settlement_deadline(record)
    if settles is not None:
        return None if now >= settles else settles
    entry = result_window(record)
    return None if now >= entry else entry


def acceptance_grace(record: MatchRecord, now: Instant) -> Instant | None:
    """When a counter stops beating a pending acceptance, while that is running.

    Present **only while it runs**, which is what ``opens_at`` on the departure
    screen's table already does one route over: a moment that has passed is a
    moment nothing counts to, and a screen printing one would be counting down to
    something that already happened.
    """

    if record.proposed_at is None or record.result_agreed:
        return None
    ends = shifted(record.proposed_at, minutes(ACCEPTANCE_GRACE_MINUTES))
    return None if now >= ends else ends


def may_enter(
    situation_now: Situation, *, holds_seat: bool, block: ResultBlock
) -> bool:
    """Whether she may put **her own side's** score on the table.

    **One act at two moments**: the first entry, and replacing her side's live
    proposal — ADR-0048 calls the second a correction rather than a second
    proposal, *"and a player fixing his own typing before anyone has read it"* is
    not one of the three attempts. The client is told *may I put up a score*
    rather than *which of the two this would be*, which is the difference
    between a fact and a rule (ADR-0053).

    It is **not** *there is a score and I played*: with the other side's score on
    the table the act she has is a counter, and offering both would put two
    controls in front of one tap and let a client pick the wrong one.
    """

    if not holds_seat:
        return False
    if situation_now is Situation.NEEDS_RESULT:
        return True
    return situation_now is Situation.CONFIRM_RESULT and block.proposed_by == 0


def may_accept(
    situation_now: Situation, *, holds_seat: bool, block: ResultBlock
) -> bool:
    """Whether she may agree with what is on the table.

    Opposing side only and one opponent suffices (ADR-0048): a teammate agreeing
    with a teammate proves nothing. ``proposed_by`` is already viewer-first, so
    *the other side put it up* is exactly ``proposed_by == 1`` and the rule is one
    comparison rather than a second reading of the seats.
    """

    return (
        holds_seat
        and situation_now is Situation.CONFIRM_RESULT
        and block.proposed_by == 1
    )


def may_counter(
    situation_now: Situation, *, holds_seat: bool, block: ResultBlock
) -> bool:
    """Whether she may put a **different** score up against the one on the table.

    Her side must not already have spoken, which at two proposals it has: from
    there ADR-0048 leaves only an explicit acceptance, and *"a third would be one
    side repeating itself"*. A player on the **proposing** side is offered
    ``may_enter`` instead, which is the freer of the two — the rule that makes a
    teammate's agreement worthless is the same rule that makes her objection
    credible, and a correction has no cap on it at all.
    """

    return (
        holds_seat
        and situation_now is Situation.CONFIRM_RESULT
        and block.proposed_by == 1
        and block.proposals < SIDES
    )


