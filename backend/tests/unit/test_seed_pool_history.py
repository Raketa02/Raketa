"""The third played-history list: **every face in her pool carries a record.**

The cohort's own history reaches *card states* and hers fills *her* sheet; this one
exists
so a developer can tap any face and get a filled record without playing a game or
answering
a card by hand. What is asserted here is what a reader of the fixture would otherwise
have
to take on trust — that it stayed inside the world as drawn, and that the two faces it
leaves empty are left empty on purpose.
"""

from __future__ import annotations

import pytest

from app.kernel import Sport
from app.modules.challenges.domain.seats import seats_per_side
from app.seeds.catalog import THE_BLANK_WEEK_PLAYER, THE_NEWCOMER
from app.seeds.cohort import (
    COHORT,
    PLAYED_GAMES,
    PROTAGONIST_GAMES,
    PROTAGONIST_HANDLE,
    RATED_WITHIN_DAYS,
)
from app.seeds.cohort import GHOSTED_AT_LEAST_DAYS_AGO
from app.seeds.pool_history import (
    THE_POOL_HAS_A_RECORD,
    THE_RATEABLE_WEEK,
    THE_RECORD_GOES_BACK,
    THE_RECORD_GOES_BACK_DAYS,
    WHAT_THE_POOL_SAID,
    address_of,
    handle_of,
)


def test_every_court_seats_what_its_sport_seats():
    """A line-up completes only when **every** seat is accepted, so a padel court one
    short of four opens no game at all."""

    for game in THE_POOL_HAS_A_RECORD:
        per_side = seats_per_side(Sport(game.sport))
        assert len(game.side_a) == per_side, game
        assert len(game.side_b) == per_side, game


def test_the_organiser_is_hers_or_a_ring_s_own_or_a_member_against_her():
    """**The three searches that cannot fill before they find everybody named.**

    A padel court seats three people and a shortlist stops at twenty. Hers provably
    returns her whole pool; a member searching at the slider's floor sees their own ring
    at nought kilometres and nobody from the centre. The third arm is the second one's
    argument rather than an exception to it: what the rule asserts is *this organiser's
    shortlist provably returns these seats*, and a cohort member reaching **her** is the
    one other thing this fixture already proves — every row in `PROTAGONIST_GAMES` is a
    member organising a singles court against her. `cohort-c-00` is why it is needed:
    their own shortlist returns one face from their ring, which cannot fill a doubles
    court, and returns her on every search they run.
    """

    for game in THE_POOL_HAS_A_RECORD:
        if game.organiser == PROTAGONIST_HANDLE:
            continue
        assert game.organiser.startswith("cohort-"), game
        if set(game.players[1:]) == {PROTAGONIST_HANDLE}:
            continue
        ring = game.organiser.split("-")[1]
        for handle in game.players[1:]:
            assert handle.startswith(f"cohort-{ring}-"), (game.organiser, handle)


def test_nobody_plays_twice_on_one_evening_across_all_three_lists():
    """*Last 5* is ordered on the instant each game was played, so two games at one
    instant leave the run to a tie-break on a uuid — a row of squares that reshuffles
    between databases. The three lists are one calendar."""

    days: dict[str, set[int]] = {}
    for game in (*PLAYED_GAMES, *PROTAGONIST_GAMES, *THE_POOL_HAS_A_RECORD):
        for handle in game.players:
            assert game.played_days_ago not in days.setdefault(handle, set()), handle
            days[handle].add(game.played_days_ago)


def test_the_rateable_week_is_inside_the_card_s_week_and_the_rest_is_not():
    """**The split is the layer, and each half buys a different thing** (#384).

    A court inside the card's week buys **stars**; a court outside it buys a **record**
    and no stars. Both are wanted and they pull in opposite directions: *Last 5* draws
    one square per counted result and nobody may play twice on a day, so seven usable
    days is a ceiling of seven results — and the protagonist, whose search is the only
    one that reaches her whole pool, was booked on every one of them by her own tennis
    history before this list existed.
    """

    for game in THE_RATEABLE_WEEK:
        assert game.played_days_ago <= RATED_WITHIN_DAYS, game

    for game in THE_RECORD_GOES_BACK:
        assert game.played_days_ago <= THE_RECORD_GOES_BACK_DAYS, game

    assert THE_POOL_HAS_A_RECORD == (*THE_RATEABLE_WEEK, *THE_RECORD_GOES_BACK)


def test_a_ghost_is_only_declared_once_its_entry_window_has_closed():
    """A plan is a ghost when the entry window shuts on silence, and not before. Sooner
    than that the platform still calls it `AWAITING_ENTRY`, so **nothing would fail** and
    the record would simply be wrong — which is what a typed seven already did once.

    It is also why there is no ghost in the week above: the floor is one day past the
    whole window that list fits inside.
    """

    for game in THE_POOL_HAS_A_RECORD:
        if game.was_a_ghost:
            assert game.played_days_ago >= GHOSTED_AT_LEAST_DAYS_AGO, game

    assert not any(game.was_a_ghost for game in THE_RATEABLE_WEEK)
    assert any(game.was_a_ghost for game in THE_RECORD_GOES_BACK)


def test_all_three_bad_endings_are_drawn_so_no_strand_is_a_full_bar():
    """A pool where every strand publishes 100% has one colour in it, and the ladder that
    tints every bar is never drawn against anything.

    Three endings do the work and each moves a different figure. An **unanswered** score
    still confirms by silence, so *Last 5* keeps its square and *answers about results*
    takes the dock. A **ghost** produces no game at all and is the one bad outcome on
    *shows up*. And a game **nobody agreed** is an evening rather than evidence: it moves
    *Counted* and leaves *Last 5* alone, which is what makes those two blocks read as
    different figures on one face.
    """

    unanswered = [
        game for game in THE_POOL_HAS_A_RECORD if game.was_scored and not game.answered
    ]
    ghosts = [game for game in THE_POOL_HAS_A_RECORD if game.was_a_ghost]
    unagreed = [
        game
        for game in THE_POOL_HAS_A_RECORD
        if not game.was_a_ghost and not game.was_scored
    ]

    assert unanswered, [game.answered for game in THE_POOL_HAS_A_RECORD]
    assert ghosts, [game.entered for game in THE_POOL_HAS_A_RECORD]
    assert unagreed, [game.won_by for game in THE_POOL_HAS_A_RECORD]


def test_somebody_plays_twice_so_variety_is_not_a_flat_hundred():
    """*Opponent variety* is distinct people over counted games. Where no pair ever
    plays
    twice it publishes 100% for everybody and the row proves nothing."""

    counted: dict[str, int] = {}
    for game in THE_POOL_HAS_A_RECORD:
        for handle in game.players:
            counted[handle] = counted.get(handle, 0) + 1

    assert any(
        played > 1 for handle, played in counted.items() if handle != PROTAGONIST_HANDLE
    ), counted


@pytest.mark.parametrize(
    "account", [THE_NEWCOMER, THE_BLANK_WEEK_PLAYER], ids=lambda one: one.slug
)
def test_the_two_faces_it_leaves_empty_stay_empty(account):
    """**Both absences are load-bearing.**

    `the-newcomer` committed inside the window, and a brand-new account with a full
    record is a lie about how a record accumulates — it is also the *absent* card
    `screens.py` requires, and this layer leaves no other. `the-blank-week-player`
    cleared their week, so her search never returns them and no same-ring organiser
    reaches the centre they sit on.
    """

    played = {handle for game in THE_POOL_HAS_A_RECORD for handle in game.players}

    assert account.slug not in played


def test_nobody_is_rated_by_somebody_they_never_played():
    """A card is drawn for an evening, so a rating with no court behind it is one the
    use
    case would refuse mid-run."""

    together: dict[str, set[str]] = {}
    for game in THE_POOL_HAS_A_RECORD:
        for pair in game.pairs:
            one, other = sorted(pair)
            together.setdefault(one, set()).add(other)
            together.setdefault(other, set()).add(one)

    for subject, said in WHAT_THE_POOL_SAID.items():
        for rater in said:
            assert rater in together.get(subject, set()), (rater, subject)


def test_what_was_said_spans_the_scale_and_the_counts():
    """A pool where every figure is 5,0 over one rater teaches a reader nothing about
    the
    field it is meant to be developed against."""

    figures = [sum(said.values()) / len(said) for said in WHAT_THE_POOL_SAID.values()]
    counts = {len(said) for said in WHAT_THE_POOL_SAID.values()}

    assert min(figures) < 2.0 and max(figures) >= 5.0, sorted(figures)
    assert len(counts) > 1, counts


def test_a_handle_resolves_from_any_of_the_three_populations():
    """One resolver, because a declaration names people by handle and does not know
    which
    list they came out of."""

    for handle in ("cohort-a-05", PROTAGONIST_HANDLE, "said-yes-to-you"):
        address = address_of(handle, COHORT)
        assert address.endswith("@raketa.example"), address
        assert handle_of(address, COHORT) == handle


def test_a_handle_nobody_carries_is_refused_by_name():
    """A typo in a declaration is a court that cannot be built, and the message says
    which
    name rather than which uuid."""

    with pytest.raises(RuntimeError, match="none of the three"):
        address_of("cohort-z-99".replace("cohort-", "nobody-"), COHORT)
