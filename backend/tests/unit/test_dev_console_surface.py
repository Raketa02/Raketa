"""What the dev surface is, and the three claims it would be easy to break.

The gate is tested next door. This is about the surface's *shape*: that its
contract holds one path, that no `/dev` path has leaked into the document the
player client generates its wire types from, and that the two constants it
spells for itself still equal the ones it declined to import.

The last of those is the price of the decline, and it is paid deliberately.
`app/api/dev/__init__.py` argues why the console does not import `app/seeds/`;
the cost is that `SEED_PASSWORD` and the reserved TLD are written twice, and
these cases are what keep the second spelling from drifting — or from being
deleted by somebody who reads it as duplication.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.api.contract import SURFACES, build_surface_spec
from app.api.dev.routes import (
    SEED_ADDRESS_TLD,
    SEED_PASSWORD,
    is_seed_account,
)
from app.seeds.catalog import (
    ACCOUNTS,
    RESERVED_TLD,
    SEED_EMAIL_DOMAIN,
    SEED_PASSWORD as CATALOG_SEED_PASSWORD,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------


def test_the_dev_contract_holds_exactly_one_path():
    """The roster, and nothing else.

    The page itself is `include_in_schema=False` — a document describing how to
    fetch an HTML file is not something anything generates types from — and
    every other request the console sends is a **player-surface** request it
    makes as the player it signed in as. One path is therefore the honest
    description of this surface, and a second one appearing here means somebody
    has built a dev-only way to do something a player can already do.
    """

    spec = build_surface_spec("Raketa Dev API", SURFACES["dev"])

    assert list(spec["paths"]) == ["/dev/roster"]
    assert list(spec["paths"]["/dev/roster"]) == ["get"]


def test_the_committed_dev_document_is_the_one_the_surface_produces():
    """The shape half of the freshness gate.

    `.github/scripts/check-contract-freshness.sh` is what fails a pull request that
    changed the surface without regenerating; this is what fails a test run, so
    the two halves of `make check` and CI agree.
    """

    on_disk = json.loads((BACKEND_ROOT / "openapi.dev.json").read_text())

    assert on_disk == build_surface_spec("Raketa Dev API", SURFACES["dev"])


def test_the_player_contract_carries_no_dev_path():
    """The leak that actually matters.

    `openapi.player.json` is what `frontend_player` generates its wire types
    from, so a `/dev` path here is a development tool's shape shipping in an
    app-store release. `.importlinter` forbids the import that would put one
    there; this asserts the document itself.
    """

    player = json.loads((BACKEND_ROOT / "openapi.player.json").read_text())

    assert not [path for path in player["paths"] if path.startswith("/dev")]


def test_every_surface_writes_a_document_of_its_own():
    """A surface with no committed contract is one nothing can go stale."""

    for surface in SURFACES:
        assert (BACKEND_ROOT / f"openapi.{surface}.json").is_file()


# ---------------------------------------------------------------------------
# The two constants the decline costs
# ---------------------------------------------------------------------------


def test_the_console_s_password_is_the_seed_system_s_password():
    assert SEED_PASSWORD == CATALOG_SEED_PASSWORD


def test_the_console_s_reserved_tld_is_the_seed_system_s():
    assert SEED_ADDRESS_TLD == RESERVED_TLD
    assert SEED_EMAIL_DOMAIN.endswith(SEED_ADDRESS_TLD)


# ---------------------------------------------------------------------------
# The data predicate — a filter, and a total one
# ---------------------------------------------------------------------------


def test_every_named_seed_account_is_a_seed_account():
    """Read off the catalog rather than off a literal: the day a scenario is
    addressed somewhere else, the roster stops showing it and this says so."""

    for account in ACCOUNTS:
        assert is_seed_account(account.email)


@pytest.mark.parametrize(
    "address",
    [
        "someone@gmail.com",
        # The trap: `example.com` is a real registrable domain and the address
        # `tests/conftest.py` signs its own fixtures up with. It is not on the
        # reserved TLD, and reading the predicate as "contains example" would
        # put every test account on the roster.
        "alice@example.com",
        "not.example@gmail.com",
        # `.test` is reserved by the same RFC sentence and is deliberately not
        # this predicate's answer: `EmailStr` refuses it, so no account can hold
        # one (`app/seeds/catalog.py`'s `RESERVED_TLD`).
        "alice@raketa.test",
        # Total rather than raising: a string with no `@` is not a seed
        # account. `nonsense.example` is the one that has to be written down —
        # `rpartition` hands back the whole string when there is no separator,
        # so a predicate that only looked at the suffix would call it one.
        "nonsense.example",
        "nonsense",
        "@raketa.example",
        "",
    ],
)
def test_a_non_seed_address_is_not_one(address):
    assert not is_seed_account(address)


def test_the_predicate_ignores_case():
    """Addresses are stored as the boundary normalised them; the roster's SQL
    filter is an `ILIKE`, so the Python predicate has to agree with it."""

    assert is_seed_account(f"Alice@RAKETA{RESERVED_TLD.upper()}")
