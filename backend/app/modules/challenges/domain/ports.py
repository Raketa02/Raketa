"""The two seams this context is built on: one to write a challenge, one to ask
whether a game is already being arranged between two people.

``ChallengeRepository`` is the **aggregate repository** kind — how a use case
reaches an event-sourced ``Challenge`` without knowing that it is event-sourced,
owning the aggregate-type name, the replay and the optimistic-concurrency
bookkeeping.

``OpenChallengeQuery`` is the read kind, and it exists because **one open
challenge per pair, across every sport** is a rule no aggregate can enforce on
its own: it is a statement about every *other* challenge, and a challenge that
could see them would not be an aggregate.

**Across every sport, and not by oversight.** Two people are either arranging a
game or they are not; asking for padel while your tennis challenge sits
unanswered is pestering with a sport chip on it. The matcher's own
``OpenChallenge`` carries no sport field at all, so this is the rule its shipped
contract already assumed rather than a new restriction — which is why nothing on
this port takes a ``Sport``.
"""

from __future__ import annotations

from typing import Collection, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.challenges.domain.challenge import Challenge


@runtime_checkable
class ChallengeRepository(Protocol):
    """Loads and saves ``Challenge`` aggregates, keyed by the challenge's own id.

    Keyed by the id and not by the people, because the id is the identity: the
    same four may be challenged again tomorrow and that is a second challenge,
    not a second version of the first.
    """

    async def load(self, challenge_id: UUID) -> Challenge | None:
        """That challenge, replayed, or nothing.

        ``None`` rather than a raise: *no such challenge* is an ordinary answer
        for an id a client sent, and a caller that wants a 404 is better placed
        to say so than this port is.
        """
        ...

    async def save(self, challenge: Challenge) -> None:
        """Append the aggregate's pending events and publish them.

        Appends and publishes; it does **not** commit, for the reason no
        repository in this codebase does — the transaction boundary is a decision
        about the *command*. A no-op when nothing is pending, which is what lets
        a sweep that found nothing to lapse be saved without growing a stream.
        """
        ...


@runtime_checkable
class OpenChallengeQuery(Protocol):
    """*Are any two of these people already arranging a game?*

    **Read at the moment it is asked, against the clock.** There is no projection
    and no cached *open* flag behind this by decision: the standing is derived
    from the seats and the clock (``standing.py``), so a copy would be wrong for
    the whole gap between a deadline passing and a sweep noticing — and it would
    be the copy that got believed.

    **It does not fail closed, and the difference from ``BlockQuery`` is the
    point.** A block is safety and a gate that cannot be evaluated excludes; this
    rule is *embarrassment* — one person asked one thing at a time — and a
    context that refused every send whenever a read hiccuped would be paying a
    safety price for a courtesy. So there is no translation to a
    ``…Unavailable`` here: a read that cannot complete raises what it raised, and
    the send it was part of fails with it inside its own transaction, writing
    nothing. What must never appear is the other answer — an implementation that
    returned *no pairs* when it could not tell, which reads as *nobody has an
    open challenge* and is the one way this rule stops holding in silence.
    """

    async def open_pairs_among(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> frozenset[frozenset[UUID]]:
        """Every pair of these people who already have an open game between them.

        **One bulk read over the whole court, never one read per pair.** A four
        contains six pairs and the organiser is in only three of them, so a send
        has to know whether two *invitees* are already arranging something —
        which is the same shape ``BlockQuery.blocked_pairs_among`` takes, and for
        the same reason: asking pairwise would be six round trips for a mask that
        is one query.

        It answers in **unordered pairs**, because there is nothing for a caller
        to learn from the direction. Sharing a line-up makes a pair regardless of
        who organised it.
        """
        ...
