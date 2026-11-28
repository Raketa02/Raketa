/**
 * **A friend's ask for a level, as a card on Home** ([#765](https://github.com/Rakieta02/Rakieta/issues/765);
 * the friends screens §6.4; the words §29.5; ADR-0202 §4 as amended 2026-11-07).
 *
 * One card per sport, naming every friend whose ask in it waits on the reader, newest first. Which
 * sentence it says is a rule of the count, never of the screen: **one** asker is named, **two** are
 * named together and the line says *they*, and **three or more** name the two newest and count the
 * rest, so the title stays one line. Up to three faces are drawn.
 */

/** Which of the card's sentences — keyed in the copy module, so a form with no words fails to compile. */
export type AskersForm = 'one' | 'two' | 'more';

/** How many askers' faces a card draws (the screens §6.4). */
export const LEVEL_ASK_FACES = 3;

/** @param count the askers on the card — never fewer than one. */
export function askersFormOf(count: number): AskersForm {
  if (count <= 1) return 'one';
  return count === 2 ? 'two' : 'more';
}

/** The askers drawn as faces, in the order served: the newest, up to three. */
export function facesOnTheCard<T>(askers: readonly T[]): readonly T[] {
  return askers.slice(0, LEVEL_ASK_FACES);
}
