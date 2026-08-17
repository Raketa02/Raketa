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
have aggregates; Clubs, Courts, Bookings and Matches do not. Nothing here invents
one — each context seeds its own scenarios when it exists, and
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

from dataclasses import dataclass

from app.engines.assessment import Question
from app.kernel import Sport
from app.modules.users.domain.value_objects import Email, Nickname, RawPassword

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
SEED_EMAIL_DOMAIN = f"rakieta{RESERVED_TLD}"

#: One password for every seeded account, so a developer signing in as any of
#: them types the same thing. It is public by construction — it is in this file
#: — which is the whole reason `app/seeds/guard.py` exists.
SEED_PASSWORD = "rakieta-seed1"

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

    A policy is *not* a promise about the rating it produces. That is
    ``RatingClaim``, which is checked; this is only how the answers are chosen.
    """

    claims: int
    demonstrations: int

    def option_id_for(self, question: Question) -> str:
        strength = self.demonstrations if question.tier is not None else self.claims
        options = question.options
        return options[min(strength, len(options) - 1)].id


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


#: What one account holds, for one sport. A closed union, so the runner's match
#: over it stops typechecking on the day a fourth state exists — an unhandled
#: scenario would otherwise be an account silently seeded into no state at all.
Scenario = OpenRun | AbandonedRun | RatedRun


@dataclass(frozen=True)
class SeedAccount:
    """One deterministic account: what it is called, and what state it is in.

    ``slug`` is the name of the *state*, and it is the only identifier here —
    the address and the nickname are derived from it. Carrying an address as its
    own field would let an account be called one thing and reachable at another,
    which is precisely the confusion a named catalog exists to remove.

    ``scenarios`` is per sport and may be empty: an account with nothing in it is
    a state, and the one every client's empty screen is drawn from.
    """

    slug: str
    description: str
    scenarios: tuple[Scenario, ...] = ()

    @property
    def email(self) -> str:
        return f"{self.slug}@{SEED_EMAIL_DOMAIN}"

    @property
    def nickname(self) -> str:
        return self.slug


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
)


def _refuse_an_impossible_catalog() -> None:
    """Fail at import rather than part-way through a run.

    The value objects are the domain's own, so this asks the exact question the
    registration endpoint would ask — an address or nickname the API would reject
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

    seen: set[str] = set()
    for account in ACCOUNTS:
        Email(account.email)
        Nickname(account.nickname)
        if account.slug in seen:
            raise RuntimeError(f"two seed accounts are named '{account.slug}'")
        seen.add(account.slug)

        sports: set[Sport] = set()
        for scenario in account.scenarios:
            if scenario.sport in sports:
                raise RuntimeError(
                    f"'{account.slug}' has two scenarios for "
                    f"{scenario.sport.value}: one sport is one state."
                )
            sports.add(scenario.sport)
            if isinstance(scenario, RatedRun):
                _refuse_an_impossible_policy(account, scenario)


def _refuse_an_impossible_policy(account: SeedAccount, scenario: RatedRun) -> None:
    """An index into a list of options is not a negative number."""

    policy = scenario.answers
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


_refuse_an_impossible_catalog()
