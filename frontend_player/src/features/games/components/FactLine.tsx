/**
 * **One line of a game's fact list** — a muted dot and a sentence in `ink`, variant C's account of
 * an evening: the facts a game with no score still is (`EVENING_FACTS`), and what is said of a
 * player at the court (_Oscar Nowak came late_, #658). **The dot is never the meaning** — the
 * sentence is, and the dot only marks where one fact ends and the next begins.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

export function FactLine({ children }: { readonly children: string }) {
  return (
    <View style={s.row}>
      <View style={s.dot} />
      <Text style={s.text}>{children}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  dot: {
    width: theme.space.xxs,
    height: theme.space.xxs,
    borderRadius: theme.space.xxs,
    backgroundColor: theme.color.muted,
  },
  text: { ...theme.type.tiny, color: theme.color.ink, flex: 1 },
});
