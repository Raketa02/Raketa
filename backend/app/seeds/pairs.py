"""Write the eleven relationships, each edge through the use case that owns it.

**Every edge costs a real search or deal run as the sender, and the cost is the
check.** ``Interest`` and ``Pass`` have no non-search constructor, and a send
cites the search its court was built on; ``resolve_origin`` and
``court_origin`` both refuse a citation the record does not bear out. So *they
said yes to you* means signing in as them, running a real search, and the
protagonist actually being in it — which proves she was findable through gender,
level and radius before any lift is claimed. A fixture that wrote the row would
prove that the row can be written.

**Nothing here opens a table and nothing here builds an aggregate of its own.**
Every write is a use case assembled in ``app/seeds/paths.py`` from the
composition root, exactly as ``runner.py``'s registrations and questionnaires
are. What this module adds to the seed path is two contexts — ``challenges`` and
``blocks`` — and it adds them as *writes through their own use cases*, which is
the distinction ``test_the_seed_path_writes_and_only_reads_the_rest`` draws.

**Re-running writes nothing twice, and each probe is the cheapest question that
tells the two states apart.** A yes is idempotent in its own use case, and a
block is; a send is not, because two challenges between the same people are two
challenges — so the send is preceded by a read of what already stands. The probe
comes **before the search**, deliberately: in the state where the edge already
exists the sender can no longer see the protagonist at all (an open challenge
gates the pair), so a run that searched first would fail on its second pass with
a message about a pool.

**A seat's window is twenty-four hours and nothing here backdates it.** A
database seeded yesterday has courts that have lapsed, and that is the right
answer rather than a defect: the pair is released the moment the last seat goes,
so the next ``make seed`` finds nothing standing and sends again. The alternative
— backdating so a court looks fresh — is a fixture for a state no organiser ever
had.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import build_candidate_source
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import ChallengeLoadRung
from app.infrastructure.redis_client import create_redis_client
from app.kernel import Instant, Sport, exhaustive
from app.modules.blocks.application.commands import BlockPlayerCommand
from app.modules.blocks.domain.surface import BlockSurface
from app.modules.challenges.application.commands import (
    AnswerSeatCommand,
    SeatChoice,
    SendChallengeCommand,
)
from app.modules.challenges.application.read_challenges import ReadChallengesCommand
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.seats import SeatAnswer, court_sides
from app.modules.challenges.domain.standing import ENDED
from app.modules.matchmaking.application.commands import (
    ExpressInterestCommand,
    ReadInterestCommand,
    RecordPassCommand,
)
from app.modules.matchmaking.domain.deck import mode_for_intent
from app.modules.matchmaking.domain.ports import PairwiseOutcome
from app.modules.matchmaking.domain.searches import SearchRecord
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.seeds.cohort import COHORT, Cohort, CohortMember
from app.seeds.paths import (
    ReadPaths,
    deal_a_deck,
    read_paths,
    returned_ids,
    run_a_shortlist,
    tick_the_tail_to_catch_up,
)
from app.seeds.relationships import (
    PROTAGONIST,
    RELATIONSHIPS,
    OnTheirCourt,
    Relationship,
    TheyBlockedYou,
    TheyChallengedYou,
    TheySaidYes,
    TheyTurnedYouDown,
    YouBlockedThem,
    YouChallengedThem,
    YouPassedThem,
    YouSaidYes,
    members_who_carry_an_inbox,
    members_who_might_organise,
)

def _mode_declared_by(
    paths: ReadPaths, intents: Sequence[tuple[Sport, PlayIntent]], sport: Sport
) -> SearchMode:
    """Which weight vector this searcher's own declaration puts them under.

    **Derived and never tabled.** A map from sport to mode would be right only
    while every account on this fixture declared the same thing: the protagonist
    declares padel *competitive* and tennis *for fun*, a relationship account
    declares competitive throughout, and a cohort member takes whatever the
    intent cycle gave them. So the mode is read off the searcher's declaration
    through ``mode_for_intent`` — the deck's own rule, so a fixture and a deal
    cannot come to two answers about what ``NO_PREFERENCE`` inherits.

    A sport the searcher never declared is refused **by name**: it is a search
    the platform would have nothing to score, and a `KeyError` here would name a
    dictionary rather than an account.
    """

    for declared, intent in intents:
        if declared is sport:
            return mode_for_intent(intent, paths.ruleset.intent)
    raise EdgeRefused(
        f"a {sport.value} search was asked for and the searcher declares "
        f"{[one.value for one, _ in intents]}. Play intent is declared per sport "
        f"(ADR-0094), so there is no mode to run this under."
    )


def _her_intents() -> Sequence[tuple[Sport, PlayIntent]]:
    """The protagonist's own declarations. She always has a profile."""

    if PROTAGONIST.profile is None:  # pragma: no cover - the catalog refuses it
        raise EdgeRefused(f"'{PROTAGONIST.slug}' declares no Play intent at all")
    return PROTAGONIST.profile.intents


def _their_intents(relationship: Relationship) -> Sequence[tuple[Sport, PlayIntent]]:
    """One relationship account's own declarations."""

    profile = relationship.account.profile
    if profile is None:  # pragma: no cover - the layer refuses it at import
        raise EdgeRefused(
            f"'{relationship.account.slug}' declares no Play intent at all"
        )
    return profile.intents

#: Where a seeded block says it was made from. The field has no default and
#: nothing branches on it, so the shortlist is named because that is the surface
#: the protagonist's own claims are read on.
BLOCKED_FROM = BlockSurface.SHORTLIST


class EdgeRefused(RuntimeError):
    """An edge the run could not write, with the reason the platform gave.

    A ``RuntimeError`` for ``SeedFailed``'s reason. It is raised rather than
    warned because a relationship that silently failed to exist is a screen
    developed against a state nobody produced — and every claim downstream of it
    would then fail somewhere else, naming a pool rather than an edge.
    """


@final
@dataclass(frozen=True, slots=True)
class WrittenEdge:
    """One relationship after the run, and the line the report prints for it."""

    relationship: Relationship
    line: str


@final
@dataclass(frozen=True, slots=True)
class ThePassAndWhatItCost:
    """Everything the one pass on this fixture left behind.

    One value rather than five returned side by side, because the four facts are
    one story — the deal that earned the origin key, whether it found a deck an
    earlier run had spent, whether the suppression reads back, and what the
    report owes a reader about both.
    """

    deal: SearchRecord
    deck_was_already_spent: bool
    suppression_reads_back: bool
    line: str
    costs: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class SeededPairs:
    """Everything the relationship layer wrote, and what it cost.

    ``the_deal_that_earned_the_pass`` is the record of the one deal this run
    ran as the protagonist. It is carried rather than re-dealt because
    ``DEALT_MEMORY`` is a day: a second deal would find every card of the first
    already spent, so the deck's own claims are read off **this** record — the
    same read path, executed a moment earlier.
    """

    edges: tuple[WrittenEdge, ...]
    inboxes: tuple[str, ...]
    costs: tuple[str, ...]
    the_deal_that_earned_the_pass: SearchRecord
    #: Whether that deal found a deck this run had **already spent**. ADR-0131
    #: remembers a deal for a day, so a second `make seed` inside one deals the
    #: remainder — the deck's own claims are then unreadable, and the report says
    #: so rather than the run going red. A target that fails as a consequence of
    #: using the thing it seeds trains people to ignore it.
    the_deck_was_already_spent: bool
    #: Whether the suppression the pass wrote **reads back**. It is a probe on
    #: the store and never the claim: the claim is that a deck does not deal a
    #: passed card. The two are kept apart because the ledger fails soft, so
    #: *unreachable* and *nothing is suppressed* are one answer — and a fixture
    #: that could not tell them apart would complain that it had rotted when the
    #: truth is that somebody flushed Redis.
    the_suppression_reads_back: bool


async def write_the_relationships(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Cohort = COHORT,
) -> SeededPairs:
    """Write every edge, in declaration order, and report what each one cost.

    **The tail is ticked first**, because the searches these edges are built on
    read the candidate index and the index has not seen what the run just wrote.
    ADR-0110 makes the tick safe and cheap to repeat, which is what lets it be a
    barrier here as well as before the assertions.
    """

    await tick_the_tail_to_catch_up(session_factory, settings=settings)
    candidates = build_candidate_source(session_factory=session_factory)
    await candidates.refresh()

    # This run opens the ephemeral store and this run closes it, for the reason
    # `screens.py` states: under the API the pool belongs to the process and the
    # lifespan owns both ends, and a command has no lifespan.
    redis = create_redis_client(settings)
    try:
        async with session_factory() as session:
            paths = await read_paths(
                session,
                settings=settings,
                candidates=candidates,
                cohort=cohort,
                now=now,
                redis=redis,
            )
            return await _write(paths, cohort=cohort)
    finally:
        # `type: ignore` for the reason `screens.py` gives: the obsolete
        # `types-redis` stubs shadow redis-py's own inline types and predate
        # `aclose`, which is the spelling `close` was deprecated in favour of.
        await redis.aclose()  # type: ignore[attr-defined]


async def _write(paths: ReadPaths, *, cohort: Cohort) -> SeededPairs:
    """The eleven, then the inboxes the cohort carries."""

    written: list[WrittenEdge] = []
    court: Challenge | None = None
    deal: SearchRecord | None = None
    costs: list[str] = []
    cached = False
    spent = False

    for relationship in RELATIONSHIPS:
        edge = relationship.edge
        match edge:
            case TheySaidYes():
                line = await _they_said_yes(paths, relationship, edge)
            case YouSaidYes():
                line = await _you_said_yes(paths, relationship, edge)
            case YouChallengedThem():
                line = await _you_challenged_them(paths, relationship, edge)
            case TheyChallengedYou():
                court, line = await _they_challenged_you(paths, relationship, edge)
            case OnTheirCourt():
                line = await _answer_a_seat(paths, relationship, edge, court)
            case TheyTurnedYouDown():
                line = await _they_turned_you_down(paths, relationship, edge)
            case YouBlockedThem():
                line = await _blocked(paths, relationship, blocked_by_her=True)
            case TheyBlockedYou():
                line = await _blocked(paths, relationship, blocked_by_her=False)
            case YouPassedThem():
                passed = await _you_passed_them(paths, relationship, edge)
                deal, line = passed.deal, passed.line
                cached = passed.suppression_reads_back
                spent = passed.deck_was_already_spent
                costs.extend(passed.costs)
            case _:
                exhaustive(edge)
        written.append(WrittenEdge(relationship=relationship, line=line))

    if deal is None:  # pragma: no cover - the union above guarantees it
        raise EdgeRefused(
            "no deal was run, so the pass has no origin and the deck has no "
            "record to read its own claims off."
        )
    inboxes = await _fill_the_inboxes(paths, cohort=cohort)
    return SeededPairs(
        edges=tuple(written),
        inboxes=inboxes,
        costs=tuple(costs),
        the_deal_that_earned_the_pass=deal,
        the_deck_was_already_spent=spent,
        the_suppression_reads_back=cached,
    )


# ---------------------------------------------------------------------------
# The two yeses
# ---------------------------------------------------------------------------


async def _they_said_yes(
    paths: ReadPaths, relationship: Relationship, edge: TheySaidYes
) -> str:
    """They run their own pool search and say *Let's play* to the protagonist.

    The ledger is read **first** and as themselves, which is the only direction
    a yes may be looked at. It is also the only probe that works in the state
    this fixture is allowed to reach: once a yes has been answered the pair have
    an open game, the protagonist is gated out of this account's own pool, and a
    run that searched first would refuse the edge it had already written.
    """

    sender = relationship.account
    target = paths.player(PROTAGONIST.email)
    standing = await _yes_from(paths, sender.email, target, edge.sport)
    if standing is not None:
        return f"{sender.slug} · {standing}"

    record = await _a_search_that_showed(
        paths,
        searcher=sender.email,
        named=sender.slug,
        intents=_their_intents(relationship),
        sport=edge.sport,
        wanted={PROTAGONIST.slug: target},
    )
    answer = await paths.interest.execute(
        ExpressInterestCommand(
            from_player_id=paths.player(sender.email),
            to_player_id=target,
            sport=edge.sport,
            search_id=record.id,
        )
    )
    return (
        f"{sender.slug} · said *Let's play* to {PROTAGONIST.slug}, citing search "
        f"{record.id} (position {answer.interest.origin.position}), "
        f"{'created' if answer.created else 'already standing'}"
    )


async def _you_said_yes(
    paths: ReadPaths, relationship: Relationship, edge: YouSaidYes
) -> str:
    """The protagonist says *Let's play*, off her own pool search.

    The mirror of the one above and deliberately not folded into it: the two
    differ in whose ledger is probed, whose search earns the origin and what the
    line is worth saying — a direction flag would make one function that reads
    as neither.
    """

    target = paths.player(relationship.account.email)
    standing = await _yes_from(paths, PROTAGONIST.email, target, edge.sport)
    if standing is not None:
        return f"{relationship.account.slug} · {standing}"

    record = await _a_search_that_showed(
        paths,
        searcher=PROTAGONIST.email,
        named=PROTAGONIST.slug,
        intents=_her_intents(),
        sport=edge.sport,
        wanted={relationship.account.slug: target},
    )
    answer = await paths.interest.execute(
        ExpressInterestCommand(
            from_player_id=paths.player(PROTAGONIST.email),
            to_player_id=target,
            sport=edge.sport,
            search_id=record.id,
        )
    )
    count = answer.outstanding
    return (
        f"{relationship.account.slug} · {PROTAGONIST.slug} said *Let's play*, "
        f"citing search {record.id}, "
        f"{'created' if answer.created else 'unchanged'} · "
        f"{count.sport.value} outstanding {count.outstanding} of {count.cap}"
    )


async def _yes_from(
    paths: ReadPaths, sender_email: str, target: UUID, sport: Sport
) -> str | None:
    """Whether this pair already has a yes this run need not write again.

    Read as **the sender**, through the one read of the interest ledger a player
    is allowed to make: their own. A mutual yes has moved out of ``outgoing`` and
    into ``mutual``, and both count — the edge exists either way, and which of
    the two states it is in is a claim rather than a probe.
    """

    summary = await paths.read_interest.execute(
        ReadInterestCommand(player_id=paths.player(sender_email))
    )
    for row in summary.outgoing:
        if row.to_player_id == target and row.sport is sport:
            return f"the yes already stands, expiring {row.expires_at:%Y-%m-%d}"
    for row in summary.mutual:
        if row.to_player_id == target and row.sport is sport:
            return "the yes was answered and a game already stands on it"
    return None


# ---------------------------------------------------------------------------
# The three courts
# ---------------------------------------------------------------------------


async def _you_challenged_them(
    paths: ReadPaths, relationship: Relationship, edge: YouChallengedThem
) -> str:
    """The protagonist sends a **singles** court, on the sport nothing else uses.

    Tennis, and it is the only account whose sport is doing work: it makes *one
    open challenge per pair, across sports* observable — this person is gated out
    of her **padel** pool by a **tennis** challenge, which is the rule's entire
    content.
    """

    them = paths.player(relationship.account.email)
    if await _an_open_challenge_stands(paths, PROTAGONIST.email, them):
        return (
            f"{relationship.account.slug} · an open {edge.sport.value} challenge "
            f"already stands with {PROTAGONIST.slug}"
        )

    record = await _a_search_that_showed(
        paths,
        searcher=PROTAGONIST.email,
        named=PROTAGONIST.slug,
        intents=_her_intents(),
        sport=edge.sport,
        wanted={relationship.account.slug: them},
    )
    challenge_id = await _send(
        paths,
        organiser=PROTAGONIST.email,
        sport=edge.sport,
        record=record,
        invitees=(relationship.account.email,),
    )
    return (
        f"{relationship.account.slug} · {PROTAGONIST.slug} sent a "
        f"{edge.sport.value} singles court, challenge {challenge_id}, "
        f"citing search {record.id}"
    )


async def _they_challenged_you(
    paths: ReadPaths, relationship: Relationship, edge: TheyChallengedYou
) -> tuple[Challenge, str]:
    """They organise a **doubles** court the protagonist holds a seat on.

    The court seats four and the two co-invitees are **named accounts**, which is
    what makes two people disappearing from every surface a declaration rather
    than a discovery. Their answers are three separate acts, so the court is
    returned for the seats that follow it to be answered against.
    """

    organiser = relationship.account.email
    # **The organiser's own side is filled first, and she sits across the net.**
    # The court is `A A B B` with the organiser on the first seat, so seating the
    # person being challenged next to them would put a challenge and the person
    # it was sent to on one side — legal, and not what anybody drew.
    partner, *across = _co_invitee_addresses(edge)
    seated = [partner, PROTAGONIST.email, *across]
    standing = await _the_court_they_sent(paths, organiser)
    if standing is not None:
        return standing, (
            f"{relationship.account.slug} · a {edge.sport.value} court already "
            f"stands, challenge {standing.id}"
        )

    record = await _a_search_that_showed(
        paths,
        searcher=organiser,
        named=relationship.account.slug,
        intents=_their_intents(relationship),
        sport=edge.sport,
        wanted={address: paths.player(address) for address in seated},
    )
    challenge_id = await _send(
        paths,
        organiser=organiser,
        sport=edge.sport,
        record=record,
        invitees=tuple(seated),
    )
    court = await _the_court_they_sent(paths, organiser)
    if court is None or court.id != challenge_id:
        raise EdgeRefused(
            f"'{relationship.account.slug}' sent challenge {challenge_id} and "
            f"{PROTAGONIST.slug}'s own list does not carry it back. The court "
            f"screen reads that list."
        )
    return court, (
        f"{relationship.account.slug} · sent {PROTAGONIST.slug} a "
        f"{edge.sport.value} doubles court, challenge {challenge_id}, citing "
        f"search {record.id}"
    )


async def _answer_a_seat(
    paths: ReadPaths,
    relationship: Relationship,
    edge: OnTheirCourt,
    court: Challenge | None,
) -> str:
    """One co-invitee answers their seat, or deliberately does not.

    ``None`` is *awaiting*, and it is written by doing nothing at all: the seat
    was invited by the send, its own day is running, and an absence of an answer
    is the state rather than a fourth value somebody records.
    """

    if court is None:
        raise EdgeRefused(
            f"'{relationship.account.slug}' declares a seat and no court has "
            f"been sent. The order in `RELATIONSHIPS` is load-bearing: a "
            f"co-invitee cannot answer a seat before the send that made it."
        )
    them = paths.player(relationship.account.email)
    seat = court.seat_of(them)
    if seat is None:
        raise EdgeRefused(
            f"'{relationship.account.slug}' holds no seat on challenge "
            f"{court.id}, though the court was sent naming them."
        )
    if edge.answer is None:
        return (
            f"{relationship.account.slug} · seat on side {seat.side.value} left "
            f"unanswered, answer_by {seat.answer_by:%Y-%m-%d %H:%M}"
        )
    if seat.answer is edge.answer:
        return (
            f"{relationship.account.slug} · seat on side {seat.side.value} "
            f"already {seat.answer.value.lower()}"
        )
    if edge.answer is not SeatAnswer.ACCEPTED:
        raise EdgeRefused(
            f"'{relationship.account.slug}' declares a seat answered "
            f"{edge.answer.value}, and the only answer this court asks for is an "
            f"acceptance — a decline here would take the last invitee out and "
            f"end the challenge the other claims are read off."
        )
    answered = await paths.accept.execute(
        AnswerSeatCommand(challenge_id=court.id, player_id=them)
    )
    return (
        f"{relationship.account.slug} · accepted their seat on side "
        f"{seat.side.value}; the court now reads {answered.standing.value}"
    )


async def _they_turned_you_down(
    paths: ReadPaths, relationship: Relationship, edge: TheyTurnedYouDown
) -> str:
    """The protagonist sends a half-built court and they decline it.

    **The challenge ends with the seat**, because nobody but the organiser is
    left in it — which is what puts this person back in her pool the same instant
    carrying a recorded refusal. It is the only shape a drawable
    ``PREVIOUS_DECLINE`` can take: every other declined seat on this fixture
    belongs to a court that still stands, and a standing court gates the pair.
    """

    them = paths.player(relationship.account.email)
    if await _has_already_declined(paths, them):
        return (
            f"{relationship.account.slug} · the refusal is already recorded "
            f"against {PROTAGONIST.slug}"
        )
    if await _an_open_challenge_stands(paths, PROTAGONIST.email, them):
        raise EdgeRefused(
            f"'{relationship.account.slug}' has an open challenge with "
            f"{PROTAGONIST.slug} and no recorded refusal. The court this account "
            f"exists for is sent and declined in one run, so a standing one is a "
            f"run that stopped half way — drop the database and seed again."
        )

    record = await _a_search_that_showed(
        paths,
        searcher=PROTAGONIST.email,
        named=PROTAGONIST.slug,
        intents=_her_intents(),
        sport=edge.sport,
        wanted={relationship.account.slug: them},
    )
    challenge_id = await _send(
        paths,
        organiser=PROTAGONIST.email,
        sport=edge.sport,
        record=record,
        invitees=(relationship.account.email,),
    )
    answered = await paths.decline.execute(
        AnswerSeatCommand(challenge_id=challenge_id, player_id=them)
    )
    return (
        f"{relationship.account.slug} · declined {PROTAGONIST.slug}'s "
        f"{edge.sport.value} court {challenge_id}; it now reads "
        f"{answered.standing.value} and the pair is released"
    )


def _co_invitee_addresses(edge: TheyChallengedYou) -> tuple[str, ...]:
    """The co-invitees' addresses, derived from their slugs the way every
    address in this system is — so a court cannot name one account and seat
    another."""

    return tuple(
        relationship.account.email
        for relationship in RELATIONSHIPS
        if relationship.account.slug in edge.co_invitees
    )


async def _send(
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
    """

    sides = court_sides(sport)
    occupants: list[UUID | None] = [
        paths.player(organiser),
        *[paths.player(address) for address in invitees],
    ]
    if len(occupants) > len(sides):
        raise EdgeRefused(
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


async def _an_open_challenge_stands(
    paths: ReadPaths, searcher_email: str, other: UUID
) -> bool:
    """Whether these two already have a game standing, in **any** sport."""

    open_ones = await paths.history.open_challenges(paths.player(searcher_email))
    return any(row.counterpart_id == other for row in open_ones)


async def _the_court_they_sent(paths: ReadPaths, organiser: str) -> Challenge | None:
    """The open challenge that organiser has with the protagonist, read as her.

    Read through the protagonist's **own** list rather than by id, because that
    is the read the court screen makes and a fixture that found its court any
    other way would not have proved the screen can.
    """

    organiser_id = paths.player(organiser)
    reader = paths.player(PROTAGONIST.email)
    standing = await paths.read_challenges.execute(
        ReadChallengesCommand(reader_id=reader)
    )
    for row in standing:
        if row.challenge.organiser_id == organiser_id and row.standing not in ENDED:
            return row.challenge
    return None


async def _has_already_declined(paths: ReadPaths, them: UUID) -> bool:
    """Whether this person has a refusal recorded against the protagonist.

    Read off the same pairwise history the signal is priced from, so the probe
    and the claim cannot disagree about what a decline is.
    """

    counterparts = await paths.history.pairwise_counterparts(
        paths.player(PROTAGONIST.email)
    )
    return any(
        counterpart.player_id == them
        and PairwiseOutcome.DECLINED in counterpart.outcomes
        for counterpart in counterparts
    )


# ---------------------------------------------------------------------------
# The two blocks and the pass
# ---------------------------------------------------------------------------


async def _blocked(
    paths: ReadPaths, relationship: Relationship, *, blocked_by_her: bool
) -> str:
    """One block, in whichever direction the account is named for.

    Idempotent in the use case: a second tap appends nothing and needs no key,
    because a block is a state somebody asks for rather than a request that
    happens once. The direction is the whole content of the pair of accounts —
    one is trivially absent and proves nothing ADR-0095 did not already promise,
    and the other is the only fixture for a **symmetric effect read off a
    directed record**.
    """

    them = relationship.account
    blocker, blocked = (
        (PROTAGONIST, them) if blocked_by_her else (them, PROTAGONIST)
    )
    await paths.block.execute(
        BlockPlayerCommand(
            blocker_id=paths.player(blocker.email),
            blocked_id=paths.player(blocked.email),
            surface=BLOCKED_FROM,
        )
    )
    return (
        f"{them.slug} · {blocker.slug} blocked {blocked.slug} from the "
        f"{BLOCKED_FROM.value.lower()}, and neither side is told"
    )


async def _you_passed_them(
    paths: ReadPaths, relationship: Relationship, edge: YouPassedThem
) -> ThePassAndWhatItCost:
    """The protagonist deals a real deck and passes on the card this account is.

    **Idempotent for the row and unconditional for the cache**, and the asymmetry
    is the point. The row is the evidence and does not expire; the suppression is
    a Redis TTL that fails soft, so a flushed cache is a deck that deals somebody
    it should not — and a complaint reading *this fixture has rotted* when the
    truth is *you flushed Redis* is the failure a named catalog exists to avoid.
    So the suppression is written again on every run, including one that creates
    nothing.
    """

    them = paths.player(relationship.account.email)
    already = await paths.pass_ledger.last_passed_at(
        passer_id=paths.player(PROTAGONIST.email),
        sport=edge.sport,
        candidate_ids=[them],
    )
    answer = await deal_a_deck(paths, PROTAGONIST.email, edge.sport)
    record = answer.record
    dealt = them in returned_ids(record)

    if them in already:
        outcome = f"the pass of {already[them]:%Y-%m-%d} stands"
    elif dealt:
        await paths.passes.execute(
            RecordPassCommand(
                passer_id=paths.player(PROTAGONIST.email),
                passed_id=them,
                sport=edge.sport,
                search_id=record.id,
            )
        )
        outcome = f"passed, citing deal {record.id}"
    else:
        raise EdgeRefused(
            f"{PROTAGONIST.slug}'s {edge.sport.value} deal did not deal "
            f"'{relationship.account.slug}' and no pass on them stands, so there "
            f"is no origin for one to cite. It dealt "
            f"{record.counts.n_returned} of {record.counts.n_generated} "
            f"generated. A pass has no non-deal constructor, and this account is "
            f"the only thing that makes deck suppression observable at all."
        )

    # **The deck is spent when the pass stands and the deal no longer carries
    # them**, which is ADR-0131 rather than anything wrong: a deal is remembered
    # for a day, so the second `make seed` inside one deals the remainder. The
    # claims read off this record and they are told, so a re-run states the
    # cost instead of failing on it.
    spent = not dealt

    # Unconditional, and after the row either way. The window is the released
    # ruleset's, passed in for the reason `RecordPass` passes it in: a mechanism
    # holding its own copy of a product number is a second place for it to be
    # true.
    days = paths.ruleset.interest.pass_suppress_days
    await paths.suppression.suppress(
        passer_id=paths.player(PROTAGONIST.email),
        passed_id=them,
        for_days=days,
    )
    # **A probe on the store, and never the claim.** The ledger fails soft, so an
    # unreachable Redis answers *nobody* — the same answer as a lapsed window —
    # and a claim that could not tell those apart would report a rotted fixture
    # to somebody who had simply flushed a cache.
    reads_back = them in await paths.suppression.suppressed_for(
        passer_id=paths.player(PROTAGONIST.email), candidate_ids=[them]
    )
    costs = (
        f"the pass's gate is a Redis TTL that fails soft while its row never "
        f"expires, so this run re-wrote the {days}-day suppression on "
        f"'{relationship.account.slug}' whether or not it wrote the row — and "
        + (
            "it reads back, so the deck will hold them out."
            if reads_back
            else "it does **not** read back, so the store is unreachable and "
            "the deck cannot be shown holding them out. Bring Redis up and "
            "seed again."
        ),
        f"ADR-0131 remembers a deal for a day, and this run makes two — the one "
        f"that earned the pass's origin key, which dealt "
        f"{record.counts.n_returned} player(s) to {PROTAGONIST.slug}, and the one "
        f"the claims deal to prove the suppression holds. Her next *Match me* is "
        f"short by both of them until they are a day old"
        + (
            ". This run's own deck was already spent by an earlier one, so the "
            "deck's claims below are stated rather than read."
            if spent
            else "."
        ),
    )
    return ThePassAndWhatItCost(
        deal=record,
        deck_was_already_spent=spent,
        suppression_reads_back=reads_back,
        line=f"{relationship.account.slug} · {outcome}",
        costs=costs,
    )


# ---------------------------------------------------------------------------
# The inboxes — CHALLENGE_LOAD's three rungs
# ---------------------------------------------------------------------------


async def _fill_the_inboxes(paths: ReadPaths, *, cohort: Cohort) -> tuple[str, ...]:
    """Give three cohort members an inbox deep enough to print each rung.

    **A loaded candidate is loaded by other people**, which is why this is not
    one of the eleven: a challenge *from the protagonist* gates that person out
    of her surfaces entirely, so a pair could never carry the code. The depths
    come from the live ruleset's own rungs, and each rung names its own printed
    code — so a threshold that moves takes this fixture with it rather than
    silently re-pointing a card at a different depth.

    **Who gets which depth is decided by what the searches found**, not written
    down: one open challenge per pair means the deepest rung needs that many
    distinct organisers, and whether a member can organise at all is a question
    about their own pool. So the run walks the cohort, learns who can see whom,
    and hands the deepest inbox to whoever the most organisers could reach.

    **One seat per court, and the pair rule is what forces it.** Sharing a
    line-up makes a pair — every occupied seat but your own — so a court holding
    two of the loaded three would pair *them* with each other, and the second
    such court is refused. An organiser filling two inboxes therefore sends two
    half-built courts rather than one four, which is also the truer fixture:
    these are unanswered seats from unrelated people, not one game everybody was
    asked to.
    """

    rungs = paths.ruleset.liveness.challenge_load_rungs
    depths = sorted(rung.at_least for rung in rungs)
    loaded = members_who_carry_an_inbox(cohort)
    ids = {member.handle: paths.player(member.email) for member in loaded}

    counts = await paths.history.open_challenge_counts(list(ids.values()))
    standing = {handle: counts.get(player, 0) for handle, player in ids.items()}
    if _every_rung_has_a_witness(standing.values(), rungs):
        return tuple(
            f"inbox · {handle}: {depth} unanswered seat(s), already standing"
            for handle, depth in sorted(standing.items())
        )

    reachable, searches = await _who_can_reach(paths, loaded, cohort=cohort)
    plan = _assign(loaded, depths, reachable, standing)
    addresses = {member.handle: member.email for member in loaded}
    lines = []
    for handle, organisers in sorted(plan.items()):
        for organiser in organisers:
            await _send(
                paths,
                organiser=organiser,
                sport=Sport.PADEL,
                record=searches[organiser],
                invitees=(addresses[handle],),
            )
    counted = await paths.history.open_challenge_counts(list(ids.values()))
    for member in loaded:
        depth = counted.get(ids[member.handle], 0)
        rung = _rung_for(depth, rungs)
        lines.append(
            f"inbox · {member.handle}: {depth} unanswered seat(s) from other "
            f"members, printing {rung}"
        )
    _refuse_a_rung_with_no_witness(loaded, counted, ids, rungs)
    return tuple(lines)


def _every_rung_has_a_witness(
    standing: Iterable[int], rungs: Sequence[ChallengeLoadRung]
) -> bool:
    """Whether these inbox depths print every code, one member per code.

    **Not an elementwise comparison against the thresholds**, and the difference
    is the whole reason this is a function. The rungs are cumulative and a card
    prints the deepest one it reaches, so three inboxes of eight print ``FULL``
    three times and leave ``SOME`` and ``BUSY`` without a witness anywhere —
    which an *at least* test would call covered.
    """

    printed = {_rung_for(depth, rungs) for depth in standing}
    return {rung.prints.value for rung in rungs} <= printed


def _declarations_of(member: CohortMember) -> Sequence[tuple[Sport, PlayIntent]]:
    """A cohort row's Play intents, as the declaration types rather than strings.

    The artifact spells them as strings because it is committed JSON; every
    reader here wants the enums the platform declares in.
    """

    return tuple(
        (Sport(sport), PlayIntent(intent)) for sport, intent in member.intents
    )


def _enough_organisers(capacity: Sequence[int], depths: Sequence[int]) -> bool:
    """Whether these organiser counts can fill inboxes of those depths.

    A different question from the one above and asked of different numbers: this
    is *how many people could put a seat in each inbox*, matched deepest to
    deepest, because one open challenge per pair makes an organiser worth exactly
    one seat.
    """

    if len(capacity) != len(depths):
        return False
    return all(
        have >= want
        for have, want in zip(sorted(capacity), sorted(depths), strict=True)
    )


async def _who_can_reach(
    paths: ReadPaths,
    loaded: Sequence[CohortMember],
    *,
    cohort: Cohort,
) -> tuple[Mapping[str, list[str]], Mapping[str, SearchRecord]]:
    """Which cohort members can actually put a seat in each of these inboxes.

    One real search per candidate organiser, because *can they see them* is a
    question about gender, level and radius that only the pipeline answers — and
    the same record is then the origin the send cites, so nothing is searched
    twice. The walk stops as soon as the depths are satisfiable, which is what
    keeps a fixture of three inboxes from costing a search per member.
    """

    wanted = {member.handle: paths.player(member.email) for member in loaded}
    depths = sorted(
        rung.at_least for rung in paths.ruleset.liveness.challenge_load_rungs
    )
    already = {
        handle: {
            row.counterpart_id
            for row in await paths.history.open_challenges(player)
        }
        for handle, player in wanted.items()
    }
    reachable: dict[str, list[str]] = {member.handle: [] for member in loaded}
    searches: dict[str, SearchRecord] = {}
    tried = 0
    for organiser in members_who_might_organise(cohort):
        record = await run_a_shortlist(
            paths,
            organiser.email,
            Sport.PADEL,
            # Their own declaration, like every other search here: a member who
            # declared *for fun* and was searched competitively would be scored
            # against a tolerance they never asked for.
            _mode_declared_by(paths, _declarations_of(organiser), Sport.PADEL),
        )
        tried += 1
        shown = returned_ids(record)
        seen = [
            handle
            for handle, player in wanted.items()
            if player in shown
            and paths.player(organiser.email) not in already[handle]
        ]
        if seen:
            searches[organiser.email] = record
            for handle in seen:
                reachable[handle].append(organiser.email)
        if _enough_organisers(
            [len(found) for found in reachable.values()], depths
        ):
            return reachable, searches
    raise EdgeRefused(
        f"{tried} cohort member(s) ran their own padel search and the deepest "
        f"inbox this fixture could fill is "
        f"{max((len(found) for found in reachable.values()), default=0)} of "
        f"{max(depths)}: "
        + ", ".join(
            f"{handle} reachable by {len(found)}"
            for handle, found in sorted(reachable.items())
        )
        + ". One open challenge per pair means a rung of N needs N distinct "
        "organisers who can each see that member, so the cohort's nearest ring "
        "is now too thin for CHALLENGE_LOAD's top rung. The rule that chooses "
        "them is `LOADED_RING`/`LOADED_ARCHETYPE` in `app/seeds/relationships.py`."
    )


def _assign(
    loaded: Sequence[CohortMember],
    depths: Sequence[int],
    reachable: Mapping[str, list[str]],
    standing: Mapping[str, int],
) -> Mapping[str, list[str]]:
    """Which organisers fill which inbox. **Deepest rung to the best-reached.**"""

    order = sorted(loaded, key=lambda one: -len(reachable[one.handle]))
    plan: dict[str, list[str]] = {}
    for member, depth in zip(order, sorted(depths, reverse=True), strict=True):
        wanted = max(0, depth - standing[member.handle])
        plan[member.handle] = reachable[member.handle][:wanted]
    return plan


def _rung_for(depth: int, rungs: Sequence[ChallengeLoadRung]) -> str:
    """Which code a card would print at this depth, or that it prints none.

    There is **no fourth code for an empty inbox**: a signal that does not fire is
    absent from the list rather than present at zero.
    """

    printed = [rung.prints.value for rung in rungs if depth >= rung.at_least]
    return printed[-1] if printed else "nothing"


def _refuse_a_rung_with_no_witness(
    loaded: Sequence[CohortMember],
    counted: Mapping[UUID, int],
    ids: Mapping[str, UUID],
    rungs: Sequence[ChallengeLoadRung],
) -> None:
    """Every rung of ``challenge_load_rungs`` has somebody standing on it."""

    depths = sorted(counted.get(ids[member.handle], 0) for member in loaded)
    if _every_rung_has_a_witness(depths, rungs):
        return
    printed = sorted({_rung_for(depth, rungs) for depth in depths})
    raise EdgeRefused(
        f"the inboxes reached {depths}, which print {printed}. A card prints the "
        f"deepest rung it reaches and nothing else, so every rung of "
        f"`challenge_load_rungs` needs an inbox of its own — "
        + ", ".join(
            f"{rung.prints.value} at {rung.at_least}" for rung in rungs
        )
        + "."
    )


async def _a_search_that_showed(
    paths: ReadPaths,
    *,
    searcher: str,
    named: str,
    intents: Sequence[tuple[Sport, PlayIntent]],
    sport: Sport,
    wanted: Mapping[str, UUID],
) -> SearchRecord:
    """One real search, run as the sender, that showed everybody it has to.

    **The search and the refusal are one act**, because they are one rule: an
    edge cites the search that surfaced the person, so a search that did not
    surface them is not an origin — and five call sites each running the search
    and then remembering to check it is five places for the check to be dropped.
    """

    record = await run_a_shortlist(
        paths, searcher, sport, _mode_declared_by(paths, intents, sport)
    )
    _refuse_a_search_that_showed_nobody(record, wanted=wanted, searcher=named)
    return record


def _refuse_a_search_that_showed_nobody(
    record: SearchRecord, *, wanted: Mapping[str, UUID], searcher: str
) -> None:
    """The origin has to resolve, and this is where it is made to say why.

    **Stronger than the edge existing**: a search that did not return somebody
    proves they were not findable through gender, level and radius, and every
    lift claimed on the edge afterwards would be claimed about a pair no screen
    could have produced.
    """

    shown = returned_ids(record)
    missing = sorted(name for name, player in wanted.items() if player not in shown)
    if not missing:
        return
    raise EdgeRefused(
        f"{searcher}'s {record.sport.value} search returned "
        f"{record.counts.n_returned} of {record.counts.n_generated} generated "
        f"and never showed {missing}. An edge cites the search that surfaced the "
        f"person and `resolve_origin` refuses one that did not, so this "
        f"relationship cannot be written at all. "
        f"Gates: {dict(sorted(record.counts.excluded_by_gate.items()))}."
    )
