/**
 * **The court block** — what a yes on the card does, what it costs, and where and when (the screens
 * A2.3; mocks 2–8, 10).
 *
 * ```
 * ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
 * ╎ [Court available]                 32 zł ╎   the tag · the share, volt and mono
 * ╎ Tomorrow 19:00 · Bonarka Arena ·        ╎   the day and the club; the late line in amber
 * ╎ no free cancellation                    ╎
 * └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
 * ```
 *
 * **Three tags, two beds, three borders.** *Court available* — your yes is a free vote — on the
 * grey bed with a **dashed** border, because nothing is held; *Book it now* — your yes fills the
 * game — in green on the green-grey bed with a **solid green** border, the tag's own green; and a
 * rescue's *Booked* in volt on the same bed with a **solid** `voltStroke` border, volt's own stroke.
 * Solid, both, because a yes there books a court or joins a booked one.
 *
 * **No court number** while the game fills: a card promises a court at a club at an hour, and the
 * number is given at booking (the mechanics §5.2). **A rescue's court is booked**, so its number
 * joins the line — *Saturday 16:00 · Ogrody 33 · Court 6* (mock 2). **One element** to a listener,
 * the tag first — what a yes does is the first thing to know about a price.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { CourtTag, DeckCard } from '../domain/deck';
import type { GameDay } from '../domain/when';

import { CardTag, type CardTagTone } from './CardTag';
import { courtLine, courtSpoken, LINE_JOIN, shareWords } from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY;

const TONE: Readonly<Record<CourtTag, CardTagTone>> = {
  available: 'grey',
  bookItNow: 'green',
  booked: 'volt',
};

export interface CourtBlockProps {
  readonly tag: CourtTag;
  readonly day: GameDay | undefined;
  readonly card: Pick<
    DeckCard,
    'startsAt' | 'club' | 'courtName' | 'indoor' | 'shareGrosze' | 'noFreeCancellation'
  >;
}

export function CourtBlock({ tag, day, card }: CourtBlockProps) {
  return (
    <View
      style={[s.block, BLOCK[tag]]}
      accessible
      accessibilityLabel={courtSpoken(tag, day, card)}
      testID={`court-block-${tag}`}
    >
      <View style={s.head}>
        <CardTag label={COPY.courtTag[tag]} tone={TONE[tag]} />
        <Text style={s.share}>{shareWords(card)}</Text>
      </View>
      <Text style={s.line}>
        {courtLine(day, card)}
        {card.noFreeCancellation ? (
          <Text style={s.late}>
            {LINE_JOIN}
            {COPY.noFreeCancellation}
          </Text>
        ) : null}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  block: {
    borderRadius: theme.radius.card,
    borderWidth: theme.size.gameCard.courtStroke,
    padding: theme.space.md,
    gap: theme.space.xs,
  },
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  share: { ...theme.num.m, ...theme.tabular, color: theme.color.volt },
  line: { ...theme.type.h2, color: theme.color.surface },
  late: { ...theme.type.h2, color: theme.color.gameAmber },
});

/** Each tag's bed and border — see the module note. */
const BLOCK = StyleSheet.create({
  available: {
    backgroundColor: theme.color.gameCourt,
    borderColor: theme.color.onDarkHair,
    borderStyle: 'dashed',
  },
  bookItNow: { backgroundColor: theme.color.gameCourtBooked, borderColor: theme.color.gameGreen },
  booked: { backgroundColor: theme.color.gameCourtBooked, borderColor: theme.color.voltStroke },
});
