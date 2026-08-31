/**
 * The top of every candidate card: **who, how good the game would be, and why they are on
 * the list at all**.
 *
 * The three cards differ below this line and not at it — a name beside a fit pill is the same
 * object on a pool row, a for-fun row and a card under a thumb — so it is a part of the kit
 * rather than ten lines written three times. Three copies of a head row is where one of them
 * eventually keeps a `numberOfLines` the other two lost.
 *
 * ## The volt tag is a sentence now
 *
 * §B10's head row laid out a name with **inline tags** beside it — `.tag.hot`, `.tag.volt`,
 * `.tag.bad` — and UI Open decision #14 replaced the volt one's two words with a whole
 * sentence bound to `INTEREST_LIFT`. **A full sentence does not go where a two-word tag went**,
 * so it lands under the name rather than beside it, at the top of the card, which is where the
 * decision put it: the lift is why this person is on the list at all, and it is read before
 * anything explaining where in it they are.
 *
 * It is drawn at the body size and not the tag one, because it is prose: `tag` is 9,5pt and
 * flat, for a word, and this is a sentence about the reader.
 *
 * **It announces nothing of its own.** §20.3 fixes the card body's spoken name and the body is
 * the action above it, so the whole head merges — the ✦ included, which is how the glyph comes
 * to be unspoken without a rule about glyphs.
 */

import { StyleSheet, Text, View } from 'react-native';

import { FitPill, theme } from '@/shared/ui';

import type { InclusionReason } from '../../domain/vocabulary';
import { inclusionLine } from '../livenessPresentation';

export interface CardHeadProps {
  /** §15's `playerName()` — the handle, whole. */
  readonly name: string;
  readonly fit: number;
  /** A union of one, and it **admits**. Omitted where nothing lifted them. */
  readonly inclusionReason?: InclusionReason;
}

export function CardHead({ name, fit, inclusionReason }: CardHeadProps) {
  return (
    <View style={s.head}>
      <View style={s.row}>
        <Text style={s.name} numberOfLines={1}>
          {name}
        </Text>
        <FitPill fit={fit} />
      </View>

      {inclusionReason === undefined ? null : (
        <Text style={s.lift}>{inclusionLine(inclusionReason)}</Text>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  head: { gap: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.xs,
  },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  // Coral is the one accent and this is the one thing on a card that is about the reader.
  lift: { ...theme.type.tiny, color: theme.color.coralInk },
});
