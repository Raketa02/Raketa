# ADR-0209 — A drawn splash opens the app, and startup runs behind it

- **Status:** Accepted — **§5 superseded 2026-11-27 by
  [ADR-0211](0211-the-brand-is-rakieta-everywhere.md)** (PRD
  [#889](https://github.com/Rakieta02/Rakieta/issues/889)): the brand is **Rakieta** everywhere, so
  the splash's wordmark is no longer an exception. This line, the amendment below, §5 and the *two
  spellings* consequence keep the old spelling as a quote.
- **Date:** 2026-11-23
- **Amends [ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §8, *"The brand is Raketa, everywhere"***, with one exception: the splash's drawn wordmark reads
  **Rakieta** (§5). The launcher's name and every string stay *Raketa*, and the mocks' *Rakieta*
  is still read as Raketa everywhere else.
- **Amends the player app's [`architecture.md`](../../frontend_player/docs/architecture.md)
  Part 3, *"The splash screen is the gate"***. Startup no longer holds the native splash. A drawn
  splash covers it, startup runs behind it, and the native launch window is released on the drawn
  splash's first layout (§1–§3). The sequence keeps its order and loses only *hide the splash
  screen*. The glossary's *Splash gate* (`frontend_player/CONTEXT.md`) said the same and changes
  with it.
- **Amends the player app's auth feature record
  ([`auth.md`](../../frontend_player/docs/features/auth.md)), its launch paragraph of
  2026-11-07.** The launch check is still sent with `networkMode: 'always'`, **unless the phone
  already reports no internet**. Then it isn't sent and the session is kept (§4).
- **Leaves standing:**
  - [ADR-0013](0013-player-app-runtime-architecture.md)'s session tri-state and its *one ordered
    bootstrap sequence behind the splash screen*. The splash it runs behind is now drawn.
  - The HTTP client's timeout classes: `launch` stays 5 s and `request` 15 s. So does the auth
    record's *not covered*: a launch that starts on an expired access token refreshes on the
    `request` budget.
  - [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md): the splash adds no
    announcement of its own.
  - [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §2's fence
    around *It's a game!*'s dark ground.
- **Does not decide the design.** The motion, the geometry, the two ground colours and the
  `splashWord` type role are the product owner's brief, as amended by the decision log and PRD
  [#852](https://github.com/Rakieta02/Rakieta/issues/852). All of it is kept in
  [`docs/specs/splash-screen/`](../specs/splash-screen/README.md). The colours and the type role
  become [design-system](../../frontend_player/docs/design-system.md) Part 16 rows, fenced to the
  splash, written by the tickets that draw them. They are a second dark surface beside *It's a
  game!*. The Android system bars, and the `expo-navigation-bar` module they need, sit behind a
  new platform port, arriving with the code that needs them under ADR-0013's rule.
- Settles PRD [#852](https://github.com/Rakieta02/Rakieta/issues/852), decided in the splash
  grilling on 2026-11-23 (Q1–Q21, three rounds, the third on a launch with no connection) and
  written by [#853](https://github.com/Rakieta02/Rakieta/issues/853). The decision log is
  [`docs/specs/splash-screen/decisions.md`](../specs/splash-screen/decisions.md), §6, §7 and §9.
  Built by:
  - [#854](https://github.com/Rakieta02/Rakieta/issues/854), the launch gate: the night launch window,
    never held, the fade, the hold and the ground glow;
  - [#855](https://github.com/Rakieta02/Rakieta/issues/855), the lockup;
  - [#856](https://github.com/Rakieta02/Rakieta/issues/856), the ball's motion;
  - [#857](https://github.com/Rakieta02/Rakieta/issues/857), the system bars;
  - [#858](https://github.com/Rakieta02/Rakieta/issues/858), the launch check's skip.

## Context

**Today a launch is a white field with Expo's logo, held for up to five seconds.** The app config
gives the `expo-splash-screen` plugin nothing, so prebuild's defaults apply: a white field with
Expo's default logo. The bootstrap gate pins it at module scope and holds it until the whole
startup sequence has resolved:

> reporting → config → focus and online managers → keychain → **session restore** → install
> referrer (never awaited) → fonts → hide the splash

Session restore asks the server who this is (`/users/me`), on the `launch` timeout class: 5 s, no
retry, and sent even when the phone says it is offline. On a bad connection the player watches a
blank white field with a stranger's logo for those five seconds. Nothing on it says what the app
is.

**The product owner wants the brand on the first frame.** Their brief: on every cold open, a
single volt ball drops in on a dark teal field and bounces three times into the wordmark
**Rakieta**, becoming its full stop. The finished lockup holds until 2.6 s and fades over 0.5 s
into the first screen, *"which is already fully drawn underneath"*. The splash is drawn, not
played from a file, so it begins on the very first frame. And *"it never waits for data and never
stretches to cover slow loading"*.

**The brief meets four facts it doesn't mention:**

- **The OS launch window cannot be removed.** iOS requires a launch screen, and without one it runs
  the app letterboxed. Android 12+ always draws a system splash, showing the launcher icon unless
  told otherwise. Something native is on screen before the first JavaScript frame, whatever is
  decided.
- **Startup sometimes takes longer than 2.6 s.** On a connection the phone believes in but that
  reaches nothing (zombie Wi-Fi, a weak signal, a server that isn't there), the launch check runs
  for its full 5 s.
- **Revealing the app before startup has finished shows a blank frame.** Until the sequence
  resolves, nothing can be drawn underneath, and the entry gate's *pending* state is blank too.
  The brief forbids both.
- **The repo's rules collide with it:** ADR-0187 §8's brand, architecture Part 3's *the splash
  screen is the gate*, and the auth record's launch check sent whatever the network says.

Rejected on the way:

- **Hold the native splash for startup, then play the drawn one.** This keeps Part 3 as it is,
  and **adds 3.1 s to every launch, after a blank wait**. Every launch would show a flat field
  for as long as startup took, and the animation only after it.
- **Cut the launch timeout to fit inside the splash.** A check that gives up before 2.6 s would
  never hold the lockup. But **a slow, working connection would flash the failure screen**, *We
  couldn't pick up where you left off*, to a player whose session would have answered at 3 s.
  The `launch` class is already the shortest, cut on 2026-11-07 from the fifteen-second
  `request` budget the check used to wait out.
- **Stretch or replay the motion while startup finishes.** The brief rules it out: the splash is
  exactly 2.6 s of motion and must never read as a loading screen.
- **Fade at 2.6 s whatever has happened.** It would reveal the blank frame the brief forbids.

## Decision

### 1. The OS launch window is a plain night field, held only until the drawn splash's first layout

The launch window becomes **a plain `#0B2B33` field with no icon** on both platforms. It is set
through the `expo-splash-screen` config plugin in the app config document, and Android 12+ gets a
transparent icon image, a new asset. `#0B2B33` is the drawn splash's edge colour, so the two read
as one field.

The package keeps **two jobs**: that colour, and **one release, on the drawn splash's first
layout**. That is the moment the splash is ready to paint its first frame, and the same moment
today's gate releases on for the tree. Releasing on the first JavaScript render instead could show
one blank frame between the two. Wherever the PRD or the log says *first frame* or *first painted
frame* for this release, it means this layout.

This is a native change. It needs a new build, and an over-the-air update cannot carry it.

### 2. Startup runs behind the splash, and is never held

**The bootstrap gate becomes the launch gate**, the one owner of the launch. On its first render
it:

1. draws the splash;
2. starts the sequence it is handed;
3. releases the launch window on the splash's first layout (§1).

**The sequence keeps its order, minus its final step:** reporting → config → focus and online
managers → keychain → session restore → install referrer (never awaited) → fonts. Nothing hides
a splash any more.

- **When the sequence resolves, the tree mounts underneath the splash**, or the startup failure
  screen does if it rejected. The first screen starts its own requests there, so Home's begin
  about two seconds before it is revealed.
- **Nothing else is warmed**, and nothing the splash does waits for data.
- **The ball needs no font and starts on the first frame.** The letters wait for Archivo 800,
  which loads from the bundle in milliseconds, long before the first letter's cue at 0.42 s.
  **So the splash loads that one face itself, as it starts.** The sequence's own font step stays
  last, behind the session check, and on a slow check that would be seconds after *Rak* is due.
  The sequence's order doesn't change for it; loading a face twice costs nothing.
- **Full motion or reduced motion is decided once, before the first frame**, from the operating
  system's answer, and never switched mid-play. Today's reduced-motion context answers `false`
  until its asynchronous read lands, so the splash takes its answer from a source that already
  knows, never from that provisional `false`.

**The splash sits above everything the root draws**, including the overlay host, the toasts and
the environment badge. **Until it is unmounted, it swallows every touch.**

> **Amended 2026-11-24 — the tree mounts once the motion is still, and the motion waits for its
> face.** Measured on the A32 (system trace of the UI thread, a cold start), the motion stuttered
> twice over. (1) **The tree mounting under the splash froze the ball**: a first screen is hundreds
> of views, and the phone created them on the thread that moves it — a 204 ms frame and a run of
> 20–50 ms ones from 0.9 s in, on a debug build. Keeping the tree out of layout (`display: none`)
> saved nothing, because Fabric creates and inserts a hidden view all the same, so **the tree now
> mounts once the sequence has resolved and the motion is still** (1.78 s; at once under reduced
> motion). The first screen's own requests therefore set out under the still lockup rather than
> under the motion — about 0.2 s before the 2.6 s fade in a release build, and sometimes after it in
> a debug one, where Home may open on its placeholders for a moment; the moment the splash fades is
> unchanged. (2) **"The ball needs no font and starts on the first frame"** held only where the face
> loads in milliseconds: a debug build fetches it from the dev server, about 0.45 s on the A32, and
> the seven letters were set on *Rak*'s cue with the ball in the air. **The motion now starts on the
> first layout when the face is there, and otherwise waits for it** — a frame past its letters being
> set, and never more than 0.6 s (`LAUNCH_CLOCK.faceWait`), after which the ball goes without it as
> before. In a release build nothing visible moves. Frames over 20 ms in the splash's first 2.6 s,
> debug build: 21 → 3–5, the overrun past 16.7 ms 488 → ~100 ms.

> **Amended 2026-11-24, again — the sequence gains a step that warms Home**
> ([PRD #867](https://github.com/Rakieta02/Rakieta/issues/867), the loading shimmer, written by
> [#868](https://github.com/Rakieta02/Rakieta/issues/868); its decision log's §7 and Q18, in
> [`docs/specs/loading-shimmer/`](../specs/loading-shimmer/README.md)). With the tree mounting once
> the motion is still, Home's own reads set out about 0.2 s before the fade, and a cold open often
> faded onto a Home still building itself. **_Nothing else is warmed_ no longer holds for Home's
> reads:**
>
> - **The step.** Right after session restore, which has already cached the account, the sequence
>   starts _warm Home_ and **never awaits it**, as it starts the install referrer. It reads with
>   exactly the query definitions Home's own hooks use (keys, functions and options, Top 10's chain
>   included), so Home finds them in the cache, fresh under the app's 30 s `staleTime`, and asks
>   for nothing twice. The order becomes: reporting → config → focus and online managers → keychain
>   → session restore → **warm Home (never awaited)** → install referrer (never awaited) → fonts.
> - **Only for an account whose entry decision is the tabs.** The entry decision becomes a pure rule
>   over the account, callable outside its hook, so the step and the entry gate always agree. So
>   there is no warm-up for naming, the social steps, a club's area or Start playing. **It is skipped
>   when the phone already knows it is offline**, by §4's rule. **Launch only**: after a sign-in,
>   Home mounts the moment the session opens, and a warm-up would gain nothing.
> - **Who builds it and who starts it.** Each feature offers its Home read's prefetch on its public
>   surface, and **the shell feature, which owns Home, composes them into the warm-up** it offers on
>   its own. **The root layout only starts that warm-up**, as a step of the sequence it hands the
>   launch gate, as it does the other steps, because the shared sequence may not import a feature.
> - **Unchanged:** the splash never waits for it, and the fade rule (§3) stands as written. _Ready_
>   still never means the data has arrived.
> - **Why it is safe where mounting was not.** The freeze came from views created on the thread
>   that moves the ball. Reads create no views. Their responses are parsed on the JavaScript thread,
>   while the ball and the letters move on the UI thread, in worklets. And a cache write that no
>   screen watches commits nothing.
> - **How it is accepted:** with the A32 system trace of a cold start, the one above. Frames over
>   20 ms in the splash's first 2.6 s must not rise above its 3–5 (debug build). Then a look on a
>   release build.

**It plays once per start of the JavaScript process**, a dev reload included. It doesn't play on
a fast refresh, a return from the background, a sign-out, or an Android reopen after Back on the
root screen, which the activity already turns into a resume.

### 3. The fade starts at the later of 2.6 s and the first screen being ready

The fade starts at the later of:

- **2.6 s**, measured from the splash's first frame, or **0.9 s under reduced motion**;
- **the first screen being ready**: the sequence has resolved, the tree has laid out, and **no
  hold stands**.

**A hold** is the one new interface between the tree and the gate. A screen under the splash can
declare itself blank, and while any declaration stands, the fade waits.

- **The entry gate holds while its decision is *pending***, the one blank state after startup. So
  *ready* means the gate has answered: a destination, or one of its two unavailable screens.
- The shared gate never imports a feature to know this.

**"Ready" never means the data has arrived.** The first screen is laid out with its own
placeholders.

**While the fade waits, the finished lockup holds still.** It never replays its motion, and it
shows no spinner and no word about why. **The fade** is the opacity of the whole splash, glow,
word and dot together. It is linear and takes 0.5 s, after which the splash unmounts. A normal
launch is interactive at 3.1 s, or 1.4 s under reduced motion.

- **A startup failure is just the first screen.** Bad configuration (*Rakieta could not start*) is
  drawn underneath and revealed by the same fade, never hidden behind a held splash. So is an
  unanswered launch check (*We couldn't pick up where you left off*).
- **Normally the hold ends a little after 5 s**: the `launch` budget, counted from when the check
  is sent, after the config, the managers and the keychain. It happens only on a connection the
  phone believes in (§4).
- **The one longer stretch is not new.** A check answered with a 401 whose refresh then hangs takes
  the ordinary 15 s `request` budget. The auth record already lists it as *not covered*, and
  today's native splash waits through it too.
- **The fade never waits for the screen to settle.** A connection returning during its 0.5 s may
  change the screen while it is half-visible.

### 4. The launch check is not sent when the phone already reports no internet

Session restore reads the phone's reachability **once, before the check**, from the same source
the online manager uses.

- **"Already reports no internet" is the online manager's own rule:** no connection, or
  reachability known to be false. That is the signal that already pauses every other query.
- **An undecided answer counts as reachable, and so does a read that fails.** Then the check is
  sent exactly as today: the `launch` budget, no retry, `networkMode: 'always'`.

**A check that isn't sent keeps the session**, exactly as an unanswered one does.

- **Nothing is written to the cache.** It is not a synthesised failure.
- So the entry gate's own read is paused, and its answer is *Waiting for a connection*, which moves
  on by itself when the connection returns. That is the true sentence.
- **That pause needs the online manager to agree by the time the gate reads.** The manager's first
  answer is asked for when it is wired, earlier in the sequence, and never awaited. The skip
  doesn't hold if the gate could read before that answer lands. The ticket that builds the skip
  makes sure it can't.
- **The use-case receives reachability as an argument**, as it already receives the read, because
  a use-case may not import the network module.

**The splash itself never mentions the network**: no hint, no indicator, and no waiting for a
connection. The screen underneath says what is true:

| A signed-in launch, or | Startup finishes | The splash fades into |
| --- | --- | --- |
| No network at all, or the phone reports no internet (a captive portal, *connected, no internet*) | at once: the check isn't sent | *Waiting for a connection*, at 2.6 s |
| A connection the phone believes in that reaches nothing | when the 5 s check gives up | *We couldn't pick up where you left off* (*Trying again…*), at about 5 s, the still lockup holding from 2.6 s |
| The connection lost after the check succeeded | normally | Home, with its own offline notes |
| **Signed out**, any connection | at once, with no network needed | Sign in, at 2.6 s. Signing in reports its own connection error |

**Only a connection the phone believes in can hold the lockup past 2.6 s.** Reduced motion follows
the same table, with 0.9 s in place of 2.6 s.

### 5. *Rakieta* is the splash's wordmark, and nothing else's

> **Superseded 2026-11-27 by [ADR-0211](0211-the-brand-is-rakieta-everywhere.md): the brand is
> *Rakieta* everywhere.** The splash's wordmark, the launcher's name, the startup failure screen
> and every string spell it alike. This section keeps the old spelling as a quote, so it reads as it
> was decided.

**Only the splash's drawn wordmark reads *Rakieta*.** It is the one exception to ADR-0187 §8:

- the launcher's display name stays **Raketa**;
- so do the startup failure screen and every other string;
- and the mocks' *Rakieta* is still read as Raketa everywhere else.

**Nothing speaks the splash's word.** It is drawn, not written, and the app adds no announcement
of its own (ADR-0198). So no sentence anywhere names the app *Rakieta*.

## Consequences

**Easier**

- **The first frame says what the app is.** There is no white field and no stranger's logo, and
  the launch reads as one continuous dark field from the tap.
- **A launch hides its own startup.** The sequence, the session check and the first screen's
  requests all run under the motion, so a normal launch never shows a wait.
- **A launch on a phone that knows it is offline is quicker and more honest.** It reaches *Waiting
  for a connection* at 2.6 s, not after a 5 s check that could not succeed.
- **The launch has one owner.** The release, the clock, the hold and the fade are all in the
  launch gate, tested on a fake clock. The router suites mount their own root and never meet it.

**Harder**

- **Every cold open now takes at least 3.1 s to become interactive**, or 1.4 s under reduced
  motion, even when startup finished long before. Today a fast launch is interactive the moment
  startup ends. The brand costs those seconds on every cold open, on purpose, and taps
  during them are swallowed.
- **The bootstrap gate grows from a gate into a clock.** It now owns the launch window's release,
  the splash, the fade and the hold. **The hold is a new interface that any screen could use**: a
  hold that is never released keeps the splash up for good. Today only the entry gate holds, and
  only while *pending*. A second user is a review question, not a lint rule.
- **The brand has two spellings.** *Rakieta* is on the first frame, and *Raketa* is on the
  launcher label the player just tapped and everywhere after. ADR-0187 §8 now has an exception to
  police, and a future rename touches both. *(Resolved 2026-11-27 by
  [ADR-0211](0211-the-brand-is-rakieta-everywhere.md): one spelling, Rakieta, on every frame.)*
- **The design system's one dark screen becomes two.** *It's a game!* gains a sibling in Part 16,
  with two fenced colours and a fenced type role. Each fence is narrow, but the case for a third
  dark surface is easier to make.
- **The still lockup can stand for about 2.4 s with no word**, a little more on a slow keychain, on
  a connection that looks fine and reaches nothing, before *We couldn't pick up where you left
  off*. On the *not covered* 401 path
  it can stand longer. The rule that the splash never mentions the network is what makes that
  silence.
- **The skip trusts the platform's judgement of reachability**, as every paused query already
  does. A phone wrongly reporting no internet now also keeps the launch check from trying, and the
  player waits on *Waiting for a connection* until the platform changes its mind.
- **Two native changes**: the launch window's config, and `expo-navigation-bar` for the bars.
  Neither shows without a fresh build, and iOS caches launch screens, so seeing the new one may
  need a reinstall.
- **The wordmark is placed from font constants, not from a text layout.** Each letter's advance
  and the kerning pairs are read once from Archivo 800 and pinned by a test against the font file.
  A font release that redraws the letters turns that test red, and the constants must be read
  again.
- **The motion's quality can't be tested.** Smoothness, the squash and the overshoot are checked
  by eye on the A32 and an iPhone. The tests prove only where things are and when.
