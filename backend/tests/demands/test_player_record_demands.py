"""What ``player_record`` asks of the platform, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/player_record_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red.

**This context stores nothing**, so every arrangement here is made through
somebody else's aggregate — a profile committed, a challenge sent, a game played
— and never an ``INSERT`` (``docs/adr/0029``). That is not ceremony: what these
ports answer is folds and queries owned by five other contexts, and the only
honest way to exercise one is to make the history it reads.

**The rule the disclosure suite is written around is that absence is silence.** A
pair with nothing between them answers the empty set, not an error and not a
partial answer — because the caller turns an empty answer into the one refusal
this route has, and any other spelling would make that refusal a different one.

**One demand is deliberately run against an empty index**: a subject with no row
in the partition asked about is a gate that *cannot be evaluated*, and a gate
that cannot be evaluated excludes. The register's row builds a real
``DatabaseCandidateSource`` and never refreshes it, which is exactly that state.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_search_store,
    build_skill_rating_repository,
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
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, court_sides
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    InclusionReason,
    RecordedCard,
    PoolDescription,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    StagedCounts,
)
from app.modules.player_profile.domain.availability import Window
from app.modules.player_record.domain.ports import (
    PriorDisclosure,
    RecordGates,
    RecordPhotoLink,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectVariety,
)
from app.modules.player_record.domain.record import OpponentVariety
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
    """**The answer almost everybody gets**, and it must be an empty set rather
    than an error: the caller turns it into the one refusal this route has."""

    disclosure = implementation.build(session)

    assert (
        await disclosure.partitions_between(
            reader_id=new_uuid(), subject_id=new_uuid(), now=_now()
        )
        == frozenset()
    )


async def test_a_search_that_returned_them_is_a_disclosure_in_its_own_sport(
    session,
):
    reader, subject = new_uuid(), new_uuid()
    await build_search_store(session).record(_a_search(reader, subject))
    await session.commit()

    disclosure = _disclosure("SearchesThatShowedThem", session)

    assert await disclosure.partitions_between(
        reader_id=reader, subject_id=subject, now=_now()
    ) == frozenset({SPORT})


async def test_a_search_discloses_nobody_to_a_different_searcher(session):
    """*The searcher may read their own rows and nobody else's* — which here is
    the difference between a disclosure and a directory of everybody the platform
    has ever shown to anybody."""

    reader, subject = new_uuid(), new_uuid()
    await build_search_store(session).record(_a_search(reader, subject))
    await session.commit()

    disclosure = _disclosure("SearchesThatShowedThem", session)

    assert (
        await disclosure.partitions_between(
            reader_id=new_uuid(), subject_id=subject, now=_now()
        )
        == frozenset()
    )


async def test_a_live_challenge_discloses_both_ways(session):
    """The organiser and the invitee are both entitled, which is the point: only
    one of the two ran the search."""

    organiser, invitee = new_uuid(), new_uuid()
    challenge = _sent(organiser, invitee, at=_now())
    await build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(challenge)
    await session.commit()

    disclosure = _disclosure("ChallengesTheyShare", session)

    for reader, subject in ((organiser, invitee), (invitee, organiser)):
        assert await disclosure.partitions_between(
            reader_id=reader, subject_id=subject, now=_now()
        ) == frozenset({SPORT})


async def test_a_challenge_that_has_ended_discloses_nobody(session):
    """A lapsed seat is a seat somebody else may be offered, so the challenge
    entitles nobody — and the sender still holds the search that made it."""

    organiser, invitee = new_uuid(), new_uuid()
    long_ago = instant(datetime.now(timezone.utc) - timedelta(days=30))
    challenge = _sent(organiser, invitee, at=long_ago)
    await build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(challenge)
    await session.commit()

    disclosure = _disclosure("ChallengesTheyShare", session)

    assert (
        await disclosure.partitions_between(
            reader_id=organiser, subject_id=invitee, now=_now()
        )
        == frozenset()
    )


async def test_a_game_they_both_played_discloses_for_ever(session):
    """An evening two people were on a court for does not stop having happened,
    so there is no window here and no standing test."""

    a, b = new_uuid(), new_uuid()
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=SPORT,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=a),
                Seating(side=GameSide.B, player_id=b),
            )
        ),
        occurred_at=instant(datetime.now(timezone.utc) - timedelta(days=400)),
    )
    await build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(game)
    await session.commit()

    disclosure = _disclosure("GamesTheyPlayed", session)

    assert await disclosure.partitions_between(
        reader_id=a, subject_id=b, now=_now()
    ) == frozenset({SPORT})


# ---------------------------------------------------------------------------
# RecordGates — the four, plus the reader's own hold
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(RecordGates))
async def test_a_subject_with_no_row_in_the_partition_is_not_admitted(
    implementation, session
):
    """**A gate that cannot be evaluated excludes**, and it excludes by answering
    rather than by raising: the reader is told the one thing this route tells
    anybody it turns away."""

    gates = implementation.build(session)

    assert (
        await gates.admits(
            reader_id=new_uuid(), subject_id=new_uuid(), sport=SPORT
        )
        is False
    )


# ---------------------------------------------------------------------------
# SubjectIdentitySource — who a person is, or nobody at all
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(SubjectIdentitySource))
async def test_a_player_this_platform_never_issued_cannot_be_described(
    implementation, session
):
    """``None`` rather than a blank record: the caller refuses, and it refuses in
    the same shape it refuses a block."""

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
    two numbers ``distinct_opponents`` and ``games_played`` and divides
    neither."""

    variety = implementation.build(session)
    now = _now()
    player, one, other = new_uuid(), new_uuid(), new_uuid()
    await _a_confirmed_game(session, player, one, sport=Sport.PADEL, won=True)
    await _a_confirmed_game(session, player, other, sport=Sport.TENNIS, won=False)
    await _a_confirmed_game(session, player, one, sport=Sport.PADEL, won=True)

    assert await variety.variety_of(player, now=now) == OpponentVariety(
        distinct_opponents=2, games_played=3
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
        distinct_opponents=2, games_played=2
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
    **one** strand: a search record says nothing about a challenge, and a
    parameterised test asserting an empty answer from the other two would be
    asserting that they cannot see a fact that is not theirs.
    """

    return next(
        one.build(session)
        for one in implementations_of(PriorDisclosure)
        if one.name == name
    )


def _sent(organiser: UUID, invitee: UUID, *, at: Instant) -> Challenge:
    """One send through the aggregate, on the sport's whole fixed court.

    An empty seat is a seat, so the rest of the court is spelled rather than
    omitted — and a newly invited seat carries the origin the send read off a
    search, because a seat that cannot say where it came from cannot be built.
    """

    sides = court_sides(SPORT)
    occupants: list[UUID | None] = [organiser, invitee]
    occupants += [None] * (len(sides) - len(occupants))
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=SPORT,
        mode=None,
        window=Window.THIS_WEEK,
        organiser_id=organiser,
        arrangement=[
            SeatPlan(
                side=side,
                player_id=occupant,
                origin=(
                    SentFromSearch(search_id=new_uuid(), position=seat)
                    if occupant == invitee
                    else None
                ),
            )
            for seat, (side, occupant) in enumerate(
                zip(sides, occupants, strict=True), 1
            )
        ],
        occurred_at=at,
    )


def _a_search(searcher: UUID, shown: UUID) -> SearchRecord:
    """One recorded search that returned one person, in ``SPORT``.

    Written out rather than trimmed to the columns this demand reads: every fact
    on a search record is search-time and there is no backfill, so a record
    assembled with holes in it is not one this platform could ever have written.
    """

    return SearchRecord(
        id=new_uuid(),
        searcher_id=searcher,
        sport=SPORT,
        mode=SearchMode.COMPETITIVE,
        intent_read=None,
        surface=SearchSurface.SHORTLIST,
        initiation=SearchInitiation.HUMAN,
        at=datetime.now(timezone.utc),
        engine_version="matchfit-v1",
        ruleset_version="r2026-08-26-a",
        snapshot_version=1,
        trace_id="trace-record",
        index_stale=False,
        counts=StagedCounts(
            n_generated=1,
            excluded_by_gate={},
            n_scored=1,
            n_cleared_floor=1,
            n_returned=1,
            n_near_miss_recorded=0,
        ),
        best_withheld_fit=None,
        pool_description=PoolDescription(
            sport=SPORT,
            radius_km_used=10,
            players_in_range=1,
            window=Window.THIS_WEEK,
        ),
        searcher_grid=("2:EVENING",),
        searcher_slot_count=1,
        searcher_area_code="A+05151-000013",
        radius_clamp_bit=False,
        rung_offers=None,
        offered_by_search_id=None,
        rung_taken=None,
        latency_ms_by_stage={"pipeline": 1},
        candidates=(
            SearchCandidateRecord(
                band=CandidateBand.RETURNED,
                position=1,
                player_id=shown,
                fit=80.0,
                terms=({"term": "LEVEL_FIT", "weight": 29.9, "value": 1.0},),
                degraded_terms=(),
                degraded_reasons=(),
                modifiers=(),
                liveness_reasons=(),
                liveness_signals={},
                shared_count=2,
                their_slot_count=5,
                days_away=1,
                inclusion_reason=InclusionReason.ZERO_EXPOSURE,
                withheld_reason=None,
                missing_terms=(),
                reliability_penalty_applied=False,
                reliability_penalty_decisive=False,
                concerns=(),
                distance_km=4,
                card=RecordedCard(
                    nickname="ada",
                    photo_id=None,
                    review=None,
                    area_code="A+05151-000013",
                    social_tags=("PLAYS_TO_WIN",),
                    level=2.7,
                    band="Improver",
                    range_low=2.36,
                    range_high=3.04,
                    player_score=None,
                    counted_games=None,
                    last_five=(),
                ),
                at_stake=AtStake(win_delta=0.07, loss_delta=-0.05),
            ),
        ),
    )
