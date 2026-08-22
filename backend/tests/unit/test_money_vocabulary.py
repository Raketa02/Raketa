"""The ledger's vocabulary: parties, causes, references and a movement.

Four claims, and each fails differently.

1. **The cause enumeration is closed, counted, and wider than the kernel's** —
   and the widening is checked rather than asserted in prose. A kernel cause the
   ledger cannot record is the defect ``settlementReopened`` was put in
   ``kernel.Cause`` to prevent, in the other direction.
2. **Both cause tables are total.** A nineteenth cause with no rule, or a fifth
   outcome with no money cause, fails at import — which is the point of asserting
   them at module load rather than in a test that could be deleted.
3. **A party is one of three and a club is never a payer**, refused where a
   movement is built rather than where it is folded.
4. **A movement refuses the four shapes nothing means.** Each refusal has its own
   case, because a single "invalid movement" test passes as soon as any one of
   the four still fires.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.kernel import CAUSE_COUNT, Cause, InvariantViolated, Outcome, grosze, instant
from app.modules.money.domain.causes import (
    CAUSE_OF_OUTCOME,
    CAUSE_RULES,
    MOVEMENT_CAUSE_COUNT,
    MovementCause,
    cause_of,
    rule_for,
)
from app.modules.money.domain.movement import Movement, SeatRef
from app.modules.money.domain.parties import (
    ClubParty,
    PartyKind,
    PlayerParty,
    RaketaParty,
    party_from,
    party_id,
    party_kind,
    player_of,
)
from app.modules.money.domain.reference import Reference, ReferenceKind

AT = instant(datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc))


def a_seat() -> SeatRef:
    return SeatRef(match_id=uuid4(), index=1)


def a_movement(**overrides: object) -> Movement:
    """A share paid online — the ordinary movement every refusal is an edge off."""

    fields: dict[str, object] = {
        "id": uuid4(),
        "payer": PlayerParty(uuid4()),
        "payee": RaketaParty(),
        "amount": grosze(3800),
        "seat": a_seat(),
        "reservation": None,
        "reference": Reference(ReferenceKind.PAYMENT, "a1"),
        "cause": MovementCause.SHARE_ONLINE,
        "occurred_at": AT,
    }
    fields.update(overrides)
    return Movement(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 1. The enumeration
# ---------------------------------------------------------------------------


def test_the_cause_count_is_pinned_and_agrees_with_the_enumeration():
    assert len(MovementCause) == MOVEMENT_CAUSE_COUNT == 18


def test_the_cause_count_is_a_literal_and_not_a_derivation():
    """`MOVEMENT_CAUSE_COUNT = len(MovementCause)` satisfies its own invariant.

    Read off the **source** rather than the value, because that is the only
    place the difference exists: pinning is about the *next* member, and a count
    derived from the enumeration cannot notice one arriving. The module's own
    docstring claims this rule — *"a member arriving or leaving is a decision
    somebody made in a diff, not a number that follows along"* — and without
    this the claim is prose: the derivation passes every other test in the file.
    Same shape as `test_the_count_is_a_literal_and_not_a_derivation` for
    `OUTCOME_COUNT`, which is where the rule was first checked.
    """

    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "modules"
        / "money"
        / "domain"
        / "causes.py"
    ).read_text(encoding="utf-8")

    assert f"MOVEMENT_CAUSE_COUNT = {MOVEMENT_CAUSE_COUNT}" in source
    assert "MOVEMENT_CAUSE_COUNT = len(" not in source


def test_the_ledger_can_record_every_cause_the_kernel_produces():
    """The inclusion, checked rather than believed.

    ``kernel.Cause`` is what a *card* may carry and the ledger's set is wider;
    the relation that matters is that nothing the kernel can produce is
    unrecordable. A sixth kernel cause nobody gave a ledger meaning fails here.
    """

    assert {cause.value for cause in Cause} <= {cause.value for cause in MovementCause}
    assert len(Cause) == CAUSE_COUNT
    for cause in Cause:
        assert cause_of(cause).value == cause.value


def test_the_ledger_names_thirteen_causes_no_card_can_carry():
    """Stated as a number, so the widening cannot happen by accident.

    If somebody moves a ledger-only cause into ``kernel.Cause`` — which grows the
    OpenAPI enum both clients generate an exhaustive table over — this is the
    line that says so.
    """

    ledger_only = {cause.value for cause in MovementCause} - {
        cause.value for cause in Cause
    }
    assert len(ledger_only) == 13
    assert "shareOnline" in ledger_only
    assert "settlementReopened" not in ledger_only


# ---------------------------------------------------------------------------
# 2. The two tables
# ---------------------------------------------------------------------------


def test_every_cause_has_a_rule():
    assert set(CAUSE_RULES) == set(MovementCause)


def test_exactly_two_causes_move_a_balance():
    """ADR-0058's whole model: one number, one sign, and two causes reach it.

    Written as the set rather than as a count, because *which* two is the
    decision — a third cause moving the balance would make an ordinary seat
    payment read as a debt.
    """

    bearing = {cause for cause in MovementCause if CAUSE_RULES[cause].bears_on_balance}
    assert bearing == {
        MovementCause.COLLECTION_FAILED,
        MovementCause.DEBT_CLEARED,
    }


def test_exactly_one_cause_names_no_seat():
    """``debtCleared``, and ADR-0058's refusal of line items is why."""

    seatless = {cause for cause in MovementCause if not CAUSE_RULES[cause].names_a_seat}
    assert seatless == {MovementCause.DEBT_CLEARED}


def test_every_outcome_has_a_money_cause():
    assert set(CAUSE_OF_OUTCOME) == set(Outcome)


def test_a_forfeit_has_a_cause_even_though_the_leaver_gets_nothing():
    """The row that makes the table a decision rather than a mapping.

    A forfeited leaver receives no movement — her share settles to the club, and
    that settlement is what carries ``leaverForfeit``. An enum member with no
    movement would have looked like an omission.
    """

    assert CAUSE_OF_OUTCOME[Outcome.FORFEITED] is MovementCause.LEAVER_FORFEIT
    assert rule_for(MovementCause.LEAVER_FORFEIT).names_a_seat


# ---------------------------------------------------------------------------
# 3. Parties
# ---------------------------------------------------------------------------


def test_a_party_round_trips_through_what_an_event_carries():
    for party in (PlayerParty(uuid4()), ClubParty(uuid4()), RaketaParty()):
        assert party_from(party_kind(party), party_id(party)) == party


def test_the_platform_party_carries_no_id():
    assert party_id(RaketaParty()) is None
    with pytest.raises(InvariantViolated):
        party_from(PartyKind.RAKETA, uuid4())


@pytest.mark.parametrize("kind", [PartyKind.PLAYER, PartyKind.CLUB])
def test_a_player_or_a_club_party_without_an_id_is_refused(kind):
    with pytest.raises(InvariantViolated):
        party_from(kind, None)


def test_two_player_parties_are_refused():
    """A movement between two players would have a claim on two streams."""

    with pytest.raises(InvariantViolated):
        player_of(PlayerParty(uuid4()), PlayerParty(uuid4()))


def test_a_movement_between_two_players_is_refused():
    """Raketa is a party to every transfer between people.

    Asserted on ``Movement`` and not only on ``player_of``: a movement is where
    the rule has to hold, and it would be the one movement with a claim on two
    streams.
    """

    with pytest.raises(InvariantViolated):
        a_movement(payer=PlayerParty(uuid4()), payee=PlayerParty(uuid4()))


def test_a_movement_with_no_player_party_is_legal_and_names_nobody():
    """The `Raketa → club` half of a pass-through share, and only it.

    ADR-0055 writes *"every movement has exactly one player party"*, justified as
    *"so no movement is homeless and none is written to two streams"* — and
    ADR-0056, the same day, requires this half or ``held`` is not derivable. The
    justification is what is enforced: it lives on exactly one stream, and it
    names nobody.
    """

    settlement = a_movement(payer=RaketaParty(), payee=ClubParty(uuid4()))
    assert settlement.player is None


# ---------------------------------------------------------------------------
# 4. A movement's four refusals
# ---------------------------------------------------------------------------


def test_a_club_may_not_be_a_payer():
    with pytest.raises(InvariantViolated):
        a_movement(payer=ClubParty(uuid4()), payee=PlayerParty(uuid4()))


@pytest.mark.parametrize("amount", [0, -3800])
def test_a_movement_of_nothing_or_of_a_negative_amount_is_refused(amount):
    """The direction is the parties, never the sign."""

    with pytest.raises(InvariantViolated):
        a_movement(amount=grosze(amount))


def test_a_movement_to_itself_is_refused():
    with pytest.raises(InvariantViolated):
        a_movement(payer=RaketaParty(), payee=RaketaParty())


def test_a_cause_that_names_a_seat_must_have_one():
    with pytest.raises(InvariantViolated):
        a_movement(seat=None)


def test_a_debt_payment_may_not_name_a_seat():
    """The only cause with no seat, refused in the direction nobody expects."""

    with pytest.raises(InvariantViolated):
        a_movement(cause=MovementCause.DEBT_CLEARED, seat=a_seat())

    cleared = a_movement(cause=MovementCause.DEBT_CLEARED, seat=None)
    assert cleared.seat is None


def test_a_balance_bearing_movement_must_name_a_player():
    """A debt with no debtor folds into a number nothing can attribute."""

    with pytest.raises(InvariantViolated):
        a_movement(
            payer=RaketaParty(),
            payee=ClubParty(uuid4()),
            cause=MovementCause.COLLECTION_FAILED,
        )


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kind,text",
    [
        (ReferenceKind.PAYMENT, "PAY-a1"),
        (ReferenceKind.REFUND, "REF-a1"),
        (ReferenceKind.REVERSAL, "REV-a1"),
    ],
)
def test_a_reference_prints_and_parses_back(kind, text):
    reference = Reference(kind, "a1")
    assert reference.text == text
    assert Reference.parse(text) == reference


def test_only_a_reversal_is_a_compensation():
    assert Reference(ReferenceKind.REVERSAL, "a1").is_compensation
    assert not Reference(ReferenceKind.PAYMENT, "a1").is_compensation
    assert not Reference(ReferenceKind.REFUND, "a1").is_compensation


@pytest.mark.parametrize("text", ["a1", "FV/2026/08/118", "XXX-a1", ""])
def test_a_reference_this_module_did_not_write_is_refused(text):
    with pytest.raises(InvariantViolated):
        Reference.parse(text)


@pytest.mark.parametrize("token", ["", "a-1", "a 1"])
def test_a_token_that_would_make_parsing_ambiguous_is_refused(token):
    with pytest.raises(InvariantViolated):
        Reference(ReferenceKind.PAYMENT, token)


def test_a_seat_at_a_negative_position_is_refused():
    with pytest.raises(InvariantViolated):
        SeatRef(match_id=uuid4(), index=-1)
