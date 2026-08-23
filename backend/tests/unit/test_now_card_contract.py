"""What a card carries on the wire, asserted by rendering one.

No composer produces a card yet — this ticket ships the envelope with its regions
empty — so the cards here are built by hand and rendered through the same
``from_domain`` the composer will use. That is the difference between a contract
that has been *designed* and one that has been *exercised*: a discriminator that
does not round-trip, a nested half that flattens, or an act that arrives with a
target beside it all fail here rather than in the ticket that first fills a
region.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.engines.fit import TermCode
from app.kernel import Cause, Cover, Situation, grosze
from app.modules.now.domain.screen import (
    ClubCard,
    DebtLine,
    EnrolledRegion,
    Fit,
    FitReason,
    HoldNote,
    Level,
    MatchCard,
    Money,
    NowScreen,
    OffersRegion,
    PersonCard,
    Place,
    SeatClaim,
    SeatCounts,
    Shelf,
    ShelvesRegion,
    SituationFacts,
    SituationHalf,
)
from app.modules.now.domain.vocabulary import (
    ActCode,
    CaptionCode,
    CardHoldReason,
    Currency,
    ShelfCode,
)
from app.modules.now.presentation.schemas import (
    ClubCardResponse,
    MatchCardResponse,
    NowResponse,
    PersonCardResponse,
    ShelfResponse,
)

AT = datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc)
WARSAW = ZoneInfo("Europe/Warsaw")

#: Every person card carries one — a player reaches that shelf only through a
#: rating at the shelf's sport, so there is no such thing as a person card with
#: no Level on it.
A_LEVEL = Level(value=2.7, provisional=True)


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Kraków",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def some_facts(**kwargs) -> SituationFacts:
    """The two facts every card carries, plus whatever the case is about.

    Counting is by money and the court's total has no audience, so both are on
    every card there is — a builder that let them be left out would be building
    a card the composition cannot produce.
    """

    return SituationFacts(
        **{
            "counts": SeatCounts(seats=4, paid=2, held=1),
            "court_total": Money(amount=grosze(15200)),
            **kwargs,
        }
    )


def a_card(**kwargs) -> MatchCard:
    return MatchCard(
        **{
            "match_id": uuid4(),
            "stamp": 1_771_000_000_000,
            "where": a_place(),
            "price": Money(amount=grosze(3800)),
            "situation": SituationHalf(situation=Situation.FORMING, facts=some_facts()),
            **kwargs,
        }
    )


def test_the_spine_is_complete_and_the_situation_half_is_nested() -> None:
    rendered = MatchCardResponse.from_domain(a_card()).model_dump()

    # Which thing, the one moment, where, how much, the badge, the emphasis flag,
    # the act, whether she may leave, the claim, the stamp — and the half below.
    assert set(rendered) == {
        "card_type",
        "match_id",
        "stamp",
        "clock",
        "where",
        "price",
        "fit",
        "emphasis",
        "act",
        "may_depart",
        "seat_claim",
        "situation",
    }
    # Nested, not flat. A flat card would leave the unknown-situation rule as a
    # discipline rather than a shape, and the first person to add a
    # situation-dependent field at the top level breaks it in silence.
    assert set(rendered["situation"]) == {"situation", "facts"}


def test_the_act_rides_as_a_code_alone_with_no_target() -> None:
    rendered = MatchCardResponse.from_domain(a_card(act=ActCode.TAKE_SEAT)).model_dump()

    assert rendered["act"] == "takeSeat"
    assert "target" not in rendered
    assert "label" not in rendered


def test_twenty_six_situations_name_no_act_and_the_card_says_so_by_absence() -> None:
    rendered = MatchCardResponse.from_domain(a_card()).model_dump()

    # Not a seventh act meaning *nothing*, and not an `Open match` fallback whose
    # destination does not exist: the slot is simply empty.
    assert rendered["act"] is None


def test_where_carries_the_club_its_zone_and_whether_there_is_a_roof() -> None:
    rendered = MatchCardResponse.from_domain(
        a_card(where=a_place(cover=Cover.OUTDOOR, distance_km=4))
    ).model_dump()

    assert rendered["where"]["zone"] == "Europe/Warsaw"
    assert rendered["where"]["cover"] == "outdoor"
    assert rendered["where"]["distance_km"] == 4


def test_the_zone_survives_a_card_whose_clock_is_empty() -> None:
    """The reason the zone is part of *where* and not part of the moment.

    A cancelled card counts to nothing, so its clock slot is empty — and it still
    prints a time as words. A zone that travelled with the moment would be absent
    exactly there, on the card that most needs to say which evening was lost.
    """

    rendered = MatchCardResponse.from_domain(
        a_card(
            clock=None,
            situation=SituationHalf(
                situation=Situation.CANCELLED_CLUB,
                facts=some_facts(cause=Cause.CLUB_CANCELLED),
            ),
        )
    ).model_dump()

    assert rendered["clock"] is None
    assert rendered["where"]["zone"] == "Europe/Warsaw"


def test_a_distance_the_platform_does_not_know_is_absent_and_never_zero() -> None:
    rendered = MatchCardResponse.from_domain(a_card()).model_dump()
    assert rendered["where"]["distance_km"] is None


def test_money_is_integer_grosze_with_a_currency_beside_it() -> None:
    rendered = MatchCardResponse.from_domain(a_card()).model_dump()

    assert rendered["price"] == {"amount": 3800, "currency": Currency.PLN}
    # Not a formatted string. The comma in *38,00 zł* is the client's, and the two
    # clients do not share a formatter's opinion about it.
    assert isinstance(rendered["price"]["amount"], int)


def test_the_badge_carries_reasons_as_codes_and_no_coverage() -> None:
    rendered = MatchCardResponse.from_domain(
        a_card(
            fit=Fit(
                score=87,
                reasons=(
                    FitReason(code=TermCode.SKILL_OVERLAP),
                    FitReason(code=TermCode.TRAVEL),
                ),
            )
        )
    ).model_dump()

    assert rendered["fit"]["score"] == 87
    assert [r["code"] for r in rendered["fit"]["reasons"]] == [
        TermCode.SKILL_OVERLAP,
        TermCode.TRAVEL,
    ]
    # Coverage ranks, gates emphasis, and may become words in a reason line. It
    # never becomes a second gauge on the card.
    assert "coverage" not in rendered["fit"]
    assert "weight" not in str(rendered["fit"])


def test_a_card_with_no_rating_in_that_sport_has_no_badge_at_all() -> None:
    rendered = MatchCardResponse.from_domain(a_card()).model_dump()
    assert rendered["fit"] is None


def test_a_live_claim_and_the_clock_agree_because_one_rule_produced_both() -> None:
    """`finishPaying` and the five minutes, composed by the server.

    The claim's presence is the fact the client needs — a card under a claim shows
    no exit control, and its clock is filled even on a shelf where every other
    card's is empty. It is never asked to infer that from the act code.
    """

    lapses = AT + timedelta(minutes=5)
    rendered = MatchCardResponse.from_domain(
        a_card(
            act=ActCode.FINISH_PAYING,
            clock=lapses,
            seat_claim=SeatClaim(expires_at=lapses),
            may_depart=False,
        )
    ).model_dump()

    assert rendered["act"] == "finishPaying"
    assert rendered["seat_claim"]["expires_at"] == lapses
    assert rendered["clock"] == lapses
    # Abandoning a payment must not be dressed as leaving.
    assert rendered["may_depart"] is False


def test_the_hold_reason_crosses_as_one_of_five_and_never_as_a_sentence() -> None:
    rendered = MatchCardResponse.from_domain(
        a_card(
            situation=SituationHalf(
                situation=Situation.HELD_SOFT,
                facts=some_facts(hold=HoldNote(reason=CardHoldReason.FAR)),
            )
        )
    ).model_dump()

    assert rendered["situation"]["facts"]["hold"] == {
        "reason": CardHoldReason.FAR,
        # The hold's own age, and only a reclaimed hold has one. A far-tier hold
        # that is still being kept has not aged out of anything.
        "age_minutes": None,
    }
    assert "note" not in rendered["situation"]["facts"]["hold"]


def test_a_reclaimed_hold_names_its_real_age_and_never_the_clubs_cap() -> None:
    """`heldStale` carries `now - heldSince`, which is the number that is true.

    A hold that has sat seventy-one hours under a forty-eight-hour cap says
    seventy-one: the card is where the marketplace's promise is being weakened,
    and it is the last place to print a number that is not the one meant.
    """

    rendered = MatchCardResponse.from_domain(
        a_card(
            situation=SituationHalf(
                situation=Situation.HELD_STALE,
                facts=some_facts(
                    hold=HoldNote(reason=CardHoldReason.STALE, age_minutes=71 * 60)
                ),
            )
        )
    ).model_dump()

    assert rendered["situation"]["facts"]["hold"]["age_minutes"] == 71 * 60


def test_every_card_counts_in_money_and_the_numbers_reach_the_wire() -> None:
    """The counting is the situation half's largest fact and it is sent, whole.

    Asserted on the rendered document rather than on the domain value: a
    ``from_domain`` that dropped a number, or built one of its own, is a card
    telling four people a match is a quarter full while a seat may still lapse
    — and nothing about the composed screen would look different.
    """

    rendered = MatchCardResponse.from_domain(
        a_card(
            situation=SituationHalf(
                situation=Situation.FORMING_HELD,
                facts=some_facts(counts=SeatCounts(seats=4, paid=2, held=1)),
            )
        )
    ).model_dump()

    assert rendered["situation"]["facts"]["counts"] == {
        "seats": 4,
        "paid": 2,
        "held": 1,
        # Nobody has played yet, and a number here would be a claim about the
        # future rather than a count of anything.
        "turned_up": None,
    }


def test_a_played_card_sends_who_turned_up_as_its_own_number() -> None:
    rendered = MatchCardResponse.from_domain(
        a_card(
            situation=SituationHalf(
                situation=Situation.PLAYED_NO_SHOW,
                facts=some_facts(
                    counts=SeatCounts(seats=4, paid=4, held=0, turned_up=3)
                ),
            )
        )
    ).model_dump()

    counts = rendered["situation"]["facts"]["counts"]
    assert (counts["turned_up"], counts["seats"]) == (3, 4)


def test_the_courts_total_crosses_beside_the_viewers_own_share() -> None:
    """One is the court's and has no audience; the other is written for her."""

    rendered = MatchCardResponse.from_domain(
        a_card(
            price=Money(amount=grosze(3800)),
            situation=SituationHalf(
                situation=Situation.CONFIRMED,
                facts=some_facts(court_total=Money(amount=grosze(15200))),
            ),
        )
    ).model_dump()

    assert rendered["price"]["amount"] == 3800
    assert rendered["situation"]["facts"]["court_total"]["amount"] == 15200


def test_a_person_card_has_no_situation_no_clock_and_no_price() -> None:
    rendered = PersonCardResponse.from_domain(
        PersonCard(player_id=uuid4(), stamp=1, nickname="kuba", level=A_LEVEL)
    ).model_dump()

    assert set(rendered) == {
        "card_type",
        "player_id",
        "stamp",
        "nickname",
        "level",
    }
    assert rendered["card_type"] == "person"
    # A Level and the quiet marker, never a second number: onboarding cannot
    # produce Confidence above 30 %, and printing that percentage beside the
    # Level is the second gauge ADR-0037 refused.
    assert rendered["level"] == {"value": 2.7, "provisional": True}
    assert "confidence" not in rendered["level"]


def test_a_person_card_cannot_be_built_without_a_Level() -> None:
    # **Required**, and asserted structurally because every construction in the
    # suite supplies one — an optional Level would compile, stay green, and be a
    # hole for a state the retrieval cannot produce, which is exactly the defect
    # one card type with holes would have had.
    with pytest.raises(TypeError):
        PersonCard(player_id=uuid4(), stamp=1, nickname="kuba")  # type: ignore[call-arg]


def test_a_club_card_has_no_situation_no_clock_and_no_price() -> None:
    rendered = ClubCardResponse.from_domain(
        ClubCard(club_id=uuid4(), stamp=1, name="Padel Kraków", distance_km=2)
    ).model_dump()

    assert set(rendered) == {"card_type", "club_id", "stamp", "name", "distance_km"}
    assert rendered["card_type"] == "club"


def test_a_shelf_carries_a_code_a_caption_code_and_cards_and_no_title() -> None:
    rendered = ShelfResponse.from_domain(
        Shelf(
            code=ShelfCode.BEST_FIT,
            caption=CaptionCode.UNDECLARED_PREFERENCES,
            cards=(
                a_card(),
                PersonCard(player_id=uuid4(), stamp=1, nickname="ola", level=A_LEVEL),
            ),
        )
    ).model_dump()

    assert set(rendered) == {"block_type", "code", "caption", "cards"}
    # The shelves list may also hold a door, so each entry says which it is.
    assert rendered["block_type"] == "shelf"
    assert rendered["code"] == "bestFit"
    assert rendered["caption"] == "undeclaredPreferences"
    # No title string, and no tail card — the client appends that and routes on
    # the shelf code and the sport it already holds.
    assert "title" not in rendered
    assert "tail" not in rendered


def test_a_shelf_discriminates_its_cards_by_the_thing_they_are_about() -> None:
    rendered = ShelfResponse.from_domain(
        Shelf(
            code=ShelfCode.NEW_PLAYERS,
            cards=(
                a_card(),
                PersonCard(player_id=uuid4(), stamp=1, nickname="ola", level=A_LEVEL),
                ClubCard(club_id=uuid4(), stamp=1, name="Padel Kraków"),
            ),
        )
    ).model_dump()

    assert [card["card_type"] for card in rendered["cards"]] == [
        "match",
        "person",
        "club",
    ]
    # Never by position and never by the shelf: one match may appear on more than
    # one shelf, and under thing identity one answer corrects every copy.
    assert "index" not in rendered["cards"][0]


def test_a_shelf_has_no_stamp_because_a_shelf_is_never_in_an_update() -> None:
    rendered = ShelfResponse.from_domain(Shelf(code=ShelfCode.NEW_CLUBS)).model_dump()
    assert "stamp" not in rendered


def test_the_envelope_is_three_regions_and_one_viewer_fact() -> None:
    rendered = NowResponse.from_domain(
        NowScreen(
            offers=OffersRegion(stamp=1),
            your_matches=EnrolledRegion(stamp=1),
            shelves=ShelvesRegion(stamp=1),
            sports=frozenset(),
        )
    ).model_dump()

    assert set(rendered) == {"offers", "your_matches", "shelves", "debt"}
    # No screen-level stamp: a screen is never replaced as a unit except by a
    # compose, and a compose is three stamped regions arriving together.
    assert "stamp" not in rendered
    assert "server_time" not in rendered
    # What `all` resolved to is the composer's, not the wire's.
    assert "sports" not in rendered


def test_the_debt_line_is_an_amount_a_currency_and_one_boolean() -> None:
    rendered = NowResponse.from_domain(
        NowScreen(
            offers=OffersRegion(stamp=1),
            your_matches=EnrolledRegion(stamp=1),
            shelves=ShelvesRegion(stamp=1),
            sports=frozenset(),
            debt=DebtLine(owed=Money(amount=grosze(3000)), blocked=True),
        )
    ).model_dump()

    assert set(rendered["debt"]) == {"owed", "blocked"}
    assert rendered["debt"]["owed"] == {"amount": 3000, "currency": Currency.PLN}
    assert rendered["debt"]["blocked"] is True
    # Not a list of blocked acts: that would invent a vocabulary to describe two
    # things nothing else in the product would ever read.
    assert "blocked_acts" not in rendered["debt"]


def test_each_region_carries_its_own_stamp() -> None:
    rendered = NowResponse.from_domain(
        NowScreen(
            offers=OffersRegion(stamp=7),
            your_matches=EnrolledRegion(stamp=8),
            shelves=ShelvesRegion(stamp=9),
            sports=frozenset(),
        )
    ).model_dump()

    assert rendered["offers"]["stamp"] == 7
    assert rendered["your_matches"]["stamp"] == 8
    assert rendered["shelves"]["stamp"] == 9
