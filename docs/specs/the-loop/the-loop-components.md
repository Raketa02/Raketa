# The loop components

**Where the seams fall across the two new contexts, what each one owns, and which of them the
design system is entitled to.**

Produced by [Write the screen specs](https://github.com/Raketa02/Raketa/issues/339) on the map
[Closing the loop](https://github.com/Raketa02/Raketa/issues/321), as the counterpart of
[`the-play-components.md`](../matchmaking/the-play-components.md) for the surfaces this map builds.

That file's opening line binds here unchanged:
[`the-words.md`](../matchmaking/the-words.md) §20.1 decides the **accessibility tree**, this file
decides the **React component tree**, *"and they are independent: a card may be one element built
from six components, or six elements built from one."*

> **This decides seams, not composition.** What each surface *draws* is
> [`the-loop-screens.md`](the-loop-screens.md); what it *says* is
> [`the-words.md`](../matchmaking/the-words.md); what it *looks like* is the design system. What is
> here is where one component stops and the next begins, and who owns each number.

---

## 0. What #338 already settled, and is not re-opened

[What returns to the design system, and at what numbers](https://github.com/Raketa02/Raketa/issues/338)
answered ownership for everything on this map and wrote a number only for what a device drew. Its
governing rule is quoted rather than restated, because it is also this file's:

> **Item 1 and item 3 are answered for everything on the list; item 2 — the number — is written
> only for what a prototype drew.** Each chat-screen build ticket carries its own design-system
> amendment.

| | Owner | Number |
| --- | --- | --- |
| Card rail, full-width variant | design system | **7.7 amended** |
| The rail's dots | design system | **7.18, new** |
| Display sans role | design system | **3.3 amended** |
| `TagProps.dot` | design system | **6.4 amended** — the dot is the sport's; urgency is a variant |
| The row stripe | design system | **5.x amended** — `amber`, and §1.2 does not grow |
| The tab badge | design system | **10.2 amended**, §1.2's sixth entry |
| Section heading | design system | **3.3 amended** — `eyebrow`, and `h2` loses *section* |
| Empty state | design system | **10.1 amended** — one rule, promoted out of a docstring |
| Text field | design system | **new Part 6 number, owed** — arrives with the composer |
| The avatar | **refused** — photograph or poster; `courtPosterFor` moves to `shared/ui` | — |
| The struck state card | **never returns** | — |
| Bubble · system line · composer · chips · plan card · game card · challenge row · conversation row · the state-detail screen | `features/*` | — |

**The rule that decides which side of the line something falls on is `the-play-components.md`
§1's**, and this map produced no case that strains it:

> **The design system holds drawn objects and control vocabulary — the things where two
> independent implementations would drift *on a number*. A feature holds every composition that
> names a domain noun.**

---

## 1. Two new features, and the arrow between them

[ADR-0146](../../adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) made the chat
**two** bounded contexts, and the client mirrors them:
`features/conversations/` and `features/plans/`. The reason is a lifecycle fact rather than a
preference — **a conversation exists without a plan**, so one module would carry a nullable half its
own lifecycle contradicts.

[ADR-0149](../../adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) fixes
the only arrow this map adds between features, and it is **one-way**:

> **`features/plans` may import `features/games`, and `features/games` never learns a plan
> exists.**

That is the client half of
[ADR-0145](../../adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md) §4's
*"`games` importing the Plan is what breaks it"*, and stating it one-way makes it **a grep rather
than a judgement**. The consequences run through the whole tree:

| | Lives in | Because |
| --- | --- | --- |
| The Now rail and its cards | **`features/plans`** | a card is keyed on the plan's filled slots and the clock, so it needs both |
| The card **ladder** — which of the four rungs a game is on | **`features/plans/domain/`** | it reads a plan; `games` may not |
| The game screen | **`features/games`** | it is `ResultScreen` grown, and the result argument is still most of it |
| The plan **on** the game screen | **`features/plans`, as a child** | `Court`'s own shape one folder over: the parent hands down a slot, the child fills it |

**The game screen taking the plan as a child is what keeps the arrow one-way with a screen that
needs both.** `features/games` renders a slot it knows nothing about; whoever composes the route
puts a `features/plans` component in it. Neither type crosses.

---

## 2. `features/conversations/`

```
features/conversations/
  api/            conversationsApi.ts
  domain/         entry.ts  membership.ts  liveState.ts
  components/     ConversationScreen.tsx
                  Bubble.tsx  SystemLine.tsx        ← two components, never one
                  Composer.tsx  QuickChips.tsx
                  DaySeparator.tsx
                  conversationPresentation.ts       ← every code-to-sentence table
  hooks/          conversationKeys.ts  useConversations.ts  useLiveConversation.ts
  mappers/        conversationMappers.ts  wireVocabulary.ts
  use-cases/      readConversations.ts  readConversation.ts  sendMessage.ts
```

### 2.1 The bubble and the system line are two components

**Not one component with a `kind` branch.** ADR-0146 decided a system line is *not* a Message with a
`kind` on the wire, and
[ADR-0148](../../adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md) made
them a **discriminated union** there. One component with a branch re-introduces at the surface
exactly the shape the wire was built to refuse — and the branch would carry a text field real for
one arm and meaningless for the other, which is the failure ADR-0022 names.

They also share nothing worth sharing. A bubble is a constrained-width block with an author, a side
and a background; a system line is `tiny` in `muted`, centred, full width, **no element and no token
— it is type** (#338 §7).

**The author label is the bubble's and it is conditional**: drawn only where the conversation has
more than two members, and always the **whole handle**. The condition is a fact about the
conversation, so it is a prop from the screen and never a read inside the component — the same rule
`the-play-components.md` §3 states about `sportName`.

**One presentation module for both**, `conversationPresentation.ts`, keyed by the system-line code
union. §1's mechanism and no other: **code → message, never message → message**, with a
`Readonly<Record<Code, string>>` for the codes that quote nothing and one function per code that
quotes a value.

### 2.2 The last entry is rendered by the same two components the stream uses

The Chats conversation row draws `last_entry`, which is one of the same two shapes. **It renders
through the same module, not a second copy** — a row that formatted a system line its own way is the
drift a shared presentation module exists to prevent, and it would be found the first time a code
gained a value.

What the row does differently is a **prop, not a fork**: one line, tail-truncated, no author label,
no bubble. That is `CandidatePhoto`'s precedent — *"one component at three sizes"*.

### 2.3 `domain/` against `components/`

`the-play-components.md` §7 drew the line once and it is not redrawn:

> **A rule somebody could be *wrong* about goes to `domain/`. A table mapping a value to the words
> this app chose for it goes to `components/`.**

| `features/conversations/domain/` | Falsifier |
| --- | --- |
| `entry.ts` — the discriminated union, `(conversation_id, seq)` as identity, the day-separator rule over the platform zone | two people in one room seeing different separators |
| `membership.ts` — derived from whichever record the room is currently about; who may be named in a `{name}` slot | a line naming somebody who is not a member |
| `liveState.ts` — the three-way *live · not live · held* the screen draws, folded from the stream port and the account state | a not-live line on a cold open, before any connect attempt has failed |

**`liveState.ts` is `domain/` and that is the load-bearing placement.** It is a rule somebody can be
wrong about — ADR-0147's *drawn only in the foreground, and only after a failure* is exactly the
kind of condition that gets quietly dropped in a component — and it is the seam that keeps
`react-native-sse` out of a screen. The screen reads a state; the port is
`shared/lib/platform/`'s, with its fake in `src/test-support/platform.ts`.

### 2.4 The live channel invalidates, and the Query cache stays the single copy

ADR-0147 §5, and it is the posture `architecture.md` Part 7 already takes for mutations. **There is
no second store for a conversation**, and *nothing in Play background-refetches* is a **scope
clarification rather than an exception**: that rule is written about ranked lists and the harm of a
pool reordering under a finger, and a conversation is append-ordered, so there is no ordering to
lose.

**One stream per open conversation, and never a second stream for the Chats list.** ADR-0147's
*never build* list, restated here because a build session looking at a live tab will reach for one.

---

## 3. `features/plans/`

```
features/plans/
  api/            plansApi.ts
  domain/         slots.ts  agreedPoint.ts  ladder.ts
  components/     PlanCard.tsx          ← Chips, in the conversation
                  PlanTags.tsx          ← Tags, on the game screen
                  DayChips.tsx  HourChips.tsx  WhereField.tsx
                  NowRail.tsx  GameCard.tsx
                  planPresentation.ts
  hooks/          planKeys.ts  usePlans.ts
  mappers/        planMappers.ts
  use-cases/      readPlans.ts  setPlace.ts  setDay.ts  setHour.ts
```

### 3.1 The plan is drawn twice, in two primitives, and that is not a variant

**`Chip`s where it is edited — the conversation and, since
[#414](https://github.com/Raketa02/Raketa/issues/414), the game screen's two plan-lead rungs —
and `Tag`s on the score lead, where it is read** (#338 §7; ADR-0149 §4 as amended). *A pressable
pill is a chip*, *tags are never pressable* — the vocabulary doing exactly what it was split to do.
The editable card is **one component on both surfaces** (`PlanCard`), with a `note` slot the game
screen fills with the panel and the room leaves empty.

**Two components rather than one with an `editable` prop**, on `the-play-components.md` §3's own
reasoning about `CourtMini` and `CourtBuild`: *"read-only avatars and interactive seats are
different children, not a flag on one component."* Here the difference is larger — one takes three
mutations and three input surfaces, the other takes none.

**What they share is the slot vocabulary, and it is `domain/`**: which slots exist, their order,
which are filled, and how each value is spelled. `slots.ts` is the one place `where · day · hour` is
an order.

### 3.2 Three writes, three use-cases, one per slot

`PUT /plans/{game_id}/place` · `/day` · `/hour`, because ADR-0144 has **three events**. **A write of
the value already there records nothing and answers `200`** — the server's rule, and the client
neither pre-empts it nor optimistically renders it.

**No optimistic write.** A slot change writes a system line other people read, and *pending, never
optimistic* is this map's rule for everything that reaches another person. The chip shows pending;
the line arrives through the stream like any other entry.

### 3.3 The ladder is `domain/`, and it is the one thing that must not drift

```ts
// features/plans/domain/ladder.ts — five rungs, read in order
1. a seat is open                          → Needs a player
2. the agreed point exists and has passed  → Needs result
3. the agreed day is today                 → Today
4. all three slots filled                  → Game on
5. otherwise                               → Planning
```

**Read in order, and the clock outranks the checklist** (ADR-0145 §3). Rungs 4 and 5 are reached
only when the point has not passed and the day is not today, so #329's *"and the agreed moment
still ahead"* is implied by the ladder rather than restated in a row. **And the open seat outranks
the clock** ([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md),
#411 rule 5, built by [#418](https://github.com/Raketa02/Raketa/issues/418)): `rungOf` reads the
court — the seats and the instant off the games list, `CourtRead` — before it reads the plan,
because a seat somebody left is a fact about the court and the game cannot be played or recorded
until somebody is in it. Nothing on the wire names the rung; `player_id: null` is the whole of
what it says, and this is the one place it is read against the plan. `momentHasPassed` is the
second rung's own test, exported for the one control drawn only while the moment is ahead.

**The agreed point is `domain/` beside it**, and it is the value #324 and #329 each keyed a rule on
without the two ever being checked against each other: **the agreed instant when day and hour are
both recorded, the start of the following local day when only the day is, nothing when no day is.**
Later rather than earlier, so nobody is asked for a result before they could have played.

**It folds against `games`' `read_at` and never against the phone's clock, and never against a
`read_at` of its own** — `GET /plans` deliberately carries none (ADR-0148). A plan folds nothing
against the clock, so there is no instant for it to have been folded against, and **Now has one
clock by construction** rather than by a rule anyone remembers.

**This is the single most drift-prone thing on the map**: five card names, two tickets that each
keyed a rule on it, and one amendment already spent closing the hole between them. It is one
function, it is `domain/`, and every surface reads it — the rail, the card and its tables, and the
game screen's arm.

### 3.4 The Now rail is `features/plans`', and the game screen is `features/games`'

#338 §7's last row and ADR-0149's arrow, together. **The rail and the card are compositions naming
domain nouns**, so they are the feature's; what the design system owes them is 7.7's full-width
variant and 7.18's dots, and nothing else.

**The card is handed `(game, plan | undefined)` and no global state** —
`the-play-components.md` §3's rule verbatim, including its clarification: what the sentence refuses
is a component reaching for a store, never a screen handing down a fact it already holds. The join
is the screen's, over two lists.

---

## 4. `features/challenges/` grows a screen, and one seam moves

`the-play-components.md` §8 placed four surfaces against *the one action in this tab that reaches
another person*. **Its table is a row short and one of its rows now has a second consumer.**

| | Owner | Change |
| --- | --- | --- |
| `GET /challenges` | `features/challenges/` | **it finally has a consumer** — two, in fact: the Chats list and the tab badge, sharing `challengeKeys.list()` |
| **`GET /challenges/{id}`** | `features/challenges/` | **new** — the challenge screen's own read |
| **The challenge screen** | `features/challenges/` | **new** — five standings and the sixth, two sides, the two answers |
| **The withdraw sheet** | `features/challenges/` | **new** — `SH.propose`'s shape, a second time |
| **⚡ Fill the seats** | `features/challenges/` — the control; `features/play/` — the act | §4.2 |
| The card block on the challenge screen | **`features/challenges/`** | §4.3 |

### 4.1 The badge's prop, and why the bar reads no hook

`challengesWaiting?: number` on `TabBar`, decided whole by
[#326](https://github.com/Raketa02/Raketa/issues/326) §10 and recorded here because it is a seam:

- **The bar reading a hook is out on architecture before taste.** `shared/ui` importing a feature
  hook inverts the dependency ([ADR-0009](../../adr/0009-feature-first-clean-architecture-frontends.md)),
  and it would give *"the drawn object only"* a network call.
- **A generic `badges?: Partial<Record<TabBarKey, number>>` is the glyph argument in a new
  costume.** A caller that can badge any tab can badge You; the badge inventory is fixed at one for
  the same reason the glyph inventory is fixed at five.

**The shell mounts the query**, and #227's *"the shell remembers nothing"* is amended rather than
quietly contradicted. That is the honest price of a count on permanent chrome.

### 4.2 The builder is `features/play`'s screen at a second route

**One screen component, two routes** — `/play/builder` and
`/chats/challenge/[challengeId]/fill` — which is ADR-0149 §9's shape reused, so each route lights
its own column and *back* is correct by construction.

**It borrows `playSession`** rather than keeping a route-local line-up: one store, one definition of
a line-up, **no fork of `domain/lineup.ts`**. Its working week is **undefined**, already the legal
value meaning *fill against the profile's grid* and the right one, since there was no *Find a game*
on which to improvise a week.

**One sentence in that store moves and the important half does not**: the session begins when the
shell lays the Play stack down **or when a challenge is re-entered from Chats**, and it still ends
in exactly one place.

**The control is `challenges`' and the act is `play`'s**, which is `the-play-components.md` §8's
own line about the card's primary button read from the other end: the challenge screen owns the
label and the placement, and it calls a `play` use-case.

### 4.3 The card block is `challenges`', not `play`'s, and the schema says so

`origins.py` already made this call on the backend and wrote the argument — *"deliberately a second
spelling… `challenges` may not import `matchmaking`, so the alternative to two spellings is the
matcher owning the vocabulary of the context that was built to take it off him."* **The client
inherits the split**: the challenge screen's card is `challenges`' components over `challenges`'
narrower schema, and `features/play`'s three candidate cards are untouched.

**They do share the parts kit's smallest members through `shared/`**, and only those:
`CandidatePhoto`'s photograph-or-poster switch, `playerName()`, and §B16's number formatters — all
three already promoted or promoted by this map (§5).

**A fourth candidate card is not created.** The challenge screen draws one person at a time on a
screen, not a row in a list, and `the-play-components.md` §3's *three components over one parts kit*
is an argument about three renderings of one list — it does not extend to a detail screen with no
list behind it.

---

## 5. What moves to `shared/`

**One promotion, on `recoveryMessage.ts`'s own stated third-caller rule** — *"Auth and onboarding
each held a copy of this table, and the second one recorded the rule: a third copy is the signal to
move it."*

- **`courtPosterFor()` → `shared/ui`.** It hashes a player id to a hue and a pose, and it lives in
  `features/player_profile/` saying *"Determinism is this feature's"* while `features/play` already
  imports it across a feature boundary. **One person being two colours on two screens is precisely
  the drift the seam rule exists for**, and this map brings the third and fourth callers: the Chats
  rows and the conversation header. #338 §5.

**And one thing that does not move.** `PLAN_HORIZON` stays in `games/domain/windows.py` and `plans`
imports it. ADR-0022 governs constant homes and the obvious move is a kernel promotion; the reason
not to is ADR-0145's interlock — *the clamp and `ENTRY_GRACE` interlock so that every plannable day
leaves at least twenty-four hours* — **two numbers whose relationship is the argument**. The
direction is permitted: the check is that `games` must not import the Plan, and this is the reverse.

---

## 6. The renames, and the broken link

Three mechanical changes on shipped, tested surfaces, each of which is a build-ticket row rather
than a decision — recorded here so they land with the code that makes them necessary.

| | From | To | Why |
| --- | --- | --- | --- |
| 1 | `ResultScreen` | **`GameScreen`** | it grows three plan arms and stops being about the result alone; `GAME_ROUTE`'s docblock stops calling it *"the result conversation for one game"* |
| 2 | `games/domain/conversation.ts` | named for what it **folds** | **two things called *conversation* in one codebase is how somebody eventually subscribes the wrong one.** `games` uses the word for the result argument, whose terms are Proposal, Correction, Counter and Acceptance; ADR-0146 gave the glossary word to the aggregate that needs it |
| 3 | `sendOptions.ts` / `SEND_MUTATION_OPTIONS` | named off the send | the override is now feature-wide across four acts, and a constant named for one caller with four is the same defect as a token nothing draws |

**And two broken ADR citations, one fixed here and one for the build ticket.**
[#332](https://github.com/Raketa02/Raketa/issues/332) found that `gamePresentation.ts` cites
`docs/adr/0022-wire-codes-never-sentences.md`, which does not exist — ADR-0022 is
[`0022-kernel-negative-space-and-constant-homes.md`](../../adr/0022-kernel-negative-space-and-constant-homes.md).
Writing §22–§24 turned up **a second instance of the same defect**, in
[`the-words.md`](../matchmaking/the-words.md) itself: it cited
`docs/adr/0021-client-derived-state.md`, which is
[`0021-kernel-in-backend-clients-derive-by-comparison.md`](../../adr/0021-kernel-in-backend-clients-derive-by-comparison.md).
**That one is fixed**, because it is in a document this ticket was editing anyway; the code one is
still #340's, one line.

**Both are the same failure and it is worth naming**: an ADR cited by a filename somebody
*remembered* rather than one they opened. A record's number is stable and its slug is not, so a
citation that resolves is the only kind worth having.

**`standingLine`'s `LINE_UP_INCOMPLETE` arm is a fix rather than a rename**, and it is the one of
the four that is *wrong* today: it counts *"still to answer"* in the one standing where `standing_of`
guarantees nothing is, so `{m}` is structurally zero and the line reads *"2 in, 0 still to
answer."* It takes `open` instead — **a field that could only ever be zero is what let the sentence
be wrong**, which is the fix worth having. Shipped and tested; safe only because no screen calls it
yet.

---

## 7. What this hands the build

| To | What |
| --- | --- |
| [#340](https://github.com/Raketa02/Raketa/issues/340) — client | Two new features, `conversations` and `plans`, and the one-way arrow between `plans` and `games` as a lint-checkable rule |
| #340 — client | §6's three renames, `standingLine`'s fix, and the broken ADR link |
| #340 — client | `courtPosterFor()` to `shared/ui` (§5) |
| #340 — design system | #338's six Part 16 amendments and 7.18, `design-system.md` and `theme.ts` in one commit (15.3) — plus **one amendment per chat-screen build ticket**, which is #338 §1's stated price |
| #340 — design system | The **text field**, at a new Part 6 number, arriving with the composer, **with auth refactored onto it in the same change** |

## 8. What this file does not decide

- **What each surface draws** — [`the-loop-screens.md`](the-loop-screens.md).
- **What each surface says, and what each control announces** —
  [`the-words.md`](../matchmaking/the-words.md) §20 and §22–§24. Independent of this tree by
  §20.1's own statement.
- **Any number in the design system.** Ownership is decided above; the numbers arrive through
  [15.1](../../../frontend_player/docs/design-system.md#151-adding-a-component) and Part 16 rows,
  and only for what a device has drawn.
- **The bubble's own geometry** — max width, tail, the two backgrounds. It has never been drawn on
  a phone; #338 §1 is explicit that its number comes with the build ticket that draws it.
- **`conversations`' and `plans`' internal client vocabulary** — the store names, the query-key
  shapes. [#228](https://github.com/Raketa02/Raketa/issues/228) deliberately left `play`'s to the
  build ticket that created the stores, and this file leaves these there rather than starting a
  second half.
