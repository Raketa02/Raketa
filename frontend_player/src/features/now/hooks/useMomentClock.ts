/**
 * The one repaint loop in this app, over whatever moments a screen is holding.
 *
 * **A repaint, and never a fetch.** `ADR-0088` states the distinction and states
 * that it is stated nowhere else: `ADR-0054` owns *refreshing* and names reaching
 * zero as one of its four occasions, so a repaint cadence must not become a fifth.
 * This module therefore cannot reach Query at all — it holds a number and hands it
 * out — and `components/nowDiscipline.test.ts` walks it to keep that true. The one
 * timer that *does* ask is `useDeadlineAsk`, and it is a one-shot wake at a moment
 * the server named.
 *
 * **This is the promotion `useDepartureClock` said to make.** That hook was written
 * as *"a second timer in a second feature"* and recorded the trigger for merging
 * them: *"a **third** screen wanting one is the signal to promote the loop
 * itself."* The result route is the third, so the loop moved here — beside the
 * arithmetic it was already borrowing — rather than being copied a third time. Two
 * loops would eventually be two cadences, and a screen that repaints on a different
 * beat from the one before it is a screen whose clock looks broken.
 *
 * It lives in **Now** and not in `shared/`, for the reason the situation table
 * does: the arithmetic and the format are `domain/countdown.ts`'s, `shared/` may
 * never import a feature, and one cross-feature import is cheaper than moving the
 * app's only derivation out of the module the walk polices it in.
 *
 * **One clock per screen, not one per element.** `ADR-0088` records that as
 * *"because a dozen cards each holding their own interval is the version that gets
 * built by accident"*. Making it a hook the screen calls once, rather than
 * something a card or a table row could call, is what stops that.
 *
 * **`setTimeout`, re-armed, rather than `setInterval`.** The cadence changes as the
 * screen crosses into the seconds band, and an interval would have to be torn down
 * and rebuilt to change it anyway — so the loop is written where its condition is
 * read.
 *
 * **Which moment the cadence follows is `domain/countdown.ts`'s**, shared with the
 * composed screen's own next-zero. Two copies of *skip a moment already behind us*
 * is how one of them comes to answer zero and re-arm on every render for the rest
 * of a screen's life.
 */

import { useEffect, useMemo, useState } from 'react';

import type { Moment } from '../domain/ComposedScreen';
import { repaintDelayMs, soonestMs } from '../domain/countdown';

/**
 * The instant every countdown on one screen subtracts from.
 *
 * One value for the whole screen, so two countdowns can never disagree about what
 * time it is by a render.
 *
 * @param moments every moment the screen is holding, in any order. The cadence
 * follows the soonest one that has not passed, and nothing is armed at all when
 * none is — a screen of spent rows costs a phone in a pocket nothing.
 */
export function useMomentClock(moments: readonly Moment[]): number {
  const [now, setNow] = useState(() => Date.now());

  // The moments as one value, because the array is rebuilt on every render and a
  // fresh array would re-run the reset below forever. It changes when a fresh
  // answer arrives, which is exactly when the reading should be retaken.
  const held = useMemo(() => moments.join('|'), [moments]);

  // A fresh answer is a fresh reading. Without this, a screen recomposed off a
  // write — or off a pull — would be drawn against whatever the last repaint left
  // behind, up to a minute stale, on the one occasion the player explicitly acted.
  useEffect(() => {
    setNow(Date.now());
  }, [held]);

  // Computed in the render body rather than inside the effect, so the effect's
  // dependencies are complete and no suppression comment is needed — this app has
  // one that crashes the plugin outright (`Raketa02/Raketa#21`). It is also the
  // honest dependency: the cadence is what the timer is armed on, and a change of
  // moments that leaves the band alone has nothing to re-arm.
  const delay = repaintDelayMs(soonestMs(moments, now));

  useEffect(() => {
    if (delay === undefined) return;

    const tick = setTimeout(() => setNow(Date.now()), delay);
    return () => clearTimeout(tick);
  }, [delay, now]);

  return now;
}
