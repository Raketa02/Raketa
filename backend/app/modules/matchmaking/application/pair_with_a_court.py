"""*What do I make of each of these people* — the pairing, recomputed at read.

``docs/adr/0143``. Somebody has been asked to play, and the screen they answer on
prints what this platform makes of the person asking. Three facts rule out every
cheaper shape, and none of them is visible from the schemas:

- **The invitee cannot read the organiser's search.** ``GET /searches/{id}`` is
  *a searcher may read their own search and nobody else's*, so the one person who
  most needs this screen has no access to the record it would be built from.
- **A challenge born of a mutual yes has no search at all**, and a design leaning
  on one leaves that conversation blank.
- **The stored reverse Fit was built not to be published.** ``fit_ba`` is scored
  with the searcher's own reliability deliberately set to ``None``; it prices how
  good a bet the searcher looks from the other side and feeds one liveness
  signal. It is the number that *looks* like exactly what a *for you* label
  wants, and it is not one.

So nothing is copied at send and nothing is replayed. **This is not a search**
(``docs/adr/0104``'s rule binds searches): no candidates are generated, nothing
is ranked, withheld or explained, there is no ``search_id``, no Origin key and no
record. What it borrows from a search is the arithmetic, and it borrows it
through the same workbench every surface uses — because two implementations of
*bind a search context* would be two answers to which reads fail closed.

**The gates are not run, and that is the decision rather than an economy**
(§2). They ran over every pair of this court in the send's own transaction, and
re-running them would tell an answerer that something changed about somebody else
on the court — the one thing a safety gate may never say, and the disclosure the
answer routes already refuse to make. Both mutual gates were passed in the
reader's own direction at mint by construction, so *the challenge is the gate* is
a permission the reader holds themselves.

**The floor is not applied either, for the neighbouring reason.** A quality floor
decides who is worth putting in a **list**; nobody is being listed here. This
person is already on your court, and a card that vanished because a term stood
down would be the same disclosure by a third route.

**Two refusals, and they are two on purpose** (§6). The reader holding no rating,
no declared intent or no committed profile in the sport they were challenged in
raises this module's own three errors and means *there is nothing to compute* —
which is how this feature works rather than a corner of it. Anything else means
*it could not be read*. The caller keeps them apart because an outage drawing the
identical absence as an unrated sport is the collapse ADR-0141's Consequences
refused in as many words.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.grouping import Arranged, Arrangement, Forecast, Seated, Split
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scorable import Searcher
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.v1 import arranged
from app.kernel import InvariantViolated, Sport, iso_weekday
from app.modules.matchmaking.application.search_workbench import (
    AnsweredCandidate,
    SearchWorkbench,
)
from app.modules.matchmaking.domain.deck import mode_for_intent
from app.modules.matchmaking.domain.errors import (
    MatchmakingUnavailable,
    PlayerProfileNotCommitted,
    PlayIntentNotDeclared,
    SportNotRated,
)
from app.modules.matchmaking.domain.fence import (
    area_of,
    combine_group_sigma,
    searcher_of,
)
from app.modules.matchmaking.domain.geography import distance_km as measure_distance
from app.modules.matchmaking.domain.lineups import seats_per_side
from app.modules.matchmaking.domain.search_context import SearchContext
from app.modules.matchmaking.domain.searches import (
    SearchInitiation,
    SearchSurface,
)
from app.modules.matchmaking.domain.shortlist import (
    Generation,
    admitted_of,
    score_all,
    viewer_spot_of,
)


#: The three conflicts that mean *there is nothing to compute about this reader*
#: (§6). Being asked to play a sport you never declared for is how this feature
#: works rather than a corner of it, so they are named here — on the use case
#: that raises them — and every adapter over it keeps them apart from an outage
#: rather than catching them with everything else.
NOTHING_TO_COMPUTE = (
    PlayerProfileNotCommitted,
    SportNotRated,
    PlayIntentNotDeclared,
)


@final
@dataclass(frozen=True, slots=True)
class PairWithACourtCommand:
    """*Price these people for me, in this sport.*

    ``court_ids`` never contains the reader: a pairing with yourself is not a
    question, and the whole read would have to refuse it.

    ``mode`` is the challenge's own and ``None`` on one born of a mutual yes,
    where the surface asked nobody to pick a kind of evening. ``None`` reads the
    reader's **own** declaration through the deck's mapping, which is the rule
    that already exists for a surface with no tab — never a third vector.
    """

    reader_id: UUID
    sport: Sport
    mode: SearchMode | None
    court_ids: tuple[UUID, ...]
    #: The subset of ``court_ids`` sharing the reader's side of the net. At most
    #: one in every sport this platform serves, and empty in singles. It exists
    #: for the forecast alone: a game needs two sides, and a partner priced as an
    #: opponent is *how even would a game against them be* said about a teammate.
    partners: frozenset[UUID] = frozenset()


@final
@dataclass(frozen=True, slots=True)
class PairedSeat:
    """One person on the court, priced in the reader's own direction.

    The forecast rides beside the card rather than on it because it has a third
    author again: the card is facts about them, the Fit is a reading of the two
    of them, and this is what the **game** would look like. It is
    ``would_be_forecast``'s own question — *what would this candidate leave on
    court* — and, like that field, it is a claim about the whole line-up rather
    than about one seat: the same figure rides on every card, because a forecast
    is a fact about the game.
    """

    answered: AnsweredCandidate
    #: The whole court as arranged — its forecast and the split the forecast was
    #: read from — carried on every seat. ``None`` where no game can be arranged
    #: out of what is left of it. The split rides with the forecast because the
    #: two are one computation (``the-two-contracts.md`` §5), and a consumer
    #: that wants only the percentage reads ``forecast`` below.
    arranged: Arranged | None

    @property
    def player_id(self) -> UUID:
        return UUID(self.answered.scored.player_id)

    @property
    def forecast(self) -> Forecast | None:
        return None if self.arranged is None else self.arranged.forecast

    @property
    def split(self) -> Split | None:
        return None if self.arranged is None else self.arranged.split


@final
class PairWithACourt:
    """The pairing block for one court, computed for one reader.

    **It holds no store it could write to.** Nothing here is recorded, which is
    what keeps a screen that is opened by a tap out of *searches run*.
    """

    def __init__(
        self,
        *,
        workbench: SearchWorkbench,
        ruleset: Ruleset,
        engine: MatchFit,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine

    async def execute(
        self, command: PairWithACourtCommand
    ) -> tuple[PairedSeat, ...]:
        """A priced seat per person the index can still describe, sorted.

        **Sorted on the player's id**, because a set is never the source of an
        order and the rule is stated on the collection rather than on what
        happens to be observable (``docs/adr/0105`` §1).
        """

        if not command.court_ids:
            return ()
        searcher = await self._work.searcher_facts(
            player_id=command.reader_id,
            sport=command.sport,
            mode_of=lambda intent: (
                command.mode
                if command.mode is not None
                else mode_for_intent(intent, self._ruleset.intent)
            ),
        )
        now = self._work.clock.now()
        # **The workbench's own binding, staleness refusal and all.** A day-old
        # index means a stale Level, a stale band and a stale area, and ADR-0111
        # refuses past that on quality grounds — which is exactly the ground a
        # card stands on. The refusal reaches the reader as *the pairing could
        # not be read*, never as a failed screen.
        snapshot, _ = self._work.bound_snapshot(command.sport, now)
        context = await self._work.bind(
            searcher,
            snapshot,
            now,
            # **The population every live read is about is the court itself.**
            # A search binds the bounding box because that is who it might
            # score; this reads at most three other people, all of them already
            # named on an arrangement the reader is inside.
            in_box=command.court_ids,
            # Neither of these is read by anything this use case runs, and
            # nothing is recorded, so neither reaches a column. They are on
            # ``SearchContext`` because a *search* stores them: ``surface`` is
            # never read outside the record at all, and ``initiation`` is read
            # by the proposals gate alone, which is one of the gates §2 does not
            # run.
            surface=SearchSurface.SHORTLIST,
            initiation=SearchInitiation.HUMAN,
            # The absorption cap binds inside the newcomer **gate**, and no gate
            # runs here — so the read it would need is skipped rather than
            # answered emptily.
            for_a_newcomer=False,
            # **No challenge to except**: this surface names none, and the
            # open-challenge gate excludes everybody the searcher is
            # arranging with, exactly as it always has.
            completing_challenge_id=None,
        )
        try:
            scored = score_all(
                _the_court(context, command.court_ids), context, self._engine
            )
        except InvariantViolated as broken:
            raise MatchmakingUnavailable(
                f"the matcher refused to price the court: {broken}"
            ) from broken
        answered = await self._work.attach(scored, context)
        arranged = self._arranged(answered, command, context)
        return tuple(
            sorted(
                (PairedSeat(answered=row, arranged=arranged) for row in answered),
                key=lambda seat: seat.player_id,
            )
        )

    def _arranged(
        self,
        answered: tuple[AnsweredCandidate, ...],
        command: PairWithACourtCommand,
        context: SearchContext,
    ) -> Arranged | None:
        """What the court as it stands would leave on court, in the reader's
        direction — **one figure, carried on every card.**

        A forecast is a claim about a **game**, so it is computed from the court
        rather than from a seat: everybody still in, placed where they actually
        sit. That is ``would_be_forecast``'s own reading — *what this candidate
        would leave on court*, which is the whole line-up's number and never a
        one-a-side one — and it is the reading the alternative fails at, because
        pricing a doubles partner as an opponent prints *how even would a game
        against them be* about a teammate.

        **The fenced candidates are reused rather than re-fenced.**
        ``evidence.py`` states the principle the other way round — *overlap is a
        fact about a pair where a calendar is a fact about a person* — and
        ``_searcher_as_candidate`` already refuses to recompute a pair's combined
        uncertainty for the same reason: two chances to disagree about one
        number.
        """

        return arrange_the_court(
            searcher_of(context),
            {
                UUID(row.scored.player_id): Seated(
                    candidate=row.scored.fenced, fit=0.0, locked=True
                )
                for row in answered
            },
            partners=command.partners,
            sport=command.sport,
            ruleset=self._ruleset,
        )


def arrange_the_court(
    searcher: Searcher,
    seated: Mapping[UUID, Seated],
    *,
    partners: frozenset[UUID],
    sport: Sport,
    ruleset: Ruleset,
) -> Arranged | None:
    """The court as it stands, arranged around the reader and priced. **Pure.**

    A module function rather than a method because two callers arrange a court
    this way — the challenge card through the use case above, and the
    determinism probe beside the game's pairing read — and the walk it makes is
    the one place a court could be arranged differently on two processes: the
    partner is the first of ``partners`` **sorted**, and the opponents are the
    rest of the court **sorted**, because a set is never the source of an order
    (``docs/adr/0105``).

    ``None`` where **no game can be arranged out of what is left**. A side with
    nobody on it is not a side, so a court whose far side has all declined
    leaves the reader and their partner with nothing to be forecast against —
    and a number invented for that is worse than an absence with a reason. A
    seat still open on the far side is a different case and is exactly what
    ``provisional`` is for: it reads as if the missing player matched the one
    already there.
    """

    partner = next((seated[one] for one in sorted(partners) if one in seated), None)
    opponents = tuple(
        seated[player_id] for player_id in sorted(seated) if player_id not in partners
    )
    if not opponents:
        return None
    per_side = seats_per_side(sport)
    return arranged(
        searcher,
        Arrangement(partner=partner, opponents=opponents[:per_side]),
        ruleset,
        combine_group_sigma,
        seats_per_side=per_side,
    )


def _the_court(context: SearchContext, court_ids: tuple[UUID, ...]) -> Generation:
    """The named people, measured — **and deliberately not gated.**

    ``generate`` walks a bounding box and applies every gate; this walks a list
    somebody was already put on an arrangement with. Neither the box nor the
    gates belong here: a court member outside the reader's radius is still on
    their court, and §2 is the whole argument for not re-running the four
    fail-closed gates against the reader.

    The two counts on :class:`Generation` are what a search **records**, and
    nothing here is recorded. ``n_generated`` is the court, and there is no gate
    to have excluded anybody.

    **Somebody the index cannot describe is simply absent**, and their seat is
    untouched. A row can be missing because the tail has not reached them yet or
    because they are gone; neither is a fact this screen is entitled to state, so
    it states none and draws the seat without a card.
    """

    centre = context.searcher.area
    viewer = viewer_spot_of(context)
    searcher_slots = context.searcher.grid.slots
    today = iso_weekday(context.now.isoweekday())
    wanted = {str(player_id) for player_id in court_ids}
    admitted = tuple(
        admitted_of(
            row,
            distance_km=measure_distance(centre, area_of(row)),
            viewer=viewer,
            searcher_slots=searcher_slots,
            today=today,
        )
        for row in context.snapshot.rows
        if row.player_id in wanted
    )
    return Generation(
        admitted=admitted, n_generated=len(admitted), excluded_by_gate={}
    )


__all__ = [
    "NOTHING_TO_COMPUTE",
    "PairWithACourt",
    "PairWithACourtCommand",
    "PairedSeat",
    "arrange_the_court",
]
