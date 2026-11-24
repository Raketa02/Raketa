# Tabs refactor: Competitive / For fun moves into the tab — decision log

- **Date:** 2026-11-24
- **Source:** `Tabs_refactor.md` (the same text as `Tabs refactor.pdf`) and the 4 mocks in this folder.
- **Status:** every branch was settled in a grilling session (Q1–Q19, with Q19a and Q19b; Q15 and Q19b each asked twice). This file is the input for `to-spec` / `to-tickets`. Nothing has been written to the repo yet, and no issue has been opened (§11).
- **Ground rules:**
  - **The brief is the scope.** The second row of tabs (*Competitive / For fun*) goes, on Games and on Friends. That choice moves into a small menu inside the tab you are on. The card below gets the room.
  - **The mocks are illustrations. No decision rests on a mock.** In the user's words (Q15): *"do not take decisions based on the mock because it is just a mock. Any decision that you make should be based on real evidences."* Wherever a mock and this log differ, this log wins (§8).
  - **Data in the mocks is only data**: names, clubs, prices, counts, times, and the *69%* bar.
  - **Player app only.** No backend change, no contract change, and no regenerated types.

---

## 1. What changes, in one paragraph

Inside a group there are four tabs: **Games · Fill in · You’re in · Friends**. Today Games and Friends each draw a second row under the tab bar, the *Competitive / For fun* segment, on screen all the time.
- **The row goes.** On the Games or Friends tab you are on, a small **chevron** sits at the right edge of the tab.
- **Tapping the tab you are on opens a small white menu** hanging from it, with two lines: **Competitive** and **For fun**. The current one has a coral tick. On Games each line keeps today's count.
- **On Games, picking the other kind swaps the deck in place**: the cards slide out and the other kind's cards rise in. **On Friends**, it sets the kind of the game being built.
- **The deck card takes the freed height.** Its player tiles get a fixed, evidence-based shape instead of stretching, and the card adapts to small phones automatically.

---

## 2. What the investigation found

**The Games switch today** (`frontend_player/src/features/proposals/components/GamesDeck.tsx`)
- **The switch is drawn by the deck, not by the page**: the `above` block at `:537-543` is the switch, then the cap line, then the offline note. It is drawn **only once the deck read has segments**:
  - while the first read is on its way, the tab is a centred spinner (`:435-446`);
  - a failed read shows `ReadFailed`;
  - with no intent for the sport, `DeclarationInterstitial` takes the deck's place (`:448-463`);
  - in each of those states, no switch is drawn.
- **Both kinds' counts come from one read** (`switchSides`, `proposals/domain/deck.ts:195`). The label is `segmentLabel` → *Competitive · 7* (`deckPresentation.ts:64`).
- **The kind your intent doesn't want is a door** (ADR-0201 §2, Q127): `Segment`'s `door`, dimmed, with no number. A tap opens **`KindDoor`** over the deck area: *Either suits me / For fun / Keep competitive* (`KindDoor.tsx`). **This is the card the brief says must keep working.**
- **While an answer is on its way, or games are being found**, the switch is still (`GamesDeck.tsx:485-486`).
- **The kind is kept in `groups/store/gameIntent.store.ts`**: in memory, one value for the app, `'competitive'` by default, corrected to the intent's kind by `useGroupDeck` (`resolveKind`). Nothing is remembered across a cold start (ADR-0188 §5).
- **Each kind is its own read** (`proposalKeys.deck(groupId, sport, kind)`, `useGroupDeck.ts:67-86`). **There is no prefetch and no placeholder.** Switching to a kind not yet read drops the whole tab, switch included, to the centred spinner until the read lands.

**The Friends switch today** (`frontend_player/src/features/groups/components/FriendsTab.tsx:147-154`)
- A plain `Segment` above the court that sets **this game's kind only** (`friendsGame.store.ts`, ADR-0202, #757). It never moves the Games deck.
- **It has no door.** A Competitive-only player can build a For-fun game with friends.

**The tab bar today** (`GroupScreen.tsx:136-187`, `shared/ui/Segment.tsx`)
- Four equal segments (`flex: 1`).
- A coral `CornerBadge` on Games, Fill in and You’re in counts what you haven't seen. **The tab you are on draws no badge** (#849, #850, fill-in split override 2).
- `Segment` reports **every** press, including one on the segment already selected (`Segment.tsx:31-33`). So a second tap is free to mean "open the menu".
- The design system measured **69pt a segment on a 320pt phone**, against about 55pt for *You’re in* (`design-system.md:1407`).

**The overlays that exist**
- `shared/ui/Popover.tsx` (7.6) is an **explainer**: 250 wide, an arrow, a close control, and focus moved to its heading. It isn't a picker.
- `KindDoor` lies over the deck area as a sibling `View`, not on `ModalStage`.

**The deck card's height** (`GameCard.tsx`, `GameTiles.tsx`, `DeckStage.tsx`)
- The card fills the stage (`flex: 1`), and the three stacked cards are the stage's height (`DeckStage.tsx:51-57`, `:464-465`). So freed height reaches the card on its own.
- **On the deck, the player tiles are the only thing that stretches.** `fill` is `flex: 1, minHeight tileMin 54`, with **no aspect ratio**. The forecast or vibe row, the week grid and the court block keep fixed heights.
- **On a game's details, tiles are `aspectRatio 1.75`** (`detailsTile`, "the mock's width to height"). **No ADR or design-system rule argues for any deck tile shape.** All three values in `theme.ts:1223-1226` were "measured off mocks 2–10".

**Measured on the user's phone** (Samsung A32 5G, SM-A326B, read-only over adb: `wm size/density`, `dumpsys window`, one `uiautomator dump`)
- The screen is 720×1600 px at density 300 (1.875), so **384×853 dp**.
- Status bar 28.3 dp. The 3-button nav bar (48 dp) is outside the window (SDK 52 isn't edge to edge, `systemBars.android.ts:27-28`). Font scale 1.0.
- **A deck tile is 160.5 × 84.3 dp (1.90 : 1).** Ribbon 30, court block 71.5, a segment 28.8.
- A layout model built from the theme's real values reproduces these to within 0.2 dp, and it is used for the other phones below.

**The card's vertical budget** (from the theme, and checked against the A32)
- **Fixed parts**: ribbon 30 + body padding 24 + four 9pt gaps + hairline + forecast or vibe 22 (`SocialVibeRow` is 22 too) + week grid 81 + court block 71 = **264.4**.
- **Doubles tile height** = (card − 264.4 − 24) / 2, where 24 is the *vs* line and its gaps. **Singles** = card − 264.4.
- The cards behind the top one are transforms only and take no height.
- **Removing the row frees 40pt on iOS and 43.8pt on Android** (Android's segment is 34.8 tall, because `type.seg` has no lineHeight). That is about +20–22 per doubles tile.
- Other things that take height: the *N people are In* line (−12.5 a tile), the cap line (−12.5), a court line wrapping (−10), and OS text at 1.3× (about −25, estimated).

| Viewport (pt / dp) | Tile width | Doubles tile h today (w:h) | Without the row (w:h) | Singles h: today → without |
|---|---|---|---|---|
| 320×568 | 128.5 | −26, doesn't fit | −6, doesn't fit | −28 → 11.5 |
| 360×800 | 148.5 | 60.0 (2.47) | 81.9 (1.81) | 144 → 188 |
| **A32 384×853** | 160.5 | **84.5 (1.90; measured 84.3)** | 106.4 (1.51) | 193 → 237 |
| 390×844 | 163.5 | 81.3 (2.01) | 101.3 (1.61) | 187 → 227 |
| 412×915 | 174.5 | 117.5 (1.49) | 139.4 (1.25) | 259 → 303 |

Assumptions, all estimates except the A32: iPhone SE inset 20/0; 390×844 iPhone 47/34; a generic Android has a 24 status bar and a 48 3-button nav bar. Gesture navigation gives about +12 per doubles tile.

**Photos**
- Android crops uploads to **3:4** (`PROFILE_PHOTO_ASPECT`, `player_profile/domain/photoCollection.ts:73`, applied at `imagePicking.ts:121`). iOS gives a **square** (`imagePicking.ts:50-57`). The backend keeps the aspect.
- **A tile draws the photo with `cover`, centred, with no focal point** (`PlayerPhoto.tsx:163,176-187`). With no photo it draws `CourtPoster`, a square silhouette (`CourtPoster.tsx:97,186-189`).
- **The tile's foot** (name 20, gap 3, level line 17, padding 6+6) is **52pt**, and it covers the photo's lower part.
  - So the wider the tile, the less face shows: **32pt of clear picture** on the A32 today.
  - A rescue's **open seat** needs **61** (`GameTiles.tsx:304-314`), more than `tileMin` 54.
  - An unrated player's tile needs 32.
- **The tile's text scales with the OS font size with no cap.** Nothing in `GameTiles` or `GameCard` sets `maxFontSizeMultiplier`.

**Small phones and the type floor**
- **Expo 52 targets iOS 15.1** (no override in `app.config.ts`). The 1st-gen iPhone SE and the 7th-gen iPod touch (320×568) run iOS 15, so **the app installs on them**. The design system reasons about 320pt phones throughout.
- **At 320×568 the deck doesn't fit today.** The card gets 236pt (276 without the row) against the 396 it needs, so the tiles collapse over the forecast and the court block is clipped. This is inferred from the layout rules, not seen on a device.
- **The design system's type floor is 9.5pt** (#219 B4). The card's tags are already at it.
- **The design system's rule for text in a fixed box** (the ON COURT mark, and the tab bar in 10.2): it *"may neither be frozen nor grow without bound"*. A `maxFontSizeMultiplier` is **derived** from Archivo's real advance widths against the box (`design-system.md:3387`, `:3431`).

---

## 3. The tab bar (Q1, Q4, Q5, Q10, Q13)

- **The second row goes**, on Games (the deck's `Segment`) and on Friends (the court's `Segment`).
- **The chevron** (Feather, pointing down) stands at the right edge of the **selected** Games or Friends tab, **only where today's switch would be live** (Q1):
  - **Games**: there is a deck read with segments. It is **not** drawn while the intent question is up, while the first read loads or after it failed, on the *add a sport* card, or on the level door.
  - **Friends**: there is a court. It is not drawn on the *add a sport* card or the level door.
  - **While an answer is on its way or games are being found**, the chevron stays drawn so the bar doesn't jump, but a tap does nothing.
  - **While the other kind's deck loads after a pick, the chevron and the menu stay** (Q13). They are drawn from the last read of either kind for this group and sport, since both carry the same pair of counts. You can pick back mid-load.
- **Fill in and You’re in never draw a chevron.** When Games or Friends isn't selected, it draws no chevron, just a label and its badge as today.
- **The selected tab widens to fit its label and the chevron, and the other three share the rest** (Q5). The change of widths moves by a **layout transition**, never a width animated frame by frame (CLAUDE.md's Reanimated rule). The 320pt and large-text cases are checked on the phone (§15).
- **Badges are unchanged** (Q4): the coral corner badge, counting what you haven't seen, and none on the tab you are on. The mocks' pale pill beside the label, and the count on the selected tab, are illustration.
- **Nothing visible says which kind you are on while the menu is closed** (Q10). The cards say it (Social vibe on For fun, the forecast on Competitive), the menu says it, and the tab's spoken name carries it (§4.5).

## 4. The menu (Q2, Q3, Q6, Q7)

### 4.1 What it is
- **A new `shared/ui` primitive**, not 7.6's Popover, which explains a word and isn't a picker. `to-spec` names it.
- It is a **white card hanging from the selected tab's bottom edge**, with no arrow. **Aligned to the tab's left edge on Games and its right edge on Friends**, and kept inside the screen gutters.
- Its **width fits its content**. It takes **the float shadow** (it floats, 4.3), and **each line is at least 44pt tall** (6.5).
- **Two lines, Competitive then For fun.** The current one has a **coral filled circle with a white tick** in front. The other line leaves that space empty, so the words line up.

### 4.2 Games' lines
- Each live kind ends in **today's count**, the number `switchSides` gives, in muted mono. The logic is unchanged.
- **The door kind** (a single intent for the sport) is drawn as today's door (Q2): **dimmed, with no number and no tick, never disabled**. Tapping it **closes the menu and opens `KindDoor` over the deck area**, exactly as today. Its answer lands the kind and reads the group's decks again, with the *Finding…* state as today.

### 4.3 Friends' lines (Q3)
- **No counts, no door, no `KindDoor`.** Any kind can be picked.
- **Friends' kind stays its own** (`friendsGame.store`). Picking on Friends never moves Games, and the reverse holds too (ADR-0202, #757).

### 4.4 Motion (Q6)
- **The chevron turns 180°**: pointing up while the menu is open.
- **The menu fades in and drops a few points from the tab**, about 150ms, using transform and opacity only. **Instant under reduce motion.** It folds away the same way.

### 4.5 Spoken names (Q6, ADR-0198: the name is the whole job)
- The selected tab says **its name, then its kind**, e.g. *Games, Competitive*, with an expanded / collapsed state. The badge's words stay as today on the unselected tab.
- The lines say e.g. *Competitive, 5 games, selected* and *For fun, 1 game*. The door line keeps today's door words (`doorSpoken`). Friends' lines are the kind alone.
- The words go in copy modules, as every sentence does. `to-spec` words them.

### 4.6 Opening and closing (Q7, and the brief)

| Tap | Result |
|---|---|
| The tab you are on (Games or Friends, chevron drawn) | The menu opens. Nothing else moves. |
| The same tab again | The menu closes. Nothing changes. |
| Anywhere else on the page | **The menu closes, and that tap does nothing else.** A transparent catcher takes it: the deck's ✕ · i · 🎾, a card, the header and the sport pill all ignore that first tap. A swipe that begins there never moves a card. |
| Another of the four tabs | **You go there in one tap**, and the menu goes. |
| The kind you are already in | The menu closes. |
| The other kind | The menu folds away and the content changes (§5). |
| Android back | The menu closes. |
| A sport change, a pushed screen, a notice arriving | The menu closes. |
| The app's bottom bar (Home · Play · You) | Still works. The menu goes with the page. |

## 5. Picking the other kind (Q9, Q14, Q8 out)

### 5.1 Games: the deck swapped in place
- **Only the cards move.** The **✕ · i · 🎾 buttons stay** when both kinds have cards.
- **The old stack slides down and fades out** (about 200ms). **The new stack rises about 24pt into the same spot and fades in** (about 250ms). **Its top card is ready to swipe once it lands.**
- Transform and opacity only. **A crossfade under reduce motion.**
- **When the new kind deals nothing**, the starting card (*Nothing picked right now*, *Just you so far*, *3 of 4*) rises instead, and the buttons fade out.
- **You stay on Games.** Nothing scrolls and nothing navigates.

### 5.2 When the new kind isn't read yet (Q14)
- **Cached** (read in the last few minutes): the motion runs straight away. A cached read refreshes as today.
- **Not cached**: the old stack slides out, then **today's centred spinner** shows in the deck area, and the new stack rises when the read lands. The tab bar stays up, since it belongs to the page now, and so do the chevron and the menu (§3).
- **The read fails**: today's `ReadFailed` with its retry, in the deck area. The menu still works.
- **That spinner is the brief's "loading indicator is visible". Nothing new is built for loading.**

> **Amended 2026-11-24** (PRD [#867](https://github.com/Raketa02/Raketa/issues/867), the loading
> shimmer's Q26, [`docs/specs/loading-shimmer/`](../loading-shimmer/README.md) §10). **Not cached
> now shows the deck-card skeleton in the deck area, not the spinner.** The old stack slides out,
> one deck-card block stands in the deck area in the skeleton's tone with the shimmer's band
> crossing it, and the new stack rises into place when the read lands, exactly as §5.1 decides. Its
> rise replaces the shimmer's cross-fade there. *Nothing new is built for loading* no longer holds:
> the deck borrows the `Skeleton` primitive that Home, Rankings, See all and the group page are
> built on. **Unchanged:** a cached swap, a failed read (`ReadFailed` and its retry) and the menu,
> which still works throughout. Built by [#876](https://github.com/Raketa02/Raketa/issues/876).

### 5.3 Making the swap faster is out of scope (Q8)
Prefetching the other kind when the menu opens, or reading both kinds on every visit, was evaluated and **left out of this work** at the user's call.

### 5.4 Friends
The court being built becomes a Competitive or a For-fun game, which is today's `chooseKind`. With every seat filled, the friends card under the court asks again for that kind and redraws as it does today, with **no motion** (an assumption the user confirmed).

## 6. The deck card's room (Q11, Q15, Q16, Q18, Q19a, Q19b)

### 6.1 The card grows (Q11)
- The cap line (*Your 2 games this week are booked — showing next week*) and the offline note move up, **directly under the tab bar**, above the deck.
- **The card takes the freed height** through its existing `flex: 1`, which is +40pt on iOS and +43.8 on Android.

### 6.2 The tiles get a fixed shape (Q15, Q18), and nothing stretches
**User's rule (Q11):** *"all elements if their size changes should keep the aspect ratio and dimension for any screen size."* The deck's tiles stop stretching to fill. They are **sized by the card's width at a fixed width:height**, and **shrink at that ratio, never squashed**, where the height runs out.

**Doubles (padel, badminton): 1.75 : 1**, the details screen's ratio, so one tile component has **one shape on both screens** (Q15).

| Viewport | Doubles tile today | **At 1.75 : 1** |
|---|---|---|
| 360×800 | 148.5 × 60 | 143 × 82 (height-bound, 5pt narrower than its column) |
| **A32** | 160.5 × 84 | **160.5 × 92** |
| 390×844 | 163.5 × 81 | 163.5 × 93 |
| 412×915 | 174.5 × 118 | 174.5 × 100 (spare height goes to the gaps, §6.3) |

- **Why 1.75, from the evidence:**
  - the tiles grow slightly where the app is used (+8 on the user's A32, +12 on a 390 iPhone);
  - the tile fills its column on every phone but a 360 Android;
  - it matches the details screen.
- **Rejected:** 1.81 (the widest shape that fits from 360 up: +5 on the A32 and the least face shown), and 1.5 (the most face, but 11pt narrower than its column on a 390 iPhone, which reads as uneven).
- `theme.ts` carries the value, **with this evidence as its reason, not a mock**. The details screen is untouched (§13).

**Singles (tennis, squash): 3:4, the photo's own shape** (Q18). It is backed by `PROFILE_PHOTO_ASPECT` and the 3:4 photo tile (`theme.ts:991`). On Android the whole photo shows.

| Viewport | Singles tile today | **At 3:4** |
|---|---|---|
| 360×800 | 148.5 × 144 | 141 × 188 (height-bound) |
| **A32** | 160.5 × 193 | **160.5 × 214** |
| 390×844 | 163.5 × 187 | 163.5 × 218 |
| 412×915 | 174.5 × 259 | 174.5 × 233 |

Giving singles the doubles 1.75 was rejected: it would have turned them into ~92pt strips with most of the card empty.

### 6.3 Spare height is shared evenly (Q16)
Where the tiles reach their width-bound size and height is left over (a tall phone), it is **spread evenly between the card's blocks**:
- the tiles;
- the *vs* line;
- the forecast or Social vibe row;
- the week grid;
- the booked or court block.

**Nothing stretches**, and the card still fills the stage, which the three-card stack needs (`DeckStage`). Packing everything at the top, or growing the week grid's cells, was rejected.

### 6.4 The tile's text cap and its floor (Q19a)
- **The tile becomes a fixed box, so the design system's own rule applies** (§2, "Small phones and the type floor").
  - The tile's foot gets a **derived `maxFontSizeMultiplier`**. The foot is the name, the IN / FRIEND tag, the level line, *paid*, and the open seat's *You complete it* and its price line.
  - The cap is worked out from Archivo's real widths against the tile at its smallest drawn size, the tab bar's mechanism (10.2), with a fit test like `tabBarLabelCap.test.ts`.
- **The tile's floor is what its own content needs at that cap**, not the `tileMin` 54 constant, which is already less than an open seat's 61. A tile shrinking at its ratio stops at its floor.

### 6.5 Small phones adapt automatically (Q19b)
- **Measured against the room the phone gives, never tuned per device**, the boxes shrink **in proportion**:
  - the tiles (at their ratio);
  - the week grid's cells (keeping their shape);
  - the card's paddings and its gaps.
- **Text keeps its size**, capped by §6.4, and **never drops below the 9.5pt type floor**.
- **Only where even that can't fit does the deck scroll, as a last resort.** In practice that means a 568pt-tall phone, or very large text. When it scrolls:
  - the card keeps its minimum height;
  - the ✕ · i · 🎾 buttons sit below it, reached by a scroll;
  - the deck's existing scroller (*"a scroller with nothing to scroll"*, there for the pull) does it;
  - a drag across is still the card's and a drag down the scroller's, as `DeckStage` already arranges.
- At 320×568 the card needs about 345pt with the text kept at size (an estimate), against 276 available.
- **Rejected:**
  - shrinking the whole card, text included, with no floor: labels at 6.6pt, below #219 B4's floor;
  - dropping the week grid on short screens: it loses content;
  - declaring phones under 360 unsupported: a product decision, and it would leave the large-text case broken.

## 7. What stays exactly as it is

- **The kind's memory**: `gameIntent.store` in memory only, one value for the app, corrected by the intent (Q12). Remembering it on the phone would be a new ADR-0188 record, and it was left out.
- **`KindDoor`**: its words, its three answers and its *Finding…*. Only the way in moves, into the menu.
- **The first-time intent question**: no chevron while it is up.
- **Badges and "seen"** (ADR-0208, #849, #850): **opening the menu doesn't change what counts as seen** (an assumption the user confirmed). The deck still marks the whole of the kind on screen, and the other kind's cards stay unseen until the deck shows them.
- **A notice opening the deck at a card** still moves the kind to the card's kind and puts the page on Games.
- **Post a game's Kind step**, the details screen, Fill in, You’re in and the friends card.
- **The card's design and every answer on it**: the swipe, Undo, the fill, refusals.

## 8. Named exceptions: the mocks, the specs and the design system

1. **The mocks' counts** (a pale pill or a red number beside the label, and *Games 3* on the selected tab) are **not built** (Q4). Today's corner badge, and no badge on the selected tab, stay.
2. **Mock 3's tile shape (~1.6) is not used** (Q15). The ratios come from §2's evidence.
3. **The coral tick** (Q6). §1.2's coral list is "closed at six". The tick is read as the **active tab** meaning (the current kind is the active sub-tab), recorded in a **Part 16 row**, and the coral bullet in `frontend_player/.claude/rules/design-system.md` names it.
4. **The segment gains a selected state with a chevron that widens** (6.3, a Part 16 row). Until now a segment was `flex: 1`, and every segment the same width.
5. **A new overlay: the tab's menu** (Part 9 and 9.3's layer order, a Part 16 row). It is placed under 7.6 or beside it, with the reason 7.6 doesn't fit (explainer vs. picker).
6. **The deck tile's shape** (7.22, *"Two heights"*). The deck's tiles stop stretching: 1.75 for doubles and 3:4 for singles, a derived cap, a content-based floor, proportional shrinking and the scroll fallback (a Part 16 row).
7. **The deck no longer has a switch above it** (the-screens A1/A2, mock 9 of games-and-fill-in). The cap line sits directly under the tab bar.

## 9. ADRs (Q17)

- **No new ADR.** This changes how the screen is laid out, not a decision about the system.
- **ADR-0201 §2** (`:113-143`, *"The switch always shows both kinds, and the unwanted one is a door"*) gets a **dated note**: the switch is now the Games tab's menu, and the door is a line in it, still dimmed, numberless and never disabled, opening the same panel. Its rejected alternative at `:92` (*a line under the switch*) needs nothing.
- **The fill-in split's override 2** (`docs/specs/fill-in-split/README.md:72`; ADR-0208) gets a **dated note**: the tab on screen still draws no badge, and the chevron is its only mark.
- **ADR-0202** (`:41`, `:551`, *"the Friends tab's switch sets one game's kind"*) is still true. `to-spec` decides whether "switch" gets a one-line note saying "the Friends tab's menu".
- **ADR-0188 §5** is unchanged (Q12).

## 10. Calls made while writing this log (flagged to the user)

1. **The swap motion (§5.1) runs only on a pick from the menu.** When the kind moves on its own (a notice opening the deck at a card, or *Finding…* landing after a `KindDoor` answer), the new kind's deck is drawn directly, as today.
2. **The ✕ · i · 🎾 buttons fade in** when the swap goes from a kind that deals nothing (starting card) to one that deals cards. This mirrors §5.1's fade-out.
3. **The door line closes the menu before `KindDoor` opens**, so the panel never sits under an open menu.
4. **The glossary's two sentences about the switch** (`CONTEXT.md:506`, `:2167`) need rewording to say *the Games tab's menu*. Whether *the tab's menu* is named in `frontend_player/CONTEXT.md` as player-app vocabulary is `to-spec`'s call. It is UI vocabulary, not a domain term.
5. **A suggested spec folder:** `docs/specs/tab-menu/` (the brief, this log, and the mocks renamed with an index), as the earlier refactors did. `to-spec` decides.

## 11. Delivery (Q17)

- **This session wrote only this file.** Nothing was written to the repo, and no issue was opened.
- The spec and the tickets come from `to-spec` / `to-tickets`, and the build from `implement`.
- **Everything lands on the current branch, `feat/RKTA-10_for_fun_refactor`.** It already carries the four tabs and the unseen badges this work builds on.
- **Player app only**: no backend change, no contract change, no `make gen-api`.
- A natural cut for `to-tickets`, offered and not decided:
  1. root docs: the spec folder, the ADR-0201 note, the split README note, and `CONTEXT.md:506`/`:2167`;
  2. player: the menu primitive, plus the chevron and the widening selected segment;
  3. player: Games' row removed, the menu wired in (counts, the door → `KindDoor`), and the chevron's states (§3);
  4. player: Friends' row removed and its menu;
  5. player: the swap motion and its loading states (§5);
  6. player: the deck tile's shape, cap, floor, proportional shrinking and scroll fallback (§6). This is independent of 2–5;
  7. the human phone walk (§15).

## 12. Docs to amend

- `CONTEXT.md` — `:506` (*"the other kind's door on a group deck's switch"*) and `:2167` (*"The switch shows both kinds"*).
- `docs/adr/0201-…` — the dated note (§9). `docs/adr/0202-…` `:41`, `:551` if `to-spec` wants it.
- `docs/specs/fill-in-split/README.md` — override 2's note (§9).
- `docs/specs/games-and-fill-in/the-screens.md`:
  - `:40` (the Q127 ruling);
  - `:80-81` (seen per kind);
  - `:131-140` (**the switch under the tabs**, which becomes the menu);
  - `:158-160` (the question: no switch);
  - `:173-186` (the door's panel, *"a tap on the switch's dimmed kind"*);
  - `:787`.
- `docs/specs/games-and-fill-in/the-mechanics.md` — `:126-131` (*"split by the Competitive · N / For fun · N switch"*), `:153-154`, `:199` (*"a dimmed tab on the switch"*).
- `docs/specs/friends/the-screens.md` `:260` (*"The switch above the court"*), `:277`. `the-mechanics.md` `:377`, `:688`. `README.md` `:54` (friends 7's switch).
- `frontend_player/docs/features/groups.md` — `:208-210` (Friends' kind), `:557-564` (*"the deck fills the page between its switch and its three buttons"*), `:629`.
- `frontend_player/docs/features/proposals.md` — `:104` (*"The kind is the switch's"*), `:136`, `:222` (*"under the switch, above the deck"*), `:597-618`, `:742-747`.
- `frontend_player/docs/features/friends.md` `:106`.
- `frontend_player/docs/design-system.md`:
  - §5.2's 2026-11-05 amendment (`:1072-1073`, *"The Games switch's door"*);
  - **§6.3** (`:1356`; the door `:1382-1394`): the chevron and the widening selected segment;
  - §7.6 (`:2750`): why it isn't the menu;
  - **§7.21** (`:3720`): the group page;
  - **§7.22** (`:3821`, *Two heights*): the tile shapes, cap, floor and shrinking;
  - **Part 9** (`:4779`) and 9.3 (`:4897`): the new overlay and its layer;
  - 10.2 (`:5039`): the derived-cap mechanism, cited;
  - Part 13 (`:5828`);
  - **Part 16**: rows for §8.3–§8.6.
- `frontend_player/.claude/rules/design-system.md` — the coral bullet (the tick, §8.3), and *"Cards never cast a shadow"* if the menu's shadow needs naming there.
- `frontend_player/src/shared/ui/theme.ts`:
  - `gameCard.tileMin` and `gameCard.detailsTile` (`:1223-1226`);
  - the singles ratio;
  - the tile foot's cap;
  - the menu's tokens.
- **Code comments** that describe the old row:
  - `GroupScreen.tsx` module note (`:54-56`);
  - `GamesTab.tsx` (`:7-10`);
  - `GamesDeck.tsx` (*The switch is the page's*, *The kind the intent doesn't want is a door*, and `above` at `:537-543`);
  - `KindDoor.tsx` (`:18-22`, *"under the switch the player tapped"*);
  - `FriendsTab.tsx` (`:6-19`);
  - `gameIntent.store.ts`, `friendsGame.store.ts`;
  - `Segment.tsx` (the door note);
  - `GameTiles.tsx` (*Two heights*, `:52-56`).

## 13. Out of scope, or rejected

- **Out of scope:**
  - making the swap faster: a prefetch on menu open, or reading both kinds per visit (Q8);
  - remembering the kind on the phone (Q12);
  - **the details screen**: its tiles stay 1.75 for doubles *and singles*, so a singles tile is 3:4 on the deck and 1.75 on the details (an assumption the user confirmed);
  - the Friends court's size: Friends only loses its row;
  - the backend.
- **Rejected:**
  - a chevron always on Games and Friends (Q1 b);
  - the door line drawn at full strength or hidden (Q2 b, c);
  - the mock's inline counts, or a badge on the selected tab (Q4 b, c);
  - four equal widths (Q5 b);
  - the tick in `ink` (Q6 b), and reusing 7.6's Popover;
  - a tap elsewhere that closes **and** acts (Q7 b);
  - a sideways slide, or a plain crossfade (Q9);
  - the kind's word in the tab, or an empty state naming the kind (Q10 b, c);
  - growing particular elements beyond the tiles (Q11);
  - letting the chevron disappear during a load (Q13 b);
  - the ratios 1.6 (the mock's), 1.81 and 1.5 (Q15);
  - spare height packed at the top, or grown into the week grid (Q16 b, c);
  - singles at 1.75 (Q18 b);
  - leaving the cap and floor as they are (Q19 a);
  - shrinking text below the floor, dropping the week grid, or declaring phones under 360 unsupported (Q19b).

## 14. Tests the change reaches (from the investigation)

- **Suites that press a kind by name today**, and so must open the menu first:
  - `groups/components/groupGames.test.tsx`;
  - `groupGamesDoor.test.tsx` (the door, from the menu now);
  - `groupBadges.test.tsx` (seen per kind follows a kind move);
  - `friendsGame.test.tsx` (`:310-332` press Friends' *For fun*);
  - `proposals/components/competitiveDetails.test.tsx`;
  - `notifications/components/notifications.test.tsx` (a notice lands on a kind);
  - `shared/ui/Segment.test.tsx`.
- `groups/components/groupPage.test.tsx` — the tab bar.
- **New:**
  - the menu primitive: open, close, the catcher swallowing a tap, another tab passing through in one tap, Android back, spoken names and states;
  - the chevron's rules (§3) as pure domain rules where they can be;
  - the swap: cached, not cached (spinner) and failed, with the menu working during a load;
  - **the tile geometry as pure functions of the room and the viewport**: the ratio, width-bound vs height-bound, the floor, the proportional shrink and when the scroll takes over. The precedents are `rowSportBarFit.test.ts` and `tabBarLabelCap.test.ts`;
  - the derived cap's fit test (`tabBarLabelCap.test.ts`, `onCourtMarkFit.test.ts`).
- **A test-support helper** that opens a tab's menu and picks a kind, so the suites above say one thing.

## 15. For the user to check on a phone

- The chevron, and the selected tab widening, on the A32, at 320pt and at a large OS text size. That is four tabs with badges and a chevron.
- The menu's placement on Games (left) and Friends (right), its shadow, and its fold-out against the deck's dark card.
- The swap: cached (immediate) and not cached (spinner), and that the top card is swipeable once landed.
- **The tiles at 1.75 and 3:4 on the A32 and an iPhone**: faces visible, the foot readable, and the spare height spread evenly on a tall phone.
- The text cap at the largest OS text size, and the scroll fallback on the smallest phone or text size available.
- The door line opening `KindDoor`, and the Friends menu on a full court.

---

## Mock index

All four are **illustrations** (ground rules). What each was used for:

| # | File | Used for | Not built |
|---|---|---|---|
| 1 | `1.games_tab_with_chevron.png` | The chevron on the selected Games tab, and the selected tab wider than the rest (Q5) | The inline count, and the count on the selected tab (§8.1) |
| 2 | `2.friends_tab_with_chevron.png` | The chevron on the selected Friends tab | The inline counts (§8.1) |
| 3 | `3_games_tap_menu_open.png` | The menu hanging from Games, aligned left, Competitive then For fun, the tick, the counts, and the chevron up | *Games 3* on the selected tab, and the tile shape (§8.1, §8.2) |
| 4 | `4_friends_tap_menu_open.png` | The menu hanging from Friends, aligned right, with no counts | The inline counts on the other tabs |

## Question index

| Q | Decision | § |
|---|---|---|
| Q1 | Chevron only where today's switch would be live; drawn but inert while finding or answering | 3 |
| Q2 | The door kind: dimmed, no number, opens today's `KindDoor` | 4.2 |
| Q3 | Friends: no counts, no door; its kind stays separate from Games | 4.3, 5.4 |
| Q4 | Badges unchanged; the mocks' counts are illustration | 3, 8.1 |
| Q5 | The selected tab widens for the chevron, as a layout transition | 3 |
| Q6 | The menu: a new primitive, placement, the coral tick as *active tab*, motion, spoken names | 4 |
| Q7 | A tap elsewhere only closes; another tab goes there in one tap; back and page changes close it | 4.6 |
| Q8 | Making the swap faster (prefetch) is out of scope | 5.3 |
| Q9 | The swap's motion: cards only, down-and-out, then rise-in; crossfade under reduce motion | 5.1 |
| Q10 | Nothing visible names the kind while the menu is closed | 3 |
| Q11 | The card grows; tiles may grow slightly; anything resized keeps its shape on every screen | 6.1, 6.2 |
| Q12 | The kind stays in memory only (ADR-0188 §5) | 7 |
| Q13 | The chevron and the menu stay while the other kind loads | 3 |
| Q14 | Not cached: slide out, today's spinner, rise in; a failure shows `ReadFailed` | 5.2 |
| Q15 | Doubles tiles 1.75 : 1, from the measured evidence, not the mock (asked twice) | 6.2 |
| Q16 | Spare height is spread evenly between the card's blocks | 6.3 |
| Q17 | No new ADR; notes on ADR-0201 §2 and split override 2; design-system rows; this branch | 9, 11 |
| Q18 | Singles tiles 3:4, the photo's shape | 6.2 |
| Q19a | The tile foot's derived text cap, and a floor equal to its content | 6.4 |
| Q19b | Boxes shrink in proportion automatically, text never below 9.5pt, scroll as the last resort (asked twice) | 6.5 |
