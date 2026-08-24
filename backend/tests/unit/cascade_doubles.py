"""Hand-written stubs over the cascade's eight ports, per the testing rule.

They record what they were **asked** as well as what they answered, because half
of what a dispatch promises is about the asking: a dark rung is a rung that read
no store at all, and a candidate excluded on a fact the record already holds is
one that never cost a rating replay. Neither is visible from the offers written.

Every scoring context is built through `shelf_doubles.a_context`, so a cascade
case and a shelf case describe a match the same way.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID, uuid4

from app.engines.forecast import PairingAnalysis
from app.engines.matchmaking import Occupant
from app.kernel import Instant, Ok, Sport

from app.modules.now.application.scoring import Unscorable
from app.modules.now.domain.cascade import Band, Offer, PendingWave, Wave
from app.modules.now.domain.funnel import MatchScoringContext


class FakeCascadeWaves:
    """The dispatch queue, with every write visible.

    `due_at` is only ever read back through `brought_forward`, because what the
    cases are about is *which* dispatch moved and never the storage.
    """

    def __init__(self, *pending: PendingWave) -> None:
        self.pending = list(pending)
        self.opened: list[PendingWave] = []
        self.done: list[tuple[UUID, Wave, Instant]] = []
        self.brought_forward: list[tuple[UUID, Wave, Instant]] = []

    async def open(self, waves: Sequence[PendingWave]) -> None:
        self.opened.extend(waves)

    async def due(self, *, now: Instant, limit: int) -> tuple[PendingWave, ...]:
        return tuple(
            wave for wave in self.pending if wave.due_at <= now
        )[:limit]

    async def dispatched(self, *, vacancy_id: UUID, wave: Wave, at: Instant) -> None:
        self.done.append((vacancy_id, wave, at))

    async def bring_forward(
        self, *, vacancy_id: UUID, wave: Wave, to: Instant
    ) -> None:
        self.brought_forward.append((vacancy_id, wave, to))


class FakeOffers:
    """What has been told, and what a dispatch tried to tell.

    `written` is every offer handed to `record`, flattened, so a case asserting
    the **order** of a dispatch reads the list rather than a set.
    """

    def __init__(
        self,
        *,
        for_vacancy: frozenset[UUID] = frozenset(),
        on_match: frozenset[UUID] = frozenset(),
    ) -> None:
        self._for_vacancy = for_vacancy
        self._on_match = on_match
        self.written: list[Offer] = []
        self.asked_for_vacancy: list[UUID] = []
        self.asked_on_match: list[UUID] = []

    async def record(self, offers: Sequence[Offer]) -> None:
        self.written.extend(offers)

    async def offered_for(self, *, vacancy_id: UUID) -> frozenset[UUID]:
        self.asked_for_vacancy.append(vacancy_id)
        return self._for_vacancy

    async def reached_on(self, *, match_id: UUID) -> frozenset[UUID]:
        self.asked_on_match.append(match_id)
        return self._on_match


class FakeContexts:
    """`CityMatches` narrowed to the one method a dispatch uses."""

    def __init__(self, *contexts: MatchScoringContext) -> None:
        self._by_id = {one.match_id: one for one in contexts}
        self.asked: list[UUID] = []

    async def contexts(
        self, *, sports: frozenset[Sport], window_from: Instant, window_to: Instant
    ) -> tuple[MatchScoringContext, ...]:  # pragma: no cover - never a dispatch's
        raise AssertionError("a dispatch reads one match, never a window")

    async def one(self, match_id: UUID) -> MatchScoringContext | None:
        self.asked.append(match_id)
        return self._by_id.get(match_id)


class FakeRatedPlayers:
    """Everybody the platform can place at a sport — rung 6's whole population."""

    def __init__(self, *player_ids: UUID) -> None:
        self._ids = tuple(player_ids)
        self.asked: list[Sport] = []

    async def at(self, sport: Sport) -> tuple[UUID, ...]:
        self.asked.append(sport)
        return self._ids


class FakeClubRegulars:
    """Rung 5. Empty unless a case says otherwise."""

    def __init__(self, *player_ids: UUID) -> None:
        self._ids = frozenset(player_ids)
        self.asked: list[tuple[UUID, Instant]] = []

    async def at(self, *, club_id: UUID, before: Instant) -> frozenset[UUID]:
        self.asked.append((club_id, before))
        return self._ids


class FakeStandbyQueue:
    """Rung 1. Empty unless a case says otherwise."""

    def __init__(self, *player_ids: UUID) -> None:
        self._ids = frozenset(player_ids)
        self.asked: list[UUID] = []

    async def queued_for(self, match_id: UUID) -> frozenset[UUID]:
        self.asked.append(match_id)
        return self._ids


class FakeDiaries:
    """`Commitments`, answering **per player** rather than once for everybody.

    The viewer's version in `shelf_doubles` answers one screen's one asker; a
    dispatch asks forty different people, and a double that answered them all
    alike would make *she is busy* and *he is busy* the same fact.
    """

    def __init__(self) -> None:
        self._held: dict[UUID, tuple[tuple[UUID, Instant, Instant], ...]] = {}
        self.asked: list[UUID] = []

    def give(
        self, player_id: UUID, *rows: tuple[UUID, Instant, Instant]
    ) -> "FakeDiaries":
        self._held[player_id] = rows
        return self

    async def held_by(
        self, player_id: UUID
    ) -> tuple[tuple[UUID, Instant, Instant], ...]:
        self.asked.append(player_id)
        return self._held.get(player_id, ())


class FakeRatings:
    """One `Occupant` per **player**, which is the cascade's direction.

    `shelf_doubles.FakeRatings` keys on the sport because a screen has one
    viewer; this keys on the person because a dispatch has forty.
    """

    def __init__(self) -> None:
        self._at: dict[UUID, Occupant | None] = {}
        self.asked: list[tuple[UUID, Sport]] = []

    def give(self, player_id: UUID, occupant: Occupant | None) -> "FakeRatings":
        self._at[player_id] = occupant
        return self

    async def occupant(self, *, player_id: UUID, sport: Sport) -> Occupant | None:
        self.asked.append((player_id, sport))
        return self._at.get(player_id)


class FakeScorer:
    """The two engines, replaced by numbers a case chooses.

    A double rather than the real pair for every case but the band's own: the
    floor, the order and the wall are all *about* a fit, and a fixture that had
    to produce a 71 through ten weighted terms would be a fixture nobody could
    read. The real engines are exercised where the claim is about **them** —
    that the band is the seated mean and that no observer moves it.
    """

    def __init__(
        self,
        *,
        fits: dict[UUID, int] | None = None,
        default: int = 90,
        band: Band | None = None,
        unscorable: frozenset[UUID] = frozenset(),
        band_raises: bool = False,
    ) -> None:
        self._fits = fits or {}
        self._default = default
        self._band = band
        self._unscorable = unscorable
        self._band_raises = band_raises
        self.scored: list[UUID] = []
        self.analysed: list[UUID] = []

    def analyse(
        self, context: MatchScoringContext, *, now: Instant
    ) -> PairingAnalysis:
        self.analysed.append(context.match_id)
        if self._band_raises:
            raise Unscorable("no analysis")
        return _AnalysisWithBand(self._band)

    def score(self, context, *, viewer, now):  # type: ignore[no-untyped-def]
        who = UUID(str(viewer.player))
        self.scored.append(who)
        if who in self._unscorable:
            raise Unscorable("no score")
        return _Fit(self._fits.get(who, self._default)), _AnalysisWithBand(self._band)


class _Fit:
    def __init__(self, fit: int) -> None:
        self.fit = fit


class _AnalysisWithBand:
    """Only the one field `_band_from` reads, so a case cannot lean on another."""

    def __init__(self, band: Band | None) -> None:
        self.target_band = (
            Ok(_TargetBand(band)) if band is not None else _NoBand()
        )


class _TargetBand:
    def __init__(self, band: Band) -> None:
        self.low = band.low
        self.high = band.high


class _NoBand:
    """Anything that is not an `Ok`, which is what `_band_from` narrows on."""


class SpyUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def flush(self) -> None:  # pragma: no cover - never a dispatch's
        raise AssertionError("a dispatch flushes nothing")

    async def rollback(self) -> None:
        self.rollbacks += 1


class FixedClock:
    def __init__(self, now: Instant) -> None:
        self._now = now

    def now(self):  # type: ignore[no-untyped-def]
        return self._now


def an_id() -> UUID:
    return uuid4()
