"""What ``player_record`` asks of the platform, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/player_record_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red.

**This context stores nothing**, so every arrangement here is made through
somebody else's aggregate — a profile committed, a group joined, a game played
— and never an ``INSERT`` (``docs/adr/0029``). That is not ceremony: what these
ports answer is folds and queries owned by other contexts, and the only honest
way to exercise one is to make the history it reads.

**The rule the disclosure suite is written around is that absence is silence.** A
pair with nothing between them answers ``False``, not an error — because the
caller turns that answer into the one refusal this route has, and any other
spelling would make that refusal a different one.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_administrator_repository,
    build_block_repository,
    build_booking_repository,
    build_club_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_group_repository,
    build_skill_rating_repository,
    build_sportsmanship_ledger,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    band_for,
    confidence_percent,
    likely_range,
)
from app.modules.games.domain.results import Score, SetScore
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.bootstrap.player_record_demands import (
    PLAYER_RECORD_DEMANDS,
    PLAYER_RECORD_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import ReliabilityStrand, SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.administrators.domain.administrator import Administrator
from app.modules.blocks.domain.block import Block
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.value_objects import (
    City,
    ClubDetails,
    ClubName,
    District,
    MapPoint,
    OfferedSports,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupCode,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)
from app.modules.player_profile.domain.weekly_hours import Window
from app.modules.player_record.domain.ports import (
    BlocksByTheReader,
    PriorDisclosure,
    RecordGates,
    RecordPhotoLink,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
)
from app.modules.player_record.domain.record import (
    OpponentVariety,
    WhatPlayersSaid,
)
from app.modules.sportsmanship.domain.card import (
    SettledCourt,
    SportsmanshipCard,
    StarsGiven,
)
from app.modules.player_score.domain.strands import (
    PUBLISHED_WEIGHTS,
    out_of_a_hundred,
)
from app.modules.users.domain.value_objects import Email, Name
from app.shared.ids import new_uuid

SPORT = Sport.PADEL


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _now() -> Instant:
    return instant(datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# The register checks itself
# ---------------------------------------------------------------------------


def test_every_demand_has_at_least_one_implementation():
    """A port added in a hurry would otherwise look contracted while nothing on
    earth ran against it."""

    unregistered = [
        port.__name__
        for port in PLAYER_RECORD_DEMANDS
        if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_is_of_a_declared_demand():
    """And the other direction, so the two lists check each other."""

    stray = [
        one.name
        for one in PLAYER_RECORD_IMPLEMENTATIONS
        if one.port not in PLAYER_RECORD_DEMANDS
    ]

    assert stray == []


@pytest.mark.parametrize(
    "implementation",
    [
        pytest.param(one, id=f"{one.port.__name__}:{one.name}")
        for one in PLAYER_RECORD_IMPLEMENTATIONS
    ],
)
def test_every_implementation_satisfies_the_protocol_it_registered_under(
    implementation, session
):
    """Structural, so a method renamed on one side is red here rather than an
    ``AttributeError`` on somebody's record sheet."""

    assert isinstance(implementation.build(session), implementation.port)


# ---------------------------------------------------------------------------
# PriorDisclosure — where has this reader already been shown this person
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PriorDisclosure))
async def test_a_pair_with_nothing_between_them_disclose_nothing(
    implementation, session
):
    """**The answer almost everybody gets**, and it must be ``False`` rather
    than an error: the caller turns it into the one refusal this route has."""

    disclosure = implementation.build(session)

    assert (
        await disclosure.discloses(reader_id=new_uuid(), subject_id=new_uuid())
        is False
    )


async def test_a_game_they_both_played_discloses_for_ever_both_ways(session):
    """An evening two people were on a court for does not stop having happened,
    so there is no window here and no standing test."""

    a, b = new_uuid(), new_uuid()
    starts = instant(datetime.now(timezone.utc) - timedelta(days=400))
    game = Game.planned(
        game_id=new_uuid(),
        # A booked game is filed under its booking's id.
        challenge_id=new_uuid(),
        sport=SPORT,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=a),
                Seating(side=GameSide.B, player_id=b),
            )
        ),
        occurred_at=instant(starts - timedelta(days=2)),
        starts_at=starts,
    )
    await build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(game)
    await session.commit()

    disclosure = _disclosure("GamesTheyPlayed", session)

    assert await disclosure.discloses(reader_id=a, subject_id=b) is True
    assert await disclosure.discloses(reader_id=b, subject_id=a) is True
    assert await disclosure.discloses(reader_id=a, subject_id=new_uuid()) is False


async def _a_club(session) -> UUID:
    """A club, through its own aggregate — a group has a home club."""

    club = Club.register(
        club_id=new_uuid(),
        details=ClubDetails(
            name=ClubName("Ogrody 33"),
            district=District("Grzegórzki"),
            city=City("Kraków"),
            sports=OfferedSports.of({SPORT}),
            point=MapPoint(latitude=50.06, longitude=19.95),
        ),
        occurred_at=datetime.now(timezone.utc),
    )
    await build_club_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(club)
    return club.id


async def _a_group(session, owner: UUID, *others: UUID, policy=JoinPolicy.ANYONE):
    """A player group at a club, and whoever else tapped *Join* — each made
    through its own aggregate, the club first because a group has a home club."""

    now = datetime.now(timezone.utc)
    events = build_event_publisher(session)
    group = Group.create_player_group(
        group_id=new_uuid(),
        name=GroupName("Czwartkowy padel"),
        home_club_id=await _a_club(session),
        join_policy=policy,
        owner_id=owner,
        code=GroupCode("k7pq2mxa"),
        occurred_at=now,
    )
    for other in others:
        group.join(other, occurred_at=now)
    await build_group_repository(
        session, event_store=build_domain_event_store(session), events=events
    ).save(group)
    await session.commit()


async def test_a_group_they_are_both_in_discloses_both_ways(session):
    """Members lists everybody in the group to everybody in it, so the group
    has shown each of them to the other."""

    owner, member = new_uuid(), new_uuid()
    await _a_group(session, owner, member)

    disclosure = _disclosure("GroupsTheyShare", session)

    for reader, subject in ((owner, member), (member, owner)):
        assert await disclosure.discloses(reader_id=reader, subject_id=subject)


async def test_a_join_request_that_waits_discloses_nobody(session):
    """Asking is not membership: the Owner reads the queue, and nothing there
    opens a record either way round."""

    owner, asking = new_uuid(), new_uuid()
    await _a_group(session, owner, asking, policy=JoinPolicy.PEOPLE_I_APPROVE)

    disclosure = _disclosure("GroupsTheyShare", session)

    for reader, subject in ((owner, asking), (asking, owner)):
        assert (
            await disclosure.discloses(reader_id=reader, subject_id=subject)
            is False
        )


async def _an_official_group(
    session,
    *,
    run_by: UUID,
    members: tuple[UUID, ...] = (),
    policy: JoinPolicy = JoinPolicy.ANYONE,
    removed: bool = False,
) -> None:
    """An official group at a club, run by the Administrator ``run_by`` took up,
    and whoever else tapped *Join* — the club, the administratorship and the
    group each through its own aggregate. ``removed`` is the club ending that
    administratorship afterwards, which hands the group to nobody."""

    now = datetime.now(timezone.utc)
    event_store, events = (
        build_domain_event_store(session),
        build_event_publisher(session),
    )
    club_id = await _a_club(session)
    administrator = Administrator.invite(
        administrator_id=new_uuid(),
        club_id=club_id,
        email=Email("marta@ogrody33.pl"),
        name=Name("Marta Wójcik"),
        occurred_at=now,
    )
    administrator.accept(account_id=run_by, now=instant(now))
    if removed:
        administrator.remove(occurred_at=now)
    await build_administrator_repository(
        session, event_store=event_store, events=events
    ).save(administrator)
    group = Group.create_official_group(
        group_id=new_uuid(),
        name=GroupName("Ogrody 33 Club"),
        club_id=club_id,
        join_policy=policy,
        administrator_id=administrator.id,
        created_by=run_by,
        whatsapp_size=WhatsAppSize(48),
        sports=DeclaredSports.of({SPORT}),
        code=GroupCode("m3nq8vwa"),
        occurred_at=now,
    )
    for member in members:
        group.join(member, occurred_at=now)
    await build_group_repository(session, event_store=event_store, events=events).save(
        group
    )
    await session.commit()


# ---------------------------------------------------------------------------
# GroupsTheReaderRuns — does this reader run a group this person is in
# ---------------------------------------------------------------------------


async def test_whoever_runs_an_official_group_runs_it_for_everybody_in_it(session):
    """Running it is not membership, and being in it runs nothing — so this is
    one way round only, which is the whole difference from the group strand."""

    account, member = new_uuid(), new_uuid()
    await _an_official_group(session, run_by=account, members=(member,))

    runners = _disclosure("GroupsTheReaderRuns", session)

    assert await runners.discloses(reader_id=account, subject_id=member)
    assert await runners.discloses(reader_id=member, subject_id=account) is False


async def test_a_removed_administrator_runs_nothing(session):
    """**Running as it stands, never as it was**: a club ending the
    administratorship takes the group from them on the next read."""

    account, member = new_uuid(), new_uuid()
    await _an_official_group(session, run_by=account, members=(member,), removed=True)

    runners = _disclosure("GroupsTheReaderRuns", session)

    assert await runners.discloses(reader_id=account, subject_id=member) is False


async def test_a_join_request_that_waits_is_not_somebody_in_the_group(session):
    """Asking is not membership: the Administrator reads the request card, and
    nothing there opens a record."""

    account, asking = new_uuid(), new_uuid()
    await _an_official_group(
        session,
        run_by=account,
        members=(asking,),
        policy=JoinPolicy.PEOPLE_I_APPROVE,
    )

    runners = _disclosure("GroupsTheReaderRuns", session)

    assert await runners.discloses(reader_id=account, subject_id=asking) is False


async def test_a_player_group_is_run_by_nobody(session):
    """Its Owner is in it, and opens its members' records through the group
    strand like every other member — under every gate."""

    owner, member = new_uuid(), new_uuid()
    await _a_group(session, owner, member)

    runners = _disclosure("GroupsTheReaderRuns", session)

    assert await runners.discloses(reader_id=owner, subject_id=member) is False


# ---------------------------------------------------------------------------
# RecordGates — the two about accounts, plus the reader's own hold
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(RecordGates))
async def test_a_pair_nothing_withholds_is_admitted(implementation, session):
    """**No preference and no partition** (#575): with no hold on either and no
    account that may not be shown, the pair is admitted — a reader who never
    committed a profile included, because no gate here reads one."""

    gates = implementation.build(session)

    assert (
        await gates.admits(reader_id=new_uuid(), subject_id=new_uuid()) is True
    )


@pytest.mark.parametrize("implementation", registered(RecordGates))
async def test_a_block_either_way_round_withholds_nobody(implementation, session):
    """**A block is not a record gate** (``docs/adr/0193`` §2): the blocker
    opens the record to undo it, and the blocked person reads it as before."""

    reader, subject = new_uuid(), new_uuid()
    await _blocks(session, (reader, subject), (subject, reader))
    gates = implementation.build(session)

    assert await gates.admits(reader_id=reader, subject_id=subject) is True
    assert await gates.admits(reader_id=subject, subject_id=reader) is True


# ---------------------------------------------------------------------------
# BlocksByTheReader — the reader's own block, and never the other direction
# ---------------------------------------------------------------------------


async def _blocks(session, *pairs: tuple[UUID, UUID], lifted=()) -> None:
    """Each ``(blocker, blocked)`` blocked through the aggregate, and each pair
    in ``lifted`` blocked and then unblocked."""

    repository = build_block_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    at = _now()
    for blocker, blocked in (*pairs, *lifted):
        block = Block.first_blocked(
            blocker_id=blocker, blocked_id=blocked, occurred_at=at
        )
        if (blocker, blocked) in lifted:
            block.unblock(occurred_at=at)
        await repository.save(block)
    await session.commit()


@pytest.mark.parametrize("implementation", registered(BlocksByTheReader))
async def test_the_readers_own_block_is_answered(implementation, session):
    reader, subject = new_uuid(), new_uuid()
    await _blocks(session, (reader, subject))

    own = implementation.build(session)

    assert await own.has_blocked(reader_id=reader, subject_id=subject) is True


@pytest.mark.parametrize("implementation", registered(BlocksByTheReader))
async def test_a_block_of_the_reader_is_never_the_readers_own(
    implementation, session
):
    """**Directed** (``docs/adr/0193`` §3): the subject blocking the reader is
    nothing this port can say, so the blocked person's sheet cannot move."""

    reader, subject = new_uuid(), new_uuid()
    await _blocks(session, (subject, reader))

    own = implementation.build(session)

    assert await own.has_blocked(reader_id=reader, subject_id=subject) is False


@pytest.mark.parametrize("implementation", registered(BlocksByTheReader))
async def test_a_lifted_block_and_a_block_of_somebody_else_are_not_this_one(
    implementation, session
):
    reader, subject, other = new_uuid(), new_uuid(), new_uuid()
    await _blocks(session, (reader, other), lifted=((reader, subject),))

    own = implementation.build(session)

    assert await own.has_blocked(reader_id=reader, subject_id=subject) is False


# ---------------------------------------------------------------------------
# SubjectIdentitySource — who a person is, or nobody at all
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectIdentitySource))
async def test_a_player_this_platform_never_issued_cannot_be_described(
    implementation, session
):
    """``None`` rather than a blank record: the caller refuses, and it refuses in
    the same shape it refuses a stranger."""

    identities = implementation.build(session)

    assert await identities.identity_of(new_uuid()) is None


# ---------------------------------------------------------------------------
# RecordPhotoLink — an address for one photograph
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(RecordPhotoLink))
async def test_a_link_names_the_owner_and_the_photograph(implementation, session):
    """Signed as the person on the record and never as the person looking. It
    costs **no round trip** — signing is a signature over a request that is never
    sent — which is what lets a link be minted per response and stored nowhere.
    """

    owner, photo = new_uuid(), new_uuid()

    link = await implementation.build(session).link_for(
        owner_id=owner, photo_id=photo
    )

    assert str(owner) in link and str(photo) in link


# ---------------------------------------------------------------------------
# SubjectRatings — every sport they hold, and nothing that could be saved
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectRatings))
async def test_every_sport_they_are_rated_in_crosses_with_its_own_figures(
    implementation, session
):
    """One person and every sport, which is the shape a tap on a face has.

    The certainty, the range and the band's published name travel with the Level
    because a Level with none of them beside it is the claim the range amendment
    exists to stop.
    """

    ratings = implementation.build(session)
    player_id = new_uuid()
    await _a_rating(session, player_id, sport=Sport.PADEL, mu=3.20)
    await _a_rating(session, player_id, sport=Sport.SQUASH, mu=4.10)

    held = await ratings.ratings_of(player_id)

    assert set(held) == {Sport.PADEL, Sport.SQUASH}
    assert held[Sport.PADEL].level == 3.20
    assert held[Sport.PADEL].sport is Sport.PADEL
    assert held[Sport.PADEL].band
    assert held[Sport.PADEL].confidence > 0
    spread = held[Sport.PADEL].likely_range
    assert spread.low < 3.20 < spread.high


@pytest.mark.parametrize("implementation", registered(SubjectRatings))
async def test_a_rating_no_result_has_moved_rests_on_nought_counted_games(
    implementation, session
):
    """**A measured nought and never an absence**, which is the one place this
    number differs in kind from every other absent figure on the sheet: a Level
    straight out of the questionnaire has been tested by no game, and saying so
    is what stops it reading like a Level built on forty."""

    ratings = implementation.build(session)
    player_id = new_uuid()
    await _a_rating(session, player_id, sport=Sport.PADEL, mu=3.00)

    assert (await ratings.ratings_of(player_id))[Sport.PADEL].counted_games == 0


@pytest.mark.parametrize("implementation", registered(SubjectRatings))
async def test_a_player_rated_in_nothing_holds_nothing(implementation, session):
    """The ordinary state part way through onboarding. The sheet draws the
    poster with no Level on it and the skill card is simply absent."""

    assert await implementation.build(session).ratings_of(new_uuid()) == {}


# ---------------------------------------------------------------------------
# SubjectForm — the run of five, in one sport, with no moment on it
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectForm))
async def test_a_run_is_this_sports_results_oldest_first(implementation, session):
    """**Per sport, which is the defect this port exists to make
    unrepresentable**: a run built across every sport and drawn beneath a single
    sport's Level was squash results under a padel number."""

    form = implementation.build(session)
    now = instant(datetime.now(timezone.utc))
    player, opponent = new_uuid(), new_uuid()
    await _a_confirmed_game(session, player, opponent, sport=Sport.PADEL, won=True)
    await _a_confirmed_game(session, player, opponent, sport=Sport.TENNIS, won=True)
    await _a_confirmed_game(session, player, opponent, sport=Sport.PADEL, won=False)

    run = await form.last_results_in(player, sport=Sport.PADEL, now=now)

    assert [one.value for one in run] == ["WIN", "LOSS"]


@pytest.mark.parametrize("implementation", registered(SubjectForm))
async def test_a_sport_with_nothing_counted_in_it_is_an_empty_run(
    implementation, session
):
    """Never padded and never a placeholder: the client draws the gap."""

    form = implementation.build(session)
    now = instant(datetime.now(timezone.utc))

    assert await form.last_results_in(new_uuid(), sport=Sport.PADEL, now=now) == ()


# ---------------------------------------------------------------------------
# SubjectVariety — the whole record, one player, and a pair rather than a share
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectVariety))
async def test_variety_crosses_as_two_counts_in_this_contexts_own_words(
    implementation, session
):
    """**The pair, renamed and not recomputed.** ``games`` measured everybody who
    was on a court with them over the games that counted; the record calls those
    two numbers ``distinct_opponents`` and ``times_on_court`` and divides
    neither."""

    variety = implementation.build(session)
    now = _now()
    player, one, other = new_uuid(), new_uuid(), new_uuid()
    await _a_confirmed_game(session, player, one, sport=Sport.PADEL, won=True)
    await _a_confirmed_game(session, player, other, sport=Sport.TENNIS, won=False)
    await _a_confirmed_game(session, player, one, sport=Sport.PADEL, won=True)

    assert await variety.variety_of(player, now=now) == OpponentVariety(
        distinct_opponents=2, times_on_court=3
    )


@pytest.mark.parametrize("implementation", registered(SubjectVariety))
async def test_a_player_no_counted_game_was_watched_for_is_absent(
    implementation, session
):
    """**Absent, and the absence passes through every layer unchanged.** A habit
    nobody has been observed having is not a narrow one, so there is no nought
    here and no empty pair for a sheet to draw a zero-width bar from."""

    variety = implementation.build(session)

    assert await variety.variety_of(new_uuid(), now=_now()) is None


@pytest.mark.parametrize("implementation", registered(SubjectVariety))
async def test_variety_is_about_every_sport_and_never_the_one_on_the_sheet(
    implementation, session
):
    """**No sport reaches this port**, unlike the run of form beside it.

    Somebody who plays padel with the same face and squash with a different one
    has one habit, and a figure narrowed to whichever sport the sheet turned out
    to be about would be a different statistic under the same word.
    """

    variety = implementation.build(session)
    player, one, other = new_uuid(), new_uuid(), new_uuid()
    await _a_confirmed_game(session, player, one, sport=Sport.PADEL, won=True)
    await _a_confirmed_game(session, player, other, sport=Sport.SQUASH, won=True)

    assert await variety.variety_of(player, now=_now()) == OpponentVariety(
        distinct_opponents=2, times_on_court=2
    )


def test_the_variety_demand_takes_one_player_and_never_a_collection():
    """**The fence is the signature on this side of the seam too.**

    The fold behind it is unbounded, which is what makes it a career statistic —
    and what makes a set-shaped version of it an invitation to call it inside a
    search's walk over five hundred candidates.
    """

    hints = get_type_hints(SubjectVariety.variety_of)

    assert hints["player_id"] is UUID
    assert hints["return"] == OpponentVariety | None


# ---------------------------------------------------------------------------
# SubjectReliability — the pill, the rows, and the absence that is not a nought
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectReliability))
async def test_both_live_strands_cross_as_their_counts_and_their_figure(
    implementation, session
):
    """**The raw pair per row, and the figure derived from it.**

    Two plans, one of which produced a game and one of which nobody ever
    claimed; two booked games, one kept and one left after its cut-off with
    nobody taking the seat (#544). Each strand is a half, and the pair is what
    makes *one of two* and *twenty of forty* different claims on a sheet.
    """

    reliability = implementation.build(session)
    subject, other = new_uuid(), new_uuid()
    await _a_played_plan(session, subject, other)
    await _a_ghosted_plan(session, subject, other)
    await _a_booked_game(session, subject, starts=_ago(days=4))
    await _a_booked_game(session, subject, starts=_ago(days=3), left=True)

    panel = await reliability.reliability_of(subject, now=_now())

    assert panel is not None
    assert [
        (row.strand, row.good, row.opportunities, row.pct) for row in panel.strands
    ] == [
        (ReliabilityStrand.SHOWS_UP, 1, 2, 50),
        (ReliabilityStrand.KEEPS_PLANS, 1, 2, 50),
    ]


@pytest.mark.parametrize("implementation", registered(SubjectReliability))
async def test_the_pill_is_the_blend_the_rows_reproduce(implementation, session):
    """**The pill is the weighted mean of the figures printed beneath it.**

    Asserted by recomputing it from the rows that crossed, through the published
    weights — which is the honesty the sheet promises: not a number arrived at
    somewhere else and stated over rows that happen to sit under it.

    The two strands are deliberately unequal here, so a blend that ignored the
    weights or read them in the wrong order would come out somewhere else.
    """

    reliability = implementation.build(session)
    subject, other = new_uuid(), new_uuid()
    await _a_played_plan(session, subject, other)
    await _a_ghosted_plan(session, subject, other)
    await _a_booked_game(session, subject, starts=_ago(days=4))

    panel = await reliability.reliability_of(subject, now=_now())

    assert panel is not None
    weighted = sum(PUBLISHED_WEIGHTS[row.strand] * row.pct for row in panel.strands)
    basis = sum(PUBLISHED_WEIGHTS[row.strand] for row in panel.strands)
    assert panel.player_score == out_of_a_hundred(weighted, 100 * basis)


@pytest.mark.parametrize("implementation", registered(SubjectReliability))
async def test_a_strand_with_nothing_behind_it_is_absent_and_never_a_nought(
    implementation, session
):
    """One record and not the other is a panel of **one row**.

    Somebody who has kept a booked game and never had a plan made for them has
    a pill built on the strand they have — the three names with no provider and
    the one with no opportunity are the same absence, and neither drags the
    number down.
    """

    reliability = implementation.build(session)
    subject = new_uuid()
    await _a_booked_game(session, subject, starts=_ago(days=4))

    panel = await reliability.reliability_of(subject, now=_now())

    assert panel is not None
    assert [row.strand for row in panel.strands] == [ReliabilityStrand.KEEPS_PLANS]
    assert panel.player_score == 100


@pytest.mark.parametrize("implementation", registered(SubjectReliability))
async def test_a_player_nothing_has_fallen_due_for_has_no_panel_at_all(
    implementation, session
):
    """**The rule the whole chain is written around.** Nobody has failed to turn
    up who was never due to, so the answer is nothing rather than a zone of
    noughts — and *no record* never becomes *a bad record*."""

    reliability = implementation.build(session)

    assert await reliability.reliability_of(new_uuid(), now=_now()) is None


@pytest.mark.parametrize("implementation", registered(SubjectReliability))
async def test_a_booked_game_still_ahead_is_no_row_at_all(implementation, session):
    """**An opportunity and never a total.** A booked game whose hour has not
    come has not been kept *or* broken, and publishing it either way would
    state a conclusion the clock has not reached."""

    reliability = implementation.build(session)
    subject = new_uuid()
    await _a_booked_game(session, subject, starts=_ago(days=-2))

    assert await reliability.reliability_of(subject, now=_now()) is None


# ---------------------------------------------------------------------------
# What other players said
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectSportsmanship))
async def test_the_figure_crosses_with_the_count_of_people_behind_it(
    implementation, session
):
    """**Both numbers, from the very first rating.** There is no minimum here,
    because the count does a minimum's work honestly: a figure over one player
    reads as one person's opinion because it says so beside itself.

    The two ratings are different on purpose, so a fold that published one of
    them rather than their mean would be visible.
    """

    subject = new_uuid()
    await _stars(session, subject=subject, stars=5)
    await _stars(session, subject=subject, stars=4)

    said = await implementation.build(session).what_players_said(subject)

    assert said == WhatPlayersSaid(average=4.5, raters=2)


@pytest.mark.parametrize("implementation", registered(SubjectSportsmanship))
async def test_a_player_nobody_has_rated_is_absent_and_never_a_nought(
    implementation, session
):
    """**A fourth absence, asking a fourth question.** Rating is a favour: not
    answering a card costs nothing and leaves no record of the omission, so a
    nought here would publish *they are unpleasant* about somebody nobody has
    ever been asked about."""

    assert await implementation.build(session).what_players_said(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(SubjectSportsmanship))
async def test_a_weekly_partner_is_one_rater_however_many_evenings(
    implementation, session
):
    """**The collapse, through the demand the sheet actually calls.** Only a
    rater's most recent stars about somebody count, so the count beside the
    figure keeps meaning *how many different people have an opinion* — which is
    what makes a high one evidence of breadth rather than of repetition."""

    subject, partner = new_uuid(), new_uuid()
    for stars in (1, 1, 5):
        await _stars(session, subject=subject, rater=partner, stars=stars)

    said = await implementation.build(session).what_players_said(subject)

    assert said == WhatPlayersSaid(average=5.0, raters=1)


def test_the_sportsmanship_demand_asks_about_one_player_and_takes_no_clock():
    """**One person, and no instant.** A record is one deliberate tap; nothing
    here decays, because the window is fifty *people* rather than fifty days, so
    a ``now`` on this port would be a second horizon nobody could keep in step
    with the first. The matcher must never read it in any shape at all, and that
    is held by an import contract rather than by this signature."""

    hints = get_type_hints(SubjectSportsmanship.what_players_said)
    assert set(hints) == {"player_id", "return"}, hints
    assert hints["player_id"] is UUID


def test_the_sportsmanship_demand_has_one_method_and_it_is_the_figures():
    """**No second resolution** (``docs/adr/0179`` §5). ``band_for`` — the
    subject's three steps, no count — is gone from this demand with the band;
    a method answering about a person at a coarser resolution than the figure
    would be that decision quietly reopened on the consumer's side."""

    declared = [
        name
        for name, value in vars(SubjectSportsmanship).items()
        if callable(value) and not name.startswith("_")
    ]

    assert declared == ["what_players_said"]


# ---------------------------------------------------------------------------
# The world these demands are run against
# ---------------------------------------------------------------------------


async def _a_rating(session, player_id: UUID, *, sport: Sport, mu: float) -> None:
    """One rating, opened through the aggregate that opens one.

    Never an ``INSERT``: what these ports answer are folds over somebody else's
    streams, and the only honest way to exercise one is to make the history it
    reads (``docs/adr/0029``).
    """

    sigma = 0.35
    band = band_for(mu)
    low, high = likely_range(mu, sigma)
    await build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(
        SkillRating.initialise(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport,
            result=AssessmentResult(
                mu=mu,
                sigma=sigma,
                confidence=confidence_percent(sigma),
                range_low=round(low, 2),
                range_high=round(high, 2),
                band=BandView(name=band.label, lower=band.lower, upper=band.upper),
                status=STATUS_INITIAL_ESTIMATE,
                questions_asked=7,
                engine_version="racketskill-fusion-v3",
                confidence_ceiling=confidence_percent(sigma),
            ),
            source_assessment_id=new_uuid(),
            occurred_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()


#: A moment far enough back that a lone score has confirmed itself by ``now``.
#: The run of form reads only confirmed counted results, and a confirmation is a
#: clock passing rather than an act (``docs/adr/0137``) — so these games are made
#: in the past instead of anything being told they are over.
_LONG_ENOUGH_AGO = timedelta(days=30)


async def _a_confirmed_game(
    session, player: UUID, opponent: UUID, *, sport: Sport, won: bool
) -> None:
    """One counted singles game, played and confirmed by silence."""

    played = instant(datetime.now(timezone.utc) - _LONG_ENOUGH_AGO)
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=sport,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=player),
                Seating(side=GameSide.B, player_id=opponent),
            )
        ),
        occurred_at=instant(played - timedelta(hours=1)),
    )
    game.state_result(
        by=player,
        score=Score.of(
            [SetScore(a=6, b=4), SetScore(a=6, b=3)]
            if won
            else [SetScore(a=4, b=6), SetScore(a=3, b=6)]
        ),
        occurred_at=played,
    )
    await build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(game)
    await session.commit()


def _disclosure(name: str, session) -> PriorDisclosure:
    """One named implementation of the three-signatory port.

    Named rather than parameterised, because these arrangements are each about
    **one** strand: a game says nothing about a group, and a parameterised test
    asserting an empty answer from the other two would be asserting that they
    cannot see a fact that is not theirs.
    """

    return next(
        one.build(session)
        for one in implementations_of(PriorDisclosure)
        if one.name == name
    )


def _ago(**offset) -> Instant:
    """A moment that far behind the clock these demands read ``now`` from."""

    return instant(datetime.now(timezone.utc) - timedelta(**offset))


#: Old enough that a plan made then has closed its entry window on silence. Read
#: off ``games``' own two windows rather than typed, so a change to either moves
#: this with it instead of leaving a test that passes for the wrong reason.
_LONG_ENOUGH_TO_GHOST = PLAN_HORIZON + ENTRY_GRACE + timedelta(days=1)


def _a_plan(one: UUID, other: UUID, *, at: Instant) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=SPORT,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=one),
                Seating(side=GameSide.B, player_id=other),
            )
        ),
        occurred_at=at,
    )


async def _a_played_plan(session, one: UUID, other: UUID) -> None:
    """A plan that produced a game: somebody said *we played*, with a score."""

    at = _ago(days=3)
    game = _a_plan(one, other, at=at)
    game.state_result(
        by=one,
        score=Score.of((SetScore(a=6, b=4),)),
        occurred_at=instant(at + timedelta(hours=2)),
    )
    await build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(game)
    await session.commit()


async def _a_ghosted_plan(session, one: UUID, other: UUID) -> None:
    """A plan nobody ever claimed, old enough that its entry window has shut.

    A ghost is charged to **everybody who was on that court**: a dissolved
    arrangement is a fact about the court, and there is nobody in it to blame.
    """

    game = _a_plan(one, other, at=instant(_now() - _LONG_ENOUGH_TO_GHOST))
    await build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(game)
    await session.commit()


async def _a_booked_game(
    session, subject: UUID, *, starts: Instant, left: bool = False
) -> None:
    """A padel game booked five days before its hour with the subject and three
    others, through the aggregate — and, when ``left``, the subject leaving it
    after its 24-hour cut-off, so with nobody taking the seat it is broken once
    its hour has come (#544)."""

    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=starts,
        share_grosze=30_00,
        first_side=(subject, new_uuid()),
        second_side=(new_uuid(), new_uuid()),
        cut_off=instant(starts - timedelta(hours=24)),
        game_id=new_uuid(),
        at=instant(starts - timedelta(days=5)),
    )
    if left:
        booking.leave(subject, at=instant(starts - timedelta(hours=3)))
    await build_booking_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(booking)
    await session.commit()


async def _stars(
    session,
    *,
    subject: UUID,
    stars: int,
    rater: UUID | None = None,
    at: Instant | None = None,
) -> None:
    """One rater answers one court, giving one person stars.

    Written through ``sportsmanship``'s own aggregate rather than an ``INSERT``
    (``docs/adr/0029``) — the collapse lives in that store's key, and a row
    inserted beside the card would be this suite arranging away the thing the
    demand is meant to prove.
    """

    when = at or _now()
    await build_sportsmanship_ledger(session).record(
        SportsmanshipCard.answered(
            court=SettledCourt(
                game_id=new_uuid(),
                rater_id=rater or new_uuid(),
                others=(subject,),
                played_at=when,
            ),
            given=[StarsGiven(subject_id=subject, stars=stars)],
            at=when,
        )
    )
    await session.commit()
