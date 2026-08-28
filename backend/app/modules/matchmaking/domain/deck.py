"""*Match me* — the deck's terminal stage, and the three exclusions before it.

Stages 1 to 6 are the shortlist's, unchanged (``shortlist.py``). What is here is
stage 7 for a surface that shows **one card at a time**, plus the three
exclusions that are the deck's alone.

**One deal, one ``search_id``, an ordered batch of at most ``DECK_DEAL_MAX``
cards.** One-at-a-time is how the deck is *shown*, not how it is computed: the
ordering policy is a property of a whole deal and cannot be evaluated one card at
a time, and per-card searches would make the deck the highest-volume writer in
the system for no analytic gain (``the-two-contracts.md`` §6).

**The deck has no mode.** It reads the viewer's own declared Play intent for that
sport — ``COMPETITIVE → comp``, ``FOR_FUN → fun``, **``NO_PREFERENCE → fun``** —
and there is never a third weight vector. :func:`mode_for_intent` is the whole of
that mapping, and the *declaration* is what the record keeps, never the vector it
mapped to, so a later change to the mapping does not rewrite history.

**Its variety is its order, and nothing in a deal moves on a fact about the other
cards** (``docs/adr/0126``). Three bands — people who already said yes, then the
candidates Liveness lifted, then the rest — and ``PASS_SUPPRESS``. §9.11's raised
λ is struck with the stage it belonged to: a card at a time makes order the whole
experience, which is the stronger case for a spread and still not strong enough
to buy a move nobody can be given a reason for.

**The relaxation ladder does not reach the deck** (``docs/adr/0099``): no rung
offers, no ladder in the pool description. Its own exclusions are here instead.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from enum import IntEnum
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import IntentRules
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1 import reverse_mode
from app.modules.matchmaking.domain.fence import searcher_of
from app.modules.matchmaking.domain.search_context import SearchContext
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.matchmaking.domain.searches import (
    InclusionReason,
    StagedCounts,
)
from app.modules.matchmaking.domain.shortlist import (
    Generated,
    Generation,
    Scored,
    generate,
    near_misses_of,
    score_all,
    with_liveness,
)

#: How long a dealt card is remembered, so that **a spent deal deals again**.
#:
#: A new deal is a new search with the same exclusions *plus everybody already
#: dealt* (``the-engine.md`` §10.3) — without which a second tap would deal the
#: same ten people, since the order is deterministic and nothing about them has
#: moved. The memory has to end somewhere, or a player who dealt through the city
#: once would never be dealt to again, and *exhausting a deal is not exhausting
#: the pool* would have become its opposite.
#:
#: **Domain, not configuration**, on the rule ``EXPOSURE_RETENTION_WEEKS`` is
#: written under: how long a fact survives decides what can be asked of it. One
#: day is the deck's own natural exhaustion as the engine document spells it —
#: *"You have seen everybody compatible today"* (``matchmaking-engine.md``
#: §9.5.1) — and it is a **rolling** window rather than a calendar day, because a
#: calendar day would reset in the middle of the evening the deck is for.
#:
#: It is deliberately **not** a ruleset row. The three numbers the deck's
#: decisions produced are ``PASS_SUPPRESS``, ``INTEREST_TTL`` and
#: ``OUTSTANDING_INTEREST_CAP``, all set by #194; this is not a fourth. It says
#: how long the deck's own short-term memory is, which is the shape of the
#: surface rather than a price the product is arguing about.
#:
#: Decided by ``docs/adr/0131``, which carries the argument, the falsifier — the
#: deepest position reached per deal, which ``DECK_DEAL_MAX`` already collects —
#: and the named owner. Any change to it lands as an ADR naming who moved it.
DEALT_MEMORY = timedelta(days=1)

#: What a declaration with **no opinion** inherits when there is nothing to
#: inherit from.
#:
#: A shortlist gives ``NO_PREFERENCE`` the searcher's own mode; the deck has no
#: such mode, so the mapping has to name one — and it names *for fun*
#: (``the-two-contracts.md`` §6). It is not a third vector and never becomes one:
#: indifference about the kind of evening is not a kind of evening.
INHERITED_ON_THE_DECK = SearchMode.FOR_FUN


def mode_for_intent(intent: PlayIntent, rules: IntentRules) -> SearchMode:
    """Which weight vector the deck scores under, for a viewer who declared this.

    **``NO_PREFERENCE`` never selects a weight vector, it inherits one**, and on
    the deck there is nothing to inherit from — no tab, no mode, no request field
    — so it takes *for fun*. That is the mapping
    ``the-two-contracts.md`` §6 fixes, and it is the same rule ``reverse_mode``
    applies to a candidate who declared it: indifference about the kind of evening
    is not a third kind of evening.

    The mapping reads ``IntentRules.same_evening`` rather than comparing two
    enums' spellings, exactly as ``reverse_mode`` does: ``PlayIntent`` and
    ``SearchMode`` are deliberately different types and a shared string is a
    coincidence the arithmetic must not lean on.
    """

    # The first argument is what a declaration with no opinion **inherits**, and
    # on the deck there is nothing to inherit *from* — no tab, no mode, no
    # request field — so it is named here rather than defaulted somewhere else.
    return reverse_mode(INHERITED_ON_THE_DECK, intent.value, rules)


@final
class DeckBand(IntEnum):
    """The deck's three bands, in the order they are dealt.

    An ``IntEnum`` because the sort key reads it directly and the *order* is the
    whole meaning — but named, because ``0``, ``1`` and ``2`` in a sort key are
    three magic numbers where the docstring above spells out three sentences.

    They are not a wire vocabulary and never become one. A band is not a reason:
    ``INTEREST_LIFT`` already crosses as the inclusion reason it is, and *you are
    second because Liveness moved you* is a statement about the ranking rather
    than about the person, which is exactly the kind of movement
    ``docs/adr/0126`` refuses to publish.
    """

    SAID_YES_TO_YOU = 0
    LIFTED = 1
    THE_REST = 2


@final
@dataclass(frozen=True, slots=True)
class DeckExclusions:
    """The three the deck adds to the gates, and whom they hold out of this deal.

    None of them is a gate: the roster is closed at ten and its histogram is
    compared across releases, and — more to the point — **a gate is a statement
    about the city and these are statements about one player's own deck**. A
    passed player is a full candidate in the shortlist, the line-up and a forecast,
    immediately (``docs/adr/0128``).

    ``suppressed`` is counted separately and recorded on the search row, because
    it is the only thing that tells *your own passes emptied your deck* apart from
    *the pool is empty* — a failure nobody can see from any screen, since no route
    returns a pass.

    **The deck's fourth exclusion is not here because it is already a gate.**
    ``the-engine.md`` §10.3 lists *already has an open game with you* beside the
    two above; it is ``GateCode.OPEN_CHALLENGE``, it binds every surface rather
    than this one, and it is counted in the gate histogram like the other nine.
    Named here so that its absence reads as *handled upstream* rather than as
    *dropped* — it is inert today, because ``matches`` does not exist and the
    read that feeds it stands down.
    """

    #: A **live** pass suppression, read from the cache that fails soft. An
    #: unreachable store answers *nobody*, which repeats a card and never empties
    #: a deal.
    suppressed: frozenset[UUID]
    #: People this player has already said *Let's play* to, for this sport. The
    #: yes lapses at ``INTEREST_TTL`` and they return to the deck — a fresh chance
    #: rather than a loop.
    already_asked: frozenset[UUID]
    #: People dealt to this player within :data:`DEALT_MEMORY`. **A spent deal
    #: deals again**, and this is what makes the second deal a different ten.
    already_dealt: frozenset[UUID]

    def holds_out(self, player_id: UUID) -> bool:
        return (
            player_id in self.suppressed
            or player_id in self.already_asked
            or player_id in self.already_dealt
        )

    def suppresses(self, player_id: UUID) -> bool:
        """Whether a **live pass** is one of the reasons this person is not dealt.

        *One of* rather than *the only one*, deliberately, and the alternative was
        tried and is worse. Counting only the removals suppression **alone**
        caused sounds more honest and makes the column read zero in the case it
        exists for: you pass on cards you were just dealt, so within
        :data:`DEALT_MEMORY` almost everybody suppressed is also *already dealt*,
        and the number that is supposed to say **your own passes emptied your
        deck** would answer nothing for the whole first day after a pass — while
        the suppression outlasts that memory by thirty times over.

        So the count is *how many people in range this player has a live
        suppression against*, and the overlap is named rather than netted out. It
        is read against ``players_in_range`` on the same row, which is what makes
        it answerable at all: a deal of nothing out of a pool of forty with
        thirty suppressed is a different sentence from the same deal with none.
        """

        return player_id in self.suppressed


@final
@dataclass(frozen=True, slots=True)
class DealtCard:
    """One card, and whether it is a **re-show**.

    ``suppression_lapsed`` reads the durable pass record and never the cache: a
    lapsed suppression leaves no trace the pair was ever passed, which is the
    exact fact a TTL destroys and the whole reason the record is durable
    (``search-telemetry.md`` §6). Without it only plain pass rate is computable,
    never *pass rate on re-shown profiles* — the only falsifier ``PASS_SUPPRESS``
    has.
    """

    scored: Scored
    suppression_lapsed: bool


@final
@dataclass(frozen=True, slots=True)
class Deal:
    """One deal: the cards, the counters, and what never leaves the building."""

    cards: tuple[DealtCard, ...]
    #: Layer 3, exactly as the shortlist's is. **Engine-internal**, and no route
    #: returns it.
    near_misses: tuple[Scored, ...]
    counts: StagedCounts
    best_withheld_fit: float | None
    #: The **post-gate** pool, before the deck's own exclusions. A number about
    #: the city has to be true about the city (``docs/adr/0099``), and *my own
    #: passes* is not a fact about the city.
    players_in_range: int
    #: How many candidates a **live** suppression removed from this deal.
    n_excluded_by_suppression: int


def deal(
    context: SearchContext,
    engine: MatchFit,
    *,
    exclusions: DeckExclusions,
    re_shows: frozenset[UUID],
) -> Deal:
    """The whole deck pipeline, from a bound snapshot to an ordered batch.

    ``re_shows`` is derived from the **durable pass record alone** — a pass whose
    window has run out, by its own date against the released ``PASS_SUPPRESS``.
    Deliberately not *whoever the suppression cache no longer holds*: that cache
    **fails soft**, so during an outage a live-suppressed player is dealt, and a
    flag read from the cache would call them a re-show they are not — corrupting
    *pass rate on re-shown profiles* at exactly the moment extra re-shows are
    happening. The record does not fail soft, and the flag is computed from it.
    """

    generation = generate(context)
    dealable = tuple(
        candidate
        for candidate in generation.admitted
        if not exclusions.holds_out(candidate.player_uuid)
    )
    scored = score_all(_only(generation, dealable), context, engine)
    admitted = tuple(row for row in scored if row.admission.admitted)
    withheld = tuple(row for row in scored if not row.admission.admitted)
    ordered = _in_bands(admitted, context, engine)[
        : context.ruleset.shape.deck_deal_max
    ]
    near_misses = near_misses_of(withheld, context)
    return Deal(
        cards=tuple(
            DealtCard(
                scored=row,
                suppression_lapsed=row.generated.player_uuid in re_shows,
            )
            for row in ordered
        ),
        near_misses=near_misses,
        counts=StagedCounts(
            n_generated=generation.n_generated,
            excluded_by_gate=generation.excluded_by_gate,
            n_scored=len(scored),
            n_cleared_floor=len(admitted),
            n_returned=len(ordered),
            n_near_miss_recorded=len(near_misses),
        ),
        best_withheld_fit=(
            max(row.modified.points for row in withheld) if withheld else None
        ),
        players_in_range=len(generation.admitted),
        n_excluded_by_suppression=sum(
            1
            for candidate in generation.admitted
            if exclusions.suppresses(candidate.player_uuid)
        ),
    )


def _only(
    generation: Generation, dealable: tuple[Generated, ...]
) -> Generation:
    """The same generation, over the candidates this deal may deal.

    The counters are kept as generation produced them: ``n_generated`` and the
    gate histogram are facts about the **city**, and subtracting one player's own
    deck exclusions from them would make two searches run a minute apart in the
    same city disagree about how many people are in it.
    """

    return replace(generation, admitted=dealable)


def _in_bands(
    admitted: tuple[Scored, ...], context: SearchContext, engine: MatchFit
) -> tuple[Scored, ...]:
    """Stage 6, then the deck's own terminal order. **Three bands, then rank.**

    1. **People who have already said yes to you** — an instant match is one tap
       away, and this is also the only band that can hold somebody the quality
       floor refused, because an interest lift is the one lift that admits.
    2. **The candidates Liveness lifted, high enough to owe an explanation** —
       ``offset >= MOVE_NOTICE``. *High* needs a line somewhere, and this is the
       one the platform already draws: ``docs/adr/0123`` budgets silent movement
       at exactly the point a move starts owing a printed reason, so a card in
       this band is one the searcher could be told *why* about. Read as *the
       offset moved them up at all*, the band would swallow most of band three
       and stop being a band — and any other line would be a new constant to
       argue over, in a design whose numbers are all set.
    3. **The rest.**

    Within a band the order is the shortlist's own — ``rank_key`` descending,
    then Fit, then the player id — so it is total, and **a set is never the
    source of an order** (``docs/adr/0105``). Nothing here reads a fact about
    another card: a card's band and its key are both properties of that one
    person, which is the rule that struck the diversity stage
    (``docs/adr/0126``).
    """

    searcher = searcher_of(context)
    moved = tuple(with_liveness(row, context, engine, searcher) for row in admitted)
    return tuple(
        sorted(
            moved,
            key=lambda row: (
                _band(row),
                -(row.rank_key or 0.0),
                -row.modified.points,
                row.player_id,
            ),
        )
    )


def _band(row: Scored) -> DeckBand:
    """Which of the three this card sits in. **A fact about this person alone.**"""

    if row.inclusion_reason is InclusionReason.INTEREST_LIFT:
        return DeckBand.SAID_YES_TO_YOU
    if (
        row.liveness is not None
        and row.liveness.offset >= row.liveness.rules.move_notice
    ):
        return DeckBand.LIFTED
    return DeckBand.THE_REST
