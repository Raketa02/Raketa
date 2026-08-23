"""The enrolled strip: her own matches, in order, each saying what it is doing.

The region a player is **committed** to, above the suggestions and never ordered
by quality. Four rules run over it and each is *one* rule rather than a table of
thirty-six judgements (ADR-0073):

- **chronological, fixed at composition**, so a card never moves as she reaches
  for it;
- **counting is by money** — seats paid, with a held-and-unpaid seat as its own
  number beside that count;
- **one clock**, the next moment something happens to her whether she acts or
  not, which is ``kernel.card_clock``;
- **a card lives twenty-four hours from the moment it closed**, not from when the
  match would have ended.

Everything else a card carries is present exactly when the fact exists — a hold,
a court's name, a refund, an owner's exposure, a score, a departure — so no
situation is named anywhere below.

**No act, and one exit control.** ADR-0083's rule is *a card names an act when
the viewer can take it now **and a v1 surface can receive it***, and of the six
surfaces exactly one now exists: the departure route (``Raketa02/Raketa#80``),
so ``may_depart`` is composed for real. The seat claim and its payment are
``#89``, the result route ``#79``, leaving standby ``#81``, and until each lands
its act stays absent — a card naming an act that opens nothing is a door offered
that will not open, which is the one thing that ADR says is worse than the gap.

**The exit is a spine boolean and not a seventh act** (ADR-0086). Leaving is not
the card's act: putting it in ``cta`` would reopen an enumeration ADR-0083
deliberately closed and give one card two act codes. It is the kernel's
``may_depart``, which is the function ``Match.depart`` refuses on, so the control
is drawn exactly where the write would succeed and nowhere else.

**No fit badge and no emphasis either.** Both are judgements about a *suggestion*
— ADR-0037's badge is about a seat she could take and ADR-0051's emphatic card
shouts *take this one* — and neither means anything about a match she is already
in.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import (
    Cause,
    Instant,
    MatchKind,
    MatchRecord,
    Minutes,
    Sport,
    Viewer,
    card_clock,
    court_named_at,
    filled,
    grosze,
    hours,
    is_terminal,
    match_end,
    may_depart,
    seat_count,
    shifted,
    situation,
)

from app.modules.now.domain.cards import counts_of, hold_note
from app.modules.now.domain.enrolled import Enrolment, PlayedScore
from app.modules.now.domain.ports import EnrolledMatches
from app.modules.now.domain.screen import (
    EnrolledRegion,
    MatchCard,
    Money,
    OwnerExposure,
    Refund,
    ScoreLine,
    ScoreSide,
    SeatClaim,
    SetScore,
    SituationFacts,
    SituationHalf,
    Stamp,
)
from app.modules.now.domain.vocabulary import (
    CANCELLATION_CAUSE_OF,
    REFUND_DESTINATION_OF,
)

#: How long a card stays after the match it is about closed. ADR-0073 narrows
#: ADR-0048's ``matchEnd + 24 h``, which stays right for every played ending —
#: for those the two moments coincide — and is absurd for a cancellation: a match
#: killed on Thursday for a Saturday game would sit on a home screen until
#: Sunday. One rule for all ten post-match situations instead of one clock for
#: played matches and another for cancelled ones.
CARD_TAIL: Minutes = hours(24)


class ComposeEnrolled:
    """The enrolled region, composed for one viewer at one instant."""

    def __init__(self, *, enrolled: EnrolledMatches) -> None:
        self._enrolled = enrolled

    async def compose(
        self,
        *,
        viewer: UUID,
        sport: Sport | None,
        now: Instant,
        stamp: Stamp,
    ) -> EnrolledRegion:
        """Her matches, chronological, with the closed ones past their tail gone.

        ``sport`` is the **named chip** and never the resolved set. ADR-0084
        filters the strip along with the shelves — ``S.sport === 'all' ||
        m.sport === S.sport``, quoted there verbatim — so a chosen sport hides
        the rest and ``all`` hides nothing. Resolving ``all`` to the sports she
        holds a rating at is an argument about *Best fit for you* being a claim
        about her, and applying it here would hide a match she has paid for and
        is playing tomorrow because nobody has rated her at it yet — which is
        the very mistake that ADR decides the default on.
        """

        rows = await self._enrolled.for_player(player_id=viewer, now=now)
        return EnrolledRegion(
            stamp=stamp,
            cards=tuple(
                card_of(row, now=now, stamp=stamp)
                for row in rows
                if sport is None or row.record.sport is sport
                if _still_on_screen(row, now)
            ),
        )


def card_of(row: Enrolment, *, now: Instant, stamp: Stamp) -> MatchCard:
    """One row as the card a phone draws, and the **only** place one is built.

    A module-level function rather than a method because an action off Now needs
    exactly this and nothing else around it: the departure route composes the
    card it hands back from the same expression the strip composes its own from
    (``Raketa02/Raketa#80``), so the screen a player is corrected onto cannot
    describe the match differently from the card she tapped. A second
    transcription would be two answers to *what is this match doing*.
    """

    record = row.record
    claim = row.claim_expires_at
    holds_claim = claim is not None and claim > now
    return MatchCard(
        match_id=row.match_id,
        stamp=stamp,
        where=row.where,
        # Written for whoever is looking: her own share inside the match,
        # what she *would* pay browsing. One number and never both with a
        # flag, which would ship a figure that does not apply on every card
        # forever and invite the bug where the wrong one prints.
        price=row.share,
        situation=SituationHalf(
            situation=situation(record, Viewer(holds_seat=row.holds_seat), now),
            facts=_facts(row, now=now),
        ),
        clock=card_clock(record, now, claim_expires_at=claim),
        # The third control in the action row, and a **spine** boolean rather
        # than an act code (ADR-0086): leaving is not the card's act, and
        # putting it in `cta` would give one card two of them. It is the
        # kernel's answer, which is the same function `Match.depart` refuses on
        # — so the control is drawn exactly where the write would succeed.
        may_depart=may_depart(
            record, now, holds_seat=row.holds_seat, holds_claim=holds_claim
        ),
        seat_claim=(
            None if claim is None or not holds_claim else SeatClaim(expires_at=claim)
        ),
    )


def _still_on_screen(row: Enrolment, now: Instant) -> bool:
    """Whether this card's twenty-four hours are still running.

    A match that has not closed has no tail at all, which is why this answers
    ``True`` by having nothing to compare against rather than by a far-future
    moment: *no closing* and *a closing a long way off* are different facts and
    only one of them is true of a match being played next month.
    """

    closed = _closed_at(row, now)
    return closed is None or now < shifted(closed, CARD_TAIL)


def _closed_at(row: Enrolment, now: Instant) -> Instant | None:
    """The moment the match stopped being a game anybody was going to play.

    Two answers and one of them is stored. A **played** match closed when it was
    played, and ``match_end`` says so — ADR-0073's own example, *"played Tuesday
    20:30, gone Wednesday 20:30"*. A **cancelled** one closed when somebody
    cancelled it, which no reader can reconstruct, so Matches records it.

    The fallback is for a terminal row written before that column existed, and
    it is ADR-0048's original ``matchEnd + 24 h`` — the rule such a card would
    have expired under anyway — rather than *never expires*, which is the only
    other thing a missing instant could mean.
    """

    if is_terminal(row.record):
        return row.closed_at or match_end(row.record)
    if now >= match_end(row.record):
        return match_end(row.record)
    return None


def _facts(row: Enrolment, *, now: Instant) -> SituationFacts:
    """Every fact this card carries, each present exactly when it exists."""

    record = row.record
    cause = _cause(record, now)
    return SituationFacts(
        counts=counts_of(record, now=now),
        court_total=row.court_total,
        hold=hold_note(record, now=now),
        cause=cause,
        court=_court(row, now=now),
        refund=_refund(row, cause=cause),
        owner=_owner(row),
        score=_score(row.score),
        departure=row.departure,
    )


def _cause(record: MatchRecord, now: Instant) -> Cause | None:
    """Which cancellation this is, off the ladder rather than off the flags.

    Reading the record's five booleans here would be rungs 1-4 written a second
    time, in a second order — and the order inside that group is load-bearing,
    because losing inventory *also* sets the club cancellation and without the
    earlier test every lost court reads as weather.
    """

    return CANCELLATION_CAUSE_OF.get(situation(record, None, now))


def _court(row: Enrolment, *, now: Instant) -> str | None:
    """The specific court, and only once it is hers to know.

    ``kernel.court_named_at`` is fifteen minutes before play, and everywhere
    earlier the card says the category — because a court is assigned and may be
    reassigned, and naming one on Monday for Thursday is a promise the club has
    not made.
    """

    if now < court_named_at(row.record.start):
        return None
    return row.court


def _refund(row: Enrolment, *, cause: Cause | None) -> Refund | None:
    """What a cancellation gives back, and where it went.

    Present only on a cancellation, and only when she put money in: a card
    naming a refund to somebody who never paid is a claim about money that never
    moved. ``paid_in`` is a fold off her own ledger rather than the seat's price,
    so a seat taken and never paid for names nothing.
    """

    if cause is None or row.paid_in is None or int(row.paid_in.amount) <= 0:
        return None
    return Refund(amount=row.paid_in, destination=REFUND_DESTINATION_OF[cause])


def _owner(row: Enrolment) -> OwnerExposure | None:
    """A private court's two figures, and why they disagree.

    ``guaranteed`` is the whole court and never shrinks (ADR-0045); ``recovered``
    is what the **marketplace** has paid in. The private party holds the seats
    that were not opened, so the marketplace's paid shares are the paid seats
    beyond them — and when fewer of the private party have paid than hold seats,
    this under-counts rather than over-counts, which is the safe direction for a
    figure telling somebody how much of her money is back.

    It is a fact about the **court** and not about the viewer, because the record
    carries no owner (``Raketa02/Raketa#99``). Every private situation in v1
    arrives from seed, so the gap is bounded by the seeded demo.
    """

    record = row.record
    if record.kind is not MatchKind.PRIVATE:
        return None
    private_party = seat_count(record) - record.open_seats
    from_the_marketplace = max(0, filled(record) - private_party)
    return OwnerExposure(
        recovered=Money(
            amount=grosze(int(row.share.amount) * from_the_marketplace),
            currency=row.share.currency,
        ),
        guaranteed=row.court_total,
    )


def _score(score: PlayedScore | None) -> ScoreLine | None:
    """The score with the viewer's side first, or the match's own order.

    The flip is the card's judgement and it happens once, here: the stored score
    reads side A then side B in the seats' fixed order, so it means the same
    thing however a card arranges the names, and a viewer who did not play gets
    that order unchanged rather than an arrangement invented for her.
    """

    if score is None:
        return None
    mine = 0 if score.viewer_side is None else score.viewer_side
    theirs = 1 - mine
    return ScoreLine(
        sides=(
            ScoreSide(players=score.sides[mine]),
            ScoreSide(players=score.sides[theirs]),
        ),
        sets=tuple(
            SetScore(first=games[mine], second=games[theirs]) for games in score.sets
        ),
    )
