# conversations — a booked game's room

> The design record for `src/features/conversations/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**`{name}` is filled from the people the response names, and the roster is not that list**
([#409](https://github.com/Raketa02/Raketa/issues/409),
[ADR-0148](../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)'s
2026-09-11 amendment). Membership is derived live — the accepted seats, then the game's frozen
line-up — and a _no_ is not an accepted seat, so the actor of a `SEAT_LEFT` line was never a member
and a lookup over the roster drew **`? said no — that seat is open again`** in a doubles room whose
third player declined. The wire now carries **`people`** on the room, the row and every page — the
members and every actor and author the entries name, one face read — and every `{name}` and the
bubble's author label read it through `personNamed`. **A person is the shape and a member is that
shape under a narrower claim**: the generated client gets two structurally equal schemas, and
`domain/membership.ts` is the one place that decides a member _is_ a person, so one mapper reads
both. `people` rides **beside** the entries rather than on the header, because it grows the way
they do — the room's first read names the members and whoever its page is about, and each page
backward names its own authors and actors, which that first read could not have known — so a
page's `people` is **merged by id** into what is held (`mergedPeople`, newest page first) and never
put in its place, since replacing would forget the members the moment the first older page landed.
Three things deliberately still read `members`: the faces the header and the row draw, because a
declined player is a name a line needs and never a face the room draws; `namesItsAuthors`, which is
a fact about the room's size; and `typingLine`, because a typist is gated on membership and is one
(ADR-0156) — the one list a departed player is on is the one list that cannot be typing. The `?`
keeps its single meaning: `nickname: null` is the platform no longer able to name the account, and
nothing else draws it.

**The room is a header, a stream and a composer**
([#364](https://github.com/Raketa02/Raketa/issues/364)). The header is 10.3's with a new **lead**
slot — a room is named by the people in it, so the faces sit beside the handles rather than in the
page under them, where the stream would scroll them away. **Its title is the handles' stems and its
spoken name is the handles whole, and the line under it is the sport and the game's state in lower
case** ([#401](https://github.com/Raketa02/Raketa/issues/401),
[ADR-0157](../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)):
`handleStem` is a prefix of the handle the person typed — ADR-0107 forbids _inventing_ a familiar
form and a stem invents nothing, which is `the-words.md` §15's and `handleStem`'s own argument — and
the state is the game's own word in lower case — the old loop's Now card's rung then, a booked
game's status now (below) — and never the twenty-state standing ADR-0148 §6 refused. **With nobody else to name, the title is
_Waiting for others to join_** ([#429](https://github.com/Raketa02/Raketa/issues/429) E4): the
organiser alone again — somebody joined and left while the rest were still deciding — is a real
room with one member, and `headerTitle` of no handles drew a blank at `h1` over the sport. The
rule lives in `headerTitle` rather than at the call site so no arrangement of props draws that gap,
and `conversationHeaderLabel` speaks the same sentence in the handles' place, since there is no
handle to keep whole. The two lines sit in 10.3's new **sub-line**
slot rather than the eyebrow, title above and a quieter line below, and the header's budget is now
counted at `h1` rather than the rows' `cardTitle`, which had let it promise a one-line title that
wrapped. **The stream is two components and never one with a branch** —
ADR-0146 refused that shape on the wire and #338 §7 refuses it here for the same reason — sharing
`conversationPresentation.ts`. **A bubble draws its author's whole handle only where the room has more than two
members**, and that is a fact about the _room_, so it is a prop from the screen; the **spoken**
name says the author every time, because in a pair what disambiguates is the side and the ground
and _never colour alone_ refuses to let a listener depend on those. **There is no per-message
timestamp** — a room lives days, so the one time-shaped fact worth drawing is which day — and the
**day separator is computed on the platform zone**, since a device zone would put two people in
one room on two different days. The stream **opens at its newest entry** (an inverted list, which
is what makes that free) and **pages backward by cursor**: no offset and no `has_more`, because a
gapless sequence makes `seq` 1 the beginning, and **no reader infers loss from a gap**. §24.1's
complement is what makes the backlog navigable — _one accessibility element per action, and one
per entry in an ordered stream_ — because a history with no actions in it would otherwise merge
into one element.

**The send is the one optimistic act in the app, and `client_message_id` is why.** Every
other act that reaches another person is pending never optimistic because it derives a standing
several people read; a message cannot be _wrong_, so the bubble is on screen before the round trip
and **the sender's own message never waits for a nudge**. It **pauses offline and resumes** — the
app default, because a message carries no deadline anybody chose — and the same key goes out on the resumed attempt, so a repeat answers `200` with
the same `seq` and one send can never become two messages. The optimistic bubble is read out of
the **mutation cache** rather than written into the query cache: a paused send outlives the screen
that made it, and client state written into the copy every other reader treats as the server's is
the second store this app does not have. A refusal **puts the words back in the box**, because the
retry is the control that failed.

**The room stays current on its own, and the whole live layer is a nudge, a fold and a sentence**
([#365](https://github.com/Raketa02/Raketa/issues/365),
[ADR-0147](../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)).
`shared/lib/platform/liveStream.ts` is the app's **third port** and the only importer of
`react-native-sse` — beside the two native ones, on the second of their two arguments: a transport
cannot be driven from a test either, so its fake sits with theirs and every state is drivable. **It
owns the route as well as the transport**, because a port taking an arbitrary path would be a
generic SSE client and the one thing that buys is the second stream ADR-0147's _never build_ list
forbids. **What crosses upward is the room and never the number**: the frame's `last_seq` is read to
know a frame is a nudge and dropped there, so nothing above can page from it — _fetch from your own
high-water mark_ stops being a rule anybody keeps and becomes one this app cannot express. The nudge
**invalidates** and the Query cache stays the single copy; the rooms list is deliberately **not**
invalidated with it, because a nudge is not an act the player took. **`liveState` is `domain/`** — a three-way _live · not live · held_ — and the placement is
load-bearing: _only in the foreground, and only after a connect attempt has failed_ is exactly the
pair of conditions a component drops quietly, and `closed` is a status of its own so a stream shut on
the way to the background is never news. **Not live is one amber line above the composer and never a
disabled one**: a send is an ordinary `POST` over a channel that is unidirectional by construction,
the fact has two parts, and only a sentence carries two. Players meet it **routinely and briefly**,
because the stream closes at the token's `exp` — so every attempt mints a fresh credential and a
`401` goes through the app's own single-flight rotation, once per channel, which is the whole of why
`shared/lib/http` grew a `streamAttempt` rather than the port growing a second `Authorization`
header. **Held is the other way round**: the composer greys out behind **one** pre-emptive note, reading is never blocked, and a hold never removes the
room. It is **unreachable in this build and that is written down where the next person will find
it** — nothing on this platform can open a case, so the only producer is the `account_held` refusal
and the pre-emptive half is bought with one tap; `domain/liveState.ts` says so, and component tests
are what drive the arm. 6.2 and 6.13 each gained a `disabled` state for it, under one condition:
**only where a note above has already said why.**

**The stream carries a second frame, and the port subscribes per name**
([#404](https://github.com/Raketa02/Raketa/issues/404),
[ADR-0156](../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
`event: nudge` and `event: typing` are the two names the route writes, and `liveStream.ts` listens
for exactly those — never `message` — so a frame under a name this build has not heard of is dropped
by the transport rather than by a branch; a port that listened to `message` hears **nothing** from
the wire as it now is, which is the break #404 had to fix before it could draw anything. **A nudge
crosses as the room and a typing frame crosses whole**, because presence has no read path to defer
to. **Typing is not query cache state**: `useLiveConversation` holds the last frame's roster as the
room's own state — replaced whole, an empty list being the only clear — and `domain/typing.ts` folds
it against the channel and the reader. **The client keeps no clock**, and that is the one place this
build reads the ticket against the wire: a frame arrives when the answer changes and never on a
tick, so a timer from the last frame would clear the indicator on exactly the person it exists for.
The client's own net is the channel — a roster is dropped, not hidden, the moment the stream is not
live, and never remembered across a reconnect, because the server re-announces on its first check.
The server filters the reader out and `typists` filters again. `TypingBubble` is a **third
component and never a branch inside `Bubble`** — three pulsing dots in the other side's bubble at
the newest end of the inverted list, one polite element named by §22.5's sentence, filled from
membership; it is **the one thing this app animates although §1.5 says nothing has to**, because
three still dots are a message that says `...`, and it is drawn still under reduced motion with the
name kept (Part 16). The heartbeat is `useTypingHeartbeat`: a beat per keystroke off the composer's
own `onChangeText`, throttled to the route's cadence by `beatIsDue`, with **nothing scheduled** — a
player who stops typing stops beating and the server's expiry does the rest — aborted with the room
so no request outlives its screen, **silent** when it fails, and closed with the composer under a
hold. It is not a `useMutation`, because a paused heartbeat resuming on reconnect would say _typing_
about a person who left a minute ago.

**A room that ends while it is on screen stays on screen, closed, and says so**
([#429](https://github.com/Raketa02/Raketa/issues/429)). A room's end is answered by the nudge's
re-read with `conversation_not_found`. The screen answered that by leaving — a player reading a
room was taken off it a moment later with the room gone from under them, which read as the app
acting on their behalf. Now `roomIsGone` on a read **with pages held** keeps the room: the stream as
it was, the header, and in the composer's place §22.5's fourth sentence, drawn as a plain `Note` and
announced. Nothing writes — no composer, no not-live line, no paging back — and a send that races
the nudge and is told the room is gone re-asks the read rather than deciding anything itself, so one
place closes the room. A room **nothing was ever read from** still leaves — a stale door into a
room that is not there.

**A booked game's room is the same screen, reached from its details**
([#556](https://github.com/Raketa02/Raketa/issues/556); the Games & Fill in screens A4.4, the
mechanics §14.3). `ConversationScreen` takes `booked: { state }` and draws the conversation alone —
no plan card, no plan quick chips, no _Details_ door (`ConversationHeader`'s `onOpenGame` is
optional for it) — with the header's second line the booking's word, because the Classic fold names
a booked Game by a rung it never stands on. The room is found by the join keyed by the **game**:
`useGameRoom(gameId)` (with `listed`, `paused` and `error`, so the screen can tell _not yet_,
_offline_ and _refused_ from _none_) and
`useGameRooms()` for Home's cards — the join `GET /bookings/{id}` documents, since a booked game's
room is filed under its booking and is about its game from its first moment. No read carries a
conversation id.

**Every room is a booked game's now, and the room lost what only the old loop's needed**
([#576](https://github.com/Raketa02/Raketa/issues/576), PRD [#569](https://github.com/Raketa02/Raketa/issues/569)).
The Chats tab's `CONVERSATIONS` section and its rows, the swipe that revealed _Leave the game_ on
them, the return re-read they took, the plan card pinned under the header, the quick chips, the
_Details_ door and the route it opened, the challenge's chat doors (`useChatDoor`,
`useAwaitedChatDoor`, `useChatDoors`) and the one write another feature made to the list
(`dropRoomOfChallenge`) went with that loop. So `ConversationScreen` takes the booking's word as
`state` rather than an optional `booked`, `ConversationHeader` takes it as `gameState` and draws no
door, `Composer` is the field and _Send_, the nudge re-reads the stream and the games list and
nothing else, and the mapper no longer maps `challenge_id` — no screen reads it, and the wire names
it `booking_id` from #575 (#577 follows). **A room that ends says only that it ended**: it named who
had left, or that nobody else was coming, in the old loop's rooms, which could end before they had a
game; a booked room always has its game, so `domain/roomOver.ts` went and `ROOM_OVER_LINE` is the
one sentence. The plan's system lines (_set the place_, _locked the plan_, _You two are a side_)
stay in the table: a stored line still folds, and a code with no words would not compile — the
backend keeps the codes for the same reason. `roomLiveness.test.tsx` and
`conversationScreen.test.tsx` walk the booked chat now, entered from the details' _Open the chat_.

**A booked game's room is found by its booking**
([#577](https://github.com/Raketa02/Raketa/issues/577), PRD
[#569](https://github.com/Raketa02/Raketa/issues/569)). #575 renamed the room's `challenge_id` to
`booking_id` — the same value, the booking whose game opened the room — and a room is opened only by
a booked game, so every room has one. The join moved onto it: `Conversation.bookingId` replaces
`gameId`, and `useGameRoom(gameId)` and `useGameRooms()` are `useBookingRoom(bookingId)` and
`useBookingRooms()`, keyed by the id the details' and the chat's route already carries. So neither
the chat's join nor a Home card's bubble reads the booking's `game_id` any more. **`game_id` is
mapped nowhere now**: it was the join and nothing else read it. **Nothing in the app calls a booking
a challenge**: `games`' `Game` lost `challengeId` too, which had no reader — `GameSchema` still
names the field `challenge_id` on the wire until the backend's own removal renames or drops it, and
only the wire fixtures spell it. `homeAndBookedGame.test.tsx` proves the join by rooms that disagree
with their booking about the game: one filed under the booking and naming no game opens from Home's
card and the details, and one filed under another booking but naming this game draws no bubble and
no _Chat_.

**A booked game's room has a second door** ([#619](https://github.com/Raketa02/Raketa/issues/619);
the mechanics Q100). The bubble on the game's Home card opens the same route as the details'
_Open the chat_, pushed straight over Home, so Back from the room is whichever screen opened it. The
screen is unchanged — it never had a way into the details and still has none; the door is
`proposals`' (`ChatDoor`), named by `OPEN_THE_CHAT` like the details' one.
