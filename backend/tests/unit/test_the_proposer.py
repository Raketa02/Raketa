"""The proposer — the pure seam beside Match Fit (#540; the mechanics §4.3, §5,
§6.2–§6.3, §7, §19; the screens C3).

**Members, weekly hours, levels, intents, the pair rule and free court hours in;
the games it builds, the seats it deals and the cards that lost their court out.**
Nothing here reads a database: every fact a batch needs is handed in, and every
answer is a value — so the rules are asserted here, one at a time, and the job
that runs them is asserted over HTTP.

Four families:

**Evenness and fit.** A court hour is dealt the most even four (or two) of the
members who are rated in its sport, want its kind, are free for the whole hour,
can afford it, have no game then and a week to spare — and who fit every pair
among them. *Most even* is the engine's own forecast.

**Courts.** A player group's home club first, then the other clubs it plays
at; an official group only its own club, unless the club lets others' courts
serve players who share no hour at its own. Fourteen days ahead, never a paused
club, and never the same people twice in one batch — of either kind.

**Dealing.** After a no, the seat goes to up to three next best fits — one in
singles, where each fit is a version; at half its seats In, a pick's
unanswered seats go out as new versions — at most three.

**A lost court hour.** A card whose last court at its club and hour went is
lost — never one whose court is there and whose club merely moved its deadline
— and the people who were In on it are dealt a new card first.

**A full game still filling** holds no court: it is lost with its court as any
card is, and is the card on its court while it fills. **A booked game its club
cancelled** is owed: the people still in are dealt a new card first, the
closest to it first (#547, #673; Q123) — the same club and hour, then, for a
player group, another club at that hour, then the closest hour — and the card
records whom it is owed to.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, instant
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.proposals.domain.proposer import (
    Batch,
    CourtHourOnSale,
    Deal,
    Member,
    Pick,
    PoolClubs,
    propose,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int, minute: int = 0) -> Instant:
    """An hour in Kraków in October 2026. The fifth is a Monday."""

    return instant(datetime(2026, 10, day, hour, minute, tzinfo=WARSAW))


NOW = warsaw(5, 8)
SAT_17 = warsaw(10, 17)
SAT_18 = warsaw(10, 18)
SUN_17 = warsaw(11, 17)

#: Every evening hour of the week, 17:00–22:00.
EVENINGS = tuple((day, hour) for day in range(1, 8) for hour in range(17, 23))

HOME, NEAR, FARTHER = (uuid4() for _ in range(3))
POOL = Pool(id=uuid4(), kind=PoolKind.GROUP)
COMPETITIVE = frozenset({SearchMode.COMPETITIVE})

A, B, C, D, E, F, G, H, K, J = (uuid4() for _ in range(10))
NAMES = {A: "A", B: "B", C: "C", D: "D", E: "E", F: "F", G: "G", H: "H"}
NAMES.update({K: "K", J: "J"})


def member(
    player: UUID,
    level: float | None = 3.0,
    *,
    cells: tuple[tuple[int, int], ...] = EVENINGS,
    wants: frozenset[SearchMode] = COMPETITIVE,
    games_per_week: int = 2,
    most_ill_pay_grosze: int | None = None,
    booked: tuple[Instant, ...] = (),
) -> Member:
    return Member(
        player_id=player,
        level=None if level is None else LevelReading(mu=level, sigma=0.4),
        week=WeeklyHours.of_cells(cells),
        wants=wants,
        limits=GamesAndMoney(
            player_id=player,
            games_per_week=games_per_week,
            most_ill_pay_grosze=most_ill_pay_grosze,
        ),
        booked=booked,
    )


def on_sale(
    start: Instant,
    club: UUID = HOME,
    *,
    sport: Sport = Sport.PADEL,
    courts: int = 1,
    share_grosze: int = 30_00,
    taking_new_cards: bool = True,
) -> CourtHourOnSale:
    return CourtHourOnSale(
        club_id=club,
        sport=sport,
        start=start,
        courts=courts,
        share_grosze=share_grosze,
        book_by=start - timedelta(hours=2),
        taking_new_cards=taking_new_cards,
    )


def unfit(*pairs: tuple[UUID, UUID]) -> dict[SearchMode, frozenset[frozenset[UUID]]]:
    mask = frozenset(frozenset(pair) for pair in pairs)
    return {kind: mask for kind in SearchMode}


def batch(
    members: list[Member],
    hours: list[CourtHourOnSale],
    *,
    clubs: PoolClubs = PoolClubs(home_club_id=HOME),
    mask: dict[SearchMode, frozenset[frozenset[UUID]]] | None = None,
    filling: tuple[Proposal, ...] = (),
    held: list[tuple[UUID, Instant]] | None = None,
    owed: tuple[Proposal, ...] = (),
    sport: Sport = Sport.PADEL,
    now: Instant = NOW,
) -> Batch:
    return propose(
        sport=sport,
        members=members,
        unfit=mask if mask is not None else unfit(),
        clubs=clubs,
        hours=hours,
        held=held
        if held is not None
        else [(hour.club_id, hour.start) for hour in hours],
        filling=filling,
        owed=owed,
        balance=LIVE_RULESET.balance,
        now=now,
    )


def a_pick(
    *named: UUID,
    start: Instant = SAT_17,
    club: UUID = HOME,
    sport: Sport = Sport.PADEL,
) -> Proposal:
    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=POOL,
        origin=Origin.PICK,
        poster_id=None,
        sport=sport,
        kind=SearchMode.COMPETITIVE,
        club_id=club,
        start=start,
        share_grosze=30_00,
        book_by=start - timedelta(hours=2),
        at=NOW - timedelta(hours=1),
    )
    proposal.deal(named, at=NOW - timedelta(hours=1))
    return proposal


def people(pick: Pick) -> set[str]:
    return {NAMES[player] for player in pick.named}


def four_even_and_one_apart() -> list[Member]:
    return [
        member(A, 3.0),
        member(B, 3.0),
        member(C, 3.0),
        member(D, 3.0),
        member(E, 3.5),
    ]


# --------------------------------------------------------------------------- #
# Evenness and fit
# --------------------------------------------------------------------------- #


def test_a_court_hour_is_dealt_the_most_even_four_of_the_members_free_for_it():
    dealt = batch([member(E, 3.5), *four_even_and_one_apart()[:4]], [on_sale(SAT_17)])

    assert dealt.picks == (
        Pick(
            kind=SearchMode.COMPETITIVE,
            club_id=HOME,
            start=SAT_17,
            named=(A, B, C, D),
        ),
    )
    assert dealt.lost == dealt.deals == ()


def test_a_tie_on_the_forecast_goes_to_the_closest_levels():
    # Both fours forecast as even as a game can be; one of them is four
    # people at one level, the other two pairs a step apart.
    dealt = batch(
        [
            member(A, 3.0),
            member(B, 3.2),
            member(C, 3.0),
            member(D, 3.2),
            member(E, 3.1),
            member(F, 3.1),
        ],
        [on_sale(SAT_17)],
        mask=unfit((A, E), (C, F)),
    )

    assert [people(pick) for pick in dealt.picks] == [{"B", "D", "E", "F"}]


def test_somebody_free_for_only_part_of_the_hour_is_not_on_the_card():
    half_past = warsaw(10, 17, 30)
    only_the_start = member(A, cells=((6, 17),))
    both_hours = [member(p, cells=((6, 17), (6, 18))) for p in (B, C, D, E)]

    dealt = batch([only_the_start, *both_hours], [on_sale(half_past)])

    assert [people(pick) for pick in dealt.picks] == [{"B", "C", "D", "E"}]


def test_two_people_who_may_not_share_a_court_are_never_on_one_card():
    dealt = batch(four_even_and_one_apart(), [on_sale(SAT_17)], mask=unfit((A, B)))

    # Without A and B together, the evenest four holds E.
    (pick,) = dealt.picks
    assert not {A, B} <= set(pick.named)
    assert E in pick.named


def test_a_card_is_dealt_only_to_people_who_want_its_kind():
    for_fun = frozenset({SearchMode.FOR_FUN})
    either = frozenset(SearchMode)
    dealt = batch(
        [
            member(A, wants=either),
            member(B, wants=either),
            member(C, wants=either),
            member(D, wants=for_fun),
            member(E, wants=COMPETITIVE),
            member(F, wants=frozenset()),
        ],
        [on_sale(SAT_17), on_sale(SUN_17)],
    )

    # Saturday's one court goes to the Competitive four; A, B and C, on it,
    # are dealt For fun on Sunday rather than a second card that hour.
    assert [(pick.kind, pick.start, people(pick)) for pick in dealt.picks] == [
        (SearchMode.COMPETITIVE, SAT_17, {"A", "B", "C", "E"}),
        (SearchMode.FOR_FUN, SUN_17, {"A", "B", "C", "D"}),
    ]


def test_the_same_people_are_never_dealt_both_kinds_in_one_batch():
    either = frozenset(SearchMode)

    dealt = batch(
        [member(player, wants=either) for player in (A, B, C, D)],
        [on_sale(SAT_17, courts=2), on_sale(SUN_17)],
    )

    assert [(pick.kind, pick.start) for pick in dealt.picks] == [
        (SearchMode.COMPETITIVE, SAT_17)
    ]


def test_somebody_not_rated_in_the_sport_is_dealt_nothing():
    dealt = batch([member(A, None), *four_even_and_one_apart()[1:]], [on_sale(SAT_17)])

    assert [people(pick) for pick in dealt.picks] == [{"B", "C", "D", "E"}]


def test_a_share_above_somebodys_most_ill_pay_is_never_dealt_to_them():
    thrifty = member(A, most_ill_pay_grosze=35_00)
    others = four_even_and_one_apart()[1:]

    dear = batch([thrifty, *others], [on_sale(SAT_17, share_grosze=40_00)])
    cheap = batch([thrifty, *others], [on_sale(SAT_17, share_grosze=35_00)])

    assert A not in dear.picks[0].named
    assert A in cheap.picks[0].named


def test_nobody_is_dealt_a_card_at_an_hour_they_have_a_game_or_in_a_week_at_its_cap():
    playing_then = member(A, booked=(warsaw(10, 17, 30),))
    week_full = member(B, games_per_week=1, booked=(warsaw(6, 19),))
    others = [member(p) for p in (C, D, E, F)]

    dealt = batch([playing_then, week_full, *others], [on_sale(SAT_17)])
    next_week = batch(
        [playing_then, week_full, *others[:2]],
        [on_sale(warsaw(17, 17))],
    )

    assert [people(pick) for pick in dealt.picks] == [{"C", "D", "E", "F"}]
    assert [people(pick) for pick in next_week.picks] == [{"A", "B", "C", "D"}]


def test_fewer_than_a_full_game_free_is_no_card():
    dealt = batch([member(A), member(B), member(C)], [on_sale(SAT_17)])

    assert dealt.picks == ()


def test_singles_is_the_most_even_two():
    dealt = batch(
        [member(A, 3.0), member(B, 3.5), member(C, 3.0)],
        [on_sale(SAT_17, sport=Sport.TENNIS)],
        sport=Sport.TENNIS,
    )

    assert [people(pick) for pick in dealt.picks] == [{"A", "C"}]


# --------------------------------------------------------------------------- #
# Courts
# --------------------------------------------------------------------------- #


def test_a_player_group_prefers_its_home_club_at_the_same_hour():
    dealt = batch(
        four_even_and_one_apart()[:4],
        [on_sale(SAT_17, NEAR), on_sale(SAT_17, HOME)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
    )

    assert [(pick.club_id, pick.start) for pick in dealt.picks] == [(HOME, SAT_17)]


def test_a_player_group_plays_at_another_of_its_clubs_when_home_has_no_court_then():
    dealt = batch(
        four_even_and_one_apart()[:4],
        [on_sale(SAT_17, NEAR), on_sale(SAT_17, FARTHER)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
    )

    assert [(pick.club_id, pick.start) for pick in dealt.picks] == [(NEAR, SAT_17)]


def test_a_paused_club_takes_no_new_card():
    dealt = batch(
        four_even_and_one_apart()[:4],
        [on_sale(SAT_17, taking_new_cards=False), on_sale(SAT_17, NEAR)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
    )

    assert [pick.club_id for pick in dealt.picks] == [NEAR]


def test_an_official_group_plays_at_home_while_its_players_share_an_hour_there():
    official = PoolClubs(
        home_club_id=HOME, others=(NEAR,), others_only_when_home_is_full=True
    )

    dealt = batch(
        four_even_and_one_apart()[:4],
        [on_sale(SAT_17, NEAR), on_sale(SUN_17, HOME)],
        clubs=official,
    )

    assert [(pick.club_id, pick.start) for pick in dealt.picks] == [(HOME, SUN_17)]


def test_an_official_group_goes_elsewhere_for_players_with_no_hour_at_home():
    official = PoolClubs(
        home_club_id=HOME, others=(NEAR,), others_only_when_home_is_full=True
    )
    saturdays = [member(p, cells=((6, 17),)) for p in (A, B, C, D)]

    dealt = batch(
        saturdays, [on_sale(SAT_17, NEAR), on_sale(SUN_17, HOME)], clubs=official
    )
    alone = batch(
        saturdays, [on_sale(SAT_17, NEAR)], clubs=PoolClubs(home_club_id=HOME)
    )

    assert [(pick.club_id, pick.start) for pick in dealt.picks] == [(NEAR, SAT_17)]
    # Without the club's leave, another club's court serves nobody.
    assert alone.picks == ()


def test_the_engine_looks_fourteen_days_ahead():
    dealt = batch(
        four_even_and_one_apart()[:4],
        [on_sale(warsaw(19, 17)), on_sale(warsaw(19, 22))],
    )

    # Fourteen days from Monday 08:00 is Monday the nineteenth, 08:00.
    assert dealt.picks == ()


def test_every_free_court_at_an_hour_is_a_card_for_different_people():
    eight = [member(p) for p in (A, B, C, D, E, F, G, H)]

    dealt = batch(eight, [on_sale(SAT_17, courts=2)])

    assert [pick.start for pick in dealt.picks] == [SAT_17, SAT_17]
    first, second = (set(pick.named) for pick in dealt.picks)
    assert not first & second


def test_at_a_crowded_hour_the_members_holding_the_fewest_cards_are_considered():
    crowd = [uuid4() for _ in range(12)]
    # A is already on a card on Sunday, beside three who play only then;
    # twelve others hold none. Everybody is at one Level, so without the rule
    # the first four to join — A among them — would be dealt on Saturday.
    sundays = [member(player, cells=((7, 17),)) for player in (B, C, D)]
    on_sunday = a_pick(A, B, C, D, start=SUN_17)

    dealt = batch(
        [member(A), *sundays, *(member(player) for player in crowd)],
        [on_sale(SAT_17), on_sale(SUN_17)],
        filling=(on_sunday,),
    )

    assert [pick.named for pick in dealt.picks] == [tuple(crowd[:4])]


def test_the_same_people_are_dealt_once_at_their_best_hour_in_a_batch():
    dealt = batch(four_even_and_one_apart(), [on_sale(SAT_18), on_sale(SAT_17)])

    assert [(pick.start, people(pick)) for pick in dealt.picks] == [
        (SAT_17, {"A", "B", "C", "D"}),
        (SAT_18, {"A", "B", "C", "E"}),
    ]


def test_a_court_hour_that_already_has_its_card_is_not_dealt_again():
    already = a_pick(A, B, C, D)

    dealt = batch(
        [*four_even_and_one_apart(), member(F), member(G), member(H)],
        [on_sale(SAT_17)],
        filling=(already,),
    )

    assert dealt.picks == ()


def test_people_already_on_a_card_together_are_not_dealt_another_at_another_hour():
    already = a_pick(A, B, C, D)

    dealt = batch(
        four_even_and_one_apart(),
        [on_sale(SAT_17), on_sale(SAT_18)],
        filling=(already,),
    )

    assert [(pick.start, people(pick)) for pick in dealt.picks] == [
        (SAT_18, {"A", "B", "C", "E"})
    ]


# --------------------------------------------------------------------------- #
# Dealing
# --------------------------------------------------------------------------- #


def test_after_a_no_the_seat_goes_to_up_to_three_next_best_fits():
    pick = a_pick(A, B, C, D)
    pick.say_no(B, at=NOW)
    members = [member(p, level) for p, level in ((A, 3.0), (B, 3.0), (C, 3.0))]
    members += [member(D, 3.0), member(E, 3.9), member(F, 3.1), member(G, 3.0)]
    members += [member(H, 3.2)]

    dealt = batch(members, [on_sale(SAT_17)], filling=(pick,))

    # The evenest with A, C and D first; E, furthest off, waits.
    assert dealt.deals == (
        Deal(proposal_id=pick.proposal_id, players=(G, F, H), into=1),
    )


def test_a_seat_with_its_three_next_best_fits_is_dealt_nothing_more():
    pick = a_pick(A, B, C, D)
    pick.say_no(B, at=NOW)
    pick.deal((E, F, G), at=NOW, into=1)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E, F, G, H)],
        [on_sale(SAT_17)],
        filling=(pick,),
    )

    assert dealt.deals == ()


def test_a_second_no_gets_its_own_next_best_fits():
    pick = a_pick(A, B, C, D)
    pick.say_no(B, at=NOW)
    pick.deal((E, F, G), at=NOW, into=1)
    pick.say_no(C, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E, F, G, H, K, J)],
        [on_sale(SAT_17)],
        filling=(pick,),
    )

    assert dealt.deals == (
        Deal(proposal_id=pick.proposal_id, players=(H, K, J), into=1),
    )


def test_a_next_best_fit_who_says_no_is_replaced_and_one_who_says_yes_took_the_seat():
    declined = a_pick(A, B, C, D)
    declined.say_no(B, at=NOW)
    declined.deal((E, F, G), at=NOW, into=1)
    declined.say_no(E, at=NOW)
    took_it = a_pick(A, B, C, D, start=SAT_18)
    took_it.say_no(B, at=NOW)
    took_it.deal((E, F, G), at=NOW, into=1)
    took_it.say_yes(E, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E, F, G, H)],
        [on_sale(SAT_17), on_sale(SAT_18)],
        filling=(declined, took_it),
    )

    assert dealt.deals == (
        Deal(proposal_id=declined.proposal_id, players=(H,), into=1),
    )


def test_in_singles_a_no_hands_its_version_to_one_fit():
    pick = a_pick(A, B, sport=Sport.TENNIS)
    pick.say_no(B, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E)],
        [on_sale(SAT_17, sport=Sport.TENNIS)],
        filling=(pick,),
        sport=Sport.TENNIS,
    )

    assert dealt.deals == (Deal(proposal_id=pick.proposal_id, players=(C,), into=1),)


def test_next_best_fits_fit_everybody_in_and_each_other():
    pick = a_pick(A, B, C, D)
    pick.say_yes(A, at=NOW)
    pick.say_no(B, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E, F, G, H)],
        [on_sale(SAT_17)],
        filling=(pick,),
        mask=unfit((A, E), (F, G)),
    )

    (deal,) = dealt.deals
    assert E not in deal.players
    assert not {F, G} <= set(deal.players)


def test_at_half_in_the_unanswered_seats_go_out_as_new_versions():
    pick = a_pick(A, B, C, D)
    pick.say_yes(A, at=NOW)
    pick.say_yes(B, at=NOW)
    others = [member(p) for p in (E, F, G, H, K)]

    dealt = batch(
        [*(member(p) for p in (A, B, C, D)), *others],
        [on_sale(SAT_17)],
        filling=(pick,),
    )

    assert [deal.into for deal in dealt.deals] == [None, None]
    assert [len(deal.players) for deal in dealt.deals] == [2, 2]
    dealt_to = [player for deal in dealt.deals for player in deal.players]
    assert len(set(dealt_to)) == 4
    assert set(dealt_to) <= {E, F, G, H, K}


def test_before_half_in_a_pick_does_not_widen():
    pick = a_pick(A, B, C, D)
    pick.say_yes(A, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E, F, G, H)],
        [on_sale(SAT_17)],
        filling=(pick,),
    )

    assert dealt.deals == ()


def test_a_game_is_dealt_in_three_versions_at_most():
    pick = a_pick(A, B, C, D)
    for player in (A, B):
        pick.say_yes(player, at=NOW)
    pick.deal((E, F), at=NOW)
    pick.deal((G, H), at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E, F, G, H, K)],
        [on_sale(SAT_17)],
        filling=(pick,),
    )

    # Three versions already — C and D still have not swiped, and K is free.
    assert dealt.deals == ()


def test_a_singles_pick_widens_after_its_first_yes_one_fit_per_version():
    pick = a_pick(A, B, sport=Sport.TENNIS)
    pick.say_yes(A, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D, E)],
        [on_sale(SAT_17, sport=Sport.TENNIS)],
        filling=(pick,),
        sport=Sport.TENNIS,
    )

    assert [(len(deal.players), deal.into) for deal in dealt.deals] == [
        (1, None),
        (1, None),
    ]


# --------------------------------------------------------------------------- #
# A lost court hour
# --------------------------------------------------------------------------- #


def test_a_card_whose_court_hour_is_no_longer_on_sale_is_lost():
    gone = a_pick(A, B, C, D)
    kept = a_pick(A, B, C, E, start=SAT_18)

    dealt = batch(four_even_and_one_apart(), [on_sale(SAT_18)], filling=(gone, kept))

    assert dealt.lost == (gone.proposal_id,)


def test_a_card_is_not_lost_while_its_court_is_there_whatever_the_club_now_says():
    # The club lengthened its release lead: the hour is no longer on sale now,
    # but its court is still there, and the card lives to its own book-by.
    card = a_pick(A, B, C, D)

    dealt = batch(four_even_and_one_apart(), [], held=[(HOME, SAT_17)], filling=(card,))

    assert dealt.lost == ()


def test_a_paused_clubs_card_keeps_its_court_hour():
    card = a_pick(A, B, C, D)

    dealt = batch(
        four_even_and_one_apart(),
        [on_sale(SAT_17, taking_new_cards=False)],
        filling=(card,),
    )

    assert dealt.lost == ()


def test_the_people_in_on_a_lost_card_are_dealt_a_new_card_first():
    gone = a_pick(A, B, C, D)
    for player in (A, B, C):
        gone.say_yes(player, at=NOW)
    # At the one court left at 18:00, E, F, G and H are the evenest four —
    # but the three who were In come first.
    members = [member(p, 3.3) for p in (A, B, C)] + [member(D, 3.3)]
    members += [member(p, 3.0) for p in (E, F, G, H)]

    dealt = batch(members, [on_sale(SAT_18)], filling=(gone,))

    assert dealt.lost == (gone.proposal_id,)
    assert dealt.picks == (
        Pick(
            kind=SearchMode.COMPETITIVE,
            club_id=HOME,
            start=SAT_18,
            named=(A, B, C, D),
            after=gone.proposal_id,
        ),
    )


def test_the_people_in_move_to_another_club_at_the_same_hour_before_another_hour():
    gone = a_pick(A, B, C, D)
    gone.say_yes(A, at=NOW)
    gone.say_yes(B, at=NOW)

    dealt = batch(
        [member(p) for p in (A, B, C, D)],
        [on_sale(SAT_18), on_sale(SAT_17, NEAR)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
        filling=(gone,),
    )

    # The same hour at another of its clubs, before the next hour at home — and the
    # four are then on a card together, so 18:00 deals them nothing more.
    assert [(pick.club_id, pick.start, pick.after) for pick in dealt.picks] == [
        (NEAR, SAT_17, gone.proposal_id)
    ]
    assert dealt.picks[0].named == (A, B, C, D)


def test_a_lost_card_nobody_was_in_on_is_simply_gone():
    gone = a_pick(A, B, C, D)

    dealt = batch(four_even_and_one_apart()[:4], [], filling=(gone,))

    assert dealt.lost == (gone.proposal_id,)
    assert dealt.picks == ()


# --------------------------------------------------------------------------- #
# A full game, and a booked one its club cancelled (#547)
# --------------------------------------------------------------------------- #


def a_full_game(*players: UUID, start: Instant = SAT_17, club: UUID = HOME) -> Proposal:
    game = a_pick(*players, start=start, club=club)
    for player in players:
        game.say_yes(player, at=NOW)
    return game


def test_a_full_game_still_filling_holds_no_court_and_is_lost_with_it():
    # No club confirms a game: nothing holds a court for a full game the fill
    # has not booked, so the last court at 17:00 going takes its card.
    full = a_full_game(A, B, C, D)

    dealt = batch([member(p) for p in (A, B, C, D)], [], held=[], filling=(full,))

    assert dealt.lost == (full.proposal_id,)


def test_a_full_game_still_filling_is_the_card_on_its_court():
    # Two courts at 17:00: the full game is one of them, the other a card's.
    full = a_full_game(A, B, C, D)
    others = [member(p) for p in (E, F, G, H)]

    dealt = batch(
        [member(p) for p in (A, B, C, D)] + others,
        [on_sale(SAT_17, courts=2)],
        filling=(full,),
    )

    assert [people(pick) for pick in dealt.picks] == [{"E", "F", "G", "H"}]


def a_cancelled_game(
    *players: UUID, still_in: tuple[UUID, ...] | None = None, club: UUID = HOME
) -> Proposal:
    """A booked game at 17:00 on Saturday its club cancelled, owed to
    ``still_in`` — everybody, unless somebody left before the cancel."""

    cancelled = a_full_game(*players, club=club)
    cancelled.fill(
        first_side=players[:2], second_side=players[2:], by=players[-1], at=NOW
    )
    cancelled.club_cancelled(players if still_in is None else still_in, at=NOW)
    return cancelled


def owed_card(dealt: Batch, cancelled: Proposal) -> Pick:
    [card] = [pick for pick in dealt.picks if pick.after == cancelled.proposal_id]
    assert dealt.redealt == (cancelled.proposal_id,)
    return card


def test_the_people_still_in_a_game_its_club_cancelled_are_dealt_a_new_card_first():
    # D left before the club cancelled: the card is owed to the three still in.
    cancelled = a_cancelled_game(A, B, C, D, still_in=(A, B, C))
    members = [member(p, 3.3) for p in (A, B, C, D)]
    members += [member(p, 3.0) for p in (E, F, G, H)]

    dealt = batch(members, [on_sale(SAT_17), on_sale(SAT_18)], owed=(cancelled,))

    first = owed_card(dealt, cancelled)
    # The club and hour that cancelled it, sold again — on a court of the other
    # kind, or at a new price — come first (#673, Q123).
    assert (first.club_id, first.start) == (HOME, SAT_17)
    assert {A, B, C} <= set(first.named)
    # It records whom it is owed to: never the best fit beside them.
    assert first.owed_card_for == (A, B, C)
    assert people(dealt.picks[1]) == {"E", "F", "G", "H"}
    assert dealt.picks[1].start == SAT_18


def test_the_owed_card_is_at_the_club_that_cancelled_before_the_home_club_at_the_hour():
    cancelled = a_cancelled_game(A, B, C, D, club=NEAR)

    dealt = batch(
        [member(p) for p in (A, B, C, D)],
        [on_sale(SAT_17), on_sale(SAT_17, NEAR), on_sale(SAT_18)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
        owed=(cancelled,),
    )

    card = owed_card(dealt, cancelled)
    assert (card.club_id, card.start) == (NEAR, SAT_17)


def test_a_player_group_s_owed_card_is_another_club_at_the_hour_before_another_hour():
    cancelled = a_cancelled_game(A, B, C, D)

    dealt = batch(
        [member(p) for p in (A, B, C, D)],
        [on_sale(SAT_18), on_sale(SAT_17, FARTHER), on_sale(SAT_17, NEAR)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR, FARTHER)),
        owed=(cancelled,),
    )

    # Its club sells nothing at 17:00 any more: the nearest other club then,
    # before 18:00 at home.
    card = owed_card(dealt, cancelled)
    assert (card.club_id, card.start) == (NEAR, SAT_17)


def test_an_official_group_s_owed_card_stays_home_while_its_players_share_an_hour():
    official = PoolClubs(
        home_club_id=HOME, others=(NEAR,), others_only_when_home_is_full=True
    )
    cancelled = a_cancelled_game(A, B, C, D)

    dealt = batch(
        [member(p) for p in (A, B, C, D)],
        [on_sale(SAT_17, NEAR), on_sale(SUN_17)],
        clubs=official,
        owed=(cancelled,),
    )

    # Never another club at the same hour while home has an hour they share.
    card = owed_card(dealt, cancelled)
    assert (card.club_id, card.start) == (HOME, SUN_17)


def test_after_the_hour_the_owed_card_is_the_closest_hour_the_home_club_first():
    cancelled = a_cancelled_game(A, B, C, D, club=NEAR)

    dealt = batch(
        [member(p) for p in (A, B, C, D)],
        [on_sale(SUN_17), on_sale(SAT_18, NEAR), on_sale(SAT_18)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
        owed=(cancelled,),
    )

    # Another hour: the club that cancelled has no precedence there.
    card = owed_card(dealt, cancelled)
    assert (card.club_id, card.start) == (HOME, SAT_18)


def test_of_two_hours_as_close_the_owed_card_is_at_the_home_club():
    cancelled = a_cancelled_game(A, B, C, D)
    free_either_side = ((6, 16), (6, 18))

    dealt = batch(
        [member(p, cells=free_either_side) for p in (A, B, C, D)],
        [on_sale(warsaw(10, 16), NEAR), on_sale(SAT_18)],
        clubs=PoolClubs(home_club_id=HOME, others=(NEAR,)),
        owed=(cancelled,),
    )

    # An hour before at another club, or an hour after at home: home first.
    card = owed_card(dealt, cancelled)
    assert (card.club_id, card.start) == (HOME, SAT_18)


def test_an_owed_card_is_dealt_only_where_every_owed_player_may_play():
    # The club sells 17:00 again at a new price, above what A will pay.
    cancelled = a_cancelled_game(A, B, C, D)
    thrifty = member(A, most_ill_pay_grosze=30_00)

    dealt = batch(
        [thrifty, *(member(p) for p in (B, C, D))],
        [on_sale(SAT_17, share_grosze=40_00), on_sale(SAT_18)],
        owed=(cancelled,),
    )

    card = owed_card(dealt, cancelled)
    assert card.start == SAT_18


def test_a_card_dealt_after_a_lost_one_is_owed_to_nobody():
    gone = a_pick(A, B, C, D)
    for player in (A, B, C):
        gone.say_yes(player, at=NOW)

    dealt = batch([member(p) for p in (A, B, C, D)], [on_sale(SAT_18)], filling=(gone,))

    [card] = dealt.picks
    # No notice promised them a game: only a club's cancel owes one (#673).
    assert (card.after, card.owed_card_for) == (gone.proposal_id, ())


def test_a_cancelled_game_with_no_hour_for_its_people_stays_owed():
    cancelled = a_cancelled_game(A, B, C, D)

    dealt = batch([member(p) for p in (A, B, C, D)], [], owed=(cancelled,))

    assert dealt.picks == ()
    # Nothing recorded: the next batch looks again.
    assert dealt.redealt == ()
