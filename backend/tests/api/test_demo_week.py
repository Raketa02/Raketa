"""The demo week: sign in, and walk the week the catalogs assembled.

Every catalog before this one asserts its own scenarios in isolation — a club's
policy series, a court claim's two intervals, a match's situation, a leaver's
money. This file asserts the thing none of them can: that the seeded week is one
**coherent** week, and that somebody can sign in and be shown all of it
(`Raketa02/Raketa#96`).

**Signing in is over HTTP and composing is not, and the split is the seeded
week's own shape.** The address, the password and the token are what a developer
actually meets, so they are exercised through the API. The *screen* cannot be:
`app/seeds/courts.py` anchors the week to a fixed absolute instant on purpose —
*"next Tuesday at 18:00 computed at run time is a different Tuesday tomorrow"* —
and the product reads the wall clock, with no way anywhere to read one inside the
week. So a walkthrough composes at the week's own instants, exactly as the seed
runner *writes* at them, through the same composition root a request is wired
from. What that leaves undone is stated rather than hidden and filed as
`Raketa02/Raketa#134`: the week is **staged**, so each scenario is named at its
own instant and no single instant shows all thirteen at once — that part is the
catalog's design. What is not is that the week is in 2026 and the wall clock will
walk past it, after which every seeded address's Now goes empty; and that the two
post-play conversations, `needsResult` and `confirmResult`, are readable only
from inside the week, which nothing in the product can do.

**The walkthrough instant is the week's own peak**, and it is the instant three
of the seeded scenarios already name: Friday at 20:00, half an hour after
`match-that-lost-a-player` lost one. It is the only moment on the week where all
three regions have something to say at once — a seat has just been offered, a
court is being kept aside, and the city still has matches to rank.

**Two audiences are asserted as renderings and never as flows**, which is this
file's other job. No v1 flow creates a private court and none opens or closes
one, and no flow puts a player's own departure on her screen except the departure
route this data predates — so what is checked is that the card composes and says
the right name, which is the whole of what a client can be developed against.
"""

from __future__ import annotations

import pytest

from app.bootstrap import composition
from app.kernel import Instant, Situation, Sport
from app.modules.now.application.commands import ComposeNowQuery, SportFilter
from app.modules.now.application.compose_now import ComposeNow
from app.modules.now.domain.screen import (
    DepartureRecoverable,
    Door,
    MatchCard,
    NowScreen,
    Shelf,
)
from app.modules.now.domain.vocabulary import ShelfCode
from app.seeds.catalog import (
    ACCOUNTS,
    BRAND_NEW_PLAYER,
    RATED_IN_EVERY_SPORT,
    SEED_PASSWORD,
    SeedAccount,
)
from app.seeds.matches import seed_moment
from app.seeds.runner import Seeded, seed

#: Friday, 20:00 on the seeded week — the instant `match-that-lost-a-player`,
#: its queue place and its offer are all already asserted at, half an hour after
#: the hole opened. Written once here so a scenario and the walkthrough cannot
#: drift into describing two different evenings.
WALKTHROUGH: Instant = seed_moment(day_offset=4, hour=20)

#: The address the week is walked by. It is the account rated in **all four**
#: sports, and that is not a convenience: `all` resolves to the sports a player
#: holds a rating at, so the ranked shelves can only be full for somebody who
#: holds several — and every other seeded address is named for a state on the way
#: *to* a rating.
WALKER: SeedAccount = RATED_IN_EVERY_SPORT

#: The four shelves a v1 server can compose, in the order `ComposeNow` emits
#: them. `recentlyViewed` is the fifth and is **absent by decision** rather than
#: by accident — ADR-0085 keeps the code in the enumeration and never composes
#: it, so its return is a server change rather than a client release
#: (`Raketa02/Raketa#123`).
COMPOSABLE_SHELVES = (
    ShelfCode.BEST_FIT,
    ShelfCode.FULL_WORTH_WAITING,
    ShelfCode.NEW_PLAYERS,
    ShelfCode.NEW_CLUBS,
)

DARK_SHELF = ShelfCode.RECENTLY_VIEWED

#: The rung-8 group: what a private court is doing, seen by somebody on it. All
#: four are reachable **only** from seeded data in v1 — nothing posts a private
#: match, nothing opens a seat on one and nothing closes one — so this is the
#: enumeration a client is developed against and there is no flow behind it.
PRIVATE_OWNER_SITUATIONS = frozenset(
    {
        Situation.PRIVATE_OPEN,
        Situation.PRIVATE_PARTIAL,
        Situation.PRIVATE_FULL,
        Situation.PRIVATE_RESERVED,
    }
)


@pytest.fixture
async def week(session_factory) -> Seeded:
    """The whole seeded week, once, through the use cases a request runs."""

    async with session_factory() as session:
        return await seed(session)


class _At:
    """A ``Clock`` pinned to one instant on the seeded week.

    The same port the runner sets per write, read back: a situation is a
    function of the record *and* the clock, so a walkthrough that asked the wall
    clock would be asking about a different week every day.
    """

    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> Instant:
        return self._at


def _compose_now(session, at: Instant) -> ComposeNow:
    """`ComposeNow`, wired from the composition root, on the week's own clock.

    Mirrors `now/presentation/dependencies.py::get_compose_now` and differs from
    it in exactly one argument. Assembled here rather than reached through the
    API because the clock is the whole difference — the route's is the host's,
    and there is nowhere to hand it another.
    """

    events = composition.build_event_publisher(session)
    store = composition.build_domain_event_store(session)
    clock = _At(at)

    ratings = composition.build_skill_rating_repository(
        event_store=store, events=events
    )
    users = composition.build_user_repository(session)
    clubs = composition.build_club_repository(session)
    reservations = composition.build_reservation_repository(session)
    matches = composition.build_match_repository(session, events=events, clock=clock)
    standby = composition.build_match_standby_places(session)
    now_ratings = composition.build_ratings(ratings)
    arrivals = composition.build_arrivals(users=users, ratings=ratings, clubs=clubs)

    return ComposeNow(
        rated_sports=composition.build_rated_sports(ratings),
        parked_runs=composition.build_parked_runs(
            composition.build_assessment_repository(event_store=store, events=events)
        ),
        new_arrivals=composition.build_compose_new_arrivals(
            arrivals=arrivals,
            rows=arrivals,
            levels=composition.build_levels(ratings),
            sets=composition.build_arrival_sets(clock=clock),
        ),
        shelves=composition.build_compose_shelves(
            city=composition.build_city_matches(
                matches=matches,
                clubs=clubs,
                reservations=reservations,
                ratings=now_ratings,
                contexts=composition.build_scoring_contexts(),
            ),
            commitments=composition.build_commitments(matches),
            standby=composition.build_standby(matches=matches, standby=standby),
            ratings=now_ratings,
            scorer=composition.build_match_scorer(),
        ),
        enrolled=composition.build_compose_enrolled(
            enrolled=composition.build_enrolled_matches(
                matches=matches,
                standby=standby,
                claims=composition.build_seat_claims(session),
                clubs=clubs,
                reservations=reservations,
                users=users,
                ledgers=composition.build_ledger_repository(
                    event_store=store, events=events
                ),
            )
        ),
        offers=composition.build_compose_offers(
            offered=composition.build_offered_seats(
                offers=composition.build_offers(session),
                matches=matches,
                clubs=clubs,
                reservations=reservations,
            )
        ),
        clock=clock,
    )


async def _screen(
    session_factory,
    week: Seeded,
    account: SeedAccount,
    chip: SportFilter = SportFilter.ALL,
) -> NowScreen:
    """This address's whole Now, at the walkthrough instant, under one chip."""

    player_id = next(
        one.player_id for one in week.accounts if one.account.slug == account.slug
    )
    async with session_factory() as session:
        return await _compose_now(session, WALKTHROUGH).execute(
            ComposeNowQuery(player_id=player_id, sport=chip)
        )


def _situations(cards: tuple[MatchCard, ...]) -> set[Situation]:
    return {card.situation.situation for card in cards}


def _shelf_codes(blocks) -> list[ShelfCode]:
    return [block.code for block in blocks if isinstance(block, Shelf)]


# --- the walkthrough --------------------------------------------------------


async def test_the_walking_address_signs_in_with_the_catalog_password(client, week):
    """What a developer actually types, before anything about a screen."""

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": WALKER.email, "password": SEED_PASSWORD},
    )

    assert login.status_code == 200, login.text

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200, me.text
    assert me.json()["nickname"] == WALKER.slug


async def test_the_seeded_week_fills_all_three_regions_for_one_address(
    session_factory, week
):
    """`Raketa02/Raketa#96`'s closing claim, and the reason this file exists.

    Each region arrived with its own ticket and each was asserted against
    fixtures written for it. Nothing until now has asked whether **one** seeded
    week can fill all three at one instant for one person — which is the only
    form of the question a demo is.
    """

    screen = await _screen(session_factory, week, WALKER)

    assert screen.offers.cards, "the offers region is empty"
    assert screen.your_matches.cards, "the enrolled strip is empty"
    assert screen.shelves.shelves, "the shelves region is empty"


async def test_the_walk_reaches_every_shelf_a_v1_server_composes(
    session_factory, week
):
    """Four of the five, in the server's fixed order, each holding cards.

    Equality rather than containment, and in the order they are emitted: a
    shelf appearing is as much a change to this screen as one disappearing, and
    ADR-0070 put both presence and order on the server precisely so they can
    move — which means they have to be pinned somewhere they can be seen to.
    """

    screen = await _screen(session_factory, week, WALKER)

    assert _shelf_codes(screen.shelves.shelves) == list(COMPOSABLE_SHELVES)
    for block in screen.shelves.shelves:
        assert isinstance(block, Shelf) and block.cards, block.code


async def test_the_fifth_shelf_is_absent_because_it_ships_dark(session_factory, week):
    """The one shelf the seeded week cannot fill, said out loud.

    ADR-0085 keeps `recentlyViewed` in the enumeration and composes it nowhere,
    so no seeded data can put it on a screen — `Raketa02/Raketa#123`. Asserted
    rather than left as a gap in the list above, because *four shelves* and
    *four of five shelves* are different claims and only the second is true.
    The day the shelf lands this goes red, which is the right place to find out.
    """

    screen = await _screen(session_factory, week, WALKER)

    assert DARK_SHELF not in _shelf_codes(screen.shelves.shelves)
    assert DARK_SHELF not in set(COMPOSABLE_SHELVES)
    assert set(COMPOSABLE_SHELVES) | {DARK_SHELF} == set(ShelfCode) - {
        ShelfCode.SAME_LEVEL
    }


async def test_the_walking_address_is_offered_a_seat_and_holds_one_of_her_own(
    session_factory, week
):
    """The two regions that are about *her*, and they say different things.

    The offers region is a seat the cascade put in front of her; the strip is a
    match she has paid for. Asserted as distinct matches, because the composer
    hands the strip whatever the offers region is already speaking for — a week
    where both regions drew the same card would satisfy the count above and be
    the overlap `ComposeNow` composes in that order to avoid.
    """

    screen = await _screen(session_factory, week, WALKER)

    offered = {card.match_id for card in screen.offers.cards}
    enrolled = {card.match_id for card in screen.your_matches.cards}

    assert offered and enrolled
    assert not (offered & enrolled)
    assert _situations(screen.offers.cards) <= {
        Situation.SEAT_OPENED,
        Situation.SEAT_OFFERED,
    }


async def test_the_account_named_for_an_empty_screen_draws_one(session_factory, week):
    """The counterpart claim, and the one a client has no other fixture for.

    Every other seeded address has *something*, so an empty region is only ever
    seen against a database nobody has seeded — which is the state a client is
    least likely to have got right. Before `Raketa02/Raketa#96` this account
    held seats on every seeded match that had anybody on it and drew eight cards.
    """

    screen = await _screen(session_factory, week, BRAND_NEW_PLAYER)

    assert screen.offers.cards == ()
    assert screen.your_matches.cards == ()
    # No rating at any sport means no sport to be ranked at, and `all` is the
    # sports she holds a rating at — so under this chip there is no door either.
    # ADR-0084 puts her in the questionnaire rather than on this screen.
    assert screen.shelves.shelves == ()

    # And the composer is answering her rather than failing to. Naming a chip
    # she is unrated at produces a **door**, which is the difference between an
    # empty screen that is a decision and one that is a broken read — without it
    # every assertion above would pass against a composer that answered nothing
    # to anybody.
    named = await _screen(session_factory, week, BRAND_NEW_PLAYER, SportFilter.PADEL)
    assert [type(block) for block in named.shelves.shelves][:1] == [Door]


# --- the two audiences with no flow behind them -----------------------------


async def test_the_four_private_owner_situations_render_from_seeded_data(
    session_factory, week
):
    """All four rung-8 names on one screen, as a **rendering** and not a flow.

    There is no flow to assert. Nothing in v1 posts a private match, opens a
    seat on one or closes one, so every one of these is reachable from seeded
    data alone — and `privateFull` was produced **zero** times across 280 224
    records in the state-table research (ADR-0072), which is exactly why a
    client that has never been handed one will get it wrong.

    Asked of whichever seeded address holds them all rather than of a named one:
    who sits on a private court is the catalog's business, and a test naming her
    would go red on a reordering that changed nothing.
    """

    seen: set[Situation] = set()
    for account in ACCOUNTS:
        screen = await _screen(session_factory, week, account)
        seen |= _situations(screen.your_matches.cards) & PRIVATE_OWNER_SITUATIONS

    assert seen == PRIVATE_OWNER_SITUATIONS


async def test_the_leaver_audience_renders_from_seeded_data(session_factory, week):
    """ADR-0030's third audience: the match's card, drawn for somebody who used
    to hold a seat.

    A rendering rather than a flow for the same reason as the four above — the
    departure route writes this card's subject, and the seeded week's leaver
    left before any route existed to do it, so what is checked is that her card
    composes and carries her money. The payload **form** is the assertion that
    matters: *nothing was taken* and *nothing has come back yet* are opposite
    sentences and a blank cannot tell them apart (ADR-0072).
    """

    leavers = []
    for account in ACCOUNTS:
        screen = await _screen(session_factory, week, account)
        leavers += [
            card
            for card in screen.your_matches.cards
            if card.situation.facts.departure is not None
        ]

    assert leavers, "no seeded address is looking at a match she left"
    for card in leavers:
        # The **recoverable** form: she paid, and nothing has decided what
        # becomes of it yet. The other form carries no amount at all, and a
        # composer that answered it here would be telling somebody who is owed
        # 38 zł that nothing was ever taken.
        assert isinstance(card.situation.facts.departure, DepartureRecoverable)
        # The leaver stays on the match's own situation and is told the truth
        # about it: a hole she left is the match's recovery, not a state of
        # hers.
        assert card.situation.situation is Situation.REPLACEMENT
        # And the one act she must not be offered twice.
        assert card.may_depart is False


# --- the week is whole ------------------------------------------------------


async def test_every_context_that_models_anything_put_scenarios_on_the_week(week):
    """*The demo week arrives in pieces, with the contexts.*

    Five catalogs, each added by the ticket that landed its context, and the
    week is what they add up to. Asserted as *each is non-empty* rather than as
    a count, because a count is a number somebody has to update and this is a
    claim about a context having turned up at all.
    """

    assert week.accounts
    assert week.clubs
    assert week.reservations
    assert week.matches
    assert week.ledgers


async def test_the_week_covers_more_than_one_sport_and_more_than_one_club(week):
    """A week at one club in one sport is one scenario repeated.

    The shelves' variety rule pushes a club's third card in an hour down the
    shelf and the sport bar is a filter over four names, so a single-club
    single-sport week would leave both undeveloped against.
    """

    assert len({one.match.sport for one in week.matches}) >= 3
    assert len({one.match.club_slug for one in week.matches}) >= 3
    assert {Sport.PADEL} < {one.match.sport for one in week.matches}
