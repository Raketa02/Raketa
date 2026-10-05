"""The Notifications context's refusals: a phone's push token the push service
would not take."""

from __future__ import annotations

from app.shared.domain import BadRequestError


class PushTokenInvalid(BadRequestError):
    """Not an Expo push token — ``ExponentPushToken[…]`` or ``ExpoPushToken[…]``,
    as the phone's notifications library hands one out. Nothing was saved."""

    code = "push_token_invalid"

    def __init__(self) -> None:
        super().__init__("not an Expo push token")
