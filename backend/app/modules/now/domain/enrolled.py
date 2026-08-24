"""What Now needs about a match the viewer is enrolled in, in Now's words.

The enrolled strip is the region a player is **committed** to, and it is the one
region on the screen that is not about inventory. Everything it prints comes from
four contexts — the match, its club, the court it will be played on and the money
that has moved — and this module is the one shape they meet in.

**The port answers facts and the composer applies rules.** A court's name is
here whether or not it may be shown; whether it may is
``kernel.court_named_at``, and it is asked once, in the composer. A score is here
in the order it was stored; putting the viewer's side first is the card's
judgement, and doing it in the adapter would make a stored fact depend on who is
looking. The same split keeps the counting, the clock, the twenty-four-hour tail
and the situation itself out of the infrastructure layer, where nothing about
them could be tested without a database.

**A leaver is here too.** ADR-0030's *"the leaver's card is the match's card
rendered for somebody who used to hold a seat"* means she is not a different
membership, so the port answers one list and the departure payload beside a row
is what says which audience it is. A strip that dropped her would hide the only
thing that decides her refund — whether her seat refills.

**And so is a standby place**, which is the one membership here that confers
nothing at all. ``waitlisted`` is the single situation only a viewer can be in
(ADR-0040) and it is one of the ten that name an act (ADR-0083, ADR-0087); the
strip is the only region on Now that could hold such a card, since the offers
region is seats offered to her and the ranked shelves exclude a match she is
queued for by rule. A card nowhere on the screen cannot carry a button, so the
row is here and the ladder is told through ``Viewer.on_standby`` — which the
kernel's played rung has expected since it shipped: *"a standby player and a
leaver both resolve to the post-play situation."*
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, MatchRecord

from app.modules.now.domain.screen import CardDeparture, Money, Place


@final
@dataclass(frozen=True)
class PlayedScore:
    """A stored score with each side's players named, in the match's own order.

    ``sides`` is side A then side B — the first half of the match's seats and
    the second, in the seats' fixed order — and ``sets`` reads in the same
    direction. ``viewer_side`` is the index of the side the viewer played on, or
    ``None`` for somebody who did not play.

    The flip that puts her side first is the composer's. Doing it here would
    make what the adapter reads out of the database depend on who asked, which
    is the one thing a stored fact must not do.
    """

    sides: tuple[tuple[str, ...], tuple[str, ...]]
    sets: tuple[tuple[int, int], ...]
    viewer_side: int | None = None


@final
@dataclass(frozen=True)
class Enrolment:
    """One match this viewer holds a seat in, or used to.

    ``record`` is the kernel's, because that is the vocabulary Matches publishes
    to be resolved and Now resolves — asking for anything narrower would be a
    second answer to *what is this match doing*.
    """

    match_id: UUID
    record: MatchRecord
    where: Place

    #: What one seat costs, and what the whole court costs. The first is the
    #: spine's price and is written for whoever is looking; the second is
    #: ``{price} settled to the club``, which has no audience at all.
    share: Money
    court_total: Money

    #: When the match stopped being a game anybody was going to play, for the
    #: five endings that had to record it. ``None`` for every match that is
    #: still one, and for a played match — whose closing is ``match_end``.
    closed_at: Instant | None = None

    #: Whether she is on it now. ``False`` with a departure beside it is the
    #: leaver; ``False`` with neither and no standby place cannot be produced by
    #: this port.
    holds_seat: bool = False

    #: Whether she asked to be told if a seat frees on this match. It is the
    #: **fourth** membership the strip has, after a seat, a departure and a live
    #: claim, and the only one that confers nothing: *priority, not a place*.
    #:
    #: It is a field on the row rather than a set the composer holds beside it
    #: because it is a fact about **this pair**, exactly like ``holds_seat``, and
    #: the kernel takes both through one ``Viewer``. A set passed alongside would
    #: be a second place the viewer is assembled.
    on_standby: bool = False

    #: Her own live seat claim on this match, if she is buying a seat in it.
    claim_expires_at: Instant | None = None

    #: The court the reservation names, if one has been assigned at all.
    #: **Whether it may be printed is not decided here** — a court is assigned
    #: and may be reassigned until fifteen minutes before play.
    court: str | None = None

    score: PlayedScore | None = None

    #: Her departure, in one of its two forms, when she is a leaver.
    departure: CardDeparture | None = None

    #: What she has actually put in for this seat, folded off her ledger. It is
    #: what a cancellation gives back, and it is read from the money rather than
    #: from the seat's price because a seat that was never paid for owes nothing
    #: back — and a card claiming a refund nobody is owed is worse than silence.
    paid_in: Money | None = None
