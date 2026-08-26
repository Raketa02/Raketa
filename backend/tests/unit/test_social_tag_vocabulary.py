"""The Social tag vocabulary: nineteen permanent ids, three groups, one home.

Two claims are load-bearing here and neither is about behaviour.

**Ids are permanent**, because they are persisted on profiles forever. So they
are written out *in this file* rather than read from the module under test: a
test that reads the constant it is checking passes just as happily after a
rename, which is precisely the change that must not happen quietly. Retiring a
tag means dropping it from the served vocabulary and continuing to honour it on
the profiles that hold it — and that change should redden this file, be argued
with, and then be made here too. **Adding one should redden it too**, which is
what happened on 2026-08-26 when ``OPEN_TO_MEET_SOMEONE`` was appended to
``WHY_YOU_ARE_HERE`` — an addition rather than an edit, with nothing above it
moved and nothing retired.

**The closed-vocabulary tripwire below was not widened to admit it**, and must
not be for anything else either: an id that needs the guard relaxed is an id that
belongs to a different product.

**The vocabulary has one home**, so the last test walks the source for a second
copy. A string literal equal to a tag id anywhere else in ``app/`` is the drift
this ticket exists to prevent; referring to the enum member is not.

One mutation survives this file and is reported rather than papered over:
deleting the ``_validate_vocabulary()`` call at the bottom of the module leaves
the suite green, because every property that call enforces is asserted here
directly. The call is still worth its line — it turns "a tag id nobody's picker
shows" into an import that refuses — but nothing here is what proves it runs.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagGroup,
)

ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_MODULE = (
    ROOT / "app" / "modules" / "player_profile" / "domain" / "social_tags.py"
)

# The contract, written out: the three groups in the order they are served, each
# with its tags in the order they are rendered.
EXPECTED: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "AFTER_THE_MATCH",
        (
            "STAYS_FOR_A_DRINK",
            "STRAIGHT_HOME_AFTER",
            "TALKS_THROUGH_THE_MATCH",
            "SETTLES_UP_ON_THE_SPOT",
            "BOOKS_THE_NEXT_ONE",
            "SHARES_A_LIFT",
        ),
    ),
    (
        "ON_THE_COURT",
        (
            "PLAYS_TO_WIN",
            "LAUGHS_OFF_MISTAKES",
            "ENCOURAGES_A_PARTNER",
            "GENEROUS_ON_LINE_CALLS",
            "QUIET_AND_FOCUSED",
            "WARMS_UP_PROPERLY",
        ),
    ),
    (
        "WHY_YOU_ARE_HERE",
        (
            "HERE_TO_IMPROVE",
            "HERE_TO_COMPETE",
            "HERE_FOR_THE_EXERCISE",
            "HERE_TO_MEET_PLAYERS",
            "HERE_FOR_A_REGULAR_GAME",
            "HERE_TO_GET_BACK_INTO_IT",
            "OPEN_TO_MEET_SOMEONE",
        ),
    ),
)

EXPECTED_IDS = frozenset(tag for _, tags in EXPECTED for tag in tags)


def test_the_vocabulary_is_exactly_these_ids_in_their_served_order():
    served = tuple(
        (group.value, tuple(tag.value for tag in tags))
        for group, tags in SOCIAL_TAG_VOCABULARY.items()
    )
    assert served == EXPECTED


def test_there_are_nineteen_tags_in_three_groups():
    # The groups are not evenly sized and never had to be: what was specified is
    # the three groups, and nothing renders a group's count. The even split the
    # first eighteen happened to have ended when the nineteenth was appended.
    assert len(SocialTag) == 19
    assert len(SocialTagGroup) == 3
    assert sum(len(tags) for tags in SOCIAL_TAG_VOCABULARY.values()) == 19


def test_every_tag_belongs_to_exactly_one_group():
    grouped = [tag for tags in SOCIAL_TAG_VOCABULARY.values() for tag in tags]
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == set(SocialTag)


def test_an_id_is_its_own_name_so_a_rename_cannot_be_silent():
    # The wire value and the Python name are the same string. A member renamed
    # without its value would otherwise keep serving the old id, which reads as
    # a rename that worked.
    for tag in SocialTag:
        assert tag.value == tag.name
    for group in SocialTagGroup:
        assert group.value == group.name


def test_the_vocabulary_is_closed_to_the_person_rather_than_the_game():
    # The glossary's rule, held structurally: age, looks, body and "looking for"
    # are a different product's vocabulary. Not a spell-check — a tripwire for
    # the day somebody adds one without reading the invariant.
    #
    # Matched on whole words rather than substrings, which is not fastidiousness:
    # the substring spelling fails on `ENCOURAGES_A_PARTNER`, which contains
    # "AGE" and is about the game.
    forbidden = {"AGE", "AGED", "LOOKS", "BODY", "HEIGHT", "SINGLE", "DATE", "DATING"}
    for tag in SocialTag:
        words = set(tag.value.split("_"))
        assert not words & forbidden, tag.value
        assert "LOOKING_FOR" not in tag.value, tag.value


def _string_literals(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def test_no_second_copy_of_a_tag_id_exists_anywhere_in_the_app():
    modules = sorted((ROOT / "app").rglob("*.py"))
    # A glob that matches nothing passes silently, so the count is asserted
    # rather than trusted.
    assert len(modules) > 100, modules
    assert VOCABULARY_MODULE in modules

    offenders = {}
    for path in modules:
        if path == VOCABULARY_MODULE:
            continue
        copied = _string_literals(path) & EXPECTED_IDS
        if copied:
            offenders[str(path.relative_to(ROOT))] = sorted(copied)

    assert offenders == {}, f"a tag id is spelled outside its one home: {offenders}"
