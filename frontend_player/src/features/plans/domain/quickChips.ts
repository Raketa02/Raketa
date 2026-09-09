/**
 * **Which questions the room still has to ask** — the quick chips' one rule.
 *
 * A chip **posts words and nothing else**
 * ([ADR-0144](../../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)):
 * *"Saturday works?"* is a question, and a chip that also filled the day slot would record an
 * agreement nobody had yet, which is the one thing the plan card must not do. So what is decided
 * here is only **which questions are worth offering**, and the sentences are
 * `components/planPresentation.ts`'s.
 *
 * > **One chip per unfilled slot, in slot order, plus `On my way` when the agreed day is today.**
 *
 * ## It is `features/plans`' and the row that draws it is the room's
 *
 * The rule is about the **plan's own slots** and reads their order, and
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22 assigns §22.4's four
 * sentences to `planPresentation.ts` beside §22.2's. It shipped in `features/conversations` with
 * [#364](https://github.com/Raketa02/Raketa/issues/364), which had no plan feature to put it in and
 * declared its own `PlanSlot` and its own slot order to make do — and a second spelling of
 * *where · day · hour* is precisely what
 * [#366](https://github.com/Raketa02/Raketa/issues/366) says `domain/slots.ts` must be the one
 * place of. So the rule and the words moved here and `QuickChips.tsx` stayed there: the row is a
 * control over the composer's send, which is the room's, and what it draws is the plan's.
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
 * `durationLeft`'s rule, and never against the device's zone, on the day separator's. A phone in
 * Los Angeles must not offer *On my way* a day late.
 *
 * **The instant is the room's here and the game's on the card**, and that is not a slip: this
 * question is asked of the read the chips are drawn beside, and the card's is asked of the read
 * its horizon comes off. Each is folded against the list it was answered by, which is the rule
 * both of them are keeping.
 *
 * ## No plan and nothing agreed are one state
 *
 * `GET /plans` has no row at all for a game nobody has arranged anything on — *"a plan is born by
 * being used"* — and a room whose line-up has not completed has no game to have one. Both arrive
 * here as `undefined`, and three questions is the right answer to either.
 */

import { platformDay } from '@/shared/date/platformZone';

import { unfilledSlots, type Plan, type PlanSlot } from './slots';

/** The four chips this row can hold, of which at most three are ever offered at once. */
export type QuickChip = PlanSlot | 'on-my-way';

/** The chips to offer, in slot order. Empty when everything is agreed and the day is not today. */
export function quickChips(plan: Plan | undefined, readAt: string): readonly QuickChip[] {
  const unfilled: readonly QuickChip[] = unfilledSlots(plan);
  const today = plan?.day !== undefined && plan.day === platformDay(readAt);

  return today ? [...unfilled, 'on-my-way'] : unfilled;
}
