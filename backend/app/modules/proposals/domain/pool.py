"""The Pool: the players who may be dealt a game, plus the clubs whose courts
they may use (``docs/adr/0189`` §1; the glossary's *Pool*).

**First-class, and a group is only its first kind.** Every proposal carries its
pool and nothing in this context names a group where it means a pool, so the
city-wide pool Explore will need is one more kind rather than a rewrite. Who is
in a pool is asked of whatever the pool is made of — a group's members, for a
group — through a port, and never by joining a table.

**A group's pool is filed under the group's own id**, as a club's courts are
under the club's and a player's payment method under the player's. It holds no
fact of its own — a group's pool is its group — so it is not an aggregate: the
``pools`` table is a projection of the proposals made in it, its row written by
the first one, and a group nobody proposed a game in has a pool that simply has
no row yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final
from uuid import UUID


class PoolKind(StrEnum):
    """What a pool is made of."""

    #: A group's members, at the group's home club and the courts around it.
    GROUP = "GROUP"


@final
@dataclass(frozen=True, slots=True)
class Pool:
    id: UUID
    kind: PoolKind
