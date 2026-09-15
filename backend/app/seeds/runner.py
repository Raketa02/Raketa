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

**That sentence is about the outbox and it does not bind the candidate index.**
The two are different subscriptions with different guarantees
(``docs/adr/0110``): the outbox delivers side effects once per platform, leased,
out of append order; the index is a **projection of the log** that anybody may
recompute, behind a single ``FOR UPDATE`` cursor, so a concurrent tick blocks and
then finds nothing to do. That property was made true on purpose, and it is what
lets this run **tick the tail to catch-up in-process** before the assertions in
``app/seeds/screens.py`` read the index. Polling ``caught_up_at`` would make a
developer command depend on the API being up; printing *now run
``make rebuild-candidate-index``* would put the assertions behind a step people
forget, which is the same failure as an account whose name lies.

**A profile is committed on an injected clock** (``app/seeds/clock.py``). On the
wall clock every seeded profile is a newcomer, and ADR-0113's whole point is that
newness changes the *gate* — which cannot be seen without both sides present. The
clock is a port and the commit is the same use case, so ``docs/adr/0029`` is
honoured rather than bent.

**The dates are relative to the run that wrote them, and a re-run re-commits
nothing.** Fifteen days on, every seeded newcomer has aged out at once — so the
run **fails by name, with the age in days**, exactly as a rating that has drifted
out of its band does. Sliding the dates forward on each run was rejected: it
makes the seed non-idempotent and puts a fabricated edit history on every
aggregate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.composition import (
    build_assessment_engine,
    build_assessment_repository,
    build_background_session_factory,
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_image_transcoder,
    build_password_hasher,
    build_photo_storage,
    build_play_intent_declaration_repository,
    build_player_profile_repository,
    build_skill_rating_repository,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings, get_settings
from app.infrastructure.database.engine import create_engine
from app.kernel import Clock, Instant, Sport, exhaustive
from app.modules.player_profile.application.change_availability import (
    ChangeAvailability,
)
from app.modules.player_profile.application.commands import (
    ChangeAvailabilityCommand,
    CommitPlayerProfileCommand,
    DeclarePlayIntentCommand,
)
from app.modules.player_profile.application.commit_player_profile import (
    CommitPlayerProfile,
)
from app.modules.player_profile.application.declare_play_intent import DeclarePlayIntent
from app.modules.player_profile.application.commands import UploadPhotoCommand
from app.modules.player_profile.application.upload_photo import UploadPhoto
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayIntentDeclarationRepository,
    PlayerProfileRepository,
)
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
from app.modules.users.application.commands import (
    NameUserCommand,
    RegisterUserCommand,
)
from app.modules.users.application.name_user import NameUser
from app.modules.users.application.register_user import RegisterUser
from app.modules.users.domain.ports import UserRepository
from app.seeds.catalog import (
    ACCOUNTS,
    SEED_CONSENT_COPY_VERSION,
    SEED_PASSWORD,
    AbandonedRun,
    AnswerPolicy,
    OpenRun,
    RatedRun,
    Scenario,
    SeedAccount,
    SeedProfile,
    answer_key,
)
from app.seeds.clock import (
    NEWCOMER_WINDOW_DAYS,
    FixedClock,
    age_in_days,
    days_before,
)
from app.seeds.cohort import (
    BAND_HISTOGRAM,
    COHORT,
    Cohort,
    CohortMember,
)
from app.seeds.games import SeededGames, write_the_played_history
from app.seeds.guard import refuse_unless_seedable
from app.seeds.loop import (
    SeededLoop,
    assert_the_loop,
    costs as loop_costs,
    write_the_loop,
)
from app.seeds.pairs import SeededPairs, write_the_relationships
from app.seeds.photos import (
    SEED_IMAGE_MEDIA_TYPE,
    DeclaredPhotoReview,
    an_image,
    the_store_answers,
)
from app.seeds.relationships import PROTAGONIST, RELATIONSHIP_ACCOUNTS
from app.seeds.plans import SeededPlans, costs as plan_costs, write_the_plans
from app.seeds.rooms import SeededRooms, open_the_rooms
from app.seeds.screens import assert_the_screens
from app.seeds.sportsmanship import SeededOpinions, write_what_players_said

#: A questionnaire the seed can no longer finish is a hang, and a hang in a
#: developer command reads as a broken database. The engine's own ceiling is well
#: under this — nine questions, plus at most one tie-breaker — so reaching it
#: means the engine no longer stops for an answer policy that used to satisfy it,
#: which is a thing to be told rather than to wait through.
MAX_ANSWERS = 24

#: How long a seeded photograph's URL would be good for. **Never read**: the run
#: keeps no URL and hands one to nobody, and a card's link is minted per response
#: by the boundary rather than by an upload. It is here because the use case a
#: request runs takes the window, and it is a constant rather than the setting so
#: that a fixture cannot be the reason somebody changes a production number.
SEED_PHOTO_URL_MINUTES = 15


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
    #: Whether *this run* committed the profile. ``False`` where there is no
    #: profile to commit and where one was already there, which is the same
    #: distinction the flags beside it draw.
    committed_profile: bool = False

    @property
    def already_present(self) -> bool:
        return (
            not self.registered
            and not self.committed_profile
            and not any(entry.created for entry in self.scenarios)
        )


@dataclass(frozen=True)
class _UseCases:
    """Everything one seed run drives, built once from one session and one clock.

    The repositories are held beside the use cases because the idempotency probes
    are repository reads — *is this run open*, *what does this player's rating
    say*, *has this player a profile yet* — and asking them through the same
    objects the use cases write through is what keeps a version the store has
    since passed out of the picture.

    **The clock is a constructor argument rather than a call**, because the whole
    point of injecting one is that different accounts are written at different
    instants: a settled member and a newcomer are the same code on two clocks.
    """

    clock: Clock
    #: The object store the upload writes to and the commit re-validates
    #: against. **One per run**, because two would be two answers to *does this
    #: player really have this photo*.
    photos: PhotoStorage
    users: UserRepository
    assessments: AssessmentRepository
    ratings: SkillRatingRepository
    profiles: PlayerProfileRepository
    declarations: PlayIntentDeclarationRepository
    register: RegisterUser
    name: NameUser
    create: CreateAssessment
    submit: SubmitAnswer
    complete: CompleteAssessment
    abandon: AbandonAssessment
    commit_profile: CommitPlayerProfile
    change_availability: ChangeAvailability
    declare_intent: DeclarePlayIntent


def _build(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    photos: PhotoStorage,
) -> _UseCases:
    # The store and the publisher are built once and handed to every repository,
    # which is what a caller outside a request has to do deliberately — under
    # FastAPI the sharing comes free from per-request dependency caching.
    event_store = build_domain_event_store(session)
    events = build_event_publisher(session)
    engine = build_assessment_engine()
    uow = build_unit_of_work(session)

    assessments = build_assessment_repository(event_store=event_store, events=events)
    ratings = build_skill_rating_repository(event_store=event_store, events=events)
    users = build_user_repository(session)
    profiles = build_player_profile_repository(
        event_store=event_store, events=events
    )
    declarations = build_play_intent_declaration_repository(
        event_store=event_store, events=events
    )

    return _UseCases(
        clock=clock,
        photos=photos,
        users=users,
        assessments=assessments,
        ratings=ratings,
        profiles=profiles,
        declarations=declarations,
        register=RegisterUser(
            users=users,
            event_store=event_store,
            hasher=build_password_hasher(),
            uow=uow,
            clock=clock,
            events=events,
        ),
        name=NameUser(
            users=users, event_store=event_store, uow=uow, clock=clock, events=events
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
        commit_profile=CommitPlayerProfile(
            profiles=profiles,
            # **The same store the upload wrote to**, which is what makes the
            # commit's own re-validation of every photo id mean anything: it
            # asks the port whether this player really holds this photograph,
            # and two stores would be two answers. Most seeded profiles still
            # name none at all and the port is never asked about them.
            photos=photos,
            uow=uow,
            clock=clock,
        ),
        change_availability=ChangeAvailability(
            profiles=profiles, uow=uow, clock=clock
        ),
        declare_intent=DeclarePlayIntent(
            declarations=declarations, uow=uow, clock=clock
        ),
    )


async def seed(
    session: AsyncSession,
    *,
    clock: Clock | None = None,
    settings: Settings | None = None,
    photos: PhotoStorage | None = None,
) -> tuple[SeededAccount, ...]:
    """Bring every account in the catalog into the state it names.

    Takes a session rather than opening one, so the API test suite can drive
    this against its own fixture database instead of standing up a second one.
    ``run`` below is what opens a session for a real command.

    ``clock`` is the run's **base** clock — the one *now* every backdated write
    is measured from — and it is read exactly once. A run that read the wall
    clock twice could straddle midnight between two accounts and move an age by a
    day for reasons having nothing to do with the fixture.
    """

    settings = settings or get_settings()
    now = (clock or build_clock()).now()
    photos = photos or build_photo_storage(settings)
    return tuple(
        [
            await _seed_account(
                session, account, now=now, settings=settings, photos=photos
            )
            for account in ACCOUNTS + RELATIONSHIP_ACCOUNTS
        ]
    )


async def _seed_account(
    session: AsyncSession,
    account: SeedAccount,
    *,
    now: Instant,
    settings: Settings,
    photos: PhotoStorage,
) -> SeededAccount:
    """One account, written on the clock its own profile names.

    **The whole account is written at that instant, not only the profile.** An
    account whose profile was committed forty days ago and whose registration
    happened a second ago is a history no player has; and the gate that reads
    ``profile_created_at`` is not the only thing a stale instant is visible in —
    the index's own liveness reads one too.
    """

    use_cases = _build(
        session,
        clock=_clock_for(account, now),
        settings=settings,
        photos=photos,
    )
    player_id, registered = await _ensure_registered(
        use_cases, email=account.email, name=account.name, nickname=account.nickname
    )
    scenarios = tuple(
        [
            await _ensure_scenario(use_cases, player_id, account, scenario)
            for scenario in account.scenarios
        ]
    )
    await _refuse_a_name_that_lies(use_cases, player_id, account)
    committed = await _ensure_profile(use_cases, player_id, account.profile)
    return SeededAccount(
        account=account,
        player_id=player_id,
        registered=registered,
        scenarios=scenarios,
        committed_profile=committed,
    )


def _clock_for(account: SeedAccount, now: Instant) -> Clock:
    """The clock this account is written on.

    An account with no profile is written **now**: it has no age to state, and
    backdating one would be inventing a fact the catalog never claimed.
    """

    if account.profile is None:
        return FixedClock(at=now)
    return days_before(now, account.profile.committed_days_ago)


async def _ensure_registered(
    use_cases: _UseCases, *, email: str, name: str, nickname: str
) -> tuple[UUID, bool]:
    """Register this address and name the account, or find the one already there.

    Takes the values rather than an account, because a named account and a
    cohort member are the same registration: both are an address derived from a
    handle, and two copies of this function would be two places for *is it
    already there* to be answered differently.

    **Two acts, as a player performs them** (``docs/adr/0171`` §2): sign-up is
    credentials only and the naming is its own use case, so a seeded account
    has the two events a real one has. The naming is asked on every run — it
    is the act's own idempotence that makes a second run write nothing, an
    unchanged re-naming recording no event — so a pool that dealt an account a
    different name is corrected rather than left as the first run wrote it.
    """

    existing = await use_cases.users.get_by_email(email)
    if existing is None:
        user = await use_cases.register.execute(
            RegisterUserCommand(
                email=email,
                password=SEED_PASSWORD,
                # A seeded account attests like any other, because it is
                # registered through the aggregate rather than around it
                # (``docs/adr/0029``). The claim is the fixture's, made on behalf
                # of a player who does not exist, and it never leaves a
                # developer's machine.
                adult_attested=True,
            )
        )
        player_id, registered = user.id, True
    else:
        player_id, registered = existing.id, False

    await use_cases.name.execute(
        NameUserCommand(user_id=player_id, name=name, nickname=nickname)
    )
    return player_id, registered


async def _ensure_profile(
    use_cases: _UseCases, player_id: UUID, profile: SeedProfile | None
) -> bool:
    """Commit onboarding's second part, and clear the week where one is named.

    Idempotent through the commit's **own** key rather than through a probe
    beside it: the same idempotency key twice is the same commit, so a second
    seed run hands back the first profile unchanged and creates nothing. The
    key is derived from the player id, which is stable for the life of the
    database and different on a fresh one — the same promise the assessments
    above make.

    **A cleared week is a commit followed by an edit**, and it has to be: the
    commit refuses an empty grid because the floor binds the answer a player is
    *asked* for, while ``ChangeAvailability`` accepts one because clearing a week
    afterwards is a legal edit. Reaching a blank week any other way would be
    reaching it by a path no player has.
    """

    if profile is None:
        return False

    result = await use_cases.commit_profile.execute(
        CommitPlayerProfileCommand(
            player_id=player_id,
            idempotency_key=f"seed-profile-{player_id}",
            social_tag_ids=list(profile.social_tag_ids),
            photo_ids=list(profile.photo_ids),
            availability=list(profile.availability),
            latitude=profile.latitude,
            longitude=profile.longitude,
            search_radius_km=profile.search_radius_km,
            gender=profile.gender,
            gender_preference=profile.gender_preference,
            proposals_opt_in=profile.proposals_opt_in,
            consent_copy_version=SEED_CONSENT_COPY_VERSION,
            consent_surface=ConsentSurface.ONBOARDING,
        )
    )
    for sport, intent in profile.intents:
        await use_cases.declare_intent.execute(
            DeclarePlayIntentCommand(
                player_id=player_id,
                sport=sport,
                intent=intent,
                surface=profile.intent_surface,
            )
        )
    if profile.clear_the_week and result.profile.availability.slots:
        await use_cases.change_availability.execute(
            ChangeAvailabilityCommand(player_id=player_id, availability=[])
        )
    return result.created


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
            return SeededScenario(
                scenario=scenario,
                assessment_id=await _rate(
                    use_cases,
                    player_id,
                    account.slug,
                    scenario.sport,
                    scenario.answers,
                ),
                created=True,
            )

        case _:
            exhaustive(scenario)


async def _rate(
    use_cases: _UseCases,
    player_id: UUID,
    handle: str,
    sport: Sport,
    policy: AnswerPolicy,
) -> UUID:
    """Answer the questionnaire to its stop, then ask for the rating.

    Two moments, not one (``docs/adr/0020``): the engine stopping is a fact about
    the transcript, and ``CompleteAssessment`` is what makes the rating. A seed
    that stopped at the stop would leave a run nobody can tell from
    ``assessment-in-progress`` — which is a state the catalog already has an
    account for.
    """

    start = await use_cases.create.execute(
        CreateAssessmentCommand(player_id=PlayerId(player_id), sport=sport)
    )
    step = await _answer_until_the_engine_stops(
        use_cases, player_id, handle, sport, policy, start.step
    )
    await use_cases.complete.execute(
        CompleteAssessmentCommand(player_id=player_id, assessment_id=step.assessment_id)
    )
    return step.assessment_id


async def _answer_until_the_engine_stops(
    use_cases: _UseCases,
    player_id: UUID,
    handle: str,
    sport: Sport,
    policy: AnswerPolicy,
    step: AssessmentStep,
) -> AssessmentStep:
    """Answer whatever is outstanding until nothing is.

    The loop reads the step the server just returned rather than counting
    questions, because how many a run gets is the engine's decision and changes
    with the answers — a strong player earns an extra demonstration, a beginner
    is finished after one.

    ``handle`` is *who is answering* — an account's slug or a cohort member's
    handle — and it is the first third of the draw key. A name rather than an id
    because the id is minted by the write path and a fresh database mints a
    different one, which would make a member's answers move between databases.
    """

    answered = 0
    while step.question is not None:
        if answered >= MAX_ANSWERS:
            raise SeedFailed(
                f"'{handle}' has answered {answered} "
                f"{sport.value} questions and the questionnaire is "
                f"still going. The engine no longer stops for this answer "
                f"policy, so the seed is refusing to keep going rather than "
                f"hang."
            )
        step = await use_cases.submit.execute(
            SubmitAnswerCommand(
                player_id=player_id,
                assessment_id=step.assessment_id,
                question_id=step.question.id,
                # **Keyed on who is answering and what they were asked**, never
                # on how far into the run this is: an engine that inserted one
                # question would otherwise reshuffle every later answer for
                # every member, and the band histogram would move for a reason
                # having nothing to do with skill.
                option_id=policy.option_id_for(
                    step.question, drawn_for=answer_key(handle, sport)
                ),
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


# ---------------------------------------------------------------------------
# The cohort — a population, on the same use cases and its own clocks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeededMember:
    """One cohort member after the run, and what this run had to build."""

    member: CohortMember
    player_id: UUID
    registered: bool
    committed_profile: bool
    #: The sports this **run** sat the questionnaire for. Empty on a second run,
    #: which is what makes ``already_present`` mean what it says: a member whose
    #: profile was there and whose rating was not is a half-written member, and
    #: reading only the profile would report them as untouched.
    rated: tuple[Sport, ...]
    #: Which of ``docs/adr/0138``'s three answers this member's photograph is
    #: declared to carry, or ``None`` for the great majority who hold none. A
    #: statement about the **declaration**, printed on the report so a developer
    #: reads which card to look at — what the card actually draws is asserted in
    #: ``app/seeds/screens.py`` off a real read.
    photograph: str | None = None

    @property
    def already_present(self) -> bool:
        return not self.registered and not self.committed_profile and not self.rated


async def seed_the_cohort(
    session: AsyncSession,
    *,
    cohort: Cohort = COHORT,
    clock: Clock | None = None,
    settings: Settings | None = None,
    photos: PhotoStorage | None = None,
    photographs: bool = True,
) -> tuple[SeededMember, ...]:
    """Write the whole population, each member on the clock their row names.

    Every write is the same use case a request runs — a registration, a rating
    earned by answering the questionnaire, a profile commit, a declaration per
    sport. There is no faster path and there is deliberately none: a member
    written any other way is a member whose Level nothing produced, whose
    transcript no review screen can render, and whose index row is a fold of
    events that were never appended.
    """

    settings = settings or get_settings()
    now = (clock or build_clock()).now()
    photos = photos or build_photo_storage(settings)
    return tuple(
        [
            await _seed_member(
                session,
                member,
                now=now,
                settings=settings,
                photos=photos,
                photographs=photographs,
            )
            for member in cohort.members
        ]
    )


async def _seed_member(
    session: AsyncSession,
    member: CohortMember,
    *,
    now: Instant,
    settings: Settings,
    photos: PhotoStorage,
    photographs: bool,
) -> SeededMember:
    use_cases = _build(
        session,
        clock=days_before(now, member.committed_days_ago),
        settings=settings,
        photos=photos,
    )
    player_id, registered = await _ensure_registered(
        use_cases, email=member.email, name=member.name, nickname=member.nickname
    )
    rated = tuple(
        [
            sport
            for sport in member.sports
            if await _ensure_member_rated(use_cases, player_id, member, sport)
        ]
    )
    uploaded = (
        await _ensure_photograph(use_cases, player_id, member)
        if photographs
        else ()
    )
    committed = await _ensure_profile(
        use_cases, player_id, _profile_of(member, uploaded)
    )
    return SeededMember(
        member=member,
        player_id=player_id,
        registered=registered,
        committed_profile=committed,
        rated=rated,
        photograph=member.photograph,
    )


async def _ensure_photograph(
    use_cases: _UseCases, player_id: UUID, member: CohortMember
) -> tuple[UUID, ...]:
    """Upload the photograph this member is declared to hold, or none.

    **Idempotent through a probe and not through a key, which is the one place
    this run departs from ``_ensure_profile`` beside it.** A commit is a request
    that happens once and says so with an idempotency key; an upload has none —
    it mints an id and stores bytes, and a second one is a second object nobody
    references. So the question asked is *has this member a profile yet*, and a
    member who has one keeps whatever photograph that commit carried: the photo
    list is settled at the commit and there is no use case in this repository
    that adds one afterwards.

    **The reviewer is the one the fixture declares**, on ``FixedClock``'s
    argument: ``PhotoReview`` is a port, the upload is the same use case a
    request runs, and what a check concluded about a synthetic image is a thing
    this fixture has to *choose* rather than discover — a workbench that asked
    the real sidecar would exhibit whichever verdicts that model happened to
    reach on a flat square.
    """

    declared = member.declared_verdict
    if declared is None:
        return ()
    if await use_cases.profiles.load(player_id) is not None:
        return ()

    upload = UploadPhoto(
        storage=use_cases.photos,
        # Real, and deliberately: re-encoding is what strips EXIF, and a faked
        # transcoder would fake away the one thing the upload path is for.
        transcoder=build_image_transcoder(),
        review=DeclaredPhotoReview(declared),
        clock=use_cases.clock,
        # Never read: the run keeps no URL and writes none anywhere. It is
        # passed because the use case a request runs takes it, and one
        # assembled with a hole in it is not the one a request runs.
        url_valid_for_minutes=SEED_PHOTO_URL_MINUTES,
    )
    uploaded = await upload.execute(
        UploadPhotoCommand(
            owner_id=player_id,
            data=an_image(),
            declared_media_type=SEED_IMAGE_MEDIA_TYPE,
        )
    )
    return (uploaded.ref.photo_id,)


def _profile_of(
    member: CohortMember, photographs: tuple[UUID, ...] = ()
) -> SeedProfile:
    """A member's row, as the profile axis the catalog already spells.

    One shape for both layers rather than two commit paths: the named accounts
    and the population answer onboarding's second part identically, because a
    developer signing in as either sees a profile the same code wrote.

    ``photographs`` is the one field a member's row cannot state, and the reason
    is that a photo id is **minted by the upload**: the catalog spells *which
    photographs*, this run spells *which ids they came back as*, and a committed
    id would be an id the write path does not own.
    """

    return SeedProfile(
        availability=member.availability,
        photo_ids=photographs,
        social_tag_ids=member.tags,
        search_radius_km=member.radius_km,
        gender=Gender(member.gender),
        gender_preference=GenderPreference(member.gender_preference),
        proposals_opt_in=member.proposals_opt_in,
        committed_days_ago=member.committed_days_ago,
        intents=tuple(
            (Sport(sport), PlayIntent(intent)) for sport, intent in member.intents
        ),
        latitude=member.latitude,
        longitude=member.longitude,
    )


async def _ensure_member_rated(
    use_cases: _UseCases, player_id: UUID, member: CohortMember, sport: Sport
) -> bool:
    """The questionnaire, answered to its stop, unless it already has been.

    Probed exactly as a named account's rated scenario is: by loading the pair's
    first attempt under its derived id, because *completed* and *never started*
    are both closed to every finder.
    """

    existing = await _first_attempt(use_cases, player_id, sport)
    if existing is not None and existing.is_completed:
        return False
    # **No ``RatingClaim`` anywhere here, and that is the point.** A named
    # account promises one band and one position inside it; a member's rating is
    # claimed by the population's *histogram*, and a per-member claim would be a
    # promise the generator made about the engine's own answer.
    await _rate(use_cases, player_id, member.handle, sport, member.answers)
    return True


# ---------------------------------------------------------------------------
# The three clocks a cohort fails on
# ---------------------------------------------------------------------------


def _readers(
    session: AsyncSession,
) -> tuple[PlayerProfileRepository, SkillRatingRepository]:
    """The two repositories the refusals read the **stored** answer through.

    Spelled once because both refusals ask the same kind of question of the same
    database, and two copies of this wiring would be two chances for one of them
    to read through a store the other has since passed.
    """

    event_store = build_domain_event_store(session)
    events = build_event_publisher(session)
    return (
        build_player_profile_repository(event_store=event_store, events=events),
        build_skill_rating_repository(event_store=event_store, events=events),
    )


async def refuse_a_cohort_that_has_aged_out(
    session: AsyncSession,
    seeded: Sequence[SeededMember],
    *,
    now: Instant,
) -> None:
    """**The calendar.** A cohort with no newcomers left fails, by name.

    The dates are relative to the run that wrote them and a re-run re-commits
    nothing, so a fortnight on every seeded newcomer has aged out **at once**.
    Left alone, a developer building the newcomer path against a population with
    no newcomers sees nothing wrong on the screen — which is precisely the
    failure ``_refuse_a_name_that_lies`` exists to refuse, one layer up.

    The age is read off the **stored** profile rather than off the declaration,
    for that check's own reason: the row written a month ago is the one nobody
    would otherwise look at.
    """

    profiles, _ = _readers(session)
    expected = [entry for entry in seeded if entry.member.is_a_newcomer]
    if not expected:
        raise SeedFailed(
            "the cohort declares no newcomer at all. ADR-0113's gate changes on "
            "newness, and a gate with one side present cannot be seen."
        )

    aged: list[tuple[str, int]] = []
    for entry in expected:
        profile = await profiles.load(entry.player_id)
        if profile is None:
            raise SeedFailed(
                f"'{entry.member.handle}' holds no profile, though the run "
                f"committed one."
            )
        age = age_in_days(now, profile.created_at)
        if age >= NEWCOMER_WINDOW_DAYS:
            aged.append((entry.member.handle, age))

    if aged:
        oldest = max(age for _, age in aged)
        names = ", ".join(f"{handle} ({age} days)" for handle, age in sorted(aged))
        raise SeedFailed(
            f"{len(aged)} of the cohort's {len(expected)} declared newcomers "
            f"have aged out of ADR-0113's {NEWCOMER_WINDOW_DAYS}-day window — "
            f"the oldest by {oldest - NEWCOMER_WINDOW_DAYS} days: {names}. The "
            f"dates are relative to the run that wrote them and a re-run "
            f"re-commits nothing, so this database is now a population with no "
            f"newcomers in it. Drop it and seed again "
            f"(`make down -v && make up && make seed`)."
        )


async def refuse_a_histogram_that_has_moved(
    session: AsyncSession, seeded: Sequence[SeededMember]
) -> None:
    """**The engine.** The band histogram, checked against stored ratings.

    A range per band and never a μ: a μ claim pins the engine, and a retune that
    moved every level by a tenth would fail a fixture whose only complaint is
    that the engine changed. What a band claim catches is what matters to a
    screen — a band that has emptied is a state nobody can reach any more, and a
    band that has swallowed the population is a pool of identical cards.
    """

    _, ratings = _readers(session)
    counted: dict[str, int] = {band: 0 for band in BAND_HISTOGRAM}
    for entry in seeded:
        for rating in await ratings.find_all_for(player_id=entry.player_id):
            counted[rating.band_name] = counted.get(rating.band_name, 0) + 1

    complaints = [
        f"{band}: {counted.get(band, 0)}, and the cohort promises {low}–{high}"
        for band, (low, high) in BAND_HISTOGRAM.items()
        if not low <= counted.get(band, 0) <= high
    ]
    unpromised = sorted(set(counted) - set(BAND_HISTOGRAM))
    if unpromised:
        complaints.append(
            f"and {', '.join(unpromised)} is a band the histogram does not name"
        )
    if complaints:
        raise SeedFailed(
            "the cohort no longer produces the population it promises — "
            + "; ".join(complaints)
            + ". The archetypes choose answers and the engine chooses bands, so "
            "this is the engine having moved under a fixture that was built on "
            "where it used to be. Either the archetypes or the histogram is now "
            "wrong, and both are in `app/seeds/cohort.py`."
        )


# ---------------------------------------------------------------------------
# The command
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedReport:
    """Everything one run did, in one value.

    One object rather than a tuple of two, because the report and the assertions
    both need the run's own *now* — the instant every age in it was measured
    against — and a caller re-reading the clock to get it would be measuring
    against a different one.
    """

    accounts: tuple[SeededAccount, ...]
    members: tuple[SeededMember, ...]
    now: Instant
    screens: tuple[str, ...] = ()
    #: The eleven relationships, the inboxes they left behind, and the two
    #: costs. ``None`` only where a caller drove the two populations without the
    #: layer above them — the API suite does, and it asserts no screen.
    pairs: SeededPairs | None = None
    #: The played history, and the pairs it spent. ``None`` on the same callers
    #: and for the same reason.
    played: SeededGames | None = None
    #: The four arranged-and-never-played games, and the plans on them.
    #: ``None`` on the same callers and for the same reason as the two above.
    plans: SeededPlans | None = None
    #: The loop's own states — a game at every moment of its life, the two courts
    #: sent for the ends they reach, and the fill — with the claims read back off
    #: the screens they are for. ``None`` on the same callers and for the same
    #: reason as the layers above.
    loop: SeededLoop | None = None
    #: The rooms the seeded acceptances earned, once the outbox was delivered.
    #: ``None`` on the callers that drive the populations without the layers
    #: above them, exactly as the two above are.
    rooms: SeededRooms | None = None
    #: The cards those evenings left behind, and what the published fold makes
    #: of them. ``None`` on the same callers and for the same reason.
    opinions: SeededOpinions | None = None
    #: Whether the object store answered at all. A photograph is the one thing
    #: the seed writes that lives outside the database, so it is the one thing a
    #: run can be missing for a reason that is nobody's fixture.
    photographs: bool = True


async def run(settings: Settings | None = None) -> SeedReport:
    """Open a connection of this command's own, seed, assert, and close it.

    The guard is re-checked against the settings actually used. Importing this
    package already checked the process's, and this is the same question asked of
    the object that decides which database is about to be written to — a caller
    that constructs its own settings does not get to skip it.

    The engine is created and disposed here rather than taken from
    ``init_engine``: a seed run is not the API process, and an engine it owns
    outright is one it can close on the way out.

    **Both layers on every run, and the assertions after both.** The run that
    matters is the one that creates nothing, because that is where drift shows —
    an engine that has been retuned, a ruleset whose floor has moved, and a
    calendar that has walked past the newcomer window all announce themselves on
    a run with nothing to do.
    """

    settings = settings or get_settings()
    refuse_unless_seedable(settings)

    clock = build_clock()
    now = clock.now()
    # **One store for the whole run**, so the upload that mints a photo id and
    # the commit that re-validates it are asking one object the same question.
    photos = build_photo_storage(settings)
    photographs = await the_store_answers(photos)
    engine = create_engine(settings)
    try:
        session_factory = build_background_session_factory(engine)
        async with session_factory() as session:
            accounts = await seed(
                session,
                clock=FixedClock(at=now),
                settings=settings,
                photos=photos,
            )
            members = await seed_the_cohort(
                session,
                clock=FixedClock(at=now),
                settings=settings,
                photos=photos,
                photographs=photographs,
            )
            await refuse_a_cohort_that_has_aged_out(session, members, now=now)
            await refuse_a_histogram_that_has_moved(session, members)
        # **The played history first, and the order is load-bearing.** A game is
        # a challenge every seat accepted, so each one spends a pair for good;
        # the relationship layer then plans its inboxes against a world those
        # games are already in, rather than discovering half way through that an
        # organiser it counted on can no longer see anybody.
        played = await write_the_played_history(
            session_factory, settings=settings, now=now, photos=photos
        )
        # **After the games and before anything reads a record**, because a card
        # is drawn for a court that is over: nothing here arranges an evening,
        # and every rating it writes is about one the layer above just wrote.
        # It spends no pair and runs no search, so its position relative to the
        # relationships is free — it sits here because it belongs to the
        # evenings rather than to the inboxes.
        opinions = await write_what_players_said(session_factory, now=now)
        # **After both populations and before every claim.** An edge is a real
        # search or deal run as the sender, so it needs everybody in the index —
        # and the claims are read off what the edges made true.
        pairs = await write_the_relationships(
            session_factory, settings=settings, now=now, photos=photos
        )
        # **After the relationships and before the delivery.** A plan needs a
        # game still inside its entry window and every other layer's games are
        # played, so this one arranges four more and stops — and it has to run
        # before the outbox is drained, so that the four system lines it writes
        # reach the rooms in the same pass everything else does. It holds a
        # delivery barrier of its own as well, because a plan line is hung on
        # the room its challenge opened and that opening is an earlier event.
        plans = await write_the_plans(
            session_factory, settings=settings, now=now
        )
        # **After the plans and before the delivery**, on the plans layer's own
        # reason twice over: the cards this layer reaches are the ones no other
        # layer draws, and the lines it writes have to reach their rooms in the
        # same pass everything else's do.
        written = await write_the_loop(
            session_factory, settings=settings, now=now
        )
        # **After every layer that writes and before the screens.** A room is
        # *told* through the outbox by contexts that do not know it exists
        # (``docs/adr/0146`` §5), so nothing above this line opened one — the
        # acceptances, the completions and the *we played*s are all sitting in
        # the queue. Delivering here is the same barrier the candidate index's
        # tick is, for the same reason: the assertions read the real path, and
        # the real path has a poller in front of it.
        rooms = await open_the_rooms(
            session_factory, settings=settings, now=now
        )
        # **After the rooms, because half its claims are about them.** A room is
        # told through the outbox and an ended one is destroyed by a sweep, so a
        # claim about which lines a standing room carries has to be made on the
        # far side of both.
        loop = SeededLoop(
            written=written,
            claims=await assert_the_loop(
                session_factory, settings=settings, now=now
            ),
        )
        screens = await assert_the_screens(
            session_factory,
            settings=settings,
            now=now,
            pairs=pairs,
            photographs=photographs,
            photos=photos,
        )
        return SeedReport(
            accounts=accounts,
            members=members,
            now=now,
            screens=screens,
            pairs=pairs,
            played=played,
            plans=plans,
            rooms=rooms,
            loop=loop,
            opinions=opinions,
            photographs=photographs,
        )
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


#: Said on the report and not only in a docstring, for the reason the ruleset
#: diff says its own disclaimer on its own report: a fixture that stands for
#: nothing outside itself has to say so where somebody reading its output will
#: see it, or the numbers get quoted.
COHORT_DISCLAIMER = (
    "The cohort is a development workbench. It is chosen so that every Play "
    "screen state is reachable, it stands for nothing outside itself, and it "
    "describes no real market — no rate here is evidence about anything. The "
    "comparator corpus is docs/specs/matchmaking/ruleset-diff/, and it answers "
    "a different question."
)


def report(run_report: SeedReport) -> list[str]:
    """The run, as lines a developer reads — address, password, state, id."""

    seeded = run_report.accounts
    lines = [
        f"Seeded {len(seeded)} account(s) and {len(run_report.members)} cohort "
        f"member(s). Password for all of them: {SEED_PASSWORD}",
        "",
    ]
    for entry in seeded:
        state = "already present" if entry.already_present else "created"
        lines.append(f"  {entry.account.email}  [{state}]")
        lines.append(f"      {entry.account.description}")
        lines.append(f"      player {entry.player_id}")
        if entry.account.profile is not None:
            days = entry.account.profile.committed_days_ago
            standing = "newcomer" if days < NEWCOMER_WINDOW_DAYS else "settled"
            lines.append(
                f"      profile committed {days} day(s) ago · {standing}"
            )
        for seeded_scenario in entry.scenarios:
            lines.append(
                f"      {seeded_scenario.scenario.sport.value} "
                f"{_state_of(seeded_scenario.scenario)} · "
                f"assessment {seeded_scenario.assessment_id}"
            )
    lines.extend(["", *_cohort_lines(run_report.members)])
    if run_report.played is not None:
        lines.extend(["", *_played_lines(run_report.played)])
    if run_report.opinions is not None:
        lines.extend(["", *_opinion_lines(run_report.opinions)])
    lines.extend(["", *_photograph_lines(run_report.members)])
    if run_report.pairs is not None:
        lines.extend(["", *_relationship_lines(run_report.pairs)])
    if run_report.plans is not None:
        lines.extend(["", *_plan_lines(run_report.plans)])
    if run_report.rooms is not None:
        lines.extend(["", *_room_lines(run_report.rooms)])
    if run_report.loop is not None:
        lines.extend(["", *_loop_lines(run_report.loop)])
    if run_report.screens:
        lines.extend(["", "The screens, read as the protagonist:"])
        lines.extend(f"  {line}" for line in run_report.screens)
    lines.extend(["", COHORT_DISCLAIMER])
    costs = list(run_report.pairs.costs if run_report.pairs else ())
    costs.extend(run_report.played.costs if run_report.played else ())
    costs.extend(plan_costs(run_report.plans) if run_report.plans else ())
    costs.extend(loop_costs(run_report.loop) if run_report.loop else ())
    if not run_report.photographs:
        costs.append(
            "the object store did not answer, so this run seeded no "
            "photograph at all and the three verdicts a card can draw are "
            "unreachable in this database. That is the store and not the "
            "fixture — bring MinIO up and seed a fresh database, because a "
            "photo list is settled at the profile commit and nothing adds one "
            "afterwards."
        )
    if costs:
        lines.append("")
        lines.extend(f"Cost: {cost}" for cost in costs)
    return lines


def _loop_lines(loop: SeededLoop) -> list[str]:
    """What the loop's own layer wrote, and what the screens then drew.

    **Written and claimed in one block**, unlike every other layer: the two halves
    run either side of the delivery — the rooms have to be told before a line can
    be read back — and printing them apart would put the claims a screenful away
    from the rows that reach them.
    """

    return [
        "The loop's own states — a game at every moment of its life:",
        *(f"  {line}" for line in loop.written.games),
        *(f"  {line}" for line in loop.written.courts),
        *(f"  {line}" for line in loop.claims),
    ]


def _room_lines(rooms: SeededRooms) -> list[str]:
    """The rooms the delivery opened, the ones the sweep took away, and the one
    shape this fixture does not reach.

    **The gap is on the report rather than in a docstring**, on the rule the two
    relationship costs already follow: a fixture that quietly reached three of
    four shapes reads as having reached four, and the person it misleads is the
    one about to build the screen.
    """

    return [
        "The rooms, once the outbox was delivered and the ended ones swept:",
        f"  {rooms.delivered} event(s) delivered · {rooms.said} message(s) said "
        f"· {rooms.swept.destroyed} room(s) destroyed",
        *(f"  {line}" for line in rooms.rooms),
        "  not reached · a room carrying every system-line code. It needs a "
        "`SeatsInvited`, and nothing here performs a fill — which would cost a "
        "real search that seats somebody new and move the gate histogram this "
        "run asserts.",
    ]


def _played_lines(played: SeededGames) -> list[str]:
    """What the platform has watched this cohort do, one line per game.

    Not a claim — the claims are read off a real card in
    ``app/seeds/screens.py`` — and it names the members so the card is findable,
    which is the question a developer opens the report with.
    """

    return [
        "The played history:",
        *(f"  {one.line}" for one in played.games),
    ]


def _plan_lines(plans: SeededPlans) -> list[str]:
    """The four card states, each read back off ``GET /plans``' own use case.

    **Nought is a row on this list**, and it is the one that reads oddly: a plan
    at no slots is a game with *no plan*, so the line says so rather than
    printing three empty values a client can never be sent.
    """

    return [
        "The plans, on games nobody has played:",
        *(f"  {line}" for line in plans.plans),
    ]


def _opinion_lines(opinions: SeededOpinions) -> list[str]:
    """The cards that were answered, and what the record will print off them.

    **The second half is read back and not computed**, which is the only reason
    it is worth printing: the figure a developer sees here is the one
    ``sportsmanship`` publishes when a record is opened, so a fold that started
    disagreeing with the fixture would show up in this section rather than on a
    screen nobody looked at.

    And the figure is what a **reader** of that record is shown. The subject is
    shown a coarse band and no count at all (``docs/adr/0158``) — so signing in
    as one of these people and opening your own sheet is *not* how to check this
    section; opening theirs from somebody else's pool is.
    """

    return [
        "What other players said:",
        *(f"  card · {line}" for line in opinions.cards),
        *(f"  published · {line}" for line in opinions.published),
    ]


def _photograph_lines(members: Sequence[SeededMember]) -> list[str]:
    """Who holds a photograph, and which of the three answers it carries.

    A section of its own rather than a tail on the games, because they are two
    fixtures: one is what the platform watched these people do and the other is
    what a check concluded about an image. What each one is **declared** to
    carry is here; what a card actually draws is asserted off a real read.
    """

    return [
        "The photographs, and the verdict each is declared to carry:",
        *(
            f"  photo · {entry.member.handle} · {entry.photograph}"
            for entry in members
            if entry.photograph is not None
        ),
    ]


def _relationship_lines(pairs: SeededPairs) -> list[str]:
    """The eleven, one line each, with what each one promises beside it.

    **The claim is printed where the address is**, because a developer signing in
    as `said-yes-to-you` is asking what they should expect to see, and an account
    named for a pair answers that only if the pair's own promise is beside it.
    """

    lines = [f"The eleven relationships, with {PROTAGONIST.slug}:"]
    for edge in pairs.edges:
        lines.append(f"  {edge.relationship.account.email}")
        lines.append(f"      {edge.line}")
        lines.append(f"      claims: {edge.relationship.claim}")
    lines.extend(f"  {line}" for line in pairs.inboxes)
    lines.append(f"  {pairs.withdrawn}")
    lines.append(f"  {pairs.half_built.sent}")
    lines.append(f"  {pairs.half_built.mutual_born}")
    return lines


def _cohort_lines(members: Sequence[SeededMember]) -> list[str]:
    """The population, one line per ring rather than one per member.

    Forty addresses on a terminal is a wall a developer scrolls past; what they
    actually need is *how many, where, and how many of them are new* — and the
    handle carries the ring, so a member's own line is readable off any card
    they appear on.
    """

    created = sum(1 for entry in members if not entry.already_present)
    lines = [
        f"Cohort: {len(members)} member(s), {created} created this run.",
    ]
    by_ring: dict[str, list[SeededMember]] = {}
    for entry in members:
        by_ring.setdefault(entry.member.ring, []).append(entry)
    for ring, entries in sorted(by_ring.items()):
        newcomers = sum(1 for entry in entries if entry.member.is_a_newcomer)
        opted_out = sum(1 for entry in entries if not entry.member.proposals_opt_in)
        lines.append(
            f"  ring {ring}: {len(entries)} member(s), {newcomers} inside the "
            f"newcomer window, {opted_out} opted out of proposals"
        )
    return lines
