# Rakieta Player App — Product Specification: **The Now Section**

**Version:** 1.0 · drafted against `rakieta-player-app-documentation-v37.md` and `rakietaPlayerPrototype.html`
**Scope:** the Now tab (home screen) end to end — every state it can present, every action it exposes, every rule that decides what appears on it.

**Evidence tag shorthand used throughout:**

| Tag | Meaning |
|---|---|
| `[SRC: doc · §x]` | Stated in `rakieta-player-app-documentation-v37.md`, section x |
| `[SRC: proto · fn]` | Implemented in `rakietaPlayerPrototype.html`, function/registry entry `fn` |
| `[VERIFIED: …]` | Behaviour confirmed by executing the prototype under a DOM stub, not inferred from reading |
| `[DERIVED: …]` | Reasoned conclusion; not stated anywhere, but follows from the sources |
| `[GAP: unspecified]` | Neither source decides this; a recommendation follows, clearly marked as a proposal |
| `[CONFLICT]` | The two sources, or a source and its own implementation, disagree |

---

# A. THE FEATURE IN ONE PARAGRAPH

**Now** is the app's home screen and its first tab. It answers, without the player tapping anything, the two questions a player opens the app to ask: *what is happening to the matches I have already paid for*, and *what could I join next*. It is built from five blocks in a fixed vertical order: a greeting header carrying the current city, day and clock; a row of sport filter chips; a horizontally-scrolling strip of **state cards**, one per match the player holds a seat in, soonest first, each showing the match's player-facing state tag, its court situation, its group situation and a bulleted set of true statements about the player's money; a sports-card block showing today's remaining club-card entries; a ranked feed of up to three open matches the player could join, ordered by **Match Fit**; and one full match worth waiting for. Nothing on Now is stored — every card is a pure function of the current clock and the current match records, recomputed on every render `[SRC: doc · §0.5, §2.1]`, which is why Now can never disagree with the match detail screen behind it.

---

# B. WHY IT EXISTS

## B1. The problem it solves, and the concrete failure without it

A seat in a Rakieta match is not a static booking. Between the moment a player pays and the moment they play, the match can gain and lose a court twice, gain and lose players, commit, decommit, be rescued, be cancelled by a checkpoint, or be cancelled by a club — and **most of those transitions are produced by the passage of time alone, while the player is not looking** `[SRC: proto · syncMatch, "the notifications that only the passage of time can produce"]`.

Without Now, the failure is specific and severe: a player who paid 38,00 zł on Wednesday for a Saturday match has no way to learn, without navigating into the match, that Zabłocie returned the court on Friday night because the match was still two seats short inside twelve hours. They arrive at a court that is not theirs, or they do not arrive at all. `[SRC: doc · §0.2 Invariant 6 — "That is the worst failure this system can have, and it is silent until somebody arrives at a court that is not theirs."]`

The doc states the entry motive directly: *"A player opens the app for one of three reasons: to check a match they are in, to find one, or because something changed. Now answers the first and third without a tap."* `[SRC: doc · §2.1]`

## B2. Business value

**For the platform:**

- Now is the only surface that shows joinable open matches **without the player choosing to go looking**. The feed shows the top three of the entire open board ranked by Match Fit — 27 candidates at the seeded clock, of which 3 are rendered `[VERIFIED: feed length 27, `feed.slice(0,3)` in `V.home`]`. This is a conversion surface, not a convenience. **[UNSOURCED CLAIM — no figure in either source attributes revenue or fill-rate to the Now feed.]**
- Retention: a finished match stays on Now for 24 hours after it ends `[SRC: proto · `KEEP_H=24`]`, which is the window in which a score must be entered (30 minutes) and confirmed. Now is therefore the surface that recovers the result, and a result is what moves a rating `[SRC: doc · §11.2]`.

**For the venue:**

- Every state card names **whose rule** produced the situation. A released hold reads *"This is a club setting, not a marketplace rule, and it is on the club's rules screen"* `[SRC: proto · `ST.heldStale`; doc · §3.4]`. This protects the club from being blamed for a marketplace rule and the marketplace from being blamed for a club rule. The doc gives the reason: *"A player told the wrong reason once stops believing the right ones."* `[SRC: doc · §3.4]`
- A hold a club extended beyond the ladder is attributed to the club and shown as good news, with the club's own published fill figure — 97% in the seeded case `[SRC: proto · `SCEN.ecoExtend`, `ST.heldExtended`]`. The club gets credit for a discretionary act it actually performed.

**Figures the sources give, with attribution:**

| Figure | Source | Applies to |
|---|---|---|
| 71% return after a balanced first match vs 34% after a lopsided one | `[SRC: doc · §0.2 Invariant 5, restated §1.1]` | The rating engine, not Now directly. Now inherits it because the feed is ranked by Match Fit, whose largest term is skill overlap at weight 30 `[SRC: proto · matchFit]` |
| 40 cross-application assertions, 0 disagreements | `[SRC: doc · §15]` | The shared engines Now reads (`courtHold`, `deadlines`, `lifeOf`, `shareOf`) |
| 90 scenarios in 14 groups | `[SRC: doc · §14]` | 89 unique scenario functions exist; the rail lists 90 entries because `ecoIntent` appears twice `[VERIFIED]` |

## B3. User value

*"The single most common question — is my match still on? — is answered before they tap anything."* `[SRC: doc · §2.1]`

Concretely, what a player gets from Now that they could not get elsewhere:

- The **court** situation and the **group** situation as two separate facts, side by side, never merged into one status word `[SRC: proto · stateCard, the two-column `Court` / `Group` hairline block]`. Three of four seats paid with a court held is a different situation from three of four seats paid with the court returned, and Now is where the difference is legible.
- A statement of **what their money is doing right now**, on every card, in every state — the first bulleted line of every non-post state is a money line `[VERIFIED: all 29 pre-play contexts begin with a `You paid …` line]`.
- Advance notice of a transition that has already happened. There is no other surface where a checkpoint cancellation that occurred at T−2h while the player was asleep is visible without navigation.

## B4. Invariants and product principles constraining Now

Each is quoted, then stated as a **forbidden design** — which is the more useful form for an implementer.

### Invariant 1 — a player pays for a seat, never a court

> *"`share = court price ÷ players the sport is sold for`, written the moment the match is created and **never re-priced**."* `[SRC: doc · §0.2]`

**Forbids on Now:** any card showing a price that differs from `payable(m)` computed from the match's stored `share`. It forbids a "price rising as it fills" indicator, a surge badge, and any per-card discount not derived from `slotDisc` (a **court** discount) or the club card. It forbids showing a court price to a player holding a seat.

### Invariant 2 — the clock alone never commits anybody

> *"A booking becomes irrevocable at the commitment deadline, which is `min(start − club window, start − 12 h)` — the earlier of the two. Before it, leaving is free."* `[SRC: doc · §0.2]`

**Forbids on Now:** presenting a state card as committed or irreversible because a deadline passed. `formingLate` and `protectedLate` exist precisely to say *"the deadline has passed, but an incomplete match commits nobody"* `[SRC: proto · ST.formingLate]`. A card must never show a countdown that implies money is at stake before `committedAt != null`.

### Invariant 3 — a refund is decided by the outcome, not the clock

> *"Full refund before commitment. After commitment, full if the seat refills, nothing if it does not."* `[SRC: doc · §0.2]`

**Forbids on Now:** any card stating a single refund figure for a committed match. Cards in `replacement` and `rescue` say what happens to the *leaver* conditionally (*"Ola gets half back if a Rescue player pays; nothing if none does"*), never a number `[SRC: proto · ST.rescue]`.

### Invariant 4 — a court is held in proportion to certainty, and the bar rises

> *"4 paid → hard, permanent. 3 paid → soft while more than 4 hours remain. 2 paid → soft while more than 12 hours remain. 0–1 → none. **Singles has no soft tier.**"* `[SRC: doc · §0.2]`

**Forbids on Now:** a court line that reads "held" for two paid seats inside 12 hours, or for one paid seat at any distance, or for one of two paid seats in a singles match at any distance `[SRC: proto · courtHold — the `n>2` guard skips the soft tiers entirely for 2-player sports]`.

### Invariant 5 — nobody types a level in

> *"A rating is produced by an adaptive questionnaire at onboarding and moved only by counted, confirmed match results and weighted coach calibration observations."* `[SRC: doc · §0.2]`

**Forbids on Now:** any editable level, and any feed ranking that lets the player assert a level to change what they are shown. The feed's skill-overlap term reads `lv('me', sport)` and `seatTarget(m)`; neither is user-writable `[SRC: proto · matchFit]`.

### Invariant 6 — this app never recomputes a club's model *(new in v36)*

> *"Where a decision belongs to the club — how likely a match is to fill, how a contested hour is ordered, whether a hold is extended past the ladder — this app reads what the club published and shows it, attributed."* `[SRC: doc · §0.2]`

**Forbids on Now:** computing a fill probability. `heldExtended` renders `m.clubExtended` and `m.clubFill` as published facts, gated on the club's `probHold` policy flag `[SRC: proto · clubExtended, clubFill]`. The doc names this as a regression that already happened once: *"the first implementation did recompute it, and the conformance suite caught the two apps disagreeing about whether a court was held."* `[SRC: doc · §3.4]`

### Principle — nothing is cached

> *"Everything derived from time recomputes on every render. Move the clock and holds lapse, deadlines pass, states change. Nothing is cached, which is why no two screens can disagree."* `[SRC: doc · §0.5]`

**Forbids on Now:** storing a resolved tag, a resolved court line, or a resolved Match Fit score on the match record. `render()` calls `syncAll()` before drawing anything `[SRC: proto · render]`.

### Principle — the system never hides its reasoning

> *"Not a system that hides its reasoning. Every state explains itself."* `[SRC: doc · §16]`

**Forbids on Now:** a state card with a tag and no explanatory lines. Every one of the 35 contexts carries between 3 and 5 bulleted lines `[VERIFIED: min 3, max 5]`.

---

# C. USERS AND ENTRY POINTS

## C1. Who uses it, in what state

| Player state | What Now shows | Evidence |
|---|---|---|
| **New — no matches, no history** | Your-matches block collapses to the empty card: *"No matches booked / Find a game or create one. You only ever pay your own share, and the fee is always zero."* Feed and full sections render normally | `[SRC: proto · V.home]` |
| **New — no rating in a sport** | Matches in that sport are **silently dropped from the feed**: `matchFit` returns `{score:null}` when `lv('me', sport)` is falsy, and the feed filters on `x.f.score != null` | `[SRC: proto · matchFit, V.home]` |
| **Returning, nothing imminent** | Strip of future matches; the earliest may be days away | `[VERIFIED: default clock Wed 21:00, earliest card Thu 19:00]` |
| **Mid-commitment** | Cards in `confirmed` / `confirmedOnFill` / `ready`; the card states *"If you cannot come now, your seat is searched for rather than refunded"* | `[SRC: proto · ST.confirmed]` |
| **Mid-recovery (a player left)** | `replacement`, `replacementTransfer`, `rescue`, `rescueLate` — two of which carry a red **alert block** above the lines | `[VERIFIED: alert present on `replacement` and `rescue` only]` |
| **Penalised — outstanding debt** | **Now is unaffected.** The debt CTA (*"Settle 112,00 zł to book here"*) is injected in the **match** view override, not Now | `[SRC: proto · `V.match` override; doc · §4.4]` `[CONFLICT-adjacent — see H]` |
| **Penalised — card authorisation required** | **Now is unaffected.** Same as above | `[SRC: proto · V.match override]` |
| **Blocked — Player Score below the 70 gate** | **Now is unaffected.** The reliability gate is applied in `passes()`/`findPool`, which Now's feed does **not** call | `[SRC: proto · V.home feed filter vs findPool]` `[CONFLICT — see H4]` |
| **Player in the scenario gallery** | `S.gallery === true` replaces the strip with all 32 forced gallery matches and the section header becomes a tag/context count | `[SRC: proto · V.home, `gal` branch]` |

## C2. Every route by which a player arrives at Now

| # | Route | Mechanism | Stack effect | Evidence |
|---|---|---|---|---|
| 1 | **Cold boot** | `runScenario('intro')` at script end | `S.tab='now'`, stack `[home]` | `[SRC: proto · boot]` |
| 2 | **Tab bar tap** | `ACT.tab` with `data-v="now"` | `reset('home')` — replaces the whole stack | `[SRC: proto · ACT.tab]` |
| 3 | **"Back to Now" button** | `ACT.home` — appears on `resolved`, `nofill`, `waitoffer`, `result` | `S.tab='now'; reset('home')` | `[SRC: proto · ACT.home; V.resolved, V.nofill, V.waitoffer, V.result]` |
| 4 | **Back affordance from a pushed screen** | `ACT.back` → `back()` pops one frame | Returns to Now only if Now is the stack root | `[SRC: proto · back()]` |
| 5 | **After paying for a seat** | `joinMatch()` ends with `reset('home'); go('match',{id})` | Now becomes the root **underneath** the match screen, so the next back lands on Now | `[SRC: proto · joinMatch]` |
| 6 | **After creating a match** | `ACT.docreate` ends with `S.tab='now'; reset('home'); go('match',{id})` | Same as above | `[SRC: proto · ACT.docreate]` |
| 7 | **After finishing onboarding** | `ACT.obfinish` → `S.ob=null; S.tab='now'; reset('home')` | Now is the first screen a new player sees | `[SRC: proto · ACT.obfinish]` |
| 8 | **A state transition that happened while the player was away** | `render()` → `syncAll()` → `syncMatch(m)` for every match, on every render | No navigation; the card simply reads differently | `[SRC: proto · render, syncAll]` |
| 9 | **Scenario rail selection** | `ACT.scenario` → `runScenario(id)` | Prototype scaffolding only; not a product route | `[SRC: proto · ACT.scenario]` |
| 10 | **Arrival from a notification** | **Not implemented.** `notify()` writes to `S.notif` and nothing routes from a notification to a screen | — | `[GAP: unspecified]` |
| 11 | **Arrival from a deep link** | **Not implemented.** `SH.invite` renders a share URL `rakieta.pl/g/{id}-k29f` but no router consumes it | — | `[GAP: unspecified]` |
| 12 | **Arrival from a request by another party** | **Does not land on Now.** `addReq` → `ecoBase()` sets `S.tab='msg'; reset('requests')` | Requests land on Inbox | `[SRC: proto · ecoBase]` `[CONFLICT — doc §2.1 says Now shows "a request from a club"]` |

**Recommended resolutions for the gaps:**

- **[GAP 10 — proposal]** A notification tap should `reset('home')` then `go('match',{id})` for match-scoped notifications, so back always lands on Now, matching routes 5 and 6. For non-match notifications (`to:'the standby pool'`), route to Inbox.
- **[GAP 11 — proposal]** A `/g/{matchId}-{token}` deep link should resolve to `reset('home'); go('match',{id})` for an authenticated player, and to the join flow for a guest, per the invite sheet's promise that *"Guests can join from the link without an account, but they confirm and pay themselves"* `[SRC: proto · SH.invite]`.

---

# D. END-TO-END JOURNEY

## D1. The happy path

The doc's narrative is preserved and the state changes are added beneath each step. `[SRC: doc · §2.1 "How a player uses it"]`

> *"Tomek opens the app at 14:00. The top card is Saturday's 18:30 padel match: three of four seats paid, court held until 14:30, and a deadline strip showing exactly where the clock sits between now and play. Below it, anything needing him — a request from a club, a score to confirm."*

**⚠ Two parts of that narrative are not what the prototype does.** The deadline strip is rendered on the **match** screen, never on Now `[SRC: proto · V.match line `h+=deadlineStrip(m)`; absent from V.home]`, and the "anything needing him" card is rendered on the **You** screen, not Now `[SRC: proto · V.you]`. Both are recorded as conflicts in section H and as open questions in section K. The steps below describe the **implemented** journey.

---

**Step 1 — The app opens on Now.**

- **User sees:** header `Hi, Tomek` with eyebrow `Kraków · Wednesday · 21:00`; a row of five sport chips with `All` selected; the your-matches strip.
- **User can do:** scroll the strip horizontally, tap a card, tap a sport chip, tap the sports-card block, tap a feed card, switch tabs.
- **System does:** `render()` → `syncAll()` → `syncMatch(m)` on **every** match in state, then `V.home()` builds the markup, then `wireStrip()` binds the horizontal scroll listener, then the tab bar, time bar and rail are redrawn.
- **Persisted state changes:** `syncMatch` may write `courtId`, `protectedAt`, `holdKind`, `releasedAt`, `committedAt`, `formCancelled`, `checkpointCancelled`, `inventoryLost`, `clubCancelled`, `rescueOpen`, `softNotified`, `invNotified`, `clubNotified`, and may **push new entries onto `S.notif`**. `VIEWKEY` is updated; scroll position is preserved when the view key is unchanged.
- `[SRC: proto · render, syncAll, syncMatch, V.home, wireStrip]`

**Step 2 — The strip is assembled.**

- **System does:** selects matches where `mySeat(m) && !m.left && matchEnd(m) + 24h > S.now`, sorts ascending by `start`, then filters by the active sport chip.
- **User sees, at the seeded clock (Wed 5 Aug 2026, 21:00):**

| Position | Match | Club | Start | Tag | Seats | Your money |
|---|---|---|---|---|---|---|
| 1 | m7 · Tennis singles | Ogrody 33 | Thu 6 Aug 19:00 | **Confirmed** | 2/2 | 20,00 zł (35,00 zł share − 15,00 zł card) |
| 2 | m1 · Padel doubles | Zabłocie Sport | Sat 8 Aug 18:30 | **Court held** | 3/4 | 38,00 zł |
| 3 | m8 · Padel doubles | Bonarka Arena | Sun 9 Aug 11:00 | **Full** | 4/4 | 38,00 zł |

- **Persisted state changes:** m7 is full and past its commitment deadline (Wed 19:00), so `syncMatch` writes `committedAt = S.now`; because that is more than 60 s after the deadline, `committedOnFill()` is true and the card resolves to `confirmedOnFill` — *"the deadline had already passed, so the final payment committed everybody at once."*
- `[VERIFIED]` `[SRC: proto · V.home, syncMatch, committedOnFill]`

**Step 3 — Each card renders its own truth.**

Every card carries, in this order: the tag with a tone-coloured dot · sport and format · the start time at 30px · the day and club · the club's court label and duration · a court glyph with one dot per seat (red filled = you, dark filled = another player, dashed outline = empty, hollow outline = guest) · the fill count · a two-column **Court / Group** block · an optional red **alert** block · the bulleted line list · a three-button row.

- `[SRC: proto · stateCard, glyph, seatSyms]`

**Step 4 — The sports-card block.**

- **User sees:** a mint-tinted card reading `MultiSport Plus` / `1 of 2 entries used today · show the QR at reception`, with a green tag `1 left`.
- **User can do:** tap it.
- **System does:** `go('card')` — pushes the Sports card screen. Now remains the stack root.
- `[SRC: proto · V.home, `CARD` constant]`

**Step 5 — The feed: "Even matches for you".**

- **System does:** selects matches where `!mySeat(m) && !m.forced && m.start > S.now && filled(m) < m.n` and the sport chip matches; computes `matchFit(m)` for each; drops any with a null score; sorts descending by score; renders the **first three**.
- **User sees, at the seeded clock:** e6 Tennis at Ogrody 33 Sun 19:30, fit **97**, 20,00 zł · c3 Padel at Zabłocie Sun 10:00, fit **95**, 38,00 zł · m5 Badminton at Hala MOSiR Tue 18:30, fit **94**, **0,00 zł** (card covers a Badminton entry in full).
- 27 matches qualified; 3 were shown.
- **User can do:** tap any card → `go('match',{id})`.
- `[VERIFIED]` `[SRC: proto · V.home, matchFit, matchCard]`

**Step 6 — "Full, but worth waiting for".**

- **System does:** selects `!mySeat(m) && !m.forced && m.start > S.now && isFull(m)` matching the sport chip; renders **the first one only**, in source order — *not* ranked by fit.
- **User sees:** m2, Padel at Bonarka Arena, Fri 7 Aug 19:00, full, Match Fit 94.
- `[VERIFIED: 1 candidate at the seeded clock]` `[SRC: proto · V.home]`

**Step 7 — The player taps their padel card.**

- **System does:** `go('match',{id:'m1'})` pushes the match detail screen. Now is preserved beneath it with its scroll position; on return, `VIEWKEY` differs so the scroll resets to top.
- `[SRC: proto · click delegation on `[data-go]`, render's `same` check]`

## D2. Significant alternate paths

**Alt A — trigger: the player holds no seat in any match (or none in the selected sport).**
The strip is replaced by a single card: *"No matches booked — Find a game or create one. You only ever pay your own share, and the fee is always zero."* The feed and full sections still render. `[SRC: proto · V.home]`

**Alt B — trigger: a sport chip is selected and no open match exists in that sport.**
The feed is replaced by: *"Nothing open in {Sport} right now — We do not invent players to make a city look busy. Try another day, or create a match."* With `All` selected the same copy reads *"Nothing open in your sports right now."* `[SRC: proto · V.home]`

**Alt C — trigger: exactly one match in the strip.**
The dot indicator row is suppressed (`shown.length > 1` guard) and, in gallery mode, so is the caption line. `[SRC: proto · V.home]`

**Alt D — trigger: `S.gallery === true` (scenario `states`).**
The strip shows all 32 forced gallery matches instead of the player's own; the section header becomes `{tags} tags · {contexts} contexts` — **17 tags · 32 contexts** at run time; a caption line under the dots names the currently-centred card's tag and context, updated live by the scroll listener. The feed and full sections render **empty** because every match in state is `forced`. `[VERIFIED]` `[SRC: proto · V.home, wireStrip, buildGallery]`

**Alt E — trigger: the player has left the match (`m.left === true`).**
The match disappears from Now entirely, even though the seat record still exists and a refund may still be pending. Scenario `s5` demonstrates this: after leaving, only m8 remains on Now. `[VERIFIED]` `[SRC: proto · V.home filter; SCEN.s5]`

**Alt F — trigger: a match finished more than 24 hours ago.**
It drops off Now. Scenario `noshow` sets the clock to Mon 10 Aug 20:20, by which point every match the player holds has aged out, and Now renders the empty state — even though the scenario's subject is a completed match. `[VERIFIED]` `[SRC: proto · KEEP_H]`

**Alt G — trigger: an open request exists (`reqOpen().length > 0`).**
A coral count badge is injected onto the **Inbox** tab button by the `render` override — the only way Now signals that something needs the player. The Now body itself is unchanged. `[SRC: proto · render override at the V36 ecosystem section]`

**Alt H — trigger: the clock moves across a threshold while Now is open.**
No push mechanism exists. State changes only become visible on the next `render()`, which is triggered by any action. `[DERIVED: `render` is only called from actions, `setNow`, and `runScenario`; there is no timer.]` `[GAP: unspecified]` **Proposal:** re-render Now on a 30-second interval while it is the visible view, and immediately on app foreground, since every threshold on the card is a clock threshold.

---

# E. STATES AND TRANSITIONS (USER-FACING)

## E1. Screen-level states of the Now section

| State | Condition that produces it | What the user is told | What they can do |
|---|---|---|---|
| **Populated** | ≥1 match passes the strip filter | Cards as described | Scroll, tap, filter, open sheets |
| **Empty (your matches)** | 0 matches pass the strip filter — either genuinely none, or all filtered out by the sport chip | *"No matches booked. Find a game or create one. You only ever pay your own share, and the fee is always zero."* | Change the sport chip, go to Find, create |
| **Empty (feed)** | 0 open matches in the selected sport, or no rating in that sport | *"Nothing open in {sport} right now. We do not invent players to make a city look busy. Try another day, or create a match."* | As above |
| **Full section absent** | 0 full future matches match the chip | No header is rendered at all — the section is omitted, not shown empty | — |
| **Gallery** | `S.gallery === true` | Header becomes `17 tags · 32 contexts`; caption names the centred card | Scroll the strip |
| **Loading** | **Not modelled.** `render()` is synchronous against in-memory state | — | — `[GAP: unspecified]` |
| **Partial data** | **Not modelled.** A match with a missing club, court or player record throws rather than degrading | — | — `[GAP: unspecified]` |
| **Stale** | **Not modelled at screen level.** Staleness is modelled per-match as `heldStale`, which is a court state, not a data-freshness state | — | — |
| **Error** | **Not modelled.** No error boundary exists around `V.home` | — | — `[GAP: unspecified]` |
| **Permission denied** | **Not modelled.** Now shows no permission-gated content | — | — |
| **Rate limited** | **Not modelled** | — | — `[GAP: unspecified]` |

**Recommended resolutions:**

- **[GAP — loading, proposal]** Render the header and sport bar immediately; render the strip as skeleton cards sized to the real card; never render an empty state until the fetch has resolved, because *"No matches booked"* shown to a player who has three is the most damaging possible false statement on this screen.
- **[GAP — partial data, proposal]** A match whose club or court record is missing must render as a card with the tag it can compute and a court line reading *"We cannot reach {club} right now"* — never be dropped from the strip, because a silently missing card is indistinguishable from a cancelled match.
- **[GAP — error, proposal]** A failure to resolve one match must not remove the others. Wrap per-card, not per-screen.
- **[GAP — rate limited, proposal]** Serve the last-known strip with a visible timestamp rather than an empty state.

## E2. Every match state Now can present — all 35 contexts

The doc claims *"35 contexts resolving to 17 player-facing tags"* `[SRC: doc · §3.1]`. The prototype's `ST` table holds exactly 35 entries and the gallery resolves exactly 17 distinct tags `[VERIFIED]`. **The doc's §3.3 table lists 35 context names but does not match the implementation** — it names `protectedCourt`/`protectedBack`/`protectedLate` under "Protected", omits `inventoryLost` from its Cancelled group where the implementation places it, and omits `heldStale`/`heldExtended` from its Held group where the implementation adds them `[CONFLICT — see H]`.

**All 35, as implemented.** `tone` maps to the dot colour via `ST_TONE`; `be` is the backend state the context declares.

### Group: Forming — court not protected (4 contexts, tag `Forming`)

| Context | Condition | Tone | Backend | What the player is told | What they can do |
|---|---|---|---|---|---|
| `forming` | Not protected, no held-but-unpaid seat, before commit | `idle` | `FORMING` | Paid your seat only, never the court · a court is held from the second paid seat · until then the club could sell its last compatible court and everybody is refunded in full · leaving now returns everything, in minutes | Open match · Inbox · Getting in |
| `formingHeld` | Some seat has `p` set but `paid` false (an invited player) | `idle` | `FORMING` | You invited Ewa at 19:41 · her seat is held until 21:41 — two hours, never past commitment · if she does not pay the seat reopens | Same |
| `formingLate` | Past `commit`, still incomplete, not protected | `idle` | `FORMING` | Two variants: if `m.created >= commit`, *"You created this inside the club's cancellation window, so it commits the moment it fills"*; otherwise *"The commitment deadline has passed, but an incomplete match commits nobody"* · still short at the checkpoint time? everybody refunded | Same |
| `formingBack` | A player left **before** commitment and the match is now unprotected | `watch` | `FORMING` | Your price does not change · Ola left before commitment and was reversed in full · the court went back and returns as soon as the ladder is satisfied again | Same |

### Group: Held / released — the ladder (5 contexts)

| Context | Condition | Tag | Tone | Backend | What the player is told |
|---|---|---|---|---|---|
| `heldSoft` | `courtHold().kind === 'soft'`, reason `far` (2 paid, >12 h) or `near` (n−1 paid, >4 h) | `Court held` | `watch` | `COURT_HELD` | A court is being held, but this is not yet a firm booking · the applicable rung, in hours · if it goes back nothing you paid is affected · leaving now returns everything |
| `heldReleased` | Hold lapsed (`farLapsed`/`nearLapsed`), a court **had** been held (`releasedAt != null`), ≥2 seats paid, before the checkpoint | `Court released` | `watch` | `COURT_RELEASED` | Your payment is unchanged and refundable in full · which rung lapsed · one more paid seat brings a court back (or *"the last seat books a court on the spot"* when `need === n`) · if the club sells its last compatible court first, everybody is refunded |
| `heldStale` | `kind === 'soft'`, match age > club `maxHoldAge`, **and** `filled < n−1` | `Court released` | `watch` | `RELEASED` | Untouched and refundable in full · the club returns a soft hold unfilled for {age} hours · **this is a club setting, not a marketplace rule** · it only ever releases a speculative hold — never a committed match, never a court the club committed by hand · one more paid seat brings a court back immediately |
| `heldExtended` | Hold had lapsed, but `m.clubExtended` **and** the club's `probHold` policy is on | `Court held` | `good` | `HELD` | The ladder would have returned this court by now; the club is holding it anyway · their model puts it at {clubFill}% to fill · **it can never work the other way: no model may release a court earlier than the ladder promised** · leaving now still returns everything |
| `clubHeld` | `m.courtLocked` — the club committed a court by hand | `Court committed` | `good` | `COURT_PROTECTED` | The club has committed a court by hand · that overrides the automatic ladder · clubs do this for matches they expect to fill, or to keep a regular group together |

### Group: Court protected (3 contexts, tag `Court protected`, tone `good`, backend `COURT_PROTECTED`)

| Context | Condition | What the player is told |
|---|---|---|
| `protectedCourt` | Protected, hard hold, one player needed, before commit | Three paid seats, so a compatible court is held until 4 h before play · the exact court is assigned by us, never chosen — the price cannot change |
| `protectedLate` | Protected, hard hold, past commit, still incomplete | The deadline has passed but the match is not complete, so nothing is committed · the last seat commits everybody the moment it is paid |
| `protectedBack` | A player left before commitment and the match is **still** protected | Your price does not change · {name} left before commitment and was reversed in full · three of you are still paid · their seat is open again at the normal price |

**⚠ `protectedCourt` and `protectedLate` are unreachable by any natural path for a 4-player open match.** For `n > 2`, a 3-of-4 match always yields `kind:'soft'`, which routes to `heldSoft`; a hard hold only arises when full, committed, locked or private, all of which are tested earlier in `matchState`. They appear only in the forced gallery. `[VERIFIED]` `[SRC: proto · courtHold, matchState resolution order]`

### Group: Full and confirmed (3 contexts)

| Context | Condition | Tag | Backend | What the player is told |
|---|---|---|---|---|
| `full` | Every seat paid, `committedAt == null`, before T−15 min | `Full` | `FULL_UNCOMMITTED` | Every seat paid and a court reserved · **free cancellation for everybody until {day} {time}** · nothing has reached the club yet · court line: *"Reserved · settles to the club at {commit time}"* |
| `confirmed` | Full and committed at the deadline | `Confirmed` | `CONFIRMED` | Full at the deadline, so the money settled · if you cannot come now, your seat is searched for rather than refunded · door code from {start − 15 min} |
| `confirmedOnFill` | Full and `committedAt > commit + 60 s` | `Confirmed` | `CONFIRMED` | The deadline had already passed, so the final payment committed everybody at once · everyone knew that joining the last seat would do this |

### Group: Recovery (4 contexts)

| Context | Condition | Tag | Tone | Backend | Alert? | What the player is told |
|---|---|---|---|---|---|---|
| `replacement` | Vacated after commitment, before `rescue` (T−4 h doubles / T−6 h singles) | `Replacement pending` | `watch` | `REPLACEMENT_PENDING` | **Yes** | *"{name} left after the commitment deadline. We are looking for a replacement. **Your payment will not change.**"* Their payment stays on the seat, so the court is safe · offered at the normal price |
| `replacementTransfer` | `m.transferring` is set | `Replacement pending` | `watch` | `REPLACEMENT_PENDING` | No | A named person always pays the full price, or is given the seat outright · **half price is never hers to hand out** |
| `rescue` | Vacated, committed, at or past `rescue`, before the checkpoint | `Rescue active` | `time` | `RESCUE_ACTIVE` | **Yes** | Nobody took it at full price, so 50/50 Rescue invitations went out at {time} · sent to standby players in waves, **not advertised as a public sale** · the leaver gets half back if a Rescue player pays; nothing if none does |
| `rescueLate` | Same, at or past the checkpoint | `Rescue active` | `time` | `RESCUE_ACTIVE` | No | The certainty checkpoint passed at {time} · this club does not offer rebooking credit, so the match stays alive · Rescue runs until {joinCut}, and you can bring a guest, or play three |

### Group: Ready (1 context)

| Context | Condition | Tag | Backend | What the player is told |
|---|---|---|---|---|
| `ready` | Full and `S.now >= start − 15 min` | `Ready to play` | `CONFIRMED` | Everything is paid and the court is yours · door code live from {start − 15 min} · tap Getting in for the code and your card QR · court line names the **actual assigned court**, not the category |

### Group: Cancelled (4 contexts, tag `Cancelled`)

| Context | Condition | Tone | Backend | What the player is told |
|---|---|---|---|---|
| `cancelledIncomplete` | At the checkpoint, `committedAt == null` and not full → `formCancelled` | `ended` | `CANCELLED` | Cancelled at {check}, two hours before play · everybody who paid is refunded in full — nobody was ever committed · the court went back with time to resell it · three matches near you at a similar hour are suggested below |
| `cancelledCheckpoint` | At the checkpoint, committed, short, no sponsored guest, **and the club has `rebooking: true`** | `ended` | `CANCELLED` | No replacement by {check}, and this club offers protected rebooking · the three of you have {share} credit at {club}, already in your account · the leaver forfeits her share — that is what pays the club for releasing the hour · two hours of notice, which is the point |
| `cancelledClub` | `m.clubCancelled` or `m.weather` | `ended` | `CANCELLED` | The club cancelled at 08:12 — standing water on the court · everybody refunded in full, **including anybody who had already left** · a Rescue payment, if one had been made, is refunded too · nobody's reliability is touched |
| `inventoryLost` | The last compatible court was sold while the match was unsecured | **`bad`** ⚠ | `CANCELLED` | Everybody refunded in full including anybody who had already left · the match was still short so it had no court held when the club sold the slot · **this is the risk the app names from the first screen — a seat is never a court** · nothing else you have booked is affected |

**⚠ `inventoryLost` declares `tone:'bad'`, which is not a key in `ST_TONE`.** The tag dot therefore renders with `background:undefined`. Every other Cancelled context uses `ended`. `[VERIFIED]` `[SRC: proto · ST.inventoryLost vs ST_TONE]`

### Group: After the match (6 contexts, all `post: 1` — the Getting-in button is suppressed)

| Context | Condition | Tag | Tone | What the player is told |
|---|---|---|---|---|
| `needsResult` | Past end, full, no score, before `matchEnd + 30 min` | `Needs result` | `watch` | You played at {start} · **any of the four can enter it — not the creator, not a nominated scorer** · 30 minutes from the last point, or it counts for nobody |
| `confirmResult` | Past end, a score exists, unconfirmed, inside the window | `Confirm the result` | `watch` | {name} entered {score} at {time} · you are on the other side, so one tap makes it final · **a teammate agreeing with a teammate proves nothing** |
| `completed` | `m.confirmed` | `Completed` | `good` | {score} confirmed by both sides · your padel level moved +0,08 to 2,79 · Player Score +1 — turned up, paid, confirmed |
| `playedShort` | Past end, `filled < n` | `Played` | `idle` | Nobody replaced Ola, and this club does not do rebooking credit · the three of you used the hour — the seat was funded either way · **not counted: a level needs four players to mean anything** · Ola is refunded nothing and her reliability takes the hit |
| `playedNoShow` | `m.noShow` | `Played` | `idle` | Marek did not arrive and did not tell anybody · no refund, and no search could run — that is what makes it worse than leaving · not counted · −18 Player Score, and a second inside 90 days restricts peak hours |
| `playedNoScore` | Past `matchEnd + 30 min` with no confirmed score | `Played` | `idle` | The match happened and everybody paid · nobody entered a score inside 30 minutes, so it counts for nobody · **all four lose a point of Player Score — it is a shared job** |

### Group: Standby (1 context)

| Context | Condition | Tag | Backend | What the player is told |
|---|---|---|---|---|
| `waitlisted` | Not my seat, but `S.waitlists` includes the match id | `On standby` | `—` | You joined the standby list · 0,00 zł · if a seat frees the top candidates are told at the same moment · ten minutes to accept, five to pay, then it moves on · **ignoring it costs nothing and you keep your place** |

**⚠ A waitlisted match cannot appear on Now.** The strip filter requires `mySeat(m)`, and a waitlisted player holds no seat. `waitlisted` is reachable only through the gallery and the match detail screen. `[VERIFIED]` `[DERIVED]`

### Group: Private court (4 contexts, tag `Reserved`, tone `good`)

| Context | Condition | Backend | What the player is told |
|---|---|---|---|
| `privateReserved` | Private, `openSeats === 0`, `payModel !== 'split'` | `RESERVED` | You paid the full court price and it is reserved · you can play with fewer players — the court is yours either way · **the club's own cancellation policy applies**, and it is printed on the booking |
| `privatePartial` | Private, `payModel === 'split'` | `PARTIALLY_PAID` | You paid your share · unpaid shares are **guaranteed by you** · at {commit} any unpaid share is charged to you · the booking stays confirmed whatever the others do |
| `privateFull` | Private, every share paid | `FULLY_PAID` | Every player paid their share · nothing is left on your guarantee · you are still the booking owner |
| `privateOpen` | Private with `openSeats > 0` | `PUBLIC_SEATS_OPEN` | You opened seats to players you do not know · **every public share that is paid reduces what you guarantee, zł for zł** · the court stays yours · you are still responsible for a seat nobody takes |

**⚠ `privateFull` is unreachable through `matchState`.** The private branch tests `openSeats > 0 → privateOpen`, then `payModel === 'split' → privatePartial`, else `privateReserved`. There is no path to `privateFull`. It exists only in the gallery. `[VERIFIED]` `[SRC: proto · matchState private branch]`

## E3. The nine canonical lifecycle states

The 17 tags are derived from nine states shared verbatim with the club console `[SRC: doc · §3.5]`. `lifeOf(m)` resolves them in this order `[SRC: proto · lifeOf]`:

| Order | State | Condition | Meaning |
|---|---|---|---|
| 1 | `CANCELLED` | `inventoryLost \|\| clubCancelled \|\| formCancelled \|\| checkpointCancelled` | Nothing recovered it |
| 2 | `PLAYED` | `S.now >= matchEnd(m)` | Finished |
| 3 | `RECOVERING` | `vacated && committedAt != null` | A replacement search or the Rescue ladder is running |
| 4 | `CONFIRMED` | Full **and** (past commit or already committed) | Paid and committed. The court never comes back |
| 5 | `FUNDED` | Full, before commit | Every seat paid, commitment deadline not yet reached |
| 6 | `AT_RISK` | ≥1 paid, within 48 h of start, hold not `none` | Paid seats, short of players, inside 48 hours |
| 7 | `HELD` | `kind === 'soft'` or `why === 'club'` | Partial payment has earned a hold under the ladder |
| 8 | `RELEASED` | `why` in {`stale`, `nearLapsed`, `farLapsed`} or `releasedAt != null` | Had a hold, lost it, still open and still looking |
| 9 | `FORMING` | Otherwise | Seats open, no court held |

**Order is the specification.** *"a cancelled match that was also full must read as cancelled."* `[SRC: doc · §3.6]`

## E4. Resolution order inside `matchState`

The tested order, which must be preserved exactly `[SRC: proto · matchState]`:

1. `m.forced` → the gallery override, with clock shims (`demoEnd`, `demoCut`, `demoFar`, `demoNear`)
2. `inventoryLost`
3. `clubCancelled || weather` → `cancelledClub`
4. `formCancelled` → `cancelledIncomplete`
5. `checkpointCancelled` → `cancelledCheckpoint`
6. `S.now >= end` → the six post-play contexts
7. `!mySeat && S.waitlists.includes(id)` → `waitlisted`
8. `kind === 'private'` → the private contexts
9. `vacated && committedAt != null` → the recovery contexts
10. `vacated` (uncommitted) → `protectedBack` or `formingBack`
11. `isFull` → `ready` / `confirmedOnFill` / `confirmed` / `full`
12. `isProtected` → `clubHeld` / `heldSoft` / `protectedLate` / `protectedCourt`
13. `releasedAt != null && filled >= 2 && S.now < check` → `heldReleased`
14. any seat held-but-unpaid → `formingHeld`
15. `S.now >= commit` → `formingLate`
16. otherwise → `forming`

**Then a post-pass** overrides the result: if the hold reason is `stale` and the resolved key is one of {`heldReleased`, `forming`, `formingLate`}, the state becomes `heldStale`; if the reason is `extended` and the key is one of {`heldReleased`, `forming`, `formingLate`, `heldSoft`}, it becomes `heldExtended`. Neither override applies to a forced or private match. `[SRC: proto · matchState override]`

**And a final rewrite for non-participants:** when the viewer holds no seat and the state is not `waitlisted`, every line matching `/^You paid/` is replaced with *"Your share would be {payable} · booking fee 0,00 zł"* `[SRC: proto · matchState]`. On Now this branch is unreachable, because the strip requires `mySeat(m)` — it exists for the match detail screen and the gallery. `[DERIVED]`

---

# F. ACCEPTANCE CRITERIA

Numbered `AC-n`, atomic, independently verifiable, each carrying its evidence tag. Grouped for navigation only — the numbering is global and stable so criteria can be cited in test names.

## F1. Screen composition and order

**AC-1** — Given the Now tab is the active view, When it renders, Then the blocks appear in this order: header, sport bar, your-matches section, sports-card block, "Even matches for you", "Full, but worth waiting for". `[SRC: proto · V.home]`

**AC-2** — Given Now renders, Then the header title is `Hi, Tomek` and the eyebrow is `Kraków · {full day name of S.now} · {HH:MM of S.now}`. `[SRC: proto · V.home, head, dowl, hm]`

**AC-3** — Given Now renders, Then the sport bar contains exactly five chips in order: `All`, `Padel`, `Tennis`, `Squash`, `Badminton`. `[SRC: proto · sportbar, SPORTS]`

**AC-4** — Given a sport chip other than `All` is selected, Then that chip carries a coloured dot matching `SPORTS[sport].c`; the `All` chip carries no dot. `[SRC: proto · sportbar]`

**AC-5** — Given Now renders, Then no bottom CTA bar is shown, because `V.home` never assigns `CTA`. `[SRC: proto · render, V.home]`

**AC-6** — Given Now renders, Then no deadline strip is shown on any card, because `deadlineStrip()` is called only from `V.match` and `V.position`. `[SRC: proto · V.match, V.position]` `[CONFLICT: doc §2.1 states Now shows "a deadline strip"]`

**AC-7** — Given Now renders, Then no "something needs you" card is shown, because that card is built in `V.you`. `[SRC: proto · V.you]` `[CONFLICT: doc §2.1 states Now shows "anything needing him"]`

**AC-8** — Given at least one open request exists, When any screen renders, Then a coral count badge is appended to the Inbox tab button showing `reqOpen().length`. `[SRC: proto · render override]`

**AC-9** — Given zero open requests exist, When any screen renders, Then no badge is appended. `[SRC: proto · render override, early return on `!n`]`

## F2. Your-matches strip — selection

**AC-10** — Given a match, When Now renders, Then it appears in the strip only if `mySeat(m)` is truthy. `[SRC: proto · V.home]`

**AC-11** — Given a match where `m.left === true`, When Now renders, Then it does not appear in the strip, regardless of any pending refund. `[SRC: proto · V.home]` `[VERIFIED: SCEN.s5]`

**AC-12** — Given a match, When Now renders, Then it appears only if `matchEnd(m) + 24h > S.now`. `[SRC: proto · V.home, KEEP_H]`

**AC-13** — Given a sport chip other than `All` is selected, When Now renders, Then the strip contains only matches where `m.sport` equals the selected sport. `[SRC: proto · V.home]`

**AC-14** — Given `All` is selected, When Now renders, Then no sport filtering is applied to the strip. `[SRC: proto · V.home]`

**AC-15** — Given two or more matches pass the filter, When Now renders, Then they are ordered ascending by `m.start`. `[SRC: proto · V.home sort]`

**AC-16** — Given two matches share an identical `start`, Then their relative order is whatever `Object.values(S.matches)` yields, because the sort comparator returns 0. `[DERIVED: `(a,b)=>a.start-b.start` is not a total order over ties]` `[GAP: unspecified]` **Proposal:** break ties by match id ascending, so the strip is deterministic across renders.

**AC-17** — Given the strip contains more than one match, When Now renders, Then a dot indicator row is shown with one dot per card, the first marked active. `[SRC: proto · V.home]`

**AC-18** — Given the strip contains exactly one match, When Now renders, Then no dot indicator row is shown. `[SRC: proto · V.home `shown.length>1` guard]`

**AC-19** — Given the strip is scrolled horizontally, When the scroll settles, Then the active dot index equals `round(scrollLeft / (cardWidth + 10))`. `[SRC: proto · wireStrip]`

**AC-20** — Given the strip is non-empty, Then the section header reads `Your matches · {count} · soonest first` with a right-aligned `swipe →` hint. `[SRC: proto · V.home]`

**AC-21** — Given zero matches pass the strip filter, Then the header is not rendered and a single empty card is shown reading `No matches booked` / `Find a game or create one. You only ever pay your own share, and the fee is always zero.` `[SRC: proto · V.home]`

**AC-22** — Given the player holds matches in Padel and Tennis and the `Squash` chip is selected, Then the empty card is shown with the same copy as AC-21 — it does **not** name the sport. `[VERIFIED]` `[SRC: proto · V.home]`

## F3. Your-matches strip — the state card

**AC-23** — Given a card renders, Then it shows the tag text of `matchState(m).tag` preceded by a dot coloured `ST_TONE[matchState(m).tone]`. `[SRC: proto · stateCard]`

**AC-24** — Given a card renders for a match whose context is `inventoryLost`, Then the tone key is `bad`, which is absent from `ST_TONE`, and the dot background resolves to `undefined`. `[VERIFIED]` **This is a defect — see AC-25.**

**AC-25** — Given a match in `inventoryLost`, Then the dot must render with the `ended` colour (`var(--red)`), consistent with the other three `Cancelled` contexts. `[DERIVED: every other Cancelled context uses `ended`]` `[GAP: unspecified]` **Proposal:** change `ST.inventoryLost` to `tone:'ended'`; do not add a `bad` key to `ST_TONE`, because a fifth tone would be an undocumented sixth tag family.

**AC-26** — Given a card renders, Then the top-right eyebrow reads `{sport} · {format}`. `[SRC: proto · stateCard]`

**AC-27** — Given a card renders, Then the start time is shown at 30px as `HH:MM`, with `{when(start)} · {club name}` beneath it and `{club court label} · {duration} min` beneath that. `[SRC: proto · stateCard]`

**AC-28** — Given a match starts today, Then `when()` renders `Today · HH:MM`; tomorrow renders `Tomorrow · HH:MM`; yesterday renders `Yesterday · HH:MM`; anything else renders `{Ddd} · HH:MM`. `[SRC: proto · when]`

**AC-29** — Given a card renders, Then a court glyph is drawn with one dot per seat: the player's own seat is a filled red circle, another player's seat a filled dark circle, a guest seat a hollow outlined circle, an empty seat a red dashed outline. `[SRC: proto · glyph, seatSyms]`

**AC-30** — Given a Squash match, Then the glyph draws two positions with a horizontal line; given any other 2-seat match, two horizontal positions with a vertical net; given a 4-seat match, four positions with a vertical net and two service lines. `[SRC: proto · glyph]`

**AC-31** — Given a card renders, Then the fill count beneath the glyph reads `{filled}/{n}` where `filled` counts seats with both `p` and `paid`. `[SRC: proto · stateCard, filled]`

**AC-32** — Given a card renders, Then a two-column block shows `Court` (from `matchState(m).court`) and `Group` (from `matchState(m).group`), separated by a vertical rule. `[SRC: proto · stateCard]`

**AC-33** — Given the resolved context declares an `alert`, Then a red-bordered alert block is rendered above the line list. `[SRC: proto · stateCard]`

**AC-34** — Given the resolved context is `replacement`, Then the alert reads `{leaver} left after the commitment deadline. We are looking for a replacement. Your payment will not change.` with the last sentence bold. `[SRC: proto · ST.replacement]`

**AC-35** — Given the resolved context is `rescue`, Then the alert reads `Still looking for a replacement. Your payment will not change.` with the last sentence bold. `[SRC: proto · ST.rescue]`

**AC-36** — Given the resolved context is any of the other 33, Then no alert block is rendered. `[VERIFIED: `alert` present on exactly two contexts]`

**AC-37** — Given a card renders, Then each line in `matchState(m).lines` is rendered with a volt tick when its first element is truthy and a hollow circle when falsy. `[SRC: proto · stateCard]`

**AC-38** — Given a card renders, Then it carries between 3 and 5 lines. `[VERIFIED: min 3, max 5 across all 35 contexts]`

**AC-39** — Given a pre-play context, Then the first line is a money line beginning `You paid`. `[VERIFIED: all 29 pre-play contexts]`

**AC-40** — Given a card renders, Then the button row contains a primary button labelled `Open match` navigating to `match` with the card's id. `[SRC: proto · stateCard, `(st.cta||{}).label||'Open match'`]`

**AC-41** — Given no context in `ST` defines a `cta` or `left` property, Then the primary button label is always `Open match` with no suffix and the target is always `match`. `[VERIFIED: zero occurrences of `cta:` and `left:` in the state table]`

**AC-42** — Given a card renders, Then the button row contains an envelope button navigating to `inbox`. `[SRC: proto · stateCard]`

**AC-43** — Given the resolved context does **not** declare `post`, Then the button row contains a `⌘` button that opens the access sheet for that match. `[SRC: proto · stateCard]`

**AC-44** — Given the resolved context declares `post` (`needsResult`, `confirmResult`, `completed`, `playedShort`, `playedNoShow`, `playedNoScore`), Then no `⌘` button is rendered. `[VERIFIED: exactly six contexts carry `post`]`

**AC-45** — Given a match in any `Cancelled` context, Then the `⌘` button **is** rendered, because no Cancelled context declares `post`. `[VERIFIED]` **This is a defect — see AC-46.**

**AC-46** — Given a match in `cancelledIncomplete`, `cancelledCheckpoint`, `cancelledClub` or `inventoryLost`, Then no access affordance must be offered, because there is no court to enter. `[DERIVED]` `[GAP: unspecified]` **Proposal:** suppress the `⌘` button when `matchState(m).be === 'CANCELLED'` as well as when `post` is set.

## F4. Sports-card block

**AC-47** — Given Now renders, Then a mint-tinted card shows `CARD.plan`, the line `{CARD.used} of {CARD.allowed} entries used today · show the QR at reception`, and a green tag reading `{allowed − used} left`. `[SRC: proto · V.home, CARD]`

**AC-48** — Given the seeded constants, Then the block reads `MultiSport Plus`, `1 of 2 entries used today`, tag `1 left`. `[VERIFIED]`

**AC-49** — Given the block is tapped, Then `go('card')` pushes the Sports card screen and Now remains the stack root. `[SRC: proto · V.home `data-go="card"`, click delegation]`

**AC-50** — Given `CARD.used === CARD.allowed`, Then the tag reads `0 left`. `[DERIVED: `allowed − used`]` `[GAP: unspecified]` **Proposal:** at zero, change the tag tone from `ok` to neutral and the line to `No entries left today`, because a green `0 left` reads as availability.

**AC-51** — Given `CARD` is a module-level constant with no per-club or per-sport arithmetic in `V.home`, Then the block is identical on every render regardless of which clubs the player's matches are at. `[SRC: proto · CARD]` `[GAP: unspecified]` **Proposal:** entry counts are club-scoped in reality; the block must read from the player record, not a constant, before release.

## F5. The "Even matches for you" feed

**AC-52** — Given Now renders, Then the feed section header reads `Even matches for you` and is always rendered, even when empty. `[SRC: proto · V.home]`

**AC-53** — Given a match, Then it is a feed candidate only if `!mySeat(m)`. `[SRC: proto · V.home]`

**AC-54** — Given a match, Then it is a feed candidate only if `!m.forced`. `[SRC: proto · V.home]`

**AC-55** — Given a match, Then it is a feed candidate only if `m.start > S.now`. `[SRC: proto · V.home]`

**AC-56** — Given a match, Then it is a feed candidate only if `filled(m) < m.n`. `[SRC: proto · V.home]`

**AC-57** — Given a sport chip other than `All`, Then only matches of that sport are candidates. `[SRC: proto · V.home]`

**AC-58** — Given a candidate whose sport the player has no rating in, Then `matchFit` returns a null score and the candidate is dropped. `[SRC: proto · matchFit, V.home filter]`

**AC-59** — Given candidates exist, Then they are sorted descending by `matchFit(m).score` and the first three are rendered. `[SRC: proto · V.home]`

**AC-60** — Given fewer than three candidates, Then all of them are rendered. `[DERIVED: `slice(0,3)`]`

**AC-61** — Given zero candidates, Then the empty card reads `Nothing open in {S.sport === 'all' ? 'your sports' : S.sport} right now` / `We do not invent players to make a city look busy. Try another day, or create a match.` `[SRC: proto · V.home]`

**AC-62** — Given the seeded clock and `All` selected, Then 27 candidates qualify and the three rendered are e6 (fit 97), c3 (fit 95), m5 (fit 94). `[VERIFIED]`

**AC-63** — Given a feed card renders, Then it shows `when(start)`, an optional hot badge from `m.badge`, `{club} · {distance} min`, chips for sport, format and `Counts`/`Friendly`, a card-discount chip when `cardOff(m) > 0`, the glyph, the fill count, the Match Fit score, the state tag, the strikethrough share when discounted, `payable(m)`, and `· 0 fee`. `[SRC: proto · matchCard]`

**AC-64** — Given `cardOff(m)` equals the full share, Then the discount chip reads `card −all`; given a partial offset, it reads `card −{amount}`. `[SRC: proto · matchCard]`

**AC-65** — Given a feed card is tapped, Then `go('match',{id})` pushes the match screen. `[SRC: proto · matchCard `data-go="match"`]`

**AC-66** — Given the feed filter, Then it does **not** call `findPool()` and therefore does not apply any of the Find screen's filters (day, time of day, duration, price ceiling, travel, court type, format, intensity, card-only, minimum Player Score). `[VERIFIED]` `[SRC: proto · V.home vs findPool, passes]`

**AC-67** — Given a match with `m.clubCancelled === true` that the player does not hold a seat in and which starts in the future and is not full, Then it **appears in the Now feed**, because the feed filter omits the `!m.clubCancelled` test that `findPool` applies. `[VERIFIED]` **This is a defect — see AC-68.**

**AC-68** — Given a match with `clubCancelled`, `weather`, `inventoryLost`, `formCancelled` or `checkpointCancelled` set, Then it must not appear in the Now feed. `[DERIVED: `findPool` excludes `clubCancelled`; the other four are equally unjoinable]` `[GAP: unspecified]` **Proposal:** filter the feed on `lifeOf(m) !== 'CANCELLED'`, which covers all five in one test and stays consistent with the shared lifecycle.

**AC-69** — Given a match whose club join cutoff has passed (`S.now >= deadlines(m).joinCut`), Then it still appears in the Now feed, because the feed tests only `m.start > S.now`. `[VERIFIED]` **This is a defect — see AC-70.**

**AC-70** — Given a match past its club's join cutoff, Then it must not appear in the Now feed. `[SRC: doc · §10.2 `joinCut` is a published club rule; proto · deadlines]` `[GAP: unspecified]` **Proposal:** add `S.now < deadlines(m).joinCut` to the feed filter.

**AC-71** — Given the player's Player Score is below the 70 gate, Then the feed still renders joinable-looking cards, because the gate is not applied on Now. `[VERIFIED]` `[CONFLICT: doc §2.2 — "Below the reliability gate (70), open matches are not joinable, and the app says so with what clears it"]` **Proposal:** render the feed but replace the price with the gate message, rather than hiding matches, so the player learns what clears it.

## F6. The "Full, but worth waiting for" section

**AC-72** — Given at least one match satisfies `!mySeat(m) && !m.forced && m.start > S.now && isFull(m)` and the sport chip, Then the header `Full, but worth waiting for` is rendered followed by exactly one card. `[SRC: proto · V.home]`

**AC-73** — Given zero such matches, Then neither the header nor any card is rendered — the section is omitted entirely, with no empty state. `[SRC: proto · V.home]`

**AC-74** — Given several such matches, Then the one rendered is the first in `Object.values(S.matches)` order, **not** the highest Match Fit. `[SRC: proto · V.home `full.slice(0,1)` with no sort]` `[GAP: unspecified]` **Proposal:** sort by `matchFit` descending, matching the feed above it, because an unranked pick undermines the section's own claim that it is "worth waiting for".

**AC-75** — Given the seeded clock and `All` selected, Then exactly one candidate exists (m2, Padel at Bonarka Arena, Fri 7 Aug 19:00) and it is rendered. `[VERIFIED]`

**AC-76** — Given the section renders, Then the card is a standard `matchCard` and tapping it pushes the match screen; there is no waitlist action on Now itself. `[SRC: proto · V.home, matchCard]`

## F7. Actions and every branch

### `ACT.sport` — the sport chips

**AC-77** — Given the `All` chip is tapped, Then `S.sport` becomes `'all'`, `S.durs` is emptied, and the screen re-renders. `[SRC: proto · ACT.sport]`

**AC-78** — Given the `Padel` chip is tapped, Then `S.sport` becomes `'Padel'` and both the strip and the feed are filtered to Padel. `[VERIFIED: strip m1, m8; feed 15; full 1]`

**AC-79** — Given the `Tennis` chip is tapped at the seeded clock, Then the strip contains m7 only, the feed has 4 candidates, and the full section is omitted. `[VERIFIED]`

**AC-80** — Given the `Squash` chip is tapped at the seeded clock, Then the strip is empty and renders the `No matches booked` card, the feed has 4 candidates, and the full section is omitted. `[VERIFIED]`

**AC-81** — Given the `Badminton` chip is tapped at the seeded clock, Then the strip is empty, the feed has 4 candidates, and the full section is omitted. `[VERIFIED]`

**AC-82** — Given any sport chip is tapped, Then `S.durs` is cleared as a side effect, silently resetting a duration filter the player set on the Find screen. `[SRC: proto · ACT.sport]` **This is a defect — see AC-83.**

**AC-83** — Given a sport chip is tapped on Now, Then no filter belonging to another screen must be mutated. `[DERIVED]` `[GAP: unspecified]` **Proposal:** move the `S.durs=[]` reset into the Find screen's own sport handler, or validate durations against the new sport at read time instead of clearing them.

**AC-84** — Given the sport selection changes, Then the view key changes and the scroll position resets to the top. `[SRC: proto · render `same` computation includes `S.tab` and `S.findTab` but **not** `S.sport`]` — **note:** because `S.sport` is absent from the view key, the key is unchanged and the scroll position is in fact **preserved**. `[VERIFIED by reading `render`]` `[GAP: unspecified]` **Proposal:** include `S.sport` in the view key, because the content changes completely and a preserved offset lands the player mid-list.

### `ACT.tab` — the tab bar, present on Now

**AC-85** — Given the `Now` tab is tapped, Then `S.tab='now'` and `reset('home')` replaces the entire stack. `[SRC: proto · ACT.tab]`

**AC-86** — Given the `Find` tab is tapped, Then `S.tab='find'` and `reset('find')`. `[SRC: proto · ACT.tab]`

**AC-87** — Given the raised create button is tapped, Then the branch `v === 'create'` runs, setting `S.tab='create'` and `reset('create')`, and returns before the generic mapping. `[SRC: proto · ACT.tab]`

**AC-88** — Given the `Inbox` tab is tapped, Then `S.tab='msg'` and `reset('inbox')`. `[SRC: proto · ACT.tab]`

**AC-89** — Given the `You` tab is tapped, Then `S.tab='you'` and `reset('you')`. `[SRC: proto · ACT.tab]`

**AC-90** — Given any tab is tapped, Then the stack is **reset**, not pushed, so a subsequent back does not return to the previous tab. `[SRC: proto · reset]`

### `data-go` navigation from Now

**AC-91** — Given a state card body is tapped, Then `go('match',{id})` pushes. `[SRC: proto · stateCard wrapper]`

**AC-92** — Given the `Open match` button is tapped, Then `go('match',{id})` pushes — the same destination as AC-91, so the button and the card body are not distinguishable in behaviour. `[SRC: proto · stateCard]`

**AC-93** — Given the envelope button is tapped, Then the click handler's special case fires: `S.tab='msg'; reset('inbox')` — the stack is **replaced**, not pushed, so back does not return to Now. `[SRC: proto · click delegation, `if(v==='inbox')`]` **This is inconsistent with every other `data-go` on the screen — see AC-94.**

**AC-94** — Given the envelope button is tapped from a match card on Now, Then the player must be able to return to Now with the back affordance. `[DERIVED: every other navigation from Now preserves Now as the root]` `[GAP: unspecified]` **Proposal:** push `inbox` rather than resetting, or scope the reset to the tab bar handler only.

**AC-95** — Given a feed card or the full-section card is tapped, Then `go('match',{id})` pushes. `[SRC: proto · matchCard]`

### `ACT.access` — the Getting-in sheet

**AC-96** — Given the `⌘` button is tapped, Then `sheet('access',{id})` opens the sheet over Now, leaving Now visible behind it. `[SRC: proto · ACT.access, doc · §0.6 "sheets … where the context behind them must stay visible"]`

**AC-97** — Given the sheet is open and `S.now >= m.start − 15 min`, Then the door code renders as `4417#`. `[SRC: proto · SH.access, `live`]`

**AC-98** — Given the sheet is open and `S.now < m.start − 15 min`, Then the door code renders as `••••`. `[SRC: proto · SH.access]`

**AC-99** — Given the sheet is open, Then it states the unlock time as `{club} · unlocks at {start − 15 min}` regardless of the branch above. `[SRC: proto · SH.access]`

**AC-100** — Given the sheet is open, Then a QR block, a gear line keyed on sport (`racket, balls` for Padel, `racket, goggles` for Squash, `racket, shuttles` otherwise), a failure phone number, and the line `That is our failure, so the refund is automatic rather than argued.` are shown. `[SRC: proto · SH.access]`

**AC-101** — Given the sheet is open, Then it states `Cached on your phone — it works with no signal.` `[SRC: proto · SH.access]` `[GAP: unspecified]` **Proposal:** this is a promise the prototype does not keep; either implement offline caching of the code and QR before release or remove the sentence, because an unmet offline promise fails exactly when it is needed.

**AC-102** — Given the scrim outside the sheet is tapped, Then the sheet closes and Now is unchanged. `[SRC: proto · click delegation, `e.target.id==='scrim'`]`

### Gallery mode

**AC-103** — Given `S.gallery === true`, Then the strip renders every match where `m.forced` is set, ignoring `mySeat`, `m.left` and the retention window. `[SRC: proto · V.home `gal` branch]`

**AC-104** — Given gallery mode, Then the section header reads `{distinct tag count} tags · {card count} contexts`, which resolves to `17 tags · 32 contexts`. `[VERIFIED]`

**AC-105** — Given gallery mode and more than one card, Then a caption line beneath the dots reads `{tag} — {ctx}` for the first card. `[SRC: proto · V.home]`

**AC-106** — Given gallery mode and the strip is scrolled, Then the caption updates to the tag and context of the centred card. `[SRC: proto · wireStrip]`

**AC-107** — Given gallery mode, Then the feed and full sections render empty, because every match in state carries `m.forced`. `[VERIFIED]`

**AC-108** — Given gallery mode, Then the three contexts absent from `ST_ORDER` — `inventoryLost`, `heldStale`, `heldExtended` — are not shown, so the gallery is not a complete state inventory despite presenting itself as one. `[VERIFIED]` `[GAP: unspecified]` **Proposal:** add the three to `ST_ORDER` so the gallery renders all 35 and the header reads `17 tags · 35 contexts`, matching the doc.

## F8. Every prototype scenario that mounts Now

Each scenario below roots its stack on `home`, so Now is either the visible screen or the screen immediately beneath the pushed one. The expected Now content is stated for each. **37 of the 89 scenarios mount Now; the remaining 52 do not and are listed in F9.**

### Group: the court hold ladder (6)

**AC-109** — `holdFar` — *"Two paid, three days out"*. Given m1 with 2 of 4 paid, created Wed 19:00, clock Fri 22:30, Then the m1 card resolves to **`heldStale` / tag `Court released`**, because the match is 51.5 h old against Zabłocie's 48 h `maxHoldAge` and `filled < n−1`. `[VERIFIED]` `[CONFLICT: the scenario's own description says "A court is held on two seats … Soft, and it says so"]`

**AC-110** — `holdFarLapsed` — *"Still two, twelve hours out"*. Given the same match at Sat 09:30, Then the card resolves to **`formingLate` / tag `Forming`**, not `heldReleased`, because the stale rule prevented a court from ever being assigned so `releasedAt` is null. `[VERIFIED]` `[CONFLICT: the description says "The court goes back", which implies `Court released`]`

**AC-111** — `holdNear` — *"Three paid, eight hours out"*. Given m1 with 3 of 4 paid at T−8 h, Then the card resolves to `heldSoft` / tag `Court held`, context `one player short`, court line naming the 4-hour rung. `[VERIFIED]`

**AC-112** — `holdNearLapsed` — *"Still three, three hours out"*. Given the same match advanced to T−3 h after a court was held, Then the card resolves to `heldReleased` / tag `Court released`, and the line reads `The last seat books a court on the spot` because `need === n`. `[VERIFIED]`

**AC-113** — `holdLost` — *"The last court goes"*. Given an unsecured match inside 12 h whose category has sold out, Then `syncMatch` sets `inventoryLost` and `clubCancelled`, and the card resolves to `inventoryLost` / tag `Cancelled` with the court line `Gone — the last Mondo court was sold`. `[VERIFIED]`

**AC-114** — `holdLocked` — *"The club commits it anyway"*. Given `m.courtLocked` with 2 of 4 paid at T−3 h, Then `courtHold` returns a **hard** hold with reason `club`, and the card resolves to `clubHeld` / tag `Court committed`, overriding the lapsed ladder. `[VERIFIED]`

### Group: match states (1)

**AC-115** — `states` — *"Every match state"*. Given the gallery is built, Then Now shows 32 forced cards, the header reads `17 tags · 32 contexts`, and the feed and full sections are empty. `[VERIFIED]`

### Group: court certainty and commitment (6)

**AC-116** — `cert0` — *"Two players · no court held"*. Given m1 reduced to 2 of 4 at Wed 21:00 with `courtId` cleared, Then `syncMatch` **re-assigns a court** and the card resolves to `heldSoft` / tag `Court held`, reason `far`. `[VERIFIED]` `[CONFLICT: the description says "nothing is reserved". Invariant 4 agrees with the code — 2 paid seats hold a court while more than 12 hours remain — so the scenario text is the error.]`

**AC-117** — `formRisk` — *"The risk while forming"*. Given the same shape at Wed 20:30, Then the card resolves to `heldSoft`, not `forming`. `[VERIFIED]` `[CONFLICT: same as AC-116]`

**AC-118** — `cert1` — *"Three players · court protected"*. Given m1 at 3 of 4, Wed 22:00, Then the card resolves to **`heldSoft` / tag `Court held`**, not `protectedCourt` / tag `Court protected`, because a 3-of-4 doubles hold is always `soft`. `[VERIFIED]` `[CONFLICT: scenario name and the doc's §3.3 "Protected" group both imply `Court protected`]`

**AC-119** — `cert2` — *"Full, before the deadline"*. Given m1 at 4 of 4 with `committedAt` null, clock Fri 12:30 (6 h before commit), Then the card resolves to `full` / tag `Full`, and the court line reads `Reserved · settles to the club at 18:30`. `[VERIFIED]`

**AC-120** — `cert2`, second assertion — Given the same clock, Then m7 also appears in the strip in `playedNoScore` / tag `Played`, because it ended Thu 20:00 and is still inside the 24-hour retention window. `[VERIFIED]`

**AC-121** — `cert3` — *"Incomplete after the deadline"*. Given m1 at 3 of 4, `committedAt` null, clock Fri 20:30 (2 h past commit), Then the card resolves to `heldSoft` / tag `Court held` and the group line reads `3 of 4 seats paid`. `[VERIFIED]` — the match is past its deadline yet nothing is committed, which is Invariant 2 made visible.

**AC-122** — `cert4` — *"The last seat fills late"*. Given m1 filled to 4 of 4 after the deadline at Fri 20:30, Then `syncMatch` writes `committedAt = S.now`, `committedOnFill()` is true, and the card resolves to `confirmedOnFill` / tag `Confirmed` with group line `4 of 4 · committed on the spot`. `[VERIFIED]`

### Group: your position on the clock (4)

**AC-123** — `pos0` — *"Free to leave"*. Given m1 full, uncommitted, clock Fri 09:30, Then the Now card resolves to `full` / tag `Full` and the pushed `position` screen is open above it. `[VERIFIED]`

**AC-124** — `pos1` — *"Full-price search"*. Given m1 committed with Ola vacated at T−10 h, clock Sat 09:30 (before T−4 h), Then the card resolves to `replacement` / tag `Replacement pending`, with the alert block present. `[VERIFIED]`

**AC-125** — `pos2` — *"50/50 Rescue"*. Given the same match at Sat 15:10 (40 min past the T−4 h rescue threshold), Then the card resolves to `rescue` / tag `Rescue active`, tone `time`, with the alert block present. `[VERIFIED]`

**AC-126** — `pos3` — *"Past the checkpoint"*. Given the same match at Sat 16:50 (T−100 min, past the T−2 h checkpoint) at a club with `rebooking: true`, Then `syncMatch` sets `checkpointCancelled` and the card resolves to `cancelledCheckpoint` / tag `Cancelled`, stating the three who stayed hold 38,00 zł credit. `[VERIFIED]`

### Group: walkthrough (2 of 9 mount Now)

**AC-127** — `intro` — *"Start here"*. Given the boot state at Wed 21:00, Then the strip shows m7 `Confirmed`, m1 `Court held`, m8 `Full`, in that order. `[VERIFIED]`

**AC-128** — `privOwn` — *"Open my empty seats"*. Given a private split-payment court `pv1` is created with 2 of 4 shares paid, Then a fourth card appears in the strip resolving to `privatePartial` / tag `Reserved`, sorted last because it starts Sun 18:30. `[VERIFIED]`

### Group: cancellation, nine scenarios (9)

**AC-129** — `s1` — *"Leave while forming"*. Given m1 at 2 of 4 with no court, clock Wed 21:00, cancel screen pushed, Then the Now card beneath resolves to `heldSoft`. `[VERIFIED]` `[CONFLICT: the description says "no court held"; see AC-116]`

**AC-130** — `s2` — *"Full, but before the deadline"*. Given m1 full and uncommitted at Fri 12:30, Then the Now card resolves to `full` / tag `Full`. `[VERIFIED]`

**AC-131** — `s3` — *"Incomplete after the deadline"*. Given m1 at 3 of 4, uncommitted, Fri 21:30, Then the Now card resolves to `heldSoft` / tag `Court held`. `[VERIFIED]`

**AC-132** — `s4` — *"Leave after commitment"*. Given m1 full and committed at the deadline, clock Sat 07:30, Then the Now card resolves to `confirmed` / tag `Confirmed`. `[VERIFIED]`

**AC-133** — `s5` — *"The Rescue Seat"*. Given the player has left (`m.left === true`) and the search screen is pushed, Then m1 is **absent** from the Now strip and only m8 remains. `[VERIFIED]`

**AC-134** — `s6` — *"Transfer my seat"*. Given m1 committed at Sat 09:30 with the transfer screen pushed, Then the Now card resolves to `confirmed` / tag `Confirmed` — the transfer has not yet been executed so `m.transferring` is unset. `[VERIFIED]`

**AC-135** — `s7` — *"Checkpoint · rebooking club"*. Given m1 at Zabłocie (rebooking) short at Sat 17:30, Then the Now card resolves to `cancelledCheckpoint` and the `nofill` screen is pushed. `[VERIFIED]`

**AC-136** — `s8` — *"Checkpoint · standard club"*. Given m2 at Bonarka (`rebooking: false`) short at T−1 h, Then the Now card for m2 resolves to `rescueLate` / tag `Rescue active` — the match stays alive rather than cancelling. `[VERIFIED]`

**AC-137** — `s9` — *"Never completed · T−2h"*. Given m1 at 2 of 4, uncommitted, at Sat 16:50, Then `syncMatch` sets `formCancelled` and the card resolves to `cancelledIncomplete` / tag `Cancelled`. `[VERIFIED]`

### Group: edge cases (2 of 3 mount Now)

**AC-138** — `noshow` — *"No-show"*. Given the clock is Mon 10 Aug 20:20, Then every match the player holds has aged past the 24-hour retention window and the Now strip renders the empty card, while the pushed match screen shows m6. `[VERIFIED]`

**AC-139** — `clubx` — *"Club or weather cancels"*. Given `m.clubCancelled` is set on m1 at Sat 09:30 with 2 of 4 paid, Then `syncMatch` also sets `inventoryLost` (the category has sold out inside 12 h) and the card resolves to **`inventoryLost`**, not `cancelledClub`, because `inventoryLost` is tested first. `[VERIFIED]` `[CONFLICT: the scenario name implies `cancelledClub`; the resolution order in `matchState` decides otherwise]`

### Group: waitlist and engine (2 of 4 mount Now)

**AC-140** — `offer` — *"A seat has opened"*. Given the player is waitlisted on m2 and the `waitoffer` screen is pushed at Fri 09:30, Then the Now strip beneath shows m7 `Played`, m1 `Court held`, m8 `Full` — the waitlisted match m2 is **absent**, because the strip requires `mySeat`. `[VERIFIED]`

**AC-141** — `engine` — *"Escalation order"*. Given m1 committed with Ola vacated, clock Sat 09:30, search screen pushed, Then the Now card resolves to `replacement` / tag `Replacement pending`. `[VERIFIED]`

### Group: ratings and money (3 of 7 mount Now)

**AC-142** — `needsres` — *"Enter the score on court"*. Given m1 ended at Sat 20:00 and the clock is Sat 20:05, Then the card resolves to `needsResult` / tag `Needs result`, `post` is set so the `⌘` button is suppressed. `[VERIFIED]`

**AC-143** — `result` — *"Confirm from the other side"*. Given a score exists entered by Kuba and the clock is Sat 20:09, Then the card resolves to `confirmResult` / tag `Confirm the result`. `[VERIFIED]`

**AC-144** — `lapsed` — *"Nobody entered it"*. Given the clock is Sat 20:50, more than 30 minutes past the 20:00 end, Then the card resolves to `playedNoScore` / tag `Played` and Now is the visible screen with nothing pushed above it. `[VERIFIED]`

### Group: ecosystem · club → player (2 of 11 mount Now)

**AC-145** — `ecoStale` — *"A hold released at 48 hours"*. Given m1 at 2 of 4 created 60 h ago, clock Fri 12:30, Then the card resolves to `heldStale` / tag `Court released` and the lines name the club's maximum hold age as a club setting. `[VERIFIED]`

**AC-146** — `ecoExtend` — *"A hold kept past the ladder"*. Given m1 at 3 of 4 at T−3 h with `clubExtended` and `clubFill: 97` at a club whose `probHold` is true, Then the card resolves to `heldExtended` / tag `Court held`, tone `good`, stating 97%. `[VERIFIED]`

## F9. Scenarios that do not mount Now

**AC-147** — Given any of the following 52 scenarios is run, Then Now is not in the navigation stack and no Now assertion applies: the 13 onboarding scenarios (`obStart`, `obSports`, `obBeginner`, `obDeveloping`, `obEstablished`, `obAdvanced`, `obDifficulty`, `obContra`, `obUnderclaim`, `obUneven`, `obLayoff`, `obDone`, `obData`); the 6 duplicate-prevention scenarios (`dupNone`, `dupOne`, `dupRoom`, `dupFew`, `dupBusy`, `dupOtherDay`); 7 walkthrough scenarios (`find`, `courts`, `join`, `create`, `createOpen`, `createPriv`, `lineup`); `late`; `wl`; `avail`; `passport`; `score`; `wallet`; `card`; the 9 request scenarios (`ecoInvite`, `ecoWiden`, `ecoShift`, `ecoMerge`, `ecoResched`, `ecoOffer`, `ecoCourt`, `ecoPay`, `ecoQueue`); the 7 "what you can now do" scenarios (`ecoIntent`, `ecoEnt`, `ecoProg`, `ecoComp`, `ecoGroups`, `ecoWallet`, `ecoClub`); and `ecoIntentEdit`, `ecoOptIn`, `ecoOnboardOpt`. `[VERIFIED]`

**AC-148** — Given the scenario registry, Then it contains 89 unique entries while the rail lists 90, because `ecoIntent` is registered in two rail groups and defined twice, the second definition overwriting the first. `[VERIFIED]` `[CONFLICT: doc §14 states 90 scenarios]` **Proposal:** remove the duplicate rail entry, or give the two a distinct id each, so the count is honest.

## F10. Boundary values

**AC-149** — Given a match whose end is exactly 24 hours before the clock, Then it is **not** shown, because the test is `matchEnd + 24h > S.now`, strictly greater. `[VERIFIED]`

**AC-150** — Given a match whose end is 24 hours minus 1 ms before the clock, Then it **is** shown. `[VERIFIED]`

**AC-151** — Given a match whose end is 24 hours plus 1 ms before the clock, Then it is not shown. `[VERIFIED]`

**AC-152** — Given a 4-player match with 3 seats paid at exactly T−4 h, Then the hold has lapsed (`nearLapsed`) and no court is held. `[VERIFIED]`

**AC-153** — Given the same match at T−4 h minus 1 ms of elapsed time (that is, 4 h + a fraction remaining), Then the hold is `soft` with reason `near`. `[VERIFIED]`

**AC-154** — Given a 4-player match with 2 seats paid at exactly T−12 h, Then the hold has lapsed (`farLapsed`). `[VERIFIED]`

**AC-155** — Given the same match with marginally more than 12 h remaining, Then the hold is `soft` with reason `far`. `[VERIFIED]`

**AC-156** — Given a 2-player match with 1 seat paid at any distance from play, Then the hold is `none` with reason `thin`, because the `n > 2` guard skips both soft tiers. `[SRC: proto · courtHold]` `[SRC: doc · §0.2 "Singles has no soft tier"]`

**AC-157** — Given a match at Zabłocie (`maxHoldAge: 48`) with a soft hold, 2 of 4 paid, aged exactly 48.0 h, Then the hold is **not** stale, because the test is strictly greater. `[VERIFIED]`

**AC-158** — Given the same match aged 48.1 h, Then the hold becomes `stale` and the state becomes `heldStale`. `[VERIFIED]`

**AC-159** — Given a match with 3 of 4 paid (`filled === n−1`) aged beyond `maxHoldAge`, Then the stale rule does **not** apply, because it additionally requires `filled < n−1`. `[SRC: proto · courtHold override]`

**AC-160** — Given a club with `maxHoldAge: null` (Ogrody 33, Krakowianka, Podgórze Hall), Then no hold ever goes stale there. `[SRC: proto · POLICY]`

**AC-161** — Given a full match at exactly T−15 min, Then the state is `ready`. `[VERIFIED]`

**AC-162** — Given a full committed match at T−15 min minus 1 ms of elapsed time, Then the state is `confirmed`, not `ready`. `[VERIFIED]`

**AC-163** — Given a full match at exactly the commitment deadline, Then `syncMatch` writes `committedAt = d.commit` (not `S.now`), because the late branch requires `S.now > commit + 60 s`. `[SRC: proto · syncMatch]`

**AC-164** — Given a full match at commit + 60 s exactly, Then `committedAt = d.commit` and the state is `confirmed`, because the test is strictly greater. `[SRC: proto · syncMatch]`

**AC-165** — Given a full match at commit + 60 s + 1 ms, Then `committedAt = S.now` and `committedOnFill()` is true, so the state is `confirmedOnFill`. `[SRC: proto · syncMatch, committedOnFill]`

**AC-166** — Given a match at exactly the checkpoint (`start − 2 h`) that is incomplete and uncommitted, Then `formCancelled` is set, because the test is `S.now >= d.check`. `[SRC: proto · syncMatch]`

**AC-167** — Given a match at exactly the checkpoint that is committed, short, has no sponsored guest, and whose club has `rebooking: true`, Then `checkpointCancelled` is set. `[SRC: proto · syncMatch]`

**AC-168** — Given the same match at a club with `rebooking: false`, Then nothing is cancelled and the state becomes `rescueLate`. `[VERIFIED: SCEN.s8]`

**AC-169** — Given a match at exactly `matchEnd + 30 min` with no confirmed score, Then the state is `playedNoScore`, because the test is `S.now >= resultWindow(m)`. `[SRC: proto · matchState, resultWindow]`

**AC-170** — Given a match at `matchEnd + 30 min` minus 1 ms with a score entered and unconfirmed, Then the state is `confirmResult`. `[SRC: proto · matchState]`

**AC-171** — Given the commitment deadline, Then it is `min(start − club.window h, start − 12 h)` — the earlier of the two — for every club, and a club may commit earlier than the platform default but never later. `[SRC: doc · §0.2 Invariant 2; proto · deadlines]`

**AC-172** — Given a doubles match, Then the Rescue threshold is `start − 4 h`; given a singles match, `start − 6 h`. `[SRC: proto · deadlines; doc · §15 "rescue at 4 h doubles and 6 h singles"]`

**AC-173** — Given any match at any club, Then the checkpoint is `start − 2 h` universally, with no club override. `[SRC: proto · deadlines; doc · §15 "checkpoint at 2 h universally"]`

---

# G. EDGE CASES AND FAILURE MODES

## G1. Timing and clock boundaries

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G1.1 | The clock crosses a hold threshold while Now is open on screen | The card must change state | **Nothing — there is no re-render timer.** The card is stale until any interaction | Yes, on any tap `[GAP]` **Proposal:** 30-second interval re-render while Now is visible, plus an immediate render on foreground |
| G1.2 | The clock crosses the checkpoint while the app is backgrounded | On the next render `syncMatch` sets `formCancelled` or `checkpointCancelled` and pushes a notification onto `S.notif` | The card reads `Cancelled`; the notification exists but has no delivery channel | Not recoverable — the match is gone. The 2-hour notice is the mitigation `[SRC: doc · §3.3, proto · syncMatch]` |
| G1.3 | A match is created inside its own commitment window, so its deadline is already past | `formingLate` renders the `born` variant: *"You created this inside the club's cancellation window, so it commits the moment it fills"* rather than the alarming variant | The non-alarming copy | Yes `[SRC: proto · ST.formingLate]` |
| G1.4 | Daylight-saving transition between now and play | **Unhandled.** All arithmetic is on epoch milliseconds with `HOUR = 3600e3`, so a 23- or 25-hour day shifts every derived deadline by an hour relative to wall-clock | Nothing | `[GAP: unspecified]` **Proposal:** compute deadlines in the club's local calendar, not in fixed millisecond offsets, because a commitment deadline that moves by an hour is a refund dispute |
| G1.5 | The player's device clock is wrong | Every state on Now is wrong, silently | Nothing | `[GAP: unspecified]` **Proposal:** derive `S.now` from a server timestamp; never from the device |
| G1.6 | Two matches start at the same instant | Strip order is non-deterministic (AC-16) | Nothing | Cosmetic |
| G1.7 | A match ends exactly 24 h ago | Card drops (AC-149) | It simply disappears — no history affordance exists on Now | `[GAP]` **Proposal:** the strip's empty state should link to history when the player has past matches |

## G2. Concurrency — two people acting on the same object

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G2.1 | Another player pays the last seat while Now is open | On the next render the card moves from `heldSoft`/`protectedCourt` to `full`, `confirmed` or `confirmedOnFill` | The new tag and lines | Yes |
| G2.2 | Another player leaves after commitment while Now is open | The card moves to `replacement` **with a red alert block** naming them | *"{name} left after the commitment deadline… Your payment will not change."* | Yes `[SRC: proto · ST.replacement]` |
| G2.3 | Two players leave simultaneously | **Not modelled.** The doc names this explicitly: *"No partial-group cancellation. Two players leaving simultaneously is not modelled."* `m.vacated` holds a single id, so the second leaver overwrites the first | The card names only one leaver | `[SRC: doc · §17.4]` `[GAP]` **Proposal:** `vacated` must become an array before release; the card should read *"Two players left"* and the group line must show the true fill |
| G2.4 | The player taps a card at the exact moment `syncMatch` cancels the match | `go('match')` pushes the match screen, which re-runs `matchState` and shows the cancelled state | The cancelled state on the pushed screen | Yes |
| G2.5 | A club releases a court in the console while the player is on Now | The player app must **read** the club's published state, never recompute it | Whatever the club published | `[SRC: doc · §0.2 Invariant 6]` — the doc records this as the worst possible failure |
| G2.6 | A replacement is found while the leaver's device shows `replacement` | `fillSeat` clears `vacated` and the card returns to `confirmed` | *"{name} took the seat"* notification and a refund ledger entry | Yes `[SRC: proto · fillSeat]` |

## G3. Money — partial failure, retry, refunds, declines

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G3.1 | A refund is pending when the card would otherwise drop off Now | The match disappears from Now the moment `m.left` is set, **before the refund settles** | Nothing on Now; the ledger entry is on the Money screen | `[SRC: proto · V.home filter, leaveMatch]` `[GAP]` **Proposal:** keep a left match on Now until its refund resolves, because the disappearance of a match with money in flight is the single most alarming silence on the screen |
| G3.2 | The seat is offered to replacements before the refund settles | Correct and deliberate: *"The seat is offered to replacements immediately, before the refund settles."* | The `replacement` card | `[SRC: doc · §4.2]` |
| G3.3 | Insufficient funds / card declined at the moment of joining | Now is not the payment surface; the failure occurs on the pay screen | — | `[SRC: proto · V.pay]` |
| G3.4 | A recurring charge fails | Retries after 24 hours before any person is asked | Nothing on Now | `[SRC: doc · §4.4]` |
| G3.5 | The player has outstanding debt above a club's threshold | The debt CTA appears on the **match** screen, not on Now. The Now feed continues to show that club's matches at full price with no indication they cannot be booked | *"Zabłocie is holding new bookings until 112,00 zł is settled"* — but only after a tap | `[SRC: doc · §4.4; proto · V.match override]` `[GAP]` **Proposal:** surface the debt state on Now, because a feed of matches the player cannot book is a feed of dead ends |
| G3.6 | Card authorisation is required (two recent no-shows) | Same as G3.5 — the disclosure lives on the match screen | *"Your card will be authorised, not charged."* | `[SRC: doc · §4.4]` |
| G3.7 | A club cancels after a Rescue payment was made | *"A Rescue payment, if one had been made, is refunded too"* | Stated on the `cancelledClub` card | Yes `[SRC: proto · ST.cancelledClub]` |
| G3.8 | A slot discount is applied to a court after seats were sold | `payable` reads `shareAfterDisc`, which recomputes from `m.price − slotDisc` at read time, so a discount applied later changes what an existing card displays | The new figure, with the old one struck through on feed cards | `[SRC: proto · shareAfterDisc, payable override]` `[CONFLICT: Invariant 1 says the share is "written the moment the match is created and never re-priced"]` — see H |

## G4. Identity and permission

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G4.1 | The viewer holds no seat in a match being rendered | Every `You paid…` line is rewritten to `Your share would be {payable} · booking fee 0,00 zł` | The conditional phrasing | `[SRC: proto · matchState]` — unreachable from the Now strip, which requires `mySeat` |
| G4.2 | A blocked player is in a match in the feed | *"A blocked player never appears in a match with you, and is never told."* **The Now feed applies no block filter** | Nothing | `[SRC: doc · §12]` `[GAP]` **Proposal:** exclude any match containing a blocked player from the feed and the full section, in the same filter that excludes cancelled matches |
| G4.3 | A private court the player owns | Appears in the strip as `Reserved`, with the guarantee stated | *"Two shares are still unpaid, and you guarantee them"* | `[VERIFIED: SCEN.privOwn]` |
| G4.4 | A match with restricted joining (`friends` / `invite only`) appears in the feed | **No visibility rule is applied.** The feed filter has no `outsideMayAsk` test | Nothing until the player taps through | `[SRC: proto · V.home vs mkMatch `outsideMayAsk`]` `[GAP]` **Proposal:** respect `outsideMayAsk` in the feed filter |

## G5. Data absence

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G5.1 | The player has no rating in a sport | Matches in that sport are dropped from the feed with no explanation | Nothing — the feed is simply shorter, or empty with the generic copy | `[SRC: proto · matchFit]` `[GAP]` **Proposal:** show the matches with the message *"Rate {sport} to see how well these fit you"*, because a silently empty feed reads as an empty city |
| G5.2 | A match has no assignable court in its category | `pickCourt` returns null; if the hold is hard, `inventoryLost` and `clubCancelled` are set | The `inventoryLost` card | `[SRC: proto · syncMatch]` |
| G5.3 | A match category has no matching courts at all | `categoryCourts` falls back to every court of that sport at the club | Nothing — silently widened | `[SRC: proto · categoryCourts]` `[GAP]` **Proposal:** this silently changes the product the player bought; it must either be prevented at creation or disclosed |
| G5.4 | A club has no published fill model | The doc requires: *"a club with no fill model publishes nothing, and the app must fall back to the ladder and say so"* | The ordinary ladder copy | `[SRC: doc · §17.2]` — implemented via the `probHold` gate in `clubExtended` |
| G5.5 | A player id on a seat has no `PLAYERS` record | `ST.protectedBack` guards with `PLAYERS[m.vacated] ? … : 'A player'`; `ST.replacement` does the same; **`ST.replacementTransfer` and `ST.playedShort` hardcode `Ola`, and `ST.playedNoShow` hardcodes `Marek`** | A wrong name | `[VERIFIED]` `[GAP]` **Proposal:** every name in a state line must come from the match record; hardcoded names are prototype residue that will ship as a data-integrity bug |
| G5.6 | `CLUBS[m.club]` is missing | `stateCard` throws on `CLUBS[m.club].n` and the whole screen fails to render | A blank screen | `[DERIVED]` `[GAP]` **Proposal:** per-card error boundary (E1) |

## G6. Third-party unavailability

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G6.1 | The club's system is unreachable when Now renders | Not modelled — all state is local | Nothing | `[GAP]` **Proposal:** show the last-known card with a `last checked {time}` line rather than an error, because a court state is more useful stale than absent |
| G6.2 | The door code service is unreachable | The sheet promises the code is cached and works with no signal | *"Cached on your phone — it works with no signal"* | `[SRC: proto · SH.access]` — the promise is currently unimplemented (AC-101) |
| G6.3 | The door code fails at the door | The sheet gives a phone number and states *"That is our failure, so the refund is automatic rather than argued"* | An automatic-refund promise | `[SRC: proto · SH.access]` `[GAP]` **Proposal:** no code path implements this refund; it must exist before the sentence ships |
| G6.4 | The payment provider is down | Now is unaffected; failure surfaces on the pay screen | — | `[DERIVED]` |

## G7. The user acting from a stale screen

| # | Trigger | Expected behaviour | What the user is told | Recoverable |
|---|---|---|---|---|
| G7.1 | The player taps a feed card for a match that filled since the render | `V.match` re-resolves and the join CTA is absent; `joinMatch` additionally guards with `toast('This match is full','bad')` | The full state and, if they reach the action, a toast | Yes `[SRC: proto · joinMatch]` |
| G7.2 | The player taps a feed card for a match that was cancelled since the render | The pushed match screen shows the cancelled state | The cancelled state | Yes |
| G7.3 | The player taps `⌘` on a card whose match was cancelled since the render | The access sheet opens and renders a door code section for a cancelled match | A masked or live door code for a match that will not happen | **No guard exists** `[VERIFIED]` — see AC-46 |
| G7.4 | The player taps a card whose match has aged out of the retention window since the render | `go('match')` still resolves, because retention affects only the Now filter | The match screen | Yes |
| G7.5 | The player acts on a state card after `syncMatch` has already cancelled the match in the same render pass | Impossible: `syncAll()` runs **before** `V.home()` builds the markup, so the card is always drawn from post-sync state | — | `[SRC: proto · render]` |

---

# H. RULES THAT ARE EASY TO GET WRONG

This is the highest-value section. Each entry states the wrong-but-plausible implementation, the correct one, and why the difference matters.

### H1. "Two paid seats means no court is held"

**Wrong:** treat a court as held only from the third payment, because three of the prototype's own scenario descriptions (`cert0`, `formRisk`, `s1`) say *"no court held"* at two paid seats.
**Correct:** two paid seats hold a **soft** court while more than 12 hours remain. Only 0 or 1 paid seats hold nothing. `[SRC: doc · §0.2 Invariant 4; proto · courtHold]` `[VERIFIED: `cert0` resolves to `heldSoft`, not `forming`]`
**Why it matters:** the whole hold ladder is a four-rung structure. Collapsing the bottom two rungs removes the tier that makes a match viable three days out, which is exactly the demand the product exists to capture. The scenario descriptions are stale; the ladder is the specification.

### H2. "Three paid seats means the tag is `Court protected`"

**Wrong:** map a 3-of-4 match to `protectedCourt` / tag `Court protected`, because the scenario is literally called *"Three players · court protected"* and the doc's §3.3 lists a Protected group.
**Correct:** a 3-of-4 doubles match yields `courtHold().kind === 'soft'`, and `matchState` routes every soft hold to `heldSoft` / tag **`Court held`**. `protectedCourt` and `protectedLate` are reachable only through the forced gallery. `[VERIFIED]`
**Why it matters:** an implementer who codes to the scenario name will produce a tag the engine never emits, and a QA engineer testing for `Court protected` will file a false defect. Decide deliberately whether the third payment deserves its own tag — see K.

### H3. "A soft hold lapses only because the clock reached the rung"

**Wrong:** treat `courtHold` as a pure function of seat count and time to play.
**Correct:** there are two additional, club-published overrides applied **after** the ladder: a hold older than the club's `maxHoldAge` goes stale (Zabłocie 48 h, Bonarka 72 h, Atlantic 24 h, Centrum 24 h, Wisła 72 h, MOSiR 48 h, three clubs `null`), and a lapsed hold may be **re-held** if the club extended it and the club's `probHold` flag is on. `[SRC: proto · courtHold override, POLICY]`
**Why it matters:** it silently changed two of the six hold-ladder scenarios (AC-109, AC-110). Any implementation that ports the base ladder without the override will disagree with the club console, which is the failure Invariant 6 exists to prevent.

### H4. "The Now feed is the Find list, shortened"

**Wrong:** call `findPool()` and take the top three, or assume the Now feed inherits Find's exclusions.
**Correct:** the Now feed uses its own filter, which shares only `!mySeat` and `start > now`. It does **not** exclude cancelled matches, does not apply the reliability gate, does not respect the join cutoff, does not honour `outsideMayAsk`, does not exclude matches containing blocked players, and does not apply any of the eight Find filters. `[VERIFIED]`
**Why it matters:** this is the single largest correctness gap on the screen. A cancelled match is currently a valid Now feed card. The doc's four structural `findPool` exclusions — *"A Rescue Seat can never appear here — there is no code path from the rescue engine to the public search"* `[SRC: doc · §2.2]` — are **not** enforced on Now by construction; they happen to hold only because a Rescue Seat is never a separate match record. That is an accident, not a guarantee.

### H5. "A hold released means the tag is `Court released`"

**Wrong:** map every lapsed hold to `heldReleased`.
**Correct:** `heldReleased` requires that a court was **actually assigned and then released** (`releasedAt != null`), that at least 2 seats are paid, and that the clock is before the checkpoint. A match that never got a court — because the stale rule or an empty category prevented assignment — falls through to `forming` or `formingLate` instead, which reads as *"Forming"* even though a player is watching a court fail to materialise. `[VERIFIED: AC-110]`
**Why it matters:** the doc's justification for `heldReleased` is that *"silence there would be the single most alarming gap on the screen"* `[SRC: proto · matchState comment]`. The stale path reintroduces exactly that silence.

### H6. "Cancelled is one state"

**Wrong:** one Cancelled card with one explanation.
**Correct:** four contexts with four different money outcomes: `cancelledIncomplete` (everybody refunded in full, nobody was committed), `cancelledCheckpoint` (the three who stayed get **club credit**, the leaver forfeits), `cancelledClub` (everybody refunded **including anybody who had already left**, and a Rescue payment too), `inventoryLost` (everybody refunded, and the explanation is that the match never had a court). `[VERIFIED]`
**Why it matters:** the refund differs in each. Merging them produces a card that is financially wrong three times out of four.

### H7. "T−2h means the match is cancelled"

**Wrong:** implement the checkpoint as a single rule.
**Correct:** T−2h means two different things. If the match was **never complete**, `formCancelled` fires and everybody is refunded — nobody was ever committed. If the match **was** committed but is short, `checkpointCancelled` fires only at a club with `rebooking: true`; at a club without it, nothing cancels and the match continues into `rescueLate` where the group may bring a guest or play three. `[SRC: proto · syncMatch; SCEN.s7 vs s8; doc · §3.3]`
**Why it matters:** implementing one branch cancels matches at half the clubs that should keep running, or keeps matches alive at clubs that already released the hour.

### H8. "The last seat filling late is the same as filling on time"

**Wrong:** one `confirmed` state.
**Correct:** `committedOnFill()` is true when `committedAt > commit + 60 s`, producing `confirmedOnFill` with different copy: *"The deadline had already passed, so the final payment committed everybody at once. Everyone knew that joining the last seat would do this."* `[SRC: proto · committedOnFill]`
**Why it matters:** the joining player was warned before paying (scenario `late`). The three already in the match were not, and the card is the only place they learn that their free-cancellation window closed the instant somebody else paid.

### H9. "A match the player left should still show, since the money is still moving"

**Wrong** *(and also right)*: this is a genuine tension. The implementation drops the match from Now the moment `m.left` is set, while the refund is still pending and while the replacement search the player's refund depends on is still running.
**Correct per the code:** dropped immediately `[VERIFIED: SCEN.s5]`.
**Correct per the product intent:** unclear. Invariant 3 makes the refund depend on an outcome that has not happened yet, and Now is the only surface that tracks outcomes. See K.
**Why it matters:** the player's refund is 100%, 50% or 0% depending on something they can no longer watch.

### H10. "Tone is decorative"

**Wrong:** treat the tone key as a colour hint and default anything unknown.
**Correct:** `ST_TONE` has exactly five keys — `good`, `watch`, `time`, `ended`, `idle` — and `ST.inventoryLost` declares a sixth, `bad`, that does not exist. `[VERIFIED]`
**Why it matters:** it renders `background:undefined` on a Cancelled card today. More broadly, the tone is the only pre-attentive signal on the card; a missing colour on the most severe state is the worst place to lose it.

### H11. "The share never changes, so `payable` can be cached"

**Wrong:** cache `payable(m)` alongside the match.
**Correct:** `payable` is overridden to compute `shareAfterDisc(m)` — `(m.price − slotDisc(m)) ÷ m.n` — then subtract the club card offset, on every read. A club applying a slot discount changes what an already-sold seat displays. `[SRC: proto · payable override, slotDisc]`
**Why it matters:** this sits in tension with Invariant 1's *"written the moment the match is created and never re-priced"* `[SRC: doc · §0.2]`. The code's own comment defends it — *"A club may reduce the COURT price for one slot. It may never set a seat price"* — but the effect on an existing seat holder is a re-price. Flagged as a conflict; see K.

### H12. "Notifications are emitted by a background job"

**Wrong:** assume `notify()` is called from a scheduler.
**Correct:** `notify()` is called from inside `syncMatch()`, which is called from `syncAll()`, which is called from `render()`. **Rendering Now is what produces the notification.** `[SRC: proto · render → syncAll → syncMatch]`
**Why it matters:** three consequences. A player who never opens the app never generates the notification. A player who opens the app generates notifications for **every match in state**, including ones they are not in. And each guard (`softNotified`, `invNotified`, `clubNotified`, `wasRescue`, `wasForm`, `wasChk`) is a per-record boolean, so the de-duplication is only as durable as the record. In production this must be a server-side job with the player app as a pure reader.

### H13. "The retention window is 'today's matches'"

**Wrong:** filter the strip on "starts today" or "not yet played".
**Correct:** `matchEnd(m) + 24 h > S.now`, which keeps a finished match on Now for a full day and, in the same list, a match four days out. The strip is not a day view. `[SRC: proto · KEEP_H]`
**Why it matters:** the 24-hour tail is where the score is entered and confirmed. Cutting it at end-of-play removes the surface that produces the ratings the entire product depends on.

### H14. "Sorting the strip by urgency is more helpful than by start time"

**Wrong:** float the `Rescue active` or `Needs result` card to the front.
**Correct:** strictly ascending by `m.start`, always. `[SRC: proto · V.home]`
**Why it matters:** the doc's framing is *"What is happening to you today and next, **in the order you need it**"* `[SRC: doc · §2.1]` — and it resolves that as chronological. A stable chronological order means the card in position one is always the next thing that happens, which is what makes the screen glanceable. Urgency is carried by tone and the alert block, not by position.

### H15. "The empty state can name the filter"

**Wrong:** assume the your-matches empty state adapts to the sport chip.
**Correct:** it says *"No matches booked"* regardless, while the feed empty state directly beneath it says *"Nothing open in Squash right now"*. A player with three booked matches who taps `Squash` is told they have no matches booked. `[VERIFIED: AC-22]`
**Why it matters:** it is a false statement about the player's own money, and it is adjacent to a correctly sport-aware message, which makes it read as authoritative.

### H16. "`heldExtended` means our model says it will fill"

**Wrong:** compute a fill probability to decide whether to extend.
**Correct:** read `m.clubExtended` and `m.clubFill` as published facts, gated on the club's `probHold` policy. Extension may only ever lengthen a hold — *"no model may release a court earlier than the ladder promised."* `[SRC: proto · clubExtended, ST.heldExtended; doc · §3.4]`
**Why it matters:** the doc records that this exact regression already shipped once and was caught only by the cross-application conformance suite.

### H17. "The `⌘` and envelope buttons behave like the rest of the card"

**Wrong:** assume all three buttons push a screen.
**Correct:** `⌘` opens a **sheet** over Now; the envelope **resets** the stack to Inbox rather than pushing, so back does not return to Now. `[SRC: proto · ACT.access, click delegation]`
**Why it matters:** the envelope is the only navigation on the screen from which the player cannot return with back.

---

# I. WHAT THIS FEATURE DELIBERATELY DOES NOT DO

Each refusal is a hard requirement. **A refusal implemented as a feature is a defect.**

| # | Refusal | Reason | Evidence |
|---|---|---|---|
| I-1 | **Now never lets a level be typed, adjusted or asserted** | Invariant 5. A rating a person can edit means nothing, so matches stop being balanced | `[SRC: doc · §0.2, §16]` |
| I-2 | **Now never shows a court price to a seat holder** | Invariant 1. The unit of sale is a seat | `[SRC: doc · §0.2]` |
| I-3 | **Now never computes a fill probability** | Invariant 6. It reads `clubFill` and attributes it | `[SRC: doc · §0.2, §3.4]` |
| I-4 | **Now never shows a single refund figure for a committed match** | Invariant 3. The refund is whatever happens to the seat; *"Showing one number would be a promise the engine cannot make"* | `[SRC: doc · §4.2]` |
| I-5 | **A Rescue Seat is never publicly listed, and never appears in the Now feed** | *"targeted only, never publicly listed"*; *"there is no code path from the rescue engine to the public search"* | `[SRC: doc · §18 Glossary, §2.2]` |
| I-6 | **Now has no feed, no followers, no social content** | *"Not a social network. No feed, no followers, no content to farm."* The "feed" on Now is a ranked match list, not a social timeline | `[SRC: doc · §16]` |
| I-7 | **Now has no ranking ladder, leaderboard or position** | *"A rating exists to make matches balanced, not to be climbed."* | `[SRC: doc · §16]` |
| I-8 | **Now offers no general messaging.** The envelope goes to Inbox, which holds requests, match chat and club announcements — never stranger-to-stranger messaging | *"Not a chat app… there is no general messaging between strangers."* | `[SRC: doc · §16]` |
| I-9 | **No state on Now is presented without an explanation** | *"Not a system that hides its reasoning. Every state explains itself."* Every context carries 3–5 lines | `[SRC: doc · §16]` `[VERIFIED]` |
| I-10 | **Now caches nothing derived from time** | *"Nothing is cached, which is why no two screens can disagree."* | `[SRC: doc · §0.5]` |
| I-11 | **Now never invents supply.** An empty feed says so plainly | *"We do not invent players to make a city look busy."* | `[SRC: proto · V.home]` |
| I-12 | **Now never puts money in the wallet automatically** | *"No automatic rule may ever put money in the wallet — issuing credit is always deliberate."* The checkpoint credit shown on `cancelledCheckpoint` is a club-initiated act, not an automatic one | `[SRC: doc · §4.3]` |
| I-13 | **Now never charges anything.** No action on the screen moves money; the only money-adjacent affordances are navigational | `[DERIVED: no ACT reachable from Now calls `ledgerAdd` or `payFor`]` |
| I-14 | **Now never reveals another player's Player Score as a public number** | *"Player Score: applied, never displayed publicly."* `stateCard` shows no score; `matchCard` shows Match Fit, which is computed for the viewer | `[SRC: doc · §18 Glossary]` |
| I-15 | **A blocked player is never told they are blocked** | *"A blocked player never appears in a match with you, and is never told."* Any block filtering added per G4.2 must be silent | `[SRC: doc · §12]` |
| I-16 | **Now does not merge the club card and the wallet** | *"The wallet and the club card never merge."* The sports-card block is a card-entry counter, never a balance | `[SRC: doc · §4.3]` |
| I-17 | **Now does not let a player choose a court** | *"The exact court is assigned by us, never chosen — the price cannot change."* Cards show a **category**, and only `ready` names a physical court | `[SRC: proto · ST.protectedCourt, ST.ready]` |
| I-18 | **A club-sponsored guest can never fill a vacated seat** | *"that would let a club decide a refund. Only the leaver's own group can sponsor."* | `[SRC: doc · §4.2]` |
| I-19 | **Nothing on Now is held or charged without the player's own act** | *"A held seat neither fills the match nor holds a court. Only money does."* | `[SRC: doc · §6.2]` |
| I-20 | **Now does not surface intent declarations, and a declaration never becomes a booking by itself** | *"It is not a booking and never becomes one by itself."* | `[SRC: doc · §7.1]` |

---

# J. PRODUCTION REQUIREMENTS

## J1. Data the feature must persist — and must never persist

**Must persist (read by Now, written elsewhere or by the lifecycle):**

| Field | Owner | Why Now needs it |
|---|---|---|
| `seats[] {player, paid, at}` | Match | Fill count, glyph, `mySeat`, `filled`, `isFull` |
| `share`, `price`, `n` | Match | `payable`, every money line |
| `start`, `dur`, `created` | Match | Every deadline, the stale rule, `matchEnd` |
| `club`, `category`, `sport`, `fmt` | Match | Court line, glyph shape, club policy lookup |
| `courtId`, `protectedAt`, `holdKind`, `releasedAt`, `courtLocked` | Match | `courtHold`, `heldReleased`, `clubHeld` |
| `committedAt` | Match | The commit/`confirmedOnFill` distinction |
| `vacated`, `vacatedAt`, `transferring`, `rescueTaken`, `sponsoredGuest` | Match | The four recovery contexts |
| `formCancelled`, `checkpointCancelled`, `clubCancelled`, `weather`, `inventoryLost` | Match | The four cancelled contexts |
| `clubExtended`, `clubFill` | **Club**, published | `heldExtended` — read-only, never derived |
| `left` | Seat/player | Strip exclusion |
| `noShow`, `score`, `scoreBy`, `confirmed` | Match | The six post-play contexts |
| `softNotified`, `invNotified`, `clubNotified`, `rescueOpen` | Match | Notification idempotency |
| `window`, `joinCut`, `rebooking`, `maxHoldAge`, `probHold`, `card` | **Club**, published | Deadlines, the stale rule, the checkpoint branch, `payable` |

**Must never persist:**

- **Any resolved tag, tone, context key, court line, group line or line list.** These are pure functions of state and the clock. *"The card is a pure function of state — nothing is stored about how it should look."* `[SRC: doc · §2.1]`
- **Any Match Fit score.** It is viewer-relative and recomputed per render.
- **Any fill probability the app computed.** Invariant 6.
- **Any refund amount for an unresolved seat.** Invariant 3.
- **A player-authored level, anywhere.** Invariant 5.

## J2. Permissions and visibility

| Object | Who can see it | Who can act | Hidden from |
|---|---|---|---|
| A state card | Only the seat holder — the strip requires `mySeat` | The seat holder | Everyone else. Non-participants see the rewritten `Your share would be…` phrasing on the match screen, never on Now |
| The door code | The seat holder, from `start − 15 min` | — | The seat holder before that time (`••••`), and everyone else always |
| Another player's Player Score | Nobody, as a number, on Now | — | All viewers `[SRC: doc · §18]` |
| Another player's level | Not shown on Now at all (`playerRow` is not used here) | — | All viewers |
| The leaver's identity | Named on `replacement`, `protectedBack`, `formingBack`, `replacementTransfer` cards to the remaining players | — | — |
| The club's fill figure | Shown, attributed to the club, when the club published it and `probHold` is on | — | Shown as the plain ladder when not published |
| A blocked player's presence | Must be invisible **and** unannounced | — | Both parties `[SRC: doc · §12]` |

## J3. Notifications and messages this feature emits

All are produced inside `syncMatch`, i.e. as a side effect of resolving state. `[SRC: proto · syncMatch]` **In production these must move to a server-side job (H12).**

| Trigger | Audience (`to`) | Content rule | Suppression |
|---|---|---|---|
| A Rescue Seat opens (`rescueCore` becomes true) | `the standby pool` | Names the club, the half price and the full price, and the ten-minute window | Once per match — guarded by `m.rescueOpen` |
| A match is cancelled for never completing | `everyone` | States the T−2h timing, full refunds, court returned | Once — guarded by `wasForm` |
| A match is cancelled at the checkpoint | `the three who stayed` | States that no replacement was found and that club credit is already in the account | Once — guarded by `wasChk` |
| A soft hold is first taken | `everyone in the match` | Names the club, the category, the 12-hour rung, and that one more player makes it firmer | Once — guarded by `m.softNotified` |
| A held court goes back | `everyone in the match` | Names which rung lapsed, states nothing paid is affected, states the court returns on the next payment | Only when `releasedAt === S.now` and not club-cancelled — **not guarded by a boolean, so it can re-fire if a court is re-held and re-released** `[GAP]` |
| Inventory is lost | `everyone` | Names the category and club, states full refunds | Once — `m.invNotified` |
| A club or weather cancellation | `everyone` | States full refunds including anybody who had already left | Once — `m.clubNotified` |
| A new player joins | `the others` | Names the payer and the new fill count | Emitted by `joinMatch`, not by Now |
| The court becomes protected | `everyone` | States that a private booking can no longer take it | `joinMatch` |
| The match is full | `everyone` | States the free-cancellation deadline when uncommitted | `joinMatch` |
| Committed on the spot | `everyone` | States that the deadline had passed | `joinMatch` |

**Channel:** unspecified in both sources. `[GAP]` **Proposal:** the `to` field already names an audience; add a channel per audience honouring the player's channel preferences `[SRC: doc · §12]`, and never send a `the standby pool` notification to a match participant.

**Suppression rules that must hold:** no notification may fire for a match the recipient has no relationship to; no notification may fire twice for the same transition; and no notification may be produced by a read on the player's device.

## J4. Localisation, formatting and currency

| Requirement | Rule | Evidence |
|---|---|---|
| Currency | `{amount with two decimals, comma decimal separator} zł` — e.g. `38,00 zł`. Zero renders `0,00 zł`, never blank or "free" | `[SRC: proto · zl]` |
| Levels | Two decimals, comma separator, and a **Unicode minus** (U+2212) not a hyphen | `[SRC: proto · lvl]` |
| Time | 24-hour, zero-padded `HH:MM` | `[SRC: proto · hm]` |
| Relative days | `Today`, `Tomorrow`, `Yesterday`, else a three-letter day abbreviation | `[SRC: proto · when]` |
| Day names | Full names in the header eyebrow, abbreviations on cards | `[SRC: proto · dowl, dow]` |
| Week start | Monday, described in the source as the Polish convention | `[SRC: proto · SH.calendar]` |
| Distance | Minutes on cards (`14 min`), kilometres available on the club record | `[SRC: proto · matchCard, CLUBS]` |
| Language | All copy is English in the prototype; clubs publish a `languages` list | `[SRC: doc · §10.2]` `[GAP]` **Proposal:** every state line is a translatable string with named interpolations, never concatenation — the current implementation concatenates heavily and will not localise as written |
| Pluralisation | `1 thing needs you` / `2 things need you` is hand-built with ternaries | `[SRC: proto · V.you]` `[GAP]` **Proposal:** ICU plural rules; Polish has three plural forms and the ternary pattern cannot express them |

## J5. Compliance, consent, audit and data retention

| Obligation | Requirement | Evidence |
|---|---|---|
| Consent | An unanswered proposals question resolves to **opt-in false**; skipping is not consent | `[SRC: doc · §7.3]` |
| Consent | Nothing on Now may be held or charged without the player's own act | `[SRC: doc · §6.2, §7.3]` |
| Legal documents | Accepted **per version**; a new version asks again rather than assuming the old answer stands | `[SRC: doc · §10.1; proto · ACT.accleg records the version]` |
| Audit | Every money movement carries a reference (`PAY-…`, `REF-…`, `REV-…`, `FV/2026/08/118` for the VAT invoice) | `[SRC: proto · ledgerAdd, runScenario baseline ledger]` |
| Audit | A staff-assisted check-in scan records who performed it — *"the record is never silent"* | `[SRC: doc · §11.1]` |
| E-money | *"The wallet is stored value, which is e-money in several jurisdictions above a threshold. Caps, expiry and refundability need a legal answer per market."* | `[SRC: doc · §17.7]` — blocks release in affected markets |
| Retention | A match leaves Now 24 h after it ends; the source does not say what happens to the record | `[SRC: proto · KEEP_H]` `[GAP]` **Proposal:** match and ledger records retained for the statutory invoicing period; state-transition logs retained long enough to settle a refund dispute; notification bodies purged sooner as they contain other players' names |
| Privacy | Observed patterns read only one club's matches, *"by deliberate privacy choice"* | `[SRC: doc · §17.6]` |
| Data export | Offered under settings; must include the state history a refund outcome depended on | `[SRC: doc · §12]` `[DERIVED]` |

## J6. Performance and freshness

| Data | Requirement | Evidence |
|---|---|---|
| Everything time-derived — holds, deadlines, commitment, checkpoint, tags, court lines | **Recomputed on every read. Never cached.** | `[SRC: doc · §0.5]` |
| Club published policy (`window`, `joinCut`, `maxHoldAge`, `probHold`, `rebooking`, `card`) | May be cached; changes are rare. Must be versioned so a card can state which version it applied | `[SRC: doc · §10.2]` `[DERIVED]` |
| `clubExtended` / `clubFill` | Must be **real-time reads of published club state**. A stale extension shows a court held that the club has released — the failure Invariant 6 names as the worst in the system | `[SRC: doc · §0.2]` |
| Court assignment (`courtId`) | Real-time. It is the difference between a category and a court | `[DERIVED]` |
| Match Fit | Recomputed per render; viewer-relative; never stored | `[SRC: proto · matchFit]` |
| The strip | Must render before the feed. The player's own money is the reason they opened the app | `[SRC: doc · §2.1]` `[DERIVED]` |
| Re-render cadence while visible | Currently none | `[GAP]` **Proposal:** 30 s interval plus foreground trigger |
| Scroll preservation | Preserved when the view key is unchanged; the key is `[view, step, id, tab, findTab]` and **omits `S.sport`** | `[SRC: proto · render]` — see AC-84 |

## J7. Analytics — events worth emitting, and the property that makes each useful

| Event | The property that makes it useful |
|---|---|
| `now_viewed` | `strip_count`, `strip_tags[]`, `feed_count`, `sport_filter`, `has_alert` — the tag distribution is the health metric for the whole lifecycle |
| `now_state_card_impression` | `context_key` (not the tag — 35 contexts, 17 tags, and the contexts are what differ) |
| `now_state_card_opened` | `context_key` + `position_in_strip` — which states drive a tap tells you which cards fail to answer their own question |
| `now_feed_impression` | `match_fit_score` bucketed, and `rank` — the feed's whole claim is that ranking works |
| `now_feed_card_opened` | `match_fit_score`, `rank`, `payable`, `seats_left` — conversion by fit is the only way to validate the seven-term weighting |
| `now_feed_empty` | `sport_filter`, `candidate_count_before_fit_filter` — distinguishes "no supply" from "no rating in this sport" |
| `now_strip_empty` | `player_has_matches_in_other_sports` — directly measures the H15 false statement |
| `now_sport_filter_changed` | `from`, `to`, `strip_count_after` |
| `now_access_sheet_opened` | `minutes_to_start`, `code_live` — how often players open it before the code exists |
| `now_card_state_transition` | `from_context`, `to_context`, `trigger` (`clock` vs `payment` vs `club_action`) — the only way to see clock-driven transitions the player never witnessed |
| `court_hold_lapsed` | `rung` (`far`/`near`), `seats_paid`, `hours_to_play` — validates whether the ladder's bar is set right |
| `court_hold_stale` | `club_id`, `max_hold_age`, `age_hours` — per-club, since it is a club setting |
| `court_hold_extended` | `club_id`, `club_fill` — measures whether extension predicts filling, **without the app computing a model** |
| `checkpoint_resolved` | `outcome` (`cancelled_incomplete` / `cancelled_checkpoint` / `continued_rescue_late`), `club_rebooking` |

## J8. Rollout

| Concern | Requirement |
|---|---|
| **Feature flag — the stale-hold rule** | `maxHoldAge` is per club and already `null` for three of nine. Ship it club-by-club by leaving `maxHoldAge` unset; no code flag needed. But the two hold-ladder scenarios it changes (AC-109, AC-110) must be re-baselined first, or the regression suite will pass on the wrong expectations |
| **Feature flag — demand-aware extension** | Gated by the club's `probHold` flag, which is already per club. Same approach |
| **Migration — `vacated` to an array** | Required by G2.3. Backfill single values to one-element arrays; every read site (four recovery contexts, `rescueCore`, `lifeOf`) must handle both during the window |
| **Migration — the six notification guard booleans** | If notifications move server-side (H12), these move with them. Records mid-flight must not re-notify |
| **Backward compatibility — the tag vocabulary** | The 17 tags are asserted identical to the club console by the conformance suite. **Adding, renaming or removing a tag is a cross-application change** and must be released to both apps together `[SRC: doc · §15]` |
| **Backward compatibility — the nine canonical states** | *"the nine canonical states in the same order"* is a conformance assertion. Order is part of the contract |
| **Backward compatibility — the shared engines** | `courtPriceOf`, `catPrice`, `shareOf`, `deadlines`, `courtHold`, `holdUntil`, `lifeOf`, `bookings`, `iComplete`, `pol` are shared with the club console. Any change is a two-app change `[SRC: doc · §13]` |
| **Rollout gate** | The 37 Now scenarios in F8 must pass, and the 40 cross-application assertions must remain at zero disagreements, before Now ships |
| **Known limitation to disclose** | *"The two prototypes do not share a backend."* Consent requests and acceptances are simulated independently; in production both are reads and writes against one state `[SRC: doc · §17.1]` |

---

# K. OPEN QUESTIONS

| # | Question | Why it blocks | Options | Recommendation | Who decides |
|---|---|---|---|---|---|
| K-1 | Does Now show requests and results needing the player, as doc §2.1 states, or not, as the prototype implements? | Changes the screen's composition and its claim to answer *"because something changed"* without a tap | (a) Add a needs-you block to Now, duplicating the You card · (b) Keep it on You and Inbox and correct the doc · (c) Show only a count on Now, linking to Inbox | **(a)** — the doc's stated purpose for Now is to answer "something changed" without a tap, and a badge on another tab does not do that. Reuse the You card's component | Product |
| K-2 | Does Now show a deadline strip, as doc §2.1 states? | Same; also affects card height and the strip's scroll behaviour | (a) Add `deadlineStrip` to the state card · (b) Keep it on the match screen and correct the doc | **(b)** — the state card already carries 3–5 explanatory lines; a strip would push the card past a glance. Correct the doc | Product + Design |
| K-3 | Should a 3-of-4 match read `Court held` or `Court protected`? | Decides whether `protectedCourt` and `protectedLate` are live states or dead code, and whether three scenario names are wrong | (a) Keep `heldSoft`; delete the unreachable contexts · (b) Route `why === 'near'` to `protectedCourt` and keep `heldSoft` for `far` · (c) Keep both and rename the scenarios | **(b)** — the doc, the scenario names and the ladder all treat the third payment as a step change ("a private booking can no longer take it"), and a distinct tag makes that visible. This is a **cross-application tag change** (J8) | Product + Club Console |
| K-4 | Should a match the player has left stay on Now until its refund resolves? | Invariant 3 makes the refund depend on an outcome the player can no longer watch | (a) Drop immediately (current) · (b) Keep until the seat resolves, in a distinct "resolving" presentation · (c) Keep for 24 h like a played match | **(b)** — the player's money is 100%, 50% or 0% depending on the search. Removing the only surface that tracks it is the largest information asymmetry on the screen | Product |
| K-5 | Should the Now feed apply the Find exclusions? | Cancelled and uncjoinable matches are currently valid feed cards (H4) | (a) Call `findPool()` · (b) Add the four safety exclusions only (cancelled, join cutoff, blocked players, `outsideMayAsk`) and keep Now unfiltered by user preferences · (c) Leave as is | **(b)** — Now should not inherit filters the player set on another screen, but must not offer a match that cannot be joined | Engineering + Product |
| K-6 | Can a club's slot discount change what an existing seat holder pays? | Directly tests Invariant 1's *"never re-priced"* | (a) Discount applies to seats sold after it · (b) Discount applies to all seats, refunding the difference · (c) Current behaviour: display changes, no refund | **(a)** — (c) shows a price the player did not pay, which is the worst of the three. If (b) is wanted commercially, it must be a deliberate, disclosed refund | Product + Finance |
| K-7 | What is the re-render cadence for Now while it is visible? | Every threshold on the card is a clock threshold and none of them currently fire on screen | (a) None (current) · (b) 30 s interval · (c) Scheduled render at the next threshold for the soonest card | **(c)**, falling back to (b) — the thresholds are computable, so waking exactly at them is cheaper and exact | Engineering |
| K-8 | Should the `⌘` Getting-in button be suppressed for cancelled matches? | A door code for a match that will not happen is a wrong instruction | (a) Suppress on `be === 'CANCELLED'` · (b) Show with an explanatory line · (c) Leave | **(a)** | Product |
| K-9 | Is the sports-card block per player or a constant? | It is currently a module constant with no club or sport scoping (AC-51) | (a) Read entries from the player record · (b) Read per club per day · (c) Remove from Now | **(b)** — entitlement is a club-and-day fact; a global counter will be wrong the first time a player visits two clubs in a day | Product |
| K-10 | Do the hold-ladder scenarios get re-baselined, or does the stale rule get scoped? | Two of six scenarios now resolve to states their descriptions contradict (AC-109, AC-110) | (a) Re-baseline the scenario descriptions to the stale behaviour · (b) Exempt matches younger than the ladder rung from the stale rule · (c) Give `holdFar` a fresher `created` so it demonstrates the rung it names | **(c) then (a)** — the scenario is meant to demonstrate the far rung, so fix the fixture, then correct the two descriptions that say "no court held" at two paid seats | Product + QA |
| K-11 | What is the notification channel per audience? | `to` names an audience but no channel exists; §12 promises channel preferences | (a) Push for participant-scoped, in-app only for pool-scoped · (b) All in-app · (c) Per-player preference for every kind | **(a)** with (c) layered on — a standby-pool notification is marketing to a non-participant and must never be a push by default | Product |
| K-12 | Is the offline door-code promise implemented before release? | `SH.access` states it as fact (AC-101) | (a) Implement caching · (b) Remove the sentence | **(a)** — the promise is load-bearing at exactly the moment signal fails | Engineering |
| K-13 | Does the doc's §3.3 context table get corrected to match the 35 implemented contexts? | A QA engineer testing from the doc will test for contexts that do not exist and miss three that do | (a) Correct the doc · (b) Rename the implementation to match | **(a)** — the implementation is the one the conformance suite asserts against | Product |
| K-14 | What is the DST rule for deadlines? | A commitment deadline that moves an hour is a refund dispute (G1.4) | (a) Fixed millisecond offsets (current) · (b) Club-local calendar arithmetic | **(b)** | Engineering |
| K-15 | Is the empty strip state sport-aware? | It currently makes a false statement about the player's own bookings (H15) | (a) Add *"…in {sport}. You have {n} in other sports"* · (b) Suppress the sport filter's effect on the strip · (c) Leave | **(a)** | Product + Design |

---

# SELF-CHECK

1. **Did I convert every relevant prototype scenario into acceptance criteria, individually?** Yes — all 37 scenarios that mount Now are enumerated individually as AC-109 to AC-146, and the 52 that do not are listed by name in AC-147 with the reason.
2. **Did I enumerate every branch of every relevant action?** Yes — `ACT.sport` (5 chip values plus the `S.durs` side effect), `ACT.tab` (5 tabs including the early-return `create` branch), `ACT.access` (live vs masked door code), the `data-go` handler's `inbox` special case versus its generic push, and the three distinct `data-go="match"` origins, at AC-77 to AC-102.
3. **Is every acceptance criterion independently testable, with no compound conditions?** Yes — each states one Given, one When and one Then; boundary criteria are split into separate ACs per side of the threshold (AC-149/150/151, AC-152/153, AC-154/155, AC-157/158, AC-161/162, AC-163/164/165).
4. **Did I document the refusals as hard requirements?** Yes — 20 refusals in section I, each with its source quotation and the note that implementing any of them as a feature is a defect.
5. **What did I mark GAP, and which gaps block implementation?** 28 gaps are marked. **Blocking:** the Now feed's missing exclusions (K-5/AC-68/AC-70 — it currently offers cancelled and unjoinable matches); the notification architecture (H12/J3 — notifications are produced by rendering, which cannot ship); simultaneous departures (G2.3 — `vacated` is a scalar); the server clock (G1.5); DST arithmetic (K-14); and the e-money legal answer (§17.7). **Non-blocking but must be scheduled:** loading/error/partial states (E1), the `inventoryLost` tone (AC-25), the cancelled-match access sheet (AC-46), hardcoded player names in five state lines (G5.5), the sports-card constant (K-9), the localisation string architecture (J4), and re-render cadence (K-7).
