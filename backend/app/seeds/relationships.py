"""The eleven accounts a distribution cannot assert, each named for a pair.

**A cohort of strangers gives a ranked list and nothing else.** Five of the ten
``LivenessSignal`` codes are facts about *two people* — *they said yes to you*,
*they turned your court down*, *their inbox is full* — and no population,
however well shaped, can exhibit one: a rate over sixty members produces edges
nobody named, and a rate cannot assert that **exactly one** instant-match pair
exists. So the pairwise five move here, and ``cohort.py`` keeps the six that are
properties of one person.

**Every account is named for the relationship and never for its own state**,
which is where this file departs from ``catalog.py``'s rule and why it is a file
of its own. ``said-yes-to-you`` is read off a pool card constantly and signed in
as once, so the second person is the *protagonist*, who is named in each
``description`` rather than in the slug. Decision 11 makes *you* unambiguous:
``the-populated-player`` is the only protagonist carrying relationships, and a
second one acquiring them is the day this rule is revisited, in the open.

**Every edge costs a real search or deal run as the sender.** ``Interest`` and
``Pass`` have no non-search constructor — a yes cites the search that showed the
person, and ``resolve_origin`` refuses one that did not — and a send cites the
search its court was built on. That cost was accepted and **turned into the
check**: the origin must resolve or the seed fails, which is stronger than the
edge existing, because it proves the protagonist was genuinely findable through
gender, level and radius before any lift is claimed. It also fixes where these
accounts sit — at the protagonist's own coordinates, on the protagonist's own
week, in the protagonist's own band — rather than leaving placement to taste.

**One code cannot be reached at all, and it is narrowed out by name.**
``SeatAccepted`` makes a seat ``ACCEPTED`` and nothing ends a game without
``matches``, so a pair with an accepted seat is permanently ``OPEN_CHALLENGE``-
gated and ``PREVIOUS_ACCEPT`` is unreachable on every surface. It is listed in
``screens.py``'s ``CANNOT_BE_DRAWN`` with that reason, and contracted by a demand
in ``tests/demands/`` rather than by a fixture — the failure this avoids is the
opposite one: a reason line missing from every card, and a developer hunting for
a bug in the ruleset.

**Outgoing singles, inbound doubles**, and the asymmetry is doing work. The one
outgoing challenge is on **tennis**, which buys the one thing a padel edge
cannot: *one open challenge per pair, across sports* becomes observable — that
person is gated out of your **padel** pool by a **tennis** challenge, which is
the rule's entire content and reads as a bug to anybody who has not met it. The
inbound one is doubles, because a doubles challenge makes every co-invitee a
counterpart, and a seat with a side, a window counting down and a line-up that is
yours is the court screen's whole subject. The two co-invitees are **named
accounts rather than anonymous cohort members**, which is what makes two people
disappearing *declared* instead of *discovered*, and they differ from each other
by seat state so the court draws a filled seat and an unanswered one side by
side.

**The eleventh is a departure from the settled table, and it is written down
rather than quietly taken.** [#225] pointed ``PREVIOUS_DECLINE`` at
*``they-challenged-you``'s declined seat* and gave it no account of its own. It
cannot live there: that account's own claim is a **live inbound seat**, so the
pair is ``OPEN_CHALLENGE``-gated and the code could never be drawn on any card —
the same trap the ticket names about absence, one layer along. A padel doubles
court seats four, and organiser plus protagonist plus the two named co-invitees
is four, so there is no fifth seat to decline from either; and refilling a
declined seat is ``Challenge.invite``, which has **no use case** to go through.
So the decline is its own account and its own court: the protagonist sends a
half-built padel court to ``they-turned-down-your-court``, who says no, which
ends the challenge — *a declined seat reopens and that person returns to the deck
immediately* — and leaves the pair with a recorded refusal and no gate.

**What a claim is.** A relationship claim is a code on a card or a named absence,
read through the protagonist's **real read path** — never a ledger lookup. A
check computed from what this file wrote could only ever pass. The claims live in
``app/seeds/screens.py`` with every other assertion; what is here is the
declaration, which is this layer's half of the same asymmetry ``cohort.py`` and
``screens.py`` are split along.

**And an absence needs one refinement a naive fixture does not have.** An account
gated for an *accidental* reason is absent, and an absence claim passes. So every
account is rated in every sport its claim touches, through the questionnaire like
everybody else, and the absence claims assert the **gate histogram** rather than
the absence: ``excluded_by_gate[OPEN_CHALLENGE] >= 4``,
``excluded_by_gate[BLOCKED] >= 2``. It is a first-in-declaration-order histogram,
so a count there names the reason exactly, and it cannot be non-zero unless a
rated, in-range, gender-satisfied candidate was excluded for that reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence, final

from app.kernel import Sport, exhaustive
from app.modules.challenges.domain.seats import SeatAnswer
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.seeds.catalog import (
    BAND_ESTABLISHED,
    MIDDLING,
    PROTAGONIST_RADIUS_KM,
    PROTAGONIST_TAGS,
    PROTAGONIST_WEEK,
    SETTLED_DAYS_AGO,
    THE_POPULATED_PLAYER,
    ACCOUNTS,
    RatedRun,
    RatingClaim,
    SeedAccount,
    SeedProfile,
    refuse_an_impossible_account,
    refuse_two_accounts_at_one_name,
)
from app.seeds.cohort import COHORT, Cohort, CohortMember

#: The one account every relationship here is a relationship **with**. Named
#: once, so *you* is a fact this module states rather than a convention its
#: eleven slugs imply.
PROTAGONIST: Final = THE_POPULATED_PLAYER

#: The band every relationship account is rated into, and where in it. **The
#: protagonist's own** — a relationship account that fell outside ``LEVEL_TOL``
#: would be gated out of her pool for a reason having nothing to do with its
#: edge, which is exactly the accidental exclusion this layer is built to refuse.
#: A tightened tolerance that pushes one of them out then fails the seed **by
#: that account's name**, which is a better falsifier than any tolerance
#: arithmetic written into the fixture.
THE_PROTAGONISTS_BAND: Final = RatingClaim(
    band=BAND_ESTABLISHED, position=(0.25, 0.75)
)


# ---------------------------------------------------------------------------
# The edges — what is written, as a closed union
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class TheySaidYes:
    """They ran their own pool search and said *Let's play* to the protagonist.

    Inbound, so the yes is **live and unanswered**: saying yes back opens a
    challenge from mutual interest, and the seed has no event to cancel one with.
    """

    sport: Sport


@final
@dataclass(frozen=True, slots=True)
class YouSaidYes:
    """The protagonist said *Let's play* to them, off her own pool search."""

    sport: Sport


@final
@dataclass(frozen=True, slots=True)
class YouChallengedThem:
    """The protagonist sent them a singles court, built on her own search."""

    sport: Sport


@final
@dataclass(frozen=True, slots=True)
class TheyChallengedYou:
    """They organised a doubles court the protagonist holds a seat on.

    ``co_invitees`` are the other two seats, by slug, and each of them declares
    its own answer through :class:`OnTheirCourt` — the send is one act and the
    answers are three separate ones, which is what lets a filled seat and an
    unanswered one sit on the same court.
    """

    sport: Sport
    co_invitees: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class OnTheirCourt:
    """A co-invitee's seat on the court :class:`TheyChallengedYou` sent.

    ``answer`` is ``None`` for a seat nobody has answered, which is *awaiting*
    and not a fourth :class:`SeatAnswer` — the absence of an answer is the state,
    exactly as the aggregate spells it.
    """

    answer: SeatAnswer | None


@final
@dataclass(frozen=True, slots=True)
class TheyTurnedYouDown:
    """They declined a seat on a court the protagonist organised.

    Half a game — one invitee on a four — so the decline leaves nobody but the
    organiser in it and the challenge **ends**. That is what makes this the one
    pairwise refusal a card can carry: the pair is released the moment the seat
    is declined, with or without a sweep having run.
    """

    sport: Sport


@final
@dataclass(frozen=True, slots=True)
class YouBlockedThem:
    """The protagonist blocked them. Trivially absent, and it proves little."""


@final
@dataclass(frozen=True, slots=True)
class TheyBlockedYou:
    """They blocked the protagonist. **The only symmetric-effect fixture.**

    Unobservable from her side by construction — indistinguishable from somebody
    out of range — so it is checkable only by reading a screen as *them*, which
    is the concrete form of why these are accounts and not rows in an edge table.
    """


@final
@dataclass(frozen=True, slots=True)
class YouPassedThem:
    """The protagonist passed on them, off a real deal.

    A pass is write-only, returned by no route, and *show them again* is struck —
    so deck suppression is entirely unobservable, and the only way to see it work
    is to know in advance who should not deal.
    """

    sport: Sport


#: What one relationship writes. A closed union, so the writer's ``match`` over
#: it stops typechecking the day a twelfth edge exists — an unhandled edge would
#: otherwise be an account seeded into no relationship at all.
Edge = (
    TheySaidYes
    | YouSaidYes
    | YouChallengedThem
    | TheyChallengedYou
    | OnTheirCourt
    | TheyTurnedYouDown
    | YouBlockedThem
    | TheyBlockedYou
    | YouPassedThem
)


def sport_of(edge: Edge) -> Sport | None:
    """Which sport this edge is written on, or ``None`` where it has none.

    A ``match`` over the closed union rather than a ``getattr``, because the
    union's whole promise is that a twelfth edge stops typechecking: an
    attribute probe would answer ``None`` for it and the new edge would be
    seeded onto no sport at all, silently. A block genuinely has none — it is
    symmetric and reaches every sport at once.
    """

    match edge:
        case TheySaidYes() | YouSaidYes():
            return edge.sport
        case YouChallengedThem() | TheyChallengedYou():
            return edge.sport
        case TheyTurnedYouDown() | YouPassedThem():
            return edge.sport
        case OnTheirCourt():
            # The seat's sport is the court's, and the court is the organiser's
            # to name. Answering one here would be a second copy of it.
            return None
        case YouBlockedThem() | TheyBlockedYou():
            return None
        case _:
            exhaustive(edge)


@final
@dataclass(frozen=True, slots=True)
class Relationship:
    """One account, the edge it carries, and what that edge makes true.

    ``claim`` is prose and the check is not: what is written here is printed on
    the seed's report so a developer reads the promise beside the address, and
    the promise itself is asserted in ``app/seeds/screens.py`` through the
    protagonist's own read paths.
    """

    account: SeedAccount
    edge: Edge
    claim: str


def _account(slug: str, description: str, *, sports: Sequence[Sport]) -> SeedAccount:
    """One relationship account: rated where its claim reaches, and nowhere else.

    **Every sport the claim touches**, because an account with no padel rating is
    excluded by ``NOT_RATED`` — the third gate, ahead of ``OPEN_CHALLENGE`` — and
    an absence fixture that fires on the wrong gate proves nothing.

    Everything else is the protagonist's own: her coordinates, her week, her
    tags, her radius and a settled commit date. A relationship account is a
    control for one edge, so every axis that is not the edge is held equal — and
    ``GenderPreference.ANY`` on both sides is what keeps ADR-0096's mutual gate
    out of an absence claim it has no business in.
    """

    return SeedAccount(
        slug=slug,
        description=description,
        scenarios=tuple(
            RatedRun(sport=sport, answers=MIDDLING, claim=THE_PROTAGONISTS_BAND)
            for sport in sports
        ),
        profile=SeedProfile(
            availability=PROTAGONIST_WEEK,
            social_tag_ids=PROTAGONIST_TAGS,
            search_radius_km=PROTAGONIST_RADIUS_KM,
            gender=Gender.WOMAN,
            gender_preference=GenderPreference.ANY,
            proposals_opt_in=True,
            committed_days_ago=SETTLED_DAYS_AGO,
            intents=tuple(
                (sport, PlayIntent.COMPETITIVE) for sport in sports
            ),
        ),
    )


# ---------------------------------------------------------------------------
# The eleven
# ---------------------------------------------------------------------------

SAID_YES_TO_YOU: Final = Relationship(
    account=_account(
        "said-yes-to-you",
        "Somebody who has already said *Let's play* to the-populated-player and "
        "is waiting on an answer. The one lift that admits a candidate below "
        "QUALITY_FLOOR, and the only printable signal no generator can write.",
        sports=(Sport.PADEL,),
    ),
    edge=TheySaidYes(sport=Sport.PADEL),
    claim="her padel pool carries INTEREST_RECEIVED on this row",
)

YOUR_YES_MAKES_IT_MUTUAL: Final = Relationship(
    account=_account(
        "your-yes-makes-it-mutual",
        "A second live yes to the-populated-player, reachable by the other "
        "code path: the deck's *wants to play you* card. Saying yes back opens a "
        "game inline — the only instant match this database can produce, and "
        "there is exactly one.",
        sports=(Sport.PADEL,),
    ),
    edge=TheySaidYes(sport=Sport.PADEL),
    claim=(
        "a two-state claim: either a live inbound yes on the deck, or the "
        "challenge it became, with this person scored into none of her surfaces"
    ),
)

YOU_SAID_YES_TO_THEM: Final = Relationship(
    account=_account(
        "you-said-yes-to-them",
        "Somebody the-populated-player has said *Let's play* to. The outgoing "
        "half of the ledger, which is what the outstanding-per-sport count and "
        "the cap are read against.",
        sports=(Sport.PADEL,),
    ),
    edge=YouSaidYes(sport=Sport.PADEL),
    claim="her outstanding padel count is non-zero and a repeat tap creates nothing",
)

YOU_CHALLENGED_THEM: Final = Relationship(
    account=_account(
        "you-challenged-them",
        "Somebody the-populated-player has an open **tennis** singles challenge "
        "with, and who is therefore missing from her **padel** pool. The "
        "one-open-challenge-per-pair-across-sports rule, which reads as a bug to "
        "anybody who has not met it.",
        sports=(Sport.PADEL, Sport.TENNIS),
    ),
    edge=YouChallengedThem(sport=Sport.TENNIS),
    claim=(
        "absent from her **padel** pool on the OPEN_CHALLENGE gate, "
        "on a tennis challenge"
    ),
)

THEY_CHALLENGED_YOU: Final = Relationship(
    account=_account(
        "they-challenged-you",
        "The organiser of a padel doubles court the-populated-player holds a "
        "seat on. The richest thing `challenges` holds: a seat with a side, a "
        "window counting down, and a line-up that is hers.",
        sports=(Sport.PADEL,),
    ),
    edge=TheyChallengedYou(
        sport=Sport.PADEL,
        co_invitees=("in-your-line-up-and-accepted", "in-your-line-up-still-deciding"),
    ),
    claim="a seat that is hers to answer, with answer_by still running",
)

IN_YOUR_LINE_UP_AND_ACCEPTED: Final = Relationship(
    account=_account(
        "in-your-line-up-and-accepted",
        "A co-invitee on the same court as the-populated-player who has said "
        "yes. A filled seat, and a person silently gone from every one of her "
        "surfaces, because sharing a line-up makes a pair.",
        sports=(Sport.PADEL,),
    ),
    edge=OnTheirCourt(answer=SeatAnswer.ACCEPTED),
    claim="a filled seat on her court, and scored into none of her surfaces",
)

IN_YOUR_LINE_UP_STILL_DECIDING: Final = Relationship(
    account=_account(
        "in-your-line-up-still-deciding",
        "The other co-invitee on the-populated-player's court, who has "
        "answered nothing. An unanswered seat beside a filled one, so the court "
        "screen draws both.",
        sports=(Sport.PADEL,),
    ),
    edge=OnTheirCourt(answer=None),
    claim="an unanswered seat on her court, and scored into none of her surfaces",
)

THEY_TURNED_DOWN_YOUR_COURT: Final = Relationship(
    account=_account(
        "they-turned-down-your-court",
        "Somebody who declined a seat on a court the-populated-player "
        "organised. The challenge ended with the seat, so they are back in her "
        "pool the same instant — carrying the refusal, which is the whole point.",
        sports=(Sport.PADEL,),
    ),
    edge=TheyTurnedYouDown(sport=Sport.PADEL),
    claim="in her padel pool, and the row's PREVIOUS_DECLINE input is true",
)

YOU_BLOCKED_THEM: Final = Relationship(
    account=_account(
        "you-blocked-them",
        "Somebody the-populated-player has blocked. Absent from every surface "
        "she has, silently, with no explanation to either side.",
        sports=(Sport.PADEL,),
    ),
    edge=YouBlockedThem(),
    claim="scored into none of her surfaces, on the BLOCKED gate",
)

THEY_BLOCKED_YOU: Final = Relationship(
    account=_account(
        "they-blocked-you",
        "Somebody who has blocked the-populated-player. The same absence from "
        "her side and a different fact — the only fixture for a symmetric effect "
        "read off a directed record, and it is checkable only as them.",
        sports=(Sport.PADEL,),
    ),
    edge=TheyBlockedYou(),
    claim="scored into none of her surfaces, and she into none of theirs",
)

YOU_PASSED_THEM: Final = Relationship(
    account=_account(
        "you-passed-them",
        "Somebody the-populated-player passed on. Gone from her deck and a full "
        "candidate in her pool — a two-surface asymmetry that reads as a bug to "
        "anybody meeting it cold, and the cheapest fixture in this file.",
        sports=(Sport.PADEL,),
    ),
    edge=YouPassedThem(sport=Sport.PADEL),
    claim="absent from her deck by a live suppression, and present in her pool",
)

#: The eleven, **in the order they are written**, and the order is load-bearing
#: twice: a co-invitee cannot answer a seat before the court that holds it has
#: been sent, and the pass is last because the deal that earns its origin key is
#: also the deal the deck's own claims are read off — a second deal would find
#: everybody it dealt already spent.
RELATIONSHIPS: Final[tuple[Relationship, ...]] = (
    SAID_YES_TO_YOU,
    YOUR_YES_MAKES_IT_MUTUAL,
    YOU_SAID_YES_TO_THEM,
    YOU_CHALLENGED_THEM,
    THEY_CHALLENGED_YOU,
    IN_YOUR_LINE_UP_AND_ACCEPTED,
    IN_YOUR_LINE_UP_STILL_DECIDING,
    THEY_TURNED_DOWN_YOUR_COURT,
    YOU_BLOCKED_THEM,
    THEY_BLOCKED_YOU,
    YOU_PASSED_THEM,
)

#: The accounts alone, for the registration walk. Written from the same tuple so
#: an account cannot be seeded without its edge or an edge declared without an
#: account.
RELATIONSHIP_ACCOUNTS: Final[tuple[SeedAccount, ...]] = tuple(
    relationship.account for relationship in RELATIONSHIPS
)

#: Which accounts are gated out of the protagonist's surfaces, and by which
#: gate. **The claim is the histogram**, so the codes are named here and the
#: counts are read off the search record the run already produced.
ABSENT_ON_THE_OPEN_CHALLENGE_GATE: Final = (
    YOU_CHALLENGED_THEM,
    THEY_CHALLENGED_YOU,
    IN_YOUR_LINE_UP_AND_ACCEPTED,
    IN_YOUR_LINE_UP_STILL_DECIDING,
)
ABSENT_ON_THE_BLOCKED_GATE: Final = (YOU_BLOCKED_THEM, THEY_BLOCKED_YOU)


# ---------------------------------------------------------------------------
# The inboxes — CHALLENGE_LOAD's three rungs, borne by the cohort
# ---------------------------------------------------------------------------

#: How many cohort members carry an inbox, one per rung of the ruleset's own
#: ``challenge_load_rungs``. **A property of that person and not of the pair**:
#: a challenge *from the protagonist* gates them out of her surfaces entirely,
#: so a loaded candidate has to be loaded by other people — which is why the
#: depths are borne by the cohort and the sends are made by cohort members.
#:
#: The depths themselves are **read off the live ruleset**, never written here:
#: each rung names its own printed code, so a threshold that moves re-points
#: nothing and this fixture follows it rather than pinning it.
LOADED_INBOXES: Final = 3

#: Who carries them. The nearest ring's club players, because the loaded rows
#: have to survive the protagonist's own level and gender gates before a dock
#: can be read off them — a member gated out is a member whose inbox nothing
#: ever prints. Taken in handle order so the choice is a rule rather than a
#: taste, and skipped where the mutual gender gate would remove them from her.
#:
#: **A departure from [#225], stated rather than smuggled.** That decision filed
#: the load as *every n-th member is invited to k unanswered seats by other
#: members*, in the cohort's own positional idiom. It cannot be one here: an
#: inbox of eight needs **eight distinct organisers**, because one open challenge
#: per pair makes an organiser worth exactly one seat — so the rule has to be
#: about who can *see* whom, and only a real search answers that. An n-th-member
#: rule would name eight organisers and discover on the day that one of them was
#: level-gated, blaming the wrong member. What survives of the original is its
#: point: the load is borne by the **cohort** and never by a relationship
#: account, because a challenge from the protagonist gates that person out of her
#: surfaces entirely and a pair could then carry no code at all.
LOADED_RING: Final = "a"
LOADED_ARCHETYPE: Final = "club-player"


def members_who_carry_an_inbox(cohort: Cohort = COHORT) -> tuple[CohortMember, ...]:
    """The ``LOADED_INBOXES`` members whose unanswered seats a card prints.

    One per rung, deepest last, so a reader of the report sees ``SOME``, ``BUSY``
    and ``FULL`` in the order the ruleset declares them.
    """

    eligible = _eligible(cohort)
    if len(eligible) < LOADED_INBOXES:
        raise RuntimeError(
            f"{len(eligible)} cohort member(s) can carry an inbox and "
            f"CHALLENGE_LOAD needs {LOADED_INBOXES}, one per rung. The rule is "
            f"`LOADED_RING`/`LOADED_ARCHETYPE` in `app/seeds/relationships.py`."
        )
    return eligible[:LOADED_INBOXES]


def members_who_might_organise(cohort: Cohort = COHORT) -> tuple[CohortMember, ...]:
    """Everybody who might be able to fill one of those inboxes, in handle order.

    **A candidate list and not an assignment, and the difference is the whole
    design.** One open challenge per pair means a member can put at most one seat
    in another member's inbox, so the deepest rung needs as many organisers as it
    has seats — and whether a given member can send at all is a question about
    *their* pool, which only a real search answers. So the writer walks this list,
    runs each member's own padel search, and hands the deepest rung to whichever
    inbox the most organisers turned out to be able to reach. A fixture that named
    eight organisers instead would discover on the day that one of them cannot see
    anybody, and it would name the wrong member as the reason.

    Handle order puts the nearest ring first, which is where an organiser is
    likeliest to see anybody at all — every member of one ring shares one
    coordinate, so they see each other at no distance whatever.
    """

    loaded = {member.handle for member in members_who_carry_an_inbox(cohort)}
    return tuple(
        member
        for member in sorted(cohort.members, key=lambda one: one.handle)
        if member.handle not in loaded
    )


def _eligible(cohort: Cohort) -> tuple[CohortMember, ...]:
    """The nearest ring's club players whose preference admits the protagonist."""

    return tuple(
        member
        for member in cohort.members
        if member.ring == LOADED_RING
        and member.archetype == LOADED_ARCHETYPE
        and member.gender_preference == GenderPreference.ANY.value
    )


# ---------------------------------------------------------------------------
# Refusals, at import
# ---------------------------------------------------------------------------


def _refuse_an_impossible_layer() -> None:
    """Fail at import rather than part-way through a run.

    Everything here is a property the *declarations* have to hold before a single
    edge is written, and each is a way this layer could stop being what it says
    it is while still seeding happily: a co-invitee nobody seats, an account
    whose claim reaches a sport it holds no rating in, two accounts at one slug.
    """

    # **Across both lists and not within this one.** The runner walks
    # ``ACCOUNTS + RELATIONSHIP_ACCOUNTS`` through one registration, and an
    # address is derived from a slug — so a name shared with the catalog is a
    # collision neither file could see alone, met half way through a run at the
    # second registration for one address.
    refuse_two_accounts_at_one_name(
        list(ACCOUNTS) + [relationship.account for relationship in RELATIONSHIPS]
    )
    for relationship in RELATIONSHIPS:
        # The catalog's own question, asked of this list too: an address the API
        # would refuse cannot sit here waiting to break a run that has already
        # written half of its accounts.
        refuse_an_impossible_account(relationship.account)
    if PROTAGONIST.slug in {
        relationship.account.slug for relationship in RELATIONSHIPS
    }:
        raise RuntimeError(
            f"'{PROTAGONIST.slug}' is the protagonist and cannot also be one of "
            f"the accounts it is in a relationship with."
        )

    seated: set[str] = set()
    for relationship in RELATIONSHIPS:
        edge = relationship.edge
        if isinstance(edge, TheyChallengedYou):
            seated.update(edge.co_invitees)

    co_invitees = {
        relationship.account.slug
        for relationship in RELATIONSHIPS
        if isinstance(relationship.edge, OnTheirCourt)
    }
    if seated != co_invitees:
        raise RuntimeError(
            f"the inbound court seats {sorted(seated)} and the accounts that "
            f"declare a seat on it are {sorted(co_invitees)}. A co-invitee "
            f"nobody seats is an account with no edge; a seat naming nobody is "
            f"a send that would be refused."
        )
    if len(set(_seat_answers())) != len(co_invitees):
        raise RuntimeError(
            "the two co-invitees answer their seats identically. They exist to "
            "differ: the court screen draws a filled seat and an unanswered one "
            "side by side, and two of the same shape proves one of them."
        )

    for relationship in RELATIONSHIPS:
        rated = {
            scenario.sport
            for scenario in relationship.account.scenarios
            if isinstance(scenario, RatedRun)
        }
        sport = sport_of(relationship.edge)
        if sport is not None and sport not in rated:
            raise RuntimeError(
                f"'{relationship.account.slug}' carries a {sport.value} edge and "
                f"holds no {sport.value} rating. `NOT_RATED` is the third gate "
                f"and `OPEN_CHALLENGE` is the fifth, so the fixture would be "
                f"absent for the wrong reason and the claim would pass."
            )
        if Sport.PADEL not in rated:
            raise RuntimeError(
                f"'{relationship.account.slug}' holds no padel rating. Every "
                f"claim in this layer is read off a padel surface, whatever "
                f"sport its own edge is on."
            )


def _seat_answers() -> tuple[SeatAnswer | None, ...]:
    return tuple(
        relationship.edge.answer
        for relationship in RELATIONSHIPS
        if isinstance(relationship.edge, OnTheirCourt)
    )


_refuse_an_impossible_layer()
