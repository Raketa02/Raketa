"""The Friend link — read it, replace it, open somebody's, and the public
site's read of a code (``docs/adr/0202`` §1–§2; the mechanics §4; #748).

**Opening a link never makes friends by itself** (Q37). As a signed-in player it
records **the owner's request to the opener**, made by ``LINK`` — *Invited you to
Rakieta* on the opener's Home, with Accept and Not now, like any request — for a
new player who signed up through it and for one who already had the app alike.
A request by link is **the one way in from outside your groups**, so it asks for
no group in common. Unless:

- **the opener is the owner**: nothing, and the answer is ``NONE``, the reader's
  relation to themselves on every surface;
- **they are already friends**: nothing, ``FRIEND``;
- **the opener had asked the owner**: the two requests cross, friends at once —
  the aggregate's own rule — ``FRIEND``;
- **the owner had already asked the opener**: no second request, ``ASKED_YOU``.
  **One the opener set aside comes back to Home** — the call the mechanics §12
  left to this ticket: the opener opened the owner's link, which is asking to see
  the owner's request, and *Not now* was theirs to take back. **A request hidden
  from them as ``unseen`` stays hidden** — asked while they had blocked the
  owner, it is one *they never see*, and unblocking brings nothing back (the
  mechanics §3.5): showing it, with the group it named, would tell them the owner
  asked across their block. The answer is ``ASKED_YOU`` all the same;
- **the owner blocked the opener**: **swallowed** — nothing is recorded, and the
  answer is ``ASKED_YOU``, exactly what a request made reads, so the opener lands
  on a Home with nothing on it. The one place a block could be guessed, and the
  cost ADR-0202 names; read live, from the owner's own blocks, and never
  answered;
- **the opener blocked the owner**: ``unblock_them_first``, as asking somebody you
  blocked is — a block of the reader's own, which the reader may always read;
- **the code was replaced, or never existed**: ``friend_link_not_found``.

**The link is made the first time its owner reads it**, so a route that reads is
a route that may write once. Two first reads that race collide on the stream and
the loser is ``concurrent_modification``; a retry reads the winner's code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.friends.domain.errors import FriendLinkNotFound, UnblockThemFirst
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.link import FriendLinkCode
from app.modules.friends.domain.ports import (
    FriendFace,
    FriendFaces,
    FriendLinkCodes,
    FriendLinkRepository,
    FriendshipRepository,
    ReadersBlocks,
)
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin


class _YourLink:
    """Reading your link and taking a New link share their collaborators: the
    owner's stream, and the codes every link ever carried."""

    def __init__(
        self,
        *,
        links: FriendLinkRepository,
        codes: FriendLinkCodes,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._links = links
        self._codes = codes
        self._uow = uow
        self._clock = clock


@final
class ReadYourFriendLink(_YourLink):
    """The reader's link — **made on their first read of it**, the same code on
    every read after."""

    async def execute(self, owner: UUID) -> FriendLinkCode:
        link = await self._links.load(owner)
        if link.code is not None:
            return link.code
        code = link.make(code=await self._codes.mint(), at=instant(self._clock.now()))
        await self._links.save(link)
        await self._uow.commit()
        return code


@final
class ReplaceYourFriendLink(_YourLink):
    """**New link** — a fresh code, and the old one dead at once, in the app and
    on the public site. Requests already made through the old one stay as they
    are: they are the owner's requests, and the link was only how they began."""

    async def execute(self, owner: UUID) -> FriendLinkCode:
        link = await self._links.load(owner)
        code = link.replace(
            code=await self._codes.mint(), at=instant(self._clock.now())
        )
        await self._links.save(link)
        await self._uow.commit()
        return code


@final
@dataclass(frozen=True, slots=True)
class OpenLinkCommand:
    """The opener opened ``code`` — whatever followed ``/f/``, unchecked."""

    opener_id: UUID
    code: str


@final
class OpenAFriendLink:
    def __init__(
        self,
        *,
        codes: FriendLinkCodes,
        friendships: FriendshipRepository,
        blocks: ReadersBlocks,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._codes = codes
        self._friendships = friendships
        self._blocks = blocks
        self._uow = uow
        self._clock = clock

    async def execute(self, command: OpenLinkCommand) -> FriendRelation:
        """The opener's relation to the owner once it is opened: ``ASKED_YOU``
        — their request is on Home — ``FRIEND``, or ``NONE`` for your own."""

        opener = command.opener_id
        owner = await _owner_of(self._codes, command.code)
        if owner == opener:
            return FriendRelation.NONE
        if owner in await self._blocks.blocked_by(opener):
            raise UnblockThemFirst()
        if opener in await self._blocks.blocked_by(owner):
            # Swallowed: what a request made reads, and nothing recorded.
            return FriendRelation.ASKED_YOU

        friendship = await self._friendships.load(owner, opener)
        if friendship.are_friends:
            return FriendRelation.FRIEND
        at = instant(self._clock.now())
        request = friendship.request
        if request is not None and request.requester_id == owner:
            friendship.bring_back(by=opener, at=at)
        else:
            # A new request, or one crossing the opener's own: friends at once.
            friendship.ask(
                requester=owner, where=Where(made_from=RequestOrigin.LINK), at=at
            )
        await self._friendships.save(friendship)
        await self._uow.commit()
        # The owner's request stands — new, brought back, or one hidden from the
        # opener, which reads exactly as any other: never ``NONE``, the answer to
        # your own link.
        return (
            FriendRelation.FRIEND
            if friendship.are_friends
            else (FriendRelation.ASKED_YOU)
        )


@final
class ReadAFriendLink:
    """What the public site's ``/f/<code>`` page draws: **the owner's nickname
    and face, and nothing else about them** — nobody signs in to read it."""

    def __init__(self, *, codes: FriendLinkCodes, faces: FriendFaces) -> None:
        self._codes = codes
        self._faces = faces

    async def execute(self, code: str) -> FriendFace:
        owner = await _owner_of(self._codes, code)
        face = (await self._faces.faces_of([owner]))[owner]
        if face.nickname is None:
            # An account gone: its link leads nowhere.
            raise FriendLinkNotFound()
        return face


async def _owner_of(codes: FriendLinkCodes, typed: str) -> UUID:
    """Whose link ``typed`` is now — one refusal for a code replaced, one never
    made, and one that could be no link's."""

    code = FriendLinkCode.read(typed)
    owner = None if code is None else await codes.owner_of(code)
    if owner is None:
        raise FriendLinkNotFound()
    return owner
