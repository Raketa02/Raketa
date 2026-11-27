"""Groups written straight into the groups projections (#813) — ``groups`` and
``group_members`` — as ``discovery_world`` writes a crowd into the people
rows' copies: a hundred groups made and joined through the routes would be
minutes of setup for one number.

**Nothing in it has a stream**: no group can be joined, left or opened, and no
member has an account, so a card names them by no nickname and draws their
initials. Each group is a player group at a real club — a card reads its club
— owned by its first member, who joined long ago with the rest, so nobody in
it is new this month and nobody has a game: its heat is its players, counted up
to 20.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.modules.clubs.domain.folding import fold
from app.modules.groups.domain.value_objects import GROUP_CODE_ALPHABET
from app.modules.groups.infrastructure.group_model import GroupMemberORM, GroupORM
from app.shared.ids import new_uuid

#: Long before any test's month, so nobody in a world is new unless asked.
LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)

_minted = 0


def _a_code() -> str:
    """A code no other world group has, in the codes' own alphabet."""

    global _minted
    _minted += 1
    n, code = _minted, ""
    for _ in range(8):
        n, digit = divmod(n, len(GROUP_CODE_ALPHABET))
        code += GROUP_CODE_ALPHABET[digit]
    return code


async def groups_at(
    session_factory,
    club_id: UUID | str,
    sizes: Sequence[int],
    *,
    named: str = "World",
) -> list[UUID]:
    """One group per size, each with that many members, in ``sizes``' order."""

    ids = [new_uuid() for _ in sizes]
    async with session_factory() as session:
        for n, (group_id, size) in enumerate(zip(ids, sizes, strict=True)):
            members = [new_uuid() for _ in range(size)]
            session.add(
                GroupORM(
                    id=group_id,
                    name=f"{named} {n:03d}",
                    name_folded=fold(f"{named} {n:03d}"),
                    home_club_id=UUID(str(club_id)),
                    join_policy="ANYONE",
                    kind="PLAYER",
                    owner_id=members[0] if members else new_uuid(),
                    code=_a_code(),
                )
            )
            await session.flush()
            for version, member in enumerate(members, start=1):
                session.add(
                    GroupMemberORM(
                        group_id=group_id,
                        player_id=member,
                        joined_at=LONG_AGO,
                        joined_version=version,
                    )
                )
        await session.commit()
    return ids


async def resize(session_factory, group_id: UUID | str, size: int) -> None:
    """The group's members, cut or filled to ``size`` — the newest leaving
    first, newcomers joining long ago — so its heat moves while nobody is
    new."""

    wanted = UUID(str(group_id))
    async with session_factory() as session:
        members = (
            await session.scalars(
                select(GroupMemberORM)
                .where(GroupMemberORM.group_id == wanted)
                .order_by(GroupMemberORM.joined_version)
            )
        ).all()
        for leaving in members[size:]:
            await session.delete(leaving)
        last = members[-1].joined_version if members else 0
        for version in range(last + 1, last + 1 + size - len(members)):
            session.add(
                GroupMemberORM(
                    group_id=wanted,
                    player_id=new_uuid(),
                    joined_at=LONG_AGO,
                    joined_version=version,
                )
            )
        await session.commit()
