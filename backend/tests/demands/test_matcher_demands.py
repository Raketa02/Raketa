"""The matcher's outward demands, run against every implementation of each.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/matcher_demands.py`` is
enrolled here automatically, the null objects included, so registering a real
adapter either satisfies the demand or turns the build red. There is no skipped
test to go stale.

**This is ADR-0098's *contract suite*, and the directory is not called that on
purpose.** ``docs/environments.md`` already has a **Contract** tier and it means
``openapi.player.json`` drift — the thing ``make test-drift`` proves still fires.
Two suites called *contract*, one about what a client generates from and one
about what an unwritten context owes us, is how a green build starts being read
as the wrong assurance. These are the matcher's **demands**, which is the word
the register and ``MATCHER_DEMANDS`` already use.
"""

from __future__ import annotations

from dataclasses import fields
from inspect import signature
from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_skill_rating_repository,
)
from app.bootstrap.matcher_demands import (
    REGISTERED_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.matchfit.core import ReliabilityStrand
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    band_for,
    confidence_percent,
    likely_range,
)
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import (
    SentFromSearch as WrittenFromSearch,
)
from app.modules.challenges.domain.seats import SeatPlan, court_sides
from app.modules.player_profile.domain.availability import Window
from app.modules.matchmaking.domain.errors import GateDataUnavailable
from app.modules.matchmaking.domain.ports import (
    FAIL_POSTURE,
    MATCHER_DEMANDS,
    PAIRWISE_COUNTERPART_BOUND,
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    ChallengeOrigin,
    FailPosture,
    MatchHistoryQuery,
    OpenChallenge,
    OutcomeTally,
    PairwiseCounterpart,
    PairwiseOutcome,
    PlayerScoreQuery,
    PlayerScoreReading,
    RatioStrand,
    SentFromSearch,
    SentOutsideASearch,
    SportsmanshipStrand,
)
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.users.domain.events import UserRegistered
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.shared.ids import new_uuid


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


# ---------------------------------------------------------------------------
# AccountHoldQuery — one live boolean per player, and nothing else
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_a_hold_read_answers_with_ids_the_caller_asked_about(
    implementation, session
):
    """The gate answers in ids, about the players it was handed, and stops.

    Both directions travel in one collection — the searcher's own id beside the
    candidates' — because ``docs/adr/0095`` points the hold both ways and asking
    once is what stops one direction being forgotten. Today nobody comes back,
    and that absence is measured rather than invented: nothing in this repository
    can open a case.
    """

    port = implementation.build(session)
    asked = (new_uuid(), new_uuid())

    held = await port.held_among(asked)

    assert held <= set(asked)


# ---------------------------------------------------------------------------
# AccountStatusQuery — the set of accounts that may not be shown
# ---------------------------------------------------------------------------
#
# The one port whose provider ships (``docs/adr/0124``), so the suite arranges a
# real world and asserts a real answer. The arrangement belongs to the **port**
# and not to any one implementation: one provider signs one contract, so the
# world an ``AccountStatusQuery`` answers about is ``users``' world whoever
# implements it, and a second implementation arriving tomorrow is held to the
# same two accounts without a line being written for it.


async def _register(session, *, nickname: str, is_active: bool):
    users = SqlAlchemyUserRepository(session)
    user_id = new_uuid()
    await users.project_registered(
        UserRegistered(
            user_id=user_id,
            email=f"{nickname}@example.com",
            nickname=nickname,
            password_hash="x" * 12,
            authority="USER",
            is_admin=False,
            is_active=is_active,
            occurred_at=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
            adult_attested=True,
        )
    )
    return user_id


@pytest.mark.parametrize("implementation", registered(AccountStatusQuery))
async def test_a_disabled_account_may_not_be_shown_and_an_active_one_may(
    implementation, session
):
    """A real provider, a real world, a real answer — and it discriminates.

    ``users`` ships ``is_active`` and ``auth`` already refuses a disabled account
    four ways; nothing in the matchmaking design had ever read it, so a disabled
    account kept its index row and stayed a candidate indefinitely. This is the
    test that says it no longer does.
    """

    port = implementation.build(session)
    playing = await _register(session, nickname="active", is_active=True)
    disabled = await _register(session, nickname="disabled", is_active=False)

    withheld = await port.may_not_be_shown([playing, disabled])

    assert withheld == frozenset({disabled})


@pytest.mark.parametrize("implementation", registered(AccountStatusQuery))
async def test_an_account_status_read_invents_nobody(implementation, session):
    """An id ``users`` has never heard of is not withheld and not asserted about.

    The gate asks *may this account be used*, and a stranger's id is not an
    answer to it. Withholding an unknown id would make a typo look like a
    disabled account; the search's own generation is what decides who is a
    candidate at all.
    """

    port = implementation.build(session)
    stranger = new_uuid()

    assert await port.may_not_be_shown([stranger]) == frozenset()


# ---------------------------------------------------------------------------
# PlayerScoreQuery — the five strands, separately, with their evidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_a_player_with_no_record_is_absent_and_never_a_zero(
    implementation, session
):
    """No record is not a bad record.

    A player without a score is not ``0.5`` and not ``0``: they are **absent**
    from the answer, the term returns ``NoEvidence`` and the surviving weights
    renormalise. It used to be every player and no longer is (``docs/adr/0140``),
    which is what makes this the assertion it was written to be: two ids nothing
    has ever arranged anything for, put to a provider that can now answer about
    somebody.
    """

    port = implementation.build(session)
    unknown = (new_uuid(), new_uuid())

    readings = await port.readings_for(unknown)

    assert set(readings) == set()


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_a_score_read_answers_only_about_players_it_was_asked_about(
    implementation, session
):
    """One batched read per search, and it volunteers nobody."""

    port = implementation.build(session)
    asked = (new_uuid(), new_uuid())

    readings = await port.readings_for(asked)

    assert set(readings) <= set(asked)


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_every_strand_that_crosses_carries_its_own_evidence(
    implementation, session
):
    """The five are read separately, and each brings what it was measured from.

    **No longer vacuous**: ``player_score`` ships and answers two of the five for
    anybody with a record (``docs/adr/0140``). It stays written over whatever
    arrives rather than over the two, because the shape is the demand — a strand
    is its own published value with the numerator and denominator behind it and
    the moment it was last observed, or, for sportsmanship, a mean and a rating
    count, because it is not a ratio.

    Asked about a stranger, so what it proves here is that a provider with a real
    database behind it still answers about nobody rather than inventing a row.
    """

    port = implementation.build(session)

    readings = await port.readings_for([new_uuid()])

    for reading in readings.values():
        assert set(reading.strands) <= set(ReliabilityStrand)
        for strand, observation in reading.strands.items():
            expected = (
                SportsmanshipStrand
                if strand is ReliabilityStrand.SPORTSMANSHIP
                else RatioStrand
            )
            assert isinstance(observation, expected)


# ---------------------------------------------------------------------------
# MatchHistoryQuery — the pairwise read, the count, and the origin key
# ---------------------------------------------------------------------------
#
# **The one port with two providers, and the arrangement belongs to the port.**
# ``challenges`` ships and answers three of the four reads; ``matches`` is
# unwritten and owes the fourth. So this block arranges a real world — through
# the ``Challenge`` aggregate and never an ``INSERT`` (``docs/adr/0029``), which
# is also the only way the fold behind these reads is exercised at all — and
# asserts real answers about it.
#
# **The arrangement splits in two, and the half that is missing is said out loud
# rather than left for a reader to mistake the coverage as even.** ``ACCEPTED``
# and ``DECLINED`` are challenge facts and are arranged below. ``PLAYED``,
# ``PLANNED_NEVER_PLAYED`` and ``late_change_threshold`` are ``matches``' and
# **cannot be arranged by anybody yet**: the demands about them stay shape-only
# until that context signs, and they are vacuous on purpose rather than by
# oversight.
#
# **Every arrangement is dated against the wall clock, and that is the point of
# the first demand.** The provider derives *open* from the seats and ``now``, so
# a seat invited twenty-five hours ago reads as lapsed with nothing having swept
# it — and an implementation that stored a standing would still be calling it
# awaiting.


def _repository(session):
    """A challenge repository over this session. **Built per act, deliberately.**

    It remembers the stream versions it has read, so each arrangement step loads
    and saves through its own — which is what a request does, and what stops one
    step's version answering for another's.
    """

    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _ago(**offset) -> Instant:
    """A moment that far behind the clock this suite's provider reads."""

    return instant(datetime.now(timezone.utc) - timedelta(**offset))


def _long_enough_ago_to_have_lapsed() -> Instant:
    """A moment far enough back that a seat invited then has run out of window.

    **Derived from ``ANSWER_WINDOW``, with an hour to spare, rather than typed as
    *yesterday*.** The window moved from a day to two (``docs/adr/0151``), and a
    fixture carrying its own copy of the old number would have gone on passing
    while asserting nothing about a lapse — which is the way a case like this
    fails silently rather than red.
    """

    return instant(datetime.now(timezone.utc) - ANSWER_WINDOW - timedelta(hours=1))


def _just_after(sent_at: Instant, **offset) -> Instant:
    """A moment that far after a send, and well inside that seat's window."""

    return instant(sent_at + timedelta(**offset))


async def _sent(
    session,
    *,
    organiser: UUID,
    invitees: tuple[UUID, ...],
    sport: Sport,
    at: Instant,
    search_id: UUID | None = None,
    positions: dict[UUID, int] | None = None,
) -> Challenge:
    """One send, through the aggregate: an organiser, a court, and a search behind it.

    Empty seats fill the rest of the court, because the court is the sport's
    whole fixed list — and every invitee arrives carrying the origin the send
    read off the search, because a seat that cannot say where it came from
    cannot be constructed at all.
    """

    sides = court_sides(sport)
    occupants: list[UUID | None] = [organiser, *invitees]
    occupants += [None] * (len(sides) - len(occupants))
    from_search = search_id or new_uuid()
    where = positions or {}
    arrangement = [
        SeatPlan(
            side=side,
            player_id=occupant,
            origin=(
                None
                if occupant is None or occupant == organiser
                else WrittenFromSearch(
                    search_id=from_search, position=where.get(occupant, seat + 1)
                )
            ),
        )
        for seat, (side, occupant) in enumerate(zip(sides, occupants, strict=True))
    ]
    challenge = Challenge.sent(
        challenge_id=new_uuid(),
        sport=sport,
        mode=None,
        window=Window.THIS_WEEK,
        organiser_id=organiser,
        arrangement=arrangement,
        occurred_at=at,
    )
    await _repository(session).save(challenge)
    return challenge


async def _mutual(session, *, one: UUID, other: UUID, at: Instant) -> Challenge:
    """The challenge two yeses that met open. **Both seats accepted, no deadline.**"""

    challenge = Challenge.opened_from_mutual_interest(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        organiser_id=one,
        other_player_id=other,
        occurred_at=at,
    )
    await _repository(session).save(challenge)
    return challenge


async def _answers(session, challenge: Challenge, player_id: UUID, *, yes: bool, at):
    repository = _repository(session)
    loaded = await repository.load(challenge.id)
    if yes:
        loaded.accept(player_id, occurred_at=at)
    else:
        loaded.decline(player_id, occurred_at=at)
    await repository.save(loaded)


async def _refill(
    session, challenge: Challenge, *, seating: UUID, beside: UUID, at: Instant
) -> None:
    """Complete a half-built court: keep who is in, and offer the open seat on.

    The path that makes today's arrangement forget a former occupant — the whole
    reason the answers are walked off the events rather than read off the seats.
    """

    repository = _repository(session)
    loaded = await repository.load(challenge.id)
    sides = court_sides(loaded.sport)
    occupants: list[UUID | None] = [loaded.organiser_id, beside, seating]
    occupants += [None] * (len(sides) - len(occupants))
    loaded.invite(
        [
            SeatPlan(
                side=side,
                player_id=occupant,
                origin=(
                    WrittenFromSearch(search_id=new_uuid(), position=seat + 1)
                    if occupant == seating
                    else None
                ),
            )
            for seat, (side, occupant) in enumerate(zip(sides, occupants, strict=True))
        ],
        occurred_at=at,
    )
    await repository.save(loaded)


async def _sweep(session, challenge: Challenge, *, now: Instant) -> int:
    """Run the record-keeping sweep over one challenge, as the loop would."""

    repository = _repository(session)
    loaded = await repository.load(challenge.id)
    recorded = loaded.lapse(now=now)
    await repository.save(loaded)
    return recorded


def _counterparts(rows) -> set[UUID]:
    return {row.counterpart_id for row in rows}


def _by_player(counterparts) -> dict[UUID, dict]:
    return {one.player_id: dict(one.outcomes) for one in counterparts}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_a_seat_past_its_window_is_not_open_with_no_sweep_having_run(
    implementation, session
):
    """**The demand that can tell a derived standing from a cached one.**

    A padel court sent yesterday: one invitee accepted inside their day, two
    never answered. Nothing has swept anything — there is no ``SeatLapsed`` in
    this stream — and the two silent seats have already left both the open read
    and the count, because *open* is folded from the seats and the clock at the
    moment it is asked.

    An implementation holding a standing column, or a projection of *who has an
    open challenge with whom*, would still be answering **awaiting** here. That
    is the whole reason this demand is written the way it is: it is right until a
    deadline passes, wrong until something sweeps it, and it is the copy that
    gets believed.

    The challenge itself still stands, which is what stops this passing for the
    wrong reason: one seat is accepted, so there is somebody left to keep faith
    with and the answer *nothing is open* would be as wrong as the answer
    *everything is*.
    """

    port = implementation.build(session)
    organiser, kept, silent, also_silent = (new_uuid() for _ in range(4))
    long_ago = _long_enough_ago_to_have_lapsed()
    challenge = await _sent(
        session,
        organiser=organiser,
        invitees=(kept, silent, also_silent),
        sport=Sport.PADEL,
        at=long_ago,
    )
    await _answers(
        session, challenge, kept, yes=True, at=_just_after(long_ago, minutes=30)
    )

    assert _counterparts(await port.open_challenges(organiser)) == {kept}
    assert _counterparts(await port.open_challenges(kept)) == {organiser}
    assert await port.open_challenges(silent) == ()
    counts = await port.open_challenge_counts([kept, silent, also_silent])
    assert dict(counts) == {kept: 0, silent: 0, also_silent: 0}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_a_decline_and_a_lapse_leave_the_open_read_and_only_one_is_an_answer(
    implementation, session
):
    """One arrangement, two opposite assertions — and the signals turning on.

    A seat that declined and a seat whose day ran out have both **reopened**, so
    neither holder is in the game and both go back to the deck at once: a
    decline must not cost somebody a candidate they never turned down, and
    neither must silence.

    What they do to the *other* read is opposite, and that is the whole demand.
    A decline is a judgement and is what ``PREVIOUS_DECLINE`` prices; a lapse is
    a fact about a window and **tallies nowhere**, because a signal that filed
    silence as judgement would be reading an erased history. The accepted seat is
    the third case: ``PREVIOUS_ACCEPT`` is *they said yes to you before*, a price
    put on **their** card, which is why the tally is their answers and never the
    reader's own.

    The challenge is still standing throughout, which is what stops this passing
    for the wrong reason: one seat is accepted, so the answer *nothing is open*
    would be as wrong as the answer *everything is*.
    """

    port = implementation.build(session)
    organiser, said_yes, said_no, said_nothing = (new_uuid() for _ in range(4))
    long_ago = _long_enough_ago_to_have_lapsed()
    challenge = await _sent(
        session,
        organiser=organiser,
        invitees=(said_yes, said_no, said_nothing),
        sport=Sport.PADEL,
        at=long_ago,
    )
    that_evening = _just_after(long_ago, minutes=20)
    a_little_later = _just_after(long_ago, minutes=40)
    await _answers(session, challenge, said_yes, yes=True, at=that_evening)
    await _answers(session, challenge, said_no, yes=False, at=a_little_later)

    assert _counterparts(await port.open_challenges(organiser)) == {said_yes}
    answered = _by_player(await port.pairwise_counterparts(organiser))
    assert set(answered) == {said_yes, said_no}
    assert set(answered[said_yes]) == {PairwiseOutcome.ACCEPTED}
    assert set(answered[said_no]) == {PairwiseOutcome.DECLINED}
    assert answered[said_yes][PairwiseOutcome.ACCEPTED].count == 1


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_refilling_a_declined_seat_erases_nobodys_answer(implementation, session):
    """A refusal is remembered after the seat it was given from is somebody else's.

    ``SeatsInvited`` carries the **whole** resulting court, so the arrangement as
    it stands today has forgotten whoever left it. An implementation reading
    *who answered* off today's seats therefore drops a recorded decline the
    moment the organiser refills that position — a real refusal, erased by an act
    of somebody else's, with the signal going quiet and nothing looking broken.

    It cuts the other way in the same arrangement, and that half is the one an
    over-eager fix gets wrong: the player seated **into** the reopened position
    was not in the game that was declined, and inherits no history from it.
    """

    port = implementation.build(session)
    organiser, said_no, kept, replacement = (new_uuid() for _ in range(4))
    challenge = await _sent(
        session,
        organiser=organiser,
        invitees=(said_no, kept),
        sport=Sport.PADEL,
        at=_ago(minutes=30),
    )
    await _answers(session, challenge, said_no, yes=False, at=_ago(minutes=20))
    await _refill(
        session, challenge, seating=replacement, beside=kept, at=_ago(minutes=10)
    )

    assert said_no not in _counterparts(await port.open_challenges(organiser))
    assert set(_by_player(await port.pairwise_counterparts(organiser))) == {said_no}
    # The newcomer shares a court with the organiser and with nobody's history.
    assert await port.pairwise_counterparts(replacement) == ()


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_every_occupied_seat_but_your_own_is_a_counterpart(
    implementation, session
):
    """Co-invitees included, because sharing a line-up makes a pair.

    If we are both in a line-up we have an open game together, which is the
    exclusion's plain sense read from the other side — and it is what makes the
    send's refusal symmetric: two people sharing a court may not open a second
    challenge against each other.

    Nobody is their own counterpart, which is the other half and is the one an
    implementation folding *the players in this challenge* would get wrong.
    """

    port = implementation.build(session)
    organiser, one, two, three = (new_uuid() for _ in range(4))
    await _sent(
        session,
        organiser=organiser,
        invitees=(one, two, three),
        sport=Sport.PADEL,
        at=_ago(minutes=5),
    )

    assert _counterparts(await port.open_challenges(two)) == {organiser, one, three}
    assert _counterparts(await port.open_challenges(organiser)) == {one, two, three}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_each_open_row_carries_its_own_seats_origin(implementation, session):
    """The telemetry join: one search, three positions, three rows.

    ``search-telemetry.md`` §19.2 joins a challenge back to the row of the
    shortlist it was drawn from, so a doubles send from one search at three
    positions has to come back as three rows carrying three positions. A
    challenge-level origin would keep the search and lose every position, and
    there is no backfill — the loss would be permanent and silent.

    A seat nobody invited says ``SentOutsideASearch`` and never nothing: the
    organiser built their own seat, so from an invitee's side the row is a claim
    rather than a missing value.
    """

    port = implementation.build(session)
    organiser, one, two, three = (new_uuid() for _ in range(4))
    search_id = new_uuid()
    await _sent(
        session,
        organiser=organiser,
        invitees=(one, two, three),
        sport=Sport.PADEL,
        at=_ago(minutes=5),
        search_id=search_id,
        positions={one: 2, two: 5, three: 9},
    )

    drawn = {
        row.counterpart_id: row.origin
        for row in await port.open_challenges(organiser)
    }
    assert all(isinstance(origin, SentFromSearch) for origin in drawn.values())
    assert {
        person: (origin.search_id, origin.position)
        for person, origin in drawn.items()
    } == {
        one: (search_id, 2),
        two: (search_id, 5),
        three: (search_id, 9),
    }
    theirs = {row.counterpart_id: row.origin for row in await port.open_challenges(one)}
    assert isinstance(theirs[organiser], SentOutsideASearch)


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_no_counterpart_appears_twice_and_the_read_is_not_sport_keyed(
    implementation, session
):
    """One row per person, over every sport at once.

    The exclusion is *anybody you already have an open game with*, and it carries
    no sport field at all: asking somebody for padel while your tennis challenge
    sits unanswered is pestering with a sport chip on it. So a searcher's two
    open challenges in two sports come back as one list, and a person in it once.

    An implementation answering one row per **challenge** rather than per person
    passes every other demand here and fails this one.
    """

    port = implementation.build(session)
    organiser, alone, one, two = (new_uuid() for _ in range(4))
    await _sent(
        session,
        organiser=organiser,
        invitees=(alone,),
        sport=Sport.TENNIS,
        at=_ago(minutes=9),
    )
    await _sent(
        session,
        organiser=organiser,
        invitees=(one, two),
        sport=Sport.PADEL,
        at=_ago(minutes=4),
    )

    rows = await port.open_challenges(organiser)
    assert _counterparts(rows) == {alone, one, two}
    assert len(rows) == len(_counterparts(rows))


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_the_count_is_unanswered_invited_seats_and_nothing_else(
    implementation, session
):
    """Seats waiting on **your** answer — not your sends, not what you accepted.

    The ruleset's own falsifier is what decides this: *answer rate by
    open-challenge bucket, and if answer rate does not fall as load rises the
    signal is measuring nothing.* Only unanswered seats are the denominator of
    that. An organiser with sends out is over-committed and is not slow to
    answer, and sinking them would dock the exact behaviour the product exists to
    produce.

    Across every sport, because the read is not sport-keyed — and a seat whose
    window has passed stops counting the moment it does, without a sweep.
    """

    port = implementation.build(session)
    organiser, accepted, busy, waiting = (new_uuid() for _ in range(4))
    somebody_else, elsewhere = new_uuid(), new_uuid()
    court = await _sent(
        session,
        organiser=organiser,
        invitees=(accepted, busy, waiting),
        sport=Sport.PADEL,
        at=_ago(minutes=20),
    )
    await _answers(session, court, accepted, yes=True, at=_ago(minutes=15))
    await _sent(
        session,
        organiser=somebody_else,
        invitees=(busy,),
        sport=Sport.TENNIS,
        at=_ago(minutes=10),
    )
    await _sent(
        session,
        organiser=elsewhere,
        invitees=(waiting,),
        sport=Sport.TENNIS,
        at=_long_enough_ago_to_have_lapsed(),
    )

    counts = await port.open_challenge_counts(
        [organiser, accepted, busy, waiting, somebody_else]
    )

    assert dict(counts) == {
        # Their own send waits on nobody, and their seat is accepted from birth.
        organiser: 0,
        somebody_else: 0,
        # They answered; nothing is waiting on them any more.
        accepted: 0,
        # Two seats, two sports, both still theirs to answer.
        busy: 2,
        # One live seat, and one whose day ran out with nothing having swept it.
        waiting: 1,
    }


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_the_open_challenge_count_keys_exactly_the_set_it_was_asked_about(
    implementation, session
):
    """Everybody asked gets a count, and a zero here is **measured**.

    This demand used to assert ``dict(counts) == {id: 0}`` for two strangers,
    which was a claim about the null object rather than about the port: it was
    stronger than the contract, and it would have failed a correct provider the
    moment anybody had an inbox. What the contract actually says is that the
    answer **keys exactly the asked set** — nobody volunteered, nobody dropped —
    and that a zero means the seats were counted and none were theirs.

    So the arrangement seeds one busy player beside two strangers, and the
    demand asserts both halves at once: the shape over everybody, and a real
    number for the one person there is a real number about. A Player Score's
    zero would have been **invented**, which is why that port answers about
    nobody at all and this one answers about everybody.
    """

    port = implementation.build(session)
    stranger, also_a_stranger, busy = (new_uuid() for _ in range(3))
    await _sent(
        session,
        organiser=new_uuid(),
        invitees=(busy,),
        sport=Sport.TENNIS,
        at=_ago(minutes=3),
    )
    asked = (stranger, also_a_stranger, busy)

    counts = await port.open_challenge_counts(asked)

    assert set(counts) == set(asked)
    assert counts[stranger] == 0
    assert counts[also_a_stranger] == 0
    assert counts[busy] >= 1


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_a_lapse_tallies_nowhere_even_once_it_has_been_recorded(
    implementation, session
):
    """Silence is a fact about a window, never a fact about a judgement.

    A lapse and a decline do the same thing to a line-up and are different facts.
    Filing one as the other would leave the *answers challenges* strand and the
    previous-decline signal reading the same erased history — the exact failure
    the outcomes are kept apart to prevent — and it would price somebody's
    forgotten notification as a refusal of the person who sent it.

    Asserted **on both sides of the sweep**, which is the part that would
    otherwise go untested: the seat already reads as lapsed before anything runs,
    and once ``SeatLapsed`` is in the log it is still not an answer. The sweep
    buys the record and never the ranking.
    """

    port = implementation.build(session)
    organiser, silent = new_uuid(), new_uuid()
    challenge = await _sent(
        session,
        organiser=organiser,
        invitees=(silent,),
        sport=Sport.TENNIS,
        at=_long_enough_ago_to_have_lapsed(),
    )

    assert await port.pairwise_counterparts(organiser) == ()
    assert await port.pairwise_counterparts(silent) == ()

    swept = await _sweep(session, challenge, now=instant(datetime.now(timezone.utc)))
    assert swept == 1

    assert await port.pairwise_counterparts(organiser) == ()
    assert await port.pairwise_counterparts(silent) == ()
    assert await port.open_challenges(organiser) == ()


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_a_challenge_born_of_a_mutual_yes_tallies_nothing(
    implementation, session
):
    """Nobody answered anything, so there is nothing to count.

    Both seats are accepted from birth, because each of them had already said
    *Let's play* to the other and asking either to answer again would make *you
    now have an open game together* not yet true. What that pair is worth is
    already priced by the interest lift, and counting it again as a previous
    accept is the double-count the shape is careful to avoid.

    It is still an **open challenge**, which is the half that must not be lost
    with the other: the two of them have a game together and the exclusion has to
    see it.
    """

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _mutual(session, one=one, other=other, at=_ago(minutes=5))

    assert await port.pairwise_counterparts(one) == ()
    assert await port.pairwise_counterparts(other) == ()
    assert _counterparts(await port.open_challenges(one)) == {other}
    assert _counterparts(await port.open_challenges(other)) == {one}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_an_accept_is_tallied_and_a_completed_line_up_reopens_the_pair(
    implementation, session
):
    """**The accept is counted, and the pair it finished arranging is released.**

    Two demands meet on one arrangement. A seat that accepts is tallied as an
    `ACCEPTED` outcome on the pair, which is what prices `PREVIOUS_ACCEPT`. And
    a singles court whose only invitee accepts is `ON` — every seat accepted, the
    arranging **finished** — so the pair is no longer *open* and each is back in
    the other's pool.

    This is [#343](https://github.com/Raketa02/Raketa/issues/343) and
    `docs/adr/0142` §1, contracted at the port both providers sign. It reversed
    the reading this test used to carry: *open* was `AWAITING_ANSWERS | ON |
    LINE_UP_INCOMPLETE`, so an accepted pair stayed gated for as long as the
    database existed and `PREVIOUS_ACCEPT` was unreachable on every surface. It
    is reachable now — the tally and the ungated row can be held by one pair at
    the same instant, which is precisely what these two assertions say.

    **`app/seeds/screens.py` still names the code in `CANNOT_BE_DRAWN`, and the
    reason there is now about that cohort rather than about this rule.** Every
    accepted seat the seed writes sits on a court still being arranged, so no
    seeded pair reaches this state — a fact about eleven fixtures, which is
    checked where it is stated and not here.
    """

    port = implementation.build(session)
    organiser, invitee = new_uuid(), new_uuid()
    challenge = await _sent(
        session,
        organiser=organiser,
        invitees=(invitee,),
        sport=Sport.TENNIS,
        at=_ago(minutes=10),
    )
    await _answers(session, challenge, invitee, yes=True, at=_ago(minutes=5))

    tallied = _by_player(await port.pairwise_counterparts(organiser))
    assert PairwiseOutcome.ACCEPTED in tallied[invitee]
    assert tallied[invitee][PairwiseOutcome.ACCEPTED].count == 1

    # And the same arrangement, read the other way: they finished arranging a
    # game, so nothing stands between them and the tally is priceable.
    assert await port.open_challenges(organiser) == ()
    assert await port.open_challenges(invitee) == ()


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_an_accept_beside_an_unanswered_seat_keeps_the_pair_open(
    implementation, session
):
    """The line the release runs along, from the side that did **not** move.

    An acceptance on a padel four with a seat still deciding is
    `AWAITING_ANSWERS`, not `ON`: somebody's answer is owed, so those people are
    still arranging a game and every occupied seat is still a counterpart. This
    is exactly the court `app/seeds/relationships.py` writes — one co-invitee in,
    one silent beside them — and the reason `PREVIOUS_ACCEPT` is drawn on no card
    in that cohort even though the platform can now draw it.
    """

    port = implementation.build(session)
    organiser, accepted, silent = (new_uuid() for _ in range(3))
    challenge = await _sent(
        session,
        organiser=organiser,
        invitees=(accepted, silent),
        sport=Sport.PADEL,
        at=_ago(minutes=10),
    )
    await _answers(session, challenge, accepted, yes=True, at=_ago(minutes=5))

    assert _counterparts(await port.open_challenges(organiser)) == {accepted, silent}
    assert _counterparts(await port.open_challenges(accepted)) == {organiser, silent}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_the_pairwise_bound_and_its_order_against_a_history_that_exceeds_it(
    implementation, session
):
    """500 counterparts, newest first — against an arrangement that passes neither
    trivially.

    The bound is what makes a counterpart cut off by it and one fully decayed by
    time **indistinguishable by construction**, and that only holds if the answer
    is ordered before it is cut. An implementation that truncated an unordered
    read would drop an arbitrary five hundred and pass every shape demand above.

    So the arrangement is two people over the bound, each with their own answer at
    their own moment, and the demand asserts the two oldest are the two missing.
    """

    port = implementation.build(session)
    searcher = new_uuid()
    over_the_bound = PAIRWISE_COUNTERPART_BOUND + 2
    people = [new_uuid() for _ in range(over_the_bound)]
    for age, person in enumerate(people):
        challenge = await _sent(
            session,
            organiser=searcher,
            invitees=(person,),
            sport=Sport.TENNIS,
            at=_ago(minutes=age + 2),
        )
        await _answers(
            session, challenge, person, yes=False, at=_ago(minutes=age + 1)
        )

    counterparts = await port.pairwise_counterparts(searcher)

    assert len(counterparts) == PAIRWISE_COUNTERPART_BOUND
    assert len({one.player_id for one in counterparts}) == len(counterparts)
    moments = [one.last_at for one in counterparts]
    assert moments == sorted(moments, reverse=True)
    assert [one.player_id for one in counterparts] == people[
        :PAIRWISE_COUNTERPART_BOUND
    ]


def test_the_send_is_where_the_pair_rule_is_verified_for_real():
    """The gate stays **soft**, and this is the backstop that lets it.

    ``OPEN_CHALLENGE`` fails soft and is deliberately not re-evaluated in the
    read-back: this is embarrassment rather than safety — *the matcher proposes,
    the backend disposes* — and withholding a row on a fact the search itself was
    willing to be wrong about would reopen what ``docs/adr/0109`` closed.

    That argument only holds because something else checks for real. The send
    re-reads the pair rule inside its own transaction, over the whole court, at
    the moment it commits — so a search from an hour ago cannot open a second
    challenge against somebody. This demand records the dependency structurally,
    because the failure it guards against is somebody removing the backstop and
    every test about the soft gate still passing.
    """

    assert FAIL_POSTURE[MatchHistoryQuery] is FailPosture.SOFT
    assert "open_challenges" in signature(SendChallenge.__init__).parameters


# ---------------------------------------------------------------------------
# AtStakeQuery — what a counted result would do to the searcher's Level
# ---------------------------------------------------------------------------


# **The provider ships and the rule exists** (``docs/adr/0139``), so these
# arrange a real world and assert a real answer — through ``rating``'s own
# aggregate, never through the adapter's insides. What is being held to the
# contract is the *pair*: signed, never zero, and the same pair the game will
# deliver if it is played.


async def _rated(session, *, mu: float, sigma: float, sport: Sport = Sport.PADEL):
    """One player carrying a Level, written through the aggregate that owns it.

    Built from the initialised rating and then moved by nothing, because what
    these demands need is *a Level exists* rather than a plausible history — and
    a hand-built stream would be the adapter's own storage detail asserted back
    at it.
    """

    player_id = new_uuid()
    ratings = build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await ratings.save(
        SkillRating.initialise(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport,
            result=_an_assessment_result(mu=mu, sigma=sigma),
            source_assessment_id=new_uuid(),
            occurred_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()
    return player_id


def _an_assessment_result(*, mu: float, sigma: float) -> AssessmentResult:
    band = band_for(mu)
    low, high = likely_range(mu, sigma)
    return AssessmentResult(
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
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_against_an_unrated_pair_is_absent_and_never_zero(
    implementation, session
):
    """The card omits the block; it never prints a pair of zeros.

    A pair with no Level between them is *we have nothing to price this
    against*, and that is the difference between an absence that was measured
    and one that was invented.
    """

    port = implementation.build(session)

    at_stake = await port.counted_game_deltas(
        searcher_id=new_uuid(), opponent_id=new_uuid(), sport=Sport.PADEL
    )

    assert at_stake is None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_one_side_rated_is_still_no_answer(implementation, session):
    """Half a pairing prices nothing, and the absence has one spelling."""

    port = implementation.build(session)
    rated = await _rated(session, mu=3.00, sigma=0.30)

    assert (
        await port.counted_game_deltas(
            searcher_id=rated, opponent_id=new_uuid(), sport=Sport.PADEL
        )
        is None
    )
    assert (
        await port.counted_game_deltas(
            searcher_id=new_uuid(), opponent_id=rated, sport=Sport.PADEL
        )
        is None
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_two_rated_players_are_priced_and_the_pair_is_signed(
    implementation, session
):
    """The demand this port was written for: a real answer, both ways signed."""

    port = implementation.build(session)
    searcher = await _rated(session, mu=3.00, sigma=0.30)
    opponent = await _rated(session, mu=3.00, sigma=0.30)

    at_stake = await port.counted_game_deltas(
        searcher_id=searcher, opponent_id=opponent, sport=Sport.PADEL
    )

    assert at_stake is not None
    assert at_stake.win_delta > 0 > at_stake.loss_delta


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_beating_somebody_above_you_is_worth_more_than_beating_an_equal(
    implementation, session
):
    """A shape demand and not a value one.

    The numbers are the rule's and are held to ``tests/unit/`` against hand-worked
    pairings; what the *contract* owes is that the block a player reads is about
    the person beside it. A port answering one figure for everybody would satisfy
    every other demand here.
    """

    port = implementation.build(session)
    searcher = await _rated(session, mu=3.00, sigma=0.30)
    equal = await _rated(session, mu=3.00, sigma=0.30)
    stronger = await _rated(session, mu=4.00, sigma=0.30)

    against_equal = await port.counted_game_deltas(
        searcher_id=searcher, opponent_id=equal, sport=Sport.PADEL
    )
    against_stronger = await port.counted_game_deltas(
        searcher_id=searcher, opponent_id=stronger, sport=Sport.PADEL
    )

    assert against_stronger.win_delta > against_equal.win_delta
    assert against_stronger.loss_delta > against_equal.loss_delta


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_is_asked_about_a_sport_and_answers_about_that_one(
    implementation, session
):
    """A Level is per ``(player, sport)``, and a padel pair prices no tennis."""

    port = implementation.build(session)
    searcher = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    opponent = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)

    assert (
        await port.counted_game_deltas(
            searcher_id=searcher, opponent_id=opponent, sport=Sport.PADEL
        )
        is not None
    )
    assert (
        await port.counted_game_deltas(
            searcher_id=searcher, opponent_id=opponent, sport=Sport.TENNIS
        )
        is None
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_never_crosses_as_a_pair_that_changes_nothing(
    implementation, session
):
    port = implementation.build(session)

    at_stake = await port.counted_game_deltas(
        searcher_id=new_uuid(), opponent_id=new_uuid(), sport=Sport.TENNIS
    )

    assert at_stake is None or (at_stake.win_delta > 0 > at_stake.loss_delta)


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("port", MATCHER_DEMANDS, ids=lambda port: port.__name__)
def test_every_outward_demand_has_something_answering_it(port):
    """A port nothing implements is a demand nothing runs against.

    It arrives by omission rather than by anybody deciding it — which is exactly
    the shape of failure ``docs/adr/0098`` exists to prevent — so it is asked
    rather than watched for.

    **This is the test that stands under all the parameterised ones.** A port
    whose register row is deleted does not turn its own contract tests red: an
    empty ``parametrize`` collects as *skipped*, and a skipped test is a test
    nobody is watching. Driven against a register with a row removed, this one
    goes red while the two ``AtStakeQuery`` cases quietly skip — which is the
    demonstration, not a footnote.
    """

    assert implementations_of(port)


@pytest.mark.parametrize(
    "implementation",
    REGISTERED_IMPLEMENTATIONS,
    ids=[implementation.name for implementation in REGISTERED_IMPLEMENTATIONS],
)
async def test_a_registered_implementation_answers_the_port_it_registered_against(
    implementation, session
):
    """It implements the port it claims, and it is the class the row names.

    The row's name is what a failure above is reported under, so a row pointing
    at a builder that returns something else would blame the wrong class for a
    broken contract — and the register is exactly the kind of list that keeps its
    old label through a rename.
    """

    assert implementation.port in MATCHER_DEMANDS
    built = implementation.build(session)
    assert isinstance(built, implementation.port)
    assert type(built).__name__ == implementation.name


# ---------------------------------------------------------------------------
# The fail posture, per port
# ---------------------------------------------------------------------------


def test_every_port_says_how_it_fails():
    assert set(FAIL_POSTURE) == set(MATCHER_DEMANDS)


async def _unreadable():
    raise RuntimeError("the provider is down")


async def test_a_gate_that_cannot_be_evaluated_refuses_the_search():
    """A gate that cannot be evaluated excludes — so the whole search refuses.

    Blocks and holds, and the account-state gate beside them: there is no
    degraded answer to fall through to, because *nobody is held* and *we could
    not find out* are not the same sentence and must not become one.
    """

    with pytest.raises(GateDataUnavailable):
        await read_demand(AccountHoldQuery, _unreadable)

    with pytest.raises(GateDataUnavailable):
        await read_demand(AccountStatusQuery, _unreadable)


async def test_a_term_that_cannot_be_evaluated_stands_down_and_the_search_goes_on():
    """History and the pending-pair set fail soft, and the search proceeds.

    Losing a game because we could not remember who you played in March is a
    worse outcome than a slightly duller list, and §7.5's re-verify on the way
    out is the backstop under a duplicate proposal.
    """

    assert await read_demand(MatchHistoryQuery, _unreadable, stood_down=()) == ()
    assert await read_demand(PlayerScoreQuery, _unreadable, stood_down={}) == {}
    assert await read_demand(AtStakeQuery, _unreadable, stood_down=None) is None


async def test_a_gate_cannot_be_handed_a_degraded_answer_to_fall_through_to():
    """Offering a gate something to stand down to is refused at the call site.

    This is what makes the posture a property of the **port** rather than of
    whoever happened to write the call: a caller cannot quietly soften a gate by
    passing it a default, and a caller cannot forget to soften a term, because
    the same function reads both and refuses the mismatch either way.
    """

    with pytest.raises(InvariantViolated):
        await read_demand(AccountHoldQuery, _unreadable, stood_down=frozenset())

    with pytest.raises(InvariantViolated):
        await read_demand(MatchHistoryQuery, _unreadable)


def test_the_two_gates_fail_closed_and_the_three_terms_fail_soft():
    assert FAIL_POSTURE[AccountHoldQuery] is FailPosture.CLOSED
    assert FAIL_POSTURE[AccountStatusQuery] is FailPosture.CLOSED
    assert FAIL_POSTURE[MatchHistoryQuery] is FailPosture.SOFT
    assert FAIL_POSTURE[PlayerScoreQuery] is FailPosture.SOFT
    assert FAIL_POSTURE[AtStakeQuery] is FailPosture.SOFT


# ---------------------------------------------------------------------------
# The shapes, and what they make unwritable
# ---------------------------------------------------------------------------
#
# The tests above ask what an implementation *answers*. These ask what an
# implementation *can* answer, which is where the expensive mistakes are refused:
# a demand that is merely described is satisfiable by accident, and the whole
# return on ``docs/adr/0098`` is that the wrong thing cannot be built rather than
# that somebody notices it was.


def test_a_player_score_cannot_be_supplied_as_one_number():
    """The failure this contract is written against, refused at the type.

    The Player Score is one number in the UI, so the obvious thing for whoever
    builds ``player_score`` to ship is that number — at which point the
    strand-decomposition argument dies quietly and nobody finds out until
    somebody wires the term up. A reading has to carry strands; the published
    figure alone is not a reading, and there is nowhere to put a blend of the
    five in place of them.
    """

    with pytest.raises(InvariantViolated):
        PlayerScoreReading(strands={}, published_score=72)


def test_a_strand_cannot_cross_without_the_evidence_behind_it():
    """Value, numerator, denominator, last observation — none of them optional.

    A bare ``0–100`` cannot distinguish one no-show out of one game from
    thirty-five of thirty-eight, and it would make the absence rule a matter of
    trusting somebody else to send nothing rather than a zero.
    """

    with pytest.raises(TypeError):
        RatioStrand(value=80)  # no numerator, denominator or observation

    assert {field.name for field in fields(RatioStrand)} == {
        "value",
        "numerator",
        "denominator",
        "observed_at",
    }
    assert {field.name for field in fields(SportsmanshipStrand)} == {
        "mean",
        "rating_count",
        "observed_at",
    }


def test_a_hold_read_carries_nothing_that_could_be_scored():
    """Reading ``cases`` to score is impossible here rather than discouraged.

    One question, answered in player ids: no case, no opened-at, no severity, no
    count. *Settles up* is ``player_score``'s to publish from the historical
    record — the prototype computes it from the **live** open case, which
    conflates the strand with the gate. A held player is both excluded here and
    carrying a low *settles up*, and that double reach is intended.
    """

    members = {
        name
        for name, value in vars(AccountHoldQuery).items()
        if callable(value) and not name.startswith("_")
    }
    assert members == {"held_among"}
    assert get_type_hints(AccountHoldQuery.held_among)["return"] == frozenset[UUID]


def test_a_challenge_cannot_be_recorded_without_saying_where_it_came_from():
    """Never an optional field: there is no third answer and no missing one.

    The first caller who finds it inconvenient omits it, the loss is silent, and
    there is no backfill — a search not joined to its outcome is evidence that no
    longer exists.
    """

    with pytest.raises(TypeError):
        OpenChallenge(counterpart_id=new_uuid(), opened_at=None)

    assert ChallengeOrigin.__args__ == (SentFromSearch, SentOutsideASearch)


def test_a_counterpart_carries_both_halves_of_familiarity():
    """``strength`` reads *days since last* **and** *n games played together*.

    ``ranking-weights.md`` §8: ``0.5 ^ (days_since_last / HALF_LIFE) × (1 −
    DEPTH_PHI ⁿ)``. One outcome and one moment per person can supply the first
    and never the second, and a shape that cannot feed the modifier it exists for
    is a demand that was never really made. The counts also keep an accept
    visible under a later decline, which the previous-decline signal needs and a
    single latest-outcome would erase.
    """

    counterpart = PairwiseCounterpart(
        player_id=new_uuid(),
        outcomes={
            PairwiseOutcome.PLAYED: OutcomeTally(
                count=4, last_at=instant(datetime(2026, 6, 1, tzinfo=timezone.utc))
            ),
            PairwiseOutcome.DECLINED: OutcomeTally(
                count=1, last_at=instant(datetime(2026, 8, 1, tzinfo=timezone.utc))
            ),
        },
    )

    assert counterpart.games_played_together == 4
    assert counterpart.last_at == instant(
        datetime(2026, 8, 1, tzinfo=timezone.utc)
    )


def test_a_counterpart_with_nothing_between_you_is_not_a_counterpart():
    """Absence keeps one spelling: they are not in the list at all.

    *You have never played this person* is true of everyone, and a row saying so
    would make familiarity fire identically on every candidate — changing no
    ranking while printing a sentence on every card.
    """

    with pytest.raises(InvariantViolated):
        PairwiseCounterpart(player_id=new_uuid(), outcomes={})


def test_a_tally_counts_something_that_happened():
    with pytest.raises(InvariantViolated):
        OutcomeTally(
            count=0,
            last_at=instant(datetime(2026, 6, 1, tzinfo=timezone.utc)),
        )


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_late_is_one_published_threshold_and_never_a_per_case_judgement(
    implementation, session
):
    """*Keeps plans* has a denominator only if *late* means one thing.

    "One late change in six months" is prose in the prototype with no denominator
    behind it, and a per-case judgement is not a fact and cannot be contracted —
    so the contract demands ``matches`` publish **the single threshold**. The
    method takes no pair, no plan and no case, which is what makes a per-case
    judgement unexpressible rather than discouraged.

    ``None`` today: nothing schedules a plan, so there is no threshold to
    publish. It is absent rather than a number somebody would otherwise pick.
    """

    port = implementation.build(session)

    assert not signature(type(port).late_change_threshold).parameters.keys() - {"self"}
    assert await port.late_change_threshold() is None


def test_all_five_strands_cross_separately_and_keep_their_own_evidence():
    """Five readings in, five readings out, none of them averaged on the way.

    The subset check above says a reading may not invent a sixth strand; this
    says it can carry all five *at once* without them collapsing into each other
    — which is the half that would go wrong if somebody satisfied the shape by
    writing the same figure into every key. Each strand keeps the numerator and
    denominator it was measured from, and sportsmanship keeps a mean and a rating
    count because it is not a ratio.

    **Only two of the five have a provider**, and this reading is hand-built to
    carry all of them: the shape has to keep working the day the other three
    land, and a contract exercised only over what happens to be wired is a
    contract that goes stale quietly (``docs/adr/0140``).
    """

    observed = instant(datetime(2026, 8, 1, tzinfo=timezone.utc))
    ratios = {
        ReliabilityStrand.SHOWS_UP: (95, 38, 40),
        ReliabilityStrand.ANSWERS_CHALLENGES: (70, 14, 20),
        ReliabilityStrand.KEEPS_PLANS: (83, 25, 30),
        ReliabilityStrand.SETTLES_UP: (50, 1, 2),
    }
    reading = PlayerScoreReading(
        strands={
            **{
                strand: RatioStrand(
                    value=value,
                    numerator=numerator,
                    denominator=denominator,
                    observed_at=observed,
                )
                for strand, (value, numerator, denominator) in ratios.items()
            },
            ReliabilityStrand.SPORTSMANSHIP: SportsmanshipStrand(
                mean=4.6,
                rating_count=9,
                observed_at=instant(datetime(2026, 7, 1, tzinfo=timezone.utc)),
            ),
        },
        published_score=84,
    )

    assert set(reading.strands) == set(ReliabilityStrand)
    for strand, (value, numerator, denominator) in ratios.items():
        observation = reading.strands[strand]
        assert (observation.value, observation.numerator, observation.denominator) == (
            value,
            numerator,
            denominator,
        )
    assert reading.strands[ReliabilityStrand.SPORTSMANSHIP].mean == 4.6
    assert reading.strands[ReliabilityStrand.SPORTSMANSHIP].rating_count == 9
    # The horizon reads one moment over the whole score, not one per strand.
    assert reading.most_recent_observation == observed


def test_the_five_strands_are_the_platform_s_five():
    """The keys are the engine's closed vocabulary, not a second spelling of it.

    A reading keyed by a locally-declared enum would satisfy every other
    assertion here and still be a second copy of a closed vocabulary, free to
    drift — the failure ``tests/unit/test_social_tag_vocabulary.py`` refuses for
    the Social tags. It binds twice over now: ``player_score`` publishes these
    names too, and it imports the same enum rather than declaring its own
    (``docs/adr/0140``).

    **There were six.** *Confirms results* was struck rather than deferred
    (``docs/adr/0137``): an unconfirmed result is a fact about a pair and a strand
    is a verdict about a person, and every denominator tried on it docked
    somebody ADR-0049 protects. It is listed nowhere because a withdrawn demand
    is withdrawn, not carried.
    """

    assert [strand.value for strand in ReliabilityStrand] == [
        "SHOWS_UP",
        "ANSWERS_CHALLENGES",
        "KEEPS_PLANS",
        "SETTLES_UP",
        "SPORTSMANSHIP",
    ]


def test_a_strand_cannot_claim_more_good_outcomes_than_opportunities():
    with pytest.raises(InvariantViolated):
        RatioStrand(
            value=100,
            numerator=41,
            denominator=40,
            observed_at=instant(datetime(2026, 8, 1, tzinfo=timezone.utc)),
        )
