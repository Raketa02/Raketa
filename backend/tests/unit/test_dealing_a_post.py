"""Dealing a post — the proposer's pure seam, for a game a member posted (#546;
the mechanics §7, §9.2; the screens A5.4).

**At posting**, the post goes to the poster's best fits free at its hour — one
version per full set of them, the evenest first, **up to three** (for doubles: 9
or more fits are three versions, 6–8 two, 3–5 one); fewer than a full set, one
version with the seats it cannot name left open. A best fit is a member rated
in the sport, wanting the kind, free for the whole hour and able to play then
— the proposer's own *may play* — whom the post is for (its *Who* and Level
range) and who fits the poster and everybody on their version.

**After posting**, every batch keeps dealing it, until its book-by: a version
naming fewer than its open seats takes whoever **becomes** a fit, a new full
set of fits is a new version while there are fewer than three, and a seat a no
left goes to the next best fits as a pick's does — always to members the post
is for. A post needs nobody In to widen: it is its poster's ask, not a pick
gathering momentum.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, instant
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import LevelRange, PostedFor, Who
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.proposals.domain.proposer import (
    CourtHourOnSale,
    Deal,
    Member,
    PoolClubs,
    propose,
    versions_of_a_post,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int) -> Instant:
    """An hour in Kraków in October 2026. The fifth is a Monday."""

    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


NOW = warsaw(5, 8)
SAT_17 = warsaw(10, 17)
EVENINGS = tuple((day, hour) for day in range(1, 8) for hour in range(17, 23))
MORNINGS = tuple((day, hour) for day in range(1, 8) for hour in range(7, 12))

HOME = uuid4()
POOL = Pool(id=uuid4(), kind=PoolKind.GROUP)
COMPETITIVE = frozenset({SearchMode.COMPETITIVE})
ANYBODY = PostedFor(who=Who.ANYONE, levels=LevelRange(low=2.0, high=4.0))

POSTER = uuid4()
A, B, C, D, E, F, G, H, K, J, L = (uuid4() for _ in range(11))
NAMES = {
    POSTER: "P",
    **dict(zip((A, B, C, D, E, F, G, H, K, J, L), "ABCDEFGHKJL", strict=True)),
}


def member(
    player: UUID,
    level: float | None = 3.0,
    *,
    cells: tuple[tuple[int, int], ...] = EVENINGS,
    wants: frozenset[SearchMode] = COMPETITIVE,
    gender: Gender | None = Gender.WOMAN,
    preference: GenderPreference | None = GenderPreference.ANY,
) -> Member:
    return Member(
        player_id=player,
        level=None if level is None else LevelReading(mu=level, sigma=0.4),
        week=WeeklyHours.of_cells(cells),
        wants=wants,
        limits=GamesAndMoney(player_id=player),
        gender=gender,
        preference=preference,
    )


def at_saturday_five() -> CourtHourOnSale:
    return CourtHourOnSale(
        club_id=HOME,
        sport=Sport.PADEL,
        start=SAT_17,
        courts=1,
        share_grosze=30_00,
        book_by=SAT_17 - timedelta(hours=2),
    )


def versions(
    members: list[Member],
    *,
    posted_for: PostedFor = ANYBODY,
    unfit: frozenset[frozenset[UUID]] = frozenset(),
    sport: Sport = Sport.PADEL,
) -> list[set[str]]:
    dealt = versions_of_a_post(
        sport=sport,
        members=[member(POSTER), *members],
        unfit=unfit,
        poster=POSTER,
        kind=SearchMode.COMPETITIVE,
        hour=at_saturday_five(),
        posted_for=posted_for,
        balance=LIVE_RULESET.balance,
        now=NOW,
    )
    return [{NAMES[player] for player in version} for version in dealt]


def fits(*players: UUID, level: float = 3.0, **kwargs) -> list[Member]:
    return [member(player, level, **kwargs) for player in players]


# --------------------------------------------------------------------------- #
# At posting
# --------------------------------------------------------------------------- #


def test_nine_fits_or_more_are_three_versions():
    dealt = versions(fits(A, B, C, D, E, F, G, H, K, J))

    assert len(dealt) == 3
    assert all(len(version) == 3 for version in dealt)
    # Each person in one version.
    assert len(set().union(*dealt)) == 9


def test_six_to_eight_fits_are_two_versions_and_three_to_five_one():
    assert [len(v) for v in versions(fits(A, B, C, D, E, F, G, H))] == [3, 3]
    assert [len(v) for v in versions(fits(A, B, C, D, E, F))] == [3, 3]
    assert [len(v) for v in versions(fits(A, B, C, D, E))] == [3]
    assert [len(v) for v in versions(fits(A, B, C))] == [3]


def test_fewer_fits_than_open_seats_is_one_version_with_seats_open():
    assert versions(fits(A, B)) == [{"A", "B"}]
    assert versions(fits(A)) == [{"A"}]
    assert versions([]) == []


def test_the_evenest_set_is_the_first_version():
    dealt = versions(
        [member(A, 3.0), member(B, 3.0), member(C, 3.0), *fits(D, E, F, level=3.4)]
    )

    assert dealt[0] == {"A", "B", "C"}


def test_in_singles_each_best_fit_is_a_version_of_its_own_up_to_three():
    dealt = versions(fits(A, B, C, D), sport=Sport.TENNIS)

    assert len(dealt) == 3
    assert all(len(version) == 1 for version in dealt)


def test_only_members_free_for_the_hour_and_wanting_the_kind_are_best_fits():
    dealt = versions(
        [
            *fits(A, B),
            member(C, cells=MORNINGS),
            member(D, wants=frozenset({SearchMode.FOR_FUN})),
            member(E, None),
        ]
    )

    assert dealt == [{"A", "B"}]


def test_a_post_is_dealt_only_to_who_it_is_for_inside_its_level_range():
    for_women = PostedFor(who=Who.WOMEN, levels=LevelRange(low=2.8, high=3.2))

    dealt = versions(
        [
            *fits(A, B),
            member(C, gender=Gender.MAN),
            member(D, gender=Gender.PREFER_NOT_TO_SAY),
            member(E, preference=GenderPreference.MEN_ONLY),
            member(F, 3.4),
            member(G, 2.7),
        ],
        posted_for=for_women,
    )

    assert dealt == [{"A", "B"}]


def test_a_mixed_pairs_post_is_two_men_and_two_women_a_version():
    mixed = PostedFor(who=Who.MIXED_PAIRS, levels=LevelRange(low=2.0, high=4.0))
    men = fits(A, B, C, gender=Gender.MAN)
    women = fits(D, E, F, G, gender=Gender.WOMAN)

    # The poster is a woman: each version is two men and one more woman.
    dealt = versions([*men, *women], posted_for=mixed)

    assert len(dealt) == 1 or all(len(version) == 3 for version in dealt)
    for version in dealt:
        named = {NAMES[p] for p in (A, B, C)} & version
        assert len(named) == 2


def test_a_post_s_versions_fit_each_other_and_the_poster():
    dealt = versions(
        fits(A, B, C, D),
        unfit=frozenset({frozenset((A, B)), frozenset((POSTER, D))}),
    )

    assert len(dealt) == 1
    assert not {"A", "B"} <= dealt[0]
    assert "D" not in dealt[0]


# --------------------------------------------------------------------------- #
# After posting
# --------------------------------------------------------------------------- #


def a_post(
    *versions_named: tuple[UUID, ...], posted_for: PostedFor = ANYBODY
) -> Proposal:
    post = Proposal.make(
        proposal_id=uuid4(),
        pool=POOL,
        origin=Origin.POST,
        poster_id=POSTER,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=HOME,
        start=SAT_17,
        share_grosze=30_00,
        book_by=SAT_17 - timedelta(hours=2),
        at=NOW - timedelta(hours=1),
        posted_for=posted_for,
    )
    for named in versions_named:
        post.deal(named, at=NOW - timedelta(hours=1))
    post.pull_events()
    return post


def batch(members: list[Member], post: Proposal):
    return propose(
        sport=Sport.PADEL,
        members=[member(POSTER), *members],
        unfit={kind: frozenset() for kind in SearchMode},
        clubs=PoolClubs(home_club_id=HOME),
        hours=[at_saturday_five()],
        held=[(HOME, SAT_17)],
        filling=[post],
        balance=LIVE_RULESET.balance,
        now=NOW,
    )


def deals_on(post: Proposal, members: list[Member]) -> tuple[Deal, ...]:
    return tuple(
        deal
        for deal in batch(members, post).deals
        if deal.proposal_id == post.proposal_id
    )


def test_somebody_who_becomes_a_fit_is_dealt_a_version_naming_fewer_than_its_seats():
    post = a_post((A, B))

    dealt = deals_on(post, fits(A, B, C))

    assert dealt == (Deal(proposal_id=post.proposal_id, players=(C,), into=1),)


def test_a_new_full_set_of_fits_is_a_new_version_with_only_the_poster_in():
    post = a_post((A, B, C))

    dealt = deals_on(post, fits(A, B, C, D, E, F))

    assert dealt == (Deal(proposal_id=post.proposal_id, players=(D, E, F), into=None),)


def test_fits_short_of_a_full_set_wait_for_a_no():
    post = a_post((A, B, C))

    assert deals_on(post, fits(A, B, C, D, E)) == ()

    post.say_no(B, at=NOW)
    dealt = deals_on(post, fits(A, B, C, D, E))

    assert dealt == (Deal(proposal_id=post.proposal_id, players=(D, E), into=1),)


def test_a_post_is_never_dealt_on_to_somebody_it_is_not_for():
    post = a_post(
        (A, B), posted_for=PostedFor(who=Who.WOMEN, levels=LevelRange(2.5, 3.5))
    )

    dealt = deals_on(
        post,
        [*fits(A, B), member(C, gender=Gender.MAN), member(D, 3.8), member(E)],
    )

    assert dealt == (Deal(proposal_id=post.proposal_id, players=(E,), into=1),)


def test_a_mixed_pairs_seat_a_no_left_goes_to_the_same_gender():
    mixed = PostedFor(who=Who.MIXED_PAIRS, levels=LevelRange(low=2.0, high=4.0))
    # The poster is a woman: a man, a woman and a man beside her.
    post = a_post((A, D, B), posted_for=mixed)
    post.say_no(D, at=NOW)
    members = [
        *fits(A, B, C, gender=Gender.MAN),
        *fits(D, E, gender=Gender.WOMAN),
    ]

    dealt = deals_on(post, members)

    assert dealt == (Deal(proposal_id=post.proposal_id, players=(E,), into=1),)


def test_a_post_whose_three_versions_are_out_takes_no_new_version():
    post = a_post((A, B, C), (D, E, F), (G, H, K))

    assert deals_on(post, fits(A, B, C, D, E, F, G, H, K, J, L, uuid4())) == ()
