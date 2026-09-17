"""The seams this context is built on: the photo path's three, and two aggregates'.

Each is here rather than in ``app/application/ports/`` because each is the
Player profile context's own: a photo belongs to a profile, and no other context
has one. Cross-cutting ports — the unit of work, the event store, the publisher
— stay where they are.

``PlayerProfileRepository`` and ``PlayIntentDeclarationRepository`` are both the
**aggregate repository** kind, not the read-model kind: each is how a use case
reaches an event-sourced aggregate without knowing that it is event-sourced,
owning the aggregate-type name, the replay and the optimistic-concurrency
bookkeeping (ADR-0018). See ``backend/CONTEXT.md`` for the distinction, and
ADR-0089 for why this context is event-sourced. **Two of them, because this
context has two aggregates**: the profile is keyed on the player and a Play
intent declaration on ``(player, sport)`` (``docs/adr/0094``), which is a
difference in identity and therefore a difference in port.

**Nothing in this file names a vendor.** ``PhotoStorage`` says *put these bytes
under this reference and give me a short-lived URL for them*; whether that is
MinIO on a laptop or S3 in a deployed environment is the composition root's
answer and is invisible from here (``docs/adr/0091``).
"""

from __future__ import annotations

from typing import AsyncGenerator, Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.player_profile.domain.photos import (
    NotedPhoto,
    PhotoRef,
    PhotoReviewDecision,
    PhotoReviewVerdict,
    StoredPhoto,
    TranscodedImage,
)
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
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

    def with_review_notes(self) -> AsyncGenerator[NotedPhoto, None]:
        """Every photo this store holds, each with its review note beside it.

        **The listing the re-review backfill walks** (``docs/adr/0132``), and a
        separate question from ``stored_before`` rather than a flag on it: that
        one asks *how old*, this one asks *what does the metadata say*, and they
        are answered by different calls in every S3-compatible store — a listing
        returns keys and stamps, and user metadata costs a request per object.
        Folding them together would make the sweep pay for the backfill's reads
        on every tick.

        **A stream rather than a list**, an ``AsyncGenerator`` rather than an
        ``AsyncIterator``, and grouped by owner: all three for the reasons
        ``stored_before`` gives, and the second one so that a caller which stops
        early — which this one does, on its budget — can close it.

        Every photo, with **no cutoff.** An unreviewed photo does not become
        less unreviewed with age, and the population that needs the work is the
        old one.
        """
        ...

    async def review_decision(self, ref: PhotoRef) -> PhotoReviewDecision | None:
        """What was concluded about this photo, or ``None`` for *nobody looked*.

        **One object, by reference, rather than the whole listing.** Its
        neighbour ``with_review_notes`` walks the bucket for a job that is going
        to re-review it; this answers about a photo somebody already named — the
        first one on a player card — and the two are different calls in every
        S3-compatible store, a listing plus a ``HEAD`` against one ``HEAD``.

        **It costs a request per photo, and that is the price this port cannot
        hide** (``docs/adr/0138``). The verdict is user metadata, which no
        listing carries and no presign reads, so a caller pays one round trip per
        photograph it wants a verdict for. What makes that affordable is where it
        is called from: a card is assembled after the floor, over the twenty rows
        that survived rather than over the pool, and the answer is written into
        the search record so the read-back pays nothing at all.

        ``None`` covers three different things on purpose — the object is gone,
        nothing ever looked at it, or it carries a decision the note cannot prove
        (`decision_on_record`). A caller draws no shield for any of them, which
        is the same act, so telling them apart here would be a distinction
        nothing downstream is allowed to use.

        **Calls are independent and may be gathered.** One answer shares nothing
        with the next — no session, no cursor, no client a second call would
        contend for — so a caller with several photographs to ask about may ask
        concurrently, and both callers do: the card source over a shortlist and
        the owner's profile read over their own three.
        """
        ...

    async def read(self, ref: PhotoRef) -> bytes | None:
        """The bytes of this photo, or ``None`` if the store no longer has it.

        ``None`` rather than a raise, because *gone* is a state a caller has to
        handle rather than a failure: the sweep deletes an orphan the moment its
        window passes, and a backfill walking the same bucket will meet one.
        Both are periodic jobs with no lock between them (``docs/adr/0092``).

        The bytes are whatever was stored, which is always JPEG — everything is
        re-encoded on receipt (this module's docstring).
        """
        ...

    async def replace_metadata(
        self, ref: PhotoRef, metadata: Mapping[str, str]
    ) -> None:
        """Replace this photo's metadata, leaving the bytes untouched.

        **Replace, not merge**, because that is what the underlying operation is
        — an S3 metadata update is a copy of the object onto itself with the new
        set — and a port that promised a merge would be one implementation
        pretending. The caller hands over the whole set it wants the object to
        carry.

        **Already gone is success**, exactly as ``delete`` is, and for the same
        reason: a job racing the sweep over the same photo must finish rather
        than fail its run. A photo id is never reused — every upload mints a
        fresh one — so an object that is absent here is one that will not come
        back, not one that might be different bytes under the same name.
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


@runtime_checkable
class PlayIntentDeclarationRepository(Protocol):
    """Loads and saves PlayIntentDeclaration aggregates.

    Keyed on the **pair**, because the stream is: there is no declaration id to
    pass, and a caller cannot ask this port a question that is not scoped to one
    player in one sport. That is the same hazard-closing shape
    ``PlayerProfileRepository`` has for the player alone.
    """

    async def load(
        self, *, player_id: UUID, sport: Sport
    ) -> PlayIntentDeclaration | None:
        """This pair's standing declaration, replayed from its stream, or nothing.

        ``None`` rather than a raise: *rated but not yet declared* is the
        ordinary state of every player between finishing a rating run and
        answering the tail, and ADR-0094 makes an undeclared **candidate** a
        common path rather than an exception. A caller distinguishes *open the
        stream* from *append to it* by this answer and by nothing else.
        """
        ...

    async def save(self, declaration: PlayIntentDeclaration) -> None:
        """Append the aggregate's pending events and publish them.

        Appends and publishes; it does **not** commit, for the reason no
        repository in this codebase does — the transaction boundary is a
        decision about the *command*.

        A no-op when nothing is pending, which is what lets a re-declaration of
        the value already held be saved without growing the stream.
        """
        ...
