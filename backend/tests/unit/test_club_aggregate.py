"""The Club aggregate: three independent series, and a catalogue that remembers.

The scenario ADR-0077 was written for is the one to read first: a club sets
`maxHoldAge` to 48 h, four matches hold courts under it, and on Friday at 16:00
the club tightens it to 6 h. Staleness never latches, so those holds lapse
immediately and retroactively and four groups lose their Saturday — and **no
money necessarily moved**, so nothing about it reaches the ledger. This aggregate
is the only place that says the cap was ever 48 h.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.kernel import (
    CardAllowance,
    NoCard,
    Sport,
    hours,
    instant,
    minutes,
    percent,
    zloty,
)
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import (
    CategoryAlreadyRetired,
    CategoryNameAlreadyUsed,
    CategoryNotFound,
    CourtAlreadyRetired,
    CourtNotFound,
)
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
from app.shared.ids import new_uuid

MONDAY = instant(datetime(2026, 8, 31, 9, 0, tzinfo=timezone.utc))
FRIDAY_1600 = instant(datetime(2026, 9, 4, 16, 0, tzinfo=timezone.utc))
SATURDAY = instant(datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc))

ADDRESS = StreetAddress(
    line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
)
POINT = GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500"))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)


def a_club(**overrides) -> Club:
    defaults = dict(
        club_id=new_uuid(),
        name=ClubName("Zabłocie Sport"),
        address=ADDRESS,
        point=POINT,
        timezone=zone_named("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PAYOUT,
        at=MONDAY,
    )
    defaults.update(overrides)
    return Club.found(**defaults)


# --- the record -------------------------------------------------------------


def test_a_new_club_opens_both_of_its_club_wide_series():
    club = a_club()

    assert len(club.policy) == 1
    assert len(club.payout) == 1
    assert club.policy_now == ClubPolicy()
    assert club.payout_now == PAYOUT
    assert club.categories == []
    assert club.courts == []
    assert club.version == 0


def test_the_record_carries_pricing_address_point_and_a_zone():
    club = a_club(
        pricing=ClubPricing(
            price_multiplier=percent(90),
            slot_discount=percent(85),
            card_offsets={Sport.PADEL: CardAllowance(zloty(15))},
        )
    )

    assert club.address.city == "Kraków"
    assert club.point.latitude == Decimal("50.048100")
    assert str(club.timezone) == "Europe/Warsaw"
    assert club.pricing.price_multiplier == percent(90)
    assert club.pricing.card_for(Sport.PADEL) == CardAllowance(zloty(15))
    assert club.pricing.card_for(Sport.TENNIS) == NoCard()


def test_renaming_and_relocating_are_ordinary_writes_with_no_history():
    """*"A club renaming itself is not a dispute, and history on every field is
    how an audit trail becomes noise nobody reads."*"""

    club = a_club()

    club.rename(ClubName("Zabłocie Sport & Padel"))
    club.relocate(
        address=StreetAddress(
            line="ul. Nowa 1", city="Kraków", postal_code="30-702"
        ),
        point=GeoPoint(latitude=Decimal("50.05"), longitude=Decimal("19.96")),
        timezone=zone_named("Europe/Warsaw"),
    )

    assert club.name.value == "Zabłocie Sport & Padel"
    assert club.address.line == "ul. Nowa 1"
    assert len(club.policy) == 1, "renaming a club is not a policy version"


# --- series 1: the policy ---------------------------------------------------


def test_tightening_the_hold_cap_leaves_the_old_one_answerable():
    """ADR-0077's motivating scenario, end to end."""

    club = a_club(policy=ClubPolicy(max_hold_age=hours(48)))

    club.change_policy(ClubPolicy(max_hold_age=hours(6)), at=FRIDAY_1600)

    assert club.policy_now.max_hold_age == hours(6)
    assert club.policy.as_of(MONDAY).max_hold_age == hours(48)
    assert club.policy.as_of(FRIDAY_1600).max_hold_age == hours(6)
    assert len(club.policy) == 2


def test_a_policy_is_versioned_whole_so_one_query_answers_every_field():
    club = a_club(policy=ClubPolicy(max_hold_age=hours(48), join_cut=minutes(30)))

    club.change_policy(
        ClubPolicy(max_hold_age=hours(6), join_cut=minutes(60)), at=FRIDAY_1600
    )

    friday = club.policy.as_of(MONDAY)
    assert (friday.max_hold_age, friday.join_cut) == (hours(48), minutes(30))


def test_re_asserting_the_same_policy_still_opens_a_version():
    """The console authors a *version*; a club that re-asserted its policy on
    Friday said so on Friday, and collapsing that is the model deciding a human's
    action was not worth recording."""

    club = a_club()

    club.change_policy(ClubPolicy(), at=FRIDAY_1600)

    assert len(club.policy) == 2


def test_the_domain_reads_policy_as_of_now_and_never_a_fold():
    club = a_club(policy=ClubPolicy(max_hold_age=hours(48)))
    club.change_policy(ClubPolicy(max_hold_age=hours(6)), at=FRIDAY_1600)

    assert club.policy_now is club.policy.current
    assert club.policy_now.hold_policy().max_hold_age == hours(6)


# --- series 2: the payout destination ---------------------------------------


def test_the_payout_destination_is_its_own_series():
    """*"Ops tunes a hold cap, finance changes a bank account."* A routine policy
    tweak must not re-assert the bank details."""

    club = a_club()

    club.change_policy(ClubPolicy(max_hold_age=hours(6)), at=FRIDAY_1600)

    assert len(club.payout) == 1, "a policy change is not a bank change"

    club.change_payout_destination(
        PayoutDestination(
            account_holder="Zabłocie Sport", iban="PL27114020040000300201355387"
        ),
        at=SATURDAY,
    )

    assert len(club.payout) == 2
    assert len(club.policy) == 2, "a bank change is not a policy change"
    assert club.payout.as_of(MONDAY).iban.endswith("1219812874")


# --- series 3: the court catalogue ------------------------------------------


def a_padel_club() -> tuple[Club, object, object]:
    """ADR-0079's `ps`: one club, two padel categories, three courts.

    Seeded flat in v37 with a per-court multiplier on `ct3`, which said two
    things that cannot both be true — you may be moved onto a different court
    after your price was quoted, and it costs a different amount. Two categories
    is the shape that makes the quote honest.
    """

    club = a_club()
    mondo = club.add_category(
        category_id=new_uuid(),
        name=CategoryName("Padel · Mondo, indoor"),
        sport=Sport.PADEL,
        rate=zloty(120),
    )
    wall = club.add_category(
        category_id=new_uuid(),
        name=CategoryName("Padel · Wall, outdoor"),
        sport=Sport.PADEL,
        rate=zloty(108),
    )
    club.add_court(
        court_id=new_uuid(),
        category_id=mondo.id,
        label=CourtLabel("Court 1"),
        at=MONDAY,
    )
    club.add_court(
        court_id=new_uuid(),
        category_id=mondo.id,
        label=CourtLabel("Court 2"),
        at=MONDAY,
    )
    club.add_court(
        court_id=new_uuid(),
        category_id=wall.id,
        label=CourtLabel("Court 3"),
        at=MONDAY,
    )
    return club, mondo, wall


def test_the_price_attaches_to_the_category_and_never_to_a_court():
    club, mondo, wall = a_padel_club()

    assert mondo.rate == zloty(120)
    assert wall.rate == zloty(108)
    assert not hasattr(club.courts[0], "rate")
    assert not hasattr(club.courts[0], "price_multiplier")


def test_a_category_is_exactly_one_sport():
    club, mondo, _ = a_padel_club()

    assert mondo.sport is Sport.PADEL
    assert len(club.live_categories) == 2
    assert {c.sport for c in club.live_categories} == {Sport.PADEL}


def test_a_court_belongs_to_one_category_and_a_scan_is_by_category():
    """*"`pickCourt` gets its predicate"*: the free courts **of one category**."""

    club, mondo, wall = a_padel_club()

    assert len(club.courts_in(mondo.id)) == 2
    assert len(club.courts_in(wall.id)) == 1


def test_retiring_a_court_closes_its_row_and_keeps_the_history():
    club, mondo, _ = a_padel_club()
    court = club.courts_in(mondo.id)[0]

    club.retire_court(court.id, at=FRIDAY_1600)

    assert court.is_retired
    assert court.entry is None
    assert court.catalogue.as_of(MONDAY).label == CourtLabel("Court 1")
    assert len(club.courts_in(mondo.id)) == 1
    assert court in club.courts, "a court is retired, never deleted"


def test_moving_a_court_between_categories_opens_a_new_catalogue_row():
    club, mondo, wall = a_padel_club()
    court = club.courts_in(wall.id)[0]

    club.move_court(court.id, category_id=mondo.id, at=FRIDAY_1600)

    assert court.category_id == mondo.id
    assert court.catalogue.as_of(MONDAY).category_id == wall.id
    assert len(court.catalogue) == 2
    assert len(club.courts_in(mondo.id)) == 3


def test_retiring_a_category_retires_the_courts_still_in_it():
    """A court pointing at a retired category could be assigned out of a group
    nobody may sell — the one way this shape can lie."""

    club, mondo, _ = a_padel_club()

    club.retire_category(mondo.id, at=FRIDAY_1600)

    assert club.category(mondo.id).is_retired
    assert club.category(mondo.id) in club.categories, "retired, never deleted"
    assert club.courts_in(mondo.id) == ()
    assert len(club.live_courts) == 1


def test_a_category_with_no_courts_left_survives_and_can_never_be_assigned():
    """ADR-0079: correct rather than a bug — the ladder treats *no free court*
    and *no courts at all* identically, which is `inventoryLost` in both."""

    club, mondo, _ = a_padel_club()
    for court in club.courts_in(mondo.id):
        club.retire_court(court.id, at=FRIDAY_1600)

    assert not club.category(mondo.id).is_retired
    assert club.courts_in(mondo.id) == ()


def test_two_live_categories_may_not_share_a_name():
    club, _, _ = a_padel_club()

    with pytest.raises(CategoryNameAlreadyUsed):
        club.add_category(
            category_id=new_uuid(),
            name=CategoryName("Padel · Mondo, indoor"),
            sport=Sport.PADEL,
            rate=zloty(120),
        )


def test_a_retired_name_may_be_used_again():
    club, mondo, _ = a_padel_club()
    club.retire_category(mondo.id, at=FRIDAY_1600)

    reborn = club.add_category(
        category_id=new_uuid(),
        name=CategoryName("Padel · Mondo, indoor"),
        sport=Sport.PADEL,
        rate=zloty(130),
    )

    assert reborn.id != mondo.id
    assert len(club.categories) == 3


@pytest.mark.parametrize(
    "act",
    [
        lambda club, cat, court: club.add_court(
            court_id=new_uuid(),
            category_id=cat,
            label=CourtLabel("Court 9"),
            at=SATURDAY,
        ),
        lambda club, cat, court: club.move_court(
            court, category_id=cat, at=SATURDAY
        ),
        lambda club, cat, court: club.retire_category(cat, at=SATURDAY),
    ],
)
def test_a_retired_category_takes_nothing_further(act):
    club, mondo, wall = a_padel_club()
    court = club.courts_in(wall.id)[0]
    club.retire_category(mondo.id, at=FRIDAY_1600)

    with pytest.raises(CategoryAlreadyRetired):
        act(club, mondo.id, court.id)


def test_a_retired_court_takes_nothing_further():
    club, mondo, wall = a_padel_club()
    court = club.courts_in(wall.id)[0]
    club.retire_court(court.id, at=FRIDAY_1600)

    with pytest.raises(CourtAlreadyRetired):
        club.move_court(court.id, category_id=mondo.id, at=SATURDAY)
    with pytest.raises(CourtAlreadyRetired):
        club.retire_court(court.id, at=SATURDAY)


def test_an_unknown_court_or_category_is_a_refusal_rather_than_a_none():
    club, _, _ = a_padel_club()

    with pytest.raises(CategoryNotFound):
        club.category(new_uuid())
    with pytest.raises(CourtNotFound):
        club.court(new_uuid())


def test_the_three_series_move_independently():
    """The property the whole shape exists for: one series changing tells you
    nothing about the other two."""

    club, mondo, _ = a_padel_club()
    court = club.courts_in(mondo.id)[0]

    club.retire_court(court.id, at=FRIDAY_1600)

    assert len(club.policy) == 1
    assert len(club.payout) == 1
    assert len(court.catalogue) == 1 and court.is_retired
