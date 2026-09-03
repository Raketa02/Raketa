/**
 * A **Play session**: the working copy of the week, and the line-up being built on it.
 *
 * It begins when the shell lays the Play stack down and ends when the shell lays any stack
 * down — which is one function, `resetShellStack`, and therefore a *definition* rather than a
 * line somebody must remember on every exit. That is the discipline `onboardingPass.end()`
 * already states, and [#261](https://github.com/Raketa02/Raketa/issues/261) identified the
 * function before there was anything for it to clear.
 *
 * ## Why the visit, and not longer
 *
 * §E8 lists *"a line-up sits half-built for an hour"* among the states that must exist, which
 * reads like a demand that a line-up survive leaving Play. Three settled facts say otherwise:
 * leaving Play **replaces** the stack, AC-2 lands a returning player on **Find a game** rather
 * than the builder, and the working copy is re-seeded from the profile on entry. A surviving
 * line-up would sit invisible behind a screen whose week no longer matched the search it was
 * built on — two facts disagreeing silently, in a state nothing on Find a game was ever
 * designed to describe.
 *
 * **And the hour does not need survival to happen.** Backgrounding does not leave Play: the
 * process lives, the stack is intact, and returning finds the same builder an hour later.
 * That is §E8's scenario exactly, and it is where the send-time re-check earns its place.
 * Backgrounding clears nothing; process death clears everything.
 *
 * ## What this store deliberately does not hold
 *
 * - **The candidates, the pool, the deck, the forecast.** Every ranked list is a
 *   mutation-minted record read by id from Query under `searchKeys.detail(id)`. Part 1's
 *   *"never copy Query data into Zustand"* is why the seats below are ids and nothing else.
 * - **The pending seat replacement.** G7 wants it forgotten when the pool is left without an
 *   addition, and the court **pops** rather than pushes, so the pool route unmounts and takes
 *   its `useState` with it. The navigation decision satisfies the requirement; a store would
 *   reintroduce the bug it is meant to prevent.
 * - **The card in flight on the deck.** Route-local too: the two buttons lock until the exit
 *   animation completes, and *which card is showing* is derived from the dealt list minus the
 *   one leaving — never held here.
 * - **Whether the account is held.** §J6 forbids a cached hold flag by name — *"a hold
 *   released on one screen must not survive on another"* — and a cached flag is the only
 *   mechanism by which a released hold *can* survive. `account_held` is a `403` code
 *   `shared/errors` already maps as terminal; every Play route re-checks server-side, so the
 *   requirement holds **by construction**. UI open decision #5 wanted the builder gated at
 *   navigation, which needs exactly that cache, and it is refused
 *   ([#228](https://github.com/Raketa02/Raketa/issues/228) §8).
 * - **A loading flag.** Part 8 names one as a thing Zustand must not hold; request state is
 *   Query's `isPending` plus a route-local minimum-display latch.
 *
 * ## The rules are in `domain/`
 *
 * `workingWeek` owns the seed, the toggle and the comparison; `lineup` owns the origin and the
 * one guard over the three acts that orphan one. This holds values and nothing else — the same
 * split `onboardingPass` and `profileDraft` use.
 */

import { create } from 'zustand';

import type { Sport } from '@/shared/vocabulary/sport';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { Lineup, SeatedPlayerId } from '../domain/lineup';
import { alsoAsked, NOTHING_ASKED, type AskedQuestions } from '../domain/raisedPrompt';
import type { Prompt } from '../domain/vocabulary';
import { sameCell, seedWorkingWeek, toggleCell, type WorkingWeek } from '../domain/workingWeek';

interface PlaySessionState {
  /**
   * The working copy. **Undefined outside a visit**, which is the state that makes the seed
   * safe: a cleared week is a legal value the wire accepts, so *no session* and *a session
   * whose every cell was unticked* are two different things and an empty array cannot tell
   * them apart.
   */
  readonly week: WorkingWeek | undefined;
  /** Undefined until somebody has been added. Nothing else in Play holds a line-up. */
  readonly lineup: Lineup | undefined;
  /**
   * **The cell a times rung added, for the search on screen and no other.**
   *
   * A rung taken on the pool widens the searcher's own grid by one slot for that one search
   * ([#223](https://github.com/Raketa02/Raketa/issues/223) §8), and the week the player filled
   * in disagrees with the search that ran until the grid says so. So it is held here, beside
   * the week, to be **ticked** on *Find a game* two pushes back — and deliberately not held
   * *in* the week: `week` is what travels as `availability_override`, so writing the offered
   * cell into it would carry a this-search-only widening into every later ask, which is the
   * conflation ADR-0099 exists to prevent arriving from the client instead of the engine
   * ([#283](https://github.com/Raketa02/Raketa/issues/283)).
   */
  readonly addedForThisSearch: WeekCell | undefined;
  /**
   * **The questions this visit has already put to the player**, by sport and code.
   *
   * Here rather than on the four screens that draw a sheet, because the questions are about
   * things this store holds. `KEEP_THESE_TIMES` is about the **working week** above it: two
   * presses over one week — *Search*, then *Let the engine fill the seats* — mint two searches
   * and raised it twice, two taps apart, with *not now* already said
   * ([#287](https://github.com/Raketa02/Raketa/issues/287)). A memory keyed by the minted
   * search id cannot see that, because what did not change between the two presses is exactly
   * what the question was about.
   *
   * It is the **only** memory that prompt has: its decline writes no durable row on purpose
   * (`promptSuppresses`), so nothing on the server will decline to raise it again. That is
   * what makes this the session's rather than a screen's, and ending with the session is what
   * keeps ADR-0099's argument whole — *a grid is a different grid next Tuesday* is about the
   * next visit and not about the next two taps.
   */
  readonly askedQuestions: AskedQuestions;
  /**
   * Enter Play: fill the grid in from the profile.
   *
   * Called on **navigation**, never during a render — §G6 bug #5 is the prototype cloning the
   * grid inside its own render, and the fix it names is *"seed the grid on navigation, not on
   * render."* Both doors into Play replace the stack, so this is a well-defined moment.
   *
   * Unconditional, unlike the preferences' seed: the reset has already emptied this store, so
   * an entry is always the start of a session and there is never a half-built week to protect.
   */
  readonly enter: (profileWeek: WorkingWeek) => void;
  /**
   * Tick or untick one cell of the working copy. A no-op outside a session.
   *
   * **A tap on the offered cell also takes the mark off it.** The two facts are about the same
   * square and only one of them can be true: once the player ticks it themselves it is their
   * own ask, travelling on every search from here, and *added for this search* would be the
   * grid saying so about a cell that outlived the search it belonged to.
   */
  readonly toggleWeekCell: (cell: WeekCell) => void;
  /**
   * Record the cell a times rung just added. **One caller: the pool, on a taken rung.**
   *
   * The offer is the pool's and the grid is *Find a game*'s, so the fact has to outlive the
   * screen that learned it — which is what this store is for, and why the mark is not a
   * `useState` on the pool the way its pending replacement is.
   */
  readonly addForThisSearch: (cell: WeekCell) => void;
  /**
   * Forget it — **the next search does not carry it.**
   *
   * Taking a rung is one search citing the offer that priced it; a search composed on *Find a
   * game* cites nothing, so from the moment one is asked for, the mark would be a claim about
   * a list nobody is holding any more. The screen that composes the ask is the one that says
   * so, because it is the one that knows.
   */
  readonly clearAddedForThisSearch: () => void;
  /**
   * Remember that this question has been put — **called on the answer, whichever answer.**
   *
   * A dismissal is a decline and a decline is an answer, so every path out of the sheet
   * arrives here: `PromptSheet` reports once and only once, and the sheet is what decides
   * which of its exits count.
   */
  readonly recordAsked: (sport: Sport, prompt: Prompt) => void;
  /**
   * Add somebody to the court, under the search they came off.
   *
   * *"Adding somebody only builds the line-up on your screen"* (AC-112) — this writes nothing
   * outbound. The `originSearchId` is an argument rather than something the store remembers,
   * because it is the caller's own fact: the row was drawn from a search, and that search is
   * what the forecast will be asked under.
   *
   * **A seat taken from a different search starts a new line-up rather than mixing two.**
   * `POST /forecasts` would refuse the mixture — every player named must have appeared in the
   * one search — so a line-up spanning two origins is unsendable by construction, and holding
   * one would only postpone the refusal to the moment it costs the most.
   */
  readonly seat: (originSearchId: string, playerId: SeatedPlayerId) => void;
  /**
   * **⚡, which fills every empty seat at once** — one act, and therefore one write.
   *
   * Not `seat` in a loop. The fill is a single answer off a single search, and seating four
   * people one at a time would put the store through three intermediate line-ups that never
   * existed — each of them a state the origin guard and the forecast key could be read in. It
   * also mints its **own** `search_id`, so the line-up rebinds wholesale: the four came off
   * that search's rows, and `POST /forecasts` refuses anybody the cited search did not show.
   *
   * An empty list clears the line-up rather than writing an empty one, which is `unseat`'s own
   * rule read from the other end: the engine seating nobody is a court with no line-up on it,
   * not a line-up with nobody in it.
   */
  readonly seatAll: (originSearchId: string, playerIds: readonly SeatedPlayerId[]) => void;
  /** Take somebody off the court. The last one out leaves no empty line-up behind. */
  readonly unseat: (playerId: SeatedPlayerId) => void;
  /**
   * Throw the line-up away, keeping the week.
   *
   * What a player confirms when `domain/lineup`'s guard asked and they went ahead: the three
   * triggers change the origin, and the change is what orphans the line-up. Discarding is the
   * act, never a synchronisation — the two stores do not read each other.
   */
  readonly discardLineup: () => void;
  /**
   * **The Play session is over.**
   *
   * One caller: the shell's reset, through `endPlaySession` on this feature's public surface.
   * Every exit from Play goes through it — a flanking tab, ⚡Play arriving again, the *Find a
   * game* segment re-entering, and the send landing on Now — so this needs no second call site
   * and must not grow one.
   */
  readonly end: () => void;
}

export const usePlaySession = create<PlaySessionState>((set) => ({
  week: undefined,
  lineup: undefined,
  addedForThisSearch: undefined,
  askedQuestions: NOTHING_ASKED,
  enter: (profileWeek) =>
    set({
      week: seedWorkingWeek(profileWeek),
      lineup: undefined,
      addedForThisSearch: undefined,
      askedQuestions: NOTHING_ASKED,
    }),
  // Dropped rather than beginning a session, for the reason the pass drops a rating recorded
  // with no pass running: the grid is only reachable from a screen the entry seeded, so this
  // guards against a future caller rather than a case the flow produces.
  toggleWeekCell: (cell) =>
    set((state) => {
      if (state.week === undefined) return state;
      const marked = state.addedForThisSearch;
      return {
        week: toggleCell(state.week, cell),
        ...(marked !== undefined && sameCell(marked, cell)
          ? { addedForThisSearch: undefined }
          : {}),
      };
    }),
  // Dropped outside a session for `toggleWeekCell`'s own reason: the pool is only reachable
  // from a screen the entry seeded, so this guards a future caller rather than a case the
  // flow produces.
  addForThisSearch: (cell) =>
    set((state) => (state.week === undefined ? state : { addedForThisSearch: cell })),
  clearAddedForThisSearch: () => set({ addedForThisSearch: undefined }),
  recordAsked: (sport, prompt) =>
    set((state) => ({ askedQuestions: alsoAsked(state.askedQuestions, sport, prompt) })),
  seat: (originSearchId, playerId) =>
    set((state) => {
      const held = state.lineup?.originSearchId === originSearchId ? state.lineup : undefined;
      if (held?.seats.includes(playerId)) return state;
      return { lineup: { originSearchId, seats: [...(held?.seats ?? []), playerId] } };
    }),
  seatAll: (originSearchId, playerIds) =>
    set({
      lineup: playerIds.length === 0 ? undefined : { originSearchId, seats: [...playerIds] },
    }),
  unseat: (playerId) =>
    set((state) => {
      if (state.lineup === undefined) return state;
      const seats = state.lineup.seats.filter((seated) => seated !== playerId);
      return { lineup: seats.length === 0 ? undefined : { ...state.lineup, seats } };
    }),
  discardLineup: () => set({ lineup: undefined }),
  end: () =>
    set({
      week: undefined,
      lineup: undefined,
      addedForThisSearch: undefined,
      askedQuestions: NOTHING_ASKED,
    }),
}));

/**
 * End the Play session, from outside React.
 *
 * The shell's reset is an imperative function called from mutation callbacks as well as from
 * presses, so the ending has to be reachable without a hook — the shape `showToast` uses, and
 * for the same reason. This is what `features/play`'s public surface exports to the shell, and
 * it is the whole of what the shell knows about Play's state.
 */
export function endPlaySession(): void {
  usePlaySession.getState().end();
}
