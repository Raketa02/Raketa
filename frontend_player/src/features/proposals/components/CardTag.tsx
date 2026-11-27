/**
 * **The game card's small tags** — **IN** on a tile and **Book it now** on a court, both white on
 * the card's green; **Court available** on the on-dark grey; **Booked** on volt (the screens A2.3).
 *
 * `Tag`'s geometry and its `tag` type role, drawn here rather than as three more variants of the
 * shared pill: the green is the game card's own (`gameGreen`, fenced to this surface in the
 * theme), and a shared variant would be a licence for the rest of the app to reach for it. The
 * grey and the volt are `Tag`'s own `onDark` and `volt` pairs, restated through the same tokens.
 * A tag is never pressable (6.4).
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

export type CardTagTone = 'green' | 'grey' | 'volt';

export interface CardTagProps {
  readonly label: string;
  readonly tone: CardTagTone;
  /** A round dot before the words — a game's details draw the stage's (*Filling*) this way. */
  readonly dot?: string;
  /**
   * The words' `maxFontSizeMultiplier`, where the tag stands in a fixed box — a tile's foot caps it
   * with the rest of its words (`footMaxScale`, #865). Absent, it grows with the OS text size.
   */
  readonly maxScale?: number;
}

/** A tag's padding about its words — `gameTileFoot.test` counts it in a tile's foot. */
export const CARD_TAG = { padX: theme.space.xs, padY: theme.space.xxs } as const;

export function CardTag({ label, tone, dot, maxScale }: CardTagProps) {
  return (
    <View style={[s.tag, BED[tone]]}>
      {dot === undefined ? null : (
        <View
          style={[s.dot, { backgroundColor: dot }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      )}
      <Text
        style={[s.label, WORDS[tone]]}
        numberOfLines={1}
        {...(maxScale === undefined ? {} : { maxFontSizeMultiplier: maxScale })}
      >
        {label}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    paddingVertical: CARD_TAG.padY,
    paddingHorizontal: CARD_TAG.padX,
    borderRadius: theme.radius.tag,
    alignSelf: 'flex-start',
  },
  label: { ...theme.type.tag },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.size.sportDot / 2,
  },
});

const BED = StyleSheet.create({
  green: { backgroundColor: theme.color.gameGreen },
  grey: { backgroundColor: theme.color.onDarkTag },
  volt: { backgroundColor: theme.color.volt },
});

const WORDS = StyleSheet.create({
  // White on the card's green is 4,62 (gameGround.test.ts).
  green: { color: theme.color.surface },
  grey: { color: theme.color.surface },
  // `ink` on volt, never white — Rule C's arithmetic runs the other way on volt (13,96).
  volt: { color: theme.color.ink },
});
