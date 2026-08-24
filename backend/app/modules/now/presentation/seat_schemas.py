"""The wire shape of taking a seat: what the tap did, and what the screen holds.

Its own module beside ``departure_schemas.py`` and for the same reason: the
envelope in ``schemas.py`` is the *screen's* contract and imports nothing above
the domain, where a write's answer is composed by a use case and names its type.

**Three parts and not one.** ADR-0070 defines an update as *"the one card that
changed, plus any of the two viewer-owned regions whose contents or order
changed, whole"*, and until now nothing in the product could move a region — a
departure keeps the leaver's card and leaving standby removes one, both of which
the card form says by itself. Taking a seat is the act that ADR names when it
explains why the second half exists: *"an accepted offer changes three things at
once — the offer is gone, the match belongs in the strip, and the shelf copy of
that match now says you are in."*

The regions ride **beside** the update rather than inside it, which keeps
``NowUpdateResponse`` the one card it has always been for the two writes that
move nothing. Growing their answers two fields nobody fills is exactly the *"two
fields with no reader"* ADR-0071 refuses, and a client already narrowing the
update's two forms narrows nothing new here.

**The shelves are never here**, on ADR-0032's rule: dropping a joined match out
of *Best fit* would be re-ordering a shelf under the player's thumb. The shelf
copy of that match is corrected by the one card instead, which is identified by
the match and never by its position.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.now.application.seat import SeatAnswer
from app.modules.now.presentation.schemas import (
    EnrolledRegionResponse,
    NowUpdateResponse,
    OffersRegionResponse,
)


class SeatWriteResponse(BaseModel):
    """Now's update for one card, and the two regions the tap moved it between.

    **The two regions are present exactly when ``claimed`` is true**, and that is
    one decision rather than two. A tap that applied moved a card out of the
    offers region and into the strip; a tap that did not moved nothing, and
    leaving the corrected card exactly where it is is what lets the client draw
    its own fading line over a seat that has gone rather than watching the card
    vanish under her thumb.
    """

    #: What the tap **did**, and the one field here that is about the command
    #: rather than about the match. It is the departure route's ``applied`` in the
    #: shape a claim needs: without it, *was I refused* is a rule the phone
    #: derives from whether a seat claim turned up on the card, and ADR-0053
    #: leaves the phone none.
    claimed: bool
    update: NowUpdateResponse
    offers: OffersRegionResponse | None = None
    your_matches: EnrolledRegionResponse | None = None

    @classmethod
    def from_domain(cls, answer: SeatAnswer) -> "SeatWriteResponse":
        return cls(
            claimed=answer.claimed,
            update=NowUpdateResponse.from_domain(answer.update),
            offers=(
                None
                if answer.offers is None
                else OffersRegionResponse.from_domain(answer.offers)
            ),
            your_matches=(
                None
                if answer.your_matches is None
                else EnrolledRegionResponse.from_domain(answer.your_matches)
            ),
        )
