"""The review port's only adapter today: it allows everything.

**This is deliberate and it is written down rather than assumed.** The product
rule is that a photo shows a racket sport on a court, and nothing checks it. The
reason it is safe to defer is that **nobody can see another player's photo yet**
— there is no matchmaking, no player card and no discovery — so a check today
protects nothing while a false reject blocks a real player on their first day
(``docs/adr/0091``).

What the seam buys is that the call site exists. When the checker lands it
replaces this class in ``app/bootstrap/composition.py`` and no use case, route or
test of the upload path changes shape.

One finding recorded here so it is not rediscovered: **Ultralytics YOLO is
AGPL-3.0**, which running inside a network service obliges publication of this
backend's source, and it is fitted to the wrong question anyway — COCO offers
``tennis racket`` and no ``court`` class at all, and a padel racket is solid,
short and stringless, so the highest-volume sport would draw the highest false
reject rate. The better-fitted candidate is CLIP, MIT-licensed, used zero-shot.
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
