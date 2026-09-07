"""The five facts a send re-verifies, and the refusal that names nobody.

Run against a real (SQLite) session for the two reads that fold the log — the
pair rule and *did anything get written* — and against hand-written stubs for the
four gates, because what those assert is a **verdict** and a real adapter would
only add a second thing that could be wrong.

Four claims, and each one fails differently.

**The send refuses whole, so the proof is an absence.** A partial send that
dropped one invitee would hand the organiser an arrangement they did not choose;
the only way to assert that it did not happen is that afterwards there is no
challenge at all.

**Every gate binds every pair.** A four contains six pairs and the organiser is
in three of them, so the block that matters most here is one between two
*invitees* — a pair no shortlist ever asked about.

**No refusal names anybody.** Not in the message, not in ``details``, not in the
type. It is asserted over the refusal's whole spelling rather than over a field,
because the field that leaks is the one nobody thought to check.

**A mutual yes is minted under the same check.** ``resolve_origin`` has no
freshness bound and a search record never expires, so two month-old yeses with a
block taken since would otherwise walk a challenge past every gate in the
product. There is no organiser standing there and no screen to refuse to, so the
whole observable is that no challenge exists afterwards.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_open_challenge_query,
    build_planned_game_opening,
)
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.commands import (
    OpenFromMutualInterestCommand,
    SeatChoice,
    SendChallengeCommand,
)
from app.modules.challenges.application.open_from_mutual_interest import (
    OpenChallengeFromMutualInterest,
)
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.domain.errors import (
    AChallengeNeedsAnInvitee,
    TheCourtDidNotComeFromThatSearch,
    TheGatesCouldNotBeEvaluated,
    TheLineUpIsNoLongerSendable,
)
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import Side
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.shared.domain.errors import AccountHeld
from app.shared.ids import new_uuid
from tests.unit.challenge_world import (
    StubAccounts,
    StubBlocks,
    StubHolds,
    StubOrigins,
    StubProfile,
    StubProfiles,
    a_safe_court,
    everybody_admissible,
)
from tests.unit.fake_event_store import CountingUnitOfWork

ORGANISER = new_uuid()
ALICE = new_uuid()
BOB = new_uuid()
CAROL = new_uuid()
SEARCH = new_uuid()
ANOTHER_SEARCH = new_uuid()

COURT = (ORGANISER, ALICE, BOB, CAROL)
SENT_AT = instant(datetime(2026, 8, 30, 12, tzinfo=timezone.utc))


class FrozenClock:
    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


def a_padel_choice(organiser, *invitees) -> tuple[SeatChoice, ...]:
    sides = (Side.A, Side.B, Side.B)
    return (SeatChoice(side=Side.A, player_id=organiser),) + tuple(
        SeatChoice(side=side, player_id=player_id)
        for player_id, side in zip(invitees, sides, strict=True)
    )


def _repository(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _send(session, *, safety=None, origins=None) -> SendChallenge:
    return SendChallenge(
        challenges=_repository(session),
        open_challenges=build_open_challenge_query(session),
        origins=origins or StubOrigins(known={SEARCH, ANOTHER_SEARCH}),
        safety=safety or a_safe_court(COURT),
        uow=CountingUnitOfWork(),
        clock=FrozenClock(SENT_AT),
    )


async def _a_full_send(session, *, safety=None, origins=None):
    return await _send(session, safety=safety, origins=origins).execute(
        SendChallengeCommand(
            organiser_id=ORGANISER,
            search_id=SEARCH,
            court=a_padel_choice(*COURT),
        )
    )


async def _nothing_was_written(session) -> None:
    """The whole-send rule, asserted the only way it can be: by an absence."""

    pairs = await build_open_challenge_query(session).open_pairs_among(
        COURT, now=SENT_AT
    )
    assert pairs == frozenset(), "a refused send wrote a challenge"


# ---------------------------------------------------------------------------
# Demand 1 — a blocked invitee leaves no challenge afterwards
# ---------------------------------------------------------------------------


async def test_a_block_between_two_invitees_refuses_the_whole_send(session_factory):
    """The pair no shortlist ever asked about, and the organiser is in neither
    half of it."""

    async with session_factory() as session:
        blocked = StubBlocks(pairs={frozenset({ALICE, BOB})})

        with pytest.raises(TheLineUpIsNoLongerSendable):
            await _a_full_send(
                session, safety=a_safe_court(COURT, blocks=blocked)
            )

        await _nothing_was_written(session)


async def test_a_block_against_the_organiser_refuses_it_too(session_factory):
    async with session_factory() as session:
        blocked = StubBlocks(pairs={frozenset({ORGANISER, CAROL})})

        with pytest.raises(TheLineUpIsNoLongerSendable):
            await _a_full_send(
                session, safety=a_safe_court(COURT, blocks=blocked)
            )

        await _nothing_was_written(session)


async def test_the_refusal_names_nobody(session_factory):
    """A payload naming the withheld seat would be a block detector, handed to
    the one person a block is meant to be invisible to."""

    async with session_factory() as session:
        blocked = StubBlocks(pairs={frozenset({ALICE, BOB})})

        with pytest.raises(TheLineUpIsNoLongerSendable) as refusal:
            await _a_full_send(
                session, safety=a_safe_court(COURT, blocks=blocked)
            )

        spelled = str(refusal.value) + str(refusal.value.details)
        assert refusal.value.details == {}
        assert not any(str(player) in spelled for player in COURT)


# ---------------------------------------------------------------------------
# The other three fail-closed gates, and the order they are refused in
# ---------------------------------------------------------------------------


async def test_a_held_invitee_refuses_the_send(session_factory):
    async with session_factory() as session:
        with pytest.raises(TheLineUpIsNoLongerSendable):
            await _a_full_send(
                session,
                safety=a_safe_court(COURT, holds=StubHolds(frozenset({BOB}))),
            )

        await _nothing_was_written(session)


async def test_the_organisers_own_hold_refuses_at_the_entry_point(session_factory):
    """**The same ``account_held`` the search returns.** A hold that stops you
    searching but lets you send invitations is that hole with the blast radius
    pointed at other people."""

    async with session_factory() as session:
        with pytest.raises(AccountHeld) as refusal:
            await _a_full_send(
                session,
                safety=a_safe_court(COURT, holds=StubHolds(frozenset({ORGANISER}))),
            )

        assert refusal.value.code == "account_held"
        await _nothing_was_written(session)


async def test_an_account_that_may_not_be_shown_refuses_the_send(session_factory):
    async with session_factory() as session:
        with pytest.raises(TheLineUpIsNoLongerSendable):
            await _a_full_send(
                session,
                safety=a_safe_court(
                    COURT, accounts=StubAccounts(frozenset({CAROL}))
                ),
            )

        await _nothing_was_written(session)


async def test_the_mutual_gender_preference_binds_two_invitees(session_factory):
    """ADR-0096 chose mutuality so a one-directional filter would not leave a
    woman open to every man who searched ``ANY`` — and under a searcher-only gate
    she is open to every man a **third party** seats beside her."""

    async with session_factory() as session:
        profiles = everybody_admissible(COURT)
        profiles[ALICE] = StubProfile(
            gender=Gender.WOMAN, gender_preference=GenderPreference.WOMEN_ONLY
        )
        profiles[BOB] = StubProfile(
            gender=Gender.MAN, gender_preference=GenderPreference.ANY
        )

        with pytest.raises(TheLineUpIsNoLongerSendable):
            await _a_full_send(
                session, safety=a_safe_court(COURT, profiles=StubProfiles(profiles))
            )

        await _nothing_was_written(session)


async def test_a_player_with_no_profile_cannot_clear_the_gate(session_factory):
    """A gate that cannot be evaluated excludes, and a court is built out of an
    index whose rows outlive the profiles they were folded from."""

    async with session_factory() as session:
        profiles = everybody_admissible(COURT)
        del profiles[CAROL]

        with pytest.raises(TheLineUpIsNoLongerSendable):
            await _a_full_send(
                session, safety=a_safe_court(COURT, profiles=StubProfiles(profiles))
            )

        await _nothing_was_written(session)


AN_EMPTY_COURT = (
    SeatChoice(side=Side.A, player_id=ORGANISER),
    SeatChoice(side=Side.A),
    SeatChoice(side=Side.B),
    SeatChoice(side=Side.B),
)


async def test_nobody_to_invite_is_refused_before_anybody_elses_state_is_read(
    session_factory,
):
    """It is a fact about the send's shape and needs no reads: telling an
    organiser their line-up went stale when they invited nobody sends them
    refreshing a screen that was never wrong."""

    async with session_factory() as session:
        send = _send(
            session,
            safety=a_safe_court(COURT, blocks=StubBlocks(pairs={frozenset(COURT[:2])})),
        )

        with pytest.raises(AChallengeNeedsAnInvitee):
            await send.execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=AN_EMPTY_COURT,
                )
            )


async def test_nobody_to_invite_outranks_a_search_that_is_not_yours(session_factory):
    """The order asserted where it can actually fail: **before anything is
    read**, including the origin.

    A stub that already knew the search would let this pass whatever the order
    was, so the search is one nothing will place. What must not happen is being
    told to go and look at a screen that was never wrong.
    """

    async with session_factory() as session:
        send = _send(session, origins=StubOrigins(known=set()))

        with pytest.raises(AChallengeNeedsAnInvitee):
            await send.execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=AN_EMPTY_COURT,
                )
            )


async def test_your_own_hold_outranks_a_search_that_is_not_yours(session_factory):
    """The hold is about the caller and nobody else, so it is asked before a
    single fact about another person — or about a search that may not be
    theirs — is read."""

    async with session_factory() as session:
        send = _send(
            session,
            safety=a_safe_court(COURT, holds=StubHolds(frozenset({ORGANISER}))),
            origins=StubOrigins(known=set()),
        )

        with pytest.raises(AccountHeld):
            await send.execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_padel_choice(*COURT),
                )
            )


async def test_a_gate_that_cannot_be_read_refuses_rather_than_admitting(
    session_factory,
):
    """*Nobody is blocked* and *we could not find out* are different sentences
    and must not become one."""

    async with session_factory() as session:
        with pytest.raises(TheGatesCouldNotBeEvaluated) as refusal:
            await _a_full_send(
                session,
                safety=a_safe_court(COURT, blocks=StubBlocks(unavailable=True)),
            )

        assert refusal.value.status_code == 503
        await _nothing_was_written(session)


# ---------------------------------------------------------------------------
# The origin the court was built on
# ---------------------------------------------------------------------------


async def test_a_court_citing_a_search_that_is_not_yours_is_refused(session_factory):
    async with session_factory() as session:
        with pytest.raises(TheCourtDidNotComeFromThatSearch):
            await _send(session, origins=StubOrigins(known=set())).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_padel_choice(*COURT),
                )
            )

        await _nothing_was_written(session)


async def test_every_invitation_cites_its_own_seats_position(session_factory):
    """**Per seat, never per challenge.** One doubles send from one search at
    three positions is three origins with three positions, which is the join the
    search telemetry needs."""

    async with session_factory() as session:
        challenge_id = await _a_full_send(session)
        await session.commit()

        stored = await _repository(session).load(challenge_id)
        assert stored is not None
        invited = {
            seat.player_id: seat.origin
            for seat in stored.seats
            if seat.player_id is not None and seat.player_id != ORGANISER
        }
        assert set(invited) == {ALICE, BOB, CAROL}
        assert all(
            isinstance(origin, SentFromSearch) and origin.search_id == SEARCH
            for origin in invited.values()
        )
        assert len({origin.position for origin in invited.values()}) == 3
        organiser_seat = next(
            seat for seat in stored.seats if seat.player_id == ORGANISER
        )
        assert organiser_seat.origin is None, "the organiser was not invited"


async def test_the_window_and_the_sport_come_from_the_search(session_factory):
    """There is no window picker anywhere: a player changes their window by
    changing their grid, which is the same act that changes their matches."""

    async with session_factory() as session:
        origins = StubOrigins(known={SEARCH}, sport=Sport.PADEL)
        challenge_id = await _a_full_send(session, origins=origins)
        await session.commit()

        stored = await _repository(session).load(challenge_id)
        assert stored is not None
        assert stored.sport is origins.sport
        assert stored.window is origins.window
        assert stored.mode is origins.mode


# ---------------------------------------------------------------------------
# Demand 3 — two stale searches with a block between them mint nothing
# ---------------------------------------------------------------------------


def _mint(session, *, safety=None) -> OpenChallengeFromMutualInterest:
    return OpenChallengeFromMutualInterest(
        challenges=_repository(session),
        open_challenges=build_open_challenge_query(session),
        safety=safety or a_safe_court([ALICE, BOB]),
        clock=FrozenClock(SENT_AT),
        planned_games=build_planned_game_opening(session),
    )


async def test_a_mutual_from_two_stale_yeses_with_a_block_between_them_mints_nothing(
    session_factory,
):
    """A *Let's play* may cite a month-old deal — a search record is immutable and
    never expires — so this is the only gate standing between a block and a
    challenge minted inline with nobody looking."""

    async with session_factory() as session:
        blocked = StubBlocks(pairs={frozenset({ALICE, BOB})})

        minted = await _mint(
            session, safety=a_safe_court([ALICE, BOB], blocks=blocked)
        ).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

        assert minted is None
        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ALICE, BOB], now=SENT_AT
        )
        assert pairs == frozenset(), "a blocked pair was given a challenge"


async def test_a_mutual_between_two_admissible_players_opens_the_game(
    session_factory,
):
    """**A singles mutual is a finished arrangement the instant it exists.**

    Both seats are accepted from birth and a tennis court seats two, so this
    challenge is ``ON`` before anybody has done anything to it — which is why
    ``open_from_mutual_interest`` hands it straight to ``games``. The pair rule
    therefore holds nobody (``docs/adr/0142`` §1): they are not *arranging*, they
    have arranged. The challenge still stands, and the two reads say so
    separately, which is the whole reason there are two of them.
    """

    async with session_factory() as session:
        minted = await _mint(session).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

        assert minted is not None
        stored = await _repository(session).load(minted)
        assert stored is not None
        assert stored.players_in_it_at(SENT_AT) == frozenset()
        assert stored.players_seated_at(SENT_AT) == frozenset({ALICE, BOB})
        assert all(seat.is_accepted() for seat in stored.seats)


async def test_a_second_mutual_mints_nothing_while_the_first_stands(session_factory):
    """One game per mutual, and a second tap must not become a second game.

    **This is refused by the mint's own question and no longer by the pair
    rule.** Releasing a completed line-up (``docs/adr/0142`` §1) took the pair
    rule out from under this: a singles mutual is ``ON`` at birth, so the two of
    them are released the instant they are minted, and *Let's play* is a button
    that says it costs nothing. What refuses a second one is
    ``standing_pairs_among`` — *a challenge already stands between these two* —
    which is a different question from *are they still arranging*, asked here
    and nowhere else.
    """

    async with session_factory() as session:
        first = await _mint(session).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

    async with session_factory() as session:
        again = await _mint(session).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.PADEL, player_id=BOB, other_player_id=ALICE
            )
        )
        await session.commit()

        assert first is not None
        assert again is None


async def test_a_repeat_tap_on_the_same_mutual_mints_nothing(session_factory):
    """**The tap that says it costs nothing, pressed twice, in one sport.**

    ``express_interest`` mints on the *mutual* and never on whether this tap
    wrote a row, because a repeat tap is the platform's one chance to retry a
    mint that a gate refused. Every other repeat tap has to be refused here, and
    a singles mutual is the case with nothing else left to refuse it: it is
    ``ON`` at birth, so the pair rule released it a moment ago. Without this
    check the same two people collect a challenge, a game, a result window and a
    rating input per press.
    """

    async with session_factory() as session:
        first = await _mint(session).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

    async with session_factory() as session:
        again = await _mint(session).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

        assert first is not None
        assert again is None


async def test_a_repeat_tap_retries_a_mint_a_gate_refused(session_factory):
    """The half the guard must **not** cost, and the reason the mint is not
    hung off *did this tap write a row*.

    A month-old pair of yeses whose mint was refused by a block have a mutual
    and no game. The block is lifted; the next tap is the only occasion the
    platform ever gets to open it, and nothing stands between them to refuse it
    with.
    """

    async with session_factory() as session:
        refused = await _mint(
            session,
            safety=a_safe_court(
                [ALICE, BOB], blocks=StubBlocks(pairs={frozenset({ALICE, BOB})})
            ),
        ).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()
        assert refused is None

    async with session_factory() as session:
        opened = await _mint(session).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

        assert opened is not None


async def test_a_gate_that_cannot_be_read_mints_nothing_and_does_not_raise(
    session_factory,
):
    """*A gate that cannot be evaluated excludes* — and on this path excluding
    means minting nothing, never refusing the tap.

    A raise would reach the only thing in this transaction: somebody\'s own
    *Let\'s play*. Losing that to a hiccup in a gate query is strictly worse than
    the pair having a mutual with no game opened, and the next tap tries again.
    """

    async with session_factory() as session:
        minted = await _mint(
            session,
            safety=a_safe_court([ALICE, BOB], blocks=StubBlocks(unavailable=True)),
        ).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

        assert minted is None
        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ALICE, BOB], now=SENT_AT
        )
        assert pairs == frozenset()


async def test_a_held_player_is_not_given_a_mutual_born_challenge(session_factory):
    async with session_factory() as session:
        minted = await _mint(
            session,
            safety=a_safe_court([ALICE, BOB], holds=StubHolds(frozenset({BOB}))),
        ).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        await session.commit()

        assert minted is None
