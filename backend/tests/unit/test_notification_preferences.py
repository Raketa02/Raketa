"""**Notification preferences** — one stream per player (#549; the mechanics
§17.2; the screens A7.2).

Three choices, each the player's: *You complete it* and *Challenges for you*
on until switched off, *Fill in alerts* off until switched on. And the phones a
push reaches: registered, removed, never twice.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import instant
from app.modules.notifications.domain.errors import PushTokenInvalid
from app.modules.notifications.domain.events import (
    NotificationChoiceSwitched,
    PushDeviceRegistered,
    PushDeviceRemoved,
)
from app.modules.notifications.domain.preferences import (
    DEVICES_KEPT,
    NotificationChoice,
    NotificationPreferences,
    device_of,
)
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 10, 5, 8, tzinfo=timezone.utc))
PHONE = "ExponentPushToken[ola-phone-1]"


def a_player() -> NotificationPreferences:
    return NotificationPreferences.from_history(new_uuid(), [])


def test_a_player_who_never_chose_has_the_defaults():
    preferences = a_player()

    assert preferences.choices == {
        NotificationChoice.YOU_COMPLETE_IT: True,
        NotificationChoice.CHALLENGES_FOR_YOU: True,
        NotificationChoice.FILL_IN_ALERTS: False,
    }
    assert preferences.devices == ()


def test_switching_a_choice_records_it_and_the_same_answer_records_nothing():
    preferences = a_player()

    preferences.switch(NotificationChoice.FILL_IN_ALERTS, on=True, at=AT)
    preferences.switch(NotificationChoice.FILL_IN_ALERTS, on=True, at=AT)
    preferences.switch(NotificationChoice.YOU_COMPLETE_IT, on=True, at=AT)

    assert preferences.wants(NotificationChoice.FILL_IN_ALERTS)
    [switched] = preferences.pull_events()
    assert isinstance(switched, NotificationChoiceSwitched)
    assert (switched.choice, switched.on) == ("FILL_IN_ALERTS", True)


def test_a_stream_folds_back_to_what_was_chosen():
    preferences = a_player()
    preferences.switch(NotificationChoice.CHALLENGES_FOR_YOU, on=False, at=AT)
    preferences.register(PHONE, at=AT)

    again = NotificationPreferences.from_history(
        preferences.player_id, preferences.pull_events()
    )

    assert not again.wants(NotificationChoice.CHALLENGES_FOR_YOU)
    assert again.devices == (device_of(PHONE),)
    assert again.version == 2


def test_a_phone_is_registered_once_and_removed_once():
    preferences = a_player()

    preferences.register(PHONE, at=AT)
    preferences.register(PHONE, at=AT)
    assert preferences.remove(device_of(PHONE), at=AT) is True
    assert preferences.remove(device_of(PHONE), at=AT) is False

    assert [type(event) for event in preferences.pull_events()] == [
        PushDeviceRegistered,
        PushDeviceRemoved,
    ]
    assert preferences.devices == ()


def test_the_stream_names_a_phone_and_never_holds_its_token():
    preferences = a_player()

    preferences.register(PHONE, at=AT)

    [registered] = preferences.pull_events()
    assert isinstance(registered, PushDeviceRegistered)
    assert PHONE not in repr(registered)
    assert registered.device == device_of(PHONE)
    # The act that registered it hands the token on to where it is kept.
    assert preferences.token_of(device_of(PHONE)) == PHONE


@pytest.mark.parametrize(
    "token",
    ["", "not-a-token", "ExponentPushToken[]", "ExponentPushToken[" + "x" * 300 + "]"],
)
def test_only_an_expo_push_token_is_a_phone(token):
    with pytest.raises(PushTokenInvalid):
        a_player().register(token, at=AT)


def test_the_newer_spelling_of_an_expo_token_is_one_too():
    preferences = a_player()

    preferences.register("ExpoPushToken[abc-123]", at=AT)

    assert preferences.devices == (device_of("ExpoPushToken[abc-123]"),)


def test_past_the_phones_kept_the_oldest_is_let_go():
    preferences = a_player()
    tokens = [f"ExponentPushToken[phone-{n}]" for n in range(DEVICES_KEPT + 1)]

    for token in tokens:
        preferences.register(token, at=AT)

    assert preferences.devices == tuple(device_of(token) for token in tokens[1:])
    removed = [
        event
        for event in preferences.pull_events()
        if isinstance(event, PushDeviceRemoved)
    ]
    assert [event.device for event in removed] == [device_of(tokens[0])]
