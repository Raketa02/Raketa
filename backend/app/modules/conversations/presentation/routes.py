"""The conversation routes: list your rooms, open one, page back, say something,
and follow it live.

**Five routes, and membership is the gate on every one of them**
(``docs/adr/0148`` §2). The four fail-closed safety gates ran over every pair of
the court in the send's own transaction; **nothing is re-evaluated against the
reader**, because telling a reader that something changed about somebody else on
the court is the one thing a safety gate may never say.

**A non-member gets ``conversation_not_found``, not a 403** — one code for *it
does not exist* and *it is not yours*, on ``challenge_not_found``'s argument
verbatim: separating them would answer *is this id real* about a stranger's
evening.

**A hold refuses the send and refuses no read** (``docs/adr/0148`` §9). The hold's
argument is about **reach**, and a message is reach; but a hold must not erase an
arrangement other people are already inside, so a held player keeps reading the
room and keeps seeing the plan.

**There is no route that creates a conversation.** A room is opened by the first
acceptance, through the outbox, by a context that does not know this one exists
(``docs/adr/0146`` §5) — so there is no ``POST /conversations`` and there will
not be one.

**The fifth route is one-directional and carries no content** (``docs/adr/0147``).
``/stream`` is Server-Sent Events on the framework's own ``EventSourceResponse``
— zero new dependencies, against a WebSocket path that starts with one and whose
absence fails *silently*, since this server is pinned without the standard extra
and would refuse the upgrade rather than erroring. Sends stay ordinary
authenticated ``POST``s on this same router: a bidirectional socket would buy a
second write path with a second place to authorise and a second place to
validate, and the only thing it adds is a capability we would then write a rule
forbidding.

**There is no second stream for the Chats list, and there will not be one.** One
stream per open conversation is the entire live surface; the list is an ordinary
read on ordinary caching.
"""

from __future__ import annotations

from typing import Any, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.sse import EventSourceResponse

from app.core.exception_handlers import ErrorResponse
from app.kernel import Instant
from app.modules.conversations.application.commands import (
    ReadConversationCommand,
    ReadConversationsCommand,
    ReadEntriesCommand,
    SendMessageCommand,
)
from app.modules.conversations.application.read_conversation import (
    OpenedConversation,
)
from app.modules.conversations.application.read_conversations import ConversationRow
from app.modules.conversations.domain.entries import Entry, Message
from app.modules.conversations.domain.live import Nudge
from app.modules.conversations.domain.paging import (
    PAGE_LIMIT_CAP,
    PAGE_LIMIT_DEFAULT,
)
from app.modules.conversations.domain.ports import MemberFace
from app.modules.conversations.presentation.dependencies import (
    FollowConversationDep,
    OpeningNudgeDep,
    ReadConversationDep,
    ReadConversationsDep,
    ReadEntriesDep,
    SendMessageDep,
)
from app.modules.conversations.presentation.schemas import (
    ConversationListResponse,
    ConversationMemberSchema,
    ConversationResponse,
    ConversationRowSchema,
    EntryPageResponse,
    LiveNudgeSchema,
    MessageSchema,
    SendMessageRequest,
    SystemLineSchema,
)
from app.modules.users.presentation.dependencies import (
    AuthenticatedSessionDep,
    CurrentUserDep,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`conversation_not_found` — **one code for two cases**: there is no "
            "room with that id, or there is one and you are not in it. They are "
            "not told apart on purpose, because a 403 would answer *is this id "
            "real* about a stranger's evening.\n\n"
            "Leave the screen. There is no retry that changes this."
        ),
    },
}


#: The same refusal, spelled as JSON. **Only this route needs it.**
#:
#: A route's ``responses`` take their media type from its response *class*, and
#: this one's is ``text/event-stream`` — so ``"model": ErrorResponse`` would
#: document the 404 envelope as an event stream, which is not what a refused
#: request answers with. The refusal is written before the stream begins
#: (``presentation/dependencies.py``), so it is an ordinary JSON error like every
#: other one on this router. The reference is built from the class's own name so
#: a rename cannot leave a dangling pointer here; ``app/api/contract.py``
#: registers that schema on every surface.
_NOT_FOUND_AS_JSON: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "description": _NOT_FOUND[status.HTTP_404_NOT_FOUND]["description"],
        "content": {
            "application/json": {
                "schema": {"$ref": f"#/components/schemas/{ErrorResponse.__name__}"}
            }
        },
    },
}


@router.get(
    "",
    response_model=ConversationListResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Every room you are a member of, the ones that moved last first."
            ),
        },
    },
    summary="Your conversations",
    description=(
        "**A room opens on the first acceptance and grows with each one after "
        "it.** A doubles court whose line-up is still filling draws the members "
        "it has, not the court it will be.\n\n"
        "**Ordered by the last entry, newest first.** A room where nothing has "
        "happened yet carries `last_entry: null` and orders on the moment it "
        "opened — the opening writes no line, so there is genuinely nothing "
        "there yet.\n\n"
        "**No state pill and no standing.** The last entry is what a pill would "
        "have said; a standing beside it would be a second place for one fact to "
        "be true. The state-keyed surfaces are the challenge screen and the game "
        "screen.\n\n"
        "**Only live rooms are here, because there are only live rooms.** A "
        "conversation is destroyed rather than delisted once the episode it was "
        "opened for is over — deliberately the opposite of `GET /challenges`, "
        "which keeps ended challenges and says so. The difference is the "
        "difference between a record and a room.\n\n"
        "**This is one of two reads for the Chats tab, and they are not "
        "merged.** `GET /challenges` is the other. Two sections, two contexts, "
        "two queries, two caches."
    ),
)
async def read_conversations(
    user: CurrentUserDep,
    use_case: ReadConversationsDep,
) -> ConversationListResponse:
    read_at, rows = await use_case.execute(ReadConversationsCommand(reader_id=user.id))
    return ConversationListResponse(
        read_at=read_at, conversations=[_row(row) for row in rows]
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "The room's header and its newest page, from one fold."
        },
        **_NOT_FOUND,
    },
    summary="One conversation",
    description=(
        "**The header and the newest page in one response**, folded against one "
        "instant, so the members you are holding and the entries you are drawing "
        "can never disagree about who is in the room.\n\n"
        "**Open at the newest entry and page backward** from `entries[0].seq` "
        "through `/entries`. You have the whole conversation when you hold `seq` "
        "1 — there is no `has_more`, because a gapless sequence makes `seq` 1 the "
        "beginning.\n\n"
        "**Nothing here is re-evaluated against you.** The safety gates ran when "
        "the challenge was minted; a read that re-ran them would tell you "
        "something changed about somebody else."
    ),
)
async def read_conversation(
    conversation_id: UUID,
    user: CurrentUserDep,
    use_case: ReadConversationDep,
) -> ConversationResponse:
    read_at, room = await use_case.execute(
        ReadConversationCommand(conversation_id=conversation_id, reader_id=user.id)
    )
    return _conversation(room, read_at=read_at)


@router.get(
    "/{conversation_id}/entries",
    response_model=EntryPageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "One page, oldest first inside it."},
        **_NOT_FOUND,
    },
    summary="A page of a conversation, backward",
    description=(
        "**A cursor over `seq`, never an offset.** One code path serves history "
        "and catch-up: a client that has been away and finds a hole below the "
        "newest page walks backward through this route until it reaches its own "
        "high-water mark.\n\n"
        "**`before_seq` is exclusive**, and omitting it asks for the newest "
        "page.\n\n"
        "**No header and no `read_at` here.** A page of entries is folded against "
        "nothing — every entry carries its own moment — so a second instant would "
        "be a second clock to reconcile against the one the detail read gave you."
    ),
)
async def read_entries(
    conversation_id: UUID,
    user: CurrentUserDep,
    use_case: ReadEntriesDep,
    before_seq: int | None = Query(
        None,
        ge=1,
        description=(
            "Return the entries **before** this one. Omit for the newest page. "
            "An empty answer means you are holding the beginning."
        ),
    ),
    limit: int = Query(
        PAGE_LIMIT_DEFAULT,
        ge=1,
        le=PAGE_LIMIT_CAP,
        description=(
            "How many entries to return. **Over the cap is a 422 rather than a "
            "silent clamp** — a route that quietly returns something other than "
            "what was asked for cannot be told apart from one that ran out."
        ),
    ),
) -> EntryPageResponse:
    entries = await use_case.execute(
        ReadEntriesCommand(
            conversation_id=conversation_id,
            reader_id=user.id,
            before_seq=before_seq,
            limit=limit,
        )
    )
    return EntryPageResponse(entries=[_entry(entry) for entry in entries])


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "The message as it was recorded — **or, on a repeat, the one "
                "that already stands.**"
            )
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`message_is_empty` — nothing but whitespace.\n\n"
                "`message_is_too_long` — past the cap. **Refused, never "
                "truncated**: a shortened message is one you believe you sent "
                "whole, in front of other people."
            ),
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": (
                "`account_held` — your account is under a live hold. **A hold "
                "stops you writing anywhere another player sees it, and never "
                "stops you reading**: every read on this context stays open to "
                "you, because a hold must not erase an arrangement other people "
                "are already inside."
            ),
        },
        **_NOT_FOUND,
    },
    summary="Say something",
    description=(
        "**`200`, not `201`, and the message comes back.** A repeat carrying the "
        "same `client_message_id` answers with the same message and the same "
        "`seq`, and records nothing — so a send that paused offline and resumed "
        "can never become two bubbles.\n\n"
        "**The message is returned rather than refetched**, which is also what "
        "keeps your own message off the live channel's round trip.\n\n"
        "**It has no id of its own.** `(conversation_id, seq)` identifies it."
    ),
)
async def send_message(
    conversation_id: UUID,
    payload: SendMessageRequest,
    user: CurrentUserDep,
    use_case: SendMessageDep,
) -> MessageSchema:
    message = await use_case.execute(
        SendMessageCommand(
            conversation_id=conversation_id,
            author_id=user.id,
            client_message_id=payload.client_message_id,
            text=payload.text,
        )
    )
    return _message(message)


@router.get(
    "/{conversation_id}/stream",
    response_class=EventSourceResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "An open `text/event-stream`. Every frame is a `LiveNudgeSchema` "
                "and nothing else."
            )
        },
        **_NOT_FOUND_AS_JSON,
    },
    summary="Follow a conversation",
    description=(
        "**A nudge, and nothing else on the wire.** Every frame is "
        "`{ v, conversation_id, last_seq }`. On receiving one, fetch from "
        "**your own** high-water mark through `GET /conversations/{id}/entries` "
        "— never from `last_seq`.\n\n"
        "**A dropped frame costs nothing.** Because you fetch from your own "
        "cursor and not from the frame's number, the *next* nudge repairs "
        "whatever the lost one would have said. There is nothing to detect and "
        "nothing to reconcile.\n\n"
        "**One frame arrives the moment the stream opens**, carrying the room's "
        "current `last_seq`. That is what makes resume correct without "
        "`Last-Event-ID` being load-bearing, and it is how a client that has "
        "been away catches up in one step.\n\n"
        "**The stream closes when your access token expires** — about every "
        "fifteen minutes. Reconnect with a fresh one through your ordinary "
        "refresh path; the token travels in the `Authorization` header, never a "
        "query string.\n\n"
        "**A closed stream means the room is not live, and nothing more.** It "
        "closes on token expiry, on a deploy, and when this server's own "
        "subscriber cannot be reached — deliberately, so that a chat which is "
        "not live *looks* not-live instead of looking up to date. Every read on "
        "this context keeps working throughout; only the latency changes.\n\n"
        "**Close it when the app backgrounds and re-open on foreground.** iOS "
        "severs a backgrounded app's connections, and re-opening is the same "
        "code path as any other reconnect."
    ),
)
async def follow_conversation(
    opening: OpeningNudgeDep,
    caller: AuthenticatedSessionDep,
    use_case: FollowConversationDep,
) -> AsyncIterator[LiveNudgeSchema]:
    """The live channel.

    **Membership ran in ``OpeningNudgeDep``, before this generator existed** —
    see ``presentation/dependencies.py``. By the time the first frame is written
    the reader has been gated and the request's database session is closed.

    **The frames go out through the declared model, and the hole that remains is
    ``docs/adr/0147`` §7's, named rather than closed.** The checks cover the
    *declaration*: `make openapi` publishes `LiveNudgeSchema` and the client
    generates its type from it. **Nothing proves the emission.** What narrows it
    is that the framework validates and serialises each yielded item against that
    model on the way out — so a frame that did not match would raise here rather
    than ship — but a stream body is not a response model, nothing type-checks
    this route against its own annotation, and the residual risk is affordable
    only because the shape is three fields wide.
    """

    async for nudge in use_case.follow(opening, until=caller.expires_at):
        yield _nudge(nudge)


# ---------------------------------------------------------------------------
# Rendering. **Nothing here folds anything** — the use case did, against one
# instant, and a second fold in the presentation layer is a second clock.
# ---------------------------------------------------------------------------


def _nudge(nudge: Nudge) -> LiveNudgeSchema:
    return LiveNudgeSchema(
        v=nudge.v,
        conversation_id=nudge.conversation_id,
        last_seq=nudge.last_seq,
    )


def _row(row: ConversationRow) -> ConversationRowSchema:
    return ConversationRowSchema(
        conversation_id=row.conversation_id,
        challenge_id=row.challenge_id,
        game_id=row.game_id,
        sport=row.sport,
        members=[_member(member) for member in row.members],
        last_entry=None if row.last_entry is None else _entry(row.last_entry),
    )


def _conversation(
    room: OpenedConversation, *, read_at: Instant
) -> ConversationResponse:
    return ConversationResponse(
        read_at=read_at,
        conversation_id=room.conversation_id,
        challenge_id=room.challenge_id,
        game_id=room.game_id,
        sport=room.sport,
        members=[_member(member) for member in room.members],
        entries=[_entry(entry) for entry in room.entries],
    )


def _member(member: MemberFace) -> ConversationMemberSchema:
    """One member. **The two photograph fields are set together or not at all.**

    Set rather than passed as ``None``, because these two are *omitted* where
    every other nullable field here is ``null``: a player with no photograph is
    not an absence to report — the client draws a generated court poster, which
    needs nothing from the wire. The routes are declared
    ``response_model_exclude_unset=True`` so an unset field is genuinely missing
    from the JSON rather than present and null.
    """

    face: dict[str, Any] = {
        "player_id": member.player_id,
        "nickname": member.nickname,
    }
    if member.photo_id is not None and member.photo_url is not None:
        face["photo_id"] = member.photo_id
        face["photo_url"] = member.photo_url
    return ConversationMemberSchema(**face)


def _entry(entry: Entry) -> MessageSchema | SystemLineSchema:
    if isinstance(entry, Message):
        return _message(entry)
    return SystemLineSchema(
        # **Set rather than defaulted**, because these routes are declared
        # ``response_model_exclude_unset=True`` for the photograph's sake and an
        # unset discriminator would be dropped with it — leaving a union a client
        # cannot tell apart.
        type="system_line",
        seq=entry.seq,
        code=entry.code.value,
        occurred_at=entry.occurred_at,
        actor_id=entry.actor_id,
        values=dict(entry.values),
    )


def _message(message: Message) -> MessageSchema:
    return MessageSchema(
        # Set rather than defaulted. See ``_entry``.
        type="message",
        seq=message.seq,
        author_id=message.author_id,
        sent_at=message.sent_at,
        text=message.text.value,
        client_message_id=message.client_message_id,
    )
