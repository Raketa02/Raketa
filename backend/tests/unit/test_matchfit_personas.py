"""Golden personas — the suite that is **meant** to break on a constant retune.

The opposite file to ``test_matchfit_invariants.py``. Every number here is read off
the current constants, so a retune turns these red and nothing else does. That is
what makes them a tripwire rather than a nuisance: a reviewer who changes a weight
and sees a dozen personas move has been told exactly what they changed.

Each one is a sentence a player could be shown, and the arithmetic behind it is
written out in the docstring so that a diff on a number is a diff on an argument.

**The headline regression is closed here**, and the persona that reported it as open
is the one that says so. An empty court that is counted, cheap and nearby scored 100
against the well-formed four's 94 for as long as every term in the table was either a
constraint it trivially satisfied or evidence missing for both. **Match viability**
is neither: it is evidence and it is *always computable*, because every match has a
phase, a court hold, a seat count and a cutoff. The empty court now scores 88 against
95, and at a saturated club with no court held, 76. Skill overlap and predicted
balance (#86) widen the gap further; they do not create it.
"""

from dataclasses import replace

import pytest

from app.engines.fit import ScoredTerm, TermCode
from app.engines.matchfit.v1 import CONSTANTS, MatchFitEngineV1
from app.engines.matchmaking import (
    CourtHold,
    LadderQualification,
    MatchSnapshot,
    MatchTypePreference,
    PlayerProfile,
    PlayerRef,
    PlayHistory,
    Weekday,
)
from app.kernel import CardAllowance, Ratio, grosze, minutes, ratio, shifted
from tests.unit.matchmaking_snapshots import (
    COURT,
    NOW,
    analysis,
    doubles,
    money,
    profile,
    skill,
    starting,
    window,
    with_records,
)

ENGINE = MatchFitEngineV1()

ADA = skill("ada", 300, 20)
BO = skill("bo", 315, 25)
CY = skill("cy", 285, 30)
DEE = skill("dee", 330, 60)

#: The four seats of a padel court at 86 zł: **21,50 each**, which is ADR-0023's own
#: worked example. Every price persona below is a comparison against this figure, so
#: a change to the rounding order shows up here as a changed ceiling rather than as a
#: changed term value.
SEAT = 2150


def scored(
    snapshot: MatchSnapshot, declaration: PlayerProfile = PlayerProfile()
) -> tuple[int, int]:
    """The two numbers a persona is about: the fit and the coverage."""

    result = ENGINE.score(
        snapshot=snapshot, profile=declaration, analysis=analysis(), now=NOW
    )
    return result.fit, result.coverage


def term(snapshot: MatchSnapshot, declaration: PlayerProfile, code: TermCode):
    result = ENGINE.score(
        snapshot=snapshot, profile=declaration, analysis=analysis(), now=NOW
    )
    return next(item for item in result.terms if item.code is code)


def warning_of(snapshot: MatchSnapshot, declaration: PlayerProfile) -> str | None:
    result = ENGINE.score(
        snapshot=snapshot, profile=declaration, analysis=analysis(), now=NOW
    )
    return None if result.warning is None else result.warning.code.value


def test_the_seat_share_the_price_personas_are_written_against():
    """The money kernel's arithmetic, not this file's, and asserted as such.

    96 zł at a 10% off-peak rate compounds to 86,40, rounds **once** to 86 zł at the
    court, and only then divides into four seats of exactly 21,50. Dividing first
    would give 21,60, and every ceiling below would be half a złoty out.
    """

    share, payable = money(4)
    assert (int(COURT), share, payable) == (8600, SEAT, SEAT)


def test_a_player_who_declared_nothing_scores_a_hundred_at_seventy_seven_per_cent():
    """**The honest launch state — and the 100 is now saying something.**

    Five constraint terms with nothing declared to hold against any of them: time 12,
    travel 8, ladder 6, price 6, match type 4, all at full marks. Beside them the
    evidence term that always runs: this match is four seats paid with the court
    booked, so viability's 12 are full marks too and the fit is 100 out of 48.

        (12 + 12 + 8 + 6 + 6 + 4) / 48 = 100%,  coverage 48 / 62 = 77%

    The difference this makes is worth reading. Before viability, a fit of 100 meant
    *nothing is known to be wrong with this match* and an empty court earned it as
    easily as a full one. It now takes a match that is actually going to be played,
    and the two silences left — reliability and familiarity — are what the remaining
    23% of coverage is.
    """

    assert scored(doubles(ADA, BO, CY, DEE)) == (100, 77)


def test_the_canonical_well_formed_match_scores_ninety_five_at_full_coverage():
    """Every term running, and the two dark ones lit for the only time they can be.

    Bo turns up 95% of the time, Cy 80%, Dee always; the group scores its **least
    reliable** member, 0,80. Ada has played Bo recently and not Cy or Dee, so two of
    three faces are new: 2/3. Everything declared is satisfied, the declared Tuesday
    evening included — the match starts at 18:30 in Warsaw — and the match is full
    with its court booked, so viability is at full marks.

        (12 + 12 + 11 × 0,80 + 8 + 6 + 6 + 4 + 3 × 2/3) / 62 = 58,8 / 62 = 94,8%

    Rounded half away from zero: **95**, at 100% coverage — the only shape in this
    suite where every term in the table actually ran.
    """

    lit = replace(
        with_records(doubles(ADA, BO, CY, DEE), None, 95, 80, 100),
        history=PlayHistory(played_recently=frozenset({PlayerRef("bo")})),
    )
    declaration = profile(
        ceiling=2500,
        radius=20,
        match_type=MatchTypePreference.COMPETITIVE,
        days=frozenset({Weekday.TUESDAY, Weekday.THURSDAY}),
        hours=(window(18, 22),),
    )
    assert scored(lit, declaration) == (95, 100)
    assert term(lit, declaration, TermCode.GROUP_RELIABILITY).value == ratio(4, 5)
    assert term(lit, declaration, TermCode.FAMILIARITY).value == ratio(2, 3)


def test_the_empty_court_no_longer_outranks_the_well_formed_match():
    """**The regression this spec exists to close, closed.**

    A court nobody has joined, counted, 3 minutes away, at a time the player said
    they can play and 11,50 after a club card. Every constraint it meets is satisfied
    — and until this term landed that was the whole score, so it came back at **100
    against the well-formed four's 94** and the home list was topped by matches
    nobody had joined.

    Viability is what it cannot satisfy. Nobody has paid for a seat, so the whole of
    the people half is a hope rather than a commitment — and a seat that might still
    fill is worth half of one that has, however much time is left:

        viability = (0 + 1 × 0,50) × 1 = 0,50
        fit       = (12 + 12 × 0,50 + 8 + 6 + 6 + 4) / 48 = 42 / 48 = 87,5% → 88

    **88 at 77% coverage, against the well-formed match's 95 at 100%.** The ordering
    is the right way round and both halves of the pair say why: a lower fit *and*
    less of it measured.

    This is the empty match at its most flattering, deliberately — the court is
    booked and the club is only half busy, which is the best an empty match can
    possibly look. The persona a saturated club with no court gets is below, at 76.
    #86 widens the gap further: skill overlap and predicted balance are excluded here
    for want of anybody to overlap with, and scored for the four.
    """

    empty = doubles(
        None,
        None,
        None,
        None,
        viewer=ADA,
        travel_minutes=3,
        card=CardAllowance(amount=grosze(1000)),
    )
    declaration = profile(
        ceiling=2500,
        radius=20,
        match_type=MatchTypePreference.COMPETITIVE,
        days=frozenset({Weekday.TUESDAY, Weekday.THURSDAY}),
        hours=(window(18, 22),),
    )
    lit = replace(
        with_records(doubles(ADA, BO, CY, DEE), None, 95, 80, 100),
        history=PlayHistory(played_recently=frozenset({PlayerRef("bo")})),
    )

    assert term(empty, declaration, TermCode.MATCH_VIABILITY).value == ratio(1, 2)
    assert scored(empty, declaration) == (88, 77)
    assert scored(lit, declaration) == (95, 100)
    assert scored(empty, declaration)[0] < scored(lit, declaration)[0]


def test_an_empty_court_at_a_saturated_club_with_no_court_held():
    """**The worst a match can be**, and it is scored rather than hidden.

    Nobody has paid, no court is held, and the club has nine tenths of its capacity
    already committed at this hour. Both halves of the probability are near the
    floor and they multiply:

        people = 0 + 1 × 0,50 = 0,50
        court  = 0 + 1 × (1 − 0,90) = 0,10
        viability = 0,05,  fit = (12 + 12 × 0,05 + 8 + 6 + 6 + 4) / 48 = 76,25% → 76

    It still scores, because *nothing is ever excluded on a condition*: a player who
    wants to start a match at that club can see this one and take a chance on it.
    What it cannot do any more is outrank a match that is actually going to happen.
    """

    hopeless = doubles(
        None, None, None, None, viewer=ADA, hold=CourtHold.NONE, crowding=90
    )
    assert term(hopeless, profile(), TermCode.MATCH_VIABILITY).value == ratio(1, 20)
    assert scored(hopeless) == (76, 77)


def test_three_quarters_paid_with_a_court_booked_at_the_same_saturated_club():
    """The comparison the persona above is only half of — **the same club**.

    Three of four seats paid, the court booked, and the club just as full. The court
    side is retired entirely by the booking, and the one open seat is the only thing
    left in doubt:

        people = 0,75 + 0,25 × 0,50 = 0,875
        court  = 1 (a booked court cannot be taken by the club being busy)
        viability = 0,875,  fit = (12 + 12 × 0,875 + 8 + 6 + 6 + 4) / 48 = 96,9% → 97

    **Seventeen and a half times the viability of the match above, and 21 points of
    fit.** That is the distinction the source design could not make at all: it spent
    a weight on a term whose value never varied, so an empty court and a
    three-quarters-paid one with a booked court were the same card.
    """

    likely = doubles(ADA, BO, CY, None, hold=CourtHold.HARD, crowding=90)
    hopeless = doubles(
        None, None, None, None, viewer=ADA, hold=CourtHold.NONE, crowding=90
    )
    good = term(likely, profile(), TermCode.MATCH_VIABILITY).value
    bad = term(hopeless, profile(), TermCode.MATCH_VIABILITY).value
    assert good == ratio(7, 8)
    assert good == bad * ratio(35, 2)
    assert scored(likely) == (97, 77)
    assert scored(likely)[0] - scored(hopeless)[0] == 21


def test_the_run_up_to_the_join_cutoff_is_a_slope_and_not_a_cliff():
    """The only place ``now`` enters a Match Fit score, as a card.

    The same three-quarters-paid match at four moments before it closes to joins.
    Half a day out the last seat has all the chance it will ever have; at the cutoff
    it has none, and the match is worth exactly the three seats already paid for.

        12 hours: 0,75 + 0,25 × 0,50 × 1    = 0,875
         6 hours: 0,75 + 0,25 × 0,50 × 1/2  = 0,8125
         3 hours: 0,75 + 0,25 × 0,50 × 1/4  = 0,78125
        at the cutoff: 0,75

    A cliff at the cutoff was the alternative and would have made a match at 12:01
    and one at 11:59 different recommendations for a reason no player could see.
    """

    def at(minutes_left: int) -> Ratio:
        forming = doubles(
            ADA, BO, CY, None, cutoff=shifted(NOW, minutes(minutes_left))
        )
        return term(forming, profile(), TermCode.MATCH_VIABILITY).value

    assert at(720) == ratio(7, 8)
    assert at(360) == ratio(13, 16)
    assert at(180) == ratio(25, 32)
    assert at(0) == ratio(3, 4)
    # Twenty-two and a half hours out — a cutoff at the match's own start, which is
    # the latest one this match admits. Past a full window there is nothing more for
    # extra time to buy, so the two agree.
    assert at(720) == at(1350)


def test_a_seat_two_zloty_over_the_ceiling_costs_the_price_term_a_third():
    """21,50 against a declared 18,00 — 3,50 over, on a span of half the ceiling.

        beyond = 350 gr, span = 0,50 × 1800 = 900 gr
        price  = 1 − 350/900 = 11/18 = 0,611
        fit    = (12 + 12 + 8 + 6 + 6 × 11/18 + 4) / 48 = 45,67 / 48 = 95,1% → 95

    Not an exclusion and not a rejection: the match is 5 points worse, which is a
    thing a player can overrule.
    """

    match = doubles(ADA, BO, CY, DEE)
    declaration = profile(ceiling=1800)
    assert term(match, declaration, TermCode.PRICE).value == ratio(11, 18)
    assert scored(match, declaration) == (95, 77)


def test_a_club_card_is_what_the_price_term_actually_reads():
    """The same 21,50 seat, with a 5,00 allowance: 16,50 is inside an 18,00 ceiling.

    The share has not moved and the term goes from 0,611 to full marks, which is the
    whole reason it reads the **Payable**. A card is often the difference between a
    match somebody joins and one they scroll past.
    """

    carded = doubles(ADA, BO, CY, DEE, card=CardAllowance(amount=grosze(500)))
    assert carded.payable == 1650
    assert carded.seat_share == SEAT
    assert scored(carded, profile(ceiling=1800)) == (100, 77)


#: The days somebody who plays after work declares, and the stretch they play in.
#: Written once because four personas below are the same declaration meeting
#: different matches, which is the comparison each of them is actually about.
AFTER_WORK = dict(
    days=frozenset(
        {
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
        }
    ),
    hours=(window(18, 22),),
)


def test_a_player_who_plays_after_work_offered_a_seven_in_the_morning_match():
    """**The term the source design had no arithmetic for at all.**

    Weekday evenings declared, and a match at 07:00 on the Tuesday: the right day
    and four hours before the window opens.

        time = 0,20, fit = (12 × 0,20 + 12 + 8 + 6 + 6 + 4) / 48 = 38,4 / 48 = 80%

    It earns the warning too: time contributes 2,4, the least of the six, and 0,20
    is below the 0,40 threshold. The source document labelled a term *"Time and
    travel"* and computed only the travel half, so this match and the 18:30 one
    below were the same card — the two differ by 20 points here.
    """

    morning = doubles(ADA, BO, CY, DEE, start=starting(hour=7, minute=0))
    declaration = profile(**AFTER_WORK)
    assert term(morning, declaration, TermCode.TIME_FIT).value == ratio(1, 5)
    assert scored(morning, declaration) == (80, 77)
    assert warning_of(morning, declaration) == "time_fit"


def test_the_same_declaration_and_a_match_in_the_middle_of_the_window():
    """18:30 on a Tuesday, against weekday evenings: full marks and no warning.

    The comparison the persona above is only half of. Nothing else moves between
    the two — same four players, same price, same club — so the 20 points are the
    time term and nothing but.
    """

    evening = doubles(ADA, BO, CY, DEE)
    declaration = profile(**AFTER_WORK)
    assert term(evening, declaration, TermCode.TIME_FIT).value == 1
    assert scored(evening, declaration) == (100, 77)
    assert warning_of(evening, declaration) is None


def test_the_right_time_on_the_wrong_day_costs_exactly_what_the_wrong_time_does():
    """One value for both halves: *you said you cannot play then*, either way.

    A Saturday 18:30 match offered to somebody who declared weekday evenings scores
    the same 0,20 as the Tuesday 07:00 one. Splitting the two would be a second
    constant and a claim about their ordering that no measurement here could settle
    — so the term reports **which** half failed on its payload instead, and the
    score stays one number about one sentence.
    """

    saturday = doubles(ADA, BO, CY, DEE, start=starting(day=5))
    declaration = profile(**AFTER_WORK)
    fact = term(saturday, declaration, TermCode.TIME_FIT).fact
    assert (fact.weekday, fact.minute) == (Weekday.SATURDAY, 18 * 60 + 30)
    assert fact.inside_a_declared_window and not fact.on_a_declared_day
    assert term(saturday, declaration, TermCode.TIME_FIT).value == ratio(1, 5)
    assert scored(saturday, declaration) == (80, 77)


def test_a_ninety_minute_match_starting_inside_the_window_is_inside_it():
    """**The overlap rule, as a card rather than as a comment.**

    Somebody who plays before work declares 06:00–09:00. A match starting at 08:30
    runs well past nine, and it scores **full marks**, because the start decides.
    The alternative rule — *the whole match must fit* — is defensible and is a
    different snapshot: it needs a duration this vocabulary deliberately does not
    carry. That is stated in ``time_outside``'s falsifying note, with the
    measurement that would overturn it, rather than left for a reader to infer from
    an absence.
    """

    early = doubles(ADA, BO, CY, DEE, start=starting(hour=8, minute=30))
    before_work = profile(days=None, hours=(window(6, 9),))
    assert term(early, before_work, TermCode.TIME_FIT).value == 1
    assert scored(early, before_work) == (100, 77)

    at_nine = doubles(ADA, BO, CY, DEE, start=starting(hour=9, minute=0))
    assert term(at_nine, before_work, TermCode.TIME_FIT).value == ratio(1, 5)


def test_a_match_thirty_five_minutes_away_for_somebody_who_said_twenty():
    """15 minutes past a declared radius, on a span of 20 minutes.

        travel = 1 − 15/20 = 0,25
        fit    = (12 + 12 + 8 × 0,25 + 6 + 6 + 4) / 48 = 42 / 48 = 87,5% → 88

    And it earns the warning: travel contributes 2 of the 42 points, the least of
    the six, and its own value is below the 0,40 threshold.
    """

    match = doubles(ADA, BO, CY, DEE, travel_minutes=35)
    declaration = profile(radius=20)
    assert term(match, declaration, TermCode.TRAVEL).value == ratio(1, 4)
    assert scored(match, declaration) == (88, 77)
    assert warning_of(match, declaration) == "travel"


def test_a_social_player_offered_a_counted_match():
    """Read from the declaration, never assumed.

        match type = 0,30
        fit = (12 + 12 + 8 + 6 + 6 + 4 × 0,30) / 48 = 45,2 / 48 = 94,2% → 94

    The source design assumed everybody wants counted matches, which is a fact the
    profile already carries and which it got wrong for every player who signed up to
    play with friends.
    """

    match = doubles(ADA, BO, CY, DEE, counted=True)
    declaration = profile(match_type=MatchTypePreference.SOCIAL)
    assert term(match, declaration, TermCode.MATCH_TYPE).value == ratio(3, 10)
    assert scored(match, declaration) == (94, 77)
    assert warning_of(match, declaration) == "match_type"


def test_a_competitive_player_offered_a_friendly_scores_the_same_way_round():
    """The mismatch is symmetric: it is a mismatch, not a preference for counting."""

    friendly = doubles(ADA, BO, CY, DEE, counted=False)
    wants_counted = profile(match_type=MatchTypePreference.COMPETITIVE)
    assert scored(friendly, wants_counted) == (94, 77)
    assert scored(doubles(ADA, BO, CY, DEE, counted=True), wants_counted) == (100, 77)


def test_a_ladder_entrant_offered_a_match_that_does_not_count_for_it():
    """A term, not a modifier — and milder than a match-type mismatch.

        ladder = 0,50, fit = (12 + 12 + 8 + 6 × 0,50 + 6 + 4) / 48 = 45 / 48 = 93,75%

    93,75 rounds up on any rule. The one that is *not* on any rule is 78,5, which
    goes **away from zero** to 79 here and to 78 under Python's half-to-even; the
    rule is stated once so two neighbouring scores cannot round in opposite
    directions.
    """

    match = doubles(ADA, BO, CY, DEE, ladder=LadderQualification.OUTSIDE)
    assert term(match, profile(), TermCode.LADDER_QUALIFICATION).value == ratio(1, 2)
    assert scored(match) == (94, 77)


def test_a_player_in_no_ladder_has_no_ladder_problem():
    """The constraint rule for a fact the *match* carries rather than the profile."""

    for state in (LadderQualification.QUALIFIES, LadderQualification.NOT_IN_A_LADDER):
        match = doubles(ADA, BO, CY, DEE, ladder=state)
        assert term(match, profile(), TermCode.LADDER_QUALIFICATION).value == 1
        assert scored(match) == (100, 77)


def test_a_match_at_double_the_ceiling_and_forty_five_minutes_away():
    """Both numeric constraints floored, and it still scores rather than vanishing.

        43,00 against a 15,00 ceiling: 2800 gr over a 750 gr span → 0
        45 minutes against 20: 25 minutes over a 20-minute span    → 0
        fit = (12 + 12 + 0 + 6 + 0 + 4) / 48 = 34 / 48 = 70,8% → 71

    *Nothing is ever excluded on distance*, and price is a condition rather than a
    rejection: 71 at 77% coverage is a card a player can see and dismiss, which is
    not the same as a match they were never shown. The warning goes to travel and
    not to price, which are tied at nothing: ``min`` keeps the **first** in table
    order, the same tie-break the reasons use.
    """

    dear = replace(
        doubles(ADA, BO, CY, DEE, travel_minutes=45),
        seat_share=grosze(4300),
        payable=grosze(4300),
    )
    declaration = profile(ceiling=1500, radius=20)
    assert scored(dear, declaration) == (71, 77)
    assert warning_of(dear, declaration) == "travel"


# --- The warning, and the asymmetry it is built on -------------------------------


def test_the_lowest_contributor_can_be_perfectly_fine_and_earns_no_warning():
    """Familiarity at **full marks** out of a weight of three is last, and fine.

    Contributions: time 12, viability 12, reliability 11, travel 8, ladder 6, price
    6, match type 4, familiarity 3. Familiarity is the weakest contributor in the
    whole table and its own value is 1,0, so warning about it would teach players to
    ignore warnings.
    """

    perfect = replace(
        with_records(doubles(ADA, BO, CY, DEE), None, 100, 100, 100),
        history=PlayHistory(played_recently=frozenset()),
    )
    familiarity = term(perfect, profile(), TermCode.FAMILIARITY)
    assert isinstance(familiarity, ScoredTerm)
    assert familiarity.contribution == min(
        item.contribution
        for item in ENGINE.score(
            snapshot=perfect, profile=profile(), analysis=analysis(), now=NOW
        ).scored
    )
    assert familiarity.value == 1
    assert scored(perfect) == (100, 100)
    assert warning_of(perfect, profile()) is None


def test_a_genuinely_bad_term_earns_no_warning_when_it_is_not_the_weakest():
    """**The asymmetry, in the direction that surprises people.**

    A group whose least reliable member turns up three times in ten scores 0,30 —
    below the 0,40 threshold — and gets *no* warning, because its contribution is
    11 × 0,30 = 3,3, while familiarity at full marks contributes 3,0 and is
    therefore the weakest. The warning is *the lowest contributor's, when its own
    value is bad*, and both halves of that are load-bearing.

    Whether that is the right rule is a product question the constant's falsifying
    note owns. What is not in doubt is that it is the rule the spec asked for, so it
    is pinned here rather than quietly widened into *any bad term warns*.
    """

    unreliable = replace(
        with_records(doubles(ADA, BO, CY, DEE), None, 30, 95, 95),
        history=PlayHistory(played_recently=frozenset()),
    )
    reliability = term(unreliable, profile(), TermCode.GROUP_RELIABILITY)
    familiarity = term(unreliable, profile(), TermCode.FAMILIARITY)
    assert isinstance(reliability, ScoredTerm) and isinstance(familiarity, ScoredTerm)

    assert reliability.value < CONSTANTS.warning_threshold
    assert reliability.contribution > familiarity.contribution
    assert warning_of(unreliable, profile()) is None
    assert scored(unreliable) == (88, 100)


def test_playing_the_same_three_people_every_week_is_gently_discouraged():
    """Every face already known: familiarity 0, and *gently* is the weight of three.

        fit = (12 + 12 + 11 + 8 + 6 + 6 + 4 + 0) / 62 = 59 / 62 = 95,2% → 95

    Five points off a perfect card for a group with no variety in it at all, and the
    warning fires: familiarity is both the weakest contributor and at zero.
    """

    the_usual = replace(
        with_records(doubles(ADA, BO, CY, DEE), None, 100, 100, 100),
        history=PlayHistory(
            played_recently=frozenset(
                {PlayerRef("bo"), PlayerRef("cy"), PlayerRef("dee")}
            )
        ),
    )
    assert term(the_usual, profile(), TermCode.FAMILIARITY).value == 0
    assert scored(the_usual) == (95, 100)
    assert warning_of(the_usual, profile()) == "familiarity"


def test_the_current_players_own_record_is_not_read_into_their_own_recommendation():
    """You know whether *you* will turn up.

    Ada is on the first seat and is the person the score is for. Give her a terrible
    record and the group's reliability does not move — otherwise the platform's
    opinion of a player would be a reason to show that player fewer matches.
    """

    others_only = replace(
        with_records(doubles(ADA, BO, CY, DEE), 5, 90, 90, 90),
        history=PlayHistory(played_recently=frozenset()),
    )
    assert term(others_only, profile(), TermCode.GROUP_RELIABILITY).value == ratio(
        9, 10
    )


@pytest.mark.parametrize(
    "reliabilities, expected",
    [((None, 90, 90, 90), ratio(9, 10)), ((None, 90, 40, 90), ratio(2, 5))],
    ids=["all dependable", "one who does not come"],
)
def test_a_group_is_only_as_dependable_as_its_least_dependable_member(
    reliabilities, expected
):
    """A match needs everybody, so an average would let three good records hide one
    bad one — and one no-show cancels the evening for the other three."""

    group = replace(
        with_records(doubles(ADA, BO, CY, DEE), *reliabilities),
        history=PlayHistory(played_recently=frozenset()),
    )
    assert term(group, profile(), TermCode.GROUP_RELIABILITY).value == expected
