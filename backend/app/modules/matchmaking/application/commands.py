"""What a client may ask for. **Asks only, never a fact about the searcher.**

The backend reads the profile, the grid, the radius, the tags, the rating, the
intent and the gender preference itself, at request time, and *that* read is what
travels inward. A stale radius supplied by a phone is a gate evaluated on a lie,
so there is no field here for one to arrive through — **there is no per-search
radius input at all**, and widening happens only by taking a rung offer.

**Taking a rung offer is a new search citing the one that offered it**, so two
of these fields arrive together and mean *this is that search*. The widening
itself is **not** sent: the radius a rung widens to is read off the offering
search's own record, because a radius a client could name would be the per-search
radius input this contract does not have.

``trace_id`` is not a client fact either: it is the request's own
``X-Request-ID``, assigned by this application's middleware, and it is here
because *"it showed me somebody strange"* has to reach the exact log line a year
later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, invariant
from app.modules.matchmaking.domain.prompts import Prompt
from app.modules.matchmaking.domain.relaxation import Rung


@final
@dataclass(frozen=True, slots=True)
class RunShortlistSearchCommand:
    """*Find me a game.* One tap, one search, and two taps are two searches."""

    searcher_id: UUID
    sport: Sport
    #: Which evening this one search is for. A ``SearchMode`` and never a
    #: ``PlayIntent``: the searcher's setting has two values and the candidate's
    #: declaration has three, and the distinct types are what make the collision
    #: a type error rather than a paragraph in a document.
    mode: SearchMode
    #: The grid to run **this one search** on, as the boundary spells a cell —
    #: ``(weekday, part)`` pairs, turned into a grid by the domain. ``None`` is
    #: *use the profile's own*, and it is emphatically not an empty grid.
    #:
    #: **The one ask that looks like a fact and is not.** A player editing the
    #: week on the search screen is asking about a different evening, not
    #: correcting the record — nothing here writes the profile, and the app
    #: offers to save it afterwards (``docs/adr/0099`` §3).
    availability_override: tuple[tuple[int, str], ...] | None
    #: The search whose offer this one accepts, and which rung of it. They travel
    #: together or not at all: a rung with nothing to cite would be a widening
    #: the engine never offered, and a citation with no rung would be a search
    #: claiming a lineage it does not use.
    offered_by_search_id: UUID | None
    rung: Rung | None
    trace_id: str


@final
@dataclass(frozen=True, slots=True)
class ExpressInterestCommand:
    """*Let's play.* One tap, costing nothing, that cites where it came from.

    **``search_id`` is required and non-nullable.** It is the origin key, and an
    interest citing a search that is unknown, that belongs to somebody else or
    that never showed this person is **refused, never linked as null**
    (``search-telemetry.md`` §4).

    **The position is not here**, and that is the same rule the rest of this file
    is written under: a client sends the ask and the backend reads the fact. The
    position is looked up on the cited search's own returned rows, so the origin
    key is true by construction rather than by a client being honest about where
    it was scrolled to.
    """

    from_player_id: UUID
    to_player_id: UUID
    sport: Sport
    search_id: UUID


@final
@dataclass(frozen=True, slots=True)
class RunDeckDealCommand:
    """*Match me.* One deal, and **the sport is the whole ask.**

    There is no ``mode`` here and there is nowhere for one to arrive: the deck
    reads the viewer's own declared Play intent for that sport, resolved
    backend-side, and ``NO_PREFERENCE`` inherits *for fun* rather than selecting a
    third vector (``the-two-contracts.md`` §6). A mode on this command would be
    the request field the telemetry constraint refuses — ``mode`` is ``NULL``
    exactly when the surface is the deck.

    There is no ``rung`` here either: **the relaxation ladder does not reach the
    deck** (``docs/adr/0099``), so a deal cannot be widened and there is no offer
    for one to cite.

    The **week** is an ask like the shortlist's, and for the same reason: a
    player who edits their week and taps *Match me* would otherwise be ranked on
    a week they have just replaced. It writes no profile either.
    """

    searcher_id: UUID
    sport: Sport
    #: The grid to run **this one deal** on, exactly as the shortlist spells it.
    #: ``None`` is *use the profile's own*, and it is not an empty grid.
    availability_override: tuple[tuple[int, str], ...] | None
    trace_id: str


@final
@dataclass(frozen=True, slots=True)
class RecordPassCommand:
    """*Not today.* One tap, on one card, citing the deal it was dealt in.

    **``search_id`` is required**, on the interest row's own rule and for a
    reason of its own: ``PASS_SUPPRESS``'s falsifier is *pass rate on re-shown
    profiles*, which is unmeasurable without knowing where a pass came from
    (``docs/adr/0128``). The position is read off the cited search rather than
    sent, exactly as it is for a yes.

    There is no field here for *how long*, and there will not be one. The
    suppression window is a released ruleset number with **zero contract
    surface** — no field, no code, no timestamp — and a client that could name
    one would be a client that could escalate a pass.
    """

    passer_id: UUID
    passed_id: UUID
    sport: Sport
    search_id: UUID


@final
@dataclass(frozen=True, slots=True)
class RecordPromptDeclineCommand:
    """*Not now.* One tap on a sheet, about a question and never about a value.

    **No Origin key**, and that is a decision rather than an omission: the pass's
    was bought for a named falsifier — *pass rate on re-shown profiles* — and
    nothing a decline is measured by needs one. Carrying a ``search_id`` because
    the neighbour does would be cargo, and it would make a prompt raised by a
    **loop** unrecordable.

    ``sport`` is *which screen asked*, and it is not the key. What the silence is
    keyed on is this backend's to decide (``declines.keyed_sport``): a
    declaration is per sport and a radius and a week are not, so for two of the
    three prompts this sport is dropped rather than stored. A client that could
    choose would be a client that could silence a question about tennis by
    answering one about padel.

    There is no field here for *how long*, and there will not be one — thirty
    days is ADR-0094's number and has no contract surface.
    """

    player_id: UUID
    prompt: Prompt
    sport: Sport


@final
@dataclass(frozen=True, slots=True)
class ReadInterestCommand:
    """*What have I got out, and who said yes back?*

    One field, because there is exactly one person whose interest anybody may
    read: their own. **Outgoing and mutuals only** — incoming-and-not-mutual
    never crosses in any shape, and there is no field here that could ask for it
    (``docs/adr/0109``).
    """

    player_id: UUID


@final
@dataclass(frozen=True, slots=True)
class RunLineupSearchCommand:
    """*Fill the seats.* One tap, one search, and a seated four comes back.

    **A line-up and filling seats are one ask that differs by one field.**
    ``locked_seats`` non-empty is ``FILL_SEATS``, derived at write time rather
    than sent, so hand-seating somebody and pressing ⚡ is the same shape as ⚡ on
    an empty court and there is no second route for a client to get wrong
    (``the-two-contracts.md`` §1).

    Everything else is the shortlist's own ask, for the reason the two surfaces
    share six stages: the mode, the week this one search runs on, and the rung
    offer it may be accepting. There is still no radius, and there is still no
    seat count — how many people sit down is the sport's own fact
    (``kernel/sports.py``), not a number a phone may name.

    **A fill names the challenge it completes, and says nothing else about the
    court** (``docs/adr/0150`` §2). ``completing_challenge_id`` and the three
    facts that challenge already holds are **mutually exclusive**: the sport, the
    kind of evening and who is already seated are read off the aggregate, and a
    caller supplying one of them is offering a second place for a fact to be
    true. The request's own boundary refuses that shape; the invariant below is
    the backstop for a caller inside this process, where a malformed command is a
    bug rather than somebody's typing.

    ``availability_override`` stays sendable beside a challenge — it is *this
    search's* week and says nothing about the court — and so do
    ``offered_by_search_id`` and ``rung``, which are about the search that
    offered a rung and not about anybody's line-up.
    """

    searcher_id: UUID
    #: ``None`` exactly when a challenge is named: the sport is that challenge's.
    sport: Sport | None
    #: ``None`` when a challenge is named, and the resolved mode never arrives
    #: here — a challenge born with one keeps it, and one born without takes the
    #: filler's declared Play intent through the deck's own mapping. **No mode
    #: picker appears anywhere.**
    mode: SearchMode | None
    #: Player ids the searcher has already seated by hand, in the order they were
    #: sent. **Their order is their seating**, so a builder that put somebody
    #: beside itself gets them beside itself. Empty when a challenge is named,
    #: because the locked seats are that challenge's live members.
    locked_seats: tuple[UUID, ...]
    #: The half-built court this fill completes, or nothing. It is what the
    #: open-challenge gate steps aside for, and it is the whole of what makes the
    #: people who accepted your court visible to the search meant to finish it.
    completing_challenge_id: UUID | None
    availability_override: tuple[tuple[int, str], ...] | None
    offered_by_search_id: UUID | None
    rung: Rung | None
    trace_id: str

    def __post_init__(self) -> None:
        if self.completing_challenge_id is None:
            invariant(
                self.sport is not None and self.mode is not None,
                "a line-up that names no challenge has to say its sport and its "
                f"mode: {self.sport}, {self.mode}",
            )
            return
        invariant(
            self.sport is None
            and self.mode is None
            and not self.locked_seats,
            "a fill names the challenge it completes and says nothing else "
            f"about the court: {self.sport}, {self.mode}, {self.locked_seats}",
        )


@final
@dataclass(frozen=True, slots=True)
class ForecastLineupCommand:
    """*What would this four leave on court?* **And it is not a search.**

    ``docs/adr/0108``: no candidates are generated, nothing is ranked, scored
    against the floor, withheld or explained — and **nothing is recorded**. A
    builder session of six edits would otherwise enter *searches run* as six
    searches, which is a lie in the one table the product uses to judge itself.

    **It is bound to a search the caller ran.** ``search_id`` is required and
    every player named must have appeared in that search's returned rows.
    Unbounded, this route is a level-and-band lookup for any player in the city,
    reachable by id — which is where the privacy line spent everywhere else in
    this design would leak.

    ``players`` are the people beside the searcher, **in seat order**: the first
    is the partner of the arrangement the response marks current. One, two or
    three of them, because a seat may be empty and *three of four* is an honest
    answer — what cannot be forecast is a court with nobody on it.
    """

    searcher_id: UUID
    sport: Sport
    mode: SearchMode
    search_id: UUID
    players: tuple[UUID, ...]
