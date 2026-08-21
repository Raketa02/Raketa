# The result conversation — throwaway prototype

Issue [#24](https://github.com/Raketa02/Raketa/issues/24). **Throwaway. Never merged to
`main`.** Lives on `prototype/result-confirmation` as the primary source behind that
ticket's resolution, exactly as `prototype/now-native-kit` does for #11.

## Run it

```bash
cd frontend_player
EXPO_PUBLIC_ENV=local EXPO_PUBLIC_API_URL=http://localhost:8000 npx expo start --ios
```

No `.env`, no backend, no sign-in: the prototype is mounted directly in
`src/app/_layout.tsx` in place of `<Slot />`, because the real route tree sits behind
`(app)/_layout.tsx`, which redirects to `/sign-in`. That one-line swap is the only edit
outside this directory.

The floating bar flips **variant** (`A · B · C`), **screen**
(`enter · asked · waiting · counter · unscored`), **sport** (`padel · squash`) and
**width** (`device · 320 · 375 · 393 · 430`). It is deliberately ugly so it never reads as
part of the design being judged.

## The question

[ADR-0048](../../../../docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)
settled the rules and deliberately declined to settle the screens. With no chat, **three
interactions are the entire conversation between four people who disagree about what
happened**. Where does that conversation live?

The three variants disagree about exactly that, and about nothing else — they share the
entry instrument (`ScoreGrid`) on purpose, because how a number is typed is not the
question.

| | Where the conversation happens | Ships |
|---|---|---|
| **A** | **in the card** — the Now state card grows a second action and opens the pad inside itself | nothing new |
| **B** | **a sheet over Now** — the card is a prompt, the sheet is the room | one modal surface |
| **C** | **a result screen** — a route; the card is a tap target | a route |

Each variant's file opens with its own argument and its own cost. Read those first; they
are the thing to disagree with.

## What was already visible from building it

Recorded here so the discussion starts above them, not at them.

1. **`6-4 3-6 6-2` is not a score.** The specification set hardcodes that string in every
   document and never says whose 6 it is. In a doubles match with four people and two
   sides, an unlabelled string is unusable — so every screen here names both sides, and
   the grid's top row is always the viewer's. This is a **wire-contract consequence**: the
   `facts` payload has to carry a score per side, not a display string.
2. **The state card's action row has one action, and `confirmResult` needs two.**
   `UI` §B6.3's `[GAP]` — `cta`/`left` read and never written — is precisely the hole this
   flow falls into. A spends the `⌘` slot the `post` flag already frees; B and C move the
   second action off the card entirely. This is the clearest structural cost of A.
3. **The pad does not survive badminton.** 0–7 is ten keys and two rows; squash's 0–11 is
   fourteen; badminton's 0–21 is twenty-four keys and four rows, which is a different
   instrument, not a wider one. Flip `sport` to see the two that do work, then decide
   whether badminton gets a `padTo` of 11 plus the `+` key or something else entirely.
4. **Nothing in the flow can say "no".** A counter carries a score (§3), so a side that
   believes the match was abandoned rather than played has no move except silence — which
   costs another 24 hours and lands on `playedNoScore` anyway. That may be correct; it is
   not stated anywhere.
5. **Silence favours whoever typed first**, and the two audience renderings make it
   visible: the same fact reads as *"this stands unless you act"* to one side and *"this
   stands unless they act"* to the other. Whether the asked side's screen should say that
   as loudly as it does here is the main thing to react to.

## Marked in the code

Every value `theme.ts` cannot express is a literal with a `MISSING TOKEN:` comment beside
it, and each file carries a scoped `eslint-disable` saying so — the rule is right, and the
literals are the finding. `grep -rn "MISSING TOKEN" .` is the list. It is #11's list plus
one new role: **the score has no display figure.** `theme.num.m/l/xl` are IBM Plex Mono
sizes chosen for balances and levels; a set score is the one figure on this screen a player
reads from arm's length in a dark corridor.
