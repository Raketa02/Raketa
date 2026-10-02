"""The push service, behind ``PushNotifications``: **Expo's**, and a **recording
fake** (#549; the mechanics §17.2 — *built with this feature, through Expo's
push service*).

``ExpoPush`` speaks Expo's push API: up to a hundred messages a request, a
ticket back for each in the same order, and a phone Expo no longer knows named
``DeviceNotRegistered`` on its ticket. An access token is sent when one is
configured — Expo requires it of a project with enhanced push security on, which
is what makes a leaked phone token useless to anybody else. **A client per
call**, as the photo-review sidecar's adapter makes one: an ``aiohttp`` session
binds to the event loop it was opened on. Expo's *receipts* — a second read,
minutes later, of what Apple and Google did with each ticket — are not asked:
a ticket's error is the one that removes a phone.

``RecordingPush`` pushes nothing and remembers everything: what a test reads,
what a seed run pushes to, and what a laptop configured to push nowhere uses.
A test makes a phone forgotten (``forget``) or the service unreachable
(``unavailable``).
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any, Final, final

import aiohttp

from app.modules.notifications.domain.ports import Push, PushReceipt, PushUnavailable

#: The most messages Expo takes in one request.
EXPO_BATCH: Final = 100
#: A ticket's error for a phone Expo no longer knows.
DEVICE_NOT_REGISTERED: Final = "DeviceNotRegistered"


@final
class ExpoPush:
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_token: str | None,
        timeout_seconds: float,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_token = access_token
        self._timeout_seconds = timeout_seconds

    async def send(self, pushes: Sequence[Push]) -> PushReceipt:
        gone: set[str] = set()
        for start in range(0, len(pushes), EXPO_BATCH):
            batch = pushes[start : start + EXPO_BATCH]
            tickets = await self._post([_message(push) for push in batch])
            for push, ticket in zip(batch, tickets, strict=True):
                details = ticket.get("details") if isinstance(ticket, dict) else None
                if (
                    isinstance(ticket, dict)
                    and ticket.get("status") == "error"
                    and isinstance(details, dict)
                    and details.get("error") == DEVICE_NOT_REGISTERED
                ):
                    gone.add(push.token)
        return PushReceipt(gone=frozenset(gone))

    async def _post(self, messages: list[dict[str, Any]]) -> list[Any]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self._endpoint_url, json=messages, headers=headers
                ) as response:
                    if response.status != 200:
                        raise PushUnavailable(f"Expo answered {response.status}")
                    answer = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
            raise PushUnavailable(f"Expo could not be asked: {exc!r}") from exc
        tickets = answer.get("data") if isinstance(answer, dict) else None
        if not isinstance(tickets, list) or len(tickets) != len(messages):
            raise PushUnavailable("Expo answered no ticket for each message")
        return tickets


def _message(push: Push) -> dict[str, Any]:
    return {
        "to": push.token,
        "title": push.title,
        "body": push.body,
        "data": dict(push.data),
        "sound": "default",
    }


@final
class RecordingPush:
    def __init__(self) -> None:
        #: Everything pushed, in the order it was.
        self.sent: list[Push] = []
        #: Everything it was asked to push, a phone it forgot included.
        self.asked: list[Push] = []
        #: When true, the service cannot be reached: nothing is pushed.
        self.unavailable = False
        self._forgotten: set[str] = set()

    def forget(self, token: str) -> None:
        """The phone was wiped: the service no longer knows it."""

        self._forgotten.add(token)

    def to(self, token: str) -> list[Push]:
        """Everything pushed to one phone."""

        return [push for push in self.sent if push.token == token]

    async def send(self, pushes: Sequence[Push]) -> PushReceipt:
        if self.unavailable:
            raise PushUnavailable("the push service is down")
        self.asked.extend(pushes)
        self.sent.extend(push for push in pushes if push.token not in self._forgotten)
        return PushReceipt(
            gone=frozenset(
                push.token for push in pushes if push.token in self._forgotten
            )
        )
