/**
 * **The deck's clock** — the instant the deck was read, moving on while a card on it counts down
 * (the screens A2.3: *45 min under an hour … at the deadline the card leaves silently*).
 *
 * The deck's read carries no `read_at`, so the countdown starts from the moment it was received
 * (`dataUpdatedAt`), and a card that counts down — its deadline under a day away — needs the clock
 * to keep going after that, or *45 min* would stand still and a card past its deadline would stay
 * on the stage until the next read. So while one does, the clock ticks every `TICK`; otherwise it
 * stands at the read, and a deck with nothing near its deadline re-renders for nothing.
 *
 * **A drawing, never a decision.** The server stays the authority on whether a game is over: a
 * card this clock has dropped is one the server would refuse with `proposal_is_over`, and a card it
 * still shows past a deadline the phone's clock disagrees about is answered by the server's word.
 */

import { useEffect, useState } from 'react';

/** Often enough that a minute's countdown is never a minute late by more than half of one. */
const TICK = 30_000;

export function useDeckClock(readAt: number, ticking: boolean): number {
  const [now, setNow] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!ticking) return;
    const timer = setInterval(() => setNow(Date.now()), TICK);
    return () => clearInterval(timer);
  }, [ticking]);

  // A newer read is always the later instant; a tick before it is stale.
  return Math.max(readAt, now ?? readAt);
}
