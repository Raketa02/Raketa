"""Who turned up to a booked game, caught at the court while it happens (#657;
``docs/adr/0195`` §3, the mechanics §15.1).

Wednesday 14 October, tennis 17:00–18:00 at Ogrody 33. **From 17:00 to 17:30**
Ivan, at the club, taps *Oscar isn't here yet*. Oscar's **arrival** — his own
*I'm here*, or a courtmate's *they're here*, each from the club — decides what it
was: **on time** before 17:10, **Came late** from 17:10, **Didn't come** with no
arrival by 17:30. *I was there* by 17:30 on Thursday, confirmed by somebody else
on the court, makes it Came late. Everybody who arrives on time does nothing.

The grading is read through the aggregate, against a clock the test supplies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.games.domain.attendance import (
    AttendanceState,
    ClubVerdict,
    LocationFix,
    Turnout,
)
from app.modules.games.domain.errors import (
    ALocationFixIsOffTheMap,
    AlreadyArrived,
    AttendanceIsForBookedGames,
    NobodySaidTheyWereNotHere,
    NotAboutYourself,
    NotAtTheClub,
    NothingToConfirm,
    NotOnThisCourt,
    SomebodyDidntCome,
    SomebodyIsNotHereYet,
    TheGameHasNotStarted,
    TheGameStartedShort,
    TheGameWasCalledOff,
    TheLateClaimHasClosed,
    TheResultIsSettled,
    TheTapWindowHasClosed,
    TheTapWindowIsOpen,
    YouAreNotHereYourself,
    YouWereNotOnThisCourt,
)
from app.modules.games.domain.events import (
    AbsenceNoted,
    ArrivalNoted,
    NoShowDisputed,
    NoShowReported,
    PresenceClaimed,
    PresenceConfirmed,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import (
    LATE_CLAIM_WINDOW,
    ON_TIME_GRACE,
    TAP_WINDOW,
)
from app.shared.ids import new_uuid

IVAN, OSCAR, MARTA, PAULA, STRANGER = (new_uuid() for _ in range(5))
BOOKED_AT = instant(datetime(2026, 10, 9, 6, tzinfo=timezone.utc))
#: Wednesday 14 October, 17:00 in Kraków.
FIVE = instant(datetime(2026, 10, 14, 15, tzinfo=timezone.utc))
HALF_PAST = instant(FIVE + TAP_WINDOW)
#: Thursday 17:30: the late claim's day is over.
CLAIMS_CLOSE = instant(HALF_PAST + LATE_CLAIM_WINDOW)

AT_THE_CLUB = ClubVerdict(at_the_club=True, club_name="Ogrody 33")
AWAY = ClubVerdict(at_the_club=False, club_name="Ogrody 33")


def at(minutes: float) -> datetime:
    """``minutes`` after 17:00."""

    return instant(FIVE + timedelta(minutes=minutes))


def _singles() -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=IVAN),
            Seating(side=GameSide.B, player_id=OSCAR),
        )
    )


def _doubles() -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=IVAN),
            Seating(side=GameSide.A, player_id=MARTA),
            Seating(side=GameSide.B, player_id=OSCAR),
            Seating(side=GameSide.B, player_id=PAULA),
        )
    )


def _game(
    *, line_up: LineUp | None = None, starts_at=FIVE, kind=GameKind.COUNTED
) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        kind=kind,
        window=None,
        line_up=line_up or _doubles(),
        occurred_at=BOOKED_AT,
        starts_at=starts_at,
    )


def _score() -> Score:
    return Score.of((SetScore(a=6, b=3), SetScore(a=6, b=4)))


def _replayed(game: Game) -> Game:
    return Game.from_history(game.pull_events())


def _absent(game: Game, absent=OSCAR, *, by=IVAN, when=10, where=AT_THE_CLUB):
    game.note_absent(by=by, absent=absent, where=where, occurred_at=at(when))


def _arrives(game: Game, arrived=OSCAR, *, by=None, when, where=AT_THE_CLUB):
    game.note_arrival(
        by=arrived if by is None else by,
        arrived=arrived,
        where=where,
        occurred_at=at(when),
    )


# --------------------------------------------------------------------------- #
# The grading: on time, Came late, Didn't come
# --------------------------------------------------------------------------- #


def test_the_clocks_are_thirty_minutes_ten_minutes_and_a_day():
    assert (TAP_WINDOW, ON_TIME_GRACE, LATE_CLAIM_WINDOW) == (
        timedelta(minutes=30),
        timedelta(minutes=10),
        timedelta(hours=24),
    )


def test_ivan_taps_oscar_isn_t_here_yet_and_the_game_waits_for_him():
    game = _game()

    _absent(game)

    assert game.standing_at(at(10)) is GameStanding.NOT_HERE_YET
    assert game.attendance_at(at(10)) == {OSCAR: AttendanceState.WAITING}
    assert GameStanding.NOT_HERE_YET not in SETTLED | PLAYED
    [event] = [e for e in game.pull_events() if isinstance(e, AbsenceNoted)]
    assert (event.player_id, event.noted_by) == (OSCAR, IVAN)


def test_arriving_within_ten_minutes_is_on_time_and_records_nothing_against_him():
    game = _game()
    _absent(game, when=2)

    _arrives(game, when=8)

    replayed = _replayed(game)
    assert replayed.attendance_at(at(8)) == {OSCAR: AttendanceState.ON_TIME}
    assert replayed.standing_at(at(8)) is GameStanding.AWAITING_ENTRY
    assert replayed.didnt_come_at(CLAIMS_CLOSE) == frozenset()


def test_ten_minutes_after_the_start_is_already_late():
    on_time, late = _game(), _game()
    _absent(on_time, when=2)
    _absent(late, when=2)

    on_time.note_arrival(
        by=OSCAR,
        arrived=OSCAR,
        where=AT_THE_CLUB,
        occurred_at=instant(FIVE + ON_TIME_GRACE - timedelta(seconds=1)),
    )
    late.note_arrival(
        by=OSCAR,
        arrived=OSCAR,
        where=AT_THE_CLUB,
        occurred_at=instant(FIVE + ON_TIME_GRACE),
    )

    assert on_time.attendance_at(at(20))[OSCAR] is AttendanceState.ON_TIME
    assert late.attendance_at(at(20))[OSCAR] is AttendanceState.CAME_LATE


def test_oscar_s_i_m_here_at_17_22_is_came_late_and_the_game_carries_on_scored():
    game = _game()
    _absent(game)

    _arrives(game, when=22)

    assert game.attendance_at(at(22)) == {OSCAR: AttendanceState.CAME_LATE}
    assert game.standing_at(at(22)) is GameStanding.AWAITING_ENTRY
    game.state_result(by=IVAN, score=_score(), occurred_at=at(65))
    assert game.standing_at(at(65)) is GameStanding.AWAITING_ANSWER
    [arrival] = [e for e in game.pull_events() if isinstance(e, ArrivalNoted)]
    assert (arrival.player_id, arrival.noted_by) == (OSCAR, OSCAR)


def test_a_courtmate_s_they_re_here_is_an_arrival_too():
    game = _game()
    _absent(game)

    _arrives(game, by=MARTA, when=15)

    assert game.attendance_at(at(15)) == {OSCAR: AttendanceState.CAME_LATE}
    assert game.attendance[OSCAR].arrival_noted_by == MARTA


def test_no_arrival_by_17_30_is_didn_t_come_and_the_game_takes_no_score():
    game = _game()
    _absent(game)

    assert game.standing_at(at(29.99)) is GameStanding.NOT_HERE_YET
    assert game.standing_at(HALF_PAST) is GameStanding.DIDNT_COME
    assert game.attendance_at(HALF_PAST) == {OSCAR: AttendanceState.DIDNT_COME}
    assert GameStanding.DIDNT_COME not in SETTLED | PLAYED
    with pytest.raises(SomebodyDidntCome):
        game.state_result(by=IVAN, score=_score(), occurred_at=at(65))
    assert game.became_history_at(at(65)) == HALF_PAST


def test_didn_t_come_is_provisional_until_the_late_claim_s_day_is_over():
    game = _game()
    _absent(game)

    assert game.didnt_come_at(instant(CLAIMS_CLOSE - timedelta(seconds=1))) == (
        frozenset()
    )
    assert game.didnt_come_at(CLAIMS_CLOSE) == frozenset({OSCAR})
    assert game.standing_at(CLAIMS_CLOSE) is GameStanding.DIDNT_COME


def test_no_score_is_taken_while_somebody_is_not_here_yet():
    game = _game()
    _absent(game)

    with pytest.raises(SomebodyIsNotHereYet):
        game.state_result(by=IVAN, score=_score(), occurred_at=at(12))


def test_two_absentees_can_each_be_tapped_and_one_didn_t_come_is_enough():
    game = _game()
    _absent(game, OSCAR)
    _absent(game, PAULA, when=11)
    _arrives(game, PAULA, when=12)

    assert game.attendance_at(HALF_PAST) == {
        OSCAR: AttendanceState.DIDNT_COME,
        PAULA: AttendanceState.CAME_LATE,
    }
    assert game.standing_at(HALF_PAST) is GameStanding.DIDNT_COME


def test_a_partner_may_be_tapped():
    game = _game()

    _absent(game, MARTA, by=IVAN)

    assert game.attendance_at(at(10)) == {MARTA: AttendanceState.WAITING}


def test_tapping_somebody_twice_writes_nothing():
    game = _game()
    _absent(game)
    game.pull_events()

    _absent(game, by=MARTA, when=12)

    assert game.pull_events() == []
    assert game.attendance[OSCAR].noted_by == IVAN


# --------------------------------------------------------------------------- #
# A phone that died: I was there, and a courtmate's yes
# --------------------------------------------------------------------------- #


def test_oscar_s_i_was_there_confirmed_by_ivan_turns_didn_t_come_into_came_late():
    game = _game(line_up=_singles())
    _absent(game)
    morning = instant(FIVE + timedelta(hours=16))

    game.claim_presence(by=OSCAR, occurred_at=morning)

    assert game.attendance_at(morning) == {OSCAR: AttendanceState.CLAIMED}
    assert game.standing_at(morning) is GameStanding.DIDNT_COME

    game.confirm_presence(by=IVAN, claimant=OSCAR, occurred_at=morning)

    replayed = _replayed(game)
    assert replayed.attendance_at(morning) == {OSCAR: AttendanceState.CONFIRMED}
    assert replayed.standing_at(morning) is GameStanding.AWAITING_ENTRY
    assert replayed.didnt_come_at(CLAIMS_CLOSE) == frozenset()
    replayed.state_result(by=IVAN, score=_score(), occurred_at=morning)
    assert replayed.standing_at(morning) is GameStanding.AWAITING_ANSWER


def test_the_claim_and_its_confirmation_are_two_events_naming_who():
    game = _game()
    _absent(game)
    morning = instant(FIVE + timedelta(hours=16))

    game.claim_presence(by=OSCAR, occurred_at=morning)
    game.confirm_presence(by=PAULA, claimant=OSCAR, occurred_at=morning)

    claimed, confirmed = [
        e
        for e in game.pull_events()
        if isinstance(e, (PresenceClaimed, PresenceConfirmed))
    ]
    assert isinstance(claimed, PresenceClaimed) and claimed.player_id == OSCAR
    assert isinstance(confirmed, PresenceConfirmed)
    assert (confirmed.player_id, confirmed.confirmed_by) == (OSCAR, PAULA)


def test_a_claim_nobody_confirms_in_its_day_is_didn_t_come_for_good():
    game = _game()
    _absent(game)
    game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)

    before = instant(CLAIMS_CLOSE - timedelta(seconds=1))
    assert game.attendance_at(before) == {OSCAR: AttendanceState.CLAIMED}
    assert game.attendance_at(CLAIMS_CLOSE) == {OSCAR: AttendanceState.DIDNT_COME}
    assert game.didnt_come_at(CLAIMS_CLOSE) == frozenset({OSCAR})
    with pytest.raises(TheLateClaimHasClosed):
        game.confirm_presence(by=IVAN, claimant=OSCAR, occurred_at=CLAIMS_CLOSE)


def test_the_late_claim_opens_when_the_tap_window_closes_and_shuts_a_day_later():
    game = _game()
    _absent(game)

    with pytest.raises(TheTapWindowIsOpen):
        game.claim_presence(by=OSCAR, occurred_at=at(29))
    with pytest.raises(TheLateClaimHasClosed):
        game.claim_presence(by=OSCAR, occurred_at=CLAIMS_CLOSE)
    game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)


def test_only_a_player_tapped_and_not_arrived_may_claim():
    game = _game()
    _absent(game)
    _arrives(game, when=20)

    with pytest.raises(NobodySaidTheyWereNotHere):
        game.claim_presence(by=PAULA, occurred_at=HALF_PAST)
    with pytest.raises(AlreadyArrived):
        game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)


def test_nobody_confirms_their_own_claim_or_one_never_made():
    game = _game()
    _absent(game)

    with pytest.raises(NothingToConfirm):
        game.confirm_presence(by=IVAN, claimant=OSCAR, occurred_at=HALF_PAST)
    game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)
    with pytest.raises(NotAboutYourself):
        game.confirm_presence(by=OSCAR, claimant=OSCAR, occurred_at=HALF_PAST)
    with pytest.raises(NotOnThisCourt):
        game.confirm_presence(by=IVAN, claimant=STRANGER, occurred_at=HALF_PAST)


def test_two_absentees_cannot_vouch_for_each_other():
    game = _game()
    _absent(game, OSCAR)
    _absent(game, PAULA)
    game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)
    game.claim_presence(by=PAULA, occurred_at=HALF_PAST)

    with pytest.raises(YouAreNotHereYourself):
        game.confirm_presence(by=PAULA, claimant=OSCAR, occurred_at=HALF_PAST)

    game.confirm_presence(by=MARTA, claimant=PAULA, occurred_at=HALF_PAST)
    game.confirm_presence(by=PAULA, claimant=OSCAR, occurred_at=HALF_PAST)
    assert game.attendance_at(HALF_PAST) == {
        OSCAR: AttendanceState.CONFIRMED,
        PAULA: AttendanceState.CONFIRMED,
    }


def test_a_second_claim_and_a_second_confirmation_write_nothing():
    game = _game()
    _absent(game)
    game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)
    game.confirm_presence(by=IVAN, claimant=OSCAR, occurred_at=HALF_PAST)
    game.pull_events()

    game.claim_presence(by=OSCAR, occurred_at=HALF_PAST)
    game.confirm_presence(by=MARTA, claimant=OSCAR, occurred_at=HALF_PAST)

    assert game.pull_events() == []
    assert game.attendance[OSCAR].confirmed_by == IVAN


# --------------------------------------------------------------------------- #
# Every tap in the window is made at the club, about somebody else
# --------------------------------------------------------------------------- #


def test_a_tap_away_from_the_club_is_refused_and_says_where_to_be():
    game = _game()

    with pytest.raises(NotAtTheClub) as refused:
        _absent(game, where=AWAY)

    assert refused.value.message == "You can say so only from Ogrody 33."
    assert game.attendance == {}
    _absent(game)
    with pytest.raises(NotAtTheClub):
        _arrives(game, when=20, where=AWAY)
    with pytest.raises(NotAtTheClub):
        _arrives(game, by=MARTA, when=20, where=AWAY)


def test_a_tap_is_refused_before_the_hour_and_from_17_30():
    game = _game()

    with pytest.raises(TheGameHasNotStarted):
        _absent(game, when=-1)
    with pytest.raises(TheTapWindowHasClosed):
        game.note_absent(
            by=IVAN, absent=OSCAR, where=AT_THE_CLUB, occurred_at=HALF_PAST
        )
    _absent(game, when=29)
    with pytest.raises(TheTapWindowHasClosed):
        game.note_arrival(
            by=OSCAR, arrived=OSCAR, where=AT_THE_CLUB, occurred_at=HALF_PAST
        )


def test_nobody_taps_themselves_or_somebody_off_the_court():
    game = _game()

    with pytest.raises(NotAboutYourself):
        _absent(game, IVAN, by=IVAN)
    with pytest.raises(NotOnThisCourt):
        _absent(game, STRANGER)
    with pytest.raises(YouWereNotOnThisCourt):
        _absent(game, OSCAR, by=STRANGER)


def test_a_player_who_is_not_here_says_nothing_about_who_else_is():
    game = _game()
    _absent(game, OSCAR)

    with pytest.raises(YouAreNotHereYourself):
        _absent(game, PAULA, by=OSCAR)
    _absent(game, PAULA)
    with pytest.raises(YouAreNotHereYourself):
        _arrives(game, PAULA, by=OSCAR, when=12)


def test_an_arrival_needs_somebody_to_have_said_they_were_not_here_and_counts_once():
    game = _game()

    with pytest.raises(NobodySaidTheyWereNotHere):
        _arrives(game, when=5)
    _absent(game)
    _arrives(game, when=20)
    with pytest.raises(AlreadyArrived):
        _arrives(game, by=MARTA, when=21)
    with pytest.raises(AlreadyArrived):
        _absent(game, when=22)
    assert game.attendance[OSCAR].arrived_at == at(20)


def test_a_score_put_up_from_home_does_not_stop_the_tap_and_counts_for_nothing():
    """The entry window opens at the hour and a score carries no location, so
    Oscar's partner can put one up at 17:01 from anywhere. It stops nothing:
    nobody agrees with it while he is awaited, and if he never comes the game
    takes no score; a confirmed *I was there* gives it back its game."""

    game = _game()
    game.state_result(by=PAULA, score=_score(), occurred_at=at(1))

    _absent(game)

    assert game.standing_at(at(10)) is GameStanding.NOT_HERE_YET
    with pytest.raises(SomebodyIsNotHereYet):
        game.accept_result(by=IVAN, occurred_at=at(12))
    assert game.standing_at(CLAIMS_CLOSE) is GameStanding.DIDNT_COME
    assert game.confirmed_score_at(CLAIMS_CLOSE) is None
    with pytest.raises(SomebodyDidntCome):
        game.accept_result(by=IVAN, occurred_at=HALF_PAST)

    morning = instant(FIVE + timedelta(hours=16))
    game.claim_presence(by=OSCAR, occurred_at=morning)
    game.confirm_presence(by=IVAN, claimant=OSCAR, occurred_at=morning)
    assert game.standing_at(morning) is GameStanding.AWAITING_ANSWER


def test_a_settled_result_is_final_and_takes_no_tap():
    """A For fun score is the result the moment it is put up: nothing after it
    can make the evening one somebody didn't come to."""

    game = _game(kind=GameKind.FRIENDLY)
    game.state_result(by=IVAN, score=_score(), occurred_at=at(1))

    with pytest.raises(TheResultIsSettled):
        _absent(game)


def test_a_game_with_no_hour_a_called_off_one_and_a_short_one_take_no_tap():
    with pytest.raises(AttendanceIsForBookedGames):
        _absent(_game(starts_at=None))

    called_off = _game()
    called_off.call_off_whole(occurred_at=instant(FIVE - timedelta(days=1)))
    with pytest.raises(TheGameWasCalledOff):
        _absent(called_off)

    short = _game()
    short.vacate(PAULA, occurred_at=instant(FIVE - timedelta(hours=2)))
    with pytest.raises(TheGameStartedShort):
        _absent(short)


# --------------------------------------------------------------------------- #
# At the club: the verdict, and the fix nobody keeps
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("metres", "accuracy_m", "at_the_club"),
    [
        (40.0, 5.0, True),
        (300.0, 0.0, True),
        (300.5, 0.0, False),
        (450.0, 150.0, True),
        (500.0, 1_000.0, True),
        (501.0, 1_000.0, False),
        (2_000.0, 10.0, False),
    ],
)
def test_at_the_club_is_300_m_allowing_for_the_fix_s_accuracy_up_to_200_m(
    metres, accuracy_m, at_the_club
):
    verdict = ClubVerdict.of(metres=metres, accuracy_m=accuracy_m, club_name="O")

    assert verdict.at_the_club is at_the_club


def test_a_club_that_could_not_be_read_is_never_where_a_tap_is_made():
    verdict = ClubVerdict.of(metres=None, accuracy_m=5.0, club_name=None)

    assert verdict == ClubVerdict(at_the_club=False, club_name=None)
    assert NotAtTheClub(None).message == "You can say so only from the club."


def test_a_fix_never_prints_where_it_was_and_refuses_a_place_off_the_map():
    fix = LocationFix(latitude=50.0614, longitude=19.9366, accuracy_m=12.0)

    assert "50.06" not in repr(fix) and "19.93" not in repr(fix)
    for off in (
        {"latitude": 91.0, "longitude": 0.0, "accuracy_m": 1.0},
        {"latitude": 0.0, "longitude": 0.0, "accuracy_m": -1.0},
        {"latitude": 0.0, "longitude": 0.0, "accuracy_m": float("inf")},
        {"latitude": float("nan"), "longitude": 0.0, "accuracy_m": 1.0},
    ):
        with pytest.raises(ALocationFixIsOffTheMap):
            LocationFix(**off)


def test_no_event_carries_a_position():
    game = _game()
    _absent(game)
    _arrives(game, when=20)

    for event in game.pull_events():
        fields = set(vars(event))
        assert not fields & {"latitude", "longitude", "accuracy_m", "fix"}


# --------------------------------------------------------------------------- #
# What the game says about each player on their record (#659)
# --------------------------------------------------------------------------- #


def test_on_time_is_played_through_once_the_game_is_played():
    """Oscar arrived at 17:08 — on time, nothing recorded — and is played
    through like everybody else once a score goes up."""

    game = _game()
    _absent(game, when=2)
    _arrives(game, when=8)

    assert game.turnout_of(OSCAR, now=at(40)) is None
    game.state_result(by=IVAN, score=_score(), occurred_at=at(65))

    assert {
        player: game.turnout_of(player, now=at(70))
        for player in (IVAN, MARTA, OSCAR, PAULA)
    } == dict.fromkeys((IVAN, MARTA, OSCAR, PAULA), Turnout.PLAYED_THROUGH)


def test_came_late_is_on_the_record_at_the_arrival_and_earns_nothing_back():
    game = _game()
    _absent(game)
    _arrives(game, when=22)

    assert game.turnout_of(OSCAR, now=at(23)) is Turnout.CAME_LATE
    game.state_result(by=IVAN, score=_score(), occurred_at=at(65))
    assert game.turnout_of(OSCAR, now=at(70)) is Turnout.CAME_LATE


def test_didnt_come_is_on_the_record_once_the_late_claim_is_over():
    """Provisional for a day, then final — and the three who came turned up to
    a game that never counted."""

    game = _game()
    _absent(game)

    assert game.turnout_of(OSCAR, now=at(31)) is None
    assert game.turnout_of(IVAN, now=at(31)) is None
    assert game.turnout_of(OSCAR, now=CLAIMS_CLOSE) is Turnout.DIDNT_COME
    assert game.turnout_of(IVAN, now=CLAIMS_CLOSE) is Turnout.TURNED_UP_UNCOUNTED


def test_a_confirmed_i_was_there_is_came_late():
    game = _game()
    _absent(game)
    game.claim_presence(by=OSCAR, occurred_at=at(60 * 10))
    game.confirm_presence(by=IVAN, claimant=OSCAR, occurred_at=at(60 * 11))

    assert game.turnout_of(OSCAR, now=CLAIMS_CLOSE) is Turnout.CAME_LATE


def test_somebody_off_the_court_and_a_game_called_off_say_nothing():
    game = _game()
    game.vacate(PAULA, occurred_at=at(-60 * 48))
    game.call_off(by=None, occurred_at=at(-60 * 24))

    assert game.turnout_of(PAULA, now=CLAIMS_CLOSE) is None
    assert game.turnout_of(IVAN, now=CLAIMS_CLOSE) is None
    assert game.turnout_of(STRANGER, now=CLAIMS_CLOSE) is None


# --------------------------------------------------------------------------- #
# The no-show report retired, and its rows fold to nothing
# --------------------------------------------------------------------------- #


def test_a_stored_no_show_report_and_its_dispute_fold_to_nothing():
    game = _game()
    reported = NoShowReported(
        game_id=game.game_id,
        player_id=OSCAR,
        reported_by=IVAN,
        occurred_at=at(120),
    )
    disputed = NoShowDisputed(
        game_id=game.game_id, player_id=OSCAR, occurred_at=at(130)
    )

    replayed = Game.from_history([*game.pull_events(), reported, disputed])

    assert replayed.attendance == {}
    after_the_window = instant(replayed.entry_closes_at)
    assert replayed.standing_at(after_the_window) is GameStanding.PLAYED_NO_SCORE
