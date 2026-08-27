"""The review port's other adapter: it allows everything.

**No longer what the composition root builds.** ``ClipSidecarPhotoReview`` is
(``docs/adr/0129``), and this stays for the two jobs it is still the right
answer to: it is what the suite puts behind the port when the check is not the
thing under test, and it is the proof that ADR-0091's seam did what it was
defined to do — the checker arrived and no use case, route or test of the upload
path changed shape.

It is deliberately not in ``tests/``. A caller that wants an upload path with no
reviewer on it — a seed run, a fixture, a one-off backfill that scores photos
itself — is asking for a real adapter's behaviour, not for a test double, and
the honest place for *the reviewer that concludes nothing* is beside the one
that concludes something.
"""

from __future__ import annotations

from app.modules.player_profile.domain.photos import (
    PhotoReviewDecision,
    PhotoReviewVerdict,
    TranscodedImage,
)


class PassThroughPhotoReview:
    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        return PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED)
