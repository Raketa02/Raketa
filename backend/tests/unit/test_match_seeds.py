"""The seeded matches: named for a situation, and the kernel is what checks it.

Same three claims the three catalogs beside it make, one context over — and one
this context alone can make.

1. **The catalog is coherent before a session is opened** — every match names a
   club and a category that exist, seats no more players than the catalog has,
   and is not an open match with seats to open.
2. **The run is idempotent**, and the second run creates nothing.
3. **A name that no longer matches its state stops the run**, checked against the
   *stored* match on every run, including one that created nothing.

And the one this context adds: **the name is checked by the ladder itself.**
Every other catalog checks a property somebody wrote down. A match's state is
*derived*, so the scenario names a `Situation` and the runner asks
`kernel.situation`. Retune a threshold and the seed stops and says which
account's screen just moved — which is the strongest available form of *an
account whose name lies is worse than one that is missing*.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_event_publisher, build_match_repository
from app.kernel import MatchKind, Situation, situation
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchORM,
    MatchSeatORM,
    MatchVacancyORM,
)
from app.seeds.catalog import ACCOUNTS
from app.seeds.clubs import CLUBS
from app.seeds.matches import MATCHES, SeedMatch, SituationClaim
from app.seeds.runner import SeedFailed, seed


def _only_the_match_catalog(monkeypatch, matches) -> None:
    monkeypatch.setattr("app.seeds.runner.MATCHES", matches)


async def count(session_factory, model):
    async with session_factory() as session:
        return (
            await session.execute(select(func.count()).select_from(model))
        ).scalar_one()


# --- 1. the catalog is coherent before anything is written ------------------


def test_there_is_a_catalog_to_walk():
    assert len(MATCHES) >= 5


def test_every_slug_is_distinct():
    assert len({match.slug for match in MATCHES}) == len(MATCHES)


def test_every_situation_the_catalog_names_is_distinct():
    """Seven matches saying the same thing would be one scenario seven times."""

    named = [match.claim.situation for match in MATCHES]

    assert len(set(named)) == len(named)


def test_every_match_names_a_club_the_club_catalog_holds():
    slugs = {club.slug for club in CLUBS}

    for match in MATCHES:
        assert match.club_slug in slugs, match.slug


def test_every_match_names_a_category_that_club_has():
    for match in MATCHES:
        club = next(one for one in CLUBS if one.slug == match.club_slug)
        names = {category.name for category in club.categories}
        assert match.category in names, match.slug


def test_every_match_names_the_sport_its_category_is_for():
    """A padel match in a squash category is a match that can never get a court."""

    for match in MATCHES:
        club = next(one for one in CLUBS if one.slug == match.club_slug)
        category = next(
            one for one in club.categories if one.name == match.category
        )
        assert category.sport is match.sport, match.slug


def test_no_match_seats_more_players_than_the_account_catalog_holds():
    for match in MATCHES:
        assert match.taken <= len(ACCOUNTS), match.slug


def test_no_match_seats_more_players_than_the_sport_is_sold_for():
    from app.kernel import SPORT_SPECS

    for match in MATCHES:
        assert match.taken <= SPORT_SPECS[match.sport].players, match.slug


def test_every_instant_is_absolute_and_not_relative_to_now():
    """A situation is a function of the record *and* the clock, so a claim
    computed at run time would be a different question tomorrow."""

    for match in MATCHES:
        assert match.start.year == 2026
        assert match.claim.resolved_at.year == 2026
        assert match.posted_at.year == 2026


def test_a_paid_seat_with_nobody_on_it_is_refused_by_the_catalog():
    with pytest.raises(ValueError, match="a paid seat with nobody on it"):
        replace(MATCHES[0], taken=1, paid=2)


def test_a_hole_with_no_instant_is_refused_by_the_catalog():
    with pytest.raises(ValueError, match="does not say when"):
        replace(MATCHES[0], taken=1, vacated=1, vacated_at=None)


def test_an_open_match_with_seats_to_open_is_refused_by_the_catalog():
    with pytest.raises(ValueError, match="that is what open means"):
        replace(MATCHES[0], kind=MatchKind.OPEN, open_seats=2)


def test_a_cancellation_with_no_moment_is_refused_by_the_catalog():
    with pytest.raises(ValueError, match="a moment as well as a cause"):
        replace(MATCHES[0], cancelled="club", cancelled_at=None)


# --- 2. the run, and the second run -----------------------------------------


async def test_the_catalog_is_written_and_a_second_run_writes_nothing(
    session_factory,
):
    async with session_factory() as session:
        first = (await seed(session)).matches

    assert len(first) == len(MATCHES)
    assert all(entry.created for entry in first)
    written = await count(session_factory, MatchORM)
    seats = await count(session_factory, MatchSeatORM)

    async with session_factory() as session:
        second = (await seed(session)).matches

    assert not any(entry.created for entry in second)
    assert [entry.match_id for entry in second] == [
        entry.match_id for entry in first
    ]
    assert await count(session_factory, MatchORM) == written
    assert await count(session_factory, MatchSeatORM) == seats


async def test_every_seeded_match_resolves_to_the_situation_it_is_named_for(
    session_factory,
):
    """The catalog's whole claim, asked of the stored record through the ladder."""

    async with session_factory() as session:
        seeded = (await seed(session)).matches

    async with session_factory() as session:
        repository = build_match_repository(
            session, events=build_event_publisher(session)
        )
        for entry in seeded:
            stored = await repository.get(entry.match_id)
            assert stored is not None
            assert (
                situation(
                    stored.as_record(), None, entry.match.claim.resolved_at
                )
                is entry.match.claim.situation
            )


async def test_the_seeded_week_writes_the_instants_and_not_the_wall_clock(
    session_factory,
):
    """A match *is* its clock. Left on the wall clock, `committed_at` would say
    *the day somebody ran make seed* and the name would be about that day."""

    async with session_factory() as session:
        seeded = (await seed(session)).matches

    committed = next(
        entry for entry in seeded if entry.match.slug == "match-that-lost-a-player"
    )
    async with session_factory() as session:
        repository = build_match_repository(
            session, events=build_event_publisher(session)
        )
        stored = await repository.get(committed.match_id)

    assert stored is not None
    assert stored.created == committed.match.posted_at
    assert stored.committed_at == committed.match.joined_at
    assert stored.open_vacancies[0].vacated_at == committed.match.vacated_at


async def test_the_hole_a_departure_left_is_a_row_of_its_own(session_factory):
    async with session_factory() as session:
        seeded = (await seed(session)).matches

    holes = sum(entry.match.vacated for entry in seeded)

    assert holes == 1
    assert await count(session_factory, MatchVacancyORM) == holes


async def test_the_seeded_accounts_fill_the_seats_in_catalog_order(
    session_factory,
):
    """Signing in as the first seeded account shows a developer her own matches."""

    async with session_factory() as session:
        run = await seed(session)

    first_player = run.accounts[0].player_id
    async with session_factory() as session:
        repository = build_match_repository(
            session, events=build_event_publisher(session)
        )
        held = [
            entry.match.slug
            for entry in run.matches
            if (stored := await repository.get(entry.match_id)) is not None
            and stored.seat_of(first_player) is not None
        ]

    # Every scenario that seats anybody seats her first, except the one whose
    # only seated player has since left it.
    assert "match-with-a-seat-held-and-unpaid" in held
    assert "match-that-lost-a-player" not in held


async def test_no_seeded_match_holds_a_court(session_factory):
    """Granting a hold is the ladder's decision (`Raketa02/Raketa#71`), and
    seeding one here would decide what the ladder decides."""

    async with session_factory() as session:
        run = await seed(session)
        repository = build_match_repository(
            session, events=build_event_publisher(session)
        )
        for entry in run.matches:
            stored = await repository.get(entry.match_id)
            assert stored is not None
            assert stored.held_since is None
            assert stored.released_at is None


# --- 3. a name that lies stops the run --------------------------------------


async def test_a_match_whose_name_no_longer_matches_stops_the_run(
    session_factory, monkeypatch
):
    lying = replace(
        MATCHES[0],
        claim=replace(
            MATCHES[0].claim,
            promise="a match that has been played",
            situation=Situation.COMPLETED,
        ),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="a match that has been played"):
            await seed(session)


async def test_the_claim_is_checked_on_a_run_that_creates_nothing(
    session_factory, monkeypatch
):
    """The load-bearing half. A match seeded last month against a ladder that
    has since had a rung reordered is caught by the next `make seed`, not by a
    developer wondering why a card says something else."""

    async with session_factory() as session:
        await seed(session)

    impossible: SeedMatch = replace(
        MATCHES[0],
        claim=SituationClaim(
            promise="a match nobody could ever reach",
            situation=Situation.READY,
            resolved_at=MATCHES[0].claim.resolved_at,
        ),
    )
    _only_the_match_catalog(monkeypatch, (impossible,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="nobody could ever reach"):
            await seed(session)


async def test_the_refusal_names_both_situations(session_factory, monkeypatch):
    """A seed that stops without saying what it found is a seed nobody can fix."""

    lying = replace(
        MATCHES[0],
        claim=replace(MATCHES[0].claim, situation=Situation.COMPLETED),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed) as raised:
            await seed(session)

    assert Situation.COMPLETED.value in str(raised.value)
    assert MATCHES[0].claim.situation.value in str(raised.value)


async def test_a_match_naming_a_club_the_catalog_lost_stops_the_run(
    session_factory, monkeypatch
):
    orphan = replace(MATCHES[0], club_slug="club-that-does-not-exist")
    _only_the_match_catalog(monkeypatch, (orphan,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="half-edited"):
            await seed(session)


async def test_a_match_naming_a_category_the_club_does_not_have_stops_the_run(
    session_factory, monkeypatch
):
    orphan = replace(MATCHES[0], category="Curling · sheet 1")
    _only_the_match_catalog(monkeypatch, (orphan,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="which that club does not have"):
            await seed(session)


async def test_a_match_seating_more_players_than_exist_stops_the_run(
    session_factory, monkeypatch
):
    from app.kernel import SPORT_SPECS

    greedy = replace(MATCHES[0], taken=SPORT_SPECS[MATCHES[0].sport].players)
    monkeypatch.setattr("app.seeds.runner.ACCOUNTS", ())
    # The court claims name a buyer, and the accounts have just been deleted —
    # so they are narrowed away too, exactly as `_only_this_catalog` does.
    monkeypatch.setattr("app.seeds.runner.RESERVATIONS", ())
    _only_the_match_catalog(monkeypatch, (greedy,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="the account catalog holds"):
            await seed(session)


async def test_a_seeded_match_write_with_no_instant_is_refused(session_factory):
    """The seeded week's clock has no default, and that is the whole point.

    Falling back to the wall clock would succeed silently and leave the match
    carrying the day the seed happened to run — which is the one failure this
    class exists to remove, and the one nobody would see.
    """

    from app.seeds.runner import _SeededWeekClock

    with pytest.raises(SeedFailed, match="no instant set"):
        _SeededWeekClock().now()
