/**
 * **Finding** — the deck's area right after an intent answer on Games, while Rakieta deals the group
 * ([#741](https://github.com/Rakieta02/Rakieta/issues/741);
 * [ADR-0201](../../../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
 * §4; the screens A2.1 state 5; the words §28).
 *
 * *Finding for-fun games for you…*, or *Finding games for you…* after *Either suits me* on the
 * first-time question. It stands where the answer was given — in the first-time question's place,
 * or over the deck's area as the door's panel did — until the deal has answered and the deck it
 * lands on has been read (`useFindGames`), and then the deck's own states take over: the cards, or
 * *Nothing picked right now* with **Post a game**. So a player who has just answered is never shown
 * a false *nothing*, which is what the read straight after the answer used to say.
 *
 * The muted spinner is the deck's own first-read one, with the sentence under it naming what is
 * being found. One element to a listener, its name the sentence, so the line is not said twice.
 */

import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { Finding } from '../domain/deck';

import { findingLine } from './doorPresentation';

export function FindingGames({ finding }: { readonly finding: Finding }) {
  const line = findingLine(finding);

  return (
    <View accessible accessibilityLabel={line} style={s.finding}>
      <ActivityIndicator color={theme.color.muted} />
      <Text style={s.line}>{line}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  finding: { alignItems: 'center', gap: theme.space.sm, paddingVertical: theme.space.xxl },
  line: { ...theme.type.inlineTitle, color: theme.color.ink, textAlign: 'center' },
});
