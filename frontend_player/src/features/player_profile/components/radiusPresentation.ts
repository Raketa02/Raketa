/**
 * The words on the radius step.
 *
 * Two of them are the same fact: **the figure and the plain-word reading**. A figure is
 * exact and a reading is meaningful, and a player who does not think in kilometres gets
 * nothing at all from the first one — *12* and *40* are different kinds of decision, not
 * different numbers, and the line beneath the figure is where that is said.
 *
 * ## The bands are distances, not positions on a track
 *
 * The served minimum, maximum, step and default are product's and may be retuned without a
 * client release, so the reading is a function of *a distance* rather than of where along
 * the range it sits. A mapping expressed as thirds of the track would rename every band
 * the day the maximum moved, and a player whose radius had not changed would be told it
 * meant something else.
 *
 * That is also why the last band has no ceiling: whatever the bounds become, every
 * distance reads as something.
 *
 * ## The step says what the number does, in both directions
 *
 * A radius **filters when the player searches and weights when the engine proposes**
 * (`CONTEXT.md`) — the same number answering two questions. Saying only the first would
 * let a player set a small radius believing it removes them from everything; saying only
 * the second would make the control look advisory when a search obeys it exactly.
 */

import { topOfScale, type SearchRadiusBounds } from '../domain/searchRadius';

/**
 * The reading, as bands with a distance each ends at.
 *
 * Held in the phrasing a sentence would use, so the spoken form is the table and the line
 * on screen is the table with a capital on it — rather than two copies of the words, one
 * release away from disagreeing about what 12 kilometres is.
 *
 * In ascending order, and the last one is reached by everything above the one before it.
 */
const BANDS: readonly { readonly upToKm: number; readonly phrase: string }[] = [
  { upToKm: 2, phrase: 'just your own neighbourhood' },
  { upToKm: 5, phrase: 'a short ride away' },
  { upToKm: 15, phrase: 'across your town' },
  { upToKm: 30, phrase: 'your town and the ones around it' },
];

const BEYOND = 'a long drive out';

/** The value, with its unit — a bare number on a screen about distance is not a reading. */
export function radiusFigure(radiusKm: number): string {
  return `${radiusKm} km`;
}

/**
 * The widest figure the served bounds can produce, for the box that reserves its width.
 *
 * The top of the *scale* rather than the served maximum: the track's far end is the last
 * value on a step, and that is the widest figure a player can actually reach.
 */
export function widestRadiusFigure(bounds: SearchRadiusBounds): string {
  return radiusFigure(topOfScale(bounds));
}

/** The line beneath the figure: what this distance means, in words. */
export function radiusWords(radiusKm: number): string {
  const phrase = bandPhrase(radiusKm);
  return `${phrase.charAt(0).toUpperCase()}${phrase.slice(1)}`;
}

/**
 * The figure and the words as **one** announcement.
 *
 * The unit is spelled out because `km` is read as two letters by some screen readers, and
 * it is singular at one kilometre for the same reason every other figure in this app is
 * written the way a person would say it.
 */
export function spokenRadius(radiusKm: number): string {
  const unit = radiusKm === 1 ? 'kilometre' : 'kilometres';
  return `${radiusKm} ${unit}, ${bandPhrase(radiusKm)}`;
}

function bandPhrase(radiusKm: number): string {
  return BANDS.find((band) => radiusKm <= band.upToKm)?.phrase ?? BEYOND;
}

/** What the slider is called, for whoever cannot see the heading above it. */
export const RADIUS_LABEL = 'How far to look';

/** The one sentence about what the number does — both of the things it does. */
export const RADIUS_TITLE = 'What this distance does';

export const RADIUS_BODY =
  'When you search, this is the edge of it — nobody further out comes back. When Raketa ' +
  'suggests a game, players closer to you come first, and this is how it works out what ' +
  'close means.';
