"""Photo bytes in an S3-compatible object store.

**One adapter, two deployments, and that is the whole point of the decision.**
ADR-0091 names a MinIO adapter for `local` and an S3 adapter for the deployed
environments; they are the same class here, because MinIO *is* the S3 protocol
and two classes with the same body are a copy that drifts. What actually differs
is one setting — the endpoint URL, which is set to the MinIO container locally
and left unset in a deployed environment so botocore resolves AWS's own. The
swap ADR-0091 promises is therefore configuration rather than code, which is
strictly stronger than what it asked for.

That is not a claim that S3-compatible is S3. Presigned URL semantics, multipart
edges and CORS behaviour differ enough that the first deployment will find at
least one of them. It is a much smaller surprise than migrating live user data
out of Postgres, which is the trade being made.

**Two endpoints, not one, and the distinction is the platform's own.** The
endpoint this application *calls* is a server-to-server URL — `http://minio:9000`
on a compose network, which no phone can resolve. The endpoint a presigned URL is
*signed against* is a public-network URL, because a player's device is what opens
it. SigV4 signs the host, so a URL signed for the internal name is invalid at the
external one; signing has its own client for exactly that reason. See
`docs/environments.md` for the rule these two names come from.

Nothing here wakes ADR-0010's dormant deployment path: no credential is created,
no workflow trigger changes, and the only store this runs against today is a
container on a laptop.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Iterable, Iterator, Mapping
from uuid import UUID

import aioboto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.kernel import Instant, instant
from app.modules.player_profile.domain.photos import (
    STORED_MEDIA_TYPE,
    NotedPhoto,
    PhotoRef,
    PhotoReviewDecision,
    StoredPhoto,
    TranscodedImage,
    decision_on_record,
    review_note_in,
)

#: Under the owner, so that *whose photo is this* is answered by the key rather
#: than by a lookup somebody could forget. A player asking for a photo id that
#: is not theirs builds a key that has never existed, which is why the endpoint
#: can answer *not found* without ever learning that the id is somebody else's.
_KEY_TEMPLATE = "players/{owner_id}/photos/{photo_id}.jpg"

#: Everything this application writes lives under here. The sweep lists with it
#: as a prefix, so an object somebody put in the bucket for another purpose is
#: never even enumerated — which is one of two independent reasons it cannot be
#: deleted, the other being that its key would not parse.
KEY_PREFIX = "players/"

#: The extension the key template ends in. Named, because the parser below has
#: to strip exactly what the template appended and a literal in two places is
#: the pair that drifts.
_KEY_SUFFIX = ".jpg"

#: The 404s `head_object` reports. botocore spells the same absence two ways
#: depending on the operation and the store, and MinIO and S3 do not agree, so
#: both are read as *no such object* rather than one being trusted.
_ABSENT_CODES = frozenset({"404", "NoSuchKey", "NotFound"})


def object_key_for(owner_id: UUID, photo_id: UUID) -> str:
    """The key one photo lives at. A pure function, so the layout is testable."""

    return _KEY_TEMPLATE.format(owner_id=owner_id, photo_id=photo_id)


def ref_from_object_key(key: str) -> PhotoRef | None:
    """`object_key_for`'s inverse, or ``None`` for a key this app did not write.

    The sweep needs it because a listing answers in keys and the rest of the
    system speaks ``PhotoRef``. **Refusing rather than guessing is the whole
    contract**: this function's output decides what a sweep is allowed to
    delete, so anything that is not exactly the shape the template produces —
    a stray object, a folder marker, a key from some future layout — comes back
    ``None`` and is left alone. Deleting an object nobody can identify is not a
    recoverable mistake.
    """

    if not key.startswith(KEY_PREFIX) or not key.endswith(_KEY_SUFFIX):
        return None
    parts = key.split("/")
    if len(parts) != 4 or parts[2] != "photos":
        return None
    try:
        owner_id = UUID(parts[1])
        photo_id = UUID(parts[3][: -len(_KEY_SUFFIX)])
    except ValueError:
        return None
    return PhotoRef(owner_id=owner_id, photo_id=photo_id)


def photo_refs_in(contents: Iterable[Mapping[str, Any]]) -> Iterator[PhotoRef]:
    """The photos in one listing page, as refs, in the order it listed them.

    What a caller that has **no business with an age** gets: the re-review
    backfill asks what the metadata says, and a stamp it does not read would be
    an invariant it could still fail on — `stored_photos_in` refuses a naive
    ``LastModified`` rather than comparing it, which is right for the sweep and
    is not this caller's rule to inherit.

    The refusal that *is* shared is the one that matters: a key which is not
    exactly what this adapter writes yields nothing (`ref_from_object_key`).
    """

    for entry in contents:
        key = entry.get("Key")
        if not isinstance(key, str):
            continue
        ref = ref_from_object_key(key)
        if ref is not None:
            yield ref


def stored_photos_in(contents: Iterable[Mapping[str, Any]]) -> Iterator[StoredPhoto]:
    """The photos in one ``list_objects_v2`` page, in the order it listed them.

    Pure, so the translation from *what a store said* to *what the sweep judges*
    is testable with no store — which matters more here than anywhere else in
    this adapter, because the thing on the other side of it is a delete.

    ``LastModified`` is the stamp, and it is the only source there is: an
    uploaded photo appears in no event stream until a commit names it. Every
    S3-compatible store returns it timezone-aware; ``instant`` refuses it if one
    ever does not, rather than letting a naive value be compared against a
    cutoff and quietly answer by an offset.
    """

    for entry in contents:
        key = entry.get("Key")
        last_modified = entry.get("LastModified")
        if not isinstance(key, str) or last_modified is None:
            continue
        ref = ref_from_object_key(key)
        if ref is None:
            continue
        yield StoredPhoto(ref=ref, stored_at=instant(last_modified))


def user_metadata_in(response: Mapping[str, Any]) -> Mapping[str, str]:
    """The user metadata out of one ``head_object`` answer.

    Pure, and defensive about the shape rather than the values: a store that
    answered with no ``Metadata`` key at all is describing an object that
    carries none, which is exactly what a photo from the pass-through era looks
    like — so it must read as *no note* rather than raise.

    Keys come back lowercased by every S3-compatible store. The two this
    application writes are lowercase already (``domain/photos.py``), which is
    why nothing here has to normalise and why nothing may start writing a key
    that would need it.
    """

    metadata = response.get("Metadata")
    if not isinstance(metadata, dict):
        return {}
    return {
        str(key): str(value) for key, value in metadata.items() if isinstance(key, str)
    }


def reports_an_absent_object(error: ClientError) -> bool:
    """Whether this store error means *no such object* rather than *broken*.

    Extracted so it can be tested without a store. The distinction is the whole
    of it: an outage, a wrong credential or a missing bucket read as an absent
    photo would surface as every player's photos silently vanishing, and a
    profile commit re-validating ids against it would refuse every photo id it
    was handed — during the outage, and only during the outage.
    """

    return str(error.response.get("Error", {}).get("Code", "")) in _ABSENT_CODES


class S3PhotoStorage:
    """`PhotoStorage` over any S3-compatible store.

    A client is created per operation rather than held. aiobotocore clients bind
    to the event loop and the connection pool they were made on, so a long-lived
    one on a module or an application object is the shape that fails under a
    second loop — a worker, a management command, a test — with a symptom far
    from its cause. The cost is one client construction per call, which is
    service-model lookup against botocore's own cache, not a round trip.
    """

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        public_endpoint_url: str | None,
        region_name: str,
        access_key_id: str,
        secret_access_key: str,
    ) -> None:
        self._bucket = bucket
        self._endpoint_url = endpoint_url
        self._public_endpoint_url = public_endpoint_url or endpoint_url
        self._session = aioboto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
        )

    def _client(self, *, endpoint_url: str | None) -> Any:
        return self._session.client(
            "s3",
            endpoint_url=endpoint_url,
            # MinIO speaks SigV4 and path-style addressing. Virtual-host style
            # would resolve `bucket.minio` on the compose network, which is not
            # a name anything answers to.
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )

    async def put(
        self,
        ref: PhotoRef,
        image: TranscodedImage,
        *,
        metadata: Mapping[str, str],
    ) -> None:
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=object_key_for(ref.owner_id, ref.photo_id),
                Body=image.data,
                ContentType=image.media_type,
                Metadata=dict(metadata),
            )

    async def exists(self, ref: PhotoRef) -> bool:
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            try:
                await s3.head_object(
                    Bucket=self._bucket,
                    Key=object_key_for(ref.owner_id, ref.photo_id),
                )
            except ClientError as exc:
                if reports_an_absent_object(exc):
                    return False
                raise
            return True

    async def stored_before(self, cutoff: Instant) -> AsyncGenerator[StoredPhoto, None]:
        # Paged rather than listed: `list_objects_v2` answers a thousand keys at
        # a time whatever the bucket holds, and the sweep's candidate set is
        # every photo on the platform older than a day. The client stays open
        # across the yields, which is what an `async with` around an async
        # generator is for.
        #
        # There is no server-side filter on `LastModified` in the S3 API, so the
        # cutoff is applied here and the whole prefix is walked either way. That
        # is the honest cost of this shape, and the reason the sweep's cadence is
        # measured in hours rather than minutes.
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=self._bucket, Prefix=KEY_PREFIX
            ):
                for photo in stored_photos_in(page.get("Contents", [])):
                    if photo.stored_at < cutoff:
                        yield photo

    async def with_review_notes(self) -> AsyncGenerator[NotedPhoto, None]:
        # **A listing does not carry user metadata in any S3-compatible store**,
        # so this is a page of keys and then one `head_object` per key. That
        # cost is the honest price of keeping the review verdict on the object
        # rather than in a table beside it, and it is why the backfill's
        # interval is measured in minutes rather than seconds — in the steady
        # state, when every photo is reviewed, a run is that many HEADs and no
        # inference at all.
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=self._bucket, Prefix=KEY_PREFIX
            ):
                for ref in photo_refs_in(page.get("Contents", [])):
                    key = object_key_for(ref.owner_id, ref.photo_id)
                    try:
                        head = await s3.head_object(Bucket=self._bucket, Key=key)
                    except ClientError as exc:
                        if reports_an_absent_object(exc):
                            # Deleted between the listing and the head — the
                            # sweep runs over this same bucket with no lock
                            # between them. Nothing to review, so nothing to
                            # yield.
                            continue
                        raise
                    yield NotedPhoto(
                        ref=ref, note=review_note_in(user_metadata_in(head))
                    )

    async def review_decision(self, ref: PhotoRef) -> PhotoReviewDecision | None:
        # One `head_object`, and **no `get_object`**: the verdict is metadata and
        # the bytes are megabytes. What may be drawn from that metadata is the
        # domain's judgement rather than this adapter's — `decision_on_record`
        # refuses a decision the note cannot prove, and an adapter that read the
        # key straight would be the second opinion `review_metadata` and
        # `review_standing` are kept side by side to prevent.
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            try:
                head = await s3.head_object(
                    Bucket=self._bucket,
                    Key=object_key_for(ref.owner_id, ref.photo_id),
                )
            except ClientError as exc:
                if reports_an_absent_object(exc):
                    # The sweep got here first, or the id names nothing. Either
                    # way there is no photograph to say anything about, and the
                    # caller draws the generated court poster.
                    return None
                raise
            return decision_on_record(user_metadata_in(head))

    async def read(self, ref: PhotoRef) -> bytes | None:
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            try:
                response = await s3.get_object(
                    Bucket=self._bucket,
                    Key=object_key_for(ref.owner_id, ref.photo_id),
                )
            except ClientError as exc:
                if reports_an_absent_object(exc):
                    return None
                raise
            # Read inside the client's context: the body is a stream over the
            # connection, and one closed with the client answers nothing.
            data: bytes = await response["Body"].read()
            return data

    async def replace_metadata(
        self, ref: PhotoRef, metadata: Mapping[str, str]
    ) -> None:
        # **A metadata update is a copy of the object onto itself.** There is no
        # cheaper operation in the S3 API — the bytes are copied server-side and
        # the caller is billed for it — which is why the backfill checks the
        # note before it ever gets here.
        #
        # `REPLACE` drops everything not passed, `ContentType` included, so the
        # stored media type is restated. It is a constant rather than a read of
        # the object: every stored photo is JPEG, always, whatever arrived
        # (``domain/photos.py``), so a HEAD to learn it would be a round trip
        # for a value this application already decided.
        key = object_key_for(ref.owner_id, ref.photo_id)
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            try:
                await s3.copy_object(
                    Bucket=self._bucket,
                    Key=key,
                    CopySource={"Bucket": self._bucket, "Key": key},
                    Metadata=dict(metadata),
                    MetadataDirective="REPLACE",
                    ContentType=STORED_MEDIA_TYPE,
                )
            except ClientError as exc:
                if reports_an_absent_object(exc):
                    # The sweep got here first. The port promises this is
                    # success: a photo id is never reused, so there is nothing
                    # this write could have been racing except a delete.
                    return
                raise

    async def delete(self, ref: PhotoRef) -> None:
        # `DeleteObject` is idempotent: an absent key is a 204, not a 404. That
        # is what the port promises callers and it is inherited rather than
        # implemented — nothing here has to check first, and two sweeps racing
        # on one orphan both succeed.
        async with self._client(endpoint_url=self._endpoint_url) as s3:
            await s3.delete_object(
                Bucket=self._bucket,
                Key=object_key_for(ref.owner_id, ref.photo_id),
            )

    async def presigned_read_url(self, ref: PhotoRef, *, valid_for_seconds: int) -> str:
        # Signed against the *public* endpoint: the URL is opened by a phone, not
        # by this process. No request is made — presigning is a signature over
        # the request that would be sent.
        async with self._client(endpoint_url=self._public_endpoint_url) as s3:
            url: str = await s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": object_key_for(ref.owner_id, ref.photo_id),
                },
                ExpiresIn=valid_for_seconds,
            )
            return url
