"""The Adult attestation, given by an account that already exists
(``docs/adr/0185`` §5).

``POST /api/v1/users/me/adult-attestation`` — what *Start playing* asks first,
of an account an Invitation opened, before anything player-side can be reached.
The claim is built as the sign-up builds it, from an :class:`AdultAttestation`
that cannot be constructed from a *no*, so a refusal is the sign-up's refusal
in the sign-up's code. **Once**: an account that has attested, here or at
sign-up, records nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.kernel import Clock
from app.modules.users.application.user_stream import USER_AGGREGATE, replay_user
from app.modules.users.domain.value_objects import AdultAttestation


@dataclass(frozen=True)
class AttestAdultCommand:
    user_id: UUID
    adult_attested: bool


class AttestAdult:
    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: AttestAdultCommand) -> None:
        # The refusal first, as registration's is: nothing is read for a no.
        AdultAttestation(command.adult_attested)
        user = await replay_user(self._event_store, command.user_id)
        if user is None:
            raise RuntimeError(f"user {command.user_id} has no stream to attest on")
        expected_version = user.version
        user.attest_adult(occurred_at=self._clock.now())
        pending = user.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=USER_AGGREGATE,
            aggregate_id=user.id,
            expected_version=expected_version,
            events=pending,
        )
        await self._events.publish_many(pending)
        await self._uow.commit()
