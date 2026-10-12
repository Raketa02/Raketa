"""The group deck as one reader is dealt it — the pure rules (#539; the mechanics
§6.6, §7, §8; the screens A2).

**Who is on my card** is my version: everybody In, me, and the rest of my
version's names for the seats still open, in the order they were dealt. A card is
withheld when somebody In is somebody I do not fit, and a name I do not fit is
left off it — two people who may not share a court are never on one card.

**The sides** are the most even arrangement the engine forecasts, with me on my
own side; **the order** is the mechanics §8.2's four keys; **the same people**
are dealt at their best hour only; and **a week at its cap** deals nothing.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.proposals.domain.deck import (
    CardForecast,
    CardType,
    CourtState,
    DeckCard,
    Sides,
    arrangements,
    capped_weeks,
    card_type,
    cut_off_passed,
    dealt_in_order,
    evenest,
    hour_taken,
    standing_for,
    view_of,
    week_of,
    weeks_ahead,
)
from app.modules.proposals.domain.overlap import (
    DayRange,
    GameCell,
    Overlap,
    OverlapGrade,
)
from app.modules.player_profile.domain.gender import Gender
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import Who, stand_together
from app.modules.proposals.domain.proposal import Origin, Proposal

WARSAW = ZoneInfo("Europe/Warsaw")
MADE_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
NOW = MADE_AT + timedelta(hours=1)
START = instant(datetime(2026, 10, 10, 17, tzinfo=WARSAW))

ME, A, B, C, D, E, F, G = (uuid4() for _ in range(8))


def a_pick(*versions: tuple[UUID, ...], sport: Sport = Sport.PADEL) -> Proposal:
    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.PICK,
        poster_id=None,
        sport=sport,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=30_00,
        book_by=START - timedelta(hours=2),
        at=MADE_AT,
    )
    for version in versions:
        proposal.deal(version, at=MADE_AT)
    return proposal


def a_post(poster: UUID, *versions: tuple[UUID, ...]) -> Proposal:
    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.POST,
        poster_id=poster,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=30_00,
        book_by=START - timedelta(hours=2),
        at=MADE_AT,
    )
    for version in versions:
        proposal.deal(version, at=MADE_AT)
    return proposal


EVERYBODY = frozenset({ME, A, B, C, D, E, F, G})


def unfit(*pairs: tuple[UUID, UUID]) -> frozenset[frozenset[UUID]]:
    return frozenset(frozenset(pair) for pair in pairs)


def view(proposal: Proposal, *, unfit=frozenset(), pool=EVERYBODY):
    return view_of(proposal, ME, unfit=unfit, in_the_pool=pool, now=NOW)


# --------------------------------------------------------------------------- #
# Who is on my card
# --------------------------------------------------------------------------- #


def test_my_card_is_everybody_in_then_me_then_my_version_in_dealt_order():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(B, at=NOW)

    seen = view(pick)

    assert seen is not None
    assert seen.in_ == (B,)
    assert seen.others == (A, C)
    assert seen.people == (B, ME, A, C)


def test_the_people_in_on_another_version_are_on_my_card_too():
    post = a_post(G, (ME, A, B), (C, D, E))
    post.say_yes(C, at=NOW)

    seen = view(post)

    assert seen is not None
    assert seen.in_ == (G, C)
    # Two seats open besides mine: the first name of my version fills it.
    assert seen.others == (A,)


def test_the_next_best_fits_dealt_after_a_no_come_after_the_names_before_them():
    pick = a_pick((ME, A, B, C))
    pick.say_no(A, at=NOW)
    pick.deal((D, E, F), at=NOW, into=1)

    seen = view(pick)

    # Three seats besides mine: the two names left, then the first fit dealt.
    assert seen is not None
    assert seen.others == (B, C, D)


def test_a_player_who_took_their_yes_back_is_on_the_card_without_being_in():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)
    pick.withdraw_yes(A, at=NOW)

    seen = view(pick)

    assert seen is not None
    assert seen.in_ == ()
    assert seen.others == (A, B, C)


def test_a_card_i_took_my_yes_back_from_is_dealt_to_me_again():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)
    pick.withdraw_yes(ME, at=NOW)

    assert view(pick) is not None


@pytest.mark.parametrize(
    "answer",
    ["no", "yes"],
    ids=["a card I said no to never returns", "a card I am In on is in Fill in"],
)
def test_a_card_i_answered_is_not_in_my_deck(answer):
    pick = a_pick((ME, A, B, C))
    getattr(pick, f"say_{answer}")(ME, at=NOW)

    assert view(pick) is None


def test_a_game_never_dealt_to_me_is_not_in_my_deck():
    assert view(a_pick((A, B, C, D))) is None


def test_a_full_game_is_not_dealt():
    pick = a_pick((ME, A, B, C), (D,))
    for player in (A, B, C, D):
        pick.say_yes(player, at=NOW)

    assert view(pick) is None


def test_a_game_past_its_book_by_is_not_dealt():
    pick = a_pick((ME, A, B, C))

    assert (
        view_of(
            pick,
            ME,
            unfit=frozenset(),
            in_the_pool=EVERYBODY,
            now=pick.book_by,
        )
        is None
    )


def test_a_card_with_somebody_in_i_do_not_fit_is_withheld():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)

    assert view(pick, unfit=unfit((ME, A))) is None


def test_a_pair_in_that_stopped_fitting_is_not_mine_to_hide():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)
    pick.say_yes(B, at=NOW)

    seen = view(pick, unfit=unfit((A, B)))

    assert seen is not None
    assert seen.in_ == (A, B)


def test_a_name_i_do_not_fit_is_left_off_and_the_next_one_takes_the_tile():
    pick = a_pick((ME, A, B, C))
    pick.say_no(C, at=NOW)
    pick.deal((D,), at=NOW, into=1)

    seen = view(pick, unfit=unfit((ME, B)))

    assert seen is not None
    assert seen.others == (A, D)


def test_a_name_who_does_not_fit_somebody_in_is_left_off():
    # Two people who may not share a court are never on one card — mine
    # included, when the pair is not me.
    post = a_post(G, (ME, A, B), (C, D, E))
    post.say_yes(C, at=NOW)

    seen = view(post, unfit=unfit((A, C)))

    assert seen is not None
    assert seen.in_ == (G, C)
    assert seen.others == (B,)


def test_a_name_who_does_not_fit_a_name_before_them_is_left_off():
    pick = a_pick((ME, A, B, C))

    seen = view(pick, unfit=unfit((A, B)))

    assert seen is not None
    assert seen.others == (A, C)


def test_a_name_who_left_the_pool_is_left_off():
    seen = view(a_pick((ME, A, B, C)), pool=EVERYBODY - {B})

    assert seen is not None
    assert seen.others == (A, C)


def test_a_card_that_would_show_nobody_but_me_is_not_dealt():
    assert view(a_pick((ME, A)), unfit=unfit((ME, A))) is None


def test_a_post_is_a_challenge_and_a_pick_is_picked_for_you():
    assert card_type(a_post(G, (ME,))) is CardType.CHALLENGE
    assert card_type(a_pick((ME, A))) is CardType.PICKED_FOR_YOU


# --------------------------------------------------------------------------- #
# The sides
# --------------------------------------------------------------------------- #


def test_three_others_are_three_arrangements_with_me_on_my_own_side():
    assert arrangements(ME, (A, B, C), seats_per_side=2) == (
        Sides(yours=(ME, A), theirs=(B, C)),
        Sides(yours=(ME, B), theirs=(A, C)),
        Sides(yours=(ME, C), theirs=(A, B)),
    )


def test_an_empty_seat_is_one_of_the_positions():
    assert arrangements(ME, (A, B), seats_per_side=2) == (
        Sides(yours=(ME, A), theirs=(B,)),
        Sides(yours=(ME, B), theirs=(A,)),
        Sides(yours=(ME,), theirs=(A, B)),
    )


def test_one_other_on_a_doubles_card_faces_me():
    assert arrangements(ME, (A,), seats_per_side=2) == (
        Sides(yours=(ME,), theirs=(A,)),
    )


def test_singles_is_one_arrangement():
    assert arrangements(ME, (A,), seats_per_side=1) == (
        Sides(yours=(ME,), theirs=(A,)),
    )


def test_the_evenest_forecast_wins_and_a_tie_keeps_the_first():
    options = arrangements(ME, (A, B, C), seats_per_side=2)

    chosen, forecast = evenest(
        options,
        [
            CardForecast(pct=81, provisional=False),
            CardForecast(pct=93, provisional=False),
            CardForecast(pct=93, provisional=False),
        ],
    )

    assert chosen == options[1]
    assert forecast == CardForecast(pct=93, provisional=False)


def test_with_no_forecast_the_first_arrangement_is_drawn_and_nothing_is_said():
    options = arrangements(ME, (A, B, C), seats_per_side=2)

    assert evenest(options, [None, None, None]) == (options[0], None)


# --------------------------------------------------------------------------- #
# The order
# --------------------------------------------------------------------------- #


def a_card(
    *,
    open_after: int,
    type_: CardType = CardType.PICKED_FOR_YOU,
    deadline_hours: int = 48,
    pct: int | None = 80,
    people: tuple[UUID, ...] | None = None,
    start: datetime = START,
) -> DeckCard:
    others = people if people is not None else tuple(uuid4() for _ in range(3))
    return DeckCard(
        proposal_id=uuid4(),
        type=type_,
        kind=SearchMode.COMPETITIVE,
        challenger_id=None,
        club_id=uuid4(),
        start=instant(start),
        share_grosze=30_00,
        deadline=NOW + timedelta(hours=deadline_hours),
        in_=(),
        sides=Sides(yours=(ME, others[0]), theirs=others[1:]),
        forecast=None if pct is None else CardForecast(pct=pct, provisional=False),
        overlap=Overlap(
            grade=OverlapGrade.GOOD,
            cells=(),
            game=GameCell(day=6, range=DayRange.EVENING),
        ),
        open_seats_after_your_yes=open_after,
        version_count=1,
        no_free_cancellation=False,
    )


def test_fewest_seats_open_after_my_yes_come_first():
    three, nought, one = (
        a_card(open_after=3),
        a_card(open_after=0),
        a_card(open_after=1),
    )

    assert dealt_in_order([three, nought, one]) == (nought, one, three)


def test_at_the_same_momentum_a_seat_open_then_a_challenge_then_a_pick():
    pick = a_card(open_after=1)
    challenge = a_card(open_after=1, type_=CardType.CHALLENGE)
    rescue = a_card(open_after=1, type_=CardType.SEAT_OPEN)

    assert dealt_in_order([pick, challenge, rescue]) == (rescue, challenge, pick)


def test_then_the_soonest_deadline_then_the_best_fit():
    later = a_card(open_after=2, deadline_hours=72, pct=95)
    sooner = a_card(open_after=2, deadline_hours=24, pct=60)
    sooner_better = a_card(open_after=2, deadline_hours=24, pct=90)
    sooner_unknown = a_card(open_after=2, deadline_hours=24, pct=None)

    assert dealt_in_order([later, sooner_unknown, sooner, sooner_better]) == (
        sooner_better,
        sooner,
        sooner_unknown,
        later,
    )


def test_the_same_people_are_dealt_only_at_their_best_hour():
    people = (A, B, C)
    best = a_card(open_after=1, people=people)
    same_later = a_card(
        open_after=2, people=people, start=datetime(2026, 10, 11, 18, tzinfo=WARSAW)
    )
    other = a_card(open_after=3)

    assert dealt_in_order([same_later, other, best]) == (best, other)


def test_the_court_block_says_book_it_now_when_my_yes_fills_the_game():
    assert a_card(open_after=0).court is CourtState.BOOK_IT_NOW
    assert a_card(open_after=1).court is CourtState.COURT_AVAILABLE


# --------------------------------------------------------------------------- #
# Weeks, the cut-off, and an hour already taken
# --------------------------------------------------------------------------- #


def test_a_week_runs_monday_to_sunday_on_the_club_s_clock():
    sunday_late = instant(datetime(2026, 10, 11, 22, tzinfo=WARSAW))
    monday_early = instant(datetime(2026, 10, 12, 7, tzinfo=WARSAW))

    assert week_of(sunday_late) == date(2026, 10, 5)
    assert week_of(monday_early) == date(2026, 10, 12)


def test_the_deck_looks_fourteen_days_ahead_week_by_week():
    monday_morning = instant(datetime(2026, 10, 5, 8, tzinfo=WARSAW))

    assert weeks_ahead(monday_morning) == (
        date(2026, 10, 5),
        date(2026, 10, 12),
        date(2026, 10, 19),
    )


def test_a_week_with_as_many_games_booked_as_the_player_allows_is_capped():
    weeks = (date(2026, 10, 5), date(2026, 10, 12))
    booked = [
        instant(datetime(2026, 10, 6, 19, tzinfo=WARSAW)),
        instant(datetime(2026, 10, 8, 19, tzinfo=WARSAW)),
        instant(datetime(2026, 10, 13, 19, tzinfo=WARSAW)),
    ]

    capped = capped_weeks(weeks, booked, games_per_week=2)

    assert [(week.starts_on, week.booked) for week in capped] == [
        (date(2026, 10, 5), 2)
    ]


def test_an_hour_with_a_game_already_is_taken():
    booked = [instant(datetime(2026, 10, 10, 17, 30, tzinfo=WARSAW))]

    assert hour_taken(START, booked)
    assert not hour_taken(START + timedelta(hours=2), booked)


def test_no_free_cancellation_once_the_club_s_cut_off_has_passed():
    assert not cut_off_passed(START, cut_off_hours=24, now=START - timedelta(hours=25))
    assert cut_off_passed(START, cut_off_hours=24, now=START - timedelta(hours=24))
    assert not cut_off_passed(START, cut_off_hours=0, now=START - timedelta(minutes=1))


# --------------------------------------------------------------------------- #
# Mixed pairs (#546)
# --------------------------------------------------------------------------- #

GENDERS = {
    ME: Gender.MAN,
    A: Gender.MAN,
    B: Gender.MAN,
    C: Gender.WOMAN,
    D: Gender.WOMAN,
}


def two_of_each(people) -> bool:
    return stand_together(Who.MIXED_PAIRS, GENDERS, people, seats=4)


def test_a_mixed_pairs_card_is_withheld_from_a_third_of_one_gender():
    post = a_post(D, (ME, A, C))
    post.say_yes(A, at=NOW)
    post.deal((B,), at=NOW)
    post.say_yes(B, at=NOW)

    assert (
        view_of(
            post,
            ME,
            unfit=frozenset(),
            in_the_pool=EVERYBODY,
            now=NOW,
            may_stand=two_of_each,
        )
        is None
    )


def test_a_name_a_mixed_pairs_card_has_no_seat_for_is_left_off():
    post = a_post(D, (ME, A, B))
    post.deal((E,), at=NOW, into=1)
    genders = {**GENDERS, E: Gender.WOMAN}

    seen = view_of(
        post,
        ME,
        unfit=frozenset(),
        in_the_pool=EVERYBODY | {E},
        now=NOW,
        may_stand=lambda people: stand_together(
            Who.MIXED_PAIRS, genders, people, seats=4
        ),
    )

    assert seen is not None
    # D and me a woman and a man; A is the other man; B would be a third.
    assert seen.others == (A, E)


def test_a_mixed_pairs_game_stands_a_man_and_a_woman_a_side():
    options = arrangements(ME, (C, A, D), seats_per_side=2)

    kept = standing_for(options, who=Who.MIXED_PAIRS, genders=GENDERS)

    assert kept == (
        Sides(yours=(ME, C), theirs=(A, D)),
        Sides(yours=(ME, D), theirs=(C, A)),
    )
    assert standing_for(options, who=Who.ANYONE, genders=GENDERS) == options
    assert standing_for(options, who=None, genders={}) == options
