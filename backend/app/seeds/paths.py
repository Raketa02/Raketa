"""The read and write paths one seed run drives, wired from the composition root.

**One wiring, two callers.** ``pairs.py`` writes the eleven relationships and
``screens.py`` reads what they and the cohort promise, and both go through the
same objects a request goes through. Two wirings would be two opinions about
which reads fail closed, and the one that drifted would be the one that quietly
softened a gate — so the assembly is here, once, and neither of them names a
concrete class.

Assembled exactly as ``matchmaking/presentation/dependencies.py`` and
``challenges/presentation/dependencies.py`` assemble them for a request. The
repositories are built once for the run rather than once per act: each remembers
the stream versions it has seen and re-remembers them on every save, so a send
and the answer to its seat agree about where the stream is — which is the same
promise a request-scoped one makes, over a longer transaction.

**The clock is the run's own injected instant**, not the wall clock. Every edge
is written at it and nothing is backdated: a yes born partly spent would be a
fixture for an age no surface draws, and a seat's twenty-four hours have to start
when the run starts or the court is over before it is read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_absent_terms,
    build_account_hold_query,
    build_account_status_query,
    build_at_stake_query,
    build_block_query,
    build_block_repository,
    build_candidate_index_tail,
    build_challenge_directory,
    build_challenge_repository,
    build_court_safety,
    build_domain_event_store,
    build_event_publisher,
    build_exposure_ledger,
    build_interest_ledger,
    build_match_fit_engine,
    build_match_history_query,
    build_mutual_challenge_minting,
    build_open_challenge_query,
    build_origin_search_query,
    build_planned_game_opening,
    build_pass_ledger,
    build_play_intent_declaration_repository,
    build_photo_storage,
    build_player_card_source,
    build_player_profile_repository,
    build_player_score_query,
    build_prompt_decline_ledger,
    build_prompt_ledger,
    build_ruleset,
    build_search_store,
    build_skill_rating_repository,
    build_suppression_ledger,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import Instant, Sport
from app.modules.blocks.application.block_player import BlockPlayer
from app.modules.challenges.application.answer_seat import AcceptSeat, DeclineSeat
from app.modules.challenges.application.read_challenges import ReadChallenges
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.matchmaking.application.commands import (
    RunDeckDealCommand,
    RunShortlistSearchCommand,
)
from app.modules.matchmaking.application.express_interest import ExpressInterest
from app.modules.matchmaking.application.read_interest import ReadInterest
from app.modules.matchmaking.application.record_pass import RecordPass
from app.modules.matchmaking.application.run_deck_deal import DeckAnswer, RunDeckDeal
from app.modules.matchmaking.application.run_lineup_search import RunLineupSearch
from app.modules.matchmaking.application.run_shortlist_search import (
    RunShortlistSearch,
)
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.ledgers import SuppressionLedger
from app.modules.matchmaking.domain.passes import PassLedger
from app.modules.matchmaking.domain.ports import MatchHistoryQuery
from app.modules.matchmaking.domain.relaxation import Rung
from app.modules.matchmaking.domain.searches import SearchRecord
from app.seeds.catalog import PROTAGONISTS
from app.seeds.clock import FixedClock
from app.seeds.cohort import Cohort
from app.seeds.relationships import RELATIONSHIP_ACCOUNTS

#: What one ``make seed`` calls its searches, so the rows it leaves behind are
#: separable from a developer's own in the one table that keeps them for ever.
TRACE_ID = "seed-assertions"


class SeedPathMissing(RuntimeError):
    """An address the run wrote and this read cannot find.

    A ``RuntimeError`` for ``SeedFailed``'s reason: it is a refusal to hand a
    developer a fixture whose promise is a lie, not a bad argument a caller might
    catch.
    """


@final
@dataclass(frozen=True)
class ReadPaths:
    """Every surface a seed run reads or writes through, and what reads it back.

    The searches, the deck and the line-up are the three surfaces; the yes, the
    pass, the block, the send and the two answers are the five gestures. They sit
    in one value because the edges and the claims are two halves of one run and a
    second assembly is a second opinion.
    """

    workbench: SearchWorkbench
    shortlist: RunShortlistSearch
    deck: RunDeckDeal
    lineup: RunLineupSearch
    interest: ExpressInterest
    read_interest: ReadInterest
    passes: RecordPass
    pass_ledger: PassLedger
    suppression: SuppressionLedger
    block: BlockPlayer
    send: SendChallenge
    accept: AcceptSeat
    decline: DeclineSeat
    read_challenges: ReadChallenges
    history: MatchHistoryQuery
    engine: MatchFit
    ruleset: Ruleset
    #: Player id per seeded address, so an assertion names an account and never
    #: a uuid a developer would have to look up.
    players: Mapping[str, UUID]

    def player(self, email: str) -> UUID:
        """The id the write path minted for this address.

        Spelled as a method rather than reached into, because a missing address
        here is a seeded account that is not in the database and the complaint
        for that is not a ``KeyError`` with a mail address in it.
        """

        found = self.players.get(email)
        if found is None:
            raise SeedPathMissing(
                f"'{email}' was seeded and this read cannot find it. The "
                f"assertions read the same database the run just wrote."
            )
        return found


async def tick_the_tail_to_catch_up(
    session_factory: async_sessionmaker[AsyncSession], *, settings: Settings
) -> int:
    """Fold everything this run appended into the candidate index. **In process.**

    Safe by the index's own design rather than by exemption: the cursor is taken
    ``FOR UPDATE`` inside the transaction, so an API worker ticking at the same
    moment blocks and then finds nothing left to apply. That is also what makes
    this a **barrier rather than a final step** — the relationship layer runs real
    searches mid-run to earn its origin keys, and those searches read the index,
    so the tick happens before every *read* and not once before the assertions.
    Calling it three times is a no-op twice.
    """

    tail = build_candidate_index_tail(settings=settings)
    applied = 0
    async with session_factory() as session:
        while True:
            report = await tail.tick(session)
            if not report.events_applied:
                return applied
            applied += report.events_applied


async def read_paths(
    session: AsyncSession,
    *,
    settings: Settings,
    candidates: CandidateSource,
    cohort: Cohort,
    now: Instant,
    redis: Redis,
) -> ReadPaths:
    """The surfaces and the gestures, wired from the composition root and nowhere else.

    The one place a seed run does not go through a use case is
    ``screens.py``'s engine-initiated fill, and that is because **there is no
    engine-initiated use case to go through**. It says so where it is written.
    """

    clock = FixedClock(at=now)
    event_store = build_domain_event_store(session)
    events = build_event_publisher(session)
    profiles = build_player_profile_repository(event_store=event_store, events=events)
    declarations = build_play_intent_declaration_repository(
        event_store=event_store, events=events
    )
    ratings = build_skill_rating_repository(event_store=event_store, events=events)
    player_scores = build_player_score_query(session)
    exposure = build_exposure_ledger(redis)
    interest = build_interest_ledger(session)
    passes = build_pass_ledger(session)
    # Built once and shared, because a store handed out four times is four
    # objects over one table and one of them will eventually be the odd one.
    searches = build_search_store(session)
    blocks = build_block_query(session)
    suppression = build_suppression_ledger(redis)
    challenges = build_challenge_repository(event_store=event_store, events=events)
    history = build_match_history_query(session)
    ruleset = build_ruleset()
    engine = build_match_fit_engine()
    uow = build_unit_of_work(session)

    workbench = SearchWorkbench(
        clock=clock,
        ruleset=ruleset,
        searches=searches,
        unit_of_work=uow,
        candidates=candidates,
        profiles=profiles,
        ratings=ratings,
        declarations=declarations,
        blocks=blocks,
        holds=build_account_hold_query(session),
        account_status=build_account_status_query(session),
        history=history,
        player_scores=player_scores,
        at_stake=build_at_stake_query(session),
        exposure=exposure,
        interest=interest,
        cards=build_player_card_source(
            session=session,
            event_store=event_store,
            events=events,
            storage=build_photo_storage(settings),
        ),
        absent_terms=build_absent_terms(),
        meter=None,
    )
    return ReadPaths(
        workbench=workbench,
        shortlist=RunShortlistSearch(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            searches=searches,
            prompts=build_prompt_ledger(redis),
            declines=build_prompt_decline_ledger(session),
        ),
        deck=RunDeckDeal(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            searches=searches,
            suppression=suppression,
            interest=interest,
            passes=passes,
        ),
        lineup=RunLineupSearch(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            blocks=blocks,
        ),
        interest=ExpressInterest(
            clock=clock,
            ruleset=ruleset,
            interest=interest,
            searches=searches,
            # Reached exactly once, and only if a run says yes back to a live
            # inbound yes — which is the second state of the mutual fixture's own
            # two-state claim. It is real rather than stubbed because a use case
            # assembled with a hole in it is not the one a request runs.
            challenges=build_mutual_challenge_minting(session),
            unit_of_work=uow,
        ),
        read_interest=ReadInterest(
            clock=clock,
            ruleset=ruleset,
            interest=interest,
            blocks=blocks,
        ),
        passes=RecordPass(
            clock=clock,
            ruleset=ruleset,
            passes=passes,
            suppression=suppression,
            searches=searches,
            unit_of_work=uow,
        ),
        pass_ledger=passes,
        suppression=suppression,
        block=BlockPlayer(
            blocks=build_block_repository(event_store=event_store, events=events),
            uow=uow,
            clock=clock,
        ),
        send=SendChallenge(
            challenges=challenges,
            open_challenges=build_open_challenge_query(session),
            origins=build_origin_search_query(session),
            safety=build_court_safety(session),
            uow=uow,
            clock=clock,
        ),
        accept=AcceptSeat(
            challenges=challenges,
            uow=uow,
            clock=clock,
            planned_games=build_planned_game_opening(session),
        ),
        decline=DeclineSeat(challenges=challenges, uow=uow, clock=clock),
        read_challenges=ReadChallenges(
            directory=build_challenge_directory(session), clock=clock
        ),
        history=history,
        engine=engine,
        ruleset=ruleset,
        players=await _players(session, cohort),
    )


async def _players(session: AsyncSession, cohort: Cohort) -> Mapping[str, UUID]:
    """Every seeded address a read here names, as the id the write path minted.

    Looked up by address rather than derived, because ``RegisterUser`` mints the
    id and a caller-chosen one is an id the write path does not own. The address
    is what the catalog promises and it is what this reads.
    """

    users = build_user_repository(session)
    found: dict[str, UUID] = {}
    addresses = (
        [account.email for account in PROTAGONISTS]
        + [account.email for account in RELATIONSHIP_ACCOUNTS]
        + [member.email for member in cohort.members]
    )
    for address in addresses:
        user = await users.get_by_email(address)
        if user is None:
            raise SeedPathMissing(
                f"'{address}' was seeded and cannot be found. The assertions "
                f"read the same database the run just wrote."
            )
        found[address] = user.id
    return found


async def run_a_shortlist(
    paths: ReadPaths,
    email: str,
    sport: Sport,
    mode: SearchMode,
    *,
    offered_by_search_id: UUID | None = None,
    rung: Rung | None = None,
) -> SearchRecord:
    """One tap, through the use case a request runs. **The record is the answer.**"""

    answer = await paths.shortlist.execute(
        RunShortlistSearchCommand(
            searcher_id=paths.player(email),
            sport=sport,
            mode=mode,
            availability_override=None,
            offered_by_search_id=offered_by_search_id,
            rung=rung,
            trace_id=TRACE_ID,
        )
    )
    return answer.record


async def deal_a_deck(paths: ReadPaths, email: str, sport: Sport) -> DeckAnswer:
    """One *Match me*, through the use case a request runs.

    **Every deal costs the next one.** ``DEALT_MEMORY`` is a day, so a card dealt
    here is a card the following deal will not deal — which is why a run deals as
    few times as it can and says on its report what the deals it did run took
    away.
    """

    return await paths.deck.execute(
        RunDeckDealCommand(
            searcher_id=paths.player(email),
            sport=sport,
            availability_override=None,
            trace_id=TRACE_ID,
        )
    )


def returned_ids(record: SearchRecord) -> frozenset[UUID]:
    """Who this search actually **showed** — the only rows an origin resolves on.

    A near-miss row is recorded and never handed to anybody, so a court or a yes
    citing one was built from something no search showed.
    """

    return frozenset(row.player_id for row in record.returned)
