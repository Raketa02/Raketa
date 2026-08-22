"""Who a movement is between: player · club · Raketa, and nothing else.

ADR-0056 draws the parties from a closed set of three and makes one of them a
rule rather than a convention: **a club is only ever a payee, never a payer**
(ADR-0045). That is refused at construction here *and* asserted over the stored
movements by the reconciliation, because the two failures are different — a bug
in a use case, and a row that reached disk before the rule existed.

**Three ``@final`` members and a union, not an enum with an optional id.** A
party is *which kind* and *which one*, and the two are not independent: Raketa
has no id and a player and a club always have one. An enum plus a nullable
``party_id`` admits ``RAKETA`` with an id and ``PLAYER`` without one — two
states nothing means, both of which typecheck. The union makes them unwritable,
and ``exhaustive`` closes a match over it so a fourth party fails the build at
every place that does not handle it. Same shape as the kernel's ``ClubCard``.

**The kind and the id are what cross into an event**, because an event carries
primitive fields (``events.py``); ``party_kind`` and ``party_id`` are that
projection and ``party_from`` is its inverse. They are here, beside the type,
rather than in the aggregate — a party that can be written to a stream one way
and read back another is a party with two definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias, final
from uuid import UUID

from app.kernel import exhaustive, invariant


class PartyKind(str, Enum):
    """The three names a party may have, as it is stored.

    A durable contract: these strings are in the payload of every movement ever
    written, so renaming one is a migration and not a refactor.
    """

    PLAYER = "player"
    CLUB = "club"
    RAKETA = "raketa"


@final
@dataclass(frozen=True)
class PlayerParty:
    """A player, by the id Users minted for her."""

    player_id: UUID


@final
@dataclass(frozen=True)
class ClubParty:
    """A club, by the id Clubs minted for it. **Only ever a payee.**"""

    club_id: UUID


@final
@dataclass(frozen=True)
class RaketaParty:
    """The platform. There is one, so it carries no id.

    Giving it an id would make *which Raketa* a question, and the answer would
    be a constant somebody would eventually make configurable.
    """


#: One of exactly three. See the module docstring for why this is a union and
#: not an enum beside a nullable id.
Party: TypeAlias = PlayerParty | ClubParty | RaketaParty


def party_kind(party: Party) -> PartyKind:
    """Which of the three this is, as it is stored."""

    match party:
        case PlayerParty():
            return PartyKind.PLAYER
        case ClubParty():
            return PartyKind.CLUB
        case RaketaParty():
            return PartyKind.RAKETA
        case _:
            exhaustive(party)


def party_id(party: Party) -> UUID | None:
    """Which player or which club, or nothing for Raketa."""

    match party:
        case PlayerParty(player_id):
            return player_id
        case ClubParty(club_id):
            return club_id
        case RaketaParty():
            return None
        case _:
            exhaustive(party)


def party_from(kind: PartyKind, identity: UUID | None) -> Party:
    """Rebuild a party from what a stored event carries.

    Refuses the two combinations the union makes unwritable, so a payload that
    was hand-edited or written by an older shape fails loudly here rather than
    producing a party with an id nobody can use.
    """

    match kind:
        case PartyKind.PLAYER:
            invariant(identity is not None, "a player party with no player id")
            assert identity is not None  # narrowed by the invariant above
            return PlayerParty(identity)
        case PartyKind.CLUB:
            invariant(identity is not None, "a club party with no club id")
            assert identity is not None  # narrowed by the invariant above
            return ClubParty(identity)
        case PartyKind.RAKETA:
            invariant(identity is None, f"the platform party carries an id: {identity}")
            return RaketaParty()
        case _:
            exhaustive(kind)


def player_of(*parties: Party) -> UUID | None:
    """The one player among these parties, or nothing.

    Refuses two: a ``player → player`` movement has no meaning in this model —
    Raketa is a party to every transfer between people — and it would be the one
    movement with a claim on two streams, which ADR-0055 forbids by name.
    """

    players = [party.player_id for party in parties if isinstance(party, PlayerParty)]
    invariant(len(players) <= 1, f"a movement between {len(players)} players")
    return players[0] if players else None
