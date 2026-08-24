/**
 * Now's clock: the shared repaint loop, over the moments the composed screen holds.
 *
 * The loop itself is `useMomentClock` — one implementation for the three screens
 * that count down, promoted there when the third arrived. What is left here is the
 * one thing that is Now's and not another screen's: **which moments a composed
 * screen is holding**, which is `momentsOnScreen` and is the pair of slots on every
 * card in three regions.
 *
 * It stays a hook of its own rather than becoming a call at the provider, because
 * `NowClockProvider` takes a screen and the mapping from *a screen* to *its
 * moments* is a fact about this feature's shape. A provider that transposed it
 * inline would put that knowledge in a component.
 */

import type { ComposedScreen, Moment } from '../domain/ComposedScreen';
import { momentsOnScreen } from '../domain/countdown';

import { useMomentClock } from './useMomentClock';

/** A screen with nothing on it holds no moments, and a stable array arms nothing. */
const NONE: readonly Moment[] = [];

/**
 * The instant every countdown on the screen subtracts from.
 *
 * One value for the whole screen, so two cards can never disagree about what time
 * it is by a render.
 */
export function useRepaintClock(screen: ComposedScreen | undefined): number {
  return useMomentClock(screen === undefined ? NONE : momentsOnScreen(screen));
}
