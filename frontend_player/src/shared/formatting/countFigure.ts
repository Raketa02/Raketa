/**
 * **A count, as drawn** — FOR YOU's count pill and *See all N ›*
 * ([#822](https://github.com/Raketa02/Raketa/issues/822); ADR-0205 §6), and the bell's and the
 * envelope's badges: the figure up to 99, ***99+*** past it.
 *
 * **A line's server never counts past 100**, which reads *100 or more*: a total is how many there are
 * to explore, and counting a busy city's pool whole is the cost ADR-0205 refused. So 100 is not a
 * figure to write, and *99+* is the most a line can truly say — on screen and to a listener alike.
 * The bell's and the envelope's counts are exact; they cap for the drawing's room, draw nothing at
 * nought (`bellFigure`, `envelopeFigure`) and say the exact number aloud. A line is hidden while its
 * read holds nobody, so it never has a nought to leave out.
 */

/** The most a count writes as a figure. */
const CEILING = 99;

/** *14* · *99+*. */
export function countFigure(count: number): string {
  return count > CEILING ? `${CEILING}+` : String(count);
}

/**
 * **A name with its count**, as a FOR YOU line is spoken — its title, then its count as drawn:
 * *Players at your level, 14*; the platform says *expanded* or *collapsed* after it. A count past 99 is
 * said as drawn, *99+*: there is no exact figure to say. No count, the name alone (Top 10).
 */
export function withCount(name: string, count: number | undefined): string {
  return count === undefined ? name : `${name}, ${countFigure(count)}`;
}
