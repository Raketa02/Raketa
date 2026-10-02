/**
 * **The exact string a value becomes** (`docs/value-formatting.md`), for the values every page
 * may draw. No `Intl.NumberFormat` and no `toFixed`: both depend on the engine, and a price
 * arrives exact.
 */

/** Grosze in a złoty: the wire's unit is the grosz. */
const GROSZE = 100;

/**
 * **Money, from the wire's grosze**: `140 zł`, `142,50 zł`. The decimal comma, a space before
 * the unit, and the grosze only when there are some, as the player app writes a share.
 */
export function formatZloty(grosze: number): string {
  return `${zlotyFigure(grosze)} zł`;
}

/** The figure alone, as a price box holds it: `140`, `142,50`. */
export function zlotyFigure(grosze: number): string {
  const whole = Math.trunc(grosze / GROSZE);
  const rest = grosze % GROSZE;
  return rest === 0 ? String(whole) : `${whole},${String(rest).padStart(2, '0')}`;
}

/**
 * **Grosze from what a desk typed**: `140`, `142,50` or `142.5`, or `null` for anything that is
 * not an amount of złoty to the grosz.
 */
export function parseZloty(typed: string): number | null {
  const match = /^(\d{1,6})(?:[.,](\d{1,2}))?$/.exec(typed.trim());
  if (match === null) return null;
  const [, whole = '', rest = ''] = match;
  return Number(whole) * GROSZE + Number(rest.padEnd(2, '0'));
}

/** An hour of the wall clock: `07:00`. */
export function clock(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`;
}
