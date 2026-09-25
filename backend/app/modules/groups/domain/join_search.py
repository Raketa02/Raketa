"""Join search: which club cards a piece of text finds, and what each carries.

``docs/adr/0183`` §9. One field on *Join a group* matches four things, and **the
answer is always club cards with groups inside**, because a group is always
shown where it lives:

- **a club's name or district** finds the club's card with **every** group at it
  — and a club with none, which is *no groups here yet*;
- **a group's name** finds that group inside its club's card, **only the groups
  that matched** when the club itself did not;
- **a group link** — any text containing ``/join/<code>`` (``link.py``) — finds
  exactly that group, and nothing else, even if the rest of the text would have
  matched something;
- **a link that leads nowhere** finds nothing, and says it was a link.

The order is home-club search's (``home_club_search.py``): nearest first by the
printed distance, then by name, twenty to a page — or A–Z with no distance for a
reader with no Location area.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import final
from uuid import UUID

from app.modules.groups.domain.ports import HomeClub


class ReadAs(StrEnum):
    """What the text was read as — so an empty answer can say which empty it is:
    *no match for "…"* for text, *nothing at that link* for a link (#500
    stories 37 and 38)."""

    TEXT = "TEXT"
    LINK = "LINK"


@final
@dataclass(frozen=True, slots=True)
class MatchedCard:
    """One club the text found, and which of its groups the card carries:
    **every** group at it when ``only`` is ``None`` — the club matched — or only
    these, which matched by their own name."""

    club: HomeClub
    only: frozenset[UUID] | None


def matched_cards(
    by_club: Sequence[HomeClub],
    by_group_name: Mapping[UUID, frozenset[UUID]],
    clubs_of_groups: Mapping[UUID, HomeClub],
) -> list[MatchedCard]:
    """The cards text finds: every club that matched, carrying all its groups,
    and the club of every group that matched by name and whose club did not,
    carrying only those groups.

    **A club that matched carries all its groups even when some of them also
    matched by name** — the card was found by the club, and a card found by the
    club shows the club. ``by_group_name`` is keyed by home club, and a club
    ``clubs_of_groups`` cannot place is left out rather than drawn without a
    header. Unordered: ordering is ``in_search_order``'s.
    """

    matched = {club.id for club in by_club}
    return [MatchedCard(club=club, only=None) for club in by_club] + [
        MatchedCard(club=clubs_of_groups[club_id], only=group_ids)
        for club_id, group_ids in by_group_name.items()
        if club_id not in matched and club_id in clubs_of_groups
    ]


@final
@dataclass(frozen=True, slots=True)
class GroupsToRead:
    """What one page of cards needs read: **every** group at these clubs, and
    these groups by id — the ones that matched by name at a club that did not."""

    every_group_at: tuple[UUID, ...]
    only: frozenset[UUID]


def groups_to_read(
    cards: Sequence[MatchedCard], on_page: Collection[UUID]
) -> GroupsToRead:
    """The groups the cards of these clubs carry — asked once the page is cut,
    so a search reads the members of the page it serves and of nothing else."""

    wanted = set(on_page)
    return GroupsToRead(
        every_group_at=tuple(
            card.club.id
            for card in cards
            if card.club.id in wanted and card.only is None
        ),
        only=frozenset(
            group_id
            for card in cards
            if card.club.id in wanted and card.only is not None
            for group_id in card.only
        ),
    )
