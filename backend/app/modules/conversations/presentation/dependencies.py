"""Request-scoped declarations for the conversations context.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

**The repository is built beside the unit of work it will commit through**, for
the reason every aggregate repository in this codebase is, and for one more: two
of its reads take the conversation row's lock, so it must never outlive the
transaction that will release it.

**Membership is built per request and not per use case**, because both reads and
the send ask the same question and a second copy would be a second pair of
adapters over one session.

**The stream is the one declaration here that is not per request, and it says so
twice.** ``get_opening_nudge`` runs the membership gate *before* the response
starts — an async generator's first exception is raised after the framework has
already written ``200 text/event-stream``, so a refusal inside the stream would
reach a stranger as an empty live channel instead of as
``conversation_not_found``. And having read, it **closes the request's database
session**, because the connection behind it would otherwise be held for the
fifteen minutes the stream lives and the pool is five deep
(``docs/adr/0147`` §6, and ``DB_POOL_SIZE``).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from redis.asyncio import Redis

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_a_room_of_yours,
    build_arranging_court,
    build_conversation_directory,
    build_conversation_hold_query,
    build_conversation_repository,
    build_follow_conversation,
    build_member_faces,
    build_membership,
    build_nudge_publisher,
    build_nudge_subscriber,
)
from app.infrastructure.redis_client import get_redis, get_redis_subscriber
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import FollowConversationCommand
from app.modules.conversations.application.follow_conversation import (
    FollowConversation,
)
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.read_conversation import ReadConversation
from app.modules.conversations.application.read_conversations import (
    ReadConversations,
)
from app.modules.conversations.application.read_entries import ReadEntries
from app.modules.conversations.application.send_message import SendMessage
from app.modules.conversations.domain.live import (
    Nudge,
    NudgePublisher,
    NudgeSubscriber,
)
from app.modules.conversations.domain.ports import (
    ArrangingCourt,
    ConversationDirectory,
    ConversationRepository,
    MemberFaces,
)
from app.modules.users.presentation.dependencies import AuthenticatedSessionDep

# The two pools are the process's, not the request's — neither takes a request
# or reads application state. They stay `Depends` so a test can override them,
# and so that a route asking to follow a room never has to know a client exists.
EphemeralStoreDep = Annotated[Redis, Depends(get_redis)]
SubscriberStoreDep = Annotated[Redis, Depends(get_redis_subscriber)]


def get_conversation_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ConversationRepository:
    return build_conversation_repository(
        session=db, event_store=event_store, events=events
    )


ConversationRepositoryDep = Annotated[
    ConversationRepository, Depends(get_conversation_repository)
]


def get_conversation_directory(
    db: DbSession, conversations: ConversationRepositoryDep
) -> ConversationDirectory:
    return build_conversation_directory(session=db, conversations=conversations)


ConversationDirectoryDep = Annotated[
    ConversationDirectory, Depends(get_conversation_directory)
]


def get_arranging_court(db: DbSession) -> ArrangingCourt:
    """Per request, and **shared** — which is why it is declared here at all.

    The list read asks it a second question the membership fold does not (*which
    challenges has this player accepted a seat on*), so without one declaration
    the request would build two, each an aggregate repository remembering its own
    stream versions over one session.
    """
    return build_arranging_court(db)


ArrangingCourtDep = Annotated[ArrangingCourt, Depends(get_arranging_court)]


def get_membership(db: DbSession, arranging: ArrangingCourtDep) -> Membership:
    return build_membership(db, arranging=arranging)


MembershipDep = Annotated[Membership, Depends(get_membership)]


def get_member_faces(db: DbSession, settings: SettingsDep) -> MemberFaces:
    """Per request, and **not** per unit of work.

    It reads and never writes, and it signs rather than fetching — so unlike the
    repository beside it, it remembers nothing it would have to commit and
    outlives no transaction it was built for.
    """
    return build_member_faces(db, settings=settings)


MemberFacesDep = Annotated[MemberFaces, Depends(get_member_faces)]


def get_read_conversations(
    directory: ConversationDirectoryDep,
    arranging: ArrangingCourtDep,
    membership: MembershipDep,
    faces: MemberFacesDep,
    clock: ClockDep,
) -> ReadConversations:
    return ReadConversations(
        directory=directory,
        arranging=arranging,
        membership=membership,
        faces=faces,
        clock=clock,
    )


ReadConversationsDep = Annotated[ReadConversations, Depends(get_read_conversations)]


def get_a_room_of_yours(
    conversations: ConversationRepositoryDep,
    membership: MembershipDep,
    clock: ClockDep,
) -> ARoomOfYours:
    """Per request, because the repository it holds is."""
    return build_a_room_of_yours(
        conversations=conversations, membership=membership, clock=clock
    )


ARoomOfYoursDep = Annotated[ARoomOfYours, Depends(get_a_room_of_yours)]


def get_read_conversation(
    rooms: ARoomOfYoursDep,
    faces: MemberFacesDep,
    clock: ClockDep,
) -> ReadConversation:
    return ReadConversation(rooms=rooms, faces=faces, clock=clock)


ReadConversationDep = Annotated[ReadConversation, Depends(get_read_conversation)]


def get_read_entries(rooms: ARoomOfYoursDep) -> ReadEntries:
    return ReadEntries(rooms=rooms)


ReadEntriesDep = Annotated[ReadEntries, Depends(get_read_entries)]


def get_nudge_publisher(store: EphemeralStoreDep) -> NudgePublisher:
    return build_nudge_publisher(store)


NudgePublisherDep = Annotated[NudgePublisher, Depends(get_nudge_publisher)]


def get_nudge_subscriber(store: SubscriberStoreDep) -> NudgeSubscriber:
    return build_nudge_subscriber(store)


NudgeSubscriberDep = Annotated[NudgeSubscriber, Depends(get_nudge_subscriber)]


def get_send_message(
    db: DbSession,
    rooms: ARoomOfYoursDep,
    conversations: ConversationRepositoryDep,
    nudges: NudgePublisherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SendMessage:
    return SendMessage(
        rooms=rooms,
        conversations=conversations,
        holds=build_conversation_hold_query(db),
        nudges=nudges,
        uow=uow,
        clock=clock,
    )


SendMessageDep = Annotated[SendMessage, Depends(get_send_message)]


def get_follow_conversation(
    rooms: ARoomOfYoursDep,
    nudges: NudgeSubscriberDep,
) -> FollowConversation:
    return build_follow_conversation(rooms=rooms, nudges=nudges)


FollowConversationDep = Annotated[
    FollowConversation, Depends(get_follow_conversation)
]


async def get_opening_nudge(
    conversation_id: UUID,
    caller: AuthenticatedSessionDep,
    db: DbSession,
    use_case: FollowConversationDep,
) -> Nudge:
    """The gate, the first frame, **and the last database statement.**

    Two things happen here that could not happen inside the stream itself.

    **The refusal.** A non-member has to be told ``conversation_not_found``
    before a byte of the response is written; raising from inside an async
    generator raises after ``200 text/event-stream`` is already on the wire.

    **The release.** The request session is closed the moment the read is done,
    so a stream that lives for the whole of an access token's fifteen minutes
    holds **no database connection** while it does. Without this, the pool
    (``DB_POOL_SIZE``, five) would be the ceiling on concurrent conversation
    screens — a limit nobody chose, discovered by everybody else's request
    timing out. Closing it here rather than trusting the route is deliberate:
    the exit stack that owns the session unwinds *after* the response completes,
    which is exactly too late. Closing twice is a no-op, so the teardown that
    follows is undisturbed.
    """

    opening = await use_case.open(
        FollowConversationCommand(
            conversation_id=conversation_id, reader_id=caller.user.id
        )
    )
    await db.close()
    return opening


OpeningNudgeDep = Annotated[Nudge, Depends(get_opening_nudge)]
