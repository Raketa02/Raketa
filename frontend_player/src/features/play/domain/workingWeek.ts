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
 * A week as **one stable identity** — the same cells in the same spelling, whatever order they
 * were ticked in.
 *
 * `sameWeek` below asks whether two weeks are the same week; this answers the same question in
 * the shape a cache key needs, which is a value that can be compared without holding the other
 * week. Sorted for exactly that reason: ticks are kept in **press order** and a week is a set,
 * so `[Tue evening, Sat morning]` and `[Sat morning, Tue evening]` have to hash alike or a
 * player who ticked a cell and unticked it would be asking a question the cache has already
 * answered and cannot recognise.
 */
export function weekIdentity(week: WorkingWeek): readonly string[] {
  return [...cellsOf(week)].sort();
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

/**
 * **The week a second search on one origin sends** — and *unprovable is sent*.
 *
 * Two screens run a search on a week an **earlier** search already ran on: ⚡ fills the seats
 * around a court, and the pool takes a rung. Neither is composing a new ask, so both must
 * reproduce the first one — and an omitted `availability_override` does not mean *the week the
 * search above me ran on*, it means *the grid on my profile*. The two coincide only where the
 * origin's week can be **shown** to be the profile's, which needs the profile read in hand.
 *
 * So the absent profile sends the week rather than omitting it. Omitting would be the app
 * quietly running the second search on a different week from the list it is widening or the
 * court it is filling — two answers on one screen disagreeing about what was asked, with
 * nothing to see. Sending costs a field the backend would have filled in identically.
 *
 * It is **not** `differsFromProfile` above with the arguments swapped. That one answers *has
 * the player edited their week*, on a working copy, and its honest answer with no profile is
 * *no*. This one answers *can I prove this week is the profile's*, and its honest answer with
 * no profile is *no* as well — which is the opposite outcome, because the questions are
 * opposite. Two rules that differ only in what an unknown means are exactly the pair that gets
 * collapsed by hand at a call site.
 *
 * @param asked the week the origin search ran on.
 * @param profileWeek the profile's own grid, or `undefined` while it has not been read.
 */
export function sentWeekForOrigin(
  asked: WorkingWeek,
  profileWeek: WorkingWeek | undefined,
): WorkingWeek | undefined {
  if (profileWeek === undefined) return asked;
  return differsFromProfile(asked, profileWeek) ? asked : undefined;
}

/** Re-exported so a Play screen reads its whole week vocabulary from one place. */
export { isTicked, sameCell, toggleCell } from '@/shared/vocabulary/week';
