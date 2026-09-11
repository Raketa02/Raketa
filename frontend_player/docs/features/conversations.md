# conversations — the Chats tab and the room

> The design record for `src/features/conversations/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The Chats tab is two sections, two contexts, two queries and two caches, and they are
deliberately not merged** ([#363](https://github.com/Raketa02/Raketa/issues/363)). `CHALLENGES` is
the **obligation** and `CONVERSATIONS` is the **rooms**, so a `LINE_UP_INCOMPLETE` challenge you
accepted draws a row in **both** — §13's own sentence asserts both facts in one breath, and drawing
it only under `CHALLENGES` would make it the waiting room #221 says it is not. That falls out of
the composition rather than being arranged anywhere: neither section knows the other exists.
**There is no pill and no standing on a conversation row** — ADR-0148 §6's _the last line is what a
pill would have said_ is a product argument as well as a wire one, and the only pill this client
could now draw would be joined off the games cache, which is the cross-feature read
[ADR-0009](../../../docs/adr/0009-feature-first-clean-architecture-frontends.md) refuses. **The last
entry renders through the module the stream will use**, keyed by the seven system-line codes
(`the-words.md` §23) with `{name}` filled from the `people` the row already holds and never from
`values`, so a corrected handle fixes the whole backlog. **What the row does differently is a prop
rather than a fork**: `LineRoom` says how much room the surface has, and it is what turns #335's
_the fix is a shorter value, not a second line_ into something a copy deck can act on — a place
line drops its court on one line and prints it in the stream. **The row asks for it twice**, and
that is §20.4 — _the visible label truncates, the spoken one never does_ — so the eye gets the
short place and every listener gets the whole value, beside every handle whole and joined with
§22.6's final _and_, which the challenge row above now speaks too. A line whose **code** this build
cannot read and one whose **values** it cannot read draw the same named gap, because a system line
**is** the whole of the slot a row draws it in. A **room whose membership is still growing draws
the members it has**, never the court it will become; **only live rooms are listed, because there
are only live rooms** — a conversation is destroyed rather than delisted (ADR-0153), which is the
opposite of the challenge list above it and the reason nothing here has a shelf life. §15's list
rule — _drop whole names, never shorten one_ — moved to `shared/formatting/handleList.ts` beside
`playerName()` when the second row kind arrived; **the face and the cluster did not**, and
`challengeRowGeometry.ts` records the three homes that were tried and are wrong.

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

**The room is a header, a stream, a composer and three questions**
([#364](https://github.com/Raketa02/Raketa/issues/364)). The header is 10.3's with a new **lead**
slot — a room is named by the people in it, so the faces sit beside the handles rather than in the
page under them, where the stream would scroll them away. **Its title is the handles' stems and its
spoken name is the handles whole, and the line under it is the sport and the game's state in lower
case** ([#401](https://github.com/Raketa02/Raketa/issues/401),
[ADR-0157](../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)):
`handleStem` is a prefix of the handle the person typed — ADR-0107 forbids _inventing_ a familiar
form and a stem invents nothing, which is `the-words.md` §15's and `handleStem`'s own argument — and
the state is _the same state as the card in Now_ — `features/plans`' four-rung ladder in its own
lower-case word, folded from the two lists the room already reads, **card name and never
standing**. That supersedes ADR-0148 §6 for the header alone; the row keeps it, and what §6 refused
— the prototype's twenty-state card-state tag, read by asking `challenges` and `games` — is still
refused. A room with no game draws the sport alone. The two lines sit in 10.3's new **sub-line**
slot rather than the eyebrow, title above and a quieter line below, and the header's budget is now
counted at `h1` rather than the rows' `cardTitle`, which had let it promise a one-line title that
wrapped. **Details is drawn only where there is a game**: `game_id` is nullable, so a
line-up-incomplete room has nothing for that door to open and draws none rather than a dead one,
and the door's spoken name is _Open the game_ because _Details_ names a screen where every other
door on this map names its act. **The stream is two components and never one with a branch** —
ADR-0146 refused that shape on the wire and #338 §7 refuses it here for the same reason — sharing
`conversationPresentation.ts`, which is the module the Chats row already renders its last entry
through. **A bubble draws its author's whole handle only where the room has more than two
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

**The send is the one optimistic act on the whole loop, and `client_message_id` is why.** Every
other act that reaches another person is pending never optimistic because it derives a standing
several people read; a message cannot be _wrong_, so the bubble is on screen before the round trip
and **the sender's own message never waits for a nudge**. It **pauses offline and resumes** — the
app default, and deliberately not `challenges`' rule, because a message carries no deadline
anybody chose — and the same key goes out on the resumed attempt, so a repeat answers `200` with
the same `seq` and one send can never become two messages. The optimistic bubble is read out of
the **mutation cache** rather than written into the query cache: a paused send outlives the screen
that made it, and client state written into the copy every other reader treats as the server's is
the second store this app does not have. A refusal **puts the words back in the box**, because the
retry is the control that failed. **The quick chips post words and change nothing** — one per
unfilled slot in slot order, plus _On my way_ only when the agreed day is today, which is what
caps the row at three rather than four, and each asks the question its slot is about and names no
weekday, no part of a day and no venue. The plan they are asked about arrives with
[#366](https://github.com/Raketa02/Raketa/issues/366); until then the room has no plan **and no
surface on which a slot could be filled**, which is the same state `GET /plans` spells by having
no row at all. _**Open the chat**_ joined the challenge screen's half-built arm in the middle of
grow · talk · end, and where it goes is a **client join over the player's own rooms** — ADR-0149
§3's shape, failing soft, because no route serves a challenge its conversation.

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
**invalidates** and the Query cache stays the single copy; the Chats list is deliberately **not**
invalidated with it, because a nudge is not an act the player took and the list sits mounted under
the room. **`liveState` is `domain/`** — a three-way _live · not live · held_ — and the placement is
load-bearing: _only in the foreground, and only after a connect attempt has failed_ is exactly the
pair of conditions a component drops quietly, and `closed` is a status of its own so a stream shut on
the way to the background is never news. **Not live is one amber line above the composer and never a
disabled one**: a send is an ordinary `POST` over a channel that is unidirectional by construction,
the fact has two parts, and only a sentence carries two. Players meet it **routinely and briefly**,
because the stream closes at the token's `exp` — so every attempt mints a fresh credential and a
`401` goes through the app's own single-flight rotation, once per channel, which is the whole of why
`shared/lib/http` grew a `streamAttempt` rather than the port growing a second `Authorization`
header. **Held is the other way round**: the composer, the quick chips and #366's three slot chips
grey out behind **one** pre-emptive note, reading is never blocked, and a hold never removes the
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
