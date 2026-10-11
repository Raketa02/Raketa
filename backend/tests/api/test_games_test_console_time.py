"""Time in the games test console (#592; ``docs/adr/0194`` §4, §5).

**Run it now** runs a timed rule's job — the scheduler's own unit of work —
over what is due at the real *now*, and leaves what is not due exactly as it
was. **A countdown on every pending moment** of a game's state pane says when a
press will find something. And three situations whose moment is a clock:
*About to expire* (5) and *Empty seat at the cut-off* (7) land on the next full
hour the rules allow and say when it fires; *Club day close* (11) writes the
last closed day's played games, so that running the day close pays the club and
emails its desk.

Every claim is read where somebody would read it: the protagonist's deck and
Home, the desk's payouts and its mail — and, for what only a job records, the
console's own state pane, which reads the record rather than the clock.

The world: **Bonarka Arena**, Instant, a padel court every hour at 30 zł a
seat, with a 24-hour cut-off and two hours' notice; **Kazimierz Padel**, On
request with thirty minutes to confirm — both desks on the seed's reserved TLD
— and nine members the seed could have made. The clock stands on **Monday 5
October 2026, 08:00 in Kraków**, so the last club day closed is Sunday's.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.jobs import build_scheduled_jobs
from app.core.config import Settings, get_settings
from app.modules.proposals.application.propose_games import DueForProposing
from tests.api import players_world as players
from tests.api.console_world import (
    CONSOLE,
    PLAYER,
    SEED,
    at,
    board_of,
    code_of,
    deck_ids,
    deck_of,
    home_of,
    pane_of,
    presses,
    says,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    a_player,
    makes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

#: The jobs the new games run, each with its *Run it now*.
GAMES_JOBS = (
    "proposer",
    "proposal-expiry",
    "request-timeout",
    "time-to-pay",
    "holding",
    "cut-off",
    "club-payouts",
    "new-bookings-summary",
    "rating-catch-up",
    "conversation-sweep",
)
#: Sunday 4 October — the last club day closed at Monday 08:00.
SUNDAY = "2026-10-04"


@pytest.fixture
def clock(app, payments):
    """Monday 5 October 2026, 08:00 in Kraków — the provider dating a payout's
    arrival off the same clock."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


@dataclass(frozen=True)
class World:
    #: Instant: a 24-hour cut-off and two hours' notice.
    bonarka: str
    bonarka_desk: dict
    #: On request, thirty minutes to confirm.
    kazimierz: str
    kazimierz_desk: dict
    group: UUID
    #: The protagonist — the phone in the tester's hand.
    marta: dict
    #: Everybody else, in the order they joined: Kuba, Zofia and Marek first.
    rest: tuple[dict, ...]

    @property
    def three(self) -> tuple[dict, ...]:
        return self.rest[:3]

    @property
    def four(self) -> tuple[dict, ...]:
        return (self.marta, *self.three)

    def named(self, name: str) -> dict:
        return next(
            member for member in (self.marta, *self.rest) if member["name"] == name
        )


@pytest.fixture
async def world(client, session_factory, payments, clock) -> World:
    bonarka, bonarka_desk = await a_club_and_its_desk(
        client, email=f"desk.bonarka@{SEED}"
    )
    kazimierz, kazimierz_desk = await a_club_and_its_desk(
        client,
        name="Kazimierz Padel",
        email=f"desk.kazimierz@{SEED}",
        way="ON_REQUEST",
        point=(50.05, 19.94),
    )
    marta, *rest = [
        await a_member(client, session_factory, payments, name, domain=SEED)
        for name in (
            "marta",
            "kuba",
            "zofia",
            "marek",
            "ola",
            "tomek",
            "ewa",
            "jan",
            "lena",
        )
    ]
    group = await a_group(client, marta, bonarka, *rest)
    return World(
        bonarka, bonarka_desk, kazimierz, kazimierz_desk, group, marta, tuple(rest)
    )


async def runs(client, job: str) -> dict:
    ran = await client.post(f"/dev/jobs/{job}")
    assert ran.status_code == 200, ran.text
    assert ran.json()["job"] == job
    return ran.json()


async def her_situation(client, situation: str, world: World, **extra):
    return await presses(
        client,
        situation,
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
        **extra,
    )


def moments_of(pane: dict) -> dict[str, tuple[str, str]]:
    """Each pending moment on a pane: when, and the job that acts at it."""

    return {m["moment"]: (m["at"], m["job"]) for m in pane["moments"]}


async def a_card(session_factory, clock, world: World, club: str, **kwargs) -> UUID:
    """A pick dealt to her and the three — Saturday 17:00 unless told otherwise."""

    return await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=club,
        versions=(world.four,),
        **kwargs,
    )


async def all_say_yes(client, game: UUID, world: World) -> dict:
    """The three from the console's rows, then her from her phone. Her answer."""

    for member in world.three:
        said = await says(client, CONSOLE, "yes", member, game)
        assert said.status_code == 200, said.text
    hers = await says(client, PLAYER, "yes", world.marta, game)
    assert hers.status_code == 200, hers.text
    return hers.json()


async def her_home_game(client, world: World, game: UUID) -> dict:
    [found] = [
        g for g in await home_of(client, world.marta) if g["booking_id"] == str(game)
    ]
    return found


# --------------------------------------------------------------------------- #
# Run it now: there for every job the new games run
# --------------------------------------------------------------------------- #


def _every_job_on() -> Settings:
    return get_settings().model_copy(
        update={
            name: True for name in Settings.model_fields if name.endswith("_ENABLED")
        }
    )


async def test_run_it_now_is_there_for_every_job_the_new_games_run(client):
    """Every job the scheduler registers has a *Run it now*, or is named with
    the reason it has none — so the next job registered is decided about."""

    listed = await client.get("/dev/jobs")

    assert listed.status_code == 200, listed.text
    here = [job["job"] for job in listed.json()["jobs"]]
    not_here = {job["job"]: job["why"] for job in listed.json()["not_here"]}
    registered = {
        job.name
        for job in build_scheduled_jobs(
            session_factory=object(),  # type: ignore[arg-type]
            settings=_every_job_on(),
            proposer_due=DueForProposing(),
        )
    }
    assert set(here) | set(not_here) == registered
    assert not set(here) & set(not_here)
    assert here == list(GAMES_JOBS)
    assert all(why for why in not_here.values())


@pytest.mark.parametrize("job", [job for job in GAMES_JOBS if job != "proposer"])
async def test_run_it_now_with_nothing_due_does_nothing(client, clock, world, job):
    ran = await runs(client, job)

    assert (ran["done"], ran["conflicts"]) == (0, 0)
    assert ran["says"]


async def test_a_job_the_console_does_not_run_is_not_there(client):
    ran = await client.post("/dev/jobs/uncommitted-photo-sweep")

    assert ran.status_code in (404, 405), ran.text


# --------------------------------------------------------------------------- #
# Run it now: the proposer
# --------------------------------------------------------------------------- #


async def test_run_it_now_runs_the_proposer_over_every_pool(client, clock, world):
    assert await deck_of(client, world.marta, world.group) == []

    ran = await runs(client, "proposer")

    assert ran["done"] >= 1, ran
    # Read as her phone reads it: the sweep dealt her group's cards.
    assert await deck_of(client, world.marta, world.group) != []


async def test_run_it_now_on_the_proposer_deals_nothing_twice(client, clock, world):
    await runs(client, "proposer")

    again = await runs(client, "proposer")

    assert again["done"] == 0, again


# --------------------------------------------------------------------------- #
# Run it now: the book-by sweep
# --------------------------------------------------------------------------- #


async def test_run_it_now_leaves_a_card_before_its_book_by_and_records_it_after(
    client, session_factory, clock, world
):
    """Monday 11:00 at Bonarka: two hours' notice, so it books by 09:00."""

    game = await a_card(
        session_factory, clock, world, world.bonarka, start=warsaw(5, 11)
    )

    assert (await runs(client, "proposal-expiry"))["done"] == 0
    assert str(game) in await deck_ids(client, world.marta, world.group)

    clock.move(timedelta(hours=1))
    # Gone from her deck at its book-by whether or not anything has swept…
    assert str(game) not in await deck_ids(client, world.marta, world.group)
    # …and the sweep records it once it is due, and once only.
    assert (await runs(client, "proposal-expiry"))["done"] == 1
    assert (await runs(client, "proposal-expiry"))["done"] == 0


# --------------------------------------------------------------------------- #
# Run it now: the chat sweep
# --------------------------------------------------------------------------- #


async def test_run_it_now_leaves_a_booked_game_s_chat_that_has_not_ended(
    client, session_factory, payments, clock, world
):
    game = await a_card(session_factory, clock, world, world.bonarka)
    await all_say_yes(client, game, world)
    await players.deliver_the_outbox(session_factory, payments=payments)
    rooms = await her_rooms(client, world)
    assert rooms, "her booked game opened its chat"

    ran = await runs(client, "conversation-sweep")

    assert (ran["done"], ran["conflicts"]) == (0, 0)
    assert await her_rooms(client, world) == rooms


async def her_rooms(client, world: World) -> list[str]:
    read = await client.get("/api/v1/conversations", headers=world.marta["headers"])
    assert read.status_code == 200, read.text
    return [room["conversation_id"] for room in read.json()["conversations"]]


# --------------------------------------------------------------------------- #
# Countdowns: every pending moment on a game's pane
# --------------------------------------------------------------------------- #


async def test_a_card_still_filling_counts_down_to_its_book_by(
    client, session_factory, clock, world
):
    game = await a_card(session_factory, clock, world, world.bonarka)

    pane = pane_of(await board_of(client, world.group), game)

    assert moments_of(pane) == {
        "BOOK_BY": (at(SATURDAY_FIVE - timedelta(hours=2)), "proposal-expiry")
    }
    [moment] = pane["moments"]
    assert moment["says"]


async def test_a_request_counts_down_to_the_club_s_answer(
    client, session_factory, clock, world
):
    game = await a_card(session_factory, clock, world, world.kazimierz)
    assert (await all_say_yes(client, game, world))["waiting_for_the_club"] is True

    pane = pane_of(await board_of(client, world.group), game)

    # A request no longer ends at its book-by: the club's answer is its moment.
    assert moments_of(pane) == {
        "CLUB_ANSWER_DUE": (
            at(MONDAY_MORNING + timedelta(minutes=30)),
            "request-timeout",
        )
    }


async def test_a_booked_game_counts_down_to_its_cut_off_and_its_days_close(
    client, session_factory, payments, clock, world
):
    """Booked on Monday morning for Saturday 17:00: its cut-off is Friday
    17:00, the desk is told on Monday's close, and paid on Saturday's."""

    game = await a_card(session_factory, clock, world, world.bonarka)
    assert (await all_say_yes(client, game, world))["booked"] is not None
    await players.deliver_the_outbox(session_factory, payments=payments)

    pane = pane_of(await board_of(client, world.group), game)

    assert moments_of(pane) == {
        "CUT_OFF": (at(warsaw(9, 17)), "cut-off"),
        "NEW_BOOKINGS_SUMMARY": (at(warsaw(5, 23)), "new-bookings-summary"),
        "CLUB_PAYOUT": (at(warsaw(10, 23)), "club-payouts"),
    }
    assert [m["moment"] for m in pane["moments"]] == [
        "NEW_BOOKINGS_SUMMARY",
        "CUT_OFF",
        "CLUB_PAYOUT",
    ]


async def test_a_game_filled_far_ahead_counts_down_to_its_holding_and_is_held_then(
    client, session_factory, payments, clock, world
):
    """Booked on Monday morning for Saturday 17 October at 17:00, its cut-off
    Friday 16 October: a Visa's hold would not last until then, so every seat
    is only checked, and held at its Holding time — Monday 12 October at
    17:00, four days before the cut-off — by *hold the shares* (#639)."""

    game = await a_card(
        session_factory, clock, world, world.bonarka, start=warsaw(17, 17)
    )
    assert (await all_say_yes(client, game, world))["booked"] is not None
    await players.deliver_the_outbox(session_factory, payments=payments)

    pane = pane_of(await board_of(client, world.group), game)

    assert moments_of(pane)["HOLDING"] == (at(warsaw(12, 17)), "holding")
    assert {charge["status"] for charge in pane["charges"]} == {"CHECKED"}
    # Not due: the press leaves every seat checked.
    assert (await runs(client, "holding"))["done"] == 0
    clock.move(warsaw(12, 17) - clock.now())
    ran = await runs(client, "holding")
    assert (ran["done"], ran["conflicts"]) == (4, 0)
    pane = pane_of(await board_of(client, world.group), game)
    assert {charge["status"] for charge in pane["charges"]} == {"HELD"}
    assert "HOLDING" not in moments_of(pane)
    assert moments_of(pane)["CUT_OFF"] == (at(warsaw(16, 17)), "cut-off")


async def test_a_game_booked_after_its_day_closed_is_summed_up_at_the_next_close(
    client, session_factory, payments, clock, world
):
    """Booked on Monday at 23:30 — after Monday's close — so its desk is told
    of it at Tuesday's."""

    clock.move(timedelta(hours=15, minutes=30))
    game = await a_card(session_factory, clock, world, world.bonarka)
    assert (await all_say_yes(client, game, world))["booked"] is not None

    pane = pane_of(await board_of(client, world.group), game)

    assert moments_of(pane)["NEW_BOOKINGS_SUMMARY"] == (
        at(warsaw(6, 23)),
        "new-bookings-summary",
    )


async def test_a_moment_once_passed_is_no_longer_counted_down(
    client, session_factory, payments, clock, world
):
    game = await a_card(session_factory, clock, world, world.bonarka)
    await all_say_yes(client, game, world)
    clock.move(timedelta(days=4, hours=10))  # Friday 18:00, past the cut-off

    pane = pane_of(await board_of(client, world.group), game)

    assert set(moments_of(pane)) == {"CLUB_PAYOUT"}


# --------------------------------------------------------------------------- #
# Situation 5 · About to expire
# --------------------------------------------------------------------------- #


async def test_about_to_expire_deals_her_a_card_that_goes_at_the_next_full_hour(
    client, clock, world
):
    pressed = await her_situation(client, "about-to-expire", world)

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    # The next full hour a book-by can be: Monday 11:00 at two hours' notice.
    assert (body["book_by"], body["starts_at"]) == (
        at(warsaw(5, 9)),
        at(warsaw(5, 11)),
    )
    assert body["club_name"] == "Bonarka Arena"
    assert "fires at 09:00 · 60 min" in body["says"]
    game = UUID(body["game_id"])
    # Her phone shows it, unanswered by anybody.
    [card] = [
        c
        for c in await deck_of(client, world.marta, world.group)
        if c["proposal_id"] == str(game)
    ]
    assert card["in_count"] == 0
    assert {p["player_id"] for p in body["dealt"]} == {str(m["id"]) for m in world.four}
    # Its pane counts down to it, and the book-by sweep acts only once it is due.
    pane = pane_of(await board_of(client, world.group), game)
    assert moments_of(pane) == {"BOOK_BY": (at(warsaw(5, 9)), "proposal-expiry")}
    clock.move(timedelta(minutes=59))
    assert (await runs(client, "proposal-expiry"))["done"] == 0
    assert str(game) in await deck_ids(client, world.marta, world.group)
    clock.move(timedelta(minutes=1))
    assert str(game) not in await deck_ids(client, world.marta, world.group)
    assert (await runs(client, "proposal-expiry"))["done"] == 1


async def test_about_to_expire_leaves_her_time_to_look_at_the_phone(
    client, clock, world
):
    """At 08:57 the next book-by is three minutes off — too soon to watch go —
    so the card books by 10:00 instead."""

    clock.move(timedelta(minutes=57))

    pressed = await her_situation(client, "about-to-expire", world)

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["book_by"] == at(warsaw(5, 10))
    assert "fires at 10:00 · 63 min" in pressed.json()["says"]


async def test_about_to_expire_skips_a_week_her_games_per_week_has_filled(
    client, session_factory, payments, clock, world
):
    """One game a week, and Saturday's is booked: her deck shows nothing more
    this week, so the card is next Monday's first hour."""

    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=world.marta["headers"],
    )
    assert capped.status_code == 200, capped.text
    booked = await a_card(session_factory, clock, world, world.bonarka)
    assert (await all_say_yes(client, booked, world))["booked"] is not None

    pressed = await her_situation(client, "about-to-expire", world)

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["starts_at"] == at(warsaw(12, 7))
    assert pressed.json()["game_id"] in await deck_ids(client, world.marta, world.group)


async def test_about_to_expire_says_so_when_no_card_can_be_dealt(client, clock, world):
    """Nobody in the group is rated in tennis."""

    pressed = await presses(
        client,
        "about-to-expire",
        group_id=world.group,
        sport="TENNIS",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 409, pressed.text
    assert code_of(pressed) == "situation_unavailable"


# --------------------------------------------------------------------------- #
# Situation 7 · Empty seat at the cut-off
# --------------------------------------------------------------------------- #


async def test_empty_seat_at_the_cut_off_opens_a_seat_before_the_next_cut_off(
    client, session_factory, payments, clock, world
):
    """Bonarka's cut-off is 24 hours: the next full hour one can fall on is
    09:00, so her game is Tuesday 09:00 — filled earlier, while it was on
    sale, and left by Kuba just now."""

    pressed = await her_situation(client, "empty-seat-at-the-cut-off", world)

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    assert (body["cut_off"], body["starts_at"]) == (
        at(warsaw(5, 9)),
        at(warsaw(6, 9)),
    )
    assert "fires at 09:00 · 60 min" in body["says"]
    assert body["left"]["player_id"] == str(world.named("kuba")["id"])
    game = UUID(body["game_id"])
    # Her phone: her game, with a seat open.
    assert (await her_home_game(client, world, game))["status"] == "SEAT_OPEN"
    await players.deliver_the_outbox(session_factory, payments=payments)
    pane = pane_of(await board_of(client, world.group), game)
    assert pane["booking"]["state"] == "SEAT_OPEN"
    assert moments_of(pane)["CUT_OFF"] == (at(warsaw(5, 9)), "cut-off")
    # Kuba's hold let go when he left; hers still held (#637).
    statuses = {c["player"]["name"]: c["status"] for c in pane["charges"]}
    assert (statuses["kuba"], statuses["marta"]) == ("CANCELLED", "HELD")

    # Not due: the cut-off leaves it as it is.
    clock.move(timedelta(minutes=59))
    assert (await runs(client, "cut-off"))["done"] == 0
    assert (
        pane_of(await board_of(client, world.group), game)["booking"]["state"]
        == "SEAT_OPEN"
    )

    # Due: called off, and every hold let go — nobody pays (#637).
    clock.move(timedelta(minutes=1))
    home = await her_home_game(client, world, game)
    assert (home["status"], home["called_off_reason"]) == (
        "CALLED_OFF",
        "SHORT_AT_THE_CUT_OFF",
    )
    assert (await runs(client, "cut-off"))["done"] == 1
    pane = pane_of(await board_of(client, world.group), game)
    assert pane["booking"]["state"] == "CALLED_OFF"
    marta = next(c for c in pane["charges"] if c["player"]["name"] == "marta")
    assert marta["status"] in ("RELEASING", "CANCELLED")
    assert marta["refund"] is None
    assert (await runs(client, "cut-off"))["done"] == 0


async def test_empty_seat_at_the_cut_off_answers_with_the_domain_s_refusal(
    client, clock, world
):
    """Nobody in the group is rated in tennis, so no four of them fit: the
    situation obeys the rules and says what the dealer said — and books
    nothing."""

    pressed = await presses(
        client,
        "empty-seat-at-the-cut-off",
        group_id=world.group,
        sport="TENNIS",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 409, pressed.text
    assert code_of(pressed) == "version_does_not_fit"
    assert await home_of(client, world.marta) == []


# --------------------------------------------------------------------------- #
# Situation 11 · Club day close
# --------------------------------------------------------------------------- #


async def payouts_of(client, desk: dict) -> list[dict]:
    read = await client.get("/api/v1/club/payouts", headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["payouts"]


async def test_club_day_close_writes_the_last_closed_day_s_played_games(
    client, session_factory, payments, clock, world, mailbox
):
    pressed = await her_situation(client, "club-day-close", world)

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    assert (body["day"], body["club_name"]) == (SUNDAY, "Bonarka Arena")
    assert body["closed_at"] == at(warsaw(4, 23))
    # Two games, two fours of the group — never her: her week is the phone's.
    assert len(body["games"]) == 2
    seated = [p["player_id"] for game in body["games"] for p in game["people"]]
    assert len(seated) == len(set(seated)) == 8
    assert str(world.marta["id"]) not in seated
    for game in body["games"]:
        # Played on Sunday, and booked inside it: after Saturday's close.
        assert at(warsaw(4, 7)) <= game["starts_at"] <= at(warsaw(4, 22))
        assert at(warsaw(3, 23)) <= game["booked_at"] < game["starts_at"]
    assert await home_of(client, world.marta) == []

    # The shares are captured from the outbox; then the day close pays the
    # club once…
    await players.deliver_the_outbox(session_factory, payments=payments)
    paid = await runs(client, "club-payouts")
    assert paid["done"] == 1, paid
    await mailbox.drain()
    [payout] = await payouts_of(client, world.bonarka_desk)
    assert payout["amount_grosze"] > 0
    assert (await runs(client, "club-payouts"))["done"] == 0
    # …and tells its desk the day's new bookings, once.
    told = await runs(client, "new-bookings-summary")
    assert told["done"] == 1, told
    summaries = [
        message
        for message in await mailbox.to(f"desk.bonarka@{SEED}")
        if message.subject == "New bookings today"
    ]
    assert len(summaries) == 1
    assert (await runs(client, "new-bookings-summary"))["done"] == 0


async def test_the_day_close_leaves_a_day_that_has_not_closed(
    client, session_factory, payments, clock, world
):
    """Her game today at Bonarka is played by the evening, but the day closes
    at 23:00: until then neither the payout nor the summary is due."""

    clock.move(timedelta(hours=-3))  # filled at five in the morning
    game = await a_card(
        session_factory, clock, world, world.bonarka, start=warsaw(5, 9)
    )
    assert (await all_say_yes(client, game, world))["booked"] is not None
    clock.move(timedelta(hours=3 + 14))  # Monday 22:00, the game long over
    await players.deliver_the_outbox(session_factory, payments=payments)

    assert (await runs(client, "club-payouts"))["done"] == 0
    assert (await runs(client, "new-bookings-summary"))["done"] == 0

    clock.move(timedelta(hours=1))  # 23:00: Monday has closed
    assert (await runs(client, "club-payouts"))["done"] == 1
    assert (await runs(client, "new-bookings-summary"))["done"] == 1


async def test_club_day_close_pressed_again_finds_the_day_closed_out(
    client, session_factory, payments, clock, world
):
    """Once Sunday is paid for and summed up at Bonarka, games written into it
    would wait for tonight's close — so the situation says so instead."""

    assert (await her_situation(client, "club-day-close", world)).status_code == 200
    await players.deliver_the_outbox(session_factory, payments=payments)
    await runs(client, "club-payouts")
    await runs(client, "new-bookings-summary")

    again = await her_situation(client, "club-day-close", world)

    assert again.status_code == 409, again.text
    assert code_of(again) == "situation_unavailable"
    assert "Bonarka Arena" in again.json()["message"]


# --------------------------------------------------------------------------- #
# Every situation here acts only as the seed's accounts
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("situation", ["about-to-expire", "empty-seat-at-the-cut-off"])
async def test_each_situation_refuses_a_protagonist_the_seed_did_not_create(
    client, payments, world, situation
):
    piotr = await a_player(client, payments, "piotr")

    pressed = await presses(
        client,
        situation,
        group_id=world.group,
        sport="PADEL",
        protagonist_id=piotr["id"],
    )

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"
