# Busy indicator — decision log

- **Date:** 2026-11-21
- **Source:** a grilling session (Q1–Q14) on the request: _a request in flight should show the app working, not a frozen screen — a loading indicator in the button on **Sign in**, **Create account** and the entry screen's **Try again**, and wherever else the player app has the same case._
- **Status:** every branch settled, and **built directly on `feat/RKTA-09_home_refactor`** (2026-11-21) without a spec or tickets, at the product owner's request. What the build learnt or changed is marked **Built:** below; §5 says what is still open.
- **App:** `frontend_player/` only. No backend change, no contract change, no new dependency, no new colour.

---

## 1. The problem, in one paragraph

A busy `Button` (`src/shared/ui/Button.tsx`) blocks presses, swaps its label for a busy word ending in "…" (_Signing in…_, _Trying again…_) and dims to `opacity: .4` — the disabled row's dim. Nothing moves, so a request in flight reads as a frozen screen, and busy and disabled look identical. Separately, the moment **Sign in** or **Create account** succeeds, the sign-in screen unmounts and the app draws blank paper until `GET /users/me` answers — up to 15 s on a first attempt — because the entry gate draws nothing while it is pending (§3.1).

## 2. The indicator (Q1–Q6)

- **Where: in the `Button` primitive** (Q1). Every busy button gets it — about 80 call sites in 69 files — rather than an opt-in on three screens. One rule, and the "other similar cases" are covered by the primitive.
- **What: React Native's `ActivityIndicator`, small, in the label's own ink** (Q2) — `LABEL[variant].color`: white on `primary` / `dark` / `settled` / `onDark`, `ink` on `secondary` / `volt` / `arranging`, `amber` on `waiting`, `mintInk` on `settledSoft`. No token, no dependency. It is the component the app's 23 existing indicators already use. Not a custom animation: that would be a new motion in a shared primitive, and it walks into the Reanimated traps in `frontend_player/CLAUDE.md`.
- **Placement: before the busy word**, where `lead` sits: "◌ Signing in…" (Q3). The word stays the primary signal and the accessible name stays the word (`accessibilityState.busy` is already set). Not spinner-only — that breaks _every state carries a word_ and _the name follows what is drawn_. Not after the idle label — "Sign in ◌" says _Sign in_ while signing in.
- **No dim on busy** (Q4). A busy button keeps its full fill and still takes no press. The 40% dim now means only _disabled / not now_. The spinner is what tells busy from disabled; until now only the word did (design-system ~1288).
- **Reduced motion: it spins anyway** (Q5). It is progress, not decoration; none of the 23 existing indicators branch on reduced motion; and a still spinner is the frozen look again, for exactly the players who asked for less motion. Recorded as the **second named exception**, beside the calculating screen's indicator (design-system ~5222). Part 13 is paused by ADR-0198 in any case.
- **Shown the moment `busy` turns on** (Q6). No delay threshold: the word already swaps at once, so a brief spinner is no worse than a brief word, and a timer in every busy button is the router harness's known trap.

## 3. Where else it applies (Q7–Q13)

### 3.1 Sign in and Create account — no blank screen (Q7)

**The cause.**

- `signIn` (`src/features/auth/use-cases/signIn.ts:30`) logs in, then calls `beginSession` (`src/shared/lib/auth/session.ts:30`), which saves the tokens and flips the status to `authenticated`.
- The `(auth)` guard redirects at once, so the sign-in screen is gone — there is never a frame with an idle button.
- The entry gate needs the account (`GET /users/me`) to choose the destination: naming, social steps, a club's area, Start playing, or the tabs.
- Nothing is cached after a fresh sign-in, because sign-out clears the cache (privacy, `session.ts:78`).
- While the read is out, `(app)/_layout.tsx:157` returns `null` — _"Nothing, not a spinner"_ — so the root's paper shows.
- A launch never shows this: the splash stays up through the same read (`fetchCurrentUserAtLaunch`).

**The decision: read the account before opening the session.**

- **New order:**
  - _Sign in:_ log in → save the tokens → read `/users/me` into the cache through the one definition, `currentUserQuery` → flip the status.
  - _Create account:_ register → log in → save → read → open, all under _Creating account…_.
- **Effect:** the button stays busy, and spinning, through the whole wait. When the status flips, the gate finds the account cached and redirects at once.
- **`beginSession` splits in two** — save, then open (names for the spec). Tokens are still written before the status flips, which is the order `session.ts` insists on.
- **Precedent:** `useNamePlayer` and `useAttestAdult` already await `fetchQuery(currentUserQuery())` before their caller navigates (`src/features/auth/hooks/useAuthActions.ts:135`, `:174`).
- **If the read fails after the password was accepted:**
  - The session opens anyway and the failure stays in the cache, so the gate opens on _We couldn't pick up where you left off_ with **Try again**.
  - That is the same path a launch takes when its read fails.
  - Never an error on the sign-in form: the password was right.
- **No spinner on what is left of the pending frame.** For an account that runs a club, that is a local last-profile read of a few milliseconds; a spinner there would only flicker. `(app)/_layout.tsx:157`'s rule stays.
- **Unchanged:** register succeeds and login fails → the error on the form, the account exists (`signUp.ts:28-32`).
- **Built:**
  - **All four session openers, not two.** _Set your password_ (an invitation) and _Set a new password_ (a reset) open a session the same way, so they had the same blank gap. They take the same read.
  - **No split.** `beginSession(tokens, readFirst?)` takes the read as an optional second argument and runs it between saving and opening, so the order stays inside `shared/lib/auth`. The launch helpers and the tests that open a session with nothing to read pass none.
  - **The read** is `fetchCurrentUserAtSessionStart` (`src/features/auth/hooks/useCurrentUser.ts`): the one `currentUserQuery`, with the `request` timeout, no retry, `networkMode: 'always'` and `staleTime: 0`.
  - **A read that ended the session itself** (a refused refresh clears the credentials) is not opened over. The error goes back to the form.

### 3.2 Try again on the entry screen

- **Covered by §2.** `EntryUnavailableScreen`'s button is a `Button` with `busy={reason.trying}`.
- `trying` is `user.isFetching` (`src/features/onboarding/hooks/useEntryDecision.ts:151`). It is true through the automatic retries and their backoff, so the spinner runs for an attempt the player pressed and for one the app made.
- A pressed **Try again** can stay busy for about 48 s on a dead server.

### 3.3 The booking after the Undo countdown (Q8)

- **Today:**
  - At zero, `FillProvider` drops the toast and calls `sendYes` (`src/features/proposals/components/FillProvider.tsx:288-305`).
  - `TakeTheSeat` (`:54`, `:74-75`) and `GameDetailsScreen` (`:226-230`) are busy only while counting.
  - So **Pay … zł** / **Yes** look pressable again while the booking — money — is on its way.
- **Decision:** they stay busy — _Booking…_ (`FILL_COPY.undo.booking`), with the spinner — until the booking answers. The in-flight send has to be readable from the Fill context: which card is being sent.
- **Built:** the booked yes sends under its own mutation key, `proposalKeys.bookingYeses()`, nested under `answers()` so the deck still counts it as an answer on its way. `useBookingsOnTheirWay` reads the pending sends off the mutation cache, and `useFillYes().sending(id)` hands them to the two buttons. It reads the cache rather than the host's one mutation result because a second booking can count and send while a slow first one is still out.
- **Not changed:** the optimistic writes whose screen changes at once:
  - deck answers;
  - settings switches, segments, steppers and chips;
  - join-request rows;
  - chat send;
  - the round friend button;
  - Hottest groups chips.

### 3.4 Busy buttons with no busy word (Q9)

- **Spinner before their own unchanged label** — "◌ Withdraw". No new copy.
- With §2's no-dim, the spinner alone is what keeps them from reading as disabled.
- **Sites:**
  - `GroupActionControl.tsx:31-38`;
  - the answer columns — `PlayIntentsSection.tsx:186-199`, `DeclarationInterstitial.tsx:113-127`, `KindDoor.tsx:83-92`;
  - `YoureInRow.tsx:71-77`;
  - `BookedGameScreen.tsx:393-406`;
  - `FriendRequestsSection.tsx:193`;
  - `LevelAsksSection.tsx:193`;
  - `FriendsGameSection.tsx:304`;
  - `GameDetailsScreen.tsx:329`, `:342`, and `:318-319` outside the countdown.

### 3.5 The "…" stays (Q10)

Busy words keep their ellipsis: it is the written form of _in progress_ and reads well beside a spinner. No change to about 75 copy strings and their tests.

### 3.6 The chip (Q11)

- **`Chip`'s busy gets the same treatment:** a spinner before the busy word, and no dim.
- The design system defines a busy chip as _"6.1's busy, whole"_ (~1288); that stays true only if the chip moves with the button.
- **One site:** _add a sport_ on the Skill passport (`SkillPassportScreen.tsx:158-167`).

### 3.7 The two text links (Q12)

- **_Remove this method_** on Payments (`PaymentsScreen.tsx:155-158`, `:221-241`) and **_Sign out_** on Start playing (`StartPlayingScreen.tsx:111-114`, an `AuthLink`) get a spinner before their busy word.
- **_Sign out_ is blocked while busy.** Today it swaps its word but still takes a second press — a bug either way.

### 3.8 The leave-rating sheet (Q13)

- **Unchanged.** Pressing the _Stop rating_ card turns the sheet's **Keep answering** button into _Leaving…_ (`LeaveAssessmentSheet.tsx:107-110`), and that button now spins.
- The cards get no busy state.

### 3.9 Unchanged, by default (raised and not objected to)

- **Controls shut because another is busy** stay as they are: the other payment-setup chips (`SetupChecklist.tsx:154-160`), form fields at `editable={false}` (design-system 6.13's busy shape), tick boxes, the leave sheet's cards. The spinner goes only on the control whose request is out.
- **An intrinsic-width button** — a row's **+ Add** or **Accept** pill — grows when busy, as it already does when its label swaps.
- **The rest of the app's motion and loading** keeps its own drawing: page and section reads (the 23 `ActivityIndicator`s, `RefreshControl`), the calculating screen, _Finding games_, the photo upload bar, the Undo ring and the typing pulse.

## 4. Docs that change with the code

- **`frontend_player/docs/design-system.md`:**
  - **6.1** — a busy paragraph (the indicator, its ink, its place, no dim) and a `busy` row in the table beside `disabled`.
  - **6.x chip** (~1288) — _"the pill dims to the same `opacity: .4`"_ becomes the spinner and no dim.
  - **1.5's list of motion** (~217-227) — the busy indicator joins it.
  - **The reduced-motion exception**, beside the calculating screen's (~5222).
  - **A dated Part 16 row.**
  - **~5978** — _"the cross-fade's length against the busy dim it follows"_: the arrival at `settled` (_Saving…_ → _Saved_) now fades from a full fill, not a dimmed one.
- **The `Button.tsx` and `Chip.tsx` module notes.**
- **`frontend_player/docs/features/`:**
  - `auth.md` — sign-in and sign-up stay busy through the account read, with no blank frame (~336).
  - `onboarding.md` — the entry gate after a fresh sign-in.
  - `proposals.md` — the booking stays busy through the send.
- **Built:** `auth.md` gained two paragraphs at its end: the account read before the session opens, and _Sign out_'s busy link. `proposals.md` gained one, on the booking. `onboarding.md` was left alone, because the gate's own rules did not change: it simply finds the account cached.
- **`architecture.md` needs nothing:** ~765 already says _"a localized indicator for a localized action"_.

## 5. Left to the spec or the implementation

- **The early account read** — **settled by the build.**
  - It goes out authenticated before the status flips: the http client attaches the bearer from the token manager's credential (`getCredential`, `httpClient.ts:255`), not from the status. `session.test.ts` holds it.
  - A 401 on it runs the rotation as any read's would. If the refresh is refused, `endSession` clears the credentials, `beginSession` does not open over them, and the form shows the error. `session.test.ts` holds that too.
- **Spinner size — still open.** iOS's small indicator is a fixed 20 pt (Android takes a number). It fits the 32 pt `sm` button exactly (20 + 2 × 6 padding) and the 27 pt chip (20 + 2 × 3). Whether it *looks* right needs a device.
- **`lead` and `marks` on a busy button** — **built as derived from Q3** (proposed at the hand-off, not objected to):
  - The spinner takes `lead`'s place (and the dot's) while busy: one glyph before the word, never two. Example: _+ Add friend_ → "◌ Asking…".
  - `marks` are hidden while busy, because they describe the idle state. Example: _Friend ✓ ▾_ → "◌ Removing…".
  - Built the same way on the chip: its sport dot and count step aside while busy. A dot beside _Starting…_ would be a dot without its name.
- **A glossed answer button** (_Competitive / For fun_): built with the spinner before the label on its first line, and the gloss under it.
- **Tests** — **built:**
  - `Button.test.tsx` and `Chip.test.tsx`: no dim on busy, the spinner in the label's ink, hidden from a listener, still turning under reduced motion, and the `lead`/`marks`/dot/count rules.
  - `theFirstRead.test.tsx` (new, through the route tree): at the instant the read arrives, the session is still shut and the button busy and turning; at the instant the session opens, the account is already cached; a failed read still signs in and lands on the entry screen.
  - `session.test.ts`: the order, and both failures.
  - `startPlaying.test.tsx` and `paymentsScreens.test.tsx`: the two links take one press.
  - `theFill.test.tsx` and `rescues.test.tsx`: _Booking…_ through the send, one request.
  - **The router-harness trap that bit:** the harness runs every pending timer on a navigation, so the account entry, unwatched between the read and the gate's mount, was garbage-collected, and the clock moved past its freshness. On a phone that window is milliseconds against a five-minute gc. So the router test asserts the cache *at the opening* instead of counting `/users/me` requests afterwards.
- **A look on a phone — still open.** The change is visual, and nobody has seen it yet.
