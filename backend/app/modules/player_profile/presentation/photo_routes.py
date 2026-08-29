"""Upload one photo, and read one back.

Two routes, both about bytes and neither about a profile. A photo id becomes
part of a Player profile only when the profile commit carries it
(``docs/adr/0091``); until then it is an orphan the sweep will eventually
collect.

**The image arrives as the request body, not as a multipart field, and that is a
size-cap decision rather than a style one.** Starlette's multipart parser caps
*non-file* parts and streams file parts to a spooled temporary file with no
limit at all, so by the time a handler taking an ``UploadFile`` runs, an
arbitrarily large body has already been written to the container's disk. Reading
the body stream directly is what lets the cap be enforced *while* the bytes
arrive — the connection is refused part-way rather than after the platform has
paid to receive all of it. The ``Content-Type`` header is then doing exactly the
job that header exists for: naming what the bytes are.

**Both routes are the owning player's.** There is no route that reads another
player's photo, because nothing in the product can see one yet — no matchmaking,
no player card, no discovery. When that changes it is a new route with its own
authorisation, not a widened parameter on this one.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, status

from app.modules.player_profile.application.commands import (
    GetPhotoCommand,
    UploadPhotoCommand,
)
from app.modules.player_profile.domain.errors import ImageTooLarge
from app.modules.player_profile.domain.photos import (
    ACCEPTED_MEDIA_TYPES,
    MAX_UPLOAD_BYTES,
)
from app.modules.player_profile.presentation.dependencies import (
    GetPhotoDep,
    UploadPhotoDep,
)
from app.modules.player_profile.presentation.schemas import PhotoResponse
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/photos", tags=["photos"])

#: FastAPI derives a request body schema from a typed parameter, and this
#: endpoint has none — it reads the stream itself. Declaring the body here is
#: what keeps the contract honest for the client that generates from it.
_BINARY_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            media_type: {"schema": {"type": "string", "format": "binary"}}
            for media_type in sorted(ACCEPTED_MEDIA_TYPES)
        },
    }
}


async def _read_body_within_the_cap(request: Request) -> bytes:
    """The whole body, or a refusal before the whole body has been received.

    Two checks, and the second is the real one. ``Content-Length`` is a claim a
    client makes and a chunked request does not make it at all, so it buys an
    early refusal for the honest case and nothing else; the running total over
    the stream is what actually bounds what this process will hold.
    """

    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES:
        raise ImageTooLarge()

    received = 0
    chunks: list[bytes] = []
    async for chunk in request.stream():
        received += len(chunk)
        if received > MAX_UPLOAD_BYTES:
            raise ImageTooLarge()
        chunks.append(chunk)
    return b"".join(chunks)


@router.post(
    "",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one photo",
    openapi_extra=_BINARY_BODY,
    description=(
        "One photo per request. The body is the raw image and `Content-Type` "
        "names its format; JPEG, PNG and HEIC/HEIF are accepted.\n\n"
        "**What is stored is not what was sent.** Every image is decoded and "
        "re-encoded to JPEG with its long edge capped, which is how EXIF — and "
        "with it the GPS coordinates a phone writes into a photo — is removed "
        "reliably rather than best-effort.\n\n"
        "The returned id is what a profile commit carries; a photo becomes "
        "part of a profile only when a commit names it. Uploaded photos that "
        "are never committed are intended to be swept, and that sweep is not "
        "running yet.\n\n"
        "**Every upload is checked against the on-court rule, and `review` "
        "says what the check concluded.** It never refuses: a `flagged` photo "
        "is stored, answers `201` and is committed like any other, and the "
        "warning is the client's to word. A photo the check could not be run "
        "on answers `allowed` — the reviewer's own outage is not a reason to "
        "tell a player anything about their photograph."
    ),
)
async def upload_photo(
    request: Request,
    user: CurrentUserDep,
    use_case: UploadPhotoDep,
) -> PhotoResponse:
    # The media type only; a browser or an SDK may append `; charset=…` or a
    # boundary, and neither says anything about what the bytes are.
    declared_media_type = request.headers.get("content-type", "").split(";")[0].strip()
    data = await _read_body_within_the_cap(request)
    uploaded = await use_case.execute(
        UploadPhotoCommand(
            owner_id=user.id,
            data=data,
            declared_media_type=declared_media_type,
        )
    )
    # The verdict crosses here and nowhere else — `PhotoResponse` argues why.
    # `uploaded.review.note` is deliberately not passed: it is the evidence the
    # threshold will be re-derived from, and it is not about the player.
    return PhotoResponse.from_domain(
        uploaded.ref.photo_id,
        uploaded.presigned,
        review=uploaded.review.decision,
    )


@router.get(
    "/{photo_id}",
    response_model=PhotoResponse,
    status_code=status.HTTP_200_OK,
    summary="A signed URL for one of your photos",
    description=(
        "Returns a short-lived signed URL rather than the bytes: the store "
        "serves the image directly, so a photo never crosses this API twice.\n\n"
        "A photo id that does not exist and one belonging to another player "
        "both answer `photo_not_found`, deliberately — the alternative is an "
        "endpoint that confirms whether a stranger's id is real.\n\n"
        "**`review` is always `null` here**, and that is not `allowed`: this "
        "route does not read what the store holds beside the bytes. The "
        "on-court check's verdict crosses on the upload, where a player has "
        "just chosen the photograph it is about."
    ),
)
async def get_photo(
    photo_id: UUID,
    user: CurrentUserDep,
    use_case: GetPhotoDep,
) -> PhotoResponse:
    presigned = await use_case.execute(
        GetPhotoCommand(owner_id=user.id, photo_id=photo_id)
    )
    return PhotoResponse.from_domain(photo_id, presigned)
