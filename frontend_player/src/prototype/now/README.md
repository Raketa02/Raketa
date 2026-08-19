# Now on the locked native kit — throwaway prototype

Issue [#11](https://github.com/Raketa02/Raketa/issues/11). **Throwaway. Never merged to
`main`.** Lives on `prototype/now-native-kit` as the primary source behind that ticket's
resolution.

## Run it

```bash
cd frontend_player
EXPO_PUBLIC_ENV=local EXPO_PUBLIC_API_URL=http://localhost:8000 npx expo start --ios
```

No `.env` file, no backend, no sign-in: the prototype is mounted directly in
`src/app/_layout.tsx` in place of `<Slot />`, because the real Now route sits behind
`(app)/_layout.tsx`, which redirects to `/sign-in`. That one-line swap is the only edit
outside this directory.

The floating bar at the bottom flips **width** (`device · 320 · 375 · 393 · 430`),
**strip geometry** (`bleed · ratio · inset`) and **overlay** (`off · touch · a11y fix`),
and prints the live geometry. It is deliberately ugly so it never reads as part of the
design being judged.

## What it is for

The UI specification is final. It was measured on a 392×788 web prototype. This builds the
screen on the real kit and records where the application does not fit. Six enrolled-match
contexts, with copy taken verbatim from the v37 `ST` table so the card is measured against
real strings — `heldSoft` (five fact lines, a Court value that wraps), `replacement` (the
alert), `waitlisted` (the `idle` tone), `cancelledClub`, `ready` (two lines) and
`completed` (the `post` variant that drops the `⌘` button).

## The three strip geometries, and why there are three

The ticket asks _"268 leaves no peek at 320pt, what is the ratio?"_. That question is
asked about `.mrail`, and UI spec §D5 says in as many words that **Now does not use
`.mrail`**. Now's strip is `.hstrip`, whose child is `flex: 0 0 100%` of the content box
with the strip bled to the frame edge.

| Knob    | Card width           | Peek at 320 | Peek at 430 | Source                                                    |
| ------- | -------------------- | ----------- | ----------- | --------------------------------------------------------- |
| `bleed` | content width        | **5pt**     | **5pt**     | v37 `.hstrip`                                             |
| `ratio` | 0.74 × content width | 65pt        | 94pt        | ADR-0012 `size.railCardRatio` — the _match rail's_ number |
| `inset` | content width        | 0           | 0           | the naive translation                                     |

So the peek is `gutter − gap` = 15 − 10 = **5pt, at every width**. It is not a ratio and it
does not depend on the card width at all. `size.railCardRatio` is correct for the component
it was written for and wrong for this one.

## Marked in the code

Every value the current `theme.ts` cannot express is written as a literal with a
`MISSING TOKEN:` comment beside it. `grep -rn "MISSING TOKEN\|MISSING FAMILY" .` is the
answer to the ticket's question 5.
