"""Who the Discovery context hears. **It records no event of its own**, so it
registers nothing in the catalog.

**One listener, the follower**, on every user and Player profile event that
changes what a directory entry holds — the account opened, named or disabled;
the profile committed, its tags, photographs, area or *Show me to new people*
changed (and *Show me in General*'s old event, decode-only, which folds into
the switch). Each names one account, and the follower writes that account's
entry again from what the owners hold now (``docs/adr/0204`` §10). It
**writes**, so it is subscribed per delivery run over that run's session
(``app/bootstrap/events.py``), as the ranking's mover is.

**Here, not in ``application/``**, because the event classes are the owners'
types and the application layer borrows none (``.importlinter``'s
*the-discovery-context-declares-its-own-ports*): this is where an owner's event
is read as *this account changed*.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from app.application.events import DeliveryContext, EventDispatcher
from app.modules.discovery.application.directory import FollowTheDirectory
from app.modules.player_profile.domain.events import (
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    RankingVisibilitySet,
    ShowMeToNewPeopleSet,
    SocialTagsChanged,
)
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    UserDisabled,
    UserNamed,
    UserRegistered,
)

#: Each event that moves an entry, and whose account it names.
_WHOSE: dict[type, Callable[[Any], UUID]] = {
    UserRegistered: lambda event: event.user_id,
    AccountOpenedByInvitation: lambda event: event.user_id,
    UserNamed: lambda event: event.user_id,
    UserDisabled: lambda event: event.user_id,
    PlayerProfileCreated: lambda event: event.player_id,
    SocialTagsChanged: lambda event: event.player_id,
    PhotosChanged: lambda event: event.player_id,
    LocationChanged: lambda event: event.player_id,
    ShowMeToNewPeopleSet: lambda event: event.player_id,
    RankingVisibilitySet: lambda event: event.player_id,
}

#: The events the follower hears — what ``tests/unit`` holds against the
#: directory's fields.
FOLLOWED: tuple[type, ...] = tuple(_WHOSE)


def subscribe_the_directory_follower(
    dispatcher: EventDispatcher, follower: FollowTheDirectory
) -> None:
    """Each owner's event writes its account's entry the moment it is
    delivered."""

    for event_cls, whose in _WHOSE.items():
        dispatcher.subscribe(event_cls, _following(follower, whose))


def _following(
    follower: FollowTheDirectory, whose: Callable[[Any], UUID]
) -> Callable[[Any, DeliveryContext], Any]:
    async def follow(event: Any, context: DeliveryContext) -> None:
        await follower.execute(whose(event))

    return follow
