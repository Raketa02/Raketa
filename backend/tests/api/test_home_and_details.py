"""**Home and a game's details** (#542; the mechanics §3, §14; the screens
A4, A8): the reader's games from the moment they fill, each with its status and
money line and how many need them; a booked game's details — and never a code
to show at a desk (#651); a game still filling, opened by anybody dealt it; the
club's *Games* figure; and the booked game's room, which the details reach
through the reader's own list of rooms.

Every read is taken over HTTP as the phone or the club's website takes it, and
every game is made the way the platform makes one: proposed, answered over HTTP,
filled by its last yes against the **fake payment provider**. **Home sends what
Home draws** (#613): live games, games that ended less than a day after their
hour, and any game that needs the reader.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a
seat — with a 24-hour cut-off, so 28,55 zł back if you leave by **Friday
17:00**. Ola lives in Kraków, 3,3 km south of the club.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_clock
from app.modules.payments.domain.entered_cards import A_CARD_THE_BANK_ALWAYS_CHECKS
from tests.api import players_world as players
from tests.api.administration_world import (
    MARTA,
    invites,
    marta_sets_her_password,
    me,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_player,
    makes,
    says_no,
    says_yes,
    warsaw,
)
from tests.api.test_official_groups import an_official_group
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
CLUB_GROUPS = "/api/v1/club/groups"
CONVERSATIONS = "/api/v1/conversations"
#: Three kilometres south of Bonarka Arena's point.
IN_KRAKOW = (50.03, 19.95)
SATURDAY_FIVE_UTC = "2026-10-10T15:00:00Z"
FRIDAY_FIVE_UTC = "2026-10-09T15:00:00Z"
A_SCORE = {"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}}


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card that pays.
    Ola lives in Kraków."""

    return [
        await a_player(client, payments, "ola", location=IN_KRAKOW),
        *[await a_player(client, payments, name) for name in ("kuba", "ewa", "tomek")],
    ]


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club, *four[1:])


async def a_card(
    session_factory, clock, *, club: str, group: UUID, four: list[dict], **kwargs
) -> UUID:
    return await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=(tuple(four),),
        **kwargs,
    )


async def a_booked_game(
    client, session_factory, clock, *, club: str, group: UUID, four: list[dict], **kw
) -> dict:
    """The four's game, every one of them In: its booking and its Game."""

    proposal = await a_card(
        session_factory, clock, club=club, group=group, four=four, **kw
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    booked = last.json()["booked"]
    assert booked is not None, last.text
    return {"booking_id": booked["booking_id"], "game_id": booked["game_id"]}


async def home_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def details_of(client, player: dict, booking_id: str):
    return await client.get(f"/api/v1/bookings/{booking_id}", headers=player["headers"])


async def proposal_of(client, player: dict, proposal_id: UUID | str):
    return await client.get(
        f"/api/v1/proposals/{proposal_id}", headers=player["headers"]
    )


def names_of(tiles: list[dict]) -> list[str]:
    return [tile["nickname"] for tile in tiles]


def opponent_of(card: dict, four: list[dict]) -> dict:
    """Somebody on the other side of the reader's card."""

    theirs = card["sides"]["theirs"][0]["player_id"]
    return next(player for player in four if str(player["id"]) == theirs)


# --------------------------------------------------------------------------- #
# Home
# --------------------------------------------------------------------------- #


async def test_home_is_empty_before_any_game_fills(
    client, session_factory, clock, club, four, group
):
    await a_card(session_factory, clock, club=club, group=group, four=four)

    home = await home_of(client, four[0])

    assert home["games"] == []
    assert home["needing_you"] == 0
    assert home["read_at"] == "2026-10-05T06:00:00Z"


async def test_every_player_finds_the_booked_game_on_home_with_its_money_line(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )

    for player in four:
        home = await home_of(client, player)
        [card] = home["games"]
        assert home["needing_you"] == 0
        assert card["booking_id"] == booked["booking_id"]
        assert card["game_id"] == booked["game_id"]
        assert card["pool_id"] == str(group)
        assert card["sport"] == "PADEL"
        assert card["kind"] == "COMPETITIVE"
        assert card["status"] == "BOOKED"
        assert card["needs_you"] is False
        assert card["starts_at"] == SATURDAY_FIVE_UTC
        assert card["club"] == {"id": club, "name": "Bonarka Arena"}
        assert (card["court_name"], card["indoor"]) == ("Court 1", True)
        assert card["money"] == {
            "share_grosze": 30_00,
            "paid": False,
            "share_state": "HELD",
            "held_from": None,
            "taken_at": FRIDAY_FIVE_UTC,
            "free_to_leave_until": FRIDAY_FIVE_UTC,
            "refunded_grosze": None,
        }
        yours, theirs = card["sides"]["yours"], card["sides"]["theirs"]
        assert yours[0]["player_id"] == str(player["id"])
        assert yours[0]["is_you"] is True
        assert len(yours) == len(theirs) == 2
        assert {tile["player_id"] for tile in yours + theirs} == {
            str(one["id"]) for one in four
        }
        # Held until the cut-off, which takes them (#637).
        assert not any(tile["paid"] for tile in yours + theirs)
        assert sorted(names_of(yours + theirs)) == ["ewa", "kuba", "ola", "tomek"]


async def test_from_the_cut_off_on_the_money_line_is_paid(
    client, session_factory, clock, club, four, group
):
    await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=4, hours=9))  # Friday 17:00

    [card] = (await home_of(client, four[0]))["games"]

    assert card["status"] == "BOOKED"
    assert (card["money"]["paid"], card["money"]["share_state"]) == (True, "TAKEN")
    assert card["money"]["free_to_leave_until"] is None
    assert all(tile["paid"] for tile in card["sides"]["yours"])


async def test_from_its_hour_the_game_needs_its_result_and_the_badge_counts_it(
    client, session_factory, clock, club, four, group
):
    await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=5, hours=9))  # Saturday 17:00

    home = await home_of(client, four[0])

    [card] = home["games"]
    assert card["status"] == "NEEDS_RESULT"
    assert card["needs_you"] is True
    assert home["needing_you"] == 1


async def test_a_score_needs_only_the_side_whose_answer_it_waits_on(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=5, hours=10))
    ola = four[0]
    [card] = (await home_of(client, ola))["games"]
    partner = next(
        one for one in four if str(one["id"]) == card["sides"]["yours"][1]["player_id"]
    )
    rival = opponent_of(card, four)
    told = await client.post(
        f"/api/v1/games/{booked['game_id']}/result",
        json=A_SCORE,
        headers=ola["headers"],
    )
    assert told.status_code == 200, told.text

    for player, waits in ((ola, False), (partner, False), (rival, True)):
        home = await home_of(client, player)
        [card] = home["games"]
        assert card["status"] == "CONFIRM_THE_RESULT"
        assert card["needs_you"] is waits
        assert home["needing_you"] == int(waits)


async def test_a_score_nobody_answered_is_counted_once_its_window_closes(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=5, hours=10))
    await client.post(
        f"/api/v1/games/{booked['game_id']}/result",
        json=A_SCORE,
        headers=four[0]["headers"],
    )
    clock.move(timedelta(hours=25))

    # A day after the hour's end too, so off Home (#613): its details say it.
    details = (await details_of(client, four[2], booked["booking_id"])).json()

    assert details["status"] == "COUNTED"
    assert details["needs_you"] is False


async def test_a_full_game_nobody_recorded_ends_played_no_score(
    client, session_factory, clock, club, four, group
):
    """Played, for all four, and no Level moves (#655): the status that took
    *Never played*'s place."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    # A day after the hour's end: Sunday 18:00.
    clock.move(timedelta(days=6, hours=10))

    details = (await details_of(client, four[0], booked["booking_id"])).json()
    home = await home_of(client, four[0])

    assert details["status"] == "PLAYED_NO_SCORE"
    assert details["uncounted_reason"] is None
    # Its entry closes as its day on Home ends (#613).
    assert home["games"] == []
    assert home["needing_you"] == 0


async def test_the_badge_counts_a_payment_to_confirm_beside_the_cards(
    client, session_factory, clock, payments, club, four
):
    """A payment to confirm is a game that needs the player (the mechanics §3)
    — counted once: the game waiting for it is on Home too (#625), and asks
    nothing more of anybody."""

    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    players = [tomek, *four[:3]]
    group = await a_group(client, four[0], club, tomek, *four[1:3])
    proposal = await a_card(
        session_factory, clock, club=club, group=group, four=players
    )
    for player in players:
        await says_yes(client, player, proposal)

    home = await home_of(client, tomek)

    [card] = home["games"]
    assert (card["status"], card["needs_you"]) == ("WAITING_FOR_A_PAYMENT", False)
    assert home["needing_you"] == 1


async def test_home_lists_the_soonest_game_first(
    client, session_factory, clock, payments, club, four, group
):
    saturday = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    tuesday = await a_booked_game(
        client,
        session_factory,
        clock,
        club=club,
        group=group,
        four=four,
        start=warsaw(6, 19),
    )

    games = (await home_of(client, four[1]))["games"]

    assert [game["booking_id"] for game in games] == [
        tuesday["booking_id"],
        saturday["booking_id"],
    ]


async def test_nobody_else_finds_the_game_on_their_home(
    client, session_factory, clock, payments, club, four, group
):
    await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    stranger = await a_player(client, payments, "stranger")

    assert (await home_of(client, stranger))["games"] == []


# --------------------------------------------------------------------------- #
# Home sends what Home draws (#613, F-HOME-5.1)
# --------------------------------------------------------------------------- #
#
# The bookings are read only from the earliest hour a game can still ask
# anything of its players, off the games' own clocks: Saturday's game has its
# entry close Sunday 18:00, and a score made then waits for its answer — as a
# report made then waits for its dispute — until Monday 18:00, when Home stops
# reading it. Of those, a card is sent while live, ended less than a day after
# its hour's end, or needing the reader. **Only a score put on the table again
# reaches further**: a correction re-dates its side's score, and that side may
# correct again while the other has not answered.

#: Another score, for a side correcting its own.
ANOTHER_SCORE = {"score": {"sets": [{"a": 6, "b": 4}, {"a": 7, "b": 5}]}}
#: The other side's score of the same game, for a counter.
A_SCORE_THEIRS = {"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}}
#: A minute before the entry closes.
SUNDAY_ONE_MINUTE_TO_SIX = warsaw(11, 17) + timedelta(minutes=59)
#: Two minutes before Home stops reading the game.
MONDAY_TWO_MINUTES_TO_SIX = warsaw(12, 17) + timedelta(minutes=58)


async def on_the_game(client, player: dict, game_id: str, act: str, body=None):
    told = await client.post(
        f"/api/v1/games/{game_id}/{act}", json=body, headers=player["headers"]
    )
    assert told.status_code == 200, told.text
    return told


async def test_a_game_a_month_old_is_not_on_home(
    client, session_factory, clock, club, four, group
):
    await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=35))  # a month after Saturday's game

    home = await home_of(client, four[0])

    assert home["games"] == []
    assert home["needing_you"] == 0


async def test_an_ended_game_is_sent_until_a_day_after_its_hour_ends(
    client, session_factory, clock, club, four, group
):
    """Counted by an agreement: settled at Saturday midnight, six hours after
    the score it agrees with."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.at = warsaw(10, 18)
    ola = four[0]
    await on_the_game(client, ola, booked["game_id"], "result", A_SCORE)
    [card] = (await home_of(client, ola))["games"]
    await on_the_game(
        client, opponent_of(card, four), booked["game_id"], "result/acceptance"
    )

    clock.at = warsaw(11, 17)  # 23 hours after the hour's end
    [card] = (await home_of(client, ola))["games"]
    assert card["status"] == "COUNTED"

    clock.at = warsaw(11, 19)  # 25 hours after it
    assert (await home_of(client, ola))["games"] == []
    details = (await details_of(client, ola, booked["booking_id"])).json()
    assert details["status"] == "COUNTED"


async def test_a_booked_game_far_ahead_is_sent(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client,
        session_factory,
        clock,
        club=club,
        group=group,
        four=four,
        start=warsaw(30, 17),
    )

    [card] = (await home_of(client, four[0]))["games"]

    assert card["booking_id"] == booked["booking_id"]
    assert card["status"] == "BOOKED"


async def test_a_game_with_a_seat_open_is_sent_and_counted(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    left = await client.post(
        f"/api/v1/bookings/{booked['booking_id']}/departure",
        headers=four[1]["headers"],
    )
    assert left.status_code == 200, left.text

    home = await home_of(client, four[0])

    [card] = home["games"]
    assert card["status"] == "SEAT_OPEN"
    assert home["needing_you"] == 1


async def test_a_result_still_to_enter_is_sent_and_counted_until_the_entry_closes(
    client, session_factory, clock, club, four, group
):
    await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )

    clock.at = SUNDAY_ONE_MINUTE_TO_SIX
    home = await home_of(client, four[0])
    [card] = home["games"]
    assert card["status"] == "NEEDS_RESULT"
    assert home["needing_you"] == 1

    clock.at = warsaw(11, 18)  # never played, and a day after the hour's end
    home = await home_of(client, four[0])
    assert home["games"] == []
    assert home["needing_you"] == 0


async def test_a_score_made_as_the_entry_closes_is_sent_and_counted_while_it_waits(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.at = SUNDAY_ONE_MINUTE_TO_SIX
    ola = four[0]
    await on_the_game(client, ola, booked["game_id"], "result", A_SCORE)
    [card] = (await home_of(client, ola))["games"]
    rival = opponent_of(card, four)

    clock.at = MONDAY_TWO_MINUTES_TO_SIX
    theirs = await home_of(client, rival)
    ours = await home_of(client, ola)

    [card] = theirs["games"]
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", True)
    assert theirs["needing_you"] == 1
    # Ola's side's score waits on the other side: live, needing nothing of her.
    [card] = ours["games"]
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", False)
    assert ours["needing_you"] == 0


async def test_a_late_claim_still_to_make_needs_only_the_player_who_didn_t_come(
    client, session_factory, clock, club, four, group
):
    """An *uncounted* card whose *I was there* the reader may still say needs
    them, and only them, while the late claim's day runs (#657) — and needs
    nobody once it is over, though it stays on Home until the shelf."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    ola, _, _, tomek = four
    clock.at = warsaw(10, 17) + timedelta(minutes=10)
    await on_the_game(
        client,
        ola,
        booked["game_id"],
        "attendance/not-here-yet",
        {
            "player_id": str(tomek["id"]),
            # Bonarka Arena's own point.
            "location": {"latitude": 50.06, "longitude": 19.95, "accuracy_m": 8},
        },
    )

    clock.at = warsaw(11, 9)
    absent = await home_of(client, tomek)
    tapper = await home_of(client, ola)

    [card] = absent["games"]
    assert (card["status"], card["needs_you"]) == ("UNCOUNTED", True)
    assert card["uncounted_reason"] == "DIDNT_COME"
    assert absent["needing_you"] == 1
    [card] = tapper["games"]
    assert (card["status"], card["needs_you"]) == ("UNCOUNTED", False)
    assert tapper["needing_you"] == 0

    clock.at = warsaw(11, 17) + timedelta(minutes=30)  # the late claim's day is over
    absent = await home_of(client, tomek)
    [card] = absent["games"]
    assert (card["status"], card["needs_you"]) == ("UNCOUNTED", False)
    assert absent["needing_you"] == 0


async def a_score_corrected_as_the_entry_closes(
    client, session_factory, clock, *, club, group, four
) -> tuple[dict, dict]:
    """Ola's score at five on Sunday, corrected by her in the entry window's
    last minute — the last moment a correction is taken (#654) — the game, and
    her rival."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.at = warsaw(11, 17)
    ola = four[0]
    await on_the_game(client, ola, booked["game_id"], "result", A_SCORE)
    [card] = (await home_of(client, ola))["games"]
    clock.at = SUNDAY_ONE_MINUTE_TO_SIX
    await on_the_game(client, ola, booked["game_id"], "result", ANOTHER_SCORE)
    return booked, opponent_of(card, four)


async def test_a_score_corrected_as_the_entry_closes_waits_a_day_from_the_correction(
    client, session_factory, clock, club, four, group
):
    """**A correction re-dates its side's score**, until the entry window
    closes (#654): the score waits on the reader a day from its last
    correction, and Home sends it until then — and a correction a minute later
    is refused."""

    booked, rival = await a_score_corrected_as_the_entry_closes(
        client, session_factory, clock, club=club, group=group, four=four
    )
    ola = four[0]

    clock.at = SUNDAY_ONE_MINUTE_TO_SIX + timedelta(minutes=1)
    refused = await client.post(
        f"/api/v1/games/{booked['game_id']}/result",
        json=A_SCORE,
        headers=ola["headers"],
    )
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "corrections_have_closed"

    clock.at = MONDAY_TWO_MINUTES_TO_SIX
    theirs = await home_of(client, rival)
    ours = await home_of(client, ola)

    [card] = theirs["games"]
    assert card["booking_id"] == booked["booking_id"]
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", True)
    assert theirs["needing_you"] == 1
    [card] = ours["games"]
    assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", False)

    clock.at = SUNDAY_ONE_MINUTE_TO_SIX + timedelta(days=1)  # counted by silence
    theirs = await home_of(client, rival)
    assert theirs["games"] == []
    assert theirs["needing_you"] == 0


async def test_a_counter_to_a_corrected_score_waits_a_day_of_its_own(
    client, session_factory, clock, club, four, group
):
    """The rival counters on Monday: two scores now wait on each other's side
    for a day from the later — past the correction's day, and past the hour
    Home otherwise reads from, so Home finds it by the score."""

    booked, rival = await a_score_corrected_as_the_entry_closes(
        client, session_factory, clock, club=club, group=group, four=four
    )
    ola = four[0]
    clock.at = warsaw(12, 17)
    await on_the_game(client, rival, booked["game_id"], "result", A_SCORE_THEIRS)

    clock.at = warsaw(13, 16)  # the correction is 46 hours old, the counter 23
    for player in (ola, rival):
        home = await home_of(client, player)
        [card] = home["games"]
        assert (card["status"], card["needs_you"]) == ("CONFIRM_THE_RESULT", True)
        assert home["needing_you"] == 1

    clock.at = warsaw(13, 17)  # a day after the counter: disputed
    for player in (ola, rival):
        assert (await home_of(client, player))["games"] == []


# --------------------------------------------------------------------------- #
# A booked game's details
# --------------------------------------------------------------------------- #


async def test_a_player_in_the_game_reads_its_details(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )

    read = await details_of(client, four[0], booked["booking_id"])

    assert read.status_code == 200, read.text
    details = read.json()
    assert details["booking_id"] == booked["booking_id"]
    assert details["game_id"] == booked["game_id"]
    assert details["pool_id"] == str(group)
    assert details["sport"] == "PADEL"
    assert details["kind"] == "COMPETITIVE"
    assert details["status"] == "BOOKED"
    assert details["needs_you"] is False
    assert details["starts_at"] == SATURDAY_FIVE_UTC
    assert details["ends_at"] == "2026-10-10T16:00:00Z"
    assert details["where"] == {"id": club, "name": "Bonarka Arena", "distance_km": 3.3}
    assert (details["court_name"], details["indoor"]) == ("Court 1", True)
    assert details["money"] == {
        "share_grosze": 30_00,
        "paid": False,
        "share_state": "HELD",
        "held_from": None,
        "taken_at": FRIDAY_FIVE_UTC,
        "free_to_leave_until": FRIDAY_FIVE_UTC,
        "refunded_grosze": None,
    }
    yours, theirs = details["sides"]["yours"], details["sides"]["theirs"]
    assert yours[0]["player_id"] == str(four[0]["id"])
    assert yours[0]["nickname"] == "ola"
    assert [tile["is_you"] for tile in yours + theirs] == [True, False, False, False]
    assert not any(tile["paid"] for tile in yours + theirs)
    assert all(tile["level"] is not None for tile in yours + theirs)
    assert details["shows_forecast"] is True


async def test_the_forecast_the_details_draw_is_the_game_s_own_pairing(
    client, session_factory, clock, club, four, group
):
    """*Balance forecast — as built today* (the screens A4.1): the booked game is
    an ordinary Game, and its pairing read answers while the details draw it."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    details = (await details_of(client, four[0], booked["booking_id"])).json()

    pairing = await client.get(
        f"/api/v1/games/{booked['game_id']}/pairing", headers=four[0]["headers"]
    )

    assert details["shows_forecast"] is True
    assert pairing.status_code == 200, pairing.text
    assert {seat["player_id"] for seat in pairing.json()["seats"]} == {
        str(player["id"]) for player in four
    }


async def test_on_the_game_day_the_details_carry_no_check_in(
    client, session_factory, clock, club, four, group
):
    """Desk check-in is removed (#651): no code to show at the desk, and no tile
    says who the desk saw — not even on the game's day."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=5))  # Saturday 08:00

    details = (await details_of(client, four[0], booked["booking_id"])).json()

    assert details["status"] == "BOOKED"
    assert "check_in" not in details
    tiles = (*details["sides"]["yours"], *details["sides"]["theirs"])
    assert all("checked_in" not in tile for tile in tiles)


async def test_the_forecast_is_not_drawn_once_a_score_is_told(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    clock.move(timedelta(days=5, hours=10))
    await client.post(
        f"/api/v1/games/{booked['game_id']}/result",
        json=A_SCORE,
        headers=four[0]["headers"],
    )

    details = (await details_of(client, four[0], booked["booking_id"])).json()

    assert details["status"] == "CONFIRM_THE_RESULT"
    assert details["shows_forecast"] is False


async def test_nobody_off_the_court_reads_a_booking(
    client, session_factory, clock, payments, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    stranger = await a_player(client, payments, "stranger")

    for booking_id in (booked["booking_id"], str(uuid4())):
        refused = await details_of(client, stranger, booking_id)
        assert refused.status_code == 404, refused.text
        assert refused.json()["code"] == "booking_not_found"


# --------------------------------------------------------------------------- #
# A game still filling
# --------------------------------------------------------------------------- #


async def test_a_player_still_deciding_reads_their_own_card(
    client, session_factory, clock, club, four, group
):
    proposal = await a_card(session_factory, clock, club=club, group=group, four=four)
    await says_yes(client, four[1], proposal)

    read = await proposal_of(client, four[0], proposal)

    assert read.status_code == 200, read.text
    details = read.json()
    assert details["proposal_id"] == str(proposal)
    assert details["pool_id"] == str(group)
    assert details["type"] == "PICKED_FOR_YOU"
    assert details["challenger"] is None
    assert details["status"] == "FILLING"
    assert details["actions"] == ["YES", "NO"]
    assert details["your_payment"] is None
    assert details["in_count"] == 1
    assert details["seats"] == 4
    assert details["starts_at"] == SATURDAY_FIVE_UTC
    assert details["where"] == {"id": club, "name": "Bonarka Arena", "distance_km": 3.3}
    assert "court_name" not in details
    assert details["share_grosze"] == 30_00
    assert details["no_free_cancellation"] is False
    # Bonarka's one padel court is indoor: the card promises it (Q122).
    assert details["indoor"] is True
    tiles = details["sides"]["yours"] + details["sides"]["theirs"]
    assert {tile["player_id"] for tile in tiles} == {str(one["id"]) for one in four}
    assert details["sides"]["yours"][0]["is_you"] is True
    assert [tile["nickname"] for tile in tiles if tile["is_in"]] == ["kuba"]
    assert len(details["overlap"]["cells"]) == 21


async def test_a_player_in_reads_everybody_in_and_may_withdraw(
    client, session_factory, clock, club, four, group
):
    proposal = await a_card(session_factory, clock, club=club, group=group, four=four)
    await says_yes(client, four[1], proposal)
    await says_yes(client, four[0], proposal)

    details = (await proposal_of(client, four[0], proposal)).json()

    assert details["actions"] == ["WITHDRAW"]
    assert details["in_count"] == 2
    tiles = details["sides"]["yours"] + details["sides"]["theirs"]
    assert sorted(tile["nickname"] for tile in tiles) == ["kuba", "ola"]
    assert all(tile["is_in"] for tile in tiles)


async def test_a_no_is_final_and_offers_nothing_more(
    client, session_factory, clock, club, four, group
):
    proposal = await a_card(session_factory, clock, club=club, group=group, four=four)
    await says_no(client, four[0], proposal)

    details = (await proposal_of(client, four[0], proposal)).json()

    assert details["status"] == "FILLING"
    assert details["actions"] == []


async def test_somebody_it_is_nothing_to_reads_nothing(
    client, session_factory, clock, payments, club, four, group
):
    proposal = await a_card(session_factory, clock, club=club, group=group, four=four)
    member = await a_player(client, payments, "member")
    joined = await client.post(
        f"/api/v1/groups/{group}/membership", headers=member["headers"]
    )
    assert joined.status_code in (200, 201), joined.text
    stranger = await a_player(client, payments, "stranger")

    for reader, proposal_id in (
        (member, proposal),
        (stranger, proposal),
        (four[0], uuid4()),
    ):
        refused = await proposal_of(client, reader, proposal_id)
        assert refused.status_code == 404, refused.text
        assert refused.json()["code"] == "proposal_not_found"


async def test_a_player_who_left_the_group_reads_nothing(
    client, session_factory, clock, club, four, group
):
    proposal = await a_card(session_factory, clock, club=club, group=group, four=four)
    left = await client.delete(
        f"/api/v1/groups/{group}/membership", headers=four[2]["headers"]
    )
    assert left.status_code in (200, 204), left.text

    refused = await proposal_of(client, four[2], proposal)

    assert refused.status_code == 404, refused.text


async def test_a_card_with_somebody_in_the_reader_blocked_is_not_shown_to_them(
    client, session_factory, clock, club, four, group
):
    proposal = await a_card(session_factory, clock, club=club, group=group, four=four)
    await says_yes(client, four[1], proposal)
    blocked = await players.block_between(client, four[0]["token"], four[1]["id"])
    assert blocked.status_code in (200, 201, 204), blocked.text

    refused = await proposal_of(client, four[0], proposal)

    assert refused.status_code == 404, refused.text


async def test_a_filled_game_reads_filled_with_nothing_to_do(
    client, session_factory, clock, club, four, group
):
    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )

    details = (await proposal_of(client, four[0], booked["booking_id"])).json()

    assert details["status"] == "FILLED"
    assert details["actions"] == []
    # Its court is given now: the kind is the booking's to say, never read off
    # the courts still free (#671).
    assert details["indoor"] is None


async def test_a_refused_payment_is_confirmed_from_the_details(
    client, session_factory, clock, payments, club, four
):
    tomek = await a_player(
        client, payments, "tomek2", entered=A_CARD_THE_BANK_ALWAYS_CHECKS
    )
    players = [tomek, *four[:3]]
    group = await a_group(client, four[0], club, tomek, *four[1:3])
    proposal = await a_card(
        session_factory, clock, club=club, group=group, four=players
    )
    for player in players:
        await says_yes(client, player, proposal)

    details = (await proposal_of(client, tomek, proposal)).json()

    # His seat is his alone while his time to pay runs (#625).
    assert details["status"] == "WAITING_FOR_A_PAYMENT"
    assert details["actions"] == ["CONFIRM_PAYMENT", "LEAVE"]
    owed = (
        await client.get(
            "/api/v1/players/me/payments-to-confirm", headers=tomek["headers"]
        )
    ).json()["payments"]
    assert details["your_payment"] == {
        "seat_charge_id": owed[0]["seat_charge_id"],
        "refusal": "AUTHENTICATION_REQUIRED",
        "confirm_by": "2026-10-05T06:30:00Z",
        "time_to": "FIX_THE_CARD",
    }


# --------------------------------------------------------------------------- #
# The club's Games figure
# --------------------------------------------------------------------------- #


async def test_the_club_counts_the_games_booked_in_each_official_group(
    client, session_factory, clock, mailbox, four
):
    club, desk = await a_club_and_its_desk(client, name="Ogrody 33")
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta_headers = await marta_sets_her_password(client, mailbox)
    marta = {
        "id": (await me(client, marta_headers))["id"],
        "headers": marta_headers,
        "administrator_id": row["id"],
    }
    official = await an_official_group(client, marta, club, join_policy="ANYONE")
    quiet = await an_official_group(
        client, marta, club, name="Ogrody open play", join_policy="ANYONE"
    )
    for player in four:
        joined = await client.post(
            f"/api/v1/groups/{official['id']}/membership", headers=player["headers"]
        )
        assert joined.status_code in (200, 201), joined.text
    await a_booked_game(
        client,
        session_factory,
        clock,
        club=club,
        group=UUID(official["id"]),
        four=four,
    )

    read = await client.get(CLUB_GROUPS, headers=desk)

    assert read.status_code == 200, read.text
    games = {group["id"]: group["games"] for group in read.json()["groups"]}
    assert games == {official["id"]: 1, quiet["id"]: 0}


# --------------------------------------------------------------------------- #
# The chat: a join over the reader's rooms
# --------------------------------------------------------------------------- #


async def test_the_booked_game_s_room_is_in_every_player_s_rooms(
    client, session_factory, clock, payments, mailbox, club, four, group
):
    """The details reach the chat as Classic play's game screen does — the
    reader's room whose ``game_id`` is the game's (``docs/adr/0149`` §3)."""

    booked = await a_booked_game(
        client, session_factory, clock, club=club, group=group, four=four
    )
    await mailbox.drain()

    for player in four:
        read = await client.get(CONVERSATIONS, headers=player["headers"])
        assert read.status_code == 200, read.text
        [room] = read.json()["conversations"]
        assert room["game_id"] == booked["game_id"]
        assert room["booking_id"] == booked["booking_id"]
    stranger = await a_player(client, payments, "stranger")
    theirs = await client.get(CONVERSATIONS, headers=stranger["headers"])
    assert theirs.json()["conversations"] == []
