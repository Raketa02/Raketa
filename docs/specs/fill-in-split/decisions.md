# Fill in / You’re in split — decision log

- **Date:** 2026-11-23
- **Source:** the brief given in the grilling session (there is no separate requirements document) and the 3 mocks in this folder.
- **Status:** every branch settled in a grilling session (Q1–Q12, with Q2b and Q3b). This file is the input for `to-spec` / `to-tickets`. Nothing has been written to the repo yet (§13).
- **Ground rules:**
  - **The split is the scope.** The two lists in today's Fill in tab become two tabs. The cards are drawn exactly as they are today.
  - **The mocks lead on design**, except where the session overrode them. Each override is recorded as a named exception (§9).
  - **Data in the mocks is only data.** It is never hardcoded and decides nothing. That covers the names, times, clubs, prices, badge numbers, and the rescue button's text *“I’m in · 27 zł”* (Q9).
  - **A badge is a nudge, not a ledger** (Q12, in the user's words: *"The badges are there just to inform that something new had happened to make the user engage with the tab"*):
    - A badge never costs an extra request.
    - It never holds back a tab switch or a navigation.
    - It never adds machinery for the sake of being exact.
    - Wherever being exact would cost one of those, the simpler rule wins. This applies to every badge decision below and to anything `to-spec` meets that this log does not settle.

---

## 1. What changes, in one paragraph

A group's page today has three tabs: **Games · Fill in · Friends**. Fill in draws two stacked sections: *Seats to fill* (rescues) and *You’re In* (the reader's own live yeses). From now on there are four tabs: **Games · Fill in · You’re in · Friends**.
- **Fill in** draws only the rescues.
- **You’re in** draws only the live yeses, and it is now where **+ Post a game** floats.
- Neither tab has a section heading.

The tab badges change meaning. Today a badge says *how many there are*. Now it says *how many you haven't seen*. It clears once you look at the tab and comes back only when something new arrives. The phone remembers what you've seen across restarts.

The Games badge needs one additive field from the server. Apart from that, the change is entirely in the player app.

---

## 2. What the investigation found

**The page today** (`frontend_player/src/features/groups/components/GroupScreen.tsx`)
- `GROUP_TABS = ['games', 'fillIn', 'friends']` (`groups/domain/groupPage.ts:22`). It opens on Games (`OPENING_TAB`), and which tab it was on is never kept (ADR-0188 §5).
- The tab is kept in `groupTab.store` while the page is up, so *Post a game* can turn the page from over it.
- Fill in draws `FillInBoard` (`proposals/components/FillInBoard.tsx`), which makes two reads:
  - *Seats to fill* is `GET /pools/{id}/fill-in?sport`, per group and sport. Its rows leave at their deadline (`standingSeats`).
  - *You’re In* is `GET /players/me/live-yeses`. It covers all your groups and takes no parameters, and the phone filters it by `yesesIn(yeses, groupId, sport)`. Each row also reads its own game for the squares.
- Each section is drawn only when it has rows. The group's starting card (`FillInTab`, *No games yet* / *No games yet — it’s just you* + *Post the first game… Or send the link…*) is drawn only once **both** reads say there is nothing. Each section has its own offline note and retry.
- **+ Post a game** floats over the page's corner only while the tab is `fillIn` (`GroupScreen.tsx:288-292`). It floats over the level door too.

**The tab name never leaves the phone.**
- No push payload, notice or link carries a tab name. Push keys are `notice_id, kind, opens, game_id, pool_id, sport, game_kind, player_id`.
- A rescue notice pushes the rescue's details directly, and a deck notice forces Games.
- Outside links never reach an app screen (`links/components/redirectSystemPath.ts`).
- So `'fillIn'` reaches the page in three ways only: the app's own route params (`groupRouteParams.ts`, `z.enum(GROUP_TABS)`), the onboarding pass's return (`onboardingPass.ts` `fromAGroup`), and `PostAGamePage.tsx:52-54`.

**Post a game today**
- `PostAGamePage` calls `show(groupId, 'fillIn')` as soon as it opens, from either door: Fill in's button, or Games' *Nothing picked right now*.
- Every way back (a post, joining from its sheet, or the back chevron) lands on Fill in, where the new post shows under *You’re In · 1* (`postAGame.test.tsx:1072-1116`).
- Its back control says *Back to Fill in* (`postingCopy.ts:19`).
- A rating pass begun from it returns to Fill in.

**Badges today**
- `Segment.tsx:164` draws `CornerBadge` whenever the count is above 0, **selected or not**. The mocks draw it on the selected tab too. **Nothing on the group page clears a badge on a visit.**
  - Home's *Needs your answer* badge does clear. It uses a server-side "seen" watermark (#819, `proposalsApi.ts:194`), which is a different mechanism.
- **Fill in** shows the server's `FillInResponse.badge`, from the fill-in read (`useFillInBadge`). It can differ from the rows drawn, which drop at their deadline on the read's clock.
- **Games** shows the server's `GroupDeckResponse.games_badge` (`useGamesBadge`): *cards where somebody is already In with the reader, **across the segments***.
  - The server counts both kinds (`backend/app/modules/proposals/application/group_deck.py:327`).
  - The deck read carries `cards` **only for the kind the switch is on**. So the phone does not have the ids of the other kind's counted cards (Q12).
- **Fill in and live yeses each bring every row they count**, so the phone can tell which of their rows are unseen.
- A You’re in badge costs no new endpoint. It reads the same cached live-yeses read that You › Payments and the board use.

**The segment** (`shared/ui/Segment.tsx`)
- One row of `flex: 1` options, so all tabs get the same width.
- Labels are `numberOfLines={1}`, with no scrolling. The badge sits outside the layout.
- Design-system §6.3 specifies it *"for a two- or three-way view switch"*. Four options exist once already (Post a game's WHO in doubles), but never with badges.

**The phone's memory** (`shared/lib/preferences/phonePreferences.ts`, ADR-0188)
- Values are kept per account and cleared at sign-out.
- ADR-0188 §5: *"Adding a fourth value is a new record, not an edit to this one's table."* ADR-0200 §8 was such a record.

**Copy** — the curly apostrophe (U+2019) everywhere. The current strings:

| Where | String |
|---|---|
| Tab label | `'Fill in'` |
| Section headings | `'Seats to fill · N'`, `'You’re In · N'` (`fillInCopy.ts`, `fillInPresentation.ts`) |
| Spoken tab names | *Games, 4 with somebody In*, *Fill in, 1 seat to fill* (`groupsPresentation.ts:160-167`) |
| Spinner | *Reading Fill in* |
| Post a game's limit | *You already have 2 posts live — withdraw one in You’re In to post again.* (`postingCopy.ts:126`) |

---

## 3. The tab bar (Q6, Q8)

- **Four tabs: Games · Fill in · You’re in · Friends**, in that order. The page still opens on Games, and which tab it was on is still not kept.
- `GROUP_TABS` gains `'youreIn'`, after `'fillIn'`.
  - The route-param schema, the onboarding pass's origin and `groupTab.store` all accept it.
  - A tab this build does not know is still dropped, as today.
- The label is ***You’re in***: lower-case *i*, like *Fill in*, with the curly apostrophe (Q6).
- Each tab keeps the page's behaviour:
  - the one pull-to-refresh, which re-reads everything as today;
  - the level door for a player rated in nothing;
  - the official group's *add a sport* card.
- A **four-way segment** is a named exception to design-system §6.3 (§9).
- **For the user to check on a phone:** four tabs with badges on a narrow screen and at large OS text sizes. The estimate is about 69 pt per tab at 320 pt width against about 55 pt for *You’re in*, but nobody has seen it drawn (§15).

## 4. Fill in — the rescues (Q1, Q3, Q3b, Q9)

- It draws **only** today's *Seats to fill* rows, unchanged:
  - the coral border;
  - title, subtitle (*fills by …* / *offered until the start*) and squares;
  - ***Pay 27 zł***, which stays as it is (Q9). The mock's *I’m in · 27 zł* is illustration;
  - tapping the upper block opens the rescue seen from outside, and holding a face opens the record;
  - soonest first, each row leaving at its deadline.
- **No section heading** (Q1).
- **Empty → the one-line note *No seats to fill right now*, always** (Q3b). It never draws the starting card, because the starting card tells you to post and the Post button no longer lives here.
- **No + Post a game** (Q4).
- Its read is its own: the spinner while the read is on its way, the offline note, and the refusal with its retry.

## 5. You’re in — your live yeses (Q1, Q3, Q3b, Q4)

- It draws **only** today's *You’re In* rows, unchanged:
  - the mint border;
  - title, subtitle (*book by …*) and squares;
  - **Withdraw**;
  - tapping opens the game still filling, and holding a face opens the record;
  - picks, challenges and posts, never a rescue (a taken rescue goes to Home, as today); soonest first.
- **No section heading** (Q1).
- **+ Post a game floats here, and only here** (Q4). This overrides mock 1, which draws it on Fill in. It floats over the level door here as it did on Fill in, and it is not drawn while an official group's *add a sport* card stands in the tab, as today.
- **Empty:**
  - **When both tabs are empty**, it draws the group's starting card (today's `FillInTab`, *No games yet* / *No games yet — it’s just you* with the link's doors). It does so only once both reads have said there is nothing, never as a first frame.
  - **When only this tab is empty**, it draws the one-line note ***You haven’t said yes to a game here yet***.
- Withdrawing the last row leaves the tab on that empty state, without navigating.
- Its read is its own (live yeses, then each row's game): the spinner, the offline note, and the refusal with its retry. The spinner reads *Reading You’re in*.

## 6. Badges — "new since you last looked" (Q2, Q2b, Q10, Q11, Q12)

### 6.1 What a badge counts
- **Games, Fill in and You’re in each count the rows on that tab that you haven't seen** (Q2b c, all three tabs).
  - Games counts the cards with somebody In with you.
  - Fill in counts the rescues.
  - You’re in counts your live yeses in this group and sport (Q2).
- A count of 0 draws nothing. The mark is the same coral `CornerBadge`.
- **Right after this ships, everything starts unseen**, so the badges show today's counts until each tab is visited.

### 6.2 What "seen" means (Q10)
- **Everything a tab counts is seen while that tab is the one on screen.**
- **The tab you're on never shows a badge.** A row that arrives while you're on it, from a pull or a re-read, is seen at once.
- "On screen" means the page is visible, not covered by a pushed screen or a sheet. This is how the session read it, matching Home's #819.
  - **Simplification allowed:** if tracking the cover turns out to be fiddly, it is enough to mark a tab's rows seen when you open the tab and again when you leave it (ground rule: a badge is a nudge).
- **A row is identified by its id:**
  - a rescue by its booking;
  - a yes by its game (proposal);
  - a Games card by the id it carries on the wire.
- A row that changes (someone joins, a new version is dealt, the deadline passes) does **not** become new again. Only a row you haven't had on screen counts.
- **Games is per kind.** The cards of the kind the switch is on are seen. The other kind's cards stay unseen until you switch to it. Opening Games marks the whole deck of that kind seen, not just the top card.

### 6.3 Where "seen" is remembered (Q11)
- **On the phone, per account, cleared at sign-out.** It survives a restart and Android killing the app, so a badge you cleared stays cleared.
- It is per phone: looking on one phone does not clear another.
- Only the ids still on a tab are kept, so it cannot grow without limit.
- It is a new value in the phone-preferences store, so it needs a new ADR record (§11).
- **It never holds the page up.** The saved ids are read once, without waiting, and written without waiting. Until they are read, a badge is simply not drawn yet. Like a count arriving, it moves nothing.

### 6.4 What each badge is computed from (Q12)
- **Fill in** — the fill-in read's rows that are still standing, minus the seen booking ids. The server's `badge` field stops being read. It stays on the wire for older app versions.
- **You’re in** — the live-yeses read, filtered by `yesesIn`, minus the seen proposal ids.
  - Today the live-yeses read starts only while Fill in is drawn. For the badge it now starts when the page opens, so the You’re in tab usually opens already read (§12, call 2).
- **Games** — a new additive field on the deck read, the ids of the cards with somebody In across the kinds the reader is shown, minus the seen ids (§8).
  - It rides on the read the page already makes, so it costs **no extra request** and keeps today's *across both kinds* meaning.
  - `games_badge` stops being read. It stays on the wire for older app versions.

### 6.5 Spoken names
- Each tab's spoken name says the count is new, for example *Fill in, 2 new seats to fill*. The exact words for each of the three tabs are for `to-spec`.

## 7. Post a game (Q4, Q5, Q7)

- **It opens from two doors:**
  - You’re in's floating **+ Post a game**;
  - Games' *Nothing picked right now* card.
- **It no longer turns the page as it opens.** `PostAGamePage`'s `show(groupId, 'fillIn')` goes.
- **A successful post lands on You’re in**, from either door, so you see your new game. The *Posted — N of your best fits have it.* toast is unchanged.
  - The same goes for joining a post from its slot sheet.
  - Joining a rescue from the sheet goes to *It's a game!* and Home as today, and leaves the page on You’re in.
- **Backing out** (chevron, hardware back or swipe) returns to the tab it was opened from: You’re in or Games.
- **The back label names that tab:** *Back to You’re in* / *Back to Games*. This replaces *Back to Fill in*.
- **A rating pass begun from Post a game** (its level door or *add a sport* card) returns to **You’re in**. Today it returns to Fill in.
- The limit line becomes *You already have 2 posts live — withdraw one in You’re in to post again.*

## 8. Backend — one additive field (Q12 c)

- **`GroupDeckResponse` gains the ids of the cards with somebody In with the reader, across the kinds the reader is shown.** The name is for `to-spec`, for example `in_card_ids`.
  - It holds exactly the cards `games_badge` counts today (`group_deck.py:327`), which the server already builds.
  - It is additive, so older app versions ignore it. `games_badge` stays.
- `backend/openapi.player.json` is regenerated, and the player app's `src/generated/` with it (`make gen-api`; the backend's `api-contract-change` skill). The contract-drift check covers the rest.
- **Nothing else changes on the server.** Fill in and live yeses already carry their ids. Nothing new is stored, and there are no new endpoints.

## 9. Named exceptions — the mocks, the spec and the design system

1. **+ Post a game on You’re in, not Fill in** (Q4). This overrides mock 1 and the-screens A3 (*"floats bottom-right, always"* on Fill in).
2. **No badge on the selected tab** (Q2b, Q10). This overrides mocks 1 and 2, which draw *Fill in 2* and *You’re in 3* on the selected tab.
3. **A four-way segment** with badges. Design-system §6.3 says *"two- or three-way"*. Record it as a Part 16 row.
4. **The badge's meaning becomes "new since you last looked"**, where it was "how many are waiting" (`Segment.tsx` module note, `CornerBadge.tsx`, `theme.ts:833-834`, the design-system Part 16 row at about `:6189`).
   - The coral-badge bullet in `frontend_player/.claude/rules/design-system.md` lists the group-page tabs it counts. It gains You’re in.
   - Its count is the reader's own yeses, which is a status more than something waiting on them. It is an exception because the mock draws it.
5. **No section headings.** The design system's §7.27 drawing (*SEATS TO FILL · 1 / YOU'RE IN · 1*, *"Fill in draws two rows and nothing else new"*) is redrawn as two tabs.

## 10. Domain language (Q6)

- **One spelling: *You’re in*** (lower-case *i*, curly apostrophe). It applies to the tab, the copy and every document. It replaces *You’re In*.
- `CONTEXT.md` today says: *"**Fill in** — the group's rescue board (**Seats to fill**) plus **You're In**, your own yeses that have not filled."* (`:1788-1789`). It becomes two entries:
  - **Fill in** — the group's rescue board: the rescues you fit and are free for.
  - **You’re in** — your own live yeses in that group and sport that have not filled, and the tab *Post a game* floats over.
  - *Rescue* (`:1777-1778`, *"Shown in **Fill in**"*) is unchanged. *Live yes* (`:2055-2057`) gains a pointer to the tab.
- **Hottest groups' *You’re in* chip is left alone** (`groups/components/HottestGroupTaps.tsx`). It means "you're a member", which is a phrase on another surface, not this term.
- *Seats to fill* stops being a heading anyone sees. Keep it only where the specs need a name for the rescue list, or drop it in favour of *Fill in*. That is for `to-spec`.

## 11. ADRs (Q8, Q11 — with a correction)

- **The split itself gets no ADR** (Q8). It changes how the screen is laid out, not a decision about the system. The specs, glossary, feature docs and design system are amended (§14).
- **ADR-0189** gets a one-line note at *"Fill in lists your own yeses on them, under You're In"* (`:119-120`), pointing at the You’re in tab.
- **Correction, made while writing this log:** the session agreed (Q11) that remembering "seen" on the phone *amends* ADR-0188. But ADR-0188 §5 says *"Adding a fourth value is a new record, not an edit to this one's table."* ADR-0200 §8 was exactly such a record.
  - So the phone memory needs a **short new ADR** (next free number, 0208): *the phone remembers which rows of a group page's tabs a player has seen*.
    - It is per account and cleared at sign-out.
    - It keeps only ids still on a tab.
    - A stale or unreadable value means "nothing seen", never an error (ADR-0188 §4).
    - It amends ADR-0188 §2 and §5, as ADR-0200 §8 did. §5's *"which tab a group page was on isn't kept"* stays true: this remembers rows, not the tab.
  - The new ADR adds no code. It is the record the repo's own rule asks for. If the user would rather avoid it, the fallback is to keep "seen" in memory while the app runs (Q11 b), and accept that badges come back after Android kills the app.

## 12. Calls made without asking (flagged to the user)

1. **The new ADR for phone memory** (§11), per ADR-0188 §5.
2. **The live-yeses read now starts when the page opens**, not when the tab is drawn, because the You’re in badge needs it.
   - It is the same read the tab needs anyway, fetched earlier and in parallel. It never delays anything, and it makes opening You’re in instant.
   - Under the nudge rule this is not an extra request. If the user disagrees, the badge could instead show only once that read is already cached.
3. **Spoken names gain *new*** (§6.5), worded by `to-spec`.
4. **Components:** `FillInBoard` splits into one board per tab in `proposals`. The starting card (`FillInTab` in `groups`) is handed to the You’re in board as `empty` is today, and is renamed if `to-spec` wants a better name.
5. **Seen ids for Games are kept per kind**, so a kind switch marks that kind's cards seen.

## 13. Delivery

- **This session wrote only this file.** Nothing was written to the repo, and no issue was opened.
- The spec and the tickets come from `to-spec` / `to-tickets`, and the build from `implement`.
- A natural cut for `to-tickets`, offered and not decided:
  1. root docs: this log and the mocks into `docs/specs/`, the new ADR, `CONTEXT.md` and the spec amendments;
  2. backend: the deck's additive ids field and the regenerated contract;
  3. player: the split, the four tabs and Post a game's landing;
  4. player: unseen badges and the phone memory (needs 2).
- The repo is on `feat/RKTA-10_for_fun_refactor`, the For-fun branch. This work gets its own branch.

## 14. Docs to amend

- `CONTEXT.md` — *Fill in* split into *Fill in* and *You’re in*; *Live yes* gets a pointer; also `:28`, `:1366`, `:1804-1805` (*"it is in You're In as well"*).
- `docs/specs/games-and-fill-in/the-screens.md`:
  - A3 (`:241-272`) becomes two sections, Fill in and You’re in, with no headings, the FAB on You’re in, the empty states and the badges;
  - the tab lists at `:30` and `:55-57`, and *"Fill in badge — the number of Seats to fill rows"*;
  - *"Fill in › You're In"* at `:216` and `:437`, *Back chevron → Fill in* at `:372`, and `:572`, `:884`, `:990`, `:1015-1017`.
- `docs/specs/games-and-fill-in/the-mechanics.md`:
  - §1 point 7 (`:49-50`), and `:119`, `:128-130` (*"Fill in has two sections… The Post a game button floats over it"*);
  - §10 (`:677-716`), which becomes §10.1 Fill in and §10.2 You’re in as tabs;
  - `:398`, `:418`, `:610`, `:661`, and the decision rows Q34 (`:2223`), Q38 (`:2227`), Q76 (`:2264`).
- `docs/adr/0189-…` — the note (§11). **New ADR 0208** (§11). `docs/adr/README.md` index.
- `frontend_player/docs/features/groups.md`:
  - `:560-576` (badges, *Fill in is proposals' board*, *The tab bar counts Fill in*), `:578-587` (the pull);
  - `:592-598` (Post a game turns the page to Fill in);
  - `:181`, `:306`, `:324`, `:644-647`.
- `frontend_player/docs/features/proposals.md`:
  - `:487-511` (*The Fill in tab is FillInBoard*), `:711-713`;
  - `:731` (*Joining from the sheet leaves for Fill in*);
  - `:141`, `:917`, `:931`.
- `frontend_player/docs/features/onboarding.md` `:179`, `:187`, `:213-215`, `:227` (a pass begun from Post a game returns to You’re in). `frontend_player/docs/features/README.md` `:40`, `:75`.
- `frontend_player/docs/design-system.md`:
  - §6.3 (`:1345-1349`, four-way, a group page's four tabs);
  - `:154-158` (the coral and mint rows are now on two tabs);
  - §7.21 (`:3685`, *"Games · Fill in · Friends · no counts"*, already out of date; `:3691`, the FAB on Fill in);
  - §7.27 (`:4029-4065`);
  - Part 16 rows `:6189`, `:6200`, `:6236`, and the new rows for §9's exceptions.
- `frontend_player/.claude/rules/design-system.md` — the coral-badge bullet (§9.4).
- Code comments that describe the old tab: `GroupScreen.tsx` module note, `FillInBoard.tsx`, `FillInTab.tsx`, `PostAGamePage.tsx`, `groupTab.store.ts:5-9`, `Segment.tsx`, `CornerBadge.tsx`, `theme.ts:833-834`, `shared/lib/preferences/phonePreferences.ts` (the new value).
- Backend descriptions: `FillInResponse.badge` and `seats_to_fill` (`openapi.player.json:12049-12060`), and the deck's new field.

## 15. Tests the change reaches (from the investigation)

- **Group page:**
  - `groups/components/groupFillIn.test.tsx` — headings, sections drawn only with rows, the starting card with the FAB, one read failing, the pull, the row blocks, and `/^Fill in/` to open;
  - `groupPage.test.tsx:410-419` (*"Games · Fill in · Friends, with no counts"*) and `:594-631`;
  - `groupInfo.test.tsx:949-957`, `officialGroups.test.tsx:525-527`, `groupGamesDoor.test.tsx:681-686`;
  - `groups/schemas/groupRouteParams.test.ts:52-70` (`'youreIn'` parses).
- **Proposals:**
  - `proposals/components/fillInPresentation.test.ts:51-55` (the headings go);
  - `postAGame.test.tsx:237-247`, `:294-346` (where back lands), `:1072-1116` (a post lands on You’re in);
  - `blocks/components/blocks.test.tsx:278-350`, `:462-477`.
- **Onboarding:** `aPassFromAGroup.test.tsx:320-336`, `:440-456`; `theDoorWherePlayBegins.test.tsx:350-375`, `:470-510`; `anotherSportAndTheHomeCard.test.tsx:376-397`; `onboarding/domain/onboardingPass.test.ts:257-335`.
- **Test support:**
  - `test-support/groupDeck.ts:272-335`, `:386-388` (the deck stub gains the ids field);
  - `test-support/onboardingRouter.tsx:1408-1411` (`stubLiveYeses`, now read on every page open).
- **New:**
  - unseen-count rules as pure domain tests (seen set, pruning, per kind);
  - the phone-memory round trip and sign-out wipe;
  - the badge clearing on visit and returning for a new row;
  - backend tests for the deck's ids field.

## 16. Out of scope, or rejected

- **Rejected:**
  - Badges that stay as standing counts (Q2b a).
  - Hiding a badge only while its tab is selected (Q2b b).
  - Unseen on You’re in only (Q2b c, one tab).
  - Each tab drawing the starting card when only its own list is empty (Q3 a).
  - The starting card on both tabs (Q3b b).
  - + Post a game on Fill in or on both tabs (Q4).
  - Opening Post a game turning the page to You’re in (Q5 a).
  - A post from Games' door landing back on Games (Q7).
  - Remembering "seen" only while the page or the app is open (Q11 a, b), or on the server (Q11 d).
  - A Games badge for the switch's kind only (Q12 a).
  - Reading the other kind's deck (Q12 b).
  - A card counted as seen only once it has been on top of the deck (Q10).
  - A new ADR for the split itself (Q8).
- **Unchanged:** the card designs and every row interaction; Pay 27 zł; the order of the rows; the opening tab; the pull; notices and links; Home and the taken rescue; the Friends tab; Home's own *Needs your answer* badge.

## 17. For the user to check on a phone

- The four-tab bar with badges on a narrow phone and at a large OS text size.
- A badge clearing on a visit and staying cleared after the app is killed and reopened.
- *+ Post a game* on You’re in over the level door.

---

## Mock index

| # | File | Used in |
|---|---|---|
| 1 | `1_fill_in_tap.png` | §4 Fill in. **Overridden** on the FAB (§9.1) and the selected tab's badge (§9.2). The button text is illustration (Q9). |
| 2 | `2_youre_in_tap.png` | §5 You’re in. **Overridden** on the selected tab's badge (§9.2). The FAB is not drawn but floats here (Q4). |
| 3 | `2_tap_bar.png` | §3 the tab bar: Games · Fill in · You’re in · Friends, with the counts as illustration. |

## Question index

| Q | Decision | § |
|---|---|---|
| Q1 | No section headings on either tab | 4, 5 |
| Q2 | You’re in has a badge: its rows (live yeses in this group and sport) | 6.1 |
| Q2b | Badges are *unseen* counts on all three tabs (c). Today's badges do not clear; corrected in session | 6 |
| Q3 | Starting card only when both lists are empty; a one-line note otherwise | 5 |
| Q3b | Starting card on You’re in only; Fill in always draws *No seats to fill right now* | 4, 5 |
| Q4 | + Post a game on You’re in only; mock 1 is wrong on this | 5, 9 |
| Q5 | A post returns to You’re in | 7 |
| Q6 | *You’re in* everywhere; Hottest groups' chip left alone | 3, 10 |
| Q7 | A post lands on You’re in from either door; back-out to the origin tab, named on the back label; a pass returns to You’re in | 7 |
| Q8 | No ADR for the split; docs amended; a note on ADR-0189 (ADR for phone memory: §11 correction) | 11, 14 |
| Q9 | *Pay 27 zł* stays | 4 |
| Q10 | Seen = on screen while the tab is shown; ids; no badge on the selected tab; Games per kind, whole deck | 6.2 |
| Q11 | Seen kept on the phone, per account, cleared at sign-out | 6.3, 11 |
| Q12 | Games' unseen count from an additive ids field on the deck read (c); a badge is a nudge, so never an extra request or a wait | 6.4, 8 |
