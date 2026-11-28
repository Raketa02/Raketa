/**
 * **LEVEL · narrow it, not widen it** — the two bounds of who may be on the post
 * ([#558](https://github.com/Rakieta02/Rakieta/issues/558); the screens A5.1; mock 19; Q78).
 *
 * ```
 * [ − 2,56 + ] ───────── [ − 2,86 + ]
 * You can narrow it, not widen it          ← after a push past the engine's own
 * ```
 *
 * Seeded with the engine's own window for the kind around the poster's Level — the grid's read
 * (`engine_level_range`) — and moved a 0,05 step a press (`stepBound`). **Inward** narrows; **outward**
 * comes back as far as the engine's bound and no further: a push past it **bounces** — the box nudges
 * sideways and back and *You can narrow it, not widen it* is said under the pair, and announced —
 * so a mis-tap is never a door that will not open again, and the wall is felt rather than greyed.
 * A key whose press would turn the range inside out is shut. Until the grid has said where the
 * window is, both read *–* and every key is shut.
 */

import { useRef, useState } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';

import { announce, theme, useReducedMotion } from '@/shared/ui';

import {
  narrowedBounds,
  stepBound,
  type Bound,
  type LevelRange,
  type Narrowing,
  type Way,
} from '../domain/posting';

import { POSTING_COPY } from './postingCopy';
import { levelFigure } from './postingPresentation';
import { Stepper } from './Stepper';

const COPY = POSTING_COPY;
const LEG = theme.motion.bounce / 4;
const BOUNCE = theme.size.postingGrid.bounce;

export interface LevelSteppersProps {
  /** The engine's window — absent until the grid has been read. */
  readonly engine: LevelRange | undefined;
  readonly narrowing: Narrowing;
  readonly onNarrow: (narrowing: Narrowing) => void;
}

export function LevelSteppers({ engine, narrowing, onNarrow }: LevelSteppersProps) {
  const reducedMotion = useReducedMotion();
  const [bounced, setBounced] = useState(false);
  const nudges = useRef({ low: new Animated.Value(0), high: new Animated.Value(0) }).current;

  const bounce = (bound: Bound) => {
    setBounced(true);
    announce(COPY.bounce);
    if (reducedMotion) return;
    const nudge = nudges[bound];
    const outward = bound === 'low' ? -BOUNCE : BOUNCE;
    Animated.sequence(
      [outward, -outward / 2, outward / 3, 0].map((toValue) =>
        Animated.timing(nudge, { toValue, duration: LEG, useNativeDriver: true }),
      ),
    ).start();
  };

  const press = (bound: Bound, way: Way): (() => void) | undefined => {
    if (engine === undefined) return undefined;
    const step = stepBound(engine, narrowing, bound, way);
    switch (step.kind) {
      case 'shut':
        return undefined;
      case 'bounced':
        return () => bounce(bound);
      case 'moved':
        return () => {
          setBounced(false);
          onNarrow(step.narrowing);
        };
    }
  };

  const bounds = engine === undefined ? undefined : narrowedBounds(engine, narrowing);
  const figure = (value: number | undefined) =>
    value === undefined ? COPY.levelPending : levelFigure(value);
  const low = figure(bounds?.low);
  const high = figure(bounds?.high);

  return (
    <View style={s.column}>
      <View style={s.row}>
        <Stepper
          figure={low}
          nudge={nudges.low}
          fewer={{
            glyph: 'minus',
            label: COPY.levelKeys.lowDown,
            value: low,
            onPress: press('low', 'down'),
          }}
          more={{
            glyph: 'plus',
            label: COPY.levelKeys.lowUp,
            value: low,
            onPress: press('low', 'up'),
          }}
        />
        <View style={s.track} />
        <Stepper
          figure={high}
          nudge={nudges.high}
          fewer={{
            glyph: 'minus',
            label: COPY.levelKeys.highDown,
            value: high,
            onPress: press('high', 'down'),
          }}
          more={{
            glyph: 'plus',
            label: COPY.levelKeys.highUp,
            value: high,
            onPress: press('high', 'up'),
          }}
        />
      </View>
      {bounced ? <Text style={s.bounce}>{COPY.bounce}</Text> : null}
    </View>
  );
}

const s = StyleSheet.create({
  column: { gap: theme.space.xs },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // The mock's bar between the two: the range's span, drawn as a meter's track.
  track: {
    flex: 1,
    height: theme.size.meter,
    borderRadius: theme.radius.meter,
    backgroundColor: theme.color.line,
  },
  bounce: { ...theme.type.rlLabel, color: theme.color.amber },
});
