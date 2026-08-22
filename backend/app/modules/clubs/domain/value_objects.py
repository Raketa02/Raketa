"""What a club is made of, validated where it is constructed.

Everything here belongs to the **unversioned** club record except ``ChangedBy``,
which rides on every row of every series, and ``PayoutDestination``, which is a
series of its own. ADR-0077's split: a club renaming itself is not a dispute,
and history on every field is how an audit trail becomes noise nobody reads.

Validation lives in the value object rather than in a use case, per
``backend/CLAUDE.md`` — so a bad point or an empty IANA name cannot be
constructed at all, and the seed catalog asks exactly the question an authoring
screen would.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping, final

from app.kernel import ClubCard, Grosze, NoCard, Ratio, Sport, Zone, percent

_NAME_RE = re.compile(r"^[^\x00-\x1f]{2,120}$")
_IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")

#: The actor written on a versioned row when no human identity exists. ADR-0077
#: fixes that the column ships from the first migration and reads this until a
#: club console and a club-staff identity exist: *"a sentinel that says 'system,
#: no human identity existed' is a true statement"*, where a nullable column
#: added later cannot tell *we did not know* from *nobody did it*.
SYSTEM_ACTOR = "system"


@final
@dataclass(frozen=True)
class ChangedBy:
    """Who changed a versioned row.

    A value object rather than a bare string so the column has a type the day a
    console starts writing a real actor into it, and so ``SYSTEM`` is one object
    every series shares rather than seven string literals.
    """

    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if not (1 <= len(v) <= 64):
            raise ValueError(f"invalid actor: {self.value!r}")
        object.__setattr__(self, "value", v)

    @property
    def is_system(self) -> bool:
        return self.value == SYSTEM_ACTOR


#: The only actor anything in ``app/`` writes in v1.
SYSTEM = ChangedBy(SYSTEM_ACTOR)


@final
@dataclass(frozen=True)
class ClubName:
    """What the club is called. The natural key ops enters it under.

    Unique across the platform, which is a data rule rather than a domain one —
    two venues genuinely called the same thing would need distinguishing before
    anybody could be told which one to walk to.
    """

    value: str

    def __post_init__(self) -> None:
        v = " ".join(self.value.split())
        if not _NAME_RE.match(v):
            raise ValueError(f"invalid club name: {self.value!r}")
        object.__setattr__(self, "value", v)


@final
@dataclass(frozen=True)
class StreetAddress:
    """Where the club's front door is, as a human would write it.

    A public venue, so — unlike a player's anchor, which ADR-0063 keeps coarse
    for privacy — there is nothing to blur and no consent to ask.
    """

    line: str
    city: str
    postal_code: str
    country: str = "PL"

    def __post_init__(self) -> None:
        for field_name in ("line", "city", "postal_code"):
            value = " ".join(getattr(self, field_name).split())
            if not (1 <= len(value) <= 160):
                raise ValueError(f"invalid club {field_name}: {value!r}")
            object.__setattr__(self, field_name, value)
        country = self.country.strip().upper()
        if not _COUNTRY_RE.match(country):
            raise ValueError(f"invalid country code: {self.country!r}")
        object.__setattr__(self, "country", country)


@final
@dataclass(frozen=True)
class GeoPoint:
    """The geocoded point, supplied by hand at authoring time.

    ADR-0078 refuses a lazy geocode outright: it would put a third-party call on
    the path that computes every distance on the busiest screen in the app, and
    fail as a blank distance rather than as an error somebody sees. There are
    nine clubs and a human is entering them.

    ``Decimal`` rather than ``float`` for the same reason ``Ratio`` is a
    ``Fraction``: what a human types is a decimal literal, and storing the
    nearest double back to it is a value nobody wrote. Six places is about
    eleven centimetres, which is finer than a front door.
    """

    latitude: Decimal
    longitude: Decimal

    def __post_init__(self) -> None:
        if not Decimal("-90") <= self.latitude <= Decimal("90"):
            raise ValueError(f"latitude out of range: {self.latitude}")
        if not Decimal("-180") <= self.longitude <= Decimal("180"):
            raise ValueError(f"longitude out of range: {self.longitude}")


def zone_named(name: str) -> Zone:
    """An IANA zone from its name, or a refusal naming the value.

    ``Zone`` is the kernel's export precisely so a club may *hold* a zone
    without importing ``zoneinfo`` — which ``app/kernel/time.py`` does exactly
    once for the whole of ``app/``, and a walk keeps that way. A constant
    ``Europe/Warsaw`` would be true today and is the trap ADR-0078 names: it is
    the one-market assumption buried somewhere far less visible than a header.
    """

    try:
        return Zone(name)
    except (KeyError, ValueError) as exc:  # ZoneInfoNotFoundError subclasses KeyError
        raise ValueError(f"not an IANA timezone: {name!r}") from exc


@final
@dataclass(frozen=True)
class ClubPricing:
    """The club's money levers. **Not policy** — see ADR-0078.

    ``price_multiplier`` (v37's ``pm``) multiplies the whole club's prices;
    ``slot_discount`` (``slotDisc``) is the off-peak rate. Neither is ever asked
    about in the past, because both are inputs to a price that is copied onto
    the match at quote time — which is why versioning them would open a policy
    version every time a club tweaks a discount.

    ``card_offsets`` is the standing per-sport club-card allowance
    (``cardOffset[sport]``). ADR-0078: *"a rate a club sets and a ledger of
    credits a player has accrued at that club are not one object"* — this is the
    rate. The per-player-per-club credit record ADR-0058 implies belongs to
    Money and is not modelled anywhere yet.

    A sport with no entry means no allowance, so the mapping is a default rather
    than a table that has to be complete.
    """

    price_multiplier: Ratio = percent(100)
    slot_discount: Ratio = percent(100)
    card_offsets: Mapping[Sport, ClubCard] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "card_offsets", MappingProxyType(dict(self.card_offsets))
        )

    def card_for(self, sport: Sport) -> ClubCard:
        return self.card_offsets.get(sport, NoCard())


@final
@dataclass(frozen=True)
class PayoutDestination:
    """Where the club is paid. Its own series, and the reason is fraud.

    ADR-0077 keeps it out of the policy row deliberately: *"ops tunes a hold
    cap, finance changes a bank account — and folding them means every routine
    tweak re-asserts the bank details, which is how a fraud-relevant field ends
    up buried in noise."*
    """

    account_holder: str
    iban: str

    def __post_init__(self) -> None:
        holder = " ".join(self.account_holder.split())
        if not (2 <= len(holder) <= 160):
            raise ValueError(f"invalid account holder: {self.account_holder!r}")
        object.__setattr__(self, "account_holder", holder)

        iban = "".join(self.iban.split()).upper()
        if not _IBAN_RE.match(iban):
            raise ValueError(f"invalid IBAN: {self.iban!r}")
        object.__setattr__(self, "iban", iban)


@final
@dataclass(frozen=True)
class CategoryName:
    """What a club calls one group of its own courts.

    Club-scoped and never compared across clubs — ADR-0079: *"anyone reaching
    for a shared vocabulary of categories is solving a problem no screen has."*
    """

    value: str

    def __post_init__(self) -> None:
        v = " ".join(self.value.split())
        if not _NAME_RE.match(v):
            raise ValueError(f"invalid category name: {self.value!r}")
        object.__setattr__(self, "value", v)


@final
@dataclass(frozen=True)
class CourtLabel:
    """What a court is called on the sign above it — *Court 2*.

    Printed to a player only once a court has been assigned, shortly before
    play (ADR-0035). Before that the card names the category, if anything.
    """

    value: str

    def __post_init__(self) -> None:
        v = " ".join(self.value.split())
        if not (1 <= len(v) <= 60):
            raise ValueError(f"invalid court label: {self.value!r}")
        object.__setattr__(self, "value", v)


def base_rate(amount: Grosze) -> Grosze:
    """A category's rate for one booked block, before the club's multipliers.

    Not a ``CourtPrice``: that brand means *after every multiplier, rounded once
    to whole złoty* (``app/kernel/money.py``), and this is the input to that
    rounding rather than its result. Quoting is
    ``court_price(base_rate, pricing.price_multiplier, ...)`` and belongs to
    whoever sells the block.
    """

    if amount < 0:
        raise ValueError(f"a category rate below zero: {amount}")
    return amount
