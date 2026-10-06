"""The things that entitle a reader to a record, one adapter each.

Three implementations of one port, in the **consumer's** infrastructure — the
shape ``sportsmanship`` takes over ``games``' directory, and for the same reason:
a provider publishes what it knows about its own subject, and the context that
wants it narrower does the narrowing. *Have I been shown this person* does not
become a method on somebody else's port.

**Each answers yes or no, and never with an id.** A game id or a group id would
be an identifier this answer is not about — and one more thing on a refusal
path that is supposed to say nothing.

**They are three because the entitlements are three, not because the stores
are** (#575): a court the pair were both on, a group they are both in, and a
group the reader runs that the subject is in. Every one is admitted under the
same gates, so the admission asks them in turn and stops at the first yes.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.games.domain.ports import GameDirectory
from app.modules.groups.domain.ports import GroupAdministrators, GroupDirectory


@final
class GamesTheyPlayed:
    """``PriorDisclosure`` over ``games``' directory. *We are on a court together.*

    A game the pair are both on — booked and still ahead, played, scored or
    argued over — is a game the platform put these two in front of each other
    for. There is no window here and no standing test; what is read is the
    court **as it stands**, so somebody who left a game before it was played is
    no longer on it.
    """

    def __init__(self, games: GameDirectory) -> None:
        self._games = games

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether the pair have shared a court, in any sport.

        **It asks *which games are mine* and never *which game is this*.** The
        directory answers about one player, so a court the reader was not on is
        not reachable through this read at all — the entitlement is the shape of
        the query rather than a check somebody remembered to write.
        """

        return any(
            subject_id in game.line_up.players
            for game in await self._games.playing(reader_id)
        )


@final
class GroupsTheyShare:
    """``PriorDisclosure`` over ``groups``' directory. *We are both in a group.*

    A group's Members lists everybody in it who plays the sport — face, name,
    Level, score — and promises *Press and hold anyone for the full record*
    (#514). A member who never played with them has been shown every one of
    them by the group and by nothing else (#529).

    **Membership as it stands, never as it was.** A game does not stop having
    happened; a group left is simply no longer one the pair are in, and Members
    stops listing whoever left. A Join request that waits is not membership
    either: the Owner reads the queue, and nothing there opens a record.
    """

    def __init__(self, groups: GroupDirectory) -> None:
        self._groups = groups

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether the pair are both in a group right now.

        **Two reads of one player's memberships each, and never a listing.**
        What the pair share is the intersection of the groups each is in, which
        says nothing about who else is in them.
        """

        return bool(
            set(await self._groups.groups_of(reader_id))
            & set(await self._groups.groups_of(subject_id))
        )


@final
class GroupsTheReaderRuns:
    """``PriorDisclosure`` over ``groups``' directory and who runs each
    official group now. *I run a group they are in.*

    An official group's Members is opened by the account running it, which is
    not a member (``docs/adr/0183`` §7) — so ``GroupsTheyShare`` never admits
    it, and every row it lists would open on ``record_unavailable`` (#566).

    **Who runs a group is ``groups``' answer, read through its own port**:
    ``GroupAdministrators`` is the one the Members list asks, so the list and
    the record it opens cannot come to two answers about who runs it — and a
    removed Administrator, or one the group was handed away from, runs nothing
    on the next read of either.
    """

    def __init__(
        self, groups: GroupDirectory, administrators: GroupAdministrators
    ) -> None:
        self._groups = groups
        self._administrators = administrators

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether the reader runs, now, any official group the subject is in.

        **Asked from the subject's side**: the groups they belong to, the
        official ones among them, and who runs each — one question about the
        set. A Join request that waits is not membership, so it is not among
        them; a player group is run by nobody, so it asks nothing.
        """

        listings = await self._groups.listings(await self._groups.groups_of(subject_id))
        administrator_ids = {
            listing.administrator_id
            for listing in listings.values()
            if listing.is_official and listing.administrator_id is not None
        }
        if not administrator_ids:
            return False
        running = await self._administrators.running(administrator_ids)
        return any(runner.account_id == reader_id for runner in running.values())


__all__ = ["GamesTheyPlayed", "GroupsTheReaderRuns", "GroupsTheyShare"]
