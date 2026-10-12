from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.clubs.application.handlers import (
    LogClubAccountOpened,
    LogClubAccountPasswordChanged,
    LogClubCourtsEvent,
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
    PaymentsAccountOpened,
    PaymentsStatusChanged,
    PricesSet,
    RaketaHoursSet,
    RaketaPaused,
    RaketaResumed,
    RaketaSettingsChanged,
)
from app.modules.clubs.domain.events import (
    ClubAccountOpened,
    ClubAccountPasswordChanged,
    ClubDetailsChanged,
    ClubRegistered,
)


#: The wire version ``clubs.raketa_settings_changed`` is written under: version
#: 1 carried the minimum notice and the time to confirm, which #670 removed with
#: Instant and On request — a change to the wire shape, versioned as one — and
#: ``check_in``, retired with desk check-in (#651) and decodable until then.
#: Version 1 is not registered: the store is reset with the removal, so a
#: stored row of it is a decoding error, and no row of version 2 ever carried
#: *We check players in*. ``clubs.way_of_working_chosen`` is unregistered with
#: the choice (``docs/adr/0196`` §1): Only Raketa is the one way, and a class
#: kept only so an old row decodes would be a reader for a fact nothing reads.
RAKETA_SETTINGS_CHANGED_VERSION = 2


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
    catalog.register(
        RaketaSettingsChanged,
        name="clubs.raketa_settings_changed",
        version=RAKETA_SETTINGS_CHANGED_VERSION,
    )
    catalog.register(RaketaPaused, name="clubs.raketa_paused", version=1)
    catalog.register(RaketaResumed, name="clubs.raketa_resumed", version=1)
    # The club's payments account (#537), on the same stream.
    catalog.register(
        PaymentsAccountOpened, name="clubs.payments_account_opened", version=1
    )
    catalog.register(
        PaymentsStatusChanged, name="clubs.payments_status_changed", version=1
    )


def subscribe_club_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(ClubRegistered, LogClubRegistered())
    dispatcher.subscribe(ClubDetailsChanged, LogClubDetailsChanged())
    dispatcher.subscribe(ClubAccountOpened, LogClubAccountOpened())
    dispatcher.subscribe(ClubAccountPasswordChanged, LogClubAccountPasswordChanged())
    # Club courts (#535). Nothing reacts to them yet, and an event with no
    # subscriber is an outbox row that never stops failing.
    dispatcher.subscribe(CourtAdded, LogClubCourtsEvent())
    dispatcher.subscribe(CourtChanged, LogClubCourtsEvent())
    dispatcher.subscribe(CourtSwitchedOff, LogClubCourtsEvent())
    dispatcher.subscribe(CourtSwitchedOn, LogClubCourtsEvent())
    dispatcher.subscribe(CourtRemoved, LogClubCourtsEvent())
    dispatcher.subscribe(RaketaHoursSet, LogClubCourtsEvent())
    dispatcher.subscribe(ExceptionAdded, LogClubCourtsEvent())
    dispatcher.subscribe(ExceptionRemoved, LogClubCourtsEvent())
    dispatcher.subscribe(PricesSet, LogClubCourtsEvent())
    dispatcher.subscribe(RaketaSettingsChanged, LogClubCourtsEvent())
    dispatcher.subscribe(RaketaPaused, LogClubCourtsEvent())
    dispatcher.subscribe(RaketaResumed, LogClubCourtsEvent())
    dispatcher.subscribe(PaymentsAccountOpened, LogClubCourtsEvent())
    dispatcher.subscribe(PaymentsStatusChanged, LogClubCourtsEvent())
