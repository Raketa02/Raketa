"""``SportsmanshipLedger`` over SQLAlchemy. **It writes rows and it never commits.**

The transaction boundary is the use case's decision, the way it is for every
durable ledger in this codebase: the card and the answers on it are one act, and
a store that committed for itself would take that decision away from the one
place that has to make it.

**The replace is two statements and not an upsert.** ``INSERT … ON CONFLICT DO
UPDATE`` is PostgreSQL's spelling and ``INSERT OR REPLACE`` is SQLite's, and this
suite runs on the second while production runs on the first — a dialect-specific
write here would be a write no test in this repository executes. A delete of the
pairs about to be written, then the insert, is one statement more and the same
answer on both, and it is the shape the interest ledger already takes.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sportsmanship.domain.card import SportsmanshipCard
from app.modules.sportsmanship.domain.errors import YouHaveAlreadyRatedThisGame
from app.modules.sportsmanship.infrastructure.card_model import (
    SportsmanshipCardORM,
    SportsmanshipRatingORM,
)


@final
class SqlAlchemySportsmanshipLedger:
    """Every answered card, and one standing answer per pair of people."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def answered_among(
        self, *, rater_id: UUID, game_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these cards are closed. **The all-blank card is one of them.**

        It asks the card table and never the ratings, which is the difference the
        two tables exist for: a card answered with everybody left blank has no
        ratings at all, and a read that looked for them would offer that player
        the card again for ever.

        **An empty ask is answered without a query.** A player with no open card
        is the common case on this route, and ``IN ()`` is a statement two
        dialects disagree about for an answer that is known before either of them
        sees it.
        """

        wanted = list(game_ids)
        if not wanted:
            return frozenset()
        found = await self._session.scalars(
            select(SportsmanshipCardORM.game_id).where(
                SportsmanshipCardORM.rater_id == rater_id,
                SportsmanshipCardORM.game_id.in_(wanted),
            )
        )
        return frozenset(found)

    async def record(self, card: SportsmanshipCard) -> None:
        """Close the card and stand its answers up. **The caller commits.**

        The delete is what makes *the most recent counts* true, and it is scoped
        to the pairs this card actually answers: a person left blank here keeps
        whatever this rater last said about them from another evening, because a
        blank is the absence of an opinion and not the withdrawal of one.

        **The primary key is the second answer to a double tap**, and it is the
        one that holds under a race. The use case asks whether the card is closed
        and refuses if it is, which serves everybody who taps twice slowly; two
        requests in flight together both find it open and both insert, and the
        loser meets the key. It is translated back into the refusal it *is*
        rather than escaping as an integrity error, because the alternative
        answers one of two identical taps with a 500 — and the card is closed
        either way, so there is nothing here a caller could usefully do
        differently.

        **The translation is narrowed to the one row that can raise it**, and
        that narrowing is what makes it honest. The card table has a single
        constraint — no foreign key, no check, no unique index beside the primary
        key — so a breach *of that row* has exactly one cause. A bare ``flush()``
        would not say that, because it flushes everything the session happens to
        be holding, and this refusal would then be free to land on somebody
        else's failure. Flushing the card alone keeps the claim true whatever a
        caller has pending.
        """

        answered = SportsmanshipCardORM(
            game_id=card.game_id,
            rater_id=card.rater_id,
            answered_at=card.answered_at,
        )
        self._session.add(answered)
        try:
            # Flushed before the ratings so the composite foreign key back to
            # the card resolves within this transaction rather than at its end —
            # and so the key's refusal arrives here, where it can be named.
            await self._session.flush([answered])
        except IntegrityError as clash:
            raise YouHaveAlreadyRatedThisGame() from clash

        if not card.given:
            return

        await self._session.execute(
            delete(SportsmanshipRatingORM).where(
                SportsmanshipRatingORM.rater_id == card.rater_id,
                SportsmanshipRatingORM.subject_id.in_(
                    [given.subject_id for given in card.given]
                ),
            )
        )
        self._session.add_all(
            [
                SportsmanshipRatingORM(
                    rater_id=card.rater_id,
                    subject_id=given.subject_id,
                    game_id=card.game_id,
                    stars=given.stars,
                    rated_at=card.answered_at,
                )
                for given in card.given
            ]
        )
        await self._session.flush()
