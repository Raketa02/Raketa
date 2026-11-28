# The A32 spike: does the dock's glass cost frames, and does the slide hold while a tab mounts?

**Ticket [#880](https://github.com/Rakieta02/Rakieta/issues/880), measured 2026-11-25** on the
product owner's Samsung Galaxy A32 5G. It completes
[ADR-0210](../../adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md) §7.

| Test | Pass mark | Debug native, JS in production mode | Release | Verdict |
| --- | --- | --- | --- | --- |
| **T1, the blur** | the blur adds no frame over 16.7 ms to a scroll or to the slide | **fails**: You's scroll 17 → 26 frames over 16.7 ms | **fails**: You's scroll 6 → 16; the slide 19 → 28 | **Android draws no glass.** Its dock is opaque `surface` |
| **T2, the mount during the slide** | no frame over 33 ms in the 460 ms | **fails**: 16 of 16 slides, blur off | **fails**: 14 of 16, blur off, up to 176 ms on Home → Play | **A confirmed fail.** The named remedy is [#886](https://github.com/Rakieta02/Rakieta/issues/886), not built |
| **T3, the shadow** | `boxShadow` is clipped outside the dock, and nothing shows through the glass | passes | not run (a drawing check, not a timing one) | Passes, but moot on Android now, which draws no glass |
| **The blur's strength** | the product owner picks one | rendered at intensities 20, 60 and 100 | | **100** is recorded, for the iPhone. It was not seen on an iPhone (see below) |

The numbers below are the whole record. No code from the prototype lands on the feature branch.

## What was measured

### The prototype

- **A throwaway branch**, `spike/880-dock-glass`, cut from `b2eb2395` in its own worktree. It was
  kept local, never pushed and never merged.
  - `expo-blur ~14.0.3` was installed there only, through `npx expo install`.
  - The tab bar was replaced by a prototype dock: 54 tall, 12 in from each side, lifted 12, radius
    22, a 1 pt `line` hairline and a 1 pt `surface` rim.
  - **Glass on:** `color.glass` (white at .88) over `BlurView` with
    `experimentalBlurMethod="dimezisBlurView"`, `tint="light"` and `blurReductionFactor` 4.
  - **Glass off:** opaque `surface`, the Android fallback.
- **The dock floated over the screens**, as the shell will after #881. Without #881's reach, a
  screen's foot ran under it: on You, the `ink` *Sign out* button sat under the dock.
- **The marker** was a 75 × 42 `coralSoft` capsule, moved by `withSpring(x, { duration: 460,
  dampingRatio: 0.75 })`.
  - Translate and scale only, on the UI thread.
  - A stretch from its speed, and a cross-fade colour-in of 300 ms starting 140 ms after the slide.
  - **It set off on the press, before the navigation**, as ADR-0210 §8 has the screen change at
    0 ms.
- **A runtime switch for every arm** (blur on or off, navigation on or off, strength, shadow), so
  each A/B ran in one build.
  - Debug: set over the debugger.
  - Release: set through a panel that a long press on a tab opens.

### The builds

Both were made locally and installed beside the player's own apps, under their own ids.

| Build | How | App id |
| --- | --- | --- |
| **Debug native, JS in production mode** (the build #880 names) | `gradlew assembleDebug`. The shared-prefs switch (`js_dev_mode_debug=false`, `js_minify_debug=true`, `hot_module_replacement=false`) and Metro on :8083 | `com.rakieta.player.spike` |
| **Release** | `gradlew assembleRelease`, arm64-v8a, signed with the debug key, from a short-path worktree. 14 min | `com.rakieta.player.spike.rel` |

**A release build is possible locally now.** ADR-0210's Context says it isn't, because of Windows'
path length. That was true until a checkout at a short path (`C:\rs`) built one. So T2's
confirming build is this one, and the product owner agreed to treat it as the confirmation on
2026-11-25.

**The phone:** Galaxy A32 5G (`SM-A326B`), Android 13, 720 × 1600 at 60 Hz, density 1.875. It ran
with no bottom inset, so the lift was 12. The API was the local Docker backend over `adb reverse`,
signed in as the populated seed player.

### The harness

- **The tool:** `atrace -a <app> -b 32000 gfx view input` around each gesture, read with
  `adb exec-out atrace --async_stop -z`.
  - A frame is the main thread's `Choreographer#doFrame <vsync>` joined to the RenderThread's
    `DrawFrames <vsync>`.
  - The 2026-11-24 performance work's method.
- **A frame over 16.7 ms** is one that held the screen for more than one vsync: the gap to the
  next frame's start is over 25 ms. *Skipped vsyncs* sums each such gap's lost vsyncs.
  - **A frame over 33 ms** held the screen for three vsyncs or more (a gap over 41.7 ms).
  - Frames start on the vsync, so a gap is a whole number of 16.7 ms steps.
- **Windows:**
  - A scroll is counted from its first touch to its last frame. A gap over 150 ms is the scroll
    having stopped, and is set aside.
  - A slide is the **460 ms from the first frame after the finger lifts**, the lift being the
    press's last `deliverInputEvent`. The wait from the lift to that frame is reported apart as
    *latency*: nothing on screen moves in it.
- **The order:** every A/B was interleaved, on then off, then off then on, with the same
  gesture on the same screen.
- **A warm-up first:** release builds compile shaders on a screen's first visit after an install,
  so every screen and both arms were run once before the release measurements.
- **Discarded:** a first debug A/B whose blur switch reached the screen only at each capture's
  first touch. That mounted or unmounted the blur inside the measured frames. All debug numbers
  here are from the re-run, where a tap on inert text applied the switch before each capture.

## T1 — the blur

**The ticket's scroll couldn't be run as written.** For the populated seed player, Home doesn't
scroll once the dock floats: its content ends above the dock. Its dark game card sits at the top
of the page (its foot at y 797 px; the dock's top is at 1388), so it never passes under the dock.
The scroll ran on the two long tabs instead:
- **You:** rows with icons, the `ink` *Show me to new people* switch and the `ink` *Sign out*
  button pass under the dock;
- **Play:** a list of white group rows.

**The gesture:** a fling up (900 px in 250 ms) and straight back, six runs an arm.

**The slide** ran with navigation off, so the marker travelled with no screen changing behind it.
The presses were You, Home, Play and Home: four slides a run, five runs an arm.

| Surface | Arm | Windows | Frames drawn | **Frames over 16.7 ms** | Skipped vsyncs | Windows with a frame over 33 ms | Longest frame (ms) | UI thread, median frame (ms) | UI frames over 16.7 ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| You, debug | blur off | 6 | 434 | **17** | 23 | 3/6 | 59.1 | 6.3 | 35 |
| You, debug | blur on | 6 | 366 | **26** | 34 | 5/6 | 59.1 | 13.1 | 55 |
| Play, debug | blur off | 6 | 353 | **14** | 54 | 6/6 | 133.4 | 2.3 | 11 |
| Play, debug | blur on | 6 | 319 | **15** | 44 | 6/6 | 148.0 | 8.0 | 13 |
| Slide, debug | blur off | 20 | 481 | **40** | 92 | 20/20 | 102.0 | 14.7 | 122 |
| Slide, debug | blur on | 20 | 494 | **43** | 81 | 17/20 | 113.9 | 13.8 | 94 |
| You, release | blur off | 6 | 442 | **6** | 8 | 2/6 | 50.9 | 7.7 | 10 |
| You, release | blur on | 6 | 376 | **16** | 18 | 2/6 | 43.7 | 8.4 | 40 |
| Play, release | blur off | 6 | 325 | **12** | 46 | 5/6 | 148.4 | 1.9 | 9 |
| Play, release | blur on | 6 | 317 | **12** | 32 | 3/6 | 147.8 | 5.6 | 10 |
| Slide, release | blur off | 20 | 553 | **19** | 22 | 3/20 | 50.6 | 5.4 | 37 |
| Slide, release | blur on | 20 | 556 | **28** | 30 | 2/20 | 46.7 | 12.2 | 111 |

**Frames over 16.7 ms, run by run:**
- **You, release:** every run with the blur had more of them than every run without it. Without:
  1, 1, 1, 1, 1, 1. With: 2, 3, 4, 2, 3, 2.
- **You, debug:** without: 3, 4, 2, 5, 2, 1. With: 3, 5, 3, 4, 5, 6.

**What the blur costs.** `dimezisBlurView` redraws everything behind the dock into a bitmap and
blurs it whenever anything under the dock or on it changes.
- That lands on the UI thread: its median frame doubles in four of the six comparisons.
- And on its tail: the release slide had three times as many UI frames over 16.7 ms.
- **Over rows dense with icons and dark controls**, that becomes frames lost.
- **Over Play's plain white rows**, it doesn't.
- **On the debug slide**, Reanimated's interpreted cost dominates both arms, and the difference is
  within the noise.

**Verdict: fail.** The pass mark is *no frame added to either*. The blur adds frames to You's
scroll on both builds, and to the slide on release. **Android's dock is opaque `surface`**, the
same shape, lift, radius, hairline, shadow and marker. The iPhone draws the glass.

## T2 — the slide while the new tab mounts

**What ran:** real presses with navigation on, in the order Home → You, You → Home, Home → Play
and Play → Home. Four runs an arm, so four slides a transition an arm.

**The longest frame in each 460 ms slide (ms):**

| Build | Arm | Home → You | You → Home | Home → Play | Play → Home | Slides with a frame over 33 ms |
| --- | --- | --- | --- | --- | --- | --- |
| Debug | blur off | 57 · 155 · 45 · 254 | 154 · 101 · 88 · 148 | 90 · 266 · 267 · 88 | 82 · 196 · 59 · 115 | **16/16** |
| Debug | blur on | 54 · 36 · 49 · 139 | 71 · 75 · 120 · 88 | 126 · 123 · 128 · 231 | 135 · 90 · 128 · 79 | **15/16** |
| Release | blur off | 160 · 58 · 108 · 136 | 78 · 66 · 63 · 29 | 151 · 176 · 136 · 122 | 41 · 52 · 84 · 89 | **14/16** |
| Release | blur on | 49 · 71 · 97 · 204 | 66 · 91 · 70 · 48 | 40 · 86 · 157 · 179 | 60 · 57 · 91 · 67 | **15/16** |

**Why:** the new tab's views are created on the UI thread, the thread that moves the marker.
- On the release build, Home → Play's worst slide is one 147 ms `Choreographer#doFrame`:
  - 89 ms of `MountItemDispatcher::mountViews preMountItems`;
  - then 42 ms of `mountItems to execute`.
- The marker can't move during it.
- You and Play are laid down fresh on every press (#227), so a press always mounts a tab.
- On release, the presses back to Home cost less.

**The slide also starts late.** On release, the median wait from the lift to the first frame was:
- **104–208 ms** with navigation on, by transition (104–240 with the blur on);
- **about 47 ms** with navigation off.

The marker is set off before the navigation in the same press handler.
- **The UI thread draws nothing until then.** With navigation off, that handler gets the marker
  moving in about 47 ms, so the extra 60–190 ms is the new tab being rendered in JavaScript.
- **Then the mount freezes it mid-flight.** So the player sees the marker wait, then jump.
- **#884 should know this**, whatever the remedy.

**Verdict: a confirmed fail.**
- It failed on the debug build, which was inconclusive alone.
- It failed on the release build, which confirms it.
- The named remedy is to keep the three tab roots mounted, so a press mounts nothing. It is opened
  as [#886](https://github.com/Rakieta02/Rakieta/issues/886), `needs-triage`, and decided there;
  #880 builds nothing.

## T3 — the shadow, with the glass on

T3's place is *only if T1 passes*. It was run anyway, before T1's verdict was in, and is recorded
for #883 and the iPhone.

**How:** the dock's real shadow was drawn with `boxShadow` (`shadow.dock`'s values: `#0B2B33`,
0/7, radius 20, .12), and a loud probe beside it (`rgba(255,0,0,.9)`, same geometry).
- **Inside the dock:** the mean of the glass between the marker and the icons, x 215–280 and
  400–540, y 1398–1478 px.
- **Below the dock:** the paper just under it, y 1491–1503 px.

| Probe | Glass | Inside the dock | Below the dock |
| --- | --- | --- | --- |
| no shadow | 88% | `#FFFEFE` | `#F4F2ED` (paper) |
| `boxShadow`, the real values | 88% | `#FFFEFE` | `#E3E4E0` |
| `boxShadow`, the red probe | 88% | `#FFFEFE` | `#FA7371` |
| no shadow | 50% | `#FDFCFB` | `#F4F2ED` |
| `boxShadow`, the red probe | 50% | `#FDFCFB` | `#FA7371` |
| the red probe on the dock's own 50% fill | 50% | `#FDFCFC` | `#FA7371` |

**Verdict: pass.**
- The shadow draws outside the dock, and nothing shows through the glass, even at 50%.
- See [`spike/shadow_box_shadow.png`](spike/shadow_box_shadow.png): no shadow, the real shadow,
  and the red probe at 50%.

**What #883 should know about `elevation`.** ADR-0210 §6 feared that Android's `elevation`
would show through a translucent fill. On this dock it doesn't.
- **With the glass:** `elevation` 8 drew under the dock (the paper below it `#D2D5D2`, darker
  than `boxShadow`'s), and the inside stayed `#FFFEFE`.
- **Why:** Android's blur paints an opaque, blurred copy of what's behind it across the dock, and
  that copy covers the shadow.
- **With the opaque dock:** the same shadow drew, and the inside stayed `#FFFFFF`.
- **So `shadow.dock`'s `elevation` serves Android's opaque dock as it is.**

## The blur's strength

**Rendered at intensities 20, 60 and 100**, which are Android blur radii 5, 15 and 25 (25 is the
limit). The dock was over Home's dark game card and over Home's white FOR YOU rows.
- The dock never reaches the card on its own (T1), so for these renders only, the prototype lifted
  it over the card.
- [`spike/blur_strength_over_dark_card.png`](spike/blur_strength_over_dark_card.png) and
  [`spike/blur_strength_over_white_rows.png`](spike/blur_strength_over_white_rows.png): top to
  bottom, opaque `surface`, then 20, 60 and 100.

**Under 88% white, the strength barely shows.** The dock's mean over the dark card is:

| Opaque | 20 | 60 | 100 |
| --- | --- | --- | --- |
| `#FFFFFF` | `#FCFCFD` | `#FDFDFD` | `#FEFEFE` |

**What the eye can find:**
- a faint cool shading at the dock's two ends over the card;
- faint grey ghosts of the dock's own idle icons. Android's blur draws the dock's own children
  into the bitmap it blurs, so the icons are blurred into the glass behind themselves. The ghosts
  are plainest at 20 and gone by 100.

**Recorded: intensity 100.**
- The product owner has no iPhone to judge on. Their call was to take the iPhone's value from what
  the A32 shows.
- Of the three, 100 is the cleanest: no ghosts and the smoothest wash. It is also the brief's
  *strong blur*.
- **It hasn't been seen on an iPhone**, where `intensity` drives a different effect. #885 looks at
  it there if an iPhone is available.

## Also learned, for the tickets that build the dock

- **#883:**
  - The glass switch is **off on Android**.
  - `expo-blur`'s view is drawn on the iPhone only, so Android carries the dependency without
    rendering it.
  - The Android dock's shadow is `shadow.dock`'s `elevation`, which draws as it is (T3).
- **#884, the spring:** `withSpring` in Reanimated 3.16 takes `{ duration: 460, dampingRatio:
  0.75 }`. It type-checks and ran on the phone, so the PRD's fallback (stiffness and damping) isn't
  needed. The overshoot wasn't measured here; #884's tests pin it.
- **#884, the slide starts late:** it waits for the JavaScript thread to render the new tab (see
  T2).
- **#885:** T2's re-run on the shipped slide still stands. It shows whether the remedy is still
  needed once the dock and the marker exist.

## Deviations from #880's text

1. **The scroll ran on You and Play, not Home**, because Home doesn't scroll for the seed player
   and its dark card never reaches the dock (T1).
2. **A release build was made locally**, which #880 and ADR-0210 assumed impossible. It confirmed
   T1 and T2, and the product owner accepted it as T2's confirming build.
3. **T3 was run although T1 failed.** It cost one probe sequence, and its result serves the
   iPhone's shadow and #883.
4. **The strength was picked from A32 renders, not on an iPhone**, at the product owner's call.
