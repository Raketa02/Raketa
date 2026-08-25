"""The Social tag vocabulary: eighteen ids, three groups, closed.

A player describes what kind of player they are by holding **2 to 6** of these
(``../../../../CONTEXT.md``). The vocabulary is *closed and platform-owned* —
never free text, never player-authored, never imported from another platform,
and never about the person rather than the game. Age, looks, body and "looking
for" belong to a different product.

**Ids are permanent.** They are persisted on accounts, so retiring a tag means
hiding it from the picker while continuing to honour it on the profiles that
already hold it — never reusing an id, never renaming one. That is why the id
and the *label* are different things: the id crosses the wire and is stored
forever, while the human-readable label is the client's own copy, in the
client's own language (``docs/adr/0022`` — the backend emits machine codes and
never display text).

This module is the vocabulary's **one home**. It is served read-only over the
player API, following the precedent ``SportSpec`` set at ``GET /api/v1/sports``
*"so neither client hardcodes it"* (``docs/adr/0089``) — because a second copy in
a client is exactly how the onboarding picker and the profile editor drift into
two different lists.

    AFTER_THE_MATCH     how a player is once the game is over
    ON_THE_COURT        what they are like while it is going on
    WHY_YOU_ARE_HERE    what they came for

**Where these eighteen came from.** The ticket that asked for this endpoint said
the eighteen were in its parent spec. They were not — the parent named the three
groups and the count, and the source documents it read them from went in the
2026-08-25 reset. So the ids below were composed here, to the glossary's rule
that a tag is about the game and never about the person, and then put to product
as a decision rather than left standing as an assumption.

**Product approved them as they stand, on 2026-08-25** — the equal six-per-group
split included, which the parent never specified either. That happened while the
list was still cheap: the profile commit had not shipped, no profile held an id,
and a replacement was an edit to this file, two tests and the contract. It is not
cheap any more. From here an id is honoured forever, so changing the vocabulary
means retiring an id and adding another beside it — never editing a line below.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Mapping

from app.kernel import invariant


class SocialTagGroup(str, Enum):
    """The three groups, which are about the game and nothing else."""

    AFTER_THE_MATCH = "AFTER_THE_MATCH"
    ON_THE_COURT = "ON_THE_COURT"
    WHY_YOU_ARE_HERE = "WHY_YOU_ARE_HERE"


class SocialTag(str, Enum):
    """The closed set of tag ids. An id here is permanent."""

    # After the match
    STAYS_FOR_A_DRINK = "STAYS_FOR_A_DRINK"
    STRAIGHT_HOME_AFTER = "STRAIGHT_HOME_AFTER"
    TALKS_THROUGH_THE_MATCH = "TALKS_THROUGH_THE_MATCH"
    SETTLES_UP_ON_THE_SPOT = "SETTLES_UP_ON_THE_SPOT"
    BOOKS_THE_NEXT_ONE = "BOOKS_THE_NEXT_ONE"
    SHARES_A_LIFT = "SHARES_A_LIFT"

    # On the court
    PLAYS_TO_WIN = "PLAYS_TO_WIN"
    LAUGHS_OFF_MISTAKES = "LAUGHS_OFF_MISTAKES"
    ENCOURAGES_A_PARTNER = "ENCOURAGES_A_PARTNER"
    GENEROUS_ON_LINE_CALLS = "GENEROUS_ON_LINE_CALLS"
    QUIET_AND_FOCUSED = "QUIET_AND_FOCUSED"
    WARMS_UP_PROPERLY = "WARMS_UP_PROPERLY"

    # Why you are here
    HERE_TO_IMPROVE = "HERE_TO_IMPROVE"
    HERE_TO_COMPETE = "HERE_TO_COMPETE"
    HERE_FOR_THE_EXERCISE = "HERE_FOR_THE_EXERCISE"
    HERE_TO_MEET_PLAYERS = "HERE_TO_MEET_PLAYERS"
    HERE_FOR_A_REGULAR_GAME = "HERE_FOR_A_REGULAR_GAME"
    HERE_TO_GET_BACK_INTO_IT = "HERE_TO_GET_BACK_INTO_IT"


#: The vocabulary as it is served: groups in order, tags in order within each.
#: Both orders are part of the contract — the picker renders what it is given
#: rather than sorting, so moving a tag between groups or reordering one is a
#: visible change to every client, not an implementation detail.
SOCIAL_TAG_VOCABULARY: Mapping[SocialTagGroup, tuple[SocialTag, ...]] = (
    MappingProxyType(
        {
            SocialTagGroup.AFTER_THE_MATCH: (
                SocialTag.STAYS_FOR_A_DRINK,
                SocialTag.STRAIGHT_HOME_AFTER,
                SocialTag.TALKS_THROUGH_THE_MATCH,
                SocialTag.SETTLES_UP_ON_THE_SPOT,
                SocialTag.BOOKS_THE_NEXT_ONE,
                SocialTag.SHARES_A_LIFT,
            ),
            SocialTagGroup.ON_THE_COURT: (
                SocialTag.PLAYS_TO_WIN,
                SocialTag.LAUGHS_OFF_MISTAKES,
                SocialTag.ENCOURAGES_A_PARTNER,
                SocialTag.GENEROUS_ON_LINE_CALLS,
                SocialTag.QUIET_AND_FOCUSED,
                SocialTag.WARMS_UP_PROPERLY,
            ),
            SocialTagGroup.WHY_YOU_ARE_HERE: (
                SocialTag.HERE_TO_IMPROVE,
                SocialTag.HERE_TO_COMPETE,
                SocialTag.HERE_FOR_THE_EXERCISE,
                SocialTag.HERE_TO_MEET_PLAYERS,
                SocialTag.HERE_FOR_A_REGULAR_GAME,
                SocialTag.HERE_TO_GET_BACK_INTO_IT,
            ),
        }
    )
)


def _validate_vocabulary() -> None:
    """Refuse to import a vocabulary that has drifted from its own enum.

    The enum and the grouping are two lists of the same eighteen things, so they
    can disagree: a tag added to the enum and forgotten here would be a legal id
    that no picker ever shows, and one listed twice would render twice. Checked
    on import rather than in a test alone, because the failure it prevents is a
    tag id that exists on the wire and in nobody's picker.
    """

    grouped = [tag for tags in SOCIAL_TAG_VOCABULARY.values() for tag in tags]
    invariant(
        len(grouped) == len(set(grouped)),
        f"a social tag is grouped more than once: {grouped}",
    )
    missing = sorted(tag.value for tag in SocialTag if tag not in set(grouped))
    invariant(not missing, f"social tags in no group: {missing}")
    invariant(
        tuple(SOCIAL_TAG_VOCABULARY) == tuple(SocialTagGroup),
        f"the vocabulary's groups are not the group enum: "
        f"{list(SOCIAL_TAG_VOCABULARY)}",
    )


_validate_vocabulary()
