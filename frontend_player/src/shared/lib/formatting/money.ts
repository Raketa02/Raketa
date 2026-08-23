/**
 * Money, rendered exactly as `docs/value-formatting.md` writes it.
 *
 * That table is repo-wide and deliberately outside both clients: the backend
 * never formats, so each client formats, and under ADR-0005 they share no code to
 * do it with. The duplication is safe because there is no *rule* in it — only the
 * risk that the two drift — and this file is this app's half of the agreement.
 *
 * `38,00 zł`: comma decimal, **always** two decimals, a **non-breaking** space
 * before `zł`, a non-breaking space as the thousands separator, U+2212 for a
 * negative, and a zero that renders rather than being omitted.
 *
 * **Neither `Intl.NumberFormat` nor `toFixed`**, both named as refusals in that
 * table. `Intl` is locale-dependent at runtime and gives different output per ICU
 * build, so one value can render two ways on two phones; `toFixed` rounds
 * half-to-even in some engines and half-up in others, and reintroduces a float
 * into a number that arrived as exact integer grosze (ADR-0023). The arithmetic
 * below is integer throughout and there is nothing to round: grosze are already
 * the smallest unit.
 *
 * Lives in `shared/` rather than in the Now feature because it is not Now's — a
 * price on a card, a price on a booking and a price in the club console's future
 * are one rendering, and a second copy in a feature is how the comma becomes a
 * dot on one screen.
 */

/**
 * The currencies this app renders.
 *
 * Narrower than a bare ISO-4217 string on purpose, and narrower on purpose than
 * whatever the wire may one day carry: a mapper assigning a widened wire union to
 * this fails `pnpm typecheck`, which is where a second market has to be met — in
 * a diff, beside the row this table would need.
 */
export type Currency = 'PLN';

/** An amount in the currency's smallest unit, with the currency beside it. */
export interface Money {
  /** Integer grosze. Never a float, never a major-unit amount. */
  readonly amount: number;
  readonly currency: Currency;
}

/** U+2212 MINUS SIGN. At small sizes a hyphen beside a digit is nearly invisible. */
const MINUS = '−';

/** U+00A0. Both spaces in a price are non-breaking, so a price never wraps mid-number. */
const NBSP = ' ';

const SUFFIX: Readonly<Record<Currency, string>> = { PLN: 'zł' };

/** How many minor units make one major one. A second currency adds a row. */
const MINOR_UNITS: Readonly<Record<Currency, number>> = { PLN: 100 };

/**
 * `38,00 zł` — the whole rendering, suffix included.
 *
 * A non-integer `amount` is a caller bug rather than a rounding question, so it is
 * truncated toward zero rather than rounded: rounding would invent a value the
 * ledger never held, and every real amount reaches here as an integer already.
 */
export function formatMoney({ amount, currency }: Money): string {
  return `${formatAmount({ amount, currency })}${NBSP}${SUFFIX[currency]}`;
}

/**
 * `2 474,25` — the figure with no suffix.
 *
 * The table's *"Money, inside a tile"* row: the `zł` is dropped only where the
 * label already carries it, so this is never the default and a caller reaches for
 * it by naming the case.
 */
export function formatAmount({ amount, currency }: Money): string {
  const minor = MINOR_UNITS[currency];
  const whole = Math.trunc(Math.abs(Math.trunc(amount)) / minor);
  const fraction = Math.abs(Math.trunc(amount)) % minor;

  const sign = amount < 0 ? MINUS : '';
  return `${sign}${group(whole)},${String(fraction).padStart(String(minor).length - 1, '0')}`;
}

/** Thousands separated by a non-breaking space, never by a comma. */
function group(whole: number): string {
  const digits = String(whole);
  let out = '';
  for (let i = 0; i < digits.length; i += 1) {
    // Count from the right: a separator goes before every third digit that is not
    // the first one written.
    const fromRight = digits.length - i;
    if (i > 0 && fromRight % 3 === 0) out += NBSP;
    out += digits[i];
  }
  return out;
}
