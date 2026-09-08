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

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.skill_rating import SkillRating


@final
@dataclass(frozen=True, slots=True)
class RatedSport:
    """One player's published rating in one sport. **What a screen may print.**

    The second thing this context publishes that is not an aggregate, and the
    wider of the two: ``SkillEstimate`` is the engine's currency and this is the
    **published** form — the figures a rating already committed to its own stream
    and a rating route already prints, carried outward without anybody deriving
    one of them a second time.

    **Nothing here is computed on the way out.** ``confidence`` is the rating's
    own whole percentage, the range is the one the engine rounded, and the band
    travels with its name because a screen printing a band it derived from a
    Level would be a second set of drawing constants (``CONTEXT.md``).

    ``counted_results`` is **how many confirmed counted results have moved this
    Level** and is deliberately not *how many counted games they have played*.
    The second is ``games``' number, is over every sport, and counts an evening
    two people never agreed a score for; this one is what a certainty rests on,
    and it moves in step with the ``mu`` beside it because they come off the same
    stream (``docs/adr/0139``).
    """

    sport: Sport
    mu: float
    confidence: int
    range_low: float
    range_high: float
    band_name: str
    counted_results: int


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

    **There is still no ``load`` by id, and ``find_for`` is not one.** Nothing
    reads a rating by an identifier it was handed; a stream id is *derived* from
    the player and the sport, so the pair is the address and a by-id member would
    be one no caller could want. ``find_for`` takes the pair, which is the
    ownership argument ``AssessmentRepository.load`` makes, satisfied by the
    signature rather than by an extra argument nobody can forget.
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
        one* has no business with an aggregate it might then mutate — which is
        why the result-update rule reaches for ``find_for`` below and not for
        this, even though the two address the same stream.
        """
        ...

    async def find_for(
        self, *, player_id: UUID, sport: Sport
    ) -> SkillRating | None:
        """This player's rating for one sport, replayed, or nothing.

        **The read the result-update rule needed and the reason ``exists_for``
        could not be it.** Moving a Level on a result is a transition, so the
        caller needs the aggregate rather than an answer about it — and it needs
        exactly one, because a game is one sport and replaying every rating a
        player holds to move one of them is a read four times too wide in a
        four.

        ``None`` for an unrated player, which is ordinary rather than an error:
        somebody can be on a court in a sport they never answered a questionnaire
        for, and a result that finds no rating moves nothing.
        """
        ...

    async def find_all_for(self, *, player_id: UUID) -> list[SkillRating]:
        """Every Skill rating this player holds, one per sport they are rated at.

        Empty for an unrated player — the ordinary state of a new account, never
        an error. Ordered as the ratings were earned, which is what the store's
        oldest-first ids already give.
        """
        ...


@runtime_checkable
class RatedPlayerQuery(Protocol):
    """Levels and uncertainties, **read and never held.**

    The one thing this context publishes outward that is not an aggregate, and it
    exists so that a consumer wanting to *know* a Level cannot accidentally hold
    something it could move. ``SkillRatingRepository`` remembers stream versions
    precisely so that a rating it found can be saved; handing that to a reader
    would put a mutation path in the matcher's hands for the sake of two floats.

    **It answers about a pair of ratings and computes nothing.** *At stake* is
    this context's own number and the rule that produces it is
    ``engines/racketskill/results.py``; what crosses this port is the input to
    that rule, so nobody outside acquires an opinion about a K-factor by having
    read a μ.

    **Two methods, and the shapes are opposite because the callers are.** The
    matcher holds twenty rows in one sport and asks once; a record is one person
    opened by a tap and wants every sport they hold. Neither is the other with an
    argument moved, and a single method covering both would be a set read
    answering about four streams per id.
    """

    async def estimates_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, SkillEstimate]:
        """Each of these players' Level and uncertainty for one sport.

        A player with no rating in this sport is **absent from the answer** —
        never a population mean and never a zero, on the rule the whole platform
        applies to a fact nobody has measured. Asked about ids the caller already
        holds, and answers only about those.
        """
        ...

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, RatedSport]:
        """Every sport this one player is rated in, keyed by sport.

        **One player and every sport**, which is the mirror of the read above and
        exists because a record is opened by a tap on one face. A sport they hold
        no rating in is **absent**, on the same rule, and an empty mapping is the
        ordinary answer for somebody part way through onboarding.

        **A read, and there is deliberately no way to save what comes back.** The
        repository beside this port remembers stream versions so that a rating it
        found can be moved; a sheet that draws a number has no business holding
        that, and the narrowness is the whole reason this port exists.
        """
        ...


__all__ = [
    "AssessmentRepository",
    "RatedPlayerQuery",
    "RatedSport",
    "SkillRatingRepository",
]
