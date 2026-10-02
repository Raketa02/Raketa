"""The register of push services, and the questions every one of them answers
(#549).

**A kind of its own, as ``payments_demands.py`` is**: the two adapters of one
port onto the outside world — Expo's, and the recording one every API test, a
seed run and a laptop that pushes nowhere stand on — so
``tests/demands/test_push_demands.py`` asks both the same questions, and a
recording service that drifts from Expo goes red rather than green.

**Expo is asked over a loopback server speaking its documented API**, never
Expo itself: a test has no phone to push to, and a push to a made-up token is a
request to a service the suite does not own. What that leaves unproven is that
Expo still answers as its documentation says.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.bootstrap.composition import build_push_notifications, build_recording_push
from app.core.config import PushProvider, Settings
from app.modules.notifications.domain.ports import PushNotifications


@dataclass(frozen=True)
class RegisteredPushService:
    """One adapter of the push service, and how to build it over settings —
    for Expo, settings naming where Expo is."""

    name: str
    build: Callable[[Settings], PushNotifications]


PUSH_IMPLEMENTATIONS: tuple[RegisteredPushService, ...] = (
    RegisteredPushService(
        name="RecordingPush", build=lambda settings: build_recording_push()
    ),
    RegisteredPushService(
        name="ExpoPush",
        build=lambda settings: build_push_notifications(
            settings.model_copy(update={"PUSH_PROVIDER": PushProvider.EXPO})
        ),
    ),
)


__all__ = ["PUSH_IMPLEMENTATIONS", "RegisteredPushService"]
