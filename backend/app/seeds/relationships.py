"""The eleven accounts named for a relationship with the protagonist.

**The relationships themselves are gone, and the accounts stay** (#578). Each
account was named for one edge the old loop could write between two people —
*they said yes to you*, *they challenged you*, *you passed them* — and a layer
(``pairs.py``) wrote it through a real search, a deal or a send, for the
matcher's screens to read back. Five of those edges were challenges, so the
layer went with the challenges, and the screens that read the other six went
with it. The accounts stay because the protagonist's **played history** seats
them: ``pool_history.py`` names them on her past courts by slug, and
``booked_history.py`` books those courts.

**A slug still says what the account was for**, which is why it reads as a
relationship nothing writes any more. Renaming them belongs with the pool's
history, which goes with the searches (#579); until then a description says
what each one is now.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Final, Sequence

from app.kernel import Sport
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.seeds.catalog import (
    ACCOUNTS,
    BAND_ESTABLISHED,
    MIDDLING,
    PROTAGONIST_RADIUS_KM,
    PROTAGONIST_TAGS,
    PROTAGONIST_WEEK,
    RELATIONSHIP_SURNAMES,
    SETTLED_DAYS_AGO,
    THE_BAND_FROM_WITHIN,
    THE_POPULATED_PLAYER,
    RatedRun,
    RatingClaim,
    SeedAccount,
    SeedProfile,
    name_them,
    refuse_an_account_nobody_named,
    refuse_an_impossible_account,
    refuse_two_accounts_at_one_name,
)

#: The one account every relationship here was a relationship **with**. Named
#: once, so *you* is a fact this module states rather than a convention its
#: eleven slugs imply.
PROTAGONIST: Final = THE_POPULATED_PLAYER

#: The band every relationship account is rated into, and where in it. **The
#: protagonist's own**, so each of them is a fit for her courts.
THE_PROTAGONISTS_BAND: Final = RatingClaim(
    band=BAND_ESTABLISHED, position=(0.25, 0.75)
)



def _account(slug: str, description: str, *, sports: Sequence[Sport]) -> SeedAccount:
    """One relationship account, rated in ``sports`` and nowhere else.

    Everything else is the protagonist's own: her coordinates, her week, her
    tags, her radius and a settled commit date, with ``GenderPreference.ANY`` —
    the accounts were controls, each for one edge, and every axis that was not
    the edge was held equal.
    """

    return SeedAccount(
        slug=slug,
        description=description,
        scenarios=tuple(
            RatedRun(sport=sport, answers=MIDDLING, claim=THE_PROTAGONISTS_BAND)
            for sport in sports
        ),
        profile=SeedProfile(
            weekly_hours=PROTAGONIST_WEEK,
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

SAID_YES_TO_YOU: Final = _account(
    "said-yes-to-you",
    (
        "Once somebody who had said *Let's play* to the-populated-player; "
        "now a player on her past courts."
    ),
    sports=(Sport.PADEL,),
)

YOUR_YES_MAKES_IT_MUTUAL: Final = _account(
    "your-yes-makes-it-mutual",
    (
        "Once a second live yes to the-populated-player; now a player "
        "seated in her played history."
    ),
    sports=(Sport.PADEL,),
)

YOU_SAID_YES_TO_THEM: Final = _account(
    "you-said-yes-to-them",
    (
        "Once somebody the-populated-player had said *Let's play* to; now "
        "a player on her past courts."
    ),
    sports=(Sport.PADEL,),
)

YOU_CHALLENGED_THEM: Final = _account(
    "you-challenged-them",
    (
        "Once the other side of her open tennis challenge; now a player on "
        "her past courts, rated in padel and tennis."
    ),
    sports=(Sport.PADEL, Sport.TENNIS),
)

THEY_CHALLENGED_YOU: Final = _account(
    "they-challenged-you",
    (
        "Once the organiser of a doubles court the-populated-player held a "
        "seat on; now a player seated in her played history."
    ),
    sports=(Sport.PADEL,),
)

IN_YOUR_LINE_UP_AND_ACCEPTED: Final = _account(
    "in-your-line-up-and-accepted",
    (
        "Once a co-invitee who had said yes on her court; now a player on "
        "her past courts."
    ),
    sports=(Sport.PADEL,),
)

IN_YOUR_LINE_UP_STILL_DECIDING: Final = _account(
    "in-your-line-up-still-deciding",
    (
        "Once a co-invitee still deciding on her court; now a player on "
        "her past courts."
    ),
    sports=(Sport.PADEL,),
)

THEY_TURNED_DOWN_YOUR_COURT: Final = _account(
    "they-turned-down-your-court",
    (
        "Once somebody who declined a seat on a court the-populated-player "
        "organised; now a player on her past courts."
    ),
    sports=(Sport.PADEL,),
)

YOU_BLOCKED_THEM: Final = _account(
    "you-blocked-them",
    (
        "Once somebody the-populated-player had blocked; now a player "
        "seated in her played history, and blocked by nobody."
    ),
    sports=(Sport.PADEL,),
)

THEY_BLOCKED_YOU: Final = _account(
    "they-blocked-you",
    (
        "Once somebody who had blocked the-populated-player; now a player "
        "seated in her played history, and blocking nobody."
    ),
    sports=(Sport.PADEL,),
)

YOU_PASSED_THEM: Final = _account(
    "you-passed-them",
    (
        "Once somebody the-populated-player passed on in her deck; now a "
        "player seated in her played history."
    ),
    sports=(Sport.PADEL,),
)

#: The eleven as written. ``_dealt`` below deals each its own level.
_AS_WRITTEN: tuple[SeedAccount, ...] = (
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


def _dealt(accounts: tuple[SeedAccount, ...]) -> tuple[SeedAccount, ...]:
    """The eleven, **dealt one answer set each out of the band they all claim.**

    ``_account`` builds every one of them on ``MIDDLING``, and eleven people at
    one level are clones: on a court together they tie, and every forecast
    between them reads the same.

    So the level is dealt here rather than declared at each of the eleven. Dealt
    **by position in a sorted list of slugs**, which is what makes this a deal
    and not a draw: eight policies over eleven accounts, each used once before
    any is used twice, and no two accounts landing on one level by chance the way
    a keyed pick did. Sorted, so the deal is a function of *which slugs exist*
    rather than of the order they happen to be written in above — an account
    inserted in the middle of the tuple moves nobody it does not have to move.

    Every policy dealt lands inside ``THE_PROTAGONISTS_BAND``, so each account is
    still held to the claim it was always held to, and ``THE_BAND_FROM_WITHIN``
    is where that is argued.
    """

    order = sorted(one.slug for one in accounts)
    return tuple(
        replace(
            one,
            scenarios=tuple(
                replace(
                    run,
                    answers=THE_BAND_FROM_WITHIN[
                        order.index(one.slug) % len(THE_BAND_FROM_WITHIN)
                    ],
                )
                if isinstance(run, RatedRun)
                else run
                for run in one.scenarios
            ),
        )
        for one in accounts
    )


#: The accounts, for the registration walk, each dealt its level.
RELATIONSHIP_ACCOUNTS: Final[tuple[SeedAccount, ...]] = _dealt(_AS_WRITTEN)

# **Named here and out of this module's own surnames**, because ``catalog.py``
# cannot see this list and a shared pool would eventually seat two people under
# one nickname. `name_them` refuses that rather than leaving it to the unique
# constraint half way through a run.
name_them(RELATIONSHIP_ACCOUNTS, RELATIONSHIP_SURNAMES)
refuse_an_account_nobody_named(RELATIONSHIP_ACCOUNTS)


# ---------------------------------------------------------------------------
# Refusals, at import
# ---------------------------------------------------------------------------


def _refuse_an_impossible_layer() -> None:
    """Fail at import rather than part-way through a run."""

    # **Across both lists and not within this one.** The runner walks
    # ``ACCOUNTS + RELATIONSHIP_ACCOUNTS`` through one registration, and an
    # address is derived from a slug — so a name shared with the catalog is a
    # collision neither file could see alone, met half way through a run at the
    # second registration for one address.
    refuse_two_accounts_at_one_name(list(ACCOUNTS) + list(RELATIONSHIP_ACCOUNTS))
    for account in RELATIONSHIP_ACCOUNTS:
        refuse_an_impossible_account(account)
    if PROTAGONIST.slug in {account.slug for account in RELATIONSHIP_ACCOUNTS}:
        raise RuntimeError(
            f"'{PROTAGONIST.slug}' is the protagonist and cannot also be one of "
            f"the accounts it is in a relationship with."
        )
    for account in RELATIONSHIP_ACCOUNTS:
        rated = {
            scenario.sport
            for scenario in account.scenarios
            if isinstance(scenario, RatedRun)
        }
        if Sport.PADEL not in rated:
            raise RuntimeError(
                f"'{account.slug}' holds no padel rating, and her played courts "
                f"are padel."
            )


_refuse_an_impossible_layer()
