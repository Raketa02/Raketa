/**
 * The screen's one repaint clock.
 *
 * **A repaint, and never a fetch.** `ADR-0088` states the distinction and states
 * that it is stated nowhere else: `ADR-0054` owns *refreshing* and names reaching
 * zero as one of its four occasions, so a repaint cadence must not become a fifth.
 * This module therefore cannot reach Query at all — it holds a number and hands it
 * out — and `components/nowDiscipline.test.ts` walks it to keep that true. The one
 * timer that *does* ask is `useDeadlineAsk`, and it is a one-shot wake at a moment
 * the server named.
 *
 * **One screen-wide clock, not one per card.** `ADR-0088` records that as an
 * implementation note *"because a dozen cards each holding their own interval is
 * the version that gets built by accident"*. Making it a hook the screen calls
 * once, rather than something a card could call, is what stops that: no component
 * arms a timer, and the walk asserts it.
 *
 * **The cadence follows the soonest live moment on the screen** — one second while
 * anything is inside `SECONDS_BAND_MS`, one minute otherwise. It is the same
 * constant the label reads, so the screen never draws a digit it will not refresh.
 * Nothing is armed at all when no moment is still ahead: a screen of cancelled
 * cards costs a phone in a pocket nothing.
 *
 * **`setTimeout`, re-armed, rather than `setInterval`.** The cadence changes as
 * the screen crosses into the band, and an interval would have to be torn down and
 * rebuilt to change it anyway — so the loop is written where its condition is read.
 */

import { useEffect, useState } from 'react';

import type { ComposedScreen } from '../domain/ComposedScreen';
import { msUntilNextZero, repaintDelayMs } from '../domain/countdown';

/**
 * The instant every countdown on the screen subtracts from.
 *
 * One value for the whole screen, so two cards can never disagree about what time
 * it is by a render.
 */
export function useRepaintClock(screen: ComposedScreen | undefined): number {
  const [now, setNow] = useState(() => Date.now());

  // A fresh screen is a fresh reading. Without this a composed screen arriving
  // after a pull would be drawn against whatever the last repaint left behind —
  // up to a minute stale, on the one occasion the player explicitly asked.
  // Keyed on the screen alone, so it runs once per answer and cannot loop.
  useEffect(() => {
    setNow(Date.now());
  }, [screen]);

  useEffect(() => {
    if (screen === undefined) return;

    const delay = repaintDelayMs(msUntilNextZero(screen, now));
    if (delay === undefined) return;

    const tick = setTimeout(() => setNow(Date.now()), delay);
    return () => clearTimeout(tick);
  }, [screen, now]);

  return now;
}
