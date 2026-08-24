"""Execute the catalog through the use cases, and report what it did.

Every write here goes through a use case assembled from
``app.bootstrap.composition``. Nothing in this module opens a table. That is what
makes a seeded aggregate a real one: the event stream, the outbox row and the
projection are written by the same code a request writes them with, in the same
transaction, so a seeded assessment replays exactly as a played one does.

**A rated account is produced by answering the questionnaire, not by writing a
result.** The engine chooses each question from the answers so far, so the only
way to a Level near the bottom of the Established band is to answer the way a
player would — which is also the only way the transcript behind that rating is
one the review screen can render. What the scenario supplies is an
``AnswerPolicy``: which option to pick, counted from the weakest, for whatever it
is asked.

**Re-running leaves the same state rather than duplicating or failing.** Each
step is a question asked of what is already there, and the answers come from
three different places:

- Registration is a read before a write. ``RegisterUser`` refuses a second
  registration for an address (``EmailAlreadyRegistered``), so the account is
  looked up through the user repository first and the registration is skipped
  when it is there. Two seed runs *racing* each other would still lose one to
  the unique constraint — which is the right outcome for a developer command,
  and not a case worth writing code for.
- Starting an assessment needs nothing at all: ``CreateAssessment`` is already
  idempotent per player and sport, and hands back the open run.
- Abandoning and completing need a look at the run itself, because *abandoned*
  and *never started* are otherwise the same answer from every finder — a
  finder reports what is **open**, and neither of them is. So the pair's first
  attempt is loaded by its derived id: the domain files a run under
  ``(player, sport, attempt)``, and these accounts have exactly one run per
  sport, because a rated sport refuses a second assessment and an abandoned one
  is never restarted here.

That last probe is also what makes an **interrupted** run resumable: a rated
scenario whose questionnaire got half way before the process died is found in
progress and answered on from where it stopped, rather than being started again
beside itself.

**A seeded account's id is not fixed, its address is.** ``RegisterUser`` mints the
user id itself, which is right — an id chosen by a caller is an id the write path
does not own — so re-seeding a *fresh* database yields a different uuid.
Everything downstream is derived from it, so the runs and the ratings that follow
the account are stable relative to it. What is promised, and what a developer
signs in with, is the address.

**A name that no longer matches its state is refused.** Every rated scenario
carries the band it promises; the check reads the *stored* rating through the
rating repository, on every run, including one that created nothing. An engine
retune that moves ``rating-barely-established`` into Developing stops the seed
and says so, because an account whose name lies is worse than one that is
missing: nothing about the screen it is developed against would look wrong.

The events this writes land on the outbox and are delivered by the API's worker
the next time it polls, exactly as a request's are. Seeding does not deliver
them itself: a seed run is not an event-delivery worker, and having two would be
two things that can disagree about what has been delivered.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_assessment_engine,
    build_assessment_repository,
    build_booking_repository,
    build_club_repository,
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_court_holds,
    build_cascade_waves,
    build_city_matches,
    build_club_regulars,
    build_commitments,
    build_join_standby,
    build_ledger_repository,
    build_match_repository,
    build_match_scorer,
    build_match_standby_places,
    build_offers,
    build_open_cascade,
    build_rated_players,
    build_ratings,
    build_run_cascade,
    build_scoring_contexts,
    build_standby,
    build_password_hasher,
    build_reservation_repository,
    build_skill_rating_repository,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings, get_settings
from app.infrastructure.database.engine import create_engine
from app.kernel import (
    MINUTES_PER_DAY,
    Instant,
    Sport,
    Viewer,
    exhaustive,
    live_outcome,
    minutes,
    shifted,
    situation,
)
from app.modules.clubs.application.add_court import AddCourt
from app.modules.clubs.application.add_court_category import AddCourtCategory
from app.modules.clubs.application.change_club_policy import ChangeClubPolicy
from app.modules.clubs.application.change_payout_destination import (
    ChangePayoutDestination,
)
from app.modules.clubs.application.commands import (
    AddCourtCategoryCommand,
    AddCourtCommand,
    ChangeClubPolicyCommand,
    ChangePayoutDestinationCommand,
    RegisterClubCommand,
    RetireCourtCategoryCommand,
    RetireCourtCommand,
)
from app.modules.clubs.application.get_club import GetClub
from app.modules.clubs.application.register_club import RegisterClub
from app.modules.clubs.application.retire_court import RetireCourt
from app.modules.clubs.application.retire_court_category import RetireCourtCategory
from app.modules.clubs.domain.catalogue import Court, CourtCategory
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.clubs.domain.value_objects import CategoryName, CourtLabel
from app.modules.courts.application.book_court import BookCourt
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.courts.application.commands import (
    BookCourtCommand,
    ClaimCourtCommand,
    ReleaseReservationCommand,
)
from app.modules.courts.application.release_reservation import ReleaseReservation
from app.modules.courts.domain.ports import BookingRepository, ReservationRepository
from app.modules.courts.domain.reservation import ClubHeld, HolderKind, Reservation
from app.modules.matches.application.cancel_match import CancelMatch
from app.modules.matches.application.commands import (
    CancellationCause,
    CancelMatchCommand,
    PaySeatCommand,
    PostMatchCommand,
    TakeSeatCommand,
    DepartCommand,
    ProposeScoreCommand,
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.now.application.cascade import (
    CascadeOutcome,
    OpenCascade,
    RunCascade,
)
from app.modules.now.domain.ports import CascadeWaves, Offers
from app.modules.matches.application.standby import (
    JoinStandby,
    JoinStandbyCommand,
)
from app.modules.matches.application.record_result import ProposeScore
from app.modules.matches.domain.score import Score, SetScore
from app.modules.matches.application.seat_moves import Depart, PaySeat, TakeSeat
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository
from app.modules.matches.domain.ports import (
    StandbyPlaces as MatchStandbyPlaces,
)
from app.modules.money.application.commands import (
    Compensation,
    HeldByRaketa,
    NewMovement,
    PaidAtTheCounter,
    PassedToTheClub,
    RecordMovementsCommand,
    RecordShareCommand,
)
from app.modules.money.application.record_movements import RecordMovements
from app.modules.money.application.record_share import RecordShare
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.invariants import breaches_in
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.parties import PlayerParty, RaketaParty
from app.modules.money.domain.ports import LedgerRepository
from app.modules.money.domain.reference import Reference, ReferenceKind
from app.modules.rating.application.abandon_assessment import AbandonAssessment
from app.modules.rating.application.commands import (
    AbandonAssessmentCommand,
    AssessmentStep,
    CompleteAssessmentCommand,
    CreateAssessmentCommand,
    SubmitAnswerCommand,
)
from app.modules.rating.application.complete_assessment import CompleteAssessment
from app.modules.rating.application.create_assessment import CreateAssessment
from app.modules.rating.application.submit_answer import SubmitAnswer
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import AssessmentNotFound
from app.modules.rating.domain.ids import PlayerId, assessment_stream_id
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.application.register_user import RegisterUser
from app.modules.users.domain.ports import UserRepository
from app.seeds.catalog import (
    ACCOUNTS,
    SEED_PASSWORD,
    AbandonedRun,
    AnswerPolicy,
    OpenRun,
    RatedRun,
    Scenario,
    SeedAccount,
)
from app.seeds.clubs import CLUBS, KRAKOW, SeedCategory, SeedClub
from app.seeds.courts import RESERVATIONS, SeedReservation
from app.seeds.courts import SEED_MONDAY
from app.seeds.matches import MATCHES, OfferClaim, SeedMatch, StandbyClaim
from app.seeds.money import LEDGERS, Arrival, SeedLedger
from app.seeds.guard import refuse_unless_seedable

#: A questionnaire the seed can no longer finish is a hang, and a hang in a
#: developer command reads as a broken database. The engine's own ceiling is well
#: under this — nine questions, plus at most one tie-breaker — so reaching it
#: means the engine no longer stops for an answer policy that used to satisfy it,
#: which is a thing to be told rather than to wait through.
MAX_ANSWERS = 24


class SeedFailed(RuntimeError):
    """The seed cannot produce the state an account's name promises.

    A ``RuntimeError`` for the same reason ``SeedRefused`` is one: it is not a bad
    argument a caller might catch beside a parse failure, it is a refusal to hand
    a developer data whose name is a lie.
    """


@dataclass(frozen=True)
class SeededScenario:
    """One sport's state on an account, and whether this run built it."""

    scenario: Scenario
    assessment_id: UUID
    created: bool


@dataclass(frozen=True)
class SeededAccount:
    """What one account is, after the run — and what this run had to create.

    The flags are about *this run*, not about the account, which is why they are
    here and not on ``SeedAccount``. They are what makes a second run legible: an
    account that reports none of them is one the seed found already in the state
    it wanted.
    """

    account: SeedAccount
    player_id: UUID
    registered: bool
    scenarios: tuple[SeededScenario, ...]

    @property
    def already_present(self) -> bool:
        return not self.registered and not any(
            entry.created for entry in self.scenarios
        )


@dataclass(frozen=True)
class SeededClub:
    """What one club is, after the run — and whether this run created it."""

    club: SeedClub
    club_id: UUID
    created: bool


@dataclass(frozen=True)
class SeededReservation:
    """What one claim is, after the run — and whether this run created it."""

    reservation: SeedReservation
    reservation_id: UUID
    court_id: UUID
    created: bool


@dataclass(frozen=True)
class SeededMatch:
    """What one match is, after the run — and whether this run created it."""

    match: SeedMatch
    match_id: UUID
    created: bool


@dataclass(frozen=True)
class SeededLedger:
    """What one ledger is, after the run — and whether this run wrote it."""

    ledger: SeedLedger
    player_id: UUID
    created: bool


@dataclass(frozen=True)
class Seeded:
    """Everything one run brought into being, per context.

    A tuple per context rather than one flat list, because they are read by
    different people: a developer signs in as an account, looks at a club to
    understand why a card says what it says, and looks at a reservation to
    understand why a court is not on offer.
    """

    accounts: tuple[SeededAccount, ...]
    clubs: tuple[SeededClub, ...]
    reservations: tuple[SeededReservation, ...]
    matches: tuple[SeededMatch, ...]
    ledgers: tuple[SeededLedger, ...]


@dataclass(frozen=True)
class _UseCases:
    """Everything one seed run drives, built once from one session.

    The repositories are held beside the use cases because two of the three
    idempotency probes are repository reads — *is this run open*, *what does this
    player's rating say* — and asking them through the same objects the use cases
    write through is what keeps a version the store has since passed out of the
    picture.
    """

    users: UserRepository
    assessments: AssessmentRepository
    ratings: SkillRatingRepository
    clubs: ClubRepository
    reservations: ReservationRepository
    bookings: BookingRepository
    matches: MatchRepository
    ledgers: LedgerRepository
    register: RegisterUser
    create: CreateAssessment
    submit: SubmitAnswer
    complete: CompleteAssessment
    abandon: AbandonAssessment
    register_club: RegisterClub
    change_policy: ChangeClubPolicy
    change_payout: ChangePayoutDestination
    add_category: AddCourtCategory
    retire_category: RetireCourtCategory
    add_court: AddCourt
    retire_court: RetireCourt
    get_club: GetClub
    claim_court: ClaimCourt
    book_court: BookCourt
    release_reservation: ReleaseReservation
    post_match: PostMatch
    take_seat: TakeSeat
    pay_seat: PaySeat
    depart: Depart
    propose_score: ProposeScore
    cancel_match: CancelMatch
    resolve_hold: ResolveCourtHold
    join_standby: JoinStandby
    standby: MatchStandbyPlaces
    open_cascade: OpenCascade
    run_cascade: RunCascade
    waves: CascadeWaves
    offers: Offers
    record_movements: RecordMovements
    record_share: RecordShare
    #: The clock the Matches use cases write with. See `_SeededWeekClock`.
    week: "_SeededWeekClock"


def _build(session: AsyncSession) -> _UseCases:
    # The store and the publisher are built once and handed to every repository,
    # which is what a caller outside a request has to do deliberately — under
    # FastAPI the sharing comes free from per-request dependency caching.
    event_store = build_domain_event_store(session)
    events = build_event_publisher(session)
    engine = build_assessment_engine()
    clock = build_clock()
    uow = build_unit_of_work(session)

    assessments = build_assessment_repository(event_store=event_store, events=events)
    ratings = build_skill_rating_repository(event_store=event_store, events=events)
    users = build_user_repository(session)
    clubs = build_club_repository(session)
    reservations = build_reservation_repository(session)
    bookings = build_booking_repository(session)
    claim_court = ClaimCourt(clubs, reservations, uow)
    # Matches is the one context seeded on a clock the runner sets. See
    # `_SeededWeekClock` for why, and `app/seeds/matches.py` for what it buys.
    week = _SeededWeekClock()
    # The repository is on the seeded week too, and for the same reason the
    # ladder below is: it arms `next_wake_at` from the record it writes, and on
    # the wall clock a seeded match's schedule would be relative to the day the
    # seed happened to run rather than to the week it describes.
    matches = build_match_repository(session, events=events, clock=week)
    # The queue is on the seeded week's clock too, for the reason everything
    # around it is: `joined_at` is a fact about the week the scenario describes
    # and not about the day somebody ran the seed.
    standby = build_match_standby_places(session)
    court_holds = build_court_holds(claim_court, reservations)
    # The ladder is on the seeded week's clock too, and it has to be: a hold is
    # granted at the instant a tier is entered, and on the wall clock every
    # seeded `held_since` would be the day the seed happened to run.
    resolve_hold = ResolveCourtHold(matches, court_holds, uow, week)
    # Money is on the seeded week's clock too, and for the matches' own reason:
    # a movement is about a seat on that week, and on the wall clock every
    # seeded `occurred_at` would be the day the seed happened to run.
    ledgers = build_ledger_repository(event_store=event_store, events=events)
    record_movements = RecordMovements(ledgers, uow, week)

    # The invitation cascade, wired from the same factories a request and the
    # worker get. **On the seeded week's clock**, like every other Matches write
    # here: an offer is a fact about the evening a seat freed, and on the wall
    # clock every seeded `offered_at` would be the day somebody ran the seed.
    #
    # It is the only thing in this file that reads Now, and it is here because
    # `Depart` alone leaves a hole nobody was ever told about — which is a state
    # the product cannot otherwise reach, since the departure **route** opens a
    # cascade in the same transaction (ADR-0061).
    cascade_waves = build_cascade_waves(session)
    cascade_offers = build_offers(session)
    now_ratings = build_ratings(ratings)
    contexts = build_city_matches(
        matches=matches,
        clubs=clubs,
        reservations=reservations,
        ratings=now_ratings,
        contexts=build_scoring_contexts(),
    )

    return _UseCases(
        open_cascade=build_open_cascade(waves=cascade_waves, contexts=contexts),
        run_cascade=build_run_cascade(
            waves=cascade_waves,
            offers=cascade_offers,
            contexts=contexts,
            players=build_rated_players(event_store),
            regulars=build_club_regulars(matches),
            commitments=build_commitments(matches),
            ratings=now_ratings,
            standby=build_standby(matches=matches, standby=standby),
            scorer=build_match_scorer(),
            uow=uow,
            clock=week,
        ),
        waves=cascade_waves,
        offers=cascade_offers,
        users=users,
        assessments=assessments,
        ratings=ratings,
        clubs=clubs,
        reservations=reservations,
        bookings=bookings,
        matches=matches,
        ledgers=ledgers,
        record_movements=record_movements,
        record_share=RecordShare(record_movements),
        claim_court=claim_court,
        book_court=BookCourt(clubs, bookings, claim_court, uow, clock),
        release_reservation=ReleaseReservation(reservations, uow, clock),
        post_match=PostMatch(matches, clubs, resolve_hold, uow, week),
        take_seat=TakeSeat(matches, resolve_hold, uow, week),
        pay_seat=PaySeat(matches, resolve_hold, uow, week),
        depart=Depart(matches, resolve_hold, uow, week),
        propose_score=ProposeScore(matches, uow, week),
        cancel_match=CancelMatch(matches, resolve_hold, uow, week),
        resolve_hold=resolve_hold,
        join_standby=build_join_standby(
            matches=matches, standby=standby, clock=week
        ),
        standby=standby,
        week=week,
        register_club=RegisterClub(clubs, uow, clock),
        change_policy=ChangeClubPolicy(clubs, uow, clock),
        change_payout=ChangePayoutDestination(clubs, uow, clock),
        add_category=AddCourtCategory(clubs, uow, clock),
        retire_category=RetireCourtCategory(clubs, uow, clock),
        add_court=AddCourt(clubs, uow, clock),
        retire_court=RetireCourt(clubs, uow, clock),
        get_club=GetClub(clubs),
        register=RegisterUser(
            users=users,
            event_store=event_store,
            hasher=build_password_hasher(),
            uow=uow,
            clock=clock,
            events=events,
        ),
        create=CreateAssessment(
            engine=engine,
            assessments=assessments,
            ratings=ratings,
            uow=uow,
            clock=clock,
        ),
        submit=SubmitAnswer(
            engine=engine, assessments=assessments, uow=uow, clock=clock
        ),
        complete=CompleteAssessment(
            engine=engine,
            assessments=assessments,
            ratings=ratings,
            uow=uow,
            clock=clock,
        ),
        abandon=AbandonAssessment(assessments=assessments, uow=uow, clock=clock),
    )


async def seed(session: AsyncSession) -> Seeded:
    """Bring every account and every club in the catalog into the state it names.

    Takes a session rather than opening one, so the API test suite can drive
    this against its own fixture database instead of standing up a second one.
    ``run`` below is what opens a session for a real command.

    Clubs are seeded after the accounts, in the order the catalog lists them.
    Nothing links the two — a club has no owner and a player has no membership —
    so the order is only about which failure a half-finished run leaves behind,
    and the accounts are what a developer signs in with.

    Reservations come last, and that order **is** a dependency: a claim names a
    club's category and a booking names a player, so both have to exist. It is
    also the one context here whose scenarios can be refused by the *database*
    rather than by the catalog — two seeded claims overlapping on one court
    would be refused by the exclusion constraint, which is the system working.

    Matches come last for the same reason and one more: a match reads its club's
    policy at posting and carries it thereafter (ADR-0077), so the club has to be
    in the state its own name promises before a match copies anything from it.

    **Ledgers are genuinely last**, because a movement references a seat and a
    seat is a match's. Nothing in Matches reads a ledger, so the dependency runs
    one way here exactly as it does in the code (ADR-0055).
    """

    use_cases = _build(session)
    accounts = tuple([await _seed_account(use_cases, account) for account in ACCOUNTS])
    clubs = tuple([await _seed_club(use_cases, club) for club in CLUBS])
    reservations = tuple(
        [
            await _seed_reservation(use_cases, accounts, clubs, reservation)
            for reservation in RESERVATIONS
        ]
    )
    matches = tuple(
        [await _seed_match(use_cases, accounts, clubs, match) for match in MATCHES]
    )
    ledgers = tuple(
        [
            await _seed_ledger(use_cases, accounts, clubs, matches, ledger)
            for ledger in LEDGERS
        ]
    )
    await _refuse_a_ledger_set_that_breaks_an_invariant(use_cases)
    return Seeded(
        accounts=accounts,
        clubs=clubs,
        reservations=reservations,
        matches=matches,
        ledgers=ledgers,
    )


async def _seed_account(use_cases: _UseCases, account: SeedAccount) -> SeededAccount:
    player_id, registered = await _ensure_registered(use_cases, account)
    scenarios = tuple(
        [
            await _ensure_scenario(use_cases, player_id, account, scenario)
            for scenario in account.scenarios
        ]
    )
    await _refuse_a_name_that_lies(use_cases, player_id, account)
    return SeededAccount(
        account=account,
        player_id=player_id,
        registered=registered,
        scenarios=scenarios,
    )


async def _ensure_registered(
    use_cases: _UseCases, account: SeedAccount
) -> tuple[UUID, bool]:
    existing = await use_cases.users.get_by_email(account.email)
    if existing is not None:
        return existing.id, False

    user = await use_cases.register.execute(
        RegisterUserCommand(
            email=account.email,
            nickname=account.nickname,
            password=SEED_PASSWORD,
        )
    )
    return user.id, True


async def _ensure_scenario(
    use_cases: _UseCases,
    player_id: UUID,
    account: SeedAccount,
    scenario: Scenario,
) -> SeededScenario:
    """Bring one sport into the state the scenario names, from wherever it is."""

    existing = await _first_attempt(use_cases, player_id, scenario.sport)

    match scenario:
        case OpenRun():
            # Nothing to probe: starting is idempotent per player and sport, so
            # this is one read on a second run and hands back the open run.
            start = await use_cases.create.execute(
                CreateAssessmentCommand(
                    player_id=PlayerId(player_id), sport=scenario.sport
                )
            )
            return SeededScenario(
                scenario=scenario,
                assessment_id=start.step.assessment_id,
                created=start.created,
            )

        case AbandonedRun():
            if existing is not None and not existing.is_in_progress:
                return SeededScenario(
                    scenario=scenario, assessment_id=existing.id, created=False
                )
            start = await use_cases.create.execute(
                CreateAssessmentCommand(
                    player_id=PlayerId(player_id), sport=scenario.sport
                )
            )
            await use_cases.abandon.execute(
                AbandonAssessmentCommand(
                    player_id=player_id,
                    assessment_id=start.step.assessment_id,
                )
            )
            return SeededScenario(
                scenario=scenario,
                assessment_id=start.step.assessment_id,
                created=True,
            )

        case RatedRun():
            if existing is not None and existing.is_completed:
                return SeededScenario(
                    scenario=scenario, assessment_id=existing.id, created=False
                )
            return await _rate(use_cases, player_id, account, scenario)

        case _:
            exhaustive(scenario)


async def _rate(
    use_cases: _UseCases,
    player_id: UUID,
    account: SeedAccount,
    scenario: RatedRun,
) -> SeededScenario:
    """Answer the questionnaire to its stop, then ask for the rating.

    Two moments, not one (``docs/adr/0020``): the engine stopping is a fact about
    the transcript, and ``CompleteAssessment`` is what makes the rating. A seed
    that stopped at the stop would leave a run nobody can tell from
    ``assessment-in-progress`` — which is a state the catalog already has an
    account for.
    """

    start = await use_cases.create.execute(
        CreateAssessmentCommand(player_id=PlayerId(player_id), sport=scenario.sport)
    )
    step = await _answer_until_the_engine_stops(
        use_cases, player_id, account, scenario, start.step
    )
    await use_cases.complete.execute(
        CompleteAssessmentCommand(player_id=player_id, assessment_id=step.assessment_id)
    )
    return SeededScenario(
        scenario=scenario, assessment_id=step.assessment_id, created=True
    )


async def _answer_until_the_engine_stops(
    use_cases: _UseCases,
    player_id: UUID,
    account: SeedAccount,
    scenario: RatedRun,
    step: AssessmentStep,
) -> AssessmentStep:
    """Answer whatever is outstanding until nothing is.

    The loop reads the step the server just returned rather than counting
    questions, because how many a run gets is the engine's decision and changes
    with the answers — a strong player earns an extra demonstration, a beginner
    is finished after one.
    """

    policy: AnswerPolicy = scenario.answers
    answered = 0
    while step.question is not None:
        if answered >= MAX_ANSWERS:
            raise SeedFailed(
                f"'{account.slug}' has answered {answered} "
                f"{scenario.sport.value} questions and the questionnaire is "
                f"still going. The engine no longer stops for this answer "
                f"policy, so the seed is refusing to keep going rather than "
                f"hang."
            )
        step = await use_cases.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=step.assessment_id,
                question_id=step.question.id,
                option_id=policy.option_id_for(step.question),
            )
        )
        answered += 1
    return step


async def _first_attempt(
    use_cases: _UseCases, player_id: UUID, sport: Sport
) -> Assessment | None:
    """This pair's first run, whatever became of it — or nothing.

    The finders answer *what is open*, and the two states this has to tell apart
    — abandoned, and never started — are both closed to them. The id is derived
    rather than looked up because that is how the domain files a run, and the
    accounts here have exactly one run per sport: a rated sport refuses a second
    assessment, and nothing in this catalog restarts an abandoned one.
    """

    try:
        return await use_cases.assessments.load(
            assessment_stream_id(player_id, sport, 0), for_player=player_id
        )
    except AssessmentNotFound:
        return None


# ---------------------------------------------------------------------------
# Clubs
# ---------------------------------------------------------------------------


async def _seed_club(use_cases: _UseCases, scenario: SeedClub) -> SeededClub:
    """Bring one club into the state its name promises, from wherever it is.

    **Every step is a question asked of what is stored**, not a script replayed
    from the top, so a second run writes nothing and a run interrupted half way
    through a club finishes it rather than starting a second one beside it. The
    catalog declares the *whole* series — a club with two policies is one that
    has changed its policy once — so *how far along is this club* is a length
    comparison, which is the only shape that survives an interruption between
    two versions of the same series.
    """

    existing = await use_cases.clubs.get_by_name(scenario.name)
    created = existing is None
    club = (
        existing if existing is not None else await _register_club(use_cases, scenario)
    )

    club = await _catch_up_policies(use_cases, club, scenario)
    club = await _catch_up_payouts(use_cases, club, scenario)
    club = await _catch_up_catalogue(use_cases, club, scenario)

    await _refuse_a_club_whose_name_lies(use_cases, club.id, scenario)
    return SeededClub(club=scenario, club_id=club.id, created=created)


async def _register_club(use_cases: _UseCases, scenario: SeedClub) -> Club:
    return await use_cases.register_club.execute(
        RegisterClubCommand(
            name=scenario.name,
            address=scenario.address,
            point=KRAKOW,
            timezone=scenario.timezone,
            policy=scenario.policies[0],
            payout=scenario.payouts[0],
            pricing=scenario.pricing,
        )
    )


async def _catch_up_policies(
    use_cases: _UseCases, club: Club, scenario: SeedClub
) -> Club:
    for policy in scenario.policies[len(club.policy) :]:
        club = await use_cases.change_policy.execute(
            ChangeClubPolicyCommand(club_id=club.id, policy=policy)
        )
    return club


async def _catch_up_payouts(
    use_cases: _UseCases, club: Club, scenario: SeedClub
) -> Club:
    for destination in scenario.payouts[len(club.payout) :]:
        club = await use_cases.change_payout.execute(
            ChangePayoutDestinationCommand(club_id=club.id, destination=destination)
        )
    return club


async def _catch_up_catalogue(
    use_cases: _UseCases, club: Club, scenario: SeedClub
) -> Club:
    """Add what is missing, then retire what the catalog says is retired.

    Two passes rather than one, and in that order, because retiring a category
    retires the courts still in it — so a court declared retired *and* in a
    retired category must exist before either retirement runs, or the second
    pass has nothing to close and the history is one row short of the truth.
    """

    for category in scenario.categories:
        club = await _ensure_category(use_cases, club, category)
    for category in scenario.categories:
        club = await _retire_what_is_retired(use_cases, club, category)
    return club


async def _ensure_category(
    use_cases: _UseCases, club: Club, scenario: SeedCategory
) -> Club:
    name = CategoryName(scenario.name)
    if _category_named(club, name) is None:
        await use_cases.add_category.execute(
            AddCourtCategoryCommand(
                club_id=club.id,
                name=name,
                sport=scenario.sport,
                cover=scenario.cover,
                rate=scenario.rate,
            )
        )
        club = await use_cases.get_club.execute(club.id)

    category = _category_named(club, name)
    assert category is not None  # just added, or already there
    for court in scenario.courts:
        if _court_labelled(club, CourtLabel(court.label)) is None:
            await use_cases.add_court.execute(
                AddCourtCommand(
                    club_id=club.id,
                    category_id=category.id,
                    label=CourtLabel(court.label),
                )
            )
            club = await use_cases.get_club.execute(club.id)
    return club


async def _retire_what_is_retired(
    use_cases: _UseCases, club: Club, scenario: SeedCategory
) -> Club:
    for court in scenario.courts:
        stored = _court_labelled(club, CourtLabel(court.label))
        if court.retired and stored is not None and not stored.is_retired:
            await use_cases.retire_court.execute(
                RetireCourtCommand(club_id=club.id, court_id=stored.id)
            )
            club = await use_cases.get_club.execute(club.id)

    category = _category_named(club, CategoryName(scenario.name))
    if scenario.retired and category is not None and not category.is_retired:
        await use_cases.retire_category.execute(
            RetireCourtCategoryCommand(club_id=club.id, category_id=category.id)
        )
        club = await use_cases.get_club.execute(club.id)
    return club


def _category_named(club: Club, name: CategoryName) -> CourtCategory | None:
    """Matched across retired categories too, so a second run does not make a
    second one under a name the partial unique index has since freed."""

    for category in club.categories:
        if category.name == name:
            return category
    return None


def _court_labelled(club: Club, label: CourtLabel) -> Court | None:
    """A court is found by the label on its **latest** catalogue row.

    A retired court has no open row, so ``court.label`` is ``None`` for it — and
    looking only at live courts would make a second run add a fresh court under
    the same label, which is how a seeded catalogue quietly grows.
    """

    for court in club.courts:
        versions = court.catalogue.versions
        if versions and versions[-1].value.label == label:
            return court
    return None


async def _refuse_a_club_whose_name_lies(
    use_cases: _UseCases, club_id: UUID, scenario: SeedClub
) -> None:
    """Check the claim against the club that is **stored**, on every run.

    Read back rather than taken from whatever the last use case returned, and
    checked on a run that created nothing as well as on one that created
    everything — a club seeded a month ago against a catalog that has since been
    edited is exactly the case a check on the fresh result would miss.
    """

    club = await use_cases.get_club.execute(club_id)
    if not scenario.claim.holds(club):
        raise SeedFailed(
            f"'{scenario.slug}' is named for {scenario.claim.promise} and is no "
            f"longer one. Either the catalog or the name is now wrong — a club "
            f"whose name lies is worse than one that is missing, because "
            f"nothing about the screen it is developed against would look wrong."
        )


async def _refuse_a_name_that_lies(
    use_cases: _UseCases, player_id: UUID, account: SeedAccount
) -> None:
    """Check every rated scenario's claim against the rating that is stored.

    Read back rather than taken from the completion that just ran, and checked on
    a run that created nothing as well as on one that created everything — an
    account seeded a month ago against an engine that has since been retuned is
    exactly the case a check on the fresh result would miss.
    """

    claims = {
        scenario.sport: scenario.claim
        for scenario in account.scenarios
        if isinstance(scenario, RatedRun)
    }
    if not claims:
        return

    stored = {
        rating.sport: rating
        for rating in await use_cases.ratings.find_all_for(player_id=player_id)
    }
    for sport, claim in claims.items():
        rating = stored.get(sport)
        if rating is None:
            raise SeedFailed(
                f"'{account.slug}' is named for a {sport.value} rating and "
                f"holds none, though its assessment completed."
            )
        complaint = claim.complaint_about(
            band_name=rating.band_name,
            level=rating.mu,
            band_lower=rating.band_lower,
            band_upper=rating.band_upper,
        )
        if complaint is not None:
            raise SeedFailed(
                f"'{account.slug}' is named for a state it no longer produces: "
                f"its {sport.value} rating {complaint}. Either the answers or "
                f"the name is now wrong — an account whose name lies is worse "
                f"than one that is missing, because nothing about the screen it "
                f"is developed against would look wrong."
            )


async def run(settings: Settings | None = None) -> Seeded:
    """Open a connection of this command's own, seed, and close it.

    The guard is re-checked against the settings actually used. Importing this
    package already checked the process's, and this is the same question asked of
    the object that decides which database is about to be written to — a caller
    that constructs its own settings does not get to skip it.

    The engine is created and disposed here rather than taken from
    ``init_engine``: a seed run is not the API process, and an engine it owns
    outright is one it can close on the way out.
    """

    settings = settings or get_settings()
    refuse_unless_seedable(settings)

    engine = create_engine(settings)
    try:
        session_factory = async_sessionmaker(
            engine, expire_on_commit=False, autoflush=False
        )
        async with session_factory() as session:
            return await seed(session)
    finally:
        await engine.dispose()


def _state_of(scenario: Scenario) -> str:
    """The one word a developer needs for a scenario, in the report."""

    match scenario:
        case OpenRun():
            return "in progress"
        case AbandonedRun():
            return "abandoned"
        case RatedRun():
            return f"rated ({scenario.claim.band})"
        case _:
            exhaustive(scenario)


# ---------------------------------------------------------------------------
# Courts and Bookings
# ---------------------------------------------------------------------------


async def _seed_reservation(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    clubs: tuple[SeededClub, ...],
    scenario: SeedReservation,
) -> SeededReservation:
    """Bring one court into the state the scenario names, from wherever it is.

    **The probe is a query over reservations**, which is the same sentence
    ADR-0035 uses about availability and for the same reason: there is nothing
    beside the rows to ask, so a second run cannot disagree with the first about
    what it already did.

    A claim is found by the window it plays and the court it is on, across the
    club's whole live catalogue — *not* by an id, because the id is minted by the
    write path and a fresh database mints a different one. Released rows are
    matched too: the scenario named *a claim that was given back* is satisfied
    by exactly one released row, and looking only at live ones would claim a
    second court on every run.
    """

    club = await use_cases.get_club.execute(_seeded_club_id(clubs, scenario))
    category = _seeded_category(club, scenario.category)
    existing = await _claim_already_seeded(use_cases, club, category, scenario)
    if existing is not None:
        _refuse_a_reservation_whose_name_lies(scenario, existing)
        return SeededReservation(
            reservation=scenario,
            reservation_id=existing.id,
            court_id=existing.court_id,
            created=False,
        )

    reservation = await _write_the_claim(use_cases, club, category, accounts, scenario)
    if scenario.released:
        reservation = await use_cases.release_reservation.execute(
            ReleaseReservationCommand(reservation_id=reservation.id)
        )

    stored = await use_cases.reservations.get(reservation.id)
    assert stored is not None  # just written, in this transaction
    _refuse_a_reservation_whose_name_lies(scenario, stored)
    return SeededReservation(
        reservation=scenario,
        reservation_id=stored.id,
        court_id=stored.court_id,
        created=True,
    )


async def _write_the_claim(
    use_cases: _UseCases,
    club: Club,
    category: CourtCategory,
    accounts: tuple[SeededAccount, ...],
    scenario: SeedReservation,
) -> Reservation:
    """Through `BookCourt` or `ClaimCourt` — never a row, never a court id.

    Which court is picked is the funnel's answer, not the catalog's. A seed that
    named a court would be a seed that could not be refused by the exclusion
    constraint, and the constraint is the thing this context exists for.
    """

    if scenario.held_by is HolderKind.BOOKING:
        assert scenario.player_slug is not None  # `SeedReservation` refuses otherwise
        booking = await use_cases.book_court.execute(
            BookCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=scenario.played,
                player_id=_seeded_player(accounts, scenario.player_slug),
            )
        )
        claimed = await use_cases.reservations.get(booking.reservation_id)
        assert claimed is not None  # written in the same transaction
        return claimed

    return await use_cases.claim_court.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=scenario.played,
            holder=ClubHeld(),
        )
    )


async def _claim_already_seeded(
    use_cases: _UseCases,
    club: Club,
    category: CourtCategory,
    scenario: SeedReservation,
) -> Reservation | None:
    """Has this scenario already been written — asked of the courts themselves.

    Every court of the category is walked rather than only the live ones,
    because a court retired since the seed ran still carries the claim that was
    made on it, and re-claiming would put a second one on a live court.
    """

    for court in club.courts:
        for reservation in await use_cases.reservations.for_court(court.id):
            if (
                reservation.category_id == category.id
                and reservation.played == scenario.played
                and reservation.kind is scenario.held_by
                and reservation.is_live is not scenario.released
            ):
                return reservation
    return None


def _seeded_club_id(clubs: tuple[SeededClub, ...], scenario: SeedReservation) -> UUID:
    for seeded in clubs:
        if seeded.club.slug == scenario.club_slug:
            return seeded.club_id
    raise SeedFailed(
        f"'{scenario.slug}' names the club '{scenario.club_slug}', which the "
        f"club catalog does not hold. A claim on a club that does not exist is "
        f"a catalog that has been half-edited."
    )


def _seeded_category(club: Club, name: str) -> CourtCategory:
    category = _category_named(club, CategoryName(name))
    if category is None:
        raise SeedFailed(
            f"a reservation names the category '{name}' at "
            f"'{club.name.value}', which that club does not have."
        )
    return category


def _seeded_player(accounts: tuple[SeededAccount, ...], slug: str) -> UUID:
    for account in accounts:
        if account.account.slug == slug:
            return account.player_id
    raise SeedFailed(
        f"a booking names the player '{slug}', which the account catalog does not hold."
    )


def _refuse_a_reservation_whose_name_lies(
    scenario: SeedReservation, stored: Reservation
) -> None:
    """Check the claim against the reservation that is **stored**, every run.

    Including a run that created nothing — a seed written a month ago against a
    catalog that has since had its turnaround edited is exactly the case a check
    on the fresh result would miss.
    """

    if not scenario.claim.holds(stored):
        raise SeedFailed(
            f"'{scenario.slug}' is named for {scenario.claim.promise} and is no "
            f"longer one. Either the catalog or the name is now wrong — a "
            f"reservation whose name lies is worse than one that is missing, "
            f"because nothing about the screen it is developed against would "
            f"look wrong."
        )


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------


class _SeededWeekClock:
    """The clock the Matches use cases write with, set by the runner per step.

    Every other seeded aggregate is timeless — an account is registered whenever
    it is registered, and nothing about its name depends on when. A match **is**
    its clock: whether it committed, when a seat was taken, when a hole opened
    and whether the result window has closed are all comparisons against it, and
    they are what the scenario's name promises. Left on the wall clock, a seeded
    ``committed_at`` would say *the day somebody ran make seed* and the name
    would be a claim about that day rather than about the state.

    So this is a ``Clock`` port whose value the runner sets, which is what a port
    is for. It is **not** a fake standing in for a real one: the instants it
    hands out are written to the database and are the match's real facts.
    """

    def __init__(self) -> None:
        self._now: Instant | None = None

    def at(self, moment: Instant) -> None:
        self._now = moment

    def now(self) -> Instant:
        """The instant the runner set, or a refusal.

        A seeded write with no instant set is a bug, not a default of *now*:
        falling back to the wall clock is exactly the failure this class exists
        to remove, and it would be invisible — the run would succeed and the
        match would carry the day it happened to run.
        """

        if self._now is None:
            raise SeedFailed(
                "a Matches seed write with no instant set. The seeded week's "
                "clock is set per step; falling back to the wall clock would "
                "make the scenario's name a claim about the day the seed ran."
            )
        return self._now


async def _seed_match(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    clubs: tuple[SeededClub, ...],
    scenario: SeedMatch,
) -> SeededMatch:
    """Bring one match into the state the scenario names, from wherever it is.

    **The probe is a query over the club's matches**, keyed on the three facts a
    scenario fixes and the write path does not choose: the sport, the hour and
    whether the court is private. Not on an id — the id is minted by the write
    path and a fresh database mints a different one.
    """

    club_id = _seeded_club_id_for_match(clubs, scenario)
    existing = await _match_already_seeded(use_cases, club_id, scenario)
    if existing is not None:
        # The queue is written on this path too, and it is the one child here
        # that has to be: a scenario that gained a standby place after the
        # database was seeded would otherwise never get one, and the check
        # below would then fail on a run that was doing its job. Joining is
        # idempotent, so a run that changes nothing writes nothing.
        await _write_the_standby_places(use_cases, accounts, existing.id, scenario)
        # The cascade is run on this path too, and for the queue's own reason: a
        # scenario that gained an offer claim after the database was seeded
        # would otherwise never get one, and the check below would then fail on
        # a run that was doing its job. Both halves are idempotent — a hole
        # already queued opens nothing and a dispatch already run is not due —
        # so a run that changes nothing writes nothing.
        await _run_the_cascade(use_cases, existing, scenario)
        _refuse_a_match_whose_name_lies(scenario, existing)
        await _refuse_a_standby_place_whose_name_lies(
            use_cases, accounts, existing, scenario
        )
        await _refuse_an_offer_whose_name_lies(
            use_cases, accounts, existing, scenario
        )
        return SeededMatch(match=scenario, match_id=existing.id, created=False)

    match = await _write_the_match(use_cases, accounts, club_id, scenario)
    await _write_the_standby_places(use_cases, accounts, match.id, scenario)
    stored = await use_cases.matches.get(match.id)
    assert stored is not None  # just written, in this transaction
    # **After the queue and never before it.** Rung 1 is *somebody who asked for
    # this match*, so a dispatch run before the places were written would find
    # an empty queue, bring the second wave forward and tell a stranger first —
    # the standby promise broken by an ordering nobody would see.
    await _run_the_cascade(use_cases, stored, scenario)
    _refuse_a_match_whose_name_lies(scenario, stored)
    await _refuse_a_standby_place_whose_name_lies(
        use_cases, accounts, stored, scenario
    )
    await _refuse_an_offer_whose_name_lies(use_cases, accounts, stored, scenario)
    return SeededMatch(match=scenario, match_id=stored.id, created=True)


async def _write_the_match(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    club_id: UUID,
    scenario: SeedMatch,
) -> Match:
    """Post it, seat the players, take the money, open the hole — in that order.

    Every step through the use case a request runs, and every step on the
    seeded week's clock rather than on the wall clock.
    """

    club = await use_cases.get_club.execute(club_id)
    category = _seeded_category(club, scenario.category)

    use_cases.week.at(scenario.posted_at)
    match = await use_cases.post_match.execute(
        PostMatchCommand(
            club_id=club_id,
            category_id=category.id,
            sport=scenario.sport,
            start=scenario.start,
            duration=scenario.duration,
            share=scenario.share,
            kind=scenario.kind,
            pay_model=scenario.pay_model,
            open_seats=scenario.open_seats,
        )
    )

    use_cases.week.at(scenario.joined_at)
    seated = _players_for(accounts, scenario)
    for index, player in enumerate(seated):
        await use_cases.take_seat.execute(
            TakeSeatCommand(match_id=match.id, player_id=player)
        )
        if index < scenario.paid:
            await use_cases.pay_seat.execute(
                PaySeatCommand(match_id=match.id, player_id=player)
            )

    if scenario.vacated:
        assert scenario.vacated_at is not None  # `SeedMatch` refuses otherwise
        use_cases.week.at(scenario.vacated_at)
        for player in seated[: scenario.vacated]:
            # **The quote is the caller's, and here the seed is the caller.** It
            # reads the live outcome off the record it is about to write
            # against, which is what the departure route will do
            # (``Raketa02/Raketa#80``). Read fresh each time rather than once:
            # a scenario that loses two players loses the second one to a match
            # the first has already changed, which is the concurrent-leave case
            # quote-and-confirm exists for and the one place a stale quote would
            # go unnoticed.
            current = await use_cases.matches.get(match.id)
            assert current is not None  # written above, in this transaction
            match = await use_cases.depart.execute(
                DepartCommand(
                    match_id=match.id,
                    player_id=player,
                    quote=live_outcome(current.as_record(), scenario.vacated_at),
                )
            )

    if scenario.score is not None:
        # **The score goes on through the aggregate**, like everything else here
        # — so a seeded proposal carries the moment silence answers it, the
        # announcement a support agent reads, and the side cap ADR-0048 puts on
        # it. Writing the column would seed the answer this ticket computes.
        use_cases.week.at(scenario.score.at)
        await use_cases.propose_score.execute(
            ProposeScoreCommand(
                match_id=match.id,
                player_id=seated[scenario.score.by_seat],
                score=Score(
                    tuple(SetScore(a, b) for a, b in scenario.score.sets)
                ),
            )
        )

    if scenario.cancelled is not None:
        assert scenario.cancelled_at is not None  # `SeedMatch` refuses otherwise
        use_cases.week.at(scenario.cancelled_at)
        await use_cases.cancel_match.execute(
            CancelMatchCommand(
                match_id=match.id, cause=CancellationCause(scenario.cancelled)
            )
        )

    return match


async def _write_the_standby_places(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    match_id: UUID,
    scenario: SeedMatch,
) -> None:
    """Queue whoever the scenario says asked, through the use case a tap would.

    Seeds execute use cases and never SQL, and here that is load-bearing rather
    than ceremonial: **v1 has no surface that joins a queue at all** — the
    prototype's waitlist toggle is a match-screen control and the match screen
    is out of scope — so the seed is the only writer, and a seeded place written
    any other way would be a state no code path in the product produces.

    On the week's own clock, like every other Matches write here.
    """

    for claim in scenario.standby:
        use_cases.week.at(claim.resolved_at)
        await use_cases.join_standby.execute(
            JoinStandbyCommand(
                match_id=match_id,
                player_id=_seeded_player_for_standby(accounts, scenario, claim),
            )
        )


#: Far enough ahead that ``due`` answers every dispatch a seeded hole opened,
#: including one the quiet hours held to the following morning. The seed runs
#: both waves itself rather than waiting for a worker tick, so *due* here means
#: *exists* — and the moment each one runs at is still its own ``due_at``.
_FAR_FUTURE: Instant = shifted(SEED_MONDAY, minutes(365 * MINUTES_PER_DAY))

#: No ceiling. The batch's ``WAKE_BATCH_SIZE`` bounds the work one **tick** does
#: and means nothing here: a seeded week has as many dispatches as it has holes,
#: and taking a slice of them would leave a scenario's own claim depending on
#: how many other scenarios came first.
_EVERY_WAVE = 10_000


async def _run_the_cascade(
    use_cases: _UseCases, stored: Match, scenario: SeedMatch
) -> None:
    """Tell somebody about every hole this scenario left (ADR-0061).

    **The seed's `Depart` is not the departure route**, and this is the gap that
    closes. `now.MakeDeparture` opens a cascade in the transaction that writes
    the hole, because a vacancy nobody was told about is a seat that dies
    quietly; `matches.Depart` is the seed's own caller and does not, so without
    this the seeded week would carry the one state the product cannot reach — a
    hole with no invitation ladder behind it.

    **Both dispatches are run here rather than left to the worker**, each at its
    own due moment on the seeded week's clock. A seeded week whose offers depend
    on a background process having ticked is a week that reads differently
    depending on how long the app has been up, and the demo walkthrough
    (`Raketa02/Raketa#96`) is a claim about the data rather than about the
    uptime. What is *not* short-circuited is the ladder itself: the pool, the
    band, the floor and the order are all the dispatch's, computed from the same
    ports a request would hand it.

    A scenario that loses nobody has no open hole and this writes nothing at
    all, which is why it is called unconditionally rather than behind
    `scenario.vacated`.
    """

    for vacancy in stored.open_vacancies:
        use_cases.week.at(vacancy.vacated_at)
        await use_cases.open_cascade.execute(
            match_id=stored.id,
            vacancy_id=vacancy.id,
            vacated_at=vacancy.vacated_at,
        )
    # Read back rather than composed, so the quiet hours a hole was actually
    # held by are the moments these dispatches run at — `delivery_at` is applied
    # once, when the hole opens, and re-deriving it here would be a second
    # answer to *when may this be delivered*.
    for wave in await use_cases.waves.due(now=_FAR_FUTURE, limit=_EVERY_WAVE):
        if wave.match_id != stored.id:
            continue
        use_cases.week.at(wave.due_at)
        outcome = await use_cases.run_cascade.execute(wave)
        if outcome is CascadeOutcome.GONE:
            raise SeedFailed(
                f"'{scenario.slug}' opened a cascade on a match the scoring "
                f"read cannot see. A hole with no context behind it is a seat "
                f"nobody will ever be told about."
            )


async def _refuse_an_offer_whose_name_lies(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    stored: Match,
    scenario: SeedMatch,
) -> None:
    """Check that the ladder told the people the scenario says it told.

    The catalog's rule applied to the one fact here that **nothing can seed
    directly**: an offer is what a dispatch computed from the pool, the band and
    the fit, so a claim that holds is a claim the whole ladder produced. Two
    things can make it lie and they fail differently on purpose. Nobody told is
    a cascade that did not reach her — the band moved, the floor moved, or a
    rule started firing. The wrong **rung** is the ladder's *order* having moved
    under the name, which is the failure the whole catalog exists for: the offer
    is there, the card would look right, and the standby promise is gone.

    A scenario claiming an offer and losing nobody is refused before either,
    because there is no hole for a ladder to have walked.
    """

    if scenario.offers and not scenario.vacated:
        raise SeedFailed(
            f"'{scenario.slug}' claims an offer and loses nobody. A cascade "
            f"walks a hole, and a scenario with no hole has nothing to tell "
            f"anybody about."
        )
    for claim in scenario.offers:
        player_id = _seeded_player_for_offer(accounts, scenario, claim)
        # Asked **by player**, which is the offers region's own read: the seed
        # is its first caller, the shape `JoinStandby` already has.
        hers = [
            one
            for one in await use_cases.offers.held_by(player_id)
            if one.match_id == stored.id
        ]
        offer = hers[0] if hers else None
        if offer is None:
            raise SeedFailed(
                f"'{scenario.slug}' says the cascade told "
                f"'{claim.player_slug}' about its hole and no offer exists. A "
                f"name promising {claim.promise} cannot be drawn against a "
                f"ladder that reached nobody."
            )
        if offer.player_rung is not claim.rung:
            raise SeedFailed(
                f"'{scenario.slug}' says '{claim.player_slug}' was told on "
                f"rung {claim.rung.value} and the ladder put her on rung "
                f"{offer.player_rung.value}. The offer is there and the card "
                f"would look right, which is what makes this the failure worth "
                f"stopping on."
            )


def _seeded_player_for_offer(
    accounts: tuple[SeededAccount, ...],
    scenario: SeedMatch,
    claim: OfferClaim,
) -> UUID:
    for account in accounts:
        if account.account.slug == claim.player_slug:
            return account.player_id
    raise SeedFailed(
        f"'{scenario.slug}' offers its seat to '{claim.player_slug}', which the "
        f"account catalog does not hold. An offer pointing at nobody is a "
        f"catalog that has been half-edited."
    )


def _seeded_player_for_standby(
    accounts: tuple[SeededAccount, ...],
    scenario: SeedMatch,
    claim: StandbyClaim,
) -> UUID:
    for account in accounts:
        if account.account.slug == claim.player_slug:
            return account.player_id
    raise SeedFailed(
        f"'{scenario.slug}' queues the player '{claim.player_slug}', which the "
        f"account catalog does not hold. A queue place pointing at nobody is a "
        f"catalog that has been half-edited."
    )


def _players_for(
    accounts: tuple[SeededAccount, ...], scenario: SeedMatch
) -> list[UUID]:
    """The seeded accounts, in catalog order, as many as the scenario seats.

    In order rather than chosen, so that signing in as the first seeded account
    shows a developer her own matches — and so that which player is on seat 2 is
    the same on every run.
    """

    if scenario.taken > len(accounts):
        raise SeedFailed(
            f"'{scenario.slug}' seats {scenario.taken} players and the account "
            f"catalog holds {len(accounts)}."
        )
    return [account.player_id for account in accounts[: scenario.taken]]


async def _match_already_seeded(
    use_cases: _UseCases, club_id: UUID, scenario: SeedMatch
) -> Match | None:
    for match in await use_cases.matches.for_club(club_id):
        if (
            match.sport is scenario.sport
            and match.start == scenario.start
            and match.kind is scenario.kind
        ):
            return match
    return None


def _seeded_club_id_for_match(
    clubs: tuple[SeededClub, ...], scenario: SeedMatch
) -> UUID:
    for seeded in clubs:
        if seeded.club.slug == scenario.club_slug:
            return seeded.club_id
    raise SeedFailed(
        f"'{scenario.slug}' names the club '{scenario.club_slug}', which the "
        f"club catalog does not hold. A match at a club that does not exist is "
        f"a catalog that has been half-edited."
    )


def _refuse_a_match_whose_name_lies(scenario: SeedMatch, stored: Match) -> None:
    """Ask the **kernel** whether the name still holds, every run.

    The strongest form of this check in the whole seed system, and the cheapest:
    a match's state is derived, so the name can be checked by the one function
    that derives it. Retune a threshold, reorder a rung, or change what a paid
    seat means, and the seed stops and says which account's screen just moved —
    rather than a developer building against a card that quietly says something
    else.

    Checked against the **stored** match, including on a run that created
    nothing, and at the scenario's own instant, because a situation is a
    function of the record *and* the clock.
    """

    resolved = situation(stored.as_record(), None, scenario.claim.resolved_at)
    if resolved is not scenario.claim.situation:
        raise SeedFailed(
            f"'{scenario.slug}' is named for {scenario.claim.promise} — "
            f"{scenario.claim.situation.value} — and the kernel now resolves it "
            f"to {resolved.value}. Either the ladder or the name is wrong: a "
            f"match whose name lies is worse than one that is missing, because "
            f"nothing about the card it is developed against would look wrong."
        )
    _refuse_a_departure_whose_name_lies(scenario, stored)
    _refuse_a_score_whose_name_lies(scenario, stored)


async def _refuse_a_standby_place_whose_name_lies(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    stored: Match,
    scenario: SeedMatch,
) -> None:
    """Ask the **kernel** what the queued account's card says, every run.

    The same check the match's own name gets, pointed at the one thing about a
    match that is true only *for somebody*: ``waitlisted`` is the single
    situation only a viewer can be in (ADR-0040), so this is the one place in
    the catalog where the kernel is asked with a ``Viewer`` rather than without.

    Two things can make it lie and they fail differently on purpose. The place
    missing from the store is a queue that was never written — an ordinary
    seeded fact gone absent. The place present and the situation something else
    is the ladder having moved under the name, which is the failure the whole
    catalog exists for: nothing about the card would look wrong.
    """

    for claim in scenario.standby:
        player_id = _seeded_player_for_standby(accounts, scenario, claim)
        if stored.id not in await use_cases.standby.held_by(player_id):
            raise SeedFailed(
                f"'{scenario.slug}' says '{claim.player_slug}' is queued for it "
                f"and the store holds no such place. A card promising "
                f"{claim.promise} cannot be drawn against a queue that is empty."
            )
        resolved = situation(
            stored.as_record(),
            Viewer(
                holds_seat=stored.seat_of(player_id) is not None,
                on_standby=True,
            ),
            claim.resolved_at,
        )
        if resolved is not claim.situation:
            raise SeedFailed(
                f"'{scenario.slug}' promises '{claim.player_slug}' "
                f"{claim.promise} — {claim.situation.value} — and the kernel now "
                f"resolves her card to {resolved.value}. A queued player whose "
                f"name lies is worse than one that is missing: the act on that "
                f"card is the only one this build can receive."
            )


def _refuse_a_score_whose_name_lies(scenario: SeedMatch, stored: Match) -> None:
    """The same check, for the score on the table.

    Three facts, and each of them changes what the card says. The scoreline
    itself, because a card prints it. **How many sides have spoken**, because
    that is what decides which way silence settles it — *stands* against
    *uncounted* — and nothing else in the run reads it. And the proposal's own
    **moment**, because it is the hero clock: a stored score with no moment
    behind it resolves against the match's deadline instead, which is the
    reversal ADR-0048 made and the one this catalog would silently undo.
    """

    claim = scenario.score
    if claim is None:
        return

    if stored.score is None:
        raise SeedFailed(
            f"'{scenario.slug}' promises {claim.promise} and the stored match "
            "has a bare table. A scenario named for a conversation nobody "
            "started is the failure this catalog exists to refuse."
        )
    stored_sets = tuple((one.side_a, one.side_b) for one in stored.score.sets)
    if stored_sets != claim.sets:
        raise SeedFailed(
            f"'{scenario.slug}' promises {claim.promise} and the stored score "
            f"is {stored_sets}."
        )
    if stored.proposals != claim.proposals:
        raise SeedFailed(
            f"'{scenario.slug}' promises {claim.proposals} proposal(s) and the "
            f"stored match carries {stored.proposals}. One proposal nobody "
            "answered stands; two leave the match uncounted, and a card cannot "
            "tell them apart from the score alone."
        )
    if stored.proposed_at != claim.at:
        raise SeedFailed(
            f"'{scenario.slug}' promises a score entered at {claim.at} and the "
            f"stored match says {stored.proposed_at}. That moment is the "
            "screen's hero clock, and a match without one answers against its "
            "own deadline instead."
        )


def _refuse_a_departure_whose_name_lies(scenario: SeedMatch, stored: Match) -> None:
    """The same check, for the leaver's money.

    A vacancy and a departure are two facts (ADR-0033) and the seed names both.
    This one is worth checking separately because it is the only seeded claim
    that is about **a refund**: a card that says *not yet decided* when the money
    has settled, or names an amount where nothing was taken, is a wrong answer
    about somebody's money and nothing else in the run would notice.
    """

    claim = scenario.departure
    if claim is None:
        return

    if len(stored.departures) != scenario.vacated:
        raise SeedFailed(
            f"'{scenario.slug}' loses {scenario.vacated} player(s) and the "
            f"stored match carries {len(stored.departures)} departure(s). A "
            "hole with no departure behind it is money nobody can account for."
        )

    undecided = "not yet decided"
    promised = claim.outcome.value if claim.outcome else undecided
    for departure in stored.departures:
        if departure.outcome is not claim.outcome:
            stored_as = departure.outcome.value if departure.outcome else undecided
            raise SeedFailed(
                f"'{scenario.slug}' promises {claim.promise} — outcome "
                f"{promised} — and the stored departure says {stored_as}."
            )
        if departure.took_nothing is claim.names_an_amount:
            named = "names an amount" if claim.names_an_amount else "names none"
            raise SeedFailed(
                f"'{scenario.slug}' promises a leaver's card that {named}, and "
                "the stored departure disagrees. The two payload forms are the "
                "difference between *nothing was taken* and *nothing has come "
                "back yet*, which are opposite sentences."
            )


def report(seeded: Seeded) -> list[str]:
    """The run, as lines a developer reads — address, password, state, id."""

    lines = [
        f"Seeded {len(seeded.accounts)} account(s). "
        f"Password for all of them: {SEED_PASSWORD}",
        "",
    ]
    for entry in seeded.accounts:
        state = "already present" if entry.already_present else "created"
        lines.append(f"  {entry.account.email}  [{state}]")
        lines.append(f"      {entry.account.description}")
        lines.append(f"      player {entry.player_id}")
        for seeded_scenario in entry.scenarios:
            lines.append(
                f"      {seeded_scenario.scenario.sport.value} "
                f"{_state_of(seeded_scenario.scenario)} · "
                f"assessment {seeded_scenario.assessment_id}"
            )

    lines.append("")
    lines.append(f"Seeded {len(seeded.clubs)} club(s).")
    lines.append("")
    for club in seeded.clubs:
        state = "created" if club.created else "already present"
        lines.append(f"  {club.club.slug}  [{state}]")
        lines.append(f"      {club.club.description}")
        lines.append(f"      club {club.club_id}")

    lines.append("")
    lines.append(f"Seeded {len(seeded.reservations)} court claim(s).")
    lines.append("")
    for claim in seeded.reservations:
        state = "created" if claim.created else "already present"
        lines.append(f"  {claim.reservation.slug}  [{state}]")
        lines.append(f"      {claim.reservation.description}")
        lines.append(
            f"      reservation {claim.reservation_id} on court {claim.court_id}"
        )

    lines.append("")
    lines.append(f"Seeded {len(seeded.matches)} match(es).")
    lines.append("")
    for match in seeded.matches:
        state = "created" if match.created else "already present"
        lines.append(f"  {match.match.slug}  [{state}]")
        lines.append(f"      {match.match.description}")
        lines.append(
            f"      match {match.match_id} · {match.match.claim.situation.value}"
        )
        for queued in match.match.standby:
            # Named here because it is the only fact in the run that is true of
            # *one account* rather than of the match, and a developer signing in
            # as somebody else would otherwise not know whose card it is.
            lines.append(
                f"      queued: {queued.player_slug} · {queued.situation.value}"
            )

    lines.append("")
    lines.append(f"Seeded {len(seeded.ledgers)} ledger(s).")
    lines.append("")
    for ledger in seeded.ledgers:
        state = "created" if ledger.created else "already present"
        lines.append(f"  {ledger.ledger.slug}  [{state}]")
        lines.append(f"      {ledger.ledger.description}")
        lines.append(
            f"      player {ledger.player_id} · "
            f"{ledger.ledger.claim.movements} movement(s) · "
            f"held {ledger.ledger.claim.held} · "
            f"balance {ledger.ledger.claim.balance}"
        )
    return lines


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------


async def _seed_ledger(
    use_cases: _UseCases,
    accounts: tuple[SeededAccount, ...],
    clubs: tuple[SeededClub, ...],
    matches: tuple[SeededMatch, ...],
    scenario: SeedLedger,
) -> SeededLedger:
    """Bring one player's ledger into the state the scenario names.

    **The probe is the reference**, which is what makes this idempotent without a
    read-modify-write: a movement is filed under a fixed ``PAY-<token>`` and the
    ledger refuses a second one under the same one, so finding it is finding that
    this scenario has already run. An id would not do — the movement's id is
    minted by the write path, and a fresh database mints a different one.
    """

    player_id = _seeded_player_for_ledger(accounts, scenario)
    ledger = await use_cases.ledgers.load(player_id)
    if ledger.movement_under(_payment(scenario)) is not None:
        _refuse_a_ledger_whose_name_lies(scenario, ledger, _seat(matches, scenario))
        return SeededLedger(ledger=scenario, player_id=player_id, created=False)

    await _write_the_movements(use_cases, clubs, matches, scenario, player_id)
    stored = await use_cases.ledgers.load(player_id)
    _refuse_a_ledger_whose_name_lies(scenario, stored, _seat(matches, scenario))
    return SeededLedger(ledger=scenario, player_id=player_id, created=True)


async def _write_the_movements(
    use_cases: _UseCases,
    clubs: tuple[SeededClub, ...],
    matches: tuple[SeededMatch, ...],
    scenario: SeedLedger,
    player_id: UUID,
) -> None:
    """Through the use cases a request runs, on the seeded week's clock.

    The instant is the match's own ``joined_at`` — when the seat this money is
    about was taken — so a movement is dated on the week it belongs to rather
    than on the day somebody ran ``make seed``.
    """

    seeded_match = _seeded_match_for_ledger(matches, scenario)
    use_cases.week.at(seeded_match.match.joined_at)
    seat = _seat(matches, scenario)
    club_id = _seeded_club_id_for_match(clubs, seeded_match.match)

    if scenario.arrival is Arrival.HELD:
        await use_cases.record_share.execute(
            RecordShareCommand(
                player_id=player_id,
                seat=seat,
                amount=scenario.amount,
                reference=_payment(scenario),
                arrival=HeldByRaketa(),
            )
        )
    elif scenario.arrival is Arrival.PASSED_THROUGH:
        await use_cases.record_share.execute(
            RecordShareCommand(
                player_id=player_id,
                seat=seat,
                amount=scenario.amount,
                reference=_payment(scenario),
                arrival=PassedToTheClub(
                    club_id=club_id, settlement=_settlement(scenario)
                ),
            )
        )
    elif scenario.arrival is Arrival.AT_COUNTER:
        await use_cases.record_share.execute(
            RecordShareCommand(
                player_id=player_id,
                seat=seat,
                amount=scenario.amount,
                reference=_payment(scenario),
                arrival=PaidAtTheCounter(club_id=club_id),
            )
        )
    elif scenario.arrival is Arrival.CORRECTED:
        # The share and its reversal in **one** write, so there is no instant at
        # which the seeded ledger says Raketa kept the money.
        await use_cases.record_movements.execute(
            RecordMovementsCommand(
                player_id=player_id,
                drafts=(
                    NewMovement(
                        payer=PlayerParty(player_id),
                        payee=RaketaParty(),
                        amount=scenario.amount,
                        cause=MovementCause.SHARE_ONLINE,
                        reference=_payment(scenario),
                        seat=seat,
                    ),
                    Compensation(
                        original=_payment(scenario),
                        reference=_reversal(scenario),
                        cause=MovementCause.CLAIM_LAPSED,
                    ),
                ),
            )
        )
    elif scenario.arrival is Arrival.COLLECTION_FAILED:
        await use_cases.record_movements.execute(
            RecordMovementsCommand(
                player_id=player_id,
                drafts=(
                    NewMovement(
                        payer=RaketaParty(),
                        payee=PlayerParty(player_id),
                        amount=scenario.amount,
                        cause=MovementCause.COLLECTION_FAILED,
                        reference=_payment(scenario),
                        seat=seat,
                    ),
                ),
            )
        )
    else:  # pragma: no cover — the enumeration is closed
        exhaustive(scenario.arrival)


def _payment(scenario: SeedLedger) -> Reference:
    return Reference(ReferenceKind.PAYMENT, scenario.token)


def _settlement(scenario: SeedLedger) -> Reference:
    return Reference(ReferenceKind.PAYMENT, f"{scenario.token}s")


def _reversal(scenario: SeedLedger) -> Reference:
    return Reference(ReferenceKind.REVERSAL, scenario.token)


def _seeded_match_for_ledger(
    matches: tuple[SeededMatch, ...], scenario: SeedLedger
) -> SeededMatch:
    for seeded in matches:
        if seeded.match.slug == scenario.match_slug:
            return seeded
    raise SeedFailed(
        f"'{scenario.slug}' names the match '{scenario.match_slug}', which the "
        f"match catalog does not hold. A movement about a seat on a match that "
        f"does not exist is a catalog that has been half-edited."
    )


def _seat(matches: tuple[SeededMatch, ...], scenario: SeedLedger) -> SeatRef:
    return SeatRef(
        match_id=_seeded_match_for_ledger(matches, scenario).match_id,
        index=scenario.seat_index,
    )


def _seeded_player_for_ledger(
    accounts: tuple[SeededAccount, ...], scenario: SeedLedger
) -> UUID:
    for account in accounts:
        if account.account.slug == scenario.account_slug:
            return account.player_id
    raise SeedFailed(
        f"'{scenario.slug}' names the account '{scenario.account_slug}', which "
        f"the account catalog does not hold."
    )


def _refuse_a_ledger_whose_name_lies(
    scenario: SeedLedger, stored: Ledger, seat: SeatRef
) -> None:
    """Check the claim against the ledger that is **stored**, every run.

    Every number here is a **fold** — nothing about a balance or a held amount is
    written down anywhere — so this is the arithmetic a screen and a support
    conversation both read, checked against the movements that produce it. Change
    what a cause does to a balance and the seed stops and says whose money just
    moved.
    """

    found = (
        len(stored.movements),
        int(stored.held_for(seat)),
        int(stored.balance),
    )
    promised = (
        scenario.claim.movements,
        int(scenario.claim.held),
        int(scenario.claim.balance),
    )
    if found != promised:
        raise SeedFailed(
            f"'{scenario.slug}' is named for {scenario.claim.promise} and is no "
            f"longer one: it promises {promised} (movements, held, balance) and "
            f"the stored ledger folds to {found}. A ledger whose name lies is "
            f"worse than one that is missing — nothing about the screen it is "
            f"developed against would look wrong."
        )


async def _refuse_a_ledger_set_that_breaks_an_invariant(
    use_cases: _UseCases,
) -> None:
    """The three the nightly reconciliation asserts, over everything seeded.

    Run on every seed, including one that creates nothing: a seeded database that
    breaks a ledger invariant is one every future Money test is developed
    against, and the invariants are cheap enough to check here that leaving it to
    a job nobody runs locally would be a choice.
    """

    for ledger in await use_cases.ledgers.all_ledgers():
        breaches = breaches_in(ledger)
        if breaches:
            raise SeedFailed(
                "the seeded ledgers break "
                f"{breaches[0].invariant}: {breaches[0].detail}"
            )
