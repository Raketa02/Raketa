"""The shortlist's wire shape — the two spellings of absence, and the closed sets.

``docs/adr/0106`` §4 gives absence two spellings and they are not
interchangeable:

- **omitted** — *this field does not apply here* — generates as ``field?: T``;
- **``null``** — *this field applies, and the answer is a measured nothing that
  is itself a recorded fact* — generates as ``field: T | null``.

A field that was both generates as ``field?: T | null`` and says neither thing.
This module refuses one, and it refuses it on the emitted schema rather than on a
review, because the two are one keystroke apart in a model definition.

It also pins the two vocabularies this route introduces. A closed set the client
generates an exhaustive renderer over is only closed while something checks it —
and the failure is **silent**: a code the client has never seen renders as
nothing at all, on the one screen whose whole promise is showing its working.
"""

from __future__ import annotations

from types import NoneType, UnionType
from typing import Union, get_args, get_origin

import pytest
from pydantic import BaseModel

from app.engines.matchfit.core import ChallengeLoad, LivenessSignal
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.domain.searches import InclusionReason
from app.modules.player_profile.presentation.schemas import AvailabilitySlotResource
from app.modules.matchmaking.presentation.schemas import (
    OMITTED,
    CandidateSchema,
    LivenessReason,
    ModifierCode,
    PlayerCardSchema,
    PromptSchema,
    RunSearchRequest,
    RungOfferSchema,
    SearchEnvelope,
    ShortlistResponse,
    WireInclusionReason,
    WithheldRowSchema,
)

#: Every model on this route, so a model added without a rule is a model this
#: file walks anyway.
MODELS: tuple[type[BaseModel], ...] = (
    ShortlistResponse,
    SearchEnvelope,
    CandidateSchema,
    WithheldRowSchema,
    PlayerCardSchema,
    RunSearchRequest,
)

#: The fields that mean *this does not apply here*, and why each does.
OMITTED_FIELDS = {
    (CandidateSchema, "distance_km"): "the distance term stood down",
    (CandidateSchema, "inclusion_reason"): "nothing admitted them; they simply fit",
    (CandidateSchema, "at_stake"): "for fun, or no result-update rule",
    (CandidateSchema, "would_be_forecast"): "no seat is open on a shortlist",
    (CandidateSchema, "withheld"): (
        "a fresh search, where every row is live by construction and the "
        "question does not arise"
    ),
    (PlayerCardSchema, "photo_id"): "they have no photo; the client draws the poster",
    (PlayerCardSchema, "counted_games"): "the card is not assembled with it yet",
}


def _nullable(annotation: object) -> bool:
    """Whether ``None`` is one of this annotation's members.

    Both spellings of a union, because Python has two — ``Optional[T]`` and
    ``T | None`` — and a check that knew only one would read a nullable field as
    inapplicable and pass.
    """

    return get_origin(annotation) in (Union, UnionType) and NoneType in get_args(
        annotation
    )


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_no_field_is_both_optional_and_nullable(model: type[BaseModel]):
    """The one shape that says neither thing."""

    for name, field in model.model_fields.items():
        both = _nullable(field.annotation) and not field.is_required()
        assert not both, f"{model.__name__}.{name} is both optional and nullable"


@pytest.mark.parametrize(
    "model,field",
    sorted(OMITTED_FIELDS, key=lambda pair: (pair[0].__name__, pair[1])),
    ids=lambda value: value if isinstance(value, str) else value.__name__,
)
def test_a_field_that_does_not_apply_is_optional_and_never_nullable(model, field):
    """``field?: T`` — the client branches on its presence, not on a null."""

    declared = model.model_fields[field]
    assert not declared.is_required(), f"{model.__name__}.{field} must be omittable"
    assert not _nullable(declared.annotation), (
        f"{model.__name__}.{field} is spelled as a measured nothing, and it is an "
        "inapplicable one"
    )


def test_a_measured_nothing_is_required_and_nullable():
    """``mode`` is null exactly on the deck: both grids were read, and the answer
    is that this surface has no mode. That is a fact, not an absence."""

    mode = SearchEnvelope.model_fields["mode"]
    assert mode.is_required()
    assert _nullable(mode.annotation)


def test_the_omitted_sentinel_is_the_only_way_a_field_is_left_out():
    """One spelling, in one place, so that *why is this field optional* has one
    answer rather than one per model."""

    assert OMITTED is None
    for model, field in OMITTED_FIELDS:
        assert model.model_fields[field].default is OMITTED


def test_the_liveness_reason_vocabulary_is_exactly_the_printable_roster():
    """Eight printable signals, with the full inbox spelled as its three coarse
    rungs instead of its own name.

    **The two silent signals must be absent**, and their absence is the promise:
    a silent move carries points and no code, so there is no name on the value to
    print. A code here for one of them would be that promise broken in the one
    place it is kept.
    """

    rules = LIVE_RULESET.liveness
    printable = {
        signal for signal in LivenessSignal if rules.signals[signal].printable
    }
    silent = set(LivenessSignal) - printable
    assert len(silent) == 2, (
        "the silent roster moved; this vocabulary must move with it"
    )

    expected = {
        signal.value
        for signal in printable
        if signal is not LivenessSignal.CHALLENGE_LOAD
    } | {
        f"{LivenessSignal.CHALLENGE_LOAD.value}_{rung.value}" for rung in ChallengeLoad
    }

    assert {reason.value for reason in LivenessReason} == expected
    for quiet in silent:
        assert quiet.value not in {reason.value for reason in LivenessReason}


def test_the_wire_publishes_one_inclusion_reason_and_the_store_keeps_three():
    """**The store is open where the wire is closed.**

    Only an interest lift *admits* anybody. The other two reorder, and a reorder
    is not a reason a searcher is owed: ``NEWCOMER_WINDOW`` reaches the client as
    a Liveness reason instead, and ``ZERO_EXPOSURE`` — *nobody has been shown
    them all week* — is a third party's unpopularity that must not cross in any
    shape, including as one value of an enum a client can read off the schema.
    """

    assert {reason.value for reason in WireInclusionReason} == {"INTEREST_LIFT"}
    assert {reason.value for reason in InclusionReason} == {
        "INTEREST_LIFT",
        "NEWCOMER_WINDOW",
        "ZERO_EXPOSURE",
    }
    # The **values** a client generates, not the prose beside them: the schema's
    # own descriptions name the two withheld codes on purpose, in the sentence
    # explaining why they are withheld.
    published = _enumerated(CandidateSchema.model_json_schema())
    assert "INTEREST_LIFT" in published
    for withheld in ("ZERO_EXPOSURE", "NEWCOMER_WINDOW"):
        assert withheld not in published, (
            f"{withheld} is a value the candidate schema publishes"
        )


def _enumerated(schema: object) -> set[str]:
    """Every value any ``enum`` in this document offers, however nested."""

    found: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "enum" and isinstance(value, list):
                found |= {str(item) for item in value}
            else:
                found |= _enumerated(value)
    elif isinstance(schema, list):
        for item in schema:
            found |= _enumerated(item)
    return found


def test_the_modifier_vocabulary_is_the_roster_plus_the_dock_outside_it():
    """Every modifier prints — there is no unprintable one — and the reliability
    dock is in the vocabulary because it prints too, while sitting outside the
    budget."""

    from app.engines.matchfit.core import Modifier

    assert {code.value for code in ModifierCode} == {
        modifier.value for modifier in Modifier
    }


def test_the_request_carries_asks_and_never_a_fact_about_the_searcher():
    """**There is no radius here, and there never will be.** A stale radius from
    a phone is a gate evaluated on a lie, and this is the field it would arrive
    through.

    Five fields, and every one of them is an *ask*. The two that widen a search
    name an **offer** rather than a value — the radius a rung goes to is read off
    the offering search's own record — so the closest thing here to a fact about
    the searcher is a week they are asking about tonight, which is the one ask
    that looks like a fact and is not.
    """

    assert set(RunSearchRequest.model_fields) == {
        "sport",
        "mode",
        "availability_override",
        "offered_by_search_id",
        "rung",
    }
    assert "radius" not in " ".join(RunSearchRequest.model_fields)


def test_the_cell_a_times_rung_offers_is_the_resource_a_grid_is_drawn_from():
    """**Two named fields, on the one slot the client never sent us.**

    Every other cell crosses as ``AvailabilitySlotResource`` because *"a client
    that had to split ``"3:EVENING"`` would be parsing our persistence format"*,
    and this one is drawn on the same seven-by-three grid as all of them —
    ticked there as this search's own (#283). It reached the wire as the joined
    code the engine holds it in, which made the one cell the player did not
    choose the one cell a client had to parse.
    """

    assert RungOfferSchema.model_fields["slot"].annotation is AvailabilitySlotResource


def test_the_week_a_prompt_quotes_back_is_the_resource_a_grid_is_drawn_from():
    """**The last place a client met the joined code, and now it does not.**

    A raised ``KEEP_THESE_TIMES`` is the only week on this route the client is
    asked to *draw* rather than to send: the prompt sheet renders it on the same
    seven-by-three grid as the profile's own and quotes the count off it. It
    crossed as the aggregate's storage codes, so the sheet had to split
    ``"3:EVENING"`` for itself — which is the one thing
    ``AvailabilitySlotResource`` was named to spare a client. It is the same
    reading the test one up gave ``RungOfferSchema.slot`` (#283), reached the
    second time on the second field that had been read as an exception (#286).

    **A quoted payload is still a resource when a grid is drawn from it.** That
    is the argument the counter-argument lost: the engine holding the week as
    codes is a fact about the engine, and this side of the boundary is where our
    persistence format is read.
    """

    assert (
        PromptSchema.model_fields["slots"].annotation
        == list[AvailabilitySlotResource]
    )


def test_the_response_has_two_halves_and_no_third_thing():
    assert set(ShortlistResponse.model_fields) == {"search", "candidates"}


def test_a_withheld_row_carries_the_statement_and_nothing_else():
    """**Stated, never vanished — and never a person.**

    A read-back re-evaluates the gates that fail closed, and a row they no longer
    admit keeps its place in the list. What it may not keep is anybody's
    identity: rendering a card, or even an id, for somebody the product has
    agreed to stop showing is the exact failure ``docs/adr/0095`` was written to
    prevent, arriving through the one route nobody thought of as a surface.

    It is a **separate shape** rather than a candidate with holes, so that is a
    property of the type rather than of whoever writes the renderer next.
    """

    assert set(WithheldRowSchema.model_fields) == {"withheld"}
    published = _enumerated(WithheldRowSchema.model_json_schema())
    assert published <= {"True", "true"}


def test_a_withheld_row_names_no_gate():
    """``docs/adr/0109`` §1 asked for the coarse gate spelling beside the
    statement; ``docs/adr/0095`` says *the other side sees no trace anywhere in
    any response*, and that is the one that wins.

    *Withheld: BLOCKED* is precisely that trace, delivered to the person the
    block was meant to be invisible to. A hold and an account state are
    moderation facts about somebody else, and a gender preference is a safety
    setting only its owner may read (``docs/adr/0096``). So the four causes are
    indistinguishable, and there is no field here for one to arrive through.
    """

    document = str(ShortlistResponse.model_json_schema())
    for gate in ("BLOCKED", "HELD_ACCOUNT", "ACCOUNT_INACTIVE", "GENDER_PREFERENCE"):
        assert gate not in document, f"{gate} is a value this contract publishes"


def test_the_two_row_shapes_are_the_only_things_a_candidate_list_holds():
    """One candidate and one tombstone. A third shape would be a third render
    path, and the near-miss band is exactly what would eventually arrive in it."""

    candidates = ShortlistResponse.model_fields["candidates"].annotation
    assert set(get_args(get_args(candidates)[0])) == {
        CandidateSchema,
        WithheldRowSchema,
    }
