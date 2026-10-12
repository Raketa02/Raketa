"""The Club context's refusals, each naming the field it is about.

**Field-level, because a desk is filling in a form.** Every refusal a sign-up or
a details edit can meet carries ``details.field`` — the control the sentence is
written under — which is the shape the player sign-up's conflicts and its
attestation already take. The club website writes the sentence, chosen from the
code (``docs/adr/0187`` §6: *decisions branch on the backend's error code, never
on its message*). A request schema bound would have refused the same inputs as a
``422 validation_error`` naming no field in a form a client may read, so the
bounds live in the value objects and are refused from here.
"""

from app.shared.domain import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)


class ClubNameInvalid(BadRequestError):
    code = "club_name_invalid"

    def __init__(self) -> None:
        super().__init__("a club's name is 2–80 characters", details={"field": "name"})


class ClubDistrictInvalid(BadRequestError):
    code = "club_district_invalid"

    def __init__(self) -> None:
        super().__init__(
            "a club's district is 2–64 characters", details={"field": "district"}
        )


class ClubCityInvalid(BadRequestError):
    code = "club_city_invalid"

    def __init__(self) -> None:
        super().__init__("a club's city is 2–64 characters", details={"field": "city"})


class ClubSportsRequired(BadRequestError):
    """A club offers at least one of the four sports (``docs/adr/0182`` §1).

    The only way the list can be wrong once it has reached the domain: a sport
    outside the registry is not a string the request schema admits."""

    code = "club_sports_required"

    def __init__(self) -> None:
        super().__init__(
            "a club offers at least one sport", details={"field": "sports"}
        )


class ClubSportDeclaredByGroup(ConflictError):
    """The desk unticked a sport an official group at the club declares.

    **Refused, and the refusal names the group** (``docs/adr/0182`` §5):
    otherwise the group would be left playing a sport its club no longer
    offers. ``details.sport`` is the sport, ``details.group`` the group's name —
    the first by name, where several play it — so the website can say which
    group to change first. Ticking it again is the other remedy."""

    code = "club_sport_declared_by_group"

    def __init__(self, *, sport: str, group: str) -> None:
        super().__init__(
            f"the official group {group!r} plays {sport.lower()}",
            details={"field": "sports", "sport": sport, "group": group},
        )


class ClubPointInvalid(BadRequestError):
    code = "club_point_invalid"

    def __init__(self) -> None:
        super().__init__(
            "a club's point is a latitude within ±90 and a longitude within ±180",
            details={"field": "point"},
        )


class ClubEmailAlreadyRegistered(ConflictError):
    """Another club's account already signs in with this email.

    **Among club accounts only** (``docs/adr/0182`` §3): the same address may
    belong to an unrelated User, and a sign-up is never refused for that."""

    code = "club_email_already_registered"

    def __init__(self) -> None:
        super().__init__(
            "a club account already uses this email", details={"field": "email"}
        )


class ClubAccountNotEligible(UnauthorizedError):
    """A club token whose account this backend cannot find.

    The club surface's counterpart of ``user_not_eligible``. Nothing deletes or
    disables a Club account today, so it is reached only by a token whose
    account is gone — a reset local store, say — and it ends the session."""

    code = "club_account_not_eligible"

    def __init__(self) -> None:
        super().__init__("club account no longer eligible")


# --------------------------------------------------------------------------- #
# Club courts — courts, hours, exceptions, prices and settings (#535)
# --------------------------------------------------------------------------- #


class CourtNameInvalid(BadRequestError):
    code = "court_name_invalid"

    def __init__(self) -> None:
        super().__init__("a court's name is 1–40 characters", details={"field": "name"})


class CourtNameTaken(ConflictError):
    """Another court at this club already has this name, ignoring case — a desk
    reading *Court 2* twice in its own table could not tell them apart."""

    code = "court_name_taken"

    def __init__(self) -> None:
        super().__init__(
            "another court at this club has this name", details={"field": "name"}
        )


class CourtSportNotOffered(BadRequestError):
    """A court plays one of the club's own sports (the screens B3), which is
    the one list a club has to change first."""

    code = "court_sport_not_offered"

    def __init__(self) -> None:
        super().__init__(
            "a court plays a sport the club offers", details={"field": "sport"}
        )


class CourtNotFound(NotFoundError):
    """No court of this club has that id — none at all, or another club's,
    which is the same answer: a desk reaches only its own courts."""

    code = "court_not_found"

    def __init__(self) -> None:
        super().__init__("no such court at this club")


class CourtHasBookings(ConflictError):
    """A court with a booking ahead of it cannot be deleted or given another
    sport — a booked game is played as booked (the mechanics §16.4). It can be
    switched off, which stops it selling anything new."""

    code = "court_has_bookings"

    def __init__(self) -> None:
        super().__init__("this court has a booking ahead of it")


class ExceptionDaysInvalid(BadRequestError):
    code = "exception_days_invalid"

    def __init__(self) -> None:
        super().__init__(
            "an exception's last day is on or after its first",
            details={"field": "days"},
        )


class ExceptionInThePast(BadRequestError):
    """Every day it would close is already over, so it would change nothing."""

    code = "exception_in_the_past"

    def __init__(self) -> None:
        super().__init__(
            "an exception closes a day that is not over yet",
            details={"field": "days"},
        )


class ExceptionHoursInvalid(BadRequestError):
    """Both hours or neither, within 07:00–23:00, and at least one hour."""

    code = "exception_hours_invalid"

    def __init__(self) -> None:
        super().__init__(
            "an exception closes whole hours between 07:00 and 23:00",
            details={"field": "hours"},
        )


class ExceptionReasonInvalid(BadRequestError):
    code = "exception_reason_invalid"

    def __init__(self) -> None:
        super().__init__(
            "an exception's reason is 1–80 characters", details={"field": "reason"}
        )


class ExceptionCourtsRequired(BadRequestError):
    """*Some courts* names at least one; every court is ``null``, never ``[]``."""

    code = "exception_courts_required"

    def __init__(self) -> None:
        super().__init__(
            "an exception closes every court or names some",
            details={"field": "courts"},
        )


class ExceptionNotFound(NotFoundError):
    code = "exception_not_found"

    def __init__(self) -> None:
        super().__init__("no such exception at this club")


class CourtBookedThen(ConflictError):
    """The exception would close an hour a booking holds. **Not allowed from the
    calendar** — the club cancels the booking instead (the mechanics §16.5), and
    the details name it so the website can link to it: *"Court 2 is booked then
    — cancel the booking first"*. The first such hour, by time and then court."""

    code = "court_booked_then"

    def __init__(self, *, court_id: str, booking_id: str, starts_at: str) -> None:
        super().__init__(
            "a booking holds an hour this exception would close",
            details={
                "court_id": court_id,
                "booking_id": booking_id,
                "starts_at": starts_at,
            },
        )


class PriceSportNotOffered(BadRequestError):
    code = "price_sport_not_offered"

    def __init__(self, *, sport: str) -> None:
        super().__init__(
            "a price is for a sport the club offers",
            details={"field": "prices", "sport": sport},
        )


class PriceSportRepeated(BadRequestError):
    """One save prices a sport once: two rows for it would be two answers."""

    code = "price_sport_repeated"

    def __init__(self, *, sport: str) -> None:
        super().__init__(
            "a sport is priced once", details={"field": "prices", "sport": sport}
        )


class PriceOutOfRange(BadRequestError):
    """A court-hour costs between ``least`` and ``most`` grosze — the bounds
    cross in ``details`` so the website can say them."""

    code = "price_out_of_range"

    def __init__(self, *, sport: str, least: int, most: int) -> None:
        super().__init__(
            "a court-hour's price is out of range",
            details={"field": "prices", "sport": sport, "least": least, "most": most},
        )


class PriceDoesNotSplit(BadRequestError):
    """The price does not divide into whole grosze among the sport's
    ``seats``, so no share could be charged exactly. A price in whole złoty
    always splits."""

    code = "price_does_not_split"

    def __init__(self, *, sport: str, seats: int) -> None:
        super().__init__(
            "a court-hour's price splits into whole grosze among its seats",
            details={"field": "prices", "sport": sport, "seats": seats},
        )


class PriceBandHoursInvalid(BadRequestError):
    code = "price_band_hours_invalid"

    def __init__(self, *, sport: str) -> None:
        super().__init__(
            "a price band covers whole hours between 07:00 and 23:00",
            details={"field": "prices", "sport": sport},
        )


class PriceBandsOverlap(BadRequestError):
    """Two bands of the same days cover one hour, which would give it two
    prices."""

    code = "price_bands_overlap"

    def __init__(self, *, sport: str) -> None:
        super().__init__(
            "two price bands of the same days overlap",
            details={"field": "prices", "sport": sport},
        )


class SettingOutOfRange(BadRequestError):
    """A Raketa setting outside the range its field offers. ``details`` names
    the field and carries the range, so the website can say both."""

    code = "setting_out_of_range"

    def __init__(self, *, field: str, least: int, most: int) -> None:
        super().__init__(
            f"{field} is between {least} and {most}",
            details={"field": field, "least": least, "most": most},
        )


class ClubSportHasCourts(ConflictError):
    """The desk unticked a sport one of the club's courts plays — switched off
    or not. **Refused, naming the court**: a court plays one of the club's own
    sports (the screens B3). Deleting the court, or giving it another sport,
    is the remedy; so is ticking the sport again."""

    code = "club_sport_has_courts"

    def __init__(self, *, sport: str, court: str) -> None:
        super().__init__(
            f"the court {court!r} plays {sport.lower()}",
            details={"field": "sports", "sport": sport, "court": court},
        )


class PaymentsAlreadyConnected(ConflictError):
    """The desk asked for a link to the provider's onboarding, and the
    provider already says the club's account is ready: there is nothing left
    to fill in, and the checklist's first step is done. Its own dashboard at
    the provider is where anything else about it is changed."""

    code = "payments_already_connected"

    def __init__(self) -> None:
        super().__init__("the club's payments account is ready")
