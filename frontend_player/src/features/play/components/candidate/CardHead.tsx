/**
 * The top of the **social and deck** cards: **who, how good the game would be, and why they
 * are on the list at all**.
 *
 * It was the top of all three, and two of them still differ below this line and not at it — a
 * name beside a fit pill is the same object on a for-fun row and on a card under a thumb — so
 * it stays a part of the kit rather than ten lines written twice. Two copies of a head row is
 * still where one of them eventually keeps a `numberOfLines` the other lost.
 *
 * ## The competitive card left, and it took the volt sentence with it
 *
 * §B10's head row laid out a name with **inline tags** beside it — `.tag.hot`, `.tag.volt`,
 * `.tag.bad` — and UI Open decision #14 replaced the volt one's two words with a whole
 * sentence bound to `INTEREST_LIFT`. The reasoning was *a full sentence does not go where a
 * two-word tag went*, which is true of the sentence and not of the fact: the two-word form was
 * never gone. `INTEREST_RECEIVED` and `INTEREST_LIFT` are *two facts with one tag*
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §10), so the tag is
 * bound to the admitting code and worded by its twin, which is what
 * [#309](https://github.com/Raketa02/Raketa/issues/309) reverses on the competitive card —
 * `IdentityRow`, a name with the **tag** beside it and the fit pill on a row of its own.
 *
 * **This component was not made to do both.** Configuring one head to put either a pill or a
 * tag on the name line and either a sentence or nothing beneath it takes two flags to say
 * which, which is
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3's `surface === …` arriving in a smaller spelling. The three cards are three components for
 * exactly this reason, and their heads are now two.
 *
 * So what stays here is the sentence, on the two cards that still draw it. It is drawn at the
 * body size and not the tag one, because it **is** prose: `tag` is 9,5pt and flat, for a word,
 * and this is a sentence about the reader.
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
