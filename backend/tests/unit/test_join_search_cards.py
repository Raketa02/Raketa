"""Which club cards join search's text finds, and what each carries
(``domain/join_search.py``, ``docs/adr/0183`` §9) — the rule without the
database: a club that matched carries every group at it, a group that matched
by name comes alone inside its club's card, and a page reads only its own."""

from __future__ import annotations

from uuid import uuid4

from app.kernel import Sport
from app.modules.groups.domain.join_search import (
    GroupsToRead,
    MatchedCard,
    groups_to_read,
    matched_cards,
)
from app.modules.groups.domain.ports import HomeClub


def a_club(name: str) -> HomeClub:
    return HomeClub(
        id=uuid4(),
        name=name,
        district="Grzegórzki",
        sports=(Sport.PADEL,),
        latitude=50.06,
        longitude=19.94,
    )


OGRODY = a_club("Ogrody 33")
WISLA = a_club("Wisła Park")
BONARKA = a_club("Bonarka Arena")


def test_a_club_that_matched_carries_every_group_even_one_that_matched_by_name():
    fans = uuid4()

    cards = matched_cards([OGRODY], {OGRODY.id: frozenset({fans})}, {})

    assert cards == [MatchedCard(club=OGRODY, only=None)]


def test_a_group_matched_by_name_comes_alone_inside_its_club_s_card():
    fans, other = uuid4(), uuid4()

    cards = matched_cards(
        [OGRODY],
        {WISLA.id: frozenset({fans}), BONARKA.id: frozenset({other})},
        {WISLA.id: WISLA, BONARKA.id: BONARKA},
    )

    assert {card.club.name: card.only for card in cards} == {
        "Ogrody 33": None,
        "Wisła Park": frozenset({fans}),
        "Bonarka Arena": frozenset({other}),
    }


def test_a_club_that_cannot_be_placed_is_left_out_rather_than_drawn_headless():
    cards = matched_cards([], {WISLA.id: frozenset({uuid4()})}, {})

    assert cards == []


def test_a_page_reads_every_group_at_its_matched_clubs_and_only_the_named_ones():
    fans = uuid4()
    cards = [
        MatchedCard(club=OGRODY, only=None),
        MatchedCard(club=WISLA, only=frozenset({fans})),
        MatchedCard(club=BONARKA, only=None),
    ]

    to_read = groups_to_read(cards, [OGRODY.id, WISLA.id])

    # Bonarka is on another page, and nothing of it is read.
    assert to_read == GroupsToRead(every_group_at=(OGRODY.id,), only=frozenset({fans}))
