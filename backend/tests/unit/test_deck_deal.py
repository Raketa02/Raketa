"""The deck's terminal stage: the ruler, the two bands, the four exclusions, the
two counts.

At the **pure** seam — a bound ``SearchContext`` in, an ordered batch out, no
I/O. What is asserted here is everything the deck decides that a shortlist does
not, and one property the whole surface rests on: **nothing in a deal moves on a
fact about the other cards** (``docs/adr/0126``).
"""

from __future__ import annotations

from datetime import timedelta

from app.engines.matchfit.core import DegradedReason, SearchMode, Term
from app.engines.matchfit.v1 import MatchFitV1
from app.kernel import instant
from app.modules.matchmaking.domain.deck import (
    INHERITED_ON_THE_DECK,
    DeckExclusions,
    cooling_off,
    deal,
    mode_for_intent,
)
from app.modules.matchmaking.domain.ports import SharedCourt
from app.modules.matchmaking.domain.searches import InclusionReason, SearchSurface
from app.modules.matchmaking.domain.shortlist import run
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.play_intent import PlayIntent
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()

NOTHING = DeckExclusions(
    suppressed=frozenset(),
    already_asked=frozenset(),
    already_dealt=frozenset(),
    cooling_off=frozenset(),
)


def holding_out(**named) -> DeckExclusions:
    """``NOTHING`` with the named sets filled in."""

    return DeckExclusions(
        **{
            field: frozenset(named.get(field, ()))
            for field in ("suppressed", "already_asked", "already_dealt", "cooling_off")
        }
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
# The ruler, and the mapping that outlived the deck
# ---------------------------------------------------------------------------


def test_the_deck_has_one_ruler_and_it_is_the_fun_one():
    """**Everyone → fun** (``docs/adr/0169`` §2). The deck is a discovery
    surface, and the ruler is a fact about the surface rather than a function of
    anything the viewer declared — which is why it is a constant here and the
    use case reads no declaration to pick it."""

    assert INHERITED_ON_THE_DECK is SearchMode.FOR_FUN


def test_a_court_born_without_a_mode_still_resolves_one_from_a_declaration():
    """``COMPETITIVE → comp``, ``FOR_FUN → fun``, **``NO_PREFERENCE → fun``**.

    The mapping used to be the deck's and no longer is; it lives on for the fill
    and the card of a court born without a mode (``docs/adr/0150`` §5), and it
    still selects no third vector: indifference about the kind of evening is not
    a third kind of evening.
    """

    rules = LIVE_RULESET.intent

    assert mode_for_intent(PlayIntent.COMPETITIVE, rules) is SearchMode.COMPETITIVE
    assert mode_for_intent(PlayIntent.FOR_FUN, rules) is SearchMode.FOR_FUN
    assert mode_for_intent(PlayIntent.NO_PREFERENCE, rules) is SearchMode.FOR_FUN


# ---------------------------------------------------------------------------
# The intent term stands down on every card
# ---------------------------------------------------------------------------


def test_the_intent_term_stands_down_on_every_card_of_a_deal_and_reads_on_a_shortlist():
    """``docs/adr/0169`` §2: stood down for every pairing when the surface is the
    deck, under a code that is neither side's gap, and its weight renormalises
    away. A shortlist over the same people still reads it."""

    rows = (
        build.row(1, declared_intent="COMPETITIVE"),
        build.row(2, declared_intent="FOR_FUN"),
    )

    dealt = a_deal(rows)
    listed = run(build.context(rows), ENGINE)

    assert len(dealt.cards) == 2
    for card in dealt.cards:
        fit = card.scored.fit
        assert Term.INTENT_ALIGNMENT not in {term.term for term in fit.terms}
        assert {
            stood.term: stood.reason for stood in fit.degraded_terms
        }[Term.INTENT_ALIGNMENT] is DegradedReason.NOT_READ_ON_THIS_SURFACE
        assert sum(term.weight for term in fit.terms) > 99.999
        assert Term.INTENT_ALIGNMENT.value not in card.scored.missing_terms, (
            "a term the surface declined to ask is not this person's gap"
        )
    for row in listed.returned:
        assert Term.INTENT_ALIGNMENT in {term.term for term in row.fit.terms}


def test_a_declaration_moves_nobody_on_the_deck_up_or_down():
    """Two people who differ only in what they declared come to one number and
    one place: the opposite declaration no longer reads the table's zero, and
    silence no longer buys the renormalisation for free."""

    rows = tuple(
        build.row(number, declared_intent=declared)
        for number, declared in enumerate(
            ("COMPETITIVE", "FOR_FUN", "NO_PREFERENCE", None), start=1
        )
    )

    dealt = a_deal(rows)

    points = {
        card.scored.player_id: card.scored.modified.points for card in dealt.cards
    }
    assert len({round(value, 9) for value in points.values()}) == 1, points
    assert dealt_ids(dealt) == [str(build.player(n)) for n in (1, 2, 3, 4)], (
        "identical people deal in id order, the tie-break that is a fact"
    )


# ---------------------------------------------------------------------------
# The two bands
# ---------------------------------------------------------------------------


def test_somebody_who_said_yes_sorts_among_the_lifted_by_rank_key():
    """**Two bands, not three** (``docs/adr/0169`` §4). The person who said yes
    is unmarked and lands where the nudge puts them: among the lifted, by rank
    key — early, because their ``+14`` is the largest lift there is, and never
    first by rule.

    Here a better-fitting person Liveness lifted for another reason outranks the
    liker on rank key, and is dealt before them; the liker still comes before
    everybody the engine did not lift at all.
    """

    lifted_by_exposure = build.row(1)
    said_yes = build.row(2, mu=build.SEARCHER_MU + 0.30)
    stiller_but_better = build.row(3)

    dealt = a_deal(
        (lifted_by_exposure, said_yes, stiller_but_better),
        interest_days_ago={build.player(2): 3},
        # Shown to nobody all week clears the notice threshold on its own; the
        # third person is merely ordinary and sits in the second band.
        times_shown={build.player(1): 0, build.player(2): 5, build.player(3): 5},
        busy_threshold=20,
    )

    by_id = {card.scored.player_id: card.scored for card in dealt.cards}
    liker = by_id[str(build.player(2))]
    other = by_id[str(build.player(1))]
    assert liker.inclusion_reason is InclusionReason.INTEREST_LIFT
    assert other.rank_key > liker.rank_key, (
        "the case this asserts: the liker is *not* first when a lifted person "
        "out-keys them"
    )
    assert dealt_ids(dealt) == [
        str(build.player(1)),
        str(build.player(2)),
        str(build.player(3)),
    ]


def test_somebody_who_said_yes_is_still_admitted_below_the_floor():
    """The admission stands with the band gone: a human's yes still outranks the
    engine's floor, and the liker is dealt — among the lifted — however poor the
    pairing reads."""

    # Inside the level gate and under the floor: a Level apart, no tags, one
    # ticked cell the searcher never ticks.
    poor = build.row(1, mu=build.SEARCHER_MU + 0.4, tags=(), slots=("2:MORNING",))

    alone = a_deal((poor,))
    said_yes = a_deal((poor,), interest_days_ago={build.player(1): 2})

    assert alone.cards == () and alone.counts.n_scored == 1, (
        "the pairing is scored, and under the floor on its own"
    )
    assert dealt_ids(said_yes) == [str(build.player(1))]
    assert said_yes.remaining == 0


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
        a_deal(rows, exclusions=holding_out(suppressed={build.player(2)}))
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
# The four exclusions
# ---------------------------------------------------------------------------


def test_a_live_suppression_holds_a_card_out_and_is_counted():
    """The count is the only thing that tells *my own passes emptied this* apart
    from *the pool is empty* — and nobody can see it from any screen."""

    rows = (build.row(1), build.row(2))

    dealt = a_deal(rows, exclusions=holding_out(suppressed={build.player(1)}))

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
        exclusions=holding_out(
            suppressed={build.player(1), build.player(2)},
            already_asked={build.player(2)},
            already_dealt={build.player(2)},
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
        exclusions=holding_out(
            already_asked={build.player(1)}, already_dealt={build.player(2)}
        ),
    )

    assert dealt_ids(dealt) == [str(build.player(3))]
    assert dealt.n_excluded_by_suppression == 0


def test_the_cool_off_holds_a_card_out_and_is_not_counted_as_a_suppression():
    """The fourth exclusion (``docs/adr/0169`` §6). Deck only, and neither a
    gate nor a pass: it is not in the gate histogram and not in the suppression
    count, because it is neither a fact about the city nor a thing the viewer
    did to their own deck."""

    rows = (build.row(1), build.row(2))

    dealt = a_deal(rows, exclusions=holding_out(cooling_off={build.player(1)}))

    assert dealt_ids(dealt) == [str(build.player(2))]
    assert dealt.n_excluded_by_suppression == 0
    assert dealt.players_in_range == 2


# ---------------------------------------------------------------------------
# Who is cooling off — the rule over the courts
# ---------------------------------------------------------------------------

COOL_OFF_DAYS = LIVE_RULESET.interest.deck_cool_off_days


def _court(number: int, *, behind_for: timedelta | None) -> SharedCourt:
    return SharedCourt(
        counterpart_id=build.player(number),
        behind_since=None if behind_for is None else instant(build.NOW - behind_for),
    )


def test_a_court_ahead_and_a_court_lately_behind_cool_off_and_an_old_one_does_not():
    """*Somebody you are already with is not in your deck, and stays out for
    thirty days after* (``docs/adr/0169`` §6).

    Ahead — planned, on, awaiting its entry — is in for as long as it stands.
    Behind — played, called off, never played — is in for the window from the
    moment it went behind them, and out on the day the window closes: the
    thirtieth day is the first day back.
    """

    courts = (
        _court(1, behind_for=None),
        _court(2, behind_for=timedelta(days=COOL_OFF_DAYS - 1, hours=23)),
        _court(3, behind_for=timedelta(days=COOL_OFF_DAYS)),
        _court(4, behind_for=timedelta(days=90)),
    )

    assert cooling_off(courts, now=build.NOW, days=COOL_OFF_DAYS) == frozenset(
        {build.player(1), build.player(2)}
    )


def test_the_cool_off_is_thirty_days_and_equals_the_pass_window_today():
    """A ruleset constant of its own, deliberately equal to ``PASS_SUPPRESS``
    today and free to part from it (``docs/adr/0169`` §6)."""

    assert COOL_OFF_DAYS == 30
    assert COOL_OFF_DAYS == LIVE_RULESET.interest.pass_suppress_days


def test_a_window_of_nought_days_cools_off_only_the_courts_still_ahead():
    """What the released rulesets that never knew the number say: no window after
    a court, and a live court is still not somebody the deck deals."""

    courts = (_court(1, behind_for=None), _court(2, behind_for=timedelta(hours=1)))

    assert cooling_off(courts, now=build.NOW, days=0) == frozenset({build.player(1)})


# ---------------------------------------------------------------------------
# The two counts on the envelope
# ---------------------------------------------------------------------------


def test_remaining_is_the_eligible_beyond_the_hand_and_drops_as_hands_are_dealt():
    """``pool.remaining`` (``docs/adr/0169`` §5): the people eligible after
    every deck exclusion who are not in this hand — so a counter can say *N
    left* and be true of the whole pool rather than of ten."""

    rows = tuple(build.row(n) for n in range(1, 15))

    first = a_deal(rows)
    second = a_deal(
        rows,
        exclusions=holding_out(already_dealt={build.player(n) for n in range(1, 11)}),
    )

    assert len(first.cards) == 10 and first.remaining == 4
    assert len(second.cards) == 4 and second.remaining == 0


def test_remaining_counts_neither_the_held_out_nor_the_withheld():
    """Eligible means *would be dealt*: somebody a live pass holds out is not
    waiting beyond the hand, and neither is somebody under the floor."""

    rows = (build.row(1), build.row(2), build.row(3, mu=build.SEARCHER_MU + 1.2))

    dealt = a_deal(rows, exclusions=holding_out(suppressed={build.player(2)}))

    assert dealt_ids(dealt) == [str(build.player(1))]
    assert dealt.remaining == 0


def test_want_to_play_you_counts_the_yeses_that_would_be_dealt_and_ignores_the_memory():
    """``pool.want_to_play_you`` (``docs/adr/0169`` §4), as a list of exclusions.

    Counted: a live yes from somebody who passes every gate, is not passed on
    within the window, is not cooling off and is not already mutual — **whether
    or not they were dealt this morning**, because somebody dealt and unanswered
    is still waiting. Not counted: a yes from somebody a gate holds out, a live
    suppression holds out, the cool-off holds out, or the viewer has already
    said yes back to.
    """

    rows = tuple(build.row(n) for n in range(1, 8))
    yeses = {build.player(n): 2 for n in range(1, 8)}

    dealt = a_deal(
        rows,
        interest_days_ago=yeses,
        blocked=frozenset({str(build.player(2))}),
        exclusions=holding_out(
            suppressed={build.player(3)},
            already_asked={build.player(4)},
            cooling_off={build.player(5)},
            already_dealt={build.player(6)},
        ),
    )

    # 1 and 7 are dealt; 6 was dealt this morning and is still waiting.
    assert dealt_ids(dealt) == [str(build.player(1)), str(build.player(7))]
    assert dealt.want_to_play_you == 3


def test_want_to_play_you_is_nought_when_nobody_is_waiting():
    dealt = a_deal((build.row(1), build.row(2)))

    assert dealt.want_to_play_you == 0
    assert dealt.remaining == 0


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
