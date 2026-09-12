"""When a mutual may mint a second game, and when it may not.

The mint asks **two** questions and both must pass (``docs/adr/0152``): the
ordinary one-open-challenge-per-pair rule the send asks, and its own idempotence
key — *has a mutual between these two, in this sport, already minted a game that
is not finished with?* This file is the second question's whole life, from both
sides.

Run against a real (SQLite) session and the real adapters on both sides of the
``challenges -> games`` seam, because what is under test is precisely what a
double would have to invent: which challenges the log says a mutual minted, and
what ``games`` says has settled.

Five claims, and each one fails differently.

**The guard has a release, and this is the shape #343 was.** A mutual-born
challenge is ``ON`` for ever — every seat accepted at birth, no lapse, no
decline, no withdraw exit — so the guard that asked *does a challenge still stand
between these two* held a pair for the life of the database. Every test here that
folds a clock forward is that failure, asked again.

**Settled is not played.** A ghost game — its entry window closed with nobody
ever saying it happened — releases the pair, and reading *settled* as *played*
is the obvious misimplementation: it would hold two people on the strength of an
evening that never occurred.

**A game that was played releases nobody until its result settles.** The other
half of the same word, and the reason the read is not ``was_played_at``.

**Per sport, and the pair rule is not.** A tennis game minted from a mutual has
nothing to say about a padel one; two people already *arranging* something are
refused in every sport, as they always were.

**A read that cannot answer refuses the mint and does not raise.** The mint runs
inside ``express_interest``'s transaction, and a raise would roll back somebody's
own yes — which is not the thing being refused.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_open_challenge_query,
    build_planned_game_handover,
    build_settled_game_query,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.commands import (
    OpenFromMutualInterestCommand,
)
from app.modules.challenges.application.open_from_mutual_interest import (
    OpenChallengeFromMutualInterest,
)
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.player_profile.domain.availability import Window
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import (
    ENTRY_GRACE,
    PLAN_HORIZON,
    PROPOSAL_WINDOW,
)
from app.shared.ids import new_uuid
from tests.unit.challenge_world import a_safe_court

ALICE = new_uuid()
BOB = new_uuid()
SEARCH = new_uuid()

MINTED_AT = instant(datetime(2026, 8, 30, 12, tzinfo=timezone.utc))
#: Past the plan horizon and its entry grace: nobody ever said the game happened,
#: so it is a ghost — and a ghost is settled.
GHOSTED = instant(MINTED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(minutes=1))


class FrozenClock:
    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


def _challenges(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _games(session):
    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _mint(
    session, *, at: Instant = MINTED_AT, settled_games=None
) -> OpenChallengeFromMutualInterest:
    return OpenChallengeFromMutualInterest(
        challenges=_challenges(session),
        open_challenges=build_open_challenge_query(session),
        settled_games=settled_games or build_settled_game_query(session),
        safety=a_safe_court([ALICE, BOB]),
        clock=FrozenClock(at),
        planned_games=build_planned_game_handover(session),
    )


async def _tap(
    session_factory,
    *,
    sport: Sport = Sport.TENNIS,
    at: Instant = MINTED_AT,
    settled_games=None,
    one: UUID = ALICE,
    other: UUID = BOB,
) -> UUID | None:
    """One *Let's play* mutual, minted the way ``express_interest`` mints one."""

    async with session_factory() as session:
        minted = await _mint(session, at=at, settled_games=settled_games).execute(
            OpenFromMutualInterestCommand(
                sport=sport, player_id=one, other_player_id=other
            )
        )
        await session.commit()
        return minted


async def _play_and_propose(session_factory, challenge_id: UUID, *, at: Instant):
    """Somebody says *we played, here is the score* — one score, unanswered."""

    async with session_factory() as session:
        games = _games(session)
        game = await games.for_challenge(challenge_id)
        assert game is not None
        game.state_result(
            by=ALICE,
            score=Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
            occurred_at=at,
        )
        await games.save(game)
        await session.commit()


async def _standing(session_factory, challenge_id: UUID, *, at: Instant):
    async with session_factory() as session:
        game = await _games(session).for_challenge(challenge_id)
        assert game is not None
        return game.standing_at(at)


# ---------------------------------------------------------------------------
# The release
# ---------------------------------------------------------------------------


async def test_a_ghosted_game_lets_the_pair_mint_a_second_one(session_factory):
    """**Settled is not played**, and this is the reading that had to be decided.

    ``NEVER_PLAYED`` is settled: the entry window closed and nobody ever said the
    game happened, so nothing more will happen to it and two people whose
    arranged game evaporated may try again. Reading *settled* as *played* would
    hold them on a game that never occurred — the same blocked-by-nothing shape
    ``docs/adr/0152`` exists to remove.
    """

    first = await _tap(session_factory)
    assert first is not None
    assert (
        await _standing(session_factory, first, at=GHOSTED)
        is GameStanding.NEVER_PLAYED
    )

    second = await _tap(session_factory, at=GHOSTED)

    assert second is not None
    assert second != first


async def test_a_confirmed_result_lets_the_pair_mint_a_second_one(session_factory):
    """The other way a game finishes: they played, and a score is agreed.

    One score on the table, unanswered until its window closes — *silence
    confirms*, which is a clock passing and nothing that announces itself. From
    that instant the mutual has finished with what it minted.
    """

    played_at = instant(MINTED_AT + timedelta(hours=2))
    settled_at = instant(played_at + PROPOSAL_WINDOW + timedelta(minutes=1))

    first = await _tap(session_factory)
    assert first is not None
    await _play_and_propose(session_factory, first, at=played_at)
    assert (
        await _standing(session_factory, first, at=settled_at)
        is GameStanding.CONFIRMED
    )

    second = await _tap(session_factory, at=settled_at)

    assert second is not None
    assert second != first


async def test_the_hold_is_on_the_sport_the_mutual_was_in(session_factory):
    """**The permanence that survived on this path, gone.**

    An ``Interest`` is keyed ``(from, to, sport)`` and expires; the guard
    justified by *a repeat tap is the same yes pressed twice* was cross-sport and
    eternal, so a pair whose tennis game was minted from a mutual could never be
    given a padel one, ever. A padel yes is not a tennis yes pressed twice.

    Asserted here while the tennis game is still **unsettled**, because that is
    the state the old rule was wrong in and is strictly stronger than asserting
    it after everything has finished.
    """

    first = await _tap(session_factory)
    assert first is not None

    a_day_on = instant(MINTED_AT + timedelta(days=1))

    # Tennis is still held, and now says what by: the game it already minted.
    assert await _tap(session_factory, at=a_day_on) == first
    # Padel was never this mutual's to hold, and mints its own.
    padel = await _tap(session_factory, sport=Sport.PADEL, at=a_day_on)
    assert padel is not None and padel != first


async def test_a_mutual_born_challenge_holds_nobody_a_year_on(session_factory):
    """The fold-forward #343 was, run against the guard that replaced it.

    A mutual-born challenge is still ``ON`` a year later — it can never lapse,
    never be declined and has no withdraw exit — so the old guard answered *a
    challenge stands between these two* for ever, in every sport. What answers
    now is *is the game it minted finished with*, and a year on it is.
    """

    assert await _tap(session_factory) is not None

    a_year_on = instant(MINTED_AT + timedelta(days=365))

    assert await _tap(session_factory, at=a_year_on) is not None


# ---------------------------------------------------------------------------
# The hold
# ---------------------------------------------------------------------------


async def test_an_unsettled_game_answers_with_the_game_they_already_have(
    session_factory,
):
    """One mutual mints one game — and **says which one** (``docs/adr/0154``).

    The refusal is still a refusal: nothing is minted, no second result window
    opens, and there is no raise, because there is no organiser at a screen and
    no press to refuse. What changes is that the answer is no longer silence.
    The guard is holding these two on a game they already have, it has that
    game's id in its hand, and discarding it is what left the pair told *you
    both said yes* with nothing behind it.
    """

    first = await _tap(session_factory)
    assert first is not None

    a_day_on = instant(MINTED_AT + timedelta(days=1))
    assert (
        await _standing(session_factory, first, at=a_day_on)
        is GameStanding.AWAITING_ENTRY
    )

    assert await _tap(session_factory, at=a_day_on) == first


async def test_the_answer_to_a_repeat_tap_is_not_a_second_mint(session_factory):
    """The claim above, from the side that would make it a catastrophe.

    Answering with an id must not be mistaken for having produced one. A second
    challenge here is a second game and a second result window between the same
    two people, which is the whole of what 0152's guard exists to prevent — so
    the log is asked directly rather than inferred from the answer.
    """

    first = await _tap(session_factory)
    assert first is not None

    a_day_on = instant(MINTED_AT + timedelta(days=1))
    assert await _tap(session_factory, at=a_day_on) == first

    async with session_factory() as session:
        assert await build_open_challenge_query(
            session
        ).mutual_born_challenges_that_became_games(
            ALICE, BOB, sport=Sport.TENNIS, now=a_day_on
        ) == (first,)


async def test_a_played_game_holds_the_pair_until_its_result_settles(
    session_factory,
):
    """**Settled is not played, read the other way round.**

    They played and a score is on the table, and until its window closes nothing
    has settled. A guard written on *was it played* would release here — which is
    the wrong half of the word, and the failure this asserts against.
    """

    played_at = instant(MINTED_AT + timedelta(hours=2))
    just_after = instant(played_at + timedelta(minutes=1))

    first = await _tap(session_factory)
    assert first is not None
    await _play_and_propose(session_factory, first, at=played_at)
    assert (
        await _standing(session_factory, first, at=just_after)
        is GameStanding.AWAITING_ANSWER
    )

    assert await _tap(session_factory, at=just_after) == first


async def test_a_half_built_doubles_mutual_holds_the_pair(session_factory):
    """A padel mutual is half a game, and the **pair rule** is what holds them.

    Nothing has been minted for ``games`` to have an opinion about, so the second
    question is silent and the first one — *are these two still arranging* — does
    the holding. When #325's withdraw ships and ends that court, the pair rule
    releases and there is nothing else left holding them, which is how a
    mutual-born challenge that produced no game comes to hold nobody.
    """

    first = await _tap(session_factory, sport=Sport.PADEL)
    assert first is not None

    async with session_factory() as session:
        stored = await _challenges(session).load(first)
        assert stored is not None
        assert stored.is_being_arranged_at(MINTED_AT)
        assert not stored.has_become_a_game_at(MINTED_AT)
        assert await build_open_challenge_query(session).open_pairs_among(
            [ALICE, BOB], now=GHOSTED
        ) == frozenset({frozenset({ALICE, BOB})})

    a_day_on = instant(MINTED_AT + timedelta(days=1))
    assert await _tap(session_factory, sport=Sport.PADEL, at=a_day_on) is None


async def test_a_standing_sent_challenge_refuses_the_mint(session_factory):
    """The pair rule, asked here **deliberately** rather than by accident.

    Two people already arranging a game must not be given a second one, and the
    idempotence key cannot catch it: no mutual minted that challenge. Today's
    shape caught it by reading a superset of the pair rule, which is exactly how
    the two questions came to be confused (``docs/adr/0152`` §2).
    """

    async with session_factory() as session:
        await _challenges(session).save(
            Challenge.sent(
                challenge_id=new_uuid(),
                sport=Sport.TENNIS,
                mode=SearchMode.FOR_FUN,
                window=Window.ANY,
                organiser_id=ALICE,
                arrangement=(
                    SeatPlan(side=Side.A, player_id=ALICE),
                    SeatPlan(
                        side=Side.B,
                        player_id=BOB,
                        origin=SentFromSearch(search_id=SEARCH, position=1),
                    ),
                ),
                occurred_at=MINTED_AT,
            )
        )
        await session.commit()

    assert await _tap(session_factory) is None


# ---------------------------------------------------------------------------
# The read that could not answer
# ---------------------------------------------------------------------------


class _ASettledReadThatCannotAnswer:
    """A ``SettledGameQuery`` whose provider is down.

    It raises rather than answering emptily, because *nothing has settled* and
    *I could not tell* must not be the same answer to a guard — that is the one
    way a hold stops holding in silence.
    """

    def __init__(self) -> None:
        self.asked: list[frozenset[UUID]] = []

    async def settled_among(self, challenge_ids, *, now):
        self.asked.append(frozenset(challenge_ids))
        raise RuntimeError("the games log could not be read")


async def test_a_settled_read_that_raises_mints_nothing_and_does_not_raise(
    session_factory,
):
    """**Fail closed, and let the yes stand.**

    A raise would reach the only thing in this transaction: somebody's own *Let's
    play*. Losing that to a hiccup is strictly worse than the pair having a
    mutual with no second game — and the next tap tries again, which is what
    makes failing closed defensible rather than merely safe.

    **What this proves and what it borrows.** It drives the mint directly, so
    what it proves is that nothing escapes ``execute`` and that the transaction
    the mint was called inside is still live and still commits afterwards. That
    the *interest row* in it survives is ``express_interest``'s own half, held by
    ``tests/api/test_challenges.py``'s
    ``test_a_gate_that_cannot_be_read_costs_the_game_and_never_the_yes`` — the
    same path with the block gate broken instead of this read. It is not
    asserted end to end for **this** read because the settled question is only
    reached once a mutual-born challenge has become a game, which needs a
    singles sport: the API world deals padel, a padel mutual is half a game, and
    there is no route that invites anybody into one.
    """

    first = await _tap(session_factory)
    assert first is not None

    unavailable = _ASettledReadThatCannotAnswer()
    a_day_on = instant(MINTED_AT + timedelta(days=1))

    async with session_factory() as session:
        minted = await _mint(
            session, at=a_day_on, settled_games=unavailable
        ).execute(
            OpenFromMutualInterestCommand(
                sport=Sport.TENNIS, player_id=ALICE, other_player_id=BOB
            )
        )
        # The transaction the yes lives in is still usable and still commits:
        # nothing here rolled anything back.
        await session.commit()

        assert minted is None
        assert unavailable.asked == [frozenset({first})]

    # And the retry the fail-closed posture depends on still works, once the
    # game it was holding on has settled.
    assert await _tap(session_factory, at=GHOSTED) is not None


async def test_a_first_mint_never_asks_the_settled_read(session_factory):
    """Two people with nothing between them are not held by an outage.

    There is no id to ask about, so the read is not made — which is what keeps a
    provider being down from refusing every first mint on the platform.
    """

    unavailable = _ASettledReadThatCannotAnswer()

    minted = await _tap(session_factory, settled_games=unavailable)

    assert minted is not None
    assert unavailable.asked == []
