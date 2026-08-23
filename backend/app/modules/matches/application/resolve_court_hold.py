"""The hold ladder, acting: grant a court, extend one, or take one back.

ADR-0031, and the ticket is ``Raketa02/Raketa#71``. Everything about *what* the
ladder says lives in ``app/kernel/holds.py`` — Rule 11 governing, Rule 12
restated as *never shorter at the same level of certainty*, the ``filled < n-1``
guard that keeps staleness off a near-tier hold, the club's cap measured from
``held_since`` and the age a card prints being the hold's own. This module is the
*act*: it asks ``kernel.hold_move`` what to do and does exactly that, and it
holds no threshold of its own.

**Two facts have to stay in step, and this is the only thing allowed to move
them.** Whether a court *should* be kept aside is composed from the seats and the
clock on every read; *since when* one has been is ``held_since``, which is stored
because it cannot be derived (ADR-0031). Let the two drift apart and the record
is internally invalid — a soft tier under a club's cap with no ``held_since`` to
age from is the one combination the kernel refuses outright, and it would arrive
as a five-hundred on somebody's home screen rather than as a red test. So this
runs **inside the transaction that moved the match**, not after it: there is no
instant at which a stored record is in a state the kernel will not read.

**A grant that finds no court is an inventory loss, not a hold with nothing
behind it.** ``keep_aside`` answers *nothing was free* — never *somebody was
faster*, which ADR-0035 makes structurally impossible — so the club has no court
of that category for that hour and the match cannot be played. Recording that is
``Match.lose_inventory``, whose own story is ADR-0035's single promise to the
player. The alternative is a card promising a court until twelve hours before
play with no reservation behind it, which is the reassuring-direction failure the
five kinds of stored fact exist to remove.

**Nothing here commits.** ``ClaimCourt.claim`` does not, ``MatchRepository.save``
does not, and this composes over both — so the seat payment, the court it earns
and both outbox rows are one write, closed by ``money.PayForASeat``
(``Raketa02/Raketa#70``).
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, HoldMove, Instant, exhaustive, hold_move, instant

from app.modules.matches.application.commands import ResolveCourtHoldCommand
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import CourtHolds, MatchRepository


class ResolveCourtHold:
    """Bring a match's court into line with what the ladder says about it."""

    def __init__(
        self,
        matches: MatchRepository,
        courts: CourtHolds,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._matches = matches
        self._courts = courts
        self._uow = uow
        self._clock = clock

    async def apply(self, match: Match, *, at: Instant) -> HoldMove:
        """The ladder over a match already in hand, without committing.

        The shape every other Matches write ends in: mutate, resolve, save. It
        takes the match rather than an id because the caller is already holding
        the one it changed, and re-reading it would be a second row-set and a
        second answer.
        """

        move = hold_move(match.as_record(), at)
        match move:
            case HoldMove.GRANT:
                won = await self._courts.keep_aside(
                    match_id=match.id,
                    club_id=match.club_id,
                    category_id=match.category_id,
                    start=match.start,
                    duration=match.duration,
                )
                if not won:
                    match.lose_inventory(at=at)
                else:
                    match.hold_court(at=at)
            case HoldMove.WITHDRAW:
                # Courts first: a released row costs the next claimant nothing,
                # while a match that has forgotten its court and failed to give
                # it back has taken a court out of the club's inventory for ever.
                await self._courts.give_back(match_id=match.id, at=at)
                match.release_court(at=at)
            case HoldMove.STAND:
                pass
            case _:  # pragma: no cover - `exhaustive` never returns
                exhaustive(move)
        return move

    async def execute(self, command: ResolveCourtHoldCommand) -> Match:
        """Look at one match and act on what is found, committing.

        The command form, for a caller holding an id and nothing else. **The
        timekeeper does not take this door** — ``TakeMatchWake`` composes
        ``apply`` instead, because a look that finds nothing still has to move
        the schedule forward and this one, correctly, writes nothing at all.
        """

        match = await self._matches.get(command.match_id)
        if match is None:
            raise MatchNotFound()

        move = await self.apply(match, at=instant(self._clock.now()))
        if move is HoldMove.STAND:
            # A look that finds nothing writes nothing. Saving anyway would bump
            # the version on every wake, so a player's own tap could lose a race
            # against a scheduled look that had changed nothing at all.
            return match
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored
