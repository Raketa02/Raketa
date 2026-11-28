# The drawn splash: the record, its brief and its mock

**What PRD [#852](https://github.com/Rakieta02/Rakieta/issues/852) is drawn from.** On every cold
open, a volt ball bounces three times into the **Rakieta** wordmark and becomes its full stop. The
lockup holds until 2.6 s, then fades over 0.5 s into the first screen, already drawn underneath,
and startup runs behind it. The PRD comes from the product owner's brief, its mock, and the
grilling held on them on 2026-11-23 (Q1–Q21, three rounds, the third on a launch with no
connection). They are copied here from the product owner's own folder, `4.splash_screen`, so every
session can read them. Landed by [#853](https://github.com/Rakieta02/Rakieta/issues/853) on
2026-11-23.

| File | What it holds |
| --- | --- |
| [splash_screen.md](splash_screen.md) | The product owner's brief, verbatim. Its sizes say *px*: read them as points, which already absorb pixel density (the log's Q7). Its last line points at their own folder: read that path by the [index](#index)'s original name |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6), whose notes on the two spellings keep the old one as a quote: every ruling with its reason, the facts it rests on (§2, with `file` paths as of 2026-11-23), and the tests and delivery. Its status line and its delivery section (§11) predate PRD #852. Its §9 puts the design-system Part 16 rows in the first ticket; the tickets moved them to [#854](https://github.com/Rakieta02/Rakieta/issues/854) and [#855](https://github.com/Rakieta02/Rakieta/issues/855), which draw what they fence |
| [`mocks/`](mocks/) | The one mock, renamed for what it shows (the [index](#index) gives its original name) |

**The decision is
[ADR-0209](../../adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)**: the OS
launch window is a plain night field released on the splash's first layout, startup runs behind the
splash and is never held, the fade waits for the first screen but never for data, a launch that
already knows it has no internet doesn't send the launch check, and *Rakieta* is the splash's
wordmark and nothing else's (until [ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) made Rakieta the brand everywhere). Where the brief or the log and ADR-0209 or PRD #852 disagree, ADR-0209
and PRD #852 win. ADR-0209 makes two of them precise:

- **The letters' font.** The log (§6) and the PRD say the letters wait for Archivo 800, *"long before
  the first letter's cue at 0.42 s"*, and that the startup order is unchanged. But that order loads
  the fonts last, behind the session check, which can take seconds. So the splash loads Archivo 800
  itself as it starts, and the sequence's order stays as it is (ADR-0209 §2).
- **The launch check's skip.** The log's Q20 skips the check on `isInternetReachable === false`
  alone, and ADR-0209 §4 uses the online manager's own rule, which also counts *no connection*. So a
  launch with no network at all skips the check too, instead of failing it at once. It lands on the
  same screen at the same moment.

**This folder holds the record, not the spec.** The player app's own docs say how its launch works
today, and the ticket that changes each part amends them: architecture Part 3, the glossary's
*Splash gate* and the agent guide's bootstrap paragraph by #854; design-system Part 16 by #854 (the
two ground colours) and #855 (`splashWord`); the auth record's launch paragraph by
[#858](https://github.com/Rakieta02/Rakieta/issues/858). Until a ticket amends them, they describe
the white native splash held by startup.

## How to read the brief and the mock

1. **The brief leads on design.** Its timeline stands as written: the times, the squash
   percentages, the letter timings, the 10 pt rise and its overshoot, the 0.5 s fade. Only the four
   [overrides](#overrides) below change it.
2. **The mock is a sequence of frames, not a timing reference.** It decides layout: what is
   centred, and where the first landing sits. The motion between its frames is smooth and physical,
   as the brief describes.
3. **The grilling added what the brief doesn't say**, and the log holds each addition: the glow
   fades in over the first fall (Q16); startup runs behind the splash and the lockup holds still
   until the first screen is ready (Q2, Q15, Q17); a launch with no connection (Q19–Q21); the
   Android bars painted the field's colour (Q12); touches swallowed until the splash is gone (Q11).

## Overrides

Each is a ruling of the grilling (its Q in [decisions.md](decisions.md)). The brief is right
everywhere else.

| Note | The brief says | What is built | Why |
| --- | --- | --- | --- |
| 1 | The first landing is **292 pt left** of the dot, and the path's other sideways distances are as its table gives them | **The sideways path is scaled** so the first landing sits at **10 % of the width**: every sideways distance, the impact nudges included, is multiplied by `k = (dotX − 0.10·W) / 292`. The heights stay as written: 150, 62 and 16 pt above the floor, 2 pt pressed into it (Q4) | At 42 pt the lockup is about 150 pt wide, so 292 pt left of the dot is **off-screen on every phone from 360 to 430 pt**: −44 pt on 360, −29 on 390, −18 on 411, −9 on 430. **The mock draws about 0.8× the brief** sideways, and every height as written. On a 390 pt phone *k* ≈ 0.77, which is the mock |
| 2 | The ball starts **460 pt above** its resting place | **The ball starts just above the top edge** on every phone, fully hidden, straight above the first landing, and still takes 0.39 s to fall (Q5) | The floor is at `H/2 + 14`, so 460 pt above it **is on screen on any phone taller than about 880 pt**. On the A32 (about 411 × 914 pt) the ball would start 11 pt below the top edge |
| 3 | **The word** is centred horizontally and vertically, and the dot sits after it | **The word and its dot are centred together**: the word, the 9 pt gap and the 12 pt dot, as one lockup, on the full physical screen (Q6) | **It is the mock's composition.** Centring the word alone pushes the lockup right by half the dot and its gap |
| 4 | The wordmark reads **Rakieta** | **Rakieta is kept**, on the splash's drawn wordmark only. The launcher's name and every string stay *Raketa* (Q1) | The product owner's choice, **against ADR-0187 §8**, *"The brand is Raketa, everywhere"*. It is recorded as that rule's one exception, by ADR-0209 §5, not bent around it. *(Superseded 2026-11-27 by [ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md): the brand is Rakieta everywhere, so the wordmark is no exception.)* |

## Index

| # | File | Original name | What it shows |
| --- | --- | --- | --- |
| 1 | [`01_ball_bounces_into_the_lockup.png`](mocks/01_ball_bounces_into_the_lockup.png) | `rakieta-splash-sequence.png` | 15 frames from 0.00 s to 2.60 s: the ball still above the top edge, its three landings, the peaks of its two bounces and its last hop, *Rak · ie · ta* rising, the ball at rest as the dot, the hold, and the frame the fade begins on |
