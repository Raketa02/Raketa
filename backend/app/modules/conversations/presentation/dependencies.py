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
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

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
    build_member_faces,
    build_membership,
)
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.read_conversation import ReadConversation
from app.modules.conversations.application.read_conversations import (
    ReadConversations,
)
from app.modules.conversations.application.read_entries import ReadEntries
from app.modules.conversations.application.send_message import SendMessage
from app.modules.conversations.domain.ports import (
    ArrangingCourt,
    ConversationDirectory,
    ConversationRepository,
    MemberFaces,
)


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
    conversations: ConversationRepositoryDep, membership: MembershipDep
) -> ARoomOfYours:
    """Per request, because the repository it holds is."""
    return build_a_room_of_yours(conversations=conversations, membership=membership)


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


def get_send_message(
    db: DbSession,
    rooms: ARoomOfYoursDep,
    conversations: ConversationRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SendMessage:
    return SendMessage(
        rooms=rooms,
        conversations=conversations,
        holds=build_conversation_hold_query(db),
        uow=uow,
        clock=clock,
    )


SendMessageDep = Annotated[SendMessage, Depends(get_send_message)]
