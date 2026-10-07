"""The games test console's *Sent* pane (#594; ``docs/adr/0194``).

**Who was told what, without a second device**: each person's row opens their
in-app notices as the bell lists them, the push each notice was given as — what
their phones were pushed, or, with none registered, what they would have been —
and their emails from the outgoing mail queue, each linking to it in the local
mail catcher.

Every claim is checked against what a person would have received: the list
behind their bell, their phone's pushes and the mail the relay was handed. The
world is the console's own (``test_games_test_console.py``): a club selling a
padel court every hour, four members addressed on the seed system's reserved
TLD, and one who is not. The clock stands on **Monday 5 October 2026, 08:00 in
Kraków**.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.core.config import get_settings
from tests.api import players_world as players
from tests.api.console_world import PLAYER, SEED, code_of, presses, says
from tests.api.proposals_world import MONDAY_MORNING, a_club_selling, a_group, a_member
from tests.unit.fake_clock import MovableClock

#: The fill's notice — *It's a game! · you paid* — and its email.
BOOKED = "GAME_BOOKED"
BOOKED_AND_PAID = "payments.game_booked.player"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@dataclass(frozen=True)
class World:
    group: UUID
    #: The protagonist — the phone in the tester's hand.
    marta: dict
    kuba: dict
    zofia: dict
    marek: dict
    #: A member the seed did not create: the console refuses to read for him.
    piotr: dict

    @property
    def four(self) -> tuple[dict, ...]:
        return (self.marta, self.kuba, self.zofia, self.marek)


@pytest.fixture
async def world(client, session_factory, payments, clock) -> World:
    club = await a_club_selling(client)
    marta, kuba, zofia, marek = [
        await a_member(client, session_factory, payments, name, domain=SEED)
        for name in ("marta", "kuba", "zofia", "marek")
    ]
    piotr = await a_member(client, session_factory, payments, "piotr")
    group = await a_group(client, marta, club, kuba, zofia, marek, piotr)
    return World(group, marta, kuba, zofia, marek, piotr)


async def her_yes_fills_it(client, world: World) -> UUID:
    """Situation 2, then her yes from her own phone: the game is booked."""

    pressed = await presses(
        client,
        "needs-her-yes-instant-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
    )
    assert pressed.status_code == 200, pressed.text
    game = UUID(pressed.json()["game_id"])
    yes = await says(client, PLAYER, "yes", world.marta, game)
    assert yes.status_code == 200, yes.text
    assert yes.json()["booked"] is not None, yes.text
    return game


async def sent_to(client, member: dict) -> dict:
    read = await client.get(f"/dev/as/{member['id']}/sent")
    assert read.status_code == 200, read.text
    return read.json()


def about(sent: dict, kind: str, game: UUID) -> list[dict]:
    return [
        notice
        for notice in sent["notices"]
        if notice["listed"]["kind"] == kind and notice["listed"]["game_id"] == str(game)
    ]


def emails_of(sent: dict, kind: str) -> list[dict]:
    return [email for email in sent["emails"] if email["kind"] == kind]


async def test_after_her_yes_fills_situation_2_everybody_s_sent_shows_it(
    client, mailbox, clock, world
):
    game = await her_yes_fills_it(client, world)
    await mailbox.drain()
    #: What the relay was handed, by the queue id it was sent under.
    handed = mailbox.mailer.sent_under
    inbox = get_settings().MAIL_CATCHER_URL

    for member in world.four:
        address = f"{member['name']}@{SEED}"
        sent = await sent_to(client, member)
        assert sent["email"] == address

        # The bell's own row — the list `GET /players/me/notices` answers.
        [booked] = about(sent, BOOKED, game)
        bell = await client.get("/api/v1/players/me/notices", headers=member["headers"])
        assert booked["listed"] in bell.json()["notices"]
        # Pushed in the same words: nothing was gathered into it.
        assert booked["pushed"]["title"] == booked["listed"]["title"]
        assert booked["pushed"]["body"] == booked["listed"]["body"]
        assert booked["pushed"]["data"]["game_id"] == str(game)
        # Nobody has a phone, so nothing was pushed: this is what would have been.
        assert sent["phones"] == 0

        # The booking confirmation, sent — to them and nobody else — and linked
        # to the message the relay was handed under that id.
        [email] = emails_of(sent, BOOKED_AND_PAID)
        assert email["subject"] == "It's a game! · you paid 30 zł"
        assert email["sent_at"] is not None
        assert email["given_up_at"] is None
        assert email["in_the_mail_catcher"] == (
            f"{inbox}/search?q=message-id%3A{email['mail_id']}"
        )
        assert handed[UUID(email["mail_id"])].to == address
        assert handed[UUID(email["mail_id"])].subject == email["subject"]
        assert {e["mail_id"] for e in sent["emails"]} <= {
            str(mail_id) for mail_id, message in handed.items() if message.to == address
        }


async def test_the_push_shown_is_the_one_their_phone_was_pushed(
    client, mailbox, pushes, clock, world
):
    phone = "ExponentPushToken[kuba-phone]"
    registered = await client.post(
        "/api/v1/players/me/devices",
        json={"token": phone},
        headers=world.kuba["headers"],
    )
    assert registered.status_code == 204, registered.text

    game = await her_yes_fills_it(client, world)
    await mailbox.drain()

    sent = await sent_to(client, world.kuba)
    assert sent["phones"] == 1
    [booked] = about(sent, BOOKED, game)
    [pushed] = [
        push
        for push in pushes.to(phone)
        if push.data["notice_id"] == booked["listed"]["notice_id"]
    ]
    assert booked["pushed"] == {
        "title": pushed.title,
        "body": pushed.body,
        "data": dict(pushed.data),
    }


async def test_an_email_still_queued_is_listed_with_no_link_until_it_is_sent(
    client, session_factory, payments, mailbox, clock, world
):
    game = await her_yes_fills_it(client, world)
    # The outbox has queued the emails; the mail worker has not run.
    await players.deliver_the_outbox(session_factory, payments=payments)

    [queued] = emails_of(await sent_to(client, world.kuba), BOOKED_AND_PAID)
    assert queued["sent_at"] is None
    assert queued["in_the_mail_catcher"] is None

    await mailbox.drain()

    [sent] = emails_of(await sent_to(client, world.kuba), BOOKED_AND_PAID)
    assert sent["mail_id"] == queued["mail_id"]
    assert sent["in_the_mail_catcher"] is not None
    assert about(await sent_to(client, world.kuba), BOOKED, game)


async def test_it_refuses_to_read_for_an_account_the_seed_did_not_create(client, world):
    read = await client.get(f"/dev/as/{world.piotr['id']}/sent")

    assert read.status_code == 403, read.text
    assert code_of(read) == "not_a_seed_account"
