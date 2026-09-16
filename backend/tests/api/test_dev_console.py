"""The dev console over HTTP: the roster, the page, and the sign-in it enables.

The console's whole claim is that it acts as another player *by being them*, so
that is what is asserted here — end to end, over the same client every other API
test uses, with nothing about the dev surface involved after the roster is read.
The roster hands over an address and a password; everything after that is
`POST /api/v1/auth/login` and the player surface.

The seed run is the fixture rather than a handful of registrations, because the
interesting claim is about the accounts a developer actually meets. The
non-seed account beside them is registered through the ordinary signup route,
which is the only way a real address gets into this database — and the roster
not showing it is the data gate, which is a **consequence** and not a refusal:
production has no addresses on the reserved TLD, so the roster is empty there by
construction.
"""

from __future__ import annotations

import pytest

from app.api.dev.routes import SEED_PASSWORD, is_seed_account
from app.seeds.runner import seed


@pytest.fixture
async def seeded(session_factory):
    """Every named and relationship account, as `make seed` writes them."""

    async with session_factory() as session:
        return await seed(session)


@pytest.fixture
async def a_real_account(client, valid_signup_payload):
    """One account on a registrable domain, created the way a person creates one."""

    response = await client.post("/api/v1/users", json=valid_signup_payload)
    assert response.status_code == 201, response.text
    return response.json()


async def _roster(client) -> dict:
    response = await client.get("/dev/roster")
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# The roster
# ---------------------------------------------------------------------------


async def test_the_roster_lists_every_seeded_account(client, seeded):
    roster = await _roster(client)

    listed = {account["email"] for account in roster["accounts"]}
    assert listed == {entry.account.email for entry in seeded}


async def test_the_roster_shows_no_account_that_is_not_a_seed_one(
    client, seeded, a_real_account
):
    """The filter, asserted against a database holding both kinds.

    Without the non-seed account present this case would pass against a roster
    that had no filter at all, which is the shape of failure it exists for.
    """

    roster = await _roster(client)

    listed = {account["email"] for account in roster["accounts"]}
    assert a_real_account["email"] not in listed
    assert all(is_seed_account(email) for email in listed)


async def test_a_database_with_no_seed_accounts_has_an_empty_roster(
    client, a_real_account
):
    """The data gate as it holds in production: not a refusal, an empty list."""

    roster = await _roster(client)

    assert roster["accounts"] == []
    # Still the password. A console that could not tell "no seed accounts here"
    # from "the roster is broken" is one nobody trusts.
    assert roster["password"] == SEED_PASSWORD


async def test_the_password_is_carried_once_at_the_top_level(client, seeded):
    """One password for every seeded account is `app/seeds/catalog.py`'s own
    decision — *"so a developer signing in as any of them types the same
    thing"* — and a per-row copy would state the opposite."""

    roster = await _roster(client)

    assert roster["password"] == SEED_PASSWORD
    for account in roster["accounts"]:
        assert set(account) == {"player_id", "email", "name", "nickname"}


async def test_the_roster_is_ordered_by_address(client, seeded):
    """Unpaginated and ordered, because the console filters client-side and a
    list whose order moved between reads is one you cannot scan."""

    roster = await _roster(client)

    emails = [account["email"] for account in roster["accounts"]]
    assert emails == sorted(emails)


#: Addresses on both sides of the line, registered through the ordinary signup
#: route. `raketa.test` is deliberately absent: `EmailStr` refuses the other TLD
#: RFC 2606 reserves, which is why the seed system is on `.example` at all.
BOTH_SIDES = (
    ("on-the-seed-tld@raketa.example", "console-a"),
    ("deeper@sub.raketa.example", "console-b"),
    # The trap. `example.com` is a real, registrable domain and is what this
    # suite's own fixtures sign up with; reading the predicate as "contains
    # example" would put every test account on the roster.
    ("looks-close@example.com", "console-c"),
    ("not.example@gmail.com", "console-d"),
)


async def test_the_two_spellings_of_the_predicate_agree(client):
    """`is_seed_account` and the SQL it is written as, over one database.

    The roster cannot load a real database's users into the process to filter
    them, so the predicate exists twice. This is what keeps the two from drifting
    — asserted over addresses that are registered the way any address gets here,
    rather than over rows inserted behind the write path.
    """

    for email, _ in BOTH_SIDES:
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password1": "hunter22!",
                "password2": "hunter22!",
                "adult_attested": True,
            },
        )
        assert response.status_code == 201, response.text

    roster = await _roster(client)

    listed = {account["email"] for account in roster["accounts"]}
    assert listed == {email for email, _ in BOTH_SIDES if is_seed_account(email)}


# ---------------------------------------------------------------------------
# What the roster is for
# ---------------------------------------------------------------------------


async def test_the_roster_signs_in_through_the_ordinary_login_route(client, seeded):
    """The acceptance criterion in one case: what the console does with a row.

    No impersonation endpoint, no `Act-As` header, no dev-only authorisation
    path — an address and a password against `POST /api/v1/auth/login`, which is
    the same request the player app makes.
    """

    roster = await _roster(client)
    row = roster["accounts"][0]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": row["email"], "password": roster["password"]},
    )
    assert login.status_code == 200, login.text

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200, me.text
    assert me.json()["email"] == row["email"]
    # The id every player-surface read and write names this account by. The
    # console renders it, and it is what makes a candidate row in one player's
    # search recognisable as another roster row.
    assert me.json()["id"] == row["player_id"]


async def test_there_is_no_impersonation_endpoint(client, seeded):
    """The shape Decision 19 refused by name, asserted as an absence at the one
    address somebody would reach for."""

    response = await client.post("/dev/sessions", json={"handle": "anybody"})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


async def test_the_console_is_served_at_dev(client):
    response = await client.get("/dev")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/html")
    assert "Raketa — dev console" in response.text
