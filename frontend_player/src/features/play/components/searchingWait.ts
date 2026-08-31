/**
 * How long a searching latch holds an answer — the **floor**, and the stagger drawn over it.
 *
 * Two waits share one mechanism with two numbers (`theme.motion.hold`, and
 * [#228](https://github.com/Raketa02/Raketa/issues/228) §9): the pool's ranking pass has a
 * floor and nothing over it, and the engine fill has a shorter floor with a seat landing every
 * 550 ms after it. Both run **over a completed answer** — `useHeldWait` starts them when the
 * response lands — so neither delays a request and neither is a guess at how long one takes.
 *
 * ## The collapse, and the half of it that does not collapse
 *
 * > **A hold is not an animation.** The floor survives; the stagger over it goes to zero.
 *
 * §G5's finding is that the prototype kills its animations and lets the 2,3-second stagger run
 * anyway ([#239](https://github.com/Raketa02/Raketa/issues/239)), so the collapsed path is the
 * one that has to be built rather than assumed. Collapsing the **floor** with it would be the
 * opposite mistake and is refused by name in `motion.hold`'s own docstring: nothing moves
 * during a hold, and the player who asked the OS to calm things down is the last one who
 * should be given a flash where an answer came into existence.
 *
 * `useCollapsedPresentation()` is what decides `collapsed`, and it is **one condition
 * satisfied by either** reduced motion or a running screen reader: a listener gets none of the
 * craft and all of the latency.
 *
 * It is a field on the **fill** rather than a second argument, because it is only the fill
 * that has anything to collapse. A pool wait asked for it and then ignored it, which is a
 * screen asking the OS a question whose answer it cannot use — and one more always-mounted
 * subscriber to a device setting, which is the cost `useCollapsedPresentation`'s own docstring
 * names.
 *
 * ## Why the seats' arithmetic is here
 *
 * `motion.hold` holds the two floors *"because two screens share them, and a floor typed twice
 * is a floor that drifts"*, and books the 550 to the animation it drives. The latch is up
 * until the last seat has landed, so the fill's floor **is** that animation's length: the two
 * are one sum, and this is where it is added up. The court that draws the seats
 * ([#271](https://github.com/Raketa02/Raketa/issues/271)) derives its per-seat delays from the
 * same constant rather than from a second copy of the addition.
 */

import { theme } from '@/shared/ui';

/** The gap between two seats landing — the moving half of the fill, and the half that goes. */
const SEAT_STAGGER_MS = 550;

/**
 * The wait a latch is over. **A code and not a duration**, so a third wait gains its floor
 * here or it does not compile.
 */
export type SearchingWait =
  /** The pool's own ranking pass — `POST /searches`. */
  | { readonly kind: 'pool' }
  /** The engine seating a court — `POST /lineups`, and the seats it lands. */
  | { readonly kind: 'fill'; readonly seats: number; readonly collapsed: boolean };

/**
 * How long the answer stays on screen once it has arrived.
 *
 * A fill is held until its **last** seat has landed, which is why it is this sum and not the
 * bare floor: a latch that lifted at 650 ms would take the court away halfway through filling
 * it. Collapsed, every seat lands on the floor itself, so the sum is the floor.
 */
export function searchingFloorMs(wait: SearchingWait): number {
  if (wait.kind === 'pool') return theme.motion.hold.pool;

  const seatsAfterTheFirst = Math.max(wait.seats - 1, 0);
  return theme.motion.hold.fill + (wait.collapsed ? 0 : seatsAfterTheFirst * SEAT_STAGGER_MS);
}
