"""What a confirmed result does to the two people who played it.

**The acceptance criterion of #304, driven through the use case.** A confirmed
counted result moves both players' μ and tightens both σ; an unscored one moves
neither; a friendly moves neither. The first is the whole point of the ticket and
the other two are ``docs/adr/0049``'s *an evening, not evidence* and *a friendly
is a thing people choose*, executable at last.

**The ledger is a hand-written stub and the games are real aggregates.** What is
under test is the catch-up's *order* and its idempotency — that a snapshot is read
before anything moves, that a game already folded is skipped, that a race is
stepped over — and the ledger's own behaviour is held to ``tests/demands/`` against
the adapter that reads the log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.application.events import EventStreamVersionConflict
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_CALIBRATING,
    STATUS_INITIAL_ESTIMATE,
    band_for,
    confidence_percent,
    likely_range,
)
from app.engines.racketskill.v3.engine import SIGMA_FLOOR
from app.kernel import Instant, Sport, instant
from app.modules.games.domain.ports import ConfirmedGame
from app.modules.rating.application.settle_results import SettleRatingsOnResults
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.ids import new_uuid

NOW = instant(datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc))
SETTLED_AT = instant(NOW - timedelta(hours=2))


class FixedClock:
    def now(self) -> Instant:
        return NOW


@dataclass
class Ledger:
    """``ConfirmedResultLedger`` over a list somebody wrote by hand."""

    results: tuple[ConfirmedGame, ...] = ()
    reads: int = 0

    async def confirmed_counted_results(self, *, now: Instant):
        self.reads += 1
        return self.results


@dataclass
class Ratings:
    """``SkillRatingRepository`` over a dict, remembering what it was asked to save."""

    held: dict[tuple[UUID, Sport], SkillRating] = field(default_factory=dict)
    saved: list[SkillRating] = field(default_factory=list)
    #: The events that were appended, kept rather than dropped. A Level is
    #: carried to two decimals, so two moves a thousandth apart are the same μ —
    #: and the **delta** is the only place a property about their difference can
    #: be asserted at all.
    appended: list[object] = field(default_factory=list)
    conflict_on: frozenset[UUID] = frozenset()

    async def find_for(self, *, player_id: UUID, sport: Sport) -> SkillRating | None:
        return self.held.get((player_id, sport))

    async def save(self, rating: SkillRating) -> None:
        if rating.player_id in self.conflict_on:
            raise EventStreamVersionConflict("somebody else got there first")
        self.appended.extend(rating.pull_events())
        self.saved.append(rating)

    async def find_all_for(self, *, player_id: UUID):  # pragma: no cover
        raise AssertionError("the catch-up reads one sport at a time")

    async def exists_for(self, **_: object) -> bool:  # pragma: no cover
        raise AssertionError("the catch-up loads the aggregate it will move")


@dataclass
class Work:
    commits: int = 0
    rollbacks: int = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def a_rating(
    *,
    player_id: UUID,
    mu: float,
    sigma: float = SIGMA_FLOOR,
    sport: Sport = Sport.TENNIS,
) -> SkillRating:
    band = band_for(mu)
    low, high = likely_range(mu, sigma)
    rating = SkillRating.initialise(
        rating_id=skill_rating_id(player_id, sport),
        player_id=player_id,
        sport=sport,
        result=AssessmentResult(
            mu=mu,
            sigma=sigma,
            confidence=confidence_percent(sigma),
            range_low=round(low, 2),
            range_high=round(high, 2),
            band=BandView(name=band.label, lower=band.lower, upper=band.upper),
            status=STATUS_INITIAL_ESTIMATE,
            questions_asked=7,
            engine_version="racketskill-fusion-v3",
            confidence_ceiling=confidence_percent(sigma),
        ),
        source_assessment_id=new_uuid(),
        occurred_at=NOW - timedelta(days=30),
    )
    rating.pull_events()
    return rating


def a_result(
    *,
    winners: tuple[UUID, ...],
    losers: tuple[UUID, ...],
    sport: Sport = Sport.TENNIS,
    confirmed_at: Instant = SETTLED_AT,
) -> ConfirmedGame:
    return ConfirmedGame(
        game_id=new_uuid(),
        sport=sport,
        winners=winners,
        losers=losers,
        played_at=instant(confirmed_at - timedelta(days=1)),
        confirmed_at=confirmed_at,
    )


def catch_up(*, ledger: Ledger, ratings: Ratings, work: Work | None = None):
    return SettleRatingsOnResults(
        results=ledger,
        ratings=ratings,
        uow=work or Work(),
        clock=FixedClock(),
    )


def held(*ratings: SkillRating) -> Ratings:
    return Ratings(
        held={(rating.player_id, rating.sport): rating for rating in ratings}
    )


# ---------------------------------------------------------------------------
# What a confirmed result does
# ---------------------------------------------------------------------------


async def test_a_confirmed_counted_result_moves_both_levels_and_tightens_both():
    """#304's acceptance, in one test. **Both players, both variables.**"""

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
    )
    ledger = Ledger((a_result(winners=(winner,), losers=(loser,)),))

    settled = await catch_up(ledger=ledger, ratings=ratings).execute()

    won = ratings.held[(winner, Sport.TENNIS)]
    lost = ratings.held[(loser, Sport.TENNIS)]
    assert won.mu > 3.00
    assert lost.mu < 3.00
    assert won.sigma < SIGMA_FLOOR
    assert lost.sigma < SIGMA_FLOOR
    assert settled.games == 1
    assert settled.ratings == 2


async def test_the_first_result_leaves_initial_estimate_behind():
    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
    )

    await catch_up(
        ledger=Ledger((a_result(winners=(winner,), losers=(loser,)),)), ratings=ratings
    ).execute()

    assert ratings.held[(winner, Sport.TENNIS)].status == STATUS_CALIBRATING
    assert ratings.held[(loser, Sport.TENNIS)].status == STATUS_CALIBRATING


async def test_the_move_is_dated_from_when_the_result_became_final():
    """Not from the run that noticed it.

    A laptop switched off for a week must produce the same stream as one that was
    not, or the same history has two answers.
    """

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
    )

    await catch_up(
        ledger=Ledger((a_result(winners=(winner,), losers=(loser,)),)), ratings=ratings
    ).execute()

    assert ratings.held[(winner, Sport.TENNIS)].updated_at == SETTLED_AT


async def test_a_result_the_ledger_never_publishes_moves_nobody():
    """*An evening, not evidence* and *a friendly is a thing people choose*.

    Both are enforced by the read rather than by a branch here, which is exactly
    why this test drives an empty ledger: an unscored game and a friendly reach
    this use case in the same way — they do not.
    """

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
    )

    settled = await catch_up(ledger=Ledger(()), ratings=ratings).execute()

    assert ratings.held[(winner, Sport.TENNIS)].mu == 3.00
    assert ratings.held[(loser, Sport.TENNIS)].mu == 3.00
    assert ratings.held[(winner, Sport.TENNIS)].sigma == SIGMA_FLOOR
    assert settled == type(settled)(games=0, ratings=0, unrated=0, conflicts=0)


# ---------------------------------------------------------------------------
# Idempotency — the rating streams are the cursor
# ---------------------------------------------------------------------------


async def test_running_twice_moves_nothing_the_second_time():
    """The whole of the catch-up's safety, and why it needs no cursor row."""

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
    )
    ledger = Ledger((a_result(winners=(winner,), losers=(loser,)),))

    first = await catch_up(ledger=ledger, ratings=ratings).execute()
    after_one = ratings.held[(winner, Sport.TENNIS)].mu
    second = await catch_up(ledger=ledger, ratings=ratings).execute()

    assert first.ratings == 2
    assert second.ratings == 0
    assert second.games == 0
    assert ratings.held[(winner, Sport.TENNIS)].mu == after_one
    # And it re-read, because the ledger consumes nothing: a run that dies half
    # way has to be a repeated read rather than a lost result.
    assert ledger.reads == 2


async def test_a_race_on_one_rating_is_counted_and_stepped_over():
    """Ending the run on the first conflict would stall every process at it."""

    winner, loser = new_uuid(), new_uuid()
    other_winner, other_loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
        a_rating(player_id=other_winner, mu=3.00),
        a_rating(player_id=other_loser, mu=3.00),
    )
    ratings.conflict_on = frozenset({winner})
    work = Work()

    settled = await catch_up(
        ledger=Ledger(
            (
                a_result(winners=(winner,), losers=(loser,)),
                a_result(
                    winners=(other_winner,),
                    losers=(other_loser,),
                    confirmed_at=instant(SETTLED_AT + timedelta(minutes=1)),
                ),
            )
        ),
        ratings=ratings,
        work=work,
    ).execute()

    assert settled.conflicts == 1
    assert settled.games == 1
    assert work.rollbacks == 1
    assert ratings.held[(other_winner, Sport.TENNIS)].mu > 3.00


# ---------------------------------------------------------------------------
# A four
# ---------------------------------------------------------------------------


async def test_a_four_moves_four_levels_against_one_snapshot():
    """Nobody's move depends on where they came in the loop.

    **The partners are deliberately a Level apart.** Four identical ratings would
    move identically whatever the rule did, so a test built that way cannot tell
    *all four move equally* from *each player is priced on their own μ* — which is
    the option that was rejected, and the one this would otherwise have shipped.
    """

    one, two, three, four = (new_uuid() for _ in range(4))
    ratings = held(
        a_rating(player_id=one, mu=4.00, sigma=0.30, sport=Sport.PADEL),
        a_rating(player_id=two, mu=2.00, sigma=0.30, sport=Sport.PADEL),
        a_rating(player_id=three, mu=3.00, sigma=0.30, sport=Sport.PADEL),
        a_rating(player_id=four, mu=3.00, sigma=0.30, sport=Sport.PADEL),
    )

    settled = await catch_up(
        ledger=Ledger(
            (
                a_result(
                    winners=(one, two), losers=(three, four), sport=Sport.PADEL
                ),
            )
        ),
        ratings=ratings,
    ).execute()

    assert settled.ratings == 4
    moved = [ratings.held[(who, Sport.PADEL)] for who in (one, two, three, four)]
    # The winners moved up by **one** amount and the losers down by one amount,
    # a Level apart though the partners are.
    assert moved[0].mu - 4.00 == pytest.approx(moved[1].mu - 2.00, abs=1e-9)
    assert moved[2].mu - 3.00 == pytest.approx(moved[3].mu - 3.00, abs=1e-9)
    assert moved[0].mu > 4.00 and moved[1].mu > 2.00
    assert moved[2].mu < 3.00 and moved[3].mu < 3.00


async def test_partners_a_level_apart_keep_their_own_certainty():
    """One Level move, two uncertainties. *Skill and certainty are separate.*"""

    newcomer, veteran, home, away = (new_uuid() for _ in range(4))
    ratings = held(
        a_rating(player_id=newcomer, mu=3.00, sigma=SIGMA_FLOOR, sport=Sport.PADEL),
        a_rating(player_id=veteran, mu=3.00, sigma=0.15, sport=Sport.PADEL),
        a_rating(player_id=home, mu=3.00, sigma=0.30, sport=Sport.PADEL),
        a_rating(player_id=away, mu=3.00, sigma=0.30, sport=Sport.PADEL),
    )

    await catch_up(
        ledger=Ledger(
            (
                a_result(
                    winners=(newcomer, veteran),
                    losers=(home, away),
                    sport=Sport.PADEL,
                ),
            )
        ),
        ratings=ratings,
    ).execute()

    fresh = ratings.held[(newcomer, Sport.PADEL)]
    settled = ratings.held[(veteran, Sport.PADEL)]
    assert fresh.mu == settled.mu
    assert fresh.sigma > settled.sigma
    assert fresh.sigma < SIGMA_FLOOR


async def test_carrying_a_weaker_partner_to_a_win_pays_more():
    """The average is what made it the upset — and the use case reads it that way."""

    async def won_by(partner_mu: float) -> float:
        you, partner = new_uuid(), new_uuid()
        home, away = new_uuid(), new_uuid()
        ratings = held(
            a_rating(player_id=you, mu=3.60, sigma=0.25, sport=Sport.PADEL),
            a_rating(player_id=partner, mu=partner_mu, sigma=0.25, sport=Sport.PADEL),
            a_rating(player_id=home, mu=3.40, sigma=0.20, sport=Sport.PADEL),
            a_rating(player_id=away, mu=3.30, sigma=0.20, sport=Sport.PADEL),
        )
        await catch_up(
            ledger=Ledger(
                (
                    a_result(
                        winners=(you, partner),
                        losers=(home, away),
                        sport=Sport.PADEL,
                    ),
                )
            ),
            ratings=ratings,
        ).execute()
        (mine,) = [
            one for one in ratings.appended if one.player_id == you
        ]
        return mine.win_delta

    assert await won_by(2.60) > await won_by(3.60) > 0


async def test_a_four_is_worth_less_than_a_singles_game_between_equals():
    """*You were half of what happened, so it is half the evidence about you.*"""

    padel_one, padel_two = new_uuid(), new_uuid()
    padel_home, padel_away = new_uuid(), new_uuid()
    padel = held(
        *(
            a_rating(player_id=who, mu=3.00, sigma=0.30, sport=Sport.PADEL)
            for who in (padel_one, padel_two, padel_home, padel_away)
        )
    )
    await catch_up(
        ledger=Ledger(
            (
                a_result(
                    winners=(padel_one, padel_two),
                    losers=(padel_home, padel_away),
                    sport=Sport.PADEL,
                ),
            )
        ),
        ratings=padel,
    ).execute()

    winner, loser = new_uuid(), new_uuid()
    singles = held(
        a_rating(player_id=winner, mu=3.00, sigma=0.30),
        a_rating(player_id=loser, mu=3.00, sigma=0.30),
    )
    await catch_up(
        ledger=Ledger((a_result(winners=(winner,), losers=(loser,)),)), ratings=singles
    ).execute()

    four = padel.held[(padel_one, Sport.PADEL)]
    two = singles.held[(winner, Sport.TENNIS)]
    assert 3.00 < four.mu < two.mu
    # And it bought less certainty, from the same starting point.
    assert four.sigma > two.sigma


# ---------------------------------------------------------------------------
# Unrated seats
# ---------------------------------------------------------------------------


async def test_a_side_nobody_on_it_is_rated_moves_nobody_and_is_reported():
    """There is nothing to price the other side against, so nothing moves.

    And it is **not** recorded as applied: a rating that arrives later still
    finds the result, which is the benefit of the streams being the cursor rather
    than a cursor row that had already walked past it.
    """

    winner, loser = new_uuid(), new_uuid()
    ratings = held(a_rating(player_id=winner, mu=3.00))
    ledger = Ledger((a_result(winners=(winner,), losers=(loser,)),))

    settled = await catch_up(ledger=ledger, ratings=ratings).execute()

    assert settled.ratings == 0
    assert settled.unrated == 1
    assert ratings.held[(winner, Sport.TENNIS)].mu == 3.00
    assert ratings.held[(winner, Sport.TENNIS)].counted_results == 0


async def test_a_result_in_a_sport_nobody_is_rated_in_moves_nobody():
    """A Level is per ``(player, sport)``, and a padel evening is not tennis."""

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00, sport=Sport.TENNIS),
        a_rating(player_id=loser, mu=3.00, sport=Sport.TENNIS),
    )

    settled = await catch_up(
        ledger=Ledger(
            (a_result(winners=(winner,), losers=(loser,), sport=Sport.PADEL),)
        ),
        ratings=ratings,
    ).execute()

    assert settled.ratings == 0
    assert settled.unrated == 2
    assert ratings.held[(winner, Sport.TENNIS)].mu == 3.00


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


async def test_results_are_folded_in_the_order_the_ledger_publishes_them():
    """A Level is moved against the Levels as they stood, so the order is a rule.

    Two results between the same pair, the second read against the first's
    output: the second win is worth **less** than the first, because after the
    first the platform is surer of them and the gap it opened made the second win
    less surprising.
    """

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00),
        a_rating(player_id=loser, mu=3.00),
    )
    first = a_result(winners=(winner,), losers=(loser,))
    second = a_result(
        winners=(winner,),
        losers=(loser,),
        confirmed_at=instant(SETTLED_AT + timedelta(hours=1)),
    )

    await catch_up(
        ledger=Ledger((first,)), ratings=ratings
    ).execute()
    after_one = ratings.held[(winner, Sport.TENNIS)].mu
    await catch_up(ledger=Ledger((first, second)), ratings=ratings).execute()
    after_two = ratings.held[(winner, Sport.TENNIS)].mu

    assert after_two > after_one > 3.00
    assert (after_two - after_one) < (after_one - 3.00) + 1e-9
    assert ratings.held[(winner, Sport.TENNIS)].counted_results == 2


@pytest.mark.parametrize("sport", [Sport.TENNIS, Sport.SQUASH])
async def test_a_singles_sport_is_priced_whole(sport):
    """Nothing is shared, so the whole result is evidence about you."""

    winner, loser = new_uuid(), new_uuid()
    ratings = held(
        a_rating(player_id=winner, mu=3.00, sport=sport),
        a_rating(player_id=loser, mu=3.00, sport=sport),
    )

    await catch_up(
        ledger=Ledger((a_result(winners=(winner,), losers=(loser,), sport=sport),)),
        ratings=ratings,
    ).execute()

    assert ratings.held[(winner, sport)].mu == pytest.approx(3.15, abs=0.001)
