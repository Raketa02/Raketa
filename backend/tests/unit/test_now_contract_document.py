"""What the emitted player document says about Now, read back from the document.

Neither client validates the wire at runtime — both generate types with
``openapi-typescript`` and those types are erased at build. So every rule this
contract makes is only as real as what ``make openapi`` actually emits, and the
document is what a client developer reads. This walk reads it back.

The load-bearing half is the enumerations. A code that crosses as a bare string
degrades the client's exhaustive ``Record<GeneratedEnum, Entry>`` into an index
signature, and an index signature **never fires**: the missing sentence ships,
typechecks, and shows up as a blank line on somebody's home screen.
"""

import json
from pathlib import Path

import pytest

from app.api.contract import build_surface_spec
from app.api.v1.club import club_api_router
from app.api.v1.player import player_api_router
from app.engines.fit import TermCode
from app.kernel import SITUATION_COUNT, Cause, Situation

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def player_spec() -> dict:
    return build_surface_spec("Raketa Player API", player_api_router)


@pytest.fixture(scope="module")
def club_spec() -> dict:
    return build_surface_spec("Raketa Club API", club_api_router)


def _reachable(spec: dict, root: str) -> set[str]:
    """Every schema reachable from one, so a walk claims about Now and not all."""

    schemas = spec["components"]["schemas"]
    seen: set[str] = set()
    frontier = [root]
    while frontier:
        name = frontier.pop()
        if name in seen or name not in schemas:
            continue
        seen.add(name)
        for ref in _refs(schemas[name]):
            frontier.append(ref)
    return seen


def _refs(node) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.append(value.rsplit("/", 1)[-1])
            else:
                found.extend(_refs(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_refs(item))
    return found


def _property_names(spec: dict, names: set[str]) -> set[str]:
    schemas = spec["components"]["schemas"]
    return {
        prop
        for name in names
        for prop in schemas[name].get("properties", {})
    }


def test_the_route_is_under_the_version_prefix(player_spec: dict) -> None:
    # The specification set writes `GET /now`, which is a name for the screen
    # rather than an address; being the one route outside the prefix is a cost
    # that buys nothing.
    assert "/api/v1/now" in player_spec["paths"]
    assert "/now" not in player_spec["paths"]


def test_the_club_surface_never_sees_the_player_screen(club_spec: dict) -> None:
    assert "/api/v1/now" not in club_spec.get("paths", {})
    assert "NowResponse" not in club_spec.get("components", {}).get("schemas", {})


def test_the_request_carries_the_sport_and_nothing_else(player_spec: dict) -> None:
    operation = player_spec["paths"]["/api/v1/now"]["get"]
    parameters = operation.get("parameters", [])

    assert [p["name"] for p in parameters] == ["sport"]
    assert all(p["in"] == "query" for p in parameters)
    # No stamp of what the phone is holding, and no conditional-request header:
    # the server never answers *nothing has changed*.
    assert "requestBody" not in operation
    assert set(operation["responses"]) == {"200", "422"}
    assert "304" not in operation["responses"]


def test_the_sport_parameter_is_an_enum_holding_all_and_the_four(
    player_spec: dict,
) -> None:
    parameter = player_spec["paths"]["/api/v1/now"]["get"]["parameters"][0]
    name = _refs(parameter["schema"])[0]
    values = player_spec["components"]["schemas"][name]["enum"]

    assert set(values) == {"all", "PADEL", "TENNIS", "SQUASH", "BADMINTON"}


def test_the_envelope_is_three_regions_and_one_viewer_fact(player_spec: dict) -> None:
    envelope = player_spec["components"]["schemas"]["NowResponse"]

    assert list(envelope["properties"]) == [
        "offers",
        "your_matches",
        "shelves",
        "debt",
    ]
    # Three regions always present; the one viewer fact absent when nothing is
    # owed.
    assert set(envelope["required"]) == {"offers", "your_matches", "shelves"}


def test_a_stamp_per_region_and_per_card_and_none_on_the_screen(
    player_spec: dict,
) -> None:
    schemas = player_spec["components"]["schemas"]

    regions = (
        "OffersRegionResponse",
        "EnrolledRegionResponse",
        "ShelvesRegionResponse",
    )
    for region in regions:
        assert schemas[region]["properties"]["stamp"]["type"] == "integer"
    for card in ("MatchCardResponse", "PersonCardResponse", "ClubCardResponse"):
        assert schemas[card]["properties"]["stamp"]["type"] == "integer"

    assert "stamp" not in schemas["NowResponse"]["properties"]
    # A shelf is never in an update, so there is nothing for a stamp to arbitrate.
    assert "stamp" not in schemas["ShelfResponse"]["properties"]


def test_a_shelf_carries_a_code_and_an_optional_caption_code(player_spec: dict) -> None:
    shelf = player_spec["components"]["schemas"]["ShelfResponse"]

    assert set(shelf["properties"]) == {"block_type", "code", "caption", "cards"}
    assert "code" in shelf["required"]
    assert "caption" not in shelf["required"]


def test_the_shelves_list_is_discriminated_on_the_blocks_own_type(
    player_spec: dict,
) -> None:
    blocks = player_spec["components"]["schemas"]["ShelvesRegionResponse"][
        "properties"
    ]["shelves"]
    union = blocks["items"]

    assert union["discriminator"]["propertyName"] == "block_type"
    assert set(union["discriminator"]["mapping"]) == {"shelf", "door"}


def test_the_door_carries_one_code_and_neither_a_sport_nor_a_destination(
    player_spec: dict,
) -> None:
    door = player_spec["components"]["schemas"]["DoorResponse"]

    # The client named the sport on the request and still holds it; a second copy
    # on the answer is a second thing that can disagree. The code determines the
    # destination, exactly as an act code does.
    assert set(door["properties"]) == {"block_type", "code"}
    assert "code" in door["required"]


def test_the_door_has_no_cards_no_caption_and_no_stamp(player_spec: dict) -> None:
    door = player_spec["components"]["schemas"]["DoorResponse"]

    # A door and a shelf are two types rather than one shelf with a nullable door
    # code, on ADR-0070's *three card types, not one with holes*.
    for absent in ("cards", "caption", "stamp"):
        assert absent not in door["properties"]


def test_a_card_is_one_of_three_types_discriminated_on_itself(
    player_spec: dict,
) -> None:
    cards = player_spec["components"]["schemas"]["ShelfResponse"]["properties"]["cards"]
    union = cards["items"]

    assert union["discriminator"]["propertyName"] == "card_type"
    assert set(union["discriminator"]["mapping"]) == {"match", "person", "club"}


def test_only_a_match_card_has_a_situation_half(player_spec: dict) -> None:
    schemas = player_spec["components"]["schemas"]

    assert "situation" in schemas["MatchCardResponse"]["properties"]
    # A person and a club have no situation, no clock, no price and no emphasis.
    # One union type would give them four permanently empty fields.
    for inert in ("PersonCardResponse", "ClubCardResponse"):
        properties = schemas[inert]["properties"]
        assert "situation" not in properties
        assert "clock" not in properties
        assert "price" not in properties
        assert "emphasis" not in properties


def test_the_situation_half_is_the_situation_and_its_facts(player_spec: dict) -> None:
    half = player_spec["components"]["schemas"]["SituationHalfResponse"]
    assert set(half["properties"]) == {"situation", "facts"}


@pytest.mark.parametrize(
    "schema,expected",
    [
        ("Situation", {s.value for s in Situation}),
        ("Cause", {c.value for c in Cause}),
        ("TermCode", {t.value for t in TermCode}),
        (
            "ActCode",
            {
                "takeSeat",
                "finishPaying",
                "enterResult",
                "answerResult",
                "seeAlternatives",
                "gettingIn",
                "leaveStandby",
            },
        ),
        ("CardHoldReason", {"committed", "far", "near", "stale", "extended"}),
        (
            "ShelfCode",
            {
                "bestFit",
                "sameLevel",
                "fullWorthWaiting",
                "recentlyViewed",
                "newPlayers",
                "newClubs",
            },
        ),
        ("CaptionCode", {"undeclaredPreferences"}),
        ("DoorCode", {"noRunYet", "runParked"}),
        ("Cover", {"indoor", "outdoor"}),
        ("Currency", {"PLN"}),
    ],
)
def test_every_code_crosses_as_a_generated_union(
    player_spec: dict, schema: str, expected: set[str]
) -> None:
    emitted = player_spec["components"]["schemas"][schema]

    assert "enum" in emitted, f"{schema} crosses as a bare string"
    assert set(emitted["enum"]) == expected


def test_the_situation_union_is_the_whole_ladder(player_spec: dict) -> None:
    emitted = player_spec["components"]["schemas"]["Situation"]["enum"]

    assert len(emitted) == SITUATION_COUNT == 36
    # In ladder order, so that reading the union is reading the specification.
    assert emitted == [s.value for s in Situation]


FORBIDDEN = (
    # ADR-0071: two fields with no reader are not forwards-compatibility.
    "server_time",
    "serverTime",
    "next_transition",
    "nextTransition",
    # A fact about our infrastructure printed on a player's home screen.
    "degraded",
    "degrade",
    # Support is us, reading our own logs; a screenshot has a timestamp.
    "policy_version",
    "policyVersion",
    # The client's own thirty-six-row table, all three of them.
    "tone",
    "tag",
    "alert",
    # ADR-0074 refused it on the result route and it is refused here too.
    "phase",
)


@pytest.mark.parametrize("field", FORBIDDEN)
def test_the_wire_does_not_carry_it(player_spec: dict, field: str) -> None:
    reachable = _reachable(player_spec, "NowResponse")
    assert field not in _property_names(player_spec, reachable)


#: A name that would be a sentence rather than a fact. A club's name and a
#: player's nickname are data about a thing; a title, a label or a note is copy,
#: and copy is the client's.
COPY_SHAPED = (
    "title",
    "label",
    "note",
    "message",
    "sentence",
    "text",
    "body",
    "copy",
    "description",
    "summary",
)


@pytest.mark.parametrize("field", COPY_SHAPED)
def test_no_free_text_crosses(player_spec: dict, field: str) -> None:
    reachable = _reachable(player_spec, "NowResponse")
    assert field not in _property_names(player_spec, reachable)


def test_the_walk_reaches_the_schemas_it_is_claiming_about(player_spec: dict) -> None:
    # A reachability walk that found nothing would pass every assertion above in
    # silence — the lesson a glob matching nothing already taught this tree.
    reachable = _reachable(player_spec, "NowResponse")

    assert "MatchCardResponse" in reachable
    assert "SituationHalfResponse" in reachable
    assert "Situation" in reachable
    # The door is reachable from the envelope, so the forbidden-field and
    # free-text walks above are claiming about it too rather than around it.
    assert {"DoorResponse", "DoorCode"} <= reachable
    assert len(reachable) >= 20
    # And it is a walk over *Now*, not over the whole document: the rating
    # context's schemas carry `label` and `text` legitimately and are not here.
    assert "QuestionResponse" not in reachable


def test_the_committed_document_matches_what_the_code_emits(player_spec: dict) -> None:
    """`make openapi` was run, and its output is in the tree.

    CI regenerates and diffs, so a contract change shipped without its client
    types fails the build. This says the same thing one step earlier, where the
    failure names the file instead of the pipeline.
    """

    committed = json.loads((ROOT / "openapi.player.json").read_text())
    assert committed["paths"]["/api/v1/now"] == player_spec["paths"]["/api/v1/now"]
    assert (
        committed["components"]["schemas"]["NowResponse"]
        == player_spec["components"]["schemas"]["NowResponse"]
    )
