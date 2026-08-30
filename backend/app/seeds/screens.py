"""What the cohort promises about the screens, proved by reading them.

**The second of the seed's two lists, and it is not symmetric with the first.**
``cohort.py`` holds the *declarations* — the generator's own inputs. This holds
the *assertions*, and every one of them is an outcome of a **real read path
executed as the protagonist**: the pool search is run, the deck is dealt, the
line-up is composed. Nothing here is asserted about a number the generator chose.

The argument for the asymmetry is the ticket's own: a ruleset that tightens
``QUALITY_FLOOR`` moves no distribution at all and still empties every screen. A
check computed from the population could only ever pass. The claim has to travel
through the gates, the scoring, the group objective and the floor, or it is not a
claim about a screen.

**The tail is ticked first, in this process.** The assertions read the candidate
index, and the index has not seen what the seed just wrote. ``runner.py``'s *a
seed run is not an event-delivery worker* is about the **outbox** and does not
bind here: the index is a projection of the log that anybody may recompute,
behind one ``FOR UPDATE`` cursor, so a concurrent tick blocks and then finds
nothing to do (``docs/adr/0110``). Polling ``caught_up_at`` would make a
developer command depend on the API being up, and printing *now run
``make rebuild-candidate-index``* would put every assertion behind a step people
forget.

**The full battery runs against one protagonist, and the other three are asked
one question each** — the state each is named for. Running everything four times
would cost a dozen assessments' worth of reading to re-observe what the default
protagonist has already proved, and an account is named for **one** state.

**Two sports, and which assertion runs on which is forced.** ``MIN_SHORTLIST``
decides whether a ladder is priced at all, so a padel search that returns the
five rows the pool assertion demands is a search with **no rungs on it**. Padel
is where the cohort is dense and is where the pool, the deck and the four are
read; tennis is where it is thin — every third member plays it — and is where the
ladder is watched. One protagonist, two screens, and neither assertion is bent to
fit the other.

**Half a gate, said out loud.** None of this runs in CI: it needs a database with
the seed in it. That is the same half-a-gate the ruleset diff ships with, and it
is stated here rather than discovered.

**These reads leave records behind.** A search run through its real use case
writes to ``matchmaking``'s own store, and a search record never expires
(``docs/adr/0104``), so every ``make seed`` grows that table by a handful of
rows. Taken as acceptable: the seed genuinely ran those searches, the records are
true, and a fixture database is disposable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_absent_terms,
    build_account_hold_query,
    build_account_status_query,
    build_at_stake_query,
    build_block_query,
    build_candidate_index_tail,
    build_candidate_source,
    build_domain_event_store,
    build_event_publisher,
    build_exposure_ledger,
    build_interest_ledger,
    build_match_fit_engine,
    build_match_history_query,
    build_mutual_challenge_minting,
    build_pass_ledger,
    build_play_intent_declaration_repository,
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
from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.infrastructure.redis_client import create_redis_client
from app.kernel import Instant, Sport
from app.modules.matchmaking.application.commands import (
    ExpressInterestCommand,
    RunDeckDealCommand,
    RunLineupSearchCommand,
    RunShortlistSearchCommand,
)
from app.modules.matchmaking.application.express_interest import ExpressInterest
from app.modules.matchmaking.application.run_deck_deal import RunDeckDeal
from app.modules.matchmaking.application.run_lineup_search import RunLineupSearch
from app.modules.matchmaking.application.run_shortlist_search import RunShortlistSearch
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.errors import SportNotRated
from app.modules.matchmaking.domain.gates import GateCode
from app.modules.matchmaking.domain.relaxation import Rung
from app.modules.matchmaking.domain.searches import (
    SearchInitiation,
    SearchRecord,
    SearchSurface,
)
from app.modules.matchmaking.domain.shortlist import run as run_the_pipeline
from app.seeds.catalog import (
    THE_BLANK_WEEK_PLAYER,
    THE_NEWCOMER,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.clock import FixedClock
from app.seeds.cohort import COHORT, Cohort, CohortMember

#: What one ``make seed`` calls its searches, so the rows it leaves behind are
#: separable from a developer's own in the one table that keeps them for ever.
TRACE_ID = "seed-assertions"

# **How many rows the pool must carry is deliberately not a constant here.** It
# is ``MIN_SHORTLIST``, read off the live ruleset at the assertion: the product's
# answer to *this list is too short to be useful* has an owner, and a second copy
# in a fixture is a fixture that can pass a screen the ruleset calls empty.

#: How many cards a deal must produce. Deliberately below ``deck_deal_max``: a
#: deck asserted at its ceiling would be asserting the cap rather than the pool.
CARDS_A_DEAL_MUST_CARRY = 3


class ScreenIsEmpty(RuntimeError):
    """A screen the cohort promised is one this database cannot draw.

    A ``RuntimeError`` for ``SeedFailed``'s reason — it is a refusal to hand a
    developer a fixture whose promise is a lie, not a bad argument a caller might
    catch. It is raised rather than warned for the same reason the whole file
    exists: a warning in a make target scrolls past, and the fixture then rots
    silently.
    """


@dataclass(frozen=True)
class _ReadPaths:
    """The three surfaces, the workbench under them, and what reads them back."""

    workbench: SearchWorkbench
    shortlist: RunShortlistSearch
    deck: RunDeckDeal
    lineup: RunLineupSearch
    interest: ExpressInterest
    engine: MatchFit
    ruleset: Ruleset
    #: Player id per seeded address, so an assertion names an account and never
    #: a uuid a developer would have to look up.
    players: Mapping[str, UUID]


async def assert_the_screens(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Cohort = COHORT,
) -> tuple[str, ...]:
    """Read every screen the cohort promises, and refuse a database that cannot.

    Returns the lines the report prints. They are the **evidence**, not a
    decoration: what a failure has to print is the assertion, the protagonist,
    the surface and both counts, and printing the same breakdown on the way
    through is what makes the passing run legible too.
    """

    await tick_the_tail_to_catch_up(session_factory, settings=settings)
    candidates = build_candidate_source(session_factory=session_factory)
    await candidates.refresh()

    lines: list[str] = []
    async with session_factory() as session:
        paths = await _read_paths(
            session,
            settings=settings,
            candidates=candidates,
            cohort=cohort,
            now=now,
        )
        lines.extend(await _the_full_battery(paths, cohort=cohort, now=now))
        lines.extend(await _the_three_named_states(paths))
    return tuple(lines)


async def tick_the_tail_to_catch_up(
    session_factory: async_sessionmaker[AsyncSession], *, settings: Settings
) -> int:
    """Fold everything this run appended into the candidate index. **In process.**

    Safe by the index's own design rather than by exemption: the cursor is taken
    ``FOR UPDATE`` inside the transaction, so an API worker ticking at the same
    moment blocks and then finds nothing left to apply.
    """

    tail = build_candidate_index_tail(settings=settings)
    applied = 0
    async with session_factory() as session:
        while True:
            report = await tail.tick(session)
            if not report.events_applied:
                return applied
            applied += report.events_applied


async def _read_paths(
    session: AsyncSession,
    *,
    settings: Settings,
    candidates: CandidateSource,
    cohort: Cohort,
    now: Instant,
) -> _ReadPaths:
    """The three surfaces, wired from the composition root and nowhere else.

    Assembled exactly as ``matchmaking/presentation/dependencies.py`` assembles
    them for a request, because a second wiring is a second opinion about which
    reads fail closed — and the one that drifted would be the one that quietly
    softened a gate.
    """

    event_store = build_domain_event_store(session)
    events = build_event_publisher(session)
    profiles = build_player_profile_repository(event_store=event_store, events=events)
    declarations = build_play_intent_declaration_repository(
        event_store=event_store, events=events
    )
    ratings = build_skill_rating_repository(event_store=event_store, events=events)
    player_scores = build_player_score_query(session)
    redis = create_redis_client(settings)
    exposure = build_exposure_ledger(redis)
    interest = build_interest_ledger(session)
    ruleset = build_ruleset()
    engine = build_match_fit_engine()

    workbench = SearchWorkbench(
        clock=FixedClock(at=now),
        ruleset=ruleset,
        searches=build_search_store(session),
        unit_of_work=build_unit_of_work(session),
        candidates=candidates,
        profiles=profiles,
        ratings=ratings,
        declarations=declarations,
        blocks=build_block_query(session),
        holds=build_account_hold_query(session),
        account_status=build_account_status_query(session),
        history=build_match_history_query(session),
        player_scores=player_scores,
        at_stake=build_at_stake_query(session),
        exposure=exposure,
        interest=interest,
        cards=build_player_card_source(
            session=session, event_store=event_store, events=events
        ),
        absent_terms=build_absent_terms(player_scores),
        meter=None,
    )
    return _ReadPaths(
        workbench=workbench,
        shortlist=RunShortlistSearch(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            searches=build_search_store(session),
            prompts=build_prompt_ledger(redis),
            declines=build_prompt_decline_ledger(session),
        ),
        deck=RunDeckDeal(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            searches=build_search_store(session),
            suppression=build_suppression_ledger(redis),
            interest=interest,
            passes=build_pass_ledger(session),
        ),
        lineup=RunLineupSearch(
            workbench=workbench,
            ruleset=ruleset,
            engine=engine,
            blocks=build_block_query(session),
        ),
        interest=ExpressInterest(
            clock=FixedClock(at=now),
            ruleset=ruleset,
            interest=interest,
            searches=build_search_store(session),
            # Wired and never reached: a mutual yes opens a game inline, and
            # nothing here answers a yes back. The collaborator is real because
            # a use case assembled with a hole in it is not the one a request
            # runs.
            challenges=build_mutual_challenge_minting(session),
            unit_of_work=build_unit_of_work(session),
        ),
        engine=engine,
        ruleset=ruleset,
        players=await _players(session, cohort),
    )


async def _players(session: AsyncSession, cohort: Cohort) -> Mapping[str, UUID]:
    """Every seeded address, as the id the write path minted for it.

    Looked up by address rather than derived, because ``RegisterUser`` mints the
    id and a caller-chosen one is an id the write path does not own. The address
    is what the catalog promises and it is what this reads.
    """

    users = build_user_repository(session)
    found: dict[str, UUID] = {}
    addresses = [account.email for account in _PROTAGONISTS] + [
        member.email for member in cohort.members
    ]
    for address in addresses:
        user = await users.get_by_email(address)
        if user is None:
            raise ScreenIsEmpty(
                f"'{address}' was seeded and cannot be found. The assertions "
                f"read the same database the run just wrote."
            )
        found[address] = user.id
    return found


_PROTAGONISTS = (
    THE_POPULATED_PLAYER,
    THE_NEWCOMER,
    THE_ONE_SPORT_PLAYER,
    THE_BLANK_WEEK_PLAYER,
)


# ---------------------------------------------------------------------------
# The full battery, against the-populated-player
# ---------------------------------------------------------------------------


async def _the_full_battery(
    paths: _ReadPaths, *, cohort: Cohort, now: Instant
) -> list[str]:
    """Everything the default protagonist proves, in the order it is proved."""

    lines: list[str] = [
        await _somebody_says_lets_play(paths, cohort=cohort),
    ]
    pool = await _shortlist(
        paths, THE_POPULATED_PLAYER, Sport.PADEL, SearchMode.COMPETITIVE
    )
    lines.append(_refuse_a_pool_that_cannot_fill_a_screen(paths, pool))
    lines.append(_refuse_a_gender_gate_that_never_fires(pool))
    lines.append(_refuse_a_window_with_only_one_side(pool))
    lines.append(_refuse_a_reason_line_that_cannot_be_drawn(paths, pool))
    lines.append(await _refuse_a_deck_that_deals_nothing(paths))
    lines.append(await _refuse_a_court_that_cannot_be_filled(paths))
    lines.extend(await _refuse_a_ladder_that_adds_nobody(paths))
    lines.append(
        await _refuse_a_fill_that_shows_an_opted_out_member(paths, pool, now=now)
    )
    return lines


async def _shortlist(
    paths: _ReadPaths,
    account: SeedAccount,
    sport: Sport,
    mode: SearchMode,
    *,
    offered_by_search_id: UUID | None = None,
    rung: Rung | None = None,
) -> SearchRecord:
    """One tap, through the use case a request runs. **The record is the answer.**"""

    answer = await paths.shortlist.execute(
        RunShortlistSearchCommand(
            searcher_id=paths.players[account.email],
            sport=sport,
            mode=mode,
            availability_override=None,
            offered_by_search_id=offered_by_search_id,
            rung=rung,
            trace_id=TRACE_ID,
        )
    )
    return answer.record


def _refuse_a_pool_that_cannot_fill_a_screen(
    paths: _ReadPaths, pool: SearchRecord
) -> str:
    """*The pool returns ≥ N above the floor*, where N is the ruleset's own.

    Read off ``min_shortlist`` rather than written here, because the product's
    answer to *this list is too short to be useful* has an owner — and a fixture
    that carried a second copy would be a fixture that could pass a screen the
    ruleset calls empty.
    """

    wanted = paths.ruleset.floors.min_shortlist
    got = pool.counts.n_returned
    if got < wanted:
        raise ScreenIsEmpty(_complaint("the pool", pool, wanted, got))
    return (
        f"pool · {THE_POPULATED_PLAYER.slug} · padel competitive: "
        f"{pool.counts.n_returned} above the floor of "
        f"{pool.counts.n_generated} generated "
        f"({pool.counts.n_cleared_floor} cleared, "
        f"{pool.counts.n_near_miss_recorded} near misses)"
    )


def _refuse_a_gender_gate_that_never_fires(pool: SearchRecord) -> str:
    """*At least one candidate is excluded by the mutual gender gate.*

    ``docs/adr/0096`` makes this gate **invisible to the scorer** and to every
    screen — the pool description is deliberately post-gate, so its delta cannot
    be read — which means a fixture is the only thing that can ever show it
    firing. A cohort where it never fires is a cohort in which the whole rule is
    dead code nobody would notice.
    """

    excluded = pool.counts.excluded_by_gate.get(GateCode.GENDER_PREFERENCE.value, 0)
    if excluded < 1:
        raise ScreenIsEmpty(
            f"the mutual gender gate excluded nobody from "
            f"{THE_POPULATED_PLAYER.slug}'s padel pool of "
            f"{pool.counts.n_generated}. ADR-0096's gate is invisible to the "
            f"scorer and to every screen, so a fixture is the only thing that "
            f"can show it firing at all. The rule that puts somebody in its way "
            f"is `EVERY_NTH_EXCLUDES_THE_PROTAGONIST` in `app/seeds/cohort.py`."
        )
    return f"gender gate · excluded {excluded} candidate(s) from the padel pool"


def _refuse_a_window_with_only_one_side(pool: SearchRecord) -> str:
    """*Both sides of the newcomer window are present.*

    Read off the **recorded raw signal input** rather than off the population,
    which is this whole file's rule: what matters is that the search saw both a
    newcomer and a settled member, not that the generator wrote both down.
    """

    seen = {
        row.liveness_signals.get("NEWCOMER_LIFT")
        for row in pool.candidates
        if row.liveness_signals
    }
    if not {True, False} <= seen:
        raise ScreenIsEmpty(
            f"{THE_POPULATED_PLAYER.slug}'s padel search saw "
            f"{'only newcomers' if seen == {True} else 'no newcomer at all'} "
            f"across {len(pool.candidates)} scored row(s). ADR-0113 changes the "
            f"*gate* on newness, and a gate with one side present cannot be "
            f"seen — the run's clocks are what put both sides there."
        )
    return "newcomer window · both sides present among the scored rows"


def _complaint(surface: str, record: SearchRecord, wanted: int, got: int) -> str:
    """What a failure prints. **Never only the two counts.**

    ``terms``, ``degraded_terms``, ``modifiers`` and ``rung_taken`` are already
    on the row the search just wrote, and not printing them is choosing to make
    every future developer re-derive what the system has just computed. The
    breakdown is the best row's, because *why did nobody clear* is answered by
    looking at whoever came closest.
    """

    best = max(
        record.candidates, key=lambda row: row.fit, default=None
    )
    breakdown = "no candidate was scored at all"
    if best is not None:
        breakdown = (
            f"best row fit {best.fit:.1f} · "
            f"terms {[term.get('code', term) for term in best.terms]} · "
            f"degraded {list(best.degraded_terms)} "
            f"({list(best.degraded_reasons)}) · "
            f"modifiers {[m.get('code', m) for m in best.modifiers]} · "
            f"concerns {list(best.concerns)}"
        )
    return (
        f"{surface} is empty for the protagonist this cohort was built around. "
        f"Searcher {record.searcher_id} · {record.sport.value} · "
        f"{record.surface.value} · asked for {wanted} and got {got}, from a "
        f"pool of {record.counts.n_generated} generated, "
        f"{record.counts.n_scored} scored and "
        f"{record.counts.n_cleared_floor} above the floor "
        f"(best withheld {record.best_withheld_fit}). "
        f"Gates: {dict(sorted(record.counts.excluded_by_gate.items()))}. "
        f"Rung taken: {record.rung_taken}. {breakdown}."
    )


# ---------------------------------------------------------------------------
# The reason lines, enumerated from the backend's own closed set
# ---------------------------------------------------------------------------

#: The printable codes this cohort **cannot** draw, each with the reason.
#:
#: **Not a list of exceptions — a list of measured absences, and each is
#: checked.** Every entry here is asserted to be genuinely absent from the run,
#: so the day its provider lands the assertion goes red and says the code has to
#: move to the promised side. The partition against the live ruleset is checked
#: too, so a ruleset that adds a printable signal fails by name rather than
#: quietly widening what *every reason line* means.
CANNOT_BE_DRAWN: Mapping[str, str] = {
    "ANSWER_RATE_AND_SPEED": (
        "*answers challenges* is a Player Score Strand, `player_score` does not "
        "exist, and `fence.py` reads `None` for it by name"
    ),
    "RECENT_ACTIVITY": (
        "`last_active_at` is projected from refresh-token events, and no seeded "
        "member has ever signed in — the seed writes no session and will not "
        "fabricate one"
    ),
    "PREVIOUS_ACCEPT": (
        "the seed writes `users`, `rating` and `player_profile` and does not "
        "write a challenge, so no pairwise answer exists to price"
    ),
    "CHALLENGE_LOAD_SOME": "no seeded member has an inbox — see PREVIOUS_ACCEPT",
    "CHALLENGE_LOAD_BUSY": "no seeded member has an inbox — see PREVIOUS_ACCEPT",
    "CHALLENGE_LOAD_FULL": "no seeded member has an inbox — see PREVIOUS_ACCEPT",
}


def _printable_codes(ruleset: Ruleset) -> frozenset[str]:
    """Every code a card can draw, off the **live ruleset** and never a copy.

    The full inbox is the one signal whose codes are not its own name: its rungs
    each carry their own, so a threshold moving cannot silently re-point a code
    at a different depth — and the vocabulary stays one flat closed set.
    """

    liveness = ruleset.liveness
    codes: set[str] = set()
    for signal, bound in liveness.signals.items():
        if not bound.printable:
            continue
        if signal.value == "CHALLENGE_LOAD":
            codes.update(
                f"{signal.value}_{rung.prints.value}"
                for rung in liveness.challenge_load_rungs
            )
        else:
            codes.add(signal.value)
    return frozenset(codes)


def _refuse_a_reason_line_that_cannot_be_drawn(
    paths: _ReadPaths, pool: SearchRecord
) -> str:
    """*Every reason line the cards can draw is exhibited by at least one row.*

    Enumerated from the **backend's own closed code set** and not from the
    client's sentence table, so this does not wait on the client having a
    sentence for each — and so that a ruleset that makes a silent signal
    printable is caught here rather than on a screen nobody looked at.
    """

    printable = _printable_codes(paths.ruleset)
    promised = printable - set(CANNOT_BE_DRAWN)
    stray = set(CANNOT_BE_DRAWN) - printable
    if stray:
        raise ScreenIsEmpty(
            f"{sorted(stray)} is named as a reason line this cohort cannot draw "
            f"and the live ruleset has no such printable code. The exclusion "
            f"list in `app/seeds/screens.py` is stale."
        )

    drawn = {code for row in pool.candidates for code in row.liveness_reasons}
    missing = sorted(promised - drawn)
    if missing:
        raise ScreenIsEmpty(
            f"{THE_POPULATED_PLAYER.slug}'s padel pool drew "
            f"{sorted(drawn)} and never {missing}, across "
            f"{len(pool.candidates)} scored row(s). Every reason line a card can "
            f"draw is meant to be exhibited by at least one candidate — a "
            f"sentence no fixture reaches is a sentence nobody has read on a "
            f"screen."
        )
    landed = sorted(drawn & set(CANNOT_BE_DRAWN))
    if landed:
        raise ScreenIsEmpty(
            f"{landed} was drawn, and this file says it cannot be. Its provider "
            f"has landed, so the code belongs on the promised side of "
            f"`CANNOT_BE_DRAWN` and the cohort owes it a witness."
        )
    return (
        f"reason lines · drew {sorted(drawn)}; "
        f"{len(CANNOT_BE_DRAWN)} code(s) provably unreachable and stated"
    )


# ---------------------------------------------------------------------------
# The deck, the court, and the ladder
# ---------------------------------------------------------------------------


async def _refuse_a_deck_that_deals_nothing(paths: _ReadPaths) -> str:
    """*The deck deals ≥ N cards.*

    A different surface and not a second read of the same one: the deck resolves
    its weight vector from the viewer's **declaration** rather than from a mode,
    orders on three bands, and applies exclusions no shortlist has. A cohort that
    fills a list and empties a deal is a cohort that has proved half of what it
    promised.
    """

    answer = await paths.deck.execute(
        RunDeckDealCommand(
            searcher_id=paths.players[THE_POPULATED_PLAYER.email],
            sport=Sport.PADEL,
            availability_override=None,
            trace_id=TRACE_ID,
        )
    )
    dealt = answer.record.counts.n_returned
    if dealt < CARDS_A_DEAL_MUST_CARRY:
        raise ScreenIsEmpty(
            _complaint("the deck", answer.record, CARDS_A_DEAL_MUST_CARRY, dealt)
        )
    return (
        f"deck · {THE_POPULATED_PLAYER.slug} · padel: {dealt} card(s) dealt, "
        f"intent read {answer.record.intent_read}, "
        f"{answer.record.n_excluded_by_suppression} removed by suppression"
    )


async def _refuse_a_court_that_cannot_be_filled(paths: _ReadPaths) -> str:
    """*A full four composes.*

    The line-up is where ``docs/adr/0116``'s six-pair rule runs, so this is the
    only assertion that reads a gate applied to a pair the searcher is not in.
    Three of four is an honest answer on a screen and a **failure** here: the
    cohort exists so that a full court is reachable.
    """

    answer = await paths.lineup.execute(
        RunLineupSearchCommand(
            searcher_id=paths.players[THE_POPULATED_PLAYER.email],
            sport=Sport.PADEL,
            mode=SearchMode.COMPETITIVE,
            locked_seats=(),
            availability_override=None,
            offered_by_search_id=None,
            rung=None,
            trace_id=TRACE_ID,
        )
    )
    open_seats = [seat for seat in answer.seats if seat.player_id is None]
    if open_seats:
        raise ScreenIsEmpty(
            _complaint(
                "the court",
                answer.record,
                len(answer.seats),
                len(answer.seats) - len(open_seats),
            )
            + " Open seats: "
            + ", ".join(
                f"{seat.seat_index} ({seat.unfilled_reason})" for seat in open_seats
            )
            + "."
        )
    return (
        f"court · {THE_POPULATED_PLAYER.slug} · padel: {len(answer.seats)} seats "
        f"filled, {len(answer.arrangements)} arrangement(s), "
        f"group reason {answer.group_reason}, dock {answer.dock}"
    )


async def _refuse_a_ladder_that_adds_nobody(paths: _ReadPaths) -> list[str]:
    """*Each rung adds at least one candidate, and the second climb is refused.*

    **Run on tennis, and the reason is structural rather than a preference.**
    ``MIN_SHORTLIST`` decides whether a ladder is priced at all, so the padel
    search the pool assertion demands — five rows or more — is by construction a
    search with no rungs on it. Tennis is the thin sport here: every third member
    plays it, so the protagonist's tennis list is short and the rungs are real.

    The rings are cut by the ladder's own multipliers, so each rung reaches a
    ring the one below it did not — which is what makes *adds at least one* a
    property of the fixture rather than a hope about a draw.
    """

    first = await _shortlist(
        paths, THE_POPULATED_PLAYER, Sport.TENNIS, SearchMode.FOR_FUN
    )
    if first.rung_offers is None:
        raise ScreenIsEmpty(
            f"{THE_POPULATED_PLAYER.slug}'s tennis list returned "
            f"{first.counts.n_returned} row(s) and cleared MIN_SHORTLIST, so no "
            f"rung was priced at all. The ladder is then unwatchable end to "
            f"end: the cohort's second sport has to stay thin enough to trigger "
            f"it. See the ring table in `app/seeds/cohort.py`."
        )
    if not first.rung_offers:
        raise ScreenIsEmpty(
            _complaint("the ladder", first, 1, 0)
            + " The ladder was priced and offered nothing, so no widening "
            "reaches anybody the base radius did not."
        )
    barren = [
        offer for offer in first.rung_offers if offer.candidates_above_floor < 1
    ]
    if barren:
        raise ScreenIsEmpty(
            f"{len(barren)} of {len(first.rung_offers)} rung(s) offered to "
            f"{THE_POPULATED_PLAYER.slug} would add nobody: "
            + ", ".join(
                f"{offer.rung.value}/{offer.ask.value} → "
                f"{offer.candidates_above_floor}"
                for offer in first.rung_offers
            )
            + ". The rings are cut by the ladder's own multipliers so that each "
            "rung finds somebody new by construction."
        )

    taken = first.rung_offers[-1]
    second = await _shortlist(
        paths,
        THE_POPULATED_PLAYER,
        Sport.TENNIS,
        SearchMode.FOR_FUN,
        offered_by_search_id=first.id,
        rung=taken.rung,
    )
    if second.rung_taken is not taken.rung:
        raise ScreenIsEmpty(
            f"the accepting search recorded rung {second.rung_taken} and cited "
            f"{second.offered_by_search_id}, where {taken.rung.value} and "
            f"{first.id} were taken."
        )
    if second.rung_offers is None or second.rung_offers:
        raise ScreenIsEmpty(
            f"a search that took rung {taken.rung.value} was offered "
            f"{second.rung_offers} more. **One climb per search screen**: a "
            f"search that is itself a taken rung prices none, or four taps from "
            f"8 km land on the 50 km ceiling without the player being asked."
        )
    return [
        "ladder · "
        + " · ".join(
            f"{offer.rung.value}/{offer.ask.value} adds "
            f"{offer.candidates_above_floor} (radius {offer.radius_km}, "
            f"slot {offer.slot}, window {offer.window.value})"
            for offer in first.rung_offers
        ),
        f"ladder · the second climb was refused: rung {second.rung_taken} taken, "
        f"{len(second.rung_offers)} offered",
    ]


# ---------------------------------------------------------------------------
# The two asymmetries a unit test cannot show
# ---------------------------------------------------------------------------


async def _somebody_says_lets_play(paths: _ReadPaths, *, cohort: Cohort) -> str:
    """A real *Let's play*, so the one lift that **admits** has a witness.

    ``INTEREST_RECEIVED`` is the only signal that can pull a candidate through
    ``QUALITY_FLOOR``, and it is the only printable signal whose input the
    generator cannot write down: a yes cites the search that showed the person,
    and an origin key is refused unless that search really showed them. So a
    member runs their **own** pool search here and says yes off it — two real
    read paths and a real write, rather than a row nobody could have produced.

    Idempotent by the use case's own rule: a second yes returns the first
    unchanged, does not re-date the expiry and does not spend a cap slot.
    """

    target = paths.players[THE_POPULATED_PLAYER.email]
    tried: list[str] = []
    for member in _who_might_see_the_protagonist(cohort):
        record = (
            await paths.shortlist.execute(
                RunShortlistSearchCommand(
                    searcher_id=paths.players[member.email],
                    sport=Sport.PADEL,
                    mode=SearchMode.COMPETITIVE,
                    availability_override=None,
                    offered_by_search_id=None,
                    rung=None,
                    trace_id=TRACE_ID,
                )
            )
        ).record
        tried.append(f"{member.handle} ({record.counts.n_returned} row(s))")
        if any(row.player_id == target for row in record.candidates):
            await paths.interest.execute(
                ExpressInterestCommand(
                    from_player_id=paths.players[member.email],
                    to_player_id=target,
                    sport=Sport.PADEL,
                    search_id=record.id,
                )
            )
            return (
                f"interest · {member.handle} said *Let's play* to "
                f"{THE_POPULATED_PLAYER.slug}, citing search {record.id}"
            )
    raise ScreenIsEmpty(
        f"no cohort member's own padel pool contained "
        f"{THE_POPULATED_PLAYER.slug}, across {len(tried)} attempt(s): "
        + ", ".join(tried)
        + ". A yes cites the search that showed the person, so without one the "
        "interest lift — the only lift that admits below the floor — has no "
        "witness on any screen."
    )


def _who_might_see_the_protagonist(cohort: Cohort) -> Sequence[CohortMember]:
    """The members most likely to have the protagonist in their own pool.

    The protagonist is at the centre and these are the nearest ring's club
    players, widest radius first — a member's own radius gates their own search,
    and nothing else here decides who can see whom.
    """

    inner = [
        member
        for member in cohort.members
        if member.ring == "a" and member.archetype == "club-player"
    ]
    return sorted(inner, key=lambda member: -member.radius_km)[:3]


async def _refuse_a_fill_that_shows_an_opted_out_member(
    paths: _ReadPaths, pool: SearchRecord, *, now: Instant
) -> str:
    """*At least one member is in the pool and not in the engine's fill.*

    ``gates.py`` gates ``SearchInitiation.ENGINE`` only — *that gate gates the
    push, not the person* — so a player who opted out of proposals is a **full
    candidate in a search a human ran** and absent from anything the engine
    pushes. A unit test proves the gate; only a fixture proves that the two
    screens differ, and somebody who has never seen one reads the difference as a
    bug in the fill.

    **No route runs an engine-initiated search in this build**, so the engine's
    side is bound through the workbench with that initiation and put through the
    same pipeline the shortlist runs. That is this system's own code rather than
    a second implementation of the gate — the one thing it does not have is a
    route, which is exactly what the fixture is standing in for.
    """

    code = GateCode.PROPOSALS_OPT_OUT.value
    by_hand = pool.counts.excluded_by_gate.get(code, 0)
    pushed = (
        await _as_the_engine_would_fill(
            paths, THE_POPULATED_PLAYER, Sport.PADEL, SearchMode.COMPETITIVE, now=now
        )
    ).get(code, 0)
    if by_hand != 0:
        raise ScreenIsEmpty(
            f"a human-run search excluded {by_hand} candidate(s) for having "
            f"opted out of proposals. That gate gates the push, not the person."
        )
    if pushed < 1:
        raise ScreenIsEmpty(
            f"the engine's fill excluded nobody for having opted out of "
            f"proposals, over a pool of {pool.counts.n_generated}. The rule that "
            f"puts somebody in its way is `EVERY_NTH_HAS_OPTED_OUT` in "
            f"`app/seeds/cohort.py`, and without a witness the two screens are "
            f"indistinguishable."
        )
    return (
        f"proposals opt-out · {pushed} member(s) are full candidates in the "
        f"human-run pool and absent from the engine's fill"
    )


async def _as_the_engine_would_fill(
    paths: _ReadPaths,
    account: SeedAccount,
    sport: Sport,
    mode: SearchMode,
    *,
    now: Instant,
) -> Mapping[str, int]:
    """The same search, bound as a push.

    **Nothing is recorded and nothing is shown**: it is run for its gate counts.
    """

    workbench = paths.workbench
    declared = await workbench.searcher_facts(
        player_id=paths.players[account.email], sport=sport, mode_of=lambda _: mode
    )
    asked = await workbench.asked_for(
        declared,
        availability_override=None,
        offered_by_search_id=None,
        rung=None,
    )
    searcher = replace(declared, grid=asked.grid, radius_km=asked.radius_km)
    snapshot, _ = workbench.bound_snapshot(sport, now)
    context = await workbench.bind(
        searcher,
        snapshot,
        now,
        in_box=workbench.population(searcher, snapshot),
        surface=SearchSurface.SHORTLIST,
        initiation=SearchInitiation.ENGINE,
        for_a_newcomer=searcher.is_new_at(now),
    )
    return run_the_pipeline(context, paths.engine).counts.excluded_by_gate


# ---------------------------------------------------------------------------
# One question each, of the three accounts named for one state
# ---------------------------------------------------------------------------


async def _the_three_named_states(paths: _ReadPaths) -> list[str]:
    """The state each of the other three protagonists is named for, and no more.

    Running the full battery four times would cost a dozen assessments' worth of
    reading to re-observe what the default protagonist has already proved, and an
    account is named for **one** state.
    """

    return [
        await _refuse_a_newcomer_whose_gate_did_not_tighten(paths),
        await _refuse_a_second_sport_that_is_not_visibly_absent(paths),
        await _refuse_a_blank_week_that_scored_a_nought(paths),
    ]


async def _refuse_a_newcomer_whose_gate_did_not_tighten(paths: _ReadPaths) -> str:
    """*the-newcomer* — the widened gate, read from the newcomer's own side.

    ADR-0113 binds the **pairing**: while either side is inside its window the
    level tolerance is the competitive one in both modes. The two accounts
    compared here answer the questionnaire identically, sit at the same
    coordinates with the same radius, the same week, the same tags and the same
    gender — the **only** difference between them is the day their profile was
    committed. So a difference in how many candidates the level gate removes from
    a *for fun* search is the window and nothing else.
    """

    settled = await _shortlist(
        paths, THE_POPULATED_PLAYER, Sport.PADEL, SearchMode.FOR_FUN
    )
    new = await _shortlist(paths, THE_NEWCOMER, Sport.PADEL, SearchMode.FOR_FUN)
    code = GateCode.LEVEL.value
    theirs = new.counts.excluded_by_gate.get(code, 0)
    hers = settled.counts.excluded_by_gate.get(code, 0)
    if theirs <= hers:
        raise ScreenIsEmpty(
            f"{THE_NEWCOMER.slug}'s *for fun* search had {theirs} candidate(s) "
            f"removed by the level gate and {THE_POPULATED_PLAYER.slug}'s had "
            f"{hers}. The two answer identically and differ only in the day "
            f"their profile was committed, so the newcomer's gate is meant to "
            f"be the **tighter** one — ADR-0113 binds the pairing, in both "
            f"modes."
        )
    return (
        f"newcomer gate · {THE_NEWCOMER.slug} lost {theirs} to the level gate "
        f"where {THE_POPULATED_PLAYER.slug} lost {hers}, on the same answers"
    )


async def _refuse_a_second_sport_that_is_not_visibly_absent(
    paths: _ReadPaths,
) -> str:
    """*the-one-sport-player* — the second sport's absence, said out loud.

    A refusal and never an empty list: *there is nobody near you in tennis* and
    *you have no tennis rating* are two different screens, and a fixture where
    the second one renders as the first is a fixture that hides the state this
    account exists for.
    """

    try:
        record = await _shortlist(
            paths, THE_ONE_SPORT_PLAYER, Sport.TENNIS, SearchMode.COMPETITIVE
        )
    except SportNotRated as refused:
        return (
            f"one sport · {THE_ONE_SPORT_PLAYER.slug}'s tennis search is "
            f"refused rather than emptied: {refused}"
        )
    raise ScreenIsEmpty(
        f"{THE_ONE_SPORT_PLAYER.slug} has no tennis rating and their tennis "
        f"search answered with {record.counts.n_returned} row(s) instead of "
        f"refusing. An unrated sport is a different screen from an empty one."
    )


async def _refuse_a_blank_week_that_scored_a_nought(paths: _ReadPaths) -> str:
    """*the-blank-week-player* — the availability term stands down.

    A cleared week is *we do not know*, not *never free*: a nought would rank
    this player below somebody whose week genuinely misses everybody's, which is
    the platform punishing a player for a question they answered and then
    withdrew. What the row must carry is a **degraded** term with a reason on it.
    """

    record = await _shortlist(
        paths, THE_BLANK_WEEK_PLAYER, Sport.PADEL, SearchMode.COMPETITIVE
    )
    term = Term.AVAILABILITY_OVERLAP.value
    standing = [row for row in record.candidates if term not in row.degraded_terms]
    if not record.candidates or standing:
        raise ScreenIsEmpty(
            f"{THE_BLANK_WEEK_PLAYER.slug} has a cleared week and "
            f"{len(standing)} of {len(record.candidates)} scored row(s) still "
            f"carry a live {term}. A cleared week is *we do not know* and the "
            f"term stands down, renormalising the rest — a nought would rank "
            f"them below somebody whose week genuinely misses everybody's."
        )
    reasons = sorted(
        {
            reason
            for row in record.candidates
            for name, reason in zip(
                row.degraded_terms, row.degraded_reasons, strict=True
            )
            if name == term
        }
    )
    return (
        f"blank week · {THE_BLANK_WEEK_PLAYER.slug}: {term} stood down on all "
        f"{len(record.candidates)} scored row(s), reasons {reasons}"
    )
