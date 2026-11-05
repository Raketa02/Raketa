"""**Each new step reaches its person in time** (#663; ``docs/adr/0195`` §3,
§5; the mechanics §15.1, §17.2) — read from outside.

Wednesday 14 October, padel **17:00–18:00 at Ogrody 33**: Marta, Ivan, Oscar
and Paula, 30 zł each, booked by their yeses.

- Ivan taps *Oscar isn't here yet*: Oscar is told at once — and Ivan the
  moment Oscar arrives.
- At 18:00 the hour ends, and all four are asked *How did it go?*.
- Marta puts 6–4 6–3 up: the other side is asked *Is that right?*.
- Oscar says *I was there* the next morning: his courtmates are asked to
  confirm it.

Every notice opens **the game's result screen**, and a For fun game is told
none of them. Every act is taken over HTTP as the phone sends it, the outbox is
drained the way the worker drains it, the job is run by its builder and by the
console's press, and every claim is read off the list behind the bell and the
phones' pushes. The clock starts on Monday 5 October, 08:00 in Kraków, and
moves.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_ask_how_did_it_go
from app.bootstrap.jobs import HOW_DID_IT_GO_JOB
from app.engines.matchfit.core import SearchMode
from tests.api.console_world import SEED, runs
from tests.api.proposals_world import (
    INTENT_WANTING,
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    changes_intent,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

#: Ogrody 33's map point, as its desk dropped it.
OGRODY = (50.0600, 19.9400)
#: A fix 40 m north of it — at the club.
FROM_THE_CLUB = {
    "latitude": 50.0600 + 40 / 111_195.0,
    "longitude": 19.94,
    "accuracy_m": 10,
}
#: Wednesday 14 October, 17:00 in Kraków — their hour.
FIVE = warsaw(14, 17)
SIX = FIVE + timedelta(hours=1)
GAMES = "/api/v1/games"
NOTICES = "/api/v1/players/me/notices"


@pytest.fixture
def clock(app, payments):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


def to(clock: MovableClock, moment) -> None:
    clock.move(moment - clock.now())


@dataclass(frozen=True)
class Court:
    booking: str
    game: str
    marta: dict
    ivan: dict
    oscar: dict
    paula: dict
    #: Marta's partner, and the two across the net.
    partner: dict
    across: tuple[dict, dict]

    @property
    def four(self) -> tuple[dict, ...]:
        return (self.marta, self.ivan, self.oscar, self.paula)


async def a_court(
    client,
    session_factory,
    payments,
    clock,
    *,
    kind: SearchMode = SearchMode.COMPETITIVE,
) -> Court:
    """Their game at Ogrody 33 on Wednesday at 17:00, booked by the four
    yeses — each of them with a phone — and delivered, so what a test does
    next is told after it. The four are addressed on the seed system's
    reserved TLD, so the console may act as them."""

    club = await a_club_selling(
        client, name="Ogrody 33", point=OGRODY, email=f"desk.ogrody@{SEED}"
    )
    marta, ivan, oscar, paula = [
        await a_member(client, session_factory, payments, name, domain=SEED)
        for name in ("marta", "ivan", "oscar", "paula")
    ]
    group = await a_group(client, marta, club, ivan, oscar, paula)
    # Whom a game is booked for want its kind: a yes is held to it (Q127).
    for player in (marta, ivan, oscar, paula):
        await changes_intent(client, player, INTENT_WANTING[kind])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=FIVE,
        kind=kind,
        versions=((marta, ivan, oscar, paula),),
    )
    for player in (ivan, oscar, paula, marta):
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    assert booked is not None, said.text
    for player in (marta, ivan, oscar, paula):
        await has_a_phone(client, player)
    read = await client.get(GAMES, headers=marta["headers"])
    [game] = [g for g in read.json()["games"] if g["game_id"] == booked["game_id"]]
    side_of = {seat["player_id"]: seat["side"] for seat in game["seats"]}
    hers = side_of[str(marta["id"])]
    others = [p for p in (ivan, oscar, paula)]
    partner = next(p for p in others if side_of[str(p["id"])] == hers)
    across = tuple(p for p in others if side_of[str(p["id"])] != hers)
    return Court(
        booking=booked["booking_id"],
        game=booked["game_id"],
        marta=marta,
        ivan=ivan,
        oscar=oscar,
        paula=paula,
        partner=partner,
        across=across,  # type: ignore[arg-type]
    )


@pytest.fixture
async def court(client, session_factory, payments, clock, mailbox) -> Court:
    made = await a_court(client, session_factory, payments, clock)
    await mailbox.drain()
    return made


@pytest.fixture
async def for_fun(client, session_factory, payments, clock, mailbox) -> Court:
    made = await a_court(
        client, session_factory, payments, clock, kind=SearchMode.FOR_FUN
    )
    await mailbox.drain()
    return made


async def has_a_phone(client, player: dict) -> None:
    token = f"ExponentPushToken[{player['name']}-phone]"
    registered = await client.post(
        "/api/v1/players/me/devices", json={"token": token}, headers=player["headers"]
    )
    assert registered.status_code == 204, registered.text
    player["phone"] = token


async def told(client, mailbox, player: dict, kind: str) -> list[dict]:
    """Every notice of ``kind`` in the player's list, newest first."""

    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return [n for n in read.json()["notices"] if n["kind"] == kind]


def words(notices: list[dict]) -> list[tuple[str, str]]:
    return [(notice["title"], notice["body"]) for notice in notices]


def pushed(pushes, player: dict, kind: str) -> list[tuple[str, str, dict]]:
    return [
        (push.title, push.body, dict(push.data))
        for push in pushes.to(player["phone"])
        if push.data["kind"] == kind
    ]


async def not_here_yet(client, by: dict, court: Court, absent: dict):
    tapped = await client.post(
        f"{GAMES}/{court.game}/attendance/not-here-yet",
        json={"player_id": str(absent["id"]), "location": FROM_THE_CLUB},
        headers=by["headers"],
    )
    assert tapped.status_code == 200, tapped.text


async def arrived(client, by: dict, court: Court, who: dict):
    tapped = await client.post(
        f"{GAMES}/{court.game}/attendance/arrival",
        json={"player_id": str(who["id"]), "location": FROM_THE_CLUB},
        headers=by["headers"],
    )
    assert tapped.status_code == 200, tapped.text


async def i_was_there(client, by: dict, court: Court):
    claimed = await client.post(
        f"{GAMES}/{court.game}/attendance/claim", headers=by["headers"]
    )
    assert claimed.status_code == 200, claimed.text


async def yes_they_were_here(client, by: dict, court: Court, claimant: dict):
    confirmed = await client.post(
        f"{GAMES}/{court.game}/attendance/confirmation",
        json={"player_id": str(claimant["id"])},
        headers=by["headers"],
    )
    assert confirmed.status_code == 200, confirmed.text


async def puts_up(client, by: dict, court: Court, sets: list[tuple[int, int]]):
    stated = await client.post(
        f"{GAMES}/{court.game}/result",
        json={"score": {"sets": [{"a": a, "b": b} for a, b in sets]}},
        headers=by["headers"],
    )
    assert stated.status_code == 200, stated.text


async def agrees(client, by: dict, court: Court):
    accepted = await client.post(
        f"{GAMES}/{court.game}/result/acceptance", headers=by["headers"]
    )
    assert accepted.status_code == 200, accepted.text


async def the_hour_ends(session_factory, clock) -> None:
    """The job's own unit of work, as the scheduler runs it each tick."""

    async with session_factory() as session:
        await build_ask_how_did_it_go(session, clock=clock).execute()


# -- isn't here yet, and they're at the club -----------------------------------


async def test_the_absent_player_is_told_the_moment_somebody_taps_isnt_here_yet(
    client, clock, court, mailbox, pushes
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)

    [notice] = await told(client, mailbox, court.oscar, "NOT_HERE_YET")
    assert words([notice]) == [
        (
            "ivan is at Ogrody 33 and you're not there yet",
            "Tap I'm here when you arrive — Padel · Wed 17:00.",
        )
    ]
    # **The game's result screen**, which the booked game's id opens.
    assert (notice["opens"], notice["game_id"]) == ("RESULT", court.booking)
    assert notice["new"] is True
    [(title, body, data)] = pushed(pushes, court.oscar, "NOT_HERE_YET")
    assert (title, body) == words([notice])[0]
    assert (data["opens"], data["game_id"]) == ("RESULT", court.booking)
    # Nobody else is told anything about it.
    for player in (court.marta, court.ivan, court.paula):
        assert await told(client, mailbox, player, "NOT_HERE_YET") == []


async def test_whoever_tapped_is_told_the_moment_the_absent_player_arrives(
    client, clock, court, mailbox, pushes
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    await mailbox.drain()
    to(clock, FIVE + timedelta(minutes=22))
    await arrived(client, court.oscar, court, court.oscar)

    [notice] = await told(client, mailbox, court.ivan, "AT_THE_CLUB")
    assert words([notice]) == [
        ("oscar is at Ogrody 33", "Padel · Wed 17:00 — arrived at 17:22.")
    ]
    assert (notice["opens"], notice["game_id"], notice["your_own"]) == (
        "RESULT",
        court.booking,
        False,
    )
    assert [title for title, _, _ in pushed(pushes, court.ivan, "AT_THE_CLUB")] == [
        "oscar is at Ogrody 33"
    ]
    for player in (court.marta, court.oscar, court.paula):
        assert await told(client, mailbox, player, "AT_THE_CLUB") == []


async def test_saying_they_are_here_yourself_is_your_own_and_pushed_to_nobody(
    client, clock, court, mailbox, pushes
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    to(clock, FIVE + timedelta(minutes=8))
    await arrived(client, court.ivan, court, court.oscar)

    [notice] = await told(client, mailbox, court.ivan, "AT_THE_CLUB")
    # He saw it happen on his own screen (the mechanics Q102).
    assert (notice["your_own"], notice["new"]) == (True, False)
    assert pushed(pushes, court.ivan, "AT_THE_CLUB") == []


async def test_a_player_who_arrived_before_it_was_delivered_is_told_nothing_awaits(
    client, clock, court, mailbox
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    to(clock, FIVE + timedelta(minutes=6))
    await arrived(client, court.oscar, court, court.oscar)

    assert await told(client, mailbox, court.oscar, "NOT_HERE_YET") == []
    assert len(await told(client, mailbox, court.ivan, "AT_THE_CLUB")) == 1


# -- were they there? -----------------------------------------------------------


async def test_the_courtmates_are_asked_were_they_there_when_a_player_says_i_was_there(
    client, clock, court, mailbox, pushes
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    # Thursday 09:00: his phone died at the court, he says.
    to(clock, warsaw(15, 9))
    await i_was_there(client, court.oscar, court)

    for player in (court.marta, court.ivan, court.paula):
        [notice] = await told(client, mailbox, player, "WERE_THEY_THERE")
        assert words([notice]) == [
            (
                "Was oscar at Ogrody 33?",
                "oscar tapped I was there for Padel · Wed 17:00 — confirm it by "
                "17:30 if so.",
            )
        ]
        assert (notice["opens"], notice["game_id"]) == ("RESULT", court.booking)
        assert len(pushed(pushes, player, "WERE_THEY_THERE")) == 1
    assert await told(client, mailbox, court.oscar, "WERE_THEY_THERE") == []


async def test_a_claim_confirmed_before_it_was_delivered_asks_nobody(
    client, clock, court, mailbox
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    to(clock, warsaw(15, 9))
    await i_was_there(client, court.oscar, court)
    await yes_they_were_here(client, court.ivan, court, court.oscar)

    for player in (court.marta, court.ivan, court.paula):
        assert await told(client, mailbox, player, "WERE_THEY_THERE") == []


# -- how did it go? -------------------------------------------------------------


async def test_all_four_are_asked_how_did_it_go_when_the_hour_ends_and_only_once(
    client, session_factory, clock, court, mailbox, pushes
):
    to(clock, SIX - timedelta(seconds=30))
    await the_hour_ends(session_factory, clock)
    for player in court.four:
        assert await told(client, mailbox, player, "HOW_DID_IT_GO") == []

    to(clock, SIX + timedelta(seconds=20))
    await the_hour_ends(session_factory, clock)
    to(clock, SIX + timedelta(seconds=50))
    await the_hour_ends(session_factory, clock)

    for player in court.four:
        [notice] = await told(client, mailbox, player, "HOW_DID_IT_GO")
        assert words([notice]) == [
            (
                "How did it go?",
                "Padel at Ogrody 33 · Wed 14 Oct, 17:00 — put the score up.",
            )
        ]
        assert (notice["opens"], notice["game_id"]) == ("RESULT", court.booking)
        # Given at the hour's end, whenever the job came to it.
        assert notice["given_at"].startswith("2026-10-14T16:00:00")
        assert len(pushed(pushes, player, "HOW_DID_IT_GO")) == 1


async def test_a_game_whose_score_is_up_before_the_hour_ends_asks_nobody(
    client, session_factory, clock, court, mailbox
):
    to(clock, FIVE + timedelta(minutes=55))
    await puts_up(client, court.marta, court, [(6, 4), (6, 3)])
    to(clock, SIX + timedelta(seconds=20))
    await the_hour_ends(session_factory, clock)

    for player in court.four:
        assert await told(client, mailbox, player, "HOW_DID_IT_GO") == []


async def test_a_game_somebody_did_not_come_to_asks_nobody(
    client, session_factory, clock, court, mailbox
):
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    to(clock, SIX + timedelta(seconds=20))
    await the_hour_ends(session_factory, clock)

    for player in court.four:
        assert await told(client, mailbox, player, "HOW_DID_IT_GO") == []


async def test_the_console_presses_the_hour_ending(
    client, session_factory, clock, court, mailbox
):
    to(clock, SIX + timedelta(seconds=20))
    ran = await runs(client, HOW_DID_IT_GO_JOB)
    assert ran["done"] == 1, ran
    assert ran["says"] == "1 game(s) whose hour ended: its players asked How did it go?"
    again = await runs(client, HOW_DID_IT_GO_JOB)
    assert again["done"] == 0, again

    for player in court.four:
        assert len(await told(client, mailbox, player, "HOW_DID_IT_GO")) == 1
    sent = await client.get(f"/dev/as/{court.marta['id']}/sent")
    assert sent.status_code == 200, sent.text
    [row] = [
        n for n in sent.json()["notices"] if n["listed"]["kind"] == "HOW_DID_IT_GO"
    ]
    assert row["pushed"]["title"] == "How did it go?"
    assert row["pushed"]["data"]["opens"] == "RESULT"


# -- is that right? -------------------------------------------------------------


async def test_the_other_side_is_asked_is_that_right_when_a_score_goes_up(
    client, clock, court, mailbox, pushes
):
    to(clock, SIX + timedelta(minutes=5))
    await puts_up(client, court.marta, court, [(6, 4), (6, 3)])

    for player in court.across:
        [notice] = await told(client, mailbox, player, "IS_THAT_RIGHT")
        assert words([notice]) == [
            (
                "Is that right? · marta put a score up",
                "Padel · Wed 17:00 at Ogrody 33. If nobody answers by Thu 18:05, it "
                "becomes the result — saying nothing costs nothing.",
            )
        ]
        assert (notice["opens"], notice["game_id"]) == ("RESULT", court.booking)
        assert len(pushed(pushes, player, "IS_THAT_RIGHT")) == 1
    # Her own side put it up.
    for player in (court.marta, court.partner):
        assert await told(client, mailbox, player, "IS_THAT_RIGHT") == []


async def test_a_correction_asks_again_and_a_different_score_asks_the_first_side(
    client, clock, court, mailbox
):
    to(clock, SIX + timedelta(minutes=5))
    await puts_up(client, court.marta, court, [(6, 4), (6, 3)])
    await mailbox.drain()
    to(clock, SIX + timedelta(minutes=10))
    await puts_up(client, court.partner, court, [(6, 4), (6, 2)])
    await mailbox.drain()
    to(clock, SIX + timedelta(minutes=20))
    across = court.across[0]
    await puts_up(client, across, court, [(6, 4), (4, 6), (7, 5)])

    for player in court.across:
        assert [
            title
            for title, _ in words(await told(client, mailbox, player, "IS_THAT_RIGHT"))
        ] == [
            f"Is that right? · {court.partner['name']} changed the score",
            "Is that right? · marta put a score up",
        ]
    for player in (court.marta, court.partner):
        assert words(await told(client, mailbox, player, "IS_THAT_RIGHT")) == [
            (
                f"Is that right? · {across['name']} put a different score up",
                "Padel · Wed 17:00 at Ogrody 33. The two scores don't match — unless "
                "one side agrees with the other's by Thu 18:20, it settles then. "
                "Saying nothing costs nothing.",
            )
        ]


async def test_a_score_agreed_with_before_it_was_delivered_asks_nobody(
    client, clock, court, mailbox
):
    to(clock, SIX + timedelta(minutes=5))
    await puts_up(client, court.marta, court, [(6, 4), (6, 3)])
    await agrees(client, court.across[0], court)

    for player in court.four:
        assert await told(client, mailbox, player, "IS_THAT_RIGHT") == []


# -- for fun --------------------------------------------------------------------


async def test_a_for_fun_game_is_told_none_of_these(
    client, session_factory, clock, for_fun, mailbox
):
    court = for_fun
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    to(clock, FIVE + timedelta(minutes=22))
    await arrived(client, court.oscar, court, court.oscar)
    to(clock, SIX + timedelta(seconds=20))
    await the_hour_ends(session_factory, clock)
    to(clock, SIX + timedelta(minutes=5))
    await puts_up(client, court.marta, court, [(6, 4), (6, 3)])

    for player in court.four:
        for kind in (
            "NOT_HERE_YET",
            "AT_THE_CLUB",
            "HOW_DID_IT_GO",
            "IS_THAT_RIGHT",
            "WERE_THEY_THERE",
        ):
            assert await told(client, mailbox, player, kind) == [], (player, kind)


async def test_a_for_fun_claim_asks_nobody(client, clock, for_fun, mailbox):
    court = for_fun
    to(clock, FIVE + timedelta(minutes=5))
    await not_here_yet(client, court.ivan, court, court.oscar)
    to(clock, warsaw(15, 9))
    await i_was_there(client, court.oscar, court)

    for player in court.four:
        assert await told(client, mailbox, player, "WERE_THEY_THERE") == []
