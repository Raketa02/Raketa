"""One open challenge per pair, across every sport — read off the log and the clock.

Run against the real adapter and a real (SQLite) session rather than a double,
because what is asserted is exactly what a double would have to invent: the match
on the serialized seats that finds every challenge a player is in, and the fold
that decides who is still in it.

Four claims:

**Sharing a line-up makes a pair.** Every occupied seat but your own is somebody
you have an open game with — co-invitees and organiser alike — so a four yields
six pairs and not three.

**The rule is across every sport.** Two people are either arranging a game or
they are not; asking for padel while a tennis challenge sits unanswered is
pestering with a sport chip on it. This is the thing a build session is likeliest
to get wrong, so it is asserted on a *different* sport rather than on the same
one.

**A departed seat releases the pair immediately.** A decline, or a window that
passed with **no sweep having run**, and that person is a stranger to everybody
else on the court once more.

**The send refuses whole and names nobody.** One refusal for the press, with no
player id anywhere in it.

And a fifth about the port's **other** question, which is not that rule and is
asserted against confusing it with one: *has a mutual between these two already
minted a game in this sport* is the mint's idempotence key — mutual-born only,
one sport, and about the two whose yeses met rather than about everybody who
ended up on the court (``docs/adr/0152``).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_open_challenge_query,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.commands import (
    SeatChoice,
    SendChallengeCommand,
)
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import (
    AnOpenChallengeStandsWithThisPair,
)
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.unit.challenge_world import StubOrigins, a_safe_court
from tests.unit.fake_event_store import CountingUnitOfWork

ORGANISER = new_uuid()
ALICE = new_uuid()
BOB = new_uuid()
CAROL = new_uuid()
STRANGER = new_uuid()
SEARCH = new_uuid()


def at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 8, 30, 12, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


SENT_AT = at(0)
INSIDE = at(1)
OUTSIDE = instant(SENT_AT + ANSWER_WINDOW + timedelta(minutes=1))


class FrozenClock:
    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


def invited(player_id, side: Side, position: int) -> SeatPlan:
    return SeatPlan(
        side=side,
        player_id=player_id,
        origin=SentFromSearch(search_id=SEARCH, position=position),
    )


def a_padel_court(organiser, *invitees) -> tuple[SeatPlan, ...]:
    sides = (Side.A, Side.B, Side.B)
    return (SeatPlan(side=Side.A, player_id=organiser),) + tuple(
        invited(player_id, side, position)
        for position, (player_id, side) in enumerate(
            zip(invitees, sides, strict=True), start=1
        )
    )


def a_tennis_court(organiser, invitee) -> tuple[SeatPlan, ...]:
    return (
        SeatPlan(side=Side.A, player_id=organiser),
        invited(invitee, Side.B, 1),
    )


def _repository(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


async def _record(session, challenge: Challenge) -> Challenge:
    """Write a challenge the way a request would, and commit it."""

    await _repository(session).save(challenge)
    await session.commit()
    return challenge


def a_tennis_challenge(*, organiser=ORGANISER, invitee=ALICE) -> Challenge:
    """Built and not saved: a test that answers a seat saves the whole life once.

    One repository per unit of work is the contract, so a second save through a
    second repository is the version conflict a request would have got.
    """

    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        mode=SearchMode.FOR_FUN,
        window=Window.ANY,
        organiser_id=organiser,
        arrangement=a_tennis_court(organiser, invitee),
        occurred_at=SENT_AT,
    )


def a_mutual_born_challenge(
    *, sport: Sport = Sport.TENNIS, organiser=ORGANISER, other=ALICE
) -> Challenge:
    """Two yeses that met. **``ON`` at birth in a singles sport, half a game in
    a doubles one** — which is the difference these tests turn on.

    Built by the aggregate rather than by the mint, because what is under test
    here is the **read** — the use case's own guards are exercised where they
    live.
    """

    return Challenge.opened_from_mutual_interest(
        challenge_id=new_uuid(),
        sport=sport,
        organiser_id=organiser,
        other_player_id=other,
        occurred_at=SENT_AT,
    )


def a_side_invited_into(challenge: Challenge, *, at_hour: int = 1) -> Challenge:
    """Fill a half-built padel court's open side, the way its organiser would."""

    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(BOB, Side.B, 1),
            invited(CAROL, Side.B, 2),
        ),
        occurred_at=at(at_hour),
    )
    return challenge


def a_padel_choice(organiser, *invitees) -> tuple[SeatChoice, ...]:
    """The same court a client would post: sides and people, no origins."""

    sides = (Side.A, Side.B, Side.B)
    return (SeatChoice(side=Side.A, player_id=organiser),) + tuple(
        SeatChoice(side=side, player_id=player_id)
        for player_id, side in zip(invitees, sides, strict=True)
    )


def a_tennis_choice(organiser, invitee) -> tuple[SeatChoice, ...]:
    return (
        SeatChoice(side=Side.A, player_id=organiser),
        SeatChoice(side=Side.B, player_id=invitee),
    )


def _send(session, *, now: Instant, sport: Sport = Sport.PADEL) -> SendChallenge:
    """The send with everything but the pair rule wired open.

    The four fail-closed gates have their own file; what is under test here is
    the one rule this adapter answers, so the safety stubs admit everybody and a
    refusal below can only have come from the open-challenge read.
    """

    return SendChallenge(
        challenges=_repository(session),
        open_challenges=build_open_challenge_query(session),
        origins=StubOrigins(known={SEARCH}, sport=sport),
        safety=a_safe_court([ORGANISER, ALICE, BOB, CAROL, STRANGER]),
        uow=CountingUnitOfWork(),
        clock=FrozenClock(now),
    )


# ---------------------------------------------------------------------------
# The query
# ---------------------------------------------------------------------------


async def test_a_challenge_between_two_people_is_a_pair(session_factory):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE], now=INSIDE
        )

        assert pairs == frozenset({frozenset({ORGANISER, ALICE})})


async def test_sharing_a_line_up_makes_a_pair_of_everybody_in_it(session_factory):
    """A four contains six pairs, and the organiser is in only three of them."""

    async with session_factory() as session:
        await _record(
            session,
            Challenge.sent(
                challenge_id=new_uuid(),
                sport=Sport.PADEL,
                mode=SearchMode.FOR_FUN,
                window=Window.WEEKEND,
                organiser_id=ORGANISER,
                arrangement=a_padel_court(ORGANISER, ALICE, BOB, CAROL),
                occurred_at=SENT_AT,
            ),
        )

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ALICE, BOB, CAROL], now=INSIDE
        )

        assert pairs == frozenset(
            {
                frozenset({ALICE, BOB}),
                frozenset({ALICE, CAROL}),
                frozenset({BOB, CAROL}),
            }
        )


async def test_a_declined_seat_releases_its_pairs(session_factory):
    async with session_factory() as session:
        challenge = a_tennis_challenge()
        challenge.decline(ALICE, occurred_at=at(1))
        await _record(session, challenge)

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE], now=INSIDE
        )

        assert pairs == frozenset()


async def test_a_lapsed_pair_releases_with_no_sweep_having_run(session_factory):
    """The gate answers the same either side of a sweep, which is the point."""

    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        query = build_open_challenge_query(session)

        assert await query.open_pairs_among([ORGANISER, ALICE], now=INSIDE)
        assert not await query.open_pairs_among([ORGANISER, ALICE], now=OUTSIDE)


async def test_a_completed_line_up_releases_the_pair(session_factory):
    """*A game is never open in this sense* — read through the adapter that
    decides it, and not only through the aggregate.

    Every seat accepted derives ``ON``, which is not an ending and is not being
    arranged either: the arranging is **finished**. So the pair is released, the
    two of them may open a second challenge, and each is back in the other's
    deck ([#343](https://github.com/Raketa02/Raketa/issues/343),
    ``docs/adr/0142`` §1).
    """

    async with session_factory() as session:
        challenge = a_tennis_challenge()
        challenge.accept(ALICE, occurred_at=at(1))
        await _record(session, challenge)

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE], now=INSIDE
        )

        assert pairs == frozenset()


async def test_a_sent_challenge_is_not_something_a_mutual_minted(session_factory):
    """The port's second question, and the first thing it must not confuse.

    ``mutual_born_challenges_that_became_games`` is the mutual mint's
    **idempotence** key — *has a mutual between these two already minted a game
    in this sport* — and a challenge somebody **sent** is not one, however
    complete it is. Answering
    otherwise would be the pair rule wearing a second hat, which is the
    conflation ``docs/adr/0152`` §1 exists to undo.
    """

    async with session_factory() as session:
        challenge = a_tennis_challenge()
        challenge.accept(ALICE, occurred_at=at(1))
        await _record(session, challenge)

        query = build_open_challenge_query(session)

        assert await query.open_pairs_among([ORGANISER, ALICE], now=INSIDE) == (
            frozenset()
        )
        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.TENNIS, now=INSIDE
        ) == frozenset()


async def test_a_mutual_born_game_comes_back_keyed_by_its_challenge(
    session_factory,
):
    """What the mint reads, in the currency ``games`` can be asked in.

    A singles mutual is ``ON`` the instant it exists, so it has minted a game
    from birth — and what comes back is the **challenge** id, because that is the
    one name both contexts spell and the one ``SettledGameQuery`` is asked with.
    """

    async with session_factory() as session:
        challenge = a_mutual_born_challenge()
        await _record(session, challenge)

        assert await build_open_challenge_query(
            session
        ).mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.TENNIS, now=INSIDE
        ) == frozenset({challenge.id})


async def test_it_answers_about_the_sport_it_was_asked_about(session_factory):
    """**Per sport, and this is the permanence the record removed.**

    An ``Interest`` is keyed ``(from, to, sport)`` and expires: a padel yes is
    not a tennis yes pressed twice. The one-open-challenge-per-pair rule stays
    cross-sport on its own justification; this question never was.
    """

    async with session_factory() as session:
        await _record(session, a_mutual_born_challenge())

        query = build_open_challenge_query(session)

        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.PADEL, now=INSIDE
        ) == frozenset()


async def test_a_half_built_mutual_born_court_has_minted_no_game(session_factory):
    """A doubles mutual is half a game, and half a game is not a game.

    Nothing has been handed to ``games``, so there is nothing to wait on
    settling — those two are held by the pair rule beside it, and released the
    moment that court stops being arranged.
    """

    async with session_factory() as session:
        await _record(session, a_mutual_born_challenge(sport=Sport.PADEL))

        query = build_open_challenge_query(session)

        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.PADEL, now=INSIDE
        ) == frozenset()
        assert await query.open_pairs_among(
            [ORGANISER, ALICE], now=INSIDE
        ) == frozenset({frozenset({ORGANISER, ALICE})})


async def test_a_later_invitee_is_not_somebody_the_mutual_was_between(
    session_factory,
):
    """The key is the **mutual**, not the court it grew into.

    A doubles mutual seats its two and leaves a side to fill; whoever is invited
    into it later shares a mutual-born court with them and shared no yes. Reading
    the aggregate's membership instead of the opening event would hold a pair no
    mutual was ever between, which is this guard reaching outside its own key.
    """

    async with session_factory() as session:
        challenge = a_side_invited_into(a_mutual_born_challenge(sport=Sport.PADEL))
        challenge.accept(BOB, occurred_at=at(2))
        challenge.accept(CAROL, occurred_at=at(2))
        await _record(session, challenge)

        query = build_open_challenge_query(session)

        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.PADEL, now=at(3)
        ) == frozenset({challenge.id})
        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, BOB, sport=Sport.PADEL, now=at(3)
        ) == frozenset()


async def test_a_mutual_born_court_with_answers_owed_has_minted_nothing(
    session_factory,
):
    """The bound on the second question, from the side that releases.

    A mutual-born court that was invited into and is still waiting on those
    answers has produced no game, so there is nothing for the mint to wait on
    settling — those two are held by the pair rule and by nothing else. It is
    what makes *a mutual-born challenge that ended without ever producing a game
    holds nobody* fall out of the release rather than need a rule of its own:
    when #325's withdraw ends this court, the pair rule lets go and there is
    nothing behind it.
    """

    async with session_factory() as session:
        await _record(
            session, a_side_invited_into(a_mutual_born_challenge(sport=Sport.PADEL))
        )

        query = build_open_challenge_query(session)

        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.PADEL, now=at(3)
        ) == frozenset()


async def test_it_holds_no_pair_a_year_on(session_factory):
    """The fold-forward that #343 was, asked of the guard that replaced it.

    A mutual-born challenge is ``ON`` for ever — every seat accepted at birth, no
    lapse, no decline and no withdraw exit — so this read keeps answering *yes*
    about it, and it is **meant** to: what releases the pair is the game
    settling, one context over. The regression the shape guards against is the
    read quietly widening back into *does a challenge still stand between these
    two, in any sport*, which is what this asserts alongside it.
    """

    async with session_factory() as session:
        challenge = a_mutual_born_challenge()
        await _record(session, challenge)

        a_year_on = at(24 * 365)
        query = build_open_challenge_query(session)

        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.TENNIS, now=a_year_on
        ) == frozenset({challenge.id})
        assert await query.mutual_born_challenges_that_became_games(
            ORGANISER, ALICE, sport=Sport.PADEL, now=a_year_on
        ) == frozenset()
        assert await query.open_pairs_among(
            [ORGANISER, ALICE], now=a_year_on
        ) == frozenset()


async def test_a_half_built_court_still_stands_between_its_pair(session_factory):
    """The line the release runs along, asserted from the side that must not move.

    One acceptance on a padel four is ``LINE_UP_INCOMPLETE``: the organiser can
    still fill the open seat, so those two are still arranging a game and the
    rule still holds them.
    """

    async with session_factory() as session:
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            mode=SearchMode.FOR_FUN,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ALICE, Side.A, 1),
                SeatPlan(side=Side.B),
                SeatPlan(side=Side.B),
            ),
            occurred_at=SENT_AT,
        )
        challenge.accept(ALICE, occurred_at=at(1))
        await _record(session, challenge)

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE], now=INSIDE
        )

        assert pairs == frozenset({frozenset({ORGANISER, ALICE})})


async def test_a_withdrawn_court_releases_the_pair_it_was_holding(session_factory):
    """The other side of that line, and the permanence the withdraw exists to end.

    A half-built four holds its pair with no expiry: nobody is deciding, so
    nothing lapses, and the acceptor cannot leave a seat they have answered.
    Before ``docs/adr/0142`` that was for ever and in **every** sport. A
    withdrawal is an ending, so the arranging stops and both of them are
    strangers again.
    """

    async with session_factory() as session:
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            mode=SearchMode.FOR_FUN,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ALICE, Side.A, 1),
                SeatPlan(side=Side.B),
                SeatPlan(side=Side.B),
            ),
            occurred_at=SENT_AT,
        )
        challenge.accept(ALICE, occurred_at=at(1))
        challenge.withdraw(ORGANISER, occurred_at=at(2))
        await _record(session, challenge)

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE], now=INSIDE
        )

        assert pairs == frozenset()


async def test_the_same_people_may_be_asked_again_once_it_is_withdrawn(
    session_factory,
):
    """**A new challenge, and that is what it is.** Fresh deadlines and its own
    record of who has answered — the send is not a resurrection of the one that
    was withdrawn, and nothing here reopens anything."""

    async with session_factory() as session:
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            mode=SearchMode.FOR_FUN,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ALICE, Side.A, 1),
                SeatPlan(side=Side.B),
                SeatPlan(side=Side.B),
            ),
            occurred_at=SENT_AT,
        )
        challenge.accept(ALICE, occurred_at=at(1))
        await _record(session, challenge)

        with pytest.raises(AnOpenChallengeStandsWithThisPair):
            await _send(session, now=INSIDE).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_padel_choice(ORGANISER, ALICE, BOB, CAROL),
                )
            )

        # One repository per unit of work, which is why the load and the save
        # are the same one: a second would not know the version it read.
        repository = _repository(session)
        loaded = await repository.load(challenge.id)
        loaded.withdraw(ORGANISER, occurred_at=at(2))
        await repository.save(loaded)
        await session.commit()

        again = await _send(session, now=INSIDE).execute(
            SendChallengeCommand(
                organiser_id=ORGANISER,
                search_id=SEARCH,
                court=a_padel_choice(ORGANISER, ALICE, BOB, CAROL),
            )
        )

        assert again != challenge.id


async def test_a_challenge_reaching_outside_this_court_is_somebody_elses(
    session_factory,
):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge(organiser=ALICE, invitee=STRANGER))

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE, BOB], now=INSIDE
        )

        assert pairs == frozenset()


async def test_one_person_is_not_a_pair(session_factory):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        assert (
            await build_open_challenge_query(session).open_pairs_among(
                [ALICE], now=INSIDE
            )
            == frozenset()
        )


async def test_a_stream_whose_membership_changed_is_read_whole(session_factory):
    """The seats moved on a later event, and the answers are on later ones still.

    A read that stopped at the row it matched would fold a court with its
    answers missing — which looks exactly like a challenge that never closes.
    """

    async with session_factory() as session:
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            mode=SearchMode.FOR_FUN,
            window=Window.WEEKEND,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ALICE, Side.A, 1),
                SeatPlan(side=Side.B),
                SeatPlan(side=Side.B),
            ),
            occurred_at=SENT_AT,
        )
        challenge.accept(ALICE, occurred_at=at(1))
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=ALICE),
                invited(BOB, Side.B, 7),
                invited(CAROL, Side.B, 8),
            ),
            occurred_at=at(2),
        )
        challenge.decline(BOB, occurred_at=at(3))
        await _record(session, challenge)

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE, BOB, CAROL], now=at(4)
        )

        assert frozenset({ALICE, CAROL}) in pairs
        assert not any(BOB in pair for pair in pairs)


# ---------------------------------------------------------------------------
# The rule, through the send
# ---------------------------------------------------------------------------


async def test_the_send_refuses_a_pair_that_already_has_an_open_challenge(
    session_factory,
):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        with pytest.raises(AnOpenChallengeStandsWithThisPair):
            await _send(session, now=INSIDE, sport=Sport.TENNIS).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_tennis_choice(ORGANISER, ALICE),
                )
            )


async def test_the_rule_holds_across_a_different_sport(session_factory):
    """`OpenChallenge` carries no sport, so this is the shipped contract's rule.

    The open challenge is tennis and the send is padel: two people are either
    arranging a game or they are not.
    """

    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        with pytest.raises(AnOpenChallengeStandsWithThisPair):
            await _send(session, now=INSIDE).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_padel_choice(ORGANISER, ALICE, BOB, CAROL),
                )
            )


async def test_the_rule_binds_two_invitees_and_not_only_the_organiser(
    session_factory,
):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge(organiser=ALICE, invitee=BOB))

        with pytest.raises(AnOpenChallengeStandsWithThisPair):
            await _send(session, now=INSIDE).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_padel_choice(ORGANISER, ALICE, BOB, CAROL),
                )
            )


async def test_a_refused_send_records_no_challenge(session_factory):
    """Whole-send: a refusal writes nothing, so there is nothing to reconcile."""

    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        with pytest.raises(AnOpenChallengeStandsWithThisPair):
            await _send(session, now=INSIDE).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_padel_choice(ORGANISER, ALICE, BOB, CAROL),
                )
            )

        pairs = await build_open_challenge_query(session).open_pairs_among(
            [ORGANISER, ALICE, BOB, CAROL], now=INSIDE
        )
        assert pairs == frozenset({frozenset({ORGANISER, ALICE})})


async def test_the_refusal_names_nobody(session_factory):
    """A payload naming the pair would be a disclosure route through an error."""

    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        with pytest.raises(AnOpenChallengeStandsWithThisPair) as refusal:
            await _send(session, now=INSIDE, sport=Sport.TENNIS).execute(
                SendChallengeCommand(
                    organiser_id=ORGANISER,
                    search_id=SEARCH,
                    court=a_tennis_choice(ORGANISER, ALICE),
                )
            )

        spelled = str(refusal.value) + str(getattr(refusal.value, "details", ""))
        assert not any(
            str(player) in spelled for player in (ORGANISER, ALICE, BOB, CAROL)
        )


async def test_the_send_lands_when_nothing_stands_between_them(session_factory):
    async with session_factory() as session:
        send = _send(session, now=SENT_AT)

        challenge_id = await send.execute(
            SendChallengeCommand(
                organiser_id=ORGANISER,
                search_id=SEARCH,
                court=a_padel_choice(ORGANISER, ALICE, BOB, CAROL),
            )
        )
        await session.commit()

        stored = await _repository(session).load(challenge_id)
        assert stored is not None
        assert stored.players_in_it_at(INSIDE) == frozenset(
            {ORGANISER, ALICE, BOB, CAROL}
        )


async def test_a_pair_whose_line_up_completed_may_arrange_a_second_game(
    session_factory,
):
    """**And this is the consequence the release was taken with open eyes.**

    Nothing replaces the block (``docs/adr/0142`` §1): the same two people may
    open a second challenge before the first game has been played. Whether an
    unplayed *game* should carry the block is a question about a ``games`` fact
    and ``challenges`` has no port onto it, so it is filed rather than answered
    here — and the send lands.
    """

    async with session_factory() as session:
        first = a_tennis_challenge()
        first.accept(ALICE, occurred_at=at(1))
        await _record(session, first)

        second = await _send(session, now=INSIDE, sport=Sport.TENNIS).execute(
            SendChallengeCommand(
                organiser_id=ORGANISER,
                search_id=SEARCH,
                court=a_tennis_choice(ORGANISER, ALICE),
            )
        )
        await session.commit()

        assert await _repository(session).load(second) is not None
        assert second != first.id


async def test_a_challenge_that_lapsed_no_longer_stands_in_the_way(session_factory):
    async with session_factory() as session:
        await _record(session, a_tennis_challenge())

        challenge_id = await _send(session, now=OUTSIDE, sport=Sport.TENNIS).execute(
            SendChallengeCommand(
                organiser_id=ORGANISER,
                search_id=SEARCH,
                court=a_tennis_choice(ORGANISER, ALICE),
            )
        )
        await session.commit()

        assert await _repository(session).load(challenge_id) is not None
