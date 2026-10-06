"""The nickname reaches ``/me``, the record and the naming's own answer — and no
other read on the player surface.

``docs/adr/0171`` §4: the **name** is what every screen says, and the nickname
is a handle drawn as ``@…`` under the name on a player's record and their own
You tab, **and said nowhere** — never on a row, a card, a sentence, a sheet, a
toast, a seat label or a spoken name. A seat, a member, a court person or a card
that grew a ``nickname`` would look like a helpful field in a diff where nothing
looks wrong, so the claim is made over the **emitted contract** rather than over
a class, the way the sportsmanship figure's is.
"""

from __future__ import annotations

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router
from tests.unit.test_no_response_carries_a_forbidden_fact import (
    schemas_reachable_from_responses,
)


def _spec() -> dict:
    return build_surface_spec("Raketa Player API", player_api_router)


def test_the_nickname_reaches_exactly_the_reads_that_may_draw_it() -> None:
    schemas = schemas_reachable_from_responses(_spec())
    assert schemas, "the walk found no schemas, so it would pass for ever"

    carrying = sorted(
        name
        for name, schema in schemas.items()
        if "nickname" in (schema.get("properties") or {})
    )

    # ``MeResponse`` is ``/me`` and ``UserResponse`` the registration's echo of
    # an unnamed account, which ``MeResponse`` extends with the account's
    # profiles; ``PlayerRecordResponse`` is the one read about *another* player
    # that carries both; ``NamingResponse`` is the act answering what it wrote.
    assert carrying == [
        "MeResponse",
        "NamingResponse",
        "PlayerRecordResponse",
        "UserResponse",
    ]


def test_every_surface_that_names_another_player_carries_the_name() -> None:
    """The rename is total: where a seat, a member, a person or a card is
    drawn, ``name`` is on it — and ``nickname`` is not."""

    schemas = _spec()["components"]["schemas"]

    # A challenge's seats and court people were three more, and went with the
    # challenges (#578); the search card was another, and went with the searches
    # (#579).
    for owner in (
        "ConversationMemberSchema",
        "ConversationPersonSchema",
        "SeatingSchema",
    ):
        properties = schemas[owner]["properties"]
        assert "name" in properties, f"{owner} names nobody"
        assert "nickname" not in properties, f"{owner} draws a handle"


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
