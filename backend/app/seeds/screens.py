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

**A third list arrived with the played history, and it is the same list.** The
record block — the Player Score, the counted-game count, the run of form — and
the photograph's verdict are asserted here like everything else: off the cards
the protagonist's own pool handed back, never off the declaration that produced
them. What a fixture may claim about them is that the **states** are reachable —
a full run, a gap, an absence, a shield and both of its silences — and never that
a particular member's count is a particular number, which would be the population
checking its own arithmetic.

**These reads leave records behind, and there are two kinds.** A search run
through its real use case writes to ``matchmaking``'s own store, and a search
record never expires (``docs/adr/0104``), so every ``make seed`` grows that
table by a handful of rows. The second kind is an **interest row**: exhibiting
``INTEREST_RECEIVED`` needs a yes, a yes cites the search that showed the person,
and no generator can write one — so a member runs their own pool search here and
says *Let's play* off it. That is a durable write outside the search store, and
it is written down rather than buried: it is **one row for the life of the yes
and not one per run**, because ``ExpressInterest`` is idempotent on the pair — a
second yes returns the first unchanged, does not re-date the expiry and does not
spend a cap slot. Both are taken as acceptable on the same argument: the seed
genuinely ran those searches and that member genuinely said yes, the rows are
true, and a fixture database is disposable. Flagged here so it can be overturned
cheaply if a later reader disagrees.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import build_candidate_source
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Instant, Sport
from app.modules.challenges.application.read_challenge import ReadChallengeCommand
from app.modules.challenges.application.read_challenges import ReadChallengesCommand
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW_HOURS
from app.modules.challenges.domain.seats import SeatAnswer
from app.modules.challenges.domain.standing import ENDED
from app.modules.games.domain.standing import GameStanding
from app.modules.player_profile.domain.photos import PhotoReviewDecision
from app.modules.player_profile.domain.ports import PhotoStorage
from app.modules.matchmaking.application.commands import (
    ExpressInterestCommand,
    ReadInterestCommand,
    RunLineupSearchCommand,
)
from app.modules.matchmaking.domain.errors import SportNotRated
from app.modules.matchmaking.domain.gates import GateCode
from app.modules.matchmaking.domain.searches import (
    LAST_FIVE,
    GameResult,
    RecordedCard,
    SearchCandidateRecord,
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
from app.seeds.cohort import COHORT, PLAYED_GAMES, Cohort, PlayedGame
from app.seeds.pairs import SeededPairs
from app.seeds.paths import (
    TRACE_ID,
    ReadPaths,
    deal_a_deck,
    read_paths,
    returned_ids,
    run_a_shortlist,
    the_ephemeral_store,
    tick_the_tail_to_catch_up,
)
from app.seeds.relationships import (
    ABSENT_ON_THE_BLOCKED_GATE,
    ABSENT_ON_THE_OPEN_CHALLENGE_GATE,
    IN_YOUR_LINE_UP_AND_ACCEPTED,
    IN_YOUR_LINE_UP_STILL_DECIDING,
    PROTAGONIST,
    SAID_YES_TO_YOU,
    THEY_BLOCKED_YOU,
    THEY_CHALLENGED_YOU,
    THEY_TURNED_DOWN_YOUR_COURT,
    YOUR_YES_MAKES_IT_MUTUAL,
    YOU_PASSED_THEM,
    YOU_SAID_YES_TO_THEM,
    Relationship,
)

# **How many rows the pool must carry is deliberately not a constant here.** It
# is ``MIN_SHORTLIST``, read off the live ruleset at the assertion: the product's
# answer to *this list is too short to be useful* has an owner, and a second copy
# in a fixture is a fixture that can pass a screen the ruleset calls empty.

#: How many cards a deal must produce. Deliberately below ``deck_deal_max``: a
#: deck asserted at its ceiling would be asserting the cap rather than the pool.
CARDS_A_DEAL_MUST_CARRY = 3

# **How long an invited seat has is read off the domain, never restated here.**
# Nothing in this package backdates a challenge, so how stale a database may be
# and still draw the inbound-court screen *is* that number — and a refusal
# carrying its own copy would send a developer looking for a court that lapsed
# hours before the sentence said it could.


class ScreenIsEmpty(RuntimeError):
    """A screen the cohort promised is one this database cannot draw.

    A ``RuntimeError`` for ``SeedFailed``'s reason — it is a refusal to hand a
    developer a fixture whose promise is a lie, not a bad argument a caller might
    catch. It is raised rather than warned for the same reason the whole file
    exists: a warning in a make target scrolls past, and the fixture then rots
    silently.
    """


async def assert_the_screens(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    pairs: SeededPairs,
    cohort: Cohort = COHORT,
    photographs: bool = True,
    photos: PhotoStorage | None = None,
) -> tuple[str, ...]:
    """Read every screen the fixture promises, and refuse a database that cannot.

    Returns the lines the report prints. They are the **evidence**, not a
    decoration: what a failure has to print is the assertion, the protagonist,
    the surface and both counts, and printing the same breakdown on the way
    through is what makes the passing run legible too.

    ``pairs`` carries the one deal this run has already made as the protagonist.
    The deck's own claims are read off that record rather than off a fresh deal,
    because ``DEALT_MEMORY`` is a day: a second deal would find every card of the
    first already spent, and asserting against it would be asserting about the
    remainder rather than about the deck.
    """

    await tick_the_tail_to_catch_up(session_factory, settings=settings)
    candidates = build_candidate_source(session_factory=session_factory)
    await candidates.refresh()

    lines: list[str] = []
    async with the_ephemeral_store(settings) as redis:
        async with session_factory() as session:
            paths = await read_paths(
                session,
                settings=settings,
                candidates=candidates,
                cohort=cohort,
                now=now,
                redis=redis,
                photos=photos,
            )
            pool = await run_a_shortlist(
                paths,
                THE_POPULATED_PLAYER.email,
                Sport.PADEL,
                SearchMode.COMPETITIVE,
            )
            deck = pairs.the_deal_that_earned_the_pass
            battery, line_up = await _the_full_battery(
                paths,
                pool,
                deck,
                spent=pairs.the_deck_was_already_spent,
                cohort=cohort,
                now=now,
            )
            lines.extend(battery)
            lines.extend(
                await _the_eleven(paths, pool, line_up, pairs=pairs)
            )
            lines.extend(
                await _the_record_block(
                    paths,
                    pool,
                    cohort=cohort,
                    now=now,
                    photographs=photographs,
                )
            )
            lines.extend(await _the_three_named_states(paths))
    return tuple(lines)


# ---------------------------------------------------------------------------
# The full battery, against the-populated-player
# ---------------------------------------------------------------------------


async def _the_full_battery(
    paths: ReadPaths,
    pool: SearchRecord,
    deck: SearchRecord,
    *,
    spent: bool,
    cohort: Cohort,
    now: Instant,
) -> tuple[list[str], SearchRecord]:
    """Everything the default protagonist proves, in the order it is proved.

    The pool is handed in rather than run here, because the eleven relationships
    are read off the **same** search: two searches would be two answers, and a
    claim about a card would then be a claim about a card nobody was shown.
    """

    court, line_up = await _refuse_a_court_that_cannot_be_filled(paths)
    lines = [
        _refuse_a_pool_that_cannot_fill_a_screen(paths, pool),
        _refuse_a_gender_gate_that_never_fires(pool),
        _refuse_a_window_with_only_one_side(pool),
        _refuse_a_reason_line_that_cannot_be_drawn(paths, pool),
        _refuse_a_deck_that_deals_nothing(deck, spent=spent),
        court,
    ]
    lines.extend(await _refuse_a_ladder_that_adds_nobody(paths))
    lines.append(
        await _refuse_a_fill_that_shows_an_opted_out_member(paths, pool, now=now)
    )
    return lines, line_up


def _refuse_a_pool_that_cannot_fill_a_screen(
    paths: ReadPaths, pool: SearchRecord
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
        "*answers challenges* is a Player Score Strand and `player_score` "
        "publishes it now, but this signal is a ramp over a rate **and a "
        "speed** — nothing publishes the speed, so `fence.py` still reads "
        "`None` for it by name (`docs/adr/0140`)"
    ),
    "RECENT_ACTIVITY": (
        "`last_active_at` is projected from refresh-token events, and no seeded "
        "member has ever signed in — the seed writes no session and will not "
        "fabricate one"
    ),
}

# **`PREVIOUS_ACCEPT` was named above until the pool got a history, and it moved
# twice.** *Open* was `AWAITING_ANSWERS | ON | LINE_UP_INCOMPLETE`, so any pair with an
# accepted seat was `OPEN_CHALLENGE`-gated for ever and the signal could not be drawn
# anywhere; `docs/adr/0142` §1 made *open* mean **still arranging**, so a completed
# line-up releases its pair and the code became drawable (#343). Both halves of that are
# contracted by demands in `tests/demands/`.
#
# It stayed absent from **this** pool for one more reason after that: every accepted
# seat the eleven relationship fixtures write sits on a court still being arranged, and
# the games that seat the protagonist seat her as the **invitee**, so the accepts were
# hers and the tally they leave sits on her card in *their* pools. `pool_history.py`
# reverses that — she organises four of its five courts, so eight of the people in her
# pool have accepted a seat **from her**, and every one of their cards carries the
# tally. The code is promised now, and the assertion below has stopped stating an
# absence and started requiring the witness.
#


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
    paths: ReadPaths, pool: SearchRecord
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


def _refuse_a_deck_that_deals_nothing(record: SearchRecord, *, spent: bool) -> str:
    """*The deck deals >= N cards.*

    A different surface and not a second read of the same one: the deck resolves
    its weight vector from the viewer's **declaration** rather than from a mode,
    orders on three bands, and applies exclusions no shortlist has. A cohort that
    fills a list and empties a deal is a cohort that has proved half of what it
    promised.

    **Read off the deal this run already made** rather than off a fresh one.
    ``DEALT_MEMORY`` is a day, so a second deal deals the remainder — and a
    fixture that asserted against the remainder would be asserting about
    whichever cards the first deal happened to leave.
    """

    dealt = record.counts.n_returned
    if spent:
        return (
            f"deck · {THE_POPULATED_PLAYER.slug} · padel: **not read** — this "
            f"run's deal found a deck an earlier one had already spent, and a "
            f"deal is remembered for a day. That is ADR-0131's cost, not an "
            f"empty pool; the run that proves the deal fills is the one against "
            f"a fresh database."
        )
    if dealt < CARDS_A_DEAL_MUST_CARRY:
        raise ScreenIsEmpty(
            _complaint("the deck", record, CARDS_A_DEAL_MUST_CARRY, dealt)
        )
    return (
        f"deck · {THE_POPULATED_PLAYER.slug} · padel: {dealt} card(s) dealt, "
        f"intent read {record.intent_read}, "
        f"{record.n_excluded_by_suppression} in range under a live suppression"
    )


async def _refuse_a_court_that_cannot_be_filled(
    paths: ReadPaths,
) -> tuple[str, SearchRecord]:
    """*A full four composes.*

    The line-up is where ``docs/adr/0116``'s six-pair rule runs, so this is the
    only assertion that reads a gate applied to a pair the searcher is not in.
    Three of four is an honest answer on a screen and a **failure** here: the
    cohort exists so that a full court is reachable.
    """

    answer = await paths.lineup.execute(
        RunLineupSearchCommand(
            searcher_id=paths.player(THE_POPULATED_PLAYER.email),
            sport=Sport.PADEL,
            mode=SearchMode.COMPETITIVE,
            locked_seats=(),
            completing_challenge_id=None,
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
        f"group reason {answer.group_reason}, dock {answer.dock}",
        answer.record,
    )


async def _refuse_a_ladder_that_adds_nobody(paths: ReadPaths) -> list[str]:
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

    first = await run_a_shortlist(
        paths, THE_POPULATED_PLAYER.email, Sport.TENNIS, SearchMode.FOR_FUN
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
    second = await run_a_shortlist(
        paths,
        THE_POPULATED_PLAYER.email,
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
# The asymmetry a unit test cannot show
# ---------------------------------------------------------------------------


async def _refuse_a_fill_that_shows_an_opted_out_member(
    paths: ReadPaths, pool: SearchRecord, *, now: Instant
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
    paths: ReadPaths,
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
        player_id=paths.player(account.email), sport=sport, mode_of=lambda _: mode
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
        completing_challenge_id=None,
    )
    return run_the_pipeline(context, paths.engine).counts.excluded_by_gate


# ---------------------------------------------------------------------------
# One question each, of the three accounts named for one state
# ---------------------------------------------------------------------------


async def _the_three_named_states(paths: ReadPaths) -> list[str]:
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


async def _refuse_a_newcomer_whose_gate_did_not_tighten(paths: ReadPaths) -> str:
    """*the-newcomer* — the widened gate, read from the newcomer's own side.

    ADR-0113 binds the **pairing**: while either side is inside its window the
    level tolerance is the competitive one in both modes. The two accounts
    compared here answer the questionnaire identically, sit at the same
    coordinates with the same radius, the same week, the same tags and the same
    gender — the **only** difference between them is the day their profile was
    committed. So a difference in how many candidates the level gate removes from
    a *for fun* search is the window and nothing else.
    """

    settled = await run_a_shortlist(
        paths, THE_POPULATED_PLAYER.email, Sport.PADEL, SearchMode.FOR_FUN
    )
    new = await run_a_shortlist(
        paths, THE_NEWCOMER.email, Sport.PADEL, SearchMode.FOR_FUN
    )
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
    paths: ReadPaths,
) -> str:
    """*the-one-sport-player* — the second sport's absence, said out loud.

    A refusal and never an empty list: *there is nobody near you in tennis* and
    *you have no tennis rating* are two different screens, and a fixture where
    the second one renders as the first is a fixture that hides the state this
    account exists for.
    """

    try:
        record = await run_a_shortlist(
            paths, THE_ONE_SPORT_PLAYER.email, Sport.TENNIS, SearchMode.COMPETITIVE
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


async def _refuse_a_blank_week_that_scored_a_nought(paths: ReadPaths) -> str:
    """*the-blank-week-player* — the availability term stands down.

    A cleared week is *we do not know*, not *never free*: a nought would rank
    this player below somebody whose week genuinely misses everybody's, which is
    the platform punishing a player for a question they answered and then
    withdrew. What the row must carry is a **degraded** term with a reason on it.
    """

    record = await run_a_shortlist(
        paths, THE_BLANK_WEEK_PLAYER.email, Sport.PADEL, SearchMode.COMPETITIVE
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


# ---------------------------------------------------------------------------
# The record block — what the platform watched, read off the cards it drew
# ---------------------------------------------------------------------------


async def _the_record_block(
    paths: ReadPaths,
    pool: SearchRecord,
    *,
    cohort: Cohort,
    now: Instant,
    photographs: bool,
) -> list[str]:
    """Everything the played history and the photographs promise, off real cards.

    **The pool is the one the battery already ran**, for the reason every claim
    here reads it: a card is what a search handed somebody, and a second search
    would be a second answer about a card nobody was shown.

    Every claim below is about a **state** and none is about a number this
    fixture chose. *Some card draws a full run of five* is a claim about a
    screen; *this member's card says six* would be the population checking its
    own arithmetic, which is the one thing the asymmetry between ``cohort.py``
    and this file exists to refuse — and it would pass on a database where the
    counting was wrong in exactly the way the generator was.
    """

    return [
        _refuse_a_card_the_platform_watched_nothing_of(pool),
        _refuse_a_run_of_form_that_is_five_of_one_thing(pool),
        _refuse_a_player_score_with_only_one_answer(pool),
        await _refuse_an_unscored_game_that_reads_as_evidence(paths, cohort),
        await _refuse_a_pair_with_nothing_between_them(paths, cohort, now=now),
        _refuse_a_shield_whose_absence_has_only_one_cause(
            pool, photographs=photographs
        ),
    ]


def _records(pool: SearchRecord) -> tuple[RecordedCard, ...]:
    """The cards this search handed over. **Returned rows and never near misses.**

    A near-miss row carries no card at all — it was shown to nobody — so a claim
    about a record block proved off one would be a claim about something no
    screen can draw.
    """

    return tuple(row.card for row in pool.returned if row.card is not None)


def _refuse_a_card_the_platform_watched_nothing_of(pool: SearchRecord) -> str:
    """*The three states of the record block are all on this one screen.*

    **Full, gapped and absent**, and the three are one assertion because they are
    one design: a count of nought is not printed as a nought, a run shorter than
    five is not padded, and a card the platform has watched nothing of carries
    neither. A fixture reaching two of them proves nothing about the third —
    *no record* and *a short record* are the two a renderer is most likely to
    draw the same way.
    """

    cards = _records(pool)
    full = [card for card in cards if len(card.last_five) == LAST_FIVE]
    gapped = [
        card
        for card in cards
        if card.counted_games is not None
        and 0 < len(card.last_five) < LAST_FIVE
    ]
    absent = [
        card
        for card in cards
        if card.counted_games is None and not card.last_five
    ]
    unscored = [
        card
        for card in cards
        if card.counted_games is not None
        and len(card.last_five) < card.counted_games
        and card.counted_games <= LAST_FIVE
    ]
    drawn = [
        (card.nickname, card.counted_games, len(card.last_five)) for card in cards
    ]
    for wanted, found, why in (
        (
            "a full run of five",
            full,
            "*Last 5* is five squares and a fixture that never fills it has "
            "never drawn the row it is named for",
        ),
        (
            "a run shorter than five beside a count",
            gapped,
            "fewer than five results is a real answer and is never padded — the "
            "card draws the **gap**, and a fixture with only full runs cannot "
            "tell a gap from a bug",
        ),
        (
            "a card with no record at all",
            absent,
            "*nought games* and *no record* would be one absence in two "
            "spellings, and the whole discipline of this surface is that "
            "absence has one — so the empty card has to be **proved** correct "
            "rather than assumed",
        ),
        (
            "a count with fewer results behind it than games",
            unscored,
            "a counted game can leave no result — an unscored one is *an "
            "evening, not evidence* (``docs/adr/0137``), and one still awaiting "
            "an answer has produced none yet — so a card can print a count its "
            "own run of form falls short of. **Which of the two causes it is, "
            "is not a question a card can answer**, and it is not asked here: "
            "the standing is checked on the games screen instead. The count is "
            "held at or under the run's own length so that a player past five "
            "games, whose gap is the cap rather than a missing result, is not "
            "mistaken for a witness",
        ),
    ):
        if not found:
            raise ScreenIsEmpty(
                f"no card in {THE_POPULATED_PLAYER.slug}'s padel pool draws "
                f"{wanted}, across {len(cards)} card(s) — {drawn}. "
                f"{why}. The population that reaches these states is "
                f"`PLAYED_GAMES` in `app/seeds/cohort.py`, and a database "
                f"seeded before it existed has none of them: drop it and seed "
                f"again."
            )
    return (
        f"record block · {len(full)} card(s) draw a full five, {len(gapped)} "
        f"draw the gap, {len(unscored)} count a game nobody scored, and "
        f"{len(absent)} of {len(cards)} carry no record at all"
    )


def _refuse_a_run_of_form_that_is_five_of_one_thing(pool: SearchRecord) -> str:
    """*The runs of form drawn on this screen are not all one square.*

    A row of five identical squares renders correctly and proves nothing: the
    reader cannot tell a win from a loss, and neither can the developer who is
    looking at the colours. Read across the whole screen rather than one card,
    because what has to be developed against is a **pool** with both in it.
    """

    drawn = {result for card in _records(pool) for result in card.last_five}
    missing = sorted(one.value for one in GameResult if one not in drawn)
    if missing:
        raise ScreenIsEmpty(
            f"every run of form in {THE_POPULATED_PLAYER.slug}'s padel pool "
            f"draws {sorted(one.value for one in drawn)} and never {missing}. "
            f"*Last 5* is win or loss and a row of five identical squares is a "
            f"row nobody can read a mistake off. Who won is declared per game "
            f"in `PLAYED_GAMES`."
        )
    return f"run of form · both {sorted(one.value for one in drawn)} are drawn"


def _refuse_a_player_score_with_only_one_answer(pool: SearchRecord) -> str:
    """*Both answers a Player Score has are on this screen.*

    A number, and an **absence** — and the absence is the claim worth checking,
    because it is the one a renderer reaches for a nought with. Somebody nothing
    was ever arranged for has not failed to turn up, so their card carries no
    figure at all rather than a zero (``docs/adr/0140``).
    """

    cards = _records(pool)
    scored = [card for card in cards if card.player_score is not None]
    silent = [card for card in cards if card.player_score is None]
    if not scored or not silent:
        raise ScreenIsEmpty(
            f"{len(scored)} of {len(cards)} card(s) in "
            f"{THE_POPULATED_PLAYER.slug}'s padel pool carry a Player Score. "
            f"Both answers have to be on one screen: a figure is what the "
            f"platform watched, and an absence is what it never had — and a "
            f"nought would say the two are the same thing."
        )
    return (
        f"player score · {len(scored)} card(s) print one "
        f"({sorted({card.player_score for card in scored if card.player_score})}) "
        f"and {len(silent)} carry none"
    )


async def _refuse_an_unscored_game_that_reads_as_evidence(
    paths: ReadPaths, cohort: Cohort
) -> str:
    """*The game nobody agreed a score for reads as unscored, on its own screen.*

    Read as **somebody who played it**, which is the only side it can be read
    from: a game is not a public record, and the screen that draws a standing is
    the games list of one of the four people who were there. The same departure
    ``they-blocked-you`` makes, and for the same reason — this state is
    unobservable from the protagonist's side by construction.

    **The claim is the standing and not the absence of a score.** ``UNSCORED``
    is what *an evening, not evidence* is called when a clock has passed over
    two people who never agreed, and a fixture that only checked the empty run
    of form on a card could not tell it from a game still awaiting an answer.
    """

    declared = _the_game_nobody_scored()
    reader = cohort.by_handle(declared.organiser)
    _, standing = await paths.read_games.execute(paths.player(reader.email))
    unscored = [row for row in standing if row.standing is GameStanding.UNSCORED]
    if not unscored:
        raise ScreenIsEmpty(
            f"'{reader.handle}' played a game this fixture declares nobody "
            f"agreed a score for, and their own games list reads "
            f"{sorted(row.standing.value for row in standing)}. Two scores and "
            f"no acceptance leave a game **unscored** once both windows close — "
            f"a game still awaiting an answer is a database seeded too "
            f"recently, and `PLAYED_AT_LEAST_DAYS_AGO` in `app/seeds/cohort.py` "
            f"is what keeps it clear of that."
        )
    return (
        f"unscored · '{reader.handle}' reads {len(unscored)} game(s) as "
        f"{GameStanding.UNSCORED.value} across {len(standing)} they played"
    )


async def _refuse_a_pair_with_nothing_between_them(
    paths: ReadPaths, cohort: Cohort, *, now: Instant
) -> str:
    """*Familiarity has something to read about at least one pair.*

    ``SharedHistory`` refuses a record of no games, so a pair who arranged and
    never played carries none at all — which means the modifier stands down for
    everybody until two people on this platform have actually played. What is
    asserted is the **input**, read through the port the matcher reads, and it
    is the input rather than the card because no card in *this* cohort can carry
    the modifier: the pairs that have played are cohort members, and the pool
    every assertion here is read from is the protagonist's, who has played
    nobody. It is no longer unreachable on the platform — `docs/adr/0142` §1
    releases a pair the moment their line-up completes, so two people who have
    played are shown each other again — which is a change of reason and not of
    assertion.
    """

    handle = PLAYED_GAMES[0].organiser
    reader = cohort.by_handle(handle)
    counterparts = await paths.games.played_counterparts(
        paths.player(reader.email), now=now
    )
    played = [one for one in counterparts if one.games_played_together >= 1]
    if not played:
        raise ScreenIsEmpty(
            f"'{handle}' has played every game this fixture declares for them "
            f"and `played_counterparts` answers {len(counterparts)} row(s) with "
            f"nothing played in any of them. Familiarity decays on *days since "
            f"last* and deepens on *games played together*, and a platform "
            f"where nobody has played is a platform where the modifier is dead "
            f"code."
        )
    return (
        f"familiarity · '{handle}' has played {len(played)} counterpart(s), "
        f"deepest {max(one.games_played_together for one in played)} game(s) "
        f"together"
    )


def _refuse_a_shield_whose_absence_has_only_one_cause(
    pool: SearchRecord, *, photographs: bool
) -> str:
    """*All three of ``docs/adr/0138``'s answers are on this screen.*

    Two of them are the **same silence**: a photograph the check flagged draws no
    shield, and so does one nothing ever looked at. They differ only in the
    store, so a fixture holding one of them proves nothing whatever about the
    other — and the state a shield must never be drawn on is the second.
    """

    if not photographs:
        # **The store and never the fixture**, and the run already knows which:
        # it asked the object store one question before it wrote anything. A
        # claim that could not tell *nobody uploaded* from *nothing answered*
        # would report a rotted fixture to somebody whose container is down —
        # the failure the pass's own suppression probe exists to avoid.
        return (
            "photo verdict · **not read** — the object store did not answer, so "
            "this database holds no photograph and the three states a card can "
            "draw are unreachable. Bring MinIO up and seed a fresh database."
        )
    with_photo = [card for card in _records(pool) if card.photo_id is not None]
    by_verdict = {
        "a shield": [
            card
            for card in with_photo
            if card.review is PhotoReviewDecision.ALLOWED
        ],
        "a photograph the check flagged": [
            card
            for card in with_photo
            if card.review is PhotoReviewDecision.FLAGGED
        ],
        "a photograph nobody looked at": [
            card for card in with_photo if card.review is None
        ],
    }
    missing = sorted(name for name, found in by_verdict.items() if not found)
    if missing:
        raise ScreenIsEmpty(
            f"{THE_POPULATED_PLAYER.slug}'s padel pool draws "
            f"{len(with_photo)} card(s) with a photograph and none of them is "
            f"{missing}. A shield says *checked and passed*, and its absence "
            f"has two causes that are indistinguishable on the wire — so a "
            f"fixture that reaches one of them has proved nothing about the "
            f"other. The three carriers are `PHOTOGRAPH_VERDICTS` in "
            f"`app/seeds/cohort.py`; a database seeded before they existed has "
            f"no photograph at all, because a photo list is settled at the "
            f"commit and nothing adds one afterwards. Drop it and seed again."
        )
    return (
        "photo verdict · "
        + ", ".join(
            f"{len(found)} card(s) draw {name}"
            for name, found in by_verdict.items()
        )
    )


def _the_game_nobody_scored() -> PlayedGame:
    """The one declared game the two sides never agreed about.

    Read off the declaration rather than written here, and refused by name when
    there is none: a fixture that quietly lost its unscored game would leave
    this assertion checking that a database has *some* unscored game, which is
    a question about a population rather than about a screen.
    """

    unscored = [game for game in PLAYED_GAMES if not game.was_scored]
    if not unscored:
        raise ScreenIsEmpty(
            "no declared game is left unscored, so *an evening, not evidence* "
            "is unreachable. `PLAYED_GAMES` in `app/seeds/cohort.py` owes this "
            "fixture one game with no agreed score."
        )
    return unscored[0]


# ---------------------------------------------------------------------------
# The eleven, read as the protagonist — the pairwise facts no cohort can assert
# ---------------------------------------------------------------------------


async def _the_eleven(
    paths: ReadPaths,
    pool: SearchRecord,
    line_up: SearchRecord,
    *,
    pairs: SeededPairs,
) -> list[str]:
    """Every relationship claim, read off a surface rather than off the ledger.

    **The pool is the one the battery already ran**, so a card's reason line and
    the absence beside it are two readings of one answer. A second search would
    be a second answer, and a claim about a card would be a claim about a card
    nobody was shown.

    Two of the claims are read off the deal this run made rather than off a fresh
    one, and one insists on a fresh one — which is the whole of what
    ``DEALT_MEMORY`` costs a fixture, said in code.
    """

    deck = pairs.the_deal_that_earned_the_pass
    return [
        _refuse_a_lift_with_no_witness(paths, pool),
        await _refuse_a_mutual_that_is_in_neither_state(
            paths, pool, deck, pairs=pairs
        ),
        await _refuse_an_outstanding_count_of_nothing(paths, pool),
        _refuse_a_refusal_no_card_carries(paths, pool),
        _refuse_an_absence_with_no_gate_behind_it(paths, pool, deck, line_up),
        await _refuse_a_block_only_one_side_can_see(paths),
        await _refuse_a_seat_that_is_not_hers_to_answer(paths),
        await _refuse_a_challenge_screen_with_nobody_on_it(paths),
        await _refuse_a_pass_the_deck_still_deals(paths, pool, pairs=pairs),
    ]


def _card_for(
    paths: ReadPaths, record: SearchRecord, relationship: Relationship
) -> SearchCandidateRecord | None:
    """That account's row **as the answer carried it**, or nothing.

    ``returned`` and never ``candidates``, because every claim that reads a row
    is a claim about a card somebody was shown — a near-miss row is recorded and
    handed to nobody, and an origin key does not resolve against one either, so a
    presence claim proved by a near miss would be proved by something no screen
    can draw.
    """

    them = paths.player(relationship.account.email)
    for row in record.returned:
        if row.player_id == them:
            return row
    return None


def _was_scored(
    paths: ReadPaths, record: SearchRecord, relationship: Relationship
) -> bool:
    """Whether this search scored them at all — shown, or recorded as a near miss.

    The **absence** claims ask this rather than :func:`_card_for`, and the
    asymmetry is deliberate: absence is the stronger statement when it is read
    over everything the search wrote down, because a gated candidate is not
    scored at all while a candidate below the floor is.
    """

    them = paths.player(relationship.account.email)
    return any(row.player_id == them for row in record.candidates)


def _refuse_a_lift_with_no_witness(paths: ReadPaths, pool: SearchRecord) -> str:
    """*``said-yes-to-you`` carries ``INTEREST_RECEIVED`` on her pool card.*

    The only signal that can pull a candidate **through** ``QUALITY_FLOOR``, and
    the only printable one whose input no generator can write down: a yes cites
    the search that showed the person, and an origin key is refused unless that
    search really showed them. So this is the one claim whose falsification is
    also a statement about the platform — if it is missing, either the yes was
    never written or the lift no longer reaches a card.
    """

    row = _card_for(paths, pool, SAID_YES_TO_YOU)
    code = "INTEREST_RECEIVED"
    if row is None or code not in row.liveness_reasons:
        raise ScreenIsEmpty(
            f"'{SAID_YES_TO_YOU.account.slug}' said *Let's play* to "
            f"{PROTAGONIST.slug} and her padel pool "
            + (
                "does not carry them at all"
                if row is None
                else f"draws {sorted(row.liveness_reasons)} on their row"
            )
            + f", never {code}. That lift is the only one that admits a "
            f"candidate below QUALITY_FLOOR, and it is the only printable "
            f"signal a distribution cannot produce."
        )
    return (
        f"interest · {SAID_YES_TO_YOU.account.slug} is in "
        f"{PROTAGONIST.slug}'s padel pool carrying {code}, "
        f"age {row.liveness_signals.get(code)} day(s)"
    )


async def _refuse_a_mutual_that_is_in_neither_state(
    paths: ReadPaths, pool: SearchRecord, deck: SearchRecord, *, pairs: SeededPairs
) -> str:
    """*``your-yes-makes-it-mutual`` is in one of its two states, and no other.*

    **A two-state machine, with everything else illegal.** Either a live inbound
    yes with no open challenge — a deck card carrying *wants to play you* — or
    the challenge that yes became, with that person gated off every surface. The
    second state is a real assertion in its own right rather than a fixture
    rotting: it is *gone for good* checked on a real read. So spending this
    fixture **buys a check rather than breaking one**, and ``make seed`` stays
    green through the ordinary use of the thing it seeds — which is the whole
    point, because a target that goes red as a consequence of using it trains
    people to ignore it.
    """

    them = paths.player(YOUR_YES_MAKES_IT_MUTUAL.account.email)
    open_ones = await paths.history.open_challenges(paths.player(PROTAGONIST.email))
    a_game_stands = any(row.counterpart_id == them for row in open_ones)
    code = "INTEREST_RECEIVED"

    if not a_game_stands and pairs.the_deck_was_already_spent:
        # **Still asserted, on the other surface the yes has.** A deck this run
        # could not deal is not a licence to assert nothing — state one is *a
        # live inbound yes with no open challenge*, and the sender's own
        # outgoing list is the screen that says the yes is still live.
        theirs = await paths.read_interest.execute(
            ReadInterestCommand(player_id=them)
        )
        alive = [
            row
            for row in theirs.outgoing + theirs.mutual
            if row.to_player_id == paths.player(PROTAGONIST.email)
            and row.sport is Sport.PADEL
        ]
        if not alive:
            raise ScreenIsEmpty(
                f"'{YOUR_YES_MAKES_IT_MUTUAL.account.slug}' is in neither state: "
                f"no game stands with {PROTAGONIST.slug} and their own outgoing "
                f"list carries no live yes to her. The fixture is a two-state "
                f"machine and everything else is illegal — a yes that lapsed is "
                f"a database whose age gate has walked past it."
            )
        return (
            f"mutual · {YOUR_YES_MAKES_IT_MUTUAL.account.slug}'s yes stands "
            f"until {alive[0].expires_at:%Y-%m-%d} and no game has been opened "
            f"on it. The deck card itself was **not read**: this run's deal "
            f"found a deck an earlier one had spent."
        )
    if not a_game_stands:
        row = _card_for(paths, deck, YOUR_YES_MAKES_IT_MUTUAL)
        if row is None or code not in row.liveness_reasons:
            raise ScreenIsEmpty(
                f"'{YOUR_YES_MAKES_IT_MUTUAL.account.slug}' has a live yes to "
                f"{PROTAGONIST.slug}, no game stands between them, and her deal "
                f"of {deck.counts.n_returned} card(s) "
                + (
                    "never dealt them"
                    if row is None
                    else f"drew {sorted(row.liveness_reasons)} on their card"
                )
                + ". *Wants to play you* is that card's whole subject, and this "
                "is the only pair on the fixture whose yes back opens a game "
                "the same instant."
            )
        return (
            f"mutual · {YOUR_YES_MAKES_IT_MUTUAL.account.slug} is on "
            f"{PROTAGONIST.slug}'s deck carrying {code}; saying yes back opens a "
            f"game inline"
        )

    if _was_scored(paths, pool, YOUR_YES_MAKES_IT_MUTUAL):
        raise ScreenIsEmpty(
            f"'{YOUR_YES_MAKES_IT_MUTUAL.account.slug}' has an open game with "
            f"{PROTAGONIST.slug} and is still scored into her padel pool. A "
            f"challenge born of a mutual yes gates the pair off every surface, "
            f"and *gone for good* is what the second state of this fixture "
            f"exists to check."
        )
    return (
        f"mutual · the fixture is spent: a game stands between "
        f"{PROTAGONIST.slug} and {YOUR_YES_MAKES_IT_MUTUAL.account.slug}, and "
        f"they are gone from her pool. Seed a fresh database to run the flow "
        f"again."
    )


async def _refuse_an_outstanding_count_of_nothing(
    paths: ReadPaths, pool: SearchRecord
) -> str:
    """*``you-said-yes-to-them`` is outstanding, and a repeat tap creates nothing.*

    The repeat tap is made **here, for real**, citing the pool the battery just
    ran: a yes is idempotent on the pair, so a second tap returns the first
    unchanged, does not re-date the expiry and does not spend a cap slot. That is
    a property of the use case and this is the only place the fixture can watch
    it happen without a second account to spend.
    """

    her = paths.player(PROTAGONIST.email)
    them = paths.player(YOU_SAID_YES_TO_THEM.account.email)
    summary = await paths.read_interest.execute(ReadInterestCommand(player_id=her))
    standing = [row for row in summary.outgoing if row.to_player_id == them]
    if not standing:
        raise ScreenIsEmpty(
            f"{PROTAGONIST.slug} said *Let's play* to "
            f"'{YOU_SAID_YES_TO_THEM.account.slug}' and her own outgoing list "
            f"does not carry it. That list is the surface the outstanding count "
            f"and the cap are both read against."
        )
    outstanding = [
        count for count in summary.outstanding if count.sport is Sport.PADEL
    ]
    if not outstanding or outstanding[0].outstanding < 1:
        raise ScreenIsEmpty(
            f"{PROTAGONIST.slug}'s padel outstanding count is "
            f"{outstanding[0].outstanding if outstanding else 'absent'} with a "
            f"yes standing. The count is what a cap the player cannot see is "
            f"shown through."
        )

    if _card_for(paths, pool, YOU_SAID_YES_TO_THEM) is None:
        raise ScreenIsEmpty(
            f"'{YOU_SAID_YES_TO_THEM.account.slug}' is not in "
            f"{PROTAGONIST.slug}'s padel pool, so the repeat tap has no search "
            f"to cite. A yes she has already sent gates nobody: an outgoing yes "
            f"holds somebody out of her **deck** and never out of her pool."
        )
    again = await paths.interest.execute(
        ExpressInterestCommand(
            from_player_id=her,
            to_player_id=them,
            sport=Sport.PADEL,
            search_id=pool.id,
        )
    )
    if again.created or again.interest.expires_at != standing[0].expires_at:
        raise ScreenIsEmpty(
            f"a second *Let's play* from {PROTAGONIST.slug} to "
            f"'{YOU_SAID_YES_TO_THEM.account.slug}' answered created="
            f"{again.created} and an expiry of {again.interest.expires_at}, "
            f"where the standing yes expires {standing[0].expires_at}. A repeat "
            f"tap says *nothing changed* rather than *nothing happened*: the yes "
            f"stands with the expiry it was born with, and it spends no cap slot."
        )
    return (
        f"outstanding · {PROTAGONIST.slug} holds "
        f"{outstanding[0].outstanding} of {outstanding[0].cap} padel yes(es), "
        f"and a repeat tap on {YOU_SAID_YES_TO_THEM.account.slug} answered "
        f"created={again.created}"
    )


def _refuse_a_refusal_no_card_carries(
    paths: ReadPaths, pool: SearchRecord
) -> str:
    """*``they-turned-down-your-court`` is in the pool, carrying the refusal.*

    A declined seat reopens and that person returns to the deck immediately, so
    this is the one pairwise answer a card in **this cohort** carries — the
    accept's counterpart is still arranging a game and is gated on that, and the
    code is narrowed out by name in ``CANNOT_BE_DRAWN`` for a reason that is now
    about these fixtures rather than about the platform (`docs/adr/0142` §1).
    ``PREVIOUS_DECLINE`` is a **silent** signal, so the claim
    is read off the row's recorded raw input rather than off a reason line: what
    is asserted is that the matcher saw the refusal, which is what a silent
    signal owes anybody.
    """

    row = _card_for(paths, pool, THEY_TURNED_DOWN_YOUR_COURT)
    code = "PREVIOUS_DECLINE"
    if row is None:
        raise ScreenIsEmpty(
            f"'{THEY_TURNED_DOWN_YOUR_COURT.account.slug}' declined "
            f"{PROTAGONIST.slug}'s court and is not in her padel pool. A "
            f"declined seat reopens and ends a court nobody else was in, so the "
            f"pair is released the same instant — an absence here is the pair "
            f"rule refusing to let go."
        )
    if not row.liveness_signals.get(code):
        raise ScreenIsEmpty(
            f"'{THEY_TURNED_DOWN_YOUR_COURT.account.slug}' is in "
            f"{PROTAGONIST.slug}'s padel pool and their row records "
            f"{code}={row.liveness_signals.get(code)!r}. "
            f"The refusal is on the pair and the matcher reads it off "
            f"`pairwise_counterparts`, so a false here is the one outward demand "
            f"`challenges` signs having stopped answering."
        )
    return (
        f"decline · {THEY_TURNED_DOWN_YOUR_COURT.account.slug} is back in "
        f"{PROTAGONIST.slug}'s padel pool with {code} recorded on the row"
    )


def _refuse_an_absence_with_no_gate_behind_it(
    paths: ReadPaths, pool: SearchRecord, deck: SearchRecord, line_up: SearchRecord
) -> str:
    """*The absent are absent from every surface, for the reason they are named for.*

    **The claim is the gate histogram, not the absence**, and the refinement is
    load-bearing: an account gated for an accidental reason is absent, and a
    naive absence claim passes. The histogram is counted first-in-declaration
    order — ``BLOCKED`` first, ``NOT_RATED`` third, ``OPEN_CHALLENGE`` fifth — so
    a count against a code names the reason exactly, and it cannot be non-zero
    unless a rated, in-range, gender-satisfied candidate was excluded for it.

    **Three surfaces are read and the fourth is the third one over.** A block is
    recorded against one of four — shortlist, deck, line-up, filling seats — and
    every one of those has to be empty of these accounts; the records for the
    first three are the ones this run has already produced, and *filling seats*
    is the line-up use case one locked argument apart, sharing its gates by
    construction (``SearchRecord.is_a_line_up`` covers both). The histogram is
    asserted on the pool alone because that is the search the counts are named
    against, and the other two are read for the absence itself.
    """

    surfaces = (("pool", pool), ("deck", deck), ("line-up", line_up))
    reported: list[str] = []
    for code, named in (
        (GateCode.OPEN_CHALLENGE, ABSENT_ON_THE_OPEN_CHALLENGE_GATE),
        (GateCode.BLOCKED, ABSENT_ON_THE_BLOCKED_GATE),
    ):
        for surface, record in surfaces:
            present = sorted(
                relationship.account.slug
                for relationship in named
                if _was_scored(paths, record, relationship)
            )
            if present:
                raise ScreenIsEmpty(
                    f"{present} should be absent from {PROTAGONIST.slug}'s padel "
                    f"{surface} on the {code.value} gate and was scored into it."
                )
        counted = pool.counts.excluded_by_gate.get(code.value, 0)
        if counted < len(named):
            raise ScreenIsEmpty(
                f"{len(named)} account(s) are named for the {code.value} gate "
                f"and it excluded {counted} candidate(s) from "
                f"{PROTAGONIST.slug}'s padel pool. An absence is not the claim: "
                f"an account gated for an accidental reason — no rating, out of "
                f"range, the wrong gender preference — is absent too, and the "
                f"histogram is the only thing that tells the two apart. "
                f"Gates: {dict(sorted(pool.counts.excluded_by_gate.items()))}."
            )
        reported.append(f"{code.value} {counted}")
    return (
        "absences · "
        + ", ".join(reported)
        + " on the pool's gate histogram, and nobody named is scored into her "
        "pool, her deck or her line-up"
    )


async def _refuse_a_block_only_one_side_can_see(paths: ReadPaths) -> str:
    """*``they-blocked-you`` cannot see her either.*

    The only fixture for a **symmetric effect read off a directed record**, and
    it is unobservable from her side by construction — indistinguishable from
    somebody simply out of range. So it is checked by reading a screen as
    *them*, which is the concrete form of why these are accounts and not rows in
    an edge table.
    """

    record = await run_a_shortlist(
        paths, THEY_BLOCKED_YOU.account.email, Sport.PADEL, SearchMode.COMPETITIVE
    )
    her = paths.player(PROTAGONIST.email)
    if any(row.player_id == her for row in record.candidates):
        raise ScreenIsEmpty(
            f"'{THEY_BLOCKED_YOU.account.slug}' blocked {PROTAGONIST.slug} and "
            f"her row is in their own padel pool. ADR-0095's effect is "
            f"symmetric from a record that is not."
        )
    counted = record.counts.excluded_by_gate.get(GateCode.BLOCKED.value, 0)
    if counted < 1:
        raise ScreenIsEmpty(
            f"'{THEY_BLOCKED_YOU.account.slug}' blocked {PROTAGONIST.slug} and "
            f"their own search excluded nobody on the {GateCode.BLOCKED.value} "
            f"gate. She is absent from it, which on its own is what being out of "
            f"range looks like. "
            f"Gates: {dict(sorted(record.counts.excluded_by_gate.items()))}."
        )
    return (
        f"block · {THEY_BLOCKED_YOU.account.slug}'s own padel pool excluded "
        f"{counted} on {GateCode.BLOCKED.value}, and {PROTAGONIST.slug} is not "
        f"in it"
    )


async def _refuse_a_seat_that_is_not_hers_to_answer(paths: ReadPaths) -> str:
    """*The inbound court is hers to answer, and both co-invitees are on it.*

    The one screen a doubles send exists for: a seat with a side, a window
    counting down, and a line-up that is hers. The two co-invitees differ by seat
    state on purpose, so the court draws a filled seat and an unanswered one side
    by side — and only a fixture can prove that two screens differ.
    """

    her = paths.player(PROTAGONIST.email)
    organiser = paths.player(THEY_CHALLENGED_YOU.account.email)
    _, standing = await paths.read_challenges.execute(
        ReadChallengesCommand(reader_id=her)
    )
    courts = [
        row
        for row in standing
        if row.challenge.organiser_id == organiser and row.standing not in ENDED
    ]
    if not courts:
        raise ScreenIsEmpty(
            f"'{THEY_CHALLENGED_YOU.account.slug}' sent {PROTAGONIST.slug} a "
            f"court and her own list carries no open one from them, across "
            f"{len(standing)} challenge(s). A seat's window is "
            f"{ANSWER_WINDOW_HOURS} hours and nothing here backdates one, so "
            f"a court seeded longer ago than that has lapsed — seed again."
        )
    court = courts[0].challenge
    hers = court.seat_of(her)
    if hers is None or not hers.is_awaiting():
        raise ScreenIsEmpty(
            f"{PROTAGONIST.slug}'s seat on challenge {court.id} reads "
            f"{hers and hers.answer}. The claim is a seat that is **hers to "
            f"answer**, with its own day running."
        )
    seats = {
        relationship.account.slug: court.seat_of(
            paths.player(relationship.account.email)
        )
        for relationship in (
            IN_YOUR_LINE_UP_AND_ACCEPTED,
            IN_YOUR_LINE_UP_STILL_DECIDING,
        )
    }
    filled = seats[IN_YOUR_LINE_UP_AND_ACCEPTED.account.slug]
    deciding = seats[IN_YOUR_LINE_UP_STILL_DECIDING.account.slug]
    if filled is None or filled.answer is not SeatAnswer.ACCEPTED:
        raise ScreenIsEmpty(
            f"'{IN_YOUR_LINE_UP_AND_ACCEPTED.account.slug}' holds "
            f"{filled and filled.answer} on challenge {court.id} and is named "
            f"for a filled seat."
        )
    if deciding is None or not deciding.is_awaiting():
        raise ScreenIsEmpty(
            f"'{IN_YOUR_LINE_UP_STILL_DECIDING.account.slug}' holds "
            f"{deciding and deciding.answer} on challenge {court.id} and is "
            f"named for a seat nobody has answered. The two exist to differ."
        )
    return (
        f"court · challenge {court.id} from "
        f"{THEY_CHALLENGED_YOU.account.slug} reads {courts[0].standing.value}: "
        f"{PROTAGONIST.slug} on side {hers.side.value} answering by "
        f"{hers.answer_by:%Y-%m-%d %H:%M}, one seat accepted and one still out"
    )


async def _refuse_a_challenge_screen_with_nobody_on_it(paths: ReadPaths) -> str:
    """*The court she is answering names who is asking, and prices playing them.*

    The one screen in this fixture whose card is **recomputed rather than
    replayed** (``docs/adr/0143``). Every other card here was recorded by the
    search that dealt it; this one is scored when the screen opens, in **her**
    direction, against somebody whose search she cannot read — which is the whole
    reason the port exists and the one thing no other assertion in this file
    touches.

    **What is asserted is a drawn card and not a shape.** A pairing block is
    allowed to be absent for two named reasons, and both of them are the fixture
    failing rather than the product working: the protagonist is rated and has
    declared for this sport, and the run has just ticked the index it is about to
    read. So an absence here is reported as the refusal it is, with the code that
    says whose gap it would have been.

    **The two absences are not fixtures, and that is written down rather than
    left as a gap.** *Nothing to compute* needs a reader with no rating in the
    sport they were challenged in, and a challenge only reaches somebody through
    a search or a mutual yes — both of which need that rating on both sides — so
    there is no way to seat one through the real routes. *Could not be read*
    needs the matcher broken, which is a dependency override rather than a state
    a database can hold. Both are contracted in ``tests/api/`` instead, where an
    override is the right instrument.
    """

    her = paths.player(PROTAGONIST.email)
    organiser = paths.player(THEY_CHALLENGED_YOU.account.email)
    _, standing = await paths.read_challenges.execute(
        ReadChallengesCommand(reader_id=her)
    )
    courts = [
        row
        for row in standing
        if row.challenge.organiser_id == organiser and row.standing not in ENDED
    ]
    if not courts:
        raise ScreenIsEmpty(
            f"'{THEY_CHALLENGED_YOU.account.slug}' sent {PROTAGONIST.slug} no "
            f"court that still stands, so there is no challenge screen to draw "
            f"a card on. The seat assertion above says why."
        )
    detail = await paths.read_challenge.execute(
        ReadChallengeCommand(challenge_id=courts[0].challenge.id, reader_id=her)
    )
    absent = None if detail.court is None else detail.court.absent
    if detail.court is None or absent is not None:
        why = "the standing draws none" if absent is None else absent.value
        raise ScreenIsEmpty(
            f"{PROTAGONIST.slug}'s challenge screen draws no card block: {why}. "
            f"She is rated and declared for {courts[0].challenge.sport.value} and "
            f"this run ticked the index before reading, so both absences are "
            f"this fixture failing rather than the product working."
        )
    card = detail.card_for(organiser)
    if card is None:
        raise ScreenIsEmpty(
            f"the card block came back with nobody in it: "
            f"'{THEY_CHALLENGED_YOU.account.slug}' organises the court "
            f"{PROTAGONIST.slug} holds a seat on, and a screen that priced "
            f"everybody except the person asking is the one card it owes her."
        )
    return (
        f"court · {PROTAGONIST.slug} reads "
        f"{THEY_CHALLENGED_YOU.account.slug}'s card on challenge "
        f"{courts[0].challenge.id}: {card.person.nickname}, level "
        f"{card.person.level:.2f} in band {card.person.band}, Fit "
        f"{card.pairing.fit:.0f} over {len(card.pairing.terms)} term(s) with "
        f"{len(card.pairing.degraded_terms)} stood down, forecast "
        + (
            "absent — no game can be arranged out of what is left of this court"
            if card.pairing.forecast is None
            else f"{card.pairing.forecast.pct}%"
        )
    )


async def _refuse_a_pass_the_deck_still_deals(
    paths: ReadPaths, pool: SearchRecord, *, pairs: SeededPairs
) -> str:
    """*``you-passed-them`` is gone from the deck and a full candidate in the pool.*

    A two-surface asymmetry that reads as a bug to anybody meeting it cold: a
    pass is *a statement about my deck* and never about the person, so ADR-0128
    keeps the suppression off the search entirely.

    **This deal is a fresh one and it has to be**, because the deal that earned
    the pass's origin key was dealt before the pass existed. It also costs: every
    card of that first deal is spent for a day, so what this one asserts about
    the gate is ``n_excluded_by_suppression`` — people in range under a **live**
    pass, counted whether or not the deal had already spent them.

    **And the gate half is asserted only where the cache answers.** The
    suppression ledger fails soft, so an unreachable Redis says *nobody* and a
    lapsed window says *nobody*; the run probes the store when it writes the
    suppression, and where the probe came back empty this reports the cache
    rather than accusing the fixture — which is the failure a named catalog
    exists to avoid. The pool half is asserted either way, because it is a fact
    about a durable row.
    """

    them = paths.player(YOU_PASSED_THEM.account.email)
    if _card_for(paths, pool, YOU_PASSED_THEM) is None:
        raise ScreenIsEmpty(
            f"'{YOU_PASSED_THEM.account.slug}' was passed on and is missing from "
            f"{PROTAGONIST.slug}'s padel pool. A pass is a statement about her "
            f"deck and about nothing else: *pass on somebody tonight, find them "
            f"third in your shortlist tomorrow* is the named cost, and a "
            f"suppression that reached the search would have taken it back."
        )
    if not pairs.the_suppression_reads_back:
        return (
            f"pass · {YOU_PASSED_THEM.account.slug} is a candidate in "
            f"{PROTAGONIST.slug}'s pool, and the deck half was **not read**: the "
            f"suppression this run wrote does not read back, so the store is "
            f"unreachable. That is the cache and not the fixture — bring Redis "
            f"up and seed again."
        )

    answer = await deal_a_deck(paths, PROTAGONIST.email, Sport.PADEL)
    record = answer.record
    if them in returned_ids(record):
        raise ScreenIsEmpty(
            f"{PROTAGONIST.slug} passed on '{YOU_PASSED_THEM.account.slug}', the "
            f"suppression reads back, and her next deal dealt them anyway. The "
            f"gate is that cache and the row that proves the pass never expires, "
            f"so the deck is no longer reading the one from the other."
        )
    if (record.n_excluded_by_suppression or 0) < 1:
        raise ScreenIsEmpty(
            f"{PROTAGONIST.slug}'s deal found nobody in range under a live "
            f"suppression, over a pool of {record.counts.n_generated}, though "
            f"the store answers for '{YOU_PASSED_THEM.account.slug}'. They are "
            f"absent from the deal either way — a card already dealt today is "
            f"held out too — so without this count the claim would be proved by "
            f"the wrong exclusion."
        )
    return (
        f"pass · {YOU_PASSED_THEM.account.slug} is gone from "
        f"{PROTAGONIST.slug}'s deck ({record.n_excluded_by_suppression} in range "
        f"under a live suppression) and still a candidate in her pool"
    )
