/**
 * **The bell on Home** — the door to the recent notices (#559; the screens A9: *the recent notices
 * are a list reached from a bell on Home*), in the header's right slot.
 *
 * **It carries no count.** The backend keeps no seen marker (#549), so a number on it would be a
 * count of everything ever told — a badge that never clears, which is worse than none. Home's own
 * badge on the bar already counts what needs the player.
 */

import Feather from '@expo/vector-icons/Feather';
import { useRouter } from 'expo-router';
import { Pressable, StyleSheet } from 'react-native';

import { theme } from '@/shared/ui';

import { NOTICES_ROUTE } from './noticeRoutes';
import { NOTIFICATIONS_COPY } from './notificationsCopy';

export function NoticeBell() {
  const router = useRouter();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={NOTIFICATIONS_COPY.bell}
      onPress={() => router.push(NOTICES_ROUTE)}
      style={({ pressed }) => [s.bell, pressed ? s.pressed : undefined]}
    >
      <Feather
        name="bell"
        size={theme.size.tabIcon}
        color={theme.color.ink}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  // 6.5's whole target, the glyph centred in it.
  bell: {
    width: theme.size.minTouch,
    height: theme.size.minTouch,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: { opacity: 0.7 },
});
