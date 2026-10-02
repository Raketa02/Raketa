/**
 * **What the Money page is asked for**: the month, in its address, `/money?month=2026-03`. This
 * month is no month at all, since the backend knows which it is.
 */

/** The page's address, read. */
export interface MonthQuery {
  /** A month, `2026-03`; `null` for this month. */
  readonly month: string | null;
}

const MONEY_PATH = '/money';

const MONTH = /^(\d{4})-(0[1-9]|1[0-2])$/;

/** A month written `2026-03`, or `null`: `2026-13` is none, and neither is one before 2000. */
export function realMonth(text: string): string | null {
  const match = MONTH.exec(text);
  return match !== null && Number(match[1]) >= 2000 ? text : null;
}

/** A month's year and its number in the year, 1 for January: `2026-03` is 2026 and 3. */
export function monthParts(month: string): { readonly year: number; readonly number: number } {
  const [year = 0, number = 1] = month.split('-').map(Number);
  return { year, number };
}

/** The month `months` after a month (before it, when negative). */
export function monthAfter(month: string, months: number): string {
  const { year, number } = monthParts(month);
  const at = new Date(Date.UTC(year, number - 1 + months, 1));
  return at.toISOString().slice(0, 7);
}

/** The page's address as asked: anything it does not understand reads as this month. */
export function readMonthQuery(
  params: Readonly<Record<string, string | string[] | undefined>>,
): MonthQuery {
  const { month } = params;
  return { month: typeof month === 'string' ? realMonth(month) : null };
}

/** The page's address for a month: this month is left out. */
export function monthHref(month: string | null): string {
  return month === null ? MONEY_PATH : `${MONEY_PATH}?month=${month}`;
}
