/**
 * **The slot vocabulary** — which slots exist, their order, which are filled, and how each value
 * is spelled. The one place `where · day · hour` is an order
 * ([ADR-0144](../../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.1).
 *
 * The order is *where · day · hour*: the order people discuss them in, and of **decreasing
 * negotiability**. It is read by the card's chip row, by the quick chips one feature over and by
 * the game screen's checklist, so it is spelled once and never re-typed.
 *
 * ## Two grids, and neither is a rule this client invented
 *
 * **The day row is `today + 6`, clamped to `planned_at + PLAN_HORIZON`** — so it shrinks as the
 * week runs out, and inside the entry grace it is empty. **The hour row is 30-minute steps between
 * 06:00 and 23:00.** Both numbers live on the server, which refuses `the_day_is_past_the_horizon`
 * and `the_hour_is_not_offered`: *"the grid a client draws is a convention, and this refusal is
 * what makes it true."* What is here is that convention, held equal to the server's by
 * `slots.test.ts` and by the refusals themselves — a client drawing a wider grid would be offering
 * a chip that cannot be pressed to any effect.
 *
 * **`PLAN_HORIZON` is mirrored rather than derived**, and the alternative is worse rather than
 * unavailable: `entry_closes_at` is `planned_at + PLAN_HORIZON + ENTRY_GRACE`, so subtracting a
 * horizon out of it would mirror `ENTRY_GRACE` instead — the same number of constants, one of them
 * about a window this file has nothing to do with.
 *
 * ## Nothing here reads a clock
 *
 * Every instant arrives as an argument, and the one it arrives as is `GET /games`' `read_at`
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §10): a plan folds nothing against the clock — *its day and hour are wall-clock facts, drawn
 * literally and never counted down* — so `GET /plans` carries no `read_at` of its own and there is
 * no instant here for `Date.now()` to disagree with. **The horizon and *today* come off the same
 * fold**, which is what makes `today + 6` and `planned_at + 7` comparable at all.
 *
 * ## A slot is never emptied
 *
 * An absent value is a slot that has **never been filled**, never one somebody cleared — so there
 * is no third state to tell apart, and *no plan* answers exactly as an empty one, because
 * `GET /plans` has no row for a game nobody has arranged anything on yet.
 */

import { daysAfter, platformDay } from '@/shared/date/platformZone';

/** The three slots a plan has, in ADR-0144's order. */
export type PlanSlot = 'where' | 'day' | 'hour';

/** **The order**, and the one place it is one. Read by every surface that lists the slots. */
export const PLAN_SLOTS: readonly PlanSlot[] = ['where', 'day', 'hour'];

/**
 * One game's plan — three slots and the moment they name.
 *
 * **Keyed on the game and on nothing else**: a plan has no id of its own, for ever, and a second
 * identity beside that would be a second name for one thing.
 */
export interface Plan {
  readonly gameId: string;
  /** Where they are meeting, as somebody typed it. Never a court and never an id. */
  readonly place?: string;
  /** The local day in the platform's zone, `YYYY-MM-DD`. */
  readonly day?: string;
  /** The local clock time, `HH:MM` — the mapper's spelling, not the wire's. */
  readonly hour?: string;
  /**
   * The moment this plan names, **derived by the server and never recomputed here**: the agreed
   * instant when the day and the hour are both recorded, the start of the following local day when
   * only the day is, and absent when no day is.
   *
   * Nothing on the card reads it — a plan is drawn literally and never counted down — and it is
   * mapped because it is the plan's own field rather than because this ticket has a use for it.
   * Its reader is the four-rung ladder that keys Now's cards
   * ([#367](https://github.com/Raketa02/Raketa/issues/367)).
   */
  readonly agreedPoint?: string;
  /**
   * The moment somebody said *we are agreed* — and absent while nobody has
   * ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
   *
   * **The one value on a plan that is not a slot.** It is an act's moment rather than a fourth
   * slot: three filled slots is a plan everybody *could* agree, and this says somebody did. A
   * locked plan is not a frozen one — every slot stays editable and every move writes its own
   * line — and there is no unlock, so it is never cleared. Read by `domain/lock.ts` and by
   * nothing that decides a slot.
   */
  readonly lockedAt?: string;
}

/** The longest *where* this platform stores, in characters. The server's cap, mirrored. */
export const PLACE_CAP = 120;

/** The step between two offered hours, in minutes. */
const HOUR_STEP_MINUTES = 30;

/** The first and last hours a plan may name, as minutes of the local day — 06:00 and 23:00. */
const EARLIEST_HOUR_MINUTE = 6 * 60;
const LATEST_HOUR_MINUTE = 23 * 60;

const MINUTES_PER_HOUR = 60;

/** How far past `planned_at` a plan may name a day. `games`' own `PLAN_HORIZON`, in days. */
const PLAN_HORIZON_DAYS = 7;

/** How many days the row offers, counting today. */
const DAYS_OFFERED = 7;

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/** What one slot holds, or nothing where it has never been filled. */
export function slotValue(plan: Plan | undefined, slot: PlanSlot): string | undefined {
  if (plan === undefined) return undefined;
  if (slot === 'where') return plan.place;
  if (slot === 'day') return plan.day;
  return plan.hour;
}

/** Whether this slot has been filled. */
export function isFilled(plan: Plan | undefined, slot: PlanSlot): boolean {
  return slotValue(plan, slot) !== undefined;
}

/** What is still to agree, **in slot order** — empty once all three are filled. */
export function unfilledSlots(plan: Plan | undefined): readonly PlanSlot[] {
  return PLAN_SLOTS.filter((slot) => !isFilled(plan, slot));
}

/**
 * **The last local day this plan may name** — `planned_at + PLAN_HORIZON`, as a platform day.
 *
 * The instant is advanced first and converted after, exactly as the server does it, so the two
 * agree across a clock change rather than only in the middle of a season.
 */
export function lastPlannableDay(plannedAt: string): string | undefined {
  const at = Date.parse(plannedAt);
  if (Number.isNaN(at)) return undefined;

  return platformDay(new Date(at + PLAN_HORIZON_DAYS * MS_PER_DAY).toISOString());
}

/**
 * **The days a plan may still be moved to** — today and the six after it, clamped to the horizon.
 *
 * Both instants come off one fold, so *today* and the horizon are read against one clock. An
 * unreadable instant offers nothing, which is the same nothing the horizon having passed offers:
 * in both cases there is no day this client can honestly put on a chip.
 */
export function offeredDays({
  readAt,
  plannedAt,
}: {
  readonly readAt: string;
  readonly plannedAt: string;
}): readonly string[] {
  const today = platformDay(readAt);
  const last = lastPlannableDay(plannedAt);
  if (today === undefined || last === undefined) return [];

  return Array.from({ length: DAYS_OFFERED }, (_, step) => daysAfter(today, step)).filter(
    (day): day is string => day !== undefined && day <= last,
  );
}

/** `HH:MM`, zero-padded, so a column of hours does not ripple. */
function asClockFace(minute: number): string {
  const pad = (value: number) => String(value).padStart(2, '0');

  return `${pad(Math.floor(minute / MINUTES_PER_HOUR))}:${pad(minute % MINUTES_PER_HOUR)}`;
}

/**
 * **The hours a plan may name** — 06:00 to 23:00 in half hours, and the same thirty-five the
 * server accepts.
 *
 * A constant rather than a function: the grid does not depend on the day, the game or the clock,
 * and nothing about it narrows once an hour has been recorded — **a plan is never unmade**, so
 * every hour on it stays offered so that the one that is set can be moved.
 */
export const HOURS_OFFERED: readonly string[] = Array.from(
  { length: (LATEST_HOUR_MINUTE - EARLIEST_HOUR_MINUTE) / HOUR_STEP_MINUTES + 1 },
  (_, step) => asClockFace(EARLIEST_HOUR_MINUTE + step * HOUR_STEP_MINUTES),
);

/**
 * The value as it would be stored — **runs of whitespace collapsed to one space**.
 *
 * The server's own normalisation, read one step early so the cap below is measured against what
 * will actually be shown. It is normalisation and not a fix: nothing is shortened here, and an
 * over-long note is refused rather than trimmed — *a shortened note is one the person who typed it
 * believes they wrote whole, in front of the other people on the court.*
 */
export function tidyPlace(written: string): string {
  return written.trim().replace(/\s+/g, ' ');
}

/**
 * Whether this box may be recorded — **non-empty once tidied, and within the cap.**
 *
 * The control that records and the check that refuses are two readers of one question, which is
 * `mayPost`'s rule one feature over: two copies of it is how one stops agreeing with the other.
 */
export function mayRecordPlace(written: string): boolean {
  const value = tidyPlace(written);

  return value.length > 0 && value.length <= PLACE_CAP;
}
