"""Friends' ``OpenToTheRequester`` over the record's rule (b), ``WithinReach``
(``docs/adr/0204`` §2, #791): a friend request is admitted exactly where a
record would be reached, so *Add friend* and the press can never disagree.
**Signed here**, so the arrow runs ``player_record → friends`` and Friends
imports none of its readers (``.importlinter``)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.player_record.application.admission import WithinReach


@final
class RecordOpenToTheRequester:
    def __init__(self, reach: WithinReach) -> None:
        self._reach = reach

    async def open_to(self, addressee: UUID, *, requester: UUID) -> bool:
        return await self._reach.reaches(reader_id=requester, subject_id=addressee)


__all__ = ["RecordOpenToTheRequester"]
