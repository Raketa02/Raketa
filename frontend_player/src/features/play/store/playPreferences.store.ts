/**
 * What Play opens on: the **sport** and the **mode**. Process-scoped, and never written back.
 *
 * §J1 remembers both *"so Play opens where they left it"* and AC-19 scopes the mode to *"that
 * session"*. [#261](https://github.com/Raketa02/Raketa/issues/261) removed the navigator as
 * their home — the shell keeps no per-tab history, so a value that used to survive inside a
 * tab's stack now has nowhere to hide.
 *
 * ## In memory, and that is a decision with a reason
 *
 * This app has **no persistence** beyond tokens in the keychain (docs/architecture.md Part 18
 * and Part 21), so the three candidates were: in memory, add a storage dependency now, or
 * persist to the server as part of the profile.
 *
 * **The third was the close one and it loses.** It is nearly free —
 * `GET /players/me/profile` already carries the per-sport Play intent — but it would make the
 * toggle and the declaration one value, and `domain/playMode` is where that argument is
 * written out: ADR-0094's drift backstop exists for the sticky-tab case, and a toggle
 * re-seeded from the declaration agrees with it on every first search. The two values must be
 * able to disagree.
 *
 * So: **seeded once, at the first entry into Play**, from `GET /ratings` for the sport — which
 * the client is already fetching for the chips (AC-6) — and from the declared intent through
 * `modeForIntent`. A relaunch landing on the declared default is correct behaviour, not a lost
 * preference.
 *
 * **There is a second seeding moment and it is one edge wide.** A player entering on a rated
 * but *undeclared* sport is seeded from no declaration, and the answer they give on the
 * interstitial arrives a moment later — so `seedModeOnFirstDeclaration` opens the mode on the
 * transition `undefined -> declared` for the sport on screen
 * ([#292](https://github.com/Raketa02/Raketa/issues/292)). It is an edge and never a value:
 * seeding on the *value* is the re-seed the paragraph above rules out, and the two must stay
 * able to disagree from the moment they are both known.
 *
 * ## Two lifetimes, two stores, and no sync between them
 *
 * This store lives for the **process**. `playSession` beside it lives for the **visit** and is
 * cleared every time the shell lays a stack down. They are two stores because they are two
 * lifetimes, and `profileDraft`'s warning against splitting — *"a sync that can be
 * forgotten"* — does not reach here, because **nothing writes across them**: a line-up is
 * invalid when its origin search was for another sport, which `domain/lineup` derives at read.
 * There is no sync to forget.
 *
 * **One field here keeps the visit's lifetime rather than the process's**, and it is bounded
 * by the screen instead of by the shell: `sportAwaitingDeclaration` is cleared by
 * `forgetAwaitedDeclaration` when *Find a game* opens. It is not moved into `playSession` for
 * this paragraph's own reason — the mode it decides is written here, and reaching across would
 * be the sync neither store has.
 *
 * **The deck writes nothing here.** `SearchEnvelope.mode` is *"null exactly on the deck, which
 * has no mode"*, so the deck genuinely has no mode to remember; §G6 bug #7 — *returning to
 * Find a game does not restore the previous mode* — is fixed by the deck not writing rather
 * than by a second remembered variable. The mode is written by the segment on Find a game and
 * by nothing else ([#228](https://github.com/Raketa02/Raketa/issues/228) §2).
 *
 * Nothing from the backend enters this store. The ratings behind the chips and the profile
 * that carries the declaration are TanStack Query's, and a second copy here would be a second
 * answer to what this player plays.
 *
 * **`sportAwaitingDeclaration` is not the exception it looks like.** It holds no answer of the
 * backend's: a declaration never enters it, and neither does the absence of one — what it
 * records is that *this screen has already been shown* a sport with nothing declared in it,
 * which is a fact about the visit and about nothing the profile could be asked. It is the one
 * thing the edge above cannot derive, because the profile read says the same thing on every
 * render and only the second reading of it is a transition. Read the value instead of the edge
 * and it would be a copy — and the toggle would agree with the declaration forever.
 */

import { create } from 'zustand';

import type { Sport } from '@/shared/vocabulary/sport';

import { MODE_WITHOUT_A_DECLARATION, modeForIntent } from '../domain/playMode';
import type { PlayIntent, SearchMode } from '../domain/vocabulary';

interface PlayPreferencesState {
  /**
   * Undefined until Play has been entered once. Absence is *"nothing has been seeded yet"*,
   * which is what makes `seedIfAbsent` safe — the same shape `onboardingPass` uses between
   * walks.
   */
  readonly sport: Sport | undefined;
  readonly mode: SearchMode;
  /**
   * The sport this process has been shown **without** a declaration — and nothing more about
   * it than that.
   *
   * It is the one thing `seedModeOnFirstDeclaration` cannot derive: *first* is a statement
   * about what came before, and the screen re-reads the same profile on every render. It is
   * **not** a copy of the declaration and cannot become one — a sport is here only while it
   * is undeclared, and what leaves the slot is the arrival of an answer.
   *
   * Alone in this store it is a **visit's** memory rather than the process's, which is what
   * `forgetAwaitedDeclaration` is for: *first* is about what the screen has seen, and a screen
   * that has been closed and reopened has seen nothing.
   */
  readonly sportAwaitingDeclaration: Sport | undefined;
  /**
   * Open Play on this sport and this declaration, **only if nothing has been chosen yet**.
   *
   * Conditional because it is called on every entry — the reset lays the Play stack down from
   * two doors — and an unconditional seed would put a player who switched to tennis back on
   * padel every time they came in from ⚡.
   *
   * The declaration is the *seed*, never a binding: see the docblock, and `domain/playMode`.
   */
  readonly seedIfAbsent: (sport: Sport, intent: PlayIntent | undefined) => void;
  /**
   * Open the mode on the declaration the player has **just made** — the transition
   * `undefined -> declared` for the sport on screen, and no other moment.
   *
   * `seedIfAbsent` returns early once a sport has been seeded, so a player who landed on a
   * rated but **undeclared** sport was seeded on *for fun* and left there by the answer they
   * gave two taps later on the interstitial. Since
   * [#293](https://github.com/Raketa02/Raketa/issues/293) the segment is not drawn at all
   * while the question is open, so what this decides is no longer a contradiction a player
   * watches being corrected — it is **the mode they find when the form arrives**, which is the
   * one moment their answer is the only thing anybody knows about them.
   *
   * **This is not a re-seed, and the difference is the whole of the action.** A toggle
   * re-derived from the declaration on every open agrees with it on every first search, and
   * ADR-0094's drift backstop — written for the sticky-tab case — would have nothing left to
   * catch (`domain/playMode`). So it fires on a transition rather than on a value: never on a
   * declaration that was already there when the screen opened, never on a sport switch, and
   * never on a profile refetch, all three of which are the same value read a second time.
   *
   * It is called **beside** `seedIfAbsent`, with the same pair, from the screen's one
   * declaration effect: the seed is what puts a sport on screen, and this is what answers the
   * sport already on it.
   */
  readonly seedModeOnFirstDeclaration: (sport: Sport, intent: PlayIntent | undefined) => void;
  /**
   * Forget what was seen without a declaration — **called by the screen when it opens.**
   *
   * *First* is a statement about the screen's own visit and not about the process: a player
   * who moved the segment, left Play and declared that sport somewhere else comes back to a
   * declaration that **already existed when the screen opened**, which is the one thing the
   * action above must never act on. Nothing else can say so — the store outlives the screen by
   * design, and a slot that outlived it too would spend itself on a declaration made two
   * screens away.
   *
   * It is not `reset`: the sport and the mode are the process's and survive leaving Play. This
   * clears the one field that is a **visit's** memory, kept here rather than in `playSession`
   * because nothing writes across those two stores.
   */
  readonly forgetAwaitedDeclaration: () => void;
  /** The sport chips. */
  readonly chooseSport: (sport: Sport) => void;
  /**
   * The segmented control on Find a game, and nothing else — in particular not the deck,
   * which has no mode.
   */
  readonly chooseMode: (mode: SearchMode) => void;
  /**
   * Back to nothing seeded — including what was seen without a declaration, which is a
   * memory of this process and dies with it.
   *
   * **Not called by the shell's reset**, which is the distinction between the two stores: a
   * player leaving Play keeps the sport they were looking at, because leaving Play is not
   * changing their mind about what they play. Process death is the real ending; this is what
   * a suite uses to stand in for it.
   */
  readonly reset: () => void;
}

export const usePlayPreferences = create<PlayPreferencesState>((set, get) => ({
  sport: undefined,
  mode: MODE_WITHOUT_A_DECLARATION,
  sportAwaitingDeclaration: undefined,
  seedIfAbsent: (sport, intent) => {
    // The pair is seeded together and only together, so the sport's absence is the pair's:
    // there is no reachable state where a mode has been chosen and no sport has, because the
    // segment that chooses one is on a screen the entry already seeded.
    if (get().sport !== undefined) return;
    set({ sport, mode: intent === undefined ? MODE_WITHOUT_A_DECLARATION : modeForIntent(intent) });
  },
  seedModeOnFirstDeclaration: (sport, intent) => {
    const awaited = get().sportAwaitingDeclaration;

    // Nothing to declare yet: remember that this sport was seen without one, which is the
    // only half of the transition the store cannot see for itself.
    if (intent === undefined) {
      if (awaited !== sport) set({ sportAwaitingDeclaration: sport });
      return;
    }

    // A declaration this process never saw the absence of — the sport was declared in before
    // the screen opened, or the chip moved to one that was. It seeds nothing, and the sport it
    // is not about stops being awaited: the screen has moved on from it.
    if (awaited !== sport) {
      if (awaited !== undefined) set({ sportAwaitingDeclaration: undefined });
      return;
    }

    // The transition, and the only place this action writes a mode: through `modeForIntent`,
    // so `NO_PREFERENCE` inherits *for fun* from the mapping rather than from a literal here.
    set({ sportAwaitingDeclaration: undefined, mode: modeForIntent(intent) });
  },
  forgetAwaitedDeclaration: () => {
    if (get().sportAwaitingDeclaration !== undefined) set({ sportAwaitingDeclaration: undefined });
  },
  chooseSport: (sport) => set({ sport }),
  chooseMode: (mode) => set({ mode }),
  reset: () =>
    set({
      sport: undefined,
      mode: MODE_WITHOUT_A_DECLARATION,
      sportAwaitingDeclaration: undefined,
    }),
}));
