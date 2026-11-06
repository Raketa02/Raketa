"""The Friendship aggregate — event-sourced, one stream per **unordered** pair
(``docs/adr/0202`` §1, §8).

**At most one thing stands between two players**: a friendship, or one open
request, or nothing. Two open requests can never stand at once, because the
second one *crosses* the first and they are friends on the spot — so the whole
state is ``are_friends`` and at most one ``OpenRequest``.

**The rules live here**, so a seed run or a later route cannot route around
them:

- nobody asks themselves, nobody asks a friend, and nobody asks while their own
  request to that person is open, set aside or not;
- a request made of somebody who asked you first crosses it: friends at once;
- only the person asked accepts or sets it aside, and *Not now* keeps it open;
- only the requester cancels, and only a friend removes; both are silent no-ops
  when there is nothing to take back, so a route answers alike either way;
- a block ends whatever stands, and is a no-op when nothing does.

**A request the addressee never sees** — asked while they had blocked the
requester, which the use case reads — is recorded ``unseen``: the requester
reads *request sent*, the addressee ``NONE``, and nothing the addressee does
answers it. One asked before a block that is not delivered yet is hidden at
every read, live, from the reader's own blocks (``application/reads.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.friends.domain.errors import (
    AlreadyFriends,
    CannotBefriendYourself,
    FriendRequestAlreadySent,
    FriendRequestNotFound,
)
from app.modules.friends.domain.events import (
    FriendRequestCancelled,
    FriendRequestCrossed,
    FriendRequested,
    FriendRequestSetAside,
    FriendshipEnded,
    FriendsMade,
)
from app.modules.friends.domain.ids import friendship_id, ordered_pair
from app.modules.friends.domain.relation import (
    FriendRelation,
    HowFriendsWereMade,
    HowItEnded,
    RequestOrigin,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass(frozen=True, slots=True)
class Where:
    """Where a request was made: the screen, and the group and sport it showed,
    when it showed one. **A link's names neither**: it was opened, not pressed
    on a group's screen."""

    made_from: RequestOrigin
    group_id: UUID | None = None
    sport: Sport | None = None

    def __post_init__(self) -> None:
        invariant(
            self.made_from is not RequestOrigin.LINK
            or (self.group_id is None and self.sport is None),
            f"a link's request names a group or a sport: {self!r}",
        )

    def without_the_group(self) -> "Where":
        """The same screen, naming no group — one the two do not share."""

        return Where(made_from=self.made_from, sport=self.sport)


@dataclass(frozen=True, slots=True)
class OpenRequest:
    requester_id: UUID
    addressee_id: UUID
    where: Where
    asked_at: Instant
    #: *Not now*: off the reader's Home, still open.
    set_aside: bool = False
    #: Asked while the addressee had blocked the requester: never shown to the
    #: addressee, for as long as it stays open (``FriendRequested.unseen``).
    unseen: bool = False


@dataclass
class Friendship:
    """What stands between two players, as their stream leaves it."""

    first_id: UUID
    second_id: UUID
    are_friends: bool = False
    #: When they became friends, while they are.
    friends_since: Instant | None = None
    request: OpenRequest | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def between(cls, one: UUID, other: UUID) -> "Friendship":
        """A pair with no history: nothing stands between them yet."""

        if one == other:
            raise CannotBefriendYourself()
        first, second = ordered_pair(one, other)
        return cls(first_id=first, second_id=second)

    @classmethod
    def from_history(
        cls, one: UUID, other: UUID, events: Iterable[DomainEvent]
    ) -> "Friendship":
        friendship = cls.between(one, other)
        for event in events:
            friendship._apply(event)
        return friendship

    @property
    def id(self) -> UUID:
        return friendship_id(self.first_id, self.second_id)

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def relation_of(self, reader: UUID) -> FriendRelation:
        """The reader's relation to the other — **before** any block hides a
        request from them, which is the reader's own read to make."""

        self._other_than(reader)
        if self.are_friends:
            return FriendRelation.FRIEND
        if self.request is None:
            return FriendRelation.NONE
        if self.request.requester_id == reader:
            return FriendRelation.SENT
        # A request the addressee never sees is nothing, from their side.
        return FriendRelation.NONE if self.request.unseen else FriendRelation.ASKED_YOU

    # -- asking -----------------------------------------------------------

    def ask(
        self, *, requester: UUID, where: Where, at: Instant, unseen: bool = False
    ) -> FriendRelation:
        """The requester asks the other. Answers the requester's relation now:
        *sent*, or *friend* when the request crossed one made of them.

        ``unseen`` — the other had blocked the requester — records a request the
        other never sees; **the requester's answer is the same**."""

        addressee = self._other_than(requester)
        if self.are_friends:
            raise AlreadyFriends()
        if self.request is not None and self.request.requester_id == requester:
            raise FriendRequestAlreadySent()
        if self.request is not None:
            # They asked first, and have not been answered: crossed.
            first_asker = self.request.requester_id
            self._record_that(
                FriendRequestCrossed(
                    requester_id=requester,
                    addressee_id=addressee,
                    made_from=where.made_from.value,
                    group_id=where.group_id,
                    sport=None if where.sport is None else where.sport.value,
                    occurred_at=at,
                )
            )
            self._record_that(
                FriendsMade(
                    requester_id=first_asker,
                    addressee_id=requester,
                    how=HowFriendsWereMade.CROSSED.value,
                    occurred_at=at,
                )
            )
            return FriendRelation.FRIEND
        self._record_that(
            FriendRequested(
                requester_id=requester,
                addressee_id=addressee,
                made_from=where.made_from.value,
                group_id=where.group_id,
                sport=None if where.sport is None else where.sport.value,
                occurred_at=at,
                unseen=unseen,
            )
        )
        return FriendRelation.SENT

    # -- answering --------------------------------------------------------

    def accept(self, *, by: UUID, at: Instant) -> None:
        request = self._asked_of(by)
        self._record_that(
            FriendsMade(
                requester_id=request.requester_id,
                addressee_id=by,
                how=HowFriendsWereMade.ACCEPTED.value,
                occurred_at=at,
            )
        )

    def set_aside(self, *, by: UUID, at: Instant) -> None:
        """*Not now*. A no-op on a request already set aside."""

        request = self._asked_of(by)
        if request.set_aside:
            return
        self._record_that(
            FriendRequestSetAside(
                requester_id=request.requester_id, addressee_id=by, occurred_at=at
            )
        )

    # -- taking back ------------------------------------------------------

    def cancel(self, *, by: UUID, at: Instant) -> None:
        """The requester takes their request back. **A no-op** when no request of
        theirs is open — never made, answered, or ended by a block — so the
        route answers alike in every case."""

        addressee = self._other_than(by)
        if self.request is None or self.request.requester_id != by:
            return
        self._record_that(
            FriendRequestCancelled(
                requester_id=by, addressee_id=addressee, occurred_at=at
            )
        )

    def remove(self, *, by: UUID, at: Instant) -> None:
        """A friend removes the other. **A no-op** when they are not friends."""

        other = self._other_than(by)
        if not self.are_friends:
            return
        self._record_that(
            FriendshipEnded(
                ended_by=by,
                other_id=other,
                how=HowItEnded.REMOVED.value,
                occurred_at=at,
            )
        )

    def end_by_a_block(self, *, blocker: UUID, at: Instant) -> None:
        """A block ends the friendship **and** any open request, either way
        round. A no-op when nothing stands between them."""

        other = self._other_than(blocker)
        if not self.are_friends and self.request is None:
            return
        self._record_that(
            FriendshipEnded(
                ended_by=blocker,
                other_id=other,
                how=HowItEnded.BLOCKED.value,
                occurred_at=at,
            )
        )

    # -- folding ----------------------------------------------------------

    def _asked_of(self, reader: UUID) -> OpenRequest:
        self._other_than(reader)
        if (
            self.request is None
            or self.request.addressee_id != reader
            or self.request.unseen
        ):
            raise FriendRequestNotFound()
        return self.request

    def _other_than(self, player: UUID) -> UUID:
        if player == self.first_id:
            return self.second_id
        if player == self.second_id:
            return self.first_id
        raise ValueError(f"{player} is not a side of this friendship")

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, FriendRequested):
            self.request = OpenRequest(
                requester_id=event.requester_id,
                addressee_id=event.addressee_id,
                where=_where(event.made_from, event.group_id, event.sport),
                asked_at=instant(event.occurred_at),
                unseen=event.unseen,
            )
        elif isinstance(event, FriendRequestSetAside):
            request = invariant(self.request, "set aside with nothing asked")
            self.request = replace(request, set_aside=True)
        elif isinstance(event, FriendRequestCancelled):
            self.request = None
        elif isinstance(event, FriendRequestCrossed):
            # The crossing is recorded for what it is; ``FriendsMade`` beside it
            # is what makes them friends.
            pass
        elif isinstance(event, FriendsMade):
            self.request = None
            self.are_friends = True
            self.friends_since = instant(event.occurred_at)
        elif isinstance(event, FriendshipEnded):
            self.request = None
            self.are_friends = False
            self.friends_since = None
        else:
            raise TypeError(f"Unsupported friendship event {event!r}")
        self.version += 1


def _where(made_from: str, group_id: UUID | None, sport: str | None) -> Where:
    return Where(
        made_from=RequestOrigin(made_from),
        group_id=group_id,
        sport=None if sport is None else Sport(sport),
    )
