/**
 * How a value becomes a string, per the repo-wide `docs/value-formatting.md`.
 *
 * A semantic home rather than a `utils/` bucket: this directory holds renderings
 * of *values*, and grows one file per kind — money today, a duration and a day
 * when a screen needs one.
 */

export { formatAmount, formatMoney, type Currency, type Money } from './money';
