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

from app.shared.domain import BadRequestError, ConflictError, UnauthorizedError


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
