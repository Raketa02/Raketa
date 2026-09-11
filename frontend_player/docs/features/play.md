# play — Find a game, Match me, the builder and the pool

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
ADR-0107's _the whole handle or nobody_ with one implementation and a type that will not take
a shortened one, the one sentence a build says about a code it is too old to read, and
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
([ADR-0154](../../../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md),
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
