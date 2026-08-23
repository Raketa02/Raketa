/**
 * The countdown, repainted by the screen's one clock.
 *
 * Its own component so that a tick re-renders the figures and nothing else — a card
 * whose clock is empty does not read the context at all — and its own **module**
 * because two card shapes draw one. `ADR-0088` gives the state card its clock in the
 * action row's first slot and gives the shelf card a clock only under a live seat
 * claim, where it **replaces** the state tone tag. Two homes for one countdown would
 * be two formats, two accessibility labels and eventually two cadences.
 *
 * **`flexShrink: 0` and a floor on the width.** `ADR-0088` makes the act the only
 * flexible element; a countdown that shrank under a long label would be the one
 * element on the card that changes size as the seconds fall.
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

import type { Moment } from '../domain/ComposedScreen';
import { countdownLabel, remainingMs } from '../domain/countdown';

import { useNowClock } from './NowClock';
import { clockAccessibilityLabel } from './nowCopy';

export const CLOCK_ID = 'now-card-clock';

export function CardClock({ moment }: { readonly moment: Moment }) {
  const now = useNowClock();
  if (now === undefined) return null;

  const left = remainingMs(moment, now);
  // A moment that does not parse is a contract failure rather than a state, and
  // the answer is *there is no countdown here* rather than a figure in decades.
  if (left === undefined) return null;

  const label = countdownLabel(left);

  return (
    <Text
      style={s.clock}
      numberOfLines={1}
      accessibilityLabel={clockAccessibilityLabel(label)}
      testID={CLOCK_ID}
    >
      {label}
    </Text>
  );
}

const s = StyleSheet.create({
  clock: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.ink,
    flexShrink: 0,
    minWidth: theme.size.timeSquare,
  },
});
