# Home screen refactor — decision log

- **Date:** 2026-11-16
- **Source:** `home_screen_refactor.md` and the 15 mocks in this folder
- **Status:** every branch settled in a grilling session (Q1–Q46). This file is the input for `to-spec` / `to-tickets`; nothing has been written to the repo yet.
- **Ground rules (from the source document):**
  - The mocks lead on design and theming. Where an ADR, a spec or the design system disagrees, the docs are changed to match the mocks.
  - Data in the mocks is only data. It is never hardcoded and decides nothing.
  - "Your games" is out of scope. The one exception is a copy line (§4.3).
  - The brand is **Rakieta** in every UI string, as the mocks spell it. *(Updated 2026-11-27 for ADR-0211, which superseded ADR-0187 §8. At the grilling, the brand was the old spelling and a mock's was read as it.)*

---

## 1. What changes, in one paragraph

Home's request cards move off Home into a **"Needs your answer"** bottom sheet: **To confirm**, **Friends game**, **Friend requests** and **Asked for a level**. The sheet opens from a new **envelope** button in the header. The envelope is present only while something waits, and it carries a "new" badge kept on the server, the way the bell's is.

Below *Your games*, the five discovery rows become **FOR YOU**: five folding lines, each showing a title, a count pill (except Top 10) and a chevron. One line is open at a time. Opening a line unfolds today's tiles, with a footer link at the bottom.

*Groups heating up* gains a new full **Groups heating up page**.

The backend gains totals on four row reads, every sport level on a friend request, the envelope's server-side "seen", and the paged groups endpoint.

---

## 2. Header (Q5, Q15, Q16, Q4/Q29, Q39)

- **Order, right-aligned:** envelope, bell, trophy (mock 1). **The trophy takes the far-right corner**, which overturns ADR-0203 §5's "the bell keeps its corner".
- **Bell and trophy:** they move and nothing else about them changes.
- **When nothing waits:** the envelope's slot collapses and the bell and trophy stay pinned right.
- **Icon:** Feather `mail` in **ink**, as drawn.
  - The volt envelope on the round friend button already means "they asked you". The overlap is accepted, because both say "someone asked you", and it is recorded in the design system.
- **Badge:** the same `CountBadge` as the bell (tone `news`, ink, capped at "99+"). It counts **new** items since the sheet was last closed (§3.2).
- **Spoken label:** "Needs your answer", plus ", N new" while the badge shows.

## 3. "Needs your answer"

### 3.1 The term (Q43)
- **Glossary entry: Needs your answer.** It names the sheet and everything waiting in it (To confirm, Friends game, Friend requests, Asked for a level).
- **Avoid:** inbox, pending, requests (a Friend request is only one kind), envelope (that word names only the button).

### 3.2 The envelope's "new" (Q4, Q29, Q30, Q31, Q42)
- **Like the bell, and kept on the server.**
  - Closing the sheet records a **visit**. It is recorded as an event, the way the bell's `RecentNoticesOpened` is, and is idempotent and never moves back.
  - The visit carries a **watermark**: the newest item **shown in the sheet** at that moment, never the time of the tap (the bell's rule).
  - An item that arrived live while the sheet was open counts as seen. An item that arrives after the close counts as new.
- **The count travels on `GET /home`** as a new field (additive). Home already reads all four lists. This is the one deliberate difference from the bell, whose count rides on its own read; the ADR says why.
- **What counts as new:**
  - a new friend request (by sender);
  - a new friends game invitation (by booking);
  - a new payment to confirm (by payment);
  - a **new asker** joining an existing Asked-for-a-level card (one card per sport).
- **What does not count:** a change of state on an item already seen, for example a payment going from "Fix your card" to "Confirm".
- **Needed on the server:** an "arrived at" for every kind of item. Level askers expose none per asker today. Which context owns the visit record is left to the spec and the ADR.

### 3.3 The sheet (Q6, Q7, Q8, Q32)
- **Component:** the app's own `BottomSheet` (on `ModalStage`; no @gorhom), titled **"Needs your answer"**, with an ✕.
  - Its height fits its content, up to the existing 88% cap, and it scrolls inside beyond that.
  - It closes with the ✕, a swipe down, or a tap on the backdrop.
- **Sections, fixed order, each hidden while empty:**
  1. **TO CONFIRM · n**: a seat in a booked game is held for the player, so it has the shortest deadline.
  2. **FRIENDS GAME · n**
  3. **FRIEND REQUESTS · n**
  4. **ASKED FOR A LEVEL · n**
- **Every section is a sideways rail**, never a vertical list.
- **After an answer:**
  - The answered tile leaves its section, and an emptied section disappears.
  - When the last item is answered, the sheet closes itself and the envelope disappears.
  - A request arriving while the sheet is open appears in it at once.
- **Follow-ups that open something else** (Q24):
  - **Another sheet** (a player's record from a face, the payment confirm or setup sheet): "Needs your answer" closes, that sheet opens, and closing it brings "Needs your answer" back if anything still waits.
  - **A screen** (the questionnaire from "Get your padel level"): "Needs your answer" closes for good. (App rule: no navigation from inside a sheet.)
- **Opening the sheet moves the screen reader's focus to its title** (Q39).

### 3.4 Tiles inside the sheet (Q2, Q3, Q9, Q28, Q32, Q46)
- **All tiles in a rail are as tall as the tallest one, and their buttons sit at the bottom**, so buttons line up across tiles. Titles are clamped to 2 lines.
- **To confirm:** one tile per payment, replacing today's one card with stacked rows. Each tile shows:
  - the game ("Padel · Saturday 15:00");
  - the club and the share;
  - the deadline line in amber ("Confirm your payment by 14:40"), or the "nothing paid now" line when it is time to fix the card;
  - the **Confirm** or **Fix** button, as today.
- **Friends game:** one big tile at a time.
  - It uses the **paging rail**: full content width, snapping one at a time, with page dots once there are 2 or more games. This is the design system's existing paging rail, as on Your games.
  - Its content is unchanged (title, clock, faces, the when/where/sport line, "Not this time" and "Accept and pay {zł}"). The sizes follow mock 2.
- **Friend requests:**
  - The tile is wider, following mock 2 (about 83% of the content width, measured from the mock; this is a new width recorded in the design system).
  - It shows the face, the title "{nickname} wants to be your friend" and the **reliability tag** (`PlayerScoreTag`, ✦ 98).
  - It shows a **sport-levels line**: every sport the sender holds a published level in, drawn as elsewhere ("● Padel 3,40 · ● Tennis 2,10"), with mono numbers, at most 2 lines. The line is omitted when they hold none.
  - Buttons: "Not now" and "Accept".
  - **Removed:** the where-line ("With you in {group}") and every found-by line ("Invited you to Rakieta", "Found you in the padel ranking", …). The mock still draws the old subtitle; the document's text wins.
- **Asked for a level:**
  - Faces and the title only. The subtitle is removed, including "You're on question 5.".
  - Buttons are unchanged. The button still says "Carry on" for a questionnaire left halfway.

### 3.5 Links and notifications (Q25)
- These all open Home with "Needs your answer" already slid up:
  - the friend link (it used to land on "Home's FRIEND REQUESTS row at the top");
  - the `FRIENDS_GAME_INVITATION` notice;
  - anything else that pointed at one of the four cards.
- **The bell's rule changes:** a *level asked* notice is listed "while its card waits in Needs your answer" instead of "while its card is on Home".

### 3.6 What does not change
- **Home's tab badge** (`needing_you`: games needing you plus payments to confirm) keeps counting payments to confirm.
- **You › Payments** is unchanged.
- **If the To confirm read fails,** no envelope appears for it. The usual re-reads retry, and the notice and email already carry the deadline.

## 4. Home after the move

### 4.1 Order, top to bottom
1. Header (§2)
2. **Get your level**, only while the player is in a group and rated in nothing (§4.2)
3. **YOUR GAMES** (out of scope)
4. **FOR YOU** (§5)

### 4.2 Get your level (Q13)
- It stays on Home, above Your games, **whenever the player is rated in nothing, whether or not someone asked them**.
- ADR-0202's rule that an ask card is drawn *instead of* Get your level is **dropped**. The ask lives in the sheet.

### 4.3 The one copy change inside Your games (Q38)
- Today, a player in no group reads "Join a group to get games — the hottest ones are just below."
- It becomes "…— see Groups heating up, just below."

## 5. FOR YOU

### 5.1 The closed state (Q20, mocks 3–4)
- The section label is **FOR YOU** (an `eyebrow`: muted, uppercase).
- Each line is a white card holding a title on the left, a small grey **count pill** and a chevron (›) on the right. There are no faces and no subtitles.
- **The five lines and their new titles.** Only the words on screen change: glossary terms, code identifiers and endpoints keep their names, and `the-words.md` records the new titles.

| # | Line title | Glossary term (unchanged) | Count |
|---|---|---|---|
| 1 | **Groups heating up** | Hottest groups | yes |
| 2 | **Players at your level** | Same competitive level players | yes |
| 3 | **New in Rakieta** | New in Rakieta | yes |
| 4 | **Players with your vibe** | Same vibe players | yes |
| 5 | **Top 10** | Top 10 | none |

### 5.2 Counts (Q17, Q33, Q34, Q45)
- **The count is a real total, capped:** the server counts at most 100, and both the pill and the footer show "99+" beyond that.
- **Each total counts the pool the line draws from**, with that line's own exclusions (the reader, blocks either way, the "Show me to new people" switch, accounts that don't play):
  - **Groups heating up:** every group with at least 3 players, which is every group the new page lists.
  - **Players at your level:** the distinct players holding a level in any sport the reader plays, each counted once.
  - **New in Rakieta:** everyone who joined in the last 30 days.
  - **Players with your vibe:** everyone sharing at least one tag with the reader.
- **The number means "how many you could explore"**, not "how many are a good match". Counting good matches would mean scoring every candidate, which is the expensive path. In a busy city the two people lines will usually read "99+", and that is accepted.
- **"See all N ›"** on the three people lines carries the same number, even though their See all screens show one sport at a time.
- **Refresh:** "live" means the existing re-read schedule (return to Home after 30 s, focus, pull to refresh, push, write invalidations). There is no new polling.
- **Cost check** (an agent read the code; none of this is measured yet). Each row is its own request, so a cost lands only on that row.
  - **Groups heating up:** free. The read's `crowds` query already counts every group, so the total is that count with no new query.
  - **New in Rakieta:** one cheap COUNT on `ix_discovery_players_joined_at` over the 30-day range.
  - **Players with your vibe:** near free when folded into the existing full pass (`count(*) OVER ()`, or a materialized CTE). Never run it as a second pass.
  - **Players at your level:** an uncapped total would scan the whole pool (estimated 10–30 ms on a row that takes 67 ms at 50,000 players). Capped at 100, it is cheap, and usually free from the candidates the windows already read; otherwise it is one `EXISTS … LIMIT 101`.
  - **Never build a total** by draining the widening windows or the vibe batches, or by counting players at 70% or more.
- **Guards:**
  - A backend test per row asserting that the total adds **at most one statement** (zero for Groups heating up). The suite has no statement counter today, so a small `before_cursor_execute` fixture is needed.
  - A timing check of Home on the phone against #809's numbers before merging.

### 5.3 Opening and closing (Q10, Q12, Q38)
- **Opening:** tap anywhere on a line. **Only one line is open at a time**: tapping a second line closes the first and opens the second.
- **Closing:** tap the open line's **header**. Nothing else closes a line: taps on tiles, swipes inside, and the footer links and the Top 10 switcher all act as before.
- **Open style:** a **dark (ink) border**, a **soft shadow** (a new named exception in the design system, §8.3), and the chevron turned to point down (⌄). The count pill stays.
- **At app start, every line is closed.** While the app stays alive, Home remembers which line is open across tab switches (Home stays mounted under every tab since #809). Nothing is remembered across restarts.
- **Exception:** for a player in no group, *Groups heating up* starts open, because joining is their next step.

### 5.4 Animation (source document, Q11)
- **Opening:** the content unfolds downward from nothing, fading in as it grows, over about 250 ms, fast at first and settling at the end. The lines below slide down; they never jump.
- **Scroll:** if the opened content would be cut off at the bottom of the screen, the page scrolls just enough to bring it into view.
- **Closing:** the content folds back up and fades over a slightly shorter time, while the lines below slide up.
- **Switching lines:** the first folds, then the second unfolds.
- **Inside an open line,** tiles swipe sideways and **snap to tile edges**. This is new for these rails, which scroll freely today; `HomeRowRail` already has a `snap` option.
- **How it is built:** never animate `height` frame by frame (a player app rule: Reanimated 3.16 under the New Architecture freezes, then jumps). Change the size once and let a Reanimated layout transition (`layout=`) move the frames, as `RecordDetails` does; move only `transform` and `opacity` per frame.
- **Reduced motion:** lines open and close instantly, with no fold or fade, and the scroll into view still happens. Use the existing `useReducedMotion`.

### 5.5 Tiles in the open state (Q22, mocks 5–13)
- **Groups heating up** (mock 5.1):
  - **Kept:** the striped band, the HOTTEST or GROWING tag, the shield monogram and the name.
  - **Figures:** "N games this week" on the left and "N players" on the right.
  - **Footer:** the face stack and the chip (Join / Ask to join / Asked / You're in).
  - **Removed:** the heat bar, "+N this month" and the sport line (dots and names).
  - **The group's bottom sheet is unchanged** and keeps all its details.
- **Players at your level** (mock 7): unchanged, except that the footer text "{x} below you / {x} above you / Same level" is removed.
- **New in Rakieta, Players with your vibe, Top 10:** tiles unchanged.

### 5.6 Footers (source document, Q18, Q19, Q37)
- The "See all" links move from the heading to the **bottom of the open content, on the right**:
  - **Groups heating up:** "All groups ›", as drawn. It opens the new page (§6).
  - **The three people lines:** "See all N ›". It opens the existing See all screen.
  - **Top 10:** "Open the rankings ›", replacing "Rankings ›". It goes where it goes today.
- **The Top 10 footer also holds the sport switcher, on the left:** "Padel ›". The chevron points the way it opens. The switcher now **slides open to the right**, with the same animation as today.
- **The closed Top 10 line shows neither** the switcher nor a count.

### 5.7 Empty, loading, failed (Q21)
- **A line appears only once its read has returned something.** While a line is loading, empty or failed, it is hidden, as rows are today.
- **If all five lines are hidden,** the FOR YOU label is hidden too.
- **A line that empties while open** (for example, the player joined the last group) closes and disappears.
- **Top 10** keeps "Nobody ranked in {sport} yet" inside the open line, and is hidden only when `anyone_listed` is false.

### 5.8 What a closed line does in the background (Q23)
- **Every line still loads its data when Home opens**, because the count and the hidden-when-empty rule need it.
- **A line's tiles are drawn only while it is open,** which helps Home's speed.
- **A tile counts as on screen only while its line is open.** The existing rule already says that opening Home without reaching a row counts nothing.

### 5.9 Accessibility (Q39)
- **Each line is a button** that announces its title, its count and whether it is open, for example "Players at your level, 99 plus, collapsed" (`accessibilityState.expanded`).
- **Each footer link is its own button.**
- **Touch targets are 44 pt** and every pressable has an explicit pressed state, as the design system requires.

## 6. The Groups heating up page (Q18, Q35, Q36)
- **New screen, title "Groups heating up"**, opened from "All groups ›".
- **Which groups:** every group with at least 3 players (the row's own rule), in the row's order (HOTTEST, then GROWING, then the rest by heat; ties go to more games this week, then the group id). **Groups the player is in are included**, marked "You're in".
- **Paging:** 20 per page by cursor. **No sport filter** in this version.
- **Layout:** follows the people See all screens (title and a vertical list loaded page by page). Each tile is **the same simplified group tile as the line uses** (§5.5), at full content width.
- **Taps:** a tile opens the same group sheet as the row. The chips act exactly as on the row: Join and withdraw are optimistic, and the cache effects match.
- **Its total** is the line's count (§5.2).

## 7. Backend work
**All of it is additive.** Old app versions stay on phones for months. Use the `api-contract-change` skill, `make openapi`, then `make gen-api` at the root, and commit the regenerated clients.

1. **Totals on the four row reads**, as specified in §5.2: capped at 100, counted in SQL on the row's own condition, with the statement-count guard tests.
2. **A friend request carries every sport the sender holds a published level in** (on `HomeFriendRequestSchema`, for the sport-levels line).
3. **The envelope's "seen"** (§3.2):
   - a visit, recorded as an event, with a watermark of the newest item shown;
   - a "new" count on `GET /home`;
   - an "arrived at" for each kind of item, including one per level asker.
4. **A paged Groups heating up endpoint**: every group with at least 3 players, in the row's order, 20 per page by cursor, with the total.

## 8. Docs, ADR, glossary, design system (Q26, Q43, design exceptions)

### 8.1 New ADR
- **ADRs are immutable,** so one new ADR (via the `write-adr` skill) records every decision above. It names the parts it replaces:
  - **ADR-0204 §1:** the order and the "header and today's rows stay on top, unchanged" rule.
  - **ADR-0202:** the three request rows on Home, their placement, the "instead of Get your level" hand-off, and the friend link landing at the top of Home.
  - **ADR-0203 §5:** "the bell keeps its corner".
- **It also argues** why the envelope's count rides on `/home` while the bell's does not.

### 8.2 Updated in place
- **Home-rows spec** (`docs/specs/home-rows/`): README, `the-screens.md` §1, §2 and §7.1, `the-mechanics.md` §3 and §9.2.
- **Friends spec** (`docs/specs/friends/`): `the-screens.md` §6, the `the-mechanics.md` lines on Home and on the link, and README :52 and :59.
- **Games and Fill in** (`docs/specs/games-and-fill-in/the-screens.md` A8) and **Rankings** (`the-screens.md`, `the-mechanics.md`): the trophy and the bell.
- **Copy deck** (`docs/specs/matchmaking/the-words.md`): the new titles, FOR YOU, "Needs your answer", the section labels, the footers and "Open the rankings ›".
- **`CONTEXT.md`:** the entry for Home, the entry for Ask for a level ("waits in Needs your answer"), and the new **Needs your answer** term. Also clear the stale "not yet built" markers.
- **Frontend docs:**
  - **Feature docs:** `_shared.md`, `shell.md`, `proposals.md`, `friends.md`, `discovery.md`, `groups.md`, `rankings.md`, `notifications.md` and `links.md`.
  - **`architecture.md`:** the touch exceptions in the PR checklist.
  - **The `tabScreens.tsx` doc comment.**
- **This document and the 15 mocks** are copied into a new spec folder in the repo, so that "mocks lead" points at files the repo holds.

### 8.3 Design-system changes
The design system is locked: `theme.ts`, `design-system.md` and the audit change together, in one commit, each with a Part 16 row. Where the mocks break its rules, the design system is changed to match, as named exceptions:
1. **Shadow:** a seventh named shadow, for the open FOR YOU line. Today cards never cast one, apart from six listed exceptions.
2. **Count pill:** the grey count pill becomes a new fenced pill exception.
3. **Friend request tile width:** a new measured width for the tile in the sheet (about 0.83 × content, taken from mock 2), beside the standard 0.74.
4. **Header envelope:** the ink envelope in the header, alongside the volt one on the friend button, with one meaning for both: "someone asked you".
5. **New components:** the folding line (closed and open), the footer link row, and the Top 10 switcher's new right-opening direction.

## 9. Delivery and verification (Q27, Q40, Q41)
- **Branch:** `feat/RKTA-08_home_refactor`.
- **Spec and tickets** come from your `to-spec` and `to-tickets` skills. Implementation is done with your `implement` skill.
- **One session changes one app.** A hook blocks writes across app boundaries, so the work runs in three kinds of session:
  - **root:** the ADR, specs, `CONTEXT.md`, and `make gen-api`;
  - **`backend/`**;
  - **`frontend_player/`**.
- **A suggested slice order** (input for to-tickets, not binding):
  1. docs and ADR;
  2. backend: totals, friend request levels, the envelope's seen, the groups page endpoint;
  3. the header and "Needs your answer";
  4. FOR YOU;
  5. the Groups heating up page;
  6. a walk on the Android phone.
- **Definition of done for each slice:**
  - **Tests first,** in the repo's existing style.
  - **Backend slices** pass `make check`.
  - **Player app slices** pass `pnpm check`, run with the known Windows line-endings workaround so the result is real.
  - **The existing Home tests are rewritten, not deleted:** `friends.test.tsx`, `levelAsks.test.tsx`, `friendsGames.test.tsx`, `homeAndBookedGame.test.tsx`, `hottestGroups.test.tsx`, `sameLevel.test.tsx`, `newInRakieta.test.tsx`, `sameVibe.test.tsx`, `topTen.test.tsx`, `rankings.test.tsx`, `notifications.test.tsx`, `theShell.test.tsx`, `ShellScreen.test.tsx`, `HomeRow.test.tsx`, `RowSportPill.test.tsx` and `anotherSportAndTheHomeCard.test.tsx`.
  - **The ADR and the specs change in the same slice** as the behaviour they describe.

---

## Appendix A — Facts the decisions rest on (as found on `main` at bc6ca793)

**Home screen**
- **Where it is drawn:** `frontend_player/src/features/shell/components/tabScreens.tsx:108-147`.
  - The header's right slot (:116-121) draws `RankingTrophy`, then `NoticeBell`.
  - The body (:131-144) draws, in order: HomeLevelCard, FriendsGamesRow, PaymentsToConfirm, HomeFriendRows (FriendRequestsRow and LevelAsksRow), HomeRail, HottestGroupsRow, SameLevelRow, NewInRakietaRow, SameVibeRow, TopTenRow.
- **Row frame:** `shared/ui/HomeRow.tsx`.
  - `HomeRow` (:125-147): the heading, a `control`, a `link` and an `over` layer.
  - `HomeRowRail` (:187-264): peeking at 0.74, scrolling freely, with `snap` only on the paging rail. Since #809 it draws the first cards in the first frame and the rest a frame later.

**The four cards that move to the sheet**
- **Feeds:**
  - `GET /api/v1/home` carries `friends_games`, `friend_requests` and `level_asks`. They are not counted in `needing_you`.
  - `GET /players/me/payments-to-confirm` feeds To confirm (`PaymentsToConfirm.tsx`, one card with stacked rows today).
- **The friend request payload** (`HomeFriendRequestSchema`) carries at most one `sport`/`level`: the sport of the screen it was sent from.

**The bell**
- **Its "new" lives on the server:** `POST /players/me/notices/visit` records `RecentNoticesOpened` with a watermark, `seen_through`.
- **Its count, `new_count`,** rides on `GET /players/me/notices`, never on Home's read (`backend/.claude/rules/notifications.md:54-74`).

**The row reads**
- **No row read returns a total today.**
- **Limits:** Hottest groups returns at most 6 (`groups/domain/hottest.py`; at least 3 players to qualify; the reader's own groups are included). The three people rows return at most 10 each, and their See all screens page 20 at a time by cursor, per sport. Top 10 returns at most 10.
- **The rule that blocks animating height:** `frontend_player/CLAUDE.md:227-232`. Animate only `transform` and `opacity` per frame, and use a layout transition for size.
- **Sheets:** the custom `shared/ui/BottomSheet.tsx` on `ModalStage`, with an 88% cap and reduced-motion support. No navigation hook is allowed inside a sheet.
- **Groups list route:** `/play` lists only the player's own groups. No screen lists every group today.
- **Brand:** UI copy is always "Rakieta" (`discoveryCopy.ts:74-75`).

## Appendix B — Question index

| Q | Decision |
|---|---|
| 1 | Superseded by Q27/Q40 (branch, to-spec and to-tickets) |
| 2 | Friend request: drop the where-line and found-by lines; keep the reliability tag; keep the sport levels (Q28) |
| 3 | Equal-height tiles, buttons at the bottom, titles clamped to 2 lines |
| 4 | Envelope gets a badge, like the bell |
| 5 | Without the envelope, the bell and trophy stay pinned right |
| 6 | Fixed section order; empty sections hidden |
| 7 | Answered tiles leave; the last answer closes the sheet; live arrivals appear |
| 8 | Sheet height fits content up to the 88% cap; sections are sideways rails |
| 9 | Friends game: one big tile at a time (paging, Q46) |
| 10 | All lines closed at app start; the open line is remembered while the app lives |
| 11 | Reduced motion: lines open and close instantly |
| 12 | Only the header toggles a line |
| 13 | Get your level stays on Home whenever unrated; the ask goes to the sheet |
| 14 | To confirm moves into the sheet |
| 15 | Trophy takes the far-right corner |
| 16 | The two envelope meanings overlap and that is accepted; the header one is ink |
| 17 | Real totals |
| 18 | New Groups heating up page |
| 19 | Top 10 footer: switcher on the left, opening right; "Open the rankings ›" on the right |
| 20 | New titles on screen only; Rakieta |
| 21 | Empty, loading and failed lines are hidden; FOR YOU hidden when all are |
| 22 | Groups tile drops the heat bar, "+N this month" and the sport line |
| 23 | All lines load at start; tiles drawn only while open; on-screen counting only while open |
| 24 | Follow-up sheets return to the sheet; screens close it |
| 25 | Links and notices open Home with the sheet up |
| 26 | New ADR, docs updated in place, the document and mocks copied into the repo |
| 27 | Branch `feat/RKTA-08_home_refactor` |
| 28 | Sport-levels line: every sport, at most 2 lines |
| 29 | The badge counts new items since the last close |
| 30 | "Seen" is kept on the server, like the bell |
| 31 | What counts as new: new items and new askers, never state changes |
| 32 | To confirm first in the sheet, one tile per payment |
| 33 | Each total counts the pool; "See all N" uses the same number |
| 34 | Counts stay only if they cost little; evaluated, and they do (Q45) |
| 35 | Page: groups with at least 3 players, the row's order, yours included, 20 per page, no filter |
| 36 | Page uses the line's group tile |
| 37 | Switcher chevron "›" |
| 38 | A groupless player sees Groups heating up open; one Your games copy line changes |
| 39 | Accessibility labels, with counts |
| 40 | Tickets come from to-spec and to-tickets |
| 41 | Tests first; `make check` and `pnpm check`; tests rewritten; built with implement |
| 42 | Server "seen" is the bell's way, recorded on close; the count rides on `/home` |
| 43 | Term: Needs your answer |
| 44 | This file |
| 45 | Keep counts, capped at "99+", with statement-count guards and a phone timing check |
| 46 | Friends game uses the paging rail with dots |
