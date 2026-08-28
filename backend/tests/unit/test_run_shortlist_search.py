"""The use case's refusals, and the order it does things in.

Seven codes, distinct at three statuses, because **a client must be able to tell
a transient outage from a refusal about *you*.* Each one is unreachable through
the HTTP suite without breaking a provider on purpose, which is exactly what a
stub is for — and each is the failure mode of a real decision:

- ``account_held`` — the hold points **both ways**, so a held searcher is refused
  at the entry point rather than merely hidden from other people's lists.
- ``gate_data_unavailable`` — *a gate that cannot be evaluated excludes*, and
  *nobody is held* and *we could not find out* are different sentences.
- ``index_too_stale`` — the refusal stands on **quality**, not safety.
- ``search_not_recorded`` — the ``search_id`` **is** the answer's identity, and a
  shortlist returned without its row is a permanently missing denominator.
- ``matchmaking_unavailable`` — when the engine is down the feature is down.
  **Never a fallback list.**

And the order: the record is written **and committed before the answer returns**,
and the exposure write happens after it, outside the transaction, because a
search that ran and was recorded is a search that happened whatever Redis
thought.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Collection, Mapping
from uuid import UUID, uuid4

import pytest

from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.v1 import MatchFitV1
from app.kernel import Instant, InvariantViolated, Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.application.run_shortlist_search import RunShortlistSearch
from app.modules.matchmaking.domain.cards import CardIdentity
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.errors import (
    AccountHeld,
    GateDataUnavailable,
    IndexTooStale,
    MatchmakingUnavailable,
    PlayerProfileNotCommitted,
    PlayIntentNotDeclared,
    SearchNotRecorded,
    SportNotRated,
)
from app.modules.matchmaking.domain.index_staleness import (
    STALENESS_ALARM_AFTER,
    STALENESS_REFUSAL_AFTER,
)
from app.modules.matchmaking.domain.searches import SearchRecord
from app.modules.matchmaking.infrastructure.absent_providers import (
    NoHoldsExist,
    NoMatchHistoryExists,
    NoPlayerScoresExist,
    NoResultUpdateRuleExists,
)
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
)
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.modules.rating.domain.skill_rating import SkillRating
from tests.unit import matchmaking_builders as build
from tests.unit.fake_ledgers import InMemoryExposureLedger

NOW = build.NOW
SEARCHER = build.SEARCHER_ID
SPORT = Sport.PADEL


class FixedClock:
    def now(self) -> Instant:
        return Instant(NOW)


@dataclass
class Profiles:
    profile: PlayerProfile | None

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        return self.profile

    async def save(self, profile: PlayerProfile) -> None:  # pragma: no cover
        raise AssertionError("a search never writes a profile")

    async def exists_for(self, *, player_id: UUID) -> bool:  # pragma: no cover
        return self.profile is not None


@dataclass
class Ratings:
    ratings: list[SkillRating]

    async def find_all_for(self, *, player_id: UUID) -> list[SkillRating]:
        return self.ratings

    async def save(self, rating: SkillRating) -> None:  # pragma: no cover
        raise AssertionError("a search never writes a rating")

    async def exists_for(self, *, player_id: UUID, sport: Sport) -> bool:
        return any(rating.sport is sport for rating in self.ratings)

    async def next_identity(self, **_: object) -> UUID:  # pragma: no cover
        raise AssertionError("a search mints no rating")


@dataclass
class Declarations:
    declaration: PlayIntentDeclaration | None

    async def load(
        self, *, player_id: UUID, sport: Sport
    ) -> PlayIntentDeclaration | None:
        return self.declaration

    async def save(self, declaration) -> None:  # pragma: no cover
        raise AssertionError("a search never declares an intent")


@dataclass
class Blocks:
    exclusions: frozenset[UUID] = frozenset()
    raises: bool = False

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        if self.raises:
            raise BlockStateUnavailable("the block store is unreachable")
        return self.exclusions

    async def blocked_between(self, first: UUID, second: UUID) -> bool:
        return False


@dataclass
class Holds:
    held: frozenset[UUID] = frozenset()

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return frozenset(self.held) & frozenset(player_ids)


class NobodyIsHidden:
    async def may_not_be_shown(
        self, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        return frozenset()


@dataclass
class Snapshots:
    rows: tuple
    caught_up_at: datetime = NOW

    def snapshot(self, partition: Partition) -> CandidateSnapshot:
        return CandidateSnapshot(
            partition=partition,
            rows=self.rows,
            snapshot_version=42,
            caught_up_at=self.caught_up_at,
        )


@dataclass
class Store:
    written: list[SearchRecord] = field(default_factory=list)
    raises: bool = False

    async def record(self, search: SearchRecord) -> None:
        if self.raises:
            raise RuntimeError("the search table is unreachable")
        self.written.append(search)

    async def returned_rows_for(self, **_: object) -> tuple:  # pragma: no cover
        return ()


@dataclass
class Work:
    commits: int = 0
    committed_after: int = -1
    store: Store | None = None

    async def commit(self) -> None:
        self.commits += 1
        self.committed_after = len(self.store.written) if self.store else -1

    async def flush(self) -> None:  # pragma: no cover
        pass

    async def rollback(self) -> None:  # pragma: no cover
        pass


@dataclass
class Cards:
    known: set[UUID] | None = None

    async def identities_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardIdentity]:
        return {
            player_id: CardIdentity(nickname=f"p{index}", photo_id=None)
            for index, player_id in enumerate(player_ids)
            if self.known is None or player_id in self.known
        }


class ARefusingEngine:
    """A scorer that raises. **There is nothing to catch it with**, deliberately:
    a hand-rolled fallback ranker arriving as a hotfix is how a second, worse,
    unexplainable ranking implementation enters the system for ever."""

    version = "matchfit-broken"

    def score(self, **_: object):
        raise InvariantViolated("a candidate row this scorer cannot read")


def a_profile() -> PlayerProfile:
    return PlayerProfile.create(
        player_id=SEARCHER,
        social_tags=SocialTagSelection.from_ids(build.TAGS),
        photo_ids=[],
        availability=AvailabilityGrid.from_codes(build.SEARCHER_SLOTS),
        location=LocationArea.around(
            build.CENTRE.latitude, build.CENTRE.longitude
        ),
        search_radius=SearchRadius.chosen(10),
        gender=Gender.WOMAN,
        gender_preference=GenderPreference.ANY,
        proposals_opt_in_accepted=True,
        consent_copy_version="proposals-2026-08",
        consent_surface=ConsentSurface.ONBOARDING,
        idempotency_key="commit-1",
        occurred_at=Instant(build.SETTLED),
    )


def a_rating(sport: Sport = SPORT) -> SkillRating:
    return SkillRating(
        id=uuid4(),
        player_id=SEARCHER,
        sport=sport,
        mu=build.SEARCHER_MU,
        sigma=build.SEARCHER_SIGMA,
        confidence=62,
        range_low=2.5,
        range_high=3.1,
        band_name="Improver",
        band_lower=2.5,
        band_upper=3.0,
        status="INITIAL_ESTIMATE",
        engine_version="v3",
        updated_at=build.SETTLED,
    )


def a_declaration() -> PlayIntentDeclaration:
    return PlayIntentDeclaration.first_declared(
        player_id=SEARCHER,
        sport=SPORT,
        intent=PlayIntent.COMPETITIVE,
        surface=PlayIntentSurface.RATING_TAIL,
        occurred_at=Instant(build.SETTLED),
    )


#: *Use the default* is not *there is none*, and both are legitimate arguments
#: here — so the absence a test wants is spelled explicitly rather than by
#: passing ``None`` and hoping the builder reads it the intended way.
DEFAULT: object = object()


def use_case(
    *,
    rows: tuple = (),
    profile: object = DEFAULT,
    ratings: list[SkillRating] | None = None,
    declaration: object = DEFAULT,
    blocks: Blocks | None = None,
    holds: Holds | None = None,
    store: Store | None = None,
    work: Work | None = None,
    cards: Cards | None = None,
    engine=None,
    caught_up_at: datetime = NOW,
    exposure: InMemoryExposureLedger | None = None,
) -> RunShortlistSearch:
    store = store or Store()
    work = work or Work(store=store)
    work.store = store
    return RunShortlistSearch(
        clock=FixedClock(),
        ruleset=LIVE_RULESET,
        engine=engine or MatchFitV1(),
        candidates=Snapshots(rows=rows, caught_up_at=caught_up_at),
        searches=store,
        unit_of_work=work,
        profiles=Profiles(a_profile() if profile is DEFAULT else profile),
        ratings=Ratings([a_rating()] if ratings is None else ratings),
        declarations=Declarations(
            a_declaration() if declaration is DEFAULT else declaration
        ),
        blocks=blocks or Blocks(),
        holds=holds or NoHoldsExist(),
        account_status=NobodyIsHidden(),
        history=NoMatchHistoryExists(),
        player_scores=NoPlayerScoresExist(),
        at_stake=NoResultUpdateRuleExists(),
        exposure=exposure or InMemoryExposureLedger(FixedClock()),
        cards=cards or Cards(),
        absent_terms=frozenset({Term.RELIABILITY}),
    )


def a_command(mode: SearchMode = SearchMode.COMPETITIVE) -> RunShortlistSearchCommand:
    return RunShortlistSearchCommand(
        searcher_id=SEARCHER, sport=SPORT, mode=mode, trace_id="trace-1"
    )


# ---------------------------------------------------------------------------
# The refusals
# ---------------------------------------------------------------------------


async def test_a_searcher_with_no_profile_is_refused():
    with pytest.raises(PlayerProfileNotCommitted):
        await use_case(profile=None, ratings=[]).execute(a_command())


async def test_a_searcher_with_no_rating_for_this_sport_is_refused():
    with pytest.raises(SportNotRated):
        await use_case(ratings=[]).execute(a_command())


async def test_a_searcher_who_has_not_declared_is_refused():
    """ADR-0094's interstitial, as a backstop. The search screen is the edit
    surface for the declaration, so this is never the designed path — which is
    exactly why the code has to be distinguishable from the rating one."""

    with pytest.raises(PlayIntentNotDeclared):
        await use_case(declaration=None).execute(a_command())


async def test_a_held_searcher_is_refused_at_the_entry_point():
    """**The hold points both ways.** A held player can still sign in and run a
    search, which is why the searcher's own side is refused here rather than by
    hiding them from other people's lists."""

    with pytest.raises(AccountHeld):
        await use_case(holds=Holds(frozenset({SEARCHER}))).execute(a_command())


async def test_a_block_set_that_cannot_be_read_refuses_the_search():
    """*A gate that cannot be evaluated excludes.* Serving a shortlist on *we
    could not find out* while printing *nobody is blocked* is the one failure
    mode a matcher may not have."""

    with pytest.raises(GateDataUnavailable):
        await use_case(blocks=Blocks(raises=True)).execute(a_command())


async def test_an_index_a_day_behind_refuses_rather_than_serving():
    """**On quality, not safety.** Every fact staleness can cost is a fact about
    who is *worth* meeting — the facts that must be live never enter the index."""

    stale = NOW - STALENESS_REFUSAL_AFTER - timedelta(minutes=1)
    with pytest.raises(IndexTooStale):
        await use_case(caught_up_at=stale).execute(a_command())


async def test_an_index_inside_the_ladders_middle_rung_serves_and_records_it():
    """Fifteen minutes to a day: serve normally, and record the flag. The
    threshold that turns it into a refusal is one rung further on."""

    lagging = NOW - STALENESS_ALARM_AFTER - timedelta(minutes=1)
    answer = await use_case(rows=(build.row(1),), caught_up_at=lagging).execute(
        a_command()
    )

    assert answer.record.index_stale is True
    assert answer.rows, "a stale-but-serving index still answers"


async def test_a_record_that_cannot_be_written_fails_the_search():
    """``docs/adr/0104``: the ``search_id`` **is** the answer's identity."""

    with pytest.raises(SearchNotRecorded):
        await use_case(rows=(build.row(1),), store=Store(raises=True)).execute(
            a_command()
        )


async def test_an_engine_that_raises_takes_the_feature_down():
    """**Never a fallback list.** The refusal is the whole of the recovery."""

    with pytest.raises(MatchmakingUnavailable):
        await use_case(rows=(build.row(1),), engine=ARefusingEngine()).execute(
            a_command()
        )


# ---------------------------------------------------------------------------
# The order of things
# ---------------------------------------------------------------------------


async def test_the_record_is_written_and_committed_before_the_answer_returns():
    store = Store()
    work = Work(store=store)

    answer = await use_case(rows=(build.row(1),), store=store, work=work).execute(
        a_command()
    )

    assert work.commits == 1
    assert work.committed_after == 1, "the commit happened before the record was added"
    assert store.written[0].id == answer.record.id


async def test_an_empty_shortlist_is_still_recorded():
    """*Empty results are recorded exactly like any other search.* There is no
    separate table and no separate path; the absence of a row is never how
    emptiness is expressed."""

    store = Store()
    answer = await use_case(store=store).execute(a_command())

    assert answer.rows == ()
    assert store.written[0].counts.n_returned == 0
    assert store.written[0].pool_description.players_in_range == 0


async def test_the_exposure_write_happens_after_the_commit_and_never_gates_it():
    """The **gate is the cache and the evidence is the row**: losing this write
    costs a slightly duller list tomorrow, and it is deliberately outside the
    transaction the search's own record is committed in."""

    from app.modules.matchmaking.domain.ledgers import week_of

    exposure = InMemoryExposureLedger(FixedClock())
    row = build.row(1)
    await use_case(rows=(row,), exposure=exposure).execute(a_command())

    shown = await exposure.times_shown(
        sport=SPORT, week=week_of(Instant(NOW)), player_ids=[UUID(row.player_id)]
    )
    assert shown[UUID(row.player_id)] == 1


async def test_a_row_whose_card_cannot_be_assembled_is_dropped_before_the_record():
    """So that ``n_returned`` and the number of ``RETURNED`` rows written agree —
    which is the whole of what makes ``n_returned`` a redaction detector later.

    A card with no nickname is not a card, so the row is dropped rather than
    shown blank.
    """

    known = build.row(1)
    nameless = build.row(2)
    store = Store()

    answer = await use_case(
        rows=(known, nameless),
        cards=Cards(known={UUID(known.player_id)}),
        store=store,
    ).execute(a_command())

    assert [row.scored.player_id for row in answer.rows] == [known.player_id]
    assert store.written[0].counts.n_returned == 1


async def test_at_stake_is_omitted_in_for_fun_by_the_methods_own_name():
    """A for-fun game is never counted, so the figure is not
    absent-because-unavailable — it is **meaningless**, and asking about it is a
    category error rather than a mode flag."""

    answer = await use_case(rows=(build.row(1),)).execute(
        a_command(SearchMode.FOR_FUN)
    )

    assert all(row.at_stake is None for row in answer.rows)


async def test_the_record_carries_both_stamps_and_the_snapshot_version():
    """*How the maths works* and *what the numbers were* are two different
    claims, and a search is only reproducible with both plus the watermark."""

    store = Store()
    await use_case(rows=(build.row(1),), store=store).execute(a_command())
    written = store.written[0]

    assert written.engine_version == MatchFitV1().version
    assert written.ruleset_version == LIVE_RULESET.version
    assert written.snapshot_version == 42
    assert written.trace_id == "trace-1"
    assert written.latency_ms_by_stage.keys() >= {"read_searcher", "pipeline"}
