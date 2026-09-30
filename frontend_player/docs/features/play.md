# play — Find a game, the builder, the pool, and the deck on Players

> The design record for `src/features/play/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**Play begins as a copy deck, and `challenges` beside it.** Nothing the matcher sends is
prose: what crosses is a `Term`, a `LivenessReason`, an `UnfilledReason`, a `Prompt`, a
`Standing` — and the app writes the words for all of them
([ADR-0106](../../../docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md),
[`the-words.md`](../../../docs/specs/matchmaking/the-words.md), cited by section and never
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
ADR-0107's _the whole handle or nobody_ — _the whole **name** or nobody_ since
[ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md),
which is how every _handle_ in this record now reads — with one implementation and a type that
will not take a shortened one, the one sentence a build says about a code it is too old to read, and
`counted()`, the single seam every counted phrase routes through so that a market with real
plural rules has one function to change rather than every sentence that counts something.

**What each Play control announces is copy too, and it lives with the rest of it.** An
accessible name is localisable, it quotes numbers that need §B16's formats, and it composes
codes whose sentences already have a home — so `accessibilityPresentation.ts` writes them
through the same _code → message, never message → message_ mechanism, and **a label is never a
template inlined in a component** ([`the-words.md`](../../../docs/specs/matchmaking/the-words.md)
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
its own box), `FactRow` and `ReasonLine`; `CardHead` is the social card's (and, through Play's surface, the
challenge screen's card's), and
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
so the pool draws one shape twice. **The two interest tags are tags on both list cards**
([ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §8):
_Wants to play you_ is bound to `INTEREST_LIFT` and takes its liveness twin's two words because
the two codes are one tag — #231's open decision #14 reversed first on the competitive card,
whose identity row has a slot beside the handle, and then on the social card, whose `CardHead`
draws the tag under the name line where the sentence _They already said yes to you_ used to
stand — and _You said yes_ is the reader's own act, a plain `base` tag off their own outgoing
list (`saidYesTo` over `useOutgoingInterest`, the deck's read), no code and no nudge. At most one
tag on a card: either interest tag over the coral one, because a fact about a person outranks a
fact about a list, and _Wants to play you_ over _You said yes_ should both ever be true — which is
a mutual, and a mutual is not on the list. The deck card draws neither. **Neither tag reaches the
card's spoken name** — the same booking the coral one has carried since #309: the body's merged
name is the identifying facts and the argument, and a tag clause is a gap named here rather than
a clause invented — see `IdentityRow`'s note. **The panel prints the
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
5.1's pressed state made permanent and stays refused, while the lifted card takes 5.1's
**marked** state in `voltStroke` — volt's meaning at a stroke's ratio, because volt itself is
1,25:1 on `surface` and would be no border at all. It is bound to **the tag being drawn** rather
than to `inclusion_reason` — to the tag's _kind_ and never its colour, so _You said yes_ draws no
outline — and it goes where the tag goes, which since ADR-0169 §8 is both list cards. The outline
can never appear on a handle saying something else, and Part 13 is discharged by the word either
way. Every ratio is derived in `Tag.test.tsx`.

**The court is one drawn object and two feature components.** `Court` (7.12) takes a Sport and
a box, draws the ground, the chrome and the seat **positions**, and **takes children in seat
order** — a `useCourtGeometry` hook was refused, because geometry that is _returned_ gets
adjusted at one call site and not the other. Over it, `CourtMini` draws read-only faces and
`CourtBuild` draws pressable seats, and they are **two components rather than a flag**: they
share every number and no behaviour. **The coordinates cannot be derived and H-25 is why** —
squash has no net, so both players stand on the same half and _seat 3_ is not where seat 3 is
in padel. That reaches the rules as well as the drawing: a seat's **side is read off seat
order, never off the picture**, and it **follows you across the net**, because a swap is
_change sides, never seats_. **The seat label is an identifier under a face** — sixty-four
characters of handle in a 46pt seat is about four, so it draws the **first three, hard, with no
ellipsis**, and the level sits beside them on the same line: a caption that told four faces
apart had four characters and spent one of them apologising for a word nobody can go and read
from there. The **sentence and the spoken name stay whole**, which is what keeps ADR-0107
intact: a truncation invents nothing. Under both, `domain/lineup.ts` holds
what somebody could be wrong about — `seatPlaces`, `seatIsLocked` / `seatIsClearable`, and the
**swap truth table**, which is a decision and never a write. **A tap on a seat trades, always**:
the `Swap players` switch above the court was removed on 2026-09-09, and with it the only reason
a tap had two meanings, because the forecast card's names row draws a face per seated player and
that is where a player goes to act on somebody now. Replacing somebody is the clear badge and
then the hole it leaves. Both **guard toasts** went with the mode — they refused a
_replacement_, your own seat and an accepted one having always been freely movable across the
net — so `seatIsLocked` answers _whether_ rather than _why_, and its one reader is the clear
badge, which is **not drawn** where it would be refused. **Volt means one thing per court**: the seat picked for a swap on the
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
count. **A press opens on an empty court**: it mints a record of its own, so whatever was
seated under the last one is orphaned and is discarded as the push is made. Popping back for
another look at the week is deliberately **not** that — the shell's stack is untouched, so the
session survives and the four are still there on the way forward — and what ends them is asking
for a new game. It is not the origin guard's confirm either: that exists because changing the
sport, the mode or the week would destroy a line-up _silently_, where this player pressed
_Build_, watched a search run and landed on a court. It is in the page rather than in
`ShellScreen`'s pinned slot, and the prototype's 2pt
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
swipe** — _the placement is struck by the deck's move to Players, and the refusal of the swipe,
the two-button card, the footer, the pass and one-sided-yes toasts and the endings' copy are
struck by the deck's redesign (#444, ADR-0169 §3–§7): the last paragraphs of this record are the
decision. What still stands below is the answer's posture — optimistic, a refusal returns the
card, offline holds the write — and the two endings' split on `players_in_range`_.
The gesture was refused **not on cost** — `RadiusSlider` already drags on the
built-in `PanResponder` — but because _Show them again_ was struck, leaving `PASS_SUPPRESS` at
thirty days with nothing that reverses one: a swipe would put the cheapest gesture in the app
on the most durable act in it. **No `react-native-gesture-handler` and no
`react-native-reanimated` are added** _(both are in the app since ADR-0176, for the radar's
field alone; the deck's drag is still on `PanResponder`)_, the leaving animation stays a leaving animation, and
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
([ADR-0154](../../../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md),
[#370](https://github.com/Raketa02/Raketa/issues/370)). The tap answers with the challenge the
two of them have — the one it just opened, or the one an earlier mutual opened that nobody has
finished with — which is what ended a player being told _you both said yes_ and left looking for
a game nobody mentioned. `mutualChallengeToast` — since retired into the yes screen, the last
paragraph of this record — named **Chats** and called the thing nothing at all: a mutual-born court
is `ON` in singles and a side short in doubles, so _your game is on_ and _your game_ are both
wrong for half the sports, while _they are in your Chats now_ is true either way. There was no
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

**Play's two ways through the tab are one control, and the count on it is the segment's** —
_struck by the deck's move to Players; the last paragraph of this record is the decision_.
`PlaySegment` was design-system **6.3**, specified since the document was locked and built for
this; its two halves move in opposite directions and that is the decision — _Find a game_ is
an **arrival** and calls the shell's reset, where _Match me_ is an ordinary push. The count is
your **own outstanding yeses**, filtered by the sport on screen so the number labels the deck
it sits above, and it moves on a tap's own response rather than on a refetch. The prototype's
number was people who had waved at _you_, and that number **cannot exist**: an incoming yes
never crosses the wire in either direction. It is the one read in Play that background-
refetches, because the rule against that is about orderings and a count has none — and it is
why the tab bar carries no badge.

**⚡Play's third screen is the builder, and a swap on it is a selection rather than a
request.** **It is called _Build a doubles_ or _Build a singles_, and its header draws nothing
else** — the same two words as the control on Find a game that opened it, because the control
names the screen it opens. Three wordings and two arrangements were tried to get there. _Build
the four_ / _Set up the match_ is one sentence in two registers and a word about a Sport a
squash court must never be told, with a third — _Complete the …_ — naming the state of the
court rather than the screen. Then the title was dropped and `Padel · doubles · for fun`
promoted into it, which put this screen and the pool under **one heading**. Then that line came
back as 10.3's eyebrow over the restored title, and read as the title said twice: _doubles_ in
both lines, the Sport already on the court in the picture and in its spoken summary. So it is
deleted, and **the cost is one word** — `for fun` against `competitive` is now stated on
neither of Play's inner screens, though the two draw different candidate cards. A court whose
search cannot be read is called something honest instead of a shape it is guessing at. The
chevron beside it is `ink` now, because it is the one control in that header and it was drawn
in the eyebrow's own grey. A finished search is pushed onto it — _"where a completed search goes"_, which #268
and #269 both declined to decide — and the push happens **when the latch lifts** rather than
when the response lands, because the wait is over the screen that launched it and the court is
what it lifts onto. Three branches fill the court and **two of them are one request**: ⚡ is
`POST /lineups`, and hand-seating somebody and then pressing ⚡ is the same request with
`locked_seats` on it, _"a property of what you send rather than of where you send it"_. Its
control says **Use Matchmaking**, one string where there were two: _Let the engine fill the
seats_ and _…the rest_ were a pair because the engine fills **around** locked seats, and
naming the act rather than the scope is true of an empty court and of one with three people on
it — so there is nothing left for a second label to correct, and the word is the platform's own
for the thing the button reaches. The
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
**And not on a challenge's fill** ([#429](https://github.com/Raketa02/Raketa/issues/429)): the
engine answers `GROUP` for any locked seat, and on that journey the locked seats are the people
who _said yes_ — nobody the organiser picked, and no trade made around them; the four are a court
being finished. So `optimisedForLine` is handed `completing` and says nothing for it, and the
ordinary builder keeps the line, which is `the-play-screens.md` §11.2's standing obligation.

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
[7.11](../design-system.md#711-the-balance-bar) takes an _advantage_ between two side
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

**The pool is opened on the list the court was searched under, and never on ⚡'s own record.**
`POST /lineups` returns exactly the people it seated — a court is its answer, not a list — so a
pool opened on the origin after ⚡ offered the one person just taken off a seat and nobody else,
from both doors: the hole a cleared seat leaves and _Pick players myself_. The builder's
`listSearchId` is the record it **arrived** on when that record has no `court`, which is the
shortlist _Find a game_ minted and which the fill rebinds the line-up away from and leaves in
the cache; on the challenge route the arrival is the fill's own answer, so there is no list to
prefer and the pool still opens on the origin — which offers nobody new, because that journey
mints no shortlist and only the backend can give it one
([#407](https://github.com/Raketa02/Raketa/issues/407)). **A pick off a list the court is not bound to
moves the court onto it** — `seatAll`, the way ⚡ rebinds, never `seat`'s line-up of one —
carrying the seats that list returned (`domain/lineup`'s `carriedOnto`) and the pick. The new
origin can vouch for nobody else: `POST /forecasts` and the send both cite one search, so a
seated player the list never showed leaves the court with the tap, and the pool **says so by
name before it**, in `replacingLine`'s own register. ⚡ seats from a wider pool than the
shortlist shows, so that player exists; the same sentence covers the strict list's people a
widened list did not return, and `POOL_LINEUP_COST` stopped promising the court _starts again_
on a rung, because it no longer does. The pool re-reads the court's own record beside its list
when the two differ, so a ⚡-built court is still marked where the gates have since said no.

**⚡Play's fourth screen is the pool, and the relaxation ladder is on it and on no other.**
**It is called _Pick players_ and its header draws nothing else**, which is the court's own
walk one screen on: the name was dropped for a day on the argument that a list of people with
an _Add to the court_ on every row says _pick players_ for itself — what that missed is the
screen next door, which had promoted the same line, so the two came out under one heading — and
the eyebrow that came back over it read as a caption on what the header card below already
draws.
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

**Nothing on this side reorders the list, and two tags mark it — a yes informs; it never takes
over** ([ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
§8). Somebody with a live yes towards the searcher is drawn **where the server placed them** —
the engine's `+14` on their rank key already puts them earlier than their Fit alone would, never
above a genuinely better pairing — tagged _Wants to play you_ with the green border, and the tag
travels with them under every chip. The **pin** that used to force them to the top of the served
order is gone with its tests: it touched no number, which was the whole of why it was not the
`+12` #231 struck, and it still put a 51 above thirty people at 80 on a list about who fits.
`poolOrder`'s module note keeps both refusals — the bonus's and the pin's — in writing, and
`orderPool` hands the served order back untouched. Somebody the reader said yes to is tagged _You
said yes_ and moved nowhere: the pool holds the same `GET /interest` the deck holds
(`useOutgoingInterest`, one cache entry, `select`ed two ways) and asks `saidYesTo` one row at a
time in the search's sport; the list moves on a deck tap's **own reply** (`outgoingAfterYes`), so
a builder opened straight after a swipe already carries the tag. Beside them, the coral **best
match** tag goes on the highest ✦ on screen — one card or none — and it is keyed to **the
ordering in force** rather than to a tapped chip, because `BEST_FIT` is withheld exactly when
the served order already is fit order and most searches therefore have no chip to have tapped.
It is hidden under the three orderings that are about something other than the number, and
where it and either interest tag fall on one card the interest tag wins, which is
`candidateTag`'s rule and not the ordering's. **A for-fun pool draws no _best match_** — the tag
sits in the competitive card's identity row and the social card has no slot beside the handle
for one — and draws both interest tags, as tags, under the name.

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

**A mutual naming a chat is the yes screen now, and the toast that stood in for it retires**
([#434](https://github.com/Raketa02/Raketa/issues/434),
[ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§1, §4). Tomek taps _Let's play_ on Marek's card; the card flies as it does; the reply comes back
`mutual` **and names a challenge**, and the phone becomes the challenges feature's yes screen as
**a mutual's** — `/chats/challenge/{id}/yes?which=mutual`, _Matched!_, the second face recorded at
the end of the challenges record — wherever Tomek is by then: the next card, another tab. **The
push lives with the mutation and not with the press.** `useSayYes`'s own `onSuccess` pushes
`yesRoute(challengeId, 'mutual')`, because the callbacks handed to `mutate()` are dropped the
moment the deck unmounts and the yes is optimistic, so a reply that lands after the player has
moved on would otherwise land on nobody — _a slow reply must not swallow the moment_. The card's
flight is not waited for, and a refused yes still returns the card exactly as before. **Why the
picture has no `vs`, and the deck is the place to say it**: the deck deals one person, and a
mutual is two people who chose each other — in tennis they will be opponents and in padel
partners with a side to fill, and both are true of the two of them, so the screen draws only
_you two_ and leaves the court's shape to the chat one tap later; a `vs` here would call a padel
partner an opponent a second before the room calls him a partner. **The doors, from the deck.**
_Later_ and Android back **pop** — to the deck's next card, or to wherever the reply found the
player. _Open the chat_ waits on the button for the room exactly as after a challenge and lands
as **[Chats list, the room]** by **the tab's own move** (`openTab`), since the list is nowhere
under the deck: the shell lays `[Chats list]` down, the Play session ending on the way as it does
on any tab press, and the room is pushed over it, so back from the room is the list with nothing
behind it. **Play keeps its held deck** in the sense the shell already gives a tab press: the deal
is Query's, keyed by the ask, so Play entered again on the same ask finds the same hand with the
next card up and deals nothing — and a deal dealt on an improvised week is a different ask once
the session has ended, exactly as it is after pressing the column. **What retires is one
sentence.** _You both said yes — {name} is in your Chats now_ is gone with its test; `yesToast`
answers `undefined` for a mutual naming a challenge, and that is a decision and not a gap. The
other two — a one-sided yes, and a mutual naming no chat — keep their words to the letter and stay
toasts raised from the press, with `deckPresentation.test.ts` pinning both verbatim and
`deck.test.tsx` asserting neither moves off the deck: a full-screen celebration must never
overstate what happened, and a mutual naming nothing is one answer covering two causes the wire
will not tell apart (ADR-0154 §3). **Under the router harness one walk is written as an offline
yes** — made in a tunnel, held by `networkMode: 'online'`, answered once the player has gone to
Chats — because the harness runs every pending timer on every navigation, and a reply merely slow
to arrive across a tab press is timed out by the walk rather than answered late by the server.
**Not seen on a device** — the author checks the screen against `2_match_from_matchme.png`.

**The deck lives on Players, and Play is Find a game**
([#443](https://github.com/Raketa02/Raketa/issues/443),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §1).
_Match me_ was the second Play screen — a segment deep, behind a declaration — and it is the
whole of the second tab now: `DeckScreen` mounts at `/players`, named by that route file exactly
as Find a game is by its own, and **moved as it was** — today's card, today's two buttons,
today's endings and today's footer — so that the card can be replaced on a surface that already
lives in the right place ([#444](https://github.com/Raketa02/Raketa/issues/444)). What changed is
the frame around it. **There is no title row**: the _Deck | Radar_ toggle is the header, in
`ScreenHeader`'s lead slot with the right slot left for the chip, and it is **component state
and not two routes** — Radar is a pane with one muted line, _Radar — not built yet_, in the
shape a placeholder tab's line has, because a map needs a location precision the platform does
not hold and the Radar is its own spec (§9); a route would make it somewhere the tab could open
on, and Players always opens on Deck. The screen's memory is three `useState`s now: the pane,
the card leaving and the card the sheet is over. **Sport chips only when there is a choice** —
`rated.length >= 2` — so a player rated in one sport sees the mock exactly and a player rated in
none still reads _Rate a sport first_, which the entry gate makes unreachable and `sportOnScreen`
represents anyway. The toggle in the lead slot takes `flex: 1` so its two segments have a width
to share; **not seen on a device** — whether that reads as the mock's compact pill is the
author's to check against `game_card_and_details/players/`.

**No declaration is read, asked for, or needed on the deck, and the intent term's gap is the
surface's** ([#443](https://github.com/Raketa02/Raketa/issues/443), ADR-0169 §2). `POST /deck`
scores every deal under the fun ruler for every viewer, so `DeclarationInterstitial` and
`DeclarationStanding` have left this screen, `findAGameStanding`'s _undeclared_ is not a state of
it — it reads `sportOnScreen` alone — and the deal's question dropped `intent` from its key:
`DealtUnder` is the radius and nothing else, because a declaration that changes no deal must not
deal again. The intent term stands down on every card as `NOT_READ_ON_THIS_SURFACE`, the
contract's fourth `DegradedReason`, with a sentence of its own in `degradedPresentation` that
blames neither person — the two features that spell the union both gained the member, so the
sheet's not-counted block keeps its row rather than drawing an out-of-date gap. The declaration
components stay for Find a game, with `PlayDeclarationSurface` narrowed to the one Play surface
that still writes — `DECK` stays in the contract for the events that carry it — and the
interstitial's gloss stopped naming _Match me_ as a reader: what reads the declaration now is
somebody else's search, and the court a mutual opens (§8).

**And the deal runs on the profile's week, so the ask carries none**
([#443](https://github.com/Raketa02/Raketa/issues/443), ADR-0169 §1). The deck was reached from
the screen the week is edited on and dealt on the working copy; it is reached from a tab of its
own now, the tab press ends the Play session on the way, and nothing can hand it an improvised
grid — so `DeckAsk` carries no `sentWeek`, `searchKeys.deck(sport, under)` carries no week, and
`availability_override` is never sent from here. ADR-0169 §1 states the consequence (_the deal
runs on the profile's week_) and not the removal; the removal is this record's, on the ground
that a key parameter nothing can set is a parameter a later session will try to set.

**Play lost its segment, and the tests moved by name**
([#443](https://github.com/Raketa02/Raketa/issues/443), ADR-0169 §1). `PlaySegment`,
`/play/deck`, `DECK_ROUTE` and `MATCH_ME_TITLE` are gone; Find a game draws nothing above its
mode section; `enterPlay` has no caller outside the shell and is no longer on its surface; the
Play stack is `[Now, Find a game]` and nothing in the app links to a deck route under Play.
_Match me_ survives as a word only in _Matched!_. In `deck.test.tsx` every `/play/deck` became
`/players`, the deck is entered through the bar and re-entered by leaving for Play and coming
back, _the segment_ and _the declaration_ blocks retired, and a _Players, the tab_ block asserts
the column lit and rootless, Deck on arrival and on return, the Radar pane, the chip row's
presence rule, and an undeclared player dealt with nothing asked.

**The deck is the swipe deck the mocks draw — a full-bleed card, a drag with two stamps, a
counter and a chip, two endings and Show them again**
([#444](https://github.com/Raketa02/Raketa/issues/444),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §3, §4,
§5, §7, §8). Ania opens Players: a volt chip top-right says _2 want to play you_; the card is
Filip's photograph edge to edge under a wash rising from the bottom — _2,60 · PADEL_ top-left in
the existing 40pt figure, _✓ on court_ top-right, his name in the card's one 24pt role beside the
existing Fit pill, _In your area · 2 km · around this week_, his intro in quotes, four tags of
which the shared one leads in volt with _· you too_, three tiles, and _8 left · 12 yeses to
give_ floating over the card's foot, with two real cards behind. **`DeckCard` is
rewritten and makes no case**: no reason line, no concern, no _They already said yes to you_ and
no _Wants to play you_ tag — the liker is unmarked and placed by the nudge (§4), and the count of
them is the chip's. `deckCardFacts` reads the card once for both registers and
`deckCardPresentation` holds its words: the meta line's third clause is `RECENT_ACTIVITY`'s own
words lower-cased and drawn only on the code (ADR-0107 §3 intact — never _active now_), the
intro is `card.intro` inside the drawing's own quotation marks and the gap closes where there is
none (ADR-0170; the field crosses now, mapped and omitted where absent — and
[#445](https://github.com/Raketa02/Raketa/issues/445) holds the shortlist and pool cards to
never drawing it, drawn or spoken, whatever the card carries), the tags are
`socialTagOverlap` re-ordered **shared first** by `domain/deckTags` so the volt one is never cut
off, and the tiles are always three — _Balance_ from `predicted_balance.pct`, _Reliability_ the
Player Score, _Overlap_ the shared-slot count — with a dash where a number is absent, spoken only
where it is not. The wash, the name role, the stamps, the pill
radius, the three round buttons, the tiles and the tick are Part 16 rows and `theme.ts` values
in the same commit, each fenced _for the deck card only_ except the tick, which changes the
mark's drawing wherever `OnCourtMark` is drawn (`_shared.md`). **The intro is set upright**: the
mocks set it in italics, and this app loads no italic Archivo — a `fontStyle` on a custom family
is ignored on Android and synthesised on iOS — so the marks carry _their words_ and the ninth
font file is the author's call at the look.

**A swipe is an answer, and the buttons remain the path** (ADR-0169 §3). `DeckStage` is
rewritten on `PanResponder` and `Animated` with the native driver — no
`react-native-gesture-handler`, no `react-native-reanimated`, as the swipe row and the slider
already prove _(and still none for the stage after ADR-0176 brought both in for the radar's
field)_ — and it never claims the press: the card is a door (a long press opens the
record), and it claims a move that has travelled the swipe row's own intent across and further
across than down, in either direction. The card follows the finger and turns; the two stamps —
_LET'S PLAY_ in volt top-left, _NOT TODAY_ in white top-right, the buttons' own words uppercased
by the style — fade in with the drag and are full at **95pt**, the mock's threshold; a release
past it asks the screen, which answers `taken` (the card flies in the drag's direction, from
wherever the finger left it) or `withheld` (it settles back, `motion.settle`); short of it, it
settles. `deckStageGeometry` holds the arithmetic as numbers. **One light haptic** as the finger
first crosses the threshold — the haptics port's second verb — and none under reduced motion,
where nothing moves and the answer still lands, because `onLeft` is a fact and not an animation's
courtesy. Two real cards stand behind the top one, offset and scaled back, only when that many
remain, hidden from assistive technology; the stage takes the height the phone gives the deck
(`ShellScreen`'s new `fill`), so all three cards are one size. The three round buttons under the
stage — ✕, i, 🎾 at the mock's 54, 42 and 66 — do the same two things and one more, named for the
person and never removed: a screen reader consumes the drag, and `deck.test.tsx`'s _cost no new
gesture dependency_ became _the three buttons remain and answer_. **i and the long press open
`PlayerRecordSheet`** with the deck's pairing in hand — subject, sport, distance, the reader's own
area, the tag overlap and `pairing: { fit, onExplain }` — so _why this Fit_ lives behind the
sheet's fit row; the direct long-press → `WhyFitSheet` is gone.

**A release reveals the card under it, and nothing blinks.** The stage is never remounted per
card: every card on it is one keyed element for as long as it is on the stage, with a `drag` and
an `arrival` of its own, and when the top card has gone the card behind becomes the top card
_as the element it already was_ — its photograph is not decoded again, nothing fades in over it,
and on the frame it takes over it stands exactly where it stood behind, from where the arrival
(`motion.rise`, a move and never a fade) brings it and the whole stack forward as one motion
(`stackLift`, `stackScale`). `DeckCard` holds its side: one `Pressable` in front and behind,
inert and no element behind, so taking on the long press does not throw the drawing away. And a
card that has **gone** stays where it went until the deal takes it away — the screen clears
`leaving` the moment it hears `onLeft` and advances the deck a tick later, and the _comes back
straight_ reset is for a card a refusal returned, not for one on its way out. Each of the three
was a blink between the release and the card under it: the answered card flashing back at the
centre, the next card starting from `opacity: 0` over the third, and its photograph mounting
again.

**The stamp and the card leaving are the feedback, so the pass toast and the one-sided yes toast
retire**; `passedToast` and `interestToast` survive only as the spoken result of every answer —
`passedAnnouncement` on the press, `interestAnnouncement` on the reply — through
`AccessibilityInfo.announceForAccessibility`. `mutualToast` (a mutual naming no chat) stays,
verbatim; a mutual naming a challenge is the yes screen as before, pushed by the mutation.
`yesOutcome` decides between the three off the reply's own shape. `DECK_FOOTER` retires: the hint
line on the card names the drag, the buttons and the long press.

**The card says less, the counter sits where its box said, and the yes is a drawn ball**
(2026-09-15, the author's look at the deck on a device). Four things off the first build.
**The _Shared tags_ tile goes**, and the row is three: the tag row directly above it already leads
with the shared ones in volt and _· you too_, so the count was a number restating what the eye
had just read — `deckTiles` returns three, `sharedTagCount` and its three spellings of absence
retire with the tile (the row keeps them), and the fourth key leaves the union so a tile with no
words cannot come back by accident. **The hint line goes**: _Drag the card, or use the buttons ·
long-press for the full record_ was a sentence of instructions on every card, and the three
buttons under the stage — the **i** among them — are the paths it named, standing where a
first-time thumb finds them; `DECK_HINT_LINE` leaves the public surface. **The counter is
centred over the card's foot**, which its box always said (`alignItems: 'center'`) and the pill
overrode: `DeckPill` carried an `alignSelf: 'flex-start'` of its own, and a child's `alignSelf`
outranks its parent's `alignItems`, so the counter hugged the card's left edge — the pill now
hugs its words and lets its bed place it, the header's right slot pinning the chip right as
before. **The yes's mark is drawn** (`DeckBall`): the 🎾 was an emoji as text, whatever the
platform substitutes in its own greens, and **clipped at the top** because a line box the height
of the font size is shorter than an emoji — the one of the four seen on the device before the
author asked. It is now a white outline with its two seams, computed in `Star.tsx`'s way, at
Feather's proportion (2 in a 24 box) so it is as heavy for its size as the ✕, on 6.1 `primary`'s
own white-on-`coralInk`; not volt for a tennis ball's sake, because colour is picked by meaning
and never by appearance. Its box is `size.deckAnswer.ball`, the 26 the emoji had, so the disc's
proportion is still the mock's. `deckCard.test.tsx` holds the seams to the ball's own circle.
The ADR's §7 still reads _four tiles_ and _🎾_; it is the record of what was decided then, and
this paragraph is the record of what changed.

**The counter is true and the chip names nobody.** _{left} left · {give} yeses to give_ is
`cardsLeft` — `pool.remaining`, which the envelope carries on a deal only, plus the cards
unanswered in hand — and `yesesToGive`, the cap less the outstanding off `GET /interest`, whose
mapper **stops dropping the cap** and carries `ttl_days` beside it (`SportInterest`); the first
half counts down per answer and the second on the yes's own reply, with _8 left_ alone until the
read has landed rather than a nought invented. The chip is `pool.want_to_play_you`, drawn at one
and above in the header's right slot, and **decremented when a yes on a card carrying
`inclusion_reason` comes back mutual** — a cache write on the held deal in `useSayYes`'s own
`onSuccess`, because the reply may land after the screen has gone. **At the ceiling** the client
pre-empts the one refusal it can read (`domain/yesBudget`): `give === 0` on a card with no
`inclusion_reason` is withheld — the card settles, a toast says the ceiling in the same sentence
a `409` says it — and a liker's yes is sent whatever the count, because it closes a mutual and is
never outstanding. The server stays the authority: a `409` still returns the card.

**The next hand is asked for at two and appended** (§5). The held deal is hands folded onto one
another (`withHand`): `refetch()` is no longer a replacement, every `DealtCard` keeps the
`search_id` it came off — the origin key its answer cites, and a card from the first hand may be
answered after the second arrives — and the envelope, the pool and the prompts are the latest
hand's. `domain/deckHand` reads the standing off the flattened list: the top card, the two
behind, the unanswered count, and `latestHand`, which is what tells a hand of nought apart from a
hand answered out — an empty hand under unanswered cards is the ending waiting its turn.
`wantsTheNextHand` fires at two while the pool says there are people and never after a hand that
brought nobody; a hand answered out with nothing appended deals again as before, and only a hand
that comes back empty is an ending. **Answers are keyed by card and not by person**: the same
player dealt again on a later `search_id` is a new card, dealt and not hidden, which is what a
reset relies on; the same card twice — the same person on the same `search_id`, which the route
never does — is dropped on append so the effect cannot ask for ever. **A reset replaces, and it is
the one act that does**: `useResetDeck` posts `POST /deck/reset {sport}` and then resets the held
entry (Query's own back-to-initial-and-refetch) rather than refetching, because appending the
fresh hand would hide exactly the people the player asked to see again.

**Two endings, and only one offers the reset** (§5). `DeckEnding` draws _You have seen everybody_
as the mock — _Nobody new in {radius} km today. Your yeses stay live for {ttl} days, so the ones
you gave are still working._, the radius off the deal and the days off the interest row, **21 and
not the mock's 14** because the number is read from the wire and never held — with **Show them
again** (`secondary`) and **Try the radar** (`dark`, flips the toggle); a refused reset leaves the
sentence above the button and the button is the retry. _Nobody in range yet_ keeps the pool
description and _widen it in You_, gated by `radius_clamp` as before, **without** the reset,
which would deal nobody. `outgoingYeses` retires with the footer: what the player has out is the
counter's second half now. **Not seen on a device** — the author checks the build against the
nine mocks under `game_card_and_details/players/`, and the wash's legibility over a photograph at
the name, the stamps' volt stroke over a photograph's top, and the counter straddling the card's
foot are the three things to look at first.

**One decimal everywhere — the deck card, the record's identity line and the why-fit sentence
print the same distance** ([#461](https://github.com/Raketa02/Raketa/issues/461),
[ADR-0174](../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §2).
`distance_km` is a one-decimal number now on every candidate — measured between two **drawn
spots**, one fixed point inside each player's coarse area, never below `0.1`, still omitted when
the distance term stood down — and Filip's card reads _In your area · 1,9 km · around this week_
where it read _2 km_. One formatter prints it, `formatDistanceKm` beside the level's in
`shared/formatting/ratingFormat` — one decimal, the comma, the unit, the trailing nought kept —
because the decimal comma has one home and _the same number for the same person_ is only true
while every surface prints it through the same function: `metaLine`, and so the social card, the
deck card, the challenge card's row and every spoken label composed over it; the record's
`identityLine`; and the why-fit sheet's `distanceReason`. **The sheet's sentence reads the
candidate's `distanceKm` and never the evidence's `km`**: the evidence's kilometres are the
engine's input — whole, cell to cell, what the Fit was scored on — and they stay whole on the
wire, so a sheet that printed them would say _4 km away_ under a card saying _4,3 km_, which is
the disagreement the rule exists to remove. `reasonLine` therefore takes the pair beside the
evidence (`PairFacts`, one field), required rather than optional so the `saysSomething` that
selects a line and the `reasonLines` that prints it cannot answer from different facts; a fired
distance term with no `distanceKm` — a row the contract does not produce — says nothing rather
than falling back to the engine's number. _In your area_ is still code equality and nothing
else on the card, the record or the sheet moves. Nothing prints a whole kilometre any more, and
the tests moved by value: the mock's own _1,9 km_ on the deck, _0,6 km_ for somebody in the
reader's cell on the record, and a sheet fixture whose candidate says `4.3` over an evidence
saying `4`, so the wrong number has somewhere to be read from.

**The Radar pane — the field, the rings, the three states by width, the ladder, fly-to and
selection, the card, the footer** ([#463](https://github.com/Raketa02/Raketa/issues/463),
[ADR-0174](../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §1, §3,
§5 and §7, [`the-radar.md`](../../../docs/specs/matchmaking/the-radar.md) §7, the words §26, the
sixteen locked mocks). The pane that said _not built_ is the map of the night: Ania at the
centre, a volt-ringed 34 pt tile labelled _you_ a little above the middle, rings at 2, 5 and 10
km, fourteen padel faces around her at 18 km across, _3 want to play you_ top-right, _14 players
in view · all of them_ in the footer over the privacy line. `RADAR_LINE` retires from
`deckPresentation` and from the public surface; the placeholder's walks in `deck.test.tsx` now
find the cluster's _Back to you_. **The reading** is `POST /radar` through `api/radarApi`,
`mappers/readingMappers` (the deal's mapper over the deal's shape, plus `bearing_deg` and
`ratings[]` — a row with no spot is dropped, a rating in a sport this build cannot name is
dropped and the row stands), `use-cases/readReading` and `hooks/useReading` — keyed
`searchKeys.reading(sport)` with **no radius in the key**, because a reading is held five minutes
and costs the pool nothing where the deal is held for ever and spent by a second ask;
`refetchOnWindowFocus` and `refetchOnReconnect` off for every ranked list's reason, `retry: false`
because a reading records a search. The chip is the reading's `pool.want_to_play_you` through
the deck's own sentence, **the deck's number by the deck's rule** (§5), so the two panes agree by
the server's arithmetic rather than by sharing a number on the client. **The geometry is pure**
(`domain/radarGeometry`, 25 assertions without a renderer): the ladder _1,5 · 3 · 5,4 · 10 · 18 ·
30 · 55 · 110_ with the widest stop the first at or above 2,2 × the reach and the opening the
first at or above 1,8 × (30 and 18 at 10 km; 30 and 30 at the harness's 12), the floor 1,5;
`nextStopIn` / `nextStopOut` snapping from wherever a pinch left off and `undefined` at the ends;
the three states with a **dead-band above each threshold only** — 10 is closer and 5,4 is
closest so a ± landing on a stop always lands in the state the stop names, and a state already
held survives until the width is 3 % past the line — which is the one reading of _about 3 %_
that never contradicts the ladder; the ring rule (radius ≥ 26 pt and ≤ 3,5 field widths from 1 ·
2 · 5 · 10 · 20 · 50, two or three at every stop and never a bullseye); a row's point from its
distance and bearing, north up; `inView` on the **point**, never the card — the point where the field
draws it, tested against the box that stops at the footer's top edge; the flight's target (the
3 km stop, centred on the row); the reach's edge (`boundCentre`, `rubberBand`); the drag
(`dragged`, no inertia) and the pinch (`pinched`, around the fingers, between the floor and the
widest stop) as functions of where each started; and the field's one transform,
`containerTransform`, with its inverse `viewFromTransform` and the flight's `betweenTransforms`,
held to `toScreen` for any view by the test. **The view is two
kilometre-facts and nothing in points** — the kilometre point at the field's **focus** (42 % of
the height, where the viewer sits at home and ±, the pinch and the flight zoom around; zooming
around the true centre would walk the viewer down the screen on every press) and the width in
kilometres — so the same view on a wider phone sees more of the same picture at the same scale.
**The field** (`radar/RadarField`) lays every tile out **once** at the home view's scale inside
one `Animated.View` whose native-driven transform — the scale and the two offsets — carries
the lot to the live view; every tile counter-scales by one shared `Animated.divide(1, scale)`
about a 0 × 0 anchor at its point, so a face is always 24 or 30 pt and a card ~190 whatever the
pinch is doing, and nothing is laid out again until a gesture ends. The rings, the footer's count
and the cluster's counter are JavaScript's over a `live` view kept in state beside the native
values — a hairline scaled by twelve is a smear — and during a flight they read the view off the
**same** linear interpolation of the transform the native side animates, so the two land
together. _(The mechanism in this sentence and the next — the native driver, the 0 × 0 anchor,
the `live` state, `PanResponder` — is what the first look on two devices disproved and ADR-0176
replaced; the shape survives and the thread does not, in the paragraph at the end of this
section.)_ Raw touches on `PanResponder`, never on the press (a face and a card are doors): one
finger past the intent distance is a drag with no inertia that rubber-bands past the reach and
settles back over `motion.settle`; two fingers is a pinch, continuous between the floor and the
widest stop, **around the fingers** — the kilometre point under their first midpoint stays under
their midpoint. A tap on empty field is a hidden background press under the tiles: deselect,
keep the zoom; ◉ is the accessible way to let somebody go. **The flight** — `motion.flyTo`, 400
ms, `easeDecel` — lands at 3 km centred on the row and **selects on landing**; under collapsed
presentation the view is simply there. The parent is told where a gesture, a ±, a flight or ◉
**ended** and never each frame. **The view is kept while the app lives** — `store/radarView`,
process-scoped like `playPreferences` because Players opens on Deck every time (ADR-0169 §1)
and the pane's own state dies with every tab press, which is the one moment the spec wants the
view to survive; `undefined` is home, because home depends on the reach the store never learns.
**The selection is kept by sport**, so a sport switch clears it by construction and keeps the
view, and _a selected player absent from the next reading is deselected silently_ is
`domain/reading`'s `selectionOn`, applied at read. `drawOrder` paints farther first and the
selected last, above everybody; `sportRows` lifts the reading's sport to the top of the card's
rows and keeps the registry order under it. **The frame is the pane's own** (`radar/RadarPane`):
the same header — `PlayersToggle`, one component for the two panes, the chip, the sport chips —
over `RadarGround`, the app's **third dark surface**, with no scroller at all, because a page
that scrolled under a pan would be two things following one finger; the toggle, the chip and the
chips take their on-dark repaints (`Segment` and `Chip` gain `onDark`, `SportChips` forwards it),
because mock 1 draws the toggle over the night and the mocks are the design. **The card**
(`radar/RadarCard`, mocks 10–14) is drawn line for line: a 34 pt face, the name in `h2`, the
distance in mono `tiny`, the on-court mark in a fourth placement (`radar`: `tag` words in
`mintInk` on paper, no on-media shadow); a rule; one sport row per rated sport — dot, eyebrow,
level in `num.s`; the Fit pill with **`fit` after its figure** (`FitPill` gains `trailing`,
mock 13's order beside a chip that ends in its word) and the reliability chip on `paper2`, a mono
figure and a word, _—_ where nobody was watched; _N tags in common_ in `mintInk` or _no tags in
common_ muted, derived by `socialTagOverlap` — **and not drawn at all where the engine compared
nothing**, because _no tags in common_ is a claim and _we do not know_ is not; _Tap for the full
card ›_ in `coralInk`. The whole card is one button named by the §26 sentence — `radarTileLabel`
in `accessibilityPresentation`: _Filip N., 1,9 km, Padel 2,60_ — the same name the face carries
at the other two widths, so a listener follows one person through every state. A tap opens
`PlayerRecordSheet` exactly as the deck's _i_ does, with the reading's envelope in hand for the
Fit sheet; the foot is [#464](https://github.com/Raketa02/Raketa/issues/464)'s. **The footer**
(`radar/RadarFooter`) is laid over the field so the rings run on beneath it and tells the field
its height, which is what _between the header and the footer_ means for the count; its four
states are `radarPresentation`'s sentences — the headline and _+N off screen_ / _all of them_,
the hint opening with the privacy line at every width and switching on the **zoom state** and
never the selection, _Nobody within 10 km plays padel yet_ with §17's widen sentence, _Looking
around…_ over the privacy line with the tile and the rings already drawn, and _The radar couldn't
load_ with _Try again_ as 6.1's on-dark button in the hint's place. **The cluster**
(`radar/RadarZoomCluster`) is three 34 pt squares on a bed of its own — `radarControl`, ink at
half strength, the one dark-on-dark tile in the app, measured off mock 15 — with the counter
between the first two, `formatWidthKm`'s one decimal below ten and whole above, always drawn;
± greyed at the ends; ◉ drawn as two circles, since Archivo ships no U+25C9. **The theme** gains
the two ground colours measured off mock 1 (`radarGroundCentre`, `radarGroundEdge`, hue 199°
beside the yes ground's and not that ground under a second name — `radarGround.test.ts` derives
every ratio their comments state), `radarControl`, `num.tiny` (the radar's small mono), `size.radar`
and `motion.flyTo`. **Tested** through the router harness with a served reading (`radar.test.tsx`,
the field laid out at its handler because `fireEvent` treats a responder's _no on the press_ as
disabled — `swipe.ts`'s finding, and `test-support/radarTouch` drives a drag and a two-finger
pinch the same way): the three states at three widths, ± walking the ladder and greying at the
ends, a tap flying, landing at 3 km and selecting, the selected card surviving a zoom-out, the
field deselecting and ◉ homing, the footer's numbers at home and after a flight, the chip, the
sport chips refetching and clearing the selection while keeping the view, the empty, loading and
failing readings, the view across a tab switch, the pinch and its snap, the drag and the rubber
band, reduced motion, and the record sheet from a card. **Not seen on a device** — the author
checks the build against the sixteen mocks at three widths; the counter-scaled anchors under a
pinch, the rings' JavaScript frame beside the tiles' native one, and touches landing on a face
hung off a 0 × 0 anchor on Android are the three things to look at first. **Four calls the
records did not make**, each one sentence in one place, for the author to keep or reverse: the
empty reading's hint keeps the privacy line first (user story 26's _always_) with the widen
sentence after it; the card draws no tags line where the engine compared nothing; the face's
corner is `PlayerPhoto`'s third of the box rather than the spec's 6 pt, because that rule has
one owner; and ± and the flight zoom around the **focus** — the viewer's 42 % — where §7.6 says
_the screen's centre_, because a zoom about the centre walks the viewer up the screen with every
press and mocks 5 and 7 hold the tile still across two widths. The root spec is not this app's
to amend; the sentence stands there until it is. **A retry** reads _Looking around…_ while it
is on its way, not the failure it answers — the spec is silent, and a wait spent under the
sentence it is meant to answer is the wrong one.

**The sheet's foot on the radar** ([#464](https://github.com/Raketa02/Raketa/issues/464),
[ADR-0174](../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §4,
[`the-radar.md`](../../../docs/specs/matchmaking/the-radar.md) §5, `the-words.md` §26). The
record sheet reached from a radar card ends in **Not today** · **Let's play** — the deck's two
words through `DECK_ANSWER_WORDS`, `secondary` and `primary`, the swipe's reading order, spoken
with the person's name as the deck's buttons are — or in what already stands between the two.
`PlayerRecordSheet` gained one optional slot for it, `foot`, which the radar fills with
`radar/RadarSheetFoot` and the deck's _i_ and long press fill with nothing
([`player_record.md`](player_record.md)). **The relation is a fold, and the fold is
`domain/standingRelation`'s**: four facts from three places — the row's `inclusion_reason`, the
reader's outgoing and mutual lists, and the challenges feature's answer to _do we share a
court_ — and one precedence, **matched › court › liker › said yes › open**, written in one place
because a component holding four `if`s is one refactor from two buttons over a match. Matched
outranks a court because a mutual-born court is the ordinary case and the door to the chat is
what the reader earned; a court outranks either yes for the cool-off's own reason — _a rematch
is arranged in the chat the two already have_ (ADR-0169 §6); a liker outranks the reader's own
yes for the builder card's reason — both true is a mutual the lists have not caught up with.
The fold hands the court back on its own arm, so the foot draws it without narrowing a value
the fold already had. The feet: a stranger gets the two buttons; a liker gets _Wants to play
you_ — §10's tag, the builder's, reached through `livenessLine('INTEREST_RECEIVED')` and never
re-typed — above them; the reader's own live yes gets the plain _You said yes_ tag beside
**Not today**, and that pass **does not take the yes back** — nothing does, a yes lives its 21
days — it says _not to my deck_, which is what a pass has always meant (ADR-0128 §1); a match
gets _You're matched_, the one sentence this surface writes for itself, and **Open the chat**
where the court has a room; a court gets its own line — the Chats row's `standingLine`, the
challenges feature's words — and no buttons. A _not today_ the reader gave earlier lands on the
two buttons: **no route anywhere returns a pass**, so the client cannot tell a stranger from
somebody passed on, and the spec asks for the same two either way — _Let's play_ lifts it.
**The mutual list crosses now**, ids per sport under its own name (`MutualInterest`,
`matchedWith`, `useMutualInterest`), and it stays the one list _You said yes_ must never be
drawn from. **The court is the challenges feature's answer** — `useCourtWith` over its own
`domain/courtWith`, whose bound on _one behind them_ is argued in
[`challenges.md`](challenges.md) — and the court's id crosses one seam while the room's id
crosses the other (`useChatDoor`), meeting at the surface as ADR-0149 §3 has the game screen's
door meet. **Two calls the records did not make**, each one sentence to reverse: matched over
court, which means somebody matched on the deck inside the last 21 days reads _You're matched_
rather than the court line while the two share one; and at the cap the sheet closes and the
sentence is a toast, as on the deck, rather than a note inside the sheet — the same closing
every press gets.

**An answer from the sheet is the deck's own, with the reading for its origin** (#464, ADR-0174
§4). `hooks/useRadarAnswers` sends `sayYes` / `sayNo` with the **reading's** `search_id` as the
Origin key; the cap is withheld first by the deck's rule; the row is **marked on the press**
(`domain/reading`'s `withAnswer`, in the mutation's own `onMutate` so the sheet's closing cannot
drop it) and unmarked on a refusal; and the reply settles through **`settleYes`** — the yes's
cache effects pulled out of `useSayYes` so the deck and the radar apply one patch: the count,
the outgoing list, the mutual list, every held deal's chip and the held reading's chip
(`oneFewerWaitingOnReading`, keyed to the answer's sport) on a liker's mutual, and the yes
screen pushed for a mutual naming a challenge. **The press side is one module too** —
`components/answerFeedback`: `withheldAtTheCap` with `CAP_REACHED_SENTENCE`, `sayPassed`,
`sayYesOutcome` — called from the deck's `answer` and the pane's, so the two surfaces cannot
drift about who may fly or what is said; `AnswerNotes` draws the amber _resumes_ and the
refusal's sentence for both, in the radar's gutter under the header because the pane has no
scroller for them to sit above a card in. **The sheet closes first on every press**, because a
`Modal` sits over a pushed screen and over the toast; the chat door is pushed by the pane after
the sheet is down. The card's last line then reads _You said yes ›_ or _Not today ›_
(`ANSWERED_LINE`: the tag's and the button's words with the door's mark) in place of _Tap for
the full card ›_; the person stays on the radar and the face never changes. **Tested** through
the router harness (`radar.test.tsx`, _the sheet's foot_): each relation's foot and its buttons
in order, the liker's line only with `inclusion_reason`, the door opening the room and absent
without one, a court named and a stale ended one released, a yes and a pass posting with the
reading's origin and marking the card while the row stays, a radar yes minting no deal and
touching no held one, the said-yes foot on reopening off the reply with no second read, a
refusal taking the mark back, a mutual naming a challenge pushing the yes route, a mutual naming
none toasting, the cap settling a stranger and flying a liker, and the chip counting down on a
liker's mutual given from either pane; `deck.test.tsx` holds the deck's _i_ and long press to no
foot. **Not seen on a device** — one yes, one pass and one mutual are asked for a look.

**The field moves on the UI thread, and the card is the selection's alone**
([ADR-0176](../../../docs/adr/0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md),
[`the-radar.md`](../../../docs/specs/matchmaking/the-radar.md) §7.3–7.5, §7.9, the words §26).
The first look, on an iPhone simulator and an Android phone, found the field's mechanism and not
its shape: on iOS every face grew with the pinch, because React Native draws **no transform on a
view with no size** (`BaseViewProps::resolveTransform`, the new architecture) and every tile's
counter-scale hung off a 0 × 0 anchor; on Android a drag came apart, because the `live` view was
written to React state on every frame, the whole field re-rendered per frame, and a re-rendered
`Animated.View` swaps its animated node — restored to the identity, re-pushed a frame later.
`RadarField` keeps its shape and changes its thread: the three values of the one transform are
**Reanimated shared values**, written by `react-native-gesture-handler`'s pan and pinch
(simultaneous; the pan waits the swipe row's intent distance, so a face, a card and the empty
ground are still doors) and by the flight — `withTiming` on all three under `easeDecel`, which is
the transform interpolated linearly, with a fourth value, 0 to 1, for the landing, because a
value already at its target is finished the moment it is asked — and read on the UI thread by
every tile's `1 / scale` counter-scale about a **one-point** anchor and by every ring's centre
and radius (`RadarRings`, `useAnimatedProps` on the circle). JavaScript hears the field through
one `useAnimatedReaction`, and only when a sentence would change: the width to a tenth of a
kilometre, or the count of points in view; a landing tells it the exact stop, which is what greys
± at the ladder's ends. Which rings exist is React's, from the width last spoken. The parent is
still told only where a gesture, a ±, a flight or ◉ ended. The swipe row, the deck's drag and the
radius slider stay on `PanResponder`; `GestureHandlerRootView` is the outermost view of the root
layout, the touch system's and not a provider's. **One card at a time**: `tileState` in
`domain/radarGeometry` draws the closest width as the closer face for everybody but the selected
player, who is the card at every width — a tap on a face flies at the 3 km stop **or the
narrower width already held** (`flyToView(row, widthKm)`), so a tap at 1,5 km across never zooms
out — and the closest hint reads _Tap anybody for their card, and the card for the full profile
and the two answers._ Mocks 3, 9 and 10 no longer bind where they draw several cards. **Under
test** both libraries are real: `jest.setup.js` runs the gesture library's setup and reanimated's
`setUpTests`, `jest.config.js` maps `react-native-reanimated/mock` — which
`expo-router/testing-library` quietly `jest.mock`s the module with, after anything a test could
hoist — to `test-support/reanimatedActual.js`, and `test-support/radarTouch` fires the pan and
the pinch through `fireGestureHandler` by the gestures' test ids, flushing the `runOnJS`
microtask the fake clock holds; `radar.test.tsx` holds the one-card rule, the flight at the
floor, the selected card through a zoom in, and the pan's intent distance in place of _never
claims the press_. The domain's geometry carries `'worklet'` directives — a build fact in a
domain module, the functions unchanged and tested as before. **Not seen on a device** — the
drag on Android, the pinch on iOS and one card at a time on both are asked for a look. The
clumps the look also found are the seed's — every member of a ring in one cell on the centre's
meridian — and are a backend ticket.

**The pinch lets go where it is, and a stack opens on a tap**
([ADR-0177](../../../docs/adr/0177-the-pinch-lets-go-where-it-is-and-a-stack-opens-on-a-tap.md),
[`the-radar.md`](../../../docs/specs/matchmaking/the-radar.md) §7.6, §7.10, the words §26).
The second look found the field jumping when a pinch let go, for two reasons the field's: the
pan that runs beside the pinch was anchored on the fingers' **position** — their average, which
moves by half a spread the moment one of two lifts — and `pinched` bound its centre with the
drag's rubber band, so a pinch past the reach's edge sprang back on release. `RadarField`
anchors the drag on the recogniser's **translation** (`event.translationX/Y`, which the
library keeps continuous as fingers land and lift), keeps the last travel seen while a pinch is
live, and re-anchors at that travel and the pinch's last view when the pinch ends with a finger
down; `pinched` binds with `boundCentre` where `dragged` bands, pinned in
`radarGeometry.test.ts`. The hand-off itself cannot be driven through `fireGestureHandler`,
which ends every gesture it fires; it is argued from the recogniser's contract and asked for a
look. **A stack at the floor**: `stacksAt` in `domain/radarGeometry` folds, at 1,5 km across
and at no other width, players whose spots lie nearer than one face is wide on this field —
`radarFaceBox('closer').width`, 34 pt, 0,131 km on a 390 pt phone — taken across by a
union–find, into a `Stack` with a stable id (the members' ids joined, served order) and a
centre at the mean of the spots; the field draws `RadarStack` there — the closer face's 30 pt
square on paper with the count in `num.s`, volt while open, a `button` named `stackLabel`
with `stackHint` and `expanded` — and its members not at all, unless one is the selection,
whose card stands at its own spot above the marker. `fanOut` seats an open stack's members on
rings from `theme.size.minTouch` out, `faceBox + space.sm` apart and between rings, north
clockwise, as kilometre points at the floor's scale so a fanned face is a tile like any other;
`RadarLegs` draws a hairline from the marker to each on the UI thread, as the rings are drawn,
because a line inside the transform would smear. A fanned face's tap flies to the fanned spot
at the width held (`flyTo(row, at)`) and selects there; the marker again, the empty-field press
or a zoom off the floor folds the fan, and the open stack — the field's own `useState`, by id —
dies with its stack. The reaction that speaks to JavaScript adds _at the floor_ to its dedupe,
so the floor is heard the moment it is reached and not a tenth of a kilometre later; the footer
gains `stacked` and the hint its third sentence. `radar.test.tsx` walks a cast with two players
60 m apart: no stack at 3 km, one marker saying _2_ at the floor with the selected one still a
card, the fold on deselect, the dissolve at 3 km; and the open — both faces back, two legs, the
marker `expanded` — the flight to a fanned face, the fold on a second tap and on empty field.
**Not seen on a device.**

**Find a game is behind the `find_a_game` flag, and the gate is Play's three route files**
([#479](https://github.com/Raketa02/Raketa/issues/479), [ADR-0180](../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md) §7). `play/index.tsx` reads the
flag once when it mounts — `useFeatureOnMount` from `features/feature_flags` — and draws
`FindAGameScreen` when it is on and `features/find_a_game_next`'s empty screen when it is off; the
shell lays the root down again on every entry to the tab, which is when a toggle that arrived
meanwhile shows. **`play/builder.tsx` and `play/pool.tsx` close to a bare link while it is off,
and never to a search under way**: each redirects to `/play` only when the search it was opened on
has no record — `useSearchWasRun`, the record being written by the act that minted the search,
before anything is pushed onto it. **Ruled by the user on 2026-09-23**, over the ticket's literal
_the builder and pool routes redirect_: a toggle that lands by foreground while a player is on Find
a game would otherwise bounce their next step to the empty screen, which is what story 21 and
ADR-0180 §7's _nobody has a screen pulled out from under them mid-task_ refuse. The same rule is
what keeps fill-the-seat open (story 25) — its builder pushes the same `/play/pool`, on a search the
fill minted — so the special case for a challenge it replaced is gone. `pool.test.tsx` walks the
toggle arriving mid-search; `theFindAGameGate.test.tsx` walks the bare links. `findAGame.test.tsx`
and the other Play suites are untouched: `stubGate` serves no datafile, which is every flag at its
code default.

**Find a game is behind `classic_play` now, with the rest of the old loop**
([#550](https://github.com/Raketa02/Raketa/issues/550),
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6). The three
route files read `classic_play` where they read `find_a_game`, and nothing else about the gate
moved: on, Play's root is Find a game and the builder and pool open as before; off — the default —
the root is Groups and a bare link to either lands there, while a search already under way and
fill-the-seat still go through. The Players deck is this feature's too, and it is behind the same
flag by way of the bar: the shell draws its column only with Classic play on
([`shell.md`](shell.md)). Every suite that walks the deck, the radar or Find a game launches through
`launchIntoClassicPlay`.
