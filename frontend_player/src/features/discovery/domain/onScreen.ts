/**
 * **The cards a row has reported on screen today** — once per card, row and Warsaw day
 * ([#804](https://github.com/Raketa02/Raketa/issues/804); the Home rows mechanics §9.2, call 2; the
 * backend's #796).
 *
 * A card on *Same competitive level* or *Same vibe* that comes at least half on screen counts one day
 * towards resting there; on its fifth different day without an add, it gives its place to a fresh
 * match. **The server counts a day once whatever the phone sends**, so this is not what makes the
 * count right — it is what keeps the phone from saying the same thing at every frame of a scroll.
 *
 * - **One ledger per row**: each row keeps its own count, so Karol seen in both is told twice.
 * - **A new Warsaw day starts it empty**: a card seen yesterday and again today is told again. A day
 *   is the platform's (`shared/date`), never the phone's zone — the server's day is Warsaw's.
 * - **Batched**: the cards seen are owed until the batch window closes, then told in one report —
 *   at most the route's fifty, in the order they were seen.
 * - **A report that fails leaves its cards owed**, at the front, so the next report tells them with
 *   whatever came on screen since. Nothing is said to the player either way.
 * - **A failed report's cards are not carried into the next day**: what is still owed when the first
 *   card of a new Warsaw day is seen is dropped, since the server would count it as that day. The
 *   batch window open at midnight is still told as it closes (`use-cases/onScreen.ts`).
 */

/** The two rows whose cards rest — each with its own count. New in Raketa and See all rest nobody. */
export type RestingRow = 'SAME_LEVEL' | 'SAME_VIBE';

/** How long the cards that come on screen are gathered before one report says them all. */
export const REPORT_BATCH_MS = 2_000;

/** The most cards one report names — the route's own cap. */
export const REPORT_AT_MOST = 50;

/** One row's reports, on one Warsaw day. */
export interface OnScreenLedger {
  /** `YYYY-MM-DD` in Warsaw. */
  readonly day: string;
  /** Told, and the server took it. */
  readonly told: ReadonlySet<string>;
  /** In a report on its way. */
  readonly telling: ReadonlySet<string>;
  /** Seen and not yet told, in the order seen. */
  readonly owed: readonly string[];
}

/** A day nothing has been seen on yet. */
export function freshLedger(day: string): OnScreenLedger {
  return { day, told: new Set(), telling: new Set(), owed: [] };
}

/** The ledger on `day` — this one, or, on a new day, an empty one. */
export function onDay(ledger: OnScreenLedger, day: string): OnScreenLedger {
  return ledger.day === day ? ledger : freshLedger(day);
}

/**
 * **These cards came on screen.** Each not told today, nor on its way, is owed; and a report is due
 * when any card just seen is owed — a new one, or one whose report failed.
 */
export function cameOnScreen(
  ledger: OnScreenLedger,
  playerIds: readonly string[],
): { readonly ledger: OnScreenLedger; readonly due: boolean } {
  const owed = [...ledger.owed];
  let due = false;
  for (const id of playerIds) {
    if (ledger.told.has(id) || ledger.telling.has(id)) continue;
    due = true;
    if (!owed.includes(id)) owed.push(id);
  }
  return { ledger: due ? { ...ledger, owed } : ledger, due };
}

/** **The next report** — up to fifty owed cards, in the order seen, now on their way. */
export function nextReport(ledger: OnScreenLedger): {
  readonly ledger: OnScreenLedger;
  readonly playerIds: readonly string[];
} {
  const playerIds = ledger.owed.slice(0, REPORT_AT_MOST);
  if (playerIds.length === 0) return { ledger, playerIds };
  return {
    ledger: {
      ...ledger,
      telling: new Set([...ledger.telling, ...playerIds]),
      owed: ledger.owed.slice(REPORT_AT_MOST),
    },
    playerIds,
  };
}

/**
 * **A report came back** — taken, so its cards are told today; or refused, timed out or never sent,
 * so they are owed again, ahead of anything seen since.
 */
export function reportAnswered(
  ledger: OnScreenLedger,
  playerIds: readonly string[],
  taken: boolean,
): OnScreenLedger {
  const telling = new Set([...ledger.telling].filter((id) => !playerIds.includes(id)));
  return taken
    ? { ...ledger, telling, told: new Set([...ledger.told, ...playerIds]) }
    : {
        ...ledger,
        telling,
        owed: [...playerIds, ...ledger.owed.filter((id) => !playerIds.includes(id))],
      };
}
