/**
 * **The exact string a value becomes** (`docs/value-formatting.md`), for the values every page
 * may draw. No `Intl.NumberFormat` and no `toFixed`: both depend on the engine, and a price
 * arrives exact.
 */

/** Grosze in a złoty: the wire's unit is the grosz. */
const GROSZE = 100;

/** Below nought: U+2212, never a hyphen, which beside a digit at small sizes is nearly lost. */
const MINUS = '\u2212';

/** Between groups of three figures: a space a line never breaks at. */
const NO_BREAK_SPACE = '\u00a0';

/**
 * Whole złoty of five figures or more in threes, as Polish sets them: `12 840`, `126 000`. Four
 * figures stay whole, `1076`.
 */
function grouped(whole: number): string {
  const figures = String(whole);
  return figures.length < 5 ? figures : figures.replace(/\B(?=(\d{3})+$)/g, NO_BREAK_SPACE);
}

/**
 * Grosze as złoty, the whole złoty written by `whole`: the decimal comma, and the grosze only
 * when there are some.
 */
function inZloty(grosze: number, whole: (zloty: number) => string): string {
  const rest = grosze % GROSZE;
  const zloty = whole(Math.trunc(grosze / GROSZE));
  return rest === 0 ? zloty : `${zloty},${String(rest).padStart(2, '0')}`;
}

/**
 * **Money, from the wire's grosze**: `140 zł`, `142,50 zł`, `12 840 zł`, `−6 zł`. The decimal
 * comma, a space before the unit, and the grosze only when there are some, as the player app
 * writes a share; a sum of five figures or more in threes; below nought, U+2212.
 */
export function formatZloty(grosze: number): string {
  return `${grosze < 0 ? MINUS : ''}${inZloty(Math.abs(grosze), grouped)} zł`;
}

/** The figure alone, as a price box holds it: `140`, `142,50`. Never grouped: the box reads it back. */
export function zlotyFigure(grosze: number): string {
  return inZloty(grosze, String);
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
