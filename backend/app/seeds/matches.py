"""Which matches exist, and what state each one is in.

Same rule as the three catalogs beside it: **a match is named for the state it
represents**, and the name is a checked claim rather than a comment. Six
plausible padel games would be one scenario — *a match is forming* — repeated six
times; what breaks a screen is the edges, so this is a list of them.

**Here the name is checked by the kernel itself.** Every other catalog checks a
property somebody wrote down; a match's whole point is that its state is
*derived*, so a scenario names the ``Situation`` it must resolve to and the
runner asks ``kernel.situation(record, None, at)`` on every run. Retune a
threshold and the seed stops and says which account's screen just changed. That
is the strongest available form of *an account whose name lies is worse than one
that is missing*: nothing about the card would look wrong.

**The instant the claim is checked at is part of the claim**, and it has to be: a
situation is a function of the record *and the clock*, so *this match is forming*
is only true until it is not. Each scenario carries the moment it is asserted at,
computed off the same fixed ``SEED_MONDAY`` the court claims hang from — so the
same run twice is the same state twice, and the check is not a different question
tomorrow.

**The seeded week's clock is what writes these matches, not the wall clock.**
Every other seeded aggregate is timeless — an account is registered whenever it
is registered — but a match *is* its clock: whether it committed, when a seat was
taken and when a hole opened all decide the situation its name promises. So the
Matches use cases are driven from a clock the runner sets to the scenario's own
instants, which is a port doing what a port is for. Left on the wall clock,
``committed_at`` would be *the day the seed happened to run* and the name would
be a claim about that day.

**No scenario says whether a court is held, and none may.** The hold ladder
decides that (ADR-0031), and it runs inside the same use cases the runner drives
— so a seeded match holds a court exactly when its seats and its clock say it
should, and ``held_since`` is the instant the seed's own week entered the tier.
Writing a hold into this catalog would be writing down the answer to the one
question the ladder exists to compute, and the seeded state would then agree with
the ladder only until somebody retuned a rung.

One scenario exists **for** the hold rather than beside it — ``HELD_SOFT``, a
court kept aside on the premise that certainty will rise. There is deliberately
no scenario for the club that holds nothing speculatively: its match resolves to
``forming``, which this catalog already names, and *"two matches saying the same
thing would be one scenario twice"* is a rule worth more than a second seeded
row. That state is invisible on a card by construction, so the place it is
checked is the ladder's own suite, where it can be asserted as *no hold* rather
than as a name that does not mention one.

**A leaver is seeded and her money is a checked claim too.** A vacancy and a
departure are two facts (ADR-0033), so a scenario that loses a player says what
that player's *money* is as well as what the match's state is — settled or open,
and whether her card names an amount at all. It is checked against the stored
departures on every run, for the same reason the situation is: a leaver's card
is the one surface where a wrong answer is somebody's refund.

**The outcome is not authored either.** Like the court hold, it is what the
rules composed on the way through the same use cases a request runs — the seed
passes the live quote and the aggregate decides. Writing an outcome into this
catalog would be writing down the answer to the question the departure exists to
compute.

**Still no seat claim, and now for a reason rather than because it does not
exist.** ADR-0081 refuses a thirty-seventh situation, so a claim moves no name
in this catalog at all: a scenario carrying one would resolve to ``forming``,
which the first entry already names, and *"two matches saying the same thing
would be one scenario twice"* is the rule ``HELD_SOFT`` was written under. It
would also be a claim that has certainly lapsed by the time anybody signs in —
five minutes measured from a fixed instant on a fixed week — so the seeded card
would say nothing. The place a claim is checked is its own suite, where it can
be asserted as *this seat is spoken for* rather than as a name that does not
mention one.

**And no money movements.** The ledger is ``Raketa02/Raketa#69``.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.kernel import (
    MINUTES_PER_DAY,
    Instant,
    MatchKind,
    Minutes,
    Outcome,
    PayModel,
    SeatShare,
    Situation,
    Sport,
    grosze,
    hours,
    minutes,
    shifted,
)

from app.modules.now.domain.cascade import Rung
from app.seeds.catalog import ACCOUNTS, EMPTY_HANDED
from app.seeds.courts import SEED_MONDAY, seed_slot


def seed_moment(*, day_offset: int = 0, hour: int = 12, minute: int = 0) -> Instant:
    """A fixed instant on the seeded week — never *now*, and never computed."""

    return shifted(
        SEED_MONDAY, minutes(day_offset * MINUTES_PER_DAY + hour * 60 + minute)
    )


#: When every seeded match was posted: a fortnight before the seeded week, so a
#: match is never *born past its own commitment deadline* by accident — which is
#: a different sentence from a deadline that has since passed, and one this
#: catalog says deliberately or not at all.
POSTED = shifted(SEED_MONDAY, minutes(-14 * MINUTES_PER_DAY))

SHARE = SeatShare(grosze(3800))


@dataclass(frozen=True)
class SituationClaim:
    """What a match's name promises, and the instant it promises it at.

    ``resolved_at`` is not a detail. A match that is *forming* on the Thursday
    before is *cancelled, incomplete* on the Monday after, and both are true of
    the same record — so a claim with no clock is not a claim.
    """

    promise: str
    situation: Situation
    resolved_at: Instant


@dataclass(frozen=True)
class DepartureClaim:
    """What a seeded leaver's money is, checked against the stored departure.

    ``outcome`` is ``None`` for a departure still waiting on a filler, which is
    a claim in its own right and the most fragile one here: it is the state a
    card renders as *not yet decided*, and it stops being true the moment
    anything settles her.

    ``names_an_amount`` is the two payload forms (ADR-0072) as a claim. It is
    not derivable from the outcome for a reader of this file, which is exactly
    why it is written down: *nothing was taken* and *nothing has come back yet*
    are the two sentences a seeded card must be able to tell apart.
    """

    promise: str
    outcome: Outcome | None
    names_an_amount: bool


@dataclass(frozen=True)
class OfferClaim:
    """Who the invitation cascade told about a hole, and on which rung.

    ADR-0061's ladder, standing in the catalog exactly as the standby claim
    does: what the name promises is that a seat which freed **reached
    somebody**, and the rung says *why her* rather than *how soon*. It is the
    strongest form of this catalog's rule available for the cascade, because an
    offer is not a fact anybody can seed directly — it is what a dispatch
    computes from the pool, the band and the fit, so a claim that holds is a
    claim the whole ladder produced.

    ``player_slug`` names an account catalog entry, so an offer cannot point at
    a player who does not exist without the run stopping. It must be an account
    the scenario does **not** seat: a seat holder is refused by the pool's own
    ``NotAlreadyMine``, so a claim naming one could never hold.

    ``rung`` is checked rather than described. Rung 1 is the standby promise —
    *somebody who asked for this match is told first* — and a scenario claiming
    it while its queue is empty is a scenario whose name has drifted off the
    ladder that produced it.
    """

    promise: str
    player_slug: str
    rung: Rung


@dataclass(frozen=True)
class ScoreClaim:
    """A score on the table, and which side put it there.

    ``by_seat`` is a seat index rather than an account slug, for the reason
    ``taken`` and ``paid`` are counts: *which* player typed it is not a fact any
    screen is developed against, and what the rendering turns on is only whether
    the viewer is on that side of the net.

    ``proposals`` is what the catalog **promises** rather than what it writes —
    the run counts the stored one and refuses a name that has drifted, which is
    the only way *a lone proposal* and *both sides have spoken* can be told
    apart on a card, and they settle in opposite directions.
    """

    promise: str
    sets: tuple[tuple[int, int], ...]
    by_seat: int
    at: Instant
    proposals: int = 1


@dataclass(frozen=True)
class StandbyClaim:
    """Who is queued for this match, and what her card must therefore say.

    The catalog's rule applied to the one membership that confers nothing: a
    standby place is *priority, not a place*, so there is no position to name —
    what the name promises is the **situation the queued account resolves to**,
    which the kernel is asked on every run exactly as it is asked for the match
    itself.

    ``player_slug`` names an account catalog entry, so a queue place cannot
    point at a player who does not exist without the run stopping. It must be
    an account the scenario does **not** seat: rung 7 tests *not seated*, and a
    queued seat holder resolves to whatever her seat says.
    """

    promise: str
    player_slug: str
    situation: Situation
    resolved_at: Instant


@dataclass(frozen=True)
class SeedMatch:
    """One deterministic match: whose club, when, and how far along it is.

    ``club_slug`` and ``category`` name the club catalog's own entries, so a
    match cannot point at a club that does not exist without the run stopping.

    ``taken`` and ``paid`` are counts rather than named players, because *which*
    player holds seat 2 is not a fact any screen is developed against — the
    seeded accounts fill them in catalog order, so signing in as one of them
    still shows her own match.

    ``seats`` is the exception that the demo week made necessary
    (``Raketa02/Raketa#96``). *Which* player holds seat 2 stops being a detail
    the moment the week has to be **walked by one address**: all three regions
    of Now are non-empty together only for a viewer who is rated at the sports
    she is being ranked at *and* holds a seat somewhere, and the account rated in
    all four sports is the last entry in a catalog ordered emptiest-first, so
    counting from the head can never reach her. Empty means *the catalog's own
    order*, which is what every scenario wanted while the only question was what
    a match looks like from the outside.
    """

    slug: str
    description: str
    claim: SituationClaim
    club_slug: str
    category: str
    sport: Sport
    start: Instant
    duration: Minutes
    share: SeatShare = SHARE
    posted_at: Instant = POSTED
    taken: int = 0
    paid: int = 0
    #: Which accounts hold the seats, by slug and in seat order. Empty means the
    #: account catalog's own order, minus the accounts whose names promise
    #: nothing at all.
    seats: tuple[str, ...] = ()
    #: When the seats are taken, which is what decides whether filling the match
    #: commits it — a match that fills past its own deadline commits on the spot.
    joined_at: Instant = POSTED
    vacated: int = 0
    vacated_at: Instant | None = None
    #: What the leavers' money is, when a scenario loses anybody.
    departure: DepartureClaim | None = None
    kind: MatchKind = MatchKind.OPEN
    pay_model: PayModel = PayModel.SPLIT
    open_seats: int = 0
    #: One of the four cancellation causes, by name, or nothing.
    cancelled: str | None = None
    cancelled_at: Instant | None = None
    #: The score on the table, for a scenario that has one. `None` everywhere
    #: else, because a bare table is what every other played match is testing.
    score: ScoreClaim | None = None
    #: Who asked to be told if a seat frees here, and what her card then says.
    #: Empty for every scenario but the one — a queue place changes nothing
    #: about the *match*, so it is a fact hung on a scenario rather than a
    #: scenario of its own, exactly as ``HELD_SOFT``'s hold is not.
    standby: tuple[StandbyClaim, ...] = ()
    offers: tuple[OfferClaim, ...] = ()
    """Who the cascade told about this scenario's hole (ADR-0061).

    Empty for every scenario that loses nobody — there is no hole, so there is
    nothing to tell anybody about — and refused for one that does not, below."""

    def __post_init__(self) -> None:
        if self.paid > self.taken:
            raise ValueError(
                f"'{self.slug}': {self.paid} seats paid of {self.taken} taken — "
                "a paid seat with nobody on it is not a state"
            )
        if self.vacated and self.vacated_at is None:
            raise ValueError(
                f"'{self.slug}' leaves a hole and does not say when. A vacancy "
                "with no instant cannot decay, which is the defect the "
                "twenty-four hours exist to fix."
            )
        if self.vacated > self.taken:
            raise ValueError(
                f"'{self.slug}' loses {self.vacated} of {self.taken} players"
            )
        if bool(self.vacated) != (self.departure is not None):
            raise ValueError(
                f"'{self.slug}': a scenario that loses a player says what that "
                "player's money is, and one that loses nobody has none to say. "
                "A vacancy and a departure are two facts and both are seeded."
            )
        if self.kind is MatchKind.OPEN and self.open_seats:
            raise ValueError(
                f"'{self.slug}' is an open match with seats to open. Every seat "
                "of an open match is on sale already — that is what open means."
            )
        if (self.cancelled is None) != (self.cancelled_at is None):
            raise ValueError(
                f"'{self.slug}': a cancellation is a moment as well as a cause"
            )
        if self.seats and len(self.seats) != self.taken:
            raise ValueError(
                f"'{self.slug}' seats {self.taken} players and names "
                f"{len(self.seats)} of them. A partial seat list is a scenario "
                "that is half-authored: the rest would silently fall back to "
                "the catalog's order, which is the answer naming them was "
                "meant to replace."
            )
        if len(self.seats) != len(set(self.seats)):
            raise ValueError(
                f"'{self.slug}' seats somebody twice, which the aggregate "
                "refuses — a player holds one seat in a match or none."
            )
        queued = [claim.player_slug for claim in self.standby]
        if len(queued) != len(set(queued)):
            raise ValueError(
                f"'{self.slug}' queues somebody twice. Asking twice is asking "
                "once — that is what makes leaving idempotent — so a catalog "
                "that says it twice is saying one thing in two rows."
            )


FORMING = SeedMatch(
    slug="match-forming",
    description=(
        "A padel match somebody posted and nobody has joined. The ordinary "
        "case, and the one every other scenario is an edge off: four empty "
        "seats, no court held, a commitment deadline still days away."
    ),
    claim=SituationClaim(
        promise="a match still forming, days out",
        situation=Situation.FORMING,
        resolved_at=seed_moment(day_offset=1, hour=12),
    ),
    club_slug="club-that-needs-a-turnaround",
    category="Padel · indoor",
    sport=Sport.PADEL,
    start=seed_slot(18, day_offset=4).start,
    duration=hours(1),
)

HELD_SEAT = SeedMatch(
    slug="match-with-a-seat-held-and-unpaid",
    description=(
        "One player is on it and has not paid. **Held and paid are two facts**, "
        "and this is the state that proves it: counting her as filled would "
        "tell the other three the match is a quarter full when her seat may "
        "still lapse."
    ),
    claim=SituationClaim(
        promise="a seat somebody holds and nobody has paid for",
        situation=Situation.FORMING_HELD,
        resolved_at=seed_moment(day_offset=1, hour=12),
    ),
    club_slug="club-that-needs-a-turnaround",
    category="Padel · indoor",
    sport=Sport.PADEL,
    start=seed_slot(19, day_offset=4).start,
    duration=hours(1),
    taken=1,
    paid=0,
    joined_at=seed_moment(day_offset=1, hour=9),
)

FORMING_LATE = SeedMatch(
    slug="match-past-its-commitment-deadline",
    description=(
        "Two of four seats paid and the commitment deadline gone by. It has "
        "**not** committed — commitment needs the deadline *and* a full match — "
        "so the card says the deadline has passed rather than that anybody is "
        "bound. Its speculative hold lapsed twelve hours out, which is what "
        "makes this the plain sentence rather than the held one."
    ),
    claim=SituationClaim(
        promise="a match short of players with its deadline behind it",
        situation=Situation.FORMING_LATE,
        resolved_at=seed_moment(day_offset=4, hour=12),
    ),
    club_slug="club-with-two-padel-categories",
    category="Padel · Mondo, indoor",
    sport=Sport.PADEL,
    start=seed_slot(20, day_offset=4).start,
    duration=hours(1),
    taken=2,
    paid=2,
    joined_at=seed_moment(day_offset=1, hour=9),
)

RECOVERING = SeedMatch(
    slug="match-that-lost-a-player",
    description=(
        "A committed match one seat short, because somebody left half an hour "
        "ago. **Recovery is above full and above the court group**: describing "
        "this as an ordinary forming match is a catastrophic thing to tell "
        "three people whose money is at stake. It terminates because the "
        "vacancy does — a filler closes the hole and the rung stops firing on "
        "the same read, which is the mechanism the prototype never had."
    ),
    claim=SituationClaim(
        promise="a committed match with a hole somebody left in it",
        situation=Situation.REPLACEMENT,
        resolved_at=seed_moment(day_offset=4, hour=20),
    ),
    club_slug="club-that-needs-a-turnaround",
    category="Padel · indoor",
    sport=Sport.PADEL,
    start=seed_slot(18, day_offset=5).start,
    duration=hours(1),
    taken=4,
    paid=4,
    # **Named because the band is part of the claim.** ADR-0061 makes the level
    # band a hard wall and the pairing engine reads it off *the seats that are
    # left*, so who is on this match decides who the cascade below can reach —
    # and the offer claim names a rung, which is the thing the whole catalog
    # exists to stop drifting. Under the catalog's own order the fourth seat
    # went to an Established padel player, the mean rose with her, and the
    # account this match is supposed to reach fell outside the wall: the offer
    # simply stopped existing, with nothing in the record looking wrong.
    #
    # **The leaver is the Established one**, and that is the same argument
    # arriving as an ordering: she is gone by the time the ladder walks, so what
    # is left is the New-band group the offer is aimed at. It also gives the
    # third audience a *rated* player, which is the leaver worth developing
    # against — a card about a refund, drawn for somebody the platform knows.
    seats=(
        "rating-barely-established",
        "assessment-in-progress",
        "assessment-abandoned",
        "assessment-completed",
    ),
    joined_at=seed_moment(day_offset=4, hour=19),
    vacated=1,
    vacated_at=seed_moment(day_offset=4, hour=19, minute=30),
    standby=(
        StandbyClaim(
            promise=(
                "a player queued for a match she holds no seat in — the one "
                "situation only a viewer can be in, and the only card in the "
                "product whose act is a bare write (ADR-0040, ADR-0087)"
            ),
            player_slug="rated-in-every-sport",
            situation=Situation.WAITLISTED,
            resolved_at=seed_moment(day_offset=4, hour=20),
        ),
    ),
    offers=(
        OfferClaim(
            promise=(
                "the seat this match lost, in front of the player who asked "
                "about it — rung 1 of the invitation ladder, and the whole of "
                "what joining a standby queue buys (ADR-0061)"
            ),
            player_slug="rated-in-every-sport",
            rung=Rung.STANDBY,
        ),
    ),
    departure=DepartureClaim(
        promise=(
            "a leaver who paid, whose money nothing has decided yet — the "
            "third audience, and the one whose card is about a refund rather "
            "than about a game"
        ),
        outcome=None,
        names_an_amount=True,
    ),
)

NEEDS_RESULT = SeedMatch(
    slug="match-played-and-unscored",
    description=(
        "Two players, played, and nobody has entered a score. The card asks "
        "for one, and it asks for twenty-four hours rather than the "
        "prototype's thirty minutes (ADR-0048). Past that it becomes an "
        "evening rather than evidence, with no penalty to anybody."
    ),
    claim=SituationClaim(
        promise="a played match waiting for a score",
        situation=Situation.NEEDS_RESULT,
        resolved_at=seed_moment(day_offset=1, hour=21),
    ),
    club_slug="club-that-retired-a-court",
    category="Squash · glass back",
    sport=Sport.SQUASH,
    start=seed_slot(19, day_offset=1).start,
    duration=hours(1),
    taken=2,
    paid=2,
    joined_at=seed_moment(day_offset=0, hour=9),
)

CONFIRM_RESULT = SeedMatch(
    slug="match-with-a-score-on-the-table",
    description=(
        "Four players, played, and one side has entered a score the other has "
        "not answered. The card asks the opponents to agree and asks the "
        "proposing side nothing — and if nobody answers, silence confirms it "
        "twenty-four hours after the proposal rather than after the match "
        "(ADR-0048). It is the one seeded state where the two deadlines are "
        "different instants, which is what the reversal in that ADR bought."
    ),
    claim=SituationClaim(
        promise="a played match with a score awaiting an answer",
        situation=Situation.CONFIRM_RESULT,
        resolved_at=seed_moment(day_offset=1, hour=22),
    ),
    club_slug="club-with-two-padel-categories",
    category="Padel · Mondo, indoor",
    sport=Sport.PADEL,
    start=seed_slot(19, day_offset=1).start,
    duration=hours(1),
    taken=4,
    paid=4,
    joined_at=seed_moment(day_offset=0, hour=9),
    score=ScoreClaim(
        promise="a 6-4 7-6 from the first side, unanswered",
        sets=((6, 4), (7, 6)),
        by_seat=0,
        at=seed_moment(day_offset=1, hour=21),
    ),
)

PRIVATE_OPEN = SeedMatch(
    slug="match-private-with-seats-opened",
    description=(
        "Somebody's own court with two of its four seats put on the "
        "marketplace. A different money model rather than a variation on the "
        "open one: the owner carries every share nobody has paid, and opening "
        "a seat took unanimous consent from everybody already on it "
        "(ADR-0030). A private court is held hard and is never stale."
    ),
    claim=SituationClaim(
        promise="a private court with seats on the marketplace",
        situation=Situation.PRIVATE_OPEN,
        resolved_at=seed_moment(day_offset=1, hour=12),
    ),
    club_slug="club-with-two-padel-categories",
    category="Padel · Wall, outdoor",
    sport=Sport.PADEL,
    start=seed_slot(17, day_offset=5).start,
    duration=hours(1),
    taken=2,
    paid=2,
    joined_at=seed_moment(day_offset=1, hour=9),
    kind=MatchKind.PRIVATE,
    open_seats=2,
)

PRIVATE_PARTIAL = SeedMatch(
    slug="match-private-with-shares-outstanding",
    description=(
        "A private court split among its seats, with half the shares still "
        "unpaid and **no seat on the marketplace**. The owner's guarantee is "
        "the whole court and never shrinks (ADR-0045), so what this card is "
        "about is a liability rather than a game: two people owe nothing yet "
        "and she is carrying them. No v1 flow reaches this state — nothing "
        "opens a private court and nothing closes one — so it is seeded, and "
        "what is asserted of it is the rendering."
    ),
    claim=SituationClaim(
        promise="a private court carrying the shares nobody has paid",
        situation=Situation.PRIVATE_PARTIAL,
        resolved_at=seed_moment(day_offset=4, hour=20),
    ),
    club_slug="club-that-never-holds",
    category="Padel · indoor",
    sport=Sport.PADEL,
    start=seed_slot(11, day_offset=6).start,
    duration=hours(1),
    taken=2,
    paid=2,
    joined_at=seed_moment(day_offset=1, hour=9),
    kind=MatchKind.PRIVATE,
    open_seats=0,
)

PRIVATE_FULL = SeedMatch(
    slug="match-private-and-paid-for",
    description=(
        "The same split court with its last share paid. **The owner stops "
        "carrying it the moment it fills**, and that is why this is its own "
        "name rather than `privatePartial` at four seats: the published ladder "
        "resolved a full split court to the partial name, whose card goes on "
        "naming a liability against a court that has just discharged it "
        "(ADR-0072). The state-table research produced this key zero times, "
        "which is exactly why it needs seeding — nothing else in the system "
        "will ever hand a client one."
    ),
    claim=SituationClaim(
        promise="a private court whose shares are all in",
        situation=Situation.PRIVATE_FULL,
        resolved_at=seed_moment(day_offset=4, hour=20),
    ),
    club_slug="club-with-two-padel-categories",
    category="Padel · Wall, outdoor",
    sport=Sport.PADEL,
    start=seed_slot(13, day_offset=6).start,
    duration=hours(1),
    taken=4,
    paid=4,
    joined_at=seed_moment(day_offset=1, hour=9),
    kind=MatchKind.PRIVATE,
    open_seats=0,
)

PRIVATE_RESERVED = SeedMatch(
    slug="match-private-and-paid-outright",
    description=(
        "An ordinary court booking wearing a match's shape: one player paid for "
        "the whole thing and whoever turns up owes nothing (`solo`). It is the "
        "quietest card in the enumeration and deliberately so — there is no "
        "share to name, no counting worth printing, and `freeCancelHours` has "
        "no reader anywhere in the product, so the card is silent in both "
        "directions. Seeded because it is silent, not in spite of it: a "
        "rendering nobody can reach is a rendering nobody has ever seen."
    ),
    claim=SituationClaim(
        promise="a court one player bought outright and brought people to",
        situation=Situation.PRIVATE_RESERVED,
        resolved_at=seed_moment(day_offset=4, hour=20),
    ),
    club_slug="club-that-tightened-its-cap",
    category="Tennis · outdoor",
    sport=Sport.TENNIS,
    start=seed_slot(10, day_offset=6).start,
    duration=hours(1),
    taken=2,
    paid=0,
    joined_at=seed_moment(day_offset=1, hour=9),
    kind=MatchKind.PRIVATE,
    pay_model=PayModel.SOLO,
    open_seats=0,
)

FULL = SeedMatch(
    slug="match-nobody-can-join",
    description=(
        "Four seats taken and paid, with the commitment deadline still ahead of "
        "it — so it is **complete and not yet committed**, which are two facts "
        "and not one. It is the only seeded state shelf 2 is about: *full, but "
        "worth waiting for* ranks matches nobody can join, and until this "
        "scenario existed the only full matches on the seeded week were ones "
        "that had already been played, so the shelf had a subject for exactly "
        "as long as the wall clock sat before the week."
    ),
    claim=SituationClaim(
        promise="a complete match still short of its commitment deadline",
        situation=Situation.FULL,
        resolved_at=seed_moment(day_offset=4, hour=20),
    ),
    club_slug="club-that-retired-a-category",
    category="Badminton · hall A",
    sport=Sport.BADMINTON,
    start=seed_slot(18, day_offset=6).start,
    duration=hours(1),
    taken=4,
    paid=4,
    joined_at=seed_moment(day_offset=1, hour=9),
)

CANCELLED_BY_CLUB = SeedMatch(
    slug="match-the-club-cancelled",
    description=(
        "A manager cancelled it. **No reader can derive that**, which is why "
        "it is stored as its own flag and announced under its own name — and "
        "why the record being the explanation is what lets this context keep "
        "no history at all. Four cancellations, four different stories, and "
        "this is the one that is a decision rather than a receipt."
    ),
    claim=SituationClaim(
        promise="a match a manager cancelled",
        situation=Situation.CANCELLED_CLUB,
        resolved_at=seed_moment(day_offset=1, hour=12),
    ),
    club_slug="club-that-retired-a-court",
    category="Squash · glass back",
    sport=Sport.SQUASH,
    start=seed_slot(20, day_offset=5).start,
    duration=hours(1),
    taken=1,
    paid=1,
    joined_at=seed_moment(day_offset=0, hour=9),
    cancelled="club",
    cancelled_at=seed_moment(day_offset=1, hour=8),
)

HELD_SOFT = SeedMatch(
    slug="match-holding-a-court-softly",
    description=(
        "Three of four seats paid, a day out, and a court kept aside on the "
        "premise that the fourth will come. **Soft is the whole point**: the "
        "club may still sell this court to somebody who wants the whole thing, "
        "and the ladder is holding it only while the match keeps earning it "
        "(ADR-0031). Nothing here was seeded — the hold is what the ladder "
        "composed from the seats and the clock, and `heldSince` is the instant "
        "the third payment landed."
    ),
    claim=SituationClaim(
        promise="a court held softly, one seat from full",
        situation=Situation.HELD_SOFT,
        resolved_at=seed_moment(day_offset=3, hour=12),
    ),
    club_slug="club-that-needs-a-turnaround",
    category="Padel · indoor",
    sport=Sport.PADEL,
    start=seed_slot(20, day_offset=5).start,
    duration=hours(1),
    taken=3,
    paid=3,
    # **Named seats, and this is the pair's other half** — the whole of what
    # makes the seeded week walkable by a single address (`Raketa02/Raketa#96`).
    # Now's three regions are non-empty together only for a viewer who is rated
    # at the sports being ranked *and* holds a seat somewhere, and the account
    # rated in all four sports is the last entry in a catalog ordered
    # emptiest-first. It is this scenario rather than one more because a second
    # match saying *she has paid and is waiting* would be one scenario twice —
    # and because it is the state whose card is worth arriving at: a court kept
    # aside on her behalf, on terms the club can still withdraw.
    #
    # The hour is load-bearing. She is queued for `match-that-lost-a-player` at
    # 18:00 the same evening and the cascade's pool refuses a candidate with a
    # clash, so a seat here at that hour would take her off the one offer the
    # seeded week has.
    seats=(
        "rated-in-every-sport",
        "rating-well-established",
        "rating-barely-established",
    ),
    joined_at=seed_moment(day_offset=1, hour=9),
)

MATCHES: tuple[SeedMatch, ...] = (
    FORMING,
    HELD_SEAT,
    FORMING_LATE,
    RECOVERING,
    NEEDS_RESULT,
    CONFIRM_RESULT,
    FULL,
    PRIVATE_OPEN,
    PRIVATE_PARTIAL,
    PRIVATE_FULL,
    PRIVATE_RESERVED,
    HELD_SOFT,
    CANCELLED_BY_CLUB,
)


def _refuse_an_impossible_catalog() -> None:
    """Fail at import rather than part-way through a run.

    Two claims, and the second is the one this file gained a reason for. A slug
    that names nobody is a catalog half-edited, and it is checked here as well
    as in the runner because a run reaches the last scenario having already
    written every one above it. A slug naming an account whose name promises
    **nothing at all** is the failure `Raketa02/Raketa#96` was opened to close:
    every seeded match filled its seats from the head of the *account* catalog,
    so the account whose description reads *registered and nothing else* was
    sitting on every one that had anybody on it, drawing a Now screen nobody had
    asked it to draw.
    """

    known = {account.slug for account in ACCOUNTS}
    for match in MATCHES:
        named = (
            *match.seats,
            *(claim.player_slug for claim in match.standby),
            *(claim.player_slug for claim in match.offers),
        )
        for slug in named:
            if slug not in known:
                raise RuntimeError(
                    f"'{match.slug}' names the player '{slug}', which the "
                    f"account catalog does not hold."
                )
            if slug in EMPTY_HANDED:
                raise RuntimeError(
                    f"'{match.slug}' enrols '{slug}', whose name promises an "
                    f"empty screen. A seat and a queue place both put a card on "
                    f"her Now, and empty is the state a client is least likely "
                    f"to have a fixture for."
                )


_refuse_an_impossible_catalog()
