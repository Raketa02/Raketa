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
    build_club_repository,
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_password_hasher,
    build_skill_rating_repository,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings, get_settings
from app.infrastructure.database.engine import create_engine
from app.kernel import Sport, exhaustive
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
class Seeded:
    """Everything one run brought into being, per context.

    A tuple per context rather than one flat list, because the two are read by
    different people: a developer signs in as an account, and looks at a club to
    understand why a card says what it says.
    """

    accounts: tuple[SeededAccount, ...]
    clubs: tuple[SeededClub, ...]


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

    return _UseCases(
        users=users,
        assessments=assessments,
        ratings=ratings,
        clubs=clubs,
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
    """

    use_cases = _build(session)
    accounts = tuple([await _seed_account(use_cases, account) for account in ACCOUNTS])
    clubs = tuple([await _seed_club(use_cases, club) for club in CLUBS])
    return Seeded(accounts=accounts, clubs=clubs)


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
    club = existing if existing is not None else await _register_club(
        use_cases, scenario
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
    return lines
