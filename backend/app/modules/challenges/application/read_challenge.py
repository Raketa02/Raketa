"""*One challenge, richly* — the arrangement, the people, and what I make of them.

``docs/adr/0143``. The list answers *what have I been asked*; this answers the
screen somebody says yes or no on, and it is opened by a tap — which is what pays
for a card the list could never afford, priced there over somebody's whole history
of being asked and here over one open arrangement.

**The challenge is the gate, and nothing is re-evaluated against the reader**
(§2). The four fail-closed gates ran over every pair of this court in the send's
own transaction. Re-running them would tell an answerer that something changed
about somebody else on the court — the one thing a safety gate may never say, and
the rule the two answer routes already state. Both mutual gates were passed in
the reader's own direction at mint by construction, so *the challenge is the
gate* is a permission the reader holds themselves rather than one inherited from
the organiser. The one refusal is the one the answer routes already make:
``challenge_not_found``, one code for *it does not exist* and for *you are not on
its court*, because separating them would answer *is this id real* about a
stranger's evening.

**Answering is never gated on the pairing** (§6). The arrangement always answers.
An unrelated matchmaking outage must not become *you cannot answer your
challenge*, so the card block carries an absence with a code on it and the two
buttons are drawn from the standing regardless.

**The card block is the arrangement's, and it stops when the deciding does**
(§8). Two standings draw one — :data:`ARRANGING` — and one rule covers every
other, so a standing added later is silent by default. One level down, the same
rule per seat: somebody who declined or lapsed inside a still-open
``LINE_UP_INCOMPLETE`` gets no card either, because the pair releases the moment
a seat leaves and *that person is a stranger to you once more*. They are not even
asked about, so nothing about them is computed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import NoChallengeOfYoursHasThatId
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    CourtCard,
    CourtCards,
    CourtPairingQuery,
    CourtSeat,
    PlayerNames,
)
from app.modules.challenges.domain.standing import ARRANGING, Standing


@final
@dataclass(frozen=True, slots=True)
class ReadChallengeCommand:
    """*Show me this one challenge.* The reader is the person asking."""

    challenge_id: UUID
    reader_id: UUID


@final
@dataclass(frozen=True, slots=True)
class DetailedChallenge:
    """One challenge, folded once, with everything the screen draws.

    ``court`` is ``None`` where the standing draws no card block at all, and that
    is a **third** state rather than a third absence code: the two codes say
    whose gap a missing pairing is, and this says the question was never asked.
    A client keys it off the standing it already holds.
    """

    challenge: Challenge
    standing: Standing
    read_at: Instant
    names: Mapping[UUID, str]
    court: CourtCards | None

    def card_for(self, player_id: UUID) -> CourtCard | None:
        """That person's card, if this read drew one for them."""

        if self.court is None:
            return None
        return next(
            (card for card in self.court.cards if card.person.player_id == player_id),
            None,
        )


@final
class ReadChallenge:
    """One challenge of the reader's own, and what the platform makes of its court."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        names: PlayerNames,
        pairings: CourtPairingQuery,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._names = names
        self._pairings = pairings
        self._clock = clock

    async def execute(self, command: ReadChallengeCommand) -> DetailedChallenge:
        """The arrangement, the names, and the cards where a card is drawn.

        **The clock is read once**, and every fold in the answer is against it —
        the standing, each seat's own deadline, and which seats are still in.
        Two readings would let a seat print as awaiting beside a standing that
        says its day ran out.
        """

        now = instant(self._clock.now())
        challenge = await self._yours(command)
        standing = challenge.standing_at(now)
        names = await self._names.names_of(
            sorted(
                seat.player_id
                for seat in challenge.seats
                if seat.player_id is not None
            )
        )
        return DetailedChallenge(
            challenge=challenge,
            standing=standing,
            read_at=now,
            names=names,
            court=await self._court(challenge, standing, command.reader_id, now),
        )

    async def _yours(self, command: ReadChallengeCommand) -> Challenge:
        """That challenge, if this player is on its court.

        **The two ways this refuses are one code**, which is the answer routes'
        own rule and the reason ``docs/adr/0143`` could put a route on a
        challenge id at all: a route keyed on a *stranger's* id answers *is this
        id real*, and a route keyed on a challenge answers nothing of the kind.
        """

        challenge = await self._challenges.load(command.challenge_id)
        if challenge is None or not any(
            seat.holds(command.reader_id) for seat in challenge.seats
        ):
            raise NoChallengeOfYoursHasThatId()
        return challenge

    async def _court(
        self,
        challenge: Challenge,
        standing: Standing,
        reader_id: UUID,
        now: Instant,
    ) -> CourtCards | None:
        """The cards, or ``None`` where this read draws none.

        **Nobody who has left is asked about.** A declined or lapsed seat inside
        a still-open court gets no card, and the way that is enforced is by not
        putting them in the question — so there is no card computed, no
        photograph signed and nothing to leak.

        **The reader is one of those people**
        ([#394](https://github.com/Raketa02/Raketa/issues/394)). A reader whose
        own seat has left draws no court at all, on the sentence above read about
        them instead of about the court: the pair releases the moment a seat
        leaves, so everybody still arranging is a stranger to them once more, and
        a live card of a stranger is ``docs/adr/0141``'s *directory with extra
        steps*. It is the same ``is_live_at`` the comprehension below already
        applies to everybody else, and it is asked of the reader's own seat —
        which is already in hand here, because the sides are read against it.

        **The predicate is *has this reader left* and never *has this reader
        answered*** (``docs/adr/0143``'s amendment, on #392). A reader who
        **accepted** has no answer left to give either, and they are still on the
        court and still held by the pair, so they keep their cards. That is the
        one case the two reasons for this rule disagree about.

        **Returning ``None`` is the whole of it, and no new absence is needed.**
        It is the shape an ended standing already produces: the route omits
        ``pairing_absence`` when there is no court, and ``card_for`` answers
        nothing for every seat. A ``PairingAbsence`` here would have to be
        ``COULD_NOT_BE_READ``, which means somebody's outage and would be a lie.

        **And never the reader themselves.** A pairing with yourself is not a
        question, and the whole read would refuse it.

        **Each of them carries which side of the net they are on**, read against
        the reader's own seat. A forecast is a claim about a game and a game
        needs two sides, so a partner handed over as an opponent would price a
        teammate under a sentence that says *against*.
        """

        if standing not in ARRANGING:
            return None
        mine = next((seat for seat in challenge.seats if seat.holds(reader_id)), None)
        # ``_yours`` has already refused a reader with no seat here, so the first
        # arm is unreachable rather than a case — and a read is the wrong place to
        # raise from, so it answers the same way the second does.
        if mine is None or not mine.is_live_at(now):
            return None
        court = tuple(
            CourtSeat(player_id=seat.player_id, beside_you=seat.side == mine.side)
            for seat in challenge.seats
            if seat.player_id is not None
            and seat.player_id != reader_id
            and seat.is_live_at(now)
        )
        return await self._pairings.cards_for(
            reader_id=reader_id,
            sport=challenge.sport,
            mode=challenge.mode,
            court=court,
        )
