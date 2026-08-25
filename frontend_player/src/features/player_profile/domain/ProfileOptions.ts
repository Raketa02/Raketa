/**
 * Everything the profile steps need in order to be **drawn** — the vocabulary they offer
 * and the numbers they enforce.
 *
 * Served rather than restated (`GET /player-profile/options`), following the precedent the
 * sports registry set: a closed set the backend owns, read over the API so that no client
 * hardcodes it and the picker cannot drift from what the commit re-validates against.
 *
 * One object for one round trip. A field is only ever added, and only once there is a
 * control to hold it — mapping a shape the app cannot yet use would be a shape invented
 * before anything reads it.
 */

import type { SearchRadiusBounds } from './searchRadius';
import type { SocialTagSelectionBounds } from './socialTagSelection';
import type { SocialTagVocabulary } from './SocialTag';

export interface ProfileOptions {
  /** The three groups and their tags, in the order they are to be rendered. */
  readonly socialTagGroups: SocialTagVocabulary;
  /** How many of them a profile must hold. Both ends included. */
  readonly socialTagSelection: SocialTagSelectionBounds;
  /** How far out a player may ask to look, and where the slider opens. */
  readonly searchRadius: SearchRadiusBounds;
}
