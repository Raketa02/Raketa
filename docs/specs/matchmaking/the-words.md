# The words

Nothing the platform sends is prose. What crosses is codes — a system line, a game's standing,
a booking's status, a `SocialTag` — and **the app writes the words for all of them**
([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md),
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).

This file is that deck. It is the artifact the build tickets cite by section, and the
artifact a later copy edit is made against — so that §F1's voice can be checked against
itself in one place rather than a dozen.

Decided by
[Every sentence the client writes from a code](https://github.com/Raketa02/Raketa/issues/234).

> **It is the whole player app's deck, and it lives here for historical reasons rather than scope ones.**
> It stays in `matchmaking/` because a dozen documents and as many docstrings cite it by relative
> path, and a move would break every one of them with no path left to repair it. **The Classic
> play loop's sections were removed on 2026-10-06
> ([#569](https://github.com/Raketa02/Raketa/issues/569))** — the candidate cards, the searches,
> challenges, plans, the Chats tab and the radar — and their numbers are kept: each such heading
> stands over one line saying what it held, so a code citation of a § still lands somewhere
> readable.

> **§F1 rule 6's *no Rakieta* has one exception, from
> [ADR-0187](../../adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
> §8 (2026-09-25).** Wherever a Play › Groups, club website or public site mock sentence names the
> app (*"Join Ogrody 33 Club on Raketa: <link>"*), the app is named, and it is named **Raketa**.
> Everywhere else the rule stands. Those surfaces' mocks are in
> [`../play-groups/`](../play-groups/README.md).

---

## 1. Where the copy lives

**This client already answered this, four times, and the answer is written down.**
`authErrorMessage.ts`: *"Localization goes **code → message**, never message → message.
The backend's `message` is a diagnostic written for a log; rendering it directly ships
English into every locale and lets a copy edit on the server change what an app already
installed says. So the copy lives here, chosen by the stable code."*
`socialTagPresentation.ts`: *"The ids are the platform's and the labels are this app's…
The three tables are exhaustive by type."*

So: feature-local `*Presentation.ts` and `*Copy.ts` modules, one per **vocabulary owner**
rather than per screen — every surface that says a vocabulary reads the same table.

**The owner is the vocabulary, not the feature.** `conversationPresentation.ts` holds the room's
words and §23's system lines; `gamePresentation.ts` a game's, and §25's pairing;
`recordPresentation.ts` the record sheet's; `shellCopy.ts` and `youCopy.ts` the tabs' own lines;
and what two features say alike — tags, the week, balance, seat places, the acts' verbs — sits in
`shared/vocabulary/`. Nothing about the rule changes — a module per vocabulary owner is what it
always said, and one feature was simply all there was.

**Two shapes, and the split is whether the sentence quotes a value.**

| Shape | For | Why |
| --- | --- | --- |
| `Readonly<Record<Code, string>>` | every code with no payload | Keyed by the generated union, so a missing key is a **compile error** — ADR-0106's *"a compiler says so"* |
| one function per code | every code whose sentence quotes a value | A sentence **over** its values cannot live in a flat table — eight of §23's nine system lines quote at least a name, so each is a function keyed by the same union |

**Three tables Play could not re-type.** `SocialTagId`, `DayPart` and `Weekday` already shipped
in `player_profile`. Play was their **third** caller, which is `recoveryMessage.ts`'s own
stated trigger — *"Auth and onboarding each held a copy of this table, and the second one
recorded the rule: a third copy is the signal to move it"* — so they were **promoted to
`shared/`**, not copied and not re-worded.

## 2. Mode — three places, and nowhere else

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): where a search's mode was worded.*

## 3. An unknown code

`tsconfig.json` sets **`noUncheckedIndexedAccess: true`**, so `TABLE[code]` is already
`string | undefined`. ADR-0106 §6's gap branch is **forced by the compiler**, not remembered.
What is left to decide is only what it says, and where a drop is legal instead.

**The rule, testable:** *a code renders a named gap wherever the screen states a count or a
total its row belongs to; everywhere else it is dropped.*

That is ADR-0106 §6's own argument — *"the player sees a Fit of 78 explained by
contributions that sum to 61"* — generalised by what it was protecting rather than by the
word *evidence*.

Today a system line (§23) and a game's standing draw the gap — each **is** the whole of its
line — and a clause that keys no total is dropped: the sentence under a game's forecast figure
(§25), the kind on an eyebrow (§22.2). The placements Classic play drew — the whyfit rows, a
modifier, an unfilled seat, a challenge's standing, a card's reason lines and tags — went with
it ([#569](https://github.com/Raketa02/Raketa/issues/569)).

**The gap's words, one string, everywhere:**

> **This app is too old to read this one — update Raketa.**

It names neither the code nor the vocabulary. A raw `SOCIAL_VIBE` is a wire token in a
player's face; *"an unknown evidence kind"* is a sentence about our schema. And one string
rather than five, because a per-placement wording is five sentences that must all stay true
of one condition.

> This is deliberately **not** the shape `evidencePresentation.ts` uses, and the difference
> is the rule above. There, an unreadable direction *"draws no mark at all, rather than a
> default one"* — because the mark is decoration over a row whose content came from the
> server, and *"the row still shows what the category said."* Here the code often **is** the
> content.

## 4. What a reason line may say

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a reason line's register. The rule below stayed.*

**Counted phrases route through one pluralisation helper.** §J4's gap — *every counted phrase
must route through proper plural handling before any further market* — is the map's fog, not
this file's; what this file owes is that no string here hardcodes an `s`.

## 5. The de-duplication filter, per surface

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the reason-line filter, per card.*

### 5a. The competitive card stopped arguing, so its filter has nothing to filter

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the competitive card's lost reason lines.*

### When nothing survives

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the reason row's fallback.*

## 6. The eight terms

### 6.1 Labels — the whyfit row heads

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the whyfit row heads.*

### 6.2 Reason lines — one renderer per evidence variant

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a reason line per evidence variant. The format below stayed.*

Levels use §B16's format throughout: two decimals, decimal comma, U+2212 minus, em dash for
an absent one.

### 6.3 `area_code` is not a word, and no card may print one

**`area_code` is a coordinate string** — `A+050612+0019938` — and `areas.py` refuses to make
it a name, in writing:

> *"the human-readable area a player card prints has no producer in this repository yet, and
> deriving one there would be inventing a naming scheme nobody has calibrated. **That refusal
> stands.**"*

The module licenses exactly one client sentence from it, and that one is honest:

> *"A card saying **they are in your area** is a comparison the client makes between two
> codes, which is exactly the shape [ADR-0021](../../adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
> licenses a client to compute."*

So the line a client writes from them is **`{km} km`**, with **`In your area · {km} km`** when
the two codes are equal — the record header's identity line, now the cards are gone. Nothing
else. The day a gazetteer exists, `area_code_of` is the one function that changes and this line
gains a name without any other consumer moving.

### 6.4 The level row — three facts, and the word the prototype spent on the wrong one

§B11 and §B12 draw the row as `"{level} · band {low}–{high}"`, where `{low}–{high}` is
`2,55–2,87`. **That is not a band.** The four bands are New 1,0–1,5 · Developing 1,6–2,6 ·
Established 2,7–3,8 · Advanced 3,9–5,0; `2,55–2,87` is the **likely range**, μ ± σ. The
prototype spent the domain's word on a different concept, and a reader who has seen the band
names anywhere else in the app reads the pair as the band's own edges — which is exactly what
`Band`'s docstring forbids: *"a card can never name a band that disagrees with the number
beside it."*

So the range carries a word of its own, and the band keeps its name:

> `{level} · {band} · likely {low}–{high}`   — e.g. `2,71 · Established · likely 2,55–2,87`

*Fact · mechanism*, §F1 rule 4's shape: the level and its plain-language meaning, then the
caveat. Levels use §B16's format on all three numbers — two decimals, decimal comma.

**No card draws this row since Classic play went**
([#569](https://github.com/Raketa02/Raketa/issues/569)), and the word outlived it: the record's
skill card draws the range as a bracket under the level bar and says it `Likely {low}–{high}`
(`likelyRangeLine`).

## 7. Concerns

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the concern sentences.*

## 8. A term that stood down

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a stood-down term's sentences.*

## 9. Modifiers

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the modifier sentences.*

## 10. Why this person is on the list

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the liveness and inclusion tags.*

## 11. An empty seat, and why this four

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): an empty seat's and a four's reasons.*

## 12. The four prompts

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the four search prompts.*

### The two answers, and the third way of giving one of them

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the prompts' answer buttons.*

## 13. A challenge's standing — seven codes, and an ended row names who

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a challenge's standing sentences.*

### 13.1 The third reading — an invitee who has left a challenge that has not

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a departed invitee's sentences.*

### 13.2 The same reading, one row up — an invitee who has answered a challenge still awaiting others

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): an answered invitee's sentences.*

## 14. Deadlines — "24 h" is not a string

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a challenge's deadline sentences.*

## 15. Names

> **Rewritten 2026-11-03 by [ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md)**, which supersedes
> [ADR-0171](../../adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md):
> the Name is retired, and the nickname is what is said.

A player is known in Raketa by one thing: their **Nickname**, a unique handle of **2–64
characters** from `[A-Za-z0-9_.-]`, which they chose and can change at any time. **The nickname is what every
sentence says, and it is never written with an @**: *ania.k put a score up*, *Hi ania.k*, a card
that draws **ania.k** large with nothing under it. ADR-0107 §4's rule reads on it: *every sentence
naming somebody uses the whole handle or names nobody — the prototype's `split(' ')[0]` has nothing
behind it here, and inventing a first name is the product addressing a person by a name they
never gave it.* Nothing cuts a first name out of *ania.k*.

> **One `playerName()`: the nickname, whole, and `You` for yourself.** Every sentence, toast,
> notice, spoken name and email that names somebody goes through it. Nothing — no sentence, row,
> card, sheet, toast, seat label or spoken name — puts an `@` in front of it.

**The result screens name a person only where a person acted**
([ADR-0141](../../adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). A games seat
carries a nickname and nothing else about its occupant, so the row's eyebrow says *who you
played* — the fact that tells two padel games in a week apart, where a duration cannot — and two
sentences name somebody: *{nickname} put a score up* and *{nickname} agreed with your score*.
**The two columns of a score stay sides.** A score is a **side's** claim, capped one per side and
answerable by either of the two who played it, so a column headed with a nickname would charge a
doubles score to one of them and a listener reading a set cell by cell would hear the wrong
person's six.

**A seat label may truncate visually; a sentence may not, and a spoken name never does.**
ADR-0107's rule is against *inventing* a familiar form — a visual truncation invents nothing,
and the accessible name carries the whole nickname, which is where the rule actually bites. A list
truncates by dropping whole nicknames (*laia.q +2*), never by shortening one; where a box draws
the **stem** (ADR-0157) it is cut at the nickname's first dot, so *diego.f* draws *diego* there;
what a box does past that, its own ellipsis, is that box's business. **The two initials over a
generated poster are the one derived form** —
[ADR-0167](../../adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §3's
exception, cut from the nickname: its first character, then the first character after its first
`.`, `_` or `-`, else its second (*ania.k* → `AK`, *kuba* → `KU`, *dorota_w* → `DW`), its fence
unchanged.

**`{list}` — a list inside a sentence — is joined with commas and a final *and***, and nothing
is dropped: `where and the hour`, `where, the day and the hour` on the checklist that first
wrote it (§22.6, gone with Classic play), and every list a sentence or a spoken name says since —
the typists in a room, the people marked as not coming, the two sides of a forecast. One join,
in `sentenceList.ts`.

> **Elsewhere in this file, and in every spec, a player is named as the day it was written spelled
> them.** A `tomek.p` is a seeded handle from before ADR-0171; *Diego Fabregat* or *Oscar Bertran*
> is a name from ADR-0171's two months. Both read as nicknames now — *oscar.b left your game* —
> and every rule those sections cite is this one, unchanged by the word.

**§B16's side-name formatter is redrawn, not kept.** *"You + Marek"* is a layout that assumed
short words; at 64 characters the 46px seat is the binding constraint (§G5 already lists the
overflow at *first-name* length) and it decides the formatter rather than the other way
round. The unknown player stays a question mark.

## 16. The searching states

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the searching states and the whyfit header.*

## 17. Windows, rungs and sorts

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): windows, rungs, sorts and the forecast's caveat. `GameResult` below stayed.*

**`GameResult`** — the run of form. The field crossed with
[#306](https://github.com/Raketa02/Raketa/issues/306) and nothing drew it;
[#312](https://github.com/Raketa02/Raketa/issues/312) drew it on the competitive card and
[#373](https://github.com/Raketa02/Raketa/issues/373) on the record sheet, and **neither code has
a sentence of its own — on purpose.**

| | |
| --- | --- |
| `WIN` | *no sentence: a square in `ink`, and one share of the count below* |
| `LOSS` | *no sentence: a square in `muted`, and one share of the same count* |

**The row is drawn as five marks and spoken as one clause**, and both halves refuse the same
thing. On the drawing it is outcomes in order, oldest to newest, distinguished by a **lightness
step** and never by a word — a square carries no label, and both squares are drawn. To a listener the whole row is `{won} of the last
{n} won` (`lastFiveReading`), because five clauses would read the row as a table and no clause at all would
leave Part 13's *never colour alone* failing in the register it was written for. **A per-code
sentence would be the thing both registers avoid**, so this table stays what it is: the codes
are exhaustive, and their words are the count they are counted into.

**Fewer than five is a real answer** and is never padded — three results are three squares, the
gap is the statement, and `{n}` is the run's **own** length rather than 5. **There is no date
beside any of them** — a moment here would be activity recency, which no card carries in any
shape (ADR-0106 §5).

## 18. Cited, not written

| Vocabulary | Where its words already are |
| --- | --- |
| `SocialTag` (19) | `socialTagPresentation.ts` — label, name and emoji, **promoted to `shared/`** (§1) |
| `DayPart` (3), weekday (7) | `availabilityPresentation.ts`, **promoted to `shared/`** (§1) |
| Levels, distances, percentages, money, clock times | §B16 and §F1 rule 8 — one shape each, already fixed |
| Balance word and tone | §B9 |
| Error codes | `authErrorMessage.ts` and `shared/errors/recoveryMessage.ts` |

## 19. What this file does not decide

- **Pluralisation and Polish-market copy.** §J4's gap; the map's fog. What is owed here is
  that no string hardcodes an `s`.
- **Anything on an out-of-scope surface** — the record sheets, *Show them again*, the
  seat-impact line, at-stake, Player Score's strands, languages. A code with no surface gets
  no words, and the map's Out of scope is the list.

**And four more, added with §22–§24 by [#339](https://github.com/Raketa02/Raketa/issues/339):**

- **How a hold ends.** §22.5 gives this app its first hold sentence and nothing else; there is no
  appeal surface in this build, and a sentence offering one would be a promise nobody made.
- **Anything a reply would say.** Replies are on the map's fog — a question about a *message's
  shape*, not about delivery, since ADR-0147 made every entry ride one sequence.
- **The unread mark inside a conversation.** Out of scope, and whatever it is called it is **not**
  `read_at` — that field is the fold instant and means the opposite.
- **Moderation and reporting.** §5.2 of the source names *a report opened*; nothing here opens one,
  so no code has a sentence.

---

## 20. What each control announces

Decided by
[What each Play control announces](https://github.com/Raketa02/Raketa/issues/236).

> **Paused in part 2026-10-25 by [ADR-0198](../../adr/0198-the-player-app-is-not-built-for-screen-readers-for-now.md).**
> A new control still gets its name, written here. The live regions, the politeness rules and the
> collapse conditions (§20.9–§20.11) are not asked of new work: for now the app is built for
> ordinary touch. What is built stays.

`design-system.md` [Part 13](../../../frontend_player/docs/design-system.md#part-13--accessibility)
is the **requirement** — names on everything tappable, `accessibilityState` on selected
chips, modal semantics on the sheet, an announcement on every toast, and *"never colour as
the only signal."*

It is not the **sentences**, and Part 13's rule is that *"a control's label is its content
**and** its state."* An accessible name is copy — it is localisable, it quotes numbers that
need §B16's formats, and it composes codes whose sentences are already in this file. So it
lives here, through §1's mechanism and no other: **code → message, never message → message.**
A label is never a template inlined in a component.

### 20.1 The rule that decides an element

Part 13's two worked examples disagree on their face and the rule has to reconcile them: the
question navigator is *"one element, one label — never one per segment"*, where the
availability grid is twenty-one elements with the column heads hidden.

> **One accessibility element per action. Everything with no action of its own merges into
> the nearest action above it.**

Actions are what a listener navigates *by*. The navigator has none, so it is one element; a
grid cell is an answer, so there are twenty-one. This is the same rule stated once instead of
twice, and it is the rule §G3's component boundaries were drawn against —
`the-play-components.md` decided the **React component tree**, this
file decides the **accessibility tree**, and they are independent: a card may be one element
built from six components, or six elements built from one.

**The cap is on what precedes an action, not on the label.** A merged label leads with the
identifying facts and continues with the argument; a listener who has heard enough interrupts
and acts. Roughly twenty words before the first action is the bound, and a merged label that
cannot state its subject inside it is evidence the seam is wrong.

### 20.2 The role vocabulary — React Native, not ARIA

§E6 asks for `tablist`, `radiogroup`, `switch`, `progressbar`, `image`, `dialog` and
`status`. React Native's `accessibilityRole` has near-namesakes for most, and its
`accessibilityState` offers only `{disabled, selected, checked, busy, expanded}` — **no
`pressed`**, which §E6 asks for three times.

> **Prefer the role that carries the state; where no role carries it, the label carries it;
> never style alone.**

That is [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid)'s own
argument — *"`checkbox` rather than `button` because the state is the point and the role is
what carries it: 21 buttons announce 21 identical actions, where 21 checkboxes announce 21
answers"* — and [7.9](../../../frontend_player/docs/design-system.md#79-the-question-navigator)'s refusal
of `progressbar` for a control with no max.

### 20.3 The candidate card

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the candidate card's spoken name.*

### 20.4 The court — side and role, never an index

§E6 proposes *"Seat 3, Marek Z., level 2,92. Tap to replace."* **An index is not a place.** A
listener has no picture of the court, and H-25 makes the number mean different things in
different sports — squash puts both players on the same half, so seat 3 is not where seat 3
was. **§E6 rewritten** — the seat and the empty seat both lose their numbers.

| | |
| --- | --- |
| **Court** | A summary element preceding the seats: `{Sport}, {n} of {m} seats filled.` Four seats announced against nothing is four seats a listener cannot place. |
| **Seat, them** | `button`. `{side}, {name}, level {level}` |
| **Seat, you** | `button`. `{side}, you` |
| **Seat, your partner** | `button`. `{side}, {name}, level {level}` |
| **Seat, empty** | `button`. `{side}, empty` |
| **Balance bar** | `image`. §B9's balance word and its figure — the word is the point, since the bar is a colour |

`{side}` is *your side* / *their side*, and in doubles the partner seat says *your side, your
partner*.

### 20.4.1 A seat's hold, and the route that does not need one

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a seated player's why-fit route and the hold on a seat. The label rule below stayed.*

**The 9,5pt seat label does not earn `allowFontScaling={false}`.** Part 13 permits the escape
only *"inside the level bar's drawn geometry"*, and §15 already ruled the court's case the
other way: *"a seat label may truncate visually; a sentence may not, and a spoken name never
does."* The visible label scales and truncates, the spoken one is whole, and nothing is
invented. **This also settles [#240](https://github.com/Raketa02/Raketa/issues/240)'s
truncation question**, which is recorded there rather than held by both.

### 20.5 The deck

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the Players deck's buttons. A group's Games deck kept the stage (`DeckStage`, in `features/proposals`) and the rules below.*

**When a card leaves, two things happen and both are deliberate.** §E3's first finding is that
focus is destroyed on every render and nothing restores it, so today a listener is dropped at
the root with no idea what happened. The toast announces the act; an explicit
`setAccessibilityFocus` moves focus to the incoming card's body. #228 §12 made both actions
optimistic, so the next card is already there to receive it.

**The swipe shipped, and it is never the only path.** VoiceOver and TalkBack consume the drag
before the card sees it, so a swipe-only deck is one a listener cannot answer. The three
buttons are the accessible path and are never removed; the test that pinned *no gesture
dependency* now pins *the buttons remain*.

### 20.6 The sheets — three, not five

Part 13 already locks `accessibilityViewIsModal`, hidden siblings, and focus returned to the
trigger on close. The one thing it leaves open is where focus lands on the way *in*:

> **The title, not the first action — one rule for all of them.**

A sheet's first action is often the one that cannot be undone — *Leave the game* is — and
landing focus on it by default would make the worst outcome the cheapest to trigger.

### 20.7 The availability grid, and the diff variant

The editor is [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid),
reused unchanged and **not restated** — `checkbox`, `checked`, `"Monday morning"`, column
heads hidden. §E6's *"'EVE' should be announced as 'evening'"* is already done there.

### 20.8 Why-fit — the meter is decoration

A metered row draws a label and its figure, **then** a meter — the why-fit row did, and the
record card's strand rows do (`Shows up`, [#385](https://github.com/Raketa02/Raketa/issues/385)).
The number is already text two words earlier.

> **The meter is hidden and the row's words carry it.**

This is [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid)'s
argument again — *"the column heads are therefore decoration to assistive technology and are
hidden from it; without that, every cell is announced twice."* A bar visualising a printed
number is that same double announcement. **§E6 rewritten**: its *"expose it as
a progress indicator with its current, minimum and maximum values"* would publish a precision
the row already states in a shape the row already chose, so **`progressbar` appears nowhere in
this contract.**

### 20.9 The three live regions

All polite. Three were listed here, and the two that were Find a game's — the searching status
and the provisional forecast figure — went with Classic play
([#569](https://github.com/Raketa02/Raketa/issues/569)):

| | |
| --- | --- |
| **The toast layer** | Part 13's requirement, with §20.10's amendment |

### 20.10 Politeness, and the one announcement that interrupts

`AccessibilityInfo.announceForAccessibility` **interrupts** on both platforms, and a toast
landing mid-card cuts a listener off in the middle of what they were listening to. Part 13's
requirement was written against onboarding, which has one toast at a time.

> **`announceForAccessibilityWithOptions` with `queue`.** The requirement survives with its
> mechanism named more precisely — a Part 16 amendment, booked in §20.12, not an exception.

**Nothing interrupts now.** The one announcement that did — the send confirmation, the whole of
what told a player the one irreversible act in Find a game had succeeded — went with Classic play
([#569](https://github.com/Raketa02/Raketa/issues/569)); `interrupting` is still a value the
toast store carries, and no caller sends it.

### 20.11 Two collapse conditions, and one screen rule

`the-play-screens.md` §3 licensed Find a game's fill animation — *"presentation over a completed
answer, and the client may take its time."* That permission is granted to **craft aimed at
sight**. A listener gets none of the craft and all of the latency, in front of an answer already
in memory.

> **`isScreenReaderEnabled` collapses presentation over an answer to its end state, wherever
> reduced motion does.**

It is a *second* condition on the same path as reduced motion, not a second path — a player
may have VoiceOver on and reduced motion off, which is the common case. #239 owns the
reduced-motion collapse; the two share one helper, `useCollapsedPresentation()`.

**Every screen title takes `accessibilityRole="header"`**, and nothing announces a screen
change beyond what the platform already fires. §C records the page header as *not* a shell
region — *"the title scrolls away"* — so the header role is what makes it reachable again,
both readers navigating by heading.

### 20.12 What this section does not write, and what gates it

**One obligation on the design system**, to land with
[#219](https://github.com/Raketa02/Raketa/issues/219)'s outstanding rows so the amendment log
stays in order: **Part 13 — every toast announces, queued rather than interrupting.**

**Two gates**, booked onto [#232](https://github.com/Raketa02/Raketa/issues/232). An
unenforced rule drifts silently, and §E6's *"seven `aria-label`s in the whole file"* is what
that looks like:

- **Label coverage is a compile error, not a test.** §1's `Record` keyed by the generated
  union already gives it: a code with no renderer does not build.
- **A lint rule over `features/games/` and `features/proposals/`** — every `Pressable` carries an
  `accessibilityLabel` or an explicit hide. This is the one that catches the historical failure,
  because the historical failure was an omission and a type cannot see one.

**The lint rule is the one gate here scoped by folder rather than by type**, and its folders
follow the features that draw raw `Pressable`s and own a copy deck to name them from: it began
over `features/play/`, widened with §24, and since Classic play went
([#576](https://github.com/Raketa02/Raketa/issues/576)) it watches `features/games/` and
`features/proposals/`. A rule that watched one feature while others drew controls would be the
guardrail that silently stops matching, which this repo already holds is worse than none.

### 20.13 Cited, not written

| | Where it already is |
| --- | --- |
| The availability grid, in edit mode | [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid) |
| Touch targets — §E4's fourteen under 44pt | [#219](https://github.com/Raketa02/Raketa/issues/219), which found the system stricter |
| Contrast, Dynamic Type, tabular figures, reduced motion | [Part 13](../../../frontend_player/docs/design-system.md#part-13--accessibility) |
| Focus order | §E3 — DOM order matches visual order on every Play screen |
| Numbers, levels, distances, durations | §B16, through §18 |
| Pluralisation | §19 — no string hardcodes an `s`, accessible names included |

## 21. A refused send — two codes, and the naming done elsewhere

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): a refused send's sentences.*

---

## 22. The loop's own sentences

Decided by [Write the screen specs](https://github.com/Raketa02/Raketa/issues/339) on the map
[Closing the loop](https://github.com/Raketa02/Raketa/issues/321). The surfaces were
`the-loop-screens.md`; the sentences are here, because this file
is the app's one copy deck and §1's mechanism is the only one there is.

**The owner is the vocabulary, not the feature** (§1). What is left of this section is held by
`conversationPresentation.ts` (§22.4's box, §22.5), `leaveSheetCopy.ts` (§22.8),
`gamePresentation.ts` (§22.2's eyebrow, §22.9's ending) and the shell's `shellCopy.ts` (§22.7's
empty Home). **Nothing below is a template inlined in a component.**

**Most of this section is short and that is the point.** Every sentence the previous map already
wrote and tested is **cited rather than reproduced**, and the ones that had a home elsewhere stayed
there.

### 22.1 The Chats tab

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the Chats tab's panel, headings and empty states.*

### 22.2 The plan

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the plan — its panel, slots, lock and refusals. The eyebrow below is still in `gamePresentation.ts`, on a lead no route opens since [#576](https://github.com/Raketa02/Raketa/issues/576).*

**The game screen's eyebrow on the plan lead is the format and the kind** — and nothing else
([#414](https://github.com/Raketa02/Raketa/issues/414)):

| Format | Counted | Friendly |
| --- | --- | --- |
| two seats | `SINGLES · COUNTED` | `SINGLES · FRIENDLY` |
| four seats | `DOUBLES · COUNTED` | `DOUBLES · FRIENDLY` |

Stored as words (`Doubles · Counted`) and drawn uppercase by 3.3's rule, so a listener hears words
and not letters. **`COUNTED`, never `COMPETITIVE`** — that is a search's mode (§5.4 #8), and the
design's own forecast sentence says *a counted game*. A kind this build cannot read drops its
clause and the format stands. There is **no title under it**: the card names the people and the
plan names the day, so the handles and *arranged n ago* the other arms' eyebrow carries would be
the same facts twice.

### 22.3 The withdraw — *Remove the challenge*

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the withdraw sheet, Remove the challenge.*

### 22.4 The quick chips

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the quick chips. The box under them stayed.*

**The composer's box says `Message about this game…` while it is empty**
([#402](https://github.com/Raketa02/Raketa/issues/402)). A hint and not a label: it goes the moment
somebody types, so the name a listener gets is `Message` (§24.4) and this is only what the empty
box says. *About this game* because the room is for the whole episode and nothing else
(`the-loop-screens.md` §3).

### 22.5 Not live, held, and somebody is typing

**Three states the records made reachable and left as rules.** ADR-0147 §8 made *not live* honest —
*"a chat that is not live looks not-live"* — ADR-0148 §9 made *held* reachable inside a
conversation, and ADR-0156 built the typing indicator. Each gets one sentence; the first two sit in
a `Note` above the composer and the third sits in the stream (§24.6).

| State | The sentence |
| --- | --- |
| not live | `Not live — you can still send, and anything you missed arrives when it reconnects.` |
| held | `Your account is on hold. You can read here, but not write.` |
| typing, one | `{name} is typing…` |
| typing, more | `{name} and {name} are typing…` · `{n} people are typing…` |
| ended | `This chat has ended.` |

**The ended sentence is the fourth state, and it stands where the composer stood** (added
2026-09-14, [#429](https://github.com/Raketa02/Raketa/issues/429)). A booked game's room ends with
its game, and why is the game's card to say, so the room says only that the chat has ended. It
named who had left, or that nobody else was coming, in Classic play's rooms, which could end
before they had a game. A fact rather than a warning or a refusal, so it is neither amber nor
coral.

**The typing sentences name people and never a count of one**, because the client already holds the
handles the frame's `player_ids` point at and a name is what the room is about. Three or more
collapses to a count on §19's rule rather than growing a list — a room is four people at most and
the reader is never in the list, so the collapse is reached only in a doubles court where everybody
else is typing at once, and *3 people are typing…* is the honest end of that. **The whole handle,
never a first name** (ADR-0107), and the ellipsis is a character rather than three dots so a screen
reader does not read *dot dot dot*.

**It is never about you.** The server filters the reader out of their own room's frame, so there is
no *you are typing* sentence to write and no state in which one could be reached.

**Not live says two things because two things are true**, and only a sentence carries both: sends
are ordinary authenticated `POST`s and the channel is unidirectional by construction, so writing is
unaffected and only reading has stopped being live. A dot could not say that, and Part 13 refuses
colour as the only signal in any case.

**Held names the fact and promises nothing**, because there is no appeal surface in this build and
a sentence offering one would be a promise nobody made. It is ADR-0130's register: state the
class of problem, name nobody, grade nothing.

> **A finding, recorded rather than acted on: this app has never drawn a hold.** `account_held` is
> a backend refusal with no client sentence anywhere, and the two above are the first. Nothing says
> how a hold ends, because nothing in this build can end one.

**One note for every refused control on the screen**, not one per control. It is one fact about the
account, and saying it five times is the failure #326 §6 names about counts.

### 22.6 The card's slots, and the screen's checklist

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the plan card's slots and the checklist; the `{list}` rule is §15's now.*

### 22.7 Now, and the two answers

**Now's empty state** — Home's, since [#550](https://github.com/Raketa02/Raketa/issues/550) —
present-tense, saying what the tab **is** and pointing at the act:

> `Every game you arrange shows up here — what is agreed, what is today, and what still needs a
> score.`
> `⚡ Play finds you one.`

*(2026-11-14, ADR-0204 §1: a player in no group reads §31.1's `Join a group to get games — the
hottest ones are just below.` in place of the second line.)*

**`PLACEHOLDER_COPY.now` dies with it**, and the test moves rather than being deleted.

**The doors**, each carrying its act's verb and each navigating rather than writing:

| Control | Where |
| --- | --- |
| `Open the chat` | a booked game's details — **one act, one spelling**; there it is the spoken name of the `Chat` button |
| `We played` · `Confirm the result` | a booked game's details, each the door to the game's result |

### 22.8 Leaving a game, and the seat it leaves open

**An irreversible act that reaches other people**
([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md), #411
rules 1, 5, 6 and 8, built by [#418](https://github.com/Raketa02/Raketa/issues/418)): a title
naming the **moment**, the act named once on the control that carries it out, a dismissal named by
what it does.

| | |
| --- | --- |
| The control | `Leave the game` — at the foot of a booked game's details ([#557](https://github.com/Raketa02/Raketa/issues/557)), which hands the sheet a body of its own; the three below are the sheet's default |
| In flight | `Leaving…` |
| Sheet title | `Before you leave` |
| Body | `The others keep the game and can fill your seat.` |
| Body | `You can't be asked back into this one.` |
| Body | `This cannot be undone.` |
| The act | `Leave the game` |
| Dismissal | `Stay in` |

**The first body line is the one that earns the sheet**: a departure destroys **nothing** — the
others keep the game and the room — so the line says what survives, and the second says the one
cost that is the leaver's alone.

**The visible control is the whole sentence**, so it is the accessible name too.

### 22.9 Filling the seat, calling it off, and the fourth end

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the seat's door, the call-off sheet and the card's two buttons. The fourth end's words stayed.*

**The ending's words** — the fourth end, drawn as *Never played* is, **and the screen says who**
(amended 2026-09-15,
[ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§8; until then the title was *It was called off* and *nobody is named*, because `called_off_by` was
on no wire):

| | |
| --- | --- |
| The tag | `Called off` |
| The state word | `called off` |
| The standing line | `Called off` |

**The screen's ending block, keyed by how it ended** — a departure, which `called_off_by`
names, or the hour, which names nobody (amended 2026-09-16, [ADR-0175](../../adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §3, §6; the button's row is
retired with the press):

| | Heading | Body |
| --- | --- | --- |
| a departure, singles | `The game was called off for lack of players` | `{name} left, so the singles game is called off. Nobody is marked for it — not you, not them.` |
| a departure, doubles | `The game was called off for lack of players` | `{name} was the last to leave, so the doubles game is called off. Nobody is marked for it — not you, not any of them.` |
| the hour, singles | `The game was called off for lack of players` | `Nobody filled the seat in time, so the singles game is called off. Nobody is marked for it — not you, not them.` |
| the hour, doubles | `The game was called off for lack of players` | `Nobody filled the seat in time, so the doubles game is called off. Nobody is marked for it — not you, not any of them.` |

The body still says what the ghost's says about the strands — the same fact about the same people:
neither an evening nor a game that never happened, so nothing anybody is measured on moves — and
the heading is the shortage's on both, because both are one. `{name}` is `called_off_by`'s
whole nickname (§15).

**One word: called off.** The tag, the headings and every sentence in this section use it;
***cancel* appears nowhere** — not on a control, not in a sentence, not in a code — and *Call
it off* is no longer a control anywhere.

### 22.10 Leaving from the Chats list, and before the court is whole

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): leaving a game from the Chats list.*

## 23. The system lines — the codes, and what publishes nothing

**A system line is a code and its values, never a Message with a `kind`**
([ADR-0146](../../adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)). ADR-0022
decides it rather than taste: one shape forces either a **stored rendered sentence**, which freezes
copy into history so rewriting a line cannot rewrite the backlog, or a text field real for one kind
and meaningless for the other. **Nobody typed *Tomek set the day*.**

**`values` never repeats what the read already resolves.** The line carries `actor_id` and the
client fills `{name}` from the **`people`** beside it — the faces the response resolved for
everybody it names — so a handle correction reaches the whole backlog for free. **Not from the
members alone** ([#408](https://github.com/Raketa02/Raketa/issues/408), ADR-0148 §4 as amended):
membership is the game's line-up, so the person a *seat left* line is
about has by definition just left it, and a client naming off the roster drew `? said no — that
seat is open again`. `members` is still the roster and still the gate; `people` is the roster and
every author and actor the page names, resolved in the same read, and a page carries its own.

| Code | Published by | The sentence |
| --- | --- | --- |
| a seat accepted | `challenges` · `SeatAccepted` | `{name} is in` |
| seats invited | `challenges` · `SeatsInvited` | `{name} asked {n} more` |
| a seat left | `challenges` · `SeatDeclined` \| `SeatLapsed` \| `SeatLeft` | `{name} said no — that seat is open again` · `{name}'s day ran out — that seat is open again` · `{name} left — that seat is open again` |
| the game was played | `games` · `GamePlayed` | `{name} said you played` |
| a place recorded | `plans` | `{name} set the place · {value}` |
| a day recorded | `plans` | `{name} set the day · {value}` |
| an hour recorded | `plans` | `{name} set the time · {value}` |
| the plan was locked | `plans` · `PlanLocked` | `{name} locked the plan` |
| a side was formed | `challenges` · `ChallengeOpenedFromMutualInterest`, **doubles only** | `You two are a side. Fill the seats to find your opponents.` |

**One of the nine is written today**: `GAME_PLAYED`, into a booked game's room. The other eight
were written into rooms a challenge opened, and nothing opens one since Classic play went
([#569](https://github.com/Raketa02/Raketa/issues/569)) — their publishers are gone, and their
sentences stay only so that a stored line still folds.

### 23.1 The events that publish nothing, and why

A builder reading the event list would write a line for each. **Each of these is refused, and the
row says which rule does it.**

| Event | Why nothing |
| --- | --- |
| `GamePlanned` | **the seats already imply it** |
| `games.seat_vacated` · `games.line_up_reseated` | membership reads the game's line-up live rather than being told, so the roster moves the moment either commits — a line for either is not drawn |
| `games.called_off` | it **destroys** the room in the same act, so there is nobody left to read a line — and it still reaches the room, because it is the telling that destroys (ADR-0165 §3) |
| `ResultProposed` · `Corrected` · `Countered` · `Accepted` | `games` has its own conversation for the argument |

**No system line announces a derived standing, and there is no *Game on* line** — the prototype
writes that phrase four different ways. `GamePlanned` is refused on ADR-0142 §3's own test:
**an event may announce a conclusion only when no arrangement of the seats could reach it**, and
everybody having accepted is exactly such an arrangement. What a player sees instead is the
**booked game on Home and its details** — drawn, not announced.

**A refused line is not a refused telling, and here that is load-bearing.** `GamePlanned` still
reaches the room and draws nothing — it is what **opens** a booked game's room — and
`Game.planned_at` **is** `GamePlanned.occurred_at`, which
is where the room's own end is derived from
([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
§2). Dropping the delivery because nothing renders would drop the anchor with it.

**The result argument is refused on scope rather than on implication, and on scope alone.** It is
`games`' and `games` has its own eight-arm conversation for it: one fact in one place, and
ADR-0146's rename argument holds at any lifetime — *"two things called conversation in one codebase
is how somebody eventually subscribes the wrong one."* **The reason used to have a second half**,
that a room dying a day after the agreed point would carry the first two turns of an eight-day
argument and then vanish mid-sentence; that lifetime no longer exists
([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §6),
and the refusal did not move, because it never depended on it.

**`GamePlayed` is the exception and earns it**: it is not the argument, it is the **answer to the
question this room was opened to ask**.

## 24. What each new control announces

§20's rules, applied to the conversation, Home and a booked game's forecast — five surfaces when
this was written, and the Chats tab and the challenge screen went with Classic play. **§20.1's
rule decides the element and §20.2's decides the role**, and both are used rather than restated —
except once, where a stream is a shape neither of §20.1's two worked examples covers.

### 24.1 §20.1 gains its complement: a stream is navigated by its entries

> **One accessibility element per action — and one per entry in an ordered stream.**

§20.1 was written against a card and a grid: *"one accessibility element per action; everything
with no action of its own merges into the nearest action above it."* A conversation's backlog has
**no actions in it at all**, so the rule as written merges an entire history into one element a
listener cannot move through — which is the failure 6.8's own argument names from the other side:
*"21 buttons announce 21 identical actions, where 21 checkboxes announce 21 answers."*

A stream is navigated **by entry**, the way a grid is navigated by cell. The complement is stated
narrowly so it does not reach the card: it applies to an **ordered stream whose entries are the
content**, and nothing else on this map is one.

### 24.2 The Chats tab

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the Chats tab's spoken rows.*

### 24.3 The challenge screen

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the challenge screen's spoken names.*

### 24.4 The conversation

| Element | Role | Announces |
| --- | --- | --- |
| The header | `header` | **every handle whole**, then the sport, then the booking's state — `tomek.p and ola.k, Padel, booked`; `Waiting for others to join, Padel` where the reader is alone in the room. **One element** for the title and the line under it |
| A message | — | **the author, always** — `Ola K.: on my way` · `You: 18:00 works` |
| A system line | — | the rendered sentence, which already names its actor |
| A day separator | `header` | the weekday |
| The composer | `textbox` | `Message` |
| Send | `button` | `Send` |

**A bubble's accessible name always names the author, even where the bubble does not.** The visible
label is drawn only in a conversation of more than two, because side and colour disambiguate the
pair — and *side and colour* is precisely what Part 13's **never colour as the only signal**
refuses to let a listener depend on. **The whole handle**, never a first name (ADR-0107).

**The header draws one thing and says another, and that is §20.4 applied to a title**
([#401](https://github.com/Raketa02/Raketa/issues/401)). The drawn title is each handle's **stem** —
`tomek, ola` — and the drawn line under it is `Padel · booked`; the element is named by the
handles **whole**, joined with §15's final *and*, then the sport, then the state, with commas
where the drawing has a `·`, because a middle dot is a mark a listener has no reading for. The
title and the sub-line are **one element** on §20.1: the line qualifies what the title names and
has no action of its own. The state is the booking's own word in lower case — `booked`,
`needs result` — never a standing (ADR-0157).

### 24.5 Now, and the game screen

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the Now card's body and doors, the read-only plan and the checklist.*

| Element | Role | Announces |
| --- | --- | --- |
| `YOUR GAMES · n` | `header` | the heading and its count |
| The chat door, on a booked game's details | `button` | `Open the chat` — **the same words as every other chat door**; the drawn word is `Chat` |
| The rail's dots | — | **one element, `Game {i} of {n}`, and no role** — 7.9's own shape (*"one element, one label — never one per segment"*), and not pressable, so it announces a position rather than offering an action |

### 24.6 The typing indicator, and why it is polite

**A live region that is not the toast layer**, so it is stated here rather than as a second row in
§20.9 — that table is a closed list, and this is a different screen with a different reader.

| Element | Role | Announces |
| --- | --- | --- |
| The typing bubble | one element, `accessibilityLiveRegion="polite"` | §22.5's sentence, whole — `ewa.m is typing…` |
| The three dots inside it | — | **hidden.** They are the drawing of the same fact, and announcing both is §1.6's count problem in two spellings |

**The bubble is the element and the sentence is its name** ([#404](https://github.com/Raketa02/Raketa/issues/404)):
the design draws three pulsing dots and no words, so the sentence a pulsing dot cannot say is
what the element is named, rather than a line of text drawn beside it. **A person is named in a
pair too.** A pair has exactly one possible typist and the name adds nothing a listener does not
know — but *somebody is typing* would be a second sentence kept only to withhold a name, the drawn
bubble carries none at all so the spoken name is the only place the name goes (§20.4), and one
sentence shape across every room is worth more to a listener than a shorter one in half of them.

**Polite, and this is the one place that word is load-bearing rather than inherited.** A listener in
a conversation is being read *messages*, one entry at a time, and an assertive region interrupts —
so the loudest thing on the screen would be the least important fact on it, delivered on top of
somebody's actual words. §20.10's argument about a toast landing mid-card is the same argument with
more at stake: a toast interrupts a card, and this would interrupt a person.

**It announces on change and not on a heartbeat**, which the wire already guarantees: a `typing`
frame arrives when the answer changes, so re-rendering the same sentence — and re-announcing it
every three seconds for as long as somebody types — is a thing the client cannot accidentally do.

**And it announces nothing when it goes away.** An empty `player_ids` removes the region's content;
a listener is not told *Ewa M. stopped typing*, because nobody said that and the platform does not
know it. What it knows is that nothing has been heard for five seconds, which is not a sentence
anybody needs.

### 24.7 Cited, not written

| | Where it already is |
| --- | --- |
| The bottom sheet's modal semantics and focus rule | 9.1, and §20.6 |
| Every toast — announced and queued | §20.10 |
| The four `AWAITING_ANSWER` arms, the score grid, and every control on them | `gameAccessibility.ts`, built and tested by [#314](https://github.com/Raketa02/Raketa/issues/314) |
| Durations, weekdays, clock times, counts | §B16, through §18 |
| Pluralisation | §19 — no string hardcodes an `s`, accessible names included |

### 24.8 The court's pairing on the game screen

One block, the forecast, on a booked game's details
([#415](https://github.com/Raketa02/Raketa/issues/415),
[#556](https://github.com/Raketa02/Raketa/issues/556), §25), and §20.1 decides the elements:
nothing in it has an action, so it is four elements of facts. The players card under it went with
Classic play ([#576](https://github.com/Raketa02/Raketa/issues/576)).

| Element | Role | Announces |
| --- | --- | --- |
| `BALANCE FORECAST` | `header` | the eyebrow |
| The split row | — | **one element** — both sides named whole over *and*, then the gap: `You and kasia.w 2,70, tomek.p and marek b 2,71, gap −0,01` |
| The balance bar | `image`, **hidden** | its own §20.4 name is kept on the element — the word and the figure — and the subtree is hidden, because the row above speaks all three of its numbers and the reading beside it speaks the word: a fourth reading of one fact is 6.8's double announcement |
| The reading | — | **one element** — §20.4's order, the word then the figure, then the sentence: `Very even, 90%. A counted game — a confirmed score moves everybody’s level.` |
| The stake tiles | — | **one element, two clauses or none** — `If you win +0,08, If you lose −0,08` |

**The bar's labels are stems and the row's name is whole**, which is §20.4's rule — *the visible
label truncates, the spoken one never does* — applied to the one place a handle is cut on this
screen.

## 25. The court's pairing

Decided by [#410](https://github.com/Raketa02/Raketa/issues/410) and built by
[#415](https://github.com/Raketa02/Raketa/issues/415), on
[ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md)'s reversal of §5.5's
refusal. The surface was `the-loop-screens.md` §5.5, and is a booked game's details since
[#556](https://github.com/Raketa02/Raketa/issues/556); the sentences are here, in
`games/components/gamePresentation.ts`, because the pairing is the game's and §1's owner is the
vocabulary.

**Most of this section is cited.** The four balance words and their breaks are §B9's through
`balancePresentation.ts` (§18); the figures take §B16's shapes through the one formatter. What is
new is the block's own frame. The players card's words went with the card
([#576](https://github.com/Raketa02/Raketa/issues/576)).

| Where | Sentence | Note |
| --- | --- | --- |
| The forecast block's eyebrow | `BALANCE FORECAST` | stored as words, drawn uppercase |
| Between the two strengths | `gap` | lower case — a unit rather than a heading |
| Under the figure, counted | `A counted game — a confirmed score moves everybody’s level.` | `worthLine`'s fact in the forecast's register — *movement*, beside the number that says how even — and not that sentence again four cards apart |
| Under the figure, friendly | `A friendly — nothing moves.` | the negative, kept: true whether or not anything reads it |
| Under the figure, unreadable kind | *nothing* | §3's drop — the figure stands and the clause goes |
| The stake tiles | `If you win` · `If you lose` | *if*, because on a game the result has not happened |

**Absence has no sentence.** ADR-0161 §4: the forecast and the split are omitted together when the
pairing cannot be computed, and *there is deliberately no reason beside the absence* — the block is
absent entirely, the tiles with it, and nothing on the screen says *unrated*, *unavailable* or
anything else.

---

## 26. The radar

*Removed with Classic play on 2026-10-06 ([#569](https://github.com/Raketa02/Raketa/issues/569)): the radar pane's sentences; its area line is §27's now.*

## 27. The You tab

> Added 2026-09-17 by [ADR-0179](../../adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md);
> the surface is [`../you/the-you-screen.md`](../you/the-you-screen.md) and the prototype beside
> it, which is locked. **This section is short on purpose.** Every editing screen on the tab is
> the onboarding step it came from and every read-only screen is the result card or the record
> sheet, so their sentences are already written — the steps' copy in `player_profile`, the
> result's in `onboarding`, the sheet's in §25 — and are cited here, never respelled. What is
> new is the tab's own words: the titles, the live lines, and the few sentences a screen gained
> or lost on the way from a step to a row.
>
> **Amended 2026-10-11** by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §1 and §6: Player
> reliability is points, read with a band, and its screen carries the reliability filter. The
> rows marked *(ADR-0195)* below say the new words; the words they replace are retired.
>
> **Amended 2026-11-03** by [ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md) and
> [ADR-0200](../../adr/0200-a-level-is-asked-where-play-begins.md) §10: *Finding players* is *Your
> games*, the *Name* row is *Nickname* and draws no `@`, and *Where you play* offers a picked club.
> The rows marked *(ADR-0199)* or *(ADR-0200)* say the new words.
>
> **Amended 2026-11-05** by [ADR-0201](../../adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md) §6: *What kind of game*'s answers
> say what a change costs, counted across the player's groups. The rows marked *(ADR-0201)* say the
> new words. The lines that drop a kind are §28's panel lines with *in your groups* added; the line
> under *Either suits me* carries no count.
>
> **Amended 2026-11-07** by [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §7:
> *On your card* gains *Show me in General*, a switch. Its words are §30.8's, cited in the row marked
> *(ADR-0203)*.

| Where | Sentence | Note |
| --- | --- | --- |
| The tab | `You` | the shell's; the eyebrow `Player profile` went in #529 (2026-10-02) |
| The three group titles | `Playing` · `Your games` · `On your card` | `flab`, uppercase by style; the shell's |
| The rows, Playing | `Skill passport` · `Player reliability` · `What kind of game` | |
| The rows, Your games | `Your week` · `Where you play` · `Who you play with` | *(ADR-0200)* the group was `Finding players`; it also titles its screens' eyebrow |
| The rows, On your card | `How others see you` · `Photos` · `Tags` · `Intro` · `Nickname` | *How others see you* is §25's `OWN_RECORD_TITLE`, cited |
| The switch, On your card | ~~`Show me in General` · `Players who don't know you can see your place, open your record and send you a request.`~~ §31.12's `Show me to new people` and its sentence, cited | *(ADR-0203)* a switch in the row, on by default, after *Nickname*; **replaced 2026-11-14** (ADR-0204 §2) |
| Live line, passport | `{sport} {level}` joined by ` · ` | one per rating, the registry's order |
| Live line, reliability | `{points} · {band}` · `100 · New` | *(ADR-0195)* written in from the sheet's own head, `75 · High` ([#660](https://github.com/Raketa02/Raketa/issues/660): *the You row's line uses points and bands*); `{score} of 100 · {n} things counted` and `Nothing counted yet` retired with the strands |
| Live line, kind of game | `{sport} {intent}` joined by ` · `, `not set` for a sport with no answer | the intent words are `playIntentPresentation`'s |
| Live line, week | `{n} slots ticked` · `Nothing ticked — we do not know when you play` | |
| Live line, area | `Area set · updates when you open Raketa` | the one state — a profile cannot be committed without an area, a reading or *(ADR-0200)* a picked club; the words for a picked club on a phone without permission, which the cold start never updates, are [#733](https://github.com/Raketa02/Raketa/issues/733)'s |
| Live line, who you play with | `Matched with anyone` · `… women only` · `… men only` | **the preference only** — the gender is drawn on its own screen and nowhere else on the tab |
| Live line, record | `Your player record, as a stranger reads it` | |
| Live line, photos | `{n} of 3 · profile photo on court` · `{n} of 3 · profile photo not checked as on court` · `None — a court poster stands in` | |
| Live line, tags | `{n} of 6 · {first}, {second}, +{rest}` | the names, not the emoji |
| Live line, intro | `“{intro}”` · `None — say it in your own words` | the second quotes the step's title |
| Live line, nickname | `{nickname}` | *(ADR-0199)* no `@` and no second line (§15); `{name} · @{nickname}` retired with the Name |
| Passport, a card's status chip | `Initial estimate` · `Calibrating` · `Stable` | `ratingStatusLabel`, cited; drawn as a `Tag`, not a row — the result card's *Rating status* row stays under the bar as well |
| Passport, add a sport | `Add a sport` · `One questionnaire, one rating. Nothing you already hold changes.` · chip `Rate {sport}` | the chip begins a pass of one sport (ADR-0179 §3) |
| Passport, the ladder | `The ladder` · `{edges}` · `{band} · you ({sports})` · *the band's meaning* | `bandPresentation`'s meanings, cited |
| Reliability, the figure and its word | `{points} · {band}` · `Out of 100` · the band said as `Very high reliability` · `High reliability` · `Medium reliability` · `Low reliability` · `New` beside 100 | *(ADR-0195)* the band is the server's — Very high 90–100, High 75–89, Medium 50–74, Low below 50 — and the phone holds no thresholds; `Reliable` from 90 · `Holding` from 70 · `Under the bar` below retired with the tone ladder |
| Reliability, the counts | `Shows up` · `turned up {n} of {m}` — `Keeps plans` · `kept {n} of {m}` — `Being late` · `late {n} time(s)` — `Results left in dispute` · `{n}` | *(ADR-0195)* over the last 6 months; no meters and no ledger ([#660](https://github.com/Raketa02/Raketa/issues/660)) |
| Reliability, a new player | the new-player sentence, which no longer speaks of plans | *(ADR-0195)* `Nothing has fallen due for you yet — no plan has settled …` retired: everyone has a figure from the start. The new sentence is #660's to write |
| Reliability, the filter | `Play only with players of at least High reliability` · `… at least Medium reliability` · off by default · `Your filter hides {n} of the {m} players in your groups.` | *(ADR-0195)* the *hides* line only while a filter is on ([#662](https://github.com/Raketa02/Raketa/issues/662)) |
| Reliability, a player someone filters out | `Some players in your groups play only with {band} reliability or above. At {floor} you're dealt with everyone again.` | *(ADR-0195)* names nobody; `{floor}` is the lowest band floor among the filters that hide them ([#662](https://github.com/Raketa02/Raketa/issues/662)) |
| What kind of game, under the title | `This changes how people find you` | replaces the section's heading and body; the footnote for an undeclared sport is #296's, cited |
| What kind of game, under an answer that drops a kind | `Your {n} {kind} cards in your groups go. Games you're In on stay.` · `Your 1 {kind} card in your groups goes. Games you're In on stay.` · `Raketa stops dealing you {kind} games. Games you're In on stay.` | *(ADR-0201)* under *Competitive* or *For fun* when the current answer is the other kind or *Either suits me*; `{kind}` is the kind that goes, `competitive` or `for-fun`; `{n}` is `GET /players/me/deck-counts`'s count of it, summed over the player's groups; the third at `{n}` = 0 ([#742](https://github.com/Raketa02/Raketa/issues/742)) |
| What kind of game, under *Either suits me* | `Keep your {kind} cards and get {other kind} ones too.` | *(ADR-0201)* when the current answer is one kind: `Keep your competitive cards and get for-fun ones too.` · `Keep your for-fun cards and get competitive ones too.`; no count |
| What kind of game, the current answer and an undeclared sport | *no line* | *(ADR-0201)* the current answer is marked as today; an undeclared sport keeps its footnote |
| Your week, the buttons | `Save your week` · `Saved` · `Clear all` | the grid's footnote is the step's, cited |
| Where you play | `Your area is set` · `Your area updates each time you open Raketa; it is never finer than about a kilometre.` · `Use my location` · `Pick a club near where you play` | the permission states are the step's, cited; the middle line is static, the one written trace of the cold-start refresh, and was §26's until the radar went; *(ADR-0200)* the two ways are the location step's own, replacing `Read my area again` ([#733](https://github.com/Raketa02/Raketa/issues/733)) |
| Who you play with | *the step's headings, labels, cost line and reach sentence* · `Save` · `Saved` | the scope sentences are not repeated |
| Photos | *the step's, whole* | title `Your court photos`; eyebrow `On-court only — up to three`; no *Continue* |
| Tags, the button | `Save` · `Saved` · `Pick {n} more tag(s) to save` | the step's *to continue* becomes *to save* |
| Intro, the buttons | `Save` · `Saved` · `Remove intro` | |
| Nickname, the refusal | `That nickname is taken. Pick another.` | `authErrorMessage`'s, cited; the server's code |
| The foot | `Sign out` | the account panel's, as today |

**What is cited.** The steps' eyebrows lose their *Step N of 8* and keep their bounds; the
result card's every word is the onboarding result's; the record sheet's every word is §25's;
the area screen's permission states are the location step's; the reach sentence is the gender
step's. **What is dropped** is recorded in ADR-0179 §9 so nobody restores it as a gap: the
tab's placeholder line, the declaration section's heading and body, the week's promise note,
the location's *why we ask*, the gender step's scope sentences, and every explanatory card of the
first draft.

## 28. The Games tab's door, and finding

> Added 2026-11-05 by [ADR-0201](../../adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md) §2 and §4,
> the mechanics Q127, PRD [#736](https://github.com/Raketa02/Raketa/issues/736). The surface is
> [the screens A1 and A2.1](../games-and-fill-in/the-screens.md#a21-states). Built by
> [#740](https://github.com/Raketa02/Raketa/issues/740) (the door and its panel) and
> [#741](https://github.com/Raketa02/Raketa/issues/741) (finding). **The three answers are not
> respelled here**: *Competitive*, *For fun* and *Either suits me* are `playIntentPresentation`'s, the
> first-time question's and the You tab's, cited.

**The panel says what the player declared, why they don't see the other kind, and what each answer
costs.** It is written twice, once for each declared kind, and each line has a singular and a zero
form. `{sport}` is the sport's name inside a sentence, as in *Carry on with your padel questions*;
`{n}` is the count of the player's own cards of their declared kind in this group, the one the
switch shows.

| Where | A competitive player taps *For fun* | A for-fun player taps *Competitive* | Note |
| --- | --- | --- | --- |
| The switch, the door | `For fun`, dimmed | `Competitive`, dimmed | no number; the same size and press target as the live kind |
| Panel, the title | `You play {sport} competitively, so Raketa only puts you in competitive games.` | `You play {sport} for fun, so Raketa only puts you in for-fun games.` | |
| Panel, the question | `Want for-fun games too?` | `Want competitive games too?` | |
| Panel, *Either suits me*'s line, `{n}` ≥ 2 | `Keep your {n} competitive cards and get for-fun ones too.` | `Keep your {n} for-fun cards and get competitive ones too.` | the first answer, highlighted |
| … `{n}` = 1 | `Keep your 1 competitive card and get for-fun ones too.` | `Keep your 1 for-fun card and get competitive ones too.` | |
| … `{n}` = 0 | `Get for-fun games as well as competitive ones.` | `Get competitive games as well as for-fun ones.` | a zero drops the number (PRD #736, call 4) |
| Panel, the tapped kind's line, `{n}` ≥ 2 | `Your {n} competitive cards go. Games you're In on stay.` | `Your {n} for-fun cards go. Games you're In on stay.` | the second answer |
| … `{n}` = 1 | `Your 1 competitive card goes. Games you're In on stay.` | `Your 1 for-fun card goes. Games you're In on stay.` | |
| … `{n}` = 0 | `Raketa stops dealing you competitive games. Games you're In on stay.` | `Raketa stops dealing you for-fun games. Games you're In on stay.` | |
| Panel, the way out | `Keep competitive` | `Keep for fun` | closes the panel and sends nothing |

**Finding** is the deck's area right after an intent answer on Games, while the deal request is in
flight:

| After | Sentence | Note |
| --- | --- | --- |
| The panel's *For fun*, or the first-time question's *For fun* | `Finding for-fun games for you…` | |
| The panel's *Competitive*, or the first-time question's *Competitive* | `Finding competitive games for you…` | |
| The panel's *Either suits me* | `Finding {kind} games for you…` | `{kind}` is the kind tapped, where the player lands |
| The first-time question's *Either suits me* | `Finding games for you…` | |

The ellipsis is one character, `…`. Finding ends on the deck's own states, whose words are already
written: the cards, or *Nothing picked right now* with **Post a game**. A new yes refused on a card of
a dropped kind is `no_longer_fits`, whose words `proposalsCopy` already has
(`frontend_player/src/features/proposals/components/proposalsCopy.ts`), cited.

## 29. Friends

> Added 2026-11-06 by [ADR-0202](../../adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md),
> the mechanics Q128, PRD [#743](https://github.com/Raketa02/Raketa/issues/743). The surfaces are
> [the Friends spec set](../friends/README.md): [the mechanics](../friends/the-mechanics.md) say what
> happens and [the screens](../friends/the-screens.md) where each sentence stands. Built by the
> player app's [#753](https://github.com/Raketa02/Raketa/issues/753),
> [#754](https://github.com/Raketa02/Raketa/issues/754) and
> [#756](https://github.com/Raketa02/Raketa/issues/756)–[#760](https://github.com/Raketa02/Raketa/issues/760),
> and the public site's [#755](https://github.com/Raketa02/Raketa/issues/755). §29.5's Home card was
> added 2026-11-07 (the mechanics Q129, PRD [#762](https://github.com/Raketa02/Raketa/issues/762)).
> §29.1's *Unblock* and §29.2's ranking rows were changed the same day by
> [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md) (the mechanics Q130, PRD
> [#766](https://github.com/Raketa02/Raketa/issues/766)): a block closes the record both ways, and a
> request may come from the ranking (§30).
>
> **Every sentence of PRD #743's *Solution* is here**, with its singular and zero forms. Rows marked
> *(a call)* are words the PRD doesn't give and a screen needs, written in while recording it, for the
> product owner to overrule. **No sentence says *her*, *his*, *she* or *he* about another player**: a
> gender never crosses to another player (ADR-0096, the glossary's **Gender**), so the PRD's *Ask Zofia
> to get her padel level*, *so he can add you* and *Zofia has her padel level — you can seat her now*
> are written without one below. The club website's two lines are its own copy
> ([#747](https://github.com/Raketa02/Raketa/issues/747)) and say *at an hour your courts are full*.

**Placeholders.** `{nickname}` is a player's whole nickname (§15). `{sport}` is the sport's name
inside a sentence (*padel*), `{Sport}` at a line's start or after a `·` (*Padel*). `{share}` is the
card's share and `{price}` the court's, both as money (*25 zł*, *100 zł*). `{when}` is the game's day
and hour as the deck's court block writes them (*Saturday 10:00*, *Sat 26 Sep 20:00*), and
`{cut-off}` the club's cut-off the same way (*Fri 10:00*). A list of names is joined `A`, `A and B`,
`A, B and C`.

### 29.1 Members, the record and the result

| Where | Sentence | Note |
| --- | --- | --- |
| Members, the pill | `+ Add` · `Accept` | black pills; the + is drawn. The pill acts, the rest of the row opens the record |
| Members, the tag | `request sent` · `friend` | amber · green, lower-case as in mocks 1–2 |
| Every face, the tag | `FRIEND` | the deck's tile tag (Q68), on the reader's own friends only; `friend` elsewhere |
| The record, the left button | `Add friend` · `Request sent` ▾ · `Accept` · `Friend` ✓ ▾ | ✓ and ▾ are drawn, never characters (Archivo has no ✓) |
| The record, the menus | `Cancel request` · `Remove friend` | |
| The record, removing's confirmation | `Remove {nickname} as a friend?` · `Nobody is told, and your games together stay as they are.` · `Remove friend` · `Keep` | *(a call)* |
| The record, someone you blocked | ~~`Unblock`~~ | **retired 2026-11-07** (ADR-0203 §8): a blocked pair's record never opens, so the record has no Unblock. Unblock is in You › Blocked players |
| The record, a stranger nobody may ask | *no Add friend* | **Block** alone, when the record says no request may be sent (§30, *a call*) |
| The result screen | `PLAYED WITH` | the eyebrow over the card; its rows are Members' |

### 29.2 Friend requests

| Where | Sentence | Note |
| --- | --- | --- |
| Needs your answer, the section's title | `FRIEND REQUESTS · {n}` | `{n}` ≥ 1; at 0 the section and its title are gone. Home's row until 2026-11-17 ([§32](#32-needs-your-answer), #816) |
| The card, who | `{nickname} wants to be your friend` | two lines at most on the tile |
| The card, where (a group) | `With you in {group} · {Sport} {level} ·` and the reliability chip | the group the request was made in and its sport; the chip is the existing one (*✦ 98*). **Retired on the tile 2026-11-17** (ADR-0205 §1, #816): the tile draws the chip alone, on its own line, and #818 adds the sender's levels. The notice's body still says it |
| The card, where (a link) | `Invited you to Raketa` | in place of the group line. **Retired on the tile 2026-11-17**, as the group line |
| The card, where (the ranking) | §30.8's `Found you in the {sport} ranking`, cited | in place of the group line, as a link's stands (ADR-0203 §9); a request from the ranking to a group-mate reads it too. **Retired on the tile 2026-11-17**, as the group line; the notice keeps it |
| The card, buttons | `Not now` · `Accept` | at the tile's foot |
| Notice, a request | `{nickname} wants to be your friend` · body: the card's where-line | once per request |
| Refused, the daily limit | ~~§30.8's limit sentence, cited~~ | **retired 2026-11-14** (ADR-0204 §2): there is no daily limit, and `daily_request_limit` leaves the contract |
| Notice, accepted | `{nickname} said yes — you're friends` | to the requester |
| Notice, crossed | `You and {nickname} are friends now` | to both, each naming the other *(a call: nobody said yes)* |

### 29.3 The Friends page and the Add friends sheet

| Where | Sentence | Note |
| --- | --- | --- |
| The page | `Friends` · `+ Add friends` | the + is drawn |
| The tabs, from You | `Friends` · `Asked you` · `You asked` | |
| *Asked you*'s count | `Asked you · {n}` | `{n}` ≥ 1; at 0, `Asked you` alone |
| A row, *Friends* | `{Sport} {level}` joined by ` · ` | every sport they play (call 11) |
| A row's button | `Accept` (*Asked you*) · `Cancel` (*You asked*) | |
| Empty, *Friends* | `No friends yet. Add them from your groups, or send your link.` | *(a call)* |
| Empty, *Asked you* | `Nobody has asked you yet.` | *(a call)* |
| Empty, *You asked* | `You haven't asked anyone.` | *(a call)* |
| The picker, a row | `{level} · {band}` | *2,75 · established*: the band's name, lower-case (`bandPresentation`, cited) |
| The picker, no level in this sport | `No {sport} level yet` · `Ask {nickname} to get a {sport} level` · after asking, `Asked` | |
| The picker, its foot | `Done` | |
| The picker, no friends | `Nobody you know here yet` and its card | `groupsCopy`'s, cited (play 55) |
| The sheet | `Add friends` · `From your groups` | |
| The sheet, a group | `{n} members · {m} to add` · `{n} members · 1 to add` · `{n} members · nobody to add` · `1 member · …` | |
| The sheet, the link | `Not on Raketa yet?` · `{public site}/f/{code}` · `Copy` · `New link` | |
| The sheet, after *New link* | `New link made. The old one no longer works.` | *(a call)* |

### 29.4 The link

| Where | Sentence | Note |
| --- | --- | --- |
| Home, the request | `{nickname} wants to be your friend` · `Invited you to Raketa` · `Not now` · `Accept` | the card of §29.2. Since 2026-11-17 it waits in Needs your answer, without `Invited you to Raketa` (#816) |
| The public page | `{nickname} invited you to play on Raketa` · the store buttons · `Open in Raketa` | the stores' own badges; the preview image carries the same sentence |
| The public page, a replaced or unknown code | `Nothing at that link` | |

### 29.5 Asking for a level

| Where | Sentence | Note |
| --- | --- | --- |
| Notice, to the friend | `{nickname} wants to play {sport} with you. Get your {sport} level so {nickname} can add you.` | the asker, twice; opens that sport's questionnaire |
| Notice, back to the asker | `{nickname} has a {sport} level — you can seat {nickname} now.` | the friend, twice; opens the picker |

> **The Home card**, added 2026-11-07 by [ADR-0202](../../adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)'s
> amendment of that day (§4), the mechanics Q129, PRD [#762](https://github.com/Raketa02/Raketa/issues/762).
> It stands on [the screens §6.4](../friends/the-screens.md#64-asked-for-a-level--n-designed-no-mock), and
> the player app's [#765](https://github.com/Raketa02/Raketa/issues/765) builds it. **Every sentence of
> PRD #762's *Solution* is here.** None says *her* or *him*: several askers are *they*. `{nickname}`
> is an asker's, newest first. **Three or more askers name two and count the rest**, unlike §29's
> list join, so the title stays one line.

| Where | Sentence | Note |
| --- | --- | --- |
| Needs your answer, the section's title | `ASKED FOR A LEVEL · {n}` | `{n}` ≥ 1 is the number of sports with a card; at 0 the section and its title are gone. Home's row until 2026-11-17 ([§32](#32-needs-your-answer), #816) |
| The card, who — one asker | `{nickname} wants to play {sport} with you` | *tomek.k wants to play padel with you* |
| … two askers | `{nickname} and {nickname} want to play {sport} with you` | *tomek.k and kuba.w want to play padel with you* |
| … three or more | `{nickname}, {nickname} and {m} more want to play {sport} with you` | the two newest; `{m}` ≥ 1 counts the rest (*tomek.k, kuba.w and 2 more*); up to three faces are drawn |
| The card, the line — one asker | `A few questions, and {nickname} can add you to a game.` | **retired 2026-11-17** (ADR-0205 §1, #816): the tile has no line under its title |
| … two or more | `A few questions, and they can add you to a game.` | *they*, never a gender (ADR-0096). **Retired 2026-11-17**, as above |
| The card, the buttons | `Not now` · `Get your {sport} level` | outline · coral; the coral one closes Needs your answer and starts the sport's questionnaire from Home, as the notice does |
| The card, a questionnaire in that sport left halfway | `Not now` · `Carry on` | the coral button changes; the title doesn't. `You're on question {n}.` was the line and is **retired 2026-11-17** with it |
| Not now, the toast | `You can get your {sport} level any time, from You › Skill passport.` | neutral, held long enough to read; the passport is where §27's `Rate {sport}` chip is. Nobody else is told |
| A start that fails | the *level asked* notice's own toasts | cited, not respelled: `You have a {sport} level already.` for `sport_already_rated` (`notificationsCopy`) |

### 29.6 The Friends tab

| Where | Sentence | Note |
| --- | --- | --- |
| The switch | `Competitive` · `For fun` | `playIntentPresentation`'s, cited; it sets this game's kind |
| The court | `THEIR SIDE` · `YOUR SIDE` · `{nickname} {level}` · `You {level}` · `+ Friends` | mock 7 |
| The court, unfilled | `Seat {n} more friends` · `Seat 1 more friend` | at 0, the card |
| The card | the deck card's words, without tiles: the *vs* line (`YOU + EWA VS MAGDA + ANIA`; singles `YOU VS ANIA`), the balance (`87%` · `Very even`), the overlap's grade, `Court available`, `{share} each`, `{when} · {club} · {court}` and the kind of court | the screens A2.3, cited |
| The card, another club | `{home club} is full at {HH:MM}` | under the court; the same marker on the deck's court block, Post a game's slot sheet and *Find a court* |
| The card, buttons | `Send game and pay {share}` · `Pick a different court` | |
| The card, refused | `These four can't all play together. Swap someone.` · singles: `These two can't play together. Swap someone.` | names nobody |
| The card, no court | `No court is free in the next 14 days.` | *(a call)* |
| *Find a court* | `Find a court` · day headings `TODAY` · `TOMORROW` · `SATURDAY` · `SAT 26 SEP` | upper-case by style, as mocks 10–11 |
| *Find a court*, a row | `{HH:MM}` · `{club} · {court}` · `{share} each` | |
| *Find a court*, who is free | `Everybody free` · `{names} busy` · `You're busy` · `You and {names} busy` | `{names}` the friends outside their weekly hours then; the reader is *You* *(a call, for the reader's own hours)* |

### 29.7 Sending

| Where | Sentence | Note |
| --- | --- | --- |
| The send sheet, the choices | `Split the cost` · `Pay the whole court` | Split first, chosen |
| Split, above the button | `We hold {price} on your card until {cut-off}. You pay {share}, plus {share} for any seat still empty then.` | doubles; the maximum, right above the order button |
| … singles | `We hold {price} on your card until {cut-off}. You pay {share}, plus {share} if the other seat is still empty then.` | *(a call)* |
| Split, the button | `Send game and pay {share}` | |
| Whole court, the button | `Send game and pay {price}` | |
| Refused, the court went | `court_just_taken`'s words, cited: `That court was just booked by another game. Nothing was charged — try again.` | `proposalsCopy`; the card is re-read |
| Refused, two waiting | `You have 2 friends games waiting for answers. Send this one once one of them is settled.` | *(a call)* |
| Refused, the sender's week or hour | the invitee's two sentences of §29.8, with the sender's own numbers | |

### 29.8 The invitation, and the sender's game

| Where | Sentence | Note |
| --- | --- | --- |
| Home, the row's title | `FRIENDS GAME · {n}` | `{n}` ≥ 1; at 0 the row and its title are gone |
| The card | `{nickname}'s game` · the clock · `{when} · {club} · {court} · {Sport} · {Kind}` | the clock is the deck ribbon's countdown, cited (`1 h 35`, `45 min`); `{Kind}` is `Competitive` or `For fun` |
| The card, the faces | `{nickname}` under each, `You` under the reader | ✓ on those In; faded while waiting |
| The card, Split | `Not this time` · `Accept and pay {share}` | |
| The card, Whole court | `{nickname} paid the court` · `Not this time` · `Accept` | the sender's nickname |
| Accept refused, a full week | `Your week is full: {n} games, the most you set in Games & money.` · `… 1 game, …` | *(a call)* |
| Accept refused, a game at that hour | `You already have a game at {HH:MM}.` | *(a call)* |
| Notice, the invitation | `{nickname} invited you to a game` · body: `{when} · {club} · {Sport} · {Kind}` | *(a call)*; opens Home on the card. A seat invitation into an empty seat says the same |
| Notice, a seat taken | `Someone took that seat first.` · body: `{when} · {club}` | *(a call)*; `seat_just_taken`'s sense |
| The last seat taken | *It's a game!*, cited | to all four |
| Your games, the sender's game | `{k} of {m} friends in · waiting for {names}` · at `{k}` = 0, `Waiting for {names}` · `{k} of {m} friends in · 1 seat empty` · `… · {e} seats empty` | `{m}` is 3 in doubles, 1 in singles: `Waiting for Ania`, then the ordinary row once In |
| The details, a seat | `In` · `waiting · {time} left` · `can't make it` · `didn't answer` · `empty` · `Seat open` | `{time}` the countdown, cited |
| The details, the pay mode | `Split` · `{nickname} paid the court` | under the price |

### 29.9 An empty seat

| Where | Sentence | Note |
| --- | --- | --- |
| Notice, a no | `{nickname} can't make it` · body: `{when} · Invite a friend, or open the seat to {group}.` | body *(a call)* |
| Notice, silence | `{nickname} didn't answer` · body: the same | body *(a call)* |
| … inside the last 24 hours | the body gains the cover line below | Split only |
| The details, the actions | `Invite a friend` · `Open to {group}` | *Open to Ogrody* |
| Opening, the confirmation | `Open this seat to {group}?` · `Anyone in {group} who fits can take it and pay {share}.` · `Open to {group}` · `Not yet` | *(a call)*; a stranger can take it (#760) |
| The cover warning, one seat | `{when} · 1 seat still empty` · `At {cut-off} you pay {sum}: your {share} and {nickname}'s seat.` | `{nickname}` the seat's last invitee; `{sum}` your share plus the seat's |
| … more seats | `{when} · {e} seats still empty` · `At {cut-off} you pay {sum}: your {share} and {e} empty seats.` | *(a call, for the plural)* |
| The cover warning, its buttons | `Invite a friend` · `Open to {group}` · `Call it off` | |

### 29.10 Leaving and calling off

| Where | Sentence | Note |
| --- | --- | --- |
| The sender's leave sheet | `Call it off for everyone` · `Leave · the others play on` | before the cut-off |
| … under *Call it off* | `Everyone is told, nobody pays, and the court goes back to {club}.` | *(a call)* |
| … under *Leave*, Split | `Your card stops covering the game. A seat still empty at {cut-off} calls it off, and nobody pays.` | *(a call)* |
| … under *Leave*, Whole court | `You still pay the court. Whoever takes your seat pays you {share} back.` | *(a call)* |
| Notice, called off | `{nickname} called off {when}` · body: `Nobody paid.` | the games and fill-in mechanics §17.2's *Game called off*, its reason the sender |
| Notice, a friend left | `{nickname} left your game` | the existing *Someone left your game*, cited; inside the last 24 hours with Split, the cover line |

## 30. Rankings

> **Amended 2026-11-14** by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
> (the mechanics Q131): §30.4's *Hidden from General* and §30.8's limit and switch rows are retired.
> The switch is §31.12's *Show me to new people*.
>
> Added 2026-11-07 by [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md), the
> mechanics Q130, PRD [#766](https://github.com/Raketa02/Raketa/issues/766). The surfaces are
> [the Rankings spec set](../rankings/README.md): [the mechanics](../rankings/the-mechanics.md) say
> what happens and [the screens](../rankings/the-screens.md) where each sentence stands. Built by the
> player app's [#775](https://github.com/Raketa02/Raketa/issues/775)–[#779](https://github.com/Raketa02/Raketa/issues/779).
>
> **Every sentence of PRD #766's *Solution* is here.** Rows marked *(a call)* are words written in
> while recording it, for the product owner to overrule. **No sentence says *her*, *his*, *she* or
> *he* about another player** (ADR-0096, the glossary's **Gender**). The marks ▲, ▼, — and the trophy
> are drawn, never characters.

**Placeholders.** `{nickname}` is a player's whole nickname (§15). `{sport}` is the sport's name
inside a sentence (*padel*). `{place}` is an ordinal: **1st, 2nd, 3rd, 4th … 11th, 12th, 13th … 21st,
22nd, 23rd … 101st, 111th, 112th**, so *-st*, *-nd* and *-rd* follow a last digit of 1, 2 and 3 except
after a ten (11–13, 111–113). `{n}` is a plain number. `{gap}` is a difference of levels with the
decimal comma and two decimals (*0,04*), and `{level}` a level (*2,71*).

### 30.1 Home

| Where | Sentence | Note |
| --- | --- | --- |
| The trophy, with a place | `#{n}` | *🏆 #7*: the place as a number, beside the drawn trophy |
| The trophy, no place | *no words* | the drawn trophy alone, still a button |

### 30.2 The header and the switch

| Where | Sentence | Note |
| --- | --- | --- |
| The title | `Rankings` | |
| Under it | `Competitive games only` | small and grey |
| The switch | `General` · `Friends` | |
| The sport pill | the sports' names | the deck's control, cited |

### 30.3 Your place card

| Where | Sentence | Note |
| --- | --- | --- |
| The eyebrow | `YOUR PLACE` | |
| The place | `{place}` | *7th*, volt |
| Beside it | `of {n}` | *of 13* |
| The chip, up | `▲ {n}` · `up this week` | |
| The chip, down | `▼ {n}` · `down this week` | |
| The chip, the same | `—` · `no change this week` | |
| The chip, new | `New` · `this week` | |

### 30.4 The gap line

The line is up to two parts joined by ` · `: the player above, then the player below. Each `{gap}` is
bold.

| Where | Sentence | Note |
| --- | --- | --- |
| Above, one win | `{gap} behind {nickname} · one win closes it` | *0,04 behind Karol · one win closes it* |
| Above, 2–5 wins | `{gap} behind {nickname} · about {n} wins close it` | *… · about 3 wins close it* |
| Above, more than 5 | `{gap} behind {nickname}` | the count left out: *0,31 behind Karol* |
| Above, level | `Level with {nickname} · one win puts you ahead` | *Level with Ewa · one win puts you ahead* |
| Below | `{nickname} is {gap} behind you` | *Zofia is 0,02 behind you*; left out in last place |
| Below, level | `{nickname} is level with you` | *(a call)* |
| First place | `Top of the list` | the whole line |
| Hidden from General | ~~`Hidden from General`~~ | **retired 2026-11-14** (ADR-0204 §2): nobody is hidden from the ranking |

**Whole lines:** *0,04 behind Karol · one win closes it · Zofia is 0,02 behind you* · *0,04 behind Karol
· about 3 wins close it · Zofia is 0,02 behind you* · *0,31 behind Karol · Zofia is 0,02 behind you* ·
*Level with Ewa · one win puts you ahead*, then the part about the player below *(a call)* · *Top of the
list*.

### 30.5 Not listed

| Where | Sentence | Note |
| --- | --- | --- |
| General, fewer than 5 results | `{n} of 5 games — {m} more competitive {sport} games put you on the list` | *2 of 5 games — 3 more competitive padel games put you on the list*; `{n}` 0–3, `{m}` = 5 − `{n}` |
| … with 4 | `4 of 5 games — 1 more competitive {sport} game puts you on the list` | the singular; PRD #766 gives the part after the dash, and the count before it stays *(a call)* |
| General, no level | `No {sport} level yet — get one, then 5 competitive games put you on the list` | with the button below |
| Friends, a level but no result | `Not ranked in {sport} yet — your first confirmed competitive game puts you on the list` | the brief's line, a call made while ticketing |
| Friends, no level | `No {sport} level yet — get one, then one competitive game puts you on the list` | with the button below |
| Both, the button | `Get your {sport} level` | coral; starts that sport's questionnaire, and returns to Rankings |
| Both, off the list | `Off the list — no competitive {sport} game in 90 days. Your next one puts you back.` | |

### 30.6 Friends

| Where | Sentence | Note |
| --- | --- | --- |
| Listed, no friend listed | `Just you so far` | with **Add friends** |
| Nobody listed | `None of your friends is ranked in {sport} yet` | with **Add friends**, in the card's place |
| The button | `Add friends` | opens the Add friends sheet, §29.3's, cited |

### 30.7 The podium and the list

| Where | Sentence | Note |
| --- | --- | --- |
| The podium, a step | `{n}` | the true place |
| The podium, a player | `{nickname}` · `{level}` | |
| A row | `{n}` · `{nickname}` · `{level}` | the reader's own row reads `You` |
| A row's chip | `▲ {n}` · `▼ {n}` · `—` · `New` | no *this week* in a row |
| A sport nobody is listed in | `Nobody ranked in {sport} yet` | *Nobody ranked in badminton yet* |
| The jump button | `You · {place}` | *You · 212th* |

### 30.8 Strangers, requests and the switch

| Where | Sentence | Note |
| --- | --- | --- |
| A request's card and notice, from the ranking | `Found you in the {sport} ranking` | in place of the group line (§29.2) |
| The record, the limit reached | ~~`You've sent 10 requests to new people today. Try again tomorrow.`~~ | **retired 2026-11-14** (ADR-0204 §2): there is no daily limit |
| The record, Block's confirmation | the existing confirmation, with `You can unblock from You › Blocked players.` | *(a call)*: the record's Unblock is gone |
| You, the switch | ~~`Show me in General`~~ | **retired 2026-11-14** (ADR-0204 §2): replaced by §31.12's `Show me to new people` |
| You, under it | ~~`Players who don't know you can see your place, open your record and send you a request.`~~ | **retired 2026-11-14**, with the switch |

## 31. Home rows

> Added 2026-11-14 by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md),
> the mechanics Q131, PRD [#789](https://github.com/Raketa02/Raketa/issues/789). The surfaces are
> [the Home rows spec set](../home-rows/README.md): [the mechanics](../home-rows/the-mechanics.md) say
> what happens and [the screens](../home-rows/the-screens.md) where each sentence stands. Built by the
> player app's [#798](https://github.com/Raketa02/Raketa/issues/798)–[#805](https://github.com/Raketa02/Raketa/issues/805).
> The same record retires §30.4's *Hidden from General*, §30.8's switch and limit rows, and §29.2's
> daily-limit row ([§31.13](#3113-retired)).
>
> **Every sentence of PRD #789's *Solution* is here.** Rows marked *(a call)* are words written in
> while recording it, for the product owner to overrule. **No sentence says *her*, *his*, *she* or
> *he* about another player** (ADR-0096, the glossary's **Gender**). The marks ▲, ▼, ✓, +, …, the
> envelope and the dots are drawn, never characters. **The mocks' names, initials, tags and numbers
> are sample data**: *Rakieta* reads **Raketa**, a district reads as a distance.

**Placeholders.** `{nickname}` is a player's whole nickname (§15), and `You` for the reader.
`{sport}` is the sport's name inside a sentence (*padel*), `{Sport}` at a line's start or after a `·`
(*Padel*). `{level}` is a level with the decimal comma (*2,71*), and `{gap}` a difference of levels the
same way (*0,02*). `{pct}` is a whole percent with no space before the sign (*91%*). `{n}` is a plain
number. `{group}` is a group's name. `{runner}` is who answers the group's requests: **the club's name**
for an Official group, **the Owner's nickname** for a Player group (*Ogrody 33*, *tomek.k*). `{club}` is
the club the group plays at.

### 31.1 Home

| Where | Sentence | Note |
| --- | --- | --- |
| Hottest groups, the heading | `HOTTEST GROUPS` | no See all |
| Same competitive level, the heading | `SAME COMPETITIVE LEVEL PLAYERS` · `See all ›` | |
| New in Raketa, the heading | `NEW IN RAKETA` · `See all ›` | never *Rakieta* |
| Same vibe, the heading | `SAME VIBE PLAYERS` · `See all ›` | |
| Top 10, the heading | `TOP 10` · the sport pill · `Rankings ›` | the pill is the deck's control, cited |
| *Your games*, a player in no group | `Join a group to get games — the hottest ones are just below.` | in place of §22.7's `⚡ Play finds you one.`; the first line stands |

### 31.2 Hottest groups — the card

| Where | Sentence | Note |
| --- | --- | --- |
| The tag, the hottest | `▲ HOTTEST` | on one card at most |
| The tag, growing | `+ GROWING` | |
| The first figure | `{n}` · `games this week` | *14 games this week*; `1 games this week` is never written: one reads `game this week` *(a call)* |
| The second figure | `{n}` · `players` | *11 players* |
| … grown | `+{n}` · `this month` | green, beside the players: *+3 this month* |
| The chip | `Join` · `Ask to join` · `Asked` · `You're in` | *Anyone* · *People I approve* · a request waiting · a member |

### 31.3 The group sheet

| Where | Sentence | Note |
| --- | --- | --- |
| The button | `Join` · `Ask to join` · `Asked` · `Open group` | *Open group* for a member, opening the group page |
| The identity row | `Open group` · `Closed group` | *Anyone* · *People I approve* |
| … who runs it | `run by {runner}` | *run by Ogrody 33*, *run by tomek.k* |
| … where | `{club}` | *Ogrody 33* |
| The first stat card | `{n}` · `games this week` | as §31.2 |
| The second stat card | `{n}` · `players · new this month` | with the green `+{n}` |
| The people row, friends | `{n} of your friends play here` | *7 of your friends play here* |
| … one friend | `1 of your friends plays here` | |
| … no friend | `{n} players` | *11 players* |

### 31.4 Withdraw

| Where | Sentence | Note |
| --- | --- | --- |
| The sheet, from *Asked* | `Waiting for {runner} to answer` | *Waiting for Ogrody 33 to answer* |
| Its button | `Withdraw request` | tells nobody |

### 31.5 Same competitive level — the card

| Where | Sentence | Note |
| --- | --- | --- |
| The reader's side | `You` · `{level}` | |
| The other's side | `{nickname}` · `{level}` | |
| Between them | `{pct}` · `EVEN` | *91%*, in the game cards' colour; the word is always *EVEN* |
| The sport | `{Sport}` | with its dot |
| The bar's mark | `YOU` | the reader's tall white mark |
| The bands | `New` · `Developing` · `Established` · `Advanced` | the reader's own in bold |
| The gap, below | `{gap} below you` | *0,02 below you* |
| The gap, above | `{gap} above you` | *0,09 above you* |
| The gap, none | `Same level` | when the gap rounds to 0,00 |
| More sports | `{n} sports ›` | *2 sports ›*; only with more than one shared sport |

### 31.6 The comparison sheet

| Where | Sentence | Note |
| --- | --- | --- |
| The title | `You vs {nickname}` | *You vs zofia.b* |
| A block's levels | `You {level} · {nickname} {level}` | *You 2,71 · zofia.b 2,69* |
| A block's gap | §31.5's gap lines, cited | |
| A block's tag | `{pct} even` | *91% even*, in the light version of its colour |

### 31.7 New in Raketa

| Where | Sentence | Note |
| --- | --- | --- |
| The tag | `NEW` | volt, top-left |
| The sports | `{Sport} {level}`, one per sport | each with its dot: one per line on the Home tile, two to a line where they fit in See all (home rows 18, 19); prose writes them *Padel 2,35 · Badminton 2,10*; none for a player with no level |
| Joined, 0 days | `Joined today` | Warsaw days *(a call)* |
| … 1 day | `Joined yesterday` | |
| … 2–6 days | `Joined {n} days ago` | *Joined 2 days ago* … *Joined 6 days ago* |
| … 7–13 days | `Joined last week` | |
| … 14 days and up | `Joined {n} weeks ago` | *Joined 2 weeks ago* … *Joined 4 weeks ago*; `{n}` = days ÷ 7, rounded down, at most 4 |
| See all, a sport with nobody | `Nobody new plays {sport} yet` | *Nobody new plays squash yet* |

### 31.8 Same vibe

| Where | Sentence | Note |
| --- | --- | --- |
| The tile, the % | `{pct}` | *98%*; one of 50%, 75%, 88%, 94%, 97%, 98% |
| The tile, in common | `{n} things in common` | *6 things in common* |
| … one | `1 thing in common` | |
| The tile, more tags | `+{n} more` | *+2 more*, dashed |
| The sheet, the title | `You and {nickname}` | *You and karol.t* |
| The sheet, the identity row | `{n} things in common · In your area · {km}` | *6 things in common · In your area · 0,6 km*; the area and the distance as the record writes them, or the kilometres alone, or nothing |
| A shared tag | `· you too` | as on the record |

### 31.9 The friend button

| Where | Sentence | Note |
| --- | --- | --- |
| On a sheet | `+ Add friend` · `Request sent` · `✓ Friends` · `Accept` | the + and ✓ drawn |
| The round button | *no words* | **+** white · **…** brown · **✓** green · **the envelope** volt |
| … its spoken name, unconnected | `Add {nickname} as a friend` | *(a call)*: the button's name, kept for tests (ADR-0198) |
| … request sent | `Request sent to {nickname}` | *(a call)* |
| … friends | `Friends with {nickname}` | *(a call)* |
| … they asked | `Accept {nickname}'s request` | *(a call)* |
| Request sent, the sheet | `Request sent` · `Cancel request` | from **…** |
| Friends, the sheet | `Remove {nickname} as a friend?` · `Remove friend` · `Keep` | from **✓**; the body is §29.1's, cited |
| A request refused from a stale card | *no words* | the button turns back to **+** *(a call)* |

### 31.10 Request lines

On the receiver's request card and its notice, in place of the group line (§29.2). **Since
2026-11-17 the card in Needs your answer draws none of them** (ADR-0205 §1, #816); the notice keeps
them, and the server still serves where a request was found:

| Found in | Sentence | Falls back to |
| --- | --- | --- |
| Same competitive level | `Your level in {sport} · {pct} even` | `Found you at your {sport} level`, when either no longer has a level there |
| New in Raketa | `Found you among new players` | — |
| Same vibe | `{n} things in common` (`1 thing in common`) | `Found you through your tags`, when none is shared any more |
| Top 10 | §30.8's `Found you in the {sport} ranking`, cited | — |

### 31.11 Top 10

| Where | Sentence | Note |
| --- | --- | --- |
| A sport with nobody ranked | `Nobody ranked in {sport} yet` | *Nobody ranked in squash yet*, in the row |
| The reader's own card | `You` | volt numeral and ring |
| A card | `{nickname}` · `{level}` | |
| The chip | `▲ {n}` · `▼ {n}` | none for no change, nor for *New* |
| The numeral | `{n}` | 1–10 |

### 31.12 The switch

| Where | Sentence | Note |
| --- | --- | --- |
| You, the switch | `Show me to new people` | on by default |
| You, under it | `Players you don't share a group or a game with can find you on Home, open your record and send you a request.` | |

### 31.13 Retired

| Was | Where | Why |
| --- | --- | --- |
| `Show me in General` · `Players who don't know you can see your place, open your record and send you a request.` | §30.8, You | replaced by §31.12's switch (ADR-0204 §2) |
| `Hidden from General` | §30.4, the place card | nobody is hidden from the ranking |
| `You've sent 10 requests to new people today. Try again tomorrow.` | §30.8, §29.2 | the daily limit goes, with `daily_request_limit` |

## 32. Needs your answer

> Added 2026-11-17 by [ADR-0205](../../adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
> §1–§2, PRD [#810](https://github.com/Raketa02/Raketa/issues/810). The sheet's words, and the
> envelope that opens it. Each section under the title keeps its own words: FRIEND REQUESTS is
> [§29.2](#292-friend-requests) and ASKED FOR A LEVEL [§29.5](#295-asking-for-a-level), moved off Home by
> the player app's [#816](https://github.com/Raketa02/Raketa/issues/816). *TO CONFIRM* and FRIENDS GAME
> join them with [#817](https://github.com/Raketa02/Raketa/issues/817), and the envelope's count with
> [#819](https://github.com/Raketa02/Raketa/issues/819). Rows marked *(a call)* were written in by #816.

| Where | Sentence | Note |
| --- | --- | --- |
| Home's header, the envelope | `Needs your answer` | its spoken name; the mark is drawn. #819 adds `, {n} new` while its count shows |
| The sheet's title | `Needs your answer` | |
| The sheet's ✕ | `Close Needs your answer` | spoken *(a call)*: a close is never just *Close* |
| The sections, in order | `TO CONFIRM · {n}` · `FRIENDS GAME · {n}` · `FRIEND REQUESTS · {n}` · `ASKED FOR A LEVEL · {n}` | each hidden at 0; the first two from #817 |
