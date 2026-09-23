"""The plannable-court fold: one challenge, maybe a game, one player, one instant
— and five answers (``docs/adr/0164`` §3).

The fold is what decides who may write a plan, so each of its answers is pinned
here in isolation rather than inferred from a route: **arranging** (the court has
no game yet and is open on the send), **on and awaiting entry** (the court is
whole and open on ``planned_at``), **history** (a challenge that ended without a
game, or a game that left its entry window), **not on it** (a stranger, an
invitee still deciding, somebody who said no), and **left it** (somebody who
took their yes back). The first three are rows; the last two are absences, and
they are the same absence on purpose.

Built on the two providers' own aggregates, because the fold reads them and a
stub that agreed with the rule would prove nothing about whether ``challenges``
and ``games`` actually fold that way.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.seats import SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import entry_closes_at
from app.modules.plans.domain.ports import PlannableCourt
from app.modules.plans.infrastructure.plannable_courts import plannable_court_of
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid

ORGANISER, ANA, BO, CY, STRANGER = (new_uuid() for _ in range(5))
SENT_AT = instant(datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc))


def _at(hours: int = 0) -> Instant:
    return instant(SENT_AT + timedelta(hours=hours))


def _a_padel_four() -> Challenge:
    search = new_uuid()
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(
                side=Side.A,
                player_id=ANA,
                origin=SentFromSearch(search_id=search, position=1),
            ),
            SeatPlan(
                side=Side.B,
                player_id=BO,
                origin=SentFromSearch(search_id=search, position=2),
            ),
            SeatPlan(
                side=Side.B,
                player_id=CY,
                origin=SentFromSearch(search_id=search, position=3),
            ),
        ),
        occurred_at=SENT_AT,
    )


def _everybody_in(challenge: Challenge, *, at: Instant) -> Challenge:
    for who in (ANA, BO, CY):
        challenge.accept(who, occurred_at=at)
    return challenge


def _the_game_of(challenge: Challenge, *, at: Instant) -> Game:
    """The game the completed line-up hands over — the fold's second record."""

    return Game.planned(
        game_id=new_uuid(),
        challenge_id=challenge.challenge_id,
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.WEEKEND,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=ORGANISER),
                Seating(side=GameSide.A, player_id=ANA),
                Seating(side=GameSide.B, player_id=BO),
                Seating(side=GameSide.B, player_id=CY),
            )
        ),
        occurred_at=at,
    )


def _fold(
    challenge: Challenge, game: Game | None, player_id: UUID, *, now: Instant
) -> PlannableCourt | None:
    return plannable_court_of(challenge, game, player_id=player_id, now=now)


# ---------------------------------------------------------------------------
# Arranging — a row on the send, open, and not whole
# ---------------------------------------------------------------------------


def test_the_first_yes_makes_the_court_plannable_for_both_on_the_send():
    """After the first acceptance the organiser and the accepter each get a
    row: open to planning, **not whole**, and anchored at the send — the one
    instant a half-built court has (``docs/adr/0164`` §4)."""

    challenge = _a_padel_four()
    challenge.accept(ANA, occurred_at=_at(1))
    assert challenge.standing_at(_at(2)) is Standing.AWAITING_ANSWERS

    for who in (ORGANISER, ANA):
        assert _fold(challenge, None, who, now=_at(2)) == PlannableCourt(
            anchor=SENT_AT, open_to_planning=True, whole=False
        )


def test_a_decline_leaves_the_half_built_court_plannable_and_still_not_whole():
    """``LINE_UP_INCOMPLETE`` is the other arranging standing, and the plan is
    untouched by somebody else's no."""

    challenge = _a_padel_four()
    challenge.accept(ANA, occurred_at=_at(1))
    challenge.decline(BO, occurred_at=_at(2))
    assert challenge.standing_at(_at(3)) is Standing.AWAITING_ANSWERS
    challenge.decline(CY, occurred_at=_at(3))
    assert challenge.standing_at(_at(4)) is Standing.LINE_UP_INCOMPLETE

    assert _fold(challenge, None, ANA, now=_at(4)) == PlannableCourt(
        anchor=SENT_AT, open_to_planning=True, whole=False
    )


# ---------------------------------------------------------------------------
# On and awaiting entry — the anchor moves to the court filling, and it is whole
# ---------------------------------------------------------------------------


def test_a_whole_court_awaiting_its_entry_is_open_whole_and_anchored_on_planned_at():
    challenge = _everybody_in(_a_padel_four(), at=_at(5))
    game = _the_game_of(challenge, at=_at(5))
    assert challenge.standing_at(_at(6)) is Standing.ON

    for who in (ORGANISER, ANA, BO, CY):
        assert _fold(challenge, game, who, now=_at(6)) == PlannableCourt(
            anchor=game.planned_at, open_to_planning=True, whole=True
        )


def test_the_anchor_only_ever_moves_later():
    """A day chosen under the send is still valid under ``planned_at``, which
    is what lets the chips widen when the court fills rather than shrink."""

    challenge = _a_padel_four()
    challenge.accept(ANA, occurred_at=_at(1))
    before = _fold(challenge, None, ANA, now=_at(2))
    for who in (BO, CY):
        challenge.accept(who, occurred_at=_at(20))
    game = _the_game_of(challenge, at=_at(20))
    after = _fold(challenge, game, ANA, now=_at(21))

    assert before is not None and after is not None
    assert before.anchor == SENT_AT
    assert after.anchor == game.planned_at
    assert after.anchor > before.anchor


# ---------------------------------------------------------------------------
# History — a row that is no longer open, whichever record ended it
# ---------------------------------------------------------------------------


def test_a_court_that_ended_after_a_yes_is_history_for_who_is_still_on_it():
    """B said yes, the other two said no, and the organiser left: B is alone
    with nobody deciding, and the court is over by itself (``docs/adr/0165``
    §3). It had a room, so it is history for B, who is still on it, rather than
    gone — and nothing for the organiser, who left it, exactly as any court
    somebody left is nothing to them. A court somebody has joined is nobody's
    to withdraw, so this is how such a court ends."""

    challenge = _a_padel_four()
    challenge.accept(ANA, occurred_at=_at(1))
    for who in (BO, CY):
        challenge.decline(who, occurred_at=_at(2))
    challenge.leave(ORGANISER, occurred_at=_at(3))
    assert challenge.standing_at(_at(4)) is Standing.DECLINED

    assert _fold(challenge, None, ANA, now=_at(4)) == PlannableCourt(
        anchor=SENT_AT, open_to_planning=False, whole=False
    )
    assert _fold(challenge, None, ORGANISER, now=_at(4)) is None


def test_a_game_past_its_entry_window_is_history_and_still_answered_about():
    """The plan is drawn beside a game whatever its standing, so the row stays
    and only ``open_to_planning`` moves."""

    challenge = _everybody_in(_a_padel_four(), at=_at(5))
    game = _the_game_of(challenge, at=_at(5))
    later = instant(entry_closes_at(game.planned_at) + timedelta(minutes=1))
    assert game.standing_at(later) is GameStanding.NEVER_PLAYED

    assert _fold(challenge, game, ANA, now=later) == PlannableCourt(
        anchor=game.planned_at, open_to_planning=False, whole=True
    )


def test_a_game_somebody_said_they_played_is_history():
    challenge = _everybody_in(_a_padel_four(), at=_at(5))
    game = _the_game_of(challenge, at=_at(5))
    game.state_result(
        by=ANA,
        score=Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
        occurred_at=_at(50),
    )

    found = _fold(challenge, game, ANA, now=_at(51))

    assert found is not None and found.open_to_planning is False


# ---------------------------------------------------------------------------
# Not on it — one absence for a stranger, an invitee deciding, and a no
# ---------------------------------------------------------------------------


def test_a_stranger_an_undecided_invitee_and_a_decliner_are_all_absent():
    """``docs/adr/0164`` §3 — *an invitee who has not answered does not read the
    plan*, and there is no field saying why anybody is absent."""

    challenge = _a_padel_four()
    challenge.accept(ANA, occurred_at=_at(1))
    challenge.decline(CY, occurred_at=_at(2))

    assert _fold(challenge, None, STRANGER, now=_at(3)) is None
    assert _fold(challenge, None, BO, now=_at(3)) is None, "still deciding"
    assert _fold(challenge, None, CY, now=_at(3)) is None, "said no"
    assert _fold(challenge, None, ANA, now=_at(3)) is not None


def test_a_court_nobody_has_said_yes_to_is_not_plannable_even_for_the_organiser():
    """The organiser's seat is accepted from birth, and that alone makes no
    court: a plan exists **from the first yes** (``docs/adr/0164`` §2), because
    the room it is drawn in opens on that yes and a slot written before it
    would be a line with nowhere to land. A send everybody declined never
    qualifies either — there was never a room to be history of."""

    just_sent = _a_padel_four()
    assert _fold(just_sent, None, ORGANISER, now=_at(1)) is None

    everybody_said_no = _a_padel_four()
    for who in (ANA, BO, CY):
        everybody_said_no.decline(who, occurred_at=_at(1))
    assert everybody_said_no.standing_at(_at(2)) is Standing.DECLINED
    assert _fold(everybody_said_no, None, ORGANISER, now=_at(2)) is None


# ---------------------------------------------------------------------------
# Left it — the leaver is absent, the others keep an open, no-longer-whole row
# ---------------------------------------------------------------------------


def test_somebody_who_left_is_absent_and_the_court_is_open_but_no_longer_whole():
    """``docs/adr/0162`` — an open seat freezes nothing for the people still
    on the court; ``docs/adr/0164`` §5 — the court is not whole again until the
    next completed line-up re-seats it, and the leaver has nothing to plan."""

    challenge = _everybody_in(_a_padel_four(), at=_at(5))
    game = _the_game_of(challenge, at=_at(5))
    challenge.leave(CY, occurred_at=_at(6))
    game.vacate(CY, occurred_at=_at(6))
    assert challenge.standing_at(_at(7)) is Standing.LINE_UP_INCOMPLETE

    assert _fold(challenge, game, CY, now=_at(7)) is None
    for who in (ORGANISER, ANA, BO):
        assert _fold(challenge, game, who, now=_at(7)) == PlannableCourt(
            anchor=game.planned_at, open_to_planning=True, whole=False
        )
