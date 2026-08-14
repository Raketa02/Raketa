"""The Assessment repository, over the event store.

Everything a use case used to have to remember lives here: which aggregate-type
string the streams are filed under, that state is rebuilt by replaying them, that
the player must be checked before the aggregate is handed back, what version the
next append expects, and which stored keys a stream is found by.

**The version is recovered, not taken.** The adapter remembers the version of
every aggregate it loaded, so ``save`` knows what the stream looked like when the
caller read it. That is why it must be constructed **per request**, from the
session, exactly as the event store dependency is — an application-scoped
instance would carry one request's versions into another and append at a version
the stream has since passed. An aggregate this repository never loaded has no
entry and is therefore appended at version zero, which is how "this stream does
not exist yet" follows from never having read it rather than from a caller
saying so.

**The finders live here for a reason of their own.** They locate a stream by
matching the *stored JSON payload* of its opening event, so their keys must agree
with ``AssessmentStarted``'s serialized field names. A rename does not raise:
the query simply returns nothing, which is indistinguishable from *no run in
progress* — the ordinary answer for almost every player. That coupling now has
one home, and it is this one, because this is the only module that knows the
streams are events at all.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Sport
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import AssessmentNotFound

ASSESSMENT_AGGREGATE = "assessment"


def _opening_key(player_id: UUID, sport: Sport | None = None) -> dict[str, str]:
    """What a stream's opening event must carry to be one of this player's.

    The keys are ``AssessmentStarted``'s field names as the codec writes them,
    and the values are its primitive forms — a sport as its ``str`` value, not
    the enum. One expression for both finders, because the per-sport lookup is
    the same key with the sport left off.
    """

    key = {"player_id": str(player_id)}
    if sport is not None:
        key["sport"] = sport.value
    return key


class EventSourcedAssessmentRepository:
    """``AssessmentRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # The identity map: aggregate id -> the stream version this request has
        # seen. Read by ``save`` as the expected version, and updated after every
        # append so a second save in the same request does not collide with the
        # first.
        self._versions: dict[UUID, int] = {}

    async def load(self, assessment_id: UUID, *, for_player: UUID) -> Assessment:
        assessment = await self._replay(assessment_id)
        if assessment is None:
            raise AssessmentNotFound()
        if assessment.player_id != for_player:
            # Another player's assessment is reported exactly as an absent one,
            # so the route cannot be used to discover which ids exist.
            raise AssessmentNotFound()

        self._remember(assessment)
        return assessment

    async def save(self, assessment: Assessment) -> None:
        pending = assessment.pull_events()
        if not pending:
            # Nothing decided anything: abandoning an already-abandoned run
            # lands here, and the retry succeeds without writing.
            return

        await self._event_store.append(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment.id,
            expected_version=self._versions.get(assessment.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction spans two aggregates when an
        # assessment completes, so its boundary stays in the use case.
        self._remember(assessment)

    async def find_open(self, *, player_id: UUID, sport: Sport) -> Assessment | None:
        open_runs = await self._newest_open_by_sport(_opening_key(player_id, sport))
        return open_runs.get(sport)

    async def find_all_open(self, *, player_id: UUID) -> list[Assessment]:
        open_runs = await self._newest_open_by_sport(_opening_key(player_id))
        # Registry order (``Sport``'s own), so a caller that wants exactly one
        # run — the entry gate does — can take the first entry and get a stable
        # answer rather than one that depends on which sport was started first.
        return [open_runs[sport] for sport in Sport if sport in open_runs]

    async def _newest_open_by_sport(
        self, payload_equals: Mapping[str, str]
    ) -> dict[Sport, Assessment]:
        """This player's unfinished runs, at most one per sport, newest winning.

        One implementation, shared by both finders, because they answer the same
        question about the same player: a gate routing to one run while the
        resume read offered another would be a bug no client could see. Narrowing
        the key to a sport is all that separates them.

        Newest-first is a tie-break between *open* runs, not a stopping rule — a
        newer run that has since ended must not hide the open one behind it —
        which is why the scan keeps going rather than stopping at the first
        stream it replays.

        This replays every assessment stream the player has ever opened,
        finished and abandoned ones included, exactly as ``list_ratings``
        replays every rating. That is the cost of reading an event-sourced store
        without a projection; a player's streams are counted in tens, and the
        alternative is a second place holding a fact the streams already hold.
        """

        candidate_ids = await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=ASSESSMENT_AGGREGATE,
            payload_equals=payload_equals,
        )

        # Candidates are ordered oldest-first; the most recently opened run is
        # the one to resume, so scan from the newest end.
        open_by_sport: dict[Sport, Assessment] = {}
        for assessment_id in reversed(candidate_ids):
            assessment = await self._replay(assessment_id)
            if assessment is None:
                continue
            if assessment.is_in_progress and assessment.sport not in open_by_sport:
                # Registered in the identity map like any loaded aggregate, so a
                # run that was found is a run that can be saved.
                self._remember(assessment)
                open_by_sport[assessment.sport] = assessment
        return open_by_sport

    async def _replay(self, assessment_id: UUID) -> Assessment | None:
        stored = await self._event_store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment_id,
        )
        if not stored:
            return None
        return Assessment.from_history(record.event for record in stored)

    def _remember(self, assessment: Assessment) -> None:
        self._versions[assessment.id] = assessment.version
