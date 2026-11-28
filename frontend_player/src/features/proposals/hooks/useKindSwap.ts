/**
 * **The deck as the Games tab draws it, and a swap's clock** — the kind chosen, or while a pick's
 * stack goes out the kind it leaves ([#863](https://github.com/Rakieta02/Rakieta/issues/863); the
 * rules are `domain/kindSwap.ts`).
 *
 * **The kind chosen is read from the pick on**, whatever is drawn: the stack going out holds the
 * kind it leaves on screen for its beat, and the read of the kind picked sets out at the press, as
 * it always has — the swap costs that read no time. Both are `useGroupDeck`'s, corrected by the
 * intent; with nothing swapping they are one read.
 *
 * **The clock.** The stack goes out over `motion.kindSwap.out`; then the kind picked comes in over
 * `.in` from the moment its read is in — at once where it was read before, or when the read lands —
 * and the swap is over. A read that comes back refused ends it there: the deck draws today's failure
 * with its retry, and a retry that lands draws the deck directly. Each timer is set in the effect of
 * the commit that draws its phase — the commit whose effect starts that phase's motion
 * (`KindSwap.tsx`) — so a test's clock moves both together.
 *
 * **A card still in flight holds the kind it leaves** (`flying`; the code review's catch): the flight
 * outlasts the beat, and the card it carries leaves that kind's read and carries that kind's answer —
 * so the kind picked comes in once the beat has run *and* the card has flown, the beat timed from
 * when the stack began going out.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { kindDrawn, type KindSwap } from '../domain/kindSwap';
import type { GameKind } from '../domain/vocabulary';

import { useGroupDeck } from './useGroupDeck';
import { useLatest } from './useLatest';

const { out: OUT, in: IN } = theme.motion.kindSwap;

/**
 * The deck as drawn, and the swap under way. `flying` is whether a card of the kind drawn is still
 * in flight.
 */
export function useKindSwap(groupId: string, sport: Sport, chosen: GameKind, flying: boolean) {
  const [swap, setSwap] = useState<KindSwap | undefined>(undefined);
  // The kind chosen, read from the pick on — see the module note.
  useGroupDeck(groupId, sport, chosen);
  const { read, kind } = useGroupDeck(groupId, sport, kindDrawn(swap, chosen));
  const landed = read.data !== undefined;
  const failed = !landed && read.error !== null;

  /** When the stack began going out — its beat is timed from there, whatever holds it. */
  const outSince = useRef(0);
  const drawn = useLatest(swap);
  const begin = useCallback(
    (next: KindSwap) => {
      if (next.phase === 'out' && drawn.current?.phase !== 'out') outSince.current = Date.now();
      setSwap(next);
    },
    [drawn],
  );

  const phase = swap?.phase;
  // Going out: over once the beat has run and no card of the kind left is in flight.
  useEffect(() => {
    if (phase !== 'out' || flying) return undefined;
    const outOver = setTimeout(
      () => setSwap((was) => (was === undefined ? was : { ...was, phase: 'in' })),
      Math.max(0, outSince.current + OUT - Date.now()),
    );
    return () => clearTimeout(outOver);
  }, [phase, flying]);
  // Coming in: from the moment the kind picked is read, and over at once if its read is refused.
  useEffect(() => {
    if (phase !== 'in') return undefined;
    if (failed) {
      setSwap(undefined);
      return undefined;
    }
    if (!landed) return undefined;
    const inOver = setTimeout(() => setSwap(undefined), IN);
    return () => clearTimeout(inOver);
  }, [phase, landed, failed]);

  /** Stop the swap — a change of sport leaves the deck it was swapping. */
  const end = useCallback(() => setSwap(undefined), []);

  return {
    /** The read of the kind drawn, and that kind — the one an answer is for. */
    read,
    kind,
    /** The swap under way — none while the deck stands still. */
    swap,
    /** Begin one, or change where one lands (`swapTo`). */
    begin,
    end,
  };
}
