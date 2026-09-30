/**
 * **Every sentence Games & money says** — the row on the You tab, the two cards and the bound under
 * them ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7, A7.1; mocks 37–39).
 *
 * Import-light — shared formatting only — because the shell composes the row into the You tab at
 * module load, and `deckPresentation`'s imports reach back into features that reach the shell.
 *
 * **The row and the bound say the same limits**: *At most 4 games a week · up to 180 zł* on the
 * row, *Your bound: at most **4 games** · up to **180 zł** a week.* under the cards. The money is
 * the week's (`weeklyBoundGrosze`) — the games times the most per game — and is said only once a
 * ceiling is set.
 */

import { counted } from '@/shared/formatting/counted';
import { formatZloty } from '@/shared/formatting/ratingFormat';

import { weeklyBoundGrosze, type GamesPerWeekRange, type Limits } from '../domain/gamesAndMoney';

/** The screen's and the row's title. */
export const GAMES_AND_MONEY_TITLE = 'Games & money';

const DOT = ' · ';

export const GAMES_AND_MONEY_COPY = {
  loading: 'Reading your limits…',
  games: {
    title: 'Games per week',
    fewer: 'Fewer games a week',
    more: 'More games a week',
  },
  ceiling: {
    title: 'Most I’ll pay per game',
    line: 'Off by default',
    off: 'Off',
    offLine: 'Every card is shown, whatever its share.',
  },
  /**
   * A refused save, by its code — the form offered a value the server no longer does. The pair is
   * read again, so the words say what the player now sees.
   */
  refused: {
    games_per_week_out_of_range:
      'That many games a week isn’t offered any more — here is what’s saved.',
    most_ill_pay_not_offered: 'That price isn’t offered any more — here is what’s saved.',
  } as Readonly<Record<string, string>>,
} as const;

/** *4 games* · *1 game*. */
function games(count: number): string {
  return counted(count, 'game', 'games');
}

/** *Mon–Sun · 1 to 7* — the stepper's title's second line, off the range the server offers. */
export function rangeLine({ least, most }: GamesPerWeekRange): string {
  return `Mon–Sun${DOT}${least} to ${most}`;
}

/** What the cap does to the week's other yeses — singular at one. */
export function gamesLine(gamesPerWeek: number): string {
  return gamesPerWeek === 1
    ? 'Once it is booked, your other yeses that week pause — they come back if the game is called off.'
    : 'Once they are booked, your other yeses that week pause — they come back if a game is called off.';
}

/** *4 games a week* — the stepper's value, spoken. */
export function gamesSpoken(gamesPerWeek: number): string {
  return `${games(gamesPerWeek)} a week`;
}

/** A ceiling's chip: *Off*, or the price in whole złoty. */
export function ceilingChipLabel(grosze: number | null): string {
  return grosze === null ? GAMES_AND_MONEY_COPY.ceiling.off : formatZloty(grosze);
}

/** What the ceiling does to the deck — nothing while off, or the price it hides above. */
export function ceilingLine(grosze: number | null): string {
  return grosze === null
    ? GAMES_AND_MONEY_COPY.ceiling.offLine
    : `Cards above ${formatZloty(grosze)} are never shown to you.`;
}

/** *At most 4 games a week*, and *· up to 180 zł* once a ceiling is set — the row's line. */
export function gamesAndMoneyRowLine(limits: Limits): string {
  const line = `At most ${games(limits.gamesPerWeek)} a week`;
  const bound = weeklyBoundGrosze(limits);
  return bound === undefined ? line : `${line}${DOT}up to ${formatZloty(bound)}`;
}

/** One run of the bound's line — bold where the mock sets the limits bold. */
export interface BoundRun {
  readonly text: string;
  readonly strong?: boolean;
}

/** *Your bound: at most **4 games** a week.* — or *… **4 games** · up to **180 zł** a week.* */
export function boundRuns(limits: Limits): readonly BoundRun[] {
  const bound = weeklyBoundGrosze(limits);
  return [
    { text: 'Your bound: at most ' },
    { text: games(limits.gamesPerWeek), strong: true },
    ...(bound === undefined
      ? []
      : [{ text: `${DOT}up to ` }, { text: formatZloty(bound), strong: true }]),
    { text: ' a week.' },
  ];
}

/** The bound as one string — its spoken form, and what a suite reads. */
export function boundText(limits: Limits): string {
  return boundRuns(limits)
    .map((run) => run.text)
    .join('');
}
