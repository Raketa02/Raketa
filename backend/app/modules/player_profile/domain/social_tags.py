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

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from app.kernel import invariant
from app.modules.player_profile.domain.errors import (
    DuplicateSocialTag,
    SocialTagSelectionOutOfBounds,
    UnknownSocialTag,
)


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


@dataclass(frozen=True)
class SocialTagSelectionBounds:
    """How many tags a selection must hold to be one.

    The unit is in both field names for the reason it is on the radius bounds: a
    bare ``minimum`` beside a vocabulary of eighteen reads as a count of
    something, and which something is exactly what a client would guess wrong.
    """

    minimum_tags: int
    maximum_tags: int

    #: The range may collapse — ``minimum_tags == maximum_tags`` is "exactly N
    #: tags", a rule a product could hold. That is the one deliberate departure
    #: from ``SearchRadiusBounds``, which refuses a collapsed range because a
    #: slider with one position is a control with nothing to do.

    def __post_init__(self) -> None:
        invariant(
            self.minimum_tags >= 0,
            f"social tag floor: {self.minimum_tags}",
        )
        invariant(
            self.minimum_tags <= self.maximum_tags,
            f"social tag range: {self.minimum_tags}–{self.maximum_tags}",
        )

    def contains(self, tag_count: int) -> bool:
        """Is this a number of tags a player is allowed to hold?

        Both ends included. It lives here rather than at the call site so that
        the endpoint serving the numbers and the commit re-validating against
        them cannot answer differently.
        """

        return self.minimum_tags <= tag_count <= self.maximum_tags


#: The served floor and ceiling. A change here changes what every client's
#: picker allows and what the profile commit accepts, in one release and without
#: an app-store one.
#:
#: Product confirmed **2 to 6** on 2026-08-25, the same day as the vocabulary
#: itself. Unlike a tag id these are not on a clock: nothing persists a bound, so
#: a later opinion is an edit here rather than a retirement.
SOCIAL_TAG_SELECTION_BOUNDS = SocialTagSelectionBounds(
    minimum_tags=2,
    maximum_tags=6,
)


@dataclass(frozen=True, slots=True)
class SocialTagSelection:
    """The tags one player holds: between the floor and the ceiling, no repeats.

    Built through ``of`` or ``from_ids``, never directly, so that no caller holds
    a selection in its own order. The order is the **vocabulary's**, which means
    two players who picked the same tags hold equal selections whatever order
    their pickers sent them in, and a stored selection reads the way the picker
    renders it.

    **This is where the served bounds are re-validated, and it has to be here.**
    The floor and the ceiling are published at ``GET /player-profile/options`` so
    a picker can grey out its confirm control, and a disabled button is not a
    validation (``docs/adr/0089``) — it is absent from a replayed request, an
    older build, and anything that is not the app.
    """

    tags: tuple[SocialTag, ...]

    def __post_init__(self) -> None:
        invariant(
            list(self.tags) == _in_vocabulary_order(set(self.tags)),
            "a social tag selection was built outside `of`",
        )

    @classmethod
    def of(cls, tags: Iterable[SocialTag]) -> "SocialTagSelection":
        """The selection these tags make, or a refusal naming which rule broke.

        Duplicates are **refused** rather than dropped, which is the opposite of
        what an availability grid does with a repeated slot — deliberately. A
        grid is a set of cells and a cell ticked twice is ticked; a selection is
        counted against a floor and a ceiling, so silently collapsing three ids
        into two would refuse a player for a mistake their client made and tell
        them they picked too few.
        """

        chosen = tuple(tags)
        unique = set(chosen)
        if len(unique) != len(chosen):
            raise DuplicateSocialTag()
        if not SOCIAL_TAG_SELECTION_BOUNDS.contains(len(unique)):
            raise SocialTagSelectionOutOfBounds()
        return cls(tags=tuple(_in_vocabulary_order(unique)))

    @classmethod
    def from_ids(cls, ids: Iterable[str]) -> "SocialTagSelection":
        """The selection these wire ids make, refusing any the vocabulary lacks.

        An id this platform does not serve is refused with its own code rather
        than folded into "invalid selection", because the two ask the client for
        different things: too many tags is a picker that let the player overfill,
        an unknown id is a picker working from a vocabulary this release no
        longer serves, and the recovery for that one is to re-read the options.
        """

        tags: list[SocialTag] = []
        for value in ids:
            try:
                tags.append(SocialTag(value))
            except ValueError as exc:
                raise UnknownSocialTag() from exc
        return cls.of(tags)

    @property
    def ids(self) -> tuple[str, ...]:
        """The selection as a stream stores it and the wire carries it."""

        return tuple(tag.value for tag in self.tags)

    def __len__(self) -> int:
        return len(self.tags)


def _in_vocabulary_order(tags: Iterable[SocialTag]) -> list[SocialTag]:
    """`tags` arranged as the vocabulary declares them, groups included.

    Reads ``SOCIAL_TAG_VOCABULARY`` rather than the enum, so the one order that
    is part of the contract is the one order a selection is stored in.
    """

    held = set(tags)
    return [
        tag
        for grouped in SOCIAL_TAG_VOCABULARY.values()
        for tag in grouped
        if tag in held
    ]


def _validate_vocabulary() -> None:
    """Refuse to import a vocabulary that has drifted from its own enum.

    The enum and the grouping are two lists of the same eighteen things, so they
    can disagree: a tag added to the enum and forgotten here would be a legal id
    that no picker ever shows, and one listed twice would render twice. Checked
    on import rather than in a test alone, because the failure it prevents is a
    tag id that exists on the wire and in nobody's picker.

    The ceiling is checked against the same list, because a ceiling above the
    vocabulary is a rule no player could break and a counter that never fills.
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
    invariant(
        SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags <= len(grouped),
        f"the social tag ceiling is above the vocabulary: "
        f"{SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags} of {len(grouped)}",
    )


_validate_vocabulary()
