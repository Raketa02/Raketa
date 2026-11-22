"""The Social tag vocabulary: twenty-seven ids, three groups, closed.

A player describes what kind of player they are by holding **2 to 8** of these
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

**A nineteenth was added on 2026-08-26: ``OPEN_TO_MEET_SOMEONE``**, at the end of
``WHY_YOU_ARE_HERE``. It is an addition and not an edit — nothing above it moved,
nothing was retired — which is the one shape of change this vocabulary permits.
The even six-per-group split goes with it, and was never a rule: what the parent
specified was the three groups, and nothing renders a group's count.

Two things about it are worth writing down rather than leaving to be
rediscovered. **It sits at the edge of this module's own rule** — a tag is about
the game, never about the person — and it is the closest any id comes to that
line, because *meeting someone* is a reason for being here rather than a way of
playing. It is on the game side of the line as written: it is a **motive**, which
is what ``WHY_YOU_ARE_HERE`` collects, it is player-stated rather than inferred,
and it claims nothing about anybody's age, looks or body. The tripwire in
``tests/unit/test_social_tag_vocabulary.py`` was not touched or widened to admit
it, and it must not be: an id that needs the guard relaxed is an id that belongs
to a different product.

**It is deliberately not ``HERE_TO_MEET_PLAYERS``**, which it sits beside. That
one is about finding people to play with; this one is not, and folding the two
would take a distinction a player drew and discard it. Both stand.

**Eight more were added on 2026-11-22** (``docs/adr/0207`` §7, #829), because
nineteen were too few to say who a player is to play with once tags build the
For-fun tables: a coffee rather than a drink, new in town, patient with
beginners. Each was appended at the end of its group — nothing above moved and
nothing was retired — which makes 27: After the match 9, On the court 10, Why
you're here 8. Each is about the game, and none needed the tripwire touched:

- ``STAYS_FOR_A_COFFEE`` and ``UP_FOR_A_BITE_AFTER`` — what a player does once
  the match is over, as ``STAYS_FOR_A_DRINK`` is. A coffee is not a drink, and
  the two earn no credit for each other (``docs/adr/0207`` §2).
- ``KEEPS_IN_TOUCH`` — whether the people from one game hear from them before
  the next, which is how a game becomes a regular one.
- ``HAPPY_TO_SWAP_PARTNERS`` — how they play a doubles evening: sides change.
- ``PATIENT_WITH_BEGINNERS`` and ``HAPPY_TO_SHARE_TIPS`` — how they are with
  a weaker player on their court. Neither is a level claim: the Skill rating
  says how anybody hits, and these say how somebody plays beside it.
- ``BRINGS_THE_ENERGY`` — what they are like while it is going on, beside
  ``QUIET_AND_FOCUSED`` at the other end.
- ``NEW_IN_TOWN`` — a **motive**, what ``WHY_YOU_ARE_HERE`` collects: they came
  to find a game in a place where they don't have one yet. It says where they
  stand with the city's courts, never where they are from.

Struck in the same session, on this module's rule: a level claim (*Just starting
out*), an intent (*Here for fun* — a tag is not a Play intent), a reliability
claim (*Always on time* — Player Score measures it), and anything about age,
family, job, looks, nationality or language; and *Sticks around to watch* and
*Here to unwind*.
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
    STAYS_FOR_A_COFFEE = "STAYS_FOR_A_COFFEE"
    UP_FOR_A_BITE_AFTER = "UP_FOR_A_BITE_AFTER"
    KEEPS_IN_TOUCH = "KEEPS_IN_TOUCH"

    # On the court
    PLAYS_TO_WIN = "PLAYS_TO_WIN"
    LAUGHS_OFF_MISTAKES = "LAUGHS_OFF_MISTAKES"
    ENCOURAGES_A_PARTNER = "ENCOURAGES_A_PARTNER"
    GENEROUS_ON_LINE_CALLS = "GENEROUS_ON_LINE_CALLS"
    QUIET_AND_FOCUSED = "QUIET_AND_FOCUSED"
    WARMS_UP_PROPERLY = "WARMS_UP_PROPERLY"
    HAPPY_TO_SWAP_PARTNERS = "HAPPY_TO_SWAP_PARTNERS"
    PATIENT_WITH_BEGINNERS = "PATIENT_WITH_BEGINNERS"
    HAPPY_TO_SHARE_TIPS = "HAPPY_TO_SHARE_TIPS"
    BRINGS_THE_ENERGY = "BRINGS_THE_ENERGY"

    # Why you are here
    HERE_TO_IMPROVE = "HERE_TO_IMPROVE"
    HERE_TO_COMPETE = "HERE_TO_COMPETE"
    HERE_FOR_THE_EXERCISE = "HERE_FOR_THE_EXERCISE"
    HERE_TO_MEET_PLAYERS = "HERE_TO_MEET_PLAYERS"
    HERE_FOR_A_REGULAR_GAME = "HERE_FOR_A_REGULAR_GAME"
    HERE_TO_GET_BACK_INTO_IT = "HERE_TO_GET_BACK_INTO_IT"
    OPEN_TO_MEET_SOMEONE = "OPEN_TO_MEET_SOMEONE"
    NEW_IN_TOWN = "NEW_IN_TOWN"


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
                SocialTag.STAYS_FOR_A_COFFEE,
                SocialTag.UP_FOR_A_BITE_AFTER,
                SocialTag.KEEPS_IN_TOUCH,
            ),
            SocialTagGroup.ON_THE_COURT: (
                SocialTag.PLAYS_TO_WIN,
                SocialTag.LAUGHS_OFF_MISTAKES,
                SocialTag.ENCOURAGES_A_PARTNER,
                SocialTag.GENEROUS_ON_LINE_CALLS,
                SocialTag.QUIET_AND_FOCUSED,
                SocialTag.WARMS_UP_PROPERLY,
                SocialTag.HAPPY_TO_SWAP_PARTNERS,
                SocialTag.PATIENT_WITH_BEGINNERS,
                SocialTag.HAPPY_TO_SHARE_TIPS,
                SocialTag.BRINGS_THE_ENERGY,
            ),
            SocialTagGroup.WHY_YOU_ARE_HERE: (
                SocialTag.HERE_TO_IMPROVE,
                SocialTag.HERE_TO_COMPETE,
                SocialTag.HERE_FOR_THE_EXERCISE,
                SocialTag.HERE_TO_MEET_PLAYERS,
                SocialTag.HERE_FOR_A_REGULAR_GAME,
                SocialTag.HERE_TO_GET_BACK_INTO_IT,
                # Appended, never inserted: the order within a group is part of
                # the contract, and moving an existing tag is a visible change to
                # every picker that has already rendered it.
                SocialTag.OPEN_TO_MEET_SOMEONE,
                SocialTag.NEW_IN_TOWN,
            ),
        }
    )
)


#: **The tags that never count** — in a For-fun table's Social vibe, or in
#: building one (``docs/adr/0207`` §2). Each is still a tag a player holds, shown
#: wherever their tags are shown, the Social vibe card's grid included; it simply
#: earns nothing at a table. ``OPEN_TO_MEET_SOMEONE`` is the one, because it sits
#: at the edge of this vocabulary's rule (above): counting it would seat people
#: together because of that motive, and For fun is a game, never a matchmaker.
UNCOUNTED_SOCIAL_TAGS: frozenset[SocialTag] = frozenset(
    {SocialTag.OPEN_TO_MEET_SOMEONE}
)


def counted(tags: Iterable[SocialTag]) -> frozenset[SocialTag]:
    """The tags a player holds that count at a table — every one but
    ``UNCOUNTED_SOCIAL_TAGS``, removed here before the Match Fit engine is
    asked, so every context that asks it removes the same ones."""

    return frozenset(tags) - UNCOUNTED_SOCIAL_TAGS


@dataclass(frozen=True)
class SocialTagSelectionBounds:
    """How many tags a selection must hold to be one.

    The unit is in both field names: a bare ``minimum`` beside a vocabulary of
    twenty-seven reads as a count of something, and which something is exactly
    what a client would guess wrong.
    """

    minimum_tags: int
    maximum_tags: int

    #: The range may collapse — ``minimum_tags == maximum_tags`` is "exactly N
    #: tags", a rule a product could hold.

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
#: a later opinion is an edit here rather than a retirement — and the first was,
#: on 2026-11-22: **2 to 8**, with the eight tags appended above
#: (``docs/adr/0207`` §7). A selection of up to six recorded before it still
#: folds, and is still one a player may choose.
SOCIAL_TAG_SELECTION_BOUNDS = SocialTagSelectionBounds(
    minimum_tags=2,
    maximum_tags=8,
)


@dataclass(frozen=True, slots=True)
class SocialTagSelection:
    """The tags one player holds: between the floor and the ceiling, no repeats.

    Built through ``of`` or ``from_ids``, never directly, so that no caller holds
    a selection in its own order. The order is the **vocabulary's**, which means
    two players who picked the same tags hold equal selections whatever order
    their pickers sent them in, and a stored selection reads the way the picker
    renders it.

    **The floor and the ceiling are not an invariant of this type**, and that is
    deliberate. ``chosen`` refuses a selection outside them; ``recorded`` does
    not, because a selection *already on a stream* was legal when it was written
    and stays a fact whatever the bounds say today. The bounds are documented as
    editable — *"a later opinion is an edit here"* — so a type that asserted them
    would make lowering the ceiling retroactively un-rehydrate every profile
    above the new one, and the first symptom would be `GET /users/me` failing for
    real players. **The write path refuses; the fold accepts.**

    What *is* an invariant of the type is the ordering: a selection is always
    held in the vocabulary's own order, so two players who picked the same tags
    hold equal selections whatever order their pickers sent them in, and a stored
    selection reads the way the picker renders it.
    """

    tags: tuple[SocialTag, ...]

    def __post_init__(self) -> None:
        invariant(
            list(self.tags) == _in_vocabulary_order(set(self.tags)),
            "a social tag selection was built outside `chosen` or `recorded`",
        )

    @classmethod
    def chosen(cls, tags: Iterable[SocialTag]) -> "SocialTagSelection":
        """A selection a player just made, checked against the served bounds.

        **This is where the served bounds are re-validated, and it has to be
        here.** The floor and the ceiling are published at
        ``GET /player-profile/options`` so a picker can grey out its confirm
        control, and a disabled button is not a validation (``docs/adr/0089``) —
        it is absent from a replayed request, an older build, and anything that
        is not the app.

        Duplicates are **refused** rather than dropped, which is the opposite of
        what a week of hours does with a repeated hour — deliberately. A
        week is a set of hours and an hour ticked twice is ticked; a selection is
        counted against a floor and a ceiling, so silently collapsing three ids
        into two would refuse a player for a mistake their client made and tell
        them they picked too few.
        """

        picked = tuple(tags)
        unique = set(picked)
        if len(unique) != len(picked):
            raise DuplicateSocialTag()
        if not SOCIAL_TAG_SELECTION_BOUNDS.contains(len(unique)):
            raise SocialTagSelectionOutOfBounds()
        return cls(tags=tuple(_in_vocabulary_order(unique)))

    @classmethod
    def from_ids(cls, ids: Iterable[str]) -> "SocialTagSelection":
        """A selection from wire ids, refusing any the vocabulary lacks.

        An id this platform does not serve is refused with its own code rather
        than folded into "invalid selection", because the two ask the client for
        different things: too many tags is a picker that let the player overfill,
        an unknown id is a picker working from a vocabulary this release no
        longer serves, and the recovery for that one is to re-read the options.
        """

        return cls.chosen(_parsed(ids))

    @classmethod
    def recorded(cls, ids: Iterable[str]) -> "SocialTagSelection":
        """A selection read back off a stream. **Not re-counted.**

        The ids themselves are still parsed, and an unparseable one still raises
        — but that is not the same hazard: **a tag id is permanent**, never
        reused and never renamed, so an id on a stream is an id this enum still
        holds. A failure here means that invariant was broken, which is a bug to
        hear about rather than a bound somebody moved.
        """

        return cls(tags=tuple(_in_vocabulary_order(_parsed(ids))))

    @property
    def ids(self) -> tuple[str, ...]:
        """The selection as a stream stores it and the wire carries it."""

        return tuple(tag.value for tag in self.tags)

    def __len__(self) -> int:
        return len(self.tags)


def _parsed(ids: Iterable[str]) -> list[SocialTag]:
    """Wire ids as tags, refusing any this platform does not serve."""

    tags: list[SocialTag] = []
    for value in ids:
        try:
            tags.append(SocialTag(value))
        except ValueError as exc:
            raise UnknownSocialTag() from exc
    return tags


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

    The enum and the grouping are two lists of the same tags, so they can
    disagree: a tag added to the enum and forgotten here would be a legal id that
    no picker ever shows, and one listed twice would render twice. Checked on
    import rather than in a test alone, because the failure it prevents is a tag
    id that exists on the wire and in nobody's picker.

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
