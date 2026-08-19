"""Money: the rounding order, the exact split, and the card that cannot credit.

Everything here goes through ``app.kernel``'s public surface, never a submodule,
and asserts what a caller can observe — a returned amount, a raised invariant —
never how it was computed.

**The load-bearing test in this file is the rounding order** (``THE_WALKS``
below). Every other guarantee — the exact split, a payable that never goes
negative — rests on a court price being a whole number of złoty, and that is
true only because the single rounding happens at the court and not at the seat.
The difference between the two is 21,50 zł and 21,60 zł, which is small enough
to survive review and large enough that a player and a club manager read
different numbers for one booking.
"""

import ast
import random
from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path

import pytest

from app.kernel import (
    GROSZE_PER_ZLOTY,
    SOLD_FORMATS,
    SPORT_SPECS,
    CardAllowance,
    CardCoversShare,
    ClubCard,
    CourtPrice,
    Grosze,
    InvariantViolated,
    NoCard,
    Sport,
    add_grosze,
    apply_fraction,
    at_least_zero,
    card_offset,
    court_price,
    divide_among_players,
    grosze,
    negate_grosze,
    payable_from,
    percent,
    ratio,
    subtract_grosze,
    zloty,
)

ROOT = Path(__file__).resolve().parents[2]
MONEY = ROOT / "app" / "kernel" / "money.py"


# --- The worked walks ----------------------------------------------------------
#
# Transcribed from the documents in this repository that record them, never
# computed from the implementation — a test that derives its expectation from
# the code under test asserts nothing. Each names its source, because the
# specification documents these figures originally come from are not in this
# repository (they describe a TypeScript codebase; `docs/adr/0021`–`0024` are
# the tiebreak) and the fourth is constructed from a stated rule rather than
# transcribed, since no document here records a worked refund figure.


def test_a_discounted_court_splits_four_ways_to_twenty_one_fifty() -> None:
    """`docs/adr/0023`, verbatim: `96 zł × 0.90 = 86.4 → 86 zł → ÷ 4 → 21,50`.

    **The walk that distinguishes the rounding order.** Dividing first gives
    9600 × 0,90 ÷ 4 = 2160, and 21,60 zł is the wrong answer. It is wrong by ten
    grosze a seat, which is why it has to be a test rather than a comment.
    """

    price = court_price(zloty(96), percent(90))
    assert price == 8600, "one rounding, at the court, to whole złoty"

    share = divide_among_players(price, 4)
    assert share == 2150

    # The order made explicit: the same figures divided before the rounding.
    assert 9600 * 90 // 100 // 4 == 2160
    assert share != 2160


def test_a_card_takes_eight_zloty_off_a_thirty_eight_zloty_seat() -> None:
    """`docs/value-formatting.md`, the *Money, discounted* row: `38,00` struck
    through, then `30,00 zł`, with a tag reading `card −8,00`.

    Three numbers, and the client needs all three — which is why the offset is
    readable on its own rather than only implied by the difference.
    """

    share = divide_among_players(court_price(zloty(152)), 4)
    assert share == 3800

    card = CardAllowance(zloty(8))
    assert card_offset(share, card) == 800
    assert payable_from(share, card) == 3000


def test_a_fifteen_zloty_allowance_against_a_thirteen_zloty_seat_pays_nothing() -> None:
    """`docs/adr/0023` and the root `CONTEXT.md`: *a 15 zł allowance against a
    13 zł share yields a 13 zł offset*.

    Never a credit, and never a negative payable. The offset is what a client
    shows in the tag, so it has to be the capped figure and not the allowance.
    """

    share = divide_among_players(court_price(zloty(52)), 4)
    assert share == 1300

    card = CardAllowance(zloty(15))
    assert card_offset(share, card) == 1300
    assert payable_from(share, card) == 0


def test_half_of_an_odd_share_comes_back_in_the_players_favour() -> None:
    """Constructed from the rule in `docs/adr/0023` rather than transcribed:
    *`apply_fraction` rounds half away from zero on the magnitude … a player
    receives at most one grosz more than the exact half*.

    An 87 zł court splits four ways into 21,75 — a share with an odd number of
    grosze, which is reachable because a whole złoty is 100 grosze and 100 ÷ 4
    is 25. Half of it is 10,875, and the player gets 10,88.
    """

    share = divide_among_players(court_price(zloty(87)), 4)
    assert share == 2175

    assert apply_fraction(share, percent(50)) == 1088
    assert apply_fraction(share, percent(50)) * 2 == share + 1, "at most one grosz"


# --- Grosze: integers, signed, and never a bool --------------------------------


def test_an_amount_is_held_as_a_plain_integer() -> None:
    assert grosze(3800) == 3800
    assert type(grosze(3800)) is int


def test_zloty_is_a_hundred_grosze() -> None:
    assert zloty(96) == 9600
    assert GROSZE_PER_ZLOTY == 100


def test_a_negative_amount_is_legal_because_money_moves_both_ways() -> None:
    assert grosze(-3800) == -3800
    assert zloty(-38) == -3800


@pytest.mark.parametrize("make", [grosze, zloty, percent])
def test_a_bool_is_never_an_amount(make: object) -> None:
    """`bool` is a subclass of `int`, so `grosze(True)` means one grosz."""

    with pytest.raises(InvariantViolated) as raised:
        make(True)  # type: ignore[operator]
    assert "bool" in str(raised.value)


# --- The rounding order, and the single rounding -------------------------------


def test_the_rounding_happens_once_and_at_the_court() -> None:
    """A base that is not whole złoty is made whole *before* anything divides."""

    assert court_price(grosze(9650)) == 9700
    assert court_price(grosze(9649)) == 9600
    assert divide_among_players(court_price(grosze(9650)), 4) == 2425


def test_multipliers_compound_into_one_product_and_one_rounding() -> None:
    """Two multipliers are one product, not two prices.

    A 24 zł court at 90% and then 85% is 18,36 zł, which is 18 zł. Rounding
    between them instead gives 21,60 → 22 zł → 18,70 → 19 zł: a whole złoty
    more, from an intermediate the domain never asked anyone to name.
    """

    assert court_price(zloty(24), percent(90), percent(85)) == 1800

    stepwise = court_price(court_price(zloty(24), percent(90)), percent(85))
    assert stepwise == 1900, "the second rounding, and the złoty it invents"

    assert court_price(zloty(100), percent(90), percent(85)) == 7700
    assert court_price(zloty(100)) == 10000, "no multipliers is still a rounding"


def test_an_exact_ratio_and_a_double_disagree_by_a_whole_zloty() -> None:
    """Why the multiplier is a `Fraction` and not a float, in one line.

    A 55 zł court at a 70% off-peak rate is 38,50 zł exactly, which rounds up to
    39 zł. Through a double, `5500 * 0.7` is 3849.9999999999995 — 38,4999… —
    which rounds *down* to 38 zł. One multiplier, one złoty, and every seat
    share under it is wrong by 25 or 50 grosze.
    """

    assert court_price(zloty(55), percent(70)) == 3900
    assert 5500 * 0.7 != 3850.0, "the double this exists to avoid"


def test_a_court_price_is_always_a_whole_number_of_zloty() -> None:
    for base in (1, 49, 50, 51, 99, 100, 9650, 12345):
        price = court_price(grosze(base))
        assert price % GROSZE_PER_ZLOTY == 0, f"not whole złoty: {base} → {price}"


def test_a_court_price_below_zero_is_refused() -> None:
    """Nothing sells a court for a negative figure, and the whole refinement
    chain below it — share, payable — is non-negative because of this guard."""

    with pytest.raises(InvariantViolated) as raised:
        court_price(grosze(-9600))
    assert "-96" in str(raised.value)


def test_a_ratio_takes_two_integers_so_a_float_has_nowhere_to_enter() -> None:
    assert ratio(9, 10) == Fraction(9, 10)
    assert percent(90) == Fraction(9, 10)
    assert ratio(90, 100) == percent(90), "one number, one spelling"


@pytest.mark.parametrize(
    "numerator, denominator, named",
    [(9, 0, "denominator"), (9, -10, "denominator"), (-9, 10, "numerator")],
)
def test_a_ratio_refuses_what_no_multiplier_means(
    numerator: int, denominator: int, named: str
) -> None:
    with pytest.raises(InvariantViolated) as raised:
        ratio(numerator, denominator)
    assert named in str(raised.value)


# --- The split -----------------------------------------------------------------


@pytest.mark.parametrize("players", SOLD_FORMATS)
def test_a_court_divides_exactly_among_the_players_it_is_sold_for(
    players: int,
) -> None:
    price = court_price(zloty(87))
    share = divide_among_players(price, players)
    assert share * players == price


def test_splitting_by_three_raises_and_the_message_names_the_count() -> None:
    """No racket sport is sold in threes, so a three is a bug upstream."""

    with pytest.raises(InvariantViolated) as raised:
        divide_among_players(court_price(zloty(96)), 3)
    assert "3" in str(raised.value)


def test_the_split_uses_the_sold_format_and_never_the_occupancy() -> None:
    """A padel match with three players still divides by four.

    The court costs what it costs. The count comes from the registry, which is
    why `divide_among_players` takes the number rather than the `Sport` — money
    stays independent of the sport registry and the caller does the reading.
    """

    price = court_price(zloty(96))
    occupancy = 3
    sold = SPORT_SPECS[Sport.PADEL].players

    assert sold == 4
    assert divide_among_players(price, sold) == 2400

    with pytest.raises(InvariantViolated):
        divide_among_players(price, occupancy)


def test_a_player_count_from_a_bool_is_refused() -> None:
    with pytest.raises(InvariantViolated) as raised:
        divide_among_players(court_price(zloty(96)), True)
    assert "bool" in str(raised.value)


def test_a_court_price_that_bypassed_its_constructor_is_caught_at_the_split() -> None:
    """`CourtPrice` is a `NewType` and erases at runtime, so this is reachable.

    It is the one path to a split that loses money — 8650 ÷ 4 is 2162,5 — and
    the whole-złoty law is asserted at the split rather than assumed so that the
    bypass fails loudly instead of quietly dropping a grosz on the floor.
    """

    smuggled = CourtPrice(Grosze(8650))
    with pytest.raises(InvariantViolated) as raised:
        divide_among_players(smuggled, 4)
    assert "8650" in str(raised.value)


# --- The card rule, which exists exactly once ----------------------------------


def test_no_card_takes_nothing_off() -> None:
    share = divide_among_players(court_price(zloty(96)), 4)
    assert card_offset(share, NoCard()) == 0
    assert payable_from(share, NoCard()) == share


def test_a_card_covering_the_seat_leaves_nothing_to_pay() -> None:
    share = divide_among_players(court_price(zloty(96)), 4)
    assert card_offset(share, CardCoversShare()) == share
    assert payable_from(share, CardCoversShare()) == 0


def test_an_allowance_smaller_than_the_share_comes_off_in_full() -> None:
    share = divide_among_players(court_price(zloty(96)), 4)
    assert card_offset(share, CardAllowance(zloty(10))) == 1000
    assert payable_from(share, CardAllowance(zloty(10))) == 1400


def test_an_allowance_larger_than_the_share_is_capped_never_credited() -> None:
    share = divide_among_players(court_price(zloty(52)), 4)
    offset = card_offset(share, CardAllowance(zloty(100)))
    assert offset == share
    assert payable_from(share, CardAllowance(zloty(100))) == 0


def test_an_allowance_below_zero_is_refused_by_the_card_itself() -> None:
    """The only way a payable could exceed its share, closed at the value
    object rather than at the two functions that read it."""

    with pytest.raises(InvariantViolated) as raised:
        CardAllowance(grosze(-500))
    assert "-500" in str(raised.value)


def test_the_offset_and_the_payable_always_add_back_up_to_the_share() -> None:
    share = divide_among_players(court_price(zloty(87)), 2)
    for card in (NoCard(), CardAllowance(zloty(20)), CardCoversShare()):
        assert card_offset(share, card) + payable_from(share, card) == share


def test_a_card_is_a_frozen_value_and_the_union_has_three_members() -> None:
    card = CardAllowance(zloty(8))
    with pytest.raises(FrozenInstanceError):
        card.amount = zloty(9)  # type: ignore[misc]

    assert set(ClubCard.__args__) == {NoCard, CardAllowance, CardCoversShare}  # type: ignore[attr-defined]


# --- Fractions of an amount, and the direction they round ----------------------


@pytest.mark.parametrize(
    "amount, expected",
    [
        (2250, 563),  # 5,625
        (2150, 538),  # 5,375
        (2050, 513),  # 5,125
        (400, 100),  # exact, so there is no rounding to argue about
    ],
)
def test_a_quarter_of_a_share_rounds_away_from_zero(
    amount: int, expected: int
) -> None:
    assert apply_fraction(grosze(amount), percent(25)) == expected


@pytest.mark.parametrize("amount, away, to_even", [(2250, 563, 562), (2050, 513, 512)])
def test_where_half_to_even_would_differ_the_answer_is_the_players(
    amount: int, away: int, to_even: int
) -> None:
    """Python's `round` is half-to-even, which is the mutation this catches.

    Half-to-even sends 5,625 to 5,62 and 5,125 to 5,12 while sending 5,375 to
    5,38 — neighbouring refunds rounded in opposite directions, for no reason a
    player could be told. The two cases here are the ones where the two rules
    part company, so `round` in place of the helper turns this red.
    """

    assert round(amount * 25 / 100) == to_even, "the rule this is not"
    assert apply_fraction(grosze(amount), percent(25)) == away


@pytest.mark.parametrize("amount", [2250, 2150, 2050, 1, 0, 99999])
def test_the_fractional_helper_is_symmetric_in_sign(amount: int) -> None:
    """Both directions, because that is what "symmetric" means and a helper
    that truncated toward zero would pass one of them."""

    fraction = percent(25)
    positive = apply_fraction(grosze(amount), fraction)
    negative = apply_fraction(grosze(-amount), fraction)

    assert negative == -positive
    assert apply_fraction(negate_grosze(grosze(amount)), fraction) == negate_grosze(
        positive
    )


def test_a_whole_fraction_returns_the_amount_and_a_zero_one_returns_nothing() -> None:
    assert apply_fraction(grosze(2175), percent(100)) == 2175
    assert apply_fraction(grosze(2175), percent(0)) == 0


# --- Arithmetic, which loses the refinement on purpose -------------------------


def test_amounts_add_subtract_and_negate() -> None:
    assert add_grosze(grosze(1000), grosze(150)) == 1150
    assert subtract_grosze(grosze(1000), grosze(150)) == 850
    assert negate_grosze(grosze(1000)) == -1000


def test_a_negative_amount_round_trips_through_all_three() -> None:
    amount = grosze(-3800)
    assert negate_grosze(negate_grosze(amount)) == amount
    assert subtract_grosze(add_grosze(amount, grosze(500)), grosze(500)) == amount
    assert add_grosze(amount, negate_grosze(amount)) == 0


def test_the_clamp_floors_at_zero_and_leaves_everything_else_alone() -> None:
    assert at_least_zero(grosze(-1)) == 0
    assert at_least_zero(grosze(0)) == 0
    assert at_least_zero(grosze(3800)) == 3800


# --- Properties, as seeded walks (no property-testing library) -----------------
#
# The repo's existing pattern — `tests/unit/test_racketskill_properties.py` — so
# it adds no dependency and a failure is reproducible from the seed printed in
# the assertion.

WALKS = 500


def _some_price(rng: random.Random) -> CourtPrice:
    """A court price built the only way one can be built."""

    base = grosze(rng.randrange(0, 500_00))
    multipliers = tuple(
        ratio(rng.randrange(0, 300), rng.choice((10, 100, 1000)))
        for _ in range(rng.randrange(0, 3))
    )
    return court_price(base, *multipliers)


def test_a_share_times_its_player_count_is_the_price_exactly() -> None:
    """The property the whole-złoty law exists for.

    A failure means the rounding order was broken upstream, which is a far more
    useful signal than a missing grosz on a receipt.
    """

    rng = random.Random(20260816)
    for seed in range(WALKS):
        price = _some_price(rng)
        assert price % GROSZE_PER_ZLOTY == 0, f"price not whole złoty: seed={seed}"
        for players in SOLD_FORMATS:
            share = divide_among_players(price, players)
            assert share * players == price, f"split lost money: seed={seed}"
            assert type(share) is int, f"a float reached a share: seed={seed}"


def test_a_payable_is_never_negative_and_never_exceeds_its_share() -> None:
    """For every share and every card value, which is three kinds of card."""

    rng = random.Random(20260817)
    for seed in range(WALKS):
        share = divide_among_players(_some_price(rng), rng.choice(SOLD_FORMATS))
        cards: tuple[ClubCard, ...] = (
            NoCard(),
            CardAllowance(grosze(rng.randrange(0, 200_00))),
            CardCoversShare(),
        )
        for card in cards:
            offset = card_offset(share, card)
            payable = payable_from(share, card)
            where = f"seed={seed} card={card}"

            assert 0 <= payable <= share, f"payable outside its share: {where}"
            assert 0 <= offset <= share, f"offset outside the share: {where}"
            assert offset + payable == share, f"offset and payable disagree: {where}"


def test_no_money_value_is_ever_anything_but_an_integer() -> None:
    """The runtime half of *no float touches a price*: the source walk below
    says none is written, and this says none arrives by arithmetic."""

    rng = random.Random(20260818)
    for _ in range(WALKS):
        price = _some_price(rng)
        share = divide_among_players(price, rng.choice(SOLD_FORMATS))
        values = (
            price,
            share,
            card_offset(share, CardAllowance(grosze(rng.randrange(0, 5000)))),
            payable_from(share, CardCoversShare()),
            apply_fraction(share, ratio(rng.randrange(0, 100), 100)),
            add_grosze(share, share),
            at_least_zero(negate_grosze(share)),
        )
        assert all(type(value) is int for value in values), values


# --- No float, and no formatting, in the module itself -------------------------


def _money_tree() -> ast.Module:
    return ast.parse(MONEY.read_text(encoding="utf-8"), filename=str(MONEY))


def test_no_float_appears_anywhere_in_the_module() -> None:
    """A float literal or a `float` annotation, either of which reintroduces
    the error the integer representation exists to avoid.

    The docstrings talk about floats at length; this reads the syntax tree, so
    the argument for not using one is not mistaken for using one.
    """

    offenders = []
    for node in ast.walk(_money_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            offenders.append(f"money.py:{node.lineno}: literal {node.value!r}")
        if isinstance(node, ast.Name) and node.id == "float":
            offenders.append(f"money.py:{node.lineno}: the name `float`")
    assert not offenders, "a float in the money module:\n" + "\n".join(offenders)


def test_the_card_rule_is_implemented_exactly_once() -> None:
    """The source documents this is derived from carried two implementations of
    the cap with different null checks — two places to change, and one that gets
    changed. So `payable_from` does not re-derive the offset, it *calls* the one
    function that owns the rule, and the cap itself is written once.
    """

    functions = {
        node.name: node
        for node in ast.walk(_money_tree())
        if isinstance(node, ast.FunctionDef)
    }
    assert {"card_offset", "payable_from"} <= functions.keys()

    calls = [
        node.func.id
        for node in ast.walk(functions["payable_from"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "card_offset" in calls, "the card rule re-derived instead of called"

    capped = [
        node
        for node in ast.walk(_money_tree())
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "min"
    ]
    assert len(capped) == 1, "the cap is written in more than one place"


def test_the_module_returns_no_string_and_defines_no_formatting() -> None:
    """The kernel emits integer minor units; `docs/value-formatting.md` is the
    rendering contract and it belongs to the clients."""

    functions = [
        node
        for node in ast.walk(_money_tree())
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    stringly = [
        f"money.py:{node.lineno}: {node.name}"
        for node in functions
        if isinstance(node.returns, ast.Name) and node.returns.id == "str"
    ]
    assert not stringly, "a money function returning text:\n" + "\n".join(stringly)

    named = {node.name for node in functions}
    assert not named & {"__str__", "__repr__", "__format__"}
    assert not [name for name in named if "format" in name or "render" in name]

    # A walk over a module that has moved passes by finding nothing.
    assert MONEY.exists()
    assert len(functions) >= 15, functions
