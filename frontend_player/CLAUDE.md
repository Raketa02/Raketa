# Raketa Player App (iOS + Android)

React Native + Expo + TypeScript. The native app players use to find courts, book slots and
organise matches. It renders with **real platform components** — this is not a website in a
WebView. Feature-first Clean Architecture
([ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)), talking to
FastAPI over HTTPS and generating its wire types from `backend/openapi.player.json`
(the player half of the two-document contract). pnpm.

> The `frontend_player/` app of a three-app monorepo — see the root
> [`CLAUDE.md`](../CLAUDE.md). Run every command from this directory. Never import from
> `../backend/`; a hook blocks writes outside this app. Shared docs:
> [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

Two contracts predate the code and are **already settled** — read them before writing a
feature, not after:

| Doc                                              | Settles                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| [`docs/architecture.md`](docs/architecture.md)   | Where code lives, who owns which state, how auth/errors/Query/native behave in production. |
| [`docs/design-system.md`](docs/design-system.md) | Every colour, type role, spacing step and interaction rule. **Locked.**                    |

## What exists

`src/app/_layout.tsx` composes the providers and `src/shared/lib/bootstrap` runs the one
ordered startup sequence. Above that: the HTTP client with its 401 → refresh → retry
rotation, the `AppError` family, `shared/lib/auth` over the keychain, and four features —
`shell` (the five tabs and the one stack under them, below), `auth` (sign up — including the
**adult attestation**, the one question on that form that is not about the account — sign in,
session restore), `onboarding` (the entry gate, welcome, the
sports picker, the adaptive question loop, the explained result, and the summary and data
screens a player leaves through) and `player_profile` (onboarding's **second part**, complete: seven
steps over a client-held draft, and the one write that ends them — the Social tags picker,
2 to 6 chips from a served vocabulary, the photos step, up to three court photos or none, each
one checked server-side against the on-court rule and **warned about rather than refused**,
the availability grid, seven days by three parts of the day, blank on arrival and requiring
one ticked cell of the twenty-one before it continues
([ADR-0102](../docs/adr/0102-silence-is-never-scored.md)), the location step, one foreground fix coarsened to about a kilometre before it is
held, the radius step, a slider over the served bounds that opens at the served default, the gender
step, one required answer about the player and one optional preference over who they are
matched with ([ADR-0096](../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)),
the Proposals opt-in, never pre-ticked and with a finish that stays closed until the player
answers either way, and the **profile commit**: every answer in one idempotent
`POST /players/me/profile` — plus the **Profile surface**, the one read of the week, the
radius and the per-sport declaration that Play's search screen is drawn from, with an unkeyed
`PUT` behind each of the three). `play` has its four screens and the sheet over them, below;
`challenges` is the send and the answer: `POST /challenges`, `SH.propose`, the two re-reads a
refusal is followed by, and **the screen a challenge is answered on** — below; `conversations` is
the room the first acceptance opens — the Chats tab's second section, and **the screen behind it**:
the header, the stream, the composer and the quick chips, below; `plans` is the three slots that
room fills in — the card pinned under its header, and the one place `where · day · hour` is an
order — **and the Now rail over both of them**, the ladder that names a card and the nine cards it
names, below; and `games` is the result argument — the screen a card pushes, and the entering,
correcting, agreeing and disagreeing that close the loop, below.

**The Chats tab is two sections, two contexts, two queries and two caches, and they are
deliberately not merged** ([#363](https://github.com/Raketa02/Raketa/issues/363)). `CHALLENGES` is
the **obligation** and `CONVERSATIONS` is the **rooms**, so a `LINE_UP_INCOMPLETE` challenge you
accepted draws a row in **both** — §13's own sentence asserts both facts in one breath, and drawing
it only under `CHALLENGES` would make it the waiting room #221 says it is not. That falls out of
the composition rather than being arranged anywhere: neither section knows the other exists.
**There is no pill and no standing on a conversation row** — ADR-0148 §6's _the last line is what a
pill would have said_ is a product argument as well as a wire one, and the only pill this client
could now draw would be joined off the games cache, which is the cross-feature read
[ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md) refuses. **The last
entry renders through the module the stream will use**, keyed by the seven system-line codes
(`the-words.md` §23) with `{name}` filled from the members the row already holds and never from
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

**The room is a header, a stream, a composer and three questions**
([#364](https://github.com/Raketa02/Raketa/issues/364)). The header is 10.3's with a new **lead**
slot — a room is named by the people in it, so the faces sit beside the handles rather than in the
page under them, where the stream would scroll them away. **Its title is the handles' stems and its
spoken name is the handles whole, and the line under it is the sport and the game's state in lower
case** ([#401](https://github.com/Raketa02/Raketa/issues/401),
[ADR-0157](../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)):
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
[ADR-0147](../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)).
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
[ADR-0156](../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
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

**The plan card is pinned under the room's header, and it is a counter, the three chips and the
lock** ([#366](https://github.com/Raketa02/Raketa/issues/366),
[#403](https://github.com/Raketa02/Raketa/issues/403),
[ADR-0144](../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
[ADR-0155](../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
**Pinned**, because a chat opens at its newest entry, so a card in the scroll is the first thing
off-screen; **no panel**, because the panel that explains the chips is the game screen's — one
panel, one home. `domain/slots.ts` is the one place `where · day · hour` is an order, and the order
is of decreasing negotiability. **The count and the lock are two facts, and `domain/lock.ts` holds
both**: `N of 3 set` is derived from the three fields and never sent, and `Locked` is `lockedAt`
and **never** the count under another name — three filled slots is a plan everybody _could_ agree,
and the lock says somebody did, by posting `{name} locked the plan` into the room, which is the
whole of what it does. _Lock the plan_ is greyed below three, live at three, busy with its own word,
and **gone** once locked rather than 6.1's `settled` — a second lock records nothing and answers
`200`, so a control still offering it would be one that provably does nothing, and the counter's
word is the carrier. **The label carries no reason**, because the counter directly above is the
note #324 owes every greyed control. **A lock freezes nothing and there is no unlock**; `locked by
everybody` stays a phrase the data cannot support. **A hold met on any plan write reaches the
room's one amber note** off the mutation cache, through `usePlanWriteRefusals`, because a hold is
a fact about the account whichever of the five writes on that screen met it. **Two grids and
neither is a rule this client invented** — the day row is today + 6
clamped to `planned_at + PLAN_HORIZON`, so it **shrinks as the week runs out** and inside the entry
grace draws **no chips at all** with the refusal sentence beneath them, and the hour row is the
thirty-five half hours between 06:00 and 23:00; both numbers are the server's, which refuses
`the_day_is_past_the_horizon` and `the_hour_is_not_offered`, and _the grid a client draws is a
convention, and this refusal is what makes it true._ **A past combination is refused in written
copy rather than by a disabled control**, because the day and the hour are filled in either order
and either can be the second — so the sentence names **both** remedies, names no value, and is
drawn under the row with both chips above it. **Nothing here is optimistic**: a slot change writes a
line other people read, so the chip goes **busy with the value it already had** and the new one is
drawn only once the server has answered — which is why 6.2 grew 6.1's `busy`, label swap included,
since this system greys for _you may not_ and for _on its way_ alike and only a word tells them
apart. **The line arrives through the stream like any other entry**, on the same nudge every other
member's copy of it arrives on, so nothing in `plans` invalidates the room — **and the room's nudge
re-reads the plan beside the stream** ([#405](https://github.com/Raketa02/Raketa/issues/405)), so
the card, the quick chips and the header's state word say on every phone what the line says, with
nothing pressed; on every nudge and never on sighting a plan line, because a trigger keyed on the
line vocabulary goes stale on exactly the build too old to read a new code. Every plan write first
**cancels** the list's in-flight read, which is not optimism — a nudge-started read can land after
the reply that was written in, and would roll the slot back for a second. **Any member may fill
or change any slot, any number of times** — the line is the friction, there is no rate limit, and
**a slot is never emptied**, so every editor opens on whatever is there and none of them offers a
way to clear one. **The card is folded against `GET /games`' `read_at`** and never against the
phone: `GET /plans` deliberately carries none, because a plan folds nothing against the clock, and
_today_ and the horizon coming off one read is what makes `today + 6` and `planned_at + 7`
comparable at all. **`features/plans` may import `features/games` and never the reverse**
([ADR-0149](../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §1) —
the client half of ADR-0145 §4's clause, and _a grep rather than a judgement_: `eslint.config.mjs`
refuses the import in three blocks, one per baseline block it shadows, and `pnpm test:boundaries`
drives all three plus the two exemptions they could silently have dropped. The room composes the
card, which is the shape #364 anticipated as a slot the route would fill and this ticket did not
take: the game id comes off the read the screen mounts and `held` off the fold below it, so a slot
would have been a render prop over a route that had joined the room itself — three props and a
second join to avoid one import through a public surface the room already makes to `features/games`
for its _Details_ door. The same read answers the quick chips, which is the `undefined` #364 left
them holding — **and the chips' rule and words moved here with it**, because §22.4 is the plan's
vocabulary by `the-words.md` §22's own assignment and the rule reads the slot order. #364 declared
its own `PlanSlot` and its own order to make do with no plan feature to put them in, and a second
spelling of _where · day · hour_ is exactly what this ticket says `domain/slots.ts` must be the one
place of. **The row stayed in the room**: a chip is a message, and the send it goes out on is the
composer's — and since [#402](https://github.com/Raketa02/Raketa/issues/402) it is drawn **inside
the composer's block**, one surface with the field and a coral Send under one hairline at the foot
of the screen, on the screen's own `paper` because the bottom inset is the frame's under it. **The platform zone left `conversations`** for `shared/date/platformZone.ts` on the
third-caller rule, and unlike the tables promoted before it a second copy would be two answers to
_which day is it in Warsaw_ on one screen; #335's _shorter value, not a second line_ moved to
`shared/formatting/placeName.ts` beside them, because the `Where` chip is the third surface that
rule governs.

**The result argument is one screen and eight states, and the state is derived**
([#314](https://github.com/Raketa02/Raketa/issues/314),
[ADR-0137](../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)). **A result is the
record that a game happened** — no booking, no calendar, no date field anywhere — so the entry
_is_ the fact, and everything after it is an argument bounded to two rounds —
`domain/resultArgument.ts` is named for it, because the glossary word _conversation_ belongs to
the room the first acceptance opens, and two of them in one codebase is how somebody eventually
subscribes the wrong one. It folds the standing, the scores on the table and **which seat is
yours** into what to draw, and nothing outside that file reads a `GameStanding`: a
**correction** and a **counter** are the same `POST` and completely different news, and #314's
own worry is that _"a player will spend an attempt fixing a typo."_ Three of the eight are worth
knowing. **Silence confirming is drawn before
it happens**: the standing line says it **on the row as well as on the screen**, so a deadline is
never something a player reaches by tapping, and the screen adds
`prototype/result-confirmation`'s clock block over it — a figure at arm's length above one
sentence. **`both-stand` draws both scores and offers the agreement that ends it** — ADR-0137
§4's only exit short of the game going unscored, and the one the screen could not offer while
`standing_proposal` was _"when exactly one is"_ and the wire returned **neither** score
([#317](https://github.com/Raketa02/Raketa/issues/317),
[#318](https://github.com/Raketa02/Raketa/issues/318)) — the **eighth** state is the agreement
itself, below. The reader's own score is drawn quiet
above the other side's, the one control is named for the score it agrees with, and the copy names
the way out instead of stating an ending as though it were the only one. There is never a counter
there: that side has had its one turn. **Which of the three `AWAITING_ANSWER` screens it is comes
off the count** — `proposals` carries nought, one or two — rather than off an absence that used to
mean _nothing entered_ and _both sides have spoken_ alike. And **an agreement is a state of its own rather than a flag on the three it can happen in**: for
the length of the grace the standing still reads `AWAITING_ANSWER`, but the proposing side has
stopped waiting on silence, so the headline and the clock say the score was agreed and when it
settles, the correction goes (`state_result` refuses it with `the_other_side_has_answered`, whose
sentence can now say _while this screen was open_, because the control's own absence is what
proves the timing), a second agreement from the same side goes with it, and **the disagreement
stays** — inside the grace a counter still beats an agreement, which is the whole reason the
grace exists. It is an arm rather than an optional field because carried as a field it was a
state every renderer had to remember to pre-empt its own `switch` with, and the one that forgot
said something false. It **keeps both proposals**, because what is left to do is read off them:
the side that may counter is the side that has not spoken, and two scores standing means neither
can — the aggregate's one-per-side cap rather than a rule this client invented.

**The instrument is the prototype's, and so is most of the copy.** #314 says the score-entry
interaction is solved work, and it is: a **pad** over a grid of the sport's own legs, both sides
named above the columns they own, because _"`6-4 3-6 6-2` is not a score until you know whose 6 it
is"_ and a stepper is six taps to reach 6. The **`+` key** beside it is what keeps the range
honest — a padel third set is often a ten-point tie-break and a badminton game goes to thirty — so
_we know the shape, not the rulebook_ is built into the instrument and not only into the
validator. Variant C's layout comes with it: the score being answered stays on screen **beside**
the one being typed, and an unscored evening ends on a fact list rather than an apology. Two
things are rewritten because the model moved. **There is no absolute time anywhere** — the
prototype quoted one beside every duration, and this platform has no calendar to print one
against — so every span is measured from `read_at`, the instant the standing beside it was folded.
And **a person is named where a person acted, and a side where a side did**
([ADR-0141](../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). A seat carries
a handle and nothing else about the person in it — no Level, no band, no run of form, because a
card is what a _searcher_ reads to decide about a game that might happen and this is the record of
one that did. So the eyebrow says **who you played**, which is what tells two padel games in a week
apart, and _tomek.p put a score up_ and _tomek.p agreed with your score_ name the person a result is
being settled with. The score's two columns stay _You / Them_ and _Your side / Their side_: a score
is a **side's** claim, capped one per side and answerable by either of the two who played it, so a
column headed with a handle would charge a doubles score to one of them. Every handle is drawn
**whole**, which is
[ADR-0107](../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4, and a seat
`users` can no longer answer for draws the unknown player's `?` rather than being dropped. The
prototype's `✓` went the way the on-court mark's did — **Archivo ships no U+2713** — and the
winner's row carries the word instead.

**Now stops being a placeholder, and what replaces it is a rail, a ladder and nine card states**
([#367](https://github.com/Raketa02/Raketa/issues/367)). `PLACEHOLDER_COPY.now` is dead and
`shellCopy.test.ts`'s _never says nothing is happening_ **moved with the copy rather than being
deleted** — it was Now's refusal first. The tab keeps the shape it has always had: it owns its own
sentences and nothing drawn under them, and the sentences are handed to `GamesRail`, which is
`features/plans`' because a card needs a **plan** beside a **game** and ADR-0149 §1's arrow runs one
way. **They are not gated on the read having landed**, and that is the point of how §22.7 worded
them: _every game you arrange shows up here_ and _Play finds you one_ are true of a player with five
games and of one with none, so there is nothing to hold them back for and holding them back would
leave a blank screen. The bolt is not drawn, on 10.2's own rule.

**The ladder is `domain/`, four rungs read in order, and the clock outranks the checklist** — _the
agreed point has passed_ → Needs result, _the agreed day is today_ → Today, _all three slots
filled_ → Game on, otherwise Planning. It is the single most drift-prone thing on the map: four card
names, two tickets that each keyed a rule on it and one amendment already spent closing the hole
between them, so it is one function every surface reads. The **agreed point** sits beside it — the
agreed instant when day and hour are both recorded, the start of the following local day when only
the day is, nothing when no day is, **later rather than earlier** so nobody is asked for a result
before they could have played — and it is the server's field, never recomputed here. Everything
folds against `GET /games`' own `read_at`, so **Now has one clock by construction** rather than by a
rule anybody remembers: `GET /plans` deliberately carries none.

**A rail, not a list.** `GamesSection` refused shelves in writing and a rail keeps that refusal by
not being a list at all — a heading with a count, one card, a swipe, and nowhere to put a shelf. The
card is 7.7's **paging** geometry at the content width, so it has **no peek**, which is what makes
7.18's dots the affordance rather than decoration: they **track the scroll**, they are not
pressable, and they say nothing, because the count is on the heading above them. The order is **the
server's — newest arrangement first — and stable**, where a clock sort silently re-orders a player's
cards between sessions; the cost is stated rather than hidden. **Endings keep a card for 24 h and
then leave**, measured from the last instant the wire dates on the game, which is exact for one that
never happened and early by at most one answer window for one that was played.

**The card is tag · eyebrow · figure · line · gloss · court · footer, and every name is folded at
read time** — no client state machine and no status column. The tag **is** the card's name and its
dot is the **sport's**, with urgency carried by the whole pill; a standing this build cannot read
draws **no tag**, because there is no name to say and the gap belongs in the line the standing
_is_. The figure takes **three shapes** — the hour, the weekday when there is a day and no hour,
nothing when there is no day — and the line takes whatever it did not, which is what keeps **the
hour printed once**. The gloss is **one rule for three rungs**: the next unfilled slot in slot
order, with _Needs result_ overriding it with the time left, so there is no fourth string to keep in
step with the ladder — and everything that is not a rung already has a sentence, `features/games`'
`gameStandingLine`, the same one the screen behind the card says. The court is 7.12 at `header`, and
its seats are **generated posters plus 7.12's three-character caption** — the caption moved to
`seatFace.tsx` when a third court needed one — with the unknown player's `?` for a seat `users` can
no longer answer for.

**The footer is a named door and the ✉, over 7.7's `marginTop: auto` hairline**, which is what
aligns footers across cards of unequal height and the whole reason a rail can hold a 40pt figure
beside none. **The button is a named door**: it carries the act's verb, it navigates, and it
**never writes** — and the body goes wherever it goes, so the two are one action and one
accessibility element whose name ends with that verb, which is why the drawn button is hidden. The
✉ is the second element because it goes somewhere else, and it is drawn only where there is a room:
the join fails soft, and an ending destroys a conversation rather than delisting it. **The ✉ is
Feather `mail` and never the character**, on the bolt's own argument — Archivo ships no U+2709.
A game is genuinely **pushed** over the rail, which made it the first screen outside Play to take
the shell's push transition and the first to need `shellTabs` to say which tab a segment is
_inside_ — Now's root is `/`, so a screen over it cannot share its segment the way the builder
shares Play's. Neither write on the screen behind it is optimistic and neither overrides
`networkMode`: a standing is folded from the record and the clock, so the only client that can be
right about what a game becomes is one that asks, and the app's own test — _does this act carry a
deadline the player chose?_ — answers no for both, where the challenge send answers yes.

**One screen shows a game whatever state it is in, and the plan arrives on it as a child**
([#368](https://github.com/Raketa02/Raketa/issues/368),
[ADR-0149](../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §2).
**Grown, not replaced**: `GameScreen` was already a state-keyed detail surface with ten arms, and a
hand-off in the middle of one standing's life would give a player two different screens for the
same game depending which day they tapped it. What it grew is **one `ReactNode`** and **one word**,
and **`features/games` still never learns a plan exists**: no `Plan`, no ladder, no rung, and
`eslint.config.mjs` refuses the import. `GameScreenWithPlan` is the one place that holds both
halves — it does the join, folds the arm and fills the slot — and **both routes mount it
unchanged**, so a composition spelled at two call sites cannot drift at one of them.

**`AWAITING_ENTRY` is one standing over two landings, and that is the arm.** §5.2 lands _Planning_
and _Game on_ on **the plan** and _Today_ and _Needs result_ on **the score grid**, so the grid is
the screen on the two arms the moment has reached and **one press away** on the two it has not —
the press being `We played`, one word in `shared/vocabulary/theActsWords.ts` that the Now card's
door reads too — shared rather than either feature's, because the two reach each other at load time
and a word read across that seam mid-evaluation reads a half-built module. The word that crosses back into that feature is `EntryLead`, in its own
vocabulary rather than a rung in somebody else's, and it is **derived from the card's own door**
(`entryLeadOf`) so the two tables cannot disagree about where a button goes — _the verb names what
you arrive at_. **_We played_ is available on every entry arm**, not only the two that lead with it,
because `standing_of` gates entry on `entry_closes_at` alone: four people can arrange a game at six
and play it at eight without filling a slot. The cancel follows from the same fact — a grid that
_is_ the screen has nothing behind it to go back to.

**The child is the plan read rather than edited** — `Tag`s and never `Chip`s, one accessibility
element, with §22.2's **inverted** panel over it: it stops explaining an absence and names one,
because a player seeing _Zabłocie Sport · Saturday · 18:00_ inside an app may reasonably assume the
app did something about it. **The checklist is three lines, capped, in one order**, and its third is
**cited, not written** — `worthLine`, the whole of what survives ADR-0143 §8's refusal — so the
screen defers its own copy of that sentence on the entry arm rather than printing it twice. What the
arm changes is **the screen around the child and nothing inside it**: §22.6 settles that _the rungs
differ by the clock and not by the arrangement_, so the checklist is one rule on all four and no arm
reaches the child at all. **A plan arm asks for nothing, so nothing on it wears the one accent** —
the chat door is 6.1 `secondary` on every arm, because an accent in the scroller beside a quieter
control in the pinned slot inverts what pinning is for, and the coral comes back where
`Send this score` is pinned. **_Open the chat_ is always drawn, whichever door you came in by** — arriving
from Now it is the point and arriving from _Details_ it is the way back, so drawing it conditionally
on the route would make the surface depend on its door; it fails soft on the room being gone and on
nothing else. **One component, two routes** — `/games/[gameId]` and
`/chats/conversation/[conversationId]/details` — so each lights its own column and _back_ is correct
by construction, with **no `from` parameter** and `tabForPathname` still pure. Eight corrections to
the details design are **absences** rather than sentences and each is a record read out in
`GamePlan`'s own note — _part of day_ is not a slot, the lock button and its coral outline are
deleted, the slots are tags, _Sun 9_ is a date this app does not have, _60 min_ is a duration nothing
holds, and _COMPETITIVE_ is a search's mode rather than a game's kind — as is **press and hold for
the full record**, and as are the **pairing forecast and the player rows**, upheld with an argument
of their own: a forecast helps you decide whether to play somebody, and on this screen you already
have. The reversal is filed as [#346](https://github.com/Raketa02/Raketa/issues/346) rather than
taken.

**The shell is five tabs over one stack, and it remembers nothing.** `TabShell` mounts the
`TabBar` once, below the navigator, and reads the active column off the current path —
`tabForPathname`, by the **first** segment, so ⚡Play stays lit for every screen inside Play.
It is a `Stack` and deliberately **not** `<Tabs>`, which keeps a history per tab and restores
it: built that way, a player who leaves the deck and comes back lands on the deck, and _back
goes where I came from_ fails with **no symptom** — nothing throws and nothing looks wrong
([#227](https://github.com/Raketa02/Raketa/issues/227)). So switching tabs **replaces**, and
entering Play lays down `[Now, Find a game]` — two screens, which is the whole of _back from
Play leaves Play_. Both go through **one function**, `resetShellStack`: a flanking tab lays
down one screen, `enterPlay` lays down two, and the second caller of `enterPlay` is the _Find
a game_ segment, because re-entering the tab from inside it is arriving rather than going
back. **A Play session ends exactly when the reset runs**, which is the definition the Play
state ticket is owed. **The bar stands down on exactly one route, the conversation**, where the
composer replaces it ([#400](https://github.com/Raketa02/Raketa/issues/400)): `barStandsDown`
beside `tabForPathname` names the whole path rather than `/chats/*`, `TabShell` does not render
the bar there rather than hiding it, and the room takes the bottom safe-area inset the bar owns
everywhere else — the one exception to design-system §10.1, recorded in Part 16. The column
stays lit while the bar is down. **Two of the five tabs are honest placeholders** now that Now has a screen
([#367](https://github.com/Raketa02/Raketa/issues/367)): one sentence naming what the tab will be
plus that it is not built, one of them a citation of a decision taken elsewhere. **No sentence the
shell writes says "nothing is happening"** — it began as Now's refusal, because Now is where a send
lands and asserting emptiness would be a lie one tap after a challenge went out, and it now governs
the two built tabs' empty states as well. `shellCopy.test.ts` holds that refusal, and it **moved
with the copy** rather than being deleted when the placeholder it was written for died. The **You**
tab still carries the account panel, because signing out is
the only way back to the beginning and the shell arriving is what gave it a home. The bar's
**transitions** follow the two moves: `none` by default, because a replace that slid in from
the right would read as going deeper on the gesture whose meaning is that nothing was kept,
and the push kept for the four Play screens, which genuinely are ones — Find a game is entered,
and the deck, the builder and the pool are each pushed over what stays underneath them.

**Sign-up asks whether the player is an adult, and it is an attestation.** The platform is
adults only, and that is a precondition of _holding an account_ rather than a rule about who
is shown to whom ([ADR-0124](../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
What the form collects is **one boolean — never a date of birth**, and it is **not age
verification**: there is no date picker anywhere in this app and this is not where the first
one arrives. The box is never pre-ticked, _Create account_ is never disabled by it, and the
refusal is a sentence under the box rather than a closed control
([ADR-0089](../docs/adr/0089-player-profile-context-event-sourced.md)). The same sentence
renders when the server refuses by `adult_attestation_required` — an older build or a
replayed request can carry a body this form would not have sent, and _try again_ would then
be the one thing that is not true.

**A flagged photo is warned about and never taken away**
([ADR-0133](../docs/adr/0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)).
Every upload is scored server-side against _shows a racket sport on a court_, and the answer
comes back on the upload response as a code — `allowed` or `flagged`, never a sentence, and
never the evidence it was taken from. The step is what writes the sentence, in
`photoStepPresentation`. **The check is wrong about some unknown share of what it flags**, so
the copy reports _we could not see a court_ rather than accusing anybody, says nobody has
looked because nothing reviews a flagged photo a second time, says nothing is blocked because
the photo is stored and committed like any other, and offers keeping it before swapping it.
The photo keeps its place, keeps the lead if it had it, is in `photo_ids`, and `Continue` is
not touched. The step does **not** announce the check up front: that is small print to the
majority whose photo is fine and reads as a threat to the rest. `null` on the wire means _this
response said nothing_, which is not `allowed` — the mapper collapses it toward silence, and a
verdict this build has no words for is collapsed the same way.

**The gender step says what narrowing costs, at the moment of the press.** The preference
is a **mutual** gate: setting _Women only_ does not only filter what a player sees, it hides
them from every man — including men who searched for anybody. That half is the one nobody
would guess, and **learning it from an empty inbox is not acceptable**, so the note is
rendered the instant a narrowing option is chosen and goes away when it is widened again.
The rule that decides whether there is a cost is `gender.reachOf`; the sentence is
`genderPresentation`'s. The answer about the player is **required and never pre-selected** —
_Prefer not to say_ is a choice somebody makes, not a default given on their behalf — while
the preference beside it opens at _Anyone_, which is the value every profile already
carries. **Neither value ever comes back out of the API** (ADR-0096 §6), so this step is the
only surface in the app either one is ever seen on.

**Onboarding is two parts, and the part is the checkpoint unit**
([ADR-0090](../docs/adr/0090-onboarding-per-player-checkpoint.md)). Part one is the Skill
rating and resumes mid-run; part two writes nothing until one commit at the end, so leaving
it restarts at step one. The entry gate reads three facts and has four destinations — resume
· welcome · the social steps · the app — and the second part's screens live in
`player_profile/` rather than in `onboarding/` because the profile screen will later edit the
same values against the same rules
([ADR-0089](../docs/adr/0089-player-profile-context-event-sourced.md)).

**The consent step's copy is frozen and versioned.** `optInPresentation.ts` owns every
sentence the Proposals opt-in card shows, together with the `copy_version` stamped beside
the answer in the draft — consent gathered against one sentence is not consent to a
different one, so re-wording that card is a **new version with the old one retained**,
never an edit. It is the only file in this app whose strings are evidence. It stands at
**`proposals-opt-in.v3`**, which rewrote two of the three promises and the scope note and
moved that note above the card; `v2` dropped the line under the title, and both it and `v1`
are retired and kept in the same file, because a version identifier with no record of what it
named evidences nothing.

**The ratings summary ends the first part, and it is the door into the second.** The order
is result → **done** → the seven steps → the commit → data → the app. The _pass_ routes as far
as the summary and no further (`nextDestination`: _is there anything to account for_), and
the **done screen** reads whether a Player profile is still owed and either enters the second
part or continues to the data screen — one fact, read once, on the screen that acts on it. A
player who is already set up — one resuming a run they left behind — passes straight through.
The summary comes before the seven steps rather than after the commit, because it is what a
player just earned and the second part was otherwise standing between them and it; a Skill
rating is written when the questionnaire completes, not when a profile is committed, so
nothing on that screen was ever waiting on the commit to be true. Entered with no pass
running, it has nothing of its own to show and says so.

**The commit is the one mutation in this app a retry may repeat.** Its **commit key** is
minted when the part is entered and lives exactly as long as the draft, so a double tap and a
retry after a failure both carry the key the first attempt carried — the disabled control is
the courtesy, the key is the defence. `Idempotency-Key` is set by `shared/lib/http` for any
request that names one, including the replay a 401 rotation makes. A failed commit keeps the
draft, keeps the player on the step, offers the control that failed as the retry, and claims
nothing. `commitStanding` and `mayFinish` own when the finish opens — a rule, not a
`disabled={…}` expression — and `readyToCommit` under them is what makes a partial commit
unrepresentable. Three things hold the finish shut. **No Location area**: location is a core
requirement for discovery, `CommitPlayerProfileRequest` requires it, and the last step asks
once more with the way back one press away rather than trapping a player on step four behind
an OS prompt. **A blank availability grid**: the week has a floor of one cell since
ADR-0102, so silence about when somebody plays is asked for rather than scored as a zero —
step three already refuses to continue on one, and this is the same rule read at the end.
**A photo still going up**: uploads outlive the step that started them, and the
body names photos by the ids the server gave back, so committing mid-upload would silently
drop a picture the player watched arrive. That one asks for nothing and opens itself.

A failed commit whose `code` names an answer — `availability_grid_empty` today — is drawn as
that answer rather than as _try again_, with the control back to the step that takes it: the
commit re-validates every rule a picker enforced, and re-sending the identical body would
fail identically.

`src/shared/lib/platform/` owns everything the app knows about the device: the Query
focus and online wirings, and three **platform ports** — `LocationPort` over `expo-location`,
`ImagePickingPort` over `expo-image-picker` and `LiveStreamPort` over `react-native-sse`. Each
is the only importer of its module, for the reason `shared/lib/auth` is the only importer of
the keychain, plus one more: a native module has no JS implementation underneath it, so a
feature that imports one cannot be tested at all — and **the third one is here on that second
argument alone**, because its far side is a socket rather than a native module and a screen
that opened one is a screen no suite can put in front of a severed stream. Hand-written fakes
live in `src/test-support/platform.ts`, and a screen reaches each through `useLocation()` /
`useImagePicking()` / `useLiveStream()` — contexts whose
default is the device, so only a test ever supplies anything else. Beside them sit the two
lifecycle wirings and `useOnForeground`, the app's one answer to _did we just come back_.
**Location is foreground only** — nothing asks for, checks or starts a background one — and
a fix is **coarsened to about a kilometre the moment it is read**, so the precise reading
never reaches a store, a screen or a crash report.

`shared/lib/http` has **two verbs**: `httpRequest` for JSON and `httpUpload` for one file.
They share the correlation id, the `Authorization` header, the timeout policy, the error
mapping and the single-flight 401 rotation — a second copy of any of those is the second
networking path the module exists to prevent. `httpUpload` also reads the local `file://`
URI a picker hands back, because `fetch` is what this module is allowed to touch, and it
reports **stages rather than bytes**: React Native's `fetch` cannot say how much of a body
has gone out, and buying that would mean a second transport. It also **authorises the one read
that is not a `fetch`**: `streamAttempt` mints the URL, the correlation id and the
`Authorization` header for one attempt at the live channel and `rotateStreamCredential` puts it
through the same single-flight rotation, so the third port forwards a bag it never reads rather
than becoming the second place a bearer header is built. A **fresh bag per attempt** is the
load-bearing half — the server closes that stream at the token's `exp`, so a channel that
captured its headers would reconnect for ever with the credential that had just expired.

**Play begins as a copy deck, and `challenges` beside it.** Nothing the matcher sends is
prose: what crosses is a `Term`, a `LivenessReason`, an `UnfilledReason`, a `Prompt`, a
`Standing` — and the app writes the words for all of them
([ADR-0106](../docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md),
[`the-words.md`](../docs/specs/matchmaking/the-words.md), cited by section and never
restated). So the two features arrive **words first**: `features/play/components/*Presentation.ts`
and `features/challenges/components/challengePresentation.ts` hold every sentence those
screens will say, and the screens are assembled from them rather than from templates inlined
in six components. **Two shapes, and the split is whether the sentence quotes a value** — a
`Readonly<Record<Code, string>>` wherever the code has no payload, so a code with no words
does not compile, and **one function per variant** for the eight evidence variants, because a
reason line is a sentence _over_ its evidence. The unions those tables are keyed by are
`domain/vocabulary.ts`'s, held equal to the generated ones by a compile-time assertion in
`mappers/wireVocabulary.ts` — the wire boundary keeps `generated/` out of `components/`, so a
code added, removed or renamed on the contract fails `pnpm typecheck` in the one file whose
job is saying so. Two rules sit over the deck. **A reason line states its evidence's facts and
never grades them** — a client thresholding a term value would be that judgement in
TypeScript — so the grading vocabulary belongs to `concerns[]`, which is the engine's and
arrives ranked. And **the de-duplication filter is per surface and runs before the cap**:
`domain/reasonSelection.ts` takes the terms a card draws, removes them, any term the engine is
concerned about, and any term whose evidence **is not a reason at all** — three of the eight
renderers legitimately decline, and a survivor that renders nothing is the blank row the whole
selection exists to prevent — and only _then_ takes three, falling back to the top
`LivenessReason` and hiding the row rather than drawing an empty one. Three tables were
**promoted to `shared/`** on
`recoveryMessage.ts`'s third-caller rule rather than re-typed here — the Social tags, the
week's days and parts, and the level and percentage formats — beside `playerName()`, which is
ADR-0107's _the whole handle or nobody_ with one implementation and a type that will not take
a shortened one, the one sentence a build says about a code it is too old to read, and
`counted()`, the single seam every counted phrase routes through so that a market with real
plural rules has one function to change rather than every sentence that counts something.

**What each Play control announces is copy too, and it lives with the rest of it.** An
accessible name is localisable, it quotes numbers that need §B16's formats, and it composes
codes whose sentences already have a home — so `accessibilityPresentation.ts` writes them
through the same _code → message, never message → message_ mechanism, and **a label is never a
template inlined in a component** ([`the-words.md`](../docs/specs/matchmaking/the-words.md)
§20). **One rule decides every element**: _one accessibility element per action, and everything
with no action of its own merges into the nearest action above it_ — which is what makes the
question navigator one element and the availability grid twenty-one, as one rule rather than
two precedents. It has three consequences worth knowing before reading the file. **The card is
spoken in a different order than it is drawn** — identifying facts lead, the argument follows —
and it is the one recorded divergence from visual order in the feature. **The seat, its clear
badge and the empty seat carry a side and a role and never an index**: a listener has no
picture of the court, and H-25 puts both squash players on the same half, so seat 3 is not
where seat 3 was. And **the why-fit meter is hidden**, because the row prints its number two
words earlier and a bar over a printed number is 6.8's double announcement — leaving
`progressbar` nowhere in this contract at all. Two Part 13 violations are fixed rather than
carried over, both colour as the only cue: the diff grid's _new_ and _dropped_, which the
sheet's own copy named as a colour, and the pool header's tinted percentage, which gains
§B9's balance word beside it. The header is not built, so what ships is the word and the rule:
`balancePresentation.ts`.

**The same person is drawn three ways, from one contract and one parts kit.** `CandidateCard`
is a **photo panel** with an identity row beside it and **one head-to-head band** under both,
`CandidateCardSocial` and `DeckCard` are media-top with fact rows, and they are **three
components rather than one with a `surface` prop** — a single card would carry `surface === …`
at nine sites, which is the sixty-line conditional the split exists to prevent. Under them sit
`CandidatePhoto` (the photo-or-poster switch, one component at three sizes, its radius 33 % of
its own box), `FactRow` and `ReasonLine`; `CardHead` is the social and deck cards' alone, and
the competitive card's `PhotoPanel`, `IdentityRow` and `HeadToHeadBand` are the three parts
[#309](https://github.com/Raketa02/Raketa/issues/309) split off it rather than adding two flags
to say which head to draw. **Each reads no global state**, taking `(candidate, envelope)` plus
whatever the _screen_ rather than the person owns — the competitive card's `sportName` is the
search's Sport, and putting it on `player_card` would be twenty copies of one fact per
response. The envelope travels whole
rather than as a `mode` string precisely because `SearchEnvelope.mode` is null on the deck and
the mode the engine priced a row under is not — the two are supposed to disagree there. **Each
card exports the set of terms it draws**, because that set is a statement about that component
and is the one thing that could go stale silently anywhere else. The set is read **both
ways**: the de-duplication filter drops those terms from the reason list, and the card's spoken
name states exactly the ones it draws — so the competitive card, which draws no distance row,
says its kilometres as a reason line and never also as a clause. The two registers stay apart —
a **fact row** is a fact the card states, a **reason line** answers _why this person_ and never
grades it, and the one concern a card draws is the engine's graded claim in the opposite tone.
Anything actionless inside the body **merges**: the photograph, and the balance bar, whose
reading is drawn as a word beside it and spoken as a clause, because a bar is a tint and
_never colour alone_ binds the sighted half too. `CandidatePhoto` draws the minted
`photo_url` and falls back to the generated poster when the id is omitted, reaching
`courtPosterFor` from `shared/ui` rather than copying the hash: one player id, one poster,
forever. **Only the deck card floats** — #219 B3's argument is about a
card that translates and rotates out under a thumb, and a row in a scrolling list does neither,
so the pool draws one shape twice. **The volt tag is a tag again on the competitive card and a
sentence on the other two**, which is #231's open decision #14 reversed where the identity row
has a slot beside the handle for one: it is bound to `INTEREST_LIFT` either way, and the tag
takes its liveness twin's two words because the two codes are one tag. **The panel prints the
Level twice on purpose** — hugely over the photograph and again on the right of the band — and
what makes that legible is the system's second pinned scrim: a photograph is a ground nobody
chose, so `photoScrim` collapses it to its worst case, pure white, at a ratio `textOnMedia.test.ts`
derives. **The panel's third label is the ON COURT mark, and it is a label rather than the
designs' shield because the panel was measured**
([#313](https://github.com/Raketa02/Raketa/issues/313)). It draws on _checked and passed_ and on
nothing else: _flagged_ and _nobody looked_ draw **identically**, because a card must not tell
one player that another's photograph was doubted, and the poster draws none because it is not a
photograph. There is **no number in either register** — ADR-0133's clause survives ADR-0138
untouched. The ✓ went because **Archivo ships no U+2713** and the app's own drawn tick leaves
51,19pt of words 45,2pt of room; the chip went because the panel's corner is a third of its own
width, leaving 39,2. What is left is centred — flush left the first letter is inside the curve —
in `mintSoft` at 4,55:1, the tightest pair on the panel and the only one that is not white, under
a `maxFontSizeMultiplier` **derived** from the real Archivo metrics as the tab bar's is
(`onCourtMarkFit.test.ts`, over `test-support/fontMetrics.ts`, which is where the tab bar's
`cmap` walk moved when a second surface needed it). The mark is spoken as `Photo checked: on
court`, straight after the level row, and it **leads with the noun** because _on court_ in a run
of clauses is one comma away from activity recency. **Up to six of their Social tags draw on the competitive card, and the amber line is the
one claim on it** ([#311](https://github.com/Raketa02/Raketa/issues/311)). The ones the searcher
also chose are tinted and carry `· you too` in words, off `matched[]` — the intersection is the
engine's and is never recomputed from a profile read, and only `matched` tints, because
complementary and clashing are a different relationship and stay sentences. **The absence has
three spellings.** Compared and nothing matched is _No tags in common_, in amber, **in the row's
place**. Both terms stood down is the platform not knowing, so the tags draw untinted and nothing
is said. And compared, matched, and this build has no words for what matched — `matchedInFull`,
the one place §3's silent drop would have turned into a claim — draws as the second, and
withholds the term's **measured zero** with it, because _Different on court_ is the same claim
one register over. **The claim needs both tag terms and a match needs only one**: a `matched`
list is a positive fact, where _No tags in common_ is a claim about everything and a
half-compared candidate has not earned it. This
**reverses `CandidateCardSocial`'s refusal on its own terms**: tags were kept off a card because
_the label cannot announce them_, so the label announces them, and the rule that ships with the
row is **never draw a tag the label does not speak**. The social and deck cards still draw none,
now for a reason about those cards. **The card that draws the row loses the `Both of you`
sentence** — §10's _said once_, filtered on **the tags the row actually drew** rather than on the
term's own list, so a match beyond the six-tag cap keeps the one sentence naming it and the two
cards without a row keep theirs. **Three record blocks and two stake boxes are what the card grew when the record-keeping
landed** ([#312](https://github.com/Raketa02/Raketa/issues/312)). _Player Score · Last 5 ·
Counted_ is what the platform **watched** — reliability, a run of form and the honesty figure
behind a rating — and _Win, counted / Lose, counted_ is what a counted game would move. Both
rows are `StatBox`: a recessed `paper2` box with a name over a figure, and the recess is
load-bearing rather than pretty — a Player Score drawn as ordinary card text beside a Level
printed twice reads as a second rating, and it is **nothing to do with skill**. **Each block is
hidden when its fact is absent and never zeroed**, because the wire omits the field rather than
sending `0`, so a card for a brand-new player draws neither row and is a correct card. **The run
of form is never padded**: three squares means three counted results and the gap is the honest
statement, which is also why an outcome this build cannot read takes the **whole field** with it
at the mapper — its length is a claim, so a run half-read is a run that cannot be drawn, and
_Counted_ beside it goes on printing. A win is `ink` and a loss `muted`, 3,24:1 apart and both
clear of the ground, derived in `recordSquares.test.ts` — a **lightness** step, so the row reads
with no hue perception; and because a square carries no word, the whole run reaches a listener as
one counted clause — _3 of the last 5 won_, against the run's own length — rather than as five
elements read like a table. **The stake pair is singles only**, keyed off the feature's one seat-count boundary —
`isDoubles`, which moved from `builderPresentation` to `domain/lineup` when a rule rather than a
sentence became its second reader — and never a new flag, because _a win against one named person
isn't a thing that exists until the other three seats are known_ — a refusal to draw rather than an absence, since the server prices
the pairing anyway; in for fun the field never crosses at all. That rule is `domain/atStake.ts`'s
and the component is handed a pair or nothing. **`COMPETITIVE_CARD_DRAWS` gained `RELIABILITY`**
the day the block printed, so `Player Score {score}` stops being a reason line on that card and
stays one on the other two — and §5's _the competitive card can never run out of reasons_ is
re-checked in the test rather than re-read, because the surviving set is one term smaller.

**The card's border is coral never and green once**: a coral outline on every card is
5.1's pressed state made permanent and stays refused, while the lifted card takes 5.1's new
**marked** state in `voltStroke` — volt's meaning at a stroke's ratio, because volt itself is
1,25:1 on `surface` and would be no border at all. It is bound to **the tag being drawn** rather
than to `inclusion_reason`, so the outline can never appear on a handle saying something else,
and Part 13 is discharged by the word either way. Every ratio is derived in `Tag.test.tsx`.

**The court is one drawn object and two feature components.** `Court` (7.12) takes a Sport and
a box, draws the ground, the chrome and the seat **positions**, and **takes children in seat
order** — a `useCourtGeometry` hook was refused, because geometry that is _returned_ gets
adjusted at one call site and not the other. Over it, `CourtMini` draws read-only faces and
`CourtBuild` draws pressable seats, and they are **two components rather than a flag**: they
share every number and no behaviour. **The coordinates cannot be derived and H-25 is why** —
squash has no net, so both players stand on the same half and _seat 3_ is not where seat 3 is
in padel. That reaches the rules as well as the drawing: a seat's **side is read off seat
order, never off the picture**, and it **follows you across the net**, because the swap toggle
is _change sides, never seats_. **The seat label is an identifier under a face** — sixty-four
characters of handle in a 46pt seat is about four, so it draws the **first three, hard, with no
ellipsis**, and the level sits beside them on the same line: a caption that told four faces
apart had four characters and spent one of them apologising for a word nobody can go and read
from there. The **sentence and the spoken name stay whole**, which is what keeps ADR-0107
intact: a truncation invents nothing. Under both, `domain/lineup.ts` holds
what somebody could be wrong about — `seatPlaces`, `seatIsLocked` / `seatIsClearable`, and the
**swap truth table**, which is a decision and never a write. `seatLock` is the one spelling of
_why_ a seat is locked, so the **two guard toasts** are its two codes: they are the
replacement's and not the trade's — your own seat and a seat somebody already accepted are both
freely movable across the net — and there is no third, because the clear badge is **not drawn**
where it would be refused. **Volt means one thing per court**: the seat picked for a swap on the
interactive one, and which seat is yours on the read-only one, which never has a selection to
confuse it with. **The clear badge is the one target in this app that cannot reach 44pt** — a
44pt square inset into a 46pt face leaves the seat a two-point border, and a slop grown outward
is never delivered past a parent's bounds, so it is bounded by the seat instead and the conflict
is recorded in `CourtSeat.tsx` rather than papered over.

**Label coverage is a compile error, and the lint rule is the other half.** The `Record`s
keyed by the generated unions already refuse a code with no words, and **every pressable
primitive in `shared/ui/` already refuses to compile without a name** — `accessibilityLabel`
is required on `PressableCard`, `CloseControl` and the photo tiles, and `label` is required
and _is_ the name on `Switch`, `TickBox`, `Button` and `Chip`. But §E6's _"seven `aria-label`s
in the whole file"_ was an **omission**, and no type can see one — so the one shape where the
prop is optional, a raw `Pressable`, is covered by lint: under `features/play/` it carries an
`accessibilityLabel` or hides itself explicitly, enforced by `eslint.config.mjs` and proven
still to fire by `pnpm test:labels`. **The right answer to a new tappable primitive is a
required prop on it**, not a wider selector here. Beside it,
`useCollapsedPresentation()` is **one condition satisfied by either** reduced motion or a
running screen reader: a player may have VoiceOver on and reduced motion off, and a surface
that asked only about motion would run its full animation in front of the one person who gets
none of the craft and all of the latency. **Reduced motion is read once**, by
`ReducedMotionProvider` at the root: a hook per consumer was one OS listener per consumer,
which was right for two overlays and wrong for surfaces mounted for as long as the tab is.

**⚡Play's first screen is _Find a game_, and it holds four facts with four lifetimes.** A
sport and a mode are **process-scoped and never written back**; the week is a **working copy**
seeded from the profile on entry, edited freely, and travelling as `availability_override` and
nowhere else; and the radius is route-local over the profile's. The asymmetry is the wire's:
`RunSearchRequest` carries a sport, a mode and — only where the player improvised one — a week,
and **there is deliberately no radius on it and never will be**, because _a radius supplied by
a phone is a gate evaluated on a lie_. So the slider's only way to mean anything is for the
profile to hold what it shows, which makes running the search **one act over two requests** —
the `PUT` first, and only where the number moved, so a failure there is a search that has not
happened and the retry is the control the player already pressed. **That control is not a
button saying _Search_.** It is **one primary button** at the foot of the form, reading _Build
a doubles_ or _Build a singles_ — named for the **game the Sport plays**, because where a
completed search goes is the builder and a verb naming the machinery left the shape of the
court a surprise one screen later. It arrived as `CourtEntryCard`, a picture of the court at
`size.court.thumb` with the whole card as the control, and both halves are struck: an
illustration was being asked to carry the affordance for the one act on the screen, and then a
drawing of an empty court was saying under the label what _doubles_ says in one word — the
picture read back as a label, which is the argument that had already removed the hot pill and
the sentence beside it. Its wording still branches on the seat count read off `Court`'s own
coordinates, so a squash court is never told to build a four, and the **spoken** name keeps the
arity in full (_Four seats, two a side_) because a listener has no picture and no chip row to
count. It is in the page rather than in `ShellScreen`'s pinned slot, and the prototype's 2pt
coral outline is **still not drawn**, because coral on a card is the pressed state — it arrives
instead as 6.1's fill on a control, where a press has somewhere to go. **A cleared week runs a
search**: an omitted override means _use my profile grid_ and an **empty list** means _I
unticked every cell_, and #247 is what stopped the wire conflating them. _Changed from your
profile_ is a **client comparison made on every tap** — a slot ticked and unticked is not a
changed week — and it is deliberately not `KEEP_THESE_TIMES`, which compares the post-rung grid
a search actually ran on and only the backend can compute. **The prompts ride on the response**,
so _it never blocks_ is arithmetic rather than a rule a screen obeys: by the time there is
anything to ask, the search has already run. The sport chips are drawn only from
`GET /ratings`, which settles `sport_not_rated` by construction, and a sport that is rated and
**undeclared** opens ADR-0094's **one-tap interstitial** — _permanent, not a migration path_ —
off a set difference the screen already holds, before `play_intent_not_declared` refuses rather
than after. Where a finished search **goes** is still not decided there: the builder
([#271](https://github.com/Raketa02/Raketa/issues/271)) owns that, and the record the search
leaves under `searchKeys.detail(id)` is the origin search it reads.

**The wait is a latch over the screen that launched it, bound to the response and floored by
the clock.** `SearchingLatch` is a sibling of the screen root, drawn while `POST /searches` is
in flight and then held for §J6's **minimum** — _so a fast answer does not flash past_.
**`useHeldWait`'s floor runs from the answer, not from the press**, and that is the half that
is easy to get backwards: the thing that must not flash past is the answer, so a search that
took five seconds shows its count for the same beat as one that took fifty milliseconds, where
a press-anchored floor would have spent itself before any real round trip and drawn the number
for no frames at all. Nothing delays a request either way — `the-play-screens.md` §3 licenses
_presentation over a completed answer_ and forbids the server making a search _feel
substantial_. It is a latch rather than a route, so there is **no back, no close and nothing to
press**: the prototype's _no back button and no escape_ was a dead end
because the wait was a 1400 ms timer, and binding it to the request dissolved the dead end
instead of furnishing it. **Two states are not a wait and would otherwise strand a player**: a
refusal has nothing to hold for and ends over the _Search_ control that failed, and a **paused**
mutation is not in flight at all — `networkMode: 'online'` holds it until the connection
returns, so a latch bound to `isPending` alone would bury the amber sentence saying so.
§B14's _live_ count came off a timer **before the response existed**; it is now
`players_in_range` off the answer, and the shape says so — `SearchingStatus.count` is absent
until there is one, so the wait's first phase has a headline and no number it could not have.
That is also §20.11's _the searching region announces the **result** once and never a stage_.
`searchingWait.ts` holds the last split: **a hold is not an animation**, so a collapsed
presentation drops the fill's 550-per-seat **stagger** to zero and **keeps the floor** — which
`motion.hold` had decided in writing before anybody asked, and which two docstrings said the
opposite of until [#269](https://github.com/Raketa02/Raketa/issues/269) put the arithmetic
somewhere a test could read it. Both files sit in `features/play/`, not `shared/`: the two
waits are Play's, the second arrives with the builder, and onboarding's floor is anchored to
the press because it holds a **sentence** to read rather than an answer.

**Play's failure layer is built before its screens, and its posture is two sentences.**
_Nothing in Play background-refetches_ was the first; _**nothing in Play retries without the
player asking**_ is the second, and it lands as `retry: false` beside the ranked list's
`staleTime: Infinity` — the read-back was the one act still inheriting the app's automatic
retry, which put the _Try again_ a player can see roughly thirty-one seconds away. **The
eight-second search timeout the spec asked for is refused, and refusing it is the decision**:
a search is a recording write on a route that is deliberately not idempotent, so giving up at
8 s on a 9 s answer leaves a recorded search nobody read and its retry records a second —
shortening the number manufactures telemetry rather than bounding a wait, and the refusal is
written beside the numbers in `timeouts.ts`. **A retry belongs to the act that failed**, never
to the screen it failed on: `POST /searches` mints a record and `GET /searches/{id}` re-reads
one, so `retryTarget` says which — re-running the search would mint a new id and orphan the
line-up bound to the old one, which `POST /forecasts` answers with `404 search_not_found`, one
code for four cases. **`OfflineBanner` is declined by name** (`docs/architecture.md` Part 11):
a pool held offline is not stale, it _is_ the record, and what breaks offline is the acts
rather than the data — so the sentence is `offlineMessage()` beside `recoveryMessage`, with
exactly two values split on **does this act resume by itself**, rendered inline at the paused
control. **`features/challenges/` alone sets `networkMode: 'always'`**, because a challenge's
answer window is derived _at send_ and the pause would split the tap from the send; the deck
keeps the pause, and the asymmetry is written down at both sites. And **a seat whose player
the live gates no longer admit is marked, never emptied** — a set difference against the rows
the read-back still holds, derived and never stored, with the marked player still in the
forecast and the court stating the fact and never the cause.

**⚡Play's second screen is _Match me_ — one person at a time, two named buttons, and no
swipe.** The gesture was refused **not on cost** — `RadiusSlider` already drags on the
built-in `PanResponder` — but because _Show them again_ was struck, leaving `PASS_SUPPRESS` at
thirty days with nothing that reverses one: a swipe would put the cheapest gesture in the app
on the most durable act in it. **No `react-native-gesture-handler` and no
`react-native-reanimated` are added**, the leaving animation stays a leaving animation, and
`deck.test.tsx` asserts both absences — the second against `package.json`, because that is
where a build session reaching for a swipe reaches first. Answering is **optimistic** so the
next card is already there to receive the focus that moves onto it, and **a refusal puts the
card back**, which is what keeps _a retry belongs to the act_ true here: the retry is the
button that was pressed, and it cannot be if the person is gone. Offline is not a refusal —
the deck **keeps the pause**, because neither a yes nor a pass derives anything from the
moment it lands. **A spent deal is not an empty pool**: ten cards answered deals again with a
new `search_id` and the player never sees it, and only a fresh deal that comes back empty is
an ending — of which there are **two, split on `players_in_range`**, because _widen in You_ is
advice for somebody with nobody in range and an insult to somebody who has answered everybody.
That sentence is gated again by `radius_clamp`, since a player at their own ceiling cannot
give what it asks for. **There is no _Show them again_**; what stands in its place is the pool
description and the count of the player's own outgoing yeses, both already on the wire. The
card in flight is **route-local**; the ids answered are held **inside the deal**, so a deal
replaced mid-flight cannot leave a stale id behind — by construction, never synchronised.

**A mutual now says whether there is a game, and its silence says nothing else**
([ADR-0154](../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md),
[#370](https://github.com/Raketa02/Raketa/issues/370)). The tap answers with the challenge the
two of them have — the one it just opened, or the one an earlier mutual opened that nobody has
finished with — which is what ended a player being told _you both said yes_ and left looking for
a game nobody mentioned. `mutualChallengeToast` names **Chats** and calls the thing nothing at all: a mutual-born court
is `ON` in singles and a side short in doubles, so _your game is on_ and _your game_ are both
wrong for half the sports, while _they are in your Chats now_ is true either way. There is no
deep link because a toast carries no action here and the row is already the door. **`challengeId: null` keeps the older sentence exactly**, down to the
wording it had before the field existed: it is one answer covering _the pair already have a game
being arranged_ and _a gate refused_, the wire does not say which and will not, and drawing the
absence as a state of its own would hand the sender the second — the trace ADR-0095 guarantees a
block never leaves anywhere in any response. `deckPresentation.test.ts` asserts that sentence
**verbatim** and bans the words that would turn it into a report.

**And the deal itself is held, because a second deal is not a second copy of the first.** It was
a `useMutation`, so it died with the route, and the entry deal was an effect guarded by a ref,
which died with it too — so every return to Match me and every return to a chip already dealt
read as _nobody has asked this yet_ and dealt again. That is not a wasted read: `POST /deck`
excludes everybody dealt within the backend's `DEALT_MEMORY`, so each accidental ask **spends
ten more people out of the player's own pool**, and toggling between two chips emptied a deck
nobody had answered a card of — after which the ending said, truthfully, that they had seen
everybody. It is now a query held under `searchKeys.deck(sport, week, under)`, keyed by **the
question rather than the answer**: the sport, the improvised week, and the radius and the
declaration, which the request does not carry but the answer turns on — left out, the deck
answers its own _Widen in You_ with the deal that ran before the widening. Every path that could
mint one unasked is closed by name — `staleTime`/`gcTime: Infinity`, no refetch on focus or
reconnect, `retry: false` and **`retryOnMount: false`**, that last one because an errored query
re-fires on the next mount and a refused deal must not be re-attempted by walking away and back.

**Play's two ways through the tab are one control, and the count on it is the segment's.**
`PlaySegment` is design-system **6.3**, specified since the document was locked and built for
this; its two halves move in opposite directions and that is the decision — _Find a game_ is
an **arrival** and calls the shell's reset, where _Match me_ is an ordinary push. The count is
your **own outstanding yeses**, filtered by the sport on screen so the number labels the deck
it sits above, and it moves on a tap's own response rather than on a refetch. The prototype's
number was people who had waved at _you_, and that number **cannot exist**: an incoming yes
never crosses the wire in either direction. It is the one read in Play that background-
refetches, because the rule against that is about orderings and a count has none — and it is
why the tab bar carries no badge.

**⚡Play's third screen is the builder, and a swap on it is a selection rather than a
request.** A finished search is pushed onto it — _"where a completed search goes"_, which #268
and #269 both declined to decide — and the push happens **when the latch lifts** rather than
when the response lands, because the wait is over the screen that launched it and the court is
what it lifts onto. Three branches fill the court and **two of them are one request**: ⚡ is
`POST /lineups`, and hand-seating somebody and then pressing ⚡ is the same request with
`locked_seats` on it, _"a property of what you send rather than of where you send it"_. The
third is the pool. **⚡'s wait is under the court rather than over it**, and the court **fills
one seat at a time**: `motion.hold.fill`'s `650 plus 550 a seat` was booked to _"the animation
it drives"_ and nothing drove it — the latch covered the screen for the sum and handed back a
court that was already complete — so `SeatingWait` is a block in the page, `seatReveal` lands
the seats in seat order behind it, and **the line-up is committed when the last seat lands
rather than when the response does**. Nothing is delayed either way: the whole answer is in
memory before the first seat appears. The court itself is `size.court.build`, the **fixed**
width at which a seat is the 46pt every rule about a seat is written against, rather than the
content width that made it 81. **⚡ mints a search of its own**, so the line-up re-binds to the
record it just wrote — the four it seated came off _that_ search's rows, and `POST /forecasts` refuses
anybody the cited search never showed. From the first locked seat the engine optimises **for
the group** and `optimised_for` says so, which the court renders in the voice a provisional
figure uses: it is a consequence of an act the player took, said before they discover it.

**Every arrangement crosses, so re-arranging costs nothing and only membership round-trips.**
`ForecastResponse` returns all three pairings of a four, each with its own forecast, and
`domain/forecast.ts` holds the one rule that turns a swap into a selection: **a pairing is who
is beside you**, so trading the two opponents keeps the same arrangement and the same number
and only crossing the net changes either. Which seat is **yours** is `Relationship.SELF`'s
answer rather than an index's — no route serves a searcher their own player id, which is also
why your own seat draws a ring and no face until an answer names you. The **seating** is
route-local and derived: absent means _whatever the current arrangement says_, so an answer
landing seats people with nothing written down, and it is reset by a membership change and by
nothing else. The forecast is read as a **query** even though it is a `POST`, because what
decides that is whether the route records; ⚡'s own answer is written straight into that key,
so a fill costs one request and not two. **No forecast arithmetic runs on the client** and the
check for it is looking for arithmetic: the builder draws no balance bar, because
[7.11](docs/design-system.md#711-the-balance-bar) takes an _advantage_ between two side
strengths and nothing on a line-up serves one. That is also what the forecast card **does not**
say: the prototype's `2,82 · gap 0,00 · 2,82` over a labelled bar is its own arithmetic over
levels it held locally — `SidesSchema` carries seats and no strengths, and the group objective
is never returned — and a _high · medium · low_ pill over `sigma_group` is a client
thresholding an engine number, where `the-words.md` §16 puts `confidence` in exactly one place
and says so. What the card says instead is **what _Even it out_ would buy**: the evenest
arrangement's own percentage, quoted beside the figure. Every arrangement crosses, so that is a
selection like the button under it and not a second forecast.

**The court states its shortfall per seat and routes every remedy to the pool.** The four
`UnfilledReason` codes replace AC-69's _"Only found N"_ with the obstacle for the actual seat,
and the statements are the seats' **own spoken names printed**, so the sentence a listener
hears and the sentence a reader sees cannot drift apart. The ladder is not here and never will
be — it is the pool's, which is the screen every remedy routes to rather than a remedy pointing
nowhere. **A withheld seat is marked rather than emptied**, derived as a set difference against
the rows the record still holds, and the marked player **stays in the forecast**: dropping them
would force a second cause for _provisional_. Such a seat is a **fourth spoken kind** rather
than a player with missing facts — a withheld row carries one field and no card, so there is no
name and no level to read out — and it says the fact and never the cause.

**⚡Play's fourth screen is the pool, and the relaxation ladder is on it and on no other.**
Every thin-result state in the specs pointed the player at a settings screen — _widen the
radius in You_ — because the prototype had no offer to point at. It is struck: pointing
somebody at a settings screen while a **one-tap widening with a true count** sits on the same
screen is the product being unhelpful on purpose, and taking a rung and changing the saved
radius stay deliberately different acts — one search against every future search. **The
`radius_clamp` bit gates the sentence and never the offers**, which is the reading that is easy
to get backwards: it says a widening _hit_ the slider's ceiling, not that the searcher is at
it — the engine clamps such a rung down to 50 km and offers it anyway — so filtering on the bit
would take a real one-tap widening away from exactly the player the ladder was built for. What
it decides is the copy written when nothing is left to offer: the **reach stated as a fact**
rather than an instruction nobody can carry out, because suppressing it would leave a player
staring at a short list with no account of why. **The count is never a delta** — the rows
shown and the people above the floor are two populations, one of which is not even a superset —
and **a rung priced at nobody is a sentence rather than a button**, because a control that
provably returns an empty list is a control lying about being useful. Taking one is
`POST /searches` **citing the offer**, with no widening in the body: the backend reads that off
the offer it made, so the two sides cannot hold different opinions about what a rung was worth.
It **replaces the list**, and what replaces _back_ is a standing statement naming the widening
and the profile it did not touch. **One climb per search screen, and the bound is the
engine's** — a search that took a rung is offered none — so this screen renders what it was
handed and keeps no memory of how far it has climbed.

**The sort row is the server's vocabulary drawn verbatim, and it vanishes when that list is
empty.** At most two chips exist today, `[]` is a tested state, and a hardcoded row of four
would be three-quarters a lie. The non-obvious half is that **the returned order becomes
selectable once the player has left it**: _Best fit_ is withheld precisely when the returned
order already _is_ best-fit order, so a row drawn from `sorts_available` alone would make
_Closest_ a one-way door. **The comparator adds no `+12`** — the interest lift is an admission
the engine already made, and re-applying it client-side would score the wire's own ranking a
second time. The seat-impact line and the _Evenest_ chip are out of scope with it: both read
`would_be_forecast`, which nothing in the backend has ever written. **_Best fit_ is a sort and
never a filter**: it hides nobody below 90, and that is written down because a coral pill at ✦ ≥
90 is a threshold somebody eventually applies to the list.

**Two things reorder or mark the list without touching a number, and a pin is not the `+12`.**
Somebody with a live yes towards the searcher is **pinned to the top of the served order**,
whatever they scored — and drops into their honest place the moment any chip is tapped, tag and
green border travelling with them. That is the distinction `poolOrder`'s module note exists to
keep: a bonus is arithmetic on a published figure, changes what _best_ means silently and
survives every re-sort; a pin changes a **position**, prints the number it was served, says why
on the card it moved, and releases. Beside it, the coral **best match** tag goes on the highest
✦ on screen — one card or none — and it is keyed to **the ordering in force** rather than to a
tapped chip, because `BEST_FIT` is withheld exactly when the served order already is fit order
and most searches therefore have no chip to have tapped. It is hidden under the three orderings
that are about something other than the number, and where both tags fall on one card the green
one wins, which is `candidateTag`'s rule and not the ordering's. **A for-fun pool draws no _best
match_** — the tag sits in the competitive card's identity row and the social card has no slot
beside the handle for one — and those rows are still pinned and still explained. The pin releases
under _Best fit_ as well as the other three, which is the ticket's _default order **only**_
followed to its cost: the chip the row adds back as **the way back** returns fit order without
the pin, and the alternative is a pin that survives a sort, which is what makes a bonus a bonus.

**The pool is where the running forecast is read, and where `provisional` is a sentence.** The
word under the tinted number is §B9's **balance** word, because Part 13 forbids colour alone
and the spec had the two slots the wrong way round; the caveat is the assumption's own sentence
beneath it, and there is no second badge. **The re-read is this screen's act** — the record is
immutable and the gates are live, so arriving here is the one moment a row the product has
since agreed not to show leaves the list and a seat on the court behind it goes blank. It
writes the **whole** record back, origin and court included, because neither crosses on a
read-back. Both card types draw here and **the pool draws one shape twice**; the pending seat
replacement is route-local and needs no clearing rule, because the court pops.

**A search that raised a question asks it on `SH.saveav`, and dismissing it is an answer.**
One sheet for all four prompts, keyed per prompt, with **no string of its own** — the title, the
body, §F2's closer, the suppression sentence and both control names come off the copy deck, so
a fifth prompt fails to compile there rather than drawing an unlabelled button. On Find a game
it is asked **after the latch lifts and before the court is pushed**: the prompts ride on the
search's own response, so _it never blocks_ is arithmetic, and what the sheet stands in front of
is the **court** — the week, the radius and the declaration are all edited on the screen
underneath it. **Four surfaces raise prompts and only that one pushes anywhere.** ⚡ mints a
search of its own, a deal mints one per hand, and taking a rung is `POST /searches` again — so
the builder, the deck and the pool draw the same sheet, each once its own answer has landed,
and on all three it stands in front of something already on screen rather than in front of a
push. **`KEEP_THIS_RADIUS` on the pool is the ladder's own argument finished rather than a
contradiction of it**: ADR-0099 refuses a rung _silently_ becoming a saved radius, and a sheet
naming the number, the profile it has not touched and what _not now_ costs is the opposite of
silent — asked on the one screen where the player can see what the widening bought. None of the
three has a week grid, so `REFRESH_YOUR_TIMES` is **dropped by the use-case before it reaches
any of them**:
asking a question whose only answer is a control that is not on the screen would, since
dismissal is _not now_ and _not now_ suppresses for thirty days, spend the offer on the one
surface that cannot honour it. What that leaves those three is a sheet whose only answer is
_carry on_. **The deck remembers its questions by the sport and the code rather than by the
deal**, because a deal is not a press — the entry deal is an effect and a spent hand deals again
on its own — so a `search_id` key would put _Keep these times?_ in front of a player again every
ten cards; ⚡ and _Search_ are presses, and both key by the search they minted. That memory is
what makes the deck draw the **first unasked** prompt rather than the first one: every later
list starts with the same leading code, so picking `prompts[0]` and _then_ finding it answered
would go silent for the whole visit with a second question standing behind it. One deal still
asks one question — the deal that took an answer is held for exactly that.
**The two answers land in two modules**, which is the shape worth knowing: a _yes_ is a `PUT`
through the route that owns the value — `player_profile`'s week, radius or declaration — and a
_not now_ is `POST /api/v1/prompt-declines`, a durable row about **the question**, keyed by the
prompt and never by the value it quoted. **Dismissal is a decline** — the scrim, the close
control and Android's back gesture all write the row — because walking away from a sheet whose
footer says the search has already run is indistinguishable in intent from pressing _not now_,
and an unanswered question is asked forever on the two prompts whose condition never stops being
true. Two prompts have a **stated absence** and neither is an oversight: `KEEP_THESE_TIMES`
declines into no row, because a grid is a different grid next Tuesday and the route refuses one;
`REFRESH_YOUR_TIMES` accepts into no write, because it carries no value and is only ever raised
on a week the profile already holds — so its _yes_ hands the player back to the grid, which is
the one thing on that screen that can make it true. `KEEP_THESE_TIMES` draws **6.8's diff
variant** of the same grid the screen edits, off the prompt's own payload rather than the
working copy — the engine compares the **post-rung** week — and a cleared one draws as every
profile cell dashed, which is §12's second body as a picture. The week arrives as the joined
codes the event stream stores, which is the one shape `AvailabilitySlotResource` exists to spare
a client, so it is split in `player_profile`'s mappers beside the two spellings that were
already there.

**⚡ becomes a challenge on the court once full, and that is `features/challenges/`.** The seam
is drawn at _the one action in this tab that reaches another person_: the pinned CTA is the
court's own slot **calling** a challenges use-case, and `SH.propose`, the send, the two
re-reads and every sentence any of them writes are that feature's. The pre-send sheet states
the **irreversibility and no duration** — each invited seat carries its own `answer_by` and a
mutual-born challenge has none, so `{window}` was one constant standing in for three sentences
and the pre-send one is discharged by **deletion**; the real deadline is per seat and arrives
the moment after the act. Its closer is two sentences, because _nothing opens until they
accept_ is false for doubles: the first acceptance opens the chat.

**The send is pending, never optimistic, and that dissolves the question rather than answering
it.** Success **replaces the whole stack** with `[Now]` and ends the Play session, so a
rolled-back send would have nowhere to return to — nothing is rolled forward, so nothing needs
rolling back. The control is busy, the stack moves on success only, and the confirmation is the
**toast**, which is the entire report that the one irreversible act in the feature succeeded
because the destination it lands on is a placeholder. That is why it is the single
**interrupting** announcement in the app. **No `Idempotency-Key`:** one open challenge per pair
across sports is a rule that does not expire and a key does, so a duplicate press is made,
read, and refused by the same check that would refuse a stranger's — the rule is the mechanism
and a key beside it would be the weaker of two.

**A refused send is followed by a re-read, never by a payload.** The refusal states the class
of problem and names nobody, because `AppError.details` is untyped, invisible to the backend's
own response fence and ungeneratable against ADR-0006 — so `line_up_no_longer_sendable`
re-reads the **origin search**, whose withheld rows the court already turns into marked seats,
and the open-challenge refusal re-reads the player's **own** challenges for the name. **Neither
re-runs the search:** a re-run mints an id the whole line-up must adopt and can drop a seat
nobody touched, which is H-18's harm arriving through the remedy. The branch is the **code and
never the status** — three refusals share `409` and one of them is about nobody's state.
And when the re-read marks nobody, the court **says so at court level** rather than leaving
somebody refused in front of four seats that all look fine; the pair rule gets the same
treatment when the game in the way is between two invitees, on a list this player cannot read.

**The send is the one act in the app that fails rather than pausing, and the screen says
_wait_.** `networkMode: 'always'` is the mechanism — a challenge's answer window is derived at
send, so a tap deferred to the next reconnect carries a deadline nobody chose — and the closed
button beside `offlineMessage('does-not-resume')` is the courtesy over it, which is Part 11's
own split. `useIsOnline` is what the court reads for that, and it is the one caller.

**The challenge screen is the second state-keyed surface, and it is keyed on a `Standing` rather
than a `GameStanding`** ([#361](https://github.com/Raketa02/Raketa/issues/361),
[ADR-0143](../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)).
A challenge with no acceptance has no game to key a screen on, so there are two of these and not
one. `domain/challengeDetail.ts`'s `challengeArm` folds six standings and two sides into five arms,
and **the sentence, the card block and the controls are three readings of that one fold** — which
is what discharges §2.4's _an affordance is never removed without the space saying what took it_
**by construction** rather than by a rule a component remembers: there is no state in which the
buttons are gone and the standing sentence has not changed. **`ON` has an arm, and the inbox row is
what reaches it** — a completed line-up keeps its row while it is news and every row is a door. The
row draws §13's `ON` sentence too; **no system line** does, because §3.4 refused the one #324 had
given it, so the row is what makes the arm reachable. #324 took the **card** away, not the row
([#390](https://github.com/Raketa02/Raketa/issues/390)).

**The two answers are gated on the seat and never on the side alone.** §2.1's table reads
`AWAITING_ANSWERS · invitee → I'm in · Not this time`, and a padel four where one invitee has
already accepted is **still** `AWAITING_ANSWERS` — that reader is an invitee in the standing that
offers the buttons with an act already spent, which `POST /accept` answers `seat_already_answered`.
So the predicate is _the reader holds a seat and nobody has answered for it_, and **neither button
names a state the act cannot produce**. §13's sentence for that reader is still the one that
assumes they have not answered, which is #339's amendment owed one row up and is filed as
[#389](https://github.com/Raketa02/Raketa/issues/389) rather than invented in a build session.
**`I'm in` replaces the design's _Accept — game on_**: accepting arranges nothing and draws
_Planning_, so the phrase is false the moment it is tapped, and the label is the standing sentence
in the first person.

**Pending, never optimistic — and the reply is the redraw.** Both answer routes return
`ChallengeSchema`, which _is_ the server's derived standing, so `redrawnFrom` folds it onto the
detail the screen holds instead of refetching. **It keeps the card block**, which ADR-0143 §8
settles in as many words — _nothing about accepting changes who those people are_ — and the arm
drops it when the standing leaves the two that draw one, **by that rule and not by a round trip**.
The merge joins seats by position and checks the occupant anyway: a card is a statement about a
**person**, and one carried onto a seat somebody else now holds is the single mistake here nothing
downstream could detect. **The neighbours are invalidated rather than patched** — an accept that
fills the last seat opens a game and a conversation in caches the reply says nothing about — and it
is `challengeKeys.list()` rather than `.all`, because `all` is a prefix that matches the detail
entry too and would send the request the redraw exists to make unnecessary.

**A stale tap is a re-read, not a toast, and there is no new copy for it.** `actRefusal` — named
for the **acts** rather than for the answers, because there are four of them and they refuse the
same three ways — re-reads on every code that means _this challenge is not what the screen thought
it was_: the closed window, the already-answered seat, a withdraw on a court that has some other
end, a withdraw offered to a side the reader is not on, a fill by somebody who has left, and a
challenge that ended under the builder. Every sentence they land on — _Your day ran out_, _You said
no_, _You withdrew this_ — is §13's and already tested; `challenge_not_found` **leaves the screen**,
one code for two cases on purpose; anything else says what it says through this feature's own
table. **Nothing in `challenges` is sent for you later** stays one line at one site:
`CHALLENGE_MUTATION_OPTIONS` covers the send, the two answers, the fill's send and the withdraw, on
the restated test _is this act's meaning fixed by the moment it is tapped?_ Offline draws the
shipped builder pattern exactly — **the controls grey out under one amber note**, not one per
button, with no third value beside `does-not-resume`. And **the offer may expire under the finger,
and it is let to**: the read sits at `staleTime: 0` with the app's focus refetch, because a pinned
pool _is_ the record where a challenge's standing goes false against a clock while you look at it.

**A half-built court is grown by any live member and ended by the organiser alone**
([#362](https://github.com/Raketa02/Raketa/issues/362),
[ADR-0150](../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)).
`LINE_UP_INCOMPLETE` _is not a waiting room_, so its arm is **grow · talk · end** — and the two
permissions differ because the acts do: the commonest half-built court is born of two mutual yeses,
whose "organiser" is only whoever said yes second, and making that tiebreak the only person who can
finish a padel four would leave the other looking at a court they can neither complete nor leave.
_Open the chat_ is the conversation's door and arrives with the ticket that has a room to open.
**⚡ runs the fill and pushes a builder holding a full court and a fresh search**, which is _Find a
game_'s own shape and is what dissolves the _which search_ question: the builder needs neither a
stale `search_id` nor a reconstructed line-up, and _Pick players myself_ works on the first screen
instead of after a mandatory ⚡. **Nothing outbound happens on the press** — the send is a separate
press, on that screen, and it **pops back here**. The ⚡ is **not drawn**, and that is 10.2's own
rule rather than an omission: _the ⚡ is `zap` and never the character_, `Button` has no slot for a
glyph, and §24.3's _decorative and hidden_ is discharged by there being nothing to hide.

**The reader who has left such a court is not a live member, and their row stays anyway.** They get
§13.1's sentence about their **own seat** — _You said no. They are still filling the court._ — and
nothing to press, because the fold reads the seat rather than the side alone. The row is not
filtered away instead: `GET /challenges` is _every challenge you hold a seat in_ and a departed seat
is still a seat, and a vanished row would take the only available explanation with it. **Not because
the pair rule holds them — it released them the moment they left** (#393); what keeps them out of
_this_ court is `already_asked_at`, per aggregate.

**The builder is `features/play`'s existing screen at a second route, and nothing about it is
forked.** `/chats/challenge/[challengeId]/fill` lights the Chats column for free and makes _back_
correct by construction, which is ADR-0149 §9's shape reused — **no `from` parameter**, because the
challenge is stamped on `PlayOrigin` by the fill that minted the record, and the screen reads it
there. It **borrows `playSession`**: one store, one definition of a line-up, no fork of
`domain/lineup.ts`. Its **working week is undefined**, already the legal value meaning _fill against
the profile's grid_, since there was no _Find a game_ on which to improvise one — and `PlayOrigin.week`
became optional for it, with `sameOrigin` refusing to collapse _nobody composed a week_ into _somebody
cleared theirs_. One sentence in that store moved and the important half did not: a session **begins**
when the shell lays the Play stack down **or when a challenge is re-entered from Chats**, and it
still **ends in exactly one place**. Nothing in the flow calls `resetShellStack` — `landOnNow`'s
_there is nothing left to be behind_ is false where the thing behind is the challenge you were
completing, and it is the surface that draws the result.

**The fill names the challenge and says nothing else about the court**, which is a second shape of
one request rather than a second route: `sport`, `mode` and `locked_seats` are read off the
challenge and **refused** beside it, so `LineupAsk` is a union and all three are unspellable rather
than optional. The record it mints is stamped with the mode **the engine resolved**, read off the
envelope, because a mutual-born challenge has none of its own — and a line-up answer carrying no
mode is refused rather than bound to one this client invented. It carries **no prompts**: the four
are about the searcher's own _Find a game_ values, this journey composes none of them, and a
dismissal spends the offer for thirty days on the one surface that cannot honour it. The pool it
opens draws **no ladder** for the same class of reason — taking a rung mints a search that does not
complete the challenge, so the gate would exclude the very people sitting on the court.

**An accepted seat is not a control, and `BuildSeat.accepted` finally has a producer.** No clear
badge, no press, no pool — swapping is the only thing that works on it, which **draws** _an
acceptance is to the game, not to the side_ rather than writing it. The truth table gained a
`NOTHING` arm and `courtPresentation` **lost a sentence**: _{Name} already accepted — they keep
their place_ was copy for a state nothing could reach, and the ticket that made it reachable decided
the other way, on #324's _no copy, no pill, no disabled control_. **_Start over_ is absent** on such
a court — not disabled, and not redefined to mean _empty it to these two_, which would be a second
meaning for one label. The send is `POST /challenges/{id}/seats`, the send's shape minus the mint,
and the pre-send sheet lists **only the people being asked**: somebody who accepted is not an
invitee and may not be removed. Its cache effect is an **invalidation rather than a redraw**, which
is the one place it differs from the two answers — the reply carries no `read_at`, and the fresh
deadlines it creates would otherwise be stated against the instant the screen was opened.

**The withdraw is the second irreversible act in this app that reaches other people, and it takes
the first one's shape.** `WithdrawSheet` is `SH.propose`'s: a real modal with hidden siblings and
Android back, a title naming the **moment** rather than the act, a dismissal named by what it does,
and **focus landing on the title rather than on the first action** — that action is the destructive
one, and landing focus there would make the worst outcome the cheapest to trigger. Its second body
line is what earns it: the conversation is **destroyed, not delisted**, so the Chats list is
**invalidated rather than patched** and what people wrote is gone. It is pending never optimistic,
it fails offline like every other act here, and the visible control says `Withdraw` while its
accessible name says `Withdraw this challenge` — 6.9's _names which photo it removes_, one surface
over.

**The card block is a fourth card over the same parts kit, and `challenges` spells its own
schema.** Narrower than a `PlayerCard` by ADR-0143 §5 — no social tags, no run of form, no counted
games, no photo verdict, no liveness, no inclusion reason — so `ChallengeCard` is a fourth
composition rather than a `surface` prop on one of the three. It is drawn in `AWAITING_ANSWERS` and
`LINE_UP_INCOMPLETE` and **per seat as well as per challenge**: somebody who declined or lapsed
inside a court that is still open gets none, because _that person is a stranger to you once more
the moment they leave_. **Four things the design draws that it does not** — no bio, which is a
refusal ADR-0143 holds is **stronger** here than where it was written because an invitee was put in
front of somebody without asking; **no _Why?_ affordance**, so the card is one accessibility element
with no action of its own; **no countdown**, the deadline being stated from the response's own
`read_at`; and the **Player Score as a segment that disappears** rather than a row reading
`Score 0`. Its drawn set is `LEVEL_FIT · DISTANCE · RELIABILITY`, and **`PREDICTED_BALANCE` is
deliberately not in it**: the court's forecast is the _screen's_ line drawn once, because the same
figure rides on every card, so a balance row here would print it once per seat.

**The evidence is mapped a second time, and that is the decision rather than the debt.** The wire
carries `Court…` schemas beside Play's because the backend spelled a second, narrower contract, so
a client mapping them through `candidateMappers` would be reading a shape it was not sent — and the
two are free to diverge, which is the point. What is **not** duplicated is the vocabulary or the
words: `challengeDetailMappers` narrows against Play's own lists and produces Play's own domain
objects, so a term or an evidence variant added to the contract reaches both features at once and
the only thing spelled twice is the field renaming, which is what a mapper is.

**`SH.whyfit` is the one surface allowed to draw a term row, and the row count is derived.**
One component taking `(candidate, envelope)` and reading no global state, which is what lets
it **name no mode on the deck**: deriving one from the declared intent would be the engine's
resolution rule rewritten in TypeScript. Five zones — term rows, the sub-total, the
adjustments, what else moved you here, and a footer — with the not-counted block beneath the
rows and their total. **A stood-down term is not a term row**: four of a row's five cells
would be empty, so the live terms are rows and the rest are a list, each line pairing the term
with **whose gap** it was; the platform's own gap is stated **once, in the footer**, or
reliability's line prints identically on twenty cards. **Concerns are marked in place** rather
than gathered, because every concern's term is guaranteed to be a row already drawn and a
summary block would restate a value the sheet has just rendered. The column **adds up on
screen**: contributions are apportioned by largest remainder against the printed sub-total, so
seven rows rounded independently cannot miss it, and `applied` is derived as `fit −
Σcontributions` because the modifier rows carry pre-budget entry points and **nothing sums
that list**. The versions in the footer are not decoration: the read-back never recomputes, so
a month-old record is today's build drawing an older ruleset. **A row this build cannot read
is kept, and the gap lands in place** — an unknown `Term` takes the row's label, an unknown
evidence variant takes the slot where the reason line goes, and the three numbers stand,
because they are numbers rather than codes. Dropping one is not a shorter list, it is a wrong
number: its contribution would reappear under _the engine adjusted it_ as an adjustment nobody
made. What **is** dropped is what no screen totals — a tag with no words, a liveness code, a
concern that could not be joined to a row.

**Two gaps were found while building the deck. One is still open; the other was argued and
closed.** The searcher's **own area code** is served by no route — `area_code` crosses on the
candidate and on the distance evidence, and both are theirs — so `SearchEnvelope.myAreaCode` is
optional and absent, and the meta line drops its one licensed clause and keeps its kilometres
([#279](https://github.com/Raketa02/Raketa/issues/279)). The other was `PlayIntentSurface`, a
closed four with **no deck value**, which had the declaration interstitial reporting
`SEARCH_SWITCH` from both Play surfaces —
[#280](https://github.com/Raketa02/Raketa/issues/280) widened it to a closed **five** with
`DECK`, so `declaredOn` is now a required prop on the interstitial, typed as the two Play
surfaces alone because the other three are other screens' to write — **spelled, not `Extract`d
off the generated union**, since transport does not reach `components/` and the `mutate` call
already fails the build if the contract drops a member. It widened rather than renaming `SEARCH_SWITCH` to a `PLAY_SWITCH` true of
both surfaces: the code is stored verbatim on the backend's `PlayIntentDeclared` and read back
as itself, so a rename is an event migration bought on a field nothing branches on.

`src/shared/ui/` holds the design-system primitives built so far — the cards, note, row,
hairline, button, tag, chip, bar, header, the overlays and drawn objects the result screen
needed (bottom sheet, popover, level bar, confidence ring), the photo tile with its
generated court poster, the availability grid and the radius slider, the tick box with
the tick both it and the grid draw, and the **tab bar** — five columns with ⚡Play raised at
the centre, drawn from one Feather family
([ADR-0135](../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)), which is
why `@expo/vector-icons` is **declared** in `package.json` rather than inherited through
`expo`: the app's primary navigation renders through it, and an SDK bump could move or drop
it with no signal in this app's own manifest. Play's five arrivals join them — the **switch**
(6.12), the **fit pill** (7.10), the **balance bar** (7.11), the **court** (7.12) and the
availability grid's **diff variant** — plus Now's one, the **rail's dots** (7.18), which are what a
paging rail has **instead** of a peek rather than decoration hanging off one: they track the
scroll, they are not pressable on 7.9's own `hitSlop` arithmetic, they carry the state in **width**
as well as tone, and they say nothing at all, because the rail's count is on the heading above
them. **None of them reclaims a deleted section number**,
because a number in `docs/design-system.md` never moves: the fit badge and the balance bar
went with their engines in the reset and come back at 7.10 and 7.11, leaving 7.1 and 7.2
empty. With them, 9.2's **toast** is built: the queue, the live region and the dismiss,
mounted **once** at 9.3's overlay host in `src/app/_layout.tsx`, over
`src/shared/store/toast.store.ts`. Part 13's announcement requirement gains its **queued**
variant there, with the send confirmation as the one message that still interrupts. 7.3's
**meter** joins them with the accessibility contract, and it is `Bar`'s opposite: a bar states
a fraction and reports one through `accessibilityValue`, where a meter visualises a number the
row beside it already printed — so it takes **no label and no value at all**, and
`progressbar` appears nowhere in Play. The **text field** (6.13) closes the oldest gap of the
lot: the app shipped four boxes on the two auth screens with no primitive under them, and
`AuthField` — geometry, focus border, error rendering and a reveal — lived in `features/auth/`
until the chat map needed a field twice more. It is **one control in two shapes**, a single line
capped by `maxLength` and one that grows an `rlValue` line at a time to a **cap the caller sets**,
because neither growing surface has been drawn on a phone and a number here is written only for
what a device drew — five lines for the composer, which is the first caller to have needed one.
**Auth moved onto it in the same commit and `AuthField` is gone** — a
primitive introduced without moving its existing caller is a second implementation, not a shared
one. Its `labelHidden` arrived with the composer exactly as 6.13 said it would: a box under a
header naming the people and the sport, with `Send` beside it, wants **the name without the
drawing**, and the name stays required either way because a listener has none of that around them.
Beside it, 10.3 gained a **lead** slot for the conversation header's faces — `right`'s counterpart
at the other end, and a slot rather than a `faces` prop because a header that knew what a face was
would be the design system owning an avatar, which #338 §5 refused by name. The rest arrive with
the features that need them. **Build outward from the structure below** rather than reaching
for `create-expo-app` — its default template contradicts ADR-0009 — and copy the shape of
`src/features/auth/` or `src/features/onboarding/` rather than inventing a second one.

**Copy `.env.example` → `.env.local` before the first run.** `EXPO_PUBLIC_API_URL` and
`EXPO_PUBLIC_ENV` are both required and validated once at launch by
`src/shared/config/env.ts`. A missing or malformed value stops the app on a startup screen
naming it — that is the guardrail working, not a bug.

`EXPO_PUBLIC_ENV` is `local | development | staging | production`, the same four the
backend uses, and **only `local` runs today.** The environment fixes the
API URL's scheme — `https://` for the three deployed ones, either for `local` — so a
laptop URL under a deployed name fails at launch naming both variables rather than
shipping a build that points at nothing.

**`app.config.ts` is a function of that environment**, not a static document — it replaced
`app.json`. It holds no logic of its own: `src/shared/config/appIdentity.ts` is a pure
table mapping each environment to the app's display name and its badge, and the config
document calls it. Outside `production` the app is named for its environment and wears an
amber badge over every screen; `production` is bare and unbadged. There is **one**
installable variant — one bundle identifier, one URL scheme, no build profiles — until a
second backend exists to point a second one at.

Expo evaluates that document in **Node**, before Metro, so it reads `process.env`
directly and refuses an unknown environment rather than defaulting to one. It registers
sucrase's TS require hook first, because Node cannot otherwise `require` the `.ts`
identity module — delete that line and `npx expo start` fails on a missing module.

**Dependency versions target Expo SDK 52.** Expo pins React Native and its own packages
tightly, so after changing dependencies run `npx expo install --check` and trust Expo's
resolution over the pins in `package.json`. That pin is why `eslint.config.mjs` reaches
`eslint-config-expo` through `FlatCompat`: its flat config ships from v9, which belongs to
SDK 53.

**`.npmrc` sets `node-linker=hoisted`.** Metro and jest-expo decide what still needs
transforming with `node_modules/(?!…)` allowlists, and pnpm's default symlinked layout
defeats them — React Native ships untranspiled Flow, so the first casualty is `jest`
failing to parse `error-guard.js`. Hoisting is Expo's documented answer; it changes nothing
architectural, and this app shares no packages with any other app — a rule that outlives
the club console it was written against.

Archivo (400–800) and IBM Plex Mono (400–600) are loaded with `expo-font` and **awaited
before the splash screen hides** — a font that arrives late reflows every number on screen.
They are imported **file by file**: each `@expo-google-fonts` index `require`s every weight
and italic it ships, and Metro does not tree-shake, so importing one name costs 4,2 MB
instead of 1,0 MB.

## Commands

```bash
pnpm start        # Expo dev server (press i / a for simulator)
pnpm ios / android
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Jest (jest-expo)
pnpm test:boundaries   # drive ESLint at code breaking each module ban; it must go red
pnpm test:labels       # drive ESLint at an unnamed Pressable in Play; it must go red
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.player.json
pnpm doctor       # npx expo-doctor — checks dependency/SDK agreement
pnpm check        # lint + format + typecheck + test + boundaries + labels — the local gate
```

**You cannot see the screen.** If a change is visual, say so and ask for a look rather than
asserting it renders correctly.

## Safety — never without an explicit request

- **Ask for a background location.** Foreground only, permanently: a stream of positions
  collected while the player is elsewhere is a movement trail, which is not what anybody
  agreed to. `app.config.ts` disables it on both platforms and two tests assert the
  absence.
- **Store credentials anywhere but the OS keychain.** Tokens live in `expo-secure-store`,
  reached only through `src/shared/lib/auth`. **Never** `AsyncStorage` (unencrypted
  plaintext on device), never a module variable that outlives a session, never a log line.
  _(ESLint blocks the AsyncStorage import.)_
- **Put a secret in `app.config.ts` `extra`, or in any `EXPO_PUBLIC_*` variable.** Everything in
  the bundle is readable from a shipped app. Those are **config**, not secrets. A secret a
  mobile client "needs" is a design error — it belongs behind the backend.
- **Run a build or release** (`eas build|submit|update`, `expo publish`). _(hook-enforced)_
- **Create or edit a real `.env*` file.** Edit `.env.example`. _(hook-enforced)_
- **Import from `src/generated/` outside a feature's `api/` or `mappers/` layer** — with one
  file's exemption, `shared/lib/platform/liveStream.ts`, which is the live channel's `api/`
  layer and has no feature to live in (ADR-0147 §7).
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put business rules in screens or hooks.** Rules live in `domain/` + `use-cases/`.
- **Call `fetch` outside `src/shared/lib/http`,** or add a second networking path.
- **Copy server data into Zustand.** TanStack Query owns every backend-derived value.
- **Retry a mutation** unless the endpoint is idempotent, takes an idempotency key, or is
  explicitly safe to repeat. Booking and payment calls are exactly where a silent retry
  charges someone twice.
- **Trust a deep-link, push or route param.** Validate with Zod before use.
- **Write a literal colour, font size, spacing or radius in a component.** Every value comes
  from `src/shared/ui/theme.ts`.
- **Add a dependency that owns styling** — NativeWind, styled-components, Unistyles,
  Restyle, a component kit. The system is a typed theme + `StyleSheet.create`
  ([ADR-0012](../docs/adr/0012-player-app-design-system.md)).
- **Commit `android/` or `ios/`.** They are `expo prebuild` output, not source.

## Architecture

Full contract: [`docs/architecture.md`](docs/architecture.md). **Every feature carries the
full layer set**, so an agent applies one rule rather than judging per feature.

```
src/
  app/                      expo-router screens (thin). File-based routing.
    _layout.tsx             root providers + the bootstrap gate
    (public)/ (auth)/ (app)/(tabs)/
  features/<feature>/
    domain/                 entities + value objects + rules (pure TS, no RN/fetch)
    use-cases/              one fn per workflow; orchestrates domain + ports
    api/                    calls FastAPI directly; speaks wire types
    mappers/                wire DTO <-> domain object
    schemas/  components/  hooks/  store/ (optional)
    types.ts                the feature's public surface
  shared/
    ui/                     theme.ts (THE source of every value) + primitives
    lib/  http/ auth/ query-client/ bootstrap/ platform/ observability/
    config/ errors/ store/
  generated/                openapi-typescript output — raw wire types ONLY
```

The per-layer contract is in [`src/features/_template/README.md`](src/features/_template/README.md).
Copy that folder to start a feature.

Rules to preserve:

- **Dependencies point inward:** `app/ → components/ → hooks/ → use-cases/ → domain/`.
  `domain/` imports nothing from React Native, Expo, `fetch` or `generated/`.
- **The wire boundary is `api/` + `mappers/`.** ESLint enforces it.
- **`src/shared/lib/auth` is the single chokepoint for credentials.** No feature, screen or
  hook imports `expo-secure-store`. One module owning the keychain is what makes token
  lifetime auditable.
- **Each platform port is the single chokepoint for its capability.** Only
  `platform/location.ts` may import `expo-location`, only `platform/imagePicking.ts`
  may import `expo-image-picker`, and only `platform/liveStream.ts` may import
  `react-native-sse` — one file each, not the platform directory, so a module
  of ports cannot become a device bucket. Nothing else: not a feature, not a screen, not a
  test. Depend on `LocationPort` / `ImagePickingPort` / `LiveStreamPort` and drive the fakes in
  `src/test-support/platform.ts`. ESLint enforces all three and `pnpm test:boundaries` proves the
  rules still fire. `platform/liveStream.ts` is also **the one file outside `api/` and
  `mappers/` that may read `src/generated/`**: ADR-0147 §7 requires the live envelope to be
  the generated type and a stream body is not a response model, so it is that route's `api/`
  layer with nowhere else to live — the exemption is one file and two bans wide, and
  `pnpm test:boundaries` asserts both.
- **`src/shared/lib/http` is the only place `fetch` is configured** — and the only place the
  401 → refresh → retry rotation lives.
- **`shared/` never imports a feature,** and a feature never deep-imports another — go
  through its `types.ts`. But **do not move code to `shared/` because two files use it**;
  keep it local until cross-feature ownership is proven.
- **No global `services/`, `utils/`, `types/` or `hooks/` bucket.** A capability is one
  directory; utilities get semantic homes (`formatting/`, `date/`, `currency/`).
- **Uniform-strict escape hatch:** where a feature genuinely has no business rule, its
  `use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the folders
  for predictability, but **do not invent fake invariants to fill them.**

### One owner per kind of state

| State                     | Owner                                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Anything from the backend | **TanStack Query** — never mirrored into a store                                                                                 |
| A live frame's roster     | React state in the hook that follows the channel — not a query, not a store: it is the frame, and it is dropped with the channel |
| Access + refresh tokens   | `shared/lib/auth` → `expo-secure-store` (+ in-memory mirror)                                                                     |
| Logged-in / out           | `SessionStatus`: `bootstrapping \| authenticated \| unauthenticated`                                                             |
| Local component state     | `useState` / `useReducer`                                                                                                        |
| Shared ephemeral UI state | Zustand, **feature-scoped first**                                                                                                |
| Form input                | The form + one Zod schema                                                                                                        |
| Navigation                | expo-router — a route param is not app state                                                                                     |
| Config                    | `shared/config/env.ts`, Zod-validated at startup                                                                                 |

Reach for Zustand last: component-local → feature store → app-wide store, and only with a
reason. Zustand never holds API entities, tokens, a backend cache, or a global loading flag.

### Session, bootstrap and routing

Model bootstrap as a **state**, never as `user === undefined` — that ambiguity is what
produces a login-screen flash while valid credentials are still being read out of the
keychain, and an authenticated-tree flash before a redirect.

`shared/lib/bootstrap` runs one ordered sequence: error reporting → validate config → wire
focus/online managers → read SecureStore → restore/validate session → hide splash → render.
Nothing renders a route tree before it resolves.

Expo Router's declarative protected routes landed **after SDK 52**, so the guard is a
redirect in `(app)/_layout.tsx` keyed on `SessionStatus`. Route groups exist so the
authorization boundary is visible in the file tree.

iOS Keychain data can survive a reinstall, so **a token existing is not proof a session
exists** — bootstrap validates it.

### Why there is no BFF here

A browser client would route everything through a server-side BFF with httpOnly cookies —
the club console did, before it was removed in the 2026-08-25 reset. This app
does not, and that is deliberate: a native app has no cookie jar and no shared-origin
browser context, so the equivalent protection is the **OS keychain**
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry by adding a proxy, and don't reach for a cookie session here.

## Mobile gotchas that bite once

- **`localhost` on a device is the device.** A physical phone needs a LAN IP or tunnel in
  `EXPO_PUBLIC_API_URL`.
- **Old app versions live on real phones for months.** Treat backend contract changes as
  breaking unless additive — you cannot force everyone to update.
- **`fetch` has no default timeout.** Timeouts are centralized in `shared/lib/http` as
  classes (request/upload/download/background) — no millisecond literal in a feature.
- **`android/` and `ios/` are `expo prebuild` output.** Native config goes through
  `app.config.ts` and config plugins; a hand edit is lost on the next prebuild.
- **Never log a token, an `Authorization` header, a password or a full payload.**

## Git & domain language

Conventional Commits scoped `player`: `feat(player): court search filters`. Run `pnpm check`
before pushing. **Contract drift fails the build:** this app's CI job regenerates from
`backend/openapi.player.json` with the `openapi-typescript` its own lockfile pins, and diffs
— commit the regenerated `src/generated/`. It is **not** part of `pnpm check`, so a local
gate can be green while CI is not. The job also runs on a backend-only pull request, because
its paths filter watches that document alongside `frontend_player/**`. Before opening a
PR, walk the Definition of Done in
[`docs/architecture.md` Part 20](docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).

Player-app technical vocabulary: [`CONTEXT.md`](CONTEXT.md). New domain concepts use the
shared glossary's vocabulary ([`../CONTEXT.md`](../CONTEXT.md)) — a `Court` is a `Court`, not
a Venue or Facility.
