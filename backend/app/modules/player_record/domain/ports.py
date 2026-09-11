"""What this context asks of contexts it does not write. **Nine demands.**

``docs/adr/0098``'s consumer-driven shape, and this is the second *consumer*
register on the platform after the matcher's. Every port here is declared in
**this context's own vocabulary** and satisfied by an adapter that translates —
which is what keeps a record from inheriting a card's closed list, a challenge's
seat codes or a search record's bands through a type it borrowed
(``docs/adr/0159``).

**This context stores nothing, so there is no repository on this list.** It has
no aggregate, no table and no migration; every fact it publishes it reads through
the owning context's published port, and the one thing it decides for itself is
whether the reader may see any of them.

**Seven of the nine are single-player reads and say so in their signatures.** A
record is one person opened by a deliberate tap, so a set-shaped port here would
be a contract nobody can honour cheaply for a caller that never batches — the
mirror of the rule every read in ``matchmaking`` takes, where the caller always
has twenty rows and asks once. On ``SubjectVariety`` that signature is a **fence
rather than a convenience**: the fold behind it is deliberately unbounded, and a
set-shaped version would be an invitation to call a career statistic inside a
walk over five hundred candidates. On ``SubjectReliability`` it runs the other
way — the provider's own read is set-shaped for a caller that holds five hundred
candidates, and the narrowing to one person happens in the adapter, so the shape
of somebody else's caller does not reach a sheet that will never batch.

**One sport crosses two of them, and it is the same sport both times.** The sheet
is *about* one sport, resolved in ``domain/sport_choice.py`` from what the reader
arrived from and what the subject is rated in, and the run of form is asked for
in it. That sport never reaches ``RecordGates``, which runs in the partition of
the **disclosure** — what a sheet is about and who may be seen are two questions,
and the second one is not the client's to influence.

**The disclosure port is the interesting one, and its shape is the whole
admission rule.** It does not answer *may this reader see this person* — that is
this context's decision and it is made in ``application/admission.py``. It
answers *where has this reader already been shown this person*, in **sports**,
because the four fail-closed gates read the other side's preference off a
candidate index row and the index is keyed by sport. A disclosure that could not
say which partition it happened in would leave the gate unable to be evaluated,
and a gate that cannot be evaluated excludes.
"""

from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.player_record.domain.record import (
    GameOutcome,
    OpinionBand,
    OpponentVariety,
    ReliabilityPanel,
    SubjectIdentity,
    SubjectRating,
    WhatPlayersSaid,
)


@runtime_checkable
class SubjectIdentitySource(Protocol):
    """Who a person is, as a record may describe them. **One player at a time.**

    Composed from more than one provider behind the port — a handle belongs to
    ``users``, a photograph, an area and a tag selection to the Player profile —
    which is ``docs/adr/0098``'s *a row names one implementation and not one
    provider*: the consumer asks one question and the adapter pays whatever that
    costs on the other side.
    """

    async def identity_of(self, player_id: UUID) -> SubjectIdentity | None:
        """This player's handle, photograph, area and tags, or ``None``.

        **``None`` is every way a person cannot be described**: an id this
        platform has never issued, an account whose handle cannot be read, and a
        player who has not committed a profile. They are one answer here because
        they have one consequence — the record refuses, in the one shape it
        refuses in — and separating them would be the route answering *is this
        id real* about a stranger.
        """
        ...


@runtime_checkable
class RecordPhotoLink(Protocol):
    """Where a record's photograph is drawn from. **Minted per response.**

    A link is signed for minutes and this context stores nothing at all, so
    unlike a search record there is not even somewhere for a stale one to be
    kept. It is a separate port from the identity above rather than a fifth field
    on it because it is the one thing on this response that is not a *fact about
    the player* — it is an address that dies within the hour.
    """

    async def link_for(self, *, owner_id: UUID, photo_id: UUID) -> str:
        """A short-lived URL that reads that photo, **signed as its owner**.

        The owner is the person on the record and never the person looking: an
        object store keys the pair, so a link signed under the reader's id would
        reach an object that does not exist.
        """
        ...


@runtime_checkable
class PriorDisclosure(Protocol):
    """*Where has this reader already been shown this person?* — in sports.

    **The credential this route runs on.** A record is read *through* a prior
    disclosure and never *about* a person: without that, a route taking a player
    id is a player-enumeration endpoint, and a UUID being hard to guess is not an
    authorization model.

    **Three implementations, one question**, which is what lets a fourth entry
    point satisfy the same demand later without this context learning what a
    challenge is. A search of the reader's that returned them, a challenge the
    pair are both seated in, a game they both played.

    **The answer is sports and not booleans**, because the gates that re-run on
    every open read a candidate index row and the index is partitioned by sport.
    A search knows the sport it ran on; a challenge and a game know theirs. What
    a reader *arrived from* is not on this port at all — it selects which sport a
    sheet is about and never who may be seen.
    """

    async def partitions_between(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        """Every sport in whose partition this reader has been shown this person.

        Empty for a pair with nothing between them, which is the ordinary answer
        about almost everybody.

        ``now`` is taken rather than read for the reason every fold in this
        codebase takes it: two sources asked at two instants could disagree about
        whether the same challenge was still open. An implementation with nothing
        to fold — a search record, a game that has been played — is entitled to
        ignore it, and says so.
        """
        ...


@runtime_checkable
class RecordGates(Protocol):
    """May this reader be shown this person **right now**, in this partition?

    The four that fail closed — a block in either direction, an account hold, an
    account state that may not be shown, and the mutual gender preference —
    re-evaluated live on every open, because a disclosure made in August is not a
    permission to show somebody in December (``docs/adr/0095``). They are spelled
    **once** on this platform and called by name from both surfaces that show one
    player to another; a second spelling of a safety gate is the defect the whole
    fail-closed rule exists to prevent.

    **It answers about the pair, and a hold on either side of it refuses.** The
    subject's hold is one of the four; the reader's own is this surface's entry
    rule, and it is here rather than in the use case because a hold points both
    ways and would otherwise end at the one route that remembers what a search
    already showed.

    **A gate that cannot be evaluated excludes.** A reader with no profile to
    read a preference from, and a subject with no row in the partition asked
    about, are both *not admitted* rather than errors — which is the fail-closed
    rule applied to the read rather than an exception to it.
    """

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, sport: Sport
    ) -> bool:
        """Whether the live gates still admit this pair in this sport's partition.

        Asked **per partition** rather than over a set, because a record is about
        one person and the caller holds at most a handful of disclosures. The
        cost of that is real and is priced in ``application/admission.py``: each
        call is one reader profile, three set reads over a single id, and one
        index container bound.
        """
        ...


@runtime_checkable
class SubjectRatings(Protocol):
    """Every sport this person is rated in, and what the platform holds in each.

    **A read and never an aggregate.** ``rating``'s own repository remembers
    stream versions precisely so that a rating it found can be saved, and handing
    that to a sheet that draws a number would put a mutation path behind a `GET`.
    This port cannot express a write, which is the narrowness being real rather
    than promised.

    **One player at a time.** A record is one person opened by a deliberate tap,
    and every sport they hold is at most four streams — where the matcher's
    equivalent read answers about one sport over twenty people, because that is
    the shape *its* caller has.
    """

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, SubjectRating]:
        """This player's rating in each sport they hold one, keyed by sport.

        **A sport they are not rated in is absent** — never a population mean and
        never a nought, on the rule the whole platform applies to a fact nobody
        has measured. An empty mapping is the ordinary answer for somebody part
        way through onboarding.

        **A mapping and not a list**, because the caller's two questions are *do
        they hold this one* and *walk them in the registry's order*, and both are
        answered off a mapping without anybody having to promise an order the
        streams underneath do not have.
        """
        ...


@runtime_checkable
class SubjectForm(Protocol):
    """How this person's last few counted games went, **in one sport.**

    The run of form the skill card draws left to right. It takes the sport
    because the panel it lands on is about one, and a run built across every sport
    and drawn beneath a single sport's Level is squash results under a padel
    number — which is the defect this port exists to make unrepresentable rather
    than to fix.
    """

    async def last_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[GameOutcome, ...]:
        """Their last few counted results in this sport, **oldest to newest.**

        At most five, and **fewer is a real answer that is never padded** — the
        card draws the gap. Empty for somebody with none, which needs no second
        spelling here: a tuple that is short is already the whole of *there is
        less to show*, and this port answers about one player rather than a
        collection an absence could be spelled in.

        ``now`` is taken rather than read, because whether a result has settled is
        folded from the record and a clock (``docs/adr/0137``) and every fact on
        one response is folded against one instant.
        """
        ...


@runtime_checkable
class SubjectReliability(Protocol):
    """What the platform watched this person do — the pill and its rows.

    **The number the matcher acts on, and the rows it is the mean of.** The pill
    is the *published* Player Score at the player's own weights and never the
    matcher's per-mode blend of the same names, because a player who works their
    record back up must be able to watch the penalty lift — which is only true
    while the figure they can look at is the figure that demotes them.

    **The weights do not cross this port.** The blend arrives already taken. A
    row carrying its weight would let a reader re-derive the pill — a second
    rounding of a number the platform acts on — and would invite a sheet drawing
    one strand as worth more than another, which nothing on this surface claims.

    **One player, and this is the one demand here whose provider reads a set.**
    ``PublishedScoreQuery`` answers about a whole collection, because the matcher
    asks it once per search over every candidate still standing. A record is one
    deliberate tap, so the narrowing is the adapter's and this signature is the
    caller's own shape.
    """

    async def reliability_of(
        self, player_id: UUID, *, now: Instant
    ) -> ReliabilityPanel | None:
        """Their pill and their metered rows, or **nothing at all**.

        ``None`` for somebody the platform has watched nothing of — no plan that
        reached the end of its entry window, no seat that reached its deadline.
        The zone is omitted rather than drawn at nought, because nobody has
        failed to turn up who was never due to, and a section of noughts is how
        *no record* becomes *a bad record* on the one screen that cannot be
        appealed.

        A strand nobody can publish is missing from the rows the same way, so a
        panel that exists carries only what was actually observed.

        ``now`` is taken rather than read, because both live strands are facts
        about an instant — a plan is a ghost once its window has closed, a seat
        has lapsed once its day has run out — and every figure on one response is
        folded against one present.
        """
        ...


@runtime_checkable
class SubjectVariety(Protocol):
    """How widely this person spreads their games — over their **whole** record.

    **Unbounded, which is what makes it a career statistic.** *How widely do they
    spread their games* is a claim about a habit, not about a season, so there is
    no window and no decay here. A second window would be a figure that must not
    disagree with the matcher's horizon, and the two would eventually part
    company with nothing to notice.

    **One player, and the signature is the fence.** Every port on this list
    answers about one person because a record is one deliberate tap; this one
    would be dangerous in any other shape, because an unbounded fold behind a
    set-shaped read is a fold somebody calls once per candidate.

    **No sport reaches it.** Variety is about every game they have played, so
    unlike the run of form it is not narrowed by whichever sport the sheet turned
    out to be about — a person who plays padel with the same four faces and
    squash with twenty has one habit, and printing it per sport would be a
    different statistic under the same word.
    """

    async def variety_of(
        self, player_id: UUID, *, now: Instant
    ) -> OpponentVariety | None:
        """Their different faces and their counted games, or **nothing at all**.

        ``None`` for a player no counted game has been recorded for. The record
        omits the row rather than drawing a nought: a habit nobody has been
        observed having is not a narrow one, and ``0 / 0`` is arithmetic nothing
        can draw.

        ``now`` is taken rather than read, because whether a game was played is
        folded from a record against a clock and every fact on one response is
        folded against one instant.
        """
        ...


@runtime_checkable
class SubjectSportsmanship(Protocol):
    """What other players said about this person — **at two resolutions.**

    The one thing on this sheet the platform did not count for itself, and the
    only demand here whose answer depends on **who is reading**. Everything else
    is the same fact retitled; this is two different facts, and the reason is
    ``docs/adr/0158``'s: a published average beside a published count lets the
    person it is about subtract, name each new rating exactly, and go and find
    the one player who could have given it.

    **Two methods and not one answer a caller narrows.** A use case that received
    the figure and chose to draw a band from it would already be holding the
    subtraction — the rule is about what crosses the seam, not about what is
    rendered. So the sheet about *you* calls a method that has no figure in its
    return type, and the one that does is unreachable from it.

    **One player, like every other read on this list.** A record is one
    deliberate tap. A set-shaped version would be a fold over fifty rows per
    candidate offered to a caller that walks five hundred of them — and the
    matcher must never read this in any shape at all, which is held by an import
    contract rather than by a signature, because a Match Fit term reading a star
    average would look like every term beside it.

    **No clock.** Nothing here decays: the window is fifty **people**, so an
    opinion falls out of the record when fifty others have since had one and
    never when a calendar passes. It is the one demand on this list that takes
    neither a sport nor an instant.
    """

    async def what_players_said(self, player_id: UUID) -> WhatPlayersSaid | None:
        """The figure and the count of people behind it — **for a stranger.**

        ``None`` for somebody nobody has rated, which is most people: the sheet
        omits the whole zone rather than drawing a nought, because nobody has
        been unpleasant who has never been on a court with anybody.

        **Published from the very first rating.** There is no minimum, because
        the count crosses beside the figure and does the work a minimum would: a
        figure over one player visibly reads as one person's opinion. Withholding
        it until it looked more authoritative would be the platform waiting to
        sound sure.
        """
        ...

    async def band_for(self, player_id: UUID) -> OpinionBand | None:
        """The coarse band — **for the person it is about, and nobody else.**

        No count and no figure, at any point on the path: this is the whole
        answer their own sheet may carry. Three steps across the scale tell them
        that something is going wrong, which is the useful half; who to blame for
        it is the half that stops people answering honestly.

        ``None`` for a subject nobody has rated — the same absence
        :meth:`what_players_said` spells, so the sheet omits one field or the
        other and never draws an empty one.
        """
        ...


#: What this context asks of the platform, declared as data so that *a port with
#: no registered implementation* is a question something can ask
#: (``app/bootstrap/player_record_demands.py``). A demand nobody executes is a
#: demand satisfied by accident.
PLAYER_RECORD_DEMANDS: tuple[type, ...] = (
    SubjectIdentitySource,
    RecordPhotoLink,
    PriorDisclosure,
    RecordGates,
    SubjectRatings,
    SubjectForm,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
)


__all__ = [
    "PLAYER_RECORD_DEMANDS",
    "PriorDisclosure",
    "RecordGates",
    "RecordPhotoLink",
    "SubjectForm",
    "SubjectIdentitySource",
    "SubjectRatings",
    "SubjectReliability",
    "SubjectSportsmanship",
    "SubjectVariety",
]
