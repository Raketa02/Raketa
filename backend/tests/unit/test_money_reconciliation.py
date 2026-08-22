"""The nightly reconciliation: what it asserts, what it reports, and what it cannot do.

**The point of this file is that it calls the same functions the job calls.** The
ticket asks for it in those words, and the reason is that two copies of an
invariant are two things that can disagree about whether the ledger is sound —
and the one that would be wrong is the one nobody runs nightly. So every
assertion here goes through ``domain/invariants.py``, and the job is driven whole
rather than reimplemented.

**Each invariant gets a ledger that breaks only it**, because a fixture that
breaks two passes as soon as either one still fires.
"""

from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path
from uuid import uuid4

import pytest

from app.bootstrap.composition import build_ledger_repository
from app.kernel import InvariantViolated, grosze, instant
from app.modules.money.application.reconcile_ledgers import ReconcileLedgers
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.invariants import (
    LEDGER_INVARIANTS,
    breaches_in,
    every_seat_chain_closes,
    no_balance_above_zero,
    no_club_is_a_payer,
)
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.movement import Movement, SeatRef
from app.modules.money.domain.parties import ClubParty, PlayerParty, RaketaParty
from app.modules.money.domain.reference import Reference, ReferenceKind
from tests.unit.fake_event_store import (
    FrozenClock,
    InMemoryEventStore,
    RecordingPublisher,
    money_event_codec,
    utc,
)

AT = instant(utc(2026, 8, 24))
SHARE = grosze(3800)
ROOT = Path(__file__).resolve().parents[2]


def pay(token: str) -> Reference:
    return Reference(ReferenceKind.PAYMENT, token)


def a_movement(**overrides: object) -> Movement:
    fields: dict[str, object] = {
        "id": uuid4(),
        "payer": RaketaParty(),
        "payee": RaketaParty(),
        "amount": SHARE,
        "seat": SeatRef(match_id=uuid4(), index=0),
        "reservation": None,
        "reference": pay("a1"),
        "cause": MovementCause.SHARE_ONLINE,
        "occurred_at": AT,
    }
    fields.update(overrides)
    return Movement(**fields)  # type: ignore[arg-type]


def as_written_before_the_rule(**fields: object) -> Movement:
    """A movement built past its own constructor, on purpose.

    ``Movement`` refuses a club payer at construction and ``Ledger.record``
    refuses it again, so a ledger breaking the first invariant cannot be built
    through the front door. This is how a row written before a rule is simulated.

    **What it simulates is the fold, not the read.** The same constructor guards
    the write *and* the replay, so a club-payer row that is genuinely on disk does
    not reach ``no_club_is_a_payer`` at all — it raises inside ``_rebuild`` and
    takes the whole run with it. That is pinned two tests below and filed as
    ``Raketa02/Raketa#101``; what this helper proves is that the invariant is
    correct once the movement is in front of it.
    """

    movement = object.__new__(Movement)
    for name, value in fields.items():
        object.__setattr__(movement, name, value)
    return movement


def a_ledger_holding(player, *movements: Movement) -> Ledger:
    """A ledger replayed from movements nothing would accept today."""

    ledger = Ledger.for_player(player)
    ledger._recorded.extend(movements)
    return ledger


@pytest.fixture
def player():
    return uuid4()


# ---------------------------------------------------------------------------
# A sound ledger
# ---------------------------------------------------------------------------


def test_an_ordinary_ledger_breaks_nothing(player):
    seat = SeatRef(match_id=uuid4(), index=1)
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            seat=seat,
            reference=pay("a1"),
        )
    )
    ledger.record(
        a_movement(
            payer=RaketaParty(),
            payee=ClubParty(uuid4()),
            seat=seat,
            reference=pay("a2"),
        )
    )
    assert breaches_in(ledger) == ()


def test_the_three_invariants_are_the_three(player):
    assert [invariant.__name__ for invariant in LEDGER_INVARIANTS] == [
        "no_club_is_a_payer",
        "no_balance_above_zero",
        "every_seat_chain_closes",
    ]


# ---------------------------------------------------------------------------
# One ledger per invariant
# ---------------------------------------------------------------------------


def test_a_club_as_payer_is_reported(player):
    club = uuid4()
    ledger = a_ledger_holding(
        player,
        as_written_before_the_rule(
            id=uuid4(),
            payer=ClubParty(club),
            payee=PlayerParty(player),
            amount=SHARE,
            seat=SeatRef(match_id=uuid4(), index=0),
            reservation=None,
            reference=pay("a1"),
            cause=MovementCause.SHARE_ONLINE,
            occurred_at=AT,
        ),
    )

    breaches = no_club_is_a_payer(ledger)
    assert [breach.invariant for breach in breaches] == ["no_club_is_a_payer"]
    assert str(club) in breaches[0].detail
    assert no_balance_above_zero(ledger) == ()


async def test_a_club_payer_on_disk_stops_the_replay_rather_than_being_reported():
    """The gap between the invariant above and what a nightly run can reach.

    ``no_club_is_a_payer`` exists because *"the door only guards what is written
    after the door existed, and this reads what is on disk"* — but the door is
    ``Movement.__post_init__``, and replay goes through it too. So the one row the
    invariant was written for raises on the way back in, and the run dies with a
    stack trace instead of reporting a breach and carrying on to the next ledger.

    Reproduced against a real PostgreSQL as well as here: a hand-inserted
    club-payer row made ``python -m app.reconciliation`` exit 1 from
    ``InvariantViolated`` inside ``_rebuild``, with no report and no float.

    **Pinned rather than fixed**, because closing it means deciding what a ledger
    holding an unreadable movement *is* — a port signature and a new domain
    concept, which is a decision and not a tidy-up (``Raketa02/Raketa#101``). This
    test is what tells whoever takes it that the behaviour changed.
    """

    store = InMemoryEventStore(codec=money_event_codec())
    repository = build_ledger_repository(event_store=store, events=RecordingPublisher())
    player = uuid4()
    ledger = await repository.load(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player), payee=RaketaParty(), reference=pay("ok1")
        )
    )
    await repository.save(ledger)

    # The same rewrite the Postgres run made, at the one layer a fake can reach.
    for stream in store._streams.values():  # noqa: SLF001 — the fake's own shape
        for stored in stream:
            payload = stored.payload
            if payload.get("payer_kind") == "player":
                payload["payer_kind"] = "club"

    with pytest.raises(InvariantViolated, match="club as payer"):
        await ReconcileLedgers(repository, FrozenClock()).execute()


def test_a_balance_above_zero_is_reported(player):
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            cause=MovementCause.DEBT_CLEARED,
            seat=None,
            amount=grosze(1000),
        )
    )

    breaches = no_balance_above_zero(ledger)
    assert [breach.invariant for breach in breaches] == ["no_balance_above_zero"]
    assert "stored value" in breaches[0].detail
    assert every_seat_chain_closes(ledger) == ()


def test_a_seat_that_settled_more_than_it_funded_is_reported(player):
    """A split computed against the wrong format, or a settlement written twice."""

    seat = SeatRef(match_id=uuid4(), index=1)
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            seat=seat,
            reference=pay("a1"),
        )
    )
    ledger.record(
        a_movement(
            payer=RaketaParty(),
            payee=ClubParty(uuid4()),
            seat=seat,
            reference=pay("a2"),
            amount=grosze(9600),
        )
    )

    breaches = every_seat_chain_closes(ledger)
    assert [breach.invariant for breach in breaches] == ["every_seat_chain_closes"]
    assert no_club_is_a_payer(ledger) == ()
    assert no_balance_above_zero(ledger) == ()


def test_settling_a_share_twice_is_reported(player):
    seat = SeatRef(match_id=uuid4(), index=1)
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            seat=seat,
            reference=pay("a1"),
        )
    )
    for token in ("a2", "a3"):
        ledger.record(
            a_movement(
                payer=RaketaParty(),
                payee=ClubParty(uuid4()),
                seat=seat,
                reference=pay(token),
            )
        )

    assert len(every_seat_chain_closes(ledger)) == 1


def test_a_refund_raketa_advanced_is_not_a_breach(player):
    """The position ADR-0045 names is legal, and the invariant says so.

    An assertion that fired here would page every night on every private court
    with a withdrawal on it, which is how a nightly check stops being read.
    """

    seat = SeatRef(match_id=uuid4(), index=1)
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            seat=seat,
            reference=pay("a1"),
        )
    )
    ledger.record(
        a_movement(
            payer=RaketaParty(),
            payee=ClubParty(uuid4()),
            seat=seat,
            reference=pay("a2"),
        )
    )
    ledger.record(
        a_movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            seat=seat,
            reference=Reference(ReferenceKind.REFUND, "a3"),
            cause=MovementCause.WITHDRAWN_BEFORE_LOCK,
        )
    )

    assert ledger.held_for(seat) == -SHARE
    assert breaches_in(ledger) == ()


def test_an_erased_ledger_is_still_reported_on(player):
    """A reconciliation that could only name a player would go quiet on exactly
    the accounts nobody can ask about."""

    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            cause=MovementCause.DEBT_CLEARED,
            seat=None,
            amount=grosze(1000),
        )
    )
    pseudonym = uuid4()
    ledger.pseudonymise(pseudonym=pseudonym, at=AT)

    breaches = breaches_in(ledger)
    assert len(breaches) == 1
    assert breaches[0].subject_id == pseudonym


# ---------------------------------------------------------------------------
# The job
# ---------------------------------------------------------------------------


class _Ledgers:
    """A ``LedgerRepository`` that hands back a fixed set and counts saves."""

    def __init__(self, ledgers: list[Ledger]) -> None:
        self._ledgers = ledgers
        self.saves = 0

    async def load(self, player_id):  # pragma: no cover — not this job's door
        raise AssertionError("the reconciliation does not load one ledger")

    async def save(self, ledger) -> None:
        self.saves += 1

    async def all_ledgers(self) -> list[Ledger]:
        return list(self._ledgers)


async def test_a_sound_run_reports_the_float_and_pages_nobody(player, caplog):
    seat = SeatRef(match_id=uuid4(), index=1)
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            seat=seat,
            reference=pay("a1"),
        )
    )

    with caplog.at_level(logging.INFO):
        report = await ReconcileLedgers(
            _Ledgers([ledger]), FrozenClock(at=utc(2026, 8, 25))
        ).execute()

    assert report.is_sound
    assert report.ledgers == 1
    assert report.movements == 1
    assert report.raketa_float == SHARE
    assert "money.reconciliation.sound" in caplog.text
    assert "money.reconciliation.breach" not in caplog.text


async def test_a_breach_is_paged_at_error_and_nothing_is_written(player, caplog):
    ledger = Ledger.for_player(player)
    ledger.record(
        a_movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            cause=MovementCause.DEBT_CLEARED,
            seat=None,
            amount=grosze(1000),
        )
    )
    ledgers = _Ledgers([ledger])

    with caplog.at_level(logging.INFO):
        report = await ReconcileLedgers(ledgers, FrozenClock()).execute()

    assert not report.is_sound
    assert [breach.invariant for breach in report.breaches] == ["no_balance_above_zero"]
    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert ledgers.saves == 0


async def test_a_run_over_a_real_repository_finds_every_ledger():
    """The scan, driven through the adapter rather than through a stub."""

    store = InMemoryEventStore(codec=money_event_codec())
    repository = build_ledger_repository(event_store=store, events=RecordingPublisher())
    seat = SeatRef(match_id=uuid4(), index=1)
    for index in range(3):
        player = uuid4()
        ledger = await repository.load(player)
        ledger.record(
            a_movement(
                payer=PlayerParty(player),
                payee=RaketaParty(),
                seat=seat,
                reference=pay(f"a{index}"),
            )
        )
        await repository.save(ledger)

    report = await ReconcileLedgers(repository, FrozenClock()).execute()

    assert report.ledgers == 3
    assert report.movements == 3
    assert report.raketa_float == grosze(3 * SHARE)
    assert report.is_sound


# ---------------------------------------------------------------------------
# It cannot repair, structurally
# ---------------------------------------------------------------------------


def test_the_reconciliation_is_built_without_a_unit_of_work():
    """*Repairs nothing* as a property of the constructor, not of a docstring.

    ADR-0055: *"a ledger that repairs itself has destroyed the evidence of the
    bug that made the repair necessary."* With no transaction to commit, the
    strongest thing this job can do is leave an aggregate dirty in memory.
    """

    parameters = set(inspect.signature(ReconcileLedgers.__init__).parameters)
    assert parameters == {"self", "ledgers", "clock"}


def test_the_reconciliation_module_never_saves_anything():
    """Read off the source, because a repository *does* have a ``save``.

    A constructor with no unit of work still leaves ``self._ledgers.save(...)``
    reachable — it simply would not commit — and a write nobody commits inside a
    session somebody else commits is exactly the accident this refuses.
    """

    source = (
        ROOT / "app" / "modules" / "money" / "application" / "reconcile_ledgers.py"
    ).read_text(encoding="utf-8")
    called = {
        node.func.attr
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "save" not in called
    assert "commit" not in called
    # The control: the walk can see the call it is supposed to be watching for.
    assert "all_ledgers" in called
