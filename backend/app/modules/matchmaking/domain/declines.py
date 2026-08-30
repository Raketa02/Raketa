"""*Not now* — the one answer to a prompt that writes no value, and its row.

A prompt is a question, and a question has three outcomes: it is **raised**, it
is **accepted**, or it is **declined**. The first two are recomputable from rows
that already exist — the raise conditions are counts over the search store, and
an accept is the player's own write through the route that owns the value — and
the third is nowhere. That asymmetry is the whole of why this module exists
(``search-telemetry.md`` §6).

**The gate is the cache; the evidence is the row** (``the-engine.md`` §12), which
is ``passes.py``'s split reached a second time by the same argument about a
**question** rather than about a person. ``prompts.py``'s two constants declare
falsifiers a TTL destroys — *take-up rate on the prompt* and *acceptance rate on
the offer* — and thirty days of silence bought by a Redis key is thirty days of
evidence that key then throws away. So ADR-0094's suppression keeps its window,
its scope and its refusal of an event, and stops living in Redis.

**It lives here, in ``matchmaking``, and it writes no profile.** The value a
decline suppresses an offer to change belongs to ``player_profile``; the record
is about **the question**, not the value, exactly as a pass's record is about the
deck rather than about the person — so ``prompts.py``'s *"nothing in this module
writes a profile"* stays literally true.

**A suppression retires nothing.** It stops the next **raise** and clears
nothing, so :class:`~app.modules.matchmaking.domain.prompts.PromptLedger`'s *two
methods and no delete* is untouched and a standing question still expires on its
own. A caller still cannot make a question quietly stop being asked; it can only
stop being **re-asked**, for a month, to the player who answered it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.matchmaking.domain.prompts import Prompt


class DeclineKey(StrEnum):
    """What a decline is keyed on. **Never the value the prompt quoted.**

    The player answered about a **habit**: declining *keep 22 km?* answers *keep
    32 km?* next week too, because a per-radius suppression silences a number the
    ladder hands them a different one of next month. So the key is read straight
    off the prompt's own identity, the way ``prompt_field`` already spells it —
    ``{code}`` or ``{code}:{sport}`` — and never off a second keying scheme.
    """

    #: One row, one player, every sport. The fact being asked about has no sport
    #: dimension.
    PLAYER = "PLAYER"
    #: One row per sport, because the fact being asked about is per sport.
    SPORT = "SPORT"


#: What each prompt's decline silences, or ``None`` for a prompt that does not
#: suppress at all. **Total over the union**, so a fifth prompt added in two
#: years cannot compile without an answer here, and ``KEEP_THESE_TIMES``'s
#: absence is a typed one rather than a line somebody forgot.
#:
#: **The line is whether the condition outlives the act**, not per-search versus
#: loop. An improvised grid is gone when the search ends and is a genuinely
#: different grid next Tuesday, which is ``the-play-screens.md`` §2's own reason
#: for no long suppression there; a widening habit, a drift and a week described
#: months ago are all still true tomorrow, so re-asking is the same question.
#:
#: **And it lands asymmetrically.** ``UPDATE_PLAY_INTENT`` is keyed per sport —
#: ADR-0094's *for that sport*, one declaration per sport. The other two are
#: keyed on the player: the availability grid is one week and not seven, and the
#: search radius is one number on ``PlayerProfile``, which has no sport
#: dimension — so a padel-driven prompt keyed per sport would go on offering to
#: change tennis with the same number.
DECLINE_KEYS: Final[Mapping[Prompt, DeclineKey | None]] = {
    Prompt.KEEP_THESE_TIMES: None,
    Prompt.KEEP_THIS_RADIUS: DeclineKey.PLAYER,
    Prompt.UPDATE_PLAY_INTENT: DeclineKey.SPORT,
    Prompt.REFRESH_YOUR_TIMES: DeclineKey.PLAYER,
}

#: How long one *not now* buys. ADR-0094's own thirty days, which its amendment
#: preserved **literally** while bending only where the suppression is kept — so
#: the number is that record's and not a release's, and it lives here beside the
#: rest of ``prompts.py``'s numbers rather than in the ruleset.
#:
#: It is also what handles the player whose habit genuinely changed: a
#: suppression that never lapsed would be a question the platform may never ask
#: again, decided by one tap on one evening.
DECLINE_SUPPRESS: Final = timedelta(days=30)


def suppresses(prompt: Prompt) -> bool:
    """Whether declining this prompt buys any silence at all."""

    return DECLINE_KEYS[prompt] is not None


def keyed_sport(prompt: Prompt, sport: Sport) -> Sport | None:
    """What this decline is keyed by: the sport it was declined on, or nobody's.

    The sport reaches here because every prompt is raised on a screen about one
    sport, and it is **dropped** for the two prompts whose subject has no sport —
    which is the asymmetry :data:`DECLINE_KEYS` argues for, applied at the one
    place a row is made.
    """

    invariant(suppresses(prompt), f"a {prompt.value} decline, which suppresses nothing")
    return sport if DECLINE_KEYS[prompt] is DeclineKey.SPORT else None


def silence_began(now: datetime) -> datetime:
    """The moment a decline has to be newer than to still be silencing.

    **A date, never a flag**, on the rule the pass record, the newcomer window
    and the interest expiry are all written under: a stored *is it still
    suppressed* goes stale hourly and a date does not. Here it is also the
    read's own cut-off, so the window is applied once, in one place, rather than
    by every caller folding rows against a clock.
    """

    return now - DECLINE_SUPPRESS


@final
@dataclass(frozen=True, slots=True)
class PromptDecline:
    """One *not now*, and the question it was an answer to.

    ``(player, prompt, sport, at)`` — and **no Origin key**. The pass's was
    bought for a named falsifier, *pass rate on re-shown profiles*, and nothing
    here demands one: a decline's falsifiers are take-up and acceptance rates
    over prompts whose raise conditions are already recomputable. Carrying a
    ``search_id`` because the neighbour does would be cargo, and it would make a
    prompt raised by a **loop** unrecordable.

    There is no ``expires_at`` and no state. The thirty-day window is
    :data:`DECLINE_SUPPRESS` read against ``at``; this row is what happened, and
    what happened does not lapse.
    """

    player_id: UUID
    prompt: Prompt
    #: The sport this decline is keyed by, or ``None`` for the player's own. Set
    #: through :func:`keyed_sport` and never from a request, because what a
    #: decline is keyed on is this backend's to decide.
    sport: Sport | None
    at: datetime

    def __post_init__(self) -> None:
        invariant(
            suppresses(self.prompt),
            f"a decline of {self.prompt.value}, which suppresses nothing",
        )
        invariant(
            (DECLINE_KEYS[self.prompt] is DeclineKey.SPORT) == (self.sport is not None),
            f"a {self.prompt.value} decline keyed on {self.sport}",
        )


@runtime_checkable
class PromptDeclineLedger(Protocol):
    """Every *not now* ever said, and the one question it answers back.

    **Write-only from the outside**, on ``PassLedger``'s template: there is no
    method here that lists a player's declines, counts them, or answers *has
    anybody declined this prompt* — no route returns a decline in any shape, and
    the corpus is read by a background reader over the table rather than through
    a port a request could reach.
    """

    async def record(self, decline: PromptDecline) -> None:
        """Write one decline. **In the caller's own transaction.**

        Append-only. A second decline of the same prompt is a second row with
        its own moment — nothing counts them and nothing may, because a tally is
        the shape a penalty grows out of, and what a second *not now* buys is
        exactly the same month the first did.
        """
        ...

    async def suppressed_for(
        self, *, player_id: UUID, sport: Sport, since: datetime
    ) -> frozenset[Prompt]:
        """Which prompts this player has declined recently enough to be silent.

        **One read per search**, answering about both families at once — the
        prompts keyed on the player and the ones keyed on this sport — which is
        the shape ``raised_for`` is written to beside it, and for its stated
        reason: a caller asking twice is a caller that could be told two things
        about one moment.

        ``since`` is :func:`silence_began`, passed in rather than known here: the
        window is a domain number and this is a store, and a store holding its
        own copy of it would be a second place for thirty days to be true.
        """
        ...
