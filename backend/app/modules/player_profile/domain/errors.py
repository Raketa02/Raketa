"""Player profile errors: the photo path's, and the profile commit's.

Each carries its own wire code, because they arrive on the same status from the
same endpoint and ask the client for different recoveries: pick a different file,
pick a smaller file, the file is broken, the photo you asked for is not there —
and, for the commit, re-read the vocabulary, drop a tag, move the slider, or ask
the consent question you skipped.

**The commit's refusals are 400s, and every one of them is something a client
already had the information to prevent.** The tag vocabulary, the floor and the
ceiling and the radius bounds are all served at `GET /player-profile/options`,
so a picker built from that response cannot produce any of these. They are
refused here anyway, because a disabled button is not a validation
(``docs/adr/0089``): it is absent from a replayed request, from an older build,
and from anything that is not the app.

**All four are 400s rather than 413 and 415**, and that is a decision rather
than an oversight. The envelope's contract is that ``code`` is *"the only half a
client may branch on"* (``app/core/exception_handlers.py``), so the status buys
nothing the code does not already carry — while adding two status classes to
``app/shared/domain/errors.py``, which three contexts share, for one endpoint's
sake. If a reverse proxy ever caps request bodies in front of this application,
its own 413 will arrive without a code and that is the moment to reconsider.
"""

from __future__ import annotations

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


class SearchRadiusOutOfBounds(BadRequestError):
    """A radius outside the served range, or off its step.

    Both are one code for the reason both ends of the tag bounds are: the served
    object carries the range *and* the step, so a client with the numbers can
    tell which it broke, and one without them can do nothing with either answer.
    """

    code = "search_radius_out_of_bounds"

    def __init__(self) -> None:
        super().__init__("This is not a Search radius a player may hold.")


class ProposalsOptInNotAnswered(BadRequestError):
    """The commit arrived without an answer to the proposals question.

    **This is the refusal that enforces "skipping is not consent"**
    (``../../../../CONTEXT.md``). The opt-in has no default: unanswered is
    neither yes nor no, so a commit carrying a null cannot be completed by
    picking one. The client's recovery is to ask the question — not to send
    ``false``, which is a recorded refusal and a different fact.
    """

    code = "proposals_opt_in_not_answered"

    def __init__(self) -> None:
        super().__init__("The proposals opt-in has not been answered.")


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
