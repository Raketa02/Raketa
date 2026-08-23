"""The two passes that read across the whole screen: the repeat guard and emphasis.

Both are properties of the *composed screen* rather than of any row in it, which
is why neither could be asserted where its subject was built: a shelf cannot know
it repeats the shelf above it, and a card cannot know it is the only one allowed
to shout (ADR-0032, ADR-0037).

The screens here are built by hand rather than composed, because what is under
test is a relationship between rows and a hand-built screen is the only way to
put two rows into an arbitrary relationship. The end-to-end half — that
``ComposeNow`` actually runs both, in the right order, over what the funnel
answered — is `test_compose_now.py`'s and `tests/api/test_now_emphasis.py`'s.
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import combinations, permutations, product
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import Cover, Situation, Sport, grosze

from app.modules.now.domain.composition import (
    EMPHASIS_COVERAGE_FLOOR,
    EMPHASIS_FIT_FLOOR,
    emphasised,
    without_repeats,
)
from app.modules.now.domain.funnel import Scored
from app.modules.now.domain.screen import (
    Block,
    ClubCard,
    EnrolledRegion,
    Fit,
    Level,
    MatchCard,
    Money,
    NowScreen,
    OffersRegion,
    PersonCard,
    Place,
    SeatCounts,
    Shelf,
    ShelfCard,
    ShelvesRegion,
    SituationFacts,
    SituationHalf,
    Door,
)
from app.modules.now.domain.vocabulary import DoorCode, ShelfCode
from tests.unit.shelf_doubles import a_context, a_match

AT = datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc)
WARSAW = ZoneInfo("Europe/Warsaw")
STAMP = 1_771_000_000_000


def a_card(match_id: UUID | None = None, **kwargs) -> MatchCard:
    return MatchCard(
        **{
            "match_id": match_id or uuid4(),
            "stamp": STAMP,
            "where": Place(
                club_id=uuid4(),
                club_name="Sport Club",
                zone=WARSAW,
                cover=Cover.INDOOR,
            ),
            "price": Money(amount=grosze(3800)),
            "situation": SituationHalf(
                situation=Situation.FORMING,
                facts=SituationFacts(
                    counts=SeatCounts(seats=4, paid=2, held=0),
                    court_total=Money(amount=grosze(15200)),
                ),
            ),
            "fit": Fit(score=91),
            **kwargs,
        }
    )


def a_shelf(code: ShelfCode, *cards: ShelfCard) -> Shelf:
    return Shelf(code=code, cards=cards)


def a_screen(
    *blocks: Block,
    offers: tuple[MatchCard, ...] = (),
    enrolled: tuple[MatchCard, ...] = (),
) -> NowScreen:
    return NowScreen(
        offers=OffersRegion(stamp=STAMP, cards=offers),
        your_matches=EnrolledRegion(stamp=STAMP, cards=enrolled),
        shelves=ShelvesRegion(stamp=STAMP, shelves=blocks),
        sports=frozenset({Sport.PADEL}),
    )


def a_score(
    card: MatchCard,
    *,
    fit: int = 95,
    coverage: int = 90,
    has_free_seat: bool = True,
) -> Scored:
    """One shouting card's three gates, defaulting to *all three cleared*.

    The context is a real one so that ``match_id`` is the only thing tying a
    score to a card — which is what the emphasis pass looks it up by, and what a
    later session reaching for a position instead would break.
    """

    return Scored(
        context=a_context(match_id=card.match_id, record=a_match(paid=1)),
        fit=fit,
        coverage=coverage,
        badge=card.fit or Fit(score=20),
        has_free_seat=has_free_seat,
    )


def _codes(screen: NowScreen) -> list[ShelfCode | DoorCode]:
    return [block.code for block in screen.shelves.shelves]


def _emphatic(screen: NowScreen) -> list[UUID]:
    """Every emphatic card on the whole screen, in composed order."""

    found: list[UUID] = []
    for block in screen.shelves.shelves:
        if not isinstance(block, Shelf):
            continue
        found.extend(
            card.match_id
            for card in block.cards
            if isinstance(card, MatchCard) and card.emphasis
        )
    return found


# --- 1 · the repeat guard ---------------------------------------------------
#
# Every case below is a screen the composer cannot produce today, and that is the
# point rather than a weakness. The four shipping lanes are pairwise incapable of
# repeating each other — a free seat against full is one exclusive rule, and
# people against clubs are two card types — so the guard is written for
# `recentlyViewed`, which is shelf 1's own population filtered by a gesture and
# arrives as a *server* change (ADR-0085). It cannot be added on the way in.


def test_a_shelf_that_is_entirely_repeats_of_the_shelf_above_is_dropped() -> None:
    one, two = a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, one, two),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, two, one),
    )

    assert _codes(without_repeats(screen)) == [ShelfCode.BEST_FIT]


def test_partial_overlap_is_allowed_and_a_match_may_appear_on_two_shelves() -> None:
    """A good match must not be hidden for having been mentioned.

    Two shelves make two different claims about one match, and the guard exists
    for the shelf that adds *nothing* rather than for the one that adds
    something.
    """

    shared, fresh = a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, shared),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, shared, fresh),
    )

    kept = without_repeats(screen)

    assert _codes(kept) == [ShelfCode.BEST_FIT, ShelfCode.FULL_WORTH_WAITING]
    assert _about(kept.shelves.shelves[1]) == {shared.match_id, fresh.match_id}


def test_a_shelf_sharing_nothing_is_untouched() -> None:
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, a_card()),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, a_card()),
    )

    assert without_repeats(screen) is screen


def test_a_shelf_is_compared_against_the_nearest_shelf_still_standing() -> None:
    """A dropped shelf is not on the screen, so it is not *the shelf above*.

    Compared against the row that was dropped, the third shelf here is new and
    survives — and the player scrolls past two rows saying the same thing with
    one row between them removed. The nearest *standing* shelf is the one she
    actually reads.
    """

    one, two = a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, one, two),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, one),
        a_shelf(ShelfCode.NEW_PLAYERS, two),
    )

    assert _codes(without_repeats(screen)) == [ShelfCode.BEST_FIT]


def test_a_shelf_repeating_two_shelves_between_them_still_stands() -> None:
    """*The shelf above* is one shelf, and not everything she has scrolled past.

    A row drawn from two rows above it is a **third** claim about a set of
    matches somebody has now seen made three ways, and the guard is not a budget
    on how many times a match may appear — that is the same reasoning as
    allowing partial overlap, one shelf further down. Accumulating everything
    above would also make the drop depend on how far down the screen a shelf
    happens to sit, which is a shelf-order rule wearing a repeat guard's name.
    """

    one, two = a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, one),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, two),
        a_shelf(ShelfCode.NEW_PLAYERS, one, two),
    )

    assert without_repeats(screen) is screen


def test_the_guard_compares_the_thing_a_card_is_about_and_not_its_kind() -> None:
    """A card is identified by its match, its player or its club (ADR-0070)."""

    player, club = uuid4(), uuid4()
    people = a_shelf(
        ShelfCode.NEW_PLAYERS,
        PersonCard(
            player_id=player,
            stamp=STAMP,
            nickname="ala",
            level=Level(value=2.7, provisional=True),
        ),
    )
    clubs = a_shelf(
        ShelfCode.NEW_CLUBS, ClubCard(club_id=club, stamp=STAMP, name="Sport Club")
    )
    same_people = a_shelf(
        ShelfCode.NEW_CLUBS,
        PersonCard(
            player_id=player,
            stamp=STAMP,
            nickname="ala",
            level=Level(value=3.1, provisional=False),
        ),
    )

    assert _codes(without_repeats(a_screen(people, clubs))) == [
        ShelfCode.NEW_PLAYERS,
        ShelfCode.NEW_CLUBS,
    ]
    assert _codes(without_repeats(a_screen(people, same_people))) == [
        ShelfCode.NEW_PLAYERS
    ]


def test_a_door_is_stepped_over_rather_than_compared() -> None:
    """It has no cards, so it can neither repeat a shelf nor be repeated by one.

    A door is always first on today's screen, so this is about what stays true
    if it ever moves: the shelf under a door is compared against the shelf above
    the door and not against the door.
    """

    shared = a_card()
    door = Door(code=DoorCode.NO_RUN_YET)
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, shared),
        door,
        a_shelf(ShelfCode.NEW_PLAYERS, shared),
    )

    kept = without_repeats(screen)

    assert kept.shelves.shelves == (screen.shelves.shelves[0], door)


def test_a_door_alone_survives_the_guard() -> None:
    screen = a_screen(Door(code=DoorCode.RUN_PARKED))

    assert without_repeats(screen) is screen


def test_a_shelf_with_no_cards_is_kept_rather_than_vacuously_dropped() -> None:
    """It cannot be composed at all — an empty shelf is *absent* (ADR-0070).

    *Every one of no cards is a repeat* is vacuously true, so a guard that did
    not say otherwise would delete the one shape that should never have existed
    instead of leaving it where somebody can see it.
    """

    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, a_card()), a_shelf(ShelfCode.NEW_PLAYERS)
    )

    assert _codes(without_repeats(screen)) == [
        ShelfCode.BEST_FIT,
        ShelfCode.NEW_PLAYERS,
    ]


def test_the_guard_touches_neither_other_region() -> None:
    """It is about rows a player scrolls past, and neither region is a row."""

    hers = a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, hers),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, hers),
        enrolled=(hers,),
        offers=(hers,),
    )

    kept = without_repeats(screen)

    assert _codes(kept) == [ShelfCode.BEST_FIT]
    assert kept.your_matches.cards == (hers,)
    assert kept.offers.cards == (hers,)


# --- 2 · emphasis -----------------------------------------------------------


def test_the_first_card_clearing_all_three_gates_is_the_one_that_shouts() -> None:
    quiet, loud, also = a_card(), a_card(), a_card()
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT, quiet, loud, also))

    flagged = emphasised(
        screen, scores=(a_score(quiet, fit=80), a_score(loud), a_score(also))
    )

    assert _emphatic(flagged) == [loud.match_id]


def test_at_most_one_card_on_the_whole_screen_is_emphatic() -> None:
    """The cap is the structural guarantee, not the thresholds (ADR-0037).

    Whatever the score distribution does as real data arrives, the screen's one
    loud colour cannot become wallpaper.
    """

    first, second, third = a_card(), a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, first, second),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, third),
    )

    flagged = emphasised(
        screen, scores=(a_score(first), a_score(second), a_score(third))
    )

    assert _emphatic(flagged) == [first.match_id]


def test_emphasis_follows_composed_order_across_shelves_and_not_the_score() -> None:
    """The card that shouts is the first she would reach, not the best one.

    Nothing here re-ranks: a higher score further down the screen does not jump
    the queue, because *"why that one?"* has to have an answer she can see.
    """

    lower, higher = a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, lower),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, higher),
    )

    flagged = emphasised(
        screen, scores=(a_score(higher, fit=99), a_score(lower, fit=90))
    )

    assert _emphatic(flagged) == [lower.match_id]


@pytest.mark.parametrize(
    "fit,coverage,has_free_seat",
    [
        (EMPHASIS_FIT_FLOOR - 1, 90, True),
        (95, EMPHASIS_COVERAGE_FLOOR - 1, True),
        (95, 90, False),
    ],
)
def test_a_card_missing_any_one_gate_does_not_shout(
    fit: int, coverage: int, has_free_seat: bool
) -> None:
    """Three gates, evaluated together. Two of three is not emphasis.

    The seat gate is the one that carries §2.2's rule: an emphatic badge points
    at a seat the player can take, and a full match — where the *highest* scores
    live — has none.
    """

    card = a_card()
    screen = a_screen(a_shelf(ShelfCode.FULL_WORTH_WAITING, card))

    flagged = emphasised(
        screen,
        scores=(
            a_score(card, fit=fit, coverage=coverage, has_free_seat=has_free_seat),
        ),
    )

    assert _emphatic(flagged) == []


@pytest.mark.parametrize(
    "fit,coverage", [(EMPHASIS_FIT_FLOOR, EMPHASIS_COVERAGE_FLOOR)]
)
def test_the_floors_are_inclusive_at_exactly_their_own_number(
    fit: int, coverage: int
) -> None:
    card = a_card()
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT, card))

    flagged = emphasised(screen, scores=(a_score(card, fit=fit, coverage=coverage),))

    assert _emphatic(flagged) == [card.match_id]


def test_the_two_gates_are_the_decided_numbers() -> None:
    """Pinned to their **literals**, because every other case reads the constants.

    A floor compared only against itself is a floor that moves with the edit that
    wanted it moved and takes every test with it — the defect the funnel's own
    retrieval bounds were found to have. ADR-0037 fixes both: 90 because roughly
    one score in twenty-three reaches it, and 80 % because a floor much above it
    could not fire at all while two terms ship dark, and a gate that cannot fire
    is one nobody should be watching.
    """

    assert (EMPHASIS_FIT_FLOOR, EMPHASIS_COVERAGE_FLOOR) == (90, 80)


def test_any_offer_on_the_screen_silences_emphasis_entirely() -> None:
    """An offer is a seat with a clock on it, and it is the loudest thing we say.

    A suggestion shouting underneath it would be two things competing to be the
    one thing she does next.
    """

    card = a_card()
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT, card), offers=(a_card(),))

    assert emphasised(screen, scores=(a_score(card),)) is screen


def test_a_card_with_no_score_never_shouts() -> None:
    """Which is what keeps the strip and the arrival shelves out of it.

    A degraded screen reaches here with no scores at all, and so does every
    person and club card there has ever been.
    """

    card = a_card()
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT, card))

    assert emphasised(screen, scores=()) is screen


def test_a_score_for_a_card_that_is_not_on_the_screen_flags_nothing() -> None:
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT, a_card()))

    assert emphasised(screen, scores=(a_score(a_card()),)) is screen


def test_the_enrolled_strip_is_never_emphasised() -> None:
    """She is already in those matches, so *take this seat now* is not about them."""

    hers = a_card()
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT), enrolled=(hers,))

    flagged = emphasised(screen, scores=(a_score(hers),))

    assert [card.emphasis for card in flagged.your_matches.cards] == [False]


def test_nothing_but_the_one_card_is_rebuilt() -> None:
    """A card the pass does not touch is the object the composer produced."""

    quiet, loud = a_card(), a_card()
    untouched = a_shelf(ShelfCode.NEW_CLUBS, ClubCard(
        club_id=uuid4(), stamp=STAMP, name="Sport Club"
    ))
    screen = a_screen(a_shelf(ShelfCode.BEST_FIT, quiet, loud), untouched)

    flagged = emphasised(screen, scores=(a_score(loud),))

    shelf = flagged.shelves.shelves[0]
    assert isinstance(shelf, Shelf)
    assert shelf.cards[0] is quiet
    assert flagged.shelves.shelves[1] is untouched


# --- 3 · the two passes together --------------------------------------------


def test_the_two_passes_commute_today_and_the_guards_condition_is_why() -> None:
    """Recorded rather than papered over: the specified order is not observable.

    A dropped shelf is *entirely* repeats of a shelf above it, so every card on
    it has a copy above — and emphasis takes the first in composed order, which
    is that copy. The flag therefore never lands on a row the guard is about to
    remove, whichever pass runs first. Checked by exhaustive search over small
    shapes as well as by the case below.

    The order at the call site is still the specified one, because the
    equivalence is a property of the **drop condition** and not of the passes: a
    guard that ever dropped a shelf for partial overlap, or for a cap on total
    rows, would put a qualifying card on a row nobody sees, and the failure is
    silent — a screen with nothing loud on it looks exactly like an ordinary
    screen.
    """

    shared, quiet = a_card(), a_card()
    screen = a_screen(
        a_shelf(ShelfCode.BEST_FIT, quiet, shared),
        a_shelf(ShelfCode.FULL_WORTH_WAITING, shared),
    )
    scores = (a_score(quiet, fit=80), a_score(shared))

    guard_first = emphasised(without_repeats(screen), scores=scores)
    emphasis_first = without_repeats(emphasised(screen, scores=scores))

    assert _emphatic(guard_first) == [shared.match_id]
    assert emphasis_first == guard_first


#: The three shelf codes the exhaustive search builds its screens out of. Any
#: three distinct codes would do — the guard never reads one, and that is worth
#: having the search demonstrate rather than assert: a pass that dropped a shelf
#: for *which* shelf it is would be a shelf order wearing a repeat guard's name.
SHAPE_CODES = (ShelfCode.BEST_FIT, ShelfCode.FULL_WORTH_WAITING, ShelfCode.NEW_PLAYERS)


def _arrangements(cards: tuple[MatchCard, ...]) -> list[tuple[MatchCard, ...]]:
    """Every non-empty ordered arrangement of distinct cards, shortest first.

    A shelf never carries one card twice — a card is identified by the thing it
    is about, and one match on one shelf twice is not a shape the composer can
    produce — so this is subsets rather than sequences with repetition.
    """

    return [
        arrangement
        for size in range(1, len(cards) + 1)
        for arrangement in permutations(cards, size)
    ]


def test_the_two_passes_commute_over_every_small_shape() -> None:
    """The exhaustive half of the claim above: 256 cases, no disagreement.

    Three shelves drawn from two matches, every ordered arrangement of them —
    sixty-four screens — against every subset of the two clearing all three
    gates. That covers a repeat of the shelf above, a repeat of a shelf that was
    itself dropped, partial overlap, disjoint shelves, and the loud card sitting
    on each shelf in turn.

    It is a search over shapes rather than a second example because the claim is
    a **negative** one: nothing in this space distinguishes the two orders. One
    case can only fail to notice a difference; a search can find one — and this
    space contains the case that finds one the day the drop condition widens.
    A guard dropping a shelf for *partial* overlap disagrees at
    ``[c0] · [c0, c1] · [c1]`` with ``c1`` loud: run second it drops the row the
    flag has just landed on and the screen goes quiet, run first it lets the
    copy below inherit it.
    """

    cards = (a_card(), a_card())
    shapes = _arrangements(cards)
    louds = [
        subset for size in range(len(cards) + 1) for subset in combinations(cards, size)
    ]
    seen = 0
    for arrangement in product(shapes, repeat=len(SHAPE_CODES)):
        rows = zip(SHAPE_CODES, arrangement, strict=True)
        screen = a_screen(*(a_shelf(code, *shape) for code, shape in rows))
        for loud in louds:
            scores = tuple(
                a_score(card, fit=95 if card in loud else 80) for card in cards
            )
            seen += 1
            assert without_repeats(emphasised(screen, scores=scores)) == emphasised(
                without_repeats(screen), scores=scores
            )

    assert seen == len(shapes) ** len(SHAPE_CODES) * len(louds) == 256


def _about(shelf: Block) -> set[UUID]:
    assert isinstance(shelf, Shelf)
    return {
        card.match_id for card in shelf.cards if isinstance(card, MatchCard)
    }
