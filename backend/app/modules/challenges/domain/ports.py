"""The two seams this context is built on: one to write a challenge, one to ask
whether a game is already being arranged between two people.

``ChallengeRepository`` is the **aggregate repository** kind — how a use case
reaches an event-sourced ``Challenge`` without knowing that it is event-sourced,
owning the aggregate-type name, the replay and the optimistic-concurrency
bookkeeping.

``OpenChallengeQuery`` is the read kind, and it exists because **one open
challenge per pair, across every sport** is a rule no aggregate can enforce on
its own: it is a statement about every *other* challenge, and a challenge that
could see them would not be an aggregate.

**Across every sport, and not by oversight.** Two people are either arranging a
game or they are not; asking for padel while your tennis challenge sits
unanswered is pestering with a sport chip on it. The matcher's own
``OpenChallenge`` carries no sport field at all, so this is the rule its shipped
contract already assumed rather than a new restriction — which is why nothing on
this port takes a ``Sport``.

Three more seams arrived with the send, and each is here for a different reason.

``AccountHoldQuery`` is a **duplicated null object**, and the duplication is the
decision. The matcher declares a port of the same shape against the same absent
provider (``cases``), and this context may not import it — the arrow runs
``matchmaking -> challenges`` and never back. Sharing it would mean the send
reading a safety fact through the matcher, which is the coupling the split
exists to prevent; what is duplicated instead is an empty answer about a
provider that does not exist, which is not what the fence was guarding. The
other three fail-closed gates need no port here at all: ``blocks`` and ``users``
own theirs and ship them, and a profile is read through
``player_profile``'s own repository.

``OriginSearchQuery`` is an **outward demand on the matcher**, signed by an
adapter on the other side of the arrow. The send has to know the window the
search ran on and where each invitee sat in it, and neither is a thing a client
may state: ``docs/adr/0100`` has no window picker anywhere, and a position a
client sent would be true only while the client was honest about where it had
scrolled to.

``ChallengeDirectory`` is the read behind *your own challenges* — the source the
client re-reads when a send is refused on the pair rule, and the one an invitee
opens to find that they were asked.

``LapsingChallengeQuery`` arrived with the sweep and is the odd one out: it
answers with **candidates** rather than with an answer. Nothing in this context
may hold a *has lapsed* column — the whole of ``standing.py`` is that refusal —
so the loop that writes the record cannot be handed the list it wants, only the
list it can safely narrow to. What it narrows on is the one thing the store
knows: a seat's deadline is its seating event plus the answer window, so a
challenge younger than that window holds nothing to record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.challenges.domain.challenge import Challenge
from app.modules.player_profile.domain.availability import Window


@runtime_checkable
class ChallengeRepository(Protocol):
    """Loads and saves ``Challenge`` aggregates, keyed by the challenge's own id.

    Keyed by the id and not by the people, because the id is the identity: the
    same four may be challenged again tomorrow and that is a second challenge,
    not a second version of the first.
    """

    async def load(self, challenge_id: UUID) -> Challenge | None:
        """That challenge, replayed, or nothing.

        ``None`` rather than a raise: *no such challenge* is an ordinary answer
        for an id a client sent, and a caller that wants a 404 is better placed
        to say so than this port is.
        """
        ...

    async def save(self, challenge: Challenge) -> None:
        """Append the aggregate's pending events and publish them.

        Appends and publishes; it does **not** commit, for the reason no
        repository in this codebase does — the transaction boundary is a decision
        about the *command*. A no-op when nothing is pending, which is what lets
        a sweep that found nothing to lapse be saved without growing a stream.
        """
        ...


@runtime_checkable
class OpenChallengeQuery(Protocol):
    """*Are any two of these people already arranging a game?*

    **Read at the moment it is asked, against the clock.** There is no projection
    and no cached *open* flag behind this by decision: the standing is derived
    from the seats and the clock (``standing.py``), so a copy would be wrong for
    the whole gap between a deadline passing and a sweep noticing — and it would
    be the copy that got believed.

    **It does not fail closed, and the difference from ``BlockQuery`` is the
    point.** A block is safety and a gate that cannot be evaluated excludes; this
    rule is *embarrassment* — one person asked one thing at a time — and a
    context that refused every send whenever a read hiccuped would be paying a
    safety price for a courtesy. So there is no translation to a
    ``…Unavailable`` here: a read that cannot complete raises what it raised, and
    the send it was part of fails with it inside its own transaction, writing
    nothing. What must never appear is the other answer — an implementation that
    returned *no pairs* when it could not tell, which reads as *nobody has an
    open challenge* and is the one way this rule stops holding in silence.
    """

    async def open_pairs_among(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> frozenset[frozenset[UUID]]:
        """Every pair of these people who already have an open game between them.

        **One bulk read over the whole court, never one read per pair.** A four
        contains six pairs and the organiser is in only three of them, so a send
        has to know whether two *invitees* are already arranging something —
        which is the same shape ``BlockQuery.blocked_pairs_among`` takes, and for
        the same reason: asking pairwise would be six round trips for a mask that
        is one query.

        It answers in **unordered pairs**, because there is nothing for a caller
        to learn from the direction. Sharing a line-up makes a pair regardless of
        who organised it.
        """
        ...


@runtime_checkable
class AccountHoldQuery(Protocol):
    """Whether an account is under a live hold. **One boolean per player.**

    ``docs/adr/0095``: live, **both directions** — a held organiser is refused at
    the entry point rather than merely withheld from other people's courts — and
    **fail-closed**, because a gate that cannot be evaluated excludes.

    **This is the matcher's port, spelled a second time, and that is deliberate.**
    Its provider is ``cases``, which does not exist; both contexts therefore wire
    an empty answer that is *measured* rather than stubbed — nobody can be held
    because nothing can hold anybody. What a shared declaration would buy is one
    fewer file; what it would cost is this context importing the matcher to ask a
    safety question, which is the one import the boundary forbids. A duplicated
    null object is not the thing that fence was guarding.

    It answers with player ids and nothing else: no case, no opened-at, no
    severity, no count. There is nothing here to weigh, and nothing a refusal
    could carry.
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these players are under a live hold, right now.

        One set read over the whole court rather than a query per seat, which is
        the block mask's shape and for the block mask's reason. The organiser's
        own id goes in beside the invitees' — the gate points both ways, and
        asking in one call is what stops one direction being forgotten.

        Answers only about ids it was asked about.
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class CourtOrigin:
    """What the search a court was built on says about that court.

    Three facts the send may not take from a client:

    ``window`` is **derived at send from the grid the search ran on**
    (``docs/adr/0100``) and stamped onto the challenge. There is no window picker
    anywhere and never will be: a player changes their window by changing their
    grid, which is the same act that changes their matches.

    ``sport`` and ``mode`` are the search's own, so a court cannot claim to be a
    padel evening because a client said so. ``mode`` is ``None`` exactly when the
    surface had none — the deck deals one card at a time and asks nobody to pick
    one.

    ``positions`` is where each invitee sat in that search, which is the origin
    key's other half. It is **read, never sent**, so the telemetry join is true
    by construction (``search-telemetry.md`` §19.2).
    """

    sport: Sport
    mode: SearchMode | None
    window: Window
    positions: Mapping[UUID, int]


@runtime_checkable
class OriginSearchQuery(Protocol):
    """*Did a search of yours show all of these people, and what did it ask?*

    An outward demand on the matcher, signed by an adapter that lives on the
    matcher's side of the arrow. The send needs the search's own reading of
    itself and cannot go and get it: ``challenges`` may not import
    ``matchmaking``.

    **One question and not three.** A caller that asked *which sport*, *which
    window* and *where did each of them sit* separately would be three reads of
    one immutable record, and a court assembled from two of them and refused on
    the third.
    """

    async def court_origin(
        self,
        *,
        search_id: UUID,
        organiser_id: UUID,
        invitee_ids: Collection[UUID],
    ) -> CourtOrigin | None:
        """The origin of a court built on that search, or nothing.

        ``None`` covers four cases and does so on purpose — the search does not
        exist, it is somebody else's, or it never showed one of these people, or
        it showed them only as a near miss. Telling them apart would answer
        questions about strangers one probe at a time, which is the refusal
        ``OriginSearchNotFound`` already makes about the same record.

        The organiser is **not** among ``invitee_ids``: a search never returns
        its own searcher, so asking about them would refuse every send.
        """
        ...


@runtime_checkable
class ChallengeDirectory(Protocol):
    """Every challenge one player is seated in. **Their own, and nobody else's.**

    Keyed on the player rather than on a challenge id, because that is the whole
    question: *what have I been asked, and what have I asked for*. There is no
    method here that takes somebody else's id, which is what stops this read
    becoming a way to ask about a stranger's evening.

    **Ended challenges come back too**, and the standing says which. A challenge
    that lapsed this morning is still a thing that happened to the person it was
    sent to, and a list that quietly dropped it would be the same class of lie as
    a read-back that got shorter.
    """

    async def seating(self, player_id: UUID) -> tuple[Challenge, ...]:
        """Every challenge this player holds a seat in, newest first.

        Newest first is part of the demand rather than a convenience: the client
        renders them in order, and a list whose order depended on how the streams
        happened to be read would reorder itself between two identical requests.
        """
        ...


@runtime_checkable
class LapsingChallengeQuery(Protocol):
    """*Which challenges could be holding a seat whose day has run out?*

    The sweep's read, and **the only port here that answers with candidates.**
    Every other read in this context is right at the instant it is asked; this
    one is deliberately allowed to name a challenge with nothing to record,
    because the fact it would have to filter on — a seat's own deadline — is
    inside a serialized seat code and not a column, and a store that could filter
    on it would be the projection ``standing.py`` exists to refuse.

    Over-naming is therefore free and under-naming is not: a challenge this
    misses keeps a lapse out of the log for ever, while one it names in vain
    costs a stream read and an aggregate that appends nothing.
    """

    async def may_have_lapsed(self, *, now: Instant) -> tuple[UUID, ...]:
        """Every challenge whose seats could include one past its window.

        **The window is what makes this narrow rather than *everything*.** A
        seat's deadline is the seating event that created it plus
        ``ANSWER_WINDOW`` and nothing else, so a challenge opened later than
        ``now`` minus that window holds no seat that could have lapsed — which
        is a claim about the store rather than about any aggregate, and is the
        one narrowing an implementation may make.

        **In one stable order, oldest first**, which is a determinism demand and
        not a safety one: a run commits as a unit, so an interrupted one records
        nothing whichever order it was walking. What the order buys is that two
        sweeps over the same store do the same work in the same sequence — and
        oldest-first is the order the one narrowing that could ever bound this
        read would want, since a seat lapses exactly one window after an event
        the log already orders.
        """
        ...
