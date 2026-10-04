"""*Forgot password?* on the player surface, read the way Tomek reads it.

Tomek forgets his password. He asks from the app, and an email arrives with a
button and an 8-character code, valid for one hour (``docs/adr/0184`` §3, §5).
He uses either one to set a new password, and every other phone he is signed in
on is signed out (``docs/adr/0185`` §7).

**Every assertion is about what a person sees**: the answer to a request, and
the email in the recording mailer once the queues have drained — its link and
its code are read off the text, the way somebody reading it would. Nothing here
asks which table was written.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM

SIGN_UP = "/api/v1/users"
SIGN_IN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/users/me"
FORGOT = "/api/v1/auth/forgot-password"
CLAIM = "/api/v1/auth/forgot-password/claim"
NEW_PASSWORD = "/api/v1/auth/forgot-password/new-password"

TOMEK = "tomek@example.com"
OLD_PASSWORD = "padel-tomek-1"
NEW = "padel-tomek-2"

#: The alphabet a code is written in, spelled here rather than imported: the
#: test's claim is that a person can read the code, and a look-alike would be a
#: character outside this set.
CODE = re.compile(r"^([ABCDEFGHJKMNPQRSTUVWXYZ23456789]{8})$", re.MULTILINE)


def link_in(email) -> str:
    """The button's address, as it is written in the plain-text part."""

    found = re.search(r"(https?://\S+/reset/\S+)", email.text)
    assert found, email.text
    return found.group(1)


def token_in(email) -> str:
    return link_in(email).rsplit("/reset/", 1)[1]


def code_in(email) -> str:
    found = CODE.search(email.text)
    assert found, email.text
    return found.group(1)


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def sign_up(client, email: str = TOMEK, password: str = OLD_PASSWORD) -> None:
    resp = await client.post(
        SIGN_UP,
        json={
            "email": email,
            "password1": password,
            "password2": password,
            "adult_attested": True,
        },
    )
    assert resp.status_code == 201, resp.text


async def sign_in(client, email: str = TOMEK, password: str = OLD_PASSWORD):
    return await client.post(SIGN_IN, json={"email": email, "password": password})


@pytest.fixture
async def tomek(client) -> None:
    await sign_up(client)


async def the_reset_email(client, mailbox, email: str = TOMEK):
    asked = await client.post(FORGOT, json={"email": email})
    assert asked.status_code == 202, asked.text
    return (await mailbox.to(email))[-1]


# ---------------------------------------------------------------------------
# Asking
# ---------------------------------------------------------------------------


async def test_asking_emails_a_button_to_the_public_site_and_a_code(
    client, tomek, mailbox
):
    asked = await client.post(FORGOT, json={"email": TOMEK})

    assert asked.status_code == 202, asked.text
    (email,) = await mailbox.to(TOMEK)
    public_site = get_settings().PUBLIC_SITE_URL.rstrip("/")
    assert link_in(email).startswith(f"{public_site}/reset/")
    assert len(code_in(email)) == 8
    # The button is the HTML part's, and it goes where the text's link goes.
    assert f'href="{link_in(email)}"' in email.html
    assert code_in(email) in email.html


async def test_an_address_with_no_account_gets_the_identical_answer_and_no_email(
    client, tomek, mailbox
):
    known = await client.post(FORGOT, json={"email": TOMEK})
    unknown = await client.post(FORGOT, json={"email": "nobody@example.com"})

    assert unknown.status_code == known.status_code == 202
    assert unknown.content == known.content == b""
    assert unknown.headers.get("content-type") == known.headers.get("content-type")
    assert await mailbox.to("nobody@example.com") == []
    assert len(await mailbox.to(TOMEK)) == 1


async def test_the_address_is_read_as_sign_up_wrote_it(client, tomek, mailbox):
    """Case and surrounding spaces are how a person types, not a second address."""

    asked = await client.post(FORGOT, json={"email": "  Tomek@Example.COM "})

    assert asked.status_code == 202
    assert len(await mailbox.to(TOMEK)) == 1


# ---------------------------------------------------------------------------
# Setting a new password
# ---------------------------------------------------------------------------


async def test_the_code_is_claimed_for_a_ticket_that_sets_the_password_and_signs_in(
    client, tomek, mailbox
):
    email = await the_reset_email(client, mailbox)

    claimed = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["expires_in"] > 0

    set_ = await client.post(
        NEW_PASSWORD, json={"ticket": claimed.json()["ticket"], "password": NEW}
    )

    assert set_.status_code == 200, set_.text
    # Signed in: the answer is a session, and it works.
    me = await client.get(ME, headers=bearer(set_.json()))
    assert me.status_code == 200, me.text
    assert me.json()["email"] == TOMEK
    assert (await sign_in(client, password=NEW)).status_code == 200
    assert (await sign_in(client, password=OLD_PASSWORD)).status_code == 401


async def test_the_link_sets_the_password_on_its_own(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)

    set_ = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )

    assert set_.status_code == 200, set_.text
    assert (await client.get(ME, headers=bearer(set_.json()))).status_code == 200
    assert (await sign_in(client, password=NEW)).status_code == 200


async def test_a_typed_code_is_forgiven_its_case_and_its_spaces(client, tomek, mailbox):
    code = code_in(await the_reset_email(client, mailbox))
    typed = f" {code[:4].lower()} {code[4:]} "

    claimed = await client.post(CLAIM, json={"email": TOMEK, "code": typed})

    assert claimed.status_code == 200, claimed.text


async def test_the_new_password_follows_the_rule_and_a_refusal_spends_nothing(
    client, tomek, mailbox
):
    email = await the_reset_email(client, mailbox)

    weak = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": "onlyletters"}
    )

    assert weak.status_code == 400
    assert weak.json()["code"] == "password_too_weak"
    assert weak.json()["details"] == {"field": "password"}
    again = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )
    assert again.status_code == 200, again.text


async def test_the_link_and_the_ticket_are_one_or_the_other(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)

    both = await client.post(
        NEW_PASSWORD,
        json={"token": token_in(email), "ticket": "anything", "password": NEW},
    )
    neither = await client.post(NEW_PASSWORD, json={"password": NEW})

    assert both.status_code == neither.status_code == 422


async def test_a_link_nobody_sent_is_not_found(client, tomek):
    resp = await client.post(
        NEW_PASSWORD, json={"token": "made-up-token", "password": NEW}
    )

    assert resp.status_code == 404
    assert resp.json()["code"] == "credential_not_found"


# ---------------------------------------------------------------------------
# One hour, once, five tries
# ---------------------------------------------------------------------------


async def test_the_link_and_the_code_work_for_an_hour(client, tomek, mailbox, clock):
    email = await the_reset_email(client, mailbox)

    clock.move(timedelta(minutes=59))

    claimed = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    assert claimed.status_code == 200, claimed.text
    set_ = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )
    assert set_.status_code == 200, set_.text
    # The session this opened survives the instant it opened under, even an
    # hour into a clock the test moved.
    assert (await client.get(ME, headers=bearer(set_.json()))).status_code == 200


async def test_after_an_hour_the_link_and_the_code_have_expired(
    client, tomek, mailbox, clock
):
    email = await the_reset_email(client, mailbox)

    clock.move(timedelta(hours=1))

    claimed = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    by_link = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )
    assert claimed.status_code == by_link.status_code == 409
    assert claimed.json()["code"] == by_link.json()["code"] == "credential_expired"
    assert (await sign_in(client)).status_code == 200


async def test_a_ticket_lasts_minutes_and_the_code_can_be_claimed_again(
    client, tomek, mailbox, clock
):
    code = code_in(await the_reset_email(client, mailbox))
    first = await client.post(CLAIM, json={"email": TOMEK, "code": code})
    assert first.status_code == 200

    clock.move(timedelta(seconds=first.json()["expires_in"]))

    late = await client.post(
        NEW_PASSWORD, json={"ticket": first.json()["ticket"], "password": NEW}
    )
    assert late.status_code == 409
    assert late.json()["code"] == "ticket_expired"
    again = await client.post(CLAIM, json={"email": TOMEK, "code": code})
    assert again.status_code == 200
    set_ = await client.post(
        NEW_PASSWORD, json={"ticket": again.json()["ticket"], "password": NEW}
    )
    assert set_.status_code == 200, set_.text


async def test_setting_the_password_spends_the_link_the_code_and_the_ticket(
    client, tomek, mailbox
):
    email = await the_reset_email(client, mailbox)
    ticket = (
        await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    ).json()["ticket"]
    assert (
        await client.post(NEW_PASSWORD, json={"ticket": ticket, "password": NEW})
    ).status_code == 200

    by_link = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": "another-one-3"}
    )
    by_code = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    by_ticket = await client.post(
        NEW_PASSWORD, json={"ticket": ticket, "password": "another-one-3"}
    )

    for used in (by_link, by_code, by_ticket):
        assert used.status_code == 409, used.text
        assert used.json()["code"] == "credential_used"
    assert (await sign_in(client, password=NEW)).status_code == 200


async def test_a_wrong_code_is_refused_and_so_is_an_address_nothing_was_sent_to(
    client, tomek, mailbox
):
    code = code_in(await the_reset_email(client, mailbox))
    wrong = "".join(reversed(code)) if code != code[::-1] else "AAAAAAAA"

    wrong_code = await client.post(CLAIM, json={"email": TOMEK, "code": wrong})
    no_account = await client.post(
        CLAIM, json={"email": "nobody@example.com", "code": code}
    )

    assert wrong_code.status_code == no_account.status_code == 400
    assert wrong_code.json()["code"] == no_account.json()["code"] == "code_incorrect"
    assert wrong_code.json()["details"] == {"field": "code"}


async def test_five_wrong_codes_lock_the_link_and_the_code(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)
    wrong = "22222222" if code_in(email) != "22222222" else "33333333"

    for _ in range(5):
        refused = await client.post(CLAIM, json={"email": TOMEK, "code": wrong})
        assert refused.json()["code"] == "code_incorrect"

    right = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    by_link = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )
    assert right.status_code == by_link.status_code == 409
    assert right.json()["code"] == by_link.json()["code"] == "credential_locked"
    # And a sixth wrong one still says only *wrong*: the lock is told to the
    # person holding the code, never to a guesser.
    sixth = await client.post(CLAIM, json={"email": TOMEK, "code": wrong})
    assert sixth.json()["code"] == "code_incorrect"


async def test_four_wrong_codes_do_not(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)
    wrong = "22222222" if code_in(email) != "22222222" else "33333333"

    for _ in range(4):
        await client.post(CLAIM, json={"email": TOMEK, "code": wrong})

    right = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})
    assert right.status_code == 200, right.text


# ---------------------------------------------------------------------------
# Asking again
# ---------------------------------------------------------------------------


async def test_a_newer_email_replaces_the_older_ones_link_and_code(
    client, tomek, mailbox
):
    first = await the_reset_email(client, mailbox)
    second = await the_reset_email(client, mailbox)

    old = await client.post(
        NEW_PASSWORD, json={"token": token_in(first), "password": NEW}
    )
    assert old.status_code == 409
    assert old.json()["code"] == "credential_expired"
    new = await client.post(
        NEW_PASSWORD, json={"token": token_in(second), "password": NEW}
    )
    assert new.status_code == 200, new.text


async def test_asking_is_throttled_per_address_and_the_answer_does_not_change(
    client, tomek, mailbox, clock
):
    answers = [await client.post(FORGOT, json={"email": TOMEK}) for _ in range(4)]

    assert {(a.status_code, a.content) for a in answers} == {(202, b"")}
    assert len(await mailbox.to(TOMEK)) == 3

    clock.move(timedelta(hours=1))
    await client.post(FORGOT, json={"email": TOMEK})
    assert len(await mailbox.to(TOMEK)) == 4


# ---------------------------------------------------------------------------
# Signing out everywhere
# ---------------------------------------------------------------------------


async def test_setting_a_new_password_signs_every_other_phone_out(
    client, tomek, mailbox, clock
):
    other_phone = (await sign_in(client)).json()
    assert (await client.get(ME, headers=bearer(other_phone))).status_code == 200
    email = await the_reset_email(client, mailbox)
    clock.move(timedelta(minutes=2))

    this_phone = (
        await client.post(
            NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
        )
    ).json()

    refused = await client.get(ME, headers=bearer(other_phone))
    assert refused.status_code == 401
    assert refused.json()["code"] == "access_token_revoked"
    renewed = await client.post(
        REFRESH, json={"refresh_token": other_phone["refresh_token"]}
    )
    assert renewed.status_code == 401
    assert renewed.json()["code"] == "refresh_token_revoked"
    # And the other side of the edge: the session the reset opened is not
    # signed out by the instant it was opened under, and renews like any other.
    assert (await client.get(ME, headers=bearer(this_phone))).status_code == 200
    rotated = await client.post(
        REFRESH, json={"refresh_token": this_phone["refresh_token"]}
    )
    assert rotated.status_code == 200, rotated.text
    assert (await client.get(ME, headers=bearer(rotated.json()))).status_code == 200


async def test_a_phone_signed_in_a_moment_before_the_reset_is_signed_out_too(
    client, tomek, mailbox, clock
):
    """A token's issue time is not rounded to the second: a phone signed in a
    millisecond before the reset is a phone signed in before it."""

    email = await the_reset_email(client, mailbox)
    other_phone = (await sign_in(client)).json()
    clock.move(timedelta(milliseconds=1))

    this_phone = (
        await client.post(
            NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
        )
    ).json()

    assert (await client.get(ME, headers=bearer(other_phone))).status_code == 401
    assert (await client.get(ME, headers=bearer(this_phone))).status_code == 200


async def test_a_session_signed_in_after_the_reset_is_untouched(
    client, tomek, mailbox, clock
):
    email = await the_reset_email(client, mailbox)
    await client.post(NEW_PASSWORD, json={"token": token_in(email), "password": NEW})
    clock.move(timedelta(minutes=5))

    later = (await sign_in(client, password=NEW)).json()

    assert (await client.get(ME, headers=bearer(later))).status_code == 200


# ---------------------------------------------------------------------------
# No secret outlives its email
# ---------------------------------------------------------------------------


async def everything_recorded(session_factory) -> str:
    """Every event stored and every event queued for delivery, as one text."""

    async with session_factory() as session:
        stored = (await session.execute(select(EventStoreORM))).scalars().all()
        queued = (await session.execute(select(EventOutboxORM))).scalars().all()
    return "\n".join(repr(row.payload) for row in [*stored, *queued])


async def test_no_link_code_or_ticket_ever_enters_an_event(
    client, tomek, mailbox, session_factory
):
    """``docs/adr/0184`` §4: events record *that*, never *what opens it* — read
    at every step, including the one where the email is still waiting."""

    asked = await client.post(FORGOT, json={"email": TOMEK})
    assert asked.status_code == 202
    waiting = await everything_recorded(session_factory)
    email = (await mailbox.to(TOMEK))[-1]
    token, code = token_in(email), code_in(email)
    ticket = (await client.post(CLAIM, json={"email": TOMEK, "code": code})).json()[
        "ticket"
    ]
    set_ = await client.post(NEW_PASSWORD, json={"ticket": ticket, "password": NEW})
    assert set_.status_code == 200
    await mailbox.drain()
    afterwards = await everything_recorded(session_factory)

    # The flow did record events — the password change and the sessions — so
    # the absence below is about their contents and not about there being none.
    assert "password_changed" in afterwards or "password_hash" in afterwards
    for secret in (token, code, ticket):
        assert secret not in waiting
        assert secret not in afterwards
