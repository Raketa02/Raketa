"""The prompts. **Each one raises a question and never changes a value.**

This is the platform's one deliberate refusal to act on what it can see. It
notices that a player has improvised a grid, that they keep taking the same
widening, that their searches disagree with their declaration, and that the week
they described is months old — and in every case it **asks**, inline, and accepts
whatever answer comes back (``matchmaking-engine.md`` §6.3, and ``docs/adr/0094``
for the shape).

Four raisers, two of them per search and two of them loops:

| Prompt | Raised by | Says |
| --- | --- | --- |
| ``KEEP_THESE_TIMES`` | this search | you improvised a week — save it? |
| ``KEEP_THIS_RADIUS`` | this search | you keep taking this widening — keep it? |
| ``UPDATE_PLAY_INTENT`` | the drift loop | your searches disagree with your intent |
| ``REFRESH_YOUR_TIMES`` | the staleness loop | the week you described is old |

**Why two of them are loops and two are not.** The first two are facts about *the
search that just ran* and are free where they are already known. The other two
are facts about a *history* — five searches, or a date months back — and reading
either on the request path would put an unbounded scan in front of a player
waiting for a shortlist. So they are computed on a cadence, written to a ledger
that expires, and read as one lookup beside the search.

**The ledger is a cache and never evidence.** Losing it costs a prompt nobody
sees this week and the loop raises it again on its next tick, which is why it
lives beside the exposure ledger in the ephemeral store rather than in a table
(``docs/adr/0093``). Nothing durable is owed here: a prompt is a question, and a
question that was never asked leaves nothing to reconstruct.

**Nothing in this module writes a profile.** Every one of the four ends at a
question on a screen; the writes are the player's own, through the routes that
already own those fields.

**The grid question is decided here rather than per surface.**
:func:`improvised_week` is the one comparison behind ``KEEP_THESE_TIMES``, and
all three surfaces that let a player edit the week for one evening — the
shortlist, the line-up and the deck — raise it through that function. The
workbench deliberately holds no prompts, so the shared rule lives with the
prompts instead.

**Every one of these questions now has a write to be answered by**, and none of
them is here: ``PUT /api/v1/play-intents/{sport}`` for the declaration, and
``PUT /api/v1/players/me/availability`` and ``PUT /api/v1/players/me/search-radius``
for the grid and the radius. A *yes* is the player making that request; this
module is not told, and does not need to be — ``KEEP_THIS_RADIUS`` stops because
a profile holding the widened radius takes no rung on the next search, and
``KEEP_THESE_TIMES`` stops because the improvised grid and the profile's now
agree.

**The other half of ``docs/adr/0094``'s pattern is built, and it is one module
over.** That record pairs the inline offer with a **30-day suppression on
decline**, and ``declines.py`` is that half: a *not now* is a durable row, and
the suppression is derived from it by one filter at the one place every prompt
converges. Three of the four suppress. The line is **whether the condition
outlives the act** rather than per-search versus loop — an improvised grid is
gone when the search ends, where a widening habit, a drift and a week described
months ago are all still true tomorrow — so ``KEEP_THESE_TIMES`` is the one
prompt that is asked again, for a reason ``the-play-screens.md`` §2 had already
written down.

**A suppression retires nothing**, which is why *two methods and no delete*
below survives it: declining stops the next **raise** and clears nothing, so the
question standing right now still expires on :data:`PROMPT_TTL` like any other
and a caller still cannot make a question quietly stop being asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.player_profile.domain.availability import AvailabilityGrid


class Prompt(StrEnum):
    """What the app is offering to ask. **Codes, never sentences.**

    The kernel's rule reaches the matcher unchanged (``docs/adr/0022``): the
    backend emits a code and the client writes the words. *"Keep 15 km?"* is one
    phrasing of ``KEEP_THIS_RADIUS`` in one language, and a backend that shipped
    it would own the copy for every client that ever exists.
    """

    KEEP_THESE_TIMES = "KEEP_THESE_TIMES"
    KEEP_THIS_RADIUS = "KEEP_THIS_RADIUS"
    UPDATE_PLAY_INTENT = "UPDATE_PLAY_INTENT"
    REFRESH_YOUR_TIMES = "REFRESH_YOUR_TIMES"


@final
@dataclass(frozen=True, slots=True)
class RaisedPrompt:
    """One prompt, with the value it is asking about and never a new one.

    The payload is what the player would be agreeing to — the grid they
    improvised, the radius they keep taking, the mode their searches keep using —
    so that the sheet can show the change rather than describing it. **It is the
    value already in play**, never a value the engine picked: the engine notices
    drift and asks; it never acts on it.
    """

    prompt: Prompt
    #: The widening they keep taking, in whole kilometres. ``KEEP_THIS_RADIUS``.
    radius_km: int | None = None
    #: The grid this search actually ran on, as slot codes.
    #: ``KEEP_THESE_TIMES``.
    #:
    #: **Two absences, and they are different answers.** ``None`` is *not this
    #: prompt*, exactly as it is for the two fields beside it; ``()`` is **a
    #: cleared week** — a player who unticked every cell and searched anyway,
    #: which is a legal edit (``player_profile``'s ``AvailabilityGrid.edited``)
    #: and therefore a legal thing to be asked about. One value carrying both
    #: made a cleared week violate this class's own invariant.
    slots: tuple[str, ...] | None = None
    #: The mode their recent searches keep choosing, as ``SearchMode`` spells it.
    #: ``UPDATE_PLAY_INTENT``.
    mode: str | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.prompt is Prompt.KEEP_THIS_RADIUS) == (self.radius_km is not None),
            f"a {self.prompt.value} prompt about {self.radius_km} km",
        )
        # Reads uniformly with the two beside it — *the payload is present
        # exactly for its own prompt* — where ``bool(self.slots)`` also asked
        # *and is not empty*, which is a question about the week rather than
        # about which prompt this is.
        invariant(
            (self.prompt is Prompt.KEEP_THESE_TIMES) == (self.slots is not None),
            f"a {self.prompt.value} prompt carrying {self.slots!r}",
        )
        invariant(
            (self.prompt is Prompt.UPDATE_PLAY_INTENT) == (self.mode is not None),
            f"a {self.prompt.value} prompt about mode {self.mode}",
        )


def improvised_week(
    *, asked: AvailabilityGrid, profile: AvailabilityGrid
) -> RaisedPrompt | None:
    """*Keep these times?* — or nothing at all, on the week a search ran on.

    **One rule, and three surfaces raise it.** The shortlist, the line-up and the
    deck each let a player edit the week for this evening, and each therefore
    owes them the offer to keep it; three copies of *is this the profile's own
    week* would be three chances for one of them to answer differently about one
    moment.

    It is a comparison and never a write: what comes back is the grid **already
    in play**, so the sheet can show the change rather than describe it.

    **A cleared week is a week.** Unticking every cell is an edit like any other
    and reaches here as ``()`` — the value the floor refuses at commit and
    accepts afterwards — where a profile that was blank already and stayed blank
    raises nothing, because the two grids agree.
    """

    if asked == profile:
        return None
    return RaisedPrompt(prompt=Prompt.KEEP_THESE_TIMES, slots=asked.codes)


#: How many searches in a row must disagree with a declaration before the drift
#: prompt is raised. §6.3's own number — *"Your last five padel searches were
#: competitive"* — and it is a rule a domain test can observe, so it lives here
#: and not in configuration.
#:
#: **Falsified by:** the take-up rate on the prompt. A threshold nobody ever acts
#: on is measuring a preference that does not exist, and the prompt is removed
#: rather than tuned — the disposal rule a rung that never converts is under.
#: **Computable now**: the raises are recomputable from the search store and the
#: declines are rows (``declines.py``), where a suppression held in a TTL would
#: have destroyed the half nothing else records.
INTENT_DRIFT_SEARCHES: Final = 5

#: How many times the same widening must be taken before the app offers to make
#: it permanent. Three rather than one, because the second take is still a player
#: exploring and the point of *offered, not applied* is that a widen is a choice
#: each time until they say otherwise.
#:
#: **Falsified by:** acceptance rate on the offer, against rung acceptance. A
#: player who takes rung B on every search and declines the offer every time is
#: telling us the widening is per-evening and the prompt is noise — and *every
#: time* is countable because each of those declines is a row (``declines.py``).
REPEATED_WIDENINGS: Final = 3

#: How old a grid must be before the backstop offers to refresh it. Sixty days is
#: the onset of §9.3.5's staleness curve, adopted as the point somebody already
#: argued a week's description stops describing a week — the *curve* is struck
#: (``docs/adr/0120``: it read account age, not the pair), and the observation
#: that made it is not.
#:
#: A prompt and never a dock: a stale grid is not scored differently, it is asked
#: about. That is the whole difference between this and the factor it replaces.
GRID_STALE_AFTER: Final = timedelta(days=60)

#: How long a raised prompt survives with nothing re-raising it. Comfortably past
#: both loops' daily cadence, so an ordinary tick refreshes it, and short enough
#: that a prompt whose condition stopped being true stops being asked within days
#: rather than staying up until somebody answers a question that no longer
#: applies.
PROMPT_TTL: Final = timedelta(days=3)


@runtime_checkable
class PromptLedger(Protocol):
    """Where a loop leaves a prompt for the next search to pick up.

    **Two methods and no delete.** A prompt is retired by its own expiry or by
    the loop no longer raising it, never by a caller — a method to clear one
    would be a method something reaches for on the request path, which is how a
    question a player never answered quietly stops being asked.

    Both fail **soft** at the seam that wraps them: a ledger that cannot be
    reached costs a prompt, and a search that refused because it could not ask a
    question would be the courtesy taking the feature down.
    """

    async def raise_prompt(
        self,
        *,
        player_id: UUID,
        prompt: Prompt,
        sport: Sport | None = None,
        detail: str | None = None,
    ) -> None:
        """Leave this prompt standing for the player.

        Idempotent, and that is a requirement rather than a convenience: the
        loops that call it run in every API process, so raising the same prompt
        four times a day must be indistinguishable from raising it once.

        ``sport`` is ``None`` for a prompt about the player rather than about one
        sport — the availability grid is one week, not seven — and a sport-shaped
        prompt is only ever read back on a search in that sport.
        """
        ...

    async def raised_for(
        self, *, player_id: UUID, sport: Sport
    ) -> Mapping[Prompt, str | None]:
        """Every prompt standing for this player in this sport, with its detail.

        One read per search, and it answers about both families: the prompts
        raised about the player and the ones raised about this sport. A caller
        asking twice is a caller that could be told two things about one moment.
        """
        ...
