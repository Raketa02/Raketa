/**
 * The value-formatting table, asserted character by character.
 *
 * Every case below is a row of `docs/value-formatting.md`, and the three the file
 * itself calls out as *"things that will be got wrong otherwise"* are asserted on
 * the code point rather than on something that looks right in a diff: an ordinary
 * space and a non-breaking one are indistinguishable on screen, and a hyphen and
 * a minus sign nearly so.
 */

import { formatAmount, formatMoney } from './money';

const NBSP = ' ';
const MINUS = '−';

describe('money renders as the shared table writes it', () => {
  it('renders an ordinary price with a comma and two decimals', () => {
    expect(formatMoney({ amount: 3800, currency: 'PLN' })).toBe(`38,00${NBSP}zł`);
  });

  it('renders the fractional part it was given, never a rounded one', () => {
    expect(formatMoney({ amount: 3825, currency: 'PLN' })).toBe(`38,25${NBSP}zł`);
    expect(formatMoney({ amount: 3805, currency: 'PLN' })).toBe(`38,05${NBSP}zł`);
  });

  it('separates thousands with a non-breaking space, never a comma', () => {
    expect(formatMoney({ amount: 247425, currency: 'PLN' })).toBe(`2${NBSP}474,25${NBSP}zł`);
    expect(formatMoney({ amount: 123456789, currency: 'PLN' })).toBe(
      `1${NBSP}234${NBSP}567,89${NBSP}zł`,
    );
  });

  it('renders a zero rather than omitting it', () => {
    expect(formatMoney({ amount: 0, currency: 'PLN' })).toBe(`0,00${NBSP}zł`);
  });

  it('renders a negative with U+2212 and not a hyphen', () => {
    const rendered = formatMoney({ amount: -3800, currency: 'PLN' });

    expect(rendered).toBe(`${MINUS}38,00${NBSP}zł`);
    expect(rendered).not.toContain('-');
  });

  it('puts a non-breaking space before the suffix', () => {
    expect(formatMoney({ amount: 3800, currency: 'PLN' })).not.toContain(' zł');
  });

  it('drops the suffix only where the caller names the case', () => {
    expect(formatAmount({ amount: 247425, currency: 'PLN' })).toBe(`2${NBSP}474,25`);
    expect(formatAmount({ amount: 247425, currency: 'PLN' })).not.toContain('zł');
  });
});
