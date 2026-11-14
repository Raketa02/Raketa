"""No read on the player or the club surface serves a player's name — only
their nickname.

``docs/adr/0199``: the **Name** is retired, and the nickname is what every
sentence, row, card, sheet, notice and seat label says about a player. A field
called ``name`` on a seat, a member or a card would look harmless in a diff, so
the claim is made over the **emitted contract** rather than over a class, the
way the sportsmanship figure's is: every ``name`` a response can reach belongs
to something that is not a player — a club, a court, a group, a band, or an
Administrator as their club typed them — and every shape that draws a player
carries ``nickname``. The club's desk reads ``ania.k`` on a booking and on a
Join request too (#725).
"""

from __future__ import annotations

from app.api.contract import SURFACES, build_surface_spec
from app.api.v1.player import player_api_router
from tests.unit.test_no_response_carries_a_forbidden_fact import (
    schemas_reachable_from_responses,
)

#: Every response schema that may carry a ``name``, and what it names. None of
#: them is a player; a new entry here is a claim somebody has to read.
NAMES_OF_THINGS = {
    "AdministeredGroupCardSchema": "a group",
    "AdministeredGroupResponse": "a group",
    "BandResponse": "a Level band",
    "BookedClubSchema": "a club",
    "ClubCardSchema": "a club",
    "ClubNameSchema": "a club",
    "DeckClubSchema": "a club",
    "GroupAtClubSchema": "a group",
    "GroupResponse": "a group",
    "GroupToAddFromSchema": "a group",
    "HomeFriendRequestGroupSchema": "a group",
    "HottestGroupSchema": "a group",
    "InvitationByTokenResponse": "an Administrator, as the club typed it",
    "LiveYesClubSchema": "a club",
    "MyGroupSchema": "a group",
    "OfficialGroupClubSchema": "a club",
    "SellerSchema": "a club",
    "WhereSchema": "a club",
}

#: Every shape that draws a person, and so carries their nickname
#: (``docs/adr/0199`` §6).
DRAWS_A_PERSON = (
    "AttendanceSchema",
    "BlockedPlayerSchema",
    "BookedTileSchema",
    "CalledOffBySchema",
    "ConversationMemberSchema",
    "ConversationPersonSchema",
    "DeckChallengerSchema",
    "DeckTileSchema",
    "FriendRequestSchema",
    "FriendSchema",
    "GroupMemberSchema",
    "GroupPersonSchema",
    "GroupPlayerSchema",
    "HomeFriendRequestSchema",
    "JoinRequestSchema",
    "MeResponse",
    "NamingResponse",
    "PlayerRecordResponse",
    "SeatingSchema",
    "SlotFitSchema",
    "UserResponse",
)


def _spec() -> dict:
    return build_surface_spec("Raketa Player API", player_api_router)


def test_every_name_a_response_reaches_names_something_that_is_not_a_player() -> None:
    schemas = schemas_reachable_from_responses(_spec())
    assert schemas, "the walk found no schemas, so it would pass for ever"

    carrying = sorted(
        schema_name
        for schema_name, schema in schemas.items()
        if "name" in (schema.get("properties") or {})
    )

    assert carrying == sorted(NAMES_OF_THINGS)


def test_every_shape_that_draws_a_person_carries_their_nickname() -> None:
    schemas = _spec()["components"]["schemas"]

    for owner in DRAWS_A_PERSON:
        properties = schemas[owner]["properties"]
        assert "nickname" in properties, f"{owner} names nobody"
        assert "name" not in properties, f"{owner} still serves a name"


def test_a_group_names_its_owner_and_its_administrator_by_nickname() -> None:
    """The *approves joins* line (``docs/adr/0199`` §4, §6)."""

    schemas = _spec()["components"]["schemas"]

    at_club = schemas["GroupAtClubSchema"]["properties"]
    assert {"owner_nickname", "administrator_nickname"} <= set(at_club)
    assert not {"owner_name", "administrator_name"} & set(at_club)
    page = schemas["GroupResponse"]["properties"]
    assert "administrator_nickname" in page
    assert "administrator_name" not in page


def test_the_naming_takes_a_nickname_and_nothing_else() -> None:
    request = _spec()["components"]["schemas"]["NameRequest"]

    assert set(request["properties"]) == {"nickname"}
    assert request["required"] == ["nickname"]
    assert request.get("additionalProperties") is False


def test_sign_up_asks_for_credentials_only() -> None:
    """The nickname left the sign-up payload (``docs/adr/0171`` §2), and a body
    still carrying one is refused rather than ignored."""

    request = _spec()["components"]["schemas"]["UserCreateRequest"]

    assert set(request["properties"]) == {
        "email",
        "password1",
        "password2",
        "adult_attested",
    }
    assert request.get("additionalProperties") is False


# --------------------------------------------------------------------------- #
# The club surface (#725)
# --------------------------------------------------------------------------- #

#: Every club response schema that may carry a ``name``, and what it names.
#: The Administrators keep the name their club typed for them — the table, an
#: invitation, *run by* and the handover (``docs/adr/0199`` §4).
CLUB_NAMES_OF_THINGS = {
    "AdministratorGroupSchema": "a group",
    "AdministratorSchema": "an Administrator, as the club typed it",
    "BookedFromSchema": "a group",
    "ClubDetailsResponse": "a club",
    "ClubGroupAdministratorSchema": "an Administrator, as the club typed it",
    "ClubGroupSchema": "a group",
    "CourtResponse": "a court",
    "CourtToMoveToSchema": "a court",
}

#: Every club shape that draws a player — a seat on a booking, somebody
#: asking to join an official group.
CLUB_DRAWS_A_PLAYER = ("ClubBookingPlayerSchema", "ClubJoinRequestSchema")


def _club_spec() -> dict:
    return build_surface_spec("Raketa Club API", SURFACES["club"])


def test_every_name_the_club_reads_names_something_that_is_not_a_player() -> None:
    schemas = schemas_reachable_from_responses(_club_spec())
    assert schemas, "the walk found no schemas, so it would pass for ever"

    carrying = sorted(
        schema_name
        for schema_name, schema in schemas.items()
        if "name" in (schema.get("properties") or {})
    )

    assert carrying == sorted(CLUB_NAMES_OF_THINGS)


def test_every_player_the_club_reads_is_drawn_by_their_nickname() -> None:
    schemas = _club_spec()["components"]["schemas"]

    for owner in CLUB_DRAWS_A_PLAYER:
        properties = schemas[owner]["properties"]
        assert "nickname" in properties, f"{owner} names nobody"
        assert "name" not in properties, f"{owner} still serves a name"
        # A player without one still reads as nobody — the website's *A
        # player* — so the field stays nullable.
        assert {"type": "null"} in properties["nickname"].get("anyOf", ()), (
            f"{owner} cannot be nobody"
        )
