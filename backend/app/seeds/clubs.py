"""Which clubs exist, and what state each one is in.

Same rule as the account catalog next door: **a club is named for the state it
represents**, and the name is a checked claim rather than a comment. Nine
plausible venues would be one scenario — *a club that looks ordinary* — repeated
nine times; what breaks a screen, and what ADR-0077 was written for, is the
edges. So this is a list of them: a club that never holds a court speculatively,
one that tightened its cap and left the old one answerable, one whose price is
attached to two different categories of the same sport, one that retired a court,
one that retired a whole category, and one that changed its bank.

**The club's name *is* its slug**, so it cannot be called one thing and reachable
at another — the same reason an account's address is derived from its name. The
demo week (`Raketa02/Raketa#96`) is where real venues arrive; these are the
states the context has to be able to represent.

**A claim is about the meaning of the name, not about the numbers.** A rated
player's claim is checked against an engine that can be retuned; a club's state
is exactly what was authored, so checking the authored numbers against themselves
would be a tautology. What is worth checking is that the state the *name*
describes is still there — edit `club-that-never-holds` to a six-hour cap and the
seed stops and says so, rather than quietly handing a developer a club whose name
is a lie.

**Nothing here is a court reservation, a booking or a match.** Those contexts have
no aggregates (`Raketa02/Raketa#65`, `#66`), and inventing one is the scope creep
`test_the_seed_path_touches_only_the_contexts_that_exist` refuses.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from app.kernel import Grosze, Sport, hours, minutes, zloty
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
    zone_named,
)

#: Kraków, because the four seeded players are, and a distance a developer can
#: sanity-check beats one they cannot. The point is supplied by hand, which is
#: what ADR-0078 fixes: a lazy geocode puts a third-party call on the path that
#: computes every distance on the busiest screen in the app.
KRAKOW = GeoPoint(latitude=Decimal("50.049683"), longitude=Decimal("19.944544"))

#: One IANA zone, entered with the address rather than assumed. A constant
#: `Europe/Warsaw` in the *code* is the one-market assumption ADR-0078 refuses;
#: a constant in a seed catalog for a Kraków venue is a fact about that venue.
POLISH = "Europe/Warsaw"

#: A payout destination no bank will ever route: the IBAN check digits are wrong
#: on purpose, so a seed run pointed at the wrong database cannot pay a stranger.
#: The same argument as the accounts' reserved TLD, one context over.
UNROUTABLE_IBAN = "PL00000000000000000000000000"
SECOND_UNROUTABLE_IBAN = "PL00111122223333444455556666"


@dataclass(frozen=True)
class ClubClaim:
    """What a club's name promises, and how to tell whether it still holds."""

    promise: str
    holds: Callable[[Club], bool]


@dataclass(frozen=True)
class SeedCourt:
    label: str
    retired: bool = False


@dataclass(frozen=True)
class SeedCategory:
    name: str
    sport: Sport
    rate: Grosze
    courts: tuple[SeedCourt, ...] = ()
    retired: bool = False


@dataclass(frozen=True)
class SeedClub:
    """One deterministic club: what it is called, and what state it is in.

    ``policies`` and ``payouts`` are the **whole series**, oldest first. The
    first entry is what the club was founded with and the rest are changes, so a
    club with two policies is one that has changed its policy once — which is
    what makes the closed row exist to be read.
    """

    slug: str
    description: str
    claim: ClubClaim
    policies: tuple[ClubPolicy, ...]
    payouts: tuple[PayoutDestination, ...] = ()
    categories: tuple[SeedCategory, ...] = ()
    pricing: ClubPricing = ClubPricing()
    address_line: str = "Rynek Główny 1"
    city: str = "Kraków"
    postal_code: str = "31-042"
    timezone: str = POLISH

    @property
    def name(self) -> ClubName:
        return ClubName(self.slug)

    @property
    def address(self) -> StreetAddress:
        return StreetAddress(
            line=self.address_line, city=self.city, postal_code=self.postal_code
        )


def _payouts(*ibans: str) -> tuple[PayoutDestination, ...]:
    return tuple(
        PayoutDestination(account_holder="Raketa seed club", iban=iban)
        for iban in ibans
    )


NEVER_HOLDS = SeedClub(
    slug="club-that-never-holds",
    description=(
        "A club whose `maxHoldAge` is 0 — *this club does not hold "
        "speculatively at all*, said plainly rather than performed by a hold "
        "that dies an hour after it is granted. The one value no platform floor "
        "is allowed to raise."
    ),
    claim=ClubClaim(
        promise="a club that never holds a court speculatively",
        holds=lambda club: club.policy_now.holds_speculatively is False,
    ),
    policies=(ClubPolicy(max_hold_age=minutes(0)),),
    payouts=_payouts(UNROUTABLE_IBAN),
    categories=(
        SeedCategory(
            name="Padel · indoor",
            sport=Sport.PADEL,
            rate=zloty(120),
            courts=(SeedCourt("Court 1"),),
        ),
    ),
)

TIGHTENED_ITS_CAP = SeedClub(
    slug="club-that-tightened-its-cap",
    description=(
        "ADR-0077's motivating scenario, standing: 48 h on the day it was "
        "entered, 6 h now. Staleness never latches, so the change lapsed every "
        "hold under it retroactively — and no money moved, so nothing about it "
        "reaches the ledger. This club's policy series is the only record that "
        "the cap was ever 48 h."
    ),
    claim=ClubClaim(
        promise="a club that tightened its hold cap and left the old one readable",
        holds=lambda club: (
            len(club.policy) >= 2
            and club.policy_now.max_hold_age is not None
            and club.policy.versions[0].value.max_hold_age is not None
            and club.policy_now.max_hold_age
            < club.policy.versions[0].value.max_hold_age
        ),
    ),
    policies=(
        ClubPolicy(max_hold_age=hours(48)),
        ClubPolicy(max_hold_age=hours(6)),
    ),
    payouts=_payouts(UNROUTABLE_IBAN),
    categories=(
        SeedCategory(
            name="Tennis · outdoor",
            sport=Sport.TENNIS,
            rate=zloty(90),
            courts=(SeedCourt("Court 1"), SeedCourt("Court 2")),
        ),
    ),
)

TWO_PADEL_CATEGORIES = SeedClub(
    slug="club-with-two-padel-categories",
    description=(
        "ADR-0079's `ps`, seeded the way the model requires: two padel "
        "categories at two prices rather than three flat courts with a "
        "per-court multiplier. The price attaches to the category, so a court "
        "swapped in after the quote costs what was quoted."
    ),
    claim=ClubClaim(
        promise="two live categories of one sport at two different prices",
        holds=lambda club: (
            len(club.live_categories) == 2
            and len({c.sport for c in club.live_categories}) == 1
            and len({c.rate for c in club.live_categories}) == 2
        ),
    ),
    policies=(ClubPolicy(),),
    payouts=_payouts(UNROUTABLE_IBAN),
    categories=(
        SeedCategory(
            name="Padel · Mondo, indoor",
            sport=Sport.PADEL,
            rate=zloty(120),
            courts=(SeedCourt("Court 1"), SeedCourt("Court 2")),
        ),
        SeedCategory(
            name="Padel · Wall, outdoor",
            sport=Sport.PADEL,
            rate=zloty(108),
            courts=(SeedCourt("Court 3"),),
        ),
    ),
)

RETIRED_A_COURT = SeedClub(
    slug="club-that-retired-a-court",
    description=(
        "A court taken out of the catalogue: its series has a closed row and no "
        "open one, so it is gone from availability and still named by every "
        "reservation that claimed it. `inventoryLost` is terminal, and this is "
        "the record that says whether nothing was free because everything was "
        "booked or because the club retired the court."
    ),
    claim=ClubClaim(
        promise="a retired court whose history is still readable",
        holds=lambda club: (
            any(court.is_retired for court in club.courts)
            and all(
                len(court.catalogue) >= 1
                for court in club.courts
                if court.is_retired
            )
            and len(club.live_courts) >= 1
        ),
    ),
    policies=(ClubPolicy(),),
    payouts=_payouts(UNROUTABLE_IBAN),
    categories=(
        SeedCategory(
            name="Squash · glass back",
            sport=Sport.SQUASH,
            rate=zloty(60),
            courts=(SeedCourt("Court 1"), SeedCourt("Court 2", retired=True)),
        ),
    ),
)

RETIRED_A_CATEGORY = SeedClub(
    slug="club-that-retired-a-category",
    description=(
        "A whole category retired, and the courts in it with it — retired, "
        "never deleted, so a past reservation still resolves. The live "
        "catalogue is smaller than the catalogue."
    ),
    claim=ClubClaim(
        promise="a retired category that is still in the catalogue",
        holds=lambda club: (
            any(category.is_retired for category in club.categories)
            and len(club.live_categories) < len(club.categories)
            and all(
                club.courts_in(category.id) == ()
                for category in club.categories
                if category.is_retired
            )
        ),
    ),
    policies=(ClubPolicy(),),
    payouts=_payouts(UNROUTABLE_IBAN),
    categories=(
        SeedCategory(
            name="Badminton · hall A",
            sport=Sport.BADMINTON,
            rate=zloty(50),
            courts=(SeedCourt("Court 1"),),
        ),
        SeedCategory(
            name="Badminton · hall B",
            sport=Sport.BADMINTON,
            rate=zloty(45),
            courts=(SeedCourt("Court 2"),),
            retired=True,
        ),
    ),
)

CHANGED_ITS_BANK = SeedClub(
    slug="club-that-changed-its-bank",
    description=(
        "Two payout destinations and one policy — the series that exists "
        "because a bank change is fraud-relevant and must not be buried under "
        "routine tuning. The only account where a closed payout row exists."
    ),
    claim=ClubClaim(
        promise="a club that changed its bank without changing its policy",
        holds=lambda club: len(club.payout) >= 2 and len(club.policy) == 1,
    ),
    policies=(ClubPolicy(),),
    payouts=_payouts(UNROUTABLE_IBAN, SECOND_UNROUTABLE_IBAN),
    categories=(
        SeedCategory(
            name="Padel · indoor",
            sport=Sport.PADEL,
            rate=zloty(130),
            courts=(SeedCourt("Court 1"),),
        ),
    ),
)

#: Every club this system creates, in the order a run walks them: simplest first,
#: so a run interrupted half way leaves the plain states done.
CLUBS: tuple[SeedClub, ...] = (
    NEVER_HOLDS,
    TWO_PADEL_CATEGORIES,
    RETIRED_A_COURT,
    RETIRED_A_CATEGORY,
    TIGHTENED_ITS_CAP,
    CHANGED_ITS_BANK,
)


def _refuse_an_impossible_catalog() -> None:
    """Fail at import rather than part-way through a run.

    The value objects are the domain's own, so this asks the exact question the
    use cases would — a name, an address, a zone or an IBAN the context would
    reject cannot sit here waiting to break a run that has already written half
    of its clubs.
    """

    seen: set[str] = set()
    for club in CLUBS:
        ClubName(club.slug)
        StreetAddress(
            line=club.address_line,
            city=club.city,
            postal_code=club.postal_code,
        )
        zone_named(club.timezone)
        if club.slug in seen:
            raise RuntimeError(f"two seed clubs are named '{club.slug}'")
        seen.add(club.slug)

        if not club.policies:
            raise RuntimeError(
                f"'{club.slug}' has no policy: a club that exists has one in force"
            )
        if not club.payouts:
            raise RuntimeError(
                f"'{club.slug}' has no payout destination: a club that exists "
                f"can be paid"
            )
        for destination in club.payouts:
            PayoutDestination(
                account_holder=destination.account_holder, iban=destination.iban
            )

        names: set[str] = set()
        labels: set[str] = set()
        for category in club.categories:
            CategoryName(category.name)
            if category.name in names:
                raise RuntimeError(
                    f"'{club.slug}' has two categories called '{category.name}'"
                )
            names.add(category.name)
            for court in category.courts:
                CourtLabel(court.label)
                if court.label in labels:
                    raise RuntimeError(
                        f"'{club.slug}' has two courts called '{court.label}': "
                        f"a label is how a seeded court is found again"
                    )
                labels.add(court.label)


_refuse_an_impossible_catalog()
