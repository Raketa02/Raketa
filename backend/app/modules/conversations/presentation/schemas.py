"""The conversation wire shapes — **two shapes in one stream, and no sentence.**

Six rules decide everything below.

**A system line is a code and its values, and the client renders it**
(``docs/adr/0022``, ``docs/adr/0146`` §4). Nothing here carries display text. A
rendered sentence on the wire would be a sentence frozen into history the moment
it was stored, so rewording a line could never reword the backlog.

**``values`` never repeats what the response already resolves.** The line
carries ``actor_id``; the client fills ``{name}`` from the ``people`` beside it,
which the read resolved at that moment. A handle correction therefore reaches the
whole backlog for free.

**And ``people`` is everybody the response names, not only the roster**
([#408](https://github.com/Raketa02/Raketa/issues/408)). Membership is derived
live — the accepted seats, then the game's line-up — and a *no* is not an
accepted seat, so the person a ``SEAT_LEFT`` line is about was never a member
and a client that filled ``{name}`` from ``members`` alone drew *? said no — that
seat is open again*. ``members`` is still the roster and still the gate;
``people`` is the roster **and** every author and actor the entries name,
resolved once. On a page it is the page's own authors and actors and nothing
about the roster.

**A message has no id of its own.** ``(conversation_id, seq)`` already identifies
it, and a UUID beside a unique key is a second identity for one row.

**And there is no ``has_more`` anywhere, and no ``last_seq`` field.** The sequence
is gapless, so ``seq`` 1 *is* the beginning of the conversation; and the newest
entry's ``seq`` is the high-water mark, on the detail and on the row alike
(``docs/adr/0148`` §3, §10).

**Every nullable field here is ``null`` and never omitted**, except a
photograph's two: a room whose line-up has not completed has no game, a room
where nothing has happened has no last entry, and a player ``users`` can no
longer name has no handle — three measured nothings. ``photo_id`` and
``photo_url`` are **omitted**, exactly together, because a player with no
photograph is not an absence to report: the client draws a generated court
poster, which needs nothing from the wire.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Final, Literal, Union
from uuid import UUID

from fastapi.sse import ServerSentEvent
from pydantic import BaseModel, Field

from app.kernel import Sport

OMITTED: Any = None


class ConversationPersonSchema(BaseModel):
    """One person this response names — **a handle and a face, and nothing else.**

    No Level, no band, no area, no score — those are a *card*'s, and a card is
    what a searcher reads to decide about a game that might happen. Everybody
    here was on this court or spoke in this room.

    **The shape `people` is a list of, and the shape a member has.** A member is
    a person who is on the court *right now*; the person a `SEAT_LEFT` line is
    about is not, and is still somebody the page has to name. One shape for
    both, so a client resolves every `actor_id` and `author_id` the same way.
    """

    player_id: UUID = Field(
        ...,
        description=(
            "Who they are, and what a line's `actor_id` and a message's "
            "`author_id` match"
        ),
    )
    nickname: str | None = Field(
        ...,
        description=(
            "The whole handle, and **`null` for an account `users` can no longer "
            "name**. The person keeps their place either way: a member dropped "
            "would draw a three-person doubles court, and an actor dropped "
            "would leave a line naming nobody. Draw the unknown player's mark "
            "for `null` and nothing else. Nothing may derive a familiar form "
            "from it."
        ),
    )
    photo_id: UUID = Field(
        OMITTED,
        description=(
            "Their current photograph. Omitted when they have none, and omitted "
            "together with `photo_url` — the two travel as a pair or not at all."
        ),
    )
    photo_url: str = Field(
        OMITTED,
        description=(
            "A short-lived signed link to that photograph, minted for **this "
            "response**. It expires within minutes and is not a stored value."
        ),
    )


class ConversationMemberSchema(ConversationPersonSchema):
    """One person who has agreed to be on this court right now.

    **Derived from whichever record is arranging, never stored**
    (``docs/adr/0146`` §7), and it **grows one acceptance at a time**: a doubles
    room whose line-up is still filling draws the members it has, because a row
    with four faces for a two-member room would be drawing the court rather than
    the room.

    **The same four fields as a person, and a narrower claim.** Being on the
    list is the fact; the face is `ConversationPersonSchema`'s. A member is
    always among the response's `people` too, resolved in the same read, so the
    two lists cannot disagree about a current member.
    """


class MessageSchema(BaseModel):
    """What a player typed. **Content, crossing as-is.**"""

    type: Literal["message"] = Field(
        "message",
        description=(
            "The discriminator. Two genuinely different shapes ride one ordered "
            "stream; this is not a `kind` on one shape (`docs/adr/0148` §4)."
        ),
    )
    seq: int = Field(
        ...,
        description=(
            "This entry's place in the conversation. **Gapless and starting at "
            "1**, so `seq` 1 is the beginning of the room — which is why there "
            "is no `has_more`. Ordering, paging, de-duplication and reconnect "
            "all key on it, and **no reader may infer loss from a gap**: the "
            "promise is the server's and nothing may depend on it."
        ),
    )
    author_id: UUID = Field(
        ...,
        description=(
            "Who typed it — a member, since only a member may send. **Name "
            "them from the `people` on the response that carried this page**, "
            "the one list every face on it is in, so a message and a line are "
            "named the same way."
        ),
    )
    sent_at: datetime = Field(..., description="When it landed")
    text: str = Field(..., description="Their own words, unrendered and unchanged")
    client_message_id: UUID = Field(
        ...,
        description=(
            "The id the sending client generated, echoed back. It does **two "
            "jobs**: the idempotency key for a resumed send, and the key an "
            "optimistic bubble is replaced on."
        ),
    )


class SystemLineSchema(BaseModel):
    """What happened, as a code and its values. **Never a sentence.**"""

    type: Literal["system_line"] = Field(
        "system_line", description="The discriminator. See `MessageSchema.type`."
    )
    seq: int = Field(..., description="This entry's place. See `MessageSchema.seq`.")
    code: str = Field(
        ...,
        description=(
            "What happened, as a machine code the client renders a sentence "
            "from. Nine: **`SEAT_ACCEPTED`**, **`SEATS_INVITED`**, "
            "**`SEAT_LEFT`**, **`GAME_PLAYED`**, the Plan's "
            "**`PLACE_RECORDED`**, **`DAY_RECORDED`**, **`HOUR_RECORDED`** and "
            "**`PLAN_LOCKED`**, and **`SIDE_FORMED`**.\n\n"
            "**`SIDE_FORMED` is the one line a room is born with, and only a "
            "doubles room** (ADR-0169 §8). Two yeses that met in a doubles "
            "sport seat both people on one side with a whole side still to "
            "fill, and this says so at `seq` 1: *You two are a side. Fill the "
            "seats to find your opponents.* A singles mutual's room carries no "
            "such line. It names no actor and carries no values.\n\n"
            "**A seat leaving is one code with the answer as a value**, because "
            "*that seat is open again* is the same news each way — and a lapse "
            "is still not a decline, which is what `values.departure` keeps "
            "apart. Somebody **leaving a game they had agreed to** is the third "
            "way, since ADR-0162, and the one whose actor was a member until "
            "this very line.\n\n"
            "**A slot set and a slot moved are one code told twice**, which is "
            "the opposite rule for the opposite case: three slots are three "
            "facts, so they are three codes, and there is no value telling a "
            "first fill from a change because they are the same fact.\n\n"
            "**`PLAN_LOCKED` is the Plan's fourth and it carries no values at "
            "all.** The three slots are the value and the room already holds a "
            "line for each. It is an act rather than a slot — a complete plan is "
            "one everybody *could* agree, and this says somebody did — and there "
            "is no unlocked code, because a slot moved afterwards keeps the lock "
            "and writes its own line.\n\n"
            "**There is no *Game on* line.** Everybody having accepted is an "
            "arrangement of the seats, so a line announcing it would be a second "
            "place for a folded standing to be true. What appears instead is the "
            "plan card and membership stopping — drawn, not announced."
        ),
    )
    occurred_at: datetime = Field(..., description="When it happened")
    actor_id: UUID | None = Field(
        ...,
        description=(
            "Who did it, or `null`. **Render `{name}` from the `people` on the "
            "response that carried this line** — the handle is never repeated "
            "here, so a corrected one fixes the whole backlog. Not from "
            "`members` alone: the actor of a `SEAT_LEFT` line is by definition "
            "no longer one, and `people` is where the read put their face. "
            "`null` on `SIDE_FORMED`, which is about both people on the side "
            "and names neither."
        ),
    )
    values: dict[str, str] = Field(
        ...,
        description=(
            "What the sentence needs beyond a handle, and **nothing membership "
            "already says**. `SEATS_INVITED` carries `count`; `SEAT_LEFT` "
            "carries `departure`, one of `DECLINED`, `LAPSED` or `LEFT`; the "
            "three plan "
            "codes each carry `value` — the place as it was typed, the day as "
            "`YYYY-MM-DD`, the hour as `HH:MM`. `SEAT_ACCEPTED`, "
            "`GAME_PLAYED` and `SIDE_FORMED` carry nothing."
        ),
    )


#: The stream's element: two shapes, discriminated on ``type``.
EntrySchema = Annotated[
    Union[MessageSchema, SystemLineSchema], Field(discriminator="type")
]


class ConversationRowSchema(BaseModel):
    """One room, as a row in the Chats tab.

    **No state pill, and no standing anywhere on it** (``docs/adr/0148`` §6).
    Reading one would make the conversation ask `challenges` and `games` what
    they are, which it never does — and it does not need to, because **the last
    entry is what a pill would have said.**
    """

    conversation_id: UUID = Field(..., description="The room's own id")
    challenge_id: UUID = Field(
        ..., description="The challenge whose first acceptance opened it"
    )
    game_id: UUID | None = Field(
        ...,
        description=(
            "The game its line-up completed into, and **`null` until it does**. "
            "A room whose line-up is still filling has no game and no plan, so "
            "there is nothing for a *Details* door to open — draw no door rather "
            "than a dead one."
        ),
    )
    sport: Sport = Field(..., description="What they are arranging")
    members: list[ConversationMemberSchema] = Field(
        ..., description="Who has agreed to be on this court right now"
    )
    people: list[ConversationPersonSchema] = Field(
        ...,
        description=(
            "Everybody this row names, resolved once and ordered by id: the "
            "members, and whoever `last_entry` is about. **A superset of "
            "`members`** — fill `{name}` and the author label from here."
        ),
    )
    last_entry: EntrySchema | None = Field(
        ...,
        description=(
            "The newest thing in the room, rendered by the same two components "
            "the stream uses — never a preview string.\n\n"
            "**`null` in a room where nothing has happened yet**, which is a "
            "real state rather than an edge case: the opening writes no line, so "
            "a room whose first acceptance is its whole history has no entry at "
            "all."
        ),
    )


class ConversationListResponse(BaseModel):
    """Every room you are a member of, the ones that moved last first."""

    read_at: datetime = Field(
        ...,
        description=(
            "The instant this list was folded. It earns one because **its very "
            "membership is a fold**: a room is destroyed rather than delisted, "
            "so whether a row appears at all was decided against this instant."
        ),
    )
    conversations: list[ConversationRowSchema]


class ConversationResponse(BaseModel):
    """One room's header **and** its newest page, from one fold."""

    read_at: datetime = Field(
        ...,
        description=(
            "The instant the header and the page were folded — **one instant for "
            "both**, so members and entries can never disagree."
        ),
    )
    conversation_id: UUID
    challenge_id: UUID
    game_id: UUID | None = Field(
        ..., description="See `ConversationRowSchema.game_id`."
    )
    sport: Sport
    members: list[ConversationMemberSchema]
    people: list[ConversationPersonSchema] = Field(
        ...,
        description=(
            "Everybody this response names, resolved once against `read_at` and "
            "ordered by id: the members, and every author and actor in "
            "`entries`. **A superset of `members`**, so a current member is the "
            "same face in both. Fill every `{name}` and every author label from "
            "here, and merge each page's `people` into it as you page back."
        ),
    )
    entries: list[EntrySchema] = Field(
        ...,
        description=(
            "The newest page, **oldest first inside it**. Page backward from "
            "`entries[0].seq` through `GET /conversations/{id}/entries`; you have "
            "the beginning when you hold `seq` 1."
        ),
    )


class EntryPageResponse(BaseModel):
    """One page backward. **No header, and no instant** — but the page's own faces.

    `people` is not a header: it says nothing about the room and nothing about
    who is in it. It is the one thing the detail read could not have given a
    client for this page, because the people a page names are not the members.
    """

    entries: list[EntrySchema] = Field(
        ...,
        description=(
            "The page, **oldest first inside it**. Empty when `before_seq` was 1 "
            "— there is nothing before the beginning."
        ),
    )
    people: list[ConversationPersonSchema] = Field(
        ...,
        description=(
            "Every author and every actor on this page, resolved once and "
            "ordered by id. **Not the roster and not a superset of it** — a "
            "page names only what is on it, so merge these into the `people` "
            "you already hold rather than replacing them. Empty when `entries` "
            "is."
        ),
    )


class LiveNudgeSchema(BaseModel):
    """**The whole live contract: a nudge, and nothing else on the wire.**

    ``docs/adr/0147`` §3. One of these is written into
    ``GET /conversations/{id}/stream`` whenever the room moves, and one is
    written the moment the stream opens carrying the room's current `last_seq`.

    **It carries no content, ever.** Not a message, not a system line, not a plan
    slot. On receiving one, fetch from **your own** high-water mark through the
    ordinary read path — never from `last_seq`. That is what makes a dropped
    frame free: the next nudge repairs it, because your cursor is yours.

    **Which also means there is nothing here to render.** Whether the UI may draw
    something it did not read from the authenticated read path stops being a rule
    anybody keeps and becomes a thing this shape cannot express.

    **The declaration is generated and the emission is not, and that hole is
    named** (``docs/adr/0147`` §7). `make openapi` publishes this model into
    `components.schemas`, the client generates **this type** from it, and the
    drift and freshness checks cover the declaration. The *operation's* 200 comes
    out of `openapi-typescript` as `unknown`, because a stream body is an
    `itemSchema` that generator has no shape for — so the client's live port
    parses each frame as this type by name, which is still generated and still
    never hand-written. **What no check covers is the emission** — a stream body is
    not a response model, and nothing type-checks the route against its own
    annotation. The mitigation is structural rather than hoped for: the route
    declares this model as its stream item, so the framework validates and
    serialises every frame **through this model** before it reaches the wire. The
    hole is narrowed, not closed, and the residual risk is that of a shape three
    fields wide.
    """

    v: int = Field(
        ...,
        description=(
            "The envelope version, **carried from the first frame**. `1` today. "
            "A client parses the shape it shipped with until that build is gone "
            "from phones, so this is what a later shape is told apart by."
        ),
    )
    conversation_id: UUID = Field(
        ...,
        description=(
            "The room that moved. It is the room this stream is for — a stream "
            "carries one room and there is deliberately no second stream for the "
            "Chats list."
        ),
    )
    last_seq: int = Field(
        ...,
        description=(
            "How long the room is now. **News, not a cursor.** Fetch from your "
            "own high-water mark, never from this number: a client that paged "
            "from here would reintroduce exactly the hole the nudge exists to "
            "close. `0` is a room where nothing has landed yet, which a stream "
            "opened on a freshly-opened room genuinely reports."
        ),
    )


class LiveTypingSchema(BaseModel):
    """**Somebody is typing**, and it is the second frame on the wire.

    ``docs/adr/0156``. It arrives when the answer changes and not on a tick, so a
    room where nobody is typing produces nothing at all.

    **It carries no `last_seq` and moves no sequence.** A typing frame is not an
    entry: nothing was appended, nothing was locked, and the gapless allocator
    behind `seq` was never asked for a number. A client must not advance any
    cursor on one, and there is nothing here it could advance it to.

    **It carries no name.** Fill handles from the membership you are already
    holding, exactly as every system line does — which is why a corrected
    nickname fixes the indicator without a frame being re-sent.

    **An empty list is the clear**, and it is the only clear there is: nobody
    sends *stopped*, and the server reports whoever's heartbeat has not expired.
    A room whose last typist's app was killed reports nobody within seconds,
    through the same field and with nothing special about it.
    """

    v: int = Field(
        ...,
        description=(
            "The envelope version, **the same `1` a nudge carries and unbumped "
            "by this frame's arrival**. A named event an installed client does "
            "not listen for never reaches it, so nothing about the shape it "
            "parses has changed."
        ),
    )
    conversation_id: UUID = Field(
        ..., description="The room this is about — the room this stream is for"
    )
    player_ids: list[UUID] = Field(
        ...,
        description=(
            "Who is typing **right now**, never including you. A list because a "
            "group chat has more than one possible typist; draw one indicator "
            "either way. **Empty means nobody is**, which is how an indicator "
            "goes away."
        ),
    )


#: The SSE `event:` name a nudge rides under. **Subscribe per name.**
#:
#: The kind is on the event field rather than inside the JSON deliberately
#: (``docs/adr/0156`` §5): a client subscribes to the names it knows, so a frame
#: it has never heard of is ignored **by construction** rather than by a branch
#: somebody wrote — which is what makes a third frame, one day, additive for
#: every phone already in the world.
#:
#: ``Final`` so the constant carries its *literal* type: that is what lets
#: ``LiveFrame.event`` be a closed set and mypy check the two call sites that
#: build a frame. The names reach no generated artifact — the SSE item schema's
#: ``event`` is a bare string the framework writes — so this is the only place
#: they are checked at all.
NUDGE_EVENT: Final = "nudge"

#: The SSE `event:` name a typing frame rides under.
TYPING_EVENT: Final = "typing"


class LiveFrame(ServerSentEvent):
    """One frame on the stream: **a named event, and one of two payloads.**

    **This class is the declaration.** ``fastapi``'s own ``ServerSentEvent``
    carries ``data: Any``, which documents a stream as an opaque string and
    leaves the client with nothing to generate from; narrowing ``data`` here is
    what puts both envelopes into ``components.schemas`` and what makes ADR-0006
    true of a live event rather than aspirational (``app/api/streaming.py``
    reads this annotation).

    **It is also the check on the way out.** A frame is validated by pydantic
    when the route constructs one, so a payload that is neither envelope raises
    here rather than shipping. That is the same narrowing ``docs/adr/0147`` §7
    described and it moved one step: the framework skips its own stream-item
    validation for a ``ServerSentEvent``, because a route yielding these is
    taken to be choosing its own frames. What remains uncovered is unchanged —
    nothing proves *which* events this route emits, only that whatever it emits
    is one of these two shapes.
    """

    data: LiveNudgeSchema | LiveTypingSchema
    #: **A closed set, so the names are checked somewhere.** The base class types
    #: this ``str | None``, and the route's own docstring concedes that nothing
    #: proves which names are emitted; narrowing it here is the cheapest half of
    #: that hole to close — a third frame kind has to be added in one place
    #: rather than spelled correctly at a call site.
    event: Literal["nudge", "typing"]
    #: **Narrowed to nothing.** The base class offers `raw_data` as a way to put
    #: a pre-formatted string on the wire without going through `data`, which is
    #: exactly the door round the declaration above. Closing it here is what lets
    #: this class claim that every frame is one of two envelopes.
    raw_data: None = None


class SendMessageRequest(BaseModel):
    """One player's own words."""

    text: str = Field(
        ...,
        description=(
            "What to say. Leading and trailing whitespace is trimmed; empty "
            "after trimming is `message_is_empty`, and past the cap is "
            "`message_is_too_long`. **Neither is silently fixed** — a shortened "
            "message is one the sender believes they sent whole."
        ),
    )
    client_message_id: UUID = Field(
        ...,
        description=(
            "An id you generate for this send, **in the body rather than an "
            "`Idempotency-Key` header**, because it does two jobs: it makes a "
            "retry safe, and it is what you reconcile your optimistic bubble "
            "on.\n\n"
            "**Send the same one on a retry.** A repeat answers `200` with the "
            "same message and the same `seq`, and records nothing — so a send "
            "that paused offline and resumed can never become two messages."
        ),
    )
