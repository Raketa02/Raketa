# The tab bar as a floating glass dock, with a travelling selection marker — decision log

- **Date:** 2026-11-24
- **Source:** a grilling session on the brief `menu_refactor.md` and its three mocks. It ran Q1–Q26 over three rounds, with one addendum (Q13–Q16) after the router was mapped.
  - `1_menu component.png`: the dock, Home selected.
  - `2_bottom_menu_home_sceen.png`: the dock on a full screen.
  - `3_bottom_menu_play_selected.png`: Play selected, shown during Q6.
- **Status:** every branch is settled and the user agreed to all 26 answers. This file is the input for `to-spec` / `to-tickets`. Nothing has been written to the repo, and no issue has been opened.
- **Ground rules:**
  - **Player app only.** No backend change, no contract change, no regenerated types.
  - **One new dependency, `expo-blur`**, installed with `npx expo install`, for the glass. It owns no styling, so ADR-0012's rule is untouched. **The bar's icons need none**: Ionicons ships in the already-declared `@expo/vector-icons@14.0.4`.
  - **The mocks lead on design** (the brief: *"The design from the mock references is priority so if you have to create new adr or update then do it"*), **but no number is taken from a mock.** Each one rests on the brief's text, the code, the theme, a computation shown here, or a measurement still owed. Where the brief's own text gave a number that the evidence moved (10 → 12, 76 → 75, coral → `coralInk` for words), the evidence won, and the user agreed.

---

## 1. What changes, in one paragraph

- **The tab bar stops ending the screen and floats over it.** It becomes a rounded slab 54 tall, 12 in from each side, lifted 12 (or the bottom inset, if larger) off the bottom, with radius 22.
- **It is frosted glass where blur is affordable**: 88% white with a strong blur, a bright inner rim, a faint outer hairline and a soft low shadow. On iPhone it always is. On Android it is glass only if an A32 spike shows the blur costs no frames; otherwise the Android dock is opaque `surface` white with the same shape.
- **The three tabs are equal columns** of an icon over a label: Home (house), Play (bolt, always filled) and You (head and shoulders). The ⚡Play disc and its ring are gone. Icons are Ionicons, outlined when idle and filled when selected.
- **The selected tab sits in an opaque `coralSoft` capsule, *the selection marker* (75 × 42).** Its icon is `coral` and its label `coralInk`.
- **When the lit tab changes, the marker travels.** It is a 460 ms spring that stretches as it speeds up, recoils as it brakes and overshoots by a few points, and the new tab colours in 140 ms after it sets off.
- **Content runs under the dock.** Every list ends 15 above it. The deck, the toasts, Post a game and the pinned CTAs all sit at the dock's reach plus their own existing gap.

---

## 2. What the investigation found

### 2.1 The bar today

Paths are relative to `frontend_player/` unless stated.

- **A custom `TabBar`** (`src/shared/ui/TabBar.tsx`), not React Navigation's.
  - Three `flex: 1` columns `Home · ⚡Play · You` (`TAB_BAR_TABS`, `:115-119`).
  - `surface` (#FFFFFF) ground with a 1pt `line` top border.
  - Padding: `paddingTop` 6, `paddingBottom` 12 + inset (`:195-198`).
- **Height:** `TAB_BAR_HEIGHT = 1 + 6 + 30 + 3 + 12 + 12 = 64` plus the inset (`:135-141`). The 30pt Play disc sets it.
- **Home and You columns:**
  - Feather `home` / `user` at 16pt, typed against `Feather.glyphMap`.
  - **Selection in tone alone**: `ink` selected, `muted` at rest (ADR-0135).
  - The column dims to 0.7 while pressed (`:401`).
- **The Play column:**
  - A 30pt `coralInk` disc (radius 11, turning `coral` on press) with a white Feather `zap` at 15pt, casting `shadow.fab` (coral-tinted on iOS only).
  - When Play is active, an absolutely positioned 2pt `coral` ring sits 2pt clear of the disc.
- **The label:** `tag` (Archivo 700, 9.5/12), one line, `maxFontSizeMultiplier` 1.6 (`size.tabBar.labelMaxScale`).
- **One badge, on Home** (`useHomeBadge()`, `features/proposals/hooks/useHome.ts:226-229`):
  - Drawn as `CountBadge` with tone `attend`: `coralInk` fill, white mono digit, minimum 18, no cap.
  - It rises 4 above the icon box and sits 3 back over the icon's right edge.
  - It is spoken as *Home, 2 games waiting on you* (`:184-189`).
- **Accessibility:** each column has `accessibilityRole="tab"`, a label, and `accessibilityState={{ selected }}`.
- **Nothing animates on a tab change.** Tab roots swap with `animation: 'none'`, and the bar never moves.
- **The Administrator's bar**, `AdministratorTabBar` (`:243-254`), draws two columns, Groups · You, in Feather `users` / `user`.

### 2.2 The shell

- **One stack, not `<Tabs>`.** `TabShell` (`src/features/shell/components/TabShell.tsx:87-125`) mounts one `Stack` and **one `TabBar` below it as a flex sibling**.
- **Selection is read from the URL's first segment**: `tabForPathname` (`features/shell/domain/shellTabs.ts:119`).
  - `INSIDE_A_TAB` (`:77-92`) maps `booking`, `notices`, `rankings` and the See all pages to Home.
- **A tab press is `openTab` → `resetShellStack`** (`features/shell/components/shellNavigation.ts:95`). The stacks are `[/]`, `[/, /play]` and `[/, /you]`.
  - Home stays mounted.
  - **You and Play are laid down fresh on every press.**
  - Pressing the lit tab at its start does nothing; pressing it from deeper in resets to the start.
- **A group opened from Home's *Groups heating up* pushes `/play/group/{id}`**, so today the lit column switches to Play, and back returns to Home (`HottestGroupTaps.tsx:98`).
- **The bar's absences:**
  - The chat (`/booking/{id}/chat`) doesn't render it (`barStandsDown`, `shellTabs.ts:141`).
  - *It's a game!* is a full-phone `ModalStage`, not a route, so it covers it.
  - Sheets, popovers, toasts and the launch splash sit above it.
  - Auth, onboarding and the entry screen are outside `(tabs)`.

### 2.3 What is placed against the bar

- **No screen reserves room for the bar**; it is a flex sibling and owns the bottom inset. Screens inside the tabs take the top inset only (`ShellScreen` via `TopSafeArea`; others `SafeAreaView edges={['top']}`).
- **`ShellScreen`'s scroller ends with `paddingBottom` 15** (`ShellScreen.tsx:299`), and its pinned `action` sits above the bar.
- **The toast** sits at `TAB_BAR_HEIGHT + insets.bottom + 9` (`shared/ui/Toast.tsx:113`). **The Undo toast** uses `toastAbove={barShown ? TAB_BAR_HEIGHT : 0}` (`TabShell.tsx:96`).
- **Post a game's button** is absolute at `bottom: gutter` inside the group page (`GroupScreen.tsx:643`).
- **Pinned CTAs** (`action=`): Friends, Invite a friend, and the You editors Intro, Photos, Tags and Your week.
- **The Games deck** (`GamesDeck.tsx`, `DeckStage.tsx`, `DeckAnswers.tsx`):
  - ✕ 54, i 42, the yes ball 66, gap 18.
  - The buttons sit **15 above the bar's hairline** (the scroller's padding).
  - The stage fills what's left above them, and since #865 it scrolls only below its least height.

### 2.4 The rules this reverses (all locked)

- **design-system §1.1 *Paper, not glass*** (`docs/design-system.md:105-113`): *"A deliberate rejection of the 'floating card on grey' pattern."*
- **§1.2's coral list** (`:115-142`): the *active tab* is one of the six. It also says ***"a coral stroke is where you are … a `coralInk` fill is a thing to attend to."***
- **§10.1** (`:5261-5300`): *"The CTA and the tab bar are **flex siblings** below the scroller, never fixed elements"* and *"The tab bar owns the bottom safe-area inset."*
- **§10.2** (`:5321-5478`): the disc, the ring, Feather, *"Selection changes tone and never shape."*
- **ADR-0135**: Feather, *"selection changes tone, and never shape"*, and *"a future surface genuinely needing a filled … glyph needs a second family or a drawn one, and this ADR authorises neither."*
- **The motion list** (`theme.ts:1973-1985`): *"Nothing else moves."* There is no spring anywhere in `src/`.
- **The shadow inventory is closed at seven** (`theme.ts:1872-1971`, `.claude/rules/design-system.md`).

### 2.5 Evidence on the platform

- **Expo SDK 52, RN 0.76.9, New Architecture on** (`app.config.ts:70`), Reanimated 3.16.7.
- **No blur library is installed.**
  - From expo-blur's documentation (not verified in the package, since it isn't installed): **Android blur in SDK 52 is the experimental `dimezisBlurView`**. It redraws the window behind it into a bitmap whenever anything under it or on it changes. iOS blur is the native `UIVisualEffectView`.
- **SDK 52 doesn't draw edge to edge on Android**, so the A32's bottom inset is 0. The navigation bar is opaque (`systemBars.android.ts`'s note).
- **Measured on the A32** (the 2026-11-24 perf work):
  - The RenderThread redraws the whole scroll viewport on every animation frame, at **14–18 ms a frame**.
  - About **150 ms** passes from touch-end to views inserted (debug native).
  - A **204 ms** frame once came from a tree mounting mid-motion (the splash).
  - Debug native costs Reanimated **8–10 ms a frame**.
  - **No local release APK can be built** (path length).
- **The project's Reanimated rule** (`frontend_player/CLAUDE.md`): per frame, move only `transform` and `opacity`; never animate a layout prop.
- **Android's expo default `softwareKeyboardLayoutMode` is `resize`** (not set in `app.config.ts`). Today's bar therefore rides up above the keyboard, and the scroller shrinks above it.
- **Glyphs checked in the installed `@expo/vector-icons@14.0.4` glyph maps:**
  - Ionicons `home`, `home-outline`, `flash`, `flash-outline`, `person`, `person-outline` ✓.
  - MaterialCommunityIcons `home-outline`, `lightning-bolt`, `account-outline` ✓.

---

## 3. Names (Q1)

- **It stays *the tab bar*.** "Floating glass dock" describes its look and isn't its name.
  - "Bottom menu" would collide with **the tab's menu** (`TabMenu`, the menu that folds out of a group page's Games/Friends tab).
  - "Tab bar" is the name in §10.2, in `TabBar`, and in both glossaries.
- **The coral capsule is *the selection marker*,** the brief's own phrase.
  - "Pill" is taken three times: the chip's shape `radius.pill`, `SportPill`, and FOR YOU's count pill.

---

## 4. Geometry (Q5, Q8)

| Part | Value | Ground |
| --- | --- | --- |
| Dock height | **54** | the brief; on the 3pt grid |
| Side inset | **12** each side | the brief; `space.md`. The dock is 6 wider than content (screen − 30), as the brief draws |
| Lift off the bottom | **the larger of 12 and the bottom inset** | the brief's 10 is off the grid. 12 = the side inset, an even margin on Android (inset 0). On a notched iPhone the dock rests on the safe-area line, as iOS's own bars do |
| Corner radius | **22** | the brief; `radius.sheet`'s existing value |
| Columns | **three equal**: (screen − 24) ÷ 3 | 98.7 at 320 · 120 on the A32 (384) |
| Marker | **75 × 42**, `radius.pill`, centred in its column | the brief's 76 is off the grid; 42 is the brief's |
| Icon | **18** | the largest that keeps the capped label inside the marker (below) |
| Icon → label gap | 3 | today's |
| Label | `tag`, `maxFontSizeMultiplier` 1.6 | today's |

**The fit, computed:**
- icon + 3 + label line inside the 42 marker:
  - **16** → 31 at 1×, 39.4 at the 1.6 cap ✓
  - **18** → 33 at 1×, **41.4** at the cap ✓
  - **20** → 43.4 at the cap ✗
- If 18 looks crowded on the phone, **16 is the fallback**.
- At the brief's peak stretch the marker is 75 × 1.30 = **97.5** wide, inside a 320 phone's 98.7 column.

**The dock's reach** (lift + 54) is the one measure everything else is placed by:
- **66** on the A32, against today's bar at 64;
- **88** on a notched iPhone, against today's 98.

So the deck's room barely changes.

**Home's badge** keeps today's rule: rise 4 above the icon box, 3 back over its right edge. With the content centred in 54, its top is **6.5** inside the dock's top edge at 1× and **2.3** at the 1.6 cap, so it is inside the dock on every text size.

---

## 5. The material (Q2, Q17, Q18, Q19)

- **The glass: 88% white with a strong blur.**
  - The brief's *"about two-thirds"* is overruled by contrast. Idle words must hold 4.5:1 over the darkest thing that can pass under the dock: Home's game card, `night` `#0A3441`.
  - The table uses WCAG 2.1 on the theme's hex values, idle drawn as `ink` at 62% alpha:

  | Glass white | Idle over paper | Idle over `night` |
  | --- | --- | --- |
  | 67% (brief) | ~4.7 ✓ | **3.76** ✗ (3:1 is enough for the icon, not the 9.5pt label) |
  | 85% | ~4.8 ✓ | 4.42 ✗ |
  | **88%** | ~4.8 ✓ | **4.53** ✓ |

  - A fixed `muted` on the 67% glass over `night` is **2.77**. The brief's alpha ink darkens along with the ground, which is why idle stays **`ink` at 62%**, not `muted`.
- **Where the glass is drawn:**
  - **iPhone:** always.
  - **Android:** only if the spike's blur test passes (§10).
  - **Otherwise, Android's dock is opaque `surface`** (Q18), with the same shape, lift, radius, rim, hairline, shadow and marker. A translucent dock without blur was rejected, because sharp text behind the labels shows through. Near-opaque (~95%) was rejected because it needs a new token for almost nothing.
- **The blur's strength and the *"touch more saturation"* are judged on the phone** (§13), not picked here. iOS's materials carry their own saturation; the Android blur has none.
- **The inner rim:** 1pt **`surface`** inside the edge. It shows over dark content and vanishes on the opaque fallback, which is harmless.
- **The outer hairline:** 1pt **`line`**, the border that *bounds a thing*.
- **The shadow:** a new **`shadow.dock`** in the slot `shadow.fab` frees (Q6 retires it), so **the inventory stays at seven**.
  - It borrows **`shadow.deckCard`'s values**: `#0B2B33`, offset 0/7, radius 20, opacity .12, elevation 8. That is the faintest, *floats-least* member.
  - **Android's `elevation` shadow shows through a translucent fill.** If the glass survives on Android, the shadow is drawn with RN 0.76's `boxShadow` instead, and the spike checks that it is clipped outside the dock.
- **The marker sits on the glass and under the icons and labels**, opaque, so it looks the same over anything.

---

## 6. The tabs and the selected state (Q3, Q4, Q6, Q7, Q21, Q26)

| Tab | Idle | Selected |
| --- | --- | --- |
| Home | Ionicons `home-outline`, `ink` .62; label `ink` .62 | `home`, `coral`; label `coralInk` |
| Play | Ionicons **`flash`** (filled in both states), `ink` .62; label `ink` .62 | `flash`, `coral`; label `coralInk` |
| You | Ionicons `person-outline`, `ink` .62; label `ink` .62 | `person`, `coral`; label `coralInk` |

- **Every glyph name is typed against Ionicons' `glyphMap`**, as today against Feather's. A missing name is a compile error.
- **Ionicons draws the bar only.** Feather stays everywhere else (Home's header `mail` and `bell`, chevrons, every other icon). Ionicons' outline stroke is finer than Feather's 2/24, so the bar reads a touch lighter than the header beside it. The user accepted that.
- **The marker is opaque `coralSoft`** (`#FDEBE6`, coral at about 11% over white). The brief's *"coral at 13%"* would be `#FCE7E3`, a hair away, and as an *alpha* it would turn murky brown-red over a dark card.
- **The contrast split:**
  - **icon `coral`**: a mark; 3.38:1 on `coralSoft` (computed), clearing 3:1 for a graphical object;
  - **label `coralInk`**: words; 5.11:1 on `coralSoft` (theme). `coral` would be 3.38, failing 4.5:1 for 9.5pt `tag`.
  - Rule C's spirit, and the tab menu's tick already took `coralInk` (#861).
  - Mock 3 draws the label in bright coral. That is illustration.
- **The selected state now has three channels**: the marker, the fill (outline → filled, except Play) and the colour. ADR-0135's *"tone, never shape"* is superseded **for the bar**.
- **The ⚡Play disc retires:** the 30pt `coralInk` disc, the 2pt `coral` ring, the white `zap`, `size.tabBar.bolt` / `ringGap` / `ringStroke`, and `shadow.fab`. Play is an ordinary column. **What pressing Play does is unchanged.**
- **Home's badge stays**: `coralInk`, white digit, today's geometry, spoken on the column's label.
  - The brief's *"the selected tab is the only coloured thing on the dock"* is read as ***the only coloured thing that means "selected"***.
  - §1.2 keeps the two meanings apart by fill: **`coralSoft` = where you are** (the marker, on the bar only) and **`coralInk` = a thing to attend to** (the badge).
- **Press feedback:** the column's icon and label dim to **0.7** while the finger is down, as today. The marker doesn't react to the press; the slide starts at the lift.
- **No haptics** on a tab press (Q26). The marker's landing is the feedback, and the app's one success haptic stays *It's a game!*'s.
- **Accessibility is unchanged:** `accessibilityRole="tab"`, the label, `accessibilityState={{ selected }}`, glyphs hidden from the reader, and the badge spoken on Home's label (ADR-0198: the name is the whole job).

---

## 7. Content under the dock, and what sits above it (Q9, Q15, Q22)

- **The dock floats over the screen**, so §10.1's flex sibling is reversed. **The dock owns no layout**, and every screen inside the tabs draws to the bottom of the phone.
- **A scroller's end padding = reach + 15**, so its last row clears the dock by exactly today's gap above the bar. Rows slide under the glass as they scroll.
- **Everything placed against the bar moves to the reach, each item keeping its own gap:**
  - **The toast and the Undo toast** sit at reach + 9 (`space.sm`), replacing `TAB_BAR_HEIGHT + inset`.
  - **Post a game's button** sits at reach + 15 (the gutter).
  - **The deck's ✕ · i · ✓** sit at reach + 15: the brief's *"fixed clearance"*, and exactly today's 15. The stage fills what's left as today, and #865's least height and scroll still apply.
  - **Pinned CTAs** (`action=`) stay in the layout, and the screen ends at the reach. On those screens content ends at the CTA and doesn't run under the dock.
- **On Android, while the keyboard is up, the dock and its reach stand down** (Q22), the way the chat's bar does.
  - It is not rendered, with no animation away, and it comes back when the keyboard closes.
  - Otherwise a focused field just above the keyboard (Intro, Name, New group, Edit, Post) could sit under the glass, because a floating dock doesn't shrink the scroller.
  - On iPhone nothing changes: the keyboard already covers the dock.

---

## 8. Where the bar is absent (confirmed, unchanged)

- **The chat** stands it down: not rendered, as today (`barStandsDown`), with the bottom inset taken on its own `SafeAreaView`.
- ***It's a game!*** is a full-phone overlay above it, as today.
- **Sheets, popovers, toasts and the launch splash** are drawn above it, as today.
- **Auth, onboarding and the entry screen** are outside the tabs and have no bar.

---

## 9. Selection and navigation (Q13, Q14, Q25)

- **The URL stays the only source of selection** (`tabForPathname`). Selection is never held as state.
- **The marker travels whenever the lit tab changes after the dock is first drawn.** That covers:
  - a tap on the bar;
  - a **landing** that lays down another tab's stack (after a rating pass, or a notice);
  - **a group opened from Home** (`/play/group/{id}`, Q13): it slides Home → Play, and back slides it home;
  - back from any of these.
- **On the dock's first draw, and when it comes back** after the chat or the keyboard, the marker is simply there under the lit tab, with no slide (Q25).
- **Navigating inside a branch never moves it**: a booked game from Home, a group from Play, game details from a group.
- **Tapping the lit tab:** the marker doesn't move, bounce or pulse. Navigation stays as today (Q14):
  - at the tab's start, nothing happens;
  - from deeper in, it **resets to the tab's start**.

---

## 10. The motion (Q10, Q11)

**The cast:** the marker; the tapped tab's icon and label; the tab left. Nothing else on the dock moves.

- **The slide:** **460 ms**, a spring with **damping ratio 0.75**. It starts fast, overshoots by a few points and settles softly.
  - Overshoot is `e^(−ζπ/√(1−ζ²))` of the trip:

  | ζ | one column (A32, 120) | two columns (240) | one column (320 phone, 98.7) |
  | --- | --- | --- | --- |
  | 0.70 | 5.5 | 11 | 4.5 |
  | **0.75** | **3.4** | **6.8** | **2.8** |
  | 0.80 | 1.8 | 3.6 | 1.5 |

  - **Any distance, the same 460 ms.** The far jump moves faster.
- **The stretch follows the marker's motion, not "% of the trip"** (Q10). It widens and flattens as the marker speeds up, and narrows and heightens as it brakes. Keyframes tied to the trip couldn't satisfy both the brief's fixed numbers and its *"the far jump stretches a little more"*, and a retarget would restart the trip and snap the shape.
  - **Calibrated so the brief's frame-by-frame trip (Home → You, two columns) hits its numbers:** about **130% wide × 84% tall** near 35% of the way, **94% × 106%** near 70%, and **100%** at rest.
  - **A one-column trip stretches about half as much** (≈ 115% × 92%, then ≈ 97% × 103%).
  - It is drawn as a `transform: scale` on the marker's own layer, under the icons and labels, so **no word or glyph ever deforms**. The caps go slightly oval at the peak, which is the bubble.
- **Rapid taps:** a tap while the marker travels **retargets it from where it is, at the speed it has**. The shape stays continuous, because it follows the motion. It never finishes the first trip first and never snaps.
- **The colour-in:**
  - The tapped tab's icon goes outline → filled and `ink` .62 → `coral`, and its label `ink` .62 → `coralInk`, over **300 ms**, **starting 140 ms after the slide begins** and ending at 440.
  - It is drawn as **a cross-fade of two stacked layers** (idle and selected), so only opacity moves.
- **The tab left goes idle at once**, at 0 ms.
- **The screen behind changes at 0 ms**, as the brief says: the reset runs on the press (Q12 (a)).
- **Reduce motion:** the marker is simply under the new tab, and the icon and label switch at once. No slide, no stretch, no cross-fade.
- **Per frame, only `transform` and `opacity` move, on the UI thread** (Reanimated). The project's rule, and what keeps the motion independent of the JS thread mounting the new screen.
- **The timings stay as the brief gives them.** They sit with the app's existing beats (`rise` 300, `flyTo` 400, `yesEntrance` 650), and a longer animation doesn't cost more per frame. The risk is the mount, not the length (§11).

**In numbers** (a new token, `motion.tabMarker`; the name is a call, §12):

```
slide        460 ms, spring, damping ratio 0.75
stretch      speed-driven; two-column trip: 1.30 × 0.84 (≈35 %) → 0.94 × 1.06 (≈70 %) → 1
             one-column trip: about half
colourIn     300 ms, starting 140 ms after the slide
outgoing     at once
reduce       no motion: marker and colours are simply there
```

---

## 11. Performance, and the A32 spike (Q2, Q12, Q20)

**A spike on the A32 decides the Android material and checks the slide, before the dock is built.**

- **Harness:** the atrace A/B harness from the 2026-11-24 perf work. JS runs in **production mode** on the debug native build, via the shared-prefs switch; this is the only build that can be made locally.
- **T1 — the blur (A/B, one build):**
  - Run the dock with blur vs the dock without, over (1) a scroll under the dock on Home (the dark game card passing) and (2) the marker's slide.
  - **It passes if the blur adds no frame over 16.7 ms to either.**
  - Pass → Android gets the glass. Fail → Android's dock is opaque `surface` (Q18). iPhone keeps the glass either way.
  - The debug overhead cancels out in an A/B, so the verdict is fair on this build.
- **T2 — the mount during the slide (absolute):**
  - Press Home → You, Home → Play and You → Home: a real tab press, the new screen mounting while the marker travels.
  - **It passes if no frame is over 33 ms during the 460 ms.**
  - **A fail on this build is inconclusive**, because debug native can fail on overhead alone. It is confirmed on a release or preview build that **you** make (builds are human-only by the safety rules).
  - **Only a confirmed fail triggers the named remedy: keep the three tab roots mounted**, so a press mounts nothing. That changes the shell's lay-it-down-fresh model (#227) and is decided then, on that evidence, not now.
- **T3 — only if the glass survives on Android:** `boxShadow` draws the dock's shadow outside it, with no shadow showing through the glass.
- **The blur's strength** is chosen by eye during the spike (§13).

---

## 12. Calls made while writing this log (for you to check)

1. **Token names:**
   - `color.glass` (white at .88) and `color.tabIdle` (`ink` at .62) are new values and live in the theme, since ESLint refuses `rgba()` outside it;
   - `radius.dock` (22, beside `radius.sheet`'s 22, which is top corners only);
   - `size.tabBar.marker` {width 75, height 42}, `size.tabBar.icon` 18, `size.tabBar.lift` 12;
   - `shadow.dock`, `motion.tabMarker`.
   - The names are mine; the values are the answers above.
2. **The colour-in curve is `easeDecel`**, the app's curve for a thing arriving, instead of the brief's *"plain ease"*. A third easing curve would be a new token for one use. Say if you want CSS `ease` instead.
3. **The stretch's calibration** is stated as behaviour (two-column trip hits the brief's keyframes, one-column about half), not as a formula. The build ticket derives the formula, and a test pins the two calibration points.
4. **Spring configuration:** a duration plus damping ratio. If Reanimated 3.16's `withSpring` doesn't take that pair, the build uses the stiffness and damping that give the same settle and overshoot. The table in §10 is the acceptance.
5. **The spec folder** in the repo would be `docs/specs/tab-bar-dock/`, with the brief, this log verbatim, the three mocks renamed `01-dock.png`, `02-home-screen.png`, `03-play-selected.png`, and a README. That mirrors `docs/specs/tab-menu/`.

---

## 13. For you to check on a phone

- **The blur's strength**, on the A32 if the glass survives T1, otherwise on an iPhone. The spike draws two or three strengths over Home's dark game card and a list of white rows, and you pick.
- **The bubble's feel** on a one-column and a two-column trip, and a rapid third tap mid-flight.
- **The 88% glass** over the dark game card. Does it still read as glass?
- **The 18pt Ionicons** beside Home's Feather header icons. If 18 looks crowded, fall back to 16.
- **The label at the largest OS text size**, inside the marker.
- **Home's badge** standing over the new house glyph.
- **The keyboard** on Intro or Name: the dock stands down and comes back.
- **On an iPhone, if one is available:** the dock resting on the safe-area line above the home indicator.

---

## 14. Docs owed — written by the first (docs) ticket, not this session (Q23)

- **ADR-0210 — the tab bar floats as glass, and its selection travels.** One record, covering:
  - **§1.1's exception:** the tab bar is glass (where the spike allows), the one surface that isn't paper;
  - **§1.2's third line:** a `coralSoft` fill is *where you are*, **on the bar only**; `coralInk` fill stays *attend*. The coral list is still six, because the marker *is* the active tab entry;
  - **§10.1 reversed:** the bar floats over the screen and owns no layout. Screens end at the reach; the inset is the lift's;
  - **ADR-0135 superseded for the bar:** Ionicons, selection by marker + shape + tone; Feather stays everywhere else;
  - **the ⚡Play disc retired**, with its ring and `shadow.fab`;
  - **the app's first spring**, and a stretch that follows the motion;
  - **the Android material decided by the spike**, and the named remedy for the mount;
  - **the keyboard stand-down on Android.**
  - **ADR-0135's status line** gets the supersession note; its body is history.
- **`docs/design-system.md`** (changing together with `theme.ts`, per the locked rule):
  - **§1.1** gets the exception's note, and **§1.2** the third line;
  - **§10.1** gets the new structure: the screen ends at the reach, the dock floats, and the chat's stand-down plus Android's keyboard stand-down;
  - **§10.2** is rewritten: geometry, material, Ionicons, the marker, the colours, the badge's position, motion, press;
  - **Part 13:** the marker under reduce motion;
  - **Part 16 rows:** `color.glass`, `color.tabIdle`, `radius.dock`, `size.tabBar.*`, `shadow.dock` (in `fab`'s slot), `motion.tabMarker`, and the motion list's new entry;
  - **Appendix B**, if it names the bar.
- **`frontend_player/.claude/rules/design-system.md`:**
  - the shadow bullet (*"The ⚡Play disc's is the only tinted one"* retires);
  - the coral list's wording (*the tab bar's badge*, and the marker as the active tab).
- **`frontend_player/CLAUDE.md`:**
  - *"Every mark is drawn or is Feather"* becomes Feather, plus Ionicons on the tab bar;
  - *"never animate a layout prop"* stands, and the marker is its example of scale on a contentless layer.
- **`frontend_player/CONTEXT.md`:**
  - **The shell**: one stack, one `TabBar` floating over it;
  - a new **selection marker** entry;
  - **The reset**: unchanged.
  - **Root `CONTEXT.md`**'s *"Home — the first tab of the bottom bar"* stands.
- **`docs/features/shell.md`** (the design record): the dock, the marker, the reach, the keyboard.
- **`docs/features/_shared.md`, `groups.md`, `proposals.md`, `notifications.md`, `administrator.md`, `src/shared/ui/README.md`**, and every other `tab bar|TabBar|bottom tab` mention that describes the bar's look or the flex-sibling layout, get notes in place. Historical ADRs and decision logs aren't rewritten.
- **The spec folder** (§12, call 5).

---

## 15. Delivery (Q24)

- **Branch: `feat/RKTA-10_for_fun_refactor`**, the current one, with no new branch.
- **Order:** after the loading shimmer's #872–#876, which touch the same shell screens (`ShellScreen`'s padding, the toasts), so the two don't race.
- **A slicing that fits the decisions** (yours to cut with `to-tickets`):
  1. **Docs:** ADR-0210, design-system, glossary, the spec folder.
  2. **The A32 spike:** T1–T3, with the blur strength shown to you. It decides Android's material.
  3. **The dock, still:**
     - geometry, material per platform, rim, hairline, shadow;
     - Ionicons, the marker in place, colours, badge, press;
     - the reach, scroller end padding, toasts, Post a game, the deck's clearance, pinned CTAs;
     - Android's keyboard stand-down;
     - the Administrator's bar.
  4. **The motion:** the spring, the stretch, retargeting, colour-in, reduce motion, and no slide on first draw or return.
  5. **The phone walk** (§13), ready-for-human.

---

## 16. Tests the change reaches

From the router map. All under `frontend_player/src/`.

- **The bar's own drawing and arithmetic** (rewritten):
  - `shared/ui/TabBar.test.tsx` (disc, ring, paddings, badge, Feather names);
  - `shared/ui/tabBadgeFit.test.ts` and `tabBarLabelCap.test.ts`: the column becomes (narrowest − 24) ÷ 3, plus the label inside the 75 × 42 marker at the 1.6 cap;
  - `shared/ui/Toast.test.tsx:230` (`TAB_BAR_HEIGHT`);
  - `features/shell/components/shellCopy.test.ts`, `ShellScreen.test.tsx` (insets), `shellTabs.test.ts`, `pushedScreens.test.ts`.
- **Suites that press tabs** find them by `getByLabelText('Home'|'Play'|'You')`, `getByRole('tab', { name, selected })`, or `getAllByRole('tab')` (3, or 0 in the chat). **Keeping role, label and selected state means they keep working.**
  - Shell: `theShell`, `forYou`, `playSegment`, `theExploreGate`.
  - Notifications.
  - Groups: `groupGames`, `groupYoureIn`, `groupPage`, `groupFillIn`, `groupBadges`, `friendsGame`, `newGroup`, `joinGroup`, `groupsList`, `groupInfo`, `groupGamesRoom`, `groupGamesDoor`, `officialGroups`, `hottestGroupsPage`.
  - Proposals: `homeAndBookedGame` (the badge's label), `theFill`, `postAGame`, `liveYesesScreens`, `gamesAndMoneyScreens`, `rescues`, `timeToPay`, `bookedForFunGame`, `forFunDetails`.
  - Payments, player profile, player record, onboarding, auth, blocks, friends, links, rankings and discovery suites.
  - The administrator's own-bar suites.
- **New tests owed:**
  - the marker's place per lit tab;
  - no slide on first draw or return;
  - retargeting;
  - reduce motion;
  - the stretch's two calibration points;
  - the keyboard stand-down;
  - the reach placing the toasts, the deck and Post a game;
  - the end padding.
- The harness's `TestRoot` uses **zero insets** (`test-support/onboardingRouter.tsx:443-447`), so tests see the lift as 12.

---

## 17. Out of scope, or rejected

- **Rejected (in this session):**
  - *"bottom menu"* / *"dock"* as names (Q1);
  - Android translucency without blur, and near-opaque (Q18);
  - blur on Android without a measurement (Q2);
  - 67% and 85% glass, and `muted` for idle (Q17);
  - an alpha coral marker, and a `coral` label (Q3);
  - keeping Feather, MaterialCommunityIcons, and a drawn SVG set (Q4);
  - icons at 20 (Q5);
  - keeping the disc (Q6);
  - dropping Home's badge (Q7);
  - the brief's 10 and 76 (Q8);
  - deformation keyed to % of the trip (Q10);
  - ζ 0.70 and 0.80 (Q11);
  - changing the screen after the marker lands, and keeping tab roots mounted *now* (Q12);
  - a group opened from Home keeping Home lit (Q13);
  - a slide on first draw (Q25);
  - haptics (Q26).
- **Not asked for, and not built:**
  - scroll-to-top on re-tapping a tab;
  - hiding the dock on scroll;
  - a dark mode;
  - iOS keyboard handling (the keyboard covers the dock already);
  - any change to what a tab opens.

---

## Evidence index

| What | Where |
| --- | --- |
| The bar | `frontend_player/src/shared/ui/TabBar.tsx` (`TAB_BAR_TABS` :115, `TAB_BAR_HEIGHT` :135, insets :195, admin bar :243, columns :256–308, a11y :331, styles :371–444) |
| The shell | `features/shell/components/TabShell.tsx:87-125`; `features/shell/domain/shellTabs.ts` (:77 `INSIDE_A_TAB`, :119 `tabForPathname`, :141 `barStandsDown`); `features/shell/components/shellNavigation.ts:95` |
| Placed against the bar | `shared/ui/Toast.tsx:113`; `TabShell.tsx:96`; `FillProvider.tsx:411`; `GroupScreen.tsx:643`; `ShellScreen.tsx:299` |
| The deck | `features/proposals/components/GamesDeck.tsx:722-827`, `DeckStage.tsx:559`, `DeckAnswers.tsx:82-154` |
| Tokens | `src/shared/ui/theme.ts`: colours :37–72, `size.tabBar` :1600–1629, `shadow` :1872–1971, `motion` :1973–2228, `radius`, `space` |
| Locked rules | `docs/design-system.md` §1.1 :105, §1.2 :115, §10.1 :5261, §10.2 :5321; `.claude/rules/design-system.md` |
| Icon family | `docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md`; `node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/glyphmaps/Ionicons.json` |
| Platform | `package.json`; `app.config.ts:70` (`newArchEnabled`); `src/shared/lib/platform/systemBars.android.ts` (no edge to edge) |
| A32 measurements | the 2026-11-24 perf diagnosis (atrace harness, RenderThread 14–18 ms/frame, ~150 ms touch → insert, 204 ms splash frame) |
| Contrast and overshoot figures | computed in this session: WCAG 2.1 relative luminance from the theme's hex values; the spring's overshoot `e^(−ζπ/√(1−ζ²))` |

## Question index

| Q | Settled |
| --- | --- |
| 1 | Name: *tab bar*; the capsule is *the selection marker* |
| 2 | Glass where blur passes an A32 A/B; otherwise Android goes simpler |
| 3 | Marker opaque `coralSoft`; icon `coral`, label `coralInk` |
| 4 | Ionicons for the bar; ADR-0135 superseded for the bar only |
| 5 | Icon 18 (16 fallback) |
| 6 | The ⚡Play disc, ring and `shadow.fab` retire; mock 3 followed |
| 7 | Home's badge stays, `coralInk` |
| 8 | 54 tall, 12 sides, lift max(12, inset), radius 22, marker 75 × 42 |
| 9 | Content runs under; scroller end = reach + 15 |
| 10 | Stretch follows the motion; calibrated to the brief on the two-column trip |
| 11 | 460 ms spring, ζ 0.75; colour-in 300 ms from 140 ms; brief's timings kept |
| 12 | Screen changes at 0 ms; the mount is measured; remedy named (keep roots mounted) |
| 13 | A group opened from Home: the marker slides to Play |
| 14 | Lit-tab tap: marker still; navigation resets from deeper in, as today |
| 15 | Toasts reach + 9; Post a game and the deck reach + 15; CTAs in the layout |
| 16 | The Administrator's bar gets the same dock (two columns), in the same change |
| 17 | 88% white glass; idle `ink` at 62% |
| 18 | Android fallback: opaque `surface` dock |
| 19 | Rim `surface`, hairline `line`, `shadow.dock` in `fab`'s slot (deckCard's values); `boxShadow` if glass on Android |
| 20 | JS-prod mode on debug native; T1 is fair; a T2 fail is confirmed on your build first |
| 21 | Press dims icon and label to 0.7; the marker doesn't react to the press |
| 22 | Android keyboard up: the dock and its reach stand down |
| 23 | One ADR-0210 + Part 16 rows, written by the docs ticket |
| 24 | Branch `feat/RKTA-10_for_fun_refactor`, after the shimmer's #872–#876 |
| 25 | No slide on first draw or return; every later lit-tab change slides |
| 26 | No haptics |
