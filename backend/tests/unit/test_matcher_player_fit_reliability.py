"""The pair rule's fourth clause — the reliability filter — in ``MatcherPlayerFit``
(``docs/adr/0195`` §6, #661).

What HTTP cannot see is asserted here, over hand-written stubs of the four reads
the adapter makes: **which pairs** the clause refuses, both ways and with *New*
passing; that a yes already given is asked **without** it; and **how many times
the points are read** — once per call, once for every kind of a deal, and never
when nobody beside anybody has a filter on. Every surface's behaviour is proven
over HTTP in ``tests/api/test_the_reliability_filter.py``.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timezone
from uuid import UUID

from app.bootstrap.composition import build_ruleset
from app.engines.matchfit.core import ReliabilityBand, SearchMode
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Instant, Sport, instant, iso_weekday
from app.modules.player_profile.domain.gender import Gender
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.modules.player_profile.domain.weekly_hours import WeeklyHour, WeeklyHours
from app.modules.player_score.domain.points import PlayerScore, ReliabilityCounts
from app.modules.proposals.infrastructure.matcher_player_fit import MatcherPlayerFit
from app.shared.ids import new_uuid

NOW = instant(datetime(2026, 10, 15, 6, 0, tzinfo=timezone.utc))
#: Long enough ago that nobody's level window is narrowed for being new.
JOINED = instant(datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc))

MARTA, SERGIO, NEREA, IVAN = (new_uuid() for _ in range(4))
NOTHING = ReliabilityCounts(
    turned_up=0, turned_up_of=0, late=0, kept=0, kept_of=0, left_in_dispute=0
)


def a_profile(player_id: UUID, *, minimum: ReliabilityBand | None) -> PlayerProfile:
    profile = PlayerProfile.create(
        player_id=player_id,
        social_tags=SocialTagSelection.from_ids(("PLAYS_TO_WIN", "HERE_TO_IMPROVE")),
        photo_ids=(),
        weekly_hours=WeeklyHours.of([WeeklyHour(day=iso_weekday(6), hour=17)]),
        location=LocationArea.around(50.06, 19.95),
        gender=Gender.WOMAN,
        idempotency_key=f"commit-{player_id}",
        occurred_at=JOINED,
    )
    profile.set_reliability_minimum(minimum, occurred_at=JOINED)
    return profile


class Profiles:
    def __init__(self, profiles: Mapping[UUID, PlayerProfile]) -> None:
        self._profiles = profiles

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        return self._profiles.get(player_id)

    async def save(self, profile: PlayerProfile) -> None:  # pragma: no cover
        raise AssertionError("the pair rule writes nothing")


class NoBlocks:
    async def blocked_pairs_among(
        self, player_ids: Collection[UUID]
    ) -> frozenset[frozenset[UUID]]:
        return frozenset()


class OneLevel:
    """Everybody at padel 2,5: no pair here is kept apart by its Levels."""

    async def estimates_for(self, player_ids, *, sport):
        return {player: SkillEstimate(mu=2.5, sigma=0.4) for player in player_ids}


class Points:
    """``PublishedScoreQuery``, counting how often it is asked."""

    def __init__(self, scores: Mapping[UUID, PlayerScore]) -> None:
        self._scores = scores
        self.reads: list[frozenset[UUID]] = []

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        self.reads.append(frozenset(player_ids))
        return {player: self._scores[player] for player in player_ids}


def a_score(points: int, *, is_new: bool = False) -> PlayerScore:
    return PlayerScore(points=points, is_new=is_new, counts=NOTHING)


#: Marta at 95; Sergio at 70 — Medium; Nerea at 50 and New; Ivan at 80.
SCORES = {
    MARTA: a_score(95),
    SERGIO: a_score(70),
    NEREA: a_score(50, is_new=True),
    IVAN: a_score(80),
}


def a_fit(
    minimums: Mapping[UUID, ReliabilityBand | None], scores=SCORES
) -> tuple[MatcherPlayerFit, Points]:
    points = Points(scores)
    fit = MatcherPlayerFit(
        blocks=NoBlocks(),
        profiles=Profiles(
            {
                player: a_profile(player, minimum=minimums.get(player))
                for player in (MARTA, SERGIO, NEREA, IVAN)
            }
        ),
        ratings=OneLevel(),
        ruleset=build_ruleset(),
        scores=points,
    )
    return fit, points


def pair(one: UUID, other: UUID) -> frozenset[UUID]:
    return frozenset((one, other))


async def unfit(fit: MatcherPlayerFit, *people: UUID, **kwargs):
    return await fit.unfit_pairs(
        people, sport=Sport.PADEL, kind=SearchMode.COMPETITIVE, at=NOW, **kwargs
    )


async def test_at_least_high_keeps_a_medium_player_off_her_courts_and_new_passes():
    fit, _ = a_fit({MARTA: ReliabilityBand.HIGH})

    refused = await unfit(fit, MARTA, SERGIO, NEREA, IVAN)

    assert refused == {pair(MARTA, SERGIO)}


async def test_the_clause_is_asked_both_ways_whoever_holds_the_filter():
    """Sergio's *at least High* keeps him off Ivan's courts too, and Marta's —
    who is Very high — not at all; the pair is one pair either way round."""

    fit, _ = a_fit({SERGIO: ReliabilityBand.HIGH})

    refused = await unfit(fit, MARTA, SERGIO, NEREA, IVAN)

    assert refused == set()

    fit, _ = a_fit({IVAN: ReliabilityBand.HIGH})
    assert await unfit(fit, SERGIO, IVAN) == {pair(SERGIO, IVAN)}


async def test_a_player_below_their_own_filter_is_kept_off_another_filters_courts():
    """Both at *at least High*: Ivan at 80 passes Sergio's, and Sergio at 70
    fails Ivan's — and that is enough."""

    fit, _ = a_fit({SERGIO: ReliabilityBand.HIGH, IVAN: ReliabilityBand.HIGH})

    assert await unfit(fit, SERGIO, IVAN) == {pair(SERGIO, IVAN)}


async def test_a_yes_already_given_is_asked_without_the_filter():
    fit, points = a_fit({MARTA: ReliabilityBand.HIGH})

    refused = await unfit(fit, MARTA, SERGIO, reliability_filter=False)

    assert refused == set()
    assert points.reads == []


async def test_nobody_with_a_filter_reads_no_points_at_all():
    fit, points = a_fit({})

    assert await unfit(fit, MARTA, SERGIO, NEREA, IVAN) == set()
    assert points.reads == []


async def test_a_call_reads_everybody_s_points_once():
    fit, points = a_fit({MARTA: ReliabilityBand.MEDIUM})

    await unfit(fit, MARTA, SERGIO, NEREA, IVAN)

    assert points.reads == [frozenset((MARTA, SERGIO, NEREA, IVAN))]


async def test_one_read_of_the_points_serves_every_kind_of_a_deal():
    """The proposer, the deck and a rescue ask every kind at once: the pair
    rule's reads are made once, and each kind's answer is what asking that
    kind alone would give."""

    fit, points = a_fit({MARTA: ReliabilityBand.HIGH})
    people = (MARTA, SERGIO, NEREA, IVAN)

    by_kind = await fit.unfit_pairs_by_kind(
        people, sport=Sport.PADEL, kinds=list(SearchMode), at=NOW
    )

    assert len(points.reads) == 1
    for kind in SearchMode:
        assert by_kind[kind] == await fit.unfit_pairs(
            people, sport=Sport.PADEL, kind=kind, at=NOW
        )
    assert by_kind[SearchMode.FOR_FUN] == {pair(MARTA, SERGIO)}
