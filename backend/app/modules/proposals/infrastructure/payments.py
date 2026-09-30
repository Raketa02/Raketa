"""The two facts that pass between proposals and payments, one each way, and
both adapters **signed here** so the arrow runs ``proposals → payments`` only.

``PaymentsSavedMethods`` answers this context's demand — *does this player have
a method to charge* — off the player's Payment method stream. A method whose
card moved brand is still a method: its terms are asked again before the fill
can charge it (the mechanics §19), and that is the fill's to meet, not a yes's.

``LiveYesCommitments`` answers **payments'** demand — *could anything still be
charged to this method* — with the player's live yeses, across pools and sports
(the mechanics §12.4: *Remove only with nothing live*). Booked games ahead are
the Booking's to count (#541), and nought until it exists.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.payments.domain.ports import Commitments, PaymentMethodRepository
from app.modules.proposals.domain.ports import ProposalDirectory


@final
class PaymentsSavedMethods:
    def __init__(self, methods: PaymentMethodRepository) -> None:
        self._methods = methods

    async def saved_for(self, player_id: UUID) -> bool:
        return (await self._methods.load(player_id)).method is not None


@final
class LiveYesCommitments:
    def __init__(self, directory: ProposalDirectory) -> None:
        self._directory = directory

    async def of(self, player_id: UUID, *, at: Instant) -> Commitments:
        live = await self._directory.live_yeses_of(player_id, now=at)
        return Commitments(live_yeses=len(live), upcoming_games=0)
