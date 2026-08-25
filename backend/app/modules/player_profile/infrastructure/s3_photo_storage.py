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

from typing import Any, Mapping
from uuid import UUID

import aioboto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.modules.player_profile.domain.photos import PhotoRef, TranscodedImage

#: Under the owner, so that *whose photo is this* is answered by the key rather
#: than by a lookup somebody could forget. A player asking for a photo id that
#: is not theirs builds a key that has never existed, which is why the endpoint
#: can answer *not found* without ever learning that the id is somebody else's.
_KEY_TEMPLATE = "players/{owner_id}/photos/{photo_id}.jpg"

#: The 404s `head_object` reports. botocore spells the same absence two ways
#: depending on the operation and the store, and MinIO and S3 do not agree, so
#: both are read as *no such object* rather than one being trusted.
_ABSENT_CODES = frozenset({"404", "NoSuchKey", "NotFound"})


def object_key_for(owner_id: UUID, photo_id: UUID) -> str:
    """The key one photo lives at. A pure function, so the layout is testable."""

    return _KEY_TEMPLATE.format(owner_id=owner_id, photo_id=photo_id)


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
