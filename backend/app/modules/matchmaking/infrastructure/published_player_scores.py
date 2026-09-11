"""``PlayerScoreQuery``'s provider — signed by ``player_score``, translated here.

**The seam ``UsersAccountStatus`` set, for the same reason.** The matcher declares
what it needs in its own vocabulary; the provider publishes what it has in its
own; and the adapter that reconciles them lives on the *consumer's* side of the
arrow, because ``player_score`` may not import the matcher and has no business
knowing that a reliability term exists. What crosses is a Player Score; what this
class does is spell it the way the engine reads one.

**It reads the provider's own port and never the provider's providers.** The
strand arithmetic — an opportunity, a good outcome, the blend over what is
present — belongs to ``player_score``, and a version of it written here would be
a second answer to *what is somebody's record worth*, with the engine's copy
winning every argument by being closer to the number on the screen.

**The translation is not free of judgement in exactly one place.** The provider
publishes each strand as its counts; the matcher demands the **published value**
beside them, because *the matcher reads what the player is shown and never
re-derives it*. So the value crossing here is ``StrandRatio.value`` — the
provider's own rounding, taken rather than recomputed — and the two counts travel
under it so that the matcher can stand a strand down below ``min_observations``
without ever needing to divide them itself.

**Three strands cross as nothing at all.** *Keeps plans* and *settles up* have
no provider on this platform, and *sportsmanship* has one the matcher may not
read (``docs/adr/0158``), so all three are absent from the mapping rather than
present at a nought — and the reliability term renormalises over the three that
arrived. That is why ``SportsmanshipStrand`` has no construction site anywhere in
this repository: the one strand that is a mean rather than a ratio is also the
one the matcher is forbidden to hear, and inventing a mean to exercise the shape
would put a number in a ranking that nobody agreed could be there.

**The third to arrive is *answers about results*** (``docs/adr/0160``), and
nothing about this translation changed to admit it — which is the point of the
shape. It is a ratio like the two beside it, it crosses as ``RatioStrand`` like
them, and the only thing that moved on this side of the seam is that three keys
arrive where two used to.

**Reliability stops being absent platform-wide the moment this is wired.** The
term is now a fact the platform *has*, which some people have no record for — so
a stood-down reliability becomes ``NOTHING_FROM_THEM`` rather than
``NOT_YET_ON_THIS_PLATFORM``, the evidence gate starts counting it as a
person-specific gap, and the live set goes from seven terms to eight. It excludes
nobody: the gate wants half of the live terms and a candidate the index can
produce always reads level, balance and distance plus at least one of intent,
availability and the two tag columns — four of eight, which clears a bar of
``0.5`` exactly as four of seven did (``docs/adr/0140``).
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.kernel import Clock
from app.modules.matchmaking.domain.ports import PlayerScoreReading, RatioStrand
from app.modules.player_score.domain.ports import PublishedScoreQuery
from app.modules.player_score.domain.strands import PlayerScore


@final
class PublishedPlayerScores:
    """``PlayerScoreQuery`` over ``player_score``'s published read."""

    def __init__(self, scores: PublishedScoreQuery, clock: Clock) -> None:
        self._scores = scores
        self._clock = clock

    async def readings_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, PlayerScoreReading]:
        """Each of these players' Player Score, for those that have one.

        **The clock is built here rather than taken**, the same choice
        ``GamesPlayedAndChallengesAnswered`` makes: both halves of the answer are
        facts about the instant the read happens — a plan is a ghost only once
        its entry window has closed — and a caller holding one instant could hold
        a stale one. The matcher's port takes no ``now`` for exactly that reason.

        A player with no record is **absent from the answer**, which is the
        provider's rule carried across unchanged rather than re-imposed: this
        loop answers about whoever the provider answered about, so there is no
        place here for an empty reading to be invented.
        """

        now = self._clock.now()
        published = await self._scores.scores_for(player_ids, now=now)
        return {
            player_id: _reading_of(score) for player_id, score in published.items()
        }


def _reading_of(score: PlayerScore) -> PlayerScoreReading:
    """One published score, as the engine's own shape.

    Every strand this platform publishes is a **ratio**, so every one of them
    crosses as ``RatioStrand``. The mean-shaped one is sportsmanship, which has no
    provider — and a translation that guessed which shape to build from the
    strand's name rather than from what arrived would be a second copy of the
    reading's own invariant, checked in the weaker place.
    """

    return PlayerScoreReading(
        strands={
            strand: RatioStrand(
                value=ratio.value,
                numerator=ratio.good,
                denominator=ratio.opportunities,
                observed_at=ratio.last_at,
            )
            for strand, ratio in score.strands.items()
        },
        published_score=score.published,
    )


__all__ = ["PublishedPlayerScores"]
