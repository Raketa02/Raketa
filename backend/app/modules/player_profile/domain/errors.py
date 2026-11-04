"""Player profile errors: the photo path's, and the profile commit's.

Each carries its own wire code, because they arrive on the same status from the
same endpoint and ask the client for different recoveries: pick a different file,
pick a smaller file, the file is broken, the photo you asked for is not there —
and, for the commit, re-read the vocabulary, drop a tag, tick an hour of the
week, or rewrite your line.

**The commit's refusals are 400s, and every one of them is something a client
already had the information to prevent.** The tag vocabulary, the floor and the
ceiling are all served at `GET /player-profile/options`; the weekly-hours floor
is not served but is *fixed* — exactly one hour, by ``docs/adr/0102`` — so a
client holds it as a constant and knows it just as surely. Either way a picker
built from what it has cannot produce any of these. They are refused here anyway,
because a disabled button is not a validation (``docs/adr/0089``): it is absent
from a replayed request, from an older build, and from anything that is not the
app.

**The photo-format ones are 400s rather than 413 and 415**, and that is a
decision rather than an oversight. The envelope's contract is that ``code`` is
*"the only half a client may branch on"* (``app/core/exception_handlers.py``), so
the status buys nothing the code does not already carry — while adding two status
classes to ``app/shared/domain/errors.py``, which three contexts share, for one
endpoint's sake. If a reverse proxy ever caps request bodies in front of this
application, its own 413 will arrive without a code and that is the moment to
reconsider.

The same reasoning puts every one of the commit's refusals on 400 and gives each
its own code, so that seven failures of one request stay seven distinct
recoveries on the wire — and one of them, ``intro_not_admitted``, is the one that
carries a ``reason`` beside its code, because *rewrite the line* is three
different recoveries and a client has to know which (``docs/adr/0170`` §2).
"""

from __future__ import annotations

from enum import StrEnum

from app.shared.domain import BadRequestError, ConflictError, NotFoundError


class UnsupportedImageFormat(BadRequestError):
    """The client declared a media type the platform does not accept.

    Recovery is to pick a different file — not to retry this one, and not to
    compress it.
    """

    code = "unsupported_image_format"

    def __init__(self) -> None:
        super().__init__("This image format is not accepted.")


class ImageTooLarge(BadRequestError):
    """Either the request body or the decoded image exceeds its cap.

    One code for both caps deliberately: the client's recovery is the same
    — send a smaller photo — and telling a caller *which* of two internal limits
    it crossed invites it to probe them.
    """

    code = "image_too_large"

    def __init__(self) -> None:
        super().__init__("This image is too large.")


class UnreadableImage(BadRequestError):
    """The bytes declared an accepted format and are not one.

    Distinct from ``unsupported_image_format`` because the recoveries differ: a
    rejected *format* means choose another photo, a rejected *file* means this
    photo is damaged or was truncated in transit and re-picking the same one may
    well work.
    """

    code = "unreadable_image"

    def __init__(self) -> None:
        super().__init__("This image could not be read.")


class PhotoNotFound(NotFoundError):
    """No photo with this id belongs to this player.

    Deliberately the same answer for *no such photo* and *somebody else's
    photo*: distinguishing them would turn the endpoint into an oracle that
    confirms a stranger's photo id exists.
    """

    code = "photo_not_found"

    def __init__(self) -> None:
        super().__init__("Photo not found.")


class UnknownSocialTag(BadRequestError):
    """A tag id this platform does not serve.

    Its own code rather than a general invalid-selection one, because the
    recovery is specific: re-read `GET /player-profile/options` and re-render the
    picker. A tag id is permanent and never reused, so this means the client is
    working from a vocabulary that is not the served one — never that a real tag
    has become invalid.
    """

    code = "unknown_social_tag"

    def __init__(self) -> None:
        super().__init__("This is not a Social tag this platform serves.")


class SocialTagSelectionOutOfBounds(BadRequestError):
    """Fewer tags than the floor, or more than the ceiling.

    One code for both ends, because a client reads the numbers from the same
    served object and the recovery is the same sentence with a different
    direction. The floor and ceiling themselves are not repeated in the message:
    they are served, and a client that needs them has them.
    """

    code = "social_tag_selection_out_of_bounds"

    def __init__(self) -> None:
        super().__init__("This is not a number of Social tags a player may hold.")


class DuplicateSocialTag(BadRequestError):
    """The same tag id arrived more than once in one selection.

    Distinct from an out-of-bounds selection because the counts a player sees
    and the platform counts would otherwise silently disagree — and the client
    fix is a deduplicated picker, not a different number of tags.
    """

    code = "duplicate_social_tag"

    def __init__(self) -> None:
        super().__init__("A Social tag was selected more than once.")


class WeeklyHoursEmpty(BadRequestError):
    """The commit arrived with nothing ticked on the 7 × 16 week of hours.

    **At least one hour of the 112** (``docs/adr/0102``, amended by
    ``docs/adr/0189``). This is a sport application; when a player usually plays
    is not optional information, and the minimum is exactly one because one tick
    is a real answer — a player who only ever plays at ten on a Saturday must be
    able to say precisely that.

    Its own code rather than a shapeless 422, for the reason every other commit
    refusal has one: ``code`` is the only half a client may branch on, and the
    recovery here is specific and is not any other refusal's — go back to the
    week and tick an hour.

    **The number is not served.** Unlike the tag floor it is fixed by the record
    rather than by product, so both sides hold it as a constant, the way the
    photo cap is held. Nothing in the message repeats it either: a client that
    reached this has a picker that should not have let it.

    This refuses a *commit*, and only a commit. A player may still clear their week
    afterwards through ``set_weekly_hours`` — a blank week encountered anyway is
    **absent**, never zero (ADR-0102 part 3).
    """

    code = "weekly_hours_empty"

    def __init__(self) -> None:
        super().__init__("The week has no hours ticked.")


class IntroRefusal(StrEnum):
    """Why an intro was not admitted — the one coarse reason that crosses.

    Three values and deliberately no fourth: *which* pattern matched is not on
    the wire, so a refusal tells a player what kind of thing to change and
    never what the fence is made of. It is a ``StrEnum`` because the value
    **is** the wire spelling, carried in ``details.reason``.
    """

    #: Over the cap after trimming.
    TOO_LONG = "too_long"
    #: A line break anywhere in it.
    MULTILINE = "multiline"
    #: A phone-shaped run of digits, an email, a URL or a bare domain, or an
    #: ``@handle``.
    CONTAINS_CONTACT = "contains_contact"


class IntroNotAdmitted(BadRequestError):
    """The intro carries contact, or breaks the one-line shape.

    **One code and one coarse reason** (``docs/adr/0170`` §2): ``too_long``,
    ``multiline`` or ``contains_contact``, carried in ``details.reason`` so the
    client can say what to change without the server explaining what it
    matched. A refusal that named the pattern — *that looks like a phone
    number* — would be a rule a player rewrites around rather than a line they
    rewrite.

    The fence is **contact**: a phone-shaped run of digits, an email, a URL or a
    bare domain, an ``@handle``. Rudeness is not refused here — a block is what
    that is for — and a false refusal costs a rewrite where a false admission
    leaks contact, which is why the patterns err the way they do.

    Nothing is stored before this fires: it is raised by the value object the
    commit builds, ahead of any read of the object store.
    """

    code = "intro_not_admitted"

    def __init__(self, reason: IntroRefusal) -> None:
        self.reason = reason
        super().__init__(
            "This intro is not one the platform admits.",
            details={"reason": reason.value},
        )


class TooManyPhotos(BadRequestError):
    """More photos than a profile may hold.

    The cap is the product's (``../../../../CONTEXT.md`` — *Profile photo*: up to
    three, or none), and it is checked here rather than at the upload, because
    uploading is not attaching: a photo id becomes part of a profile only when a
    commit names it.
    """

    code = "too_many_photos"

    def __init__(self) -> None:
        super().__init__("A profile may not hold this many photos.")


class DuplicatePhoto(BadRequestError):
    """The same photo id arrived more than once in one commit.

    Refused rather than deduplicated because a profile's photos are **ordered** —
    the first is the one a player card shows — and a list with a repeat in it is
    a client that has lost track of which tile holds what.
    """

    code = "duplicate_photo"

    def __init__(self) -> None:
        super().__init__("A photo was included more than once.")


class PlayerProfileAlreadyExists(ConflictError):
    """This player already has a profile, and this is not the request that made
    it.

    A **different** idempotency key against an existing profile. The same key
    twice is not this — it replays, which is the whole point of the key — so
    reaching this means a second, genuinely new commit for a player who has
    already committed. Onboarding's second part happens once
    (``docs/adr/0090``); editing a profile afterwards is the profile screen's
    job and a different request.
    """

    code = "player_profile_already_exists"

    def __init__(self) -> None:
        super().__init__("This player already has a profile.")


class PlayerProfileNotFound(NotFoundError):
    """This player has not committed a profile, and one was asked for.

    The ordinary state of every account that has not finished onboarding's
    second part, so it is a **refusal** rather than a broken precondition: the
    client's recovery is to finish that part, which is the same thing
    ``GET /users/me``'s entry gate already tells it (``docs/adr/0090``).

    It is scoped to the caller's own profile — every route that raises it reads
    or writes ``/players/me`` — so it says nothing about whether anybody else
    exists. A **declaration** does not raise it: intent is asked for at a rating
    run's tail, which happens before the profile commit, and its aggregate is a
    different stream keyed on a different pair (``docs/adr/0094``).
    """

    code = "player_profile_not_found"

    def __init__(self) -> None:
        super().__init__("This player has no profile.")


class ReliabilityMinimumNotOffered(BadRequestError):
    """A reliability filter at a band the switch does not offer.

    *Play only with players of at least Medium* or *at least High* reliability
    (``docs/adr/0195`` §6), or no filter at all: *at least Low* lets everybody
    through and is the filter off said another way, and *at least Very high* is
    not a choice the product makes. The switch draws three positions, so a client
    built from it cannot send another; it is refused here because a disabled
    button is not a validation.
    """

    code = "reliability_minimum_not_offered"

    def __init__(self) -> None:
        super().__init__("A reliability filter is at least Medium or at least High.")


class LocationClubUnknown(BadRequestError):
    """The club picked for a Location area is no club in Raketa.

    A player who refuses the phone's location **picks a club near where they
    play**, and that club's point on the map, rounded to the cell, becomes their
    area (``docs/adr/0200`` §10). The picker only offers clubs that exist, so this
    is reached by a club that stopped existing between the search and the tap,
    or by a client that invented one — a field to correct, as a group's unknown
    home club is.
    """

    code = "location_club_unknown"

    def __init__(self) -> None:
        super().__init__(
            "Only a club in Raketa can stand in for a location.",
            details={"field": "club_id"},
        )
