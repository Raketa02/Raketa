"""Clubs-context errors.

There is no club console in v1 and no route mounts this context, so none of
these has ever been rendered as JSON. They carry a status and a code anyway, for
the reason ``app/shared/domain/errors.py`` gives for keeping the two on the
class: the alternative is a registry entry somebody forgets, and the miss is a
500 in production rather than a red test. The day an authoring screen exists,
these are already the vocabulary it refuses in.
"""

from __future__ import annotations

from app.shared.domain import ConflictError, NotFoundError


class ClubNotFound(NotFoundError):
    """No club with this id."""

    code = "club_not_found"

    def __init__(self) -> None:
        super().__init__("Club not found.")


class ClubNameAlreadyUsed(ConflictError):
    """A club is already registered under this name."""

    code = "club_name_already_used"

    def __init__(self) -> None:
        super().__init__("A club with this name already exists.")


class ConcurrentClubModification(ConflictError):
    """Somebody else wrote this club between the read and the write.

    ADR-0077 puts a version on the club *as well as* a partial unique index per
    series, and they answer different questions: the version stops a race, the
    index stops an invariant violation from reaching disk. This is the version
    speaking, and the recovery is to re-read and re-apply — never to merge.
    """

    code = "concurrent_club_modification"

    def __init__(self) -> None:
        super().__init__("This club was changed by someone else. Reload and retry.")


class CategoryNotFound(NotFoundError):
    """This club has no category with that id."""

    code = "club_category_not_found"

    def __init__(self) -> None:
        super().__init__("Court category not found.")


class CategoryAlreadyRetired(ConflictError):
    """A retired category cannot be retired again, or take a court.

    Retired and not deleted (ADR-0079): a past reservation still resolves, and a
    category with no courts left is a group that can never be assigned rather
    than a bug.
    """

    code = "club_category_already_retired"

    def __init__(self) -> None:
        super().__init__("This court category is retired.")


class CategoryNameAlreadyUsed(ConflictError):
    """This club already has a category by that name."""

    code = "club_category_name_already_used"

    def __init__(self) -> None:
        super().__init__("This club already has a category with that name.")


class CourtNotFound(NotFoundError):
    """This club has no court with that id."""

    code = "club_court_not_found"

    def __init__(self) -> None:
        super().__init__("Court not found.")


class CourtAlreadyRetired(ConflictError):
    """The court's catalogue series is closed; nothing further can be said of it."""

    code = "club_court_already_retired"

    def __init__(self) -> None:
        super().__init__("This court is retired.")
