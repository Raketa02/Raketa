from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.friends.domain.relation import FriendRelation
from app.modules.groups.application.views import (
    GroupAtClub,
    NamedClub,
    at_clubs,
    face_of,
)
from app.modules.groups.domain.hottest import (
    AT_LEAST_PLAYERS,
    GAMES_WINDOW,
    NEW_WINDOW,
    GroupActivity,
    HeatTag,
    faces_to_show,
    hottest_groups,
)
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupBornGames,
    GroupDirectory,
    GroupFace,
    GroupFaces,
    HomeClubs,
    MemberRelations,
    RatedGroupMembers,
)
from app.modules.groups.domain.value_objects import GroupKind


@final
@dataclass(frozen=True, slots=True)
class HottestGroupCard:
    """One card of Hottest groups, carrying **everything its group sheet
    shows**, so the sheet needs no second read (``docs/adr/0204`` §11).

    ``group`` is the group as a club's card draws it for the reader — its row,
    its policy, their relation to it and whether they run it — **built by the
    one function the searches build theirs with**, so the card and a search
    row cannot disagree about a group. ``run_by`` is who answers its requests,
    as the sheet's *run by* says it: an official group's club — whoever runs
    it, and while nobody does (a call made while writing #790) — and a player
    group's Owner by their whole nickname, ``None`` for an Owner ``users`` can
    no longer name. ``faces`` are up to six, the reader's friends first, then
    the longest-standing members, never the reader; ``friends_count`` is every
    friend of the reader's in it now."""

    group: GroupAtClub
    run_by: str | None
    club: NamedClub
    games_this_week: int
    new_this_month: int
    heat_share: float
    tag: HeatTag | None
    faces: tuple[GroupFace, ...]
    friends_count: int


class ReadHottestGroups:
    """Home's *Hottest groups* (#792; the Home rows mechanics §5) — up to six of
    the groups with the most going on, **whether the reader is in them or
    not**, their own included.

    **Worked out on every read**: the heat of every group of three or more,
    from two counts — the members, and who of them joined in the last 30 days,
    off the groups projections; the games booked in each with a court time in
    the last 7 days, off Bookings' through ``GroupBornGames`` — and then the
    rule (``domain/hottest.py``). Only the six it keeps are read whole.

    **Nine questions at most, whatever the number of groups**: the counts, the
    games and the six listings; the three a club's card asks (``at_clubs``:
    every dot's ratings, who runs the official ones, every Owner's and
    runner's nickname); their clubs; and — one question each about the union
    — the reader's relation to every member and the faces drawn. A group page
    is still members-only: this read shows a group, never the way into it.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        games: GroupBornGames,
        clubs: HomeClubs,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        relations: MemberRelations,
        administrators: GroupAdministrators,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._games = games
        self._clubs = clubs
        self._ratings = ratings
        self._faces = faces
        self._relations = relations
        self._administrators = administrators
        self._clock = clock

    async def execute(self, reader_id: UUID) -> tuple[HottestGroupCard, ...]:
        now = self._clock.now()
        crowds = await self._directory.crowds(
            at_least=AT_LEAST_PLAYERS, joined_after=instant(now - NEW_WINDOW)
        )
        if not crowds:
            return ()
        games = await self._games.born_between(
            [crowd.group_id for crowd in crowds],
            after=instant(now - GAMES_WINDOW),
            by=now,
        )
        ranked = hottest_groups(
            GroupActivity(
                group_id=crowd.group_id,
                games_this_week=games.get(crowd.group_id, 0),
                new_this_month=crowd.new,
                players=crowd.players,
            )
            for crowd in crowds
        )
        listings = await self._directory.listings(
            [hot.activity.group_id for hot in ranked]
        )
        # A group deleted between the two reads is simply not drawn.
        shown = [
            (hot, listings[hot.activity.group_id])
            for hot in ranked
            if hot.activity.group_id in listings
        ]
        if not shown:
            return ()
        groups = [listing for _, listing in shown]

        drawn_at_club = await at_clubs(
            groups,
            reader_id=reader_id,
            ratings=self._ratings,
            faces=self._faces,
            administrators=self._administrators,
        )
        clubs = await self._clubs.by_id({listing.home_club_id for listing in groups})
        relations = await self._relations.relations_of(
            reader_id, {member for listing in groups for member in listing.members}
        )
        friends = frozenset(
            player
            for player, relation in relations.items()
            if relation is FriendRelation.FRIEND
        )
        chosen = {
            listing.id: faces_to_show(
                listing.members, friends=friends, reader=reader_id
            )
            for listing in groups
        }
        drawn = await self._faces.faces_of(
            {player for players in chosen.values() for player in players}
        )

        cards = []
        for hot, listing in shown:
            club = clubs[listing.home_club_id]
            group = drawn_at_club[listing.id]
            cards.append(
                HottestGroupCard(
                    group=group,
                    run_by=(
                        club.name
                        if listing.kind is GroupKind.OFFICIAL
                        else group.owner_nickname
                    ),
                    club=NamedClub(id=club.id, name=club.name),
                    games_this_week=hot.activity.games_this_week,
                    new_this_month=hot.activity.new_this_month,
                    heat_share=hot.share,
                    tag=hot.tag,
                    faces=tuple(
                        face_of(drawn, player) for player in chosen[listing.id]
                    ),
                    friends_count=len(friends.intersection(listing.members)),
                )
            )
        return tuple(cards)
