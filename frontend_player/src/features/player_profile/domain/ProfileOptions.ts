/**
 * Everything the profile steps need in order to be **drawn** — the vocabulary they offer
 * and the numbers they enforce.
 *
 * Served rather than restated (`GET /player-profile/options`), following the precedent the
 * sports registry set: a closed set the backend owns, read over the API so that no client
 * hardcodes it and the picker cannot drift from what the commit re-validates against.
 *
 * One object for one round trip. The steps that need the rest of it — the Search radius
 * bounds — add their own field here when they are built; a field is only ever added, and
 * mapping one the app cannot yet use would be a shape invented before there is a control
 * to hold it.
 */

import type { SocialTagSelectionBounds } from './socialTagSelection';
import type { SocialTagVocabulary } from './SocialTag';

export interface ProfileOptions {
  /** The three groups and their tags, in the order they are to be rendered. */
  readonly socialTagGroups: SocialTagVocabulary;
  /** How many of them a profile must hold. Both ends included. */
  readonly socialTagSelection: SocialTagSelectionBounds;
}
