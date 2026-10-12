"""The catch-up — **the only thing on this platform that tests a rating.**

**It exists because nothing announces a confirmation.** ADR-0137 refused a
``ResultConfirmed`` event on the grounds that a derived standing has exactly one
place to be true, and recorded the cost in its own Consequences: *the rating
context has nothing to subscribe to, so #304 must read games forward*. This is
that read, and ``docs/adr/0139`` is where its shape is argued.

**One transaction per game, and that is the interesting decision.** Everything a
result touches is the two or four rating streams of one game, so nothing spans two
games and a boundary drawn around a whole run would buy no consistency anybody
wanted. What it would cost is progress: ADR-0092 puts a copy of every job in every
API process with no lock between them, and this run is derived from the clock, so
N processes walk the *same* games in the *same* order. One version conflict on one
rating would roll back the whole run, and every process would keep colliding at the
same place. So a conflict is **counted and stepped over**.

**Idempotent, and the ratings are the cursor.** Every move records the game that
caused it, so a game already folded into a stream is skipped by the aggregate
itself; a run that dies half way costs a repeat of the read and never a repeat of
a move. Nothing here holds a cursor, so there is no second record of progress to
go stale, and re-deriving the whole walk from the clock is the recovery path
rather than an incident.

**And one game, from the outbox** (#654; ``docs/adr/0195`` §5). *That's right*
settles a result at once, so the delivery of that agreement settles its game for
rating — that game alone, as it stood at the tap, in the delivery's own
transaction — and Levels move within a minute rather than at the next run. The
catch-up still walks every result a window closing settled, now every minute; a
game the delivery already moved is one its walk steps over. The cost is the
order: an agreement settled from the outbox may be applied before a result whose
window closed a moment earlier and that the next run picks up — at most a
minute's disorder, accepted for a Level that moves when the result does.

**A four moves four ratings against one snapshot.** Every player's move is priced
against the Levels as they stood *before* the game, not against a partner who has
already been updated inside the same loop — otherwise whoever the iteration reached
first would get a different number for the same evening, and the order of a
``for`` would be a rule nobody wrote down.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import (
    information_share,
    one_side,
    rating_after,
)
from app.kernel import Clock, Instant, Sport, invariant
from app.modules.games.domain.ports import ConfirmedGame, ConfirmedResultLedger
from app.modules.rating.domain.ports import SkillRatingRepository
from app.modules.rating.domain.skill_rating import SkillRating


@final
@dataclass(frozen=True, slots=True)
class Settled:
    """What one run of the catch-up moved.

    ``games`` is results newly folded into at least one rating — the figure that
    should be zero on a quiet platform and non-zero the day after somebody plays.

    ``ratings`` is how many Levels moved, and the two together are the shape of
    the run: four ratings over one game is a padel evening, and four over four is
    a week of singles. It is the second figure and not a third, because *what the
    Levels became* is a question about ratings and belongs to whoever reads one.

    ``unrated`` is seats whose player has no rating in that sport. Reported rather
    than swallowed, because *nobody played* and *everybody who played was unrated*
    have one symptom — nothing moves — and only one of them is a defect.

    ``conflicts`` is ratings another process reached first. Here rather than
    swallowed because *the loop is doing nothing* and *the loop is losing every
    race* look identical from outside.
    """

    games: int
    ratings: int
    unrated: int
    conflicts: int

    def __post_init__(self) -> None:
        invariant(
            min(self.games, self.ratings, self.unrated, self.conflicts) >= 0,
            f"a run that moved a negative number of things: {self!r}",
        )


@final
class SettleRatingsOnResults:
    """Fold every confirmed counted result nobody has folded yet."""

    def __init__(
        self,
        *,
        results: ConfirmedResultLedger,
        ratings: SkillRatingRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._results = results
        self._ratings = ratings
        self._uow = uow
        self._clock = clock

    async def execute(self) -> Settled:
        now = self._clock.now()
        games = 0
        moved = 0
        unrated = 0
        conflicts = 0

        for game in await self._results.confirmed_counted_results(now=now):
            try:
                outcome = await self._move_levels(game)
                if outcome.ratings:
                    await self._uow.commit()
            except EventStreamVersionConflict:
                # Somebody else got there first. Their append is this game
                # applied, so stepping over it loses nothing — and ending the run
                # here would stall every process at the same game for ever.
                await self._uow.rollback()
                conflicts += 1
                continue
            unrated += outcome.unrated
            if outcome.ratings:
                games += 1
                moved += outcome.ratings

        return Settled(
            games=games, ratings=moved, unrated=unrated, conflicts=conflicts
        )

    async def settle(self, game_id: UUID, *, at: Instant) -> Settled:
        """One game, **as it stood at ``at``** — the moment an agreement settled
        it (#654). **No commit**: the outbox delivery that asks is the
        transaction, and a conflict is its to retry, the rating streams being
        the cursor either way.

        Folded at the agreement's own moment rather than at the delivering
        process's clock, so a delivery that runs late — or on a clock a test
        moved — settles the game exactly as the tap left it.
        """

        game = await self._results.confirmed_counted_result(game_id, now=at)
        if game is None:
            return Settled(games=0, ratings=0, unrated=0, conflicts=0)
        outcome = await self._move_levels(game)
        return Settled(
            games=1 if outcome.ratings else 0,
            ratings=outcome.ratings,
            unrated=outcome.unrated,
            conflicts=0,
        )

    async def _move_levels(self, game: ConfirmedGame) -> "_Outcome":
        """One game. **The snapshot is read before anything moves**, and the
        caller decides where the transaction ends."""

        winners = await self._ratings_of(game.winners, game.sport)
        losers = await self._ratings_of(game.losers, game.sport)
        unrated = (len(game.winners) - len(winners)) + (
            len(game.losers) - len(losers)
        )
        if not winners or not losers:
            # A side nobody on it is rated in this sport. There is nothing to
            # price the other side against, so the game moves nobody and is not
            # recorded as applied — a rating that arrives later will still find
            # it, which is the whole benefit of the streams being the cursor.
            return _Outcome(ratings=0, unrated=unrated)

        share = information_share(game.sport)
        # Both sides as they stood **before** this game, so nobody's move depends
        # on where they came in the loop.
        winning_side = one_side([rating.estimate for rating in winners])
        losing_side = one_side([rating.estimate for rating in losers])

        moved = 0
        moved += await self._move(
            winners, own_side=winning_side, opposition=losing_side,
            won=True, share=share, game=game,
        )
        moved += await self._move(
            losers, own_side=losing_side, opposition=winning_side,
            won=False, share=share, game=game,
        )
        return _Outcome(ratings=moved, unrated=unrated)

    async def _move(
        self,
        ratings: list[SkillRating],
        *,
        own_side: SkillEstimate,
        opposition: SkillEstimate,
        won: bool,
        share: float,
        game: ConfirmedGame,
    ) -> int:
        """Everybody on one side, moved by **the side's** delta.

        ``own_side`` is what the Level move is priced from and is the same for
        both partners; each player's certainty still folds into the uncertainty
        they actually had. In a singles game it is that one player, so nothing
        about a two is special-cased.
        """

        moved = 0
        for rating in ratings:
            if rating.has_applied(game.game_id):
                continue
            rating.move_on_result(
                game_id=game.game_id,
                moved=rating_after(
                    player=rating.estimate,
                    own_side=own_side,
                    opposition=opposition,
                    won=won,
                    results_so_far=rating.counted_results,
                    share=share,
                ),
                won=won,
                opposition=opposition,
                information_share=share,
                occurred_at=game.confirmed_at,
            )
            await self._ratings.save(rating)
            moved += 1
        return moved

    async def _ratings_of(
        self, player_ids: tuple[UUID, ...], sport: Sport
    ) -> list[SkillRating]:
        """The rated players on one side, in the line-up's own order.

        Unrated seats are simply missing, which is the ordinary state of somebody
        who was invited to a padel evening and has only ever answered the tennis
        questionnaire.
        """

        found = []
        for player_id in player_ids:
            rating = await self._ratings.find_for(player_id=player_id, sport=sport)
            if rating is not None:
                found.append(rating)
        return found


@final
@dataclass(frozen=True, slots=True)
class _Outcome:
    ratings: int
    unrated: int
