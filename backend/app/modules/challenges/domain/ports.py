"""Every seam this context is built on: one to write a challenge, and the reads.

One write and eight reads, then. The first two are the ones it started with: one
to write a challenge, and one to ask whether a game is already being arranged
between two people.

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
contract already assumed rather than a new restriction.

**One read here does take a ``Sport``, and it is not that rule.** The mutual
mint's idempotence key is *has a mutual between these two already minted a game
in this sport* — a question about an ``Interest``, which is keyed
``(from, to, sport)`` and expires — and it is a different rule with a different
scope that happens to be answered off the same log (``docs/adr/0152`` §1). The
pair rule stays cross-sport; what narrowed is the guard that had been borrowing
it.

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

``PlayerNames`` is the one thing this context borrows about a person on a list,
and ``CourtPairingQuery`` is everything it borrows about one on a **detail**. The
split is ``docs/adr/0143``'s: a name is what these people already call each
other and costs a set read, while a card is as-of-now and costs a profile read
and an object-store signature per person — which is why the list carries the
first and only the detail carries the second.

``LapsingChallengeQuery`` arrived with the sweep and is the odd one out: it
answers with **candidates** rather than with an answer. Nothing in this context
may hold a *has lapsed* column — the whole of ``standing.py`` is that refusal —
so the loop that writes the record cannot be handed the list it wants, only the
list it can safely narrow to. What it narrows on is the one thing the store
knows: a seat's deadline is its seating event plus the answer window, so a
challenge younger than that window holds nothing to record.

``ChallengeHistoryQuery`` is the seventh and the only one whose readers are not
this repository's own screens: it is **what this context owes two other
contexts**. The matcher declares ``MatchHistoryQuery`` and an adapter on *its*
side of the arrow signs it (``docs/adr/0098`` as amended — two providers sign one
contract), reading this port and translating. The set read stays the provider's,
exactly as ``UsersAccountStatus`` leaves ``users``' disabled-account read with
``users``; what crosses is this context's own vocabulary, and the adapter is where
the two spellings meet. Its fourth read has a different consumer —
``player_score`` (``docs/adr/0140``), which turns *did you answer inside your day*
into a strand and publishes it, so that fact reaches the engine through a
provider rather than through this port.

**Nothing on it answers *did they play*.** A challenge accepted is not a game
played (map Decision 3), so the half of the matcher's contract that is about
games stays absent until ``matches`` signs — which is why there are three reads
here and four over there.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, invariant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.origins import ChallengeOrigin
from app.modules.challenges.domain.seats import SeatAnswer
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
    """*Are any two of these people already arranging a game?* — and the
    question the mutual mint asks beside it: *what has a mutual between these
    two already minted?*

    **Two questions off one fold, and they are about different things.** The
    first is the ordinary one-open-challenge-per-pair rule and it is a statement
    about **what state two people are in**; the second is the mutual mint's
    idempotence key and it is a statement about **whether an act has already been
    performed** (``docs/adr/0152`` §1). Those have different natural endings, and
    conflating them is what once gave the mint a guard with no release at all —
    a question about a *state* answered ``ON`` for ever, bounding an *act*. The
    mint asks both and both must pass, so it is strictly stricter than a send
    rather than accidentally so.

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
        self,
        player_ids: Collection[UUID],
        *,
        now: Instant,
        except_challenge_id: UUID | None = None,
    ) -> frozenset[frozenset[UUID]]:
        """Every pair of these people who already have an open game between them.

        **One challenge may be excepted, and exactly one** (``docs/adr/0150``
        §3). A fill names the challenge it completes, and asking this question
        over the whole court of *that* challenge would return the court's own
        pairs and refuse the send for the arrangement it is made of. The
        exception is an **input** rather than a condition somebody reconstructs:
        a reader asking why a send into a half-built court is not refused finds
        it in the argument list. Every other open challenge still refuses, so the
        rule is not weakened — it is read correctly.

        **One bulk read over the whole court, never one read per pair.** A four
        contains six pairs and the organiser is in only three of them, so a send
        has to know whether two *invitees* are already arranging something —
        which is the same shape ``BlockQuery.blocked_pairs_among`` takes, and for
        the same reason: asking pairwise would be six round trips for a mask that
        is one query.

        It answers in **unordered pairs**, because there is nothing for a caller
        to learn from the direction. Sharing a line-up makes a pair regardless of
        who organised it.

        **Every caller asks this one**, the mutual mint included. A repeat tap
        landing on two people who are already arranging something would be a
        second challenge between them, and catching that used to be an accident
        of reading a superset (``docs/adr/0152`` §2).
        """
        ...

    async def mutual_born_challenges_that_became_games(
        self,
        one_player: UUID,
        other_player: UUID,
        *,
        sport: Sport,
        now: Instant,
    ) -> tuple[UUID, ...]:
        """Every mutual-born challenge between these two, in this sport, that
        completed into a game — by id, **newest first**.

        **The mutual mint's idempotence key, and nobody else's read.** *Let's
        play* is a tap that costs nothing, ``express_interest`` mints on the
        **mutual** rather than on whether this tap wrote a row — deliberately,
        because a repeat tap is the one occasion the platform ever gets to retry
        a mint a gate refused — and a singles mutual is ``ON`` the instant it
        exists, so the pair rule above lets those two go a moment later. Without
        this question a repeat tap opens a second challenge, a second game and a
        second result window between the same two people.

        **Challenges rather than games, because the answer is only half of one.**
        *Has this mutual finished with what it minted* needs a fact about a
        **game**, which this context does not own; what comes back here is what
        :class:`~app.modules.challenges.domain.settled_game.SettledGameQuery`
        is asked next, and a challenge id is the one name both contexts spell.

        **Mutual-born only.** A challenge somebody *sent* is not something a
        mutual minted, and holding the mint on one would be the pair rule wearing
        a second hat — which is the conflation ``docs/adr/0152`` §1 exists to
        undo. It is answerable off the streams as they stand, because
        ``ChallengeOpenedFromMutualInterest`` is already its own event: no new
        event, no field and no migration.

        **Per sport, and this is where the permanence went.** An ``Interest`` is
        keyed ``(from, to, sport)`` and expires; a padel yes is not a tennis yes
        pressed twice, so a tennis game minted from a mutual has nothing to say
        about a padel one. The one-open-challenge-per-pair rule above stays
        cross-sport and keeps its own justification — these are two rules, and
        only one of them was ever about idempotence.

        **Only what has become a game, and the other half of the hold leans on
        the read above.** ``docs/adr/0152`` §4 puts the mint's hold on a
        mutual-born challenge that is *unfinished*, which is **either** still
        being arranged **or** settled on a game that is not. Only the second half
        is here: a doubles court with a side to fill has minted no game yet, and
        what holds those two is :meth:`open_pairs_among`, which is cross-sport
        and therefore strictly broader than this question needs. **That is the
        coupling to notice** — narrowing the pair rule without moving *still
        being arranged* into this read would open the hold silently, on the one
        path where a refusal has nobody to tell. One that ended without ever
        producing a game holds nobody at all under either question: it is
        finished with, and there is nothing to wait on settling.

        **Pair-shaped, and deliberately not ``…_among``.** The mint has exactly
        two people and always will; the bulk shape next door exists to answer a
        send's six pairs on one court. A method that took a collection and was
        only ever called with two would be inviting somebody to pass three.

        **Ordered, because one of these is named to a player** (``docs/adr/0154``
        §4). The mint answers a repeat tap with the game the mutual already has,
        so it takes the first unfinished row — and a set has nothing to take a
        *first* of. The guard above makes a second row impossible while the first
        is unfinished, so in practice there is one; a restore, a clock moving
        backwards or two taps racing reach two, and what a player is then shown
        may not be set iteration order (``docs/adr/0105``). It was a
        ``frozenset`` while its only reader was a subset test, which is the
        honest shape for that question and the wrong one for this.

        Ties break on the id, so two challenges opened in the same instant order
        the same way on every read rather than on whichever the log yielded
        first.
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


@final
@dataclass(frozen=True, slots=True)
class CourtPerson:
    """Who one person on this court is — **the person half of a card.**

    ``docs/adr/0143`` §5's first block, and every field on it is a fact that
    person changes about themselves. There is **no bio and no free text of any
    kind**: ``PlayerCardSchema`` refuses one *"ever"*, and the refusal is
    stronger here than where it was written, because a searcher chose to look and
    an invitee was put in front of somebody without asking.

    ``photo_id`` and ``photo_url`` are present **exactly together**. An id with
    no link beside it is a photograph nothing can draw, and neither means the
    client draws the generated court poster — which needs nothing from the wire
    (``docs/adr/0134``). Refusing the photograph outright would make the person
    who asked you to play more anonymous than a stranger in a deck, which is the
    wrong way round.

    ``player_score`` is the **published** figure and never a re-derivation of
    one, ``None`` where the platform has watched nothing — which is most people,
    and is why the segment disappears rather than reading ``Score 0``
    (``docs/adr/0140``).
    """

    player_id: UUID
    #: The **name**, whole, and never the nickname (``docs/adr/0171`` §4): a
    #: card is a place a person is *named*, and the handle is drawn on the
    #: record alone.
    name: str
    area_code: str
    level: float
    band: str
    range_low: float
    range_high: float
    photo_id: UUID | None = None
    photo_url: str | None = None
    player_score: int | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.photo_id is None) == (self.photo_url is None),
            f"a photograph with only half an address: {self!r}",
        )


@final
@dataclass(frozen=True, slots=True)
class LevelDeltas:
    """What a **counted** game against this person would do to the reader's Level.

    Never a pair of zeros: ``None`` in for-fun, where a counted result is
    meaningless rather than unavailable, and ``None`` where either of the two
    holds no rating in the sport.
    """

    win_delta: float
    loss_delta: float


@final
@dataclass(frozen=True, slots=True)
class PairingForecast:
    """What this pairing would leave on court, read in the reader's direction."""

    pct: int
    sigma_group: float
    provisional: bool
    assumption: str | None = None


@final
@dataclass(frozen=True, slots=True)
class CourtPairing:
    """What this platform makes of the reader **against** one person on the court.

    ``docs/adr/0143`` §5's second block, and it has a different author from the
    first: the person block is facts about them, and this is a reading of the two
    of them together, computed **in the reader's own direction**. Neither stored
    Fit could stand in for it — ``fit_ab`` is the organiser's reading of the
    invitee under a label that says *for you*, and ``fit_ba`` is scored with the
    searcher's own reliability deliberately set to ``None`` and was built not to
    be published (§9).

    ``terms`` crosses as the same opaque mappings the search record stores. One
    serialiser, two consumers: the store keeps it opaque so a five-year-old row
    still deserialises, and this context validates it into its own closed union
    so the wire type stays exhaustive today.

    **The forecast is the one field here that is not about the two of you.** It
    is the whole court's, computed once and carried on every seat, because a
    forecast is a fact about the **game** rather than about one person — the same
    reading ``would_be_forecast`` takes, which is *what this candidate would
    leave on court* and never a one-a-side figure. It rides in this block because
    that is where ``docs/adr/0143`` §5 puts it.

    ``degraded_terms`` is ``(term, whose gap)`` pairs and **ships even though no
    *Why?* sheet is drawn over them**: without the renormalisation basis a Fit is
    uninterpretable — a 78 built on four terms and a 78 built on seven are
    different readings of one number — and the alternative, printing no Fit,
    throws away the number the screen exists to give.

    ``distance_km`` is whole kilometres and ``None`` when the distance term stood
    down, which is **omitted** on the wire and never a zero: somebody whose
    distance could not be read is not next door.
    """

    fit: float
    terms: tuple[Mapping[str, Any], ...]
    degraded_terms: tuple[tuple[str, str], ...]
    concerns: tuple[str, ...]

    #: What the court as it stands would leave on court, read in the reader's
    #: direction. ``None`` where **no game can be arranged out of what is left**
    #: — a side with nobody on it is not a side, and a court whose whole far side
    #: has declined is one nothing can be forecast about.
    forecast: PairingForecast | None = None
    distance_km: int | None = None
    at_stake: LevelDeltas | None = None


@final
@dataclass(frozen=True, slots=True)
class CourtCard:
    """One person on the court, and the reader's pairing with them."""

    person: CourtPerson
    pairing: CourtPairing


@final
@dataclass(frozen=True, slots=True)
class CourtSeat:
    """One person the reader wants a card for, **and which side of the net.**

    The side travels because a forecast is a claim about a **game**, and a game
    needs two sides. Somebody beside you and somebody across from you produce
    different arrangements of the same four people, and a read that only knew
    *who* would have to price your partner as your opponent — which is what
    *how even would a game against them be* says about a teammate.

    It is ``beside_you`` rather than a ``Side``, because the answer is computed
    for one reader and *which letter* is not a thing this question turns on:
    ``challenges`` seats the organiser on ``A`` and the reader may be anywhere.
    """

    player_id: UUID
    beside_you: bool


class PairingAbsence(str, Enum):
    """Why a court came back with no cards on it. **Two codes, and a third
    answer that is their absence** (``docs/adr/0143`` §6).

    Three answers rather than two, because an outage drawing the *identical*
    absence as an unrated sport is the collapse ADR-0141's Consequences refused
    in as many words. And refusing the whole read with a 503 is worse than
    either: it turns an unrelated matchmaking outage into *you cannot answer your
    challenge*, and answering is not gated.

    **The codes are the contract and the client writes both sentences**
    (``docs/adr/0106``).
    """

    #: There is nothing to compute. The reader holds no rating, has declared no
    #: Play intent, or has committed no player profile in the sport they were
    #: challenged in — and being asked to play a sport you never declared for is
    #: how this feature works rather than a corner of it.
    NOTHING_TO_COMPUTE = "NOTHING_TO_COMPUTE"
    #: It could not be read. Somebody else's outage, and the arrangement still
    #: answers.
    COULD_NOT_BE_READ = "COULD_NOT_BE_READ"


@final
@dataclass(frozen=True, slots=True)
class CourtCards:
    """The cards for one court, **or the reason there are none.**

    Not a bare tuple, because an empty one would have to mean two different
    things at once. ``absent`` names whose gap it is; with no ``absent`` the read
    ran, and a court whose every card failed to assemble is still a court that
    was read.
    """

    cards: tuple[CourtCard, ...] = ()
    absent: PairingAbsence | None = None

    def __post_init__(self) -> None:
        invariant(
            self.absent is None or not self.cards,
            f"cards beside the reason there are none: {self!r}",
        )


@runtime_checkable
class CourtPairingQuery(Protocol):
    """*Who are these people, and what do I make of each of them?*

    An outward demand on the matcher, signed by an adapter that lives on the
    matcher's side of the arrow — ``OriginSearchQuery``'s seam exactly, one
    screen later. The detail read needs a card and a pairing and cannot go and
    get them: ``challenges`` may not import ``matchmaking``.

    **One question and not three**, carrying the origin seam's own sentence. The
    card, the pairing and the photograph's address come back **together**,
    because a caller that asked for each separately would be three reads of one
    computation, and a court assembled from two of them and refused on the third.

    **The photograph is minted where the photo store already is.** ``photo_url``
    is a short-lived signed link minted per response by the adapter, exactly as
    the shortlist, deck and line-up routes mint theirs, so ``challenges`` never
    touches the photo store.

    **Nothing here re-gates.** The four fail-closed gates ran over every pair of
    this court in the send's own transaction and are not run again
    (``docs/adr/0143`` §2): a card that vanished from behind two buttons that
    still work is the disclosure a safety gate may never make, by a slower route.
    What makes that safe is that the pairing is **recomputed rather than
    replayed** — a card that cannot be assembled today has no card, which is
    fail-closed without leaving a trace.
    """

    async def cards_for(
        self,
        *,
        reader_id: UUID,
        sport: Sport,
        mode: SearchMode | None,
        court: Collection[CourtSeat],
    ) -> CourtCards:
        """A card per person on that court, computed **for the reader**.

        ``court`` is everybody the reader wants a card for, with which side of
        the net each of them is on, and it never includes the reader themselves:
        a pairing with yourself is not a question, and asking would refuse the
        whole court.

        ``mode`` is the challenge's own, and ``None`` on one born of a mutual yes
        — where the surface it came from asked nobody to pick one. The
        implementation reads the reader's own declaration in that case, which is
        the deck's rule and not a third vector.

        **Asked once for the whole court and handed back sorted**, on the
        player's id. A set is never the source of an order (``docs/adr/0105``
        §1), stated on the collection rather than on what happens to be
        observable, because what is safe today is what changes silently.

        **A person with no card is absent from the answer and keeps their seat.**
        Their row may be gone from the index, or their profile from the store;
        the arrangement is unchanged and the screen draws the seat without one.
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
class PlayerNames(Protocol):
    """What the people on a court are called. **A name, and the whole of it.**

    **A second spelling of ``games``' port of the same name, and the duplication
    is the decision** — ``origins.py`` and ``Side`` take it for the same reason.
    Two contexts each need *what do I print on this seat*, neither may import the
    other, and the alternative to two spellings is one of them owning the other's
    vocabulary. The adapters meet ``users``' own ``find_namings_of`` and it is
    where the two sentences are kept apart — and where the nickname is left
    behind, because a handle is drawn on a record and said nowhere
    (``docs/adr/0171`` §4).

    ``docs/adr/0141`` §1 fixes what may be borrowed about a person here and
    ``docs/adr/0143`` §7 applies it one surface over: the name they gave, and
    nothing that changes with who is looking. A Level, an area and a photograph
    are what a **card** carries, and a card is drawn on the detail read alone,
    where the arrangement is still being decided.

    **One call for a whole list, never one per seat**, which is the shape every
    set read in this codebase takes: reading a challenge list costs one question
    about the union of everybody on any of its courts.
    """

    async def names_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each of these players' name, as one set read.

        **A player absent from the answer keeps their seat.** The name goes
        ``None`` on the wire and the seat stays, because a seat with no name
        is still a person who was asked — and dropping it would publish a
        three-person doubles court. That is ``games``' rule verbatim, and it is
        the reason ``docs/adr/0143`` §7 could put the field on the seat at all.
        A null there never means *unnamed*: the gate holds an unnamed account
        at the naming step.
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
        seat's deadline is the seating event that created it plus the window that
        stood when it was invited, and nothing else — so a challenge opened later
        than ``now`` minus ``SHORTEST_WINDOW_EVER_STAMPED`` holds no seat that
        could have lapsed, which is a claim about the store rather than about any
        aggregate and is the one narrowing an implementation may make.

        **The shortest window ever stamped, and never the current one.** They are
        the same number only while the window has never moved; the moment it has,
        a cutoff written from today's promise goes looking for yesterday's seats
        after they have already lapsed, and the record this port exists to make
        possible is written late for every seat in flight across the change.

        **In one stable order, oldest first**, which is a determinism demand and
        not a safety one: a run commits as a unit, so an interrupted one records
        nothing whichever order it was walking. What the order buys is that two
        sweeps over the same store do the same work in the same sequence — and
        oldest-first is the order the one narrowing that could ever bound this
        read would want, since a seat lapses exactly one window after an event
        the log already orders.
        """
        ...


class LeftCourtQuery(Protocol):
    """*Which courts has somebody left?* — the hour's candidates
    (``docs/adr/0175`` §3).

    The second port here that answers with candidates, on
    :class:`LapsingChallengeQuery`'s terms: over-naming is free and
    under-naming is not. A court is short of a player only if somebody left
    it — a departure is the one act that reopens a seat on a court that has
    been a game — so a stream with no ``SeatLeft`` on it has nothing for the
    sweep, and one with any is named whether or not it is still short, still
    a game, or a game at all. The sweep loads what it is named and asks the
    fold; this read filters on nothing the fold answers.
    """

    async def courts_somebody_left(self) -> tuple[UUID, ...]:
        """Every challenge whose stream holds a departure, in one stable order,
        oldest first — the determinism demand
        :meth:`LapsingChallengeQuery.may_have_lapsed` states, for its reason.
        No clock: which of them are past their hour is a question about a
        plan, asked one layer up of the game each became.
        """
        ...


#: How many answering counterparts one player's history crosses with, most
#: recent first.
#:
#: **Deliberately the same number as the matcher's ``PAIRWISE_COUNTERPART_BOUND``,
#: spelled a second time** — the same decision ``origins.py`` and ``Side`` take,
#: for the same reason: this context may not import ``matchmaking``, and the
#: alternative to two spellings is the matcher owning the vocabulary of the
#: context built to take work off him. The adapter that signs the matcher's port
#: is where the two meet, and it refuses to import if they ever disagree.
#:
#: The bound is what makes a counterpart cut off by it and one fully decayed by
#: time indistinguishable by construction, so it travels with the ordering rather
#: than as a separate courtesy.
ANSWERED_COUNTERPART_BOUND = 500


@final
@dataclass(frozen=True, slots=True)
class AnswerTally:
    """How many times one answer was given between two people, and when it last was.

    The count and the moment, because the two readers want different halves: a
    signal asks *has this ever happened* and the bound orders on *when it last
    did*. A shape with one moment and no count could feed neither honestly.
    """

    count: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.count >= 1,
            f"a tally of something that never happened: count {self.count}",
        )


@final
@dataclass(frozen=True, slots=True)
class ChallengeCounterpart:
    """One other player, and what they have answered on challenges you were in.

    **Their answers, never yours, and the direction is the whole point.** The
    two signals downstream are *they said yes to you before* and *they turned you
    down before*, and both are prices put on **that** person's card. A pair fact
    that folded in the reader's own answers would dock a candidate for a
    challenge the searcher declined, which is the searcher's judgement charged to
    somebody who never made it.

    **A lapse is not an answer and is not here.** ``SeatAnswer.LAPSED`` is
    refused below rather than merely omitted: silence and a no do the same thing
    to a line-up and are different facts, and a shape that could carry both
    would leave the *answers challenges* denominator and the previous-decline
    signal reading the same erased history.
    """

    player_id: UUID
    answers: Mapping[SeatAnswer, AnswerTally]

    def __post_init__(self) -> None:
        invariant(
            bool(self.answers),
            "a counterpart who has answered nothing is not a counterpart — "
            "absence is spelled by not being in the list at all",
        )
        invariant(
            SeatAnswer.LAPSED not in self.answers,
            f"a lapse tallied as an answer: {self!r}",
        )

    @property
    def last_at(self) -> Instant:
        """The most recent thing they answered, of either kind."""

        return max(tally.last_at for tally in self.answers.values())


@final
@dataclass(frozen=True, slots=True)
class AnsweringRecord:
    """What one player did about the seats they were **asked** to sit in.

    The *answers challenges* strand's whole input (``docs/adr/0140``).
    ``answered`` is invitations that got a yes or a no inside their day;
    ``lapsed`` is invitations whose day ran out with nothing in it. A seat still
    inside its window is in **neither**: the answer is still wanted, and counting
    it either way would state a conclusion the clock has not reached.

    **Only a seat somebody was asked to take is an opportunity.** Three seats in
    this context carry an answer nobody was invited to give — the organiser's,
    accepted from birth because they are the one proposing, and both seats of a
    challenge born from a mutual yes. They have no deadline, which is exactly
    what makes them recognisable: an invitation is a seat with an ``answer_by``,
    and a strand that counted the organiser's own seat would publish a hundred
    per cent for anybody who only ever organises.

    **A lapse is not a decline, and this is the shape that needs them apart.**
    ``SeatAnswer.LAPSED`` and ``SeatAnswer.DECLINED`` do the same thing to a
    line-up and are different facts about a person: turning somebody down inside
    your day is answering, and it is the *only* strand on this platform where a
    no is a good outcome.

    ``last_at`` is the most recent moment one of those opportunities closed — the
    instant an answer was given, or the deadline that passed without one.
    """

    answered: int
    lapsed: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.answered >= 0 and self.lapsed >= 0,
            f"a negative invitation count: {self.answered} answered, "
            f"{self.lapsed} lapsed",
        )
        invariant(
            self.answered + self.lapsed >= 1,
            "an answering record with no closed invitation behind it is an "
            "absence, not a zero — absence is spelled by not being in the answer",
        )


@final
@dataclass(frozen=True, slots=True)
class SharedChallenge:
    """One challenge standing open between this player and one other.

    ``origin`` is **the counterpart's own seat's**, so one doubles send from one
    search at three positions yields three rows carrying three positions — which
    is the join ``search-telemetry.md`` §19.2 needs, and it is lost the moment a
    challenge-level origin is substituted for it.

    A seat nobody was invited into has no origin to carry — the organiser's, and
    both seats of a mutual-born challenge — and those rows say
    ``SentOutsideASearch`` rather than nothing. That is the same claim the writer
    makes: **the invitation came from somewhere else, said explicitly**, and it is
    a claim rather than a missing value on purpose.

    ``opened_at`` is the send moment, or on a mutual-born challenge the moment the
    second yes landed. Both are the challenge's own opening, so there is one
    reading and not two.
    """

    counterpart_id: UUID
    origin: ChallengeOrigin
    opened_at: Instant
    #: Which challenge this row is about. **The only field here that is not
    #: about the pair**, and it is here because one reader needs to take exactly
    #: one row out of this answer: a fill names the challenge it completes, and
    #: the open-challenge gate steps aside for that one and for nothing else
    #: (``docs/adr/0150`` §3). A counterpart and an instant cannot say *which*
    #: challenge, and reconstructing it from ``opened_at`` would be a join on a
    #: timestamp.
    challenge_id: UUID


@final
@dataclass(frozen=True, slots=True)
class HalfBuiltLineUp:
    """A court still being arranged, as the search that would finish it reads it.

    **The whole of what a fill needs and nothing a fill could decide.** The
    sport, the kind of evening and who is already sitting down are facts this
    challenge holds, and a caller that could send any of them would be offering a
    second place for one of them to be true (``docs/adr/0150`` §2).

    ``mode`` is ``None`` exactly where the challenge has none — deck-born, and
    every mutual-born court — and the filler's own declared Play intent resolves
    one on the deck's own rule. **There is no window here and there never will
    be**: a window is stamped by ``ChallengeSent`` and by nothing else, so a
    mutual-born challenge stays window-less for its whole life (§5).

    ``seated_ids`` is everybody live on the court **other than the member
    asking**, in the court's own order, and they are what a fill locks. It
    excludes the member for the reason a search never returns its own searcher.
    **It may be empty**: a court that has been a game and lost everybody but the
    filler is still a court with seats to fill (``docs/adr/0162`` §6).

    ``answered_and_gone`` is everybody who answered this challenge and holds no
    seat on it any more — the declined and the lapsed. They are released back
    into the deck the instant they leave (``open_challenges_with``), so without
    this they would be candidates for the very fill they turned down and
    ``NobodyIsAskedTwice`` would refuse the send *after* the player chose them
    (§4). It never contains anybody in ``seated_ids``: somebody who accepted has
    answered and is still in.
    """

    challenge_id: UUID
    sport: Sport
    mode: SearchMode | None
    seated_ids: tuple[UUID, ...]
    answered_and_gone: frozenset[UUID]

    def __post_init__(self) -> None:
        invariant(
            not (set(self.seated_ids) & self.answered_and_gone),
            f"somebody both seated and gone from {self.challenge_id}: "
            f"{sorted(set(self.seated_ids) & self.answered_and_gone)}",
        )
        # **Empty is a court the filler is alone on, and it is a real court**
        # (``docs/adr/0162`` §6). Rarer since ``docs/adr/0165`` §3 — the
        # departure that leaves one player on a game now calls it off — but
        # still reached: a court whose others left while a newcomer was still
        # deciding, whose newcomer then said no, leaves the filler alone with
        # a game to fill. It used to be refused here, when
        # ``LINE_UP_INCOMPLETE`` needed a second person; a court that has been
        # a game does not.


@runtime_checkable
class ChallengeHistoryQuery(Protocol):
    """Who answered, who is open, who is full, who answers at all — and one court.

    **Five reads and not one bag.** They are separate because their consumers
    are: two Liveness signals, one gate, a third signal that is a count over
    everybody rather than a fact about a pair, one Player Score strand since
    ``docs/adr/0140``, and — since ``docs/adr/0150`` — the fill that completes one
    named challenge. Bundling them would make the slowest read's cost and the
    strictest read's failure everybody's, which is the same argument
    ``MatchHistoryQuery`` makes about carrying them as separate methods on one
    port.

    **The fifth read fails differently from the other four, and that is decided
    where the matcher declares it rather than here.** The four are history and a
    search survives without them; a fill that cannot read the court it is
    completing has nothing to complete, so the matcher declares it as its own
    port with its own posture (``HalfBuiltCourtQuery``) rather than folding it
    into the soft one.

    **Three of the four go to the matcher and the fourth does not**, which is why
    the sentence above no longer says *what this context owes the matcher*.
    ``answering_for`` is read by ``player_score``, which publishes a strand the
    matcher then reads from its own provider — so the same fact reaches the
    engine, one context further along, already turned into a verdict about a
    person.

    **Three of the four take the clock and one does not, and nothing here is
    projected.** An answer is a thing that happened and reads the same at every
    instant, so ``answered_counterparts`` has no clock to be given.
    ``answering_for`` does, and the difference is not a contradiction: what it
    needs the clock for is the *other* half of its answer — whether an
    unanswered invitation's day has run out yet. *Open* is ``AWAITING_ANSWERS ∪ ON ∪
    LINE_UP_INCOMPLETE`` computed from the seats and ``now`` (``standing.py``), so
    a seat past its window has left both the open read and the count whether or
    not the sweep has been past — **the sweep exists for the record, not for
    correctness**. A projection storing the standing would be the status column
    ``standing.py`` refuses, relocated into a read model, and it would be the copy
    that got believed.
    """

    async def answered_counterparts(
        self, player_id: UUID
    ) -> tuple[ChallengeCounterpart, ...]:
        """Everybody who has answered a challenge this player was on the court for.

        **On the court when they answered**, and not merely on it now. A declined
        seat can be re-offered to somebody else, and the arrangement that results
        has forgotten whoever left it — so a read that asked today's court would
        erase a real refusal the day the organiser refilled the seat, and would
        hand the replacement a history they were never part of.

        At most ``ANSWERED_COUNTERPART_BOUND``, **ordered on ``last_at``, newest
        first** — the order is part of the demand rather than a convenience,
        because it is what the bound means.

        **A challenge born of a mutual yes tallies nothing.** Nobody answered
        anything: both seats are accepted from birth and no answer event exists,
        so the pair produce no row here at all. What two yeses that met are worth
        is already priced by the interest lift, and counting it again would be the
        double-count the whole shape is careful to avoid.

        **A lapse tallies nowhere.** A pair whose only history is one lapsed seat
        has no row here.
        """
        ...

    async def open_challenges_with(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[SharedChallenge, ...]:
        """Everybody this player currently has an open game with. **One row each.**

        A counterpart is **everybody occupying a seat other than your own** on a
        challenge still being *arranged* — co-invitees included, because if we
        are both in a line-up we have an open game together and that is the same
        fact from the other side. Somebody whose seat has declined or lapsed is
        out of the game and out of this answer immediately, because their seat is
        open again; otherwise a decline would cost them a candidate they never
        turned down.

        **And a completed line-up is out of it too** (``docs/adr/0142`` §1). A
        challenge every seat accepted has not *ended* — ``invite`` does not call
        it over, and the client still prints ``ON``; what refuses a send into it
        is the full court, not an ending. But the arranging is finished and a
        game exists, so it holds nobody here. This is **not** the complement of
        ``ENDED``, and reading it as one is the bug this sentence replaced.

        **Unbounded**, because it is small by construction: a player has a handful
        of live challenges rather than a history of them, and one open challenge
        per pair is a rule this context enforces on the way in.

        **Somebody who *lapsed* is out of this answer, and that is them being
        free rather than the opposite** ([#393](https://github.com/Raketa02/Raketa/issues/393)).
        Their seat reopened, so they leave this read — and leaving this read *is*
        the pair releasing, because this read is the pair rule. Every search
        reaches them from that moment, in any sport.

        **What they are still out of is one pool, and it is not this one.** The
        challenge they never answered still stands, and the fill that would
        replace them excludes everybody who has answered it — ``already_asked_at``
        feeding ``NobodyIsAskedTwice``, *per aggregate*. So they cannot be put
        back on **that** court for as long as it stands, and asking them again is
        a new challenge.

        ``docs/adr/0150`` §4 drew the wider conclusion — *unreachable in every
        sport* — from that narrower fact, and its amendment retracts it. This
        paragraph stated the premise correctly and then contradicted it, which is
        how the claim survived being written next to the mechanism that refutes
        it.
        """
        ...

    async def seats_awaiting_answers(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, int]:
        """How many seats are waiting on each of these players' answers.

        **Invited, unanswered, inside their own window, across every sport, on
        a challenge that still stands.** Not challenges they organised — an
        organiser with eight sends out is over-committed but is not slow to
        answer, and docking them would sink the exact behaviour the product
        exists to produce — not seats they have already accepted, which are
        waiting on nobody, and not a seat on a challenge its organiser removed
        while that seat's day was still running (``docs/adr/0165`` §4), which
        is waiting on nobody either: the seat reads as awaiting and the court
        is over, and the court decides.

        Across every sport because the pair rule is, and because the ruleset's own
        falsifier for this signal is *answer rate by open-challenge bucket*: only
        unanswered seats are the denominator of that.

        **Every player asked about gets a count**, and a zero here is measured:
        the seats were counted and there were none.
        """
        ...

    async def answering_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, AnsweringRecord]:
        """What each of these people did about the seats they were **asked** to take.

        ``player_score``'s input for the *answers challenges* strand
        (``docs/adr/0140``), and the fourth read here because its consumer is a
        fourth one. It is deliberately not derived from ``answered_counterparts``:
        that read is about **other people's** answers to challenges you were in,
        because the two signals it feeds are prices on somebody else's card, and
        a per-player rate folded out of it would be counting the same answer once
        per person who happened to be on the court.

        **A player nobody ever invited is absent from the answer**, which is the
        opposite rule to ``seats_awaiting_answers`` above and for the reason
        ``docs/adr/0098`` names: a count of live seats is measured and there were
        none, where a ``0/0`` answer rate would say somebody was asked and stayed
        silent. The two rules sit on one port so that the difference is read
        rather than rediscovered.

        **It walks the stream rather than folding the aggregate**, for the reason
        ``answered_counterparts`` does: a declined seat can be re-offered, and
        today's court has forgotten whoever left it. A read that asked today's
        seats would lose every answer given by somebody who has since been
        replaced — and the replacement's own invitation would inherit a deadline
        that was never theirs.
        """
        ...

    async def half_built_line_up(
        self, *, challenge_id: UUID, member_id: UUID, now: Instant
    ) -> HalfBuiltLineUp | None:
        """The court this member is on and could still grow, or nothing.

        **The fifth read, and the first that is asked about one challenge rather
        than about one player.** A fill names the challenge it completes
        (``docs/adr/0150`` §2), so the sport, the kind of evening and the people
        already sitting down are read off *that* aggregate — and an id is the
        only thing a caller has to hand over for it.

        **``None`` covers three cases and does so on purpose**: no such
        challenge, this member holds no live seat on it, and a challenge nobody
        is arranging any more. Telling them apart would answer *is this challenge
        id real* about a stranger's evening, which is the refusal
        ``NoChallengeOfYoursHasThatId`` already makes one surface over.

        **Any live member, and never only the organiser** (§1). Growing a court
        and ending one are different acts with different permissions: removing
        a court is the organiser's while nobody has joined and nobody's once
        somebody has (``docs/adr/0165`` §4), and the fill is everybody's who is
        still on the court.
        A mutual-born doubles challenge decides it — it is ``LINE_UP_INCOMPLETE``
        from birth with an "organiser" who is only whoever's yes arrived second,
        and making that arbitrary tiebreak the only person who can finish the four
        would leave the other looking at a court they can neither complete nor
        leave.

        **Still *being arranged*, which is the pair rule's own set** and not a
        narrower one of this read's invention (``standing.py``'s ``ARRANGING``).
        A court every seat accepted has become a game and holds no open seat; a
        court that ended has ended. What is left is exactly where a seat can still
        be grown, and ``Challenge.invite``'s own refusals stay the authority on
        the rest.
        """
        ...
