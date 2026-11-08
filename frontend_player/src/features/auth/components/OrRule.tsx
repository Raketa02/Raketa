/**
 * **The *or* rule** — a thin line with the word in its middle, between signing in and the other
 * way in on the stage's sheet ([#784](https://github.com/Raketa02/Raketa/issues/784)).
 *
 * The line is `line`, the boxes' own border — measured off mock 3, where the rule and the boxes'
 * edges are one value — because it **bounds** the two ways in from each other rather than folding
 * one thing (`line2`, which on paper is 1,02:1 and not there). The word is spoken: *Sign in, or, I
 * have an invitation code* is how a listener meets the choice.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

export function OrRule({ word }: { readonly word: string }) {
  return (
    <View style={s.row}>
      <View style={s.line} />
      <Text style={s.word}>{word}</Text>
      <View style={s.line} />
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  line: { flex: 1, borderTopWidth: 1, borderTopColor: theme.color.line },
  word: { ...theme.type.tiny, color: theme.color.muted },
});
