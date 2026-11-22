"""**For-fun tables are built by shared tags** — the proposer's pure seam
(``docs/adr/0207`` §1, §3; #831).

Among the fours that pass the unchanged gates, For fun prefers, in order: the
highest **Social vibe**, compared exactly before it is rounded; the most **new
faces** — pairs who have never played together and are not friends; the
evenest forecast; the smallest level spread. **Competitive picks are exactly
today's**: the best forecast, then the smallest spread, whatever anybody's tags
or history.

The rule is the same wherever the engine names somebody for a For-fun seat: a
new pick, the next best fits after a no, a post's open seats — at posting and
after — and the people of a card that lost its court dealt a new one. 💘 *Open
to meet someone* never builds anything.

**Nothing in the gates moves**: who may play an hour (free for the whole of
it), who fits whom, the twelve considered at a crowded hour, one card per free
court, and Competitive dealt before For fun within an hour.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timedelta
from fractions import Fraction
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, instant
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import LevelRange, PostedFor, Who
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.proposals.domain.proposer import (
    Batch,
    CourtHourOnSale,
    Deal,
    Member,
    Pick,
    PoolClubs,
    propose,
    versions_of_a_post,
)
from app.modules.proposals.domain.vibe import social_vibe_of, social_vibe_share_of

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int) -> Instant:
    """An hour in Kraków in October 2026. The fifth is a Monday."""

    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


NOW = warsaw(5, 8)
SAT_17 = warsaw(10, 17)
SUN_17 = warsaw(11, 17)
EVENINGS = tuple((day, hour) for day in range(1, 8) for hour in range(17, 23))

HOME = uuid4()
POOL = Pool(id=uuid4(), kind=PoolKind.GROUP)
FOR_FUN = frozenset({SearchMode.FOR_FUN})
COMPETITIVE = frozenset({SearchMode.COMPETITIVE})
EITHER = frozenset(SearchMode)
ANYBODY = PostedFor(who=Who.ANYONE, levels=LevelRange(low=2.0, high=4.0))

POSTER, A, B, C, D, E, F, G, H = (uuid4() for _ in range(9))
NAMES = dict(zip((POSTER, A, B, C, D, E, F, G, H), "PABCDEFGH", strict=True))

DRINK = SocialTag.STAYS_FOR_A_DRINK
LAUGHS = SocialTag.LAUGHS_OFF_MISTAKES
QUIET = SocialTag.QUIET_AND_FOCUSED
HOMEWARD = SocialTag.STRAIGHT_HOME_AFTER
LIFT = SocialTag.SHARES_A_LIFT
#: 💘 — held, shown, and never counted.
SOMEONE = SocialTag.OPEN_TO_MEET_SOMEONE

Tags = Mapping[UUID, Collection[SocialTag]]


def member(
    player: UUID,
    level: float = 3.0,
    *,
    wants: frozenset[SearchMode] = FOR_FUN,
    cells: tuple[tuple[int, int], ...] = EVENINGS,
) -> Member:
    return Member(
        player_id=player,
        level=LevelReading(mu=level, sigma=0.4),
        week=WeeklyHours.of_cells(cells),
        wants=wants,
        limits=GamesAndMoney(player_id=player, games_per_week=2),
    )


def on_sale(start: Instant = SAT_17, *, courts: int = 1) -> CourtHourOnSale:
    return CourtHourOnSale(
        club_id=HOME,
        sport=Sport.PADEL,
        start=start,
        courts=courts,
        share_grosze=30_00,
        book_by=start - timedelta(hours=2),
    )


def batch(
    members: list[Member],
    *,
    tags: Tags,
    known: Collection[frozenset[UUID]] = (),
    hours: list[CourtHourOnSale] | None = None,
    unfit: Collection[tuple[UUID, UUID]] = (),
    filling: tuple[Proposal, ...] = (),
    owed: tuple[Proposal, ...] = (),
) -> Batch:
    hours = hours if hours is not None else [on_sale()]
    mask = frozenset(frozenset(pair) for pair in unfit)
    return propose(
        sport=Sport.PADEL,
        members=members,
        unfit={kind: mask for kind in SearchMode},
        clubs=PoolClubs(home_club_id=HOME),
        hours=hours,
        held=[(hour.club_id, hour.start) for hour in hours],
        filling=filling,
        owed=owed,
        balance=LIVE_RULESET.balance,
        now=NOW,
        tags=tags,
        known=known,
    )


def met(*pairs: tuple[UUID, UUID]) -> frozenset[frozenset[UUID]]:
    """Pairs who are no new faces to each other — they have played together,
    or they are friends."""

    return frozenset(frozenset(pair) for pair in pairs)


def people(pick: Pick) -> set[str]:
    return {NAMES[player] for player in pick.named}


def picked(dealt: Batch) -> list[set[str]]:
    return [people(pick) for pick in dealt.picks]


def a_card(
    *named: UUID,
    kind: SearchMode = SearchMode.FOR_FUN,
    origin: Origin = Origin.PICK,
    start: Instant = SAT_17,
) -> Proposal:
    card = Proposal.make(
        proposal_id=uuid4(),
        pool=POOL,
        origin=origin,
        poster_id=POSTER if origin is Origin.POST else None,
        sport=Sport.PADEL,
        kind=kind,
        club_id=HOME,
        start=start,
        share_grosze=30_00,
        book_by=start - timedelta(hours=2),
        at=NOW - timedelta(hours=1),
        posted_for=ANYBODY if origin is Origin.POST else None,
    )
    card.deal(named, at=NOW - timedelta(hours=1))
    card.pull_events()
    return card


# --------------------------------------------------------------------------- #
# The four a court hour is dealt
# --------------------------------------------------------------------------- #

#: A, B, C and E share a drink and the laughs; D shares nothing. E is the one
#: whose Level is apart, so the evenest four is A, B, C and D.
SHARED_BUT_E_APART = {
    A: (DRINK, LAUGHS),
    B: (DRINK, LAUGHS),
    C: (DRINK, LAUGHS),
    D: (QUIET, HOMEWARD),
    E: (DRINK, LAUGHS),
}


def five(wants: frozenset[SearchMode]) -> list[Member]:
    return [
        member(A, wants=wants),
        member(B, wants=wants),
        member(C, wants=wants),
        member(D, wants=wants),
        member(E, 3.6, wants=wants),
    ]


def test_for_fun_deals_the_higher_vibe_four_over_a_more_even_one():
    dealt = batch(five(FOR_FUN), tags=SHARED_BUT_E_APART)

    # A, B, C and E share everything they hold: 100%, against the evenest
    # four's 50%.
    assert dealt.picks == (
        Pick(kind=SearchMode.FOR_FUN, club_id=HOME, start=SAT_17, named=(A, B, C, E)),
    )


def test_a_competitive_four_is_today_s_whatever_anybody_s_tags_or_history():
    dealt = batch(five(COMPETITIVE), tags=SHARED_BUT_E_APART, known=met((A, B), (C, D)))

    assert dealt.picks == (
        Pick(
            kind=SearchMode.COMPETITIVE,
            club_id=HOME,
            start=SAT_17,
            named=(A, B, C, D),
        ),
    )


def test_new_faces_break_a_tie_on_the_vibe():
    alike = {player: (DRINK, LAUGHS) for player in (A, B, C, D, E)}
    five_alike = [member(player) for player in (A, B, C, D, E)]

    # Every four shares everything, and is as even: the first to join.
    assert picked(batch(five_alike, tags=alike)) == [{"A", "B", "C", "D"}]
    # A and B have played together, or are friends: a four without one of
    # them is six new pairs to five.
    assert picked(batch(five_alike, tags=alike, known=met((A, B)))) == [
        {"A", "C", "D", "E"}
    ]


def test_the_forecast_then_the_level_spread_break_the_rest():
    alike = {player: (DRINK,) for player in (A, B, C, D, E, F)}

    # The same vibe and the same new faces everywhere: the evenest four.
    assert picked(batch(five(FOR_FUN), tags=alike)) == [{"A", "B", "C", "D"}]

    # Both fours forecast as even as a game can be; one of them is four
    # people at one level, the other two pairs a step apart.
    six = [
        member(A, 3.0),
        member(B, 3.2),
        member(C, 3.0),
        member(D, 3.2),
        member(E, 3.1),
        member(F, 3.1),
    ]
    dealt = batch(six, tags=alike, unfit=[(A, E), (C, F)])

    assert picked(dealt) == [{"B", "D", "E", "F"}]


def test_the_vibe_is_compared_exactly_before_it_is_rounded():
    tags = {
        A: (DRINK, LAUGHS, LIFT),
        B: (DRINK, HOMEWARD, LIFT),
        C: (LAUGHS, HOMEWARD, LIFT),
        D: (DRINK, LAUGHS),
        E: (DRINK, QUIET, LIFT),
    }
    # Both print 61%: A, B, C and D share 20/33 of what they carry, A, B, C
    # and E 11/18 — a hair more.
    assert social_vibe_of((A, B, C, D), tags) == social_vibe_of((A, B, C, E), tags)
    assert social_vibe_share_of((A, B, C, D), tags) == Fraction(20, 33)
    assert social_vibe_share_of((A, B, C, E), tags) == Fraction(11, 18)

    # Rounded first, the tie would go to the forecast, and E is apart.
    assert picked(batch(five(FOR_FUN), tags=tags)) == [{"A", "B", "C", "E"}]


def test_open_to_meet_someone_builds_nothing():
    # Counted, 💘 would make A, B, C and D a 75% table — as high as A, B, C
    # and E, which the forecast would then pass over for D. Left out, they
    # are 50% against 80%.
    tags = {
        A: (DRINK, SOMEONE),
        B: (DRINK, SOMEONE),
        C: (DRINK, SOMEONE),
        D: (SOMEONE, QUIET),
        E: (DRINK, HOMEWARD),
    }

    assert picked(batch(five(FOR_FUN), tags=tags)) == [{"A", "B", "C", "E"}]


# --------------------------------------------------------------------------- #
# Wherever the engine names somebody for a For-fun seat
# --------------------------------------------------------------------------- #

#: A, C and D share a drink and the laughs. Of the fits for B's seat, F shares
#: both but is apart, G shares the drink, H holds a tag nobody else does, and E
#: — as even as G and H — shares nothing.
FOR_B_S_SEAT = {
    A: (DRINK, LAUGHS),
    B: (DRINK, LAUGHS),
    C: (DRINK, LAUGHS),
    D: (DRINK, LAUGHS),
    E: (QUIET, HOMEWARD),
    F: (DRINK, LAUGHS),
    G: (DRINK,),
    H: (QUIET,),
}


def b_s_seat(wants: frozenset[SearchMode]) -> list[Member]:
    return [
        member(A, wants=wants),
        member(B, wants=wants),
        member(C, wants=wants),
        member(D, wants=wants),
        member(E, wants=wants),
        member(F, 3.4, wants=wants),
        member(G, wants=wants),
        member(H, wants=wants),
    ]


def test_after_a_no_a_for_fun_seat_goes_to_the_next_best_fits_by_the_vibe():
    friendly = a_card(A, B, C, D)
    friendly.say_no(B, at=NOW)

    dealt = batch(b_s_seat(FOR_FUN), tags=FOR_B_S_SEAT, filling=(friendly,))

    # F at 100%, G at 86%, H at 57%; E, at 50%, waits.
    assert dealt.deals == (
        Deal(proposal_id=friendly.proposal_id, players=(F, G, H), into=1),
    )


def test_after_a_no_a_competitive_seat_goes_to_the_evenest_as_today():
    game = a_card(A, B, C, D, kind=SearchMode.COMPETITIVE)
    game.say_no(B, at=NOW)

    dealt = batch(b_s_seat(COMPETITIVE), tags=FOR_B_S_SEAT, filling=(game,))

    assert dealt.deals == (
        Deal(proposal_id=game.proposal_id, players=(E, G, H), into=1),
    )


def test_new_faces_break_a_tie_among_the_next_best_fits():
    friendly = a_card(A, B, C, D)
    friendly.say_no(B, at=NOW)
    alike = {player: (DRINK,) for player in (A, B, C, D, E, F, G, H)}
    even = [member(player) for player in (A, B, C, D, E, F, G, H)]

    # E has played with A; F is friends with C.
    dealt = batch(even, tags=alike, known=met((A, E), (C, F)), filling=(friendly,))

    assert dealt.deals == (
        Deal(proposal_id=friendly.proposal_id, players=(G, H, E), into=1),
    )


def versions(kind: SearchMode, fits: list[Member], tags: Tags) -> list[set[str]]:
    dealt = versions_of_a_post(
        sport=Sport.PADEL,
        members=[member(POSTER, wants=frozenset({kind})), *fits],
        unfit=frozenset(),
        poster=POSTER,
        kind=kind,
        hour=on_sale(),
        posted_for=ANYBODY,
        balance=LIVE_RULESET.balance,
        now=NOW,
        tags=tags,
    )
    return [{NAMES[player] for player in version} for version in dealt]


#: The poster shares a drink and the laughs with D, E and F, who are apart;
#: A, B and C, as even as can be with them, share nothing with anybody.
THE_POSTER_S_COMPANY = {
    POSTER: (DRINK, LAUGHS),
    A: (QUIET,),
    B: (HOMEWARD,),
    C: (SocialTag.SHARES_A_LIFT,),
    D: (DRINK, LAUGHS),
    E: (DRINK, LAUGHS),
    F: (DRINK, LAUGHS),
}


def the_poster_s_fits(wants: frozenset[SearchMode]) -> list[Member]:
    return [
        member(A, wants=wants),
        member(B, wants=wants),
        member(C, wants=wants),
        member(D, 3.4, wants=wants),
        member(E, 3.4, wants=wants),
        member(F, 3.4, wants=wants),
    ]


def test_a_for_fun_post_is_dealt_first_to_the_poster_s_best_company():
    assert versions(
        SearchMode.FOR_FUN, the_poster_s_fits(FOR_FUN), THE_POSTER_S_COMPANY
    ) == [{"D", "E", "F"}, {"A", "B", "C"}]
    # A competitive post, as today: the evenest set first.
    assert versions(
        SearchMode.COMPETITIVE, the_poster_s_fits(COMPETITIVE), THE_POSTER_S_COMPANY
    ) == [{"A", "B", "C"}, {"D", "E", "F"}]


def test_a_for_fun_post_s_open_seat_goes_to_the_best_company():
    post = a_card(A, B, origin=Origin.POST)
    tags = {**THE_POSTER_S_COMPANY, A: (DRINK, LAUGHS), B: (DRINK, LAUGHS)}

    dealt = batch(
        [member(POSTER), member(A), member(B), member(C), member(D, 3.4)],
        tags=tags,
        filling=(post,),
    )

    # C is the evener; D shares everything with the poster, A and B.
    assert [deal for deal in dealt.deals if deal.proposal_id == post.proposal_id] == [
        Deal(proposal_id=post.proposal_id, players=(D,), into=1)
    ]


def test_the_people_in_on_a_lost_friendly_are_completed_by_their_best_company():
    lost = a_card(A, B, C, D, start=SUN_17)
    for player in (A, B):
        lost.say_yes(player, at=NOW - timedelta(minutes=30))
    tags = {
        A: (DRINK,),
        B: (DRINK,),
        C: (QUIET,),
        D: (QUIET,),
        E: (DRINK,),
        F: (DRINK,),
    }

    # Its Sunday court went; Saturday's is on sale.
    dealt = propose(
        sport=Sport.PADEL,
        members=[member(p) for p in (A, B, C, D)] + [member(E, 3.4), member(F, 3.4)],
        unfit={kind: frozenset() for kind in SearchMode},
        clubs=PoolClubs(home_club_id=HOME),
        hours=[on_sale(SAT_17)],
        held=[(HOME, SAT_17)],
        filling=(lost,),
        balance=LIVE_RULESET.balance,
        now=NOW,
        tags=tags,
    )

    assert dealt.lost == (lost.proposal_id,)
    assert [(pick.after, pick.named) for pick in dealt.picks] == [
        (lost.proposal_id, (A, B, E, F))
    ]


# --------------------------------------------------------------------------- #
# The gates do not move
# --------------------------------------------------------------------------- #


def test_the_best_company_is_never_seated_with_somebody_who_may_not_share_a_court():
    dealt = batch(five(FOR_FUN), tags=SHARED_BUT_E_APART, unfit=[(A, E)])

    (pick,) = dealt.picks
    assert not {A, E} <= set(pick.named)


def test_the_best_company_is_dealt_only_an_hour_they_are_all_free_for():
    not_on_saturdays = [*five(FOR_FUN)[:4], member(E, 3.6, cells=((7, 17),))]

    assert picked(batch(not_on_saturdays, tags=SHARED_BUT_E_APART)) == [
        {"A", "B", "C", "D"}
    ]


def test_at_a_crowded_hour_the_twelve_holding_the_fewest_cards_are_considered():
    crowd = [uuid4() for _ in range(12)]
    # A is on a card on Sunday, beside three who play only then. A and the
    # first three of the crowd hold the one tag they share; the rest each
    # hold one nobody else does — so with A considered, A's four would be
    # the whole table's company.
    sundays = [member(player, cells=((7, 17),)) for player in (B, C, D)]
    on_sunday = a_card(A, B, C, D, start=SUN_17)
    singles = [tag for tag in SocialTag if tag not in (DRINK, SOMEONE)]
    tags: dict[UUID, tuple[SocialTag, ...]] = {A: (DRINK,)}
    for index, player in enumerate(crowd):
        tags[player] = (DRINK,) if index < 3 else (singles[index],)

    dealt = batch(
        [member(A), *sundays, *(member(player) for player in crowd)],
        tags=tags,
        hours=[on_sale(SAT_17), on_sale(SUN_17)],
        filling=(on_sunday,),
    )

    assert [pick.named for pick in dealt.picks] == [tuple(crowd[:4])]


def test_competitive_is_dealt_before_for_fun_one_card_a_free_court():
    alike = {player: (DRINK, LAUGHS) for player in (A, B, C, D, E, F, G, H)}
    eight = [
        *(member(player, wants=EITHER) for player in (A, B, C, D)),
        *(member(player) for player in (E, F, G, H)),
    ]

    two_courts = batch(eight, tags=alike, hours=[on_sale(courts=2)])
    one_court = batch(eight, tags=alike, hours=[on_sale(courts=1)])

    assert [(pick.kind, people(pick)) for pick in two_courts.picks] == [
        (SearchMode.COMPETITIVE, {"A", "B", "C", "D"}),
        (SearchMode.FOR_FUN, {"E", "F", "G", "H"}),
    ]
    assert [(pick.kind, people(pick)) for pick in one_court.picks] == [
        (SearchMode.COMPETITIVE, {"A", "B", "C", "D"}),
    ]
