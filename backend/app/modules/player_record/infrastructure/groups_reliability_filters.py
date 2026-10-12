"""``ReliabilityFilters`` over the reader's groups, their profiles and their points.

The reader's own filter is a preference on their Player profile; everybody else
in every group they are in — read off ``groups``' directory, each counted once —
is who it could hide, and their own filters are who could hide the reader.
Whether a filter hides somebody is the engine's ``passes_reliability_minimum``
over ``player_score``'s points and *New*: the clause ``proposals``' pair rule
asks, so the sheet cannot count a player the deck would deal
(``docs/adr/0195`` §6, #661).

**Nobody's points are read while nobody filters** — the reader's filter off and
no group-mate's on answers *hides 0* and nothing to come back to without asking
``player_score`` anything. Otherwise everybody's, **once**, the set read that port
exists for.

**It names nobody.** What crosses is two counts and a band: never which
group-mates the filter hides, and never whose filter keeps the reader off a court.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.engines.matchfit.core import (
    RELIABILITY_BAND_FLOORS,
    ReliabilityBand,
    passes_reliability_minimum,
)
from app.kernel import Instant
from app.modules.groups.domain.ports import GroupDirectory
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_record.domain.record import (
    BackWithEveryone,
    ReliabilityFilter,
)
from app.modules.player_score.domain.ports import PublishedScoreQuery


@final
class FiltersInTheGroups:
    def __init__(
        self,
        *,
        groups: GroupDirectory,
        profiles: PlayerProfileRepository,
        scores: PublishedScoreQuery,
    ) -> None:
        self._groups = groups
        self._profiles = profiles
        self._scores = scores

    async def filter_of(self, player_id: UUID, *, now: Instant) -> ReliabilityFilter:
        listings = await self._groups.listings(await self._groups.groups_of(player_id))
        mates = tuple(
            dict.fromkeys(
                member
                for listing in listings.values()
                for member in listing.members
                if member != player_id
            )
        )
        minimums = {
            person: await self._minimum_of(person) for person in (player_id, *mates)
        }
        mine = minimums[player_id]
        if mine is None and not any(minimums[mate] for mate in mates):
            return ReliabilityFilter(
                minimum=None, hides=0, of=len(mates), back_with_everyone=None
            )

        scores = await self._scores.scores_for([player_id, *mates], now=now)
        own = scores[player_id]
        hides = sum(
            1
            for mate in mates
            if not passes_reliability_minimum(
                mine, band=scores[mate].band, is_new=scores[mate].is_new
            )
        )
        kept_off_by: list[ReliabilityBand] = [
            minimum
            for mate in mates
            if (minimum := minimums[mate]) is not None
            and not passes_reliability_minimum(
                minimum, band=own.band, is_new=own.is_new
            )
        ]
        return ReliabilityFilter(
            minimum=mine,
            hides=hides,
            of=len(mates),
            # The highest of them: reaching it passes every one at once.
            back_with_everyone=(
                BackWithEveryone(
                    band=max(kept_off_by, key=RELIABILITY_BAND_FLOORS.__getitem__)
                )
                if kept_off_by
                else None
            ),
        )

    async def _minimum_of(self, player_id: UUID) -> ReliabilityBand | None:
        """Their filter, or none — a member with no profile filters nobody."""

        profile = await self._profiles.load(player_id)
        return None if profile is None else profile.reliability_minimum


__all__ = ["FiltersInTheGroups"]
