"""Courts-and-Bookings errors.

No route mounts this context in v1 — there is no club console and no player
booking screen — so none of these has been rendered as JSON. They carry a status
and a code anyway, for the reason `app/shared/domain/errors.py` gives: a status
held in a separate registry is one a new subclass can be added without, and the
miss is a 500 in production rather than a red test.

**``InventoryLost`` is the one to read.** ADR-0035 settles the sub-question doc
5's finding C1 leaves open — whether losing a court is a *query result* (nothing
was free) or a *race outcome* (something was free and somebody else took it) —
with **always the first**. The exclusion constraint makes the race impossible
rather than detectable, so there is exactly one story to tell the player: the
last court of this category was sold. ``CourtAlreadyClaimed`` is therefore not
that story and never reaches a player: it is the constraint speaking to the use
case, which re-asks and either finds another court or reports the one story.
"""

from __future__ import annotations

from app.shared.domain import ConflictError, NotFoundError


class ReservationNotFound(NotFoundError):
    """No reservation with this id."""

    code = "reservation_not_found"

    def __init__(self) -> None:
        super().__init__("Reservation not found.")


class BookingNotFound(NotFoundError):
    """No booking with this id."""

    code = "booking_not_found"

    def __init__(self) -> None:
        super().__init__("Booking not found.")


class InventoryLost(ConflictError):
    """No court of this category is free for this window.

    Terminal for a match: it cancels and refunds everybody, including anybody
    who had already left. Which is why it must mean one thing — *the category
    sold out* — and never *we raced somebody and lost*.
    """

    code = "court_inventory_lost"

    def __init__(self) -> None:
        super().__init__("No court of this category is free for that time.")


class CourtAlreadyClaimed(ConflictError):
    """The exclusion constraint refused this claim: the court is already taken.

    **Internal to the context.** It is what the database says when two writers
    reach one court in the same instant, and the caller's answer is to look
    again — not to tell a player anything. A player only ever hears
    ``InventoryLost``, and only when the second look finds nothing free either.
    """

    code = "court_already_claimed"

    def __init__(self) -> None:
        super().__init__("That court is already claimed for that time.")


class ReservationAlreadyReleased(ConflictError):
    """The claim is already given back; nothing further can be said of it."""

    code = "reservation_already_released"

    def __init__(self) -> None:
        super().__init__("This reservation has already been released.")


class CourtNotInCategory(ConflictError):
    """A reassignment that would leave the category the player bought.

    *"The exact court is assigned, never chosen — and the price cannot change."*
    The price attaches to the category, so moving a live reservation into
    another one would move the price under a quote already given.
    """

    code = "court_not_in_category"

    def __init__(self) -> None:
        super().__init__("That court is not in this reservation's category.")


class ConcurrentBookingModification(ConflictError):
    """Somebody else wrote this booking between the read and the write."""

    code = "concurrent_booking_modification"

    def __init__(self) -> None:
        super().__init__("This booking was changed by someone else. Reload and retry.")


class ConcurrentReservationModification(ConflictError):
    """Somebody else wrote this reservation between the read and the write.

    The version speaking, not the exclusion constraint. The recovery is to
    re-read and re-apply — never to merge.
    """

    code = "concurrent_reservation_modification"

    def __init__(self) -> None:
        super().__init__(
            "This reservation was changed by someone else. Reload and retry."
        )
