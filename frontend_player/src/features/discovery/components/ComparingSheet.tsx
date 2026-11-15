/**
 * **The comparison sheet, for whoever's is up** — Home's row and See all keep the same state (#802),
 * the people lists' own (`usePersonSheet`): the sheet draws the person's latest read, closes — drawn as
 * they last were — when a write moves them out of the list, and never reopens by itself.
 */

import type { SameLevelPlayer } from '../domain/sameLevel';
import type { PersonSheet } from '../hooks/usePersonSheet';

import { ComparisonSheet } from './ComparisonSheet';

export function ComparingSheet({
  comparing,
}: {
  readonly comparing: PersonSheet<SameLevelPlayer>;
}) {
  if (comparing.person === undefined) return null;
  return (
    <ComparisonSheet visible={comparing.open} player={comparing.person} onClose={comparing.close} />
  );
}
