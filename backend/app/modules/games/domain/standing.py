"""What a game **is** right now, read off the record and the clock.

**Derived, never stored, and never announced** (``docs/adr/0137``). A status
column would be wrong for the whole gap between a deadline passing and anything
noticing, and it would be the copy that gets believed — which is why there is no
status field on the aggregate, no ``ResultConfirmed`` event, and this function is
the only place a standing exists. It is ``challenges``' own rule, *nothing
announces a conclusion the seats already imply*, applied to a result.

Five values, and they are the five the record and the clock can answer for. Three
of them are ends and two of them are waits.

**The class is ``GameStanding`` and the domain term is *standing*.** ``challenges``
already publishes a ``Standing`` component on ``openapi.player.json``, and a
second class of that name does not shadow it — it renames it, breaking types a
shipped mobile app generated months ago. See ``lineup.py`` for the rule: the
contract is one namespace, and the cost of a shared word is paid by whoever
arrives second.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.results import Score
from app.modules.games.domain.windows import (
    acceptance_settles_at,
    entry_closes_at,
    proposal_closes_at,
)


@final
class GameStanding(str, Enum):
    """The five standings, as codes. A client's words are the client's own."""

    #: Arranged, and nobody has said it happened yet.
    AWAITING_ENTRY = "AWAITING_ENTRY"
    #: The entry window closed and nobody ever said it happened. **A ghost game**
    #: — the pairwise outcome familiarity must be able to tell from a real one.
    NEVER_PLAYED = "NEVER_PLAYED"
    #: They played, a score is on the table, and its window is still open.
    AWAITING_ANSWER = "AWAITING_ANSWER"
    #: They played and a score is agreed — by an acceptance, or by silence.
    CONFIRMED = "CONFIRMED"
    #: They played and no score is agreed. **An evening, not evidence**: it counts
    #: toward how much these people have played and moves nobody's Level.
    UNSCORED = "UNSCORED"


#: The three standings that mean *nothing more will happen to this game*. A
#: settled game refuses every act, which is ADR-0048's *a settled result is
#: final* with no support correction path and no reversal.
SETTLED = frozenset(
    {
        GameStanding.NEVER_PLAYED,
        GameStanding.CONFIRMED,
        GameStanding.UNSCORED,
    }
)

#: The two standings that mean these people were on a court together. Read by the
#: pairwise fold, and by ``counted_games``.
PLAYED = frozenset(
    {
        GameStanding.AWAITING_ANSWER,
        GameStanding.CONFIRMED,
        GameStanding.UNSCORED,
    }
)


@final
@dataclass(frozen=True, slots=True)
class Proposal:
    """One side's score, and the moment its clock started.

    ``at`` is the proposal's own or the correction's that re-dated it — the two
    are one fact here, because what the other side is answering is a score they
    can see.
    """

    side: GameSide
    by: UUID
    score: Score
    at: Instant


@final
@dataclass(frozen=True, slots=True)
class Acceptance:
    """Somebody agreed with the other side's score, and when.

    ``of_side`` is the side whose proposal was accepted — always the accepter's
    opposite, because *a teammate agreeing with a teammate proves nothing*. It is
    recorded rather than re-derived so the grace can be measured from the
    proposal it settles.
    """

    by: UUID
    side: GameSide
    of_side: GameSide
    at: Instant


def live_acceptance(
    *,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
) -> Acceptance | None:
    """The acceptance that still stands, if one does.

    **A counter beats a pending acceptance**, and this is the whole of that rule.
    Inside the grace a disagreement wins, so an acceptance with a score put on
    the table *after* it is void — and there is no other way for a proposal to be
    younger than an acceptance, because a correction is refused once the other
    side has answered and everything is refused once the grace has passed.

    Written here rather than inside the fold because two callers need the same
    answer: the fold, to decide whether anything has settled, and the aggregate,
    to decide whether a second tap from the same side is a repeat or an agreement
    with a score that has since changed.
    """

    if acceptance is None:
        return None
    countered = any(
        proposal.at > acceptance.at for proposal in proposals.values()
    )
    return None if countered else acceptance


def standing_of(
    *,
    planned_at: Instant,
    played_at: Instant | None,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
    now: Instant,
) -> GameStanding:
    """The game's standing, from its record and this instant.

    The order of the questions is the design, and each rung is a decision:

    **Did it happen at all?** Nothing about a score matters until somebody says
    they played, and after the entry window nothing ever will.

    **Did somebody explicitly agree?** An acceptance settles the result once its
    grace has passed, and inside the grace it settles nothing — which is what
    keeps a fast partner from closing the door on an opponent still in the
    shower.

    **Is one score on the table, or two?** A lone proposal is confirmed by
    silence when its window closes; two standing proposals are the disagreement
    this platform has refused to arbitrate, and when both windows have closed
    they leave the game unscored.
    """

    if played_at is None:
        return (
            GameStanding.AWAITING_ENTRY
            if now < entry_closes_at(planned_at)
            else GameStanding.NEVER_PLAYED
        )

    standing = live_acceptance(proposals=proposals, acceptance=acceptance)
    if standing is not None:
        accepted = proposals.get(standing.of_side)
        if accepted is not None and now >= acceptance_settles_at(accepted.at):
            return GameStanding.CONFIRMED

    if not proposals:
        # Unreachable through the aggregate — the entry that records *we played*
        # records a score in the same act, and there is no other way to set a
        # played moment. Stated rather than left to a ``max()`` over an empty
        # sequence, because the failure mode of the alternative is a crash in a
        # read rather than a wrong answer, and a stream that somehow arrived here
        # is still a game nobody has agreed a score for.
        return GameStanding.AWAITING_ANSWER

    if len(proposals) == 1:
        (only,) = proposals.values()
        return (
            GameStanding.CONFIRMED
            if now >= proposal_closes_at(only.at)
            else GameStanding.AWAITING_ANSWER
        )

    if standing is not None:
        # Inside the grace, with both sides' scores on the table. The acceptance
        # is pending and a counter still beats it, so nothing has settled.
        return GameStanding.AWAITING_ANSWER

    latest = max(proposal.at for proposal in proposals.values())
    return (
        GameStanding.UNSCORED
        if now >= proposal_closes_at(latest)
        else GameStanding.AWAITING_ANSWER
    )


def agreed_score(
    *,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
) -> Score | None:
    """**Which** score would settle, if anything has. Never *whether*.

    The two questions are deliberately apart: this one is answerable off the
    proposals alone, and *has it settled* needs the clock. A caller wanting the
    confirmed result asks ``standing_of`` first — ``Game.confirmed_score_at``
    is that pair written once, so nobody publishes a score the standing has not
    reached.

    ``None`` when two scores stand with nothing accepted, which is the
    disagreement this platform refuses to arbitrate.
    """

    standing = live_acceptance(proposals=proposals, acceptance=acceptance)
    if standing is not None:
        accepted = proposals.get(standing.of_side)
        if accepted is not None:
            return accepted.score
    if len(proposals) == 1:
        (only,) = proposals.values()
        return only.score
    return None
