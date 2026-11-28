/**
 * **How the stage's pictures move** — what sign-in's loop (#787) and sign-up's rise (#788) build their
 * sequences from ([#787](https://github.com/Rakieta02/Rakieta/issues/787),
 * [#788](https://github.com/Rakieta02/Rakieta/issues/788); design system 12.2): both `move` on the
 * native driver and land with `ARRIVE`; the loop alone also throws a card off on a curve of its own
 * and `put`s values back between cycles.
 *
 * `Animated` on the native driver, as the yes screen and the deck do: a timed move is the native
 * driver's, frames precomputed with its curve, so the picture moves on the UI thread and nothing
 * re-renders as it does.
 */

import { Animated, Easing } from 'react-native';

import { theme } from '@/shared/ui';

/** A theme curve, as `Animated` takes one. */
export const curve = ({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) =>
  Easing.bezier(x1, y1, x2, y2);

/** `easeDecel`, the app's curve for a thing arriving: a quick start and a soft landing. */
export const ARRIVE = curve(theme.motion.easeDecel);

/** One value to one place, on the native driver. */
export function move(
  value: Animated.Value,
  toValue: number,
  duration: number,
  easing?: (t: number) => number,
) {
  return Animated.timing(value, {
    toValue,
    duration,
    useNativeDriver: true,
    ...(easing === undefined ? {} : { easing }),
  });
}

/** One value put somewhere at once — inside a sequence, where `setValue` cannot reach. */
export const put = (value: Animated.Value, toValue: number) => move(value, toValue, 0);
