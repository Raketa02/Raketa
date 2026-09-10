"""Open the rooms the seeded acceptances earned, fill one, and read them back.

**A room is not written and cannot be.** A conversation is *told*, through the
outbox, by contexts that do not know it exists (``docs/adr/0146`` §5) — so this
layer has no *open a room* use case to call and deliberately none. What it does
is **deliver**: it drains the transactional outbox in process, exactly as the
embedded worker drains it under the API, and every acceptance, decline, lapse,
completion and *we played* the layers above already seeded arrives at the room it
belongs to.

That barrier is the whole of the first half, and it is safe rather than exempt
for the reason ``tick_the_tail_to_catch_up`` is: the batch takes its rows
``FOR UPDATE SKIP LOCKED``, so an API worker draining at the same moment finds
nothing left. Calling it twice is a no-op the second time.

**The second half is the one thing a room cannot be told**: somebody saying
something. Messages go through ``SendMessage``, the use case a request runs, so a
seeded bubble has the stream position, the sequence number and the idempotency a
real one has. They exist to reach a state no arrangement produces — **a room long
enough to page backward through** — which is a screen state and therefore this
fixture's business.

**Every message is idempotent on its own ``client_message_id``**, derived from
the room and the position rather than minted, so a second ``make seed`` writes
nothing and the room does not grow by fifty every run. That is the same move
every layer here makes and the reason none of them needs a probe.

**The third thing it does is destroy**, and that is what a fixture can show and
a test cannot: the played history is written in the past and ``CONVERSATION_GRACE``
is forty-eight hours, so **every room it opened has ended** (``docs/adr/0153``) —
while the game ``app/seeds/loop.py`` has played *this evening* keeps its room, and
that pair of facts is the lifetime rather than an accident of the population. The
run sweeps in process, exactly as it delivers in process, and then reads the list
again: what the report prints is a count of rooms that stopped existing beside a
count of rooms that did not, which is the only way *destroyed, not delisted* is
visible on a laptop.

**Three of the four room shapes are reached and the fourth is named**, because a
fixture that quietly reached three would read as having reached four:

- **a two-member room whose line-up completed** — one of the four tennis singles
  games ``plans.py`` arranges and nobody plays, which is the shape a Chats row
  draws with a *Details* door on it. It comes from **that** layer rather than
  from the played history, and the reason is the destruction: a played game's
  room is over before the run reads it;
- **a doubles room whose membership is still growing** — the half-built court
  ``pairs.py`` leaves standing, which has no game and therefore no *Details*
  door. **It is not the protagonist's**, and that is worth knowing rather than
  fixing here: she is *invited* to that court and has not answered, so she is not
  a member of the room it opened. A room she is in is a state the relationship
  layer does not currently reach, which is why the claims below read as everybody
  rather than as her;
- **a room long enough to page backward through** — this layer's own messages.

The fourth, **a room carrying every system-line code**, is
``app/seeds/loop.py``'s: three codes need a court that grew or shrank after its
room opened and one needs a game played inside the grace, and that layer sends
the courts and the game for them. The Plan's four are ``app/seeds/plans.py``'s,
and one of those — the **lock** — has a single producer, so the claim is what
holds that row in place. It is asserted there rather than here, beside
the rows that reach it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, final
from uuid import UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_a_room_of_yours,
    build_arranging_court,
    build_clock,
    build_conversation_directory,
    build_conversation_repository,
    build_conversation_hold_query,
    build_destroy_ended_conversations,
    build_domain_event_store,
    build_event_publisher,
    build_member_faces,
    build_membership,
    build_nobody_is_following,
    build_unit_of_work,
    build_user_repository,
)
from app.bootstrap.events import get_event_runtime
from app.core.config import Settings
from app.kernel import Instant
from app.modules.conversations.application.commands import (
    ReadConversationsCommand,
    ReadEntriesCommand,
    SendMessageCommand,
)
from app.modules.conversations.application.destroy_ended_conversations import (
    SweptRooms,
)
from app.modules.conversations.application.read_conversations import (
    ConversationRow,
    ReadConversations,
)
from app.modules.conversations.application.read_entries import ReadEntries
from app.modules.conversations.application.send_message import SendMessage
from app.modules.conversations.domain.entries import (
    Entry,
    SystemLine,
    SystemLineCode,
)
from app.modules.conversations.domain.lifetime import CONVERSATION_GRACE
from app.modules.conversations.domain.paging import PAGE_LIMIT_DEFAULT
from app.seeds.clock import FixedClock
from app.seeds.cohort import PLAYED_GAMES, SEED_EMAIL_DOMAIN
from app.seeds.relationships import PROTAGONIST, RELATIONSHIP_ACCOUNTS

#: How many entries the pageable room carries. **One page and a little**, so the
#: newest page is full and there is genuinely a page behind it — a room of
#: exactly ``PAGE_LIMIT_DEFAULT`` would leave *page backward* indistinguishable
#: from *there is nothing behind this*.
A_PAGE_AND_A_BIT = PAGE_LIMIT_DEFAULT + 10

#: What a room's last entry says when somebody has said they played. Read from
#: the enum rather than spelled, so a renamed code moves the claim instead of
#: silently making it vacuous.
THE_PLAYED_CODE = SystemLineCode.GAME_PLAYED.value

#: The namespace the seeded ``client_message_id``s are derived in. Any constant
#: uuid does; what matters is that it never changes, because it is what makes a
#: second run write nothing.
SEEDED_MESSAGES = UUID("6f1f0f3a-0000-4000-8000-000000000000")

#: What the two members of the pageable room say, cycled. Short and about
#: arranging a game, because a room's contents are read by a person developing a
#: screen and lorem ipsum tells them nothing about how a bubble wraps.
THE_SMALL_TALK: tuple[str, ...] = (
    "Thursday works for me",
    "same, evening?",
    "six or seven?",
    "seven is easier after work",
    "the courts by the river are usually free then",
    "I'll check if we need to book",
    "no booking needed apparently",
    "perfect — see you there",
)


#: Everybody this layer reads as. **The protagonist, the eleven relationship
#: accounts, and everybody the played history seated** — which is every account
#: that could hold a seat somebody accepted.
#:
#: There is no *all the rooms* read and there should not be: membership is the
#: gate on every route this context has, so a fixture that wanted the whole list
#: would have to go round the gate to get it.
_THE_READERS: tuple[str, ...] = (
    PROTAGONIST.email,
    *(account.email for account in RELATIONSHIP_ACCOUNTS),
    *dict.fromkeys(
        f"{handle}@{SEED_EMAIL_DOMAIN}"
        for game in PLAYED_GAMES
        for handle in game.players
    ),
)


class SeedRoomMissing(RuntimeError):
    """A room state a screen has to draw is not in this database.

    Raised rather than reported, on this fixture's own rule: an assertion here is
    a claim about the **real read path**, so a shape that is missing is a screen
    a developer is about to open and find empty.
    """


@final
@dataclass(frozen=True)
class SeededRooms:
    """What the delivery opened and what this layer wrote, as lines for the report."""

    delivered: int
    rooms: tuple[str, ...]
    said: int
    #: What the in-process sweep destroyed, and out of how many. **Printed rather
    #: than swallowed**: *nothing had ended* and *the sweep did not run* have one
    #: symptom on a fixture — the same list twice — and only one of them is a
    #: defect.
    swept: SweptRooms


async def deliver_everything_told(
    session_factory: async_sessionmaker[AsyncSession],
) -> int:
    """Drain the outbox in process, until a round delivers nothing.

    **Rounds, because delivery cascades.** A room opened by an acceptance
    publishes its own events, and those are outbox rows too; draining until a
    round publishes nothing is the honest stopping condition rather than a fixed
    number of passes.

    It builds the batch through ``EventRuntime.create_event_batch_for`` rather
    than assembling handlers here, so this is the delivery that ships — including
    the session-bound subscriber the batch adds for itself.

    **Nobody is following, and the seed says so rather than defaults to it.** A
    seed run has no phone attached: it drains a laptop's outbox with no
    conversation screen open anywhere, so the live channel is handed
    ``NobodyIsFollowing`` — the correct answer, not a degraded one. The API
    process passes the real publisher (``app/core/lifespan.py``), and the
    parameter is required at both so the difference stays written down.
    """

    runtime = get_event_runtime()
    delivered = 0
    while True:
        async with session_factory() as session:
            batch = runtime.create_event_batch_for(
                session=session,
                clock=build_clock(),
                batch_size=200,
                nudges=build_nobody_is_following(),
            )
            published = await batch.execute(worker_id="seed")
        if not published:
            return delivered
        delivered += published


async def open_the_rooms(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> SeededRooms:
    """Deliver, say something, sweep, and read every claim back off the real path."""

    delivered = await deliver_everything_told(session_factory)

    async with session_factory() as session:
        rooms = await every_room_in_the_database(session, settings=settings, now=now)
        said = await _say_a_page_and_a_bit(
            session,
            settings=settings,
            now=now,
            room=_a_room_still_arranging(rooms),
        )
        await session.commit()

    swept = await _destroy_what_has_ended(session_factory, now=now)

    # **Re-read after the writes**, because what is asserted is what a screen
    # would draw and not what this function believes it wrote.
    async with session_factory() as session:
        rooms = await every_room_in_the_database(session, settings=settings, now=now)
        lines = [
            _refuse_a_database_with_no_rooms_in_it(rooms),
            _refuse_a_court_that_stopped_growing(rooms),
            _refuse_a_pair_with_no_room_of_their_own(rooms),
            _refuse_a_room_too_short_to_page(rooms),
            _refuse_a_room_that_outlived_its_game(swept, rooms, now=now),
        ]
    return SeededRooms(
        delivered=delivered, rooms=tuple(lines), said=said, swept=swept
    )


async def _destroy_what_has_ended(
    session_factory: async_sessionmaker[AsyncSession], *, now: Instant
) -> SweptRooms:
    """Run the sweep in process, on the run's own clock.

    **The same barrier the delivery above is**, for the same reason: the
    assertions read the real path, and the real path has a loop in front of it.
    A laptop that never ran the sweep would hold every played evening's room for
    ever and read as a platform where nothing ever ends.

    **The clock is the run's, not the wall's.** Everything the played history
    wrote is dated against this instant, so a sweep reading a second clock would
    be answering about a slightly different day than the fixture it is sweeping.
    """

    async with session_factory() as session:
        return await build_destroy_ended_conversations(
            session, clock=FixedClock(at=now)
        ).execute()


async def every_room_in_the_database(
    session: AsyncSession, *, settings: Settings, now: Instant
) -> tuple[ConversationRow, ...]:
    """Every room, read as somebody who is in it. **Never off the table.**

    There is no *all the rooms* read and there should not be — membership is the
    gate on every route this context has — so the fixture reads as each seeded
    player in turn and keeps one copy of each room it is shown. That is more
    reads than a query would be, and it is the right cost: what the claims below
    assert is then what a **screen** draws rather than what a table holds.

    **The protagonist is on the list and is not expected to be in a room.** The
    relationship layer seats her on a court she has not answered and organises one
    nobody has answered, so a room she is a member of is a state that layer does
    not currently reach — and a claim written against her alone would fail here
    for somebody else's reason.
    """

    reader = _read_conversations(session, settings=settings, now=now)
    found: dict[UUID, ConversationRow] = {}
    for email in _THE_READERS:
        player_id = await _player_if_present(session, email=email)
        if player_id is None:
            continue
        _, rooms = await reader.execute(ReadConversationsCommand(reader_id=player_id))
        for room in rooms:
            found.setdefault(room.conversation_id, room)
    # Sorted, because a mapping's iteration order is the order the claims
    # traverse in and a fixture's answer may not depend on it.
    return tuple(found[key] for key in sorted(found))


async def read_the_entries(
    session: AsyncSession,
    *,
    room: ConversationRow,
    settings: Settings,
    now: Instant,
) -> tuple[Entry, ...]:
    """One room's whole stream, read as somebody who is in it, **by paging back**.

    **The newest page and then the page before it**, which is exactly what a
    client does: the room opens at the newest entry and walks backward as somebody
    scrolls (``docs/adr/0147``). A caller that read only the first page would be
    asking *what does this room open on* — and the one room this fixture fills past
    a page holds fifty messages above the lines that were written before them, so
    that question and *what is in this room* have different answers.

    The cursor is the sequence and it is gapless, so ``seq`` 1 is the beginning and
    the walk ends when a page comes back empty. There is no ``has_more`` to read
    and deliberately none.

    Here rather than in ``app/seeds/loop.py``, beside the walk it belongs to: the
    reader has to be a member — membership is the gate on every route this context
    has — and *which member* is a question this module already answers for the
    list read.
    """

    reader = room.members[0].player_id
    conversations = build_conversation_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    entries = ReadEntries(
        rooms=build_a_room_of_yours(
            conversations=conversations,
            membership=build_membership(session),
            clock=FixedClock(at=now),
        )
    )
    walked: list[Entry] = []
    cursor: int | None = None
    while True:
        page = await entries.execute(
            ReadEntriesCommand(
                conversation_id=room.conversation_id,
                reader_id=reader,
                before_seq=cursor,
                limit=PAGE_LIMIT_DEFAULT,
            )
        )
        if not page:
            return tuple(walked)
        walked = [*page, *walked]
        cursor = page[0].seq



# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


async def _say_a_page_and_a_bit(
    session: AsyncSession,
    *,
    settings: Settings,
    now: Instant,
    room: ConversationRow,
) -> int:
    """Fill one room past a page, alternating between the two members it has.

    Alternating rather than one long monologue, because the bubble a screen draws
    is keyed on *is this mine*, and a room where every entry is the reader's own
    would draw one side of the conversation.
    """

    send = _send_message(session, settings=settings, now=now)
    authors = [member.player_id for member in room.members]
    if len(authors) < 2:
        raise SeedRoomMissing(
            f"the room to fill has {len(authors)} member(s); a conversation needs "
            f"two people to alternate between, and this one cannot draw the "
            f"*not mine* bubble at all."
        )

    for position in range(1, A_PAGE_AND_A_BIT + 1):
        await send.execute(
            SendMessageCommand(
                conversation_id=room.conversation_id,
                author_id=authors[position % len(authors)],
                # Derived from the room and the position, so a second run says
                # the same things at the same sequence numbers and writes
                # nothing.
                client_message_id=uuid5(
                    SEEDED_MESSAGES, f"{room.conversation_id}:{position}"
                ),
                text=THE_SMALL_TALK[position % len(THE_SMALL_TALK)],
            )
        )
    return A_PAGE_AND_A_BIT


# ---------------------------------------------------------------------------
# The claims, each read off the real path
# ---------------------------------------------------------------------------


def _a_room_still_arranging(rooms: Sequence[ConversationRow]) -> ConversationRow:
    """A room whose line-up has not completed: **no game, so no *Details* door.**

    Found by shape rather than named, because which court ``pairs.py`` leaves
    half-built is that layer's business — a fixture that named the challenge
    would go looking for a uuid the day the relationship moved.
    """

    for room in rooms:
        if room.game_id is None and len(room.members) >= 2:
            return room
    raise SeedRoomMissing(
        "no room whose line-up is still filling. A room opens on the first "
        "acceptance and grows with each one after it, so this is a doubles court "
        "with one seat answered and one still open — and without it the Chats "
        "tab cannot draw a room that has no *Details* door to offer."
    )


def _refuse_a_database_with_no_rooms_in_it(
    rooms: Sequence[ConversationRow],
) -> str:
    """*Somebody, somewhere, is in a room.*"""

    if not rooms:
        raise SeedRoomMissing(
            "no conversation in this database. A room opens on the first "
            "acceptance, so this means either nothing was ever accepted or the "
            "outbox was not delivered — and the Chats tab's second section is "
            "empty on every screen."
        )
    return f"rooms · {len(rooms)} conversation(s), read as the people in them"


def _refuse_a_court_that_stopped_growing(
    rooms: Sequence[ConversationRow],
) -> str:
    """*One room has no game and fewer members than its court will hold.*"""

    room = _a_room_still_arranging(rooms)
    return (
        f"growing · {len(room.members)} member(s), no game — the room draws the "
        f"members it has rather than the court it will be"
    )


def _refuse_a_room_too_short_to_page(rooms: Sequence[ConversationRow]) -> str:
    """*One room holds more than a page.*

    Read off the last entry's ``seq`` rather than by counting, because that is
    what the sequence is for: it is gapless, so the newest entry's number **is**
    how many entries the room holds.
    """

    deepest = max(
        (room.last_entry.seq for room in rooms if room.last_entry is not None),
        default=0,
    )
    if deepest <= PAGE_LIMIT_DEFAULT:
        raise SeedRoomMissing(
            f"the deepest room holds {deepest} entries and a page is "
            f"{PAGE_LIMIT_DEFAULT}. Nothing here can be paged backward through, "
            "so the one screen state that exercises the cursor is unreachable."
        )
    return (
        f"deepest · {deepest} entries, against a page of {PAGE_LIMIT_DEFAULT} — "
        f"the room pages backward"
    )


def _refuse_a_pair_with_no_room_of_their_own(
    rooms: Sequence[ConversationRow],
) -> str:
    """*One two-member room's line-up completed into a game.*

    It is the shape a Chats row draws with a **Details** door on it, and it comes
    from the games ``plans.py`` arranges and nobody plays: a singles court is two
    people, its line-up completed, and the game is still inside its entry window.

    **Not from the played history, and that is the destruction showing.** Every
    game that layer records was played at least ``PLAYED_AT_LEAST_DAYS_AGO`` ago
    and ``CONVERSATION_GRACE`` is forty-eight hours, so each of those rooms is
    over before this run reads it (``docs/adr/0153``). A room with a *Details*
    door therefore has to be a game somebody has **not** said they played.
    """

    for room in rooms:
        if len(room.members) == 2 and room.game_id is not None:
            return (
                f"details · a two-member room whose game is still to be played, "
                f"last entry {_code_of(room)}"
            )
    raise SeedRoomMissing(
        "no two-member room whose line-up completed into a game. The four games "
        "`plans.py` arranges are singles courts inside their entry window, and "
        "each one's first acceptance opens a room — so this means the outbox was "
        "not delivered, no game was arranged, or the sweep destroyed a room it "
        "should not have. Without it the Chats tab draws no *Details* door at "
        "all."
    )


def _refuse_a_room_that_outlived_its_game(
    swept: SweptRooms, rooms: Sequence[ConversationRow], *, now: Instant
) -> str:
    """*No room that was told* we played *more than a grace ago is still standing.*

    **The claim is the lifetime, not the absence.** It used to be *no room
    anywhere carries* ``GAME_PLAYED``, which was true only because every game in
    this fixture had been played days ago — a property of the population rather
    than of the rule, and it went red the day ``app/seeds/loop.py`` seeded a game
    played **this** evening, which is exactly the room the seventh system-line code
    needs. What survives is the rule itself: a room outlives *we played* by
    ``CONVERSATION_GRACE`` and not a moment longer (``docs/adr/0153``), so what is
    refused is a room still carrying that entry from **before** the grace.

    It is read off ``last_entry``, which is enough: *we played* is the last thing
    that ever happens in a room — the result argument is ``games``' own
    conversation and draws no line here — so a room still carrying that entry is a
    room whose episode ended when the entry did.

    **It is idempotent because it is a claim about state.** A second ``make seed``
    has nothing left to destroy — the first run already did it, and the outbox does
    not redeliver — so a fixture that asserted *this run destroyed something* would
    pass once and fail for ever after.

    **What stops it being vacuous is the claim beside it.** On its own this would
    pass a database in which the played history never opened a room at all — so it
    is paired with :func:`_refuse_a_pair_with_no_room_of_their_own`, which demands
    a **standing** two-member room whose line-up completed. **A live room is
    required beside it** for the same reason: an ended room is only legible next to
    one that is not, and a Chats tab that is empty on every screen proves nothing
    about when a room ends.

    **There is deliberately no before-and-after count.** The list read already
    drops a room past its end, so the same read on either side of the sweep returns
    the same rows — which is not a bug to work around but the rule itself: the sweep
    changes the table and never the answer (``docs/adr/0153`` §5). What the run
    destroyed is on the report because it is the only place that difference is
    visible at all.
    """

    outlived = [
        room
        for room in rooms
        if _code_of(room) == THE_PLAYED_CODE
        and isinstance(room.last_entry, SystemLine)
        and now - room.last_entry.occurred_at > CONVERSATION_GRACE
    ]
    if outlived:
        raise SeedRoomMissing(
            f"{len(outlived)} room(s) still stand whose last entry is "
            f"{THE_PLAYED_CODE} from more than {CONVERSATION_GRACE} ago. A room "
            f"outlives *we played* by that grace and no longer, so each of these "
            f"is past its end — either the sweep did not run or the lifetime no "
            f"longer reaches it."
        )
    if not rooms:
        raise SeedRoomMissing(
            f"no room stands at all; the sweep walked {swept.walked} and "
            f"destroyed {swept.destroyed}. An ended room is only legible beside "
            f"a live one, and a Chats tab that is empty on every screen proves "
            f"nothing about when a room ends."
        )
    told = len([room for room in rooms if _code_of(room) == THE_PLAYED_CODE])
    return (
        f"ended · {swept.destroyed} of {swept.walked} room(s) destroyed this "
        f"run, {len(rooms)} standing, and the {told} still carrying "
        f"{THE_PLAYED_CODE} were all told so inside {CONVERSATION_GRACE} — the "
        f"played evenings are gone and this evening's is not"
    )


def _code_of(room: ConversationRow) -> str:
    """What the newest entry is, for the report. **Two shapes, named apart.**

    A system line is its code; a message is not named, because what somebody
    typed is not a fixture's to print.
    """

    entry = room.last_entry
    if isinstance(entry, SystemLine):
        return entry.code.value
    return "a message" if entry is not None else "nothing"


# ---------------------------------------------------------------------------
# Wiring, from the composition root and nowhere else
# ---------------------------------------------------------------------------


def _read_conversations(
    session: AsyncSession, *, settings: Settings, now: Instant
) -> ReadConversations:
    conversations = build_conversation_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    # One court for both questions it is asked, exactly as a request has one.
    arranging = build_arranging_court(session)
    return ReadConversations(
        directory=build_conversation_directory(
            session=session, conversations=conversations
        ),
        arranging=arranging,
        membership=build_membership(session, arranging=arranging),
        faces=build_member_faces(session, settings=settings),
        clock=FixedClock(at=now),
    )


def _send_message(
    session: AsyncSession, *, settings: Settings, now: Instant
) -> SendMessage:
    conversations = build_conversation_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    return SendMessage(
        rooms=build_a_room_of_yours(
            conversations=conversations,
            membership=build_membership(session),
            clock=FixedClock(at=now),
        ),
        conversations=conversations,
        holds=build_conversation_hold_query(session),
        # Same reason as the drain above: nobody is following a laptop.
        nudges=build_nobody_is_following(),
        uow=build_unit_of_work(session),
        clock=FixedClock(at=now),
    )


async def _player_if_present(session: AsyncSession, *, email: str) -> UUID | None:
    """The id the write path minted for this address, or ``None``.

    ``None`` rather than a refusal, because the caller is looking **for** players
    who are in a room and one that is missing is not a failure on its own — the
    failure is finding no room at all, and that is the caller's own complaint to
    make, with the reason in it.
    """

    found = await build_user_repository(session).get_by_email(email)
    return None if found is None else found.id
