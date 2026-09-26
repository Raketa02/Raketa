"""The Group's stream.

``docs/adr/0183`` §1 lists the whole of what a group's stream will say. This
build writes thirteen: a player group is **created**, somebody **joins** it, and
on a *People I approve* group somebody **asks** and the Owner **approves** or
**declines** (#505); a member **leaves**, a leaving Owner's group **passes** to
the longest-standing member, the Owner **renames** it, **changes who can join**
and, alone in it, **deletes** it (#506); and an Administrator **creates an
official group**, **sets its WhatsApp size** and **declares its sports** again
(#509) — answering, renaming and changing who can join with the events a player
group's Owner already writes. The handover is its own event and arrives with
the ticket that needs it (#510).

**Each kind is created by its own event**, because every rule that differs by
kind has to say so in its own words and none may be inferred from a null
(``docs/adr/0183`` §1): a player group names its Owner, and an official group
names its Administrator and no Owner at all.

**Declared sports travel as registry codes in the registry's order, and are
forced to a tuple on the way in and out of storage**, as a club's are: the codec
hands a JSON array back as a list, and an event read back must equal the one
appended.

**Every ``*_by`` is an account** — the person who tapped, a User's id — on both
kinds: on an official group it is the account behind its Administrator, so the
history says who let somebody in, as it does on a player group.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlayerGroupCreated:
    """A player created a group at a home club — **and is its Owner and first
    member from this instant**, so there is no separate *joined* for them: the
    group has never existed without its creator in it.

    ``code`` is the one its link will carry for ever (``docs/adr/0183`` §4).
    """

    group_id: UUID
    name: str
    home_club_id: UUID
    join_policy: str
    owner_id: UUID
    code: str
    occurred_at: datetime


@dataclass(frozen=True)
class OfficialGroupCreated:
    """An Administrator created an official group for their club
    (``docs/adr/0183`` §3) — one per WhatsApp group they run.

    **No Owner, and nobody in it**: running an official group is not
    membership, so the Administrator is not its first member — an Administrator
    who plays joins it like anybody, and directly (§7). ``administrator_id`` is
    the Administrator who runs it, ``created_by`` the account that tapped
    *Create*. ``home_club_id`` is the Administrator's club, fixed. ``sports``
    are registry codes in the registry's order; ``whatsapp_size`` limits
    nothing. ``code`` is the one its link will carry for ever (§4).
    """

    group_id: UUID
    name: str
    home_club_id: UUID
    join_policy: str
    administrator_id: UUID
    created_by: UUID
    whatsapp_size: int
    sports: tuple[str, ...]
    code: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "sports", tuple(self.sports))


@dataclass(frozen=True)
class WhatsAppSizeSet:
    """Its Administrator changed how many people the WhatsApp group an official
    group mirrors has (``docs/adr/0183`` §3) — the club's *From WhatsApp*
    denominator, which limits nothing. Official groups only."""

    group_id: UUID
    whatsapp_size: int
    set_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SportsDeclared:
    """Its Administrator declared what an official group plays again — the whole
    set, as the settings hold it, registry codes in the registry's order
    (``docs/adr/0183`` §3). Its dots move on the next read. Official groups
    only."""

    group_id: UUID
    sports: tuple[str, ...]
    declared_by: UUID
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "sports", tuple(self.sports))


@dataclass(frozen=True)
class GroupJoined:
    """A player became a Group member. Recorded once per joining: joining a
    group you are already in records nothing (``docs/adr/0183`` §7)."""

    group_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinRequested:
    """A player asked to join a *People I approve* group, and their Join request
    waits for whoever answers it. **At most one waits per player per group**:
    asking again while waiting records nothing (``docs/adr/0183`` §7)."""

    group_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinRequestApproved:
    """The Owner approved a Join request — **and the person is a Group member
    from this instant**, so there is no separate *joined* beside it: approving
    is admitting, and one act is one event. ``approved_by`` is who answered,
    because ownership passes (#506) and the history should still say who let
    somebody in."""

    group_id: UUID
    player_id: UUID
    approved_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinRequestDeclined:
    """The Owner declined a Join request. **Silent**: the request is gone, the
    person's relation to the group is *none* again and they may ask again, and
    nothing tells them (``docs/adr/0183`` §7). The stream remembers it; no read
    serves it."""

    group_id: UUID
    player_id: UUID
    declined_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class GroupLeft:
    """A Group member left. They may join again later, under whatever the
    group's policy is then — and a joining after this one is a new one, so
    *how long they have been in* starts again (``docs/adr/0183`` §7)."""

    group_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class OwnershipPassed:
    """The Owner left a group other people are in, and it passed to the member
    who had been in longest (``docs/adr/0183`` §7) — so the group keeps somebody
    who can approve people, and the queue waiting on it passes with it.

    **Recorded before the Owner's ``GroupLeft``**, so at no point in the stream
    is the Owner somebody who is not in the group."""

    group_id: UUID
    from_id: UUID
    to_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class JoinPolicyChanged:
    """The Owner changed who can join (``docs/adr/0183`` §7).

    **Switching to *Anyone* admits everybody waiting at once**, because nobody
    should be left waiting under a rule that no longer applies — and each of
    those admissions is its own ``JoinRequestApproved``, recorded right after
    this and answered by whoever made the switch: letting a waiting person in is
    what approving already records, and a separate spelling of it would be a
    second way for somebody to become a member."""

    group_id: UUID
    join_policy: str
    changed_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class GroupRenamed:
    """The Owner renamed the group. **Its code does not move**, so every post of
    its link still finds it, and its monogram's colour stays because it is
    derived from the id (``docs/adr/0183`` §4, §5). ``name`` is as recorded:
    trimmed and collapsed."""

    group_id: UUID
    name: str
    renamed_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class GroupDeleted:
    """The Owner deleted a group nobody else was in (``docs/adr/0183`` §7).
    **The end of the stream**: the group is in no list and no search, its link
    reads *nothing at that link*, and whatever requests were waiting on it are
    gone with it."""

    group_id: UUID
    deleted_by: UUID
    occurred_at: datetime
