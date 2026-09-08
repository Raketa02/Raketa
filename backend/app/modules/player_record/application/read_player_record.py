"""Reading one player's record. **Two use cases, one assembler.**

``ReadPlayerRecord`` answers about somebody else and runs the admission rule
first; ``ReadOwnRecord`` answers about the person asking and has no admission
collaborator to run. ``docs/adr/0155`` calls that *the same assembler with the
gate short-circuited*, and the short circuit is spelled in the **wiring** rather
than as a branch:

- the ``/me`` route declares no gate machinery, so a process whose candidate
  index is not running still serves a player their own record. The gates bind the
  index once per evaluation (``docs/adr/0112``) and refuse the whole read when
  there is none — correct for a sheet about a stranger, and absurd for the one
  screen that tells a player how they appear.
- there is no branch anybody can delete. A use case that took an admission and
  skipped it when ``reader == subject`` is one refactor away from skipping it
  when it should not.

**The assembler does no arithmetic and holds no rule.** It reads identity, mints
one link, and says whether the record is the reader's own. Every figure that
lands on this sheet later — the strands, the pills, the sportsmanship average —
arrives from the context that owns it, already decided.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock
from app.modules.player_record.application.admission import RecordAdmission
from app.modules.player_record.domain.errors import (
    RECORD_UNAVAILABLE,
    RecordUnavailable,
)
from app.modules.player_record.domain.ports import (
    RecordPhotoLink,
    SubjectIdentitySource,
)
from app.modules.player_record.domain.record import PlayerRecord


async def assemble_record(
    *,
    subject_id: UUID,
    is_self: bool,
    identities: SubjectIdentitySource,
    photos: RecordPhotoLink,
) -> PlayerRecord:
    """The record itself, once somebody has decided it may be read.

    **It refuses when the platform cannot describe the person**, and it refuses
    in the one shape this context refuses in — an id nobody has been issued, a
    handle that cannot be read and a profile that was never committed are one
    answer here, because they have one remedy and separating them would answer
    *is this id real* about a stranger.
    """

    identity = await identities.identity_of(subject_id)
    if identity is None:
        raise RecordUnavailable(RECORD_UNAVAILABLE)
    photo_url = (
        None
        if identity.photo_id is None
        else await photos.link_for(
            # **Signed as the person on the record**, never as the person
            # looking: an object store keys the pair, so a link signed under the
            # reader's id would reach an object that does not exist.
            owner_id=subject_id,
            photo_id=identity.photo_id,
        )
    )
    return PlayerRecord(is_self=is_self, identity=identity, photo_url=photo_url)


@final
class ReadPlayerRecord:
    """Somebody else's record, read through what entitled the reader to it."""

    def __init__(
        self,
        *,
        admission: RecordAdmission,
        identities: SubjectIdentitySource,
        photos: RecordPhotoLink,
        clock: Clock,
    ) -> None:
        self._admission = admission
        self._identities = identities
        self._photos = photos
        self._clock = clock

    async def execute(self, *, reader_id: UUID, subject_id: UUID) -> PlayerRecord:
        """**Gate first, and everything else afterwards.**

        The order is the decision: a read that fetched a stranger's handle,
        photograph and area and *then* refused would have performed the lookup
        the admission rule exists to prevent, and would have paid for it besides.

        ``is_self`` is read off the same comparison the admission's first strand
        makes, and that is one comparison used for two purposes rather than a
        rule spelled twice: one decides whether a gate is owed, the other decides
        what the sheet is titled.
        """

        if not await self._admission.admits(
            reader_id=reader_id, subject_id=subject_id, now=self._clock.now()
        ):
            raise RecordUnavailable(RECORD_UNAVAILABLE)
        return await assemble_record(
            subject_id=subject_id,
            is_self=reader_id == subject_id,
            identities=self._identities,
            photos=self._photos,
        )


@final
class ReadOwnRecord:
    """Your own record — *How others see you*, and nothing gates it.

    A block is between two people, the gender preference is mutual, and neither
    has anything to say about somebody reading their own sheet. A hold does not
    reach it either: a held player is refused every surface that would show them
    to somebody else, and this is the one that shows them to themselves.
    """

    def __init__(
        self, *, identities: SubjectIdentitySource, photos: RecordPhotoLink
    ) -> None:
        self._identities = identities
        self._photos = photos

    async def execute(self, *, reader_id: UUID) -> PlayerRecord:
        return await assemble_record(
            subject_id=reader_id,
            is_self=True,
            identities=self._identities,
            photos=self._photos,
        )


__all__ = [
    "ReadOwnRecord",
    "ReadPlayerRecord",
    "assemble_record",
]
