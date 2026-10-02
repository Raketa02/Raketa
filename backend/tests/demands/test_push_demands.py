"""What every push service answers alike (#549), run against every adapter
registered in ``app/bootstrap/push_demands.py``.

**The recording service is what every API test reads**, so it is only as good
as its agreement with Expo's: a phone it forgets must be in the receipt as one
Expo no longer knows is, a service that cannot be reached must raise as Expo's
adapter does, and everything pushed must reach its phone with its words and
what a tap opens.

**Expo is a loopback server speaking its documented push API** — a list of
messages in, a ticket for each in the same order, ``DeviceNotRegistered`` on a
phone it no longer knows, at most a hundred messages a request — never Expo
itself (see the register).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.bootstrap.push_demands import PUSH_IMPLEMENTATIONS, RegisteredPushService
from app.core.config import get_settings
from app.modules.notifications.domain.ports import (
    Push,
    PushNotifications,
    PushUnavailable,
)
from app.modules.notifications.infrastructure.push import (
    DEVICE_NOT_REGISTERED,
    EXPO_BATCH,
    RecordingPush,
)

PATH = "/--/api/v2/push/send"


class ExpoStandIn:
    """Expo's push API as its documentation describes it, and what it was sent."""

    def __init__(self) -> None:
        self.requests: list[list[dict[str, Any]]] = []
        self.forgotten: set[str] = set()
        self.down = False

    async def _send(self, request: web.Request) -> web.StreamResponse:
        if self.down:
            return web.json_response(
                {"errors": [{"code": "INTERNAL_SERVER_ERROR"}]}, status=503
            )
        messages = await request.json()
        assert isinstance(messages, list), "Expo is always sent a list"
        assert len(messages) <= EXPO_BATCH, "at most a hundred messages a request"
        self.requests.append(messages)
        return web.json_response(
            {
                "data": [
                    {
                        "status": "error",
                        "message": f"{message['to']} is not a registered push token",
                        "details": {"error": DEVICE_NOT_REGISTERED},
                    }
                    if message["to"] in self.forgotten
                    else {"status": "ok", "id": f"ticket-{index}"}
                    for index, message in enumerate(messages)
                ]
            }
        )

    def application(self) -> web.Application:
        app = web.Application()
        app.router.add_post(PATH, self._send)
        return app

    def delivered(self, token: str) -> list[tuple[str, str, dict[str, str]]]:
        return [
            (message["title"], message["body"], message["data"])
            for request in self.requests
            for message in request
            if message["to"] == token and message["to"] not in self.forgotten
        ]


@dataclass
class PushWorld:
    """One push service, and the levers its outside world offers a test."""

    service: PushNotifications
    forget: Callable[[str], None]
    go_down: Callable[[], None]
    delivered: Callable[[str], list[tuple[str, str, dict[str, str]]]]


def registered():
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in PUSH_IMPLEMENTATIONS
    ]


@pytest.fixture
async def world(request) -> AsyncIterator[PushWorld]:
    implementation: RegisteredPushService = request.param
    if implementation.name == "RecordingPush":
        service = implementation.build(get_settings())
        assert isinstance(service, RecordingPush)

        def go_down() -> None:
            service.unavailable = True

        yield PushWorld(
            service=service,
            forget=service.forget,
            go_down=go_down,
            delivered=lambda token: [
                (push.title, push.body, dict(push.data)) for push in service.to(token)
            ],
        )
        return
    assert implementation.name == "ExpoPush", f"no world for {implementation.name}"
    expo = ExpoStandIn()
    server = TestServer(expo.application())
    await server.start_server()
    try:

        def expo_goes_down() -> None:
            expo.down = True

        yield PushWorld(
            service=implementation.build(
                get_settings().model_copy(
                    update={"EXPO_PUSH_URL": str(server.make_url(PATH))}
                )
            ),
            forget=expo.forgotten.add,
            go_down=expo_goes_down,
            delivered=expo.delivered,
        )
    finally:
        await server.close()


def a_push(token: str, *, title: str = "It's a game! · you paid 30 zł") -> Push:
    return Push(
        token=token,
        title=title,
        body="Padel at Bonarka Arena · Sat 10 Oct, 17:00.",
        data={"kind": "GAME_BOOKED", "opens": "BOOKING", "game_id": "g-1"},
    )


def test_every_registered_service_has_a_world():
    assert {one.name for one in PUSH_IMPLEMENTATIONS} == {"RecordingPush", "ExpoPush"}


@pytest.mark.parametrize("world", registered(), indirect=True)
async def test_every_push_reaches_its_phone_with_its_words_and_where_it_opens(world):
    receipt = await world.service.send(
        [a_push("ExponentPushToken[ola]"), a_push("ExponentPushToken[kuba]")]
    )

    assert receipt.gone == frozenset()
    assert world.delivered("ExponentPushToken[ola]") == [
        (
            "It's a game! · you paid 30 zł",
            "Padel at Bonarka Arena · Sat 10 Oct, 17:00.",
            {"kind": "GAME_BOOKED", "opens": "BOOKING", "game_id": "g-1"},
        )
    ]
    assert len(world.delivered("ExponentPushToken[kuba]")) == 1


@pytest.mark.parametrize("world", registered(), indirect=True)
async def test_a_phone_the_service_no_longer_knows_is_in_the_receipt(world):
    world.forget("ExponentPushToken[wiped]")

    receipt = await world.service.send(
        [a_push("ExponentPushToken[wiped]"), a_push("ExponentPushToken[ola]")]
    )

    assert receipt.gone == frozenset({"ExponentPushToken[wiped]"})
    assert len(world.delivered("ExponentPushToken[ola]")) == 1


@pytest.mark.parametrize("world", registered(), indirect=True)
async def test_a_service_that_cannot_be_reached_raises(world):
    world.go_down()

    with pytest.raises(PushUnavailable):
        await world.service.send([a_push("ExponentPushToken[ola]")])


@pytest.mark.parametrize("world", registered(), indirect=True)
async def test_more_phones_than_one_request_holds_are_all_pushed(world):
    tokens = [f"ExponentPushToken[phone-{n}]" for n in range(EXPO_BATCH + 5)]
    world.forget(tokens[-1])

    receipt = await world.service.send([a_push(token) for token in tokens])

    assert receipt.gone == frozenset({tokens[-1]})
    assert all(len(world.delivered(token)) == 1 for token in tokens[:-1])
