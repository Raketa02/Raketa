"""Player profile errors, so far all of them about a photo's bytes.

Each carries its own wire code, because the four of them arrive on the same
status from the same endpoint and ask the client for different recoveries:
pick a different file, pick a smaller file, the file is broken, or the photo you
asked for is not there.

**All four are 400s rather than 413 and 415**, and that is a decision rather
than an oversight. The envelope's contract is that ``code`` is *"the only half a
client may branch on"* (``app/core/exception_handlers.py``), so the status buys
nothing the code does not already carry — while adding two status classes to
``app/shared/domain/errors.py``, which three contexts share, for one endpoint's
sake. If a reverse proxy ever caps request bodies in front of this application,
its own 413 will arrive without a code and that is the moment to reconsider.
"""

from __future__ import annotations

from app.shared.domain import BadRequestError, NotFoundError


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
