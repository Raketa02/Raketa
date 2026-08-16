"""Money: integer grosze, the rounding order, and the exact seat split.

See ``docs/adr/0023-money-integer-grosze-gross-whole-zloty.md``.

**Money is integer grosze**, one hundred to the złoty, and no float touches a
price anywhere in this module — not in a constant, not in a signature, not in
an intermediate. Where an exact non-integer is genuinely needed, a rate
multiplier or a refund percentage, it is a ``Fraction`` over two integers, which
is exact where ``0.9 * 0.85`` is not.

**The rounding order is the specification, not an implementation detail.**
Multipliers compound, then **one** rounding to whole złoty at the court level,
then the split::

    96 zł × 0.90 = 86.4  →  86 zł court  →  ÷ 4  →  21,50 zł share

Dividing first gives 21,60. The order is the difference between those two
answers, and here it is made *unwritable* rather than documented: `CourtPrice`
has exactly one constructor and it performs that rounding, `SeatShare` has
exactly one constructor and it accepts **only** a `CourtPrice`. There is no path
from a raw number to a `SeatShare`, so dividing before rounding does not
typecheck — a claim worth precisely what checks it, which is
``tests/typecheck/kernel_misuse.py``.

**The split is exact, and that rests on a law.** A whole-złoty court price is a
multiple of one hundred grosze, and both 100 ÷ 2 and 100 ÷ 4 are integers, so
the split never rounds and never loses a grosz. That property holds only while
court prices are whole złoty — marketplace law, not an observation about seeded
data. Here it holds **by construction**: anything built through `court_price`
satisfies it. The second enforcement point — rejecting a club rate whose product
does not round cleanly — needs a club to exist and is out of scope.

**Every figure is gross**, VAT-inclusive, the number the player sees. There is
no net type and no VAT arithmetic here; decomposing a gross figure for an
invoice belongs to whichever context issues one.

**The kernel does not format money.** It leaves as integer minor units;
``docs/value-formatting.md`` is the rendering contract and it belongs to the
clients, because one price needs three renderings and a preformatted string can
only be one of them.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import NewType, TypeAlias, final

from app.kernel.invariants import exhaustive, invariant

#: One hundred grosze to the złoty. The only conversion factor in the module,
#: and the number the whole-złoty law is stated against.
GROSZE_PER_ZLOTY = 100

#: The player counts a racket court is sold in. Two or four; there is no third,
#: which is why `divide_among_players` refuses one rather than rounding it.
SOLD_FORMATS = (2, 4)

#: An amount of money, in whole grosze. **Signed**: a negative figure is money
#: out, which is what a refund or a ledger debit is.
Grosze = NewType("Grosze", int)

#: What a whole court costs for one booked block, after every multiplier.
#: **Always a whole number of złoty** — see the module docstring.
CourtPrice = NewType("CourtPrice", Grosze)

#: One player's part of a `CourtPrice`, divided by the **sold** player count.
SeatShare = NewType("SeatShare", Grosze)

#: What one player actually owes: their `SeatShare` less any card offset.
#: Never negative.
Payable = NewType("Payable", Grosze)

#: An exact ratio — a rate multiplier, or the fraction of a share a refund
#: returns. A `Fraction` and never a float, so that compounding is exact.
Ratio = NewType("Ratio", Fraction)


def _not_a_bool(value: int, named: str) -> int:
    """Refuse the one `int` that is never an amount.

    `bool` is a subclass of `int`, so `grosze(True)` typechecks and means one
    grosz — a wrong answer rather than a loud one, and the only value in the
    type that is always a mistake. The same guard as the time module's, because
    it is the same hole in the same place.
    """

    invariant(not isinstance(value, bool), f"{named} from a bool: {value!r}")
    return value


def _round_half_away_from_zero(value: Fraction) -> int:
    """The one rounding rule in the module, stated once.

    **Half away from zero, on the magnitude.** Plain rounding is wrong here in
    two separate ways: Python's `round` is half-to-even, so 5,625 zł becomes
    5,62 and 5,635 becomes 5,64 — two neighbouring refunds rounded in opposite
    directions — and truncation toward zero would send negative halves one way
    while positive ones went the other, an asymmetry nobody intended in a figure
    whose sign is what distinguishes a charge from a refund.

    Rounding on the magnitude makes the result symmetric in sign, and means a
    player receives at most one grosz *more* than the exact half. Rounding in
    the player's favour is the defensible direction, and it is decided here
    rather than re-argued by each reader.
    """

    magnitude = abs(value)
    whole, remainder = divmod(magnitude.numerator, magnitude.denominator)
    if remainder * 2 >= magnitude.denominator:
        whole += 1
    return -whole if value < 0 else whole


def grosze(value: int) -> Grosze:
    """An amount of money in whole grosze; negative is money out."""

    return Grosze(_not_a_bool(value, "grosze"))


def zloty(value: int) -> Grosze:
    """A whole number of złoty, as grosze.

    Here so that a ninety-six-złoty rate is written `zloty(96)` rather than
    `Grosze(96 * 100)` at each call site — the second spelling reaches past the
    validating constructor, which is exactly what a brand is for. The same
    argument as `hours()` in the time module.
    """

    return grosze(_not_a_bool(value, "zloty") * GROSZE_PER_ZLOTY)


def ratio(numerator: int, denominator: int) -> Ratio:
    """An exact ratio: a rate multiplier, or the fraction a refund returns.

    **Two integers in, deliberately.** `Fraction` also accepts a float, and
    `Fraction(0.9)` is not nine tenths — it is 8106479329266893/9007199254740992,
    the double nearest to it, and it would round every price the same way as
    nine tenths for years before the one time it did not. Taking a numerator and
    a denominator means the float has nowhere to enter.

    Negative is refused. A negative multiplier turns a price into a credit and a
    negative refund fraction takes money off a refund; neither is a thing anyone
    means, and refusing it here names the offending value at the call site that
    wrote it rather than at the price three frames later.
    """

    invariant(denominator > 0, f"ratio with a denominator of {denominator}")
    invariant(numerator >= 0, f"ratio with a numerator of {numerator}")
    return Ratio(Fraction(_not_a_bool(numerator, "ratio"), denominator))


def percent(value: int) -> Ratio:
    """A ratio written as a percentage: `percent(90)` is a 10% discount.

    The spelling the domain actually uses — an off-peak multiplier, a refund
    band — so that `ratio(9, 10)` and `ratio(90, 100)` do not become two ways to
    write one number.
    """

    return ratio(_not_a_bool(value, "percent"), GROSZE_PER_ZLOTY)


def court_price(base: Grosze, *multipliers: Ratio) -> CourtPrice:
    """The **one** constructor for a court price: compound, then round once.

    Every multiplier applies to `base` before anything is rounded, and the
    single rounding is to whole złoty. Both halves are load-bearing:

    * compounding in exact rationals means 0,90 × 0,85 is 0,765 and not
      0,7649999999999999, so a two-multiplier price does not depend on the order
      the multipliers arrived in;
    * rounding **once**, at the court, is what makes the seat split exact
      afterwards. Round at the seat instead and four seats stop adding up to the
      court they are seats of.

    A price below zero is refused. Nothing in the domain sells a court for a
    negative figure, and the whole refinement chain below this point —
    `SeatShare`, `Payable` — is non-negative because of it, which is what makes
    *"a payable never exceeds its share"* a statement with a satisfiable
    meaning. `Grosze` itself stays signed: a refund is money, and money moves
    both ways.
    """

    product = Fraction(base)
    for multiplier in multipliers:
        product *= multiplier

    whole_zloty = _round_half_away_from_zero(product / GROSZE_PER_ZLOTY)
    invariant(whole_zloty >= 0, f"court price below zero: {whole_zloty} zł")
    return CourtPrice(zloty(whole_zloty))


def divide_among_players(price: CourtPrice, players: int) -> SeatShare:
    """The **one** constructor for a seat share, and it takes only a court price.

    `players` is the **sold** format — the number of players the court is sold
    for — never the current occupancy. A padel match with three players still
    divides by four, because the court costs what it costs. The caller reads the
    count from `SPORT_SPECS`; this takes the number rather than the `Sport` so
    that money stays independent of the sport registry.

    Two or four. Three raises, and the message names the count: no racket sport
    is sold in threes, so a three here is a bug upstream and rounding it away
    would hide the bug and lose a grosz at the same time.

    The whole-złoty law is asserted rather than assumed. It holds by
    construction for anything built through `court_price` — but `CourtPrice` is
    a `NewType` and erases at runtime, so `CourtPrice(Grosze(8650))` is
    reachable from a call site that ignores the convention. That is the one path
    to a split that loses money, and this is the guard on it.
    """

    invariant(not isinstance(players, bool), f"player count from a bool: {players!r}")
    invariant(players in SOLD_FORMATS, f"a court is not sold in {players}s")
    invariant(
        price % GROSZE_PER_ZLOTY == 0,
        f"court price is not a whole number of złoty: {price}",
    )

    # Exact, and provably so: `price` is a multiple of 100 and both 100 ÷ 2 and
    # 100 ÷ 4 are integers, so there is no remainder to decide what to do with.
    return SeatShare(grosze(price // players))


@final
@dataclass(frozen=True)
class NoCard:
    """No club card, so nothing comes off the share."""


@final
@dataclass(frozen=True)
class CardAllowance:
    """A club card carrying a capped allowance against one seat.

    Non-negative: a card that *adds* to what a player owes is not a card, and
    admitting one here is the only way a payable could exceed its share.
    """

    amount: Grosze

    def __post_init__(self) -> None:
        invariant(self.amount >= 0, f"card allowance below zero: {self.amount}")


@final
@dataclass(frozen=True)
class CardCoversShare:
    """A club card covering the whole seat, whatever the seat costs."""


#: A club's allowance against one seat: none, a capped amount, or the whole
#: share. Three `@final` members, so `exhaustive` can close a match over it and
#: a fourth kind of card fails the build at every place that does not handle it.
ClubCard: TypeAlias = NoCard | CardAllowance | CardCoversShare


def card_offset(share: SeatShare, card: ClubCard) -> Grosze:
    """How much of `share` the card takes off. **The one card rule.**

    **Capped at the share, so a card can never produce a credit.** A fifteen-
    złoty allowance against a thirteen-złoty share yields a thirteen-złoty
    offset and nothing more. The cap lives here, once, because the source
    documents this is derived from carried two implementations of it with
    different null checks — which is two places to change and one that gets
    changed.
    """

    match card:
        case NoCard():
            return grosze(0)
        case CardAllowance(amount):
            return grosze(min(amount, share))
        case CardCoversShare():
            return grosze(share)
        case _:
            exhaustive(card)


def payable_from(share: SeatShare, card: ClubCard) -> Payable:
    """What the player owes: the share, less the card offset.

    **Never negative, by construction rather than by clamping.** The offset is
    already capped at the share by `card_offset`, so there is no second rule
    here and no second place for the two to disagree — a clamp on the way out
    would be exactly that second place, silently correcting an offset that
    should never have been computed.
    """

    return Payable(subtract_grosze(share, card_offset(share, card)))


def apply_fraction(amount: Grosze, fraction: Ratio) -> Grosze:
    """A fraction of an amount, rounded half away from zero on the magnitude.

    This is the refund path: refunds are percentages of a share, and half of an
    odd share is not an integer. See `_round_half_away_from_zero` for why the
    direction is the one it is.
    """

    return grosze(_round_half_away_from_zero(amount * fraction))


def add_grosze(left: Grosze, right: Grosze) -> Grosze:
    """The sum of two amounts.

    The unit is in the name because the kernel is one flat import path: `add`
    is a name three future modules would each want, and `add(a, b)` at a call
    site says nothing about what it added. **Arithmetic loses the refinement** —
    a share plus a fee is a `Grosze`, not a `SeatShare` — which is deliberate:
    the refined types mean something specific and a sum is not it.
    """

    return grosze(left + right)


def subtract_grosze(left: Grosze, right: Grosze) -> Grosze:
    """The difference between two amounts; negative is legal."""

    return grosze(left - right)


def negate_grosze(amount: Grosze) -> Grosze:
    """The same magnitude, the other way: a charge becomes a refund."""

    return grosze(-amount)


def at_least_zero(amount: Grosze) -> Grosze:
    """`amount`, or zero if it is below it.

    For the places a floor is genuinely wanted. Note that `payable_from` is not
    one of them — it is non-negative because the offset is capped, and clamping
    there would paper over the arithmetic instead of getting it right.
    """

    return grosze(max(amount, 0))
