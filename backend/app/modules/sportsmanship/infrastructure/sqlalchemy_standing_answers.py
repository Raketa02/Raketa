"""``PublishedSportsmanshipQuery`` over the rating table. **One window, two reads.**

**The collapse costs this file nothing, which is the whole argument for the key.**
*Only a rater's most recent stars about a person count* is
``sportsmanship_rating``'s primary key, so there is no ``GROUP BY``, no
``DISTINCT ON`` and no window function here — one row already **is** one person.
A read-time collapse would be the rule the first reader to forget hands the
farming problem back with a plausible number (``docs/adr/0158``), and this file
is what that decision bought.

**The window is applied in the statement and checked in the fold.** ``LIMIT`` is
where fifty rows stop being read; the domain's ``published_from`` refuses a wider
window than the rule allows, so an over-fetch here is a broken precondition
rather than a quietly wider figure.

**The order is total, deliberately.** *The fifty most recent raters* is an
ordering before it is a limit, and two rows written in the same transaction carry
the same ``rated_at`` — an all-blank-but-one card and a two-person card both do.
``rater_id`` breaks the tie, which decides nothing about who is right and
everything about two processes folding the same record to the same figure
(``docs/adr/0105``).

**Two methods, and the second cannot say what the first says.** ``band_for``
folds the same window and coarsens it; what it returns has no figure and no count
in it, because the caller for it is the sheet the *subject* reads.
"""

from __future__ import annotations

from typing import Sequence, final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sportsmanship.domain.published import (
    RATER_WINDOW,
    PublishedSportsmanship,
    SportsmanshipBand,
    band_of,
    published_from,
)
from app.modules.sportsmanship.infrastructure.card_model import (
    SportsmanshipRatingORM,
)


@final
class StandingAnswersAboutThem:
    """The fifty most recent people to have said something, and what they said."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def published_for(self, subject_id: UUID) -> PublishedSportsmanship | None:
        """The figure and how many different people it rests on."""

        return published_from(await self._window(subject_id))

    async def band_for(self, subject_id: UUID) -> SportsmanshipBand | None:
        """The coarse band, taken from the figure and never from the raw mean.

        **It goes through ``published_from`` rather than round its own mean**, so
        there is one rounding of one record on this platform and a subject's band
        cannot land on the other side of an edge from the figure a reader sees.
        What leaves this method is three steps wide and carries neither number.
        """

        published = published_from(await self._window(subject_id))
        return None if published is None else band_of(published.average)

    async def _window(self, subject_id: UUID) -> Sequence[int]:
        """This subject's fifty most recent standing answers, newest first.

        The index behind it is ``(subject_id, rated_at)``, which is this read and
        nothing else — the table has no other question asked of it.
        """

        found = await self._session.scalars(
            select(SportsmanshipRatingORM.stars)
            .where(SportsmanshipRatingORM.subject_id == subject_id)
            .order_by(
                SportsmanshipRatingORM.rated_at.desc(),
                SportsmanshipRatingORM.rater_id.desc(),
            )
            .limit(RATER_WINDOW)
        )
        return list(found)


__all__ = ["StandingAnswersAboutThem"]
