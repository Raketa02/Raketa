/**
 * **Which questions the room still has to ask** — the quick chips' one rule.
 *
 * A chip **posts words and nothing else** (ADR-0144): *"Saturday works?"* is a question, and a
 * chip that also filled the day slot would record an agreement nobody had yet, which is the one
 * thing the plan card must not do. So what is decided here is only **which questions are worth
 * offering**, and the sentences are `conversationPresentation.ts`'s.
 *
 * > **One chip per unfilled slot, in slot order, plus `On my way` when the agreed day is today.**
 *
 * ## The fallback is conditional, and that is what caps the row at three
 *
 * [#329](https://github.com/Raketa02/Raketa/issues/329) collapsed the rule to *one per unfilled
 * slot plus an unconditional fallback, which never reaches the four-chip cap* — and three unfilled
 * slots plus an unconditional fallback is **exactly** four. *On my way* on a Monday for a Saturday
 * game is nonsense besides.
 *
 * **The cap is structural here rather than checked.** `On my way` is offered only when a day is
 * agreed, and a day that is agreed is a slot that is not unfilled — so the two can never both
 * count three, and there is no `slice(0, 3)` anywhere to get wrong.
 *
 * ## *Today* is the platform's, and it is folded against `read_at`
 *
 * The plan's day is a **local date in the platform's one zone**, so *is it today* is that date
 * against the platform day of the instant the room was folded — never against `Date.now()`, on
 * `durationLeft`'s rule, and never against the device's zone, on the day separator's
 * (`entry.ts`). A phone in Los Angeles must not offer *On my way* a day late.
 *
 * ## The plan arrives as an argument, and this build has none to give it
 *
 * `features/plans` owns the plan — its read, its three writes, its slot vocabulary and the card
 * that edits it ([#366](https://github.com/Raketa02/Raketa/issues/366),
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3). This
 * feature never imports it: {@link AgreedPlan} is the **structural** shape the plan will satisfy,
 * so the day that read exists the screen hands one down and nothing here changes.
 *
 * Until then the screen passes `undefined`, and **that is honest rather than a placeholder**:
 * `GET /plans` has no row at all for a game nothing has been agreed on — *"a plan is born by
 * being used"* — so *no plan* and *nothing agreed* are one state on the wire as well as here, and
 * this build has no surface on which a slot can be filled.
 */

import { platformDay } from './entry';

/**
 * The three slots a plan has.
 *
 * Spelled here because the chips are **keyed by slot** and a copy table needs its key; the order
 * below is [ADR-0144](../../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)'s
 * — *where · day · hour*, the order people discuss them in and of decreasing negotiability.
 */
export type PlanSlot = 'where' | 'day' | 'hour';

/** The four chips this row can hold, of which at most three are ever offered at once. */
export type QuickChip = PlanSlot | 'on-my-way';

/**
 * What has been agreed, as much of it as this rule reads.
 *
 * Structural on purpose — see the module note. An absent field is a slot that has **never been
 * filled**: a slot is never emptied, so there is no third state to tell apart.
 */
export interface AgreedPlan {
  /** Where they are meeting, as somebody typed it. */
  readonly place?: string;
  /** The local day in the platform's zone, `YYYY-MM-DD`. */
  readonly day?: string;
  /** The local clock time, `HH:MM`. */
  readonly hour?: string;
}

/** The chips to offer, in slot order. Empty when everything is agreed and the day is not today. */
export function quickChips(plan: AgreedPlan | undefined, readAt: string): readonly QuickChip[] {
  const unfilled: readonly QuickChip[] = [
    ...(plan?.place === undefined ? (['where'] as const) : []),
    ...(plan?.day === undefined ? (['day'] as const) : []),
    ...(plan?.hour === undefined ? (['hour'] as const) : []),
  ];

  const today = plan?.day !== undefined && plan.day === platformDay(readAt);

  return today ? [...unfilled, 'on-my-way'] : unfilled;
}
