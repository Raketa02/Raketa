/**
 * **Somebody is typing** — three pulsing dots in the other side's bubble, at the newest end of the
 * stream ([#404](https://github.com/Raketa02/Raketa/issues/404),
 * [ADR-0156](../../../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
 *
 * ## A third component, and never a branch inside `Bubble`
 *
 * ADR-0146 refused one shape with a `kind` on the wire and `the-loop-components.md` §2.1 refuses
 * it at the surface for the same reason — *one component with a branch re-introduces at the
 * surface exactly what the wire was shaped to prevent*. A typing indicator is not a message: it
 * has no author line, no text, no `seq`, and no place in the stream's ordering. What it shares
 * with a bubble is a ground and a tail, and both are the theme's rather than `Bubble`'s.
 *
 * **It is always the other side's bubble** — `surface` bounded by `line`, the bottom-left corner
 * dropped to `radius.bubbleTail` — and never the reader's `night`, because the reader is not who
 * it is about: the server filters them out of the frame and `domain/typing.ts` filters again.
 *
 * ## The one thing this app animates that does not have to — and does
 *
 * Design-system §1.5 is *nothing animates that does not have to*, and this is the argued
 * exception rather than a quiet one: **the motion is the whole signal.** Three still dots in a
 * bubble are indistinguishable from a message that says `...`, and a message that says `...` is a
 * thing people send. Pulsing is what tells the eye *this is happening now* rather than *this was
 * said* — the same job the sentence does for a listener, and the reason the two are one element.
 * The loop runs on the native driver so the JS thread is free while somebody types, and it stops
 * when the bubble goes and when motion is reduced.
 *
 * **Under reduced motion the dots are drawn still**, on the ticket's own decision and with the
 * cost stated: the visual signal degrades to a shape a sighted reader with reduced motion could
 * read as a sent `...`. The element keeps its name, so a listener loses nothing; `Part 16`
 * records the trade rather than papering over it.
 *
 * ## One element, polite
 *
 * The dots are not a sentence, so the bubble is given one — `typingLine`, §22.5's — as its
 * accessible name, and the element is a **polite** live region: an indicator that interrupted a
 * listener mid-message to say somebody is typing would be the loudest possible way to say the
 * least important thing on the screen (§24.6). The dots themselves are hidden from assistive
 * technology, because they are decoration for the same fact.
 *
 * ## The geometry is new, and no device has drawn it
 *
 * A bubble's width comes from its text and this one has none, so the dots' diameter, their gap
 * and the bubble's padding are this component's own numbers, taken from the theme's steps and
 * recorded in Part 16 beside the exception above. The pulse is a cycle over opacity — three
 * phases of one clock — because opacity is the cheapest property the native driver animates and
 * the one that says *pulse* without moving anything.
 */

import { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';

import { theme, useCollapsedPresentation } from '@/shared/ui';

export interface TypingBubbleProps {
  /** §22.5's sentence, whole — the element's name, and the only words here. */
  readonly sentence: string;
}

/** Three dots, and each one's share of the cycle: where in the beat it is brightest. */
const DOTS = [0, 1, 2] as const;

/** How faint a dot goes between beats. Not invisible: three dots are the shape, the pulse is the signal. */
const DOT_REST_OPACITY = 0.3;

/**
 * One dot's opacity over the cycle — brightest a third of a beat after the dot before it, so the
 * three read as one wave rather than three blinks, and back to where it started at the end so the
 * loop has no seam.
 */
function pulseOf(
  cycle: Animated.Value,
  dot: (typeof DOTS)[number],
): Animated.AnimatedInterpolation<number> {
  const peaks = DOTS.map((at) => (at === dot ? 1 : DOT_REST_OPACITY));

  return cycle.interpolate({
    inputRange: [0, 1 / 3, 2 / 3, 1],
    outputRange: [...peaks, peaks[0] ?? DOT_REST_OPACITY],
  });
}

export function TypingBubble({ sentence }: TypingBubbleProps) {
  const collapsed = useCollapsedPresentation();
  const cycle = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (collapsed) return;

    const loop = Animated.loop(
      Animated.timing(cycle, {
        toValue: 1,
        duration: theme.motion.typing,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    );
    loop.start();

    // Stopped with the bubble, and with the indicator clearing — a loop left running here would
    // run for the life of the screen.
    return () => loop.stop();
  }, [collapsed, cycle]);

  return (
    <View
      style={s.row}
      accessible
      accessibilityLabel={sentence}
      accessibilityLiveRegion="polite"
      testID="typing-indicator"
    >
      <View style={s.bubble}>
        {DOTS.map((dot) => (
          <Animated.View
            key={dot}
            style={[s.dot, collapsed ? undefined : { opacity: pulseOf(cycle, dot) }]}
            accessibilityElementsHidden
            importantForAccessibility="no"
          />
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  // The other side's row, exactly as `Bubble` draws it: full width, content at the start.
  row: { width: '100%', alignItems: 'flex-start' },
  // 5.1's card on `Bubble`'s geometry — `surface` bounded by `line`, the speaker's corner dropped
  // — and the one number of its own: no text, so the padding is what gives it a height.
  bubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.size.typing.gap,
    paddingVertical: theme.space.sm,
    paddingHorizontal: theme.space.md,
    borderRadius: theme.radius.bubble,
    borderBottomLeftRadius: theme.radius.bubbleTail,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
  },
  dot: {
    width: theme.size.typing.dot,
    height: theme.size.typing.dot,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.muted,
    opacity: DOT_REST_OPACITY,
  },
});
