/**
 * **The bell on Home** — the door to the recent notices (#559; the screens A9: *the recent notices
 * are a list reached from a bell on Home*), in the header's right slot.
 *
 * **It carries the number of notices since the list was last opened** (#627; Q101): the server's
 * count, the same on every phone, drawn up to 99 and *99+* above it, and nothing at nought. Opening
 * the list clears it. It is the session's read of the list, so the minute's read, a push and a
 * return to the app all move it — and **what was told while Raketa was closed is in it**, since
 * nothing comes down as a banner at launch.
 *
 * **The tab bar's badge in `ink`** (10.2, 7.29): `shared/ui`'s `CountBadge`, the same mark out of
 * the layout and over the glyph's top-right, in its `news` tone rather than the bar's `attend`.
 * Coral is a count of things only the player can clear (1.2), and news is not an obligation. Spoken
 * on the bell's own name, *Recent notifications, 3 new* — exactly, since a listener is not short of
 * room — and hidden as a mark, so the number is not read twice.
 */

import Feather from '@expo/vector-icons/Feather';
import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { CountBadge, theme } from '@/shared/ui';

import { useRecentNotices } from '../hooks/useRecentNotices';

import { NOTICES_ROUTE } from './noticeRoutes';
import { bellFigure, bellSpoken } from './notificationsCopy';

export function NoticeBell() {
  const router = useRouter();
  const count = useRecentNotices().data?.newCount ?? 0;
  const figure = bellFigure(count);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={bellSpoken(count)}
      onPress={() => router.push(NOTICES_ROUTE)}
      style={({ pressed }) => [s.bell, pressed ? s.pressed : undefined]}
    >
      {/* The glyph gets a box of its own so the number sits against the mark, as the tab bar's
          does, rather than against the whole target. */}
      <View style={s.glyphBox}>
        <Feather
          name="bell"
          size={theme.size.tabIcon}
          color={theme.color.ink}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
        {figure === undefined ? null : <CountBadge figure={figure} tone="news" />}
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // 6.5's whole target, the glyph centred in it. The number overhangs the glyph, so nothing clips.
  bell: {
    width: theme.size.minTouch,
    height: theme.size.minTouch,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
  },
  pressed: { opacity: 0.7 },
  // The badge's box (`CountBadge`): `visible`, because Android clips a child drawn outside it.
  glyphBox: {
    width: theme.size.tabIcon,
    height: theme.size.tabIcon,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
  },
});
