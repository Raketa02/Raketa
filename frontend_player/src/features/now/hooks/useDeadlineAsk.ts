/**
 * The fourth ask: a countdown reaching zero.
 *
 * The client says *the clock you gave me has run out, and you will know more than
 * I do*, and fetches. It decides nothing and renders nothing of its own — a
 * visibly expired timer above a live-looking button is the one place where
 * *nothing until asked* looks broken rather than static (`ADR-0054`).
 *
 * **One wake, at a moment the server named — never a period.** There is no
 * interval here and none anywhere else in the feature; the walk in
 * `components/nowDiscipline.test.ts` is what keeps that true. The timeout is
 * re-armed whenever the screen changes, because a fresh screen names fresh
 * moments, and cleared when it goes away.
 *
 * It watches **both** slots a match card can carry — its own clock and a live
 * seat claim's five minutes. Which of the two a card *shows* is the card's rule;
 * which of them can run out is not a choice, so this needs no precedence to be
 * right.
 */

import { useEffect } from 'react';

import { msUntilNextZero } from '../domain/countdown';
import type { ComposedScreen } from '../domain/ComposedScreen';

export function useDeadlineAsk(screen: ComposedScreen | undefined, ask: () => void): void {
  useEffect(() => {
    if (screen === undefined) return;

    const left = msUntilNextZero(screen, Date.now());
    if (left === undefined) return;

    const wake = setTimeout(ask, left);
    return () => clearTimeout(wake);
  }, [screen, ask]);
}
