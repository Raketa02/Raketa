/**
 * Inbox — the fourth tab, and a destination before it is a feature.
 *
 * It is also where the tab bar's one badge points
 * ([ADR-0082](../../../../../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md)).
 * `TabBar` draws that badge from a count, and **nothing counts anything yet** — so no
 * count is passed and no badge appears, rather than a zero being sent to stand for one.
 *
 * Nothing about a seat offer is retracted here either: `ADR-0052`'s Inbox line for a
 * withdrawn offer does not ship (`ADR-0062`), and the wording on the notification carries
 * the retraction instead.
 */

import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader, theme } from '@/shared/ui';

export default function InboxRoute() {
  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <View style={s.content}>
        <ScreenHeader eyebrow="Not built yet" title="Inbox" />
        <Text style={s.body}>
          Messages and club requests arrive with their own screen. Anything with a clock on it is on
          Now.
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
