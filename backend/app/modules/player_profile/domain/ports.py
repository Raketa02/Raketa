"""The seams this context is built on: the photo path's three, and the profile's.

Each is here rather than in ``app/application/ports/`` because each is the
Player profile context's own: a photo belongs to a profile, and no other context
has one. Cross-cutting ports — the unit of work, the event store, the publisher
— stay where they are.

``PlayerProfileRepository`` is the **aggregate repository** kind, not the
read-model kind: it is how a use case reaches an event-sourced aggregate without
knowing that it is event-sourced, owning the aggregate-type name, the replay and
the optimistic-concurrency bookkeeping (ADR-0018). See ``backend/CONTEXT.md`` for
the distinction, and ADR-0089 for why this context is event-sourced.

**Nothing in this file names a vendor.** ``PhotoStorage`` says *put these bytes
under this reference and give me a short-lived URL for them*; whether that is
MinIO on a laptop or S3 in a deployed environment is the composition root's
answer and is invisible from here (``docs/adr/0091``).
"""

from __future__ import annotations

from typing import AsyncGenerator, Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewVerdict,
    StoredPhoto,
    TranscodedImage,
)
from app.modules.player_profile.domain.profile import PlayerProfile


class PhotoStorage(Protocol):
    """Where a photo's bytes live.

    Every method takes a ``PhotoRef``, which carries the owner — so a store
    cannot be asked a question that is not scoped to a player, and an adapter
    cannot forget to scope one.
    """

    async def put(
        self,
        ref: PhotoRef,
        image: TranscodedImage,
        *,
        metadata: Mapping[str, str],
    ) -> None:
        """Store `image` at `ref`, replacing anything already there.

        ``metadata`` is small, non-pixel context the store keeps beside the
        bytes — today the review verdict, so a photo the reviewer flagged is
        findable later without a second table to keep in step with the blobs.
        """
        ...

    async def exists(self, ref: PhotoRef) -> bool:
        """Whether this player has a photo with this id.

        The profile commit re-validates every photo id it is handed through this
        (``docs/adr/0089``): a client that sends an id it never uploaded, or one
        belonging to somebody else, must be refused rather than trusted.
        """
        ...

    async def presigned_read_url(self, ref: PhotoRef, *, valid_for_seconds: int) -> str:
        """A URL that reads this photo and stops working after the window.

        Pure computation in every S3-compatible store — a signature, not a round
        trip — so it says nothing about whether the object is there. Callers
        that need to know ask ``exists`` first.
        """
        ...

    def stored_before(self, cutoff: Instant) -> AsyncGenerator[StoredPhoto, None]:
        """Every photo this store took before `cutoff`, oldest bucket order.

        **A stream rather than a list**, because the answer is unbounded: it is
        every photo the platform holds that is older than a day, and a store
        that grew past what one process can hold in memory would turn the sweep
        from slow into fatal. An adapter pages; this iterates.

        **An ``AsyncGenerator`` rather than an ``AsyncIterator``, deliberately:
        the caller must be able to close it.** An adapter holds an open store
        client across the yields, and a caller that abandoned the stream
        mid-walk — because a delete raised — would leave that client to be
        finalised whenever the event loop got round to it. Saying *generator* in
        the type is what makes ``aclosing`` at the call site typecheck rather
        than be a hopeful call on an object that may not answer it.

        **Grouped by owner**, which is a promise and not an accident. Every
        S3-compatible store lists lexicographically and the owner is the first
        variable component of a key, so one player's photos arrive together —
        which is what lets the sweep replay a profile once per owner rather than
        once per photo.

        The stamp is the store's own, and there is no other source for it: an
        uploaded photo is not in any event stream until a commit names it, so
        *when did this arrive* is a question only the store can answer.
        """
        ...

    async def delete(self, ref: PhotoRef) -> None:
        """Remove this photo. **Already gone is success, not an error.**

        That is what makes a sweep safe to run beside itself: two of them
        handed the same orphan both finish, and the loser deleting nothing is
        the ordinary outcome rather than a failure to recover from. Every
        S3-compatible store already behaves this way — an adapter that turned an
        absent object into a raise would be inventing a failure.
        """
        ...


class ImageTranscoder(Protocol):
    """Bytes in, the one stored format out.

    A port rather than a function call because it is the only thing on the
    upload path that needs an imaging library, and a use case that imported one
    would be an application layer depending on an adapter. It stays *real* in
    tests while storage is faked: re-encoding is pure and needs no container, and
    faking it would fake away the EXIF stripping that is the point of it.
    """

    async def transcode(self, data: bytes) -> TranscodedImage:
        """Decode `data`, apply its orientation, cap its long edge, re-encode.

        Raises the module's ``UnreadableImage`` for bytes no supported decoder
        understands, and ``ImageTooLarge`` for an image whose declared
        dimensions exceed the decode cap — checked before any pixel is read, so
        a decompression bomb is refused rather than decoded.
        """
        ...


class PhotoReview(Protocol):
    """Whether a photo looks like the product's rule says it should.

    The rule is that a photo shows a racket sport on a court, and it is checked
    — server-side, because a client-side check is trivially bypassed, and by a
    sidecar holding the model rather than by this process (``docs/adr/0129``).
    Nothing in this file knows that: the port says *look at this image and tell
    me what you conclude*, and the answer arrives the same way whether it came
    from a model, from a pass-through, or from a queue of humans.

    **It soft-warns; it never blocks** — a flagged photo is stored, and the
    verdict rides on the object (``docs/adr/0091``). The seam was defined a
    release before the checker existed so that the checker would change no call
    site, and it did not.
    """

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict: ...


@runtime_checkable
class PlayerProfileRepository(Protocol):
    """Loads and saves PlayerProfile aggregates.

    Every method is keyed on the player and nothing else, because the stream is
    — there is no profile id to pass and no ownership argument to forget, which
    is the one hazard ``AssessmentRepository.load`` needs its ``for_player`` to
    close.
    """

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        """This player's profile, replayed from its stream, or nothing.

        ``None`` rather than a raise, because *no profile yet* is the ordinary
        state of every account that has not finished onboarding's second part —
        it is what the commit expects to find, and what the entry gate asks
        about (``docs/adr/0090``).
        """
        ...

    async def save(self, profile: PlayerProfile) -> None:
        """Append the aggregate's pending events and publish them.

        Appends and publishes; it does **not** commit. The transaction stays a
        use-case dependency for the reason it does in the rating context: the
        boundary is a decision about the *command*, not about persistence.

        A no-op when nothing is pending, which is what lets a transition that
        changed nothing be saved without growing the stream.
        """
        ...

    async def exists_for(self, *, player_id: UUID) -> bool:
        """Whether this player has committed a profile.

        A question rather than the aggregate, deliberately: this is what
        ``GET /users/me`` reads on every launch to decide whether onboarding's
        second part is still owed (``docs/adr/0090``), and replaying a profile
        to answer a boolean would be paying for state nobody looks at. A caller
        that only asked a question also has no business with an aggregate it
        might then mutate.

        **It reads the stream, not a projection.** The gate is checked
        immediately after the commit that creates the profile, and a read model
        that has not caught up would send a player who has just finished the
        social steps back into them.
        """
        ...
