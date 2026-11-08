"""What this context asks of contexts it does not write. **Twelve demands.**

``docs/adr/0098``'s consumer-driven shape, and this is the second *consumer*
register on the platform after the matcher's. Every port here is declared in
**this context's own vocabulary** and satisfied by an adapter that translates —
which is what keeps a record from inheriting a card's closed list, a seat code
or a search record's band through a type it borrowed (``docs/adr/0159``).

**This context stores nothing, so there is no repository on this list.** It has
no aggregate, no table and no migration; every fact it publishes it reads through
the owning context's published port, and the one thing it decides for itself is
whether the reader may see any of them.

**Most are single-player reads and say so in their signatures.** A
record is one person opened by a deliberate tap, so a set-shaped port here would
be a contract nobody can honour cheaply for a caller that never batches. On
``SubjectVariety`` that signature is a **fence rather than a convenience**: the
fold behind it is deliberately unbounded, and a set-shaped version would be an
invitation to call a career statistic inside a walk over five hundred
candidates. On ``SubjectReliability`` it runs the other way — the provider's own
read is set-shaped for a caller that holds a whole group's members, and the
narrowing to one person happens in the adapter, so the shape of somebody else's
caller does not reach a sheet that will never batch.

**One sport crosses two of them, and it is the same sport both times.** The sheet
is *about* one sport, resolved in ``domain/sport_choice.py`` from what the reader
arrived from and what the subject is rated in, and the run of form is asked for
in it. That sport never reaches the admission: what a sheet is about and who may
be seen are two questions, and the second one is not the client's to influence.

**The disclosure port is the interesting one, and its shape is almost the whole
admission rule.** It does not answer *may this reader see this person* — that is
this context's decision and it is made in ``application/admission.py``. It
answers *has this reader already been shown this person*, as a yes or a no, and
three providers answer it: a court they shared, a group they are both in, and a
group the reader runs that the subject is in (#575). **The fourth strand is a
port of its own** (#773; ``docs/adr/0203`` §9): ``ShownToEverybody`` asks no
question about the reader at all — *does the Ranking show this person to
everybody* — so it is not a disclosure *to* anybody, and it takes the
response's one instant, since a listing ends when a clock passes.
"""

from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.player_record.domain.record import (
    GameOutcome,
    OpponentVariety,
    RecordRelation,
    ReliabilityFilter,
    ReliabilityPanel,
    SubjectIdentity,
    SubjectRating,
    WhatPlayersSaid,
)


@runtime_checkable
class SubjectIdentitySource(Protocol):
    """Who a person is, as a record may describe them. **One player at a time.**

    Composed from more than one provider behind the port — a name and a nickname
    belong to ``users``, a photograph, an area and a tag selection to the Player
    profile — which is ``docs/adr/0098``'s *a row names one implementation and
    not one provider*: the consumer asks one question and the adapter pays
    whatever that costs on the other side.
    """

    async def identity_of(self, player_id: UUID) -> SubjectIdentity | None:
        """This player's name and nickname, photograph, area and tags, or ``None``.

        **``None`` is every way a person cannot be described**: an id this
        platform has never issued, an account not yet named, and a
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
    """*Has this reader already been shown this person?* — yes or no.

    **The credential this route runs on.** A record is read *through* a prior
    disclosure and never *about* a person: without that, a route taking a player
    id is a player-enumeration endpoint, and a UUID being hard to guess is not an
    authorization model.

    **Three implementations, one question**, which is what lets an entry point
    satisfy the same demand without this context learning what it is: a court
    the pair were both on, a group they are both in, and a group the reader runs
    that the subject is in (#575).

    **A boolean, and nothing about where.** The gates that re-run on every open
    are about accounts and read no partition, so a disclosure has nothing to
    say beyond *yes*. What a reader *arrived from* is not on this port at all —
    it selects which sport a sheet is about and never who may be seen.
    """

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether this reader has been shown this person.

        ``False`` for a pair with nothing between them, which is the ordinary
        answer about almost everybody.
        """
        ...


@runtime_checkable
class ShownToEverybody(Protocol):
    """*Does the Ranking show this person to everybody?* — the record's fourth
    strand (``docs/adr/0203`` §9, #773).

    **Listed on General in at least one sport, and *Show me in General* on.**
    Lent by the Rankings context, read live: a player whose 90 days ran out, or
    who turned the switch off, opens to no stranger on the next tap. **It asks
    nothing about the reader**: General is a page anybody can read, with or
    without a level, so General discloses whom it shows to everybody at once.
    The gates still run after it, a block among them.
    """

    async def shows(self, subject_id: UUID, *, now: Instant) -> bool:
        """Whether this person is listed on General in a sport at ``now`` and
        not hidden from it. ``False`` for an id nobody holds."""
        ...


@runtime_checkable
class RecordGates(Protocol):
    """May this reader be shown this person **right now**?

    The two gates about accounts — the subject's hold, an account state that may
    not be shown — the reader's own hold, and **a block made by either of them**,
    re-evaluated live on every open, because a disclosure made in August is not a
    permission to show somebody in December (``docs/adr/0095``). They are spelled
    **once** on this platform; a second spelling of a safety gate is the defect
    the whole fail-closed rule exists to prevent.

    **A block is one of them again, in both directions** (``docs/adr/0203`` §8,
    #773, superseding ``docs/adr/0193`` §2 for the record): neither of a blocked
    pair opens the other's record, from anywhere, group-mates included. It is
    refused with the one unnamed refusal, so the blocked person cannot tell it
    from any other closed record. **A block state that cannot be read raises**
    — a gate that cannot be evaluated excludes, and an outage is not a verdict
    about a person, so the route answers 503 rather than the refusal.

    **No preference** (#575). The mutual gender preference says who a player is
    willing to be *matched* with, and every strand here is a court shared or a
    group shared or run — the pair have already been put in front of each
    other.

    **A hold points both ways.** The subject's is one of the three; the
    reader's own is this surface's entry rule, and it is here rather than in
    the use case because a hold would otherwise end at the one route that
    remembers who a player has been shown.
    """

    async def admits(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether the live gates still admit this pair."""
        ...


@runtime_checkable
class RelationsOfTheReader(Protocol):
    """Where **the reader** stands with this person (``docs/adr/0202`` §1–§2) —
    lent by Friends. **Facts on the sheet and never a gate**: asked only once
    the record is admitted, and they refuse nothing."""

    async def relation_to(self, *, reader_id: UUID, subject_id: UUID) -> RecordRelation:
        """The reader's relation to the subject: ``NONE`` where nothing stands,
        and on the reader's own record."""
        ...

    async def may_ask(self, *, reader_id: UUID, subject_id: UUID, now: Instant) -> bool:
        """Whether a friend request from the reader to the subject would be
        admitted at ``now`` (``docs/adr/0203`` §9, #773): they share a group, or
        the subject is listed on General and not hidden — **Friends' own rule**,
        the one the ask is admitted by, so *Add friend* is offered exactly where
        a press would go through. It says nothing of the daily limit, which
        refuses the press itself, nor of a block, which never reaches an open
        record."""
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
    """Player reliability — the figure in points, its band, *New* and the four
    counts (``docs/adr/0195`` §1, #659).

    **Everything crosses already taken.** The band is the backend's and *New*
    reads every game ever played through, so nothing on this side re-derives
    either — a second derivation would be a second place for the number a
    player reads about themselves to be true.

    **One player, and this is the one demand here whose provider reads a set.**
    ``PublishedScoreQuery`` answers about a whole collection, because a group's
    Members list asks about everybody it draws. A record is one deliberate tap,
    so the narrowing is the adapter's and this signature is the caller's own
    shape.
    """

    async def reliability_of(
        self, player_id: UUID, *, now: Instant
    ) -> ReliabilityPanel:
        """Their reliability — **always**: everyone starts at a hundred, so
        somebody nothing has happened to reads *100 · New* with every count at
        nought.

        ``now`` is taken rather than read, because every line under it is a fact
        about an instant — a game is played through once its window has closed,
        a line drops out six months after it happened — and every figure on one
        response is folded against one present.
        """
        ...


@runtime_checkable
class ReliabilityFilters(Protocol):
    """The reader's own reliability filter in their groups, and the figure that
    brings them back where somebody's keeps them off a court (``docs/adr/0195``
    §6, #661).

    **The eleventh demand, and the only one about the reader's groups rather than
    the subject.** It is asked on your own record alone — the ``/me`` wiring
    holds it and the other route has no such collaborator — because a filter is
    a preference about other people and a stranger's sheet must not say who
    filters whom. **It names nobody**: two counts and a band.

    **The pair rule's clause, counted.** Who a filter hides is the engine's
    ``passes_reliability_minimum`` over each group-mate's points and *New* — the
    same clause ``proposals``' pair rule asks — so the sheet cannot count a
    player the deck would deal.
    """

    async def filter_of(self, player_id: UUID, *, now: Instant) -> ReliabilityFilter:
        """Their minimum, how many of the players in their groups it hides out
        of how many, and — where somebody's filter there keeps them off a court
        — the figure that brings them back to everyone. Folded against one
        ``now``, like every figure on the sheet."""
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
    """What other players said about this person — **one answer, for every
    reader.**

    The one thing on this sheet the platform did not count for itself. It used
    to be the only demand here whose answer depended on **who is reading** — a
    coarse band for the subject, off a second method — until ``docs/adr/0179``
    §5 served the figure to its subject and retired the band; the cost is
    written there. This port has one method since, asked whoever reads.

    **One player, like every other read on this list.** A record is one
    deliberate tap. A set-shaped version would be a fold over fifty rows per
    candidate offered to a caller that walks five hundred of them — and the
    matcher must never read this in any shape at all, which is held by an import
    contract rather than by a signature.

    **No clock.** Nothing here decays: the window is fifty **people**, so an
    opinion falls out of the record when fifty others have since had one and
    never when a calendar passes. It is the one demand on this list that takes
    neither a sport nor an instant.
    """

    async def what_players_said(self, player_id: UUID) -> WhatPlayersSaid | None:
        """The figure and the count of people behind it.

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


#: What this context asks of the platform, declared as data so that *a port with
#: no registered implementation* is a question something can ask
#: (``app/bootstrap/player_record_demands.py``). A demand nobody executes is a
#: demand satisfied by accident.
PLAYER_RECORD_DEMANDS: tuple[type, ...] = (
    SubjectIdentitySource,
    RecordPhotoLink,
    PriorDisclosure,
    ShownToEverybody,
    RecordGates,
    RelationsOfTheReader,
    SubjectRatings,
    SubjectForm,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
    ReliabilityFilters,
)


__all__ = [
    "ShownToEverybody",
    "PLAYER_RECORD_DEMANDS",
    "PriorDisclosure",
    "RecordGates",
    "RecordPhotoLink",
    "RelationsOfTheReader",
    "ReliabilityFilters",
    "SubjectForm",
    "SubjectIdentitySource",
    "SubjectRatings",
    "SubjectReliability",
    "SubjectSportsmanship",
    "SubjectVariety",
]
