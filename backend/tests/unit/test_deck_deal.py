"""The deck's terminal stage: the mapping, the three bands, the three exclusions.

At the **pure** seam — a bound ``SearchContext`` in, an ordered batch out, no
I/O. What is asserted here is everything the deck decides that a shortlist does
not, and one property the whole surface rests on: **nothing in a deal moves on a
fact about the other cards** (``docs/adr/0126``).
"""

from __future__ import annotations

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.domain.deck import (
    DeckExclusions,
    deal,
    mode_for_intent,
)
from app.modules.matchmaking.domain.searches import SearchSurface
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.play_intent import PlayIntent
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()

NOTHING = DeckExclusions(
    suppressed=frozenset(), already_asked=frozenset(), already_dealt=frozenset()
)


def a_deal(rows, *, exclusions=NOTHING, re_shows=frozenset(), **context):
    return deal(
        build.context(rows, surface=SearchSurface.DECK, **context),
        ENGINE,
        exclusions=exclusions,
        re_shows=re_shows,
    )


def dealt_ids(dealt):
    return [card.scored.player_id for card in dealt.cards]


# ---------------------------------------------------------------------------
# The mapping
# ---------------------------------------------------------------------------


def test_the_deck_reads_a_declaration_and_never_selects_a_third_vector():
    """``COMPETITIVE → comp``, ``FOR_FUN → fun``, **``NO_PREFERENCE → fun``**.

    Indifference about the kind of evening is not a third kind of evening, which
    is why ``SearchMode`` has two values where a declaration has three — and why
    a player with no preference gets a working deck rather than a refusal.
    """

    rules = LIVE_RULESET.intent

    assert mode_for_intent(PlayIntent.COMPETITIVE, rules) is SearchMode.COMPETITIVE
    assert mode_for_intent(PlayIntent.FOR_FUN, rules) is SearchMode.FOR_FUN
    assert mode_for_intent(PlayIntent.NO_PREFERENCE, rules) is SearchMode.FOR_FUN


# ---------------------------------------------------------------------------
# The three bands
# ---------------------------------------------------------------------------


def test_somebody_who_said_yes_is_dealt_first_whatever_their_fit():
    """Band one, and it is the band that makes the deck a product loop.

    An instant match is one tap away, so a yes outranks a better Fit — which is
    the same lift the shortlist prints, applied here as an *order* rather than as
    a place in a list.
    """

    strong = build.row(1)
    said_yes = build.row(2, mu=build.SEARCHER_MU + 0.15)

    dealt = a_deal(
        (strong, said_yes),
        interest_days_ago={build.player(2): 3},
    )

    assert dealt_ids(dealt)[0] == str(build.player(2))
    assert len(dealt.cards) == 2, "the lift orders the deck, it does not shorten it"


def test_a_lifted_candidate_is_dealt_above_a_better_fit_who_was_not():
    """Band two above band three, and the bands are **strict**.

    *High liveness* is read as *the offset moved them up* — the one reading that
    needs no new constant and no threshold to argue about — and the band beats
    the arithmetic: a lift of eight does not merely add eight, it puts that card
    in front of a stiller one whose Fit is higher by more.
    """

    lifted = build.row(1, mu=build.SEARCHER_MU + 0.22)
    docked = build.row(2)

    dealt = a_deal(
        (lifted, docked),
        # Shown to nobody all week, which is the lift that clears the notice
        # threshold; and an inbox full enough to move the other one **down**,
        # which is what makes this two bands rather than two numbers.
        times_shown={build.player(1): 0, build.player(2): 5},
        open_challenge_counts={build.player(2): 8},
        busy_threshold=20,
    )

    by_id = {card.scored.player_id: card.scored for card in dealt.cards}
    up, down = by_id[str(build.player(1))], by_id[str(build.player(2))]
    notice = up.liveness.rules.move_notice
    assert up.liveness.offset >= notice > down.liveness.offset, (
        "the band is *high* liveness at the platform's own notice threshold, "
        "not merely *any* lift"
    )
    assert down.rank_key > up.rank_key, (
        "the shortlist's own key would deal them the other way round, which is "
        "the whole of what this asserts: the band decides, not the arithmetic"
    )
    assert dealt_ids(dealt)[0] == str(build.player(1))


def test_a_card_never_moves_on_a_fact_about_the_other_cards():
    """The rule that struck the diversity stage, asserted over a deal.

    Removing one person from the pool changes who is dealt and never the
    **relative order** of everybody else — because a card's band and its key are
    both properties of that one person.
    """

    rows = tuple(build.row(n, mu=build.SEARCHER_MU + n * 0.01) for n in range(1, 5))

    whole = dealt_ids(a_deal(rows))
    without_one = dealt_ids(
        a_deal(rows, exclusions=DeckExclusions(
            suppressed=frozenset({build.player(2)}),
            already_asked=frozenset(),
            already_dealt=frozenset(),
        ))
    )

    assert [one for one in whole if one != str(build.player(2))] == without_one


def test_a_deal_stops_at_the_cap():
    """``DECK_DEAL_MAX`` is a cap and never a target.

    A deal is scored once and its liveness ages as the player taps through, so a
    deal of forty is stale by the bottom and writes forty rows nobody looks at.
    """

    rows = tuple(build.row(n) for n in range(1, 15))

    dealt = a_deal(rows)

    assert len(dealt.cards) == LIVE_RULESET.shape.deck_deal_max


# ---------------------------------------------------------------------------
# The three exclusions
# ---------------------------------------------------------------------------


def test_a_live_suppression_holds_a_card_out_and_is_counted():
    """The count is the only thing that tells *my own passes emptied this* apart
    from *the pool is empty* — and nobody can see it from any screen."""

    rows = (build.row(1), build.row(2))

    dealt = a_deal(
        rows,
        exclusions=DeckExclusions(
            suppressed=frozenset({build.player(1)}),
            already_asked=frozenset(),
            already_dealt=frozenset(),
        ),
    )

    assert dealt_ids(dealt) == [str(build.player(2))]
    assert dealt.n_excluded_by_suppression == 1
    assert dealt.players_in_range == 2, (
        "the pool is a fact about the city, and my own passes are not"
    )


def test_the_count_counts_an_overlapping_exclusion_too():
    """Somebody both suppressed **and** already dealt still counts as suppressed.

    Netting the overlap out sounds more honest and is worse: you pass on cards
    you were just dealt, so within `DEALT_MEMORY` nearly everybody suppressed is
    also already dealt — and the number that exists to say *your own passes
    emptied your deck* would read zero for the whole first day after a pass,
    while the suppression outlasts that memory by thirty times over.
    """

    rows = (build.row(1), build.row(2), build.row(3))

    dealt = a_deal(
        rows,
        exclusions=DeckExclusions(
            suppressed=frozenset({build.player(1), build.player(2)}),
            already_asked=frozenset({build.player(2)}),
            already_dealt=frozenset({build.player(2)}),
        ),
    )

    assert dealt_ids(dealt) == [str(build.player(3))]
    assert dealt.n_excluded_by_suppression == 2


def test_already_asked_and_already_dealt_are_held_out_too():
    """The deck's other two exclusions. Neither is a gate, and neither is
    counted: a gate is a statement about the city, and these are statements about
    one player's own deck."""

    rows = (build.row(1), build.row(2), build.row(3))

    dealt = a_deal(
        rows,
        exclusions=DeckExclusions(
            suppressed=frozenset(),
            already_asked=frozenset({build.player(1)}),
            already_dealt=frozenset({build.player(2)}),
        ),
    )

    assert dealt_ids(dealt) == [str(build.player(3))]
    assert dealt.n_excluded_by_suppression == 0


def test_a_re_show_is_flagged_from_the_durable_record():
    """``suppression_lapsed`` is what makes *pass rate on re-shown profiles*
    computable, and it reads the row rather than the cache — a lapsed key leaves
    no trace the pair was ever passed."""

    rows = (build.row(1), build.row(2))

    dealt = a_deal(rows, re_shows=frozenset({build.player(1)}))

    by_id = {card.scored.player_id: card.suppression_lapsed for card in dealt.cards}
    assert by_id[str(build.player(1))] is True
    assert by_id[str(build.player(2))] is False


def test_a_suppression_outage_repeats_a_card_and_calls_it_no_re_show():
    """The failure the flag is computed from the **record** to avoid.

    A soft-failing cache answers *nobody is suppressed*, so a live-suppressed
    player is dealt — that is the trade, and it is the right way round. What must
    not follow is calling that card a re-show: the falsifier would then be
    corrupted at exactly the moment extra re-shows are happening. Nothing about
    ``re_shows`` comes from the cache, so the outage below changes one thing and
    not two.
    """

    rows = (build.row(1),)

    dealt = a_deal(rows, exclusions=NOTHING, re_shows=frozenset())

    assert dealt_ids(dealt) == [str(build.player(1))], "the outage emptied the deck"
    assert dealt.cards[0].suppression_lapsed is False
    assert dealt.n_excluded_by_suppression == 0


def test_an_empty_deal_is_an_answer():
    """A deal that came back with nothing is recorded exactly like any other, and
    the pool it came from is described either way."""

    dealt = a_deal(())

    assert dealt.cards == ()
    assert dealt.players_in_range == 0
    assert dealt.n_excluded_by_suppression == 0
    assert dealt.best_withheld_fit is None
