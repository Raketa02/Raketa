"""The card's record block, over ``games``' published reads.

**Two rules, and both are inversions of what the provider answers.**
``counted_games_for`` answers a *measured* zero for everybody it is asked about —
the games were counted and none of them was theirs — and a card may not print
one, because on that surface *nought games* and *no record* would be one absence
in two spellings. And a game whose result nobody agreed is in the count and not
in the run: an unscored game is an evening, not evidence.

The provider's own behaviour is contracted in ``tests/demands/`` against the
aggregate. What is asserted here is the **translation**, which is this module's
and nobody else's.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping
from uuid import UUID, uuid4

import pytest

from app.kernel import Instant, Sport
from app.modules.games.domain.ports import CountedResult
from app.modules.games.domain.results import Outcome
from app.modules.matchmaking.domain.searches import GameResult
from app.modules.matchmaking.infrastructure.games_card_records import (
    GamesPlayedAndAgreed,
    _refuse_two_runs,
)

NOW = datetime(2026, 9, 4, 19, 0, tzinfo=timezone.utc)
ALICE = uuid4()
BRUNO = uuid4()
CHIARA = uuid4()


class FixedClock:
    def now(self) -> datetime:
        return NOW


class Games:
    """``GameHistoryQuery``, answering only the two reads a card uses.

    The other three are not stubbed on purpose: a source that called one of them
    would fail here rather than quietly paying for a read the card has no use
    for.
    """

    def __init__(
        self,
        *,
        counts: Mapping[UUID, int],
        results: Mapping[UUID, tuple[CountedResult, ...]] | None = None,
    ) -> None:
        self._counts = counts
        self._results = results or {}
        self.asked_counts: list[frozenset[UUID]] = []
        self.asked_results: list[frozenset[UUID]] = []

    async def counted_games_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, int]:
        wanted = frozenset(player_ids)
        self.asked_counts.append(wanted)
        # The provider's own rule: everybody asked about gets a count.
        return {player_id: self._counts.get(player_id, 0) for player_id in wanted}

    async def recent_results_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, tuple[CountedResult, ...]]:
        wanted = frozenset(player_ids)
        self.asked_results.append(wanted)
        return {
            player_id: results
            for player_id, results in self._results.items()
            if player_id in wanted
        }


def result(outcome: Outcome, days_ago: int) -> CountedResult:
    return CountedResult(
        game_id=uuid4(),
        sport=Sport.PADEL,
        outcome=outcome,
        played_at=Instant(NOW - timedelta(days=days_ago)),
    )


def source(games: Games) -> GamesPlayedAndAgreed:
    return GamesPlayedAndAgreed(games=games, clock=FixedClock())


async def test_a_measured_zero_becomes_an_absence_rather_than_a_nought():
    """The inversion this adapter exists for.

    ``games`` is right to answer ``0`` — it counted the games and none of them
    was this player's. The card is right not to print it, because *0 games* and
    *no record* are the same thing and this surface spells absence one way.
    """

    records = await source(Games(counts={ALICE: 0, BRUNO: 3})).records_for(
        [ALICE, BRUNO]
    )

    assert ALICE not in records, "a nought reached the card as a figure"
    assert records[BRUNO].counted_games == 3


async def test_a_run_of_form_keeps_the_order_the_provider_answered_in():
    """Oldest to newest, because the row is read left to right as a run.

    Reversing here would be a second answer to *which way round*, written where
    nobody would look for it — and a client that reversed a list can reverse it
    wrongly.
    """

    games = Games(
        counts={ALICE: 4},
        results={
            ALICE: (
                result(Outcome.LOSS, days_ago=30),
                result(Outcome.WIN, days_ago=9),
                result(Outcome.WIN, days_ago=2),
            )
        },
    )

    records = await source(games).records_for([ALICE])

    assert records[ALICE].last_five == (
        GameResult.LOSS,
        GameResult.WIN,
        GameResult.WIN,
    )


async def test_counted_games_without_an_agreed_score_are_a_count_and_no_run():
    """An unscored game is **an evening, not evidence**.

    It says these people were on a court, so it is in the count; it moved
    nobody's Level, so there is nothing for the run of form to say about it. The
    card draws the first block and not the second, and neither absence is the
    other.
    """

    records = await source(Games(counts={ALICE: 2}, results={})).records_for([ALICE])

    assert records[ALICE].counted_games == 2
    assert records[ALICE].last_five == ()


async def test_the_run_is_never_padded_to_five():
    """Fewer than five is a real answer, and the card draws the gap."""

    games = Games(
        counts={ALICE: 1}, results={ALICE: (result(Outcome.WIN, days_ago=1),)}
    )

    records = await source(games).records_for([ALICE])

    assert records[ALICE].last_five == (GameResult.WIN,)


async def test_it_is_one_read_per_fact_and_never_one_per_row():
    """*One batched read per shortlist*, which is the shape every set read in
    this module has — and the reason the card's price is bounded by the twenty
    rows that survived the floor rather than by the pool."""

    games = Games(counts={ALICE: 1, BRUNO: 2, CHIARA: 3})

    await source(games).records_for([ALICE, BRUNO, CHIARA])

    assert games.asked_counts == [frozenset({ALICE, BRUNO, CHIARA})]
    assert games.asked_results == [frozenset({ALICE, BRUNO, CHIARA})]


async def test_nobody_asked_about_is_nobody_read_about():
    """An empty shortlist pays for no read at all."""

    games = Games(counts={ALICE: 5})

    assert await source(games).records_for([]) == {}
    assert games.asked_counts == []
    assert games.asked_results == []


def test_the_run_length_is_spelled_twice_and_a_disagreement_stops_the_process():
    """The import-time check, driven at a disagreement.

    ``games`` may not import ``matchmaking``, so *how many* is written down once
    per context. What is avoidable about that is it being silent: a card asking
    for five and handed six would draw a longer run than it says it draws, and
    nothing would fail.
    """

    with pytest.raises(RuntimeError, match="spelled twice"):
        _refuse_two_runs(5, 6)
