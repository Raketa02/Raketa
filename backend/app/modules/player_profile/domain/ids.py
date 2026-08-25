"""Identity in the Player profile context.

A **Player** is a User acting in the player app — its identity *is* the
``UserId`` (``../../../../CONTEXT.md``). ``PlayerId`` is declared here rather
than imported from the rating context for the reason ADR-0018 declined a shared
event-sourced base: a type shared between two contexts is a coupling neither of
them asked for, and the day one of them needs a player to be something else the
shared type is the thing that has to be untangled first.

**A profile's stream id is the player id itself.** There is no derivation and no
namespace, because there is nothing to derive *from* — a Skill rating is keyed on
``(player, sport)`` and needs a function to collapse the pair, where a profile is
keyed on the player and only the player (``docs/adr/0089``). One player therefore
has exactly one profile stream, and the store's own uniqueness on
``(aggregate_type, aggregate_id, version)`` is what makes *at most one profile
per player* something the database enforces rather than something a
read-before-write hopes for.
"""

from __future__ import annotations

from typing import NewType
from uuid import UUID

PlayerId = NewType("PlayerId", UUID)
