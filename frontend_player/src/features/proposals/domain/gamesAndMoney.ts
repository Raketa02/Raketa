/**
 * **Games & money — a player's two limits** (You › Account; the screens A7.1; the mechanics §6.6;
 * [#554](https://github.com/Raketa02/Raketa/issues/554)), the backend's second Proposals aggregate
 * (#539).
 *
 * **Games per week**: once that many games are booked in a week, Monday to Sunday, the deck deals
 * nothing more for it. **Most I'll pay per game**: a card whose share is above it is never dealt;
 * *Off* is `null`. Both apply across sports and groups, which is why the deck reads them and a
 * change re-reads every deck.
 *
 * **The client holds neither range.** The read carries what the form offers — the stepper's least
 * and most, and the ceilings beside *Off* — so a range the server widens reaches the phone without
 * a release. What is decided here is only how a tap moves a value inside what was offered.
 */

/** What the stepper may be set to, inclusive. */
export interface GamesPerWeekRange {
  readonly least: number;
  readonly most: number;
}

/** The two limits as the server holds them, with what the form offers. */
export interface GamesAndMoney {
  readonly gamesPerWeek: number;
  /** In grosze — one of `ceilingChoicesGrosze` — or `null` for *Off*. */
  readonly mostIllPayGrosze: number | null;
  readonly gamesPerWeekRange: GamesPerWeekRange;
  /** The ceilings offered beside *Off*, in grosze, as the server lists them. */
  readonly ceilingChoicesGrosze: readonly number[];
}

/** The two values a save writes — both, every time, as the route takes them. */
export type Limits = Pick<GamesAndMoney, 'gamesPerWeek' | 'mostIllPayGrosze'>;

/** One press of the stepper: a game fewer, or a game more. */
export type Step = -1 | 1;

function clamped(value: number, { least, most }: GamesPerWeekRange): number {
  return Math.min(most, Math.max(least, value));
}

/** The games a week after one press — held inside the range, so a press at an end moves nothing. */
export function steppedGames(held: GamesAndMoney, by: Step): number {
  return clamped(held.gamesPerWeek + by, held.gamesPerWeekRange);
}

/** Whether a press would move the value — the stepper's end shuts its own button. */
export function canStep(held: GamesAndMoney, by: Step): boolean {
  return steppedGames(held, by) !== held.gamesPerWeek;
}

/** The two values of a read — what a save would send unchanged. */
export function limitsOf({ gamesPerWeek, mostIllPayGrosze }: Limits): Limits {
  return { gamesPerWeek, mostIllPayGrosze };
}

/** Whether two pairs are the same limits — a tap that lands on the saved pair sends nothing. */
export function sameLimits(a: Limits, b: Limits): boolean {
  return a.gamesPerWeek === b.gamesPerWeek && a.mostIllPayGrosze === b.mostIllPayGrosze;
}

export function withGames(held: GamesAndMoney, gamesPerWeek: number): GamesAndMoney {
  return { ...held, gamesPerWeek };
}

export function withCeiling(held: GamesAndMoney, mostIllPayGrosze: number | null): GamesAndMoney {
  return { ...held, mostIllPayGrosze };
}

/**
 * **The week's money bound** — the most a week of games can cost: the games times the most per
 * game (*up to 180 zł*, the screens A7.1). None while the ceiling is off, when only the games are
 * bounded.
 */
export function weeklyBoundGrosze(held: Limits): number | undefined {
  return held.mostIllPayGrosze === null ? undefined : held.gamesPerWeek * held.mostIllPayGrosze;
}
