/**
 * **The lock** — the count it is guarded on, and the control's four states as a pure function of
 * the plan
 * ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
 * [#403](https://github.com/Raketa02/Raketa/issues/403)).
 *
 * ## The count and the lock are two facts
 *
 * ADR-0144 folded them together — *filling the third slot is the lock* — and ADR-0155 §3 takes
 * that sentence back: **a complete plan is one everybody *could* agree, and a locked plan is one
 * somebody did.** So `isLocked` reads `lockedAt` and is **explicitly not** `slotCount === SLOTS`;
 * the count is what the lock is guarded on, never what it is.
 *
 * A file of its own rather than three lines in `slots.ts`, because the lock is not a slot. Nothing
 * here decides a slot and nothing in `slots.ts` reads the lock — which is the client half of
 * *locking freezes nothing*: a slot write does not read `locked_at` and never will.
 *
 * ## Four states, and one of them is an absence
 *
 * | | |
 * | --- | --- |
 * | `greyed` | a slot is still empty — the act is refused and the counter above says why |
 * | `live` | all three are set and nobody has locked |
 * | `busy` | the lock is going out — pending, never optimistic |
 * | `gone` | the plan is locked, and the control is removed rather than settled |
 *
 * **Gone rather than 6.1's `settled`**, and the argument is §6.1's own test read against the
 * wire. `settled` is for a control whose act *is still available*: pressing it again obtains the
 * thing a second time. A second lock **records nothing and answers `200`** — the server's
 * idempotency language applied to an act — so a control still offering it would be one that
 * provably does nothing, which is the pool's own argument against a rung priced at nobody. The
 * fact travels on the counter instead, in a word, which is what Part 13's *never colour alone*
 * asks of the only carrier.
 *
 * **The greyed state's sentence is the counter, and this is where that is argued.** #324 attaches
 * one condition to every greyed control in this app — *a note above it has already said why* —
 * and the design drops the reason from the label on purpose. The counter is that note. It is
 * drawn always rather than only when the control is greyed, it sits directly above the control in
 * reading order — sighted and spoken alike, a `header` two elements before the button — and it
 * states exactly the condition the act is waiting on, because the count **is** the guard
 * (ADR-0155 §3: *`SLOTS` says how far along a plan is and is what the lock is guarded on*). A
 * second sentence — *set all three first* — would restate `1 of 3 set` one line lower, which is
 * §1.6's count problem in two spellings and the reason the author struck it from the label.
 *
 * A hold is not one of the four: it greys the control under the **room's** note, exactly as it
 * greys the chips, and the component reads it beside this rather than through it.
 */

import { PLAN_SLOTS, isFilled, type Plan } from './slots';

/** How many slots a plan has, and the count the lock is guarded on. Three, and never a fourth. */
export const SLOTS = PLAN_SLOTS.length;

/** How many of the three are filled. A missing plan is three empty slots, so it counts nought. */
export function slotCount(plan: Plan | undefined): number {
  return PLAN_SLOTS.filter((slot) => isFilled(plan, slot)).length;
}

/** Whether somebody has said *we are agreed*. **Never** the count under another name. */
export function isLocked(plan: Plan | undefined): boolean {
  return plan?.lockedAt !== undefined;
}

/** What the control is, read off the plan and the write in flight. See the module note. */
export type LockControl = 'greyed' | 'live' | 'busy' | 'gone';

export function lockControl(
  plan: Plan | undefined,
  { pending }: { readonly pending: boolean },
): LockControl {
  if (isLocked(plan)) return 'gone';
  if (pending) return 'busy';

  return slotCount(plan) === SLOTS ? 'live' : 'greyed';
}
