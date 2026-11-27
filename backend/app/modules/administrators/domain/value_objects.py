from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Name:
    """What a club calls the person it invites to run its official groups
    (``docs/adr/0184`` §1) — **the Administrator's**, and never a player's
    (``docs/adr/0199`` §4).

    Free text: trimmed, runs of whitespace collapsed to one space, 2–64
    characters after that, and **never unique** — it is checked against nobody.
    *Marta Wójcik* and *Marta W.* are both names. The club's own pages and the
    Administrator's own emails use it, and one player surface reads it: *"… runs
    this group"*, for an Administrator with no nickname yet. A player has no
    Name in Rakieta, only a nickname.

    It lived in ``users`` until ADR-0199 retired the player's Name, and moved
    here with the one holder it has left.
    """

    value: str

    def __post_init__(self) -> None:
        # ``split()`` with no argument splits on any run of whitespace and drops
        # the ends, so this is the trim and the collapse in one step.
        v = " ".join(self.value.split())
        if not (2 <= len(v) <= 64):
            raise ValueError(f"invalid name: {self.value!r}")
        object.__setattr__(self, "value", v)
