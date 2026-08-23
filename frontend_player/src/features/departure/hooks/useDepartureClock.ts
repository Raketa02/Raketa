/**
 * This screen's one repaint clock.
 *
 * **A repaint, and never a fetch.** The distinction is `ADR-0088`'s and it holds
 * here for the same reason: this module cannot reach Query at all — it holds a
 * number and hands it out — so a cadence can never become an occasion to ask.
 * Nothing on this screen asks on a timer either; the quote is asked for when the
 * screen opens and corrected by the write's own refusal, which is the mechanism
 * that makes a ticking clock safe to draw beside it.
 *
 * **A second timer in a second feature, and that is a decision.** Now's clock is
 * shaped around a composed screen — it reads the moments off three regions — and
 * this screen has three moments of its own and no regions. What is *not* duplicated
 * is the part that matters: the arithmetic and the format come from Now's
 * `countdown`, so `2 h 14 min` reads the same on both screens and `Date.parse`
 * still appears in exactly one module in this app. A **third** screen wanting one
 * is the signal to promote the loop itself, which is the rule this app applies to
 * its error-copy tables too.
 *
 * **One clock for the whole screen, not one per row.** The outcome table draws up
 * to four moments and the reasons draw one more; five components each holding a
 * timer is the version that gets built by accident.
 */

import { useEffect, useMemo, useState } from 'react';

import type { Moment } from '@/features/now/types';
import { remainingMs, repaintDelayMs } from '@/features/now/types';

/**
 * The instant every countdown on this screen subtracts from.
 *
 * @param moments every moment the screen is holding, in any order. The cadence
 * follows the soonest one that has not passed, and nothing is armed at all when
 * none is — a screen of spent rows costs a phone in a pocket nothing.
 */
export function useDepartureClock(moments: readonly Moment[]): number {
  const [now, setNow] = useState(() => Date.now());

  // The moments as one value, because the array is rebuilt on every render and a
  // fresh array would re-run the reset below forever. It changes when a fresh
  // answer arrives, which is exactly when the reading should be retaken.
  const held = useMemo(() => moments.join('|'), [moments]);

  // A fresh answer is a fresh reading. Without this, a screen recomposed off a
  // write would be drawn against whatever the last repaint left behind — up to a
  // minute stale, on the one occasion the player explicitly acted.
  useEffect(() => {
    setNow(Date.now());
  }, [held]);

  // Computed in the render body rather than inside the effect, so the effect's
  // dependencies are complete and no suppression comment is needed — this app has
  // one that crashes the plugin outright (`Raketa02/Raketa#21`). It is also the
  // honest dependency: the cadence is what the timer is armed on, and a change of
  // moments that leaves the band alone has nothing to re-arm.
  const delay = repaintDelayMs(soonest(moments, now));

  useEffect(() => {
    if (delay === undefined) return;

    const tick = setTimeout(() => setNow(Date.now()), delay);
    return () => clearTimeout(tick);
  }, [delay, now]);

  return now;
}

/**
 * Milliseconds until the soonest moment that has not passed, or `undefined`.
 *
 * A moment already behind us is skipped rather than answered as zero: it has
 * nothing left to repaint, and answering zero would re-arm on every render for
 * the rest of the screen's life.
 */
function soonest(moments: readonly Moment[], now: number): number | undefined {
  let best: number | undefined;

  for (const moment of moments) {
    const left = remainingMs(moment, now);
    if (left === undefined || left <= 0) continue;
    if (best === undefined || left < best) best = left;
  }

  return best;
}
