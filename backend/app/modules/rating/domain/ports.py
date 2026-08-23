"""The rating context's ports.

An **aggregate repository** is how a use case reaches an event-sourced aggregate
without knowing that it is event-sourced. It owns the aggregate-type name, the
replay, the ownership scoping and the optimistic-concurrency bookkeeping, so a
use case reads as domain steps — load, decide, save — and can be unit-tested
against a fake event store rather than a running database.

This is not the *read-model* kind of repository. See ``backend/CONTEXT.md`` for
the distinction, and ADR-0017 for why this context is event-sourced.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Sport
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.skill_rating import SkillRating


@runtime_checkable
class AssessmentRepository(Protocol):
    """Loads and saves Assessment aggregates.

    ``save`` appends and publishes; it does **not** commit. The transaction stays
    a use-case dependency because completing an assessment writes two streams in
    one transaction, and ADR-0017 states that as a domain rule rather than a
    persistence detail.
    """

    async def load(self, assessment_id: UUID, *, for_player: UUID) -> Assessment:
        """The player's assessment, replayed from its stream.

        ``for_player`` is required so that forgetting the ownership check is a
        type error rather than one player reading another's transcript. An
        assessment that does not exist and one belonging to another player raise
        the same error, so the API cannot be used to discover which ids exist.
        """
        ...

    async def save(self, assessment: Assessment) -> None:
        """Append the aggregate's pending events and publish them.

        A no-op when nothing is pending, which is what keeps abandoning an
        already-abandoned run idempotent without the caller checking first.
        """
        ...

    async def next_identity(self, *, player_id: UUID, sport: Sport) -> UUID:
        """The id the next run for this pair will be filed under.

        Derived from ``(player, sport, attempt)`` rather than minted at random,
        which is what makes *at most one open run per sport* something the store
        enforces instead of something a read-before-write hopes for. Two starts
        that both read before either appends compute the **same** id and collide
        on one stream's version 1; one wins and the other is told (#35).

        Asked of the repository because the attempt number is a fact about what
        the store already holds. The read is not load-bearing for correctness —
        a stale count yields a candidate id that the unique constraint rejects,
        which is exactly the outcome it should.
        """
        ...

    async def find_open(self, *, player_id: UUID, sport: Sport) -> Assessment | None:
        """This player's unfinished run for a sport, or nothing.

        At most one, and the newest of them if the store somehow holds two — the
        same rules ``find_all_open`` reports, because the two answer the same
        question about the same player. A gate routing to one run while the
        resume read offered another would be a bug no client could see.
        """
        ...

    async def find_all_open(self, *, player_id: UUID) -> list[Assessment]:
        """Every sport's unfinished run, at most one per sport, in registry order.

        Registry order (``Sport``'s own) so a caller that wants exactly one — the
        entry gate does — can take the first entry and get a stable answer rather
        than one that depends on which sport was started first.
        """
        ...


@runtime_checkable
class SkillRatingRepository(Protocol):
    """Saves and reads back SkillRating aggregates.

    ``save`` appends and publishes without committing, exactly as
    ``AssessmentRepository.save`` does and for the same reason: completing an
    assessment writes this stream and the assessment's inside one transaction,
    so the boundary belongs to the use case.

    **There is still no by-id ``load``.** A rating's stream id is derived from
    the player and the sport rather than looked up, so a by-id port would be a
    member no caller could want. What did arrive, on that paragraph's own
    invitation, is ``find_for`` — the by-**pair** read, which names whose rating
    it is in its signature and therefore carries the ownership argument
    ``AssessmentRepository.load`` makes rather than sidestepping it.
    """

    async def save(self, rating: SkillRating) -> None:
        """Append the rating's pending events and publish them.

        A no-op when nothing is pending, on the same rule as the assessment's.
        """
        ...

    async def exists_for(self, *, player_id: UUID, sport: Sport) -> bool:
        """Whether this player already holds a rating for this sport.

        Asked before an assessment is started, so a sport that cannot produce a
        second rating is refused before the player answers anything.

        A question rather than the aggregate, deliberately. The stream is keyed
        by ``(player, sport)`` so this is one lookup, where ``find_all_for``
        replays every rating the player holds; and a caller asking *is there
        one* has no business with an aggregate it might then mutate. The
        by-id ``load`` this port still lacks stays unwritten until something
        wants to transition a rating — which is the match-update engine's
        problem, not this one's.
        """
        ...

    async def find_for(self, *, player_id: UUID, sport: Sport) -> SkillRating | None:
        """This player's rating at one sport, or nothing.

        The by-pair read the module docstring above kept unwritten until
        something wanted it, and what wants it is Now's *New on Raketa* shelf:
        its whole order is one subtraction between two Levels at one sport, and
        ``find_all_for`` replays every rating a player holds to answer it.

        Ownership is in the signature for the reason ``AssessmentRepository.load``
        gives, and here it is not even a check — the stream id **is** the pair, so
        a rating cannot be reached without saying whose it is.
        """
        ...

    async def find_all_for(self, *, player_id: UUID) -> list[SkillRating]:
        """Every Skill rating this player holds, one per sport they are rated at.

        Empty for an unrated player — the ordinary state of a new account, never
        an error. Ordered as the ratings were earned, which is what the store's
        oldest-first ids already give.
        """
        ...
