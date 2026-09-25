"""The Members list's order, and the faces on the Info tab's members row.

**The reader, then the Owner, then everybody else newest joined first** (#500
story 81): the people who matter most to the reader come first — themselves,
and who runs the group — and after them whoever arrived last, because a crowd
that is growing is read from its newest faces. The members row on the Info tab
is a preview of that list, so its faces are the same order without the reader.

Pure: the members come in **joining order** (the directory's), and which of them
are shown at all — rated in the sport, not blocked — is the caller's to have
filtered first.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Final
from uuid import UUID

#: How many faces the Info tab's members row stacks before its *+N*
#: (play mocks 58–59).
MEMBERS_ROW_FACES: Final = 5


def in_members_order(
    members: Sequence[UUID], *, reader_id: UUID, owner_id: UUID
) -> tuple[UUID, ...]:
    """``members``, given in joining order, as the Members list draws them.

    The reader and the Owner lead only when they are among ``members`` — a
    reader not rated in the sport asked, or an Owner a block hides, is not
    listed first for being who they are.
    """

    leading = tuple(
        dict.fromkeys(member for member in (reader_id, owner_id) if member in members)
    )
    return leading + tuple(
        member for member in reversed(members) if member not in leading
    )


def members_row(
    members: Sequence[UUID],
    *,
    reader_id: UUID,
    owner_id: UUID,
    hidden: Collection[UUID],
) -> tuple[UUID, ...]:
    """The faces the Info tab's members row stacks: everybody the reader may
    see **but the reader**, in the Members list's order, at most
    ``MEMBERS_ROW_FACES``. Empty for a reader alone in the group, whose row
    draws their own face."""

    shown = [
        member for member in members if member != reader_id and member not in hidden
    ]
    return in_members_order(shown, reader_id=reader_id, owner_id=owner_id)[
        :MEMBERS_ROW_FACES
    ]
