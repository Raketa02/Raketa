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
- **nobody sends an eleventh request in a Warsaw day to somebody they share no
  group with** (#773) — the use case reads how many they sent and whether this
  one counts; a crossing never counts;
- a request made of somebody who asked you first crosses it: friends at once;
- only the person asked accepts or sets it aside, and *Not now* keeps it open;
- the person asked who opens the requester's link brings back a request they
  set aside onto their Home (#748) — never one hidden from them;
- only the requester cancels, and only a friend removes; both are silent no-ops
  when there is nothing to take back, so a route answers alike either way;
- a block ends whatever stands, and is a no-op when nothing does;
- **only a friend is asked for a level, once per sport, ever** (#749) — the
  asks outlive the friendship, so one removed and made again asks nobody
  twice — and the friend's first level in that sport answers the ask once;
- **only the friend asked sets an ask aside**, once, and it stays waiting for
  the level (#764).

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
    FriendNotFound,
    FriendRequestAlreadySent,
    FriendRequestNotFound,
    LevelAlreadyAsked,
)
from app.modules.friends.domain.events import (
    FriendRequestBroughtBack,
    FriendRequestCancelled,
    FriendRequestCrossed,
    FriendRequested,
    FriendRequestSetAside,
    FriendshipEnded,
    FriendsMade,
    LevelAsked,
    LevelAskSetAside,
    LevelGot,
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
    on a group's screen. **The ranking's names its sport and no group** (#773):
    the Rankings page is one sport's and no group's, and the card reads *Found
    you in the padel ranking*. **New in Raketa's names neither** (#793): its
    card reads *Found you among new players* and nothing more. **Same
    competitive level's names its sport and no group** (#794): the card reads
    *Your level in padel · 91% even*."""

    made_from: RequestOrigin
    group_id: UUID | None = None
    sport: Sport | None = None

    def __post_init__(self) -> None:
        invariant(
            self.made_from is not RequestOrigin.LINK
            or (self.group_id is None and self.sport is None),
            f"a link's request names a group or a sport: {self!r}",
        )
        invariant(
            self.made_from is not RequestOrigin.RANKING
            or (self.group_id is None and self.sport is not None),
            f"a ranking's request names a group, or no sport: {self!r}",
        )
        invariant(
            self.made_from is not RequestOrigin.NEW_PLAYERS
            or (self.group_id is None and self.sport is None),
            f"a new player's request names a group or a sport: {self!r}",
        )
        invariant(
            self.made_from is not RequestOrigin.SAME_LEVEL
            or (self.group_id is None and self.sport is not None),
            f"a same level request names a group, or no sport: {self!r}",
        )

    @classmethod
    def pressed_on(
        cls, made_from: RequestOrigin, *, group_id: UUID | None, sport: Sport | None
    ) -> "Where":
        """Where a client says a request was pressed — **the ranking's group
        dropped**, since the Rankings page shows none (#773), **New in
        Raketa's group and sport** both, since its line names neither (#793),
        and **Same competitive level's group**, since its row shows none
        (#794)."""

        if made_from in (
            RequestOrigin.RANKING,
            RequestOrigin.NEW_PLAYERS,
            RequestOrigin.SAME_LEVEL,
        ):
            group_id = None
        if made_from is RequestOrigin.NEW_PLAYERS:
            sport = None
        return cls(made_from=made_from, group_id=group_id, sport=sport)

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


@dataclass(frozen=True, slots=True)
class LevelAsk:
    """One **Ask for a level** (#749): ``asker_id`` asked the other side of the
    pair to get a level in ``sport``, from ``group_id``'s picker — when the
    other set it aside (*Not now*, #764), and when the other's first level in
    it answered the ask, set aside or not."""

    asker_id: UUID
    sport: Sport
    group_id: UUID
    asked_at: Instant
    got_at: Instant | None = None
    set_aside_at: Instant | None = None


@dataclass
class Friendship:
    """What stands between two players, as their stream leaves it — and every
    ask for a level either ever made of the other, which nothing ends."""

    first_id: UUID
    second_id: UUID
    are_friends: bool = False
    #: When they became friends, while they are.
    friends_since: Instant | None = None
    request: OpenRequest | None = None
    version: int = 0
    _level_asks: dict[tuple[UUID, Sport], LevelAsk] = field(
        default_factory=dict, init=False, repr=False
    )
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
        self,
        *,
        requester: UUID,
        where: Where,
        at: Instant,
        unseen: bool = False,
    ) -> FriendRelation:
        """The requester asks the other. Answers the requester's relation now:
        *sent*, or *friend* when the request crossed one made of them.

        ``unseen`` — the other had blocked the requester — records a request the
        other never sees; **the requester's answer is the same**. **Nothing
        limits how many a requester sends** (``docs/adr/0204`` §2)."""

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

    def bring_back(self, *, by: UUID, at: Instant) -> None:
        """The person asked opened the requester's link: a request they set aside
        is back on their Home. **A no-op** on a request already there, on one
        hidden from them as ``unseen`` — which they never see, not after an
        unblock either — and on anything but a request made of them."""

        self._other_than(by)
        request = self.request
        if request is None or request.addressee_id != by:
            return
        if not request.set_aside or request.unseen:
            return
        self._record_that(
            FriendRequestBroughtBack(
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

    # -- asking for a level (#749) ----------------------------------------

    @property
    def level_asks(self) -> tuple[LevelAsk, ...]:
        """Every ask either side ever made of the other, in the order made."""

        return tuple(self._level_asks.values())

    def ask_for_a_level(
        self, *, asker: UUID, sport: Sport, group_id: UUID, at: Instant
    ) -> None:
        """The asker asks their friend to get a level in ``sport``. **Only a
        friend**, and **once per sport, ever**: an ask outlives the friendship,
        answered or not. Whether the friend has a level already is the rating's,
        which the use case reads."""

        friend = self._other_than(asker)
        if not self.are_friends:
            raise FriendNotFound()
        if (asker, sport) in self._level_asks:
            raise LevelAlreadyAsked()
        self._record_that(
            LevelAsked(
                asker_id=asker,
                friend_id=friend,
                sport=sport.value,
                group_id=group_id,
                occurred_at=at,
            )
        )

    def answer_the_ask(self, *, friend: UUID, sport: Sport, at: Instant) -> None:
        """The friend has a level in ``sport`` now: the other's ask, if they made
        one, is answered — ``friends.level_got``. **A no-op** with nothing
        asked, or the ask already answered — a delivery seen twice records
        nothing twice."""

        asker = self._other_than(friend)
        ask = self._level_asks.get((asker, sport))
        if ask is None or ask.got_at is not None:
            return
        self._record_that(
            LevelGot(
                asker_id=asker,
                friend_id=friend,
                sport=sport.value,
                group_id=ask.group_id,
                occurred_at=at,
            )
        )

    def set_aside_the_ask(self, *, by: UUID, sport: Sport, at: Instant) -> None:
        """**Not now** (#764): ``by`` sets aside the other's ask of them in
        ``sport`` — off their Home, and still waiting for the level, which
        answers it as it answers any ask. **Only the friend asked**: the press
        is about an ask made *of* ``by``, so the asker's own is never touched.
        **A no-op** with nothing asked of them in the sport, the ask answered,
        or set aside already — so a press on a card just gone records
        nothing."""

        asker = self._other_than(by)
        ask = self._level_asks.get((asker, sport))
        if ask is None or ask.got_at is not None or ask.set_aside_at is not None:
            return
        self._record_that(
            LevelAskSetAside(
                asker_id=asker, friend_id=by, sport=sport.value, occurred_at=at
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
        elif isinstance(event, FriendRequestBroughtBack):
            request = invariant(self.request, "brought back with nothing asked")
            self.request = replace(request, set_aside=False)
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
            # The asks for a level stay: once per sport is ever.
            self.request = None
            self.are_friends = False
            self.friends_since = None
        elif isinstance(event, LevelAsked):
            sport = Sport(event.sport)
            self._level_asks[(event.asker_id, sport)] = LevelAsk(
                asker_id=event.asker_id,
                sport=sport,
                group_id=event.group_id,
                asked_at=instant(event.occurred_at),
            )
        elif isinstance(event, LevelGot):
            key = (event.asker_id, Sport(event.sport))
            ask = invariant(self._level_asks.get(key), "a level got, nothing asked")
            self._level_asks[key] = replace(ask, got_at=instant(event.occurred_at))
        elif isinstance(event, LevelAskSetAside):
            key = (event.asker_id, Sport(event.sport))
            ask = invariant(self._level_asks.get(key), "set aside, nothing asked")
            self._level_asks[key] = replace(
                ask, set_aside_at=instant(event.occurred_at)
            )
        else:
            raise TypeError(f"Unsupported friendship event {event!r}")
        self.version += 1


def _where(made_from: str, group_id: UUID | None, sport: str | None) -> Where:
    return Where(
        made_from=RequestOrigin(made_from),
        group_id=group_id,
        sport=None if sport is None else Sport(sport),
    )
