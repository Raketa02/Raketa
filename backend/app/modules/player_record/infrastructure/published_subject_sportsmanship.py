"""``SubjectSportsmanship`` over ``sportsmanship``'s published fold.

**A rename, and nothing else.** What crosses is the figure and the count,
translated word for word from ``PublishedSportsmanship`` into this context's
``WhatPlayersSaid`` — for a reader and for the subject alike, since
``docs/adr/0179`` §5 served the figure to the person it is about and retired the
band this file used to fetch through a second method. No arithmetic happens
here: the mean was taken and rounded once, in the context that owns the scale.

**The name breaks the habit of the four adapters beside it, deliberately.**
Those are ``<provider><demand>`` — ``GamesSubjectForm``,
``ScoreSubjectReliability`` — and here the provider and the demand are the same
word, so that rule spells ``SportsmanshipSubjectSportsmanship``, which is not a
name. It is named for the port it reads instead.

**The absence passes straight through.** ``None`` from the provider is
``None`` here: a player nobody has rated has nothing said about them, and every
layer between the fold and the response spells that the same way rather than
turning it into a nought on the way past.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.player_record.domain.record import (
    HIGHEST_AVERAGE,
    LOWEST_AVERAGE,
    RATER_WINDOW,
    WhatPlayersSaid,
)
from app.modules.sportsmanship.domain.ports import PublishedSportsmanshipQuery
from app.modules.sportsmanship.domain.published import (
    HIGHEST_AVERAGE as PUBLISHED_HIGHEST,
)
from app.modules.sportsmanship.domain.published import (
    LOWEST_AVERAGE as PUBLISHED_LOWEST,
)
from app.modules.sportsmanship.domain.published import (
    RATER_WINDOW as PUBLISHED_WINDOW,
)

# **The scale and the window, checked at import against their second spellings.**
# Both sides bound the figure to one-to-five and the count to fifty, and neither
# may read the other's constant — so this is where the two meet, and what is
# avoidable about a second spelling is it being silent: a bound that grew on the
# provider's side would answer a perfectly legitimate published figure with a
# broken precondition, on a route, in production, and the wire would go on
# documenting the old one to clients. It is the guard ``games_subject_form``
# already puts the run of form's two spellings through.
if (LOWEST_AVERAGE, HIGHEST_AVERAGE, RATER_WINDOW) != (
    PUBLISHED_LOWEST,
    PUBLISHED_HIGHEST,
    PUBLISHED_WINDOW,
):
    raise RuntimeError(
        "the published figure's bounds are spelled twice and the two spellings "
        f"disagree: the record draws {LOWEST_AVERAGE}–{HIGHEST_AVERAGE} over at "
        f"most {RATER_WINDOW} raters and sportsmanship publishes "
        f"{PUBLISHED_LOWEST}–{PUBLISHED_HIGHEST} over at most {PUBLISHED_WINDOW}"
    )


@final
class PublishedSubjectSportsmanship:
    """What other players said, in the record's own words."""

    def __init__(self, published: PublishedSportsmanshipQuery) -> None:
        self._published = published

    async def what_players_said(self, player_id: UUID) -> WhatPlayersSaid | None:
        """The figure and the count, renamed — or nothing, unchanged.

        No arithmetic happens here and none happens anywhere on this side of the
        wire. The mean was taken and rounded once, in the context that owns the
        scale, so a record and any future surface print one rounding of one
        record.
        """

        published = await self._published.published_for(player_id)
        if published is None:
            return None
        return WhatPlayersSaid(average=published.average, raters=published.raters)


__all__ = ["PublishedSubjectSportsmanship"]
