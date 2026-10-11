"""How the club works with Raketa, and its settings (#535, the mechanics §16.3,
§16.6, §16.15, the screens B5)."""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.clubs.application.commands import (
    ChooseWayOfWorkingCommand,
    SaveRaketaSettingsCommand,
)
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.ports import ClubCourtsRepository
from app.modules.clubs.domain.raketa_terms import OtherClubsCourts, RaketaSettings


class ChooseWayOfWorking:
    """The club chooses Only Raketa, Instant or On request — the checklist's
    second step. **Changing it later applies to hours not yet booked** (the
    mechanics §16.3): a booked game keeps the terms it was booked on."""

    def __init__(
        self, *, courts: ClubCourtsRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._courts = courts
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChooseWayOfWorkingCommand) -> ClubCourts:
        club = await self._courts.load(command.club_id)
        club.choose_way(command.way, occurred_at=self._clock.now())
        await self._courts.save(club)
        await self._uow.commit()
        return club


class SaveRaketaSettings:
    """The club saves — and the first time, **confirms** — its settings: the
    checklist's last step. Pausing is on the same form, and stops new cards on
    the club's courts while booked games are played as booked (§16.15)."""

    def __init__(
        self, *, courts: ClubCourtsRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._courts = courts
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SaveRaketaSettingsCommand) -> ClubCourts:
        settings = RaketaSettings(
            release_lead_days=command.release_lead_days,
            cut_off_hours=command.cut_off_hours,
            minimum_notice_hours=command.minimum_notice_hours,
            time_to_confirm_minutes=command.time_to_confirm_minutes,
            other_clubs_courts=OtherClubsCourts(
                offered=command.other_clubs_courts,
                within_km=command.other_clubs_within_km,
            ),
        )
        club = await self._courts.load(command.club_id)
        club.save_settings(
            settings, paused=command.paused, occurred_at=self._clock.now()
        )
        await self._courts.save(club)
        await self._uow.commit()
        return club
