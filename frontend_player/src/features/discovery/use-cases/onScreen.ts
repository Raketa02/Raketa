/**
 * **A row's reporter** — the cards that came on screen, told in batches, once per card and Warsaw
 * day ([#804](https://github.com/Rakieta02/Rakieta/issues/804); the rules are `domain/onScreen.ts`).
 *
 * The first owed card opens a batch window of `REPORT_BATCH_MS`; when it closes, one report tells
 * everything owed — the rest of the scroll's cards with it. A report that fails leaves its cards
 * owed for the next one, which the next card seen that is still owed opens: **never a retry on a
 * timer of its own**, and nothing said to the player. **The window open at Warsaw's midnight is
 * still told as it closes** — the server counts it on its own day — but a report answered after
 * the day turned changes nothing on the new day's ledger.
 *
 * **The row going stops it**: an open window closes with nothing told, and a report on its way is
 * called off, so nothing outlives the row's place on Home — sign-out included.
 *
 * What a day is and how a window waits are handed in (`ReporterClock`), so the rules run without a
 * screen or a real clock.
 */

import { postOnScreen } from '../api/discoveryApi';
import {
  REPORT_BATCH_MS,
  cameOnScreen,
  freshLedger,
  nextReport,
  onDay,
  reportAnswered,
  type OnScreenLedger,
  type RestingRow,
} from '../domain/onScreen';
import { toOnScreenReport } from '../mappers/discoveryMappers';

export interface OnScreenReporter {
  /** These cards are at least half on screen in the row, now. */
  readonly seen: (playerIds: readonly string[]) => void;
  /** The row is gone: an open window closes with nothing told, a report on its way is called off. */
  readonly stop: () => void;
}

export interface ReporterClock {
  /** Today in Warsaw, `YYYY-MM-DD`. */
  readonly today: () => string;
  /** Run this once `ms` have passed; answers how to call it off. */
  readonly after: (ms: number, run: () => void) => () => void;
}

export function onScreenReporter(row: RestingRow, clock: ReporterClock): OnScreenReporter {
  let ledger: OnScreenLedger = freshLedger(clock.today());
  let closeBatch: (() => void) | undefined;
  const reports = new AbortController();

  const tell = () => {
    closeBatch = undefined;
    const next = nextReport(ledger);
    ledger = next.ledger;
    if (next.playerIds.length === 0) return;
    const day = ledger.day;
    const answered = (taken: boolean) => {
      if (!reports.signal.aborted && ledger.day === day) {
        ledger = reportAnswered(ledger, next.playerIds, taken);
      }
    };
    void postOnScreen(toOnScreenReport(row, next.playerIds), { signal: reports.signal }).then(
      () => answered(true),
      () => answered(false),
    );
  };

  return {
    seen: (playerIds) => {
      if (reports.signal.aborted) return;
      const now = cameOnScreen(onDay(ledger, clock.today()), playerIds);
      ledger = now.ledger;
      if (now.due && closeBatch === undefined) closeBatch = clock.after(REPORT_BATCH_MS, tell);
    },
    stop: () => {
      reports.abort();
      closeBatch?.();
      closeBatch = undefined;
    },
  };
}
