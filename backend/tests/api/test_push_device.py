"""`PUT /api/v1/push/device` over HTTP: the channel's whole wire surface.

The unit suite asserts the rules against stubs and the store suite asserts the
table. What this file adds is the half neither can reach — that the route is
really mounted under the player API, that it really takes the caller's identity
from her token rather than from a body, that all three `timeSensitiveSetting`
values are really accepted, and that the row a request leaves behind is the row
the send reads.

The last one is why this exists rather than as another unit case: the request
model, the command and the stored row are three shapes for one fact, and a
`platform` dropped between any two of them would pass every rule test in the
tree and ship a channel that sends every message with an Android channel id to
an iPhone.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.now.domain.push import Platform, TimeSensitiveSetting
from app.modules.now.infrastructure.push_stores import SqlAlchemyPushDevices

ALICE = {
    "email": "alice@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "alice",
}
BOB = {
    "email": "bob@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "bob",
}

TOKEN = "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"


async def _register(client, payload) -> str:
    created = await client.post("/api/v1/users", json=payload)
    assert created.status_code in (200, 201), created.text
    return created.json()["id"]


async def _sign_in(client, payload) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _join(client, payload) -> tuple[UUID, dict[str, str]]:
    who = await _register(client, payload)
    return UUID(who), await _sign_in(client, payload)


def _body(**kwargs) -> dict[str, str]:
    return {
        "token": TOKEN,
        "platform": "ios",
        "time_sensitive_setting": "enabled",
        **kwargs,
    }


async def test_registering_a_phone_answers_no_content(client) -> None:
    """204, because registering a token is not an act off Now.

    ADR-0074 has every action off that screen hand back Now's update so the
    screen corrects itself; this moves no card and has nothing to say back.
    """

    _, headers = await _join(client, ALICE)

    answer = await client.put("/api/v1/push/device", json=_body(), headers=headers)

    assert answer.status_code == 204, answer.text
    assert answer.content == b""


async def test_the_row_carries_what_the_request_said(
    client, session_factory
) -> None:
    her, headers = await _join(client, ALICE)

    await client.put(
        "/api/v1/push/device",
        json=_body(platform="android", time_sensitive_setting="notSupported"),
        headers=headers,
    )

    async with session_factory() as session:
        (device,) = await SqlAlchemyPushDevices(session).for_player(her)
    assert device.token == TOKEN
    assert device.platform is Platform.ANDROID
    assert device.time_sensitive is TimeSensitiveSetting.NOT_SUPPORTED


async def test_all_three_settings_are_accepted(client, session_factory) -> None:
    """`notSupported` is a fourth state and not a synonym for a refusal.

    A player on an iPad was never going to get a Focus-piercing alert and has
    refused anything; a route that turned her away would make the one value that
    reports *this phone has no such setting* unreportable.
    """

    her, headers = await _join(client, ALICE)

    for setting in TimeSensitiveSetting:
        answer = await client.put(
            "/api/v1/push/device",
            json=_body(time_sensitive_setting=setting.value),
            headers=headers,
        )
        assert answer.status_code == 204, (setting, answer.text)
        async with session_factory() as session:
            (device,) = await SqlAlchemyPushDevices(session).for_player(her)
        assert device.time_sensitive is setting


async def test_a_missing_setting_is_refused(client) -> None:
    """Omitting it would report *disabled* by silence.

    The three values are three different facts about a phone, and a client that
    could leave the field out would make *we do not know* indistinguishable from
    *she turned it off* — which is the whole of what this field is observed for.
    """

    _, headers = await _join(client, ALICE)
    body = _body()
    del body["time_sensitive_setting"]

    answer = await client.put("/api/v1/push/device", json=body, headers=headers)

    assert answer.status_code == 422, answer.text


async def test_an_unknown_platform_is_refused(client) -> None:
    _, headers = await _join(client, ALICE)

    answer = await client.put(
        "/api/v1/push/device", json=_body(platform="web"), headers=headers
    )

    assert answer.status_code == 422, answer.text


async def test_an_empty_token_is_refused(client) -> None:
    _, headers = await _join(client, ALICE)

    answer = await client.put(
        "/api/v1/push/device", json=_body(token=""), headers=headers
    )

    assert answer.status_code == 422, answer.text


async def test_the_route_needs_a_token_of_its_own(client) -> None:
    """The player is the caller and never a field on the request.

    A body naming a player would let one account point the channel at another
    account's phone, which is the one failure in this channel worse than
    silence.
    """

    answer = await client.put("/api/v1/push/device", json=_body())

    assert answer.status_code in (401, 403), answer.text


async def test_signing_in_on_a_phone_takes_it_off_the_last_player(
    client, session_factory
) -> None:
    """A token names a phone, and a phone has one player at a time.

    The full sign-out: Alice registers her phone, Bob signs in on the same
    handset, and the phone reports the same token under his account. Alice must
    stop being reachable there, because nothing can take a delivered message
    back.
    """

    alice, hers = await _join(client, ALICE)
    bob, his = await _join(client, BOB)

    await client.put("/api/v1/push/device", json=_body(), headers=hers)
    await client.put("/api/v1/push/device", json=_body(), headers=his)

    async with session_factory() as session:
        devices = SqlAlchemyPushDevices(session)
        assert await devices.for_player(alice) == ()
        assert [one.player_id for one in await devices.for_player(bob)] == [bob]


async def test_re_registering_the_same_phone_is_one_row(
    client, session_factory
) -> None:
    """A phone re-registers on every sign-in and on every token rotation."""

    her, headers = await _join(client, ALICE)

    for setting in ("enabled", "disabled"):
        await client.put(
            "/api/v1/push/device",
            json=_body(time_sensitive_setting=setting),
            headers=headers,
        )

    async with session_factory() as session:
        held = await SqlAlchemyPushDevices(session).for_player(her)
    assert len(held) == 1
    assert held[0].time_sensitive is TimeSensitiveSetting.DISABLED


async def test_the_contract_names_the_three_settings_as_an_enum(client) -> None:
    """A bare string degrades a client's exhaustive table into an index signature.

    Both clients build copy and behaviour tables keyed on the enums this
    document emits, and the failure a bare string causes is the one no typecheck
    can reach afterwards.
    """

    document = (await client.get("/openapi.json")).json()
    schemas = document["components"]["schemas"]

    assert set(schemas["TimeSensitiveSetting"]["enum"]) == {
        "enabled",
        "disabled",
        "notSupported",
    }
    assert set(schemas["Platform"]["enum"]) == {"ios", "android"}
    assert "/api/v1/push/device" in document["paths"]
