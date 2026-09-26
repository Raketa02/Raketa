from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from app.modules.groups.application.commands import SearchGroupsToJoinCommand
from app.modules.groups.application.views import JoinSearchResults, club_cards
from app.modules.groups.domain.home_club_search import (
    ClubPage,
    in_search_order,
    page_of,
)
from app.modules.groups.domain.join_search import (
    ReadAs,
    groups_to_read,
    matched_cards,
)
from app.modules.groups.domain.link import PastedLink, link_in
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupDirectory,
    GroupFaces,
    GroupListing,
    HomeClubs,
    RatedGroupMembers,
    ReaderAreas,
)
from app.modules.groups.domain.value_objects import SearchText


class SearchGroupsToJoin:
    """*Join a group*'s one field: a club, a district, a group's name or a
    group link, answered as club cards with groups inside (``docs/adr/0183``
    §9, ``domain/join_search.py``).

    **A link is read before anything else**, and once the text holds one it is
    searched for nothing but that link: a WhatsApp message pasted whole has
    words around the link that would otherwise match clubs, and the player
    pasted it for the group.

    **A blank field is not a search** and answers nothing (``SearchText``).

    The whole match is ordered before a page is cut, because *nearest first* is
    a property of the answer and not of a page; then only the page's groups are
    read, with their members, their dots, who runs the official ones and every
    name on an *approves joins* line — one question each about all of them.
    """

    def __init__(
        self,
        *,
        clubs: HomeClubs,
        areas: ReaderAreas,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        administrators: GroupAdministrators,
    ) -> None:
        self._clubs = clubs
        self._areas = areas
        self._directory = directory
        self._ratings = ratings
        self._faces = faces
        self._administrators = administrators

    async def execute(self, command: SearchGroupsToJoinCommand) -> JoinSearchResults:
        typed = SearchText(command.text)
        if typed.is_blank:
            return _nothing(ReadAs.TEXT)
        link = link_in(typed.value)
        if link is not None:
            return await self._by_link(link, command)
        return await self._by_text(typed.value, command)

    async def _by_link(
        self, link: PastedLink, command: SearchGroupsToJoinCommand
    ) -> JoinSearchResults:
        """Exactly the group the link names, in its club's card — or nothing
        at that link, for a code no group has."""

        listing = (
            None if link.code is None else await self._directory.with_code(link.code)
        )
        if listing is None:
            return _nothing(ReadAs.LINK)
        clubs = await self._clubs.by_id([listing.home_club_id])
        page = page_of(
            in_search_order(
                list(clubs.values()), await self._areas.of(command.reader_id)
            ),
            command.page,
        )
        return await self._answer(
            page, {listing.home_club_id: [listing]}, command, ReadAs.LINK
        )

    async def _by_text(
        self, text: str, command: SearchGroupsToJoinCommand
    ) -> JoinSearchResults:
        """Clubs by name or district with every group at them, and groups by
        name inside their clubs' cards."""

        by_club = await self._clubs.matching(text)
        by_group_name = await self._directory.named(text)
        found_by_club = {club.id for club in by_club}
        cards = matched_cards(
            by_club,
            by_group_name,
            await self._clubs.by_id(set(by_group_name) - found_by_club),
        )
        page = page_of(
            in_search_order(
                [card.club for card in cards], await self._areas.of(command.reader_id)
            ),
            command.page,
        )

        to_read = groups_to_read(cards, [placed.club.id for placed in page.clubs])
        groups_at: dict[UUID, list[GroupListing]] = {
            club_id: list(listings)
            for club_id, listings in (
                await self._directory.listings_at(to_read.every_group_at)
            ).items()
        }
        for listing in (await self._directory.listings(to_read.only)).values():
            groups_at.setdefault(listing.home_club_id, []).append(listing)
        return await self._answer(page, groups_at, command, ReadAs.TEXT)

    async def _answer(
        self,
        page: ClubPage,
        groups_at: Mapping[UUID, Sequence[GroupListing]],
        command: SearchGroupsToJoinCommand,
        read_as: ReadAs,
    ) -> JoinSearchResults:
        return JoinSearchResults(
            clubs=await club_cards(
                page,
                groups_at,
                reader_id=command.reader_id,
                ratings=self._ratings,
                faces=self._faces,
                administrators=self._administrators,
            ),
            next_page=page.next_page,
            read_as=read_as,
        )


def _nothing(read_as: ReadAs) -> JoinSearchResults:
    return JoinSearchResults(clubs=(), next_page=None, read_as=read_as)
