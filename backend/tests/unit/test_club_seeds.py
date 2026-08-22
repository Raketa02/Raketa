"""The club catalog: named states, checked names, and a re-run that writes nothing.

The account catalog's rule, one context over. Three claims, each failing
differently.

1. **Every club is named for a state**, and its name is its natural key, so it
   cannot be called one thing and reachable at another.
2. **A name that stops matching its state stops the seed** — checked against the
   *stored* club on every run, including a run that created nothing, because a
   club seeded a month ago against a catalog that has since been edited is
   exactly the case a check on the fresh result would miss.
3. **The catalog covers the edges the context exists to represent**: the three
   series each with history, `maxHoldAge = 0`, a category as the priced unit, and
   retirement without deletion.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.bootstrap.composition import build_club_repository
from app.kernel import Sport, hours, minutes
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import ClubName, PayoutDestination
from app.seeds import clubs as club_catalog
from app.seeds.clubs import (
    CLUBS,
    NEVER_HOLDS,
    TIGHTENED_ITS_CAP,
    SECOND_UNROUTABLE_IBAN,
    UNROUTABLE_IBAN,
    ClubClaim,
    SeedCategory,
    SeedClub,
    SeedCourt,
)
from app.seeds.runner import SeedFailed, seed


# --- the catalog ------------------------------------------------------------


def test_every_club_is_named_for_its_state():
    for club in CLUBS:
        assert club.name == ClubName(club.slug)
        assert club.description
        assert club.claim.promise


def test_no_two_clubs_share_a_name():
    assert len({club.slug for club in CLUBS}) == len(CLUBS)


def test_every_club_has_a_policy_and_a_payout_in_force():
    """A club that exists has a policy the ladder can read and an account it can
    be paid into. Neither series may start empty."""

    for club in CLUBS:
        assert club.policies
        assert club.payouts


def test_no_seeded_payout_could_ever_reach_a_real_bank():
    """The reserved-TLD argument, one context over: a seed run pointed at the
    wrong database must not be able to pay a stranger."""

    for club in CLUBS:
        for destination in club.payouts:
            assert destination.iban in {UNROUTABLE_IBAN, SECOND_UNROUTABLE_IBAN}
            assert destination.iban[2:4] == "00", "the check digits must be invalid"


def test_the_catalog_covers_the_edges_this_context_exists_for():
    """Each of ADR-0077's three series has at least one club with history in it,
    and ADR-0078's three-valued hold cap has the value that is easiest to lose."""

    assert any(len(club.policies) > 1 for club in CLUBS), "no policy history"
    assert any(len(club.payouts) > 1 for club in CLUBS), "no payout history"
    assert any(
        court.retired
        for club in CLUBS
        for category in club.categories
        for court in category.courts
    ), "no retired court, so the catalogue series never carries a closed row"
    assert any(
        category.retired for club in CLUBS for category in club.categories
    ), "no retired category"
    assert any(
        policy.max_hold_age == 0 for club in CLUBS for policy in club.policies
    ), "no club that declines to hold speculatively"
    assert any(
        len({category.rate for category in club.categories}) > 1
        and len({category.sport for category in club.categories}) == 1
        for club in CLUBS
    ), "no club where one sport is priced as two categories"


def test_every_sport_appears_somewhere_in_the_catalogue():
    """Four sports, so a screen filtered to any of them has a club behind it."""

    sports = {
        category.sport for club in CLUBS for category in club.categories
    }
    assert sports == set(Sport)


def test_a_court_label_is_unique_within_a_club():
    """The label is how a seeded court is found again on a second run — two
    courts sharing one would make a re-run add a third."""

    for club in CLUBS:
        labels = [
            court.label
            for category in club.categories
            for court in category.courts
        ]
        assert len(labels) == len(set(labels)), club.slug


@pytest.mark.parametrize(
    "broken, complaint",
    [
        (
            lambda: replace(NEVER_HOLDS, policies=()),
            "has no policy",
        ),
        (
            lambda: replace(NEVER_HOLDS, payouts=()),
            "has no payout destination",
        ),
        (
            lambda: replace(
                NEVER_HOLDS,
                categories=(
                    SeedCategory("Hall A", Sport.PADEL, minutes(1), (SeedCourt("C1"),)),
                    SeedCategory("Hall A", Sport.PADEL, minutes(1)),
                ),
            ),
            "two categories called",
        ),
        (
            lambda: replace(
                NEVER_HOLDS,
                categories=(
                    SeedCategory("Hall A", Sport.PADEL, minutes(1), (SeedCourt("C1"),)),
                    SeedCategory("Hall B", Sport.PADEL, minutes(1), (SeedCourt("C1"),)),
                ),
            ),
            "two courts called",
        ),
    ],
)
def test_an_impossible_catalog_is_refused_at_import(monkeypatch, broken, complaint):
    """The refusals fire before a session is opened. Halfway through a run is the
    one place a bad entry must not be found."""

    monkeypatch.setattr(club_catalog, "CLUBS", (broken(),))
    with pytest.raises(RuntimeError, match=complaint):
        club_catalog._refuse_an_impossible_catalog()


def test_two_clubs_with_one_name_are_refused_at_import(monkeypatch):
    monkeypatch.setattr(club_catalog, "CLUBS", (NEVER_HOLDS, NEVER_HOLDS))
    with pytest.raises(RuntimeError, match="two seed clubs are named"):
        club_catalog._refuse_an_impossible_catalog()


# --- the run ----------------------------------------------------------------


async def _seeded_clubs(session_factory):
    async with session_factory() as session:
        return (await seed(session)).clubs


def _only_the_club_catalog(monkeypatch) -> None:
    """Narrow the court claims away while the club catalog is under test.

    The catalogs are coupled on purpose: a court claim names a club's category,
    and the runner refuses a claim whose club is missing rather than skipping it
    — a half-edited catalog is a failure, not a smaller run. So a test that
    replaces `CLUBS` with one club has, by construction, deleted the venue a
    seeded claim names.
    """

    monkeypatch.setattr("app.seeds.runner.RESERVATIONS", ())



async def test_every_club_reaches_the_state_its_name_promises(session_factory):
    """The claims, met by the use cases the API actually serves. This is what
    makes the names mean something."""

    seeded = await _seeded_clubs(session_factory)

    assert [entry.club.slug for entry in seeded] == [club.slug for club in CLUBS]
    assert all(entry.created for entry in seeded)


async def test_the_hold_caps_land_where_the_names_say(session_factory):
    """Read back through the repository, not from what the run returned."""

    await _seeded_clubs(session_factory)

    async with session_factory() as session:
        repository = build_club_repository(session)
        never = await repository.get_by_name(ClubName("club-that-never-holds"))
        tightened = await repository.get_by_name(
            ClubName("club-that-tightened-its-cap")
        )

    assert never is not None and tightened is not None
    assert never.policy_now.max_hold_age == 0
    assert never.policy_now.holds_speculatively is False
    assert len(tightened.policy) == 2
    assert tightened.policy.versions[0].value.max_hold_age == hours(48)
    assert tightened.policy_now.max_hold_age == hours(6)
    assert tightened.policy.versions[0].valid_to is not None


async def test_the_retired_court_and_category_survive_as_history(session_factory):
    await _seeded_clubs(session_factory)

    async with session_factory() as session:
        repository = build_club_repository(session)
        court_club = await repository.get_by_name(
            ClubName("club-that-retired-a-court")
        )
        category_club = await repository.get_by_name(
            ClubName("club-that-retired-a-category")
        )

    assert court_club is not None and category_club is not None
    retired = [court for court in court_club.courts if court.is_retired]
    assert len(retired) == 1
    assert retired[0].catalogue.versions[0].value.label.value == "Court 2"
    assert len(court_club.live_courts) == 1

    assert len(category_club.categories) == 2
    assert len(category_club.live_categories) == 1
    assert len(category_club.live_courts) == 1


async def test_a_second_run_writes_nothing_further(session_factory):
    """Every step is a question asked of what is stored, so a re-run leaves the
    same clubs with the same ids and the same number of rows in every series."""

    async with session_factory() as session:
        first = (await seed(session)).clubs
    async with session_factory() as session:
        second = (await seed(session)).clubs

    assert [entry.club_id for entry in first] == [entry.club_id for entry in second]
    assert all(entry.created for entry in first)
    assert not any(entry.created for entry in second)

    async with session_factory() as session:
        repository = build_club_repository(session)
        stored = await repository.find_all()

    assert len(stored) == len(CLUBS)
    tightened = next(
        club for club in stored if club.name.value == "club-that-tightened-its-cap"
    )
    assert len(tightened.policy) == 2, "a re-run opened another policy version"
    banked = next(
        club for club in stored if club.name.value == "club-that-changed-its-bank"
    )
    assert len(banked.payout) == 2, "a re-run opened another payout version"
    assert sum(len(club.courts) for club in stored) == sum(
        len(category.courts) for club in CLUBS for category in club.categories
    )


async def test_a_name_that_stops_matching_its_state_stops_the_seed(
    session_factory, monkeypatch
):
    """The failure this catalog is built to refuse: a club whose name is a lie.

    `club-that-never-holds` is edited to a six-hour cap. Nothing about the
    screens it is developed against would look wrong — which is why the seed
    stops instead of quietly renaming it.
    """

    lying = replace(
        NEVER_HOLDS, policies=(ClubPolicy(max_hold_age=hours(6)),)
    )
    monkeypatch.setattr("app.seeds.runner.CLUBS", (lying,))
    _only_the_club_catalog(monkeypatch)

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="never holds a court speculatively"):
            await seed(session)


async def test_a_claim_is_checked_on_a_run_that_creates_nothing(
    session_factory, monkeypatch
):
    """The load-bearing half. A club seeded last month against a catalog that has
    since been edited is caught by the next `make seed`, not by a developer
    wondering why the screen looks wrong."""

    async with session_factory() as session:
        await seed(session)

    impossible = SeedClub(
        slug="club-that-never-holds",
        description=NEVER_HOLDS.description,
        claim=ClubClaim(promise="a club with no courts at all", holds=lambda c: False),
        policies=NEVER_HOLDS.policies,
        payouts=NEVER_HOLDS.payouts,
    )
    monkeypatch.setattr("app.seeds.runner.CLUBS", (impossible,))
    _only_the_club_catalog(monkeypatch)

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="no courts at all"):
            await seed(session)


async def test_an_interrupted_club_is_finished_rather_than_duplicated(
    session_factory, monkeypatch
):
    """A run that died between two versions of one series resumes from where it
    stopped — the catalog declares the whole series, so *how far along* is a
    length comparison."""

    half_done = replace(
        TIGHTENED_ITS_CAP,
        policies=TIGHTENED_ITS_CAP.policies[:1],
        payouts=TIGHTENED_ITS_CAP.payouts,
        claim=ClubClaim(promise="a club part-way through", holds=lambda c: True),
    )
    monkeypatch.setattr("app.seeds.runner.CLUBS", (half_done,))
    _only_the_club_catalog(monkeypatch)
    async with session_factory() as session:
        await seed(session)

    monkeypatch.setattr("app.seeds.runner.CLUBS", (TIGHTENED_ITS_CAP,))
    async with session_factory() as session:
        finished = (await seed(session)).clubs

    assert not finished[0].created
    async with session_factory() as session:
        club = await build_club_repository(session).get_by_name(
            ClubName("club-that-tightened-its-cap")
        )
    assert club is not None
    assert len(club.policy) == 2
    assert club.policy_now.max_hold_age == hours(6)


async def test_every_versioned_row_a_seed_writes_reads_system(session_factory):
    """`changedBy` ships from the first migration and reads *system* in v1."""

    await _seeded_clubs(session_factory)

    async with session_factory() as session:
        for club in await build_club_repository(session).find_all():
            assert all(version.changed_by.is_system for version in club.policy)
            assert all(version.changed_by.is_system for version in club.payout)
            for court in club.courts:
                assert all(
                    version.changed_by.is_system for version in court.catalogue
                )


async def test_a_seeded_club_is_paid_where_its_catalog_says(session_factory):
    await _seeded_clubs(session_factory)

    async with session_factory() as session:
        club = await build_club_repository(session).get_by_name(
            ClubName("club-that-changed-its-bank")
        )

    assert club is not None
    assert club.payout_now == PayoutDestination(
        account_holder="Raketa seed club", iban=SECOND_UNROUTABLE_IBAN
    )
    assert club.payout.versions[0].value.iban == UNROUTABLE_IBAN
    assert len(club.policy) == 1, "a bank change is not a policy change"
