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
 * ## Two lifetimes, two stores, and no sync between them
 *
 * This store lives for the **process**. `playSession` beside it lives for the **visit** and is
 * cleared every time the shell lays a stack down. They are two stores because they are two
 * lifetimes, and `profileDraft`'s warning against splitting — *"a sync that can be
 * forgotten"* — does not reach here, because **nothing writes across them**: a line-up is
 * invalid when its origin search was for another sport, which `domain/lineup` derives at read.
 * There is no sync to forget.
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
   * Open Play on this sport and this declaration, **only if nothing has been chosen yet**.
   *
   * Conditional because it is called on every entry — the reset lays the Play stack down from
   * two doors — and an unconditional seed would put a player who switched to tennis back on
   * padel every time they came in from ⚡.
   *
   * The declaration is the *seed*, never a binding: see the docblock, and `domain/playMode`.
   */
  readonly seedIfAbsent: (sport: Sport, intent: PlayIntent | undefined) => void;
  /** The sport chips. */
  readonly chooseSport: (sport: Sport) => void;
  /**
   * The segmented control on Find a game, and nothing else — in particular not the deck,
   * which has no mode.
   */
  readonly chooseMode: (mode: SearchMode) => void;
  /**
   * Back to nothing seeded.
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
  seedIfAbsent: (sport, intent) => {
    // The pair is seeded together and only together, so the sport's absence is the pair's:
    // there is no reachable state where a mode has been chosen and no sport has, because the
    // segment that chooses one is on a screen the entry already seeded.
    if (get().sport !== undefined) return;
    set({ sport, mode: intent === undefined ? MODE_WITHOUT_A_DECLARATION : modeForIntent(intent) });
  },
  chooseSport: (sport) => set({ sport }),
  chooseMode: (mode) => set({ mode }),
  reset: () => set({ sport: undefined, mode: MODE_WITHOUT_A_DECLARATION }),
}));
