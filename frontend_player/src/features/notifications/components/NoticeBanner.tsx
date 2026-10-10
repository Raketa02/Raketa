/**
 * **The in-app banner** — a notice pushed while the app is open (#559; the screens A9: *an in-app
 * banner when the app is open*).
 *
 * ```
 * ┌──────────────────────────────────────────┐
 * │ It's a game! · 30 zł held              × │   night, radius toast, padding md × lg
 * │ Padel · Sat 16:00 · Bonarka Arena        │   inlineTitle surface · tiny onDarkTiny
 * └──────────────────────────────────────────┘
 * ```
 *
 * **The phone draws nothing itself while the app is open** (no foreground handler is set, so a push
 * is not presented), and this is what it draws instead — at the top, under the status bar, where a
 * phone's own banner comes down, held for `motion.hold.notice` and gone.
 *
 * **Not 9.2's toast**: a toast never blocks a tap and has no control, and this one *is* a control —
 * a press opens the game the notice is about, as a tap on the phone's own would. So it is its own
 * component, placed by `NoticesHost`, never pushed onto the toast queue, and it carries a close
 * control, because it sits over a header's back button for as long as it is up. It neither arrives
 * nor leaves on an animation (1.5). A notice that opens nothing — a sport this build cannot name — is
 * drawn all the same, and only closes.
 *
 * Spoken once, as it arrives, queued (`NoticesHost`); the banner itself is then a button named by
 * the notice's own words.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

import { NOTIFICATIONS_COPY, noticeSpoken } from './notificationsCopy';

export interface NoticeBannerProps {
  readonly title: string;
  readonly body: string;
  /** Open the game it is about — absent for a notice this build has nowhere to open. */
  readonly onOpen?: () => void;
  readonly onClose: () => void;
}

export function NoticeBanner({ title, body, onOpen, onClose }: NoticeBannerProps) {
  const insets = useSafeAreaInsets();
  const spoken = noticeSpoken(title, body);
  const words = (
    <View style={s.words}>
      <Text style={s.title}>{title}</Text>
      {body === '' ? null : <Text style={s.body}>{body}</Text>}
    </View>
  );

  return (
    <View pointerEvents="box-none" style={[s.host, { top: insets.top + theme.space.sm }]}>
      <View style={s.banner}>
        {onOpen === undefined ? (
          <View accessible accessibilityLabel={spoken} style={s.face}>
            {words}
          </View>
        ) : (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={spoken}
            accessibilityHint={NOTIFICATIONS_COPY.banner.opens}
            onPress={onOpen}
            style={({ pressed }) => [s.face, pressed ? s.pressed : undefined]}
          >
            {words}
          </Pressable>
        )}
        {/* Not 9.1's `CloseControl`: that one is drawn for a paper sheet — a `line2` disc, a muted
            mark — and this sits on `night`, where the mark is the surface's own white. */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={NOTIFICATIONS_COPY.banner.close}
          onPress={onClose}
          hitSlop={theme.hit.infoMark}
          style={({ pressed }) => [s.close, pressed ? s.pressed : undefined]}
        >
          <Text style={s.mark} accessibilityElementsHidden importantForAccessibility="no">
            {'×'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  // The toast host's own edges (9.2), at the top rather than above the bar.
  host: {
    position: 'absolute',
    left: theme.space.lg,
    right: theme.space.lg,
    zIndex: theme.layer.toast,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    borderRadius: theme.radius.toast,
    backgroundColor: theme.color.night,
    paddingVertical: theme.space.md,
    paddingLeft: theme.space.lg,
    paddingRight: theme.space.md,
  },
  face: { flex: 1 },
  words: { gap: theme.space.xxs },
  title: { ...theme.type.inlineTitle, color: theme.color.surface },
  body: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  pressed: { opacity: 0.7 },
  close: {
    width: theme.size.sheetClose,
    height: theme.size.sheetClose,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mark: { ...theme.type.h2, color: theme.color.surface },
});
