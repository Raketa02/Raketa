"""Shelves 1 and 2: retrieve → eligibility → score → floor → order → diversity → cap.

The ranked half of Now, and the only part of the screen where a match is judged
rather than merely listed. Two shelves run through **one** funnel; what separates
them is a single eligibility rule, a floor and a cap, which is the delta's *"a
lane is data, not a branch"* held to.

**Retrieval knows nothing about the viewer.** ``CityMatches`` takes a window and
a sport filter and answers scoring contexts, and its own safety valve bounds what
it will build. Every judgement about *this* player — what she is already doing,
what she is queued for, whether she can be ranked at all — is made here, where it
can be exercised without a database.

**The context cache is behind ``CityMatches`` rather than in front of it**, and
that is where ADR-0068's own line puts it: the new-arrivals cache is cache-aside
in its composer because *"the key is a fact about the viewer and the port's
question is not"*, and this key — ``matchId : recordVersion`` — is a fact about
the match. Above the port it would mean assembling every context and then
discarding it for the copy already held, which is a cache that saves nothing.
Nothing in this file knows it exists.

**Eligibility is exhaustive.** ``exclusions`` answers the set of rules a
candidate failed, so nothing in this file can be a chain of ``and``s that stops
at the first ``False``, and the histogram the delta asks for is a by-product
rather than a second pass.

**Degrade is caught once, per screen.** A scorer that throws leaves the whole
ranking untrustworthy, not one card of it: shelf 1 falls back to soonest-first
with no badge under the ``sameLevel`` code, and shelf 2 is **dropped entirely**,
because an 80 floor with no scorer is not a claim we can make. **No marker
crosses the wire** — a degrade flag would be a fact about our infrastructure
printed on a player's home screen.

**Every ask pays the full funnel.** ADR-0068 deletes the player feed cache by
name: it was the answer to a load shape that no longer exists, and it is the only
place on this screen that could serve a stale answer to a direct question.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from app.engines.matchmaking import Occupant, PlayerRef, UnratedPlayer
from app.kernel import (
    MINUTES_PER_DAY,
    Instant,
    Sport,
    card_clock,
    is_full,
    minutes,
    shifted,
    situation,
)

from app.modules.now.application.scoring import MatchScorer, Unscorable, badge_from
from app.modules.now.domain.cards import counts_of, hold_note
from app.modules.now.domain.funnel import (
    CANDIDATE_HORIZON_DAYS,
    Lane,
    MatchScoringContext,
    Ranked,
    Scored,
    Viewer,
    cap_for,
    code_for,
    diversify,
    exclusions,
    feed_key,
    floor_for,
    keep,
)
from app.modules.now.domain.ports import (
    CityMatches,
    Commitments,
    Ratings,
    StandbyPlaces,
)
from app.modules.now.domain.screen import (
    Fit,
    MatchCard,
    Place,
    Shelf,
    SituationFacts,
    SituationHalf,
    Stamp,
)


class ComposeShelves:
    """The two ranked shelves, composed for one viewer at one instant."""

    def __init__(
        self,
        *,
        city: CityMatches,
        commitments: Commitments,
        standby: StandbyPlaces,
        ratings: Ratings,
        scorer: MatchScorer,
    ) -> None:
        self._city = city
        self._commitments = commitments
        self._standby = standby
        self._ratings = ratings
        self._scorer = scorer

    async def compose(
        self,
        *,
        viewer: UUID,
        sports: frozenset[Sport],
        now: Instant,
        stamp: Stamp,
    ) -> Ranked:
        """Shelf 1 and shelf 2, in the server's order, absent when empty.

        **Shelf 1 is never absent for a viewer with any eligible match**, which
        is what the retitle buys: when nothing clears 70 the shelf keeps its
        cards, drops its floor and changes its claim. Shelf 2 has no such
        fallback and is absent whenever nothing clears 80, because *wait for
        this* is a claim that cannot be softened.

        **A player with no rating at a sport is not ranked against it.** She is
        owed a door into that questionnaire instead (ADR-0084), and the door
        takes these two shelves' position precisely because there is nothing for
        them to hold. Composing a ranked shelf for her would print an order
        computed from a Level nobody holds.

        **The scores come out with the shelves.** Emphasis is a property of the
        composed *screen* and gates on three numbers this funnel has already
        computed, so stopping them at this edge would mean scoring twice on the
        one screen whose whole cost is scoring. Only what a shelf **kept** is
        carried: a candidate the floor, the cap or a lane rule removed is not on
        the screen, and a pass that could reach it would be flagging a card
        nobody can see.
        """

        rankable = await self._rankable(viewer, sports)
        if not rankable:
            return Ranked()

        candidates = await self._candidates(sports=rankable, now=now)
        if not candidates:
            return Ranked()

        who = await self._viewer(viewer)
        shelves: list[Shelf] = []
        scores: list[Scored] = []
        for lane in Lane:
            one = await self._shelf(
                lane=lane,
                candidates=candidates,
                who=who,
                sports=rankable,
                now=now,
                stamp=stamp,
            )
            if one is None:
                continue
            shelves.extend(one.shelves)
            scores.extend(one.scores)
        return Ranked(shelves=tuple(shelves), scores=tuple(scores))

    async def _rankable(
        self, viewer: UUID, sports: frozenset[Sport]
    ) -> frozenset[Sport]:
        """The sports of the filter this viewer can actually be ranked at.

        ``all`` already resolves to the sports she holds a rating at, so this
        only ever narrows a **named** chip — the one case ADR-0084 answers with a
        door rather than with a shelf. Asking the rating port rather than
        trusting the filter is what keeps the two answers from disagreeing on
        the one path where they can.
        """

        held: set[Sport] = set()
        for sport in sports:
            if await self._ratings.occupant(player_id=viewer, sport=sport) is not None:
                held.add(sport)
        return frozenset(held)

    async def _viewer(self, viewer: UUID) -> Viewer:
        """Her identity, her diary and her queue — the three eligibility reads."""

        commitments = await self._commitments.held_by(viewer)
        return Viewer(
            player_id=viewer,
            mine=frozenset(match_id for match_id, _, _ in commitments),
            busy=tuple((start, end) for _, start, end in commitments),
            on_standby=await self._standby.for_player(viewer),
        )

    async def _candidates(
        self, *, sports: frozenset[Sport], now: Instant
    ) -> tuple[MatchScoringContext, ...]:
        """Every match in the horizon, in the order retrieval answered.

        The horizon is the only window a *suggestion* has: a match five months
        out is a real match and a bad recommendation, and the retrieval's own
        specification asks for high recall against an index rather than for the
        whole table.
        """

        window_to = shifted(now, minutes(CANDIDATE_HORIZON_DAYS * MINUTES_PER_DAY))
        return await self._city.contexts(
            sports=sports, window_from=now, window_to=window_to
        )

    async def _shelf(
        self,
        *,
        lane: Lane,
        candidates: Sequence[MatchScoringContext],
        who: Viewer,
        sports: frozenset[Sport],
        now: Instant,
        stamp: Stamp,
    ) -> Ranked | None:
        eligible = tuple(
            one
            for one in candidates
            if not exclusions(one, viewer=who, sports=sports, lane=lane, now=now)
        )
        if not eligible:
            return None

        try:
            scored = await self._score(eligible, who=who, now=now)
        except Unscorable:
            return self._degraded(lane, eligible, now=now, stamp=stamp)

        return self._ranked(lane, scored, now=now, stamp=stamp)

    async def _score(
        self, candidates: Sequence[MatchScoringContext], *, who: Viewer, now: Instant
    ) -> tuple[Scored, ...]:
        out: list[Scored] = []
        for context in candidates:
            viewer = await self._occupant(who.player_id, context.record.sport)
            score, analysis = self._scorer.score(context, viewer=viewer, now=now)
            badge = badge_from(
                score,
                analysis,
                rated=not isinstance(viewer, UnratedPlayer),
                # The platform holds no player location, so the travel term's
                # minutes are a sentinel: they may rank, because a constraint
                # term scores the same for every candidate, and they may never be
                # printed. One boolean at one call site, on the day #102 lands.
                travel_measured=_distance(None) is not None,
            )
            out.append(
                Scored(
                    context=context,
                    fit=score.fit,
                    coverage=score.coverage,
                    # A viewer who reaches a ranked shelf holds a rating at its
                    # sport — ``_rankable`` is what guarantees it — so the badge
                    # is never withheld here in practice. It is still read
                    # through the rule rather than assumed, because the rule and
                    # the guarantee are two different statements and only one of
                    # them is this file's.
                    badge=badge if badge is not None else Fit(score=20),
                    has_free_seat=not is_full(context.record),
                )
            )
        return tuple(out)

    async def _occupant(self, player_id: UUID, sport: Sport) -> Occupant:
        """Her rating at the match's sport, or the honest absence of one.

        ``UnratedPlayer`` is an ordinary state and not an error: the *filter*
        guarantees a rating at the chip's sport, and under ``all`` a candidate's
        sport is one of the sports she holds — so this falls back only where a
        rating vanished between two reads of one compose.
        """

        found = await self._ratings.occupant(player_id=player_id, sport=sport)
        if found is not None:
            return found
        return UnratedPlayer(player=PlayerRef(str(player_id)))

    def _ranked(
        self, lane: Lane, scored: Sequence[Scored], *, now: Instant, stamp: Stamp
    ) -> Ranked | None:
        """Floor → ``FEED_ORDER`` → diversity → cap, in that order and no other.

        The floor runs **before** the order, so a shelf that has to be retitled
        is one that had nothing above its floor rather than nothing in its first
        six. Diversity runs **after** the order and before the cap, because it
        is a delta over ``FEED_ORDER`` and a cap applied first would be a cap
        over an order nobody composed.
        """

        above = _above(scored, floor=floor_for(lane, retitled=False))
        retitled = lane is Lane.OPEN and not above
        if retitled:
            above = _above(scored, floor=floor_for(lane, retitled=True))
        if not above:
            return None

        ordered = sorted(
            above, key=lambda one: feed_key(one, distance_km=_distance(one))
        )
        # Shelf 2's cards are full matches, so *two from one club in one hour*
        # is not a variety problem the player can act on — every one of them is
        # something to wait for rather than something to choose between. The
        # delta gives it no diversity policy, and a pass that reorders a
        # three-card shelf would be a rule with nowhere to fire.
        varied = diversify(ordered) if lane is Lane.OPEN else tuple(ordered)
        kept = keep(varied, cap=cap_for(lane))

        return Ranked(
            shelves=(
                Shelf(
                    code=code_for(lane, retitled=retitled),
                    cards=tuple(
                        _card(one.context, badge=one.badge, now=now, stamp=stamp)
                        for one in kept
                    ),
                ),
            ),
            scores=kept,
        )

    def _degraded(
        self,
        lane: Lane,
        eligible: Sequence[MatchScoringContext],
        *,
        now: Instant,
        stamp: Stamp,
    ) -> Ranked | None:
        """What a shelf is when the scorer could not answer.

        Shelf 1 keeps its cards, loses every badge and takes the ``sameLevel``
        code — the fallback a thin week already produces, so the degraded screen
        is one players have seen rather than a mode built for an incident. Shelf
        2 is dropped, because asking somebody to wait for something we cannot
        currently grade is worse than not asking.

        **Nothing says so on the wire.** The card carries no badge, which is what
        an unrated viewer's card also carries, and that is the whole of the
        client's experience of a degrade.

        **And no score comes out**, so the degraded screen has no emphatic card
        either. That is one consequence rather than a second decision: emphasis
        gates on a fit and a coverage, and a screen that could not compute a
        badge cannot have computed the two numbers that would license shouting
        about one.
        """

        if lane is Lane.FULL:
            return None
        soonest = sorted(
            eligible, key=lambda one: (one.record.start, str(one.match_id))
        )
        return Ranked(
            shelves=(
                Shelf(
                    code=code_for(lane, retitled=True),
                    cards=tuple(
                        _card(one, badge=None, now=now, stamp=stamp)
                        for one in soonest[: cap_for(lane)]
                    ),
                ),
            ),
        )


def _above(scored: Sequence[Scored], *, floor: int | None) -> tuple[Scored, ...]:
    if floor is None:
        return tuple(scored)
    return tuple(one for one in scored if one.fit >= floor)


def _distance(scored: Scored | None) -> int | None:
    """How far the club is from the viewer. **Unknown for every viewer today.**

    ADR-0063 makes a player's anchor optional and *precision follows the
    anchor*, and no context stores one (``Raketa02/Raketa#102``). It is read
    through a named function rather than written as ``None`` at the call site so
    that the day the fact has a source, the sort key is not the thing being
    edited.
    """

    return None


def _card(
    context: MatchScoringContext,
    *,
    badge: Fit | None,
    now: Instant,
    stamp: Stamp,
) -> MatchCard:
    """A shelf card: the spine, the situation half, and no action row.

    **A shelf card names no act and offers no exit**, which is the same refusal
    the enrolled strip makes and for the same reason: ADR-0083's rule is *a card
    names an act when the viewer can take it now **and a v1 surface can receive
    it***, and the seat claim that a suggestion's *take a seat* would open is
    ``Raketa02/Raketa#89``. A door that will not open is worse than the gap.

    **Emphasis is not set here.** It is at most one card on the *whole screen*
    and is therefore a property of the composed screen rather than of a shelf
    (ADR-0032, ADR-0037), so the pass that sets it runs above this one.
    """

    record = context.record
    where = Place(
        club_id=context.club.club_id,
        club_name=context.club.name,
        zone=context.club.zone,
        cover=context.club.cover,
        distance_km=None,
    )
    return MatchCard(
        match_id=context.match_id,
        stamp=stamp,
        where=where,
        price=context.share,
        situation=SituationHalf(
            # No viewer: a suggestion is a match she is **not** in, so every
            # viewer rung of the ladder is answered by her absence. Passing a
            # viewer that says *not seated, no offer, not on standby* would be
            # the same answer written twice.
            situation=situation(record, None, now),
            facts=SituationFacts(
                counts=counts_of(record, now=now),
                court_total=context.court_total,
                hold=hold_note(record, now=now),
                # A suggestion names **no court**, and that is reachability
                # rather than a rule of its own: ``kernel.court_named_at`` does
                # not assign one until fifteen minutes before play, and
                # eligibility stops at the join cutoff, which is at or before
                # the start. A club that publishes a zero-minute cutoff can put
                # a match inside the naming window on a shelf, and its card then
                # loses a line it could have printed rather than printing one it
                # could not — the direction a card should fail in.
                #
                # Everything else on ``SituationFacts`` is a fact a suggestion
                # cannot have: a cause needs a cancellation, a refund needs one
                # too, an owner's exposure needs a private court she bought, a
                # score needs a match that was played and a departure needs a
                # seat she held. Eligibility has excluded every one of those.
            ),
        ),
        clock=card_clock(record, now),
        fit=badge,
    )
