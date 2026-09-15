/**
 * The top of the **social** card, and of the challenge screen's: **who, how good the game would
 * be, and — on the social card — the one tag a yes between the two people earns.**
 *
 * It was the top of all three Play cards, and the deck and the competitive card left it at
 * different times and for different reasons — a name beside a fit pill is still the same object
 * on a for-fun row and on the challenge screen's card, so it stays a part of the kit rather than
 * ten lines written twice. Two copies of a head row is still where one of them eventually keeps
 * a `numberOfLines` the other lost.
 *
 * ## The sentence went, and the tag took its place
 *
 * §B10's head row laid out a name with **inline tags** beside it — `.tag.hot`, `.tag.volt`,
 * `.tag.bad` — and UI Open decision #14 replaced the volt one's two words with a whole sentence
 * bound to `INTEREST_LIFT`, *They already said yes to you*, drawn beneath the name at the body
 * size because it **was** prose. [#309](https://github.com/Raketa02/Raketa/issues/309) reversed
 * that on the competitive card alone — `IdentityRow`, the tag beside the handle — and left this
 * head drawing the sentence. [ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8 finished the reversal: **both tags on both card styles, the two-word tag in place of the
 * social card's sentence.** So the slot under the name row holds a `Tag` now, and the words are
 * `candidateTag`'s — *Wants to play you* off the admitting code, *You said yes* off the reader's
 * own list — which is also what keeps the two cards' tags one string apiece.
 *
 * **Why the tag is under the row here and beside the handle on the competitive card.** This
 * head puts the fit pill on the name line, and a pill and a tag on one line is a row whose
 * width depends on how lucky the reader got. The competitive card moved the pill to a row of
 * its own to make room; this one keeps its two lines and gives the tag the second, which is
 * exactly where the sentence stood. **This component was still not made to do both**: one head
 * configured for either layout is
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3's `surface === …` arriving in a smaller spelling, and the cards are separate components
 * for exactly this reason.
 *
 * **It announces nothing of its own.** §20.3 fixes the card body's spoken name and the body is
 * the action above it, so the whole head merges — the ✦ included, which is how the glyph comes
 * to be unspoken without a rule about glyphs. The tag's words are booked as unspoken with the
 * competitive card's, for `IdentityRow`'s reason.
 */

import { StyleSheet, Text, View } from 'react-native';

import { FitPill, Tag, theme } from '@/shared/ui';

import type { CandidateTag } from '../playerCardPresentation';

export interface CardHeadProps {
  /** §15's `playerName()` — the handle, whole. */
  readonly name: string;
  readonly fit: number;
  /** At most one, and often none. `candidateTag`'s answer, never a component's. */
  readonly tag?: CandidateTag;
}

export function CardHead({ name, fit, tag }: CardHeadProps) {
  return (
    <View style={s.head}>
      <View style={s.row}>
        <Text style={s.name} numberOfLines={1}>
          {name}
        </Text>
        <FitPill fit={fit} />
      </View>

      {tag === undefined ? null : <Tag label={tag.label} variant={tag.variant} />}
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
});
