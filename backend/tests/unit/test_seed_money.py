"""The seeded ledgers: named states, names that are checked, and a sound set.

Three claims, and each fails differently.

1. **The catalog refuses a scenario whose claim disagrees with its arrival**,
   before a session is ever opened. Exactly one arrival moves a balance, and a
   claim that says otherwise is a claim about a number nothing computes that way.
2. **The name is checked against the *stored* ledger on every run**, including a
   run that creates nothing — the ledger seeded a month ago is the one nobody
   would check otherwise. Every number in the claim is a **fold**, so this is the
   arithmetic a screen and a support conversation both read.
3. **The whole seeded set passes the reconciliation's own three invariants.** A
   seeded database that breaks one is one every future Money test is developed
   against.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from app.kernel import grosze
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.invariants import breaches_in
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.parties import ClubParty, RaketaParty
from app.modules.money.domain.reference import Reference, ReferenceKind
from app.seeds.money import LEDGERS, Arrival, LedgerClaim, SeedLedger
from app.seeds.runner import SeedFailed, seed


def _scenario(slug: str) -> SeedLedger:
    for ledger in LEDGERS:
        if ledger.slug == slug:
            return ledger
    raise AssertionError(f"no seeded ledger called {slug}")


# ---------------------------------------------------------------------------
# 1. The catalog's own refusals
# ---------------------------------------------------------------------------


def test_every_scenario_has_its_own_slug_and_its_own_reference_token():
    """The token is the idempotency probe, so two sharing one would make the
    second scenario read as already seeded and never run."""

    assert len({ledger.slug for ledger in LEDGERS}) == len(LEDGERS)
    assert len({ledger.token for ledger in LEDGERS}) == len(LEDGERS)


def test_at_most_one_scenario_per_account_moves_a_balance():
    """``balance`` is a claim about the whole player, not about one scenario.

    Two debts on one account would leave both claims quietly wrong — each would
    be describing a number the other had also moved.
    """

    owing = [
        ledger.account_slug
        for ledger in LEDGERS
        if ledger.arrival is Arrival.COLLECTION_FAILED
    ]
    assert len(owing) == len(set(owing))


def test_a_claim_that_disagrees_with_its_arrival_is_refused():
    held = _scenario("ledger-holding-a-share")
    with pytest.raises(ValueError, match="Exactly one arrival moves a balance"):
        replace(
            held,
            claim=replace(held.claim, balance=grosze(-3000)),
        )


def test_a_debt_that_claims_a_balance_of_zero_is_refused():
    debt = _scenario("ledger-in-debt")
    with pytest.raises(ValueError, match="Exactly one arrival moves a balance"):
        replace(debt, claim=replace(debt.claim, balance=grosze(0)))


def test_a_reference_token_that_would_not_print_is_refused():
    held = _scenario("ledger-holding-a-share")
    with pytest.raises(ValueError, match="letters and digits"):
        replace(held, token="hs-1")


def test_the_five_scenarios_cover_the_five_arrivals():
    """One scenario per shape, and no shape twice — *two ledgers saying the same
    thing would be one scenario twice*."""

    assert {ledger.arrival for ledger in LEDGERS} == set(Arrival)
    assert len(LEDGERS) == len(Arrival)


# ---------------------------------------------------------------------------
# 2. The name is checked against what is stored
# ---------------------------------------------------------------------------


async def test_the_seeded_ledgers_fold_to_what_they_promise(session_factory):
    async with session_factory() as session:
        seeded = await seed(session)

    assert {entry.ledger.slug for entry in seeded.ledgers} == {
        ledger.slug for ledger in LEDGERS
    }
    assert all(entry.created for entry in seeded.ledgers)


async def test_a_second_run_creates_nothing_and_still_checks_every_claim(
    session_factory,
):
    async with session_factory() as session:
        await seed(session)
        again = await seed(session)

    assert not any(entry.created for entry in again.ledgers)


async def test_the_two_custody_regimes_are_two_different_chains(session_factory):
    """The same 38 zł, and a different answer to *who has it*."""

    async with session_factory() as session:
        seeded = await seed(session)
        by_slug = {entry.ledger.slug: entry for entry in seeded.ledgers}

        from app.bootstrap.composition import (
            build_domain_event_store,
            build_event_publisher,
            build_ledger_repository,
        )

        ledgers = build_ledger_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        held_entry = by_slug["ledger-holding-a-share"]
        through_entry = by_slug["ledger-with-a-share-passed-through"]

        held = await ledgers.load(held_entry.player_id)
        through = await ledgers.load(through_entry.player_id)

    assert held.raketa_float == grosze(3800)
    assert through.raketa_float == grosze(0)
    assert len(through.movements) == 2
    assert isinstance(through.movements[1].payee, ClubParty)


async def test_a_name_that_stops_matching_its_state_stops_the_run(
    session_factory, monkeypatch
):
    """The strongest form of the rule available here: every number is a fold.

    The claim is re-checked on a run that creates nothing, so a catalog whose
    arithmetic has since moved is caught rather than developed against.
    """

    async with session_factory() as session:
        await seed(session)

        lying = tuple(
            replace(
                ledger,
                claim=LedgerClaim(
                    promise=ledger.claim.promise,
                    movements=ledger.claim.movements + 1,
                    held=ledger.claim.held,
                    balance=ledger.claim.balance,
                ),
            )
            for ledger in LEDGERS
        )
        monkeypatch.setattr("app.seeds.runner.LEDGERS", lying)

        with pytest.raises(SeedFailed, match="is no longer one"):
            await seed(session)


async def test_a_held_claim_that_stops_matching_stops_the_run(
    session_factory, monkeypatch
):
    """Each part of the claim on its own.

    A mutation run put this here: making the ``held`` comparison a tautology
    survived every test, because the only case that moved a claim moved the
    movement **count** — and one number changing is enough for a check on three
    to go red. Three numbers, three cases.
    """

    async with session_factory() as session:
        await seed(session)

        held = _scenario("ledger-holding-a-share")
        monkeypatch.setattr(
            "app.seeds.runner.LEDGERS",
            (replace(held, claim=replace(held.claim, held=grosze(1))),),
        )
        with pytest.raises(SeedFailed, match="is no longer one"):
            await seed(session)


async def test_a_balance_claim_that_stops_matching_stops_the_run(
    session_factory, monkeypatch
):
    """And the balance, which is the one a debt scenario is entirely about."""

    async with session_factory() as session:
        await seed(session)

        debt = _scenario("ledger-in-debt")
        monkeypatch.setattr(
            "app.seeds.runner.LEDGERS",
            (replace(debt, claim=replace(debt.claim, balance=grosze(-1))),),
        )
        with pytest.raises(SeedFailed, match="is no longer one"):
            await seed(session)


async def test_a_ledger_naming_an_account_the_catalog_lost_stops_the_run(
    session_factory, monkeypatch
):
    monkeypatch.setattr(
        "app.seeds.runner.LEDGERS",
        (replace(_scenario("ledger-holding-a-share"), account_slug="nobody"),),
    )
    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="which the account catalog"):
            await seed(session)


async def test_a_ledger_naming_a_match_the_catalog_lost_stops_the_run(
    session_factory, monkeypatch
):
    monkeypatch.setattr(
        "app.seeds.runner.LEDGERS",
        (replace(_scenario("ledger-holding-a-share"), match_slug="no-such-match"),),
    )
    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="which the match catalog"):
            await seed(session)


# ---------------------------------------------------------------------------
# 3. The set is sound
# ---------------------------------------------------------------------------


async def test_the_seeded_set_breaks_no_ledger_invariant(session_factory):
    """The same three functions the nightly reconciliation calls."""

    from app.bootstrap.composition import (
        build_domain_event_store,
        build_event_publisher,
        build_ledger_repository,
    )

    async with session_factory() as session:
        await seed(session)
        ledgers = build_ledger_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        stored = await ledgers.all_ledgers()

    assert len(stored) == len(LEDGERS)
    assert [breach for ledger in stored for breach in breaches_in(ledger)] == []


async def test_a_seeded_set_that_breaks_an_invariant_stops_the_run(
    session_factory,
):
    """The guard's own negative control: it can tell a broken set from a sound one.

    Written onto a player **no scenario names**, deliberately. Each scenario's
    own claim is checked first and would catch a movement added to its ledger, so
    a broken movement on a seeded player would prove the name check fires rather
    than this one. A ledger nothing in the catalog describes is the case only the
    set-wide assertion can reach — and it is the realistic one: whatever writes a
    bad movement in production will not have been the seed.

    The shape is ADR-0056's *broken split* — a club settled more than the player
    funded for that seat.
    """

    from app.bootstrap.composition import (
        build_domain_event_store,
        build_event_publisher,
        build_ledger_repository,
        build_unit_of_work,
    )
    from app.infrastructure.clock import SystemClock
    from app.modules.money.application.commands import (
        NewMovement,
        RecordMovementsCommand,
    )
    from app.modules.money.application.record_movements import RecordMovements

    stranger = uuid4()

    async with session_factory() as session:
        seeded = await seed(session)
        match_id = seeded.matches[0].match_id

        ledgers = build_ledger_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        await RecordMovements(
            ledgers, build_unit_of_work(session), SystemClock()
        ).execute(
            RecordMovementsCommand(
                player_id=stranger,
                drafts=(
                    NewMovement(
                        payer=RaketaParty(),
                        payee=ClubParty(uuid4()),
                        amount=grosze(9600),
                        cause=MovementCause.SHARE_ONLINE,
                        reference=Reference(ReferenceKind.PAYMENT, "broken"),
                        seat=SeatRef(match_id=match_id, index=0),
                    ),
                ),
            )
        )

        with pytest.raises(SeedFailed, match="every_seat_chain_closes"):
            await seed(session)


def test_a_seeded_ledger_is_about_a_player_the_catalog_names():
    """Every scenario points at an account slug that exists, read statically.

    Cheap, and it catches a rename in the account catalog on the run that never
    reaches a database — a `make seed` on an empty machine fails on the account
    catalog first and would otherwise never say which ledger was orphaned.
    """

    from app.seeds.catalog import ACCOUNTS

    known = {account.slug for account in ACCOUNTS}
    assert {ledger.account_slug for ledger in LEDGERS} <= known


def test_a_seeded_ledger_is_about_a_match_the_catalog_names():
    from app.seeds.matches import MATCHES

    known = {match.slug for match in MATCHES}
    assert {ledger.match_slug for ledger in LEDGERS} <= known


def test_the_corrected_scenario_sits_on_a_seat_nobody_holds():
    """The story only works if the seat is empty on the match record too.

    A claim that lapsed leaves the seat free; a scenario that put the reversal on
    a seat somebody is sitting in would be seeded data disagreeing with itself.
    """

    from app.seeds.matches import MATCHES

    corrected = _scenario("ledger-with-a-corrected-movement")
    match = next(found for found in MATCHES if found.slug == corrected.match_slug)
    assert corrected.seat_index >= match.taken
