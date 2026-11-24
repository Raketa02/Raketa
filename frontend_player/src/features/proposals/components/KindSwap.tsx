/**
 * **The Games deck's swap, drawn** ([#863](https://github.com/Raketa02/Raketa/issues/863), PRD #859;
 * the tab menu log §5.1–§5.2) — the layer the stack stands in, and the one the buttons stand in. The
 * rules are `domain/kindSwap.ts`, the clock `useKindSwap`; this file only moves what it is told to.
 *
 * ## The stack's layer
 *
 * **Going out** it slides `motion.kindSwap.rise` down and fades out over `.out`; **coming in** it
 * rises from the same `rise` below into its place and fades in over `.in`. **Away** — the kind picked
 * still on its way — it holds where going out left it, unseen, and today's spinner stands in its
 * place. **Opacity and a translation only**, on React Native's `Animated` and its native driver: no
 * layout prop moves frame by frame, and nothing is scaled — iOS rasterises a scaled layer blurred.
 * The stage inside it stands still; the cards a swap brings stand in place from their first frame,
 * so the layer's rise is the only motion (`DeckStage`'s `standing`). **Under reduced motion it is a
 * crossfade**: nothing travels, the two fades run. While it moves it takes no touch.
 *
 * The layer is drawn always, at rest when nothing swaps, so a swap beginning is a value changing and
 * never a stage drawn again.
 *
 * ## The buttons' layer
 *
 * The ✕ · i · ball stay through a swap where both sides have them — kept, as they are. Where one side
 * has none they fade over the stack's beat: out with the stack going out, in with the stack coming in.
 * **They take no touch while the stack goes out** (`inert`): nothing reaches the kind being left. The
 * stack itself takes none until it has landed.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { Animated, Easing, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

import { theme, useReducedMotion } from '@/shared/ui';

import type { ButtonsMotion, StackMotion } from '../domain/kindSwap';

const EASE = Easing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

const { out: OUT, in: IN, rise: RISE } = theme.motion.kindSwap;

/** One value to its end over a beat — a fade or a travel is no interaction (`TabMenu`'s reason). */
function towards(value: Animated.Value, toValue: number, duration: number) {
  return Animated.timing(value, {
    toValue,
    duration,
    easing: EASE,
    useNativeDriver: true,
    isInteraction: false,
  });
}

export interface SwapStackProps {
  readonly motion: StackMotion;
  /** The layer's own box: the stage's, or none round the starting card. */
  readonly style?: StyleProp<ViewStyle>;
  /** What stands in the stack's place while a read is on its way — today's spinner. */
  readonly waiting?: ReactNode;
  readonly children?: ReactNode;
}

/** The layer the stack stands in — see the module note. */
export function SwapStack({ motion, style, waiting, children }: SwapStackProps) {
  const reduced = useReducedMotion();
  const travel = reduced ? 0 : RISE;
  const lift = useRef(new Animated.Value(0)).current;
  const seen = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (motion === 'rest') {
      lift.setValue(0);
      seen.setValue(1);
      return undefined;
    }
    // Away, and the start of coming in, are where going out ends: `rise` down, unseen.
    if (motion !== 'out') {
      lift.setValue(travel);
      seen.setValue(0);
    }
    if (motion === 'away') return undefined;
    const going = motion === 'out';
    const beat = going ? OUT : IN;
    const run = Animated.parallel([
      towards(lift, going ? travel : 0, beat),
      towards(seen, going ? 0 : 1, beat),
    ]);
    run.start();
    return () => run.stop();
  }, [motion, travel, lift, seen]);

  return (
    <View style={style}>
      <Animated.View
        testID="games-deck-stack"
        style={[s.grow, { opacity: seen, transform: [{ translateY: lift }] }]}
        pointerEvents={motion === 'rest' ? 'auto' : 'none'}
      >
        {children}
      </Animated.View>
      {waiting === undefined ? null : <View style={s.waiting}>{waiting}</View>}
    </View>
  );
}

export interface SwapButtonsProps {
  readonly motion: Exclude<ButtonsMotion, 'none'>;
  /** The stack is going out: nothing here is pressed. */
  readonly inert: boolean;
  readonly children: ReactNode;
}

/** The layer the buttons stand in — see the module note. */
export function SwapButtons({ motion, inert, children }: SwapButtonsProps) {
  // Drawn for a stack coming in, they start unseen.
  const seen = useRef(new Animated.Value(motion === 'in' ? 0 : 1)).current;

  useEffect(() => {
    if (motion === 'kept') {
      seen.setValue(1);
      return undefined;
    }
    const run = towards(seen, motion === 'out' ? 0 : 1, motion === 'out' ? OUT : IN);
    run.start();
    return () => run.stop();
  }, [motion, seen]);

  return (
    <Animated.View
      testID="games-deck-buttons"
      style={{ opacity: seen }}
      pointerEvents={inert ? 'none' : 'auto'}
    >
      {children}
    </Animated.View>
  );
}

const s = StyleSheet.create({
  // As tall as the box it is in, where that box has a height — the stage's — and its content's
  // height where it has none.
  grow: { flexGrow: 1 },
  // Today's spinner, centred in the stack's place.
  waiting: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
