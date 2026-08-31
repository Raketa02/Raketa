/**
 * The **working copy** of the player's week: the grid Play searches on, which starts as the
 * profile's and is never written back to it.
 *
 * Two facts about it, and the second is the subtle one.
 *
 * **It is seeded on entry, never during a render.** UI spec §G6 bug #5 is the prototype
 * *"rendering the screen mutates state"* — the search grid lazily cloned inside the render
 * itself — and the fix it names is *"seed the grid on navigation, not on render."*
 * [#261](https://github.com/Raketa02/Raketa/issues/261) made both doors into Play **replace**
 * the stack, so *on entry* is a well-defined moment rather than a lifecycle guess, and
 * `seedWorkingWeek` is what that moment calls. AC-25 is the requirement: the grid *"arrives
 * already filled in from the user's profile."*
 *
 * **Whether it differs from the profile is a client comparison, on every tap.** AC-27 is the
 * case that decides the shape: tick a slot on, tick it off, and the week must stop reporting
 * itself as changed — so *changed* cannot be a flag a toggle sets, it has to be a comparison
 * against the grid the profile holds. §J6 puts it among the things that *"must update the
 * instant something changes"*, and ADR-0021 permits derivation by comparison.
 *
 * **This is not the search prompt, and the two must not be collapsed.**
 * [#226](https://github.com/Raketa02/Raketa/issues/226) refused a client-side diff for
 * `KEEP_THESE_TIMES`, because the backend compares the *post-rung* grid a search actually ran
 * on and only the backend knows what that was. The marker here is a different fact, asked
 * before any search: *this grid, against the one on your profile*. The marker is client-side;
 * the prompt stays server-raised on the search response.
 *
 * §J1's *"must forget a week used just for this search"* is honoured by the improvised grid
 * never being written anywhere but `availability_override` on the request.
 *
 * ## What is here, and what is `shared/`
 *
 * A cell's identity and the press over it are **`shared/vocabulary/week`**, beside the days
 * and the parts of the day that were already there. `player_profile` toggles these
 * twenty-one cells for the availability step and Play toggles them for the week it searches
 * on, and the second was written identically to the first — which is that folder's own test,
 * *"whether a second feature would have written the identical table"*, and the cross-feature
 * ownership `docs/architecture.md`'s fourth non-negotiable asks to see proven before a move.
 *
 * What is **here** is what only Play needs: seeding a copy on entry, and comparing one week
 * against another. A profile has no reason to ask whether a week equals another week, and
 * that comparison is the half AC-27 turns on — and the half the origin of a line-up is
 * judged by.
 */

import type { WeekCell } from '@/shared/vocabulary/week';

/**
 * The week Play is searching on: the cells that are ticked, in the order they were ticked.
 *
 * The same shape the profile's own week has, and deliberately not a distinct type — the two
 * are compared for equality on every tap, and a wrapper would mean unwrapping to do it.
 */
export type WorkingWeek = readonly WeekCell[];

/**
 * One cell as a single comparable value.
 *
 * The comparison below is a **set** comparison, and doing it by scanning lists is what makes a
 * duplicated cell invisible: `[Tue evening, Tue evening]` and `[Tue evening, Sat morning]` are
 * the same length, and every member of the first is in the second. Nothing in this app's own
 * toggle can produce a repeat, but a week arriving off the wire is not this app's own, and a
 * comparison the origin of every line-up rests on should not depend on that.
 */
function cellKey(cell: WeekCell): string {
  return `${cell.day}-${cell.part}`;
}

function cellsOf(week: WorkingWeek): ReadonlySet<string> {
  return new Set(week.map(cellKey));
}

/**
 * Whether two weeks tick the same cells — **as sets**, because order is not a fact about a
 * week.
 *
 * This is the whole of AC-27. A player who ticks Tuesday evening and unticks it has a list in
 * a different order and a week that is the same week, and anything comparing lists positionally
 * would report it as changed forever.
 */
export function sameWeek(one: WorkingWeek, other: WorkingWeek): boolean {
  const ticked = cellsOf(one);
  const against = cellsOf(other);
  if (ticked.size !== against.size) return false;
  return [...ticked].every((cell) => against.has(cell));
}

/**
 * The week the player is searching on, at the moment they enter Play.
 *
 * A copy rather than the profile's own array, so that a tap on the grid cannot be a tap on
 * the profile: the two are the same twenty-one cells and nothing else about them is shared.
 */
export function seedWorkingWeek(profileWeek: WorkingWeek): WorkingWeek {
  return [...profileWeek];
}

/**
 * *· changed from your profile* — the marker, as a fact rather than a sentence.
 *
 * The words are the screen's; what is decided here is whether there is anything to say. It is
 * a named rule rather than a negation written at each call site because it is the *product's*
 * question — §J6 requires it on every tap, and a screen comparing two weeks inline is a screen
 * that has re-decided what "changed" means.
 */
export function differsFromProfile(working: WorkingWeek, profileWeek: WorkingWeek): boolean {
  return !sameWeek(working, profileWeek);
}

/** Re-exported so a Play screen reads its whole week vocabulary from one place. */
export { isTicked, toggleCell } from '@/shared/vocabulary/week';
