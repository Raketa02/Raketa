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
 * ## Five states, and two of them are absences
 *
 * | | |
 * | --- | --- |
 * | `waiting` | the line-up has not completed — the control is not drawn, and the count line stands where it will be |
 * | `greyed` | a slot is still empty — the act is refused and the counter above says why |
 * | `live` | all three are set and nobody has locked |
 * | `busy` | the lock is going out — pending, never optimistic |
 * | `gone` | the plan is locked, and the control is removed rather than settled |
 *
 * **The lock waits for the court**
 * ([ADR-0164](../../../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)
 * §5). Where, day and hour are proposals anybody on the court may make and move; *we are agreed*
 * is said only once everybody who will have to keep it is in. So while the room has no game the
 * control is **absent, never greyed** — #324's rule: a greyed button would promise an act the
 * server refuses with `the_court_is_not_whole`, and no count of slots would unlock it — and in its
 * place the surface draws one line, `2 of 4 in — you can plan now, lock when everyone's here`,
 * which is the note #324 owes. **The fact this reads is whether the line-up has completed** — *has
 * this court become a game* is derived from the line-up having completed
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §1), so a game a seat has since been left open on is still complete, still draws the button,
 * and meets the server's refusal in words if it is ever reached. The count of members over seats
 * rides on the incomplete arm because that is the only arm with a line to say it on; the numbers
 * are the surface's to state — the room knows who is in and the sport knows how many it takes —
 * and this file decides only that a court still being filled has no lock to draw. It is read
 * before the slot count, as the server asks its refusals in that order.
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
 * A hold is not one of the five: it greys the control under the **room's** note, exactly as it
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

/**
 * **Who is in against how many the court takes** — the two numbers the count line says. `members`
 * is the room's, `seats` is the sport's court; neither is this feature's to count.
 */
export interface CourtCount {
  readonly members: number;
  readonly seats: number;
}

/**
 * **The court's line-up, as far as the lock reads it**: complete — the court has become a game,
 * and stays complete whatever happens to a seat after — or still filling, with the count for the
 * line drawn where the lock will be. A discriminated pair rather than an optional count, so the
 * fold reads a named fact and the numbers exist exactly where there is a line to say them on.
 */
export type LineUp = { readonly complete: true } | ({ readonly complete: false } & CourtCount);

/** The line-up of a court that has its game — what every game surface hands the card. */
export const LINE_UP_COMPLETE: LineUp = { complete: true };

/** What the control is, read off the plan, the line-up and the write in flight. See the module note. */
export type LockControl = 'waiting' | 'greyed' | 'live' | 'busy' | 'gone';

export function lockControl(
  plan: Plan | undefined,
  { pending, lineUp }: { readonly pending: boolean; readonly lineUp: LineUp },
): LockControl {
  if (isLocked(plan)) return 'gone';
  if (!lineUp.complete) return 'waiting';
  if (pending) return 'busy';

  return slotCount(plan) === SLOTS ? 'live' : 'greyed';
}
