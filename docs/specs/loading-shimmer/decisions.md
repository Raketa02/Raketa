# Loading shimmer: Home, Rankings, See all and the group page, and the jump button's busy state — decision log

- **Date:** 2026-11-24
- **Source:** a grilling session (Q1–Q27, in three rounds plus one late question) on the request below. There is no brief document and there are no mocks.
- **Status:** every branch is settled. This file is the input for `to-spec` / `to-tickets`. Nothing has been written to the repo, and no issue has been opened.
- **Ground rules:**
  - **Player app only.** No backend change, no contract change, no regenerated types, no new dependency, no new colour value.
  - **Every number here comes from the code, the theme, a primary source, or a measurement still owed.** None of them was picked by taste (the planning workflow's rule).
  - **Keep it simple** (the user, Q21): *"it is just a loading effect in the end."*

The request, in the user's words:

> 1. A nice and minimalistic shimmer effect on the home screen when it has no data yet and the screen is not completely built. When the whole screen is loaded, smoothly and nicely show the entire home data.
> 2. A shimmer effect when the ranking screen is loading, either when landing from the home screen or when changing the sport on the selector inside the ranking screen.
> 3. Inside the ranking screen, when the button to navigate to your position is visible and pressed, a loading indicator in the button itself, showing the app is looking for your position, so it doesn't look frozen.

---

## 1. What changes, in one paragraph

- **A new `Skeleton` primitive in `shared/ui/` draws grey shapes in each screen's own layout, with one soft light band sweeping across all of them.** It is used on Home, Rankings, the four See all screens and the group page.
- **Content is revealed with one 200 ms cross-fade** once it is ready.
  - **Home** reveals everything together. After a 2.5 s ceiling it reveals from the top down instead: your things first, then FOR YOU.
  - **Home's data starts being read during the splash**, so a normal cold open should fade straight onto a full Home.
- **Rankings' *You · 212th* button** turns into "◌ Finding you…" while it reads the page around you.

---

## 2. What the investigation found

### 2.1 No loading primitive exists

- **There is no `Skeleton`, `LoadingState`, `EmptyState` or shimmer anywhere in `src/`.**
  - `docs/architecture.md:789-791` asks for them in `src/shared/ui/`, and `:812-814` says they *"stand as written"*.
  - `:825-826`: *"Skeletons where the layout is known and perceived speed matters; a localized indicator for a localized action."*
- **The record sheet's "skeleton" (`docs/features/player_record.md:494`) is a muted `ActivityIndicator`** inside a 380 pt standing body (`RecordRead.tsx:73-76`, `PlayerRecordSheet.tsx:165-170`, `:438-440`).
- **`ActivityIndicator` has 26 render sites in 25 files** outside `Button.tsx:318` and `Chip.tsx:175`. The busy-indicator log's *"23"* (`docs/specs/busy-indicator/decisions.md:17`) is out of date. That doesn't matter here.
- **Dependencies:** `react-native-reanimated` ~3.16.1 and `react-native-svg` 15.8.0 are installed (`package.json:56`, `:60`). `expo-linear-gradient` is not. SVG gradients are already drawn in `TintedTile.tsx:40,111` and `DrawnSplash.tsx:67`.
- **The Reanimated rule** (`frontend_player/CLAUDE.md`): per frame, only `transform` and `opacity` may move.

### 2.2 The design system's motion rules

- **§1.5 *"Nothing animates that does not have to"*** (`docs/design-system.md:217-237`) is a closed list. Reduced motion stops all of it except two items: the calculating screen's indicator and the busy spinner. Part 13 repeats this at `:5846-5849`.
- **A new loop needs a written Part 16 argument.** The typing entry says so, *"so the next one is not taken for free"* (`:6182`).
- **The empty state** (`:5021-5030`): *"one line of `tiny` in `muted`… No illustration, no spinner… a screen pretending to be loading something."*
- **Motion tokens** (`theme.ts:1927-2024`): `fade` 200, `rise` 300, `sheet` 260, `lineUnfold` 250, `lineFold` 200. The loops are `ripple` 1400 and `typing` 1200. The header says *"Nothing else moves"* and *"Every one of these is skipped when … isReduceMotionEnabled"*.
- **The neutral colours** (`theme.ts:37-51`), with contrast computed from their hex values:

| Token | Hex | On `paper` | On `surface` (white) | Meaning today |
| --- | --- | --- | --- | --- |
| `paper` | `#F4F2ED` | — | 1.12:1 | the app's ground |
| `paper2` | `#EDEAE3` | 1.07:1 | 1.20:1 | recessed |
| `paper3` | `#E2DED3` | 1.20:1 | 1.34:1 | the club card's tray |
| `line` | `#E5E1D8` | 1.17:1 | 1.30:1 | **bounds** a thing |
| `line2` | `#F0EDE6` | 1.05:1 | 1.17:1 | a fold inside a thing |

### 2.3 Home

- **`HomeScreen`** is in `features/shell/components/tabScreens.tsx:104-137`, on `ShellScreen`, mounted by `app/(app)/(tabs)/index.tsx`.
- **It has about ten independent reads**, and each section draws itself when its own read lands. Nothing draws a placeholder.
  - **The header** is pinned (`ShellScreen.tsx:248-255`).
    - The **envelope** is fed by `useHome`. It draws nothing until something is waiting (`NeedsYourAnswer.tsx:22-26`, `:173`).
    - The **bell** is fed by `['notifications','notices']`. It is always drawn, and its badge appears when the count is above 0.
    - The **trophy** is always drawn. Its number appears once a place is known (`RankingTrophy.tsx:13-15`, `:84`).
  - **The level card** (`HomeLevelCard.tsx:23-25`) is fed by the ratings, then by your groups. It is `null` until the answer is *ask*.
  - **YOUR GAMES** (`HomeRail.tsx:72-126`) is fed by `['proposals','home']`.
    - **It is deliberately drawn before its read lands**: *"Your games · 0"* and the two empty sentences (`:36-40`, `:78-99`).
    - A refused read with no data draws a coral `Note`.
  - **FOR YOU** (`tabScreens.tsx:143-182`) has five lines: Groups heating up, Players at your level, New in Raketa, Players with your vibe and Top 10. Each line is hidden while its read is in flight, empty or failed. The whole block, heading included, is `null` until one line exists (`:160`).
- **Top 10 waits for three other reads.** It is `skipToken` until `useOpeningSport` knows a sport from the ratings, the deck sport and Home's ranking (`useTopTen.ts:59-70`).
- **So the final layout cannot be known in advance.**
- **Pull to refresh** (`ShellScreen.tsx:98-106`, `:191-234`; `tabScreens.tsx:119-126`) invalidates four groups of reads. Content already drawn stays.
- **The app's query defaults:** `staleTime` 30 s, `gcTime` 5 min, `refetchOnMount: true` (`shared/lib/query-client/queryClient.ts:46-60`).

### 2.4 The splash and Home's first read

- **Home does not hold the splash.** The only `useSplashHold` caller is the entry gate, while it is *pending* (`app/(app)/_layout.tsx:156`; `splashHold.tsx:16-17`).
- **ADR-0209 §3:** the fade starts at the later of 2.6 s and the first screen being ready. *Ready* never means its data has arrived. The splash *"never waits for data and never stretches to cover slow loading"*.
- **ADR-0209's 2026-11-24 amendment is in the working tree, not committed.** **The tree mounts only once the ball is still**, at 1.78 s: mounting it mid-motion froze the ball (a 204 ms frame on the A32). So Home's own reads start about 0.2 s before the fade in a release build.
- **The ball and letters are moved by worklets on the UI thread** (`shared/lib/bootstrap/domain/splashMotion.ts`).
- **The startup sequence is composed in `app/_layout.tsx`.**
  - `restoreSessionStep` caches the account through `fetchCurrentUserAtLaunch` (`:58-60`).
  - `readInstallReferrerStep` is *"started, never awaited"* (`:62-68`). That is the precedent for a warm-up step.

### 2.5 Rankings

- **While a sport's first read is in flight, nothing is drawn under the General | Friends switch** (`RankingsScreen.tsx:212-218`).
- **A sport change remounts the view** (`key={page.sport}`, `:138`). General re-reads every time it opens (`refetchOnMount: 'always'`, `useGeneral.ts:70`).
- **The view switch is also a new read** (`GeneralView` / `FriendsView`, `:137-141`).
- **A refused read draws `ReadFailure` with *Try again*. A paused read draws the amber offline note.**
- **The jump button** is `JumpToMe.tsx`, a `dark` `Button` reading *You · 212th* (`jumpButtonLabel`, `rankingsCopy.ts:293`).
  - **A press on a row that is already drawn** scrolls to it, animated (`RankingList.tsx:135-140`).
  - **A press on a row that isn't drawn** resets and reads the page around you (`useGeneral.ts:108-112`). The list stays as it is until that page lands (`:11-14`, `:82`), then a new list of 50 rows is drawn and centred over a few frames (`RankingList.tsx:184-196`).
  - **A second press during the read** resets the query and starts again.
  - **Friends reads its whole table, so a press there is always a scroll** (`useFriendsTable.ts:52`).
- **`Button` already has `busy` and `busyLabel`**: a spinner before the busy word, at full fill, with presses blocked (`Button.tsx:127-137`, `:228-229`; busy-indicator log §2).

### 2.6 See all and the group page

- **The four See all screens** are New in Raketa, Same level and Same vibe (on `SeeAllScreen.tsx`) and Hottest groups (`HottestGroupsScreen.tsx`).
  - The real header is drawn first. Then a muted `ActivityIndicator` sits at the top of a padded body (`SeeAllScreen.tsx:138-146`, `:195`; `HottestGroupsScreen.tsx:91-95`).
  - Each is an infinite FlatList, 20 per page, with pull to refresh.
  - **The shapes are fixed:**
    - two-column tiles at `portraitTile.gridAspect` 1.125 (New in Raketa);
    - Same vibe's tiles (face 36, % circle 30);
    - Same level's cards (44 pt face);
    - Hottest groups' full-width cards.
- **The group page:**
  - **While the group read is in flight** there is a back arrow only, a **blank body** with no tab bar (`GroupHeader.tsx:62`; `GroupScreen.tsx:407-412`, `:423-436`). **Offline, it draws nothing at all**, not even the offline note.
  - **Games:** a muted spinner, **with no offline branch** (`GamesDeck.tsx:460-465`).
  - **Fill in** and **You're in:** spinners (`FillInBoard.tsx:81-87`; `YoureInBoard.tsx:92-106`).
  - ***Finding … games for you…*** (`FindingGames.tsx:26-38`) is an interstitial for a process the player started, not a first read.
  - **The Friends card's *Building*** is a dark card with a word (`FriendsCard.tsx:232-238`).
- **The tab-menu log** (`5.club_tab/decisions.md` §5.2, and `docs/specs/tab-menu/`): a kind swap to a kind that isn't cached shows *"today's centred spinner"* in the deck area, and *"Nothing new is built for loading."*

### 2.7 Research (the Q11 evidence)

- **No controlled study compares revealing a screen all at once against section by section.** The studies that exist compare skeletons, spinners and blank screens, and they disagree:
  - Viget, 136 people: skeletons were the slowest.
  - Bill Chung, 80 people: slightly faster, and **a left-to-right shimmer beat a pulse**.
  - Mejtoft et al. 2018: no significant difference.
- **Progressive filling assumes a known layout.** Apple's HIG says *"replacing these elements as content becomes available"*, and Wroblewski's 2013 original idea is the same.
- **Content inserted above what you are reading is the harm** (web.dev, CLS). React's docs call a lower section landing first and then being pushed down *"jarring"*. Their fix, `revealOrder="forwards"`, never shows an item before the ones above it.
- **React batches reveals within 300 ms.** From 19.2 it stops batching near **2.5 s**, which is borrowed from Google's "good" Largest Contentful Paint (LCP).
- **Facebook (2020) aims for a *"smooth, top-down page load"*.** Material 1 said *"Load and display all content at once"* for a first load. Instagram shows the cached feed first.
- **Facebook's Shimmer libraries, read from their source:**
  - **Android** (`Shimmer.java`): `animationDuration = 1000L`, no repeat delay, `RESTART`, `INFINITE`, `LEFT_TO_RIGHT`, `tilt = 20f`.
  - **iOS** (`FBShimmeringLayer.m`): speed 230 pt/s and a 0.4 s pause.

---

## 3. The look (Q1, Q2, Q3, Q21, Q23, Q24)

- **A sweep, not a pulse or still blocks** (Q1).
  - **Grey shapes in the content's place, with one soft light band crossing the whole screen at once**, not each shape on its own beat.
  - The band is a `react-native-svg` linear gradient, moved by `translateX` only. Each shape shows the part of the band that crosses it, positioned in the screen's coordinates.
- **The shapes take each screen's own content shape, at the real sizes** (Q1, Q21): rows, faces, tiles and cards come from `theme.ts`.
  - **Only parts that are always there are drawn.** A skeleton never guesses at optional sections.
  - **It does not remember last session's layout.** That would be content-shaped data on the phone with no ADR.
  - **A container that is always there is drawn as itself**, such as the Rankings list's white card and See all's white cards. **Everything else is a rounded shape.** The dark place card on Rankings is a `paper3` block, not dark.
- **Colour** (Q23): **shapes in `paper3`** (1.20:1 on paper, 1.34:1 on white). **At its peak the band brightens them to `paper`**: the gradient runs shape → paper → shape, so no opacity number is needed. `line` was rejected because it means *bounds*; `paper2` and `line2` are too faint on paper.
- **Timing** (Q24): Facebook's Android defaults. **One sweep per 1000 ms, left to right, no pause, repeating forever, the band tilted 20°, at constant speed.**
- **Reduced motion: it sweeps anyway** (Q2). This is the **third named exception** beside the calculating screen's indicator and the busy spinner, for the same reasons:
  - A still loading state reads as frozen.
  - ADR-0198: a screen adds no setting-driven timing of its own.
  - In code, the sweep is given `ReduceMotion.Never`. Reanimated cuts `withTiming` under reduced motion otherwise.
- **One primitive, `Skeleton`, in `shared/ui/`** (Q3). It provides the shapes (block, line, circle) and the one band. **Each feature composes its own layout from it**: the layouts are the features', the primitive is shared.
- **Hidden from a listener, announcing nothing** (raised and not objected to): ADR-0198, the name is the whole job.

## 4. When a skeleton shows (Q4, Q7, Q14, Q20)

- **Only when the screen, or the part of it, has nothing to draw**, which means a first read with nothing cached.
  - **Cached data is drawn at once, and a fresh read replaces it quietly** (Q4, Q14).
  - **Pull to refresh and background re-reads never show a skeleton.**
  - **Once a screen has revealed, it never goes back to its skeleton while it stays mounted.**
- **Only while a read is actually in flight** (Q7):
  - **A refused read** replaces the skeleton with today's `ReadFailure` and its *Try again*.
  - **A read waiting for a connection** replaces it with the amber offline note.
  - **A skeleton never stands in for an empty state** (design-system `:5021-5030`).
- **No delay before it shows, and no minimum time on screen** (Q20).
  - It is drawn from the screen's first frame if anything is unfinished.
  - The cross-fade (§5) turns a short wait into a soft fade, not a flash.
  - If everything is already cached or warmed (§7), there is no skeleton and no fade.
  - Why: NN/g and React would delay an indicator, but here the alternative is a blank body, which is the frozen look. A timer in every skeleton is also the router harness's known trap; the busy indicator rejected one for the same reason (busy log Q6).
- **Pull to refresh still works while a skeleton is up**, and the skeleton stays until the reveal (raised and not objected to).

## 5. The reveal (Q11, Q17)

- **One cross-fade from the skeleton to the content, on `motion.fade` (200 ms), opacity only** (Q17).
  - **The content is drawn underneath the skeleton while it waits**, hidden, so it is already laid out and the fade reveals a finished screen.
  - One fade, no stagger.
- **Reveal together, top-down, with a ceiling** (Q11), on every screen with more than one read:
  - **Before the ceiling: one reveal.** Everything appears together once every read it waits for has finished.
  - **At the ceiling:** what is ready is revealed **from the top down, stopping at the first part that isn't ready**. That part and everything below it keep their skeleton, and appear in order as each finishes. **A lower part never appears before an upper one.**
  - **The ceiling is 2.5 s** (React 19.2's cut-off, from LCP's "good"). **Check it against a cold open on the A32** before the spec settles it (Q13).
- **A read counts as finished** (Q13) when any of these happens:
  - it lands;
  - it is refused;
  - it pauses because the phone is offline;
  - **it fails once and starts retrying.** One failing read must not hold the screen through its backoff.
- **A screen with one read** (Rankings, See all) simply reveals when its read finishes.

## 6. Home (Q11–Q16)

- **When:** only when Home has nothing to show: the first open after launch or sign-in, with the cache empty (Q14).
- **The header is drawn for real from the start**: the title, the bell and the trophy. **Its numbers wait**: the envelope, the trophy's place and the bell's badge (Q12).
- **What the skeleton draws** (Q15), with no level card and no envelope, since they are often absent:
  - a *YOUR GAMES* heading bar and **one game-card block at the rail's real card size**;
  - a *FOR YOU* heading bar and **four closed-line bars at the real line height**.
- **YOUR GAMES' *"· 0"* while loading goes** (Q16). The skeleton replaces it, and the count and sentences arrive with the reveal. **This reverses `HomeRail.tsx:36-40`'s written rule** (§11).
- **Two parts, top-down** (Q11, Q12):

| Part | Draws | Waits for |
| --- | --- | --- |
| **1 — your things** | the header's numbers, the level card, YOUR GAMES | the home read; the ratings (and your groups, where the level card needs them); in-no-group; the bell's notices |
| **2 — FOR YOU**, all its lines together | the FOR YOU heading and whichever lines have content | Hottest groups; the three discovery lines; Top 10 (last, behind its three reads) |

- **After the ceiling, the header's numbers appear as soon as they land.** They sit in a right-aligned slot and push nothing down.
- **Photo bytes are never waited for.** Faces load on their own.

## 7. Home's data is read while the splash plays (Q18)

The user's idea: *"start asking for the data in the background while the splash animation takes place without interfering with the splash animation."*

- **Why it is safe where mounting was not:** the freeze came from creating views on the thread that moves the ball (§2.4). **Reads create no views.**
  - Responses are parsed on the JS thread. The ball and letters move on the UI thread (worklets).
  - A read landing in a cache that nothing watches causes no React commit.
- **A new launch step, "warm Home", started and never awaited**, like `readInstallReferrerStep` (`app/_layout.tsx:62-68`). It runs **right after `restoreSessionStep`**, which has cached the account by then.
  - **Only when the account's entry decision is the tabs**, not naming, the social steps, a club's area or Start playing. The entry decision has to be callable from the launch step, not only from its hook (`useEntryDecision`). That is for the spec.
  - **Skipped when the phone already knows it is offline**, by the launch check's rule (#858, `readReachability`).
  - **Same keys and query functions as Home's hooks**, Top 10's chain included, so Home's hooks find the reads already in the cache. The app's 30 s `staleTime` means Home finds them fresh when it mounts and does not ask again.
  - **Who composes it:** `shared/lib/bootstrap` may not import a feature, so the root layout composes the step, as it does the other two. The shell feature, which owns Home, offers the warm-up from each feature's public prefetchers through their `types.ts`. Names are for the spec.
- **The splash still never waits** (the user, Q18: *"the home should not hold the splash"*). ADR-0209's fade rule is unchanged.
- **Launch only.** After sign-in, Home mounts the moment the session opens, so a warm-up would gain nothing.
- **Expected effect:** on a normal connection, a cold open fades straight onto a full Home. The shimmer shows on slow networks, after sign-in, and once the cache has been cleared.
- **Acceptance test: the A32 system trace of a cold start** (the perf harness). Frames over 20 ms in the splash's first 2.6 s must not rise above the amendment's 3–5 (debug build). Then a look on a release build.
- **Recorded as an amendment to ADR-0209**: the sequence gains a step.

### 7.1 The shimmer's own cost on the A32 (Q27)

- **The risk:** the sport-pill trace (2026-11-24, the perf notes) found that while anything inside a scroller moves, Android's RenderThread redraws **the whole scroll viewport every frame**: 14–18 ms on the A32, against a 16.7 ms budget.
  - Moving content doesn't clip to its own area on RN Android, and `renderToHardwareTextureAndroid` did not bound the redraw.
  - The shimmer moves every frame for as long as it is up, so it will pay that cost the whole time.
  - The splash's 0.5 s fade onto Home's shimmer, and the 200 ms reveal, run on top of it.
  - **One unknown in its favour:** while the skeleton is up the content underneath is hidden, so each redraw may cost less than it did behind the pill.
- **Decision: keep the look and measure the cost.** The check uses the same atrace harness on the A32, with Home and Rankings shimmering, through the splash fade and the reveal. **Frames over 20 ms must stay at the level of a still screen.**
- **No fallback is decided now.** If the check fails, the numbers go back to the user. A pulse would not help, because anything that moves every frame causes the same redraw.

## 8. Rankings (Q4–Q7, Q22)

- **When:** opening the page, a sport change and a view change (General | Friends), each **only when that sport and view have nothing cached** (Q4, Q5).
- **What it draws** (Q6): one fixed skeleton for both views, below the switch:
  - a card-sized block, where the place card or the not-listed card will be;
  - three podium steps;
  - rows on one white card, enough to fill the screen. Each row has the real row's padding, a `ROW_FACE` circle, and bars for the name and the level.
  - It does not predict the page's true shape (no card, *Nobody ranked*, or Friends' empty card on its own).
- **Refused, offline and pull to refresh: §4's rules** (Q7).
- **Home does not read the Rankings page ahead** (Q22). A 50-row read on every Home open is not worth it while Q4 already makes a second visit instant. **Revisit if a measurement shows the landing feels slow.**

## 9. The jump button (Q8–Q10)

- **Busy is `Button`'s own `busy`** (Q8): **"◌ Finding you…"**, a spinner before the busy word at full fill.
  - The word goes in `rankingsCopy.ts`. While busy it is also the button's spoken name.
  - The button sizes to its text, so its width changes, as other buttons' already do when their label swaps.
- **Busy only on a jump that has to read** (Q9): a row that isn't drawn yet. A press on a row already drawn is only a scroll, and a spinner there would flicker. Friends never shows busy.
  - **It starts at the press.**
  - **It ends** at the first of these:
    - the reader's row is on screen, and the button goes away as it does today;
    - the jump is refused, and today's failure takes the button's place;
    - the reader drags the list themselves. The read still lands and swaps the list as it does today.
- **A second press while busy is blocked** (Q10). `busy` already blocks presses, which fixes today's restart of the read (`useGeneral.ts:108-112`).
- **A sport change during a jump** remounts the view, so busy simply resets (raised and not objected to).

## 10. See all and the group page (Q19, Q26)

- **Both get the shimmer** (Q19). Their layouts are known (`architecture.md:825`). The blank group page is exactly the frozen look. A tap from a shimmering Home to a spinner would feel inconsistent.
- **See all**, on all four screens: the real header, then **that screen's own tiles or cards in grey, at their real grid and sizes**, filling the screen.
  - New in Raketa and Same vibe: two-column tiles.
  - Same level and Hottest groups: full-width cards.
  - Later pages keep today's footer behaviour.
- **The group page:** a monogram circle and a name bar, the tab bar's shape, and the active tab's body:
  - **Games:** one deck-card block filling the stage;
  - **Fill in and You're in:** rows.
  - **It reveals together, top-down, with the same 2.5 s ceiling.** At the ceiling the header and the tabs come first, and the body keeps its skeleton.
  - **Switching to a tab with nothing cached** shimmers only that tab's body (§4).
  - **The offline gaps are fixed by §4's rule**: the group read held offline, and the deck's spinner offline, both draw the amber note.
- **The tab menu's kind swap** (Q26), amending the tab-menu log §5.2:
  - **To a kind that isn't cached:** the old stack slides out, **the deck-card skeleton stands in the deck area** in place of the spinner, and the new stack rises into place exactly as the tab menu decided. Its rise replaces §5's cross-fade there.
  - **Unchanged:** cached swaps, the failed read and the menu.
  - **Whichever of the two pieces of work lands second on the branch adapts to the other.**

## 11. What stays exactly as it is, and named exceptions

- **Keeps its own drawing** (Q19):
  - *Finding … games for you…*;
  - the Friends card's dark *Building*;
  - the record sheet's spinner in its standing height;
  - the calculating screen;
  - every other screen's spinner (Game details, Skill passport, Post a game and the rest);
  - the busy buttons and chips;
  - `RefreshControl`.
- **Exceptions and reversals this work records:**
  - **Design system §1.5 and Part 13:** a new loop, and the **third** reduced-motion exception, each with a dated Part 16 entry.
  - **`theme.ts`'s motion header** (*"Nothing else moves"*, *"Every one of these is skipped…"*) gains the loop and its exception.
  - **`HomeRail.tsx:36-40`:** *"not gated on the read having landed"* is reversed (Q16).
  - **ADR-0209:** the startup sequence gains the warm-up step (Q18).
  - **The tab-menu log §5.2:** *"today's centred spinner… Nothing new is built for loading"* is amended (Q26).

## 12. Calls made while writing this log (for the user to check)

- **The reveal's fade under reduced motion is a cut.** Only the sweep is the exception (Q2). `fade` stays on `theme.ts`'s rule, where every motion is skipped under reduced motion.
- **The ceiling is measured from the screen's mount.** On a cold open Home mounts under the splash at about 1.78 s, so its ceiling ends about 1.7 s after the fade.
- **On Rankings, a skeleton is drawn below the header** while the sport or the view is still unknown. The switch's place is then a pill-shaped shape, rather than a blank moment.

## 13. Docs to amend

- **`frontend_player/src/shared/ui/theme.ts`**, in the same commit as the design system:
  - `color.skeleton` (`paper3`'s value) and `color.skeletonSheen` (`paper`'s value);
  - `motion.skeleton` 1000, with the band's 20° tilt beside it;
  - the motion header's list and exception.
- **`frontend_player/docs/design-system.md`:**
  - §1.5's list (`:217-237`);
  - Part 13's exceptions (`:5846-5849`);
  - Part 15 for the new tokens;
  - Part 5 or 7 for the `Skeleton` primitive;
  - dated Part 16 entries: the loop, the colours, the third exception.
- **`frontend_player/src/shared/ui/README.md`:** `Skeleton` built.
- **`frontend_player/docs/architecture.md`:** `:789-791`, `:812-814`, so `Skeleton` is built and no longer *"as written"*.
- **`docs/adr/0209-…md`:** an amendment for the warm-up step. Commit the 2026-11-24 amendment first; it is in the working tree.
- **`frontend_player/CLAUDE.md`:** the bootstrap sequence's order line gains the warm-up step.
- **`frontend_player/docs/features/`:**
  - `shell.md`: Home's skeleton, reveal and warm-up;
  - `rankings.md`: the skeleton and the jump's busy;
  - `discovery.md` and `groups.md`: See all, Hottest groups and the group page;
  - `proposals.md`: YOUR GAMES' *· 0*, the deck and the boards.
- **`docs/specs/tab-menu/` and `5.club_tab/decisions.md` §5.2:** the dated Q26 amendment.
- **Module notes:**
  - `HomeRail.tsx` (`:36-40`), `JumpToMe.tsx`, `RankingsScreen.tsx`, `useGeneral.ts`;
  - `SeeAllScreen.tsx`, `HottestGroupsScreen.tsx`, `GroupScreen.tsx`, `GamesDeck.tsx`, `FillInBoard.tsx`, `YoureInBoard.tsx`.

## 14. Delivery (Q25)

- **This log:** `C:\Users\rober\Desktop\rakieta_features\6.loading_shimmer\decisions.md`.
- **The work is done on the current branch, `feat/RKTA-10_for_fun_refactor`** (the user).
- **The user writes the spec and the tickets with their own `to-spec` / `to-tickets`.**
- **A natural split, for the user to judge:**
  1. docs: the ADR-0209 amendment, the design-system rows, the theme tokens;
  2. the `Skeleton` primitive;
  3. the jump button;
  4. Rankings;
  5. Home's skeleton and reveal;
  6. Home's warm-up, with its trace;
  7. See all;
  8. the group page and the kind swap.

  The jump button (3) is independent of everything else.

## 15. Tests the change reaches

- **`Skeleton` primitive tests:**
  - it sweeps under reduced motion (`ReduceMotion.Never`);
  - it is hidden from a listener;
  - the band moves by transform only.
  - Use `getAnimatedStyle`, not `props.style`.
- **Rankings:** `rankings.test.tsx`.
  - Skeleton on a first read, none on a cached sport;
  - refused and offline replace it;
  - the jump is busy through the around-me read, a second press is ignored (one request), and busy ends on refusal.
- **Home:** the shell suites (`theShell.test.tsx`, `friendsGames.test.tsx` and the line suites).
  - Skeleton while the reads are in flight;
  - one reveal when all have finished;
  - the top-down reveal at the ceiling, where a part never appears above an unfinished one.
  - **Router-harness traps:** fake timers exist only after `launchSignedIn`, and navigation runs every pending timer, which includes the ceiling's.
- **The warm-up:** the launch gate's or the root layout's suite.
  - Started after the session is restored, never awaited;
  - skipped for non-tabs destinations and when known offline;
  - Home's hooks find the reads fresh (no second request).
- **The group page:** `groupGames.test.tsx`, `joinGroup.test.tsx` and the board suites, including the offline note.
- **See all:** `newInRaketa.test.tsx`, `sameLevel.test.tsx`, `sameVibe.test.tsx` and the Hottest groups suite.

## 16. For the user to check on a phone

- **The sweep's look:** its colour, the 1000 ms beat and the 20° tilt, on the A32 and an iPhone.
- **The 200 ms cross-fade**, and that it doesn't jump.
- **Home's cold open with the warm-up:** the ball must stay smooth (the trace), and the splash should usually fade onto a full Home.
- **The shimmer's frame cost** (§7.1, Q27): an atrace of Home and Rankings while they shimmer, through the splash fade and the reveal. Frames over 20 ms must stay at a still screen's level. If not, bring the numbers back to the user.
- **The 2.5 s ceiling** against a measured cold open.
- **"◌ Finding you…" on the dark button**, and its width change.

## 17. Out of scope, or rejected

- **Out of scope:**
  - every other screen's loading (§11);
  - reading Rankings ahead from Home (Q22);
  - a warm-up at sign-in (Q18);
  - remembering last session's layout (Q21);
  - the backend.
- **Rejected:**
  - a pulse, or still blocks (Q1 b, c);
  - each shape shimmering on its own beat (Q1);
  - pausing the sweep under reduced motion (Q2);
  - a skeleton on every sport switch even when cached (Q4 b);
  - predicting the Rankings page's shape (Q6);
  - spinner plus the unchanged label on the jump (Q8 b);
  - busy on a scroll-only jump (Q9);
  - section-by-section reveal with no ceiling, and all-at-once with no ceiling (Q11 a, b as first put);
  - no time limit on Home (Q13);
  - a fixed number picked without a source (Q13, Q24);
  - Home holding the splash (Q18);
  - a delay before, or a minimum time for, a skeleton (Q20);
  - the iOS library's 230 pt/s with its 0.4 s pause (Q24);
  - `line`, `paper2` or `line2` for the shapes (Q23);
  - the spinner in the tab menu's kind swap (Q26).

---

## Evidence index

- NN/g, response times: https://www.nngroup.com/articles/response-times-3-important-limits/
- NN/g, Skeleton Screens 101: https://www.nngroup.com/articles/skeleton-screens/
- Wroblewski, *Avoid the spinner* (2013): https://www.lukew.com/ff/entry.asp?1797
- Viget, *A bone to pick with skeleton screens*: https://www.viget.com/articles/a-bone-to-pick-with-skeleton-screens/
- Mejtoft et al., ECCE 2018: https://doi.org/10.1145/3232078.3232086
- Bill Chung, skeleton screens study: https://uxdesign.cc/what-you-should-know-about-skeleton-screens-a820c45a571a
- web.dev, CLS: https://web.dev/articles/cls and https://web.dev/articles/optimize-cls
- Apple HIG, Loading: https://developer.apple.com/design/human-interface-guidelines/loading
- Material 1, progress & activity: https://m1.material.io/components/progress-activity.html
- React, Suspense: https://react.dev/reference/react/Suspense
- React 19.2, batching Suspense boundaries: https://react.dev/blog/2025/10/01/react-19-2#batching-suspense-boundaries-for-ssr
- React 17, concurrent-mode reference (`SuspenseList`): https://17.reactjs.org/docs/concurrent-mode-reference.html
- Facebook, 2020 redesign: https://engineering.fb.com/2020/05/08/web/facebook-redesign/
- Facebook Shimmer, Android defaults: https://raw.githubusercontent.com/facebook/shimmer-android/main/shimmer/src/main/java/com/facebook/shimmer/Shimmer.java
- Facebook Shimmer, iOS defaults: https://raw.githubusercontent.com/facebook/Shimmer/master/FBShimmering/FBShimmeringLayer.m
- Slack, incremental boot: https://slack.engineering/getting-to-slack-faster-with-incremental-boot/
- Instagram, cache-first: https://instagram-engineering.com/making-instagram-com-faster-part-3-cache-first-6f3f130b9669

## Question index

| Q | Settles | § |
| --- | --- | --- |
| Q1 | A sweep, one band across the screen, in the content's shape | 3 |
| Q2 | It sweeps under reduced motion: the third exception | 3 |
| Q3 | One `Skeleton` primitive in `shared/ui`; layouts per feature | 3 |
| Q4 | Rankings: only when nothing is cached | 8 |
| Q5 | Rankings: the view switch too | 8 |
| Q6 | Rankings: one fixed skeleton | 8 |
| Q7 | Only while a read is in flight; refused and offline replace it | 4 |
| Q8 | Jump: "◌ Finding you…" | 9 |
| Q9 | Jump: busy only on a reading jump, and when it ends | 9 |
| Q10 | Jump: a second press is blocked | 9 |
| Q11 | Reveal together, top-down, with a ceiling (researched) | 5, 6 |
| Q12 | Home: which reads, in two parts | 6 |
| Q13 | What "finished" means; a ceiling, checked by measurement | 5 |
| Q14 | Home: only with nothing to show, once per mount | 6 |
| Q15 | Home: what the skeleton draws | 6 |
| Q16 | Home: YOUR GAMES' *· 0* goes | 6 |
| Q17 | A 200 ms cross-fade, content laid out underneath | 5 |
| Q18 | Home's reads are warmed during the splash; it never waits | 7 |
| Q19 | See all and the group page get it | 10 |
| Q20 | No delay, no minimum | 4 |
| Q21 | Each screen's own shape, kept simple | 3 |
| Q22 | Home doesn't read Rankings ahead | 8 |
| Q23 | `paper3` shapes, `paper` at the band's peak | 3 |
| Q24 | 1000 ms, left to right, no pause, 20° | 3 |
| Q25 | This folder; the current branch | 14 |
| Q26 | The tab menu's kind swap gets the skeleton | 10 |
| Q27 | The shimmer's redraw cost on the A32: measured, no fallback decided yet | 7.1, 16 |
