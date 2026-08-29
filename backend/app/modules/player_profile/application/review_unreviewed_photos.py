"""Ask the reviewer about the photos nobody ever asked it about.

**Every photo uploaded before the checker landed carries ``review: allowed``,
written by a pass-through that allowed everything by construction.** Nothing
looked at those images; the metadata says otherwise. That was harmless while no
player could see another player's photo, and it stops being harmless at the
first route that returns a photo to a client that renders it
(``docs/adr/0107``) — on that day the corpus is part reviewed and part not.

**Which photos need re-reviewing is a query, not a guess**, and that is the one
thing that makes this tractable: an unreviewed photo is already distinguishable
from a reviewed one by its note (``domain/photos.py`` — `review_standing`).
Three populations, and only two of them are this job (``docs/adr/0132``): the
pass-through era, which is fixed and only shrinks; the ones that arrived while
the sidecar was unreachable, which **keeps growing** and is why this is a
re-runnable loop rather than a script; and the ones judged honestly against a
prompt set that has since moved, which are counted here and touched by nothing.

**It is not a second reviewer.** The verdict comes back through the same
`PhotoReview` port the upload path holds, so the rule applied is
`verdict_from_similarities` in both places. A batch with its own copy of the
threshold is a batch that can disagree with the upload path about one image, and
nothing downstream could say which of them was right.

**It does not rewrite what it already fixed.** A metadata update is a copy of
the object onto itself — real work, per object, on every tick — and the reviewed
note is self-identifying, so skipping is a string test rather than a lookup.

**It is idempotent and safe beside itself, with no lock** (``docs/adr/0092``).
Two runs handed the same photo both ask, both write the same-shaped metadata,
and the loser overwrites a verdict with a verdict; the object's bytes are
untouched either way. What two runs cost is duplicated inference, which is why
the budget is small and the interval is not.

**And ``unavailable`` is a failure mode of the fix, too.** A run against an
unhealthy sidecar must leave a photo alone rather than stamp a fresh
*could not be asked* over an old one — so the first ask that says *the reviewer
is not answering* ends the run, and the next tick is the retry.

**But a refusal about one image is not the reviewer being down**, and the
difference decides whether this job can stall. A status or a malformed body may
be about the photo in hand; ending the run on one would let a single object end
every run at the same place for ever, and nothing past it in the listing would
ever be looked at again — the same trap the decode failure below is caught to
avoid. Those are counted and stepped over; only *unreachable* stops the walk
(``domain/photos.py`` — `PhotoReviewUnavailability.is_about_the_reviewer`).
"""

from __future__ import annotations

from asyncio import sleep
from contextlib import aclosing
from dataclasses import dataclass

from app.modules.player_profile.domain.errors import (
    ImageTooLarge,
    UnreadableImage,
)
from app.modules.player_profile.domain.photos import (
    PhotoReviewUnavailability,
    awaits_review,
    judged_against_a_superseded_set,
    review_metadata,
    unavailability_in,
)
from app.modules.player_profile.domain.ports import (
    ImageTranscoder,
    PhotoReview,
    PhotoStorage,
)


@dataclass(frozen=True, slots=True)
class PhotoReviewBackfillReport:
    """What one run did, for the log line that is its only output.

    The counts are the five things that can happen to a photo the walk reads,
    and they are separate because their recoveries are: ``updated`` is progress,
    ``vanished`` is the sweep having got there first and needs nobody,
    ``unreadable`` is an object no decoder understands and needs a human,
    ``refused`` is the reviewer answering about one image and the answer being
    unusable, and ``superseded`` is population 3 — a number whose only job is to
    make *is it worth re-running the corpus against the new prompts* an
    answerable question.

    **Every count describes what this run walked, not what the bucket holds.** A
    run that stopped early walked less than the corpus, which is exactly what the
    two stop flags say — so ``superseded`` beside a ``stopped_on_budget`` of
    ``True`` is a floor on population 3 rather than its size. Without them a run
    that spent its budget and a run that finished the corpus print the same line.
    ``unavailable`` names the reviewer's reason when it gave one, because *it is
    down* and *it is refusing us* want two different people looking.
    """

    examined: int
    updated: int
    vanished: int
    unreadable: int
    refused: int
    superseded: int
    stopped_on_budget: bool
    stopped_unreviewable: bool
    unavailable: PhotoReviewUnavailability | None


class ReviewUnreviewedPhotos:
    def __init__(
        self,
        *,
        storage: PhotoStorage,
        transcoder: ImageTranscoder,
        review: PhotoReview,
        batch_limit: int,
        pause_seconds: float,
    ) -> None:
        self._storage = storage
        self._transcoder = transcoder
        self._review = review
        self._batch_limit = batch_limit
        self._pause_seconds = pause_seconds

    async def execute(self) -> PhotoReviewBackfillReport:
        examined = 0
        updated = 0
        vanished = 0
        unreadable = 0
        refused = 0
        superseded = 0
        asked = 0
        stopped_on_budget = False
        stopped_unreviewable = False
        unavailable: PhotoReviewUnavailability | None = None

        # `aclosing` rather than a bare `async for`, and here it is doing more
        # than it does in the sweep: this walk stops early *by design* — on its
        # budget, and on a reviewer that cannot answer — so the adapter's open
        # store client would be abandoned on the ordinary path rather than only
        # on a failing one.
        async with aclosing(self._storage.with_review_notes()) as photos:
            async for photo in photos:
                if not awaits_review(photo.note):
                    examined += 1
                    if judged_against_a_superseded_set(photo.note):
                        superseded += 1
                    continue
                if asked >= self._batch_limit:
                    # Stopping here rather than walking on: the rest of the
                    # listing is work this run may not do, and reading it would
                    # be a request per object for an answer nothing uses. The
                    # next tick starts at the top and skips what this one fixed,
                    # which is what makes a bounded run still make progress.
                    stopped_on_budget = True
                    break
                examined += 1

                data = await self._storage.read(photo.ref)
                if data is None:
                    # The sweep got here first. Two periodic jobs over one
                    # bucket with no lock between them (``docs/adr/0092``), and
                    # this is the whole of what that race costs.
                    vanished += 1
                    continue

                try:
                    image = await self._transcoder.transcode(data)
                except (UnreadableImage, ImageTooLarge):
                    # An object no decoder understands. It cannot be reviewed by
                    # anything, so it is counted and left carrying whatever it
                    # carries — stamping a verdict nobody took would be worse.
                    # Caught rather than raised because a run that died here
                    # would die on the same object every tick and never reach
                    # the photos past it.
                    unreadable += 1
                    continue

                if asked:
                    # **Between the asks**, and nowhere else: the thing being
                    # spaced is one sidecar container running one worker by
                    # design, with a live upload path queueing behind whatever
                    # it is doing. Not before the first, which would delay every
                    # run for a queue nothing is in, and not around a photo that
                    # never reached it.
                    await sleep(self._pause_seconds)

                asked += 1
                verdict = await self._review.review(image)
                if awaits_review(verdict.note):
                    # The ask came back without a verdict, and **which kind
                    # decides whether there is any point continuing.** Writing
                    # it over what is already there is never the answer — that
                    # is work that looks like progress.
                    why = unavailability_in(verdict.note)
                    if why is not None and not why.is_about_the_reviewer:
                        # It answered, and the answer was unusable — possibly
                        # about this one image. Counted and stepped over, for
                        # the reason the decode failure above is: a run that
                        # ended here would end at the same object every tick and
                        # never reach the photos past it.
                        refused += 1
                        continue
                    # Unreachable, or a reviewer that concludes nothing at all.
                    # The next photo gets the same answer, so the run ends
                    # rather than spending its budget one full timeout at a
                    # time, and the next tick is the retry.
                    stopped_unreviewable = True
                    unavailable = why
                    break

                await self._storage.replace_metadata(
                    photo.ref, review_metadata(verdict)
                )
                updated += 1

        return PhotoReviewBackfillReport(
            examined=examined,
            updated=updated,
            vanished=vanished,
            unreadable=unreadable,
            refused=refused,
            superseded=superseded,
            stopped_on_budget=stopped_on_budget,
            stopped_unreviewable=stopped_unreviewable,
            unavailable=unavailable,
        )
