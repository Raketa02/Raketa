"""Money's stream as a **durable** contract, and its place in the graph.

Three claims.

1. **Both events are registered under a durable name at version 1**, and every
   field survives the real codec. A ledger *is* its stream — unlike Matches,
   which keeps a record and uses its events as a trail — so a payload that does
   not decode is not a lost audit line, it is a balance nobody can compute.
2. **The set of names is exactly two.** An event class that exists and is never
   registered decodes as nothing; a name registered for a class nobody emits is
   a contract with no writer.
3. **The dependency is one-way.** ADR-0055: *Money reads Matches; Matches never
   reads Money.* ``.importlinter`` holds the second half at module granularity;
   what is here is the first half's shape — Money's **domain and application**
   layers reach into no other context at all, so the only place the two can be
   joined is the composition root.
"""

from __future__ import annotations

import ast
from pathlib import Path
from uuid import uuid4

import pytest

from app.application.events.catalog import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.modules.money.application.event_subscriptions import register_money_events
from app.modules.money.domain.events import MovementRecorded, PlayerPseudonymised
from tests.unit.fake_event_store import money_event_codec, utc

ROOT = Path(__file__).resolve().parents[2]
MONEY = ROOT / "app" / "modules" / "money"
NOW = utc(2026, 8, 24)

RECORDED = MovementRecorded(
    ledger_id=uuid4(),
    player_id=uuid4(),
    movement_id=uuid4(),
    payer_kind="player",
    payer_id=uuid4(),
    payee_kind="raketa",
    payee_id=None,
    amount=3800,
    seat_match_id=uuid4(),
    seat_index=2,
    reservation_id=uuid4(),
    reference="PAY-a1",
    cause="shareOnline",
    occurred_at=NOW,
)

PSEUDONYMISED = PlayerPseudonymised(
    ledger_id=uuid4(),
    player_id=uuid4(),
    pseudonym=uuid4(),
    occurred_at=NOW,
)


def _round_trip(event):
    codec = money_event_codec()
    encoded = codec.encode(event)
    return codec.decode(
        SerializedEventEnvelope(
            id=uuid4(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )


# ---------------------------------------------------------------------------
# 1 & 2. The durable contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event", [RECORDED, PSEUDONYMISED], ids=lambda e: type(e).__name__
)
def test_every_field_survives_the_codec(event):
    assert _round_trip(event) == event


def test_a_movement_with_no_seat_and_no_reservation_survives():
    """``debtCleared``, which is the one cause that names neither."""

    from dataclasses import replace

    cleared = replace(
        RECORDED,
        cause="debtCleared",
        seat_match_id=None,
        seat_index=None,
        reservation_id=None,
    )
    assert _round_trip(cleared) == cleared


def test_the_platform_party_survives_as_a_party_with_no_id():
    from dataclasses import replace

    settlement = replace(
        RECORDED,
        payer_kind="raketa",
        payer_id=None,
        payee_kind="club",
        payee_id=uuid4(),
    )
    decoded = _round_trip(settlement)
    assert decoded.payer_id is None
    assert decoded == settlement


def test_the_two_events_are_filed_under_their_own_names_at_version_one():
    catalog = EventCatalog()
    register_money_events(catalog)

    for event_cls, name in (
        (MovementRecorded, "money.movement_recorded"),
        (PlayerPseudonymised, "money.player_pseudonymised"),
    ):
        contract = catalog.contract_for(event_cls)
        assert (contract.name, contract.version) == (name, 1)
        assert catalog.class_for(name, 1) is event_cls


def test_the_context_announces_exactly_two_things():
    """Two facts happen to a ledger. A third would be a decision in a diff."""

    catalog = EventCatalog()
    register_money_events(catalog)
    registered = {
        contract.event_cls
        for contract in catalog._by_class.values()  # noqa: SLF001 — the whole set
    }
    assert registered == {MovementRecorded, PlayerPseudonymised}


# ---------------------------------------------------------------------------
# 3. The dependency is one-way
# ---------------------------------------------------------------------------


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
    return found


INWARD = sorted((MONEY / "domain").glob("*.py")) + sorted(
    (MONEY / "application").rglob("*.py")
)


def test_the_walk_has_something_to_walk():
    """A glob matching nothing passes silently and reads like a rule that held.

    The names rather than the count, so a file added tomorrow says which one it
    is instead of moving a number by one.
    """

    assert {f"{path.parent.name}/{path.name}" for path in INWARD} == {
        "domain/__init__.py",
        "domain/causes.py",
        "domain/errors.py",
        "domain/events.py",
        "domain/ids.py",
        "domain/invariants.py",
        "domain/ledger.py",
        "domain/movement.py",
        "domain/parties.py",
        "domain/ports.py",
        "domain/reference.py",
        "application/__init__.py",
        "application/commands.py",
        "application/event_subscriptions.py",
        "application/pseudonymise_player.py",
        "application/reconcile_ledgers.py",
        "application/record_movements.py",
        "application/record_share.py",
        "handlers/__init__.py",
        "handlers/log_money_events.py",
    }


@pytest.mark.parametrize("path", INWARD, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_money_reaches_into_no_other_context(path):
    """The ledger is downstream, and today it is downstream of nothing.

    ADR-0055 permits Money to *read* Matches. If it ever needs to, the read is a
    port of Money's own with the adapter in ``infrastructure/`` — the shape Now
    used for ``RatedSports`` — so this stays true of the layers where the rules
    are and the fence in ``.importlinter`` keeps the arrow pointing one way.
    """

    reached = {
        module
        for module in imported_modules(path)
        if module.startswith("app.modules.")
        and not module.startswith("app.modules.money")
    }
    assert not reached, f"{path.name} reaches {sorted(reached)}"


def test_money_stores_no_table():
    """No ORM model and no migration: a ledger *is* its stream.

    Stated as an absence because the failure is additive — somebody reaching for
    a projection before anything has measured that the scan is slow, which is
    ADR-0018's escape hatch used as a default.
    """

    assert not list(MONEY.rglob("*_model*.py"))
    assert not list(MONEY.rglob("*models.py"))
    for path in MONEY.rglob("*.py"):
        assert "sqlalchemy" not in imported_modules(path), path.name
