/**
 * **A game's court facts on an accent line** — WHERE · DAY · TIME · the money row (details 8),
 * each one element to a listener: its label, its value, its aside and the line under it, in that
 * order.
 *
 * Drawn by a game still filling, a booked game's details and a Home card (#553, #556), so drawn
 * once. The line takes the status's colour (A4.1: *an accent line in the status colour*); the
 * details draw the values at the mock's size, a Home card at the card's.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

/** One fact of the accent line: its label, its value, the words after it and a line under it. */
export interface FactWords {
  readonly label: string;
  readonly value: string;
  readonly aside?: string;
  /**
   * A line of its own under the value, in the aside's type — *Bonarka Arena answers by 20:45 ·
   * Nobody pays until it confirms* under the share while the club decides, as Home's card draws it.
   */
  readonly below?: string;
}

export interface GameFactsProps {
  readonly facts: readonly FactWords[];
  /** The accent line's colour — the stage's, or the status's. */
  readonly accent: string;
  /** The details' figures, or a rail card's smaller ones. */
  readonly size?: 'details' | 'card';
}

export function GameFacts({ facts, accent, size = 'details' }: GameFactsProps) {
  const value = size === 'details' ? s.valueDetails : s.valueCard;
  return (
    <View style={[s.facts, { borderLeftColor: accent }]}>
      {facts.map((fact) => (
        <View
          key={fact.label}
          style={s.fact}
          accessible
          accessibilityLabel={[fact.label, fact.value, fact.aside, fact.below]
            .filter((part) => part !== undefined)
            .join(', ')}
        >
          <Text style={s.label}>{fact.label}</Text>
          <Text style={value}>
            <Text style={value}>{fact.value}</Text>
            {fact.aside === undefined ? null : <Text style={s.aside}> {fact.aside}</Text>}
          </Text>
          {fact.below === undefined ? null : <Text style={s.aside}>{fact.below}</Text>}
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  facts: {
    borderLeftWidth: theme.size.gameCard.courtStroke,
    paddingLeft: theme.space.md,
    gap: theme.space.sm,
  },
  fact: { gap: theme.space.xxs },
  label: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
  },
  valueDetails: { ...theme.type.h1, color: theme.color.surface },
  valueCard: { ...theme.type.h2, color: theme.color.surface },
  aside: { ...theme.type.tiny, color: theme.color.onDarkTiny },
});
