/**
 * One plain line at the top of Now, held and then faded (design-system 11.4).
 *
 * `ADR-0062` specifies it exactly: *"one plain line at the top of Now — that seat
 * has gone. Not a card, no action, no tap target; it fades."* A card is what a
 * **takeable** seat wears, so the acknowledgement that a seat is gone must not
 * wear one — and a dialog would stop her to say that something did *not* happen,
 * which is the interruption `ADR-0070` refuses by answering a refusal with the
 * corrected card in the first place.
 *
 * **It is not a control.** `pointerEvents: 'none'`, no role, nothing to press: it
 * sits above the card it is about while the card itself says the rest.
 *
 * **The hold is not the animation.** Design-system 12.1 established the
 * distinction for the calculating screen — *"a held duration is not an animation:
 * nothing moves"* — so reduced motion keeps the three seconds and skips only the
 * fade. A player who asked the OS to calm things down still gets the sentence for
 * as long as it takes to read; what she does not get is the 200ms of it moving.
 *
 * **It announces itself**, on Part 13's rule for the toast — *"a toast a
 * screen-reader user cannot hear is a toast that did not happen"*, which is truer
 * of something quieter than a toast. `AccessibilityInfo.announceForAccessibility`
 * rather than a live region, because the line is unmounted a moment later and a
 * region that has gone announces nothing.
 *
 * The animation **is** the clock. Nothing here arms a `setTimeout`: the fade is
 * the thing that ends, and the callback is where it ended — which is what keeps
 * this feature's two timers at two, both of them about a moment the server named.
 */

import { AccessibilityInfo, Animated, StyleSheet, Text } from 'react-native';
import { useEffect, useRef } from 'react';

import { theme, useReducedMotion } from '@/shared/ui';

import { GUTTER } from './nowGeometry';

/** So *there is exactly one, and it went away* is assertable rather than implied. */
export const TRANSIENT_LINE_ID = 'now-transient-line';

export interface TransientLineProps {
  readonly line: string;
  /** Called once the line has finished fading, so the screen can stop holding it. */
  readonly onFaded: () => void;
}

export function TransientLine({ line, onFaded }: TransientLineProps) {
  const reducedMotion = useReducedMotion();
  const opacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    AccessibilityInfo.announceForAccessibility(line);
  }, [line]);

  useEffect(() => {
    const fade = Animated.sequence([
      Animated.delay(theme.motion.hold.line),
      Animated.timing(opacity, {
        toValue: 0,
        duration: reducedMotion ? 0 : theme.motion.fade,
        useNativeDriver: true,
      }),
    ]);

    // `finished` is false when the line was unmounted or replaced mid-fade — a
    // second seat tapped, or the screen left. Reporting *faded* there would clear
    // whichever line is now on screen.
    fade.start(({ finished }) => {
      if (finished) onFaded();
    });

    return () => fade.stop();
  }, [opacity, onFaded, reducedMotion]);

  return (
    <Animated.View
      testID={TRANSIENT_LINE_ID}
      style={[s.line, { opacity }]}
      pointerEvents="none"
      // One element, so the sentence is read as a sentence rather than as loose
      // text between a chip row and a card.
      accessible
    >
      <Text style={s.text}>{line}</Text>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  line: { paddingHorizontal: GUTTER, paddingBottom: theme.space.sm },
  text: { ...theme.type.tiny, color: theme.color.muted },
});
