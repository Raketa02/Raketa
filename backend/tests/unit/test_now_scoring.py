"""Assembling a snapshot: the sentinel that cannot move a score, and the phase.

Two of this module's decisions are the kind no behavioural test reaches on its
own, so they are asserted as **properties** rather than described in a comment:

* a travel time the platform never measured provably does not change any score,
  because the travel term is a constraint and no player can declare a radius;
* a cancelled match never reaches an engine, because eligibility holds the guard
  the snapshot's ``phase`` field was written to hold.

The day either stops being true, one of these goes red — which is the whole
reason they are here and not in prose.
"""

from __future__ import annotations

from dataclasses import fields
from uuid import uuid4

import pytest

from app.engines.fit import TermCode
from app.engines.matchfit.v1 import MatchFitEngineV1
from app.engines.matchmaking import (
    CourtHold,
    LadderQualification,
    MatchPhase,
    MatchTypePreference,
    PlayerProfile,
    SeatState,
)
from app.engines.pairing.v1 import PairingEngineV1
from app.kernel import InvariantViolated, Sport, instant, minutes, ratio

from app.modules.now.application.scoring import (
    REASON_CAP,
    TRAVEL_UNMEASURED,
    MatchScorer,
    Unscorable,
    badge_from,
    profile_for,
    snapshot_for,
)
from app.modules.now.domain.funnel import BADGE_CEILING, BADGE_FLOOR
from app.modules.now.domain.screen import Fit
from tests.unit.match_records import at
from tests.unit.shelf_doubles import a_club, a_context, a_match, rated, unrated

NOW = at(-2880)
VIEWER = rated(300)

#: A match aimed well above the viewer below it. Both of the two largest terms
#: score badly, which is what lifts travel — weight 8, always full marks — into
#: the engine's top three by contribution.
_MISMATCHED = a_context(
    record=a_match(paid=1), occupants=(rated(480), None, None, None)
)


def _scorer() -> MatchScorer:
    return MatchScorer(pairing=PairingEngineV1(), matchfit=MatchFitEngineV1())


# --- 1 · the profile --------------------------------------------------------


def test_a_player_has_declared_nothing_and_that_is_the_honest_launch_state() -> None:
    """The preferences editor has no screen and no contract (#105).

    ``PlayerProfile()`` is what the engine calls the honest launch state: such a
    player has no price problem, no travel problem and no match-type problem, so
    those terms score full marks, keep their weight, and Coverage is untouched.
    """

    assert profile_for(uuid4()) == PlayerProfile()


def test_no_player_can_declare_a_travel_radius_today() -> None:
    """The precondition the sentinel below rests on, asserted separately.

    If this ever fails, the property test under it is measuring nothing.
    """

    assert profile_for(uuid4()).travel_radius is None


# --- 2 · the travel sentinel ------------------------------------------------


@pytest.mark.parametrize("sentinel", [minutes(0), minutes(5), minutes(600)])
def test_an_unmeasured_travel_time_cannot_move_a_score(sentinel) -> None:
    """The property that makes a fabricated number safe, run rather than argued.

    Travel is a **constraint** term: an undeclared radius is genuinely *no
    limit*, so the term scores full marks whatever the minutes beside it are.
    Every player has an undeclared radius today, so the sentinel provably does
    not move any score — and the day a radius reaches the profile, this goes red,
    which is the day the sentinel stops being safe and the field wants the
    optional treatment ADR-0027 gives evidence.

    The **fit, the coverage and every term's value** are what is compared, and
    that is the whole of the claim. The fact *payload* does differ — it carries
    the minutes it was handed — which is exactly why a travel reason is withheld
    from the badge: a number that ranks identically for every candidate is safe,
    and the same number printed on a card is a claim about a journey nobody
    measured.
    """

    context = a_context(record=a_match(paid=2))
    engine = MatchFitEngineV1()
    pairing = PairingEngineV1()

    def score_with(travel):
        snapshot = snapshot_for(context, viewer=VIEWER, now=NOW)
        moved = type(snapshot)(
            **{
                **snapshot.__dict__,
                "club": type(snapshot.club)(
                    travel_minutes=travel,
                    zone=snapshot.club.zone,
                    crowding=snapshot.club.crowding,
                ),
            }
        )
        return engine.score(
            snapshot=moved,
            profile=profile_for(uuid4()),
            analysis=pairing.analyse(snapshot=moved, now=NOW),
            now=NOW,
        )

    theirs = score_with(sentinel)
    ours = score_with(TRAVEL_UNMEASURED)

    assert (theirs.fit, theirs.coverage) == (ours.fit, ours.coverage)
    assert [term.value for term in theirs.scored] == [
        term.value for term in ours.scored
    ]


def test_the_sentinel_is_pessimistic_rather_than_flattering() -> None:
    """Zero would be the one value that flatters if the guard above ever failed.

    A suggestion that is quietly too cautious is recoverable; one that is quietly
    too generous is a wasted evening.
    """

    assert TRAVEL_UNMEASURED > 0


def test_a_declared_radius_would_make_the_sentinel_visible() -> None:
    """The negative control: the term *does* read the minutes once a limit exists.

    Without this the property above would pass for a term that reads nothing at
    all, and it would keep passing after somebody deleted the travel term.
    """

    context = a_context(record=a_match(paid=2))
    engine = MatchFitEngineV1()
    pairing = PairingEngineV1()
    snapshot = snapshot_for(context, viewer=VIEWER, now=NOW)
    analysis = pairing.analyse(snapshot=snapshot, now=NOW)
    declared = PlayerProfile(travel_radius=minutes(10))

    near = type(snapshot)(
        **{
            **snapshot.__dict__,
            "club": type(snapshot.club)(
                travel_minutes=minutes(5),
                zone=snapshot.club.zone,
                crowding=snapshot.club.crowding,
            ),
        }
    )

    assert (
        engine.score(snapshot=near, profile=declared, analysis=analysis, now=NOW).fit
        != engine.score(
            snapshot=snapshot, profile=declared, analysis=analysis, now=NOW
        ).fit
    )


# --- 3 · what the assembler states -----------------------------------------


def test_the_phase_is_forming_even_for_a_full_match() -> None:
    """The decision that lets shelf 2 exist at all, stated rather than derived.

    ``MATCH_PHASE_OF`` maps a full match to ``LOCKED`` and ``MatchSnapshot``
    refuses anything but ``FORMING`` — its error message reads *"only a forming
    match is a candidate"*. The projection asks *is this roster fixed*; the guard
    asks *is this a candidate*. Eligibility answers the second, exhaustively and
    before this function runs, so deriving the phase here would make the
    *Full, but worth waiting for* shelf unbuildable for a question already
    answered.
    """

    full = snapshot_for(a_context(record=a_match(paid=4)), viewer=VIEWER, now=NOW)

    assert full.phase is MatchPhase.FORMING


def test_a_cancelled_match_reaching_an_engine_is_loud_rather_than_scored() -> None:
    """The other half of the same decision: the guard still fires.

    Nothing composes a cancelled candidate — eligibility's ``NotCancelled`` runs
    first — but if something ever did, the scorer raises rather than ranking a
    card nobody can join. ``Unscorable`` is the degrade signal, so the shelf
    falls back instead of 500-ing on a home screen.
    """

    cancelled = a_context(record=a_match(paid=1, club_cancelled=True))
    playable = a_context(record=a_match(paid=1))

    # **Before the start**, so the sibling guard cannot answer for this one: a
    # cancelled match two days out is refused for being cancelled and for
    # nothing else, which is what the assertion is about.
    with pytest.raises(Unscorable):
        _scorer().score(cancelled, viewer=VIEWER, now=NOW)
    _scorer().score(playable, viewer=VIEWER, now=NOW)

    # And the other guard on its own, at an instant the first cannot reach.
    with pytest.raises(Unscorable):
        _scorer().score(playable, viewer=VIEWER, now=at(200))


def test_a_clock_reading_with_seconds_in_it_still_scores() -> None:
    """The regression this file could not have caught on its own.

    Every fixture in a unit suite is minute-aligned by construction, and both
    engines refuse a ``now`` carrying seconds — *"a coordinate read off an
    instant carrying seconds is silently one minute early"*. A composed screen's
    clock is ``SystemClock``, which reads microseconds, so before the scorer
    truncated it **every live compose raised**, every raise became an
    ``Unscorable``, and every screen in the product served a degraded shelf with
    nothing on the wire saying so. It took an HTTP case to see it.
    """

    ragged = instant(NOW.replace(second=41, microsecond=576412))

    score, _ = _scorer().score(
        a_context(record=a_match(paid=1)), viewer=VIEWER, now=ragged
    )

    assert 0 <= score.fit <= 100


def test_no_ladder_qualification_is_claimed_for_a_player_in_no_ladder() -> None:
    """A player in none has no ladder problem, which is the constraint rule.

    ``OUTSIDE`` would be the platform docking every match on a ladder nobody has
    entered.
    """

    snapshot = snapshot_for(a_context(record=a_match(paid=1)), viewer=VIEWER, now=NOW)

    assert snapshot.ladder is LadderQualification.NOT_IN_A_LADDER


def test_the_seats_state_and_their_occupants_are_made_to_agree() -> None:
    """The record carries the commitment and the context carries the person.

    The snapshot refuses a seat where the two disagree, so this is the one place
    they are put together.
    """

    context = a_context(
        record=a_match(paid=1, held=1),
        occupants=(rated(300), rated(280), None, None),
    )

    snapshot = snapshot_for(context, viewer=VIEWER, now=NOW)

    assert [seat.state for seat in snapshot.seats] == [
        SeatState.PAID,
        SeatState.HELD,
        SeatState.EMPTY,
        SeatState.EMPTY,
    ]
    assert snapshot.seats[2].occupant is None


def test_an_occupant_on_a_seat_the_record_calls_empty_is_refused() -> None:
    """A caller's bug arrives as one rather than as a count that is quietly wrong."""

    with pytest.raises(InvariantViolated):
        snapshot_for(
            a_context(
                record=a_match(paid=0),
                occupants=(rated(300), None, None, None),
            ),
            viewer=VIEWER,
            now=NOW,
        )


def test_both_instants_are_truncated_to_the_minute_and_stay_ordered() -> None:
    """The snapshot requires minute resolution and nothing upstream rounds.

    Truncation is monotone, so ``join_cutoff <= start`` survives the rounding
    that satisfies its neighbour — the two checks cannot be made to disagree.
    """

    record = a_match(paid=1)
    seconds = type(record)(
        **{**record.__dict__, "start": instant(record.start.replace(second=41))}
    )

    snapshot = snapshot_for(a_context(record=seconds), viewer=VIEWER, now=at(-2880))

    assert snapshot.start.second == 0
    assert snapshot.join_cutoff.second == 0
    assert snapshot.join_cutoff <= snapshot.start


def test_the_hold_crosses_in_the_engines_own_three_value_vocabulary() -> None:
    held = snapshot_for(a_context(record=a_match(paid=2)), viewer=VIEWER, now=NOW)

    assert held.hold in set(CourtHold)


def test_crowding_reaches_the_snapshot_from_the_club_and_is_never_defaulted() -> None:
    """Crowding is **evidence** and multiplies straight into the score.

    Unlike travel, a default here is an empty club — the most flattering answer
    available, and exactly the fabricated observation ADR-0027 exists to remove.
    """

    busy = a_context(record=a_match(paid=1), club=a_club(crowding=ratio(9, 10)))
    quiet = a_context(record=a_match(paid=1), club=a_club(crowding=ratio(1, 10)))
    scorer = _scorer()

    busier, _ = scorer.score(busy, viewer=VIEWER, now=NOW)
    quieter, _ = scorer.score(quiet, viewer=VIEWER, now=NOW)

    assert busier.fit < quieter.fit


# --- 4 · the badge ----------------------------------------------------------


def test_the_badge_is_withheld_from_a_viewer_with_no_rating_in_that_sport() -> None:
    """ADR-0037's rule with its key corrected to a fact about the player.

    An unrated viewer scores 91 at 62 % coverage in a good match, and skill
    overlap is the largest term in the table — so printing 91 is
    flattery-through-absence. **The score still ranks her list.**
    """

    score, analysis = _scorer().score(
        a_context(record=a_match(paid=1)), viewer=unrated(), now=NOW
    )

    assert badge_from(score, analysis, rated=False, travel_measured=False) is None
    assert badge_from(score, analysis, rated=True, travel_measured=False) is not None


def test_a_travel_reason_never_reaches_a_card_while_travel_is_unmeasured() -> None:
    """The sentinel may rank and may not be printed.

    Travel is weight 8 and scores full marks with no declared radius, so it
    reaches the engine's top three by contribution whenever the two largest
    terms score badly — which is every player at the edge of a band, the exact
    population a suggestion matters most to. Left alone, the card would print
    *"90 minutes away"* — the fabricated observation ADR-0027 exists to remove,
    arriving through a reason line instead of through a score.
    """

    score, analysis = _scorer().score(_MISMATCHED, viewer=rated(100), now=NOW)
    badge = badge_from(score, analysis, rated=True, travel_measured=False)

    assert badge is not None
    assert TermCode.TRAVEL not in {reason.code for reason in badge.reasons}


def test_the_travel_reason_returns_the_day_travel_has_a_source() -> None:
    """The negative control: withheld rather than deleted.

    Without this, removing the travel term from the engine entirely would leave
    the test above green — and the suppression would be indistinguishable from
    the term never having existed.
    """

    score, analysis = _scorer().score(_MISMATCHED, viewer=rated(100), now=NOW)
    measured = badge_from(score, analysis, rated=True, travel_measured=True)
    withheld = badge_from(score, analysis, rated=True, travel_measured=False)

    assert measured is not None and withheld is not None
    assert TermCode.TRAVEL in {reason.code for reason in measured.reasons}
    assert len(withheld.reasons) < len(measured.reasons)


def test_the_badge_carries_at_most_three_reasons() -> None:
    score, analysis = _scorer().score(
        a_context(record=a_match(paid=1)), viewer=VIEWER, now=NOW
    )
    badge = badge_from(score, analysis, rated=True, travel_measured=False)

    assert badge is not None
    assert len(badge.reasons) <= REASON_CAP
    assert REASON_CAP == 3


def test_the_reasons_are_the_engines_own_term_objects() -> None:
    """Asserted with ``is``, so a card cannot show a reason computed elsewhere."""

    score, analysis = _scorer().score(
        a_context(record=a_match(paid=1)), viewer=VIEWER, now=NOW
    )
    badge = badge_from(score, analysis, rated=True, travel_measured=False)

    assert badge is not None
    facts = [reason.fact for reason in badge.reasons]
    assert all(any(fact is term.fact for term in score.reasons) for fact in facts)


def test_the_warning_is_the_engines_and_its_threshold_is_never_respelled() -> None:
    """``unsure`` restates the engine's warning rather than re-deriving it.

    The threshold — 0,40 on the *raw* value of the lowest contributor — lives in
    ``matchfit/v1/constants.py``, so a retune moves the card and the score
    together.
    """

    quiet, analysis = _scorer().score(
        a_context(record=a_match(paid=1)), viewer=VIEWER, now=NOW
    )
    loud, mismatch = _scorer().score(_MISMATCHED, viewer=rated(100), now=NOW)

    # A match aimed four Levels above her: skill overlap scores a raw 0,0, which
    # is under the engine's 0,40 and is what a warning is *for*.
    assert loud.warning is not None and float(loud.warning.value) < 0.40
    assert quiet.warning is None

    assert badge_from(loud, mismatch, rated=True, travel_measured=False).unsure
    assert not badge_from(quiet, analysis, rated=True, travel_measured=False).unsure


def test_no_coverage_reaches_the_badge_in_any_form() -> None:
    """It ranks, it gates emphasis, and it never becomes a second gauge."""

    score, analysis = _scorer().score(
        a_context(record=a_match(paid=1)), viewer=VIEWER, now=NOW
    )
    badge = badge_from(score, analysis, rated=True, travel_measured=False)

    assert badge is not None
    assert not hasattr(badge, "coverage")
    assert "coverage" not in {field.name for field in fields(Fit)}


def test_the_badge_is_inside_the_pill_range_for_every_shape_of_match() -> None:
    scorer = _scorer()
    for paid in range(5):
        score, analysis = scorer.score(
            a_context(record=a_match(paid=paid)), viewer=VIEWER, now=NOW
        )
        badge = badge_from(score, analysis, rated=True, travel_measured=False)
        assert badge is not None
        assert BADGE_FLOOR <= badge.score <= BADGE_CEILING


def test_a_match_type_preference_is_never_assumed() -> None:
    """The source design hard-coded a preference for counted matches."""

    assert profile_for(uuid4()).match_type is None
    assert MatchTypePreference.COMPETITIVE not in {profile_for(uuid4()).match_type}


def test_a_snapshot_reads_the_sport_off_the_record_and_never_a_filter() -> None:
    tennis = snapshot_for(
        a_context(record=a_match(sport=Sport.TENNIS, paid=1)), viewer=VIEWER, now=NOW
    )

    assert tennis.sport is Sport.TENNIS
    assert len(tennis.seats) == 2
