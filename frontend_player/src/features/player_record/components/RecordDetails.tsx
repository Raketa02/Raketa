/**
 * **The full record, folded** — everything under the sheet's three blocks, behind one quiet row:
 * a chevron, centred, and no words (the product owner's ask, 2026-10-01). The row is still named
 * *Full record* for a screen reader, which has no chevron to see. The blocks are the summary a
 * reader came for; the counted card (shows up, answers challenges, answers about results,
 * opponent variety, sportsmanship) and the tags are the account of it, one tap away rather than a
 * scroll away.
 *
 * ## Shut by default, and shut again for every sheet
 *
 * The sheet opens on the person — the photograph, the Level, the three blocks — and a held row on
 * Members or a face on a card opens it to answer *who is this*, which the blocks answer. The fold
 * is local state, so every sheet starts shut and nothing is remembered between two people.
 *
 * ## It moves both ways, on the UI thread
 *
 * One shared value from 0 to 1 over `motion.disclose`, `easeDecel`: the fold's **height** runs to
 * the content's measured height, so the sheet grows with it and the rest of the record slides
 * down; the content fades in from a `space.md` above its place; the chevron turns over. Closing
 * runs the same value back, so the sheet gives the space back rather than jumping. Nothing is
 * scaled — iOS rasterises a scaled layer blurred (ADR-0176 §2, amended) — and the content is laid
 * out once, absolutely, at its whole height, which is what the fold is measured against. Under
 * reduced motion the value jumps and the fold is simply open or shut.
 *
 * ## Shut is hidden, not just clipped
 *
 * A clipped card is still a card to VoiceOver and TalkBack, which would read a record the eye
 * cannot see. So shut, the fold is hidden from assistive technology and takes no touches; the row
 * is a button that says whether it is expanded. Never a `Modal`: it is a layer of the sheet.
 */

import Feather from '@expo/vector-icons/Feather';
import { useEffect, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Animated, {
  Easing,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { theme, useReducedMotion } from '@/shared/ui';

import { FULL_RECORD } from './recordPresentation';

const EASE = Easing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/** How far the content travels into place as it opens — `space.md`, the fast filter's slide. */
const SLIDE = theme.space.md;

/** Half a turn: the chevron points down shut and up open. */
const TURN = 180;

export function RecordDetails({ children }: { readonly children: ReactNode }) {
  const reduced = useReducedMotion();
  const [open, setOpen] = useState(false);
  const progress = useSharedValue(0);
  const height = useSharedValue(0);

  useEffect(() => {
    const to = open ? 1 : 0;
    progress.value = reduced
      ? to
      : withTiming(to, { duration: theme.motion.disclose, easing: EASE });
  }, [open, reduced, progress]);

  const fold = useAnimatedStyle(() => ({ height: height.value * progress.value }));
  const slide = useAnimatedStyle(() => ({
    opacity: progress.value,
    transform: [{ translateY: interpolate(progress.value, [0, 1], [-SLIDE, 0]) }],
  }));
  const turn = useAnimatedStyle(() => ({
    transform: [{ rotate: `${TURN * progress.value}deg` }],
  }));

  return (
    <View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={FULL_RECORD}
        accessibilityState={{ expanded: open }}
        onPress={() => setOpen((was) => !was)}
        // 6.6: the row is the target, so the row dims.
        style={({ pressed }) => [s.row, pressed ? s.pressed : undefined]}
      >
        <Animated.View
          style={turn}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          <Feather name="chevron-down" size={theme.size.tabIcon} color={theme.color.muted} />
        </Animated.View>
      </Pressable>

      <Animated.View
        testID="full-record-fold"
        style={[s.fold, fold]}
        pointerEvents={open ? 'auto' : 'none'}
        accessibilityElementsHidden={!open}
        importantForAccessibility={open ? 'auto' : 'no-hide-descendants'}
      >
        <Animated.View
          testID="full-record-content"
          style={[s.content, slide]}
          onLayout={(event) => {
            height.value = event.nativeEvent.layout.height;
          }}
        >
          {children}
        </Animated.View>
      </Animated.View>
    </View>
  );
}

const s = StyleSheet.create({
  // A quiet row on the sheet: the chevron alone, centred, a `line2` fold above it — the hairline
  // is a fold inside the sheet, not a bound around a card — and the whole row at the touch
  // minimum, so the target is the sheet's width rather than the chevron's.
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: theme.size.minTouch,
    borderTopWidth: 1,
    borderTopColor: theme.color.line2,
  },
  pressed: { opacity: 0.7 },
  fold: { overflow: 'hidden' },
  // Laid out at its whole height whatever the fold's is, so the measure is the record's own. The
  // sheet's `space.sm` between its regions, kept between the card and the tags inside it.
  content: { position: 'absolute', top: 0, left: 0, right: 0, gap: theme.space.sm },
});
