I want to introduce the splash screen animation when the app is opened. For this I will provide you with the description of the screen and the animation itself that you must follow. Take into account that the size in px I am giving you is orientative so you should infer and calculate the suitable sizes taking into account that the app will obviously run in different screen sizes so it should always feel symmetric and well layout on each screen size.

## 1. What it is

The first thing a player sees when the app opens: a dark screen on which a single volt ball drops in, bounces three times across the middle of the screen and comes to rest as the dot of the word **Rakieta**, the letters appearing with each bounce. It lasts 2.6 seconds, then fades into the first screen (Sign in for a new or signed-out player, Home for a signed-in one). There is no logo image, no tagline, no loading indicator, no sound. One object with real weight, and the brand is literally the ball.

## 2. The screen

- **Canvas.** The splash covers the entire phone screen edge to edge, including the status-bar area. Nothing else is visible under it while it plays.
- **Background.** A deep teal, slightly lighter at its centre than at its edges: a soft radial glow centred horizontally and a little above the middle (about 42 % down the screen), from a dark teal (`#134652`) at the centre to the brand's night colour (`#0B2B33`) at three quarters of the way to the edges and beyond. It should read as one calm dark field with a faint light behind the wordmark, not as a visible spotlight.
- **Wordmark.** The word **Rakieta** in Archivo ExtraBold, 42 px, tight letter-spacing (−4 %), pure white, set on one line and centred both horizontally and vertically on the screen. It is built from seven separate letters — R · a · k · i · e · t · a — because they arrive one at a time.
- **The dot.** A 12 px circle in volt (`#D9F24B`) that belongs to the wordmark: it sits 9 px to the right of the final "a", vertically on the baseline — its centre 14 px below the vertical midline of the letters — like a full stop. It is not drawn as a static dot: the ball of the animation *becomes* it, so its position is simply the ball's resting place. If the dot were drawn statically it would be exactly here.
- **The ball.** The same 12 px volt circle. One ball only; it never leaves a trail, glow or shadow. When it lands it squashes (wider and flatter) and immediately rounds back.
- **Final frame.** White "Rakieta" with the volt dot after it, centred on the dark field — the brand lockup.

All positions below are given relative to the dot's resting place (the point where the ball ends). The wordmark is centred first; everything else follows from it, so the piece works on any screen size as long as the ball starts above the top edge.

## 3. The animation, second by second

The ball is the only thing that moves continuously. Its path is three bounces along an invisible floor that runs along the baseline of the letters, each bounce lower and further right than the last, ending at the dot's resting place. The letters rise into place in three groups, one group per landing. Timings are from the moment the splash appears (0.0 s).

### The ball

| Time | What happens | Where the ball is (relative to its resting place) |
|---|---|---|
| 0.00 s | The ball appears above the top edge of the screen, already falling, full colour. | 292 px to the left, 460 px above (off-screen) |
| 0.00 → 0.39 s | It falls straight down, accelerating like something dropped, not drifting. | straight down to the floor |
| 0.39 s | **First landing.** The ball hits the floor and squashes: 140 % of its width, 65 % of its height, pressed 2 px into the floor and nudged 4 px to the right by the impact. | 292 → 288 px left, on the floor |
| 0.39 → 0.46 s | It rounds back and leaves the floor. | — |
| 0.46 → 0.72 s | **First bounce**, the big one: a high arc up and to the right, slowing towards the top. | peak at 0.72 s: 202 px left, 150 px above the floor |
| 0.72 → 0.98 s | It falls, accelerating, further to the right. | — |
| 0.98 s | **Second landing.** Squash 130 % wide, 72 % tall, 2 px into the floor. | 122 → 118 px left |
| 0.98 → 1.05 s | Rounds back, leaves the floor. | — |
| 1.05 → 1.23 s | **Second bounce**, lower: peak at 1.23 s. | 62 px left, 62 px above the floor |
| 1.23 → 1.40 s | Falls again. | — |
| 1.40 s | **Third landing.** Squash 120 % wide, 80 % tall. | 12 → 10 px left |
| 1.40 → 1.47 s | Rounds back. | — |
| 1.47 → 1.58 s | A last tiny hop, barely a flicker. | peak at 1.58 s: 2 px left, 16 px above the floor |
| 1.58 → 1.68 s | Settles onto the resting place and stops dead. | 0 / 0 — it is now the dot of the wordmark |
| 1.68 → 2.60 s | Everything holds still. | — |

Feel of the motion: every fall accelerates (gravity), every rise decelerates (a thrown ball). The three bounces shrink in a natural ratio — roughly 150 px, 62 px, 16 px high — and each landing's squash is a little gentler than the last. Each bounce also carries the ball to the right, so the whole path reads as one object thrown in from the top-left corner that skips across the screen and comes to rest exactly where the brand needs it. The landings are what make it feel real: the squash is brief (about 0.03 s) and always followed by an immediate return to a perfect circle.

### The letters

Each letter rises from 10 px below its final position to its final position while fading from invisible to fully white, over 0.32 s, with a slight overshoot (it travels a touch past its resting height and settles back) so the arrival feels like a small bounce of its own. Within a group the letters are staggered 0.04 s apart. The groups are timed to the three landings, so each impact "shakes" the next letters up out of the floor:

- **First landing → "Rak":** R at 0.42 s, a at 0.46 s, k at 0.50 s.
- **Second landing → "ie":** i at 1.00 s, e at 1.04 s.
- **Third landing → "ta":** t at 1.42 s, a at 1.46 s.

By 1.78 s the full word is standing still; by 1.68 s the ball is resting beside it. From then until 2.6 s the screen is the finished brand lockup, motionless.

### The exit

At 2.60 s the whole splash — background, word and dot together — fades out over 0.5 s, revealing the first screen of the app, which is already fully drawn underneath (no blank frame, no second loading state). At 3.1 s the splash is gone and the app is interactive. There is no zoom, slide or morph on exit: a plain, even fade, so the lockup simply dissolves into the app.

## 4. Behaviour

- **When it plays.** Once, on every cold open of the app, before the first screen. It does not replay when returning from the background, switching tabs or signing out.
- **Reduced motion.** If the device asks for reduced motion, there is no flight and no bouncing: the wordmark and dot appear in their final positions almost instantly, hold briefly, and the splash fades out at 0.9 s.
- **Nothing loads behind it.** The splash is drawn, not played from a file; it has nothing to download or decode, so it must begin on the very first frame the app shows. It never waits for data and never stretches to cover slow loading — it is exactly 2.6 s plus the fade, every time.
- **Orientation and size.** Portrait only. The wordmark stays centred on any phone; the ball's path is defined relative to the wordmark, so it scales with the layout, and its starting point must always be above the top edge of the screen.

## 5. What must be true at the end

- The ball comes to rest *exactly* on the dot's position: 9 px right of the last "a", on the baseline. If it stops a few pixels off, the lockup looks broken.
- The last frame of the splash is the static brand lockup, pixel for pixel: white Archivo ExtraBold "Rakieta", volt dot after it, centred on the dark teal field.
- Three landings, three letter groups, in sync: Rak · ie · ta.
- Total duration 2.6 s to the start of the fade, 3.1 s to interactive.

This is the mock reference for the sequence of the splash animation so that you can have more details about the design. Take into account that is just a sequence and many frames from the animation are skipped. This is just information for you to show you how the overal splash screen looks like as reference but you must implement the animation smoothly.

->mock reference:

"C:\Users\rober\Desktop\rakieta_features\4.splash_screen\rakieta-splash-sequence.png"
