"""Friends among the named accounts (#745; ``docs/adr/0202`` §1–§2): friends made
both ways, requests open both ways, a request set aside, and a block that ended
a friendship and hides a request made since.

**Through the aggregates, as a phone makes them** — ``AskToBeFriends``,
``AcceptFriendRequest``, ``SetAsideFriendRequest`` and the block route's own
``BlockPlayer`` — each from a group the pair share, with that group's padel, so
every card reads *With you in Czwartkowy padel · Padel …*. Nothing here opens a
table.

**The protagonist's screens are the point** (``THE_POPULATED_PLAYER``):

- **Friends**: ``rating-well-established``, who accepted her request, and
  ``the-one-sport-player``, whose request crossed hers;
- **Home's FRIEND REQUESTS**: ``rating-barely-established`` asked her;
- **Asked you**, set aside: ``assessment-completed`` asked, and she said *Not
  now* — off Home, still open, still hers to accept;
- **You asked**: she asked ``brand-new-player``, who has not answered.

**The block case is two other accounts**, so nothing she is dealt moves: the
``blank-week-player`` and ``rated-in-every-sport`` were friends in *Błonia po
pracy* until the first blocked the second; the friendship ended when the block
was delivered, and ``rated-in-every-sport`` asked again — and reads *request
sent* for ever while the blocker sees nothing.

**Every named account has a Friend link** (#748), read through
``ReadYourFriendLink`` as the Add friends sheet reads it — which makes it on the
first run and reads the same code on every run after — and printed in the
report, so a developer can open one on a phone signed in as somebody else.

**After every layer that deals and before the screens**, because a block keeps
two people off one court, and the block's delivery is drained here so the
friendship has ended before the second request is made. **Re-running asks
nobody twice**: each pair is read first, and only what is missing is done.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_block_query,
    build_block_repository,
    build_domain_event_store,
    build_event_publisher,
    build_friendship_repository,
    build_group_directory,
    build_read_relations,
    build_read_requests_on_home,
    build_read_your_friend_link,
    build_readers_blocks,
    build_readers_groups,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.blocks.application.block_player import BlockPlayer
from app.modules.blocks.application.commands import BlockPlayerCommand
from app.modules.friends.application.commands import AnswerCommand, AskCommand
from app.modules.friends.application.requests import (
    AcceptFriendRequest,
    AskToBeFriends,
    SetAsideFriendRequest,
)
from app.modules.friends.domain.ports import FriendshipRepository
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.link import friend_link_url
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.seeds.catalog import (
    ACCOUNTS,
    ASSESSMENT_COMPLETED,
    BRAND_NEW_PLAYER,
    RATED_IN_EVERY_SPORT,
    RATING_BARELY_ESTABLISHED,
    RATING_WELL_ESTABLISHED,
    THE_BLANK_WEEK_PLAYER,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.clock import FixedClock, hours_before
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.rooms import deliver_everything_told

#: The groups the pairs are asked from — each shared by the pair.
CZWARTKOWY: Final = "Czwartkowy padel"
BONARKA: Final = "Bonarka weekend"
BLONIA: Final = "Błonia po pracy"


@final
@dataclass(frozen=True, slots=True)
class SeededFriends:
    #: Her friends, by slug.
    friends: tuple[str, ...]
    #: Who asked her and waits on her Home, by slug.
    on_her_home: tuple[str, ...]
    #: Who asked her and was set aside.
    set_aside: tuple[str, ...]
    #: Whom she asked.
    she_asked: tuple[str, ...]
    #: Whether the block case stands: friends ended by a block, a request since.
    block_case: bool
    #: Every named account's Friend link, by slug.
    links: Mapping[str, str]


def _friendships(session: AsyncSession) -> FriendshipRepository:
    """The repository the three friend use cases take — the one aggregate this
    layer writes, besides the block."""

    return build_friendship_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


@final
class _Acts:
    """The acts this layer takes, each in a session of its own and on a clock
    stopped some hours before the run, so Home's newest-first has an order."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        ids: dict[str, UUID],
        groups: dict[str, UUID],
        now: Instant,
    ) -> None:
        self._sessions = session_factory
        self._ids = ids
        self._groups = groups
        self._now = now

    async def relation(self, one: SeedAccount, other: SeedAccount) -> FriendRelation:
        async with self._sessions() as session:
            relations = await build_read_relations(session).relations_of(
                self._ids[one.slug], [self._ids[other.slug]]
            )
        return relations[self._ids[other.slug]]

    async def ask(
        self, asker: SeedAccount, asked: SeedAccount, *, group: str, hours: int
    ) -> None:
        async with self._sessions() as session:
            await AskToBeFriends(
                friendships=_friendships(session),
                blocks=build_readers_blocks(session),
                groups=build_readers_groups(session),
                uow=build_unit_of_work(session),
                clock=hours_before(self._now, hours),
            ).execute(
                AskCommand(
                    requester_id=self._ids[asker.slug],
                    addressee_id=self._ids[asked.slug],
                    where=Where(
                        made_from=RequestOrigin.MEMBERS,
                        group_id=self._groups[group],
                        sport=Sport.PADEL,
                    ),
                )
            )

    async def accept(
        self, reader: SeedAccount, asker: SeedAccount, *, hours: int
    ) -> None:
        async with self._sessions() as session:
            await AcceptFriendRequest(
                friendships=_friendships(session),
                blocks=build_readers_blocks(session),
                uow=build_unit_of_work(session),
                clock=hours_before(self._now, hours),
            ).execute(self._answer(reader, asker))

    async def set_aside(
        self, reader: SeedAccount, asker: SeedAccount, *, hours: int
    ) -> None:
        async with self._sessions() as session:
            await SetAsideFriendRequest(
                friendships=_friendships(session),
                blocks=build_readers_blocks(session),
                uow=build_unit_of_work(session),
                clock=hours_before(self._now, hours),
            ).execute(self._answer(reader, asker))

    async def has_blocked(self, blocker: SeedAccount, blocked: SeedAccount) -> bool:
        async with self._sessions() as session:
            own = await build_block_query(session).blocks_made_by(
                self._ids[blocker.slug]
            )
        return any(block.blocked_id == self._ids[blocked.slug] for block in own)

    async def block(
        self, blocker: SeedAccount, blocked: SeedAccount, *, hours: int
    ) -> None:
        """The block route's own use case."""

        async with self._sessions() as session:
            await BlockPlayer(
                blocks=build_block_repository(
                    event_store=build_domain_event_store(session),
                    events=build_event_publisher(session),
                ),
                uow=build_unit_of_work(session),
                clock=hours_before(self._now, hours),
            ).execute(
                BlockPlayerCommand(
                    blocker_id=self._ids[blocker.slug],
                    blocked_id=self._ids[blocked.slug],
                )
            )

    def _answer(self, reader: SeedAccount, asker: SeedAccount) -> AnswerCommand:
        return AnswerCommand(
            reader_id=self._ids[reader.slug], requester_id=self._ids[asker.slug]
        )


async def write_the_friends(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    money: SeedMoney = THE_FAKE,
) -> SeededFriends:
    her = THE_POPULATED_PLAYER
    async with session_factory() as session:
        ids = await _ids(session)
        groups = await _groups(session, ids)
    acts = _Acts(session_factory, ids=ids, groups=groups, now=now)

    # Friends, accepted: she asked, a week ago, and was answered the next day.
    if await acts.relation(her, RATING_WELL_ESTABLISHED) is FriendRelation.NONE:
        await acts.ask(her, RATING_WELL_ESTABLISHED, group=CZWARTKOWY, hours=7 * 24)
    if await acts.relation(her, RATING_WELL_ESTABLISHED) is FriendRelation.SENT:
        await acts.accept(RATING_WELL_ESTABLISHED, her, hours=6 * 24)
    # Friends, crossed: each asked the other before either answered.
    if await acts.relation(her, THE_ONE_SPORT_PLAYER) is FriendRelation.NONE:
        await acts.ask(THE_ONE_SPORT_PLAYER, her, group=CZWARTKOWY, hours=5 * 24)
    if await acts.relation(her, THE_ONE_SPORT_PLAYER) is FriendRelation.ASKED_YOU:
        await acts.ask(her, THE_ONE_SPORT_PLAYER, group=CZWARTKOWY, hours=5 * 24 - 1)
    # Set aside: asked two days ago, *Not now* the same evening.
    if await acts.relation(her, ASSESSMENT_COMPLETED) is FriendRelation.NONE:
        await acts.ask(ASSESSMENT_COMPLETED, her, group=BONARKA, hours=48)
    if await acts.relation(her, ASSESSMENT_COMPLETED) is FriendRelation.ASKED_YOU:
        await acts.set_aside(her, ASSESSMENT_COMPLETED, hours=44)
    # On her Home: asked this morning.
    if await acts.relation(her, RATING_BARELY_ESTABLISHED) is FriendRelation.NONE:
        await acts.ask(RATING_BARELY_ESTABLISHED, her, group=CZWARTKOWY, hours=3)
    # She asked, and nobody answered.
    if await acts.relation(her, BRAND_NEW_PLAYER) is FriendRelation.NONE:
        await acts.ask(her, BRAND_NEW_PLAYER, group=BONARKA, hours=26)

    block_case = await _the_block_case(session_factory, acts, money=money)
    links = await _their_links(session_factory, settings=settings, now=now)

    async with session_factory() as session:
        home = await build_read_requests_on_home(
            session, settings=settings, clock=FixedClock(at=now)
        ).execute(ids[her.slug])
        relations = await build_read_relations(session).relations_of(
            ids[her.slug], list(ids.values())
        )
    slug_of = {player_id: slug for slug, player_id in ids.items()}
    on_home = tuple(slug_of[card.requester_id] for card in home)
    seeded = SeededFriends(
        friends=_with(relations, FriendRelation.FRIEND, slug_of),
        on_her_home=on_home,
        set_aside=tuple(
            slug
            for slug in _with(relations, FriendRelation.ASKED_YOU, slug_of)
            if slug not in on_home
        ),
        she_asked=_with(relations, FriendRelation.SENT, slug_of),
        block_case=block_case,
        links=links,
    )
    _refuse_a_seed_that_lies(seeded)
    return seeded


async def _the_block_case(
    session_factory: async_sessionmaker[AsyncSession],
    acts: _Acts,
    *,
    money: SeedMoney,
) -> bool:
    """Friends in *Błonia po pracy* (created nine days ago) until the block four
    days ago — **delivered before the second request**, which is what ends the
    friendship — and the request made since, yesterday."""

    blocker, blocked = THE_BLANK_WEEK_PLAYER, RATED_IN_EVERY_SPORT
    if await acts.relation(blocked, blocker) is not FriendRelation.SENT:
        if not await acts.has_blocked(blocker, blocked):
            if await acts.relation(blocked, blocker) is FriendRelation.NONE:
                await acts.ask(blocked, blocker, group=BLONIA, hours=8 * 24)
                await acts.accept(blocker, blocked, hours=7 * 24)
            await acts.block(blocker, blocked, hours=4 * 24)
        await deliver_everything_told(session_factory, money=money)
        await acts.ask(blocked, blocker, group=BLONIA, hours=24)
    return (
        await acts.relation(blocked, blocker) is FriendRelation.SENT
        and await acts.relation(blocker, blocked) is FriendRelation.NONE
    )


async def _their_links(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> dict[str, str]:
    """Every named account's link, read as the sheet reads it: made on the first
    run, the same code on every run after."""

    links: dict[str, str] = {}
    for account in ACCOUNTS:
        async with session_factory() as session:
            user = await build_user_repository(session).get_by_email(account.email)
            if user is None:
                raise RuntimeError(
                    f"{account.slug} is not registered — the accounts layer runs first"
                )
            code = await build_read_your_friend_link(
                session, clock=FixedClock(at=now)
            ).execute(user.id)
        links[account.slug] = friend_link_url(settings.PUBLIC_SITE_URL, code)
    return links


def _with(
    relations: Mapping[UUID, FriendRelation],
    relation: FriendRelation,
    slug_of: Mapping[UUID, str],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            slug_of[player]
            for player, standing in relations.items()
            if standing is relation
        )
    )


def _refuse_a_seed_that_lies(seeded: SeededFriends) -> None:
    """Every screen state this layer promises, read back — or the run fails by
    name."""

    expected = {
        "friends": (
            tuple(sorted((RATING_WELL_ESTABLISHED.slug, THE_ONE_SPORT_PLAYER.slug))),
            seeded.friends,
        ),
        "on her Home": ((RATING_BARELY_ESTABLISHED.slug,), seeded.on_her_home),
        "set aside": ((ASSESSMENT_COMPLETED.slug,), seeded.set_aside),
        "she asked": ((BRAND_NEW_PLAYER.slug,), seeded.she_asked),
    }
    wrong = {what: (want, got) for what, (want, got) in expected.items() if want != got}
    unlinked = [
        account.slug for account in ACCOUNTS if account.slug not in seeded.links
    ]
    if unlinked:
        raise RuntimeError(f"the friends layer gave no Friend link to {unlinked}")
    if wrong or not seeded.block_case:
        raise RuntimeError(
            f"the friends layer did not reach its states: {wrong}, "
            f"block case {'stands' if seeded.block_case else 'missing'}"
        )


async def _ids(session: AsyncSession) -> dict[str, UUID]:
    users = build_user_repository(session)
    ids: dict[str, UUID] = {}
    for account in (
        THE_POPULATED_PLAYER,
        RATING_WELL_ESTABLISHED,
        THE_ONE_SPORT_PLAYER,
        ASSESSMENT_COMPLETED,
        RATING_BARELY_ESTABLISHED,
        BRAND_NEW_PLAYER,
        THE_BLANK_WEEK_PLAYER,
        RATED_IN_EVERY_SPORT,
    ):
        user = await users.get_by_email(account.email)
        if user is None:
            raise RuntimeError(
                f"{account.slug} is not registered — the accounts layer runs first"
            )
        ids[account.slug] = user.id
    return ids


async def _groups(session: AsyncSession, ids: dict[str, UUID]) -> dict[str, UUID]:
    """Each group the pairs are asked from, by name **among the groups of the
    account that owns it** — names are not unique, and a developer may make a
    second *Czwartkowy padel* by hand."""

    directory = build_group_directory(session)
    found: dict[str, UUID] = {}
    for name, owner in (
        (CZWARTKOWY, THE_POPULATED_PLAYER),
        (BONARKA, THE_POPULATED_PLAYER),
        (BLONIA, THE_BLANK_WEEK_PLAYER),
    ):
        listings = await directory.listings(await directory.groups_of(ids[owner.slug]))
        group = next(
            (listing.id for listing in listings.values() if listing.name.value == name),
            None,
        )
        if group is None:
            raise RuntimeError(f"{name} is not seeded — the groups layer runs first")
        found[name] = group
    return found


def friend_lines(seeded: SeededFriends) -> list[str]:
    """The report's section."""

    return [
        f"Friends — {THE_POPULATED_PLAYER.email}:",
        f"  friends: {', '.join(seeded.friends)}",
        f"  on her Home: {', '.join(seeded.on_her_home)}",
        f"  asked her, set aside: {', '.join(seeded.set_aside)}",
        f"  she asked: {', '.join(seeded.she_asked)}",
        f"  {THE_BLANK_WEEK_PLAYER.slug} blocked {RATED_IN_EVERY_SPORT.slug}, "
        "their friendship ended, and the request made since reads sent",
        "Friend links — open one signed in as somebody else:",
        *(f"  {slug}: {link}" for slug, link in seeded.links.items()),
    ]
