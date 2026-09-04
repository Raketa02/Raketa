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

from app.engines.matchfit.core import DegradedReason, SearchMode, Term
from app.engines.matchfit.v1 import MatchFitV1
from app.kernel import Instant, InvariantViolated, Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.application.run_shortlist_search import RunShortlistSearch
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.cards import CardIdentity
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.declines import DECLINE_SUPPRESS
from app.shared.domain.errors import AccountHeld
from app.modules.matchmaking.domain.errors import (
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
from app.modules.matchmaking.domain.prompts import Prompt
from app.modules.matchmaking.domain.relaxation import Rung
from app.modules.matchmaking.domain.searches import InclusionReason, SearchRecord
from app.modules.matchmaking.infrastructure.absent_providers import (
    NoHoldsExist,
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
from tests.unit.fake_ledgers import InMemoryExposureLedger, InMemoryPromptLedger

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


class NothingHasHappenedBetweenAnybody:
    """``MatchHistoryQuery`` over a world where nobody has been asked anything.

    A hand-written stub rather than the deleted ``NoMatchHistoryExists``: the
    real provider is now half ``challenges``, which needs a database and a
    challenge in it, and this file is about the workbench's **order** rather than
    about anybody's history. The port's real behaviour is held to
    ``tests/demands/``, which arranges through the aggregate.

    Every count is a zero here because there is nothing seated anywhere, and that
    is the same shape the provider answers with — every player asked about gets
    a count.
    """

    async def pairwise_counterparts(self, searcher_id: UUID):
        return ()

    async def open_challenges(self, searcher_id: UUID):
        return ()

    async def late_change_threshold(self):
        return None

    async def open_challenge_counts(self, player_ids: Collection[UUID]):
        return {player_id: 0 for player_id in player_ids}


@dataclass
class Yeses:
    """Who has said *Let's play* to the searcher, and how long ago.

    Only the read the search path makes is implemented, and it records the
    population it was asked about: the whole safety property of that method is
    that it is **bounded by the candidate set**, so a test can assert the search
    never asked about anybody outside the box.
    """

    days_ago: dict[UUID, int] = field(default_factory=dict)
    asked_about: list[tuple[UUID, ...]] = field(default_factory=list)

    async def days_ago_towards(
        self,
        *,
        player_id: UUID,
        sport,
        senders: Collection[UUID],
        now: datetime,
    ) -> dict[UUID, int]:
        self.asked_about.append(tuple(senders))
        return {
            sender: age
            for sender, age in self.days_ago.items()
            if sender in set(senders)
        }


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
class Declines:
    """The durable record of every *not now*, as a set and a stub that breaks.

    It records the window it was asked about, because *thirty days* is the whole
    of what the read means and a filter that asked about *ever* would silence a
    question the player answered a year ago.
    """

    silenced: frozenset = field(default_factory=frozenset)
    raises: bool = False
    asked: list[tuple[UUID, Sport, datetime]] = field(default_factory=list)

    async def record(self, decline) -> None:  # pragma: no cover
        raise AssertionError("a search never records a decline")

    async def suppressed_for(self, *, player_id, sport, since):
        if self.raises:
            raise RuntimeError("the decline table is unreachable")
        self.asked.append((player_id, sport, since))
        return frozenset(self.silenced)


@dataclass
class Store:
    written: list[SearchRecord] = field(default_factory=list)
    raises: bool = False

    async def record(self, search: SearchRecord) -> None:
        if self.raises:
            raise RuntimeError("the search table is unreachable")
        self.written.append(search)

    async def find(
        self, *, search_id: UUID, searcher_id: UUID
    ) -> SearchRecord | None:
        """The row this store wrote, or nothing. **Their own row only.**

        A rung is taken by citing the search that offered it, so a stub that
        always answered ``None`` could not tell *nobody offered that* from *the
        offer is right there* — which is the whole of what the ladder's bound is
        about.
        """

        for search in self.written:
            if search.id == search_id and search.searcher_id == searcher_id:
                return search
        return None

    async def widenings_taken(
        self, *, searcher_id: UUID, sport: Sport, radius_km: int
    ) -> int:
        """This radius, taken by this searcher, counted off the rows themselves.

        The rows are the only place a taken rung is recorded — a widen touches
        no profile — so the stub counts them rather than answering a constant.
        """

        return sum(
            1
            for search in self.written
            if search.searcher_id == searcher_id
            and search.sport is sport
            and search.rung_taken is not None
            and search.pool_description.radius_km_used == radius_km
        )


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
            player_id: CardIdentity(nickname=f"p{index}", photo_id=None, review=None)
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


def a_profile(*, committed_at: datetime = build.SETTLED) -> PlayerProfile:
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
        occurred_at=Instant(committed_at),
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
    interest: "Yeses | None" = None,
    prompts=None,
    declines: "Declines | None" = None,
    meter: object = None,
) -> RunShortlistSearch:
    store = store or Store()
    work = work or Work(store=store)
    work.store = store
    return RunShortlistSearch(
        workbench=SearchWorkbench(
            clock=FixedClock(),
            ruleset=LIVE_RULESET,
            searches=store,
            unit_of_work=work,
            candidates=Snapshots(rows=rows, caught_up_at=caught_up_at),
            profiles=Profiles(a_profile() if profile is DEFAULT else profile),
            ratings=Ratings([a_rating()] if ratings is None else ratings),
            declarations=Declarations(
                a_declaration() if declaration is DEFAULT else declaration
            ),
            blocks=blocks or Blocks(),
            holds=holds or NoHoldsExist(),
            account_status=NobodyIsHidden(),
            history=NothingHasHappenedBetweenAnybody(),
            player_scores=NoPlayerScoresExist(),
            at_stake=NoResultUpdateRuleExists(),
            exposure=exposure or InMemoryExposureLedger(FixedClock()),
            interest=interest or Yeses(),
            cards=cards or Cards(),
            absent_terms=frozenset({Term.RELIABILITY}),
            meter=meter,
        ),
        ruleset=LIVE_RULESET,
        engine=engine or MatchFitV1(),
        searches=store,
        prompts=prompts or InMemoryPromptLedger(FixedClock()),
        declines=declines or Declines(),
    )


def a_command(
    mode: SearchMode = SearchMode.COMPETITIVE,
    *,
    availability_override: tuple[tuple[int, str], ...] | None = None,
    offered_by_search_id: UUID | None = None,
    rung: Rung | None = None,
) -> RunShortlistSearchCommand:
    return RunShortlistSearchCommand(
        searcher_id=SEARCHER,
        sport=SPORT,
        mode=mode,
        availability_override=availability_override,
        offered_by_search_id=offered_by_search_id,
        rung=rung,
        trace_id="trace-1",
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
    assert answer.record.returned, "a stale-but-serving index still answers"


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
# One climb per search screen
# ---------------------------------------------------------------------------


async def test_a_search_that_took_a_rung_prices_no_second_climb():
    """**The ladder does not chain.**

    The widened radius *is* the searcher's radius by the time the ladder is
    priced, so a rung offered on a search that already took one would be a rung
    off the widening — and four taps from 8 km would land on the 50 km ceiling
    without the player being asked once. ``relaxation.py``'s *there is no third
    radius rung* is that sentence, and this is where it binds.
    """

    store = Store()
    search = use_case(rows=(build.row(1),), store=store)
    offered = await search.execute(a_command())
    assert offered.record.rung_offers, "nothing was offered; this proves nothing"

    climbed = await search.execute(
        a_command(offered_by_search_id=offered.record.id, rung=Rung.B)
    )

    assert climbed.record.rung_taken is Rung.B
    assert climbed.record.rung_offers == ()


async def test_a_times_rung_ends_the_ladder_exactly_as_a_radius_rung_does():
    """**By climb and not by ask.**

    The guard reads ``rung_taken``, so the cheapest rung spends the climb too.
    A then B would be two climbs on one screen, and rung A can **evict** — a
    radius rung priced after it would be priced over a population the player
    never chose. All three rungs travel on the offer, so somebody who wants
    distance takes the radius rung and is not made to spend the climb on times.
    """

    week = ((3, "EVENING"),)
    store = Store()
    search = use_case(
        rows=(
            build.row(1, mu=3.22, slots=("2:EVENING",)),
            build.row(2, mu=3.22, slots=("2:EVENING",)),
        ),
        store=store,
    )
    offered = await search.execute(a_command(availability_override=week))
    times = [
        offer for offer in offered.record.rung_offers or () if offer.rung is Rung.A
    ]
    assert times and times[0].slot == "2:EVENING", "no times rung; this proves nothing"

    climbed = await search.execute(
        a_command(
            availability_override=week,
            offered_by_search_id=offered.record.id,
            rung=Rung.A,
        )
    )

    assert climbed.record.rung_taken is Rung.A
    assert climbed.record.rung_offers == (), "the radius rungs did not survive it"


async def test_the_climbed_search_says_empty_and_never_not_computed():
    """**No new field, on the request or the response.**

    ``null`` already means *your list was long enough that nobody priced a rung*,
    which is false about a list that is still short. So the refusal is an empty
    list, and the record's own ``rung_taken`` beside it is what tells the two
    empties apart.
    """

    plenty = tuple(build.row(one) for one in range(1, 8))
    long_enough = await use_case(rows=plenty).execute(a_command())
    assert long_enough.record.rung_offers is None, "the other empty, spelled null"

    store = Store()
    search = use_case(rows=(build.row(1),), store=store)
    offered = await search.execute(a_command())

    climbed = await search.execute(
        a_command(offered_by_search_id=offered.record.id, rung=Rung.B)
    )

    assert climbed.record.rung_offers == ()
    assert climbed.record.rung_taken is Rung.B, "and this is what tells them apart"


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

    assert answer.record.returned == ()
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


async def test_a_newcomers_search_writes_both_counts_and_an_ordinary_one_does_not():
    """The absorption tally is *appearances in a newcomer's list*, so it is
    written by the searches that make one and by no others.

    Two counts in one bucket. Being volunteered into a newcomer's list is being
    shown, plus one further fact about who was looking — so the newcomer's search
    writes both families over the same rows, and a settled player's search moves
    only the first.
    """

    from app.modules.matchmaking.domain.ledgers import week_of

    week = week_of(Instant(NOW))
    row = build.row(1)
    ids = [UUID(row.player_id)]

    settled = InMemoryExposureLedger(FixedClock())
    await use_case(rows=(row,), exposure=settled).execute(a_command())

    newcomer = InMemoryExposureLedger(FixedClock())
    await use_case(
        rows=(row,),
        profile=a_profile(committed_at=NOW - timedelta(days=2)),
        exposure=newcomer,
    ).execute(a_command())

    async def volunteered(ledger: InMemoryExposureLedger) -> int:
        counts = await ledger.times_shown_to_a_newcomer(
            sport=SPORT, week=week, player_ids=ids
        )
        return counts[ids[0]]

    assert await volunteered(settled) == 0
    assert await volunteered(newcomer) == 1


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

    assert [str(row.player_id) for row in answer.record.returned] == [
        known.player_id
    ]
    assert store.written[0].counts.n_returned == 1


async def test_at_stake_is_omitted_in_for_fun_by_the_methods_own_name():
    """A for-fun game is never counted, so the figure is not
    absent-because-unavailable — it is **meaningless**, and asking about it is a
    category error rather than a mode flag."""

    answer = await use_case(rows=(build.row(1),)).execute(
        a_command(SearchMode.FOR_FUN)
    )

    assert all(row.at_stake is None for row in answer.record.returned)


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


async def test_the_two_columns_answering_whose_gap_this_is_cannot_drift():
    """``missing_terms`` is the non-platform half of ``degraded_reasons``.

    Two columns computing overlapping facts is how they drift, and these two are
    stamped by different halves of the pipeline: ``missing_terms`` by the evidence
    gate's own ``live``/``fired``, which answers a floor investigation, and the
    reasons by the term that stood down, which answers a player. They may not
    come to two answers about whose gap this is, so the relationship is asserted
    rather than trusted.

    **The one way they could legitimately part is a term weighted in neither
    mode.** ``live_terms`` drops such a term from the gate's basis while it can
    still stand down and be printed; no term is weighted at zero in both modes
    today, and the day one is, this goes red — which is the right answer, because
    it is a term the wire would be explaining and the gate would not be counting.
    """

    store = Store()
    # One candidate who declared and one who did not, so both halves of the
    # relationship are exercised: reliability has no provider on this platform
    # and is nobody's gap, and a silent intent is theirs.
    await use_case(
        rows=(build.row(1), build.row(2, declared_intent=None)), store=store
    ).execute(a_command())
    rows = store.written[0].candidates
    assert rows

    for row in rows:
        assert row.missing_terms == tuple(
            term
            for term, reason in zip(
                row.degraded_terms, row.degraded_reasons, strict=True
            )
            if reason != DegradedReason.NOT_YET_ON_THIS_PLATFORM.value
        )

    # And neither half is vacuous: the platform's own gap is on every row, and
    # the silent candidate carries one of their own that the gate counted.
    assert all(
        DegradedReason.NOT_YET_ON_THIS_PLATFORM.value in row.degraded_reasons
        for row in rows
    )
    silent = next(
        row for row in rows if Term.INTENT_ALIGNMENT.value in row.missing_terms
    )
    assert silent.degraded_reasons[
        silent.degraded_terms.index(Term.INTENT_ALIGNMENT.value)
    ] == DegradedReason.NOTHING_FROM_THEM.value


async def test_the_lift_read_is_bounded_by_the_box_and_never_by_the_city():
    """*Which of **these** people said yes*, and never *who said yes to me*.

    The bound is what keeps the read from being an inbox: it is asked about the
    population the bounding box already admitted, so it cannot answer a question
    the searcher was not going to be shown the answer to anyway. Asserted here
    rather than only at the port, because a caller that passed the whole city
    would satisfy the signature and break the promise.
    """

    inside = build.row(1)
    outside = build.row(2, latitude=52.20)
    yeses = Yeses()

    await use_case(rows=(inside, outside), interest=yeses).execute(a_command())

    (asked,) = yeses.asked_about
    assert UUID(inside.player_id) in asked
    assert UUID(outside.player_id) not in asked


async def test_a_yes_reaches_the_record_as_an_age_and_a_printed_reason():
    """The ledger's answer travels into the context and out into the row.

    Two columns land, and they say different things: ``liveness_signals`` keeps
    the **age in days** because the ``+14`` is flat and a boolean would lose the
    x-axis of *acceptance by age of yes*, and ``inclusion_reason`` keeps
    ``INTEREST_LIFT`` because it is the only reason that can be why somebody is
    on the screen at all.
    """

    row = build.row(1)
    store = Store()
    yeses = Yeses(days_ago={UUID(row.player_id): 18})

    await use_case(rows=(row,), store=store, interest=yeses).execute(a_command())

    recorded = store.written[0].returned[0]
    assert recorded.liveness_signals["INTEREST_RECEIVED"] == 18
    assert recorded.inclusion_reason is InclusionReason.INTEREST_LIFT
    assert "INTEREST_RECEIVED" in recorded.liveness_reasons


# ---------------------------------------------------------------------------
# The scoring histogram (scale-posture.md §4)
# ---------------------------------------------------------------------------


class Histogram:
    """Trigger 1's meter, as a list of the calls it was told about."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def observe_scoring(self, milliseconds: float) -> None:
        self.calls.append(milliseconds)


async def test_a_search_reports_its_scoring_call_to_the_histogram() -> None:
    """**One search, one sample**, and it is the span the search row already
    records as ``pipeline``.

    Asserted as a count and not as a duration: what this build owes is a trigger
    that is *instrumented*, and asserting how long this runner took to score six
    candidates would be asserting a metric — which goes red for the runner's
    reasons and gets widened until it says nothing.
    """

    meter = Histogram()
    use = use_case(rows=(build.row(1), build.row(2)), meter=meter)
    answer = await use.execute(a_command())

    assert len(meter.calls) == 1
    # The instrument keeps the fraction the row rounds away, which is what stops
    # a p99 over integers reading 0 ms for every shortlist on a fast worker.
    assert meter.calls[0] >= answer.record.latency_ms_by_stage["pipeline"]


async def test_a_search_without_a_histogram_is_an_ordinary_search() -> None:
    """Every test in this file runs one, and a platform that could not answer
    without an instrument would have the priority exactly backwards."""

    answer = await use_case(rows=(build.row(1),)).execute(a_command())

    assert answer.record.latency_ms_by_stage["pipeline"] >= 0


# ---------------------------------------------------------------------------
# The prompts, and the one gate every one of them passes
# ---------------------------------------------------------------------------


async def a_standing_prompt(*prompts: Prompt) -> InMemoryPromptLedger:
    """A ledger with the loops' questions already in it, as a tick leaves them."""

    ledger = InMemoryPromptLedger(FixedClock())
    for prompt in prompts:
        await ledger.raise_prompt(
            player_id=SEARCHER,
            prompt=prompt,
            sport=SPORT if prompt is Prompt.UPDATE_PLAY_INTENT else None,
            detail=SearchMode.COMPETITIVE.value
            if prompt is Prompt.UPDATE_PLAY_INTENT
            else None,
        )
    return ledger


async def test_a_question_the_player_has_declined_is_not_asked_again() -> None:
    """**The whole point.** The loop goes on raising it — that is what the loops
    are for — and the search stays quiet about it."""

    answer = await use_case(
        rows=(build.row(1),),
        prompts=await a_standing_prompt(Prompt.REFRESH_YOUR_TIMES),
        declines=Declines(silenced=frozenset({Prompt.REFRESH_YOUR_TIMES})),
    ).execute(a_command())

    assert answer.prompts == ()


async def test_a_decline_silences_its_own_question_and_no_other() -> None:
    """A player who said *not now* to one offer is still asked the others: these
    are four questions about four facts, and a decline is an answer to one."""

    answer = await use_case(
        rows=(build.row(1),),
        prompts=await a_standing_prompt(
            Prompt.UPDATE_PLAY_INTENT, Prompt.REFRESH_YOUR_TIMES
        ),
        declines=Declines(silenced=frozenset({Prompt.UPDATE_PLAY_INTENT})),
    ).execute(a_command())

    assert [raised.prompt for raised in answer.prompts] == [Prompt.REFRESH_YOUR_TIMES]


async def test_the_gate_asks_about_this_searcher_this_sport_and_thirty_days() -> None:
    """The window is a **date**, applied in the read: a filter asking *has this
    player ever declined* would be a silence nothing ever lifts."""

    declines = Declines()

    await use_case(
        rows=(build.row(1),),
        prompts=await a_standing_prompt(Prompt.REFRESH_YOUR_TIMES),
        declines=declines,
    ).execute(a_command())

    assert declines.asked == [(SEARCHER, SPORT, NOW - DECLINE_SUPPRESS)]


async def test_a_search_that_raises_nothing_asks_the_table_nothing() -> None:
    """The majority of searches. A filter over no questions has no answer to
    look up, and looking one up anyway would put a query on every search for the
    sake of the few that carry a prompt."""

    declines = Declines()

    answer = await use_case(rows=(build.row(1),), declines=declines).execute(
        a_command()
    )

    assert answer.prompts == ()
    assert declines.asked == []


async def test_a_gate_that_cannot_be_read_asks_nothing_at_all() -> None:
    """**It degrades to no prompt**, which is the opposite collapse from the
    ledgers around it and is the right one here: the two degraded outcomes are
    *ask somebody who said no* and *say nothing*, and the block this sits in
    already says nothing when a ledger is unreachable."""

    answer = await use_case(
        rows=(build.row(1),),
        prompts=await a_standing_prompt(
            Prompt.UPDATE_PLAY_INTENT, Prompt.REFRESH_YOUR_TIMES
        ),
        declines=Declines(raises=True),
    ).execute(a_command())

    assert answer.prompts == ()
    assert answer.record.returned, "a search that ran must still answer"


async def test_an_unreadable_gate_never_fails_the_search_it_follows() -> None:
    """The block runs *after* the commit, so raising here would fail a search
    that has already happened and been recorded."""

    store = Store()
    use = use_case(rows=(build.row(1),), store=store, declines=Declines(raises=True))

    answer = await use.execute(a_command())

    assert len(store.written) == 1
    assert answer.record is store.written[0]
