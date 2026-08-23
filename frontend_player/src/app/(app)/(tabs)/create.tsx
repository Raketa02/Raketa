/**
 * Create — the middle tab, and a destination before it is a feature.
 *
 * The coral circle in the bar is not a fifth destination in the visual sense
 * ([ADR-0082](../../../../../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md))
 * and it is one in the routing sense: it is a tab like the others, so it needs a screen
 * like the others. Posting a match is its own effort and is not on this map.
 *
 * A player in debt cannot create a match at all (`Raketa02/Raketa#92`), which is a rule
 * the server states on Now's debt line — it is named here so the screen that replaces
 * this one does not go looking for it on the phone.
 */

import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader, theme } from '@/shared/ui';

export default function CreateRoute() {
  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <View style={s.content}>
        <ScreenHeader eyebrow="Not built yet" title="Create a match" />
        <Text style={s.body}>
          Posting a match — the sport, the court, the hour and who pays for what — arrives with its
          own screen.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: { paddingHorizontal: theme.size.gutter, gap: theme.space.sm },
  body: { ...theme.type.tiny, color: theme.color.muted },
});
