"""Hand-written stubs over the ranked funnel's five ports, per the testing rule.

They record what they were asked as well as what they answered, because half of
what the funnel promises is about the *asking*: a context that was cached is a
context the retrieval was not asked to rebuild, and a rule that was evaluated for
every candidate is invisible from outside unless something counted.

Every context here is built through ``a_context``, which takes offsets against
one fixed start the way ``match_records`` does — a case reads as *three seats
paid, twenty hours out* rather than as two timestamps a reader has to subtract.
"""

from __future__ import annotations

from typing import Mapping, Sequence
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.engines.matchmaking import (
    Occupant,
    PlayerRef,
    PlayerSkill,
    UnratedPlayer,
    level,
    uncertainty,
)
from app.kernel import (
    Cover,
    Grosze,
    Instant,
    MatchRecord,
    Ratio,
    Sport,
    grosze,
    ratio,
)

from app.modules.now.domain.funnel import ClubFacts, MatchScoringContext
from app.modules.now.domain.screen import Money
from tests.unit.match_records import DURATION, at, seats

WARSAW = ZoneInfo("Europe/Warsaw")
STAMP = 1_771_000_000_000
SHARE: Grosze = grosze(3800)
COURT: Grosze = grosze(15200)


def a_match(
    *,
    sport: Sport = Sport.PADEL,
    paid: int = 0,
    held: int = 0,
    starts: int = 0,
    created: int = -4320,
    **facts: object,
) -> MatchRecord:
    """A match ``starts`` minutes from ``START``, with its seats as named.

    ``match_records.a_match`` pins every record to one instant, which is right
    for a ladder suite reading a single match against a moving clock and wrong
    for a funnel suite whose whole subject is the order between several. This is
    the same builder with the start as an offset.
    """

    players = 4 if sport in (Sport.PADEL, Sport.BADMINTON) else 2
    facts.setdefault("held_since", at(created) if paid >= 2 else None)
    return MatchRecord(
        sport=sport,
        start=at(starts),
        duration=DURATION,
        created=at(created),
        seats=seats(players, paid, held),
        **facts,
    )


def a_club(*, which: UUID | None = None, crowding: Ratio | None = None) -> ClubFacts:
    return ClubFacts(
        club_id=which or uuid4(),
        name="Sport Club Kraków",
        zone=WARSAW,
        cover=Cover.INDOOR,
        crowding=crowding if crowding is not None else ratio(1, 4),
    )


def a_context(
    *,
    record: MatchRecord | None = None,
    match_id: UUID | None = None,
    version: int = 1,
    club: ClubFacts | None = None,
    occupants: tuple[Occupant | None, ...] | None = None,
    counted: bool = True,
    share: Grosze = SHARE,
    court_total: Grosze = COURT,
) -> MatchScoringContext:
    """One candidate, defaulting to an empty padel match at ``START``."""

    resolved = record if record is not None else a_match()
    return MatchScoringContext(
        match_id=match_id or uuid4(),
        version=version,
        record=resolved,
        club=club or a_club(),
        share=Money(amount=share),
        court_total=Money(amount=court_total),
        occupants=(
            occupants
            if occupants is not None
            else tuple(rated(240) if seat.taken else None for seat in resolved.seats)
        ),
        counted=counted,
    )


def rated(hundredths: int, *, sigma: int = 60, who: UUID | None = None) -> PlayerSkill:
    """One seated player's rating. σ and Confidence derived as the context does."""

    return PlayerSkill(
        player=PlayerRef(str(who or uuid4())),
        level=level(hundredths),
        uncertainty=uncertainty(sigma),
        confidence=max(0, min(99, round(100 * (1 - sigma / 120)))),
    )


def unrated(who: UUID | None = None) -> UnratedPlayer:
    return UnratedPlayer(player=PlayerRef(str(who or uuid4())))


class FakeCityMatches:
    """Retrieval, answering whatever a case set up and remembering the window."""

    def __init__(self, *contexts: MatchScoringContext) -> None:
        self._contexts = contexts
        self.asked: list[tuple[frozenset[Sport], Instant, Instant]] = []

    async def contexts(
        self, *, sports: frozenset[Sport], window_from: Instant, window_to: Instant
    ) -> tuple[MatchScoringContext, ...]:
        self.asked.append((sports, window_from, window_to))
        return self._contexts


class RecordingScoringContexts:
    """The context cache, with both halves visible.

    ``asked`` is every key a compose looked up and ``stored`` every context it
    wrote, which is the only way to see from outside that the key is
    ``matchId : recordVersion`` and that a bumped version misses.
    """

    def __init__(self, *held: MatchScoringContext) -> None:
        self._held = {(one.match_id, one.version): one for one in held}
        self.asked: list[tuple[tuple[UUID, int], ...]] = []
        self.stored: list[tuple[tuple[UUID, int], ...]] = []

    async def known(
        self, keys: Sequence[tuple[UUID, int]]
    ) -> Mapping[tuple[UUID, int], MatchScoringContext]:
        self.asked.append(tuple(keys))
        return {key: self._held[key] for key in keys if key in self._held}

    async def remember(self, contexts: Sequence[MatchScoringContext]) -> None:
        self.stored.append(tuple((one.match_id, one.version) for one in contexts))
        for one in contexts:
            self._held[(one.match_id, one.version)] = one


class FakeCommitments:
    """What the viewer is already doing, as ``(id, start, end)`` triples."""

    def __init__(self, *held: tuple[UUID, Instant, Instant]) -> None:
        self._held = held
        self.asked: list[UUID] = []

    async def held_by(
        self, player_id: UUID
    ) -> tuple[tuple[UUID, Instant, Instant], ...]:
        self.asked.append(player_id)
        return self._held


class FakeStandbyPlaces:
    """Which matches she is queued for. Empty unless a case says otherwise."""

    def __init__(self, *queued: UUID) -> None:
        self._queued = frozenset(queued)
        self.asked: list[UUID] = []

    async def for_player(self, player_id: UUID) -> frozenset[UUID]:
        self.asked.append(player_id)
        return self._queued


class FakeRatings:
    """The viewer's own rating, per sport, in the engines' vocabulary."""

    def __init__(self, **at_sport: Occupant | None) -> None:
        self._at = {Sport(name): who for name, who in at_sport.items()}
        self.asked: list[tuple[UUID, Sport]] = []

    async def occupant(self, *, player_id: UUID, sport: Sport) -> Occupant | None:
        self.asked.append((player_id, sport))
        return self._at.get(sport)


def a_viewer_rated_at(hundredths: int = 300, *sports: Sport) -> FakeRatings:
    """Somebody the platform can place, at whichever sports a case names."""

    return FakeRatings(
        **{sport.value: rated(hundredths) for sport in (sports or (Sport.PADEL,))}
    )
