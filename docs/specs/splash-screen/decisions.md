# Splash screen — decision log

- **Date:** 2026-11-23
- **Source:** `splash_screen.md` (the brief) and `rakieta-splash-sequence.png` (the mock), both in this folder.
- **Status:** every branch settled in a grilling session, Q1–Q21 over three rounds (the third on a launch with no connection), with every "settled unless you object" list confirmed. This file is the input for `to-spec` / `to-tickets`. Nothing has been written to the repo and no issue has been opened.
- **Ground rules:**
  - **The brief leads on design.** Its timeline (times, squash percentages, letter timings, the 10 pt rise and overshoot, the 0.5 s fade) stands as written. This log changes only what the brief could not get right on every screen (§4) and what the repo forced a choice on (§2).
  - **The mock is a sequence of frames, not a timing reference.** It decides layout (what is centred, where the first landing sits). The motion between frames is smooth and physical, as the brief describes.
  - **Departures from accepted rules are recorded, never bent around** (§8).

---

## 1. What it is, in one paragraph

On every cold open, the first thing the player sees is a dark teal field with a faint glow. A single volt ball drops in from above the top edge, bounces three times along the baseline of the word, and comes to rest as the full stop of **Rakieta**. The letters rise in three groups, one group per landing: **Rak · ie · ta**. The finished lockup holds still until 2.6 s, then the whole splash fades over 0.5 s into the first screen, which is already drawn underneath. The splash is drawn, not played from a file. It starts on the first frame the app paints, and startup runs behind it.

---

## 2. What the investigation found

- **The brand rule.** ADR-0187 §8, *"The brand is Raketa, everywhere"*, says *"The mocks' Rakieta is read as Raketa"*. `docs/specs/home-refactor/decisions.md` and `frontend_player/docs/features/auth.md` apply it. The launcher name is **Raketa** (`src/shared/config/appIdentity.ts`).
- **Startup today.** `src/shared/lib/bootstrap/BootstrapGate.tsx` calls `preventAutoHideAsync()` at module scope. It holds the native splash until `bootstrapApp` resolves:
  - The sequence is: reporting → config → focus/online → keychain → **session restore, which asks the server who this is** → install referrer (not awaited) → fonts.
  - The gate renders `null` while bootstrapping and hides the splash on the tree's first layout.
  - The server check's ceiling is the HTTP client's `launch` timeout, **5 s** (`src/shared/lib/http/timeouts.ts`).
- **A launch without a connection today** (`src/features/auth/use-cases/restoreSession.ts`, `docs/features/auth.md` 2026-11-07):
  - The check `/users/me` has the 5 s `launch` budget, no retry, and `networkMode: 'always'`, so it is sent even when the phone says it's offline.
  - If nobody answers, the session is **kept**, and the failure is left in the cache as the entry gate's first answer.
  - The gate (`src/features/onboarding/hooks/useEntryDecision.ts`, `components/EntryUnavailableScreen.tsx`) then shows one of two screens:
    - **"Waiting for a connection"** (amber, no button) when its read is paused because the phone knows it's offline. It resumes by itself and routes on.
    - **"We couldn't pick up where you left off"** (coral, *Try again*, usually already *Trying again…*) when the phone thought it was online.
  - "Online" means reachable, not just "an interface is up" (`src/shared/lib/platform/networkState.ts`, `isInternetReachable`). A captive portal counts as offline once the platform has decided, and an undecided answer counts as online.
  - The token refresh is reactive, on a 401. A launch whose check is answered with a 401 refreshes with the ordinary 15 s `request` budget. `auth.md` lists this as *not covered*.
  - The rule is documented as the **Splash gate** (`frontend_player/CONTEXT.md`) and in `docs/architecture.md` Part 3: *"The splash screen is the gate"*.
- **The native splash today.** No `expo-splash-screen` plugin config exists in `app.config.ts`, so prebuild's defaults apply: a **white** field with Expo's default logo. The Android status bar is opaque **white** (`styles.xml`) and the root layout sets `<StatusBar style="dark" />`. `android/` is prebuild output and is not committed.
- **What the app already has:**
  - Archivo 800 is loaded at startup (`src/shared/lib/bootstrap/fonts.ts`).
  - `ReducedMotionProvider` is mounted in the root layout.
  - Reanimated 3.16 and `react-native-svg` 15.8 are installed.
  - `expo-navigation-bar` is **not** installed.
  - The app is portrait-only, and iOS `supportsTablet: true`.
- **The design system** (`docs/design-system.md`, locked):
  - The only dark screen is *It's a game!*, on `yesGroundCentre`/`yesGroundEdge`, fenced by ADR-0167.
  - The brief's `#0B2B33` is **not** the theme's `night` (`#0A3441`), and `#134652` is not in the theme. Neither is one of the four banned stage colours (`#0B2B36` is close, but it is a different colour).
  - The largest sans role is `yesWord` (32/800), which is fenced. 42/800 is a new role.
- **The brief's horizontal path does not fit a phone.** At 42 pt the lockup (word + 9 + 12) is about 150 pt wide, so the dot's centre sits at about `W/2 + 68`. The first landing, 292 pt left of it, falls at −44 pt on a 360-wide phone, −29 on 390, −18 on 411 (the A32) and −9 on 430. **It is off the left edge on every phone.**
  - The mock draws that landing about 40 pt in from the left edge of a ~390 pt frame.
  - Every sideways distance in the mock is about **0.8×** the brief's table. Every height matches the table (150 / 62 / 16).
- **460 pt above the floor is on screen on tall phones.** The floor is at `H/2 + 14`, so any phone taller than about 880 pt starts with the ball visible. On the A32 (about 411 × 914 pt) it would start 11 pt *below* the top edge.
- **Android Back on the root screen** moves the task to the background (`MainActivity.invokeDefaultOnBackPressed`). Reopening is a resume, not a cold open.
- **The OS launch window cannot be removed.** iOS requires a launch screen, and without one it runs the app letterboxed. Android 12+ always draws a system splash, showing the launcher icon unless told otherwise.

---

## 3. The word

- **Q1 — The wordmark reads Rakieta, on the splash only.** It is seven separate letters, R · a · k · i · e · t · a, in three groups timed to the landings, exactly as the brief has them:
  - **Rak** after the first landing: R 0.42 s, a 0.46 s, k 0.50 s.
  - **ie** after the second: i 1.00 s, e 1.04 s.
  - **ta** after the third: t 1.42 s, a 1.46 s.
- This is a named exception to ADR-0187 §8 (see §9 below). Every other string, the launcher name and the startup failure screen stay **Raketa**. Nothing speaks the splash's word (ADR-0198).

---

## 4. Layout and geometry

All values are in points. **W × H** is the full physical screen.

- **Q6 — The lockup is centred, not the word.** The lockup is the word, the 9 pt gap and the 12 pt dot, as the mock draws it. It is centred horizontally and vertically on the **full physical screen**, status bar included. Where the app's view does not cover a system bar (Android's opaque status bar and three-button navigation bar), the centre is offset by the bars' sizes, so the lockup sits at the screen's centre, not the view's. The glow's centre (42 % down) uses the same coordinates.
- **Q7 — The wordmark is a fixed 42 pt on every phone.** It is Archivo 800 with −1.68 tracking (−4 %) and ignores the phone's text-size setting. Points already absorb pixel density.
- **The floor and the dot.** The letters' vertical midline is at `H/2`, the floor (the dot's centre) is at `H/2 + 14`, and the dot's centre x is 9 + 6 pt right of the last "a"'s right edge.
- **Q4 — The sideways path scales to the screen, the heights do not.**
  - The first landing sits at **10 % of W** from the left edge, as the mock draws it.
  - Every sideways distance in the brief's table is multiplied by one factor, `k = (dotX − 0.10·W) / 292`. That covers 292, 288, 202, 122, 118, 62, 12, 10 and 2, and the impact nudges with them.
  - The heights stay as written: 150, 62 and 16 above the floor, and 2 pt pressed into it.
  - On a 390 phone k ≈ 0.77, which is the mock. The same rule holds on a tablet.
- **Q5 — The ball always starts just above the top edge.** It is fully hidden there, straight above the first landing point, and still takes **0.39 s** to fall to the floor. Taller phones get a slightly faster drop, and on every phone the ball enters within the first frames.
- **Consequence for the spec.** The ball's very first frame needs the dot's position, which needs the word's width. That width cannot wait for a text layout. The seven letters' positions and the word's width should come from Archivo 800's own advances (and kerning) at 42 pt with −1.68 tracking. A test pins those numbers against the font file, the way the repo's fit tests already read the real font (`src/test-support/fontMetrics`). The final position is a pure function of W, H and those constants, and is unit-tested to land **exactly** on the dot.

---

## 5. Colour, type and the handoff

- **Q8 — New tokens, used by the splash and nothing else, with the brief's exact values:**
  - `splashGroundCentre` `#134652`.
  - `splashGroundEdge` `#0B2B33`.
  - a `splashWord` type role (Archivo 800, 42, −1.68).
  - The ball and dot use the theme's `volt` (`#D9F24B`), which matches the brief.

  They are Part 16 rows: the second dark surface beside *It's a game!*, fenced to the splash.
- **The glow** is a radial from `splashGroundCentre` at the centre (horizontally centred, 42 % down) to `splashGroundEdge` at 75 % of the way to the edges and beyond. It is drawn with `react-native-svg`. No new dependency is needed for it.
- **Q16 — The glow fades in over the first fall (0.0 → 0.39 s).** The launch window is flat `#0B2B33`, so fading the glow in reads as a light coming on, not a jump at the handoff. Under reduced motion the glow is simply there.
- **The ball is drawn above the letters.** At the second landing it comes down among "Rak", as the mock shows. The squash keeps the ball's bottom on the floor. There is no trail, glow or shadow.
- **Motion** runs on the UI thread with Reanimated and animates only `transform` and `opacity`. That follows the player app's rule against animating layout props per frame.

---

## 6. Startup and timing

- **Q2 + Q15 — Startup is never held. The drawn splash covers it.**
  - The OS launch window becomes a **plain `#0B2B33` field with no icon** on both platforms (Android 12+ gets a transparent icon). It is set through the `expo-splash-screen` plugin in `app.config.ts`. It is held only until the drawn splash's **first painted frame**, then released. That is the package's one remaining job besides the colour.
  - The drawn splash is mounted above the bootstrap gate, so it paints before startup resolves. Startup runs behind it unchanged in order, minus the "hide the splash" step.
  - The ball starts on the first frame. The letters wait for Archivo, which loads in milliseconds, long before 0.42 s.
- **The fade starts at max(2.6 s, the moment startup has finished and the first screen has laid out).**
  - In the normal case that is exactly 2.6 s, and the app is interactive at 3.1 s.
  - If startup is slow, the finished lockup holds still, with no replay and no extra pause, until the first screen has laid out.
    - Normally that is at most about 5 s, the `launch` timeout, and only on a connection the phone believes in (§7, Q20).
    - The one longer stretch is not new: a check answered with a 401 whose refresh then hangs, which takes the 15 s `request` budget. Today's native splash waits through it too.
  - "Laid out" means the screen is drawn with its own placeholders. It never means its data has arrived.
  - "The first screen" means the entry gate has **answered**: a destination, or one of its two unavailable screens. Its blank *pending* state never counts, because revealing it would be the blank frame the brief forbids.
- **A startup failure is just the first screen.** Bad config ("Raketa could not start") and an unreachable server ("We couldn't pick up where you left off") are drawn underneath and revealed by the same fade.
- **Q17 — The first screen loads its own data under the splash, and nothing more.** The tree mounts under the splash the moment startup finishes, so Home's own requests start about 2 s before the reveal. No other tab is warmed, and the fade never waits for data.

---

## 7. A launch with no connection (Q19–Q21)

**The splash never mentions the network.** No hint, no indicator, and no waiting for a connection. The screen underneath says it.

| Case | Startup finishes | The splash fades into |
|---|---|---|
| **No network at all** (airplane mode, no signal), signed in | almost at once, because the check fails immediately | **"Waiting for a connection"** at 2.6 s. It moves on to Home by itself when the connection returns (Q19) |
| **The phone already reports no internet** (a captive portal, "connected, no internet"), signed in | at once: **the check is not sent** (Q20) | **"Waiting for a connection"** at 2.6 s |
| **A connection the phone believes in that reaches nothing** (zombie Wi-Fi, weak signal, server down), signed in | when the 5 s check gives up | **"We couldn't pick up where you left off"** (*Trying again…*), at about 5 s; the still lockup holds from 2.6 s until then |
| **Signed out**, any connection | at once, with no network needed | **Sign in** at 2.6 s. Signing in reports its own connection error, as today |
| **Connection lost after the check succeeded** | normally | **Home**, with its own offline notes. Its requests resume when the connection returns |

- **Q20 — The launch check is skipped when the phone already knows there is no internet.**
  - "Knows" means `isInternetReachable === false`, the same signal that pauses every other query. An undecided `null` still sends the check.
  - The session is kept, exactly as for an unanswered check. The gate's read is paused, so its answer is "Waiting for a connection", the true sentence.
  - Only a connection the phone believes in can hold the lockup past 2.6 s.
  - This amends auth's launch rule (§9).
- **Q21 — The connection changing during the splash.**
  - If it returns before the fade, the gate has already routed to Home underneath, and the player never sees "Waiting for a connection".
  - If it returns during the 0.5 s fade, the screen underneath may change while half-visible. That is accepted: the fade never waits for the screen to settle.
- **Nothing the splash draws needs the network.** The font and colours are bundled, and the feature-flag file uses the saved copy (ADR-0206).
- **Reduced motion** follows the same table, with 0.9 s in place of 2.6 s.

---

## 8. Behaviour

- **When it plays.** On every cold open of the JavaScript process (a dev reload included). It does not play on fast refresh, on a return from the background, on sign-out, or on a reopen after Android Back on the root screen, which is a resume.
- **Q10 — Opening from a notification or link** still plays the splash. The target screen is drawn underneath.
- **Q11 — No tap-to-skip.** Touches are swallowed until the splash is gone at 3.1 s, not just until the fade starts.
- **Q9 — Reduced motion** means no flight and no bounce. The lockup is in place within about 0.15 s and the glow is there from the start. The fade **begins at 0.9 s** and lasts 0.5 s, so the app is interactive at 1.4 s. The same hold rule applies: max(0.9 s, first screen laid out).
- **Q12 — The system bars match the field.**
  - On Android the status bar and navigation bar are painted `#0B2B33` with light icons during the splash, so they read as the field's edges. They return to today's look (white status bar, dark icons; the system's navigation bar) when the fade starts.
  - On iOS the status bar shows light content during the splash, then dark.
  - The navigation bar needs **`expo-navigation-bar`**, a new Expo module installed with `npx expo install`. It sits behind a new port in `src/shared/lib/platform/`, the tenth.
- **Q13 — Silent.** No sound and no haptics.
- **The splash sits above everything**, including the LOCAL environment badge, toasts and the overlay host. It has no screen-reader announcement (ADR-0198).
- **Portrait only**, which the app already is.

---

## 9. What this changes in the repo's rules (Q18, Q20)

These four accepted rules are amended, not worked around:

1. **ADR-0187 §8, "The brand is Raketa, everywhere".** The splash's drawn wordmark, **Rakieta**, becomes its one exception.
2. **`frontend_player/docs/architecture.md` Part 3 and `frontend_player/CONTEXT.md` "Splash gate".** These said that startup holds the native splash. Now startup is never held: the drawn splash covers it and fades on max(2.6 s, first screen laid out).
3. **`frontend_player/docs/design-system.md` Part 16.** It gains a second dark surface, two fenced colours (`splashGroundCentre`, `splashGroundEdge`) and one fenced type role (`splashWord`). `theme.ts` changes in the same commit.
4. **`frontend_player/docs/features/auth.md`, the launch paragraph (2026-11-07).** It said the check is sent with `networkMode: 'always'`. Now it is still sent that way, **unless the phone already reports no internet**, in which case it is not sent and the session is kept (Q20). `restoreSession.ts`'s doc comment changes with it.

**The first ticket is a docs ticket**, following the pattern of #828 and #845. It contains:
- **ADR-0209**, the drawn splash, amending 0187 §8 and Part 3, and recording the launch check's skip.
- The Part 16 rows.
- A `docs/specs/splash-screen/` folder holding `splash_screen.md`, `rakieta-splash-sequence.png` and this log.

---

## 10. Tests

- **Pure geometry, the hardest tests:** k, the start point, every keyframe's position, and the final position landing **exactly** on the dot. This covers 360, 390, 411 and 430 wide, and a short and a tall phone.
- **The font constants** are pinned against `Archivo_800ExtraBold.ttf`.
- **The splash component** is tested with fake timers:
  - The letter groups appear at their landings.
  - The fade starts at 2.6 s when startup is done, holds when it isn't, and runs at 0.9 s under reduced motion.
  - Touches are swallowed until the splash is gone.
  - The fade starts only once the entry gate has answered, never while it is pending.
- **No connection** (§7):
  - With `isInternetReachable === false`, the launch check is not sent, the session is kept, and the splash fades at 2.6 s into "Waiting for a connection".
  - With `null`, the check is sent.
  - On a believed connection that never answers, the lockup holds until the 5 s timeout and fades into "We couldn't pick up where you left off".
  - Signed out and offline, it fades at 2.6 s into Sign in.
- **Router tests** start past the splash, so no suite waits 3.1 s.
- **Visual checks.** The motion can't be confirmed in tests. It needs a look on the A32 and an iPhone.

---

## 11. Delivery

- **Q14 — Branch:** `feat/RKTA-10_for_fun_refactor`, the current branch, next to the Fill in / You're in work already on it.
- **App:** `frontend_player/` only, plus the repo-level ADR and spec folder from the docs ticket. There is no backend change and no contract change.
- **Next:** `to-spec` → `to-tickets` → `implement`, by the user.
