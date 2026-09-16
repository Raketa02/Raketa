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

**The clock is the run's own injected instant**, not the wall clock, and it is a
constructor argument rather than a call — which is what lets one run assemble
these more than once, at more than one instant.

**An edge is written at the run's own now and a played game is not**, and the two
halves of that are one rule rather than an exception to it: a seat's own answer
window has to start when the run starts or the court is over before it is read,
and a *result* is confirmed by silence when its window closes — so a
game seeded an hour ago is a game still awaiting an answer, which is a different
card from the one the fixture is for. A relationship is a thing happening now; a
played game is a thing that happened. ``app/seeds/games.py`` builds one of these
per game, at the instant that game declares.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Mapping, Sequence, final
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
    build_deck_reset_ledger,
    build_domain_event_store,
    build_event_publisher,
    build_exposure_ledger,
    build_game_directory,
    build_game_history_query,
    build_game_repository,
    build_half_built_court_query,
    build_interest_ledger,
    build_match_fit_engine,
    build_match_history_query,
    build_mutual_challenge_minting,
    build_game_of_court_query,
    build_open_challenge_query,
    build_origin_search_query,
    build_planned_game_handover,
    build_seatable_game_query,
    build_pass_ledger,
    build_play_intent_declaration_repository,
    build_photo_storage,
    build_player_card_source,
    build_challenge_names,
    build_court_pairing_query_over,
    build_player_names,
    build_player_record_source,
    build_player_profile_repository,
    build_player_score_query,
    build_prompt_decline_ledger,
    build_prompt_ledger,
    build_read_plans,
    build_ruleset,
    build_search_store,
    build_shared_court_query,
    build_skill_rating_repository,
    build_suppression_ledger,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.infrastructure.redis_client import create_redis_client
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import Instant, Sport
from app.modules.blocks.application.block_player import BlockPlayer
from app.modules.challenges.application.answer_seat import AcceptSeat, DeclineSeat
from app.modules.challenges.application.commands import (
    SeatChoice,
    SendChallengeCommand,
)
from app.modules.challenges.application.fill_seats import FillSeats
from app.modules.challenges.application.leave_game import LeaveGame
from app.modules.challenges.application.read_challenge import ReadChallenge
from app.modules.challenges.application.read_challenges import ReadChallenges
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.application.withdraw_challenge import WithdrawChallenge
from app.modules.challenges.domain.seats import court_sides
from app.modules.games.application.answer_result import AcceptResult, StateResult
from app.modules.games.application.read_games import ReadGames
from app.modules.games.domain.ports import GameHistoryQuery
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
from app.modules.plans.application.read_plans import ReadPlans
from app.modules.player_profile.domain.ports import PhotoStorage
from app.seeds.catalog import PROTAGONISTS
from app.seeds.clock import FixedClock
from app.seeds.cohort import Cohort
from app.seeds.relationships import RELATIONSHIP_ACCOUNTS

#: What one ``make seed`` calls its searches, so the rows it leaves behind are
#: separable from a developer's own in the one table that keeps them for ever.
TRACE_ID = "seed-assertions"


class SeedCourtRefused(RuntimeError):
    """A court this run could not shape, before the platform was ever asked.

    Raised by :func:`send_a_court` alone, and only for the one thing that
    function decides: a send naming more people than the sport seats. Kept apart
    from each caller's own refusal because it is a fact about the *sport*, and
    two callers discovering it separately would be two spellings of one rule.
    """


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
    #: The organiser's exit from a line-up nobody will finish, and the only act
    #: in this fixture that **ends** a challenge on purpose. It is here for the
    #: same reason the two answers are: a state a screen has to draw is reached
    #: through the use case a request runs, never written into the log.
    withdraw: WithdrawChallenge
    #: *Leave the game* — the one act that takes a yes back (``docs/adr/0165``),
    #: and since ``docs/adr/0172`` §1 the one that ends a court that has been a
    #: game: the departure that leaves one player on it records ``CALLED_OFF``
    #: and calls the game off in the same act. Here because that ending — the
    #: seventh standing, and the *Called off* card it draws — is reached by no
    #: other act, and a state a screen has to draw is reached through the use
    #: case a request runs.
    leave: LeaveGame
    #: *Fill the seats* — the send's shape minus the mint (``docs/adr/0150``).
    #: Here because a court that has been **grown** is a state no other act
    #: reaches: the room learns ``SEATS_INVITED`` from a fill and from nothing
    #: else, and half of this mechanism was written and unreachable until #362.
    fill: FillSeats
    read_challenges: ReadChallenges
    #: The detail read, and **the only surface in this fixture that costs the
    #: matcher a whole scoring pass** (``docs/adr/0143``). It is here so the run
    #: can assert the card block a challenge screen draws rather than only the
    #: arrangement behind it — which is the one half of that screen no other
    #: read in this file exercises.
    read_challenge: ReadChallenge
    #: The three acts a played game costs after the seats are answered, and the
    #: screen that reads one back. ``games`` opens the game itself — inline, in
    #: the transaction of the accept that filled the last seat — so there is no
    #: *open a game* use case here and deliberately none: a game nobody was
    #: invited to is a game no line-up completed.
    state_result: StateResult
    accept_result: AcceptResult
    read_games: ReadGames
    #: *Every plan for the games you are on the court of.* Beside the games read
    #: because a card is folded from the two of them and from one instant: the
    #: standing is ``GET /games``' and the slots are this one's, and ``GET /plans``
    #: carries no instant at all so that a rail has one clock by construction.
    read_plans: ReadPlans
    history: MatchHistoryQuery
    #: What ``games`` publishes outward — the pairwise history familiarity reads,
    #: the counted-game count and the run of form. Held beside ``history``
    #: because the composed port above answers about a *pair* and this answers
    #: about a person, and a claim about a card is the second question.
    games: GameHistoryQuery
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


@asynccontextmanager
async def the_ephemeral_store(settings: Settings) -> AsyncIterator[Redis]:
    """The run's Redis client, opened and closed by whoever asked for it.

    **A command has no lifespan, so the ownership has to be written down.** Under
    the API the pool belongs to the process and FastAPI's lifespan owns both
    ends; a client left open here is a developer command that does not exit. Each
    of the three layers that runs a search needs one, so it is spelled once —
    three copies were three chances for the closing half to be dropped from one
    of them.

    ``type: ignore`` because the obsolete ``types-redis`` stubs shadow redis-py's
    own inline types and predate ``aclose``, which exists and is the spelling
    ``close`` was deprecated in favour of.
    """

    redis = create_redis_client(settings)
    try:
        yield redis
    finally:
        await redis.aclose()  # type: ignore[attr-defined]


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
    players: Mapping[str, UUID] | None = None,
    photos: PhotoStorage | None = None,
) -> ReadPaths:
    """The surfaces and the gestures, wired from the composition root and nowhere else.

    The one place a seed run does not go through a use case is
    ``screens.py``'s engine-initiated fill, and that is because **there is no
    engine-initiated use case to go through**. It says so where it is written.
    """

    clock = FixedClock(at=now)
    # **The run's own store, or this process's.** A card with a photograph costs
    # one object-store ``HEAD`` for its verdict, so the read that draws a card
    # and the upload that put the photograph there have to be looking at one
    # place — which is a caller's decision, exactly as the clock is.
    photos = photos or build_photo_storage(settings)
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
    games = build_game_repository(
        session=session, event_store=event_store, events=events
    )
    names = build_player_names(session)
    # ``challenges`` declares its own names port and may not sign ``games``'
    # (``docs/adr/0143`` §7), so the seed holds both adapters exactly as a
    # request does.
    court_names = build_challenge_names(session)
    court_games = build_game_of_court_query(session)
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
            storage=photos,
        ),
        records=build_player_record_source(session),
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
            courts=build_shared_court_query(session),
            resets=build_deck_reset_ledger(session),
        ),
        lineup=RunLineupSearch(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            blocks=blocks,
            # Real rather than stubbed, for the reason the mutual mint above is:
            # the seed completes a half-built court through this use case, and a
            # use case assembled with a hole in it is not the one a request runs.
            courts=build_half_built_court_query(session),
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
            names=court_names,
            court_games=court_games,
            uow=uow,
            clock=clock,
            planned_games=build_planned_game_handover(session),
            games=build_seatable_game_query(session),
        ),
        decline=DeclineSeat(
            challenges=challenges,
            names=court_names,
            court_games=court_games,
            uow=uow,
            clock=clock,
        ),
        # **The send's three extra reads, built the same way here as there**, so
        # a fill and a send cannot come to two answers about who may share a
        # court — which is the whole of what a fill re-verifies.
        fill=FillSeats(
            challenges=challenges,
            names=court_names,
            court_games=court_games,
            open_challenges=build_open_challenge_query(session),
            origins=build_origin_search_query(session),
            safety=build_court_safety(session),
            games=build_seatable_game_query(session),
            uow=uow,
            clock=clock,
        ),
        withdraw=WithdrawChallenge(
            challenges=challenges,
            names=court_names,
            court_games=court_games,
            uow=uow,
            clock=clock,
        ),
        # **The accept's hand-over and the accept's moment guard**, built the
        # same way, because a departure is the accept's mirror — a seat moving
        # on a court that has been a game, told to the game in the same
        # transaction — and the court's safety gates, because a departure
        # writes a line into a room other people are in.
        leave=LeaveGame(
            challenges=challenges,
            names=court_names,
            court_games=court_games,
            safety=build_court_safety(session),
            games=build_seatable_game_query(session),
            uow=uow,
            clock=clock,
            planned_games=build_planned_game_handover(session),
        ),
        state_result=StateResult(games=games, names=names, uow=uow, clock=clock),
        accept_result=AcceptResult(games=games, names=names, uow=uow, clock=clock),
        read_games=ReadGames(
            games=build_game_directory(session), names=names, clock=clock
        ),
        read_plans=build_read_plans(session, clock=clock),
        read_challenges=ReadChallenges(
            directory=build_challenge_directory(session),
            names=court_names,
            court_games=court_games,
            clock=clock,
        ),
        read_challenge=ReadChallenge(
            challenges=challenges,
            names=court_names,
            # **The run's own workbench**, not a second one over the same
            # session — which is what the stores above say about themselves and
            # is truer of this one, since it holds four of them. It also carries
            # the run's own index and ledger for the reason every other seam here
            # takes the caller's: the run ticks the index in process before it
            # reads, and a pairing computed against a different one would be a
            # card about a city this run never built.
            pairings=build_court_pairing_query_over(
                workbench=workbench, settings=settings
            ),
            clock=clock,
        ),
        history=history,
        games=build_game_history_query(session),
        engine=engine,
        ruleset=ruleset,
        players=players or await player_ids(session, cohort),
    )


async def player_ids(session: AsyncSession, cohort: Cohort) -> Mapping[str, UUID]:
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


async def send_a_court(
    paths: ReadPaths,
    *,
    organiser: str,
    sport: Sport,
    record: SearchRecord,
    invitees: Sequence[str],
) -> UUID:
    """One send: the organiser first, then the invitees, on the sport's own sides.

    The court is the sport's fixed list of sides and every position is passed,
    empty ones included — *an empty seat is a seat*, and a padel court with one
    invitee is half a game rather than a shorter court.

    **Here rather than in either caller**, because both of them send: the
    relationship layer sends the two courts the eleven are named for, and the
    played history sends one per game. Two copies would be two opinions about
    where the organiser sits, and the second is the one nobody would think to
    change.
    """

    sides = court_sides(sport)
    occupants: list[UUID | None] = [
        paths.player(organiser),
        *[paths.player(address) for address in invitees],
    ]
    if len(occupants) > len(sides):
        raise SeedCourtRefused(
            f"a {sport.value} court seats {len(sides)} and this send names "
            f"{len(occupants)}."
        )
    occupants.extend([None] * (len(sides) - len(occupants)))
    return await paths.send.execute(
        SendChallengeCommand(
            organiser_id=paths.player(organiser),
            search_id=record.id,
            court=tuple(
                SeatChoice(side=side, player_id=occupant)
                for side, occupant in zip(sides, occupants, strict=True)
            ),
        )
    )


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
