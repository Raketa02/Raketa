"""*Who is drawn, and in what order* — the one projection every read here shares.

Three reads answer with faces — the list, the room and the page — and each of
them projects a set of ids through one ``MemberFaces`` answer. The projection is
here rather than in whichever read happened to be written first, so the rule it
carries is stated once: **somebody the faces read cannot name keeps their place,
and a set is never the source of a traversal**.
"""

from __future__ import annotations

from typing import Collection, Mapping
from uuid import UUID

from app.modules.conversations.domain.ports import MemberFace


def faces_in(
    people: Collection[UUID], faces: Mapping[UUID, MemberFace]
) -> tuple[MemberFace, ...]:
    """These people's faces, ordered by id and never by a set's iteration.

    **Somebody the faces read cannot name keeps their place**, carrying their id
    and no handle. For a member that is ``games``' rule verbatim — they are still
    somebody who agreed to play, and dropping them would draw a three-person
    doubles court. For somebody a line names it is the same rule for the same
    reason: the line still happened, and a client that finds nobody under the
    id draws the unknown player's mark exactly as it would for a handle
    ``users`` has lost.

    Sorted because a set is never the source of a traversal (``docs/adr/0105``
    §1) — two identical requests would otherwise reorder the faces on a row.
    """

    return tuple(
        faces.get(player_id, MemberFace(player_id=player_id))
        for player_id in sorted(people)
    )
