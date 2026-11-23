"""A For-fun table's **Social vibe**, as Proposals asks it (``docs/adr/0207``
§2, #830): the people at the table, and the tags each holds now.

**One rule, borrowed twice and kept nowhere.** The tags that don't count are
the Player profile's, beside its vocabulary (``counted``), and the arithmetic
is the Match Fit engine's (``social_vibe``); this is only where Proposals hands
one to the other, so the deck, the details, the Friends card and Post a game's
fits all ask the same question in the same words. Nothing is stored: it is
worked out from the current tags on every read.

**The table is whoever the caller names** — on a card, everybody on the
reader's version: the people In, the reader and the names dealt. An empty seat
is nobody, so it is not at the table. Somebody whose tags aren't known carries
none: they share nothing, and they are still one of the others a tag could be
carried by.

**The details add the grid** (``docs/adr/0207`` §6, #833): the card's number,
and one row per tag **the reader** holds — 💘 too, which is shown and never
counted — each naming everybody at the table who carries it. The number says
how much the whole table shares; the rows say who shares the reader's.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import final
from uuid import UUID

from app.engines.matchfit.v1 import social_vibe, social_vibe_share
from app.kernel import invariant
from app.modules.player_profile.domain.social_tags import (
    SocialTag,
    counted,
    in_vocabulary_order,
)


def social_vibe_of(
    table: Iterable[UUID], tags: Mapping[UUID, Collection[SocialTag]]
) -> int | None:
    """The whole percent a card shows for these people at one table — ``None``
    with fewer than two of them, when nothing is drawn."""

    return social_vibe([counted(tags.get(player, ())) for player in table])


def social_vibe_share_of(
    table: Iterable[UUID], tags: Mapping[UUID, Collection[SocialTag]]
) -> Fraction | None:
    """The same table's vibe **exact, before it is rounded** — what For fun
    ranks tables by when it builds them (``docs/adr/0207`` §1, #831), so two
    tables a card would print alike are still told apart."""

    return social_vibe_share([counted(tags.get(player, ())) for player in table])


@final
@dataclass(frozen=True, slots=True)
class VibeRow:
    """One row of a For-fun game's grid: one of the reader's tags, and
    everybody at the table who carries it — the reader first, so never
    nobody."""

    tag: SocialTag
    carried_by: tuple[UUID, ...]


@final
@dataclass(frozen=True, slots=True)
class TableVibe:
    """A For-fun table's Social vibe as its details draw it: the card's own
    number, and the reader's rows."""

    pct: int
    rows: tuple[VibeRow, ...]


def table_vibe_of(
    reader: UUID,
    table: Sequence[UUID],
    tags: Mapping[UUID, Collection[SocialTag]],
) -> TableVibe | None:
    """The vibe of ``table`` — the reader among them — and a row for each tag
    the reader holds, **in the vocabulary's order**, each carried by the
    reader and then by whoever else at the table holds it, in ``table``'s
    order. ``None`` exactly when the card draws no vibe: fewer than two at the
    table, or nobody there holding a counted tag."""

    invariant(reader in table, "a grid for a reader who is not at the table")
    pct = social_vibe_of(table, tags)
    if pct is None:
        return None
    seated = (reader, *(player for player in table if player != reader))
    return TableVibe(
        pct=pct,
        rows=tuple(
            VibeRow(
                tag=tag,
                carried_by=tuple(
                    player for player in seated if tag in tags.get(player, ())
                ),
            )
            for tag in in_vocabulary_order(tags.get(reader, ()))
        ),
    )
