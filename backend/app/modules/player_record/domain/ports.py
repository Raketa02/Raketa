"""What this context asks of contexts it does not write. **Six demands.**

``docs/adr/0098``'s consumer-driven shape, and this is the second *consumer*
register on the platform after the matcher's. Every port here is declared in
**this context's own vocabulary** and satisfied by an adapter that translates —
which is what keeps a record from inheriting a card's closed list, a challenge's
seat codes or a search record's bands through a type it borrowed
(``docs/adr/0155``).

**This context stores nothing, so there is no repository on this list.** It has
no aggregate, no table and no migration; every fact it publishes it reads through
the owning context's published port, and the one thing it decides for itself is
whether the reader may see any of them.

**Four of the six are single-player reads and say so in their signatures.** A
record is one person opened by a deliberate tap, so a set-shaped port here would
be a contract nobody can honour cheaply for a caller that never batches — the
mirror of the rule every read in ``matchmaking`` takes, where the caller always
has twenty rows and asks once.

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
    SubjectIdentity,
    SubjectRating,
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
)


__all__ = [
    "PLAYER_RECORD_DEMANDS",
    "PriorDisclosure",
    "RecordGates",
    "RecordPhotoLink",
    "SubjectForm",
    "SubjectIdentitySource",
    "SubjectRatings",
]
