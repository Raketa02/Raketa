"""``CourtPairingQuery``'s adapter — the card, the pairing and the photograph.

``challenges`` may not import the matcher, and the detail screen needs three
things that are the matcher's and nobody else's: who each person on the court is,
what the reader's own pairing with them prices at, and an address for the
photograph. **One question and not three** — a caller that asked for each
separately would be three reads of one computation, and a court assembled from
two of them and refused on the third (``docs/adr/0143`` §4).

**It reads the provider's own use case and never the provider's store.** The
decision about what a pairing *is* — recomputed for the reader, ungated, unranked,
unrecorded — belongs to ``pair_with_a_court.py``; a snapshot walk written here
would make ``challenges`` a second author of it. That is
``ChallengesMutualChallenge``'s shape, one direction over.

**The photograph is minted here, where the photo store already is.** Refusing it
would make the person who asked you to play more anonymous than a stranger in
your deck, which is the wrong way round; and minting it in ``challenges`` would
put that context in front of a bucket it has no business knowing about.
``photo_id`` and ``photo_url`` cross **exactly together**, so a signature that
failed leaves the client drawing the generated court poster rather than an id it
can do nothing with.

**Two refusals and never an exception** (§6). The arrangement always answers,
because answering is not gated and an unrelated matchmaking outage must never
become *you cannot answer your challenge*. The reader's own three conflicts mean
*there is nothing to compute*; anything else means *it could not be read*, and
the two are kept apart because an outage drawing the identical absence as an
unrated sport is the collapse ADR-0141's Consequences refused in as many words.
"""

from __future__ import annotations

import logging
from typing import Collection, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.challenges.domain.ports import (
    CourtCard,
    CourtCards,
    CourtPairing,
    CourtPerson,
    LevelDeltas,
    PairingAbsence,
    PairingForecast,
)
from app.modules.matchmaking.application.pair_with_a_court import (
    PairedSeat,
    PairWithACourt,
    PairWithACourtCommand,
)
from app.modules.matchmaking.application.record_rows import term_rows
from app.modules.matchmaking.domain.cards import CardPhotoLinks
from app.modules.matchmaking.domain.errors import (
    PlayerProfileNotCommitted,
    PlayIntentNotDeclared,
    SportNotRated,
)

logger = logging.getLogger(__name__)

#: The three conflicts that mean *there is nothing to compute about this reader*.
#: Being asked to play a sport you never declared for is how this feature works
#: rather than a corner of it, so they are named rather than caught with
#: everything else.
NOTHING_TO_COMPUTE = (
    PlayerProfileNotCommitted,
    SportNotRated,
    PlayIntentNotDeclared,
)


@final
class ChallengeCourtCards:
    """What the matcher makes of each person on a court, for the reader."""

    def __init__(
        self, *, pairing: PairWithACourt, photos: CardPhotoLinks
    ) -> None:
        self._pairing = pairing
        self._photos = photos

    async def cards_for(
        self,
        *,
        reader_id: UUID,
        sport: Sport,
        mode: SearchMode | None,
        court_ids: Collection[UUID],
    ) -> CourtCards:
        try:
            seats = await self._pairing.execute(
                PairWithACourtCommand(
                    reader_id=reader_id,
                    sport=sport,
                    mode=mode,
                    court_ids=tuple(court_ids),
                )
            )
            links = await self._photos.links_over(_photographs(seats))
        except NOTHING_TO_COMPUTE:
            return CourtCards(absent=PairingAbsence.NOTHING_TO_COMPUTE)
        except Exception:
            # **Broad, and deliberately so**, on ``read_demand``'s precedent: a
            # provider that raises and one that answers something this adapter
            # cannot translate are the same event to the screen — the pairing
            # could not be read — and the arrangement answers either way. What
            # keeps it from being silent is this line and the code on the wire,
            # which is a named gap rather than an empty block.
            logger.warning(
                "the court's pairing could not be read", exc_info=True
            )
            return CourtCards(absent=PairingAbsence.COULD_NOT_BE_READ)
        return CourtCards(
            cards=tuple(_card(seat, links.get(seat.player_id)) for seat in seats)
        )


@final
class NoCourtCanBePriced:
    """``CourtPairingQuery`` where this process cannot price a court at all.

    No candidate index, or no ephemeral store behind the exposure ledger — two
    outages with one answer, because the reader is owed *whose gap this is* and
    not *which of our machines*.

    **A null object rather than a refusal**, which is the one place this differs
    from ``get_candidate_source``'s. A search with no index is a search that
    cannot answer and says ``503``; a challenge detail answers anyway, because
    the arrangement is the read and answering is not gated (``docs/adr/0143``
    §6). What the reader gets is the code for *it could not be read* — the same
    answer any other outage produces, which is what stops the three states
    collapsing into two.
    """

    async def cards_for(
        self,
        *,
        reader_id: UUID,
        sport: Sport,
        mode: SearchMode | None,
        court_ids: Collection[UUID],
    ) -> CourtCards:
        return CourtCards(absent=PairingAbsence.COULD_NOT_BE_READ)


def _photographs(seats: Collection[PairedSeat]) -> dict[UUID, UUID]:
    """Whose photograph needs an address, by owner.

    A card with no photo id is absent rather than present as ``None``: there is
    nothing to sign, and the poster is what the client draws instead.
    """

    return {
        seat.player_id: photo_id
        for seat in seats
        if (photo_id := seat.answered.card.photo_id) is not None
    }


def _card(seat: PairedSeat, photo_url: str | None) -> CourtCard:
    """One priced seat, in ``challenges``' own vocabulary.

    **This is the second mapper ``docs/adr/0143`` priced in its Consequences**,
    and it is where the narrowing happens: no bio, no ``liveness_reasons`` — *why
    did this person move* is a question about a list, and there is no list — no
    ``inclusion_reason``, no ``modifiers``, no counted games, no run of form and
    no photo verdict. What survives is what the screen draws.
    """

    scored = seat.answered.scored
    card = seat.answered.recorded_card()
    return CourtCard(
        person=CourtPerson(
            player_id=seat.player_id,
            nickname=card.nickname,
            area_code=card.area_code,
            level=card.level,
            band=card.band,
            range_low=card.range_low,
            range_high=card.range_high,
            # Exactly together: a signature that could not be minted leaves the
            # poster, never an id with nothing behind it.
            photo_id=None if photo_url is None else card.photo_id,
            photo_url=photo_url,
            player_score=card.player_score,
        ),
        pairing=CourtPairing(
            # The **modified** Fit, which is the number a card prints: the
            # reliability dock is part of what the platform makes of a pairing,
            # and a figure that left it out would disagree with every other
            # surface's.
            fit=scored.modified.points,
            terms=term_rows(scored.fit),
            degraded_terms=tuple(
                (stood.term.value, stood.reason.value)
                for stood in scored.fit.degraded_terms
            ),
            concerns=tuple(term.value for term in scored.fit.concerns),
            forecast=PairingForecast(
                pct=seat.forecast.pct,
                sigma_group=seat.forecast.sigma_group,
                provisional=seat.forecast.provisional,
                assumption=(
                    None
                    if seat.forecast.assumption is None
                    else seat.forecast.assumption.value
                ),
            ),
            # ``None`` and never a zero when the distance term stood down,
            # decided once on ``Scored`` so this screen and a shortlist cannot
            # come to two answers about one distance.
            distance_km=scored.shown_distance_km,
            at_stake=(
                None
                if seat.answered.at_stake is None
                else LevelDeltas(
                    win_delta=seat.answered.at_stake.win_delta,
                    loss_delta=seat.answered.at_stake.loss_delta,
                )
            ),
        ),
    )
