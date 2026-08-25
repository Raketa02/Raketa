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

from app.core.config import get_settings
from app.bootstrap.composition import (
    build_clock,
    build_event_publisher,
    build_match_repository,
    build_match_standby_places,
    build_reservation_repository,
)
from app.kernel import (
    Instant,
    MatchKind,
    Outcome,
    Situation,
    Viewer,
    court_hold,
    is_held,
    situation,
)
from app.modules.courts.domain.reservation import MatchHeld
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchDepartureORM,
    MatchORM,
    MatchSeatORM,
    MatchVacancyORM,
)
from app.seeds.catalog import ACCOUNTS, EMPTY_HANDED
from app.seeds.clubs import CLUBS
from app.modules.now.domain.cascade import Rung
from app.seeds import matches as match_catalog
from app.seeds.matches import (
    HELD_SOFT,
    MATCHES,
    DepartureClaim,
    SeedMatch,
    SituationClaim,
    seed_moment,
)
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


def test_a_hole_with_no_money_behind_it_is_refused_by_the_catalog():
    """A vacancy and a departure are two facts, and the catalog names both."""

    with pytest.raises(ValueError, match="two facts and both are seeded"):
        replace(
            MATCHES[0],
            taken=1,
            vacated=1,
            vacated_at=seed_moment(day_offset=1),
            departure=None,
        )


def test_a_departure_claim_on_a_match_that_loses_nobody_is_refused():
    with pytest.raises(ValueError, match="two facts and both are seeded"):
        replace(
            MATCHES[0],
            departure=DepartureClaim(
                promise="a leaver who never left",
                outcome=None,
                names_an_amount=True,
            ),
        )


# --- 1b. named seats, and the account that must never be on one -------------


def test_a_scenario_names_every_seat_or_none_of_them():
    """A half-named seat list falls back to the catalog's order for the rest,
    which is the answer naming them was there to replace."""

    with pytest.raises(ValueError, match="half-authored"):
        replace(HELD_SOFT, seats=HELD_SOFT.seats[:1])


def test_a_scenario_seating_one_player_twice_is_refused():
    """The aggregate refuses it too — this is where a developer meets it."""

    with pytest.raises(ValueError, match="one seat in a match or none"):
        replace(
            HELD_SOFT,
            taken=2,
            paid=2,
            seats=(HELD_SOFT.seats[0], HELD_SOFT.seats[0]),
        )


def test_no_scenario_enrols_the_account_named_for_an_empty_screen():
    """`Raketa02/Raketa#96`'s rule, over the catalog as it stands.

    Written against `EMPTY_HANDED` rather than against the slug, because the
    claim lives on the account and a test naming the string would go on passing
    the day the account was renamed. The set is asserted non-empty first, for
    the reason every wildcard fence in this tree is: an intersection with
    nothing holds vacuously and reads exactly like one that holds.
    """

    assert EMPTY_HANDED

    for match in MATCHES:
        enrolled = {
            *match.seats,
            *(claim.player_slug for claim in match.standby),
            *(claim.player_slug for claim in match.offers),
        }
        assert not (enrolled & EMPTY_HANDED), match.slug


def test_a_catalog_that_enrols_an_empty_handed_account_is_refused_at_import(
    monkeypatch,
):
    """The import-time half. Halfway through a run is the one place a bad entry
    must not be found — a run reaches the ninth scenario having written eight."""

    slug = sorted(EMPTY_HANDED)[0]
    lying = replace(HELD_SOFT, seats=(slug, *HELD_SOFT.seats[1:]))

    monkeypatch.setattr(match_catalog, "MATCHES", (lying,))
    with pytest.raises(RuntimeError, match="promises an empty screen"):
        match_catalog._refuse_an_impossible_catalog()


def test_a_catalog_naming_a_player_who_does_not_exist_is_refused_at_import(
    monkeypatch,
):
    lying = replace(HELD_SOFT, seats=("nobody-at-all", *HELD_SOFT.seats[1:]))

    monkeypatch.setattr(match_catalog, "MATCHES", (lying,))
    with pytest.raises(RuntimeError, match="account catalog does not hold"):
        match_catalog._refuse_an_impossible_catalog()


def test_the_catalog_as_authored_passes_its_own_import_refusal():
    """The negative control the two above need: a refusal that fired on
    everything would pass both of them and stop every run."""

    match_catalog._refuse_an_impossible_catalog()


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
            session,
            events=build_event_publisher(session),
            clock=build_clock(get_settings()),
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
            session,
            events=build_event_publisher(session),
            clock=build_clock(get_settings()),
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


async def test_the_leaver_is_a_second_row_beside_the_hole(session_factory):
    """Two facts, two tables (ADR-0033). The seeded week has one of each, and
    the departure is the demo's whole leaver audience."""

    async with session_factory() as session:
        seeded = (await seed(session)).matches

    leavers = sum(entry.match.vacated for entry in seeded)

    assert await count(session_factory, MatchDepartureORM) == leavers
    assert leavers == 1


async def test_the_seeded_leaver_is_owed_something_nothing_has_decided(
    session_factory,
):
    """The state a card renders as *not yet decided*, seeded rather than
    described — and the outcome is what the rules composed, not what the
    catalog wrote down."""

    async with session_factory() as session:
        await seed(session)
        stored = await _stored_departures(session)

    (departure,) = stored
    assert departure.outcome is None
    assert departure.settled_at is None
    assert departure.amount_grosze == 3800


async def test_a_departure_whose_money_no_longer_matches_stops_the_run(
    session_factory, monkeypatch
):
    """The claim is checked, like every other name in the catalog. This one is
    the only claim in the whole seed system that is about a **refund**."""

    recovering = next(one for one in MATCHES if one.departure is not None)
    lying = replace(
        recovering,
        departure=replace(
            recovering.departure,
            promise="a leaver who has been paid back in full",
            outcome=Outcome.REFUNDED_IN_FULL,
        ),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="paid back in full"):
            await seed(session)


async def test_a_departure_whose_payload_form_no_longer_matches_stops_the_run(
    session_factory, monkeypatch
):
    """*Nothing was taken* and *nothing has come back yet* are the two sentences
    the forms exist to keep apart, and a seeded card must not blur them."""

    recovering = next(one for one in MATCHES if one.departure is not None)
    lying = replace(
        recovering,
        departure=replace(recovering.departure, names_an_amount=False),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="opposite sentences"):
            await seed(session)


async def _stored_departures(session):
    rows = await session.execute(select(MatchDepartureORM))
    return list(rows.scalars().all())


async def _seats_held_by(session_factory, run, player_id) -> list[str]:
    """Every seeded match this player is sitting on, by slug."""

    async with session_factory() as session:
        repository = build_match_repository(
            session,
            events=build_event_publisher(session),
            clock=build_clock(get_settings()),
        )
        return [
            entry.match.slug
            for entry in run.matches
            if (stored := await repository.get(entry.match_id)) is not None
            and stored.seat_of(player_id) is not None
        ]


async def test_the_seeded_accounts_fill_the_seats_in_catalog_order(
    session_factory,
):
    """Signing in as an early seeded account shows a developer her own matches.

    *Early* rather than *first*: the head of the catalog is the account whose
    name promises nothing at all, and she is skipped. The one below her is what
    catalog order now means, so a scenario that names no seats reaches her.
    """

    async with session_factory() as session:
        run = await seed(session)

    seatable = [one for one in run.accounts if not one.account.holds_nothing]
    held = await _seats_held_by(session_factory, run, seatable[0].player_id)

    # Every scenario that neither names its seats nor has since lost her seats
    # her first.
    assert "match-with-a-seat-held-and-unpaid" in held
    assert "match-holding-a-court-softly" not in held


async def test_the_account_named_for_an_empty_screen_sits_on_nothing(
    session_factory,
):
    """`Raketa02/Raketa#96`'s own rule, asked of the seats that are there.

    Counting from the head of the catalog seated `brand-new-player` on every
    scenario that seats anybody, so the account a client's empty state is drawn
    from sat on every one that had anybody on it. Nothing about the cards she drew would
    have looked wrong — they were simply not the screen her name promises, which
    is the failure mode this catalog exists to refuse.

    Asserted against the **stored** seats and not against `_players_for`, for
    the same reason the runner's own refusal is: what a developer meets is the
    database, and the arithmetic that fills it is one of two ways in.
    """

    async with session_factory() as session:
        run = await seed(session)

    empty_handed = [one for one in run.accounts if one.account.holds_nothing]
    assert empty_handed, "no seeded account promises an empty screen"

    for account in empty_handed:
        held = await _seats_held_by(session_factory, run, account.player_id)
        assert held == [], f"{account.account.slug} is sitting on {held}"


async def test_a_seeded_match_holds_a_court_exactly_when_the_ladder_says_so(
    session_factory,
):
    """The catalog never says whether a court is held; the ladder does.

    Asserted against the kernel rather than against a list, and at the instant
    the *last write* happened rather than at the scenario's own claim instant —
    a hold is granted when a tier is entered and taken back on the next look, so
    a tier that has since lapsed leaves `held_since` standing until a wake
    (`Raketa02/Raketa#72`). What may never differ is the answer at the moment the
    ladder last ran, which is what this reads.
    """

    async with session_factory() as session:
        run = await seed(session)
        repository = build_match_repository(
            session,
            events=build_event_publisher(session),
            clock=build_clock(get_settings()),
        )
        for entry in run.matches:
            stored = await repository.get(entry.match_id)
            assert stored is not None
            wrote_at = _last_write(entry.match)
            wanted = is_held(court_hold(stored.as_record(), wrote_at))
            assert (stored.held_since is not None) is wanted, entry.match.slug


async def test_a_held_court_is_a_reservation_the_match_holds(session_factory):
    """`held_since` is the match's fact; the court itself is Courts'.

    The match stores no `reservation_id` — the reservation already says
    `MatchHeld(match_id)`, and a column here would be the same arrow drawn twice
    (ADR-0034, ADR-0035). So *which* court a seeded match holds is answered by
    asking Courts, and this is the assertion that the ladder actually went and
    got one rather than writing an instant onto a record.
    """

    async with session_factory() as session:
        run = await seed(session)
        matches = build_match_repository(
            session,
            events=build_event_publisher(session),
            clock=build_clock(get_settings()),
        )
        reservations = build_reservation_repository(session)

        held, unheld = [], []
        for entry in run.matches:
            stored = await matches.get(entry.match_id)
            assert stored is not None
            reservation = await reservations.for_match(entry.match_id)
            (held if stored.held_since is not None else unheld).append(entry.match.slug)
            assert (reservation is not None) is (stored.held_since is not None)
            if reservation is not None:
                assert reservation.holder == MatchHeld(match_id=entry.match_id)
                assert reservation.club_id == stored.club_id
                assert reservation.category_id == stored.category_id

        # Both sides are non-empty, or the assertion above is vacuous on one of
        # them and would pass with the ladder deleted.
        assert held and unheld
        assert "match-holding-a-court-softly" in held
        assert "match-forming" in unheld


def _last_write(scenario) -> Instant:
    """When the ladder last ran for this scenario, which is its last write."""

    return max(
        moment
        for moment in (
            scenario.posted_at,
            scenario.joined_at if scenario.taken else None,
            scenario.vacated_at,
            scenario.cancelled_at,
        )
        if moment is not None
    )


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


# --- the queue: the one claim asked with a viewer ---------------------------


async def test_the_queued_account_is_really_on_the_queue(session_factory):
    """A seeded place is written through the use case a tap would run.

    There is no join route in v1 (ADR-0087), so the catalog is the only writer
    and a place that failed to land would leave the one card in the product that
    names an act unreachable — with nothing else in the run looking different.
    """

    async with session_factory() as session:
        seeded = (await seed(session)).matches
        queued = next(entry for entry in seeded if entry.match.standby)
        claim = queued.match.standby[0]
        player = next(
            account.player_id
            for account in (await seed(session)).accounts
            if account.account.slug == claim.player_slug
        )

        places = build_match_standby_places(session)
        assert queued.match_id in await places.held_by(player)


async def test_the_queued_account_resolves_to_the_situation_it_is_named_for(
    session_factory,
):
    """The catalog's claim, asked of the kernel **with a viewer**.

    `waitlisted` is the one situation only a viewer can be in (ADR-0040), so
    this is the only place in the whole seed system where `situation()` is asked
    with one — everywhere else the name is a fact about the match alone.
    """

    async with session_factory() as session:
        seeded = (await seed(session)).matches
        queued = next(entry for entry in seeded if entry.match.standby)
        claim = queued.match.standby[0]

    async with session_factory() as session:
        repository = build_match_repository(
            session,
            events=build_event_publisher(session),
            clock=build_clock(get_settings()),
        )
        stored = await repository.get(queued.match_id)
        assert stored is not None
        assert (
            situation(
                stored.as_record(),
                Viewer(on_standby=True),
                claim.resolved_at,
            )
            is claim.situation
        )


async def test_a_queued_account_whose_card_no_longer_says_so_stops_the_run(
    session_factory, monkeypatch
):
    """The negative control for the check above, and it is the whole of it.

    The situation is derived, so retuning the ladder can move it under the name
    — and the card it moves is the only one this build can act on. Without this
    the check is a line nobody has seen fire.
    """

    queued = next(one for one in MATCHES if one.standby)
    lying = replace(
        queued,
        standby=(
            replace(
                queued.standby[0],
                promise="a player whose match has been played",
                situation=Situation.NEEDS_RESULT,
            ),
        ),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="whose match has been played"):
            await seed(session)


async def test_a_queue_place_naming_nobody_stops_the_run(
    session_factory, monkeypatch
):
    """A catalog that has been half-edited, refused before it can be seeded."""

    queued = next(one for one in MATCHES if one.standby)
    lying = replace(
        queued,
        standby=(replace(queued.standby[0], player_slug="nobody-at-all"),),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="nobody-at-all"):
            await seed(session)


async def test_an_offer_claim_naming_somebody_the_ladder_did_not_reach_stops_the_run(
    session_factory, monkeypatch
):
    """The check that an offer claim exists at all, driven where it can fire.

    An ordinary run reaches the person the catalog names, so this half is
    unreachable from a green seed — the same shape the standby check's own
    negative controls take, and the same defect the last commit found in two of
    them. Here the claim names an account the cascade has no reason to tell:
    somebody seated in the match, whom the pool's own `NotAlreadyMine` refuses.
    """

    offered = next(one for one in MATCHES if one.offers)
    seated = ACCOUNTS[0].slug
    lying = replace(
        offered,
        offers=(replace(offered.offers[0], player_slug=seated),),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="reached nobody"):
            await seed(session)


async def test_an_offer_claim_on_the_wrong_rung_stops_the_run(
    session_factory, monkeypatch
):
    """**The negative control the whole claim exists for.**

    The offer is there, the card would look right, and the ladder has quietly
    stopped putting the person who *asked* first — which is the standby promise
    gone with nothing on any screen to say so. The rung is what makes that
    visible, and without this case it is a field nobody has seen checked.
    """

    offered = next(one for one in MATCHES if one.offers)
    lying = replace(
        offered,
        offers=(replace(offered.offers[0], rung=Rung.IN_THE_BAND),),
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="rung"):
            await seed(session)


async def test_an_offer_claim_naming_nobody_stops_the_run(
    session_factory, monkeypatch
):
    """A catalog that has been half-edited, refused before it can be checked."""

    offered = next(one for one in MATCHES if one.offers)
    lying = replace(
        offered, offers=(replace(offered.offers[0], player_slug="nobody-at-all"),)
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="nobody-at-all"):
            await seed(session)


async def test_a_scenario_claiming_an_offer_and_losing_nobody_stops_the_run(
    session_factory, monkeypatch
):
    """A cascade walks a hole, so a claim with no hole is a claim about nothing.

    Refused explicitly rather than as *the ladder reached nobody*, because the
    two are different edits: one is a scenario whose ladder stopped working, and
    this is a scenario that never had one.
    """

    intact = next(one for one in MATCHES if one.offers)
    lying = replace(
        next(one for one in MATCHES if not one.vacated and not one.offers),
        offers=intact.offers,
    )
    _only_the_match_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="loses nobody"):
            await seed(session)


def test_every_offer_claim_names_an_account_the_scenario_does_not_seat():
    """A seat holder could never be offered the seat, so a claim naming one lies.

    Checked here, before the write, because the run's own check would find it as
    *the ladder reached nobody* — which is the right refusal for a ladder that
    stopped working and the wrong sentence for a catalog that was never
    coherent.
    """

    for scenario in MATCHES:
        seated = {account.slug for account in ACCOUNTS[: scenario.taken]}
        for claim in scenario.offers:
            assert claim.player_slug not in seated, scenario.slug


def test_a_catalog_queuing_somebody_twice_is_refused():
    """Asking twice is asking once, so a catalog saying it twice says one thing.

    Refused in `__post_init__`, before anything is written, on the rule every
    other impossible scenario here is refused by.
    """

    queued = next(one for one in MATCHES if one.standby)
    with pytest.raises(ValueError, match="queues somebody twice"):
        replace(queued, standby=(queued.standby[0], queued.standby[0]))


def test_the_queued_account_holds_no_seat_in_the_match_it_is_queued_for():
    """Rung 7 tests *not seated*, so a queued seat holder would name no act.

    The catalog seats accounts in order, so this is a property of the counts and
    the slug rather than of the run — and it is checked here, before the write,
    because the run's own check would find it as a situation that moved.
    """

    for scenario in MATCHES:
        seated = {account.slug for account in ACCOUNTS[: scenario.taken]}
        for claim in scenario.standby:
            assert claim.player_slug not in seated, scenario.slug


async def test_a_queue_place_that_was_never_written_stops_the_run(
    session_factory, monkeypatch
):
    """The other half of the check, and the half no ordinary run reaches.

    The situation check above fires when the *ladder* moves; this one fires when
    the **place** does not land, which is the failure a silent write produces —
    a seeded week whose one actionable card is simply absent, with nothing else
    in the run looking different. Driven by removing the write, because that is
    the only thing that makes the guard reachable.
    """

    async def wrote_nothing(*args, **kwargs) -> None:
        return None

    monkeypatch.setattr(
        "app.seeds.runner._write_the_standby_places", wrote_nothing
    )

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="holds no such place"):
            await seed(session)
