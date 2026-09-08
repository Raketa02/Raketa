/**
 * **One pill per sport somebody holds a rating in.**
 *
 * It is [6.4](../../../../docs/design-system.md#64-tag)'s tag with its own dot and nothing new
 * drawn: 15.1's first question — *is it one of the existing primitives?* — is answered yes here,
 * where the star row answered it no. What the composition adds is the label, and the label is
 * `recordPresentation`'s.
 *
 * It answers *what else do they play*, which is useful to a reader inside a padel four and is
 * the whole of what a pill is for: how sure the platform is and what that rests on belong to
 * the one sport the sheet is about, and repeating them four times would be four skill cards
 * drawn as jewellery.
 *
 * ## The order is the server's, and nothing here sorts
 *
 * The sports arrive in the sport registry's own order, which is the order every list of sports
 * on this surface takes. A client that sorted them — by level, say — would make the header a
 * boast about whichever sport somebody happens to be best at.
 *
 * ## Colour, and the condition attached to drawing it
 *
 * `theme.color.sport` reuses the semantic palette rather than extending it, and it does so on
 * one stated condition: *the dot is always accompanied by the sport name in text*. Every pill
 * here carries the name, which is why the dot is allowed at all — and it is why the label is
 * the sport's **name** rather than an abbreviation. Four sports fit; a fifth sport is a real
 * decision, not a shorter word.
 *
 * ## It announces nothing of its own
 *
 * The row is inside the header, which is one accessibility element and states these same pills
 * in its own label (§20.1). A tag that named itself would be the same fact read twice, and this
 * is a row of four of them.
 */

import { StyleSheet, View } from 'react-native';

import { sportColour, sportLabel } from '@/features/onboarding/types';
import { Tag, theme } from '@/shared/ui';

import type { RatedSport } from '../domain/playerRecord';

import { sportPill } from './recordPresentation';

export interface SportPillsProps {
  /** In the registry's own order, as served. Never re-sorted here. */
  readonly sports: readonly RatedSport[];
}

export function SportPills({ sports }: SportPillsProps) {
  if (sports.length === 0) return null;

  return (
    <View style={s.row}>
      {sports.map(({ sport, level }) => (
        <Tag key={sport} label={sportPill(sportLabel(sport), level)} dot={sportColour(sport)} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  // It wraps: four sports beside a 112pt panel is two lines on the narrowest phone, and a row
  // that scrolled sideways would hide the fourth pill behind a gesture nothing advertises.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xxs },
});
