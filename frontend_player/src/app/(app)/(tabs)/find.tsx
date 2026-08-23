/**
 * Find — the second tab, and a destination before it is a feature.
 *
 * The tab bar reaches five places ([ADR-0082](../../../../../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md))
 * and three of them have no feature yet. A tab that went nowhere would be a dead control,
 * and a tab that rendered nothing would be a white screen a player reads as a crash — so
 * each of the three says what it is and what it is not, and is deleted by the ticket that
 * builds it. Find is what every shelf's tail card opens (`Raketa02/Raketa#88`).
 *
 * Written out here rather than shared with the other two: three copies of ten lines that
 * are each deleted separately is cheaper than a placeholder abstraction, and `shared/`
 * is not where code goes because two files look alike.
 */

import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader, theme } from '@/shared/ui';

export default function FindRoute() {
  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <View style={s.content}>
        <ScreenHeader eyebrow="Not built yet" title="Find" />
        <Text style={s.body}>
          Searching for matches and courts arrives with its own screen. Until then, Now is where the
          app says what is happening.
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
