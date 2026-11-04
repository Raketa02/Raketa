"""What ``/me`` reads off the account's own stream.

The **nickname**, whose absence is the gate's first destination — *no
nickname* (``docs/adr/0199`` §3), an account an Invitation opened included.
And whether the account has given the **Adult attestation**
(``docs/adr/0185`` §5), which *Start playing* asks first when it has not.

From the stream rather than the projection: the gate reads these the instant
after the commit that wrote them, which is exactly when a read model that had
not caught up would send a player back to a step they just finished — and the
projection has no column for the attestation at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final
from uuid import UUID

from app.application.ports import DomainEventStore
from app.modules.users.application.user_stream import replay_user
from app.modules.users.domain.errors import AdultAttestationMissing


@final
@dataclass(frozen=True, slots=True)
class OwnAccount:
    nickname: Optional[str]
    adult_attested: bool


class ReadOwnAccount:
    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def execute(self, user_id: UUID) -> OwnAccount:
        user = await replay_user(self._event_store, user_id)
        if user is None:
            return OwnAccount(nickname=None, adult_attested=False)
        return OwnAccount(
            nickname=None if user.nickname is None else user.nickname.value,
            adult_attested=bool(user.adult_attested),
        )

    async def refuse_unless_attested(self, user_id: UUID) -> None:
        """**Playing requires the Adult attestation** (``docs/adr/0185`` §5):
        asked where a player-side record begins — an assessment, a Player
        profile — because an account an Invitation opened holds none until
        *Start playing*, and sign-up no longer guarantees every account one."""

        if not (await self.execute(user_id)).adult_attested:
            raise AdultAttestationMissing()
