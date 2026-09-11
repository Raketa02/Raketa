"""Ruleset ``2026.09.08-a`` — a third live strand, at the share it used to hold.

**One release, and it moves exactly two things**: the two ``strand_weights``
vectors gain ``ANSWERS_RESULTS``, and ``min_observations`` becomes a bar per
strand so that one of them can ask for five without the other five asking for it
too (``docs/adr/0160``). Everything else in this file is ``2026.08.26-a``
unchanged, and it is copied rather than referenced because a released dataset is
read as a whole — a file that inherited most of its numbers from another one
would make *what did this search run under* a question answered by a diff.

**The strand weights are restored and not retuned.** They are the six numbers
this vector carried before ``docs/adr/0137`` struck *confirms results*:
competitive 25/22/24/14/10/5 and for fun 32/22/4/14/12/16. ``2026.08.26-a``'s
five were those same ratios rescaled by largest remainder over the smaller
vocabulary (``docs/adr/0140`` §7), so restoring the sixth share restores the
five beside it exactly. **Nothing was learned about the other five** — this is a
strand arriving with its old share, and inventing new numbers for the survivors
would be a hypothesis with no evidence behind it dressed up as tidiness.

**The name is different and so is the measurement.** *Confirms results* counted
agreements and was struck because an unconfirmed result is a fact about a
**pair**; *answers about results* counts **answers**, and a counter is as good as
an acceptance, so nobody is docked for disagreeing. The record is
``docs/adr/0160`` and the argument that this is not a reinstatement is its
Decision 1.

**What this release costs, and it is not nothing.** Every player with a record is
re-mixed on deploy: a third strand enters the published blend and both mode
vectors, so a matcher penalty can appear or lift through no action of the
player's. The offline diff is what that claim is argued on, and it is committed
beside this file.

**This file is frozen.** A number moves in a *new* dataset with a *new* name, and
the pull request carries the offline diff plus one line per changed constant: the
hypothesis, and what would falsify it. Editing a released ruleset would make every
recorded search's ``ruleset_version`` a lie about the numbers it ran under.

**The owner who signs a release is the owner of the quality floor** — one number
decides when the product says nothing rather than something, and the numbers
around it decide what it says instead; splitting the accountability makes each
owner reasonable and the pair of them wrong. Owner: ``RobertConstantin02``.

**Tag ids are read from the vocabulary, never retyped.** The engine holds them as
opaque machine-code strings because it may not import a module; this file is on
the other side of that fence, so every id below comes off ``SocialTag`` and a
retired or renamed one is an import error rather than a row that silently never
fires. That they are exhaustive over ``WHY_YOU_ARE_HERE`` — and that a ruleset
arriving one day from a runtime store names ids this platform serves — is checked
in the composition root.
"""

from __future__ import annotations

from types import MappingProxyType

from app.engines.matchfit.core import (
    ChallengeLoad,
    ClashSeverity,
    FamiliarityReading,
    GroupTerm,
    LivenessSignal,
    Modifier,
    RelaxationRung,
    ReliabilityStrand,
    SearchMode,
    Seat,
    TagColumn,
    TagRelationshipKind,
    Term,
)
from app.engines.matchfit.ruleset import (
    BalanceRules,
    ChallengeLoadRung,
    DistanceRules,
    ExplanationRules,
    FamiliarityRules,
    Floors,
    GroupRules,
    IntentRules,
    InterestRules,
    LivenessRules,
    ModeRules,
    ModifierRules,
    PointRange,
    RelaxationRules,
    ReliabilityRules,
    Ruleset,
    ShapeRules,
    SignalBound,
    TagRelationship,
    TagRules,
    TelemetryRules,
)
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.social_tags import SocialTag

VERSION = "2026.09.08-a"

#: The complement discount, defined once. It is both ``TagRules.complement_strength``
#: and the default a row that states no strength takes — and those two must be one
#: constant, because ``validate_ruleset`` refuses a row *below the ruleset's own
#: default*. Two spellings would make moving one of them either silently change what
#: *at the default* means or refuse the whole dataset on load.
_COMPLEMENT_STRENGTH = 0.70

_BOTH_MODES = (SearchMode.COMPETITIVE, SearchMode.FOR_FUN)
_BOTH_SEATS = (Seat.PARTNER, Seat.OPPONENT)


def _match(tag: SocialTag, column: TagColumn) -> TagRelationship:
    """One id against itself. Column defaults to the id's group in the picker and
    is overridden only where the claim plainly sits elsewhere — which happens
    exactly once, for ``TALKS_THROUGH_THE_MATCH``: it is filed under *after the
    match*, and *"you both talk through the match"* is felt during the hour.
    """

    return TagRelationship(
        a=tag.value,
        b=tag.value,
        kind=TagRelationshipKind.MATCH,
        column=column,
        modes=_BOTH_MODES,
        seats=_BOTH_SEATS,
    )


def _complement(
    a: SocialTag,
    b: SocialTag,
    column: TagColumn,
    strength: float = _COMPLEMENT_STRENGTH,
    modes: tuple[SearchMode, ...] = _BOTH_MODES,
) -> TagRelationship:
    return TagRelationship(
        a=a.value,
        b=b.value,
        kind=TagRelationshipKind.COMPLEMENT,
        column=column,
        modes=modes,
        seats=_BOTH_SEATS,
        strength=strength,
    )


def _clash(
    a: SocialTag,
    b: SocialTag,
    column: TagColumn,
    severity: ClashSeverity,
    modes: tuple[SearchMode, ...] = _BOTH_MODES,
    seats: tuple[Seat, ...] = _BOTH_SEATS,
) -> TagRelationship:
    return TagRelationship(
        a=a.value,
        b=b.value,
        kind=TagRelationshipKind.CLASH,
        column=column,
        modes=modes,
        seats=seats,
        severity=severity,
    )


#: Eighteen match rows over the nineteen ids that shipped.
#:
#: **Exhaustive on the match arm by obligation** — each id either takes a row or
#: is named here with the reason it takes none. That is a nineteen-row
#: obligation, not a 171-pair one: authoring 171 pairs to a standard anyone would
#: defend is not possible, and a pair with no row is not silence, it is the
#: legitimate answer *different, not incompatible*.
#:
#: **``OPEN_TO_MEET_SOMEONE`` takes no row of any kind.** A tag about the person
#: rather than the game may be shown; it may never score (``docs/adr/0115``). A
#: player who spends one of their minimum two tags on it has spent half their
#: budget on something the matcher never reads, and nothing tells them — a price
#: that record accepts rather than solves.
_MATCH_ROWS = (
    _match(SocialTag.TALKS_THROUGH_THE_MATCH, TagColumn.STYLE),
    _match(SocialTag.PLAYS_TO_WIN, TagColumn.STYLE),
    _match(SocialTag.LAUGHS_OFF_MISTAKES, TagColumn.STYLE),
    _match(SocialTag.ENCOURAGES_A_PARTNER, TagColumn.STYLE),
    _match(SocialTag.GENEROUS_ON_LINE_CALLS, TagColumn.STYLE),
    _match(SocialTag.QUIET_AND_FOCUSED, TagColumn.STYLE),
    _match(SocialTag.WARMS_UP_PROPERLY, TagColumn.STYLE),
    _match(SocialTag.STAYS_FOR_A_DRINK, TagColumn.VIBE),
    _match(SocialTag.STRAIGHT_HOME_AFTER, TagColumn.VIBE),
    _match(SocialTag.SETTLES_UP_ON_THE_SPOT, TagColumn.VIBE),
    _match(SocialTag.BOOKS_THE_NEXT_ONE, TagColumn.VIBE),
    _match(SocialTag.SHARES_A_LIFT, TagColumn.VIBE),
    _match(SocialTag.HERE_TO_IMPROVE, TagColumn.VIBE),
    _match(SocialTag.HERE_TO_COMPETE, TagColumn.VIBE),
    _match(SocialTag.HERE_FOR_THE_EXERCISE, TagColumn.VIBE),
    _match(SocialTag.HERE_TO_MEET_PLAYERS, TagColumn.VIBE),
    _match(SocialTag.HERE_FOR_A_REGULAR_GAME, TagColumn.VIBE),
    _match(SocialTag.HERE_TO_GET_BACK_INTO_IT, TagColumn.VIBE),
)

#: Twelve complement rows. Six are the input document's; six are added, because
#: six complements over 171 pairs leaves the arm decorative.
#:
#: **All twelve are unscoped on ``seats``**, the two returning-player rows
#: included: their value is largest in exactly the unseated shortlist a
#: ``PARTNER`` scope would exclude them from, and ``ENCOURAGES_A_PARTNER``'s
#: wording is partner-shaped where its behaviour is not.
#:
#: **Two rows sit at parity and no row sits below the default.** A complement
#: product is not confident about should not be a row.
_COMPLEMENT_ROWS = (
    # One wants to get better; the other runs the half hour that does it.
    _complement(
        SocialTag.HERE_TO_IMPROVE, SocialTag.WARMS_UP_PROPERLY, TagColumn.STYLE
    ),
    # The returning player, and the person who makes returning bearable.
    _complement(
        SocialTag.HERE_TO_GET_BACK_INTO_IT,
        SocialTag.ENCOURAGES_A_PARTNER,
        TagColumn.STYLE,
        1.00,
    ),
    # A first game back should not be litigated.
    _complement(
        SocialTag.HERE_TO_GET_BACK_INTO_IT,
        SocialTag.GENEROUS_ON_LINE_CALLS,
        TagColumn.STYLE,
    ),
    # The standing four, and the person who actually makes it standing.
    _complement(
        SocialTag.HERE_FOR_A_REGULAR_GAME,
        SocialTag.BOOKS_THE_NEXT_ONE,
        TagColumn.VIBE,
        1.00,
    ),
    # One needs a way in; the other is already going.
    _complement(
        SocialTag.HERE_TO_MEET_PLAYERS, SocialTag.SHARES_A_LIFT, TagColumn.VIBE
    ),
    # The same, an hour later.
    _complement(
        SocialTag.HERE_TO_MEET_PLAYERS, SocialTag.STAYS_FOR_A_DRINK, TagColumn.VIBE
    ),
    # Rust, unremarked on.
    _complement(
        SocialTag.HERE_TO_GET_BACK_INTO_IT,
        SocialTag.LAUGHS_OFF_MISTAKES,
        TagColumn.STYLE,
    ),
    # A body that has been off needs the half hour more, not less.
    _complement(
        SocialTag.HERE_TO_GET_BACK_INTO_IT, SocialTag.WARMS_UP_PROPERLY, TagColumn.STYLE
    ),
    # One wants a way in; the other turns one game into several.
    _complement(
        SocialTag.HERE_TO_MEET_PLAYERS, SocialTag.BOOKS_THE_NEXT_ONE, TagColumn.VIBE
    ),
    # For one of them the conversation is the point.
    _complement(
        SocialTag.HERE_TO_MEET_PLAYERS,
        SocialTag.TALKS_THROUGH_THE_MATCH,
        TagColumn.VIBE,
    ),
    # *That is precisely how you improve* — in tag ids only, and competitive
    # only, which is what keeps it disjoint from the for-fun clash below.
    _complement(
        SocialTag.HERE_TO_IMPROVE,
        SocialTag.PLAYS_TO_WIN,
        TagColumn.STYLE,
        modes=(SearchMode.COMPETITIVE,),
    ),
    # The standing game somebody drives to — the weakest of the six added.
    _complement(
        SocialTag.HERE_FOR_A_REGULAR_GAME, SocialTag.SHARES_A_LIFT, TagColumn.VIBE
    ),
)

#: Seven clash rows, and the arm is sparse **on purpose**: competitive players
#: are separated by level rather than by temperament, so the clash arm is worth
#: half a point of 100 in competitive singles and up to 7.3 in for fun.
#:
#: **One deliberate omission, stated rather than left silent.**
#: ``PLAYS_TO_WIN`` against ``HERE_TO_GET_BACK_INTO_IT`` is a real mismatch and
#: takes no row: level fit already separates them, and the returning player is
#: the population the newcomer path decided to protect. A clash row against them
#: costs more than it buys.
_CLASH_ROWS = (
    # *Ruins the hour for both* — far worse as partners, which one severity field
    # cannot say, so it is two rows with disjoint seat scope and no new constant.
    _clash(
        SocialTag.TALKS_THROUGH_THE_MATCH,
        SocialTag.QUIET_AND_FOCUSED,
        TagColumn.STYLE,
        ClashSeverity.REAL,
        seats=(Seat.PARTNER,),
    ),
    _clash(
        SocialTag.TALKS_THROUGH_THE_MATCH,
        SocialTag.QUIET_AND_FOCUSED,
        TagColumn.STYLE,
        ClashSeverity.MILD,
        seats=(Seat.OPPONENT,),
    ),
    # *In a competitive game nobody promised an evening.*
    _clash(
        SocialTag.STAYS_FOR_A_DRINK,
        SocialTag.STRAIGHT_HOME_AFTER,
        TagColumn.VIBE,
        ClashSeverity.MILD,
        modes=(SearchMode.FOR_FUN,),
    ),
    _clash(
        SocialTag.PLAYS_TO_WIN,
        SocialTag.HERE_FOR_THE_EXERCISE,
        TagColumn.STYLE,
        ClashSeverity.MILD,
        modes=(SearchMode.FOR_FUN,),
    ),
    # Partner relationship only.
    _clash(
        SocialTag.PLAYS_TO_WIN,
        SocialTag.LAUGHS_OFF_MISTAKES,
        TagColumn.STYLE,
        ClashSeverity.MILD,
        seats=(Seat.PARTNER,),
    ),
    # *A mild one in a friendly* — disjoint with the competitive complement above.
    _clash(
        SocialTag.PLAYS_TO_WIN,
        SocialTag.HERE_TO_IMPROVE,
        TagColumn.STYLE,
        ClashSeverity.MILD,
        modes=(SearchMode.FOR_FUN,),
    ),
    # Added — the negation of two complements already in the table.
    _clash(
        SocialTag.STRAIGHT_HOME_AFTER,
        SocialTag.HERE_TO_MEET_PLAYERS,
        TagColumn.VIBE,
        ClashSeverity.MILD,
        modes=(SearchMode.FOR_FUN,),
    ),
)

RULESET = Ruleset(
    version=VERSION,
    released_on="2026-09-08",
    modes=MappingProxyType(
        {
            # Level fit carries a quarter of a competitive match. Falsified by
            # return rate by level gap, split by band: if pairs at Δμ 0.4 return
            # as well as pairs at 0.1, the curve is too steep.
            SearchMode.COMPETITIVE: ModeRules(
                weights=MappingProxyType(
                    {
                        Term.LEVEL_FIT: 26,
                        Term.PREDICTED_BALANCE: 17,
                        Term.INTENT_ALIGNMENT: 14,
                        Term.RELIABILITY: 13,
                        Term.AVAILABILITY_OVERLAP: 11,
                        Term.PLAYING_STYLE: 9,
                        Term.DISTANCE: 6,
                        Term.SOCIAL_VIBE: 4,
                    }
                ),
                # **Restored, not retuned** (``docs/adr/0160``). These are the
                # six numbers this vector carried before *confirms results* was
                # struck; 2026.08.26-a's five are the same ratios rescaled by
                # largest remainder over the smaller vocabulary, so putting a
                # third live strand in at the share it held is the whole of the
                # release. Falsified the way every weight here is: if
                # candidates a searcher was shown who never answer a score
                # accept and turn up as well as those who do, twenty-four is
                # too much of a competitive record.
                strand_weights=MappingProxyType(
                    {
                        ReliabilityStrand.SHOWS_UP: 25,
                        ReliabilityStrand.ANSWERS_CHALLENGES: 22,
                        ReliabilityStrand.ANSWERS_RESULTS: 24,
                        ReliabilityStrand.KEEPS_PLANS: 14,
                        ReliabilityStrand.SETTLES_UP: 10,
                        ReliabilityStrand.SPORTSMANSHIP: 5,
                    }
                ),
                level_tolerance=0.55,
                free_band=None,
                # Roughly half the tolerance — *a noticeably better game*.
                tag_stuffing_margin=0.30,
            ),
            # **The inversion is the shape.** Social vibe is the largest term in
            # a friendly — larger than level — because that is what *for fun*
            # means, and it is a bigger shift than the prototype ever made.
            SearchMode.FOR_FUN: ModeRules(
                weights=MappingProxyType(
                    {
                        Term.LEVEL_FIT: 11,
                        Term.PREDICTED_BALANCE: 6,
                        Term.INTENT_ALIGNMENT: 14,
                        Term.RELIABILITY: 9,
                        Term.AVAILABILITY_OVERLAP: 16,
                        Term.PLAYING_STYLE: 11,
                        Term.DISTANCE: 11,
                        Term.SOCIAL_VIBE: 22,
                    }
                ),
                # Restored the same way, and **this is where the inversion
                # lives**: a score answered promptly is a quarter of a
                # competitive record and a twenty-fifth of a friendly one,
                # against sportsmanship's five and sixteen. That pair is the
                # standing justification for reading strands separately at all,
                # and it was the pair the strike took away.
                strand_weights=MappingProxyType(
                    {
                        ReliabilityStrand.SHOWS_UP: 32,
                        ReliabilityStrand.ANSWERS_CHALLENGES: 22,
                        ReliabilityStrand.ANSWERS_RESULTS: 4,
                        ReliabilityStrand.KEEPS_PLANS: 14,
                        ReliabilityStrand.SETTLES_UP: 12,
                        ReliabilityStrand.SPORTSMANSHIP: 16,
                    }
                ),
                level_tolerance=0.90,
                free_band=0.25,
                # None, and deliberately: in a friendly the tags are
                # *supposed* to outrank level.
                tag_stuffing_margin=None,
            ),
        }
    ),
    # The six cells, unamended from ADR-0094's table. **`NO_PREFERENCE` is
    # nearly as good as a match** — these players are the glue, and punishing
    # the honest middle would teach everybody to declare a side. The two zeros
    # are not symmetric: a competitive searcher meeting a declared friendly
    # reads 0.00, where a for-fun searcher meeting a declared competitor reads
    # 0.35, because a competitor will play a friendly and the reverse ruins the
    # evening for one of them.
    #
    # Falsified by acceptance rate across the six cells: if the 0.35 cell
    # accepts like the 0.85 one, the asymmetry is imagined.
    intent=IntentRules(
        alignment=MappingProxyType(
            {
                SearchMode.COMPETITIVE: MappingProxyType(
                    {
                        PlayIntent.COMPETITIVE.value: 1.00,
                        PlayIntent.FOR_FUN.value: 0.00,
                        PlayIntent.NO_PREFERENCE.value: 0.85,
                    }
                ),
                SearchMode.FOR_FUN: MappingProxyType(
                    {
                        PlayIntent.COMPETITIVE.value: 0.35,
                        PlayIntent.FOR_FUN.value: 1.00,
                        PlayIntent.NO_PREFERENCE.value: 0.85,
                    }
                ),
            }
        ),
        same_evening=MappingProxyType(
            {
                SearchMode.COMPETITIVE: PlayIntent.COMPETITIVE.value,
                SearchMode.FOR_FUN: PlayIntent.FOR_FUN.value,
            }
        ),
    ),
    tags=TagRules(
        # 1 tag 0.55 · 2 tags 0.80 · 3 tags 0.91 · 6 tags 0.99. The second matched
        # tag is worth less than the first, so tag-stuffing does not pay — and the
        # platform caps selection at six precisely because it expects people to try.
        phi=0.45,
        complement_strength=_COMPLEMENT_STRENGTH,
        clash_severities=MappingProxyType(
            {
                ClashSeverity.REAL: 0.15,
                ClashSeverity.MILD: 0.06,
            }
        ),
        # Binds at two real clashes, or one real plus two mild.
        clash_cap=0.25,
        relationship_matrix=_MATCH_ROWS + _COMPLEMENT_ROWS + _CLASH_ROWS,
        # Exhaustive over the seven ``WHY_YOU_ARE_HERE`` ids. Two are in
        # *neither* on purpose: ``HERE_TO_COMPETE`` wants good opposition and
        # says nothing about repetition, and ``HERE_FOR_THE_EXERCISE`` says
        # nothing about **who**. Repetition wins a tie; an all-*neither* reader
        # falls to the default lean.
        familiarity_reading_map=MappingProxyType(
            {
                SocialTag.HERE_FOR_A_REGULAR_GAME.value: FamiliarityReading.REPETITION,
                SocialTag.HERE_TO_MEET_PLAYERS.value: FamiliarityReading.VARIETY,
                SocialTag.HERE_TO_GET_BACK_INTO_IT.value: FamiliarityReading.VARIETY,
                SocialTag.HERE_TO_IMPROVE.value: FamiliarityReading.VARIETY,
                SocialTag.HERE_TO_COMPETE.value: FamiliarityReading.NEITHER,
                SocialTag.HERE_FOR_THE_EXERCISE.value: FamiliarityReading.NEITHER,
                SocialTag.OPEN_TO_MEET_SOMEONE.value: FamiliarityReading.NEITHER,
            }
        ),
    ),
    # The term goes blind at Δμ ≈ 0.34 for a typical σ_pair of 0.495 — that is
    # where `pct` reaches its floor and stops discriminating, which is what the
    # level gate exists to cover.
    balance=BalanceRules(
        mu_coefficient=145.0,
        sigma_coefficient=32.0,
        pct_min=35,
        pct_max=96,
        # A doubles side is attacked at its weaker half all evening, so the
        # weaker partner sets 0.55 of it against the stronger's 0.45. It reads
        # only in a four, and it is the whole reason the three arrangements of
        # one four differ: at 0.50 every arrangement of the same people would
        # forecast the same game and the seat delta would be deciding alone.
        stronger_partner_share=0.45,
    ),
    # Full marks inside 70% of the searcher's own ring, zero at 115% of it. The
    # curve is generous at the top because inside two thirds of the radius you
    # said you would travel, one kilometre more is not a fact about the evening;
    # it costs from there and is still worth a third of the term at the ring
    # itself, where the gate cuts.
    #
    # Falsified by acceptance rate by distance as a fraction of the searcher's
    # own radius. If acceptance is flat out to the ring the curve is too steep,
    # and if it falls away well inside 70% the shoulder is in the wrong place.
    distance=DistanceRules(
        full_marks_within=0.70,
        zero_at=1.15,
    ),
    # 70 is roughly *you have missed something like a fifth of what you committed
    # to*. It is a **dock, not an exclusion**: refusing to show a genuinely good
    # match over one missed game is the block's job, not the matcher's.
    reliability=ReliabilityRules(
        # **One bar per strand, and only one of them moved** (``docs/adr/0160``).
        # Three is what the other five have always asked and they keep it: one
        # ghost out of one arrangement stands *shows up* down rather than
        # publishing a nought. *Answers about results* asks five, because it
        # prices **silence** and silence is cheap to produce by accident — a flat
        # battery and simple inattention are the same event to us (``docs/adr/
        # 0049``), so a short record of them is noise rather than a habit.
        #
        # Raising the single number to five instead was rejected in the record:
        # it would take a newcomer who has played three games and turned up to
        # all three from a full score to no score at all, which is a decision
        # about how this product treats newcomers and not a consequence of
        # tuning one strand.
        #
        # Falsified by the same measurement the strand is: if a player's answer
        # rate over their first five results predicts their rate over the next
        # twenty no better than their rate over the first three does, the bar is
        # higher than the evidence needs.
        min_observations=MappingProxyType(
            {
                ReliabilityStrand.SHOWS_UP: 3,
                ReliabilityStrand.ANSWERS_CHALLENGES: 3,
                ReliabilityStrand.ANSWERS_RESULTS: 5,
                ReliabilityStrand.KEEPS_PLANS: 3,
                ReliabilityStrand.SETTLES_UP: 3,
                ReliabilityStrand.SPORTSMANSHIP: 3,
            }
        ),
        horizon_days=365,
        published_score_bar=70,
    ),
    modifiers=ModifierRules(
        budget=10,
        ranges=MappingProxyType(
            {
                # The only modifier whose input exists today, and **binary rather
                # than a ramp**: `calibration_priority` has two values. Competitive
                # only, and printed — a player is entitled to know when they are
                # being matched partly for somebody else's benefit.
                Modifier.CALIBRATION_VALUE: PointRange(minimum=0, maximum=4),
                Modifier.FAMILIARITY: PointRange(minimum=-4, maximum=5),
                Modifier.WELCOMING_RECORD: PointRange(minimum=0, maximum=4),
            }
        ),
        familiarity=FamiliarityRules(
            half_life_days=90,
            depth_phi=0.45,
            default_lean=0.5,
        ),
        newcomer_absorption_cap=None,
    ),
    liveness=LivenessRules(
        offset_minimum=-25,
        offset_maximum=25,
        signals=MappingProxyType(
            {
                # Flat, and it must print: a human's own ask outranks the
                # engine's opinion of that human's popularity.
                LivenessSignal.INTEREST_RECEIVED: SignalBound(
                    PointRange(14, 14), printable=True
                ),
                LivenessSignal.PREVIOUS_ACCEPT: SignalBound(
                    PointRange(6, 6), printable=True
                ),
                LivenessSignal.ANSWER_RATE_AND_SPEED: SignalBound(
                    PointRange(-6, 6), printable=True
                ),
                LivenessSignal.RECENT_ACTIVITY: SignalBound(
                    PointRange(-5, 4), printable=True
                ),
                LivenessSignal.OVERLAP_PROXIMITY: SignalBound(
                    PointRange(0, 4), printable=True
                ),
                # Printable as a coarse code and **never the number**: their
                # inbox depth is theirs. Anchored twice rather than chosen —
                # strictly inside the interest lift, and equal to reciprocal
                # asymmetry, the other *this candidate is a bad bet for you*
                # signal.
                LivenessSignal.CHALLENGE_LOAD: SignalBound(
                    PointRange(-12, 0), printable=True
                ),
                LivenessSignal.RECIPROCAL_ASYMMETRY: SignalBound(
                    PointRange(-12, 0), printable=True
                ),
                # Never shown to either side, which is why it is budgeted rather
                # than bounded on its own.
                LivenessSignal.PREVIOUS_DECLINE: SignalBound(
                    PointRange(-6, -6), printable=False
                ),
                # *They're new — this game does most of its work for them* is a
                # sentence the product wants said, so the lift speaks and
                # reclaims its points honestly.
                LivenessSignal.NEWCOMER_LIFT: SignalBound(
                    PointRange(8, 8), printable=True
                ),
                # *You are seeing this person because nobody has been shown them
                # all week* is a third party's unpopularity, and the searcher is
                # owed no version of it.
                LivenessSignal.EXPOSURE_ADJUSTMENT: SignalBound(
                    PointRange(-6, 6), printable=False
                ),
            }
        ),
        # §14.4's three thresholds, adopted whole by `docs/adr/0125` — only the
        # third's *effect* changed, from a 24-hour withholding to the sink's own
        # floor. They are the one liveness signal read from a count rather than
        # from a normalised reading, because they are the one set of thresholds
        # somebody measured before this map existed.
        #
        # Falsified by answer rate by open-challenge bucket. If answer rate does
        # not fall as load rises, the signal is measuring nothing and all three
        # rungs are noise.
        challenge_load_rungs=(
            ChallengeLoadRung(at_least=3, points=-4, prints=ChallengeLoad.SOME),
            ChallengeLoadRung(at_least=5, points=-8, prints=ChallengeLoad.BUSY),
            ChallengeLoadRung(at_least=8, points=-12, prints=ChallengeLoad.FULL),
        ),
        move_notice=6,
        asymmetry_tolerance=12,
        # `dock = −min(12, asym × 0.5)`. Half a point of dock per point of
        # shortfall past the tolerance, saturating at a shortfall of 24 — which
        # is twice the tolerance, so a candidate has to be as far past the head
        # start again as the head start itself before the sink bottoms out.
        #
        # Falsified with the tolerance beside it: decline rate by asymmetry
        # bucket. If decline rate is flat across the buckets, the shortfall
        # predicts nothing and the slope is docking people for arithmetic.
        asymmetry_slope=0.5,
    ),
    group=GroupRules(
        weights=MappingProxyType(
            {
                SearchMode.COMPETITIVE: MappingProxyType(
                    {
                        GroupTerm.BALANCE: 34,
                        GroupTerm.SEAT_FIT: 20,
                        GroupTerm.MIN_SEAT_FIT: 16,
                        GroupTerm.CROSS: 8,
                        GroupTerm.CROSS_MIN: 6,
                        GroupTerm.AVAILABILITY: 16,
                    }
                ),
                # Balance at 16 against seat fit at 17 is parity, and it is the
                # vector's known weak point: for-fun balance is 6.6 of 100 in
                # Fit and evenness is not what a friendly is for. **The first
                # contrast to re-run** once real fours exist.
                SearchMode.FOR_FUN: MappingProxyType(
                    {
                        GroupTerm.BALANCE: 16,
                        GroupTerm.SEAT_FIT: 17,
                        GroupTerm.MIN_SEAT_FIT: 13,
                        GroupTerm.CROSS: 20,
                        GroupTerm.CROSS_MIN: 14,
                        GroupTerm.AVAILABILITY: 20,
                    }
                ),
            }
        ),
        k=24,
    ),
    # 44 rather than the input document's 52, and the case that refutes 52 is
    # named: **52 hides the median stranger in both modes**, and that case's
    # stated job is to sit at the bar. The bound is arithmetic —
    # `24.5 < floor ≤ 44.5` — and the margin is half a point.
    floors=Floors(
        quality_floor=44,
        min_shortlist=5,
        minimum_evidence_fraction=0.5,
    ),
    shape=ShapeRules(
        shortlist_max=20,
        deck_deal_max=10,
    ),
    relaxation=RelaxationRules(
        radius_multipliers=MappingProxyType(
            {
                RelaxationRung.RADIUS_NEAR: 1.5,
                RelaxationRung.RADIUS_FAR: 2.0,
            }
        ),
    ),
    telemetry=TelemetryRules(near_miss_recorded=10),
    # Five points of a hundred. The smallest weight any term carries on the
    # day-one basis is social vibe's 4.6 competitive, so a lower bar would let a
    # term warn about a shortfall it cannot produce even by reading zero.
    #
    # Falsified by the fraction of shown candidates carrying no concern at all:
    # if almost every card warns about something, the line has stopped being a
    # warning and become a caption.
    explanation=ExplanationRules(concern_points=5),
    interest=InterestRules(
        # 21 rather than 7: a yes is silent, and a player who searches once a
        # fortnight would never see most of a week-long one. The failure that
        # costs the product is *the yes never fired*, not *the yes was stale*.
        ttl_days=21,
        outstanding_cap_per_sport=20,
        pass_suppress_days=30,
    ),
)
