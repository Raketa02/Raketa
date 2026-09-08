"""The two evidence unions are one vocabulary in two files, and may not drift.

``challenges`` may not import the matcher, so the scored terms on a challenge
detail carry their evidence in that context's own copy of the union
(``docs/adr/0143`` §5, on ``origins.py``'s argument). **The import is the thing
the fence forbids, so the guard is a test rather than an assertion in the code** —
which is what ``games_match_history.py`` does for its own duplicated constant,
one kind of duplication over.

What is compared is the **shape**, variant by variant: the kinds, the field
names, and the JSON schema each one generates. What is deliberately *not*
compared is the class names — the challenge copy is prefixed ``Court`` so that
two models of one name do not collide into module-path-qualified types in the
OpenAPI document, and ``docs/adr/0143`` records that the client generating two
types for what a designer sees as one component is the cost being paid.

**A failure here is a real one.** A variant grown on one side and not the other
publishes a kind one client can draw and the other cannot, on the one screen
whose entire promise is that it shows its working — where a missing reason line
looks identical to a term that stood down.
"""

from __future__ import annotations

import pytest

from app.modules.challenges.presentation.evidence import (
    COURT_EVIDENCE_KINDS,
    COURT_EVIDENCE_VARIANTS,
)
from app.modules.matchmaking.presentation.evidence import (
    EVIDENCE_VARIANTS,
    WIRE_EVIDENCE_KINDS,
)

#: The prefix the challenge copy carries, and the whole of what may differ
#: between the two class names.
PREFIX = "Court"

_PAIRS = list(zip(EVIDENCE_VARIANTS, COURT_EVIDENCE_VARIANTS, strict=True))


def _named(variant) -> str:
    return variant.__name__


def _schema(variant) -> dict:
    """One variant's JSON schema, with the names of nested models normalised.

    The ``$ref`` targets and the model titles carry the ``Court`` prefix, which
    is the one difference this file is asserting is the *only* difference — so
    they are stripped before the comparison rather than compared and excused.
    """

    import json

    text = json.dumps(variant.model_json_schema(), sort_keys=True)
    return json.loads(text.replace(PREFIX, ""))


def test_both_unions_publish_the_same_kinds():
    """The discriminator's whole value set, which is what a client dispatches on."""

    assert COURT_EVIDENCE_KINDS == WIRE_EVIDENCE_KINDS


def test_the_two_unions_hold_the_same_variants_in_the_same_order():
    """Order as well as membership, because both files enumerate the union for
    code to read and a reader comparing them by eye reads them in order."""

    assert [_named(one) for one in COURT_EVIDENCE_VARIANTS] == [
        PREFIX + _named(one) for one in EVIDENCE_VARIANTS
    ]


@pytest.mark.parametrize(
    "matcher_variant,court_variant",
    _PAIRS,
    ids=[_named(one) for one in EVIDENCE_VARIANTS],
)
def test_each_variant_is_the_same_shape_in_both_files(
    matcher_variant, court_variant
):
    """Field for field, type for type, constraint for constraint.

    A variant that grew a field on one side is a payload one client can read and
    the other silently drops — which is the failure mode the closed union exists
    to make impossible in the first place.
    """

    assert set(matcher_variant.model_fields) == set(court_variant.model_fields)
    assert _schema(matcher_variant) == _schema(court_variant)
