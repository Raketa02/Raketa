from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.clubs.application.handlers import (
    LogClubAccountOpened,
    LogClubAccountPasswordChanged,
    LogClubDetailsChanged,
    LogClubRegistered,
)
from app.modules.clubs.domain.club_courts_events import (
    CourtAdded,
    CourtChanged,
    CourtRemoved,
    CourtSwitchedOff,
    CourtSwitchedOn,
    ExceptionAdded,
    ExceptionRemoved,
    PricesSet,
    RaketaHoursSet,
    RaketaPaused,
    RaketaResumed,
    RaketaSettingsChanged,
    WayOfWorkingChosen,
)
from app.modules.clubs.domain.events import (
    ClubAccountOpened,
    ClubAccountPasswordChanged,
    ClubDetailsChanged,
    ClubRegistered,
)


def register_club_events(catalog: EventCatalog) -> None:
    catalog.register(ClubRegistered, name="clubs.club_registered", version=1)
    catalog.register(ClubDetailsChanged, name="clubs.club_details_changed", version=1)
    catalog.register(ClubAccountOpened, name="clubs.club_account_opened", version=1)
    catalog.register(
        ClubAccountPasswordChanged,
        name="clubs.club_account_password_changed",
        version=1,
    )
    # Club courts (#535): one stream per club, under the club's own id.
    catalog.register(CourtAdded, name="clubs.court_added", version=1)
    catalog.register(CourtChanged, name="clubs.court_changed", version=1)
    catalog.register(CourtSwitchedOff, name="clubs.court_switched_off", version=1)
    catalog.register(CourtSwitchedOn, name="clubs.court_switched_on", version=1)
    catalog.register(CourtRemoved, name="clubs.court_removed", version=1)
    catalog.register(RaketaHoursSet, name="clubs.raketa_hours_set", version=1)
    catalog.register(ExceptionAdded, name="clubs.exception_added", version=1)
    catalog.register(ExceptionRemoved, name="clubs.exception_removed", version=1)
    catalog.register(PricesSet, name="clubs.prices_set", version=1)
    catalog.register(WayOfWorkingChosen, name="clubs.way_of_working_chosen", version=1)
    catalog.register(
        RaketaSettingsChanged, name="clubs.raketa_settings_changed", version=1
    )
    catalog.register(RaketaPaused, name="clubs.raketa_paused", version=1)
    catalog.register(RaketaResumed, name="clubs.raketa_resumed", version=1)


def subscribe_club_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(ClubRegistered, LogClubRegistered())
    dispatcher.subscribe(ClubDetailsChanged, LogClubDetailsChanged())
    dispatcher.subscribe(ClubAccountOpened, LogClubAccountOpened())
    dispatcher.subscribe(ClubAccountPasswordChanged, LogClubAccountPasswordChanged())
