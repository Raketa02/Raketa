"""The Player Score: six strand names, three of them live, and one published number.

**This context keeps no record of its own.** It has no aggregate, no table and no
migration — every fact it publishes is folded out of ``games``' and
``bookings``' streams at the moment somebody asks. That is not an economy; it
is the whole shape (``docs/adr/0140``). A stored Player Score would be a second
place for *did that game happen* to be true, and the first one to be wrong would
be the copy every screen believed. It is the same refusal ``games``' standing and
``challenges``' standing already make about a single game, applied to the fold
over all of them.

**The six names, and which of them can be published today.**

+---------------------+-------------------------------------------------------+
| ``SHOWS_UP``        | live — a game played, or a final Didn't come (#657)    |
| ``ANSWERS_CHALLENGES`` | stands down — challenges no longer wait (#544)      |
| ``ANSWERS_RESULTS`` | live — a score answered inside its window, or ignored  |
| ``KEEPS_PLANS``     | live — a booked game kept, or broken by leaving (#544) |
| ``SETTLES_UP``      | stands down — the court money is taken up front        |
| ``SPORTSMANSHIP``   | stands down — it is not a ratio and never was          |
+---------------------+-------------------------------------------------------+

**A strand that stands down is not a zero, and it is not a half.** It is simply
not in the mapping, and a player with no strand at all is not in the answer —
``docs/adr/0098``'s test, which is whether a zero would be *measured* or
*invented*. Nobody has failed to answer a challenge since challenges stopped
waiting for answers, and nobody owes a court share, because a share is taken
before the game exists.

**The vocabulary is the engine's ``ReliabilityStrand`` and not a second spelling
of it.** The strand names are the *player's* words before they are the matcher's,
but they are a closed set with exactly one home, and a locally-declared enum here
would satisfy every contract in the suite while being free to drift — the failure
``tests/unit/test_social_tag_vocabulary.py`` refuses for the Social tags and
``tests/demands/`` refuses for these. A module may import an engine; the reverse
is the fence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from types import MappingProxyType
from typing import Final, Mapping, final

from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant, instant, invariant

#: What each strand is worth in the number **the player is shown**, and nothing
#: else. The matcher's two per-mode vectors over the same strands went with the
#: ranking (#580), so this is the only blend of them left — it exists because the
#: player reads *one* number on their own screen.
#:
#: **Six names, and the numbers are the original vector's own.** The published
#: blend was 35/20/15/12/10/8 while *confirms results* was a strand; it was struck
#: (``docs/adr/0137``) and its 15 came out with it rather than being
#: redistributed, precisely so that a third live strand could take that share
#: back without anything else moving — which is what ``docs/adr/0160`` does.
#: Nothing has been retuned in either direction, because nothing was learned: a
#: weight that moved would be a hypothesis about the player's own screen with no
#: evidence behind the move.
#:
#: **It sums to a hundred again, and that is an accident of arithmetic rather
#: than a rule.** It is not a budget: its basis is *the strands the player
#: actually has*, which is three today and was two yesterday, and the blend
#: renormalises over whatever is there. It summed to 85 while a name was
#: missing and nobody rescaled it; it sums to 100 now because the missing name
#: came back at its own share. What the numbers state is the ratios between the
#: names, and those have never moved.
#:
#: **They live here rather than in the ruleset**, and that is a boundary rather
#: than a convenience: this is what a player sees about themselves, and a number
#: a ruleset release could move would let a release change what somebody's own
#: profile says about them.
#:
#: Falsified if two players the same distance apart on this blend are
#: indistinguishable on no-show rate, challenge answer rate and result answer
#: rate: then the split between the three live names is wrong.
PUBLISHED_WEIGHTS: Mapping[ReliabilityStrand, int] = MappingProxyType(
    {
        ReliabilityStrand.SHOWS_UP: 35,
        ReliabilityStrand.ANSWERS_CHALLENGES: 20,
        ReliabilityStrand.ANSWERS_RESULTS: 15,
        ReliabilityStrand.KEEPS_PLANS: 12,
        ReliabilityStrand.SETTLES_UP: 10,
        ReliabilityStrand.SPORTSMANSHIP: 8,
    }
)


#: How far back *answers about results* remembers. **The one window in this
#: context, and it belongs to one strand** (``docs/adr/0160``).
#:
#: ``docs/adr/0140`` §4 refused a rolling window for *shows up* and *answers
#: challenges* and that refusal stands: every opportunity there counts for ever,
#: because a ratio over a career already fades with new evidence and a window
#: would make *out of what* stop meaning a career. This strand is the exception
#: and the reason is what it prices. Turning up and answering an invitation are
#: **commitments somebody made**; answering a score is a **habit of opening the
#: app**, and ADR-0049 has already said in as many words that a flat battery and
#: simple inattention are the same event to us. A mark for something that easy to
#: fail by accident, and that never lapses, is a mark a player cannot work off —
#: so this is the only strand where the platform forgets.
#:
#: **Twelve months.** It was chosen to equal the matcher's ``horizon_days`` — the
#: other place this platform decided a record had gone stale — and that horizon
#: went with the ranking (#580), so this is now the only one.
ANSWERED_RESULTS_WINDOW: Final = timedelta(days=365)


def answered_results_since(now: Instant) -> Instant:
    """The oldest score answer *answers about results* still counts.

    Written here rather than at the one call site so the subtraction has a home
    beside the number it subtracts, the way every window in ``games`` is a
    function beside its own constant.
    """

    return instant(now - ANSWERED_RESULTS_WINDOW)


def out_of_a_hundred(part: float, whole: float) -> int:
    """A proportion as the whole number a player is shown, **half rounding up.**

    ``round`` is not used: it rounds halves to even, so a player at exactly 45,5
    would be shown 46 one week and a player at 46,5 would be shown 46 the next,
    and nobody reading a percentage expects that. Spelled once and used by both a
    strand and the blend over them, so **one rule decides every figure a player
    sees**, and two of them cannot disagree about a half.

    **It is one rule, not one rounding, and the difference matters.** A strand is
    rounded to the figure the player is shown, and the blend is then taken over
    *those* figures rather than over the ratios behind them — deliberately, so
    that the number on the profile is the weighted mean of the numbers printed
    beside it. A blend over the unrounded ratios would be defensible arithmetic
    and would occasionally differ from the strands it claims to summarise by a
    point, which is the one thing a player reading their own screen would notice.
    """

    invariant(whole > 0, f"a proportion out of nothing: {whole}")
    return int(100 * part / whole + 0.5)


@final
@dataclass(frozen=True, slots=True)
class StrandRatio:
    """One strand: the opportunities, what came of them, and the last of them.

    **The denominator is an opportunity and never a total.** A strand exists
    because something *fell due* — a plan reached the end of its entry window, a
    seat reached its deadline — so a game still awaiting its entry and a seat
    still inside its day are in neither half. Publishing them either way would
    state a conclusion the clock has not reached.

    ``last_at`` is the most recent of those opportunities and is what the
    matcher's horizon reads once it is folded across the strands. It is the
    moment the opportunity **closed**, not the moment the plan was made: a game
    nobody recorded is observed when its entry window shuts, and dating it from
    the booking would age a record faster than the record aged.
    """

    good: int
    opportunities: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.opportunities >= 1,
            "a strand with no opportunity behind it is an absence, not a zero: "
            f"{self.opportunities}",
        )
        invariant(
            0 <= self.good <= self.opportunities,
            f"a strand claiming more good outcomes than opportunities: "
            f"{self.good}/{self.opportunities}",
        )

    @property
    def value(self) -> int:
        """The figure out of a hundred **the player is shown for this strand.**

        Derived here and nowhere else. Every consumer reads this rather than the
        two counts beside it, so a card, a profile and the matcher's evidence
        cannot print three roundings of one record.
        """

        return out_of_a_hundred(self.good, self.opportunities)


@final
@dataclass(frozen=True, slots=True)
class PlayerScore:
    """One player's record: the strands that could be published, and their blend.

    **A score with no strand in it is not a score.** Absence has one spelling —
    the player is not in the answer at all — because two spellings of *we have
    nothing* is how a measured nothing and an unasked question start being
    confused. It is the invariant the matcher's own ``PlayerScoreReading`` makes,
    stated on this side of the wire too so that the adapter between them can
    never be the thing that first noticed.

    **The blend renormalises over the strands that are there**, exactly as the
    reliability term renormalises inside itself. That is what makes a player with
    three strands comparable to a player with six without either of them being
    credited for a record nobody keeps, and it is why the three standing-down
    names cost the published number nothing.
    """

    strands: Mapping[ReliabilityStrand, StrandRatio]

    def __post_init__(self) -> None:
        invariant(
            bool(self.strands),
            "a Player Score with no strands is an absence, and an absence is "
            "spelled by not answering about that player at all",
        )

    @property
    def published(self) -> int:
        """The number out of a hundred **on the player's own profile.**

        The one deliberate blend in this system, and the reason it exists is that
        a player reads one number about themselves. It is read by three consumers
        and computed by none of them: the reliability floor, whose
        ``published_score_bar`` prices it, the player card, which prints it
        (``docs/adr/0140``), and the player record, which prints it **beside the
        rows it is the mean of** (``docs/adr/0159``). A penalty justified by a
        figure that exists nowhere a human can look is unexplainable, and a card
        that printed a figure the player's own profile disagreed with would be
        worse than a card that said nothing.

        The third consumer is why ``StrandRatio.value`` is worth deriving in one
        place rather than at each call site: the record prints this number and
        every figure under it on one screen, so two roundings of one record would
        be visible side by side.
        """

        weighted = sum(
            PUBLISHED_WEIGHTS[strand] * ratio.value
            for strand, ratio in self.strands.items()
        )
        basis = sum(PUBLISHED_WEIGHTS[strand] for strand in self.strands)
        # The strand values are already out of a hundred, so the weighted mean
        # is ``weighted / basis`` — over a hundred rather than over one, which is
        # why the whole is scaled to match rather than the part divided down.
        return out_of_a_hundred(weighted, 100 * basis)

    @property
    def last_at(self) -> Instant:
        """The freshest opportunity across every strand — what the horizon reads.

        **One moment over the whole score rather than one per strand**, because
        the strands share one cause: *this player stopped playing*. Two ages
        would be two places for it to disagree with itself, and the matcher asks
        one question of it.
        """

        return max(ratio.last_at for ratio in self.strands.values())


__all__ = [
    "ANSWERED_RESULTS_WINDOW",
    "answered_results_since",
    "PUBLISHED_WEIGHTS",
    "PlayerScore",
    "StrandRatio",
    "out_of_a_hundred",
]
