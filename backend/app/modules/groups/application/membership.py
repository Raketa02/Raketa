"""What every group use case asks first: is the person acting in this group?

**One refusal for a stranger, spelled once.** Every act and every read on a
group is for its members, and anyone else meets ``group_not_found`` — the same
answer as a group that does not exist, or one that was deleted — because the
cases have one remedy and telling them apart would tell a stranger which ids are
real (#504). What a member who is not the Owner may not do is the aggregate's to
refuse, after this.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupListing,
    GroupRepository,
    HiddenMembers,
)


async def group_of_a_member(
    groups: GroupRepository, group_id: UUID, player_id: UUID
) -> Group:
    """The group, to act on, if this player is in it."""

    group = await groups.load(group_id)
    if group is None or not group.is_member(player_id):
        raise GroupNotFound()
    return group


async def listing_for_a_member(
    directory: GroupDirectory, group_id: UUID, reader_id: UUID
) -> GroupListing:
    """The group, to read, if this reader is in it."""

    listing = (await directory.listings([group_id])).get(group_id)
    if listing is None or reader_id not in listing.members:
        raise GroupNotFound()
    return listing


async def hidden_in(
    hidden: HiddenMembers, listing: GroupListing, reader_id: UUID
) -> frozenset[UUID]:
    """Who in this group the reader and have a block between them.

    **A reader alone in the group has nobody to hide**, so the block state is
    not read at all — which is what keeps a group's creation, whose answer is
    read straight after its commit, from failing closed over a question with
    no one in it.
    """

    if all(member == reader_id for member in listing.members):
        return frozenset()
    return await hidden.hidden_from(reader_id)
