"""Which addresses exist, and what state each one is in.

An account is **named for the state it represents**, so signing in as an address
is a statement about what you expect to see rather than a lookup in somebody's
notes. One hundred random players is one scenario — *a player who looks average*
— repeated a hundred times; what breaks a screen is the edges, so the catalog is
a list of edges: nothing yet, one run open, one run abandoned, one rating just
made, a rating barely inside its band, a rating well inside it, and every sport
rated at once.

The address is *derived* from that name rather than typed beside it, so the two
cannot drift. The domain is on a TLD RFC 2606 reserves and no registry will ever
sell: a seed account can never become a real mailbox, so a run pointed at the
wrong database cannot mail a stranger. Which of the four reserved TLDs, and why
it is not the one the ticket names, is on ``RESERVED_TLD`` below.

**Scope is what is modeled.** Players, onboarding assessments and Skill ratings
have aggregates; Courts, Bookings and Matches do not. Nothing here invents one —
each context seeds its own scenarios when it exists (the clubs, in ``clubs.py``,
the day the Club context did), and
``test_the_seed_path_touches_only_the_contexts_that_exist`` is what keeps that
from being a promise nobody checks.

**A name that no longer matches its state is the failure this file is built to
refuse.** A rated scenario therefore carries a ``RatingClaim`` — the band it
promises and where in that band the Level must sit — and the runner checks it
against the *stored* rating on every run, including one that creates nothing. An
engine retune that moves a seeded player out of the band their address names
fails the seed run by name, rather than quietly renaming them.

**The catalog is validated on import, through the domain's own value objects.**
An address the API would refuse is refused here, before a session is opened —
otherwise the failure lands halfway through a run, with some accounts written and
some not.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping, Sequence
from uuid import UUID

from app.engines.assessment import Question
from app.kernel import Sport
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.location import LOCATION_PRECISION_DP
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import (
    SocialTag,
    SocialTagSelection,
)
from app.modules.users.domain.value_objects import (
    Email,
    Name,
    Nickname,
    RawPassword,
)

#: A TLD RFC 2606 reserves: no registry will ever sell a name under it, so a
#: seed account can never become somebody's real mailbox.
#:
#: **`.example` rather than the `.test` the ticket asks for, and the reason is
#: measured rather than preferred.** RFC 2606 §2 reserves four TLDs in one
#: sentence — `.test`, `.example`, `.invalid`, `.localhost` — and the boundary
#: schemas refuse two of them. `LoginRequest.email` and `UserResponse.email` are
#: `pydantic.EmailStr`, which is `email-validator`, which refuses any address
#: whose TLD is in its special-use list: `arpa, invalid, local, localhost,
#: onion, test`. So a `.test` account is one **no client can sign in as** (422)
#: and one `/users/me` cannot even serialise (500) — which contradicts this
#: ticket's other acceptance criterion, that an API-level test authenticates as
#: it. `example` is not on that list, and is reserved by the same sentence.
#:
#: Widening the boundary schema is the alternative and was deliberately not
#: taken: it is a public API change made to suit a development tool, and it
#: would let `alice@localhost` register. Reported on #94 and #97 instead.
#:
#: `test_the_boundary_schemas_accept_every_seeded_address` is what keeps this
#: honest — if a future `email-validator` adds `example` to that list, the suite
#: says so by name rather than through a 422 nobody can explain.
RESERVED_TLD = ".example"

#: Unregistrable, and visibly not a real address.
SEED_EMAIL_DOMAIN = f"raketa{RESERVED_TLD}"

#: One password for every seeded account, so a developer signing in as any of
#: them types the same thing. It is public by construction — it is in this file
#: — which is the whole reason `app/seeds/guard.py` exists.
SEED_PASSWORD = "raketa-seed1"

# The four band names the rating vocabulary prints (root `CONTEXT.md`). Written
# here as the strings a *result* carries rather than imported from an engine's
# own enum: a claim is a statement about what the platform tells the player, and
# the engine version that produced it is free to change underneath.
BAND_NEW = "New"
BAND_DEVELOPING = "Developing"
BAND_ESTABLISHED = "Established"
BAND_ADVANCED = "Advanced"


@dataclass(frozen=True)
class AnswerPolicy:
    """How a scenario answers whatever the questionnaire puts to it.

    An index into the question's *own* options, counted from the weakest — the
    bank orders every question's options weakest to strongest, and clamps to the
    last one when a question offers fewer than the index asks for. So a policy is
    two small numbers rather than a script of option ids, and it keeps working
    when a question's copy is rewritten or its options are renamed.

    The two numbers are the split the engine's own port draws: ``Question.tier``
    is *"the difficulty tier for execution questions and ``None`` otherwise"*, so
    ``demonstrations`` answers what happens inside a point and ``claims``
    answers everything else. Read off the abstraction rather than off a question
    id, because an id belongs to an engine version and the seed is wired to
    whichever version the API serves.

    **``spread`` widens an index into an index drawn per question**, and it is
    what makes a *population* out of a policy. The questionnaire is the only door
    to a level (there is no *record a rating* use case), so sixty members sharing
    six policies would be sixty players at six values of μ: ``combine_sigma``
    constant, predicted balance a function of a handful of Δμ, and a pool of
    near-identical cards ranked arbitrarily. That is a screen defect rather than
    a statistics defect, and no amount of realism elsewhere fixes it.

    **The draw is keyed ``(handle, sport, question_id)``, never by consumption
    order.** The engine chooses adaptively; a policy that consumed a stream in
    ask-order would have an inserted question reshuffle every later answer for
    every member, and the band histogram would move for a reason having nothing
    to do with skill. Keyed this way, a member's answers are a function of who
    they are and what they were asked — so adding a member changes that member's
    row and nobody else's, and a question added to the bank changes only the
    answer to *that* question.

    **The width is per axis, and that is where the one departure lives.** Every
    question is drawn — there is no question the key is not consulted for — but
    each of the two axes declares its own width, and an archetype standing for a
    band declares **zero on the claims**. The reason is the opening question: it
    is a claim, and its weakest option puts the engine on its one-question
    beginner path, so a jittered claim would not spread a member around their
    band — it would move them into a different archetype's. Declared per axis
    rather than carved out of the mechanism, so the exception is a number in a
    fixture rather than a branch in this method.

    Both widths default to zero, which is the six named policies below
    unchanged: a draw of zero width is the index itself.

    A policy is *not* a promise about the rating it produces. That is
    ``RatingClaim``, which is checked; this is only how the answers are chosen.
    """

    claims: int
    demonstrations: int

    #: Half-widths of the draw around each centre, in option steps. **Zero is a
    #: named policy**; anything larger is an archetype standing for a band.
    claim_spread: int = 0
    demonstration_spread: int = 0

    def option_id_for(self, question: Question, *, drawn_for: str) -> str:
        """The option this policy picks, for this question, for this member.

        ``drawn_for`` is *who is answering, in which sport* — the two halves of
        the key the question id completes, and :func:`answer_key` is what spells
        it. **Required and never defaulted**, even though a zero-spread policy
        never consults it: a default would let a spread policy be asked without
        a key and answer identically for everybody, which is a population that
        looks like a population and is one player repeated.
        """

        options = question.options
        centre, width = (
            (self.claims, self.claim_spread)
            if question.tier is None
            else (self.demonstrations, self.demonstration_spread)
        )
        strength = self._drawn(centre, width, key=f"{drawn_for}|{question.id}")
        return options[min(max(strength, 0), len(options) - 1)].id

    def _drawn(self, centre: int, width: int, *, key: str) -> int:
        """One index, drawn from ``key`` alone.

        ``random.Random`` seeded with a *string* hashes it with SHA-512 before
        seeding, so this is reproducible across processes and unaffected by
        ``PYTHONHASHSEED`` — which ``docs/adr/0105`` makes the question worth
        answering out loud rather than assuming.
        """

        if width == 0:
            return centre
        return centre + random.Random(key).randint(-width, width)


def answer_key(handle: str, sport: Sport) -> str:
    """The first two thirds of a draw key, spelled once.

    Here rather than at each call site because a key assembled two ways is two
    populations, and the one that drifted would be the one nobody re-derived.
    """

    return f"{handle}|{sport.value}"


#: The weakest answer to everything. The opening question's weakest option is
#: *"I have never played"*, which the engine's beginner fast path turns into a
#: one-question run — the shortest complete assessment there is.
NEVER_PLAYED = AnswerPolicy(claims=0, demonstrations=0)

#: Somebody who has tried the sport a few times and says so consistently.
MODEST = AnswerPolicy(claims=1, demonstrations=1)

#: Claims of a club player, demonstrations of a beginner. The weakest answer set
#: that still lands in Established, which is what makes *barely* a description
#: rather than a hope.
CLAIMS_AHEAD_OF_THE_HANDS = AnswerPolicy(claims=2, demonstrations=0)

#: A consistent club player.
MIDDLING = AnswerPolicy(claims=2, demonstrations=2)

#: A consistently strong player, comfortably inside Established.
STRONG = AnswerPolicy(claims=3, demonstrations=3)

#: The strongest answer to everything.
STRONGEST = AnswerPolicy(claims=4, demonstrations=4)

#: **Eight answer sets that all land inside one band, and differ everywhere
#: else.** Every one of these finishes between 2,97 and 3,50 for padel — inside
#: ``Established`` at a position of 0,25 to 0,75, which is
#: ``THE_PROTAGONISTS_BAND`` — so an account may take any of them and still be
#: held to the same claim it was held to before.
#:
#: **What they exist for.** The eleven relationship accounts are *controls*:
#: everything that is not the edge under test is held equal, deliberately. The
#: rating was held equal with it, and it did not have to be — a block, a pass, an
#: interest and an open challenge are gates on a **pair**, and none of them reads
#: μ. Holding it equal anyway put eleven accounts at one level in the
#: protagonist's own pool, where they outscore everybody and tie with each other:
#: the evenest four is then a tie between clones, ⚡ returns the same court every
#: time, and the balance forecast reads the same number whatever was asked for.
#: The edge stays the only axis under test; the level stops being a sixteenth
#: copy of hers.
#:
#: They are **fixed policies and not a spread** — each account answers one way,
#: deterministically, and ``_refuse_an_impossible_policy`` still refuses a drawn
#: one. A claim is a band and a position, and a fixed policy can be held to it.
#:
#: The two axes move independently on purpose: ``(4, 0)`` and ``(1, 4)`` reach
#: much the same μ as ``(2, 2)`` by disagreeing with themselves, which finishes
#: with a **wider σ** — so the spread is a spread of confidence as well as of
#: level, and the balance term has both to read.
THE_BAND_FROM_WITHIN: tuple[AnswerPolicy, ...] = (
    AnswerPolicy(claims=4, demonstrations=0),  # 3,10 — widest
    AnswerPolicy(claims=3, demonstrations=0),  # 3,06 — wide
    AnswerPolicy(claims=2, demonstrations=2),  # 3,15 — MIDDLING
    AnswerPolicy(claims=1, demonstrations=3),  # 3,18 — wide
    AnswerPolicy(claims=4, demonstrations=1),  # 3,29 — wide
    AnswerPolicy(claims=2, demonstrations=3),  # 3,32
    AnswerPolicy(claims=1, demonstrations=4),  # 3,41 — widest
    AnswerPolicy(claims=2, demonstrations=4),  # 3,50
)


@dataclass(frozen=True)
class RatingClaim:
    """What an account's name promises about the rating its run produces.

    Checked by the runner against the **stored** rating on every run, including
    a run that creates nothing — so an account that was seeded last month and
    has drifted out of its band is caught by the next `make seed`, not by a
    developer wondering why the screen looks wrong.
    """

    band: str

    #: Where in that band the Level must sit, as a fraction of the band's own
    #: width. A claim about the band alone leaves it wide open.
    #:
    #: A fraction rather than a pair of Levels, because a band's edges travel on
    #: the rating: re-cut the bands and *barely inside Established* still means
    #: what it says, where a literal ``2,70–2,95`` would quietly start meaning
    #: something else — or nothing.
    position: tuple[float, float] = (0.0, 1.0)

    def complaint_about(
        self, *, band_name: str, level: float, band_lower: float, band_upper: float
    ) -> str | None:
        """What is wrong with this rating, in a developer's words, or nothing.

        The band's edges are the *rating's own*, never a second copy held here:
        a screen printing a range prints those values, so a claim compared
        against anything else would be checking the seed against a number
        nothing keeps honest.
        """

        if band_name != self.band:
            return f"is in the {band_name} band and its name promises {self.band}"

        low, high = self.position
        width = band_upper - band_lower
        where = (level - band_lower) / width if width > 0 else 0.0
        if low <= where <= high:
            return None
        return (
            f"sits {where:.0%} into the {band_name} band "
            f"({level:.2f} of {band_lower:.2f}–{band_upper:.2f}), outside the "
            f"{low:.0%}–{high:.0%} its name promises"
        )


@dataclass(frozen=True)
class OpenRun:
    """An assessment started and left at its first question."""

    sport: Sport


@dataclass(frozen=True)
class AbandonedRun:
    """An assessment started and then abandoned — the failed case.

    Abandonment is a transition and not a deletion, so this leaves a stream that
    ended without a rating: the state a resume gate has to route *past*, and the
    one that is easiest to forget exists.
    """

    sport: Sport


@dataclass(frozen=True)
class RatedRun:
    """An assessment answered to the engine's stop and completed.

    The claim is required rather than optional: a rated scenario that promised
    nothing would be an account whose name no one could check, which is the
    failure this catalog is shaped to refuse.
    """

    sport: Sport
    answers: AnswerPolicy
    claim: RatingClaim


@dataclass(frozen=True, slots=True)
class Centre:
    """Where the seed's centre is: the protagonists' own cell, and the point
    every ring is measured from. Two decimal places, ``LocationArea``'s own."""

    latitude: float
    longitude: float


#: The one coordinate every distance in this seed is measured from — the
#: protagonists' own, and the centre ``cohort.py`` cuts its rings around.
#:
#: **It lives here rather than in the cohort** because it is a *protagonist's*
#: fact and the rings are derived from it: a centre owned by the population
#: would be a centre the four named accounts had to agree with by hand, and the
#: day one of them moved, every ring would quietly be measured from somewhere
#: else. London, at ``LocationArea``'s own two decimal places, because that is
#: the resolution the commit rounds to on the way in.
#:
#: **This is the reference, and the run may sit somewhere else.** The committed
#: population (``cohort.json``) and every distance in its tables are measured
#: from here, and nothing moves them. The *run* is centred wherever
#: ``SEED_CENTRE`` says (``CENTRE`` below), because the client puts the phone's
#: own position on the profile at every cold start (``docs/adr/0174`` §6): a
#: developer in Kraków who signs into a seeded account from a phone moves it
#: 1,400 km from a London cohort, and every location screen goes empty. Seeding
#: the cohort around the developer instead is what keeps that write a same-cell
#: no-op. Every member sits on the centre's own meridian, so the move is a
#: translation and every distance survives it exactly.
REFERENCE_CENTRE = Centre(latitude=51.51, longitude=-0.13)

#: The environment variable that moves the run's centre: ``"lat,lon"``, decimal
#: degrees, rounded to the cell on the way in. Read from the process environment
#: rather than from ``Settings``, because it is a developer command's argument
#: and not the application's configuration: ``.env.docker`` supplies it to
#: ``make seed``, and a shell export to ``make seed-host``.
SEED_CENTRE_VARIABLE = "SEED_CENTRE"


def seed_centre(environ: Mapping[str, str]) -> Centre:
    """Where this run is centred: ``SEED_CENTRE`` if set, the reference if not.

    A pure function of the record, tested exhaustively like the config parsers
    (``docs/environments.md``). Rounds to ``LocationArea``'s two decimal places
    so the centre is a cell — which is exactly what a phone's fix becomes on the
    way into the platform, and what makes the cold-start write a no-op there.
    """

    raw = environ.get(SEED_CENTRE_VARIABLE)
    if raw is None or raw.strip() == "":
        return REFERENCE_CENTRE
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        raise ValueError(
            f"{SEED_CENTRE_VARIABLE} must be 'latitude,longitude' in decimal "
            f"degrees, e.g. '50.06,19.94'; got {raw!r}"
        )
    try:
        latitude, longitude = (float(part) for part in parts)
    except ValueError:
        raise ValueError(
            f"{SEED_CENTRE_VARIABLE} must be 'latitude,longitude' in decimal "
            f"degrees, e.g. '50.06,19.94'; got {raw!r}"
        ) from None
    if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
        raise ValueError(
            f"{SEED_CENTRE_VARIABLE} is off the globe: {raw!r} (latitude within "
            f"±90, longitude within ±180)"
        )
    return Centre(
        latitude=round(latitude, LOCATION_PRECISION_DP),
        longitude=round(longitude, LOCATION_PRECISION_DP),
    )


#: The centre this run seeds around. Resolved once, at import, from the process
#: environment — the same moment the production guard reads its settings.
CENTRE = seed_centre(os.environ)
CENTRE_LATITUDE = CENTRE.latitude
CENTRE_LONGITUDE = CENTRE.longitude

#: What a seeded profile calls its consent copy. One string, so the accounts and
#: the cohort answer the consent question the same way.
SEED_CONSENT_COPY_VERSION = "proposals-seed"


@dataclass(frozen=True)
class SeedProfile:
    """The Player profile one account commits, as onboarding's second part.

    **A per-player axis on the account, not a fourth member of ``Scenario``.** A
    scenario is per *sport* — a rating, an open run, an abandoned one — and a
    profile is per *player*: one week, one radius, one location, one answer about
    photographs. Folding it into the per-sport union would make an account with
    two sports carry two profiles, which is a state the domain cannot reach.

    ``intents`` is the one field that *is* per sport, because a declaration is
    (``docs/adr/0094``). It is a tuple of pairs rather than a mapping so the
    account stays hashable and its order is the order the run declares in.

    ``committed_days_ago`` is how far **before this run's own now** the profile
    was committed, and it is what makes ADR-0113's fourteen-day window visible:
    a profile committed through the wall clock is a newcomer, always, and a gate
    with only one side present cannot be seen at all. The run injects a clock
    (``app/seeds/clock.py``); this is the number it is set to.

    ``clear_the_week`` is the one state the commit itself cannot express: the
    commit refuses an empty grid — the floor binds the answer a player is *asked*
    for — while ``ChangeAvailability`` accepts one, because clearing a week
    afterwards is a legal edit. So a blank week is a commit followed by an edit,
    which is exactly how a player reaches it.
    """

    #: ``(iso weekday 1–7, part of day)`` — one pair per cell ticked.
    availability: tuple[tuple[int, str], ...]
    social_tag_ids: tuple[str, ...]
    search_radius_km: int
    gender: Gender
    gender_preference: GenderPreference
    proposals_opt_in: bool
    committed_days_ago: int
    intents: tuple[tuple[Sport, PlayIntent], ...] = ()
    latitude: float = CENTRE_LATITUDE
    longitude: float = CENTRE_LONGITUDE
    clear_the_week: bool = False

    #: Which screen the declaration was made on. Client-asserted everywhere else
    #: and asserted here too — the seed answers the questionnaire and declares in
    #: its tail, which is what ``RATING_TAIL`` names.
    intent_surface: PlayIntentSurface = PlayIntentSurface.RATING_TAIL

    #: **No photograph, ever**, and it is a wired field rather than a hard-coded
    #: empty list at the commit: a seeded photo would need bytes in this
    #: repository and an object store to put them in, and the card renders the
    #: generated court poster without one — which is the state most cards are in
    #: and the one worth developing against. It is passed to the command like
    #: every other answer, so *no photograph* is a declaration something checks
    #: rather than a line in the runner nothing reads.
    photo_ids: tuple[UUID, ...] = ()

    #: The line this player wrote about themselves, or ``None`` for the most
    #: who wrote none (``docs/adr/0170``). Passed to the commit like every other
    #: answer, so it goes through the same fence a phone's line does — a seeded
    #: line carrying contact fails ``make seed`` rather than bypassing the rule.
    intro: str | None = None


#: What one account holds, for one sport. A closed union, so the runner's match
#: over it stops typechecking on the day a fourth state exists — an unhandled
#: scenario would otherwise be an account silently seeded into no state at all.
Scenario = OpenRun | AbandonedRun | RatedRun


#: **The names every seeded player is shown under.**
#:
#: A slug says what an account *is for* — ``said-yes-to-you`` names a state, and
#: naming states is what makes the catalog readable from the report. It is a
#: terrible thing to meet on a card. Every screen in this product draws the
#: **name**, so a developer testing the builder was reading a sentence about a
#: fixture where a person's name goes, and could not tell a crowded court from a
#: list of test conditions.
#:
#: So the slug stays the identifier — the address is still ``{slug}@…``, the
#: report still prints it, and every assertion still names it — and the account
#: is **named** as a player is: a **Name**, ``First Last``, and a **Nickname**
#: derived from it, the lowercase ``first_last`` (``docs/adr/0171`` §5). This
#: file used to argue ``First.Last`` *and not* ``First Last``, because a nickname
#: is a handle and a space is not in it, and declined to reopen the users
#: context's rule from a fixture. It was right to decline; ADR-0171 is where the
#: rule was reopened, and the dot went with it.
#:
#: **Two surname pools, and that is what keeps them apart.** The catalog and the
#: cohort are dealt by two different modules and neither can see the other's
#: list, so a shared pool would collide on a name eventually and the collision
#: would surface as a unique-constraint violation on the **nickname** half way
#: through a run — a name may be shared, a handle may not, and the handle is a
#: function of the name. Given separate surnames, a catalog name and a cohort
#: name cannot be equal whatever either list grows to.
FIRST_NAMES: tuple[str, ...] = (
    "Marta", "Ines", "Carla", "Nuria", "Alba", "Rocio", "Lucia", "Elena",
    "Sofia", "Paula", "Irene", "Clara", "Laia", "Nerea", "Ainhoa", "Julia",
    "Diego", "Hugo", "Pablo", "Mateo", "Bruno", "Alvaro", "Nacho", "Rafa",
    "Javier", "Sergio", "Tomas", "Adrian", "Ivan", "Marcos", "Gonzalo", "Unai",
    "Aitor", "Ruben", "Oscar", "Dani", "Pau", "Guillem", "Arnau", "Nil",
)

#: The catalog's own surnames — see ``FIRST_NAMES`` on why there are two pools.
CATALOG_SURNAMES: tuple[str, ...] = (
    "Ferrer", "Solano", "Vidal", "Rojas", "Miralles", "Andrade",
)

#: The eleven relationship accounts', dealt by their own module.
RELATIONSHIP_SURNAMES: tuple[str, ...] = (
    "Nogueira", "Peralta", "Quintana", "Sabater",
)

#: The cohort's, and disjoint from the other two by construction.
COHORT_SURNAMES: tuple[str, ...] = (
    "Bertran", "Casals", "Duarte", "Esteve", "Fabregat", "Gallego",
    "Herrero", "Iglesias",
)


@lru_cache(maxsize=None)
def _roster(surnames: tuple[str, ...]) -> tuple[str, ...]:
    """Every ``First Last`` this pool can make, **in one shuffled order.**

    Shuffled rather than enumerated, and that is the whole point of the
    indirection. Read in the obvious nested order, the first forty names dealt
    all share a surname and a seeded population reads as one family; read with
    the surname cycling fastest, one first name repeats six times running. A
    shuffle makes both halves vary at every step while the list stays a
    permutation of distinct pairs — so uniqueness is still by construction and
    not by a stride argument nobody re-checks when a surname is added.

    ``random.Random`` seeded with a *string* hashes it with SHA-512 first, so the
    order is stable across processes and unaffected by ``PYTHONHASHSEED``
    (``docs/adr/0105``). Keyed off the pool itself, so adding a surname reshuffles
    that pool and leaves the others alone.
    """

    pairs = [f"{first} {last}" for last in surnames for first in FIRST_NAMES]
    random.Random(f"names|{'|'.join(surnames)}").shuffle(pairs)
    return tuple(pairs)


def handle_of(name: str) -> str:
    """The nickname a seeded ``First Last`` is given: **lowercase, no dot**
    (``docs/adr/0171`` §5) — ``Diego Fabregat`` is ``@diego_fabregat``.

    A function of the name and nothing else, so the two lists dealt out of
    disjoint surname pools stay disjoint on the handle too, which is the field
    that is unique.
    """

    return "_".join(name.lower().split())


def dealt_name(index: int, surnames: tuple[str, ...]) -> str:
    """The ``index``-th name out of one pool, and **no two indices share one.**

    The caller is refused rather than wrapped past the end, since a wrapped name
    is a duplicate and a duplicate is a unique-constraint violation discovered
    half way through a seed run.
    """

    roster = _roster(surnames)
    if not 0 <= index < len(roster):
        raise RuntimeError(
            f"name {index} was asked of a pool that holds {len(roster)}: "
            f"{len(FIRST_NAMES)} first name(s) over {len(surnames)} surname(s). "
            f"Add surnames — the pools must stay disjoint from each other."
        )
    return roster[index]


@dataclass(frozen=True)
class SeedAccount:
    """One deterministic account: what it is called, and what state it is in.

    ``slug`` is the name of the *state*, and it is the only identifier here —
    the address, the name and the nickname are derived from it. Carrying an
    address as its own field would let an account be called one thing and
    reachable at another, which is precisely the confusion a named catalog
    exists to remove.

    ``scenarios`` is per sport and may be empty: an account with nothing in it is
    a state, and the one every client's empty screen is drawn from.

    ``profile`` is the **per-player** axis, and ``None`` is a state of its own —
    a player who has finished the questionnaire and never answered onboarding's
    second part. The four protagonists carry one; the seven states above it do
    not, because each of those is named for a *rating* state and giving them a
    week and a location would make each of them two claims in one address.
    """

    slug: str
    description: str
    scenarios: tuple[Scenario, ...] = ()
    profile: SeedProfile | None = None

    @property
    def email(self) -> str:
        return f"{self.slug}@{SEED_EMAIL_DOMAIN}"

    @property
    def name(self) -> str:
        """The name this account is shown under — **never its slug.**

        Read out of the register rather than stored on the account, because the
        constants above are referenced by name from ``screens.py`` and from the
        tests: a name written into a field would have to be written at every one
        of those definitions, and the one somebody forgot would be the account
        that seeded under a slug again.

        **The slug is the fallback and it is proven unreachable**, by
        ``refuse_an_account_nobody_named`` over each real list at import. The
        alternative — raising here — makes ``name`` partial, and every guard in
        this module reads it: an account built to be *refused* for a bad address
        would explode on its name before the guard could say so, and the refusal
        a developer got would name the wrong thing.
        """

        return NAMES.get(self.slug, self.slug)

    @property
    def nickname(self) -> str:
        """The handle, derived from the name (``docs/adr/0171`` §5): what the
        record and the You tab draw as ``@…``, and no other screen says."""

        return handle_of(self.name)


BRAND_NEW_PLAYER = SeedAccount(
    slug="brand-new-player",
    description=(
        "A registered player with nothing else at all — no assessment, no "
        "rating. Every empty state a client can show, in one account."
    ),
)

ASSESSMENT_IN_PROGRESS = SeedAccount(
    slug="assessment-in-progress",
    description=(
        "A registered player with an onboarding assessment open at its first "
        "question and no rating yet — the state a resume flow is developed "
        "against."
    ),
    scenarios=(OpenRun(sport=Sport.PADEL),),
)

ASSESSMENT_ABANDONED = SeedAccount(
    slug="assessment-abandoned",
    description=(
        "A player who started an onboarding assessment and abandoned it: a run "
        "that ended without a rating, and a sport that is free to be started "
        "again."
    ),
    scenarios=(AbandonedRun(sport=Sport.PADEL),),
)

ASSESSMENT_COMPLETED = SeedAccount(
    slug="assessment-completed",
    description=(
        "A player who has just finished onboarding: one completed assessment "
        "and the rating it produced, at the bottom of the scale after the "
        "one-question beginner path."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=NEVER_PLAYED,
            claim=RatingClaim(band=BAND_NEW),
        ),
    ),
)

RATING_BARELY_ESTABLISHED = SeedAccount(
    slug="rating-barely-established",
    description=(
        "A player whose Level sits just inside the Established band, with a "
        "likely range that still reaches down into Developing — the card that "
        "has to render a band its own range does not stay inside."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=CLAIMS_AHEAD_OF_THE_HANDS,
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.0, 0.25)),
        ),
    ),
)

RATING_WELL_ESTABLISHED = SeedAccount(
    slug="rating-well-established",
    description=(
        "A player well inside the Established band, clear of its lower edge — "
        "the same band as `rating-barely-established` and a different player."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=STRONG,
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.6, 1.0)),
        ),
    ),
)

RATED_IN_EVERY_SPORT = SeedAccount(
    slug="rated-in-every-sport",
    description=(
        "A rating in all four sports, one per band — the longest list a ratings "
        "screen can be asked to draw, and the only account where the four bands "
        "are on screen together."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=NEVER_PLAYED,
            claim=RatingClaim(band=BAND_NEW),
        ),
        RatedRun(
            sport=Sport.TENNIS,
            answers=MODEST,
            claim=RatingClaim(band=BAND_DEVELOPING),
        ),
        RatedRun(
            sport=Sport.SQUASH,
            answers=MIDDLING,
            claim=RatingClaim(band=BAND_ESTABLISHED),
        ),
        RatedRun(
            sport=Sport.BADMINTON,
            answers=STRONGEST,
            claim=RatingClaim(band=BAND_ADVANCED),
        ),
    ),
)

# ---------------------------------------------------------------------------
# The four protagonists — a Play screen is developed *as* one of these
# ---------------------------------------------------------------------------
#
# **They live in the catalog and not in the cohort**, and the reason is the
# catalog's own idiom: each is named for a state, and a distribution asserting
# the existence of exactly one person is not a distribution. *the-blank-week-
# player* is the clearest case — a single named edge — and the cohort is what
# stands behind them, never what they are drawn from.
#
# Each carries a **profile**, which is the axis this file gained for them, and
# each is committed at a stated age so that ADR-0113's window has both of its
# sides present among the people a developer actually signs in as. Three of the
# four settled and one inside the window, deliberately: a protagonist accidental-
# ly inside it would tighten the level gate on every search a developer ran and
# nothing on the screen would say why.

#: The week the protagonists tick. Six of the twenty-one cells, spread across
#: four evenings and a weekend morning, so that a cohort member drawn against it
#: can share two cells or none and both are ordinary rather than contrived.
PROTAGONIST_WEEK: tuple[tuple[int, str], ...] = (
    (2, "EVENING"),
    (3, "EVENING"),
    (4, "EVENING"),
    (5, "EVENING"),
    (6, "MORNING"),
    (6, "AFTERNOON"),
)

#: Three tags on the competitive side of the vocabulary's own split, so the tag
#: term has something to agree and disagree with.
#:
#: **Through the enum and never as strings.** A tag id is persisted on profiles
#: for ever and has exactly one home; a literal here would be the second copy
#: `test_no_second_copy_of_a_tag_id_exists_anywhere_in_the_app` exists to refuse,
#: and it would keep working right up until somebody retired one of the three.
PROTAGONIST_TAGS: tuple[str, ...] = (
    SocialTag.PLAYS_TO_WIN.value,
    SocialTag.HERE_TO_IMPROVE.value,
    SocialTag.WARMS_UP_PROPERLY.value,
)

#: The radius every ring in ``cohort.py`` is cut against. **Ten, and not the
#: fifty the slider allows**, because the relaxation ladder multiplies what the
#: searcher asked for: at fifty both rungs clamp to the ceiling and there is no
#: ladder to watch. At ten the rungs land on fifteen and twenty, which is what
#: the rings are cut by.
PROTAGONIST_RADIUS_KM = 10

#: Settled, and clear of the fourteen-day window on the far side.
SETTLED_DAYS_AGO = 40

#: Inside the window, and clear of its near edge — so a change to the window
#: moves who is a newcomer rather than the arithmetic of one edge case.
NEWCOMER_DAYS_AGO = 3

#: **Only the default protagonist stays on ``MIDDLING``.** She is the reference
#: every Play screen is developed against, so her level is the one the others are
#: read relative to and it does not move. The other three take a level of their
#: own out of the same band, for the reason ``THE_BAND_FROM_WITHIN`` gives: a
#: pool holding four people at one μ has an **exactly** even four in it, the
#: group objective prefers it over every other arrangement because a gap of zero
#: cannot be beaten, and ⚡ returns that court and a forecast of 62% for ever.
#: Their own claims are unchanged — each is still *Established, a quarter to
#: three-quarters in* — because what each of these three exists to show is a
#: window, a missing second sport and a cleared week, and not one of those reads
#: a level.
THE_POPULATED_PLAYER = SeedAccount(
    slug="the-populated-player",
    description=(
        "The default protagonist: rated in two sports, settled well clear of "
        "the newcomer window, at the centre of every ring the cohort is cut "
        "into. Every Play screen is developed signed in as this account."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=MIDDLING,
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.25, 0.75)),
        ),
        RatedRun(
            sport=Sport.TENNIS,
            answers=MIDDLING,
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.25, 0.75)),
        ),
    ),
    profile=SeedProfile(
        availability=PROTAGONIST_WEEK,
        social_tag_ids=PROTAGONIST_TAGS,
        search_radius_km=PROTAGONIST_RADIUS_KM,
        gender=Gender.WOMAN,
        gender_preference=GenderPreference.ANY,
        proposals_opt_in=True,
        committed_days_ago=SETTLED_DAYS_AGO,
        intents=(
            (Sport.PADEL, PlayIntent.COMPETITIVE),
            (Sport.TENNIS, PlayIntent.FOR_FUN),
        ),
        # So *how others see you* has a line under the name for the account
        # most work is done against.
        intro="Padel on weekdays, tennis when the sun is out.",
    ),
)

THE_NEWCOMER = SeedAccount(
    slug="the-newcomer",
    description=(
        "A player whose profile was committed inside ADR-0113's fourteen-day "
        "window — the widened gate, from the newcomer's own side, which is the "
        "half a settled protagonist can never show."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=THE_BAND_FROM_WITHIN[5],  # 3,32
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.25, 0.75)),
        ),
    ),
    profile=SeedProfile(
        availability=PROTAGONIST_WEEK,
        social_tag_ids=PROTAGONIST_TAGS,
        search_radius_km=PROTAGONIST_RADIUS_KM,
        gender=Gender.WOMAN,
        gender_preference=GenderPreference.ANY,
        proposals_opt_in=True,
        committed_days_ago=NEWCOMER_DAYS_AGO,
        intents=((Sport.PADEL, PlayIntent.COMPETITIVE),),
    ),
)

THE_ONE_SPORT_PLAYER = SeedAccount(
    slug="the-one-sport-player",
    description=(
        "Rated in padel and in nothing else, with no tennis declaration at "
        "all — the account that shows what a second sport's absence looks like "
        "on a screen built to switch between them."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=THE_BAND_FROM_WITHIN[1],  # 3,06
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.25, 0.75)),
        ),
    ),
    profile=SeedProfile(
        availability=PROTAGONIST_WEEK,
        social_tag_ids=PROTAGONIST_TAGS,
        search_radius_km=PROTAGONIST_RADIUS_KM,
        gender=Gender.MAN,
        gender_preference=GenderPreference.ANY,
        proposals_opt_in=True,
        committed_days_ago=SETTLED_DAYS_AGO,
        intents=((Sport.PADEL, PlayIntent.COMPETITIVE),),
    ),
)

THE_BLANK_WEEK_PLAYER = SeedAccount(
    slug="the-blank-week-player",
    description=(
        "A player who committed a week and then cleared it. The availability "
        "term stands down for them rather than scoring a nought, and every "
        "surface that took a week has to say so."
    ),
    scenarios=(
        RatedRun(
            sport=Sport.PADEL,
            answers=THE_BAND_FROM_WITHIN[7],  # 3,50
            claim=RatingClaim(band=BAND_ESTABLISHED, position=(0.25, 0.75)),
        ),
    ),
    profile=SeedProfile(
        availability=PROTAGONIST_WEEK,
        social_tag_ids=PROTAGONIST_TAGS,
        search_radius_km=PROTAGONIST_RADIUS_KM,
        gender=Gender.WOMAN,
        gender_preference=GenderPreference.ANY,
        proposals_opt_in=True,
        committed_days_ago=SETTLED_DAYS_AGO,
        intents=((Sport.PADEL, PlayIntent.COMPETITIVE),),
        clear_the_week=True,
    ),
)

#: The four a Play screen is developed *as*, in the order the run walks them:
#: the default first, so an interrupted run leaves the account most work is done
#: against already built.
PROTAGONISTS: tuple[SeedAccount, ...] = (
    THE_POPULATED_PLAYER,
    THE_NEWCOMER,
    THE_ONE_SPORT_PLAYER,
    THE_BLANK_WEEK_PLAYER,
)

#: The accounts that carry the **tester mark** (``docs/adr/0180`` §9), so a rule
#: the flags repo gives only to its ``testers`` segment can be seen on a freshly
#: seeded database without anybody running ``make tester`` first.
#:
#: **The default protagonist is one because she is the account a phone is signed
#: in as**, and a flag is decided on the device. **Two of the four and not all of
#: them**, so a gated Play screen can be read from either side of the mark by
#: signing in as another protagonist — a set that marked everybody a screen is
#: developed against would leave nothing to compare with. The mark is set through
#: the same use case the command runs, and a re-run finds it already set.
TESTERS: tuple[SeedAccount, ...] = (
    THE_POPULATED_PLAYER,
    THE_NEWCOMER,
)

#: Every account this system creates, in the order a run walks them: emptiest
#: first, so a run interrupted half way leaves the simple states done.
ACCOUNTS: tuple[SeedAccount, ...] = (
    BRAND_NEW_PLAYER,
    ASSESSMENT_IN_PROGRESS,
    ASSESSMENT_ABANDONED,
    ASSESSMENT_COMPLETED,
    RATING_BARELY_ESTABLISHED,
    RATING_WELL_ESTABLISHED,
    RATED_IN_EVERY_SPORT,
) + PROTAGONISTS


#: slug -> the name it is shown under, written by ``name_them`` at import.
#:
#: A register rather than a field for the reason ``SeedAccount.name`` gives,
#: and **module-level rather than per-list** so that a name dealt twice is a
#: collision this process can see. Two lists dealt out of two disjoint surname
#: pools cannot collide, and this is where that would show up if they ever did.
NAMES: dict[str, str] = {}

#: The inverse, lower-cased — **only** so a second deal onto a taken name is
#: refused. Separate from ``NAMES`` because a register keyed by two different
#: kinds of string is a register whose lookups cannot be read.
_TAKEN: dict[str, str] = {}


def name_them(accounts: Sequence[SeedAccount], surnames: tuple[str, ...]) -> None:
    """Deal one name to each account in a list, **by sorted slug.**

    Sorted, so the deal is a function of *which accounts exist* rather than of
    the order somebody wrote them in: a state inserted in the middle of a list
    moves nobody it does not have to move, and a diff of the seed report stays
    readable.

    Refuses a name already dealt, which is the check that keeps the surname
    pools honest: two pools that stopped being disjoint would otherwise seat two
    people under one nickname — the handle is a function of the name — and fail
    on the unique constraint half way through a run, with some accounts written
    and some not.
    """

    for index, slug in enumerate(sorted(one.slug for one in accounts)):
        name = dealt_name(index, surnames)
        if (taken := _TAKEN.get(handle_of(name))) is not None:
            raise RuntimeError(
                f"'{slug}' was dealt the name '{name}', which '{taken}' already "
                f"holds. The surname pools have stopped being disjoint."
            )
        NAMES[slug] = name
        _TAKEN[handle_of(name)] = slug


name_them(ACCOUNTS, CATALOG_SURNAMES)


def refuse_an_account_nobody_named(accounts: Sequence[SeedAccount]) -> None:
    """Every account in a real list was dealt a name. **Asked at import.**

    ``SeedAccount.name`` falls back to the slug so that the guards can run
    against accounts built to be refused, and this is what stops that fallback
    ever reaching a database: a list somebody forgot to hand to ``name_them``
    fails the import rather than seeding people under ``said-yes-to-you`` again.
    """

    forgotten = sorted(one.slug for one in accounts if one.slug not in NAMES)
    if forgotten:
        raise RuntimeError(
            f"{forgotten} would seed under their slug: no list holding them was "
            f"handed to `name_them`. See `FIRST_NAMES`."
        )


def _refuse_an_impossible_catalog() -> None:
    """Fail at import rather than part-way through a run.

    The value objects are the domain's own, so this asks the exact question the
    naming would ask — an address, a name or a nickname the API would reject
    cannot sit here waiting to break a seed run that has already written half of
    its accounts.

    Two scenarios for one sport on one account is refused for the same reason,
    and it is not hypothetical: an account with two rated padel runs describes a
    state the domain cannot reach at all, because a rated sport refuses a second
    assessment. The seed would fail on the second one, three quarters of the way
    through.
    """

    RawPassword(SEED_PASSWORD)

    if not SEED_EMAIL_DOMAIN.endswith(RESERVED_TLD):
        raise RuntimeError(
            f"seed accounts must be addressed on the reserved '{RESERVED_TLD}' "
            f"TLD, which cannot be registered. '{SEED_EMAIL_DOMAIN}' can be."
        )

    refuse_two_accounts_at_one_name(ACCOUNTS)
    for account in ACCOUNTS:
        refuse_an_impossible_account(account)


def refuse_two_accounts_at_one_name(accounts: Sequence[SeedAccount]) -> None:
    """No two of these are the same person. **Asked across every list at once.**

    Public, and taking the accounts rather than reading ``ACCOUNTS``, because the
    catalog is no longer the only list the runner walks: the eleven relationships
    are seeded through the same registration, so a slug shared *between* the two
    lists is a collision this file could not see and the run would meet half way
    through, at the second registration for one address.
    """

    seen: set[str] = set()
    for account in accounts:
        if account.slug in seen:
            raise RuntimeError(f"two seed accounts are named '{account.slug}'")
        seen.add(account.slug)


def refuse_an_impossible_account(account: SeedAccount) -> None:
    """Everything that makes one account seedable, asked before a session opens.

    Public because the catalog is no longer the only list of accounts: the
    eleven relationships in ``app/seeds/relationships.py`` are seeded through the
    same walk and have to answer the same questions. One copy, so an account
    added to either list is held to one standard — two would be two standards,
    and the one that drifted would be the one nobody re-read.
    """

    Email(account.email)
    Name(account.name)
    Nickname(account.nickname)

    sports: set[Sport] = set()
    rated: set[Sport] = set()
    for scenario in account.scenarios:
        if scenario.sport in sports:
            raise RuntimeError(
                f"'{account.slug}' has two scenarios for "
                f"{scenario.sport.value}: one sport is one state."
            )
        sports.add(scenario.sport)
        if isinstance(scenario, RatedRun):
            rated.add(scenario.sport)
            _refuse_an_impossible_policy(account, scenario)
    if account.profile is not None:
        # **The rated sports and not merely the ones with a scenario.** An open
        # run and an abandoned one are sports this account has no rating in, and
        # every Play surface refuses an unrated sport — so a declaration against
        # one would name a screen the account cannot reach.
        _refuse_an_impossible_profile(account, account.profile, rated=rated)


def _refuse_an_impossible_policy(account: SeedAccount, scenario: RatedRun) -> None:
    """An index into a list of options is not a negative number."""

    policy = scenario.answers
    if policy.claim_spread or policy.demonstration_spread:
        raise RuntimeError(
            f"'{account.slug}' answers {scenario.sport.value} with a drawn "
            f"policy ({policy.claim_spread}/{policy.demonstration_spread}). A "
            f"named account's claim is a band and a position inside it, and a "
            f"drawn answer set cannot be held to one — a spread belongs to the "
            f"cohort's archetypes, whose claim is a histogram."
        )
    if policy.claims < 0 or policy.demonstrations < 0:
        raise RuntimeError(
            f"'{account.slug}' answers {scenario.sport.value} with {policy}, and "
            f"an answer policy is an index into the options a question offers, "
            f"counted from the weakest."
        )

    low, high = scenario.claim.position
    if not 0.0 <= low <= high <= 1.0:
        raise RuntimeError(
            f"'{account.slug}' claims a position of {scenario.claim.position} "
            f"inside the {scenario.claim.band} band, which is not a fraction of "
            f"that band read low to high."
        )


def _refuse_an_impossible_profile(
    account: SeedAccount, profile: SeedProfile, *, rated: set[Sport]
) -> None:
    """A profile the commit would refuse, refused before a session is opened.

    Asked of the **domain's own value objects**, which is the same discipline the
    addresses above are held to: a tag id this platform does not serve, a radius
    off the slider or a week with nothing in it would otherwise fail half way
    through a run, with some accounts written and some not — and a profile is
    written *after* the questionnaire, so the half that is already there is the
    expensive half.
    """

    SocialTagSelection.from_ids(profile.social_tag_ids)
    SearchRadius.chosen(profile.search_radius_km)
    AvailabilityGrid.of_cells(profile.availability)

    if profile.committed_days_ago < 0:
        raise RuntimeError(
            f"'{account.slug}' commits its profile {profile.committed_days_ago} "
            f"days ago, which is in the future. A seeded profile is backdated "
            f"from the run's own now and never forward of it."
        )

    for sport, _ in profile.intents:
        if sport not in rated:
            raise RuntimeError(
                f"'{account.slug}' declares a {sport.value} Play intent and "
                f"holds no {sport.value} rating. Every Play surface refuses an "
                f"unrated sport, so the declaration would name a screen the "
                f"account cannot reach."
            )


refuse_an_account_nobody_named(ACCOUNTS)
_refuse_an_impossible_catalog()
