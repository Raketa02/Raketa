/**
 * **The reveal, for a screen with one read** (design system 5.6; PRD #867,
 * [#870](https://github.com/Raketa02/Raketa/issues/870); the loading shimmer log §4, §5) — how a
 * screen's content takes its skeleton's place.
 *
 * - **The content is drawn underneath the skeleton**, laid out and hidden — from sight, and from a
 *   listener — so the reveal shows a finished screen and nothing rearranges.
 * - **The reveal is one cross-fade on `motion.fade`** (200 ms), opacity only: the content comes in
 *   as the skeleton goes, and the skeleton is unmounted once it has, its clock with it. **Under
 *   reduced motion it is a cut** — only the sweep is Part 13's exception, not the fade.
 * - **A skeleton is drawn only if, at the first draw, the read has nothing**: a screen whose read is
 *   cached is simply drawn, with no skeleton and no fade. **Once the content is in, it never goes
 *   back** to its skeleton during this mount, whatever its read does next — a pull, a background
 *   re-read.
 * - **No delay before the skeleton, and no minimum time on screen**: it stands from the first frame,
 *   and a read that lands at once fades at once — the fade is what turns a short wait into a soft one.
 *
 * **Two words are the caller's.** **Finished**: the read has landed, been refused, or is held for a
 * connection — so the failure or the offline note is revealed in the content's place as the content
 * would be. **Landed**: what it finished with is the content. A refusal or the offline note is not
 * the content, so when the read sets out again — *Try again*, or the connection back — with still
 * nothing to draw, the skeleton stands again rather than a blank page. A screen with several reads,
 * revealed together and then top-down past a ceiling, is #871's.
 *
 * The skeleton is the screen's own layout of `Skeleton`'s shapes, drawn over the content's place and
 * taking no touch: a pull still reaches the list beneath it.
 */

import { useEffect, useState, type ReactNode } from 'react';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import Animated, {
  ReduceMotion,
  cancelAnimation,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';

import { useReducedMotion } from './overlay';
import { theme } from './theme';

export interface RevealProps {
  /** Whether the read has finished — landed, refused, or held for a connection. */
  readonly finished: boolean;
  /** Whether it finished with the content — once it has, the skeleton never comes back. */
  readonly landed: boolean;
  /** The screen's skeleton: its shapes, laid out where the content will stand. */
  readonly skeleton: ReactNode;
  /** The content, drawn underneath until the reveal. */
  readonly children: ReactNode;
  /** The area the content and its skeleton share. */
  readonly style?: StyleProp<ViewStyle>;
}

/** What a listener is kept from while the content waits under its skeleton. */
const HIDDEN = {
  accessibilityElementsHidden: true,
  importantForAccessibility: 'no-hide-descendants',
} as const;

export function Reveal({ finished, landed, skeleton, children, style }: RevealProps) {
  // Once the content is in, it stays in for the rest of the mount.
  const [settled, setSettled] = useState(landed);
  if (landed && !settled) setSettled(true);
  // The read is out with nothing to draw: the skeleton stands, from the first draw or again.
  const waiting = !settled && !finished;
  // How far the content has come in: the content's opacity, and the skeleton's the other way.
  const shown = useSharedValue(waiting ? 0 : 1);
  const contentFade = useAnimatedStyle(() => ({ opacity: shown.value }));

  return (
    <View style={style}>
      <Animated.View
        testID="reveal-content"
        style={[s.content, contentFade]}
        {...(waiting ? HIDDEN : {})}
      >
        {children}
      </Animated.View>
      <FadingSkeleton waiting={waiting} shown={shown}>
        {skeleton}
      </FadingSkeleton>
    </View>
  );
}

/**
 * **The skeleton over the content's place**: up while the read is out with nothing to draw, faded out
 * once it has finished, and unmounted once gone — its clock with it. It owns its coming and going so
 * that the content is not drawn again at the fade's end.
 */
function FadingSkeleton({
  waiting,
  shown,
  children,
}: {
  readonly waiting: boolean;
  readonly shown: SharedValue<number>;
  readonly children: ReactNode;
}) {
  const reduced = useReducedMotion();
  const [up, setUp] = useState(waiting);
  // Back at once when the read sets out again with nothing drawn — no delay before a skeleton.
  if (waiting && !up) setUp(true);

  useEffect(() => {
    if (waiting) {
      cancelAnimation(shown);
      shown.value = 0;
      return;
    }
    if (!up) return;
    // `Never`: whether to fade was decided here, from the app's own reduced-motion answer. Under
    // reduced motion it is a cut, but still a timing, so the skeleton goes only once the UI thread has
    // drawn the content whole — never a frame with neither.
    shown.value = withTiming(
      1,
      { duration: reduced ? 0 : theme.motion.fade, reduceMotion: ReduceMotion.Never },
      (done) => {
        if (done === true) runOnJS(setUp)(false);
      },
    );
  }, [waiting, up, reduced, shown]);

  const fade = useAnimatedStyle(() => ({ opacity: 1 - shown.value }));

  if (!up) return null;
  return (
    <Animated.View
      testID="reveal-skeleton"
      pointerEvents="none"
      style={[s.skeleton, fade]}
      {...HIDDEN}
    >
      {children}
    </Animated.View>
  );
}

const s = StyleSheet.create({
  content: { flex: 1 },
  // Over the content's place, clipped to it: a skeleton that fills the screen stops at its edge.
  skeleton: { ...StyleSheet.absoluteFillObject, overflow: 'hidden' },
});
