/**
 * **A Home row's on-screen reports** ([#804](https://github.com/Rakieta02/Rakieta/issues/804); the Home
 * rows mechanics §9.2) — what the row hands its rail as `onScreen`, so every card the rail says is at
 * least half on screen is told once that Warsaw day (`use-cases/onScreen.ts`).
 *
 * **The reporter lives as long as the row's place on Home**, called by the row before it knows
 * whether it has anybody to draw: Home stays mounted under every screen pushed over it and every
 * other tab, and goes at sign-out — so the cards told today are one account's. A Home drawn again
 * starts a new ledger and may tell a card the server already counted today, which it counts once.
 * **It is made at the first card seen**, not in an effect: the rail's effects run before its row's,
 * and a card seen first would otherwise find no reporter there.
 *
 * The day is the platform's, Warsaw's (`shared/date`), read off the clock at each card.
 */

import { useCallback, useEffect, useRef } from 'react';

import { platformDay } from '@/shared/date/platformZone';

import type { RestingRow } from '../domain/onScreen';
import { onScreenReporter, type OnScreenReporter, type ReporterClock } from '../use-cases/onScreen';

const CLOCK: ReporterClock = {
  today: () => platformDay(new Date().toISOString()) ?? '',
  after: (ms, run) => {
    const timer = setTimeout(run, ms);
    return () => clearTimeout(timer);
  },
};

export function useOnScreenReports(
  row: RestingRow,
): (people: readonly { readonly playerId: string }[]) => void {
  const reporter = useRef<OnScreenReporter>();

  useEffect(
    () => () => {
      reporter.current?.stop();
      reporter.current = undefined;
    },
    [row],
  );

  return useCallback(
    (people) => {
      reporter.current ??= onScreenReporter(row, CLOCK);
      reporter.current.seen(people.map((one) => one.playerId));
    },
    [row],
  );
}
