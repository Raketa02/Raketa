/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * The entry instrument, shared by all three variants because the variants disagree about
 * WHERE the conversation happens, not about how a number is typed. It is surface-aware —
 * the same instrument sits on the night card in A and on paper in B and C — which is
 * `deltas/native-kit.md` §4's rule applied one component further.
 *
 * Two things it is arguing for:
 *
 * 1. **A pad, not a stepper and not a keyboard.** §5's constraint is a score typed
 *    standing on a court, one-handed, in the dark, at 30 minutes past the final point.
 *    A stepper is 6 taps to reach 6; the system keyboard puts a 300pt panel over the
 *    thing being typed and offers 10 keys where the sport has 8 legal values.
 * 2. **The grid is named on both axes.** `6-4 3-6 6-2` is not a score until you know
 *    whose 6 it is. Every screen here that shows a score shows the two sides with it.
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { Leg, Shape, Side } from './data';

export type Surface = 'night' | 'paper';

export interface ScoreGridProps {
  readonly shape: Shape;
  readonly sides: readonly [Side, Side];
  readonly value: readonly Leg[];
  readonly onChange: (next: readonly Leg[]) => void;
  readonly surface: Surface;
}

export function ScoreGrid({ shape, sides, value, onChange, surface }: ScoreGridProps) {
  const [focus, setFocus] = useState<readonly [number, 0 | 1]>([0, 0]);
  const ink = surface === 'night' ? theme.color.surface : theme.color.ink;
  const dim = surface === 'night' ? theme.color.onDarkEyebrow : theme.color.muted;
  const cellBg = surface === 'night' ? theme.color.onDarkFill : theme.color.paper2;
  const focusBg = surface === 'night' ? theme.color.volt : theme.color.night;
  const focusInk = surface === 'night' ? theme.color.night : theme.color.surface;

  function write(n: number | null): void {
    const [leg, col] = focus;
    const next = value.map((l, i) =>
      i === leg ? ((col === 0 ? [n, l[1]] : [l[0], n]) as Leg) : l,
    );
    onChange(next);
    if (n === null) return;
    setFocus(col === 0 ? [leg, 1] : [Math.min(leg + 1, shape.legs - 1), 0]);
  }

  const keys: (number | 'back' | 'more')[] = [
    ...Array.from({ length: shape.padTo + 1 }, (_, i) => i),
    'more',
    'back',
  ];

  return (
    <View>
      {/* The two sides, named once, above the columns they own. */}
      <View style={s.headRow}>
        <Text style={[s.legLabel, { color: dim }]} />
        {sides.map((side) => (
          <Text
            key={side.label}
            style={[s.sideLabel, { color: side.mine ? ink : dim }]}
            numberOfLines={1}
          >
            {side.label}
          </Text>
        ))}
      </View>

      {value.slice(0, shape.legs).map((leg, i) => (
        <View key={i} style={s.legRow}>
          <Text style={[s.legLabel, { color: dim }]}>
            {shape.leg} {i + 1}
          </Text>
          {([0, 1] as const).map((col) => {
            const on = focus[0] === i && focus[1] === col;
            return (
              <Pressable
                key={col}
                onPress={() => setFocus([i, col])}
                accessibilityRole="button"
                accessibilityLabel={`${shape.leg} ${i + 1}, ${sides[col].label}`}
                style={[
                  s.cell,
                  { backgroundColor: on ? focusBg : cellBg },
                  on ? null : { borderColor: 'transparent' },
                ]}
              >
                <Text style={[s.cellNum, { color: on ? focusInk : ink }]}>
                  {leg[col] === null ? '·' : leg[col]}
                </Text>
              </Pressable>
            );
          })}
        </View>
      ))}

      <Text style={[s.shapeNote, { color: dim }]}>
        {shape.note} · the app knows the shape, not the rulebook
      </Text>

      {/* The pad. 44 x 44 without hitSlop, so a cold thumb in the dark hits it. */}
      <View style={s.pad}>
        {keys.map((k) => (
          <Pressable
            key={String(k)}
            accessibilityRole="button"
            accessibilityLabel={k === 'back' ? 'Clear' : k === 'more' ? 'Higher' : String(k)}
            onPress={() => {
              if (k === 'back') write(null);
              else if (k === 'more') {
                const [leg, col] = focus;
                const cur = value[leg]?.[col] ?? shape.padTo;
                onChange(
                  value.map((l, i) =>
                    i === leg ? ((col === 0 ? [cur + 1, l[1]] : [l[0], cur + 1]) as Leg) : l,
                  ),
                );
              } else write(k);
            }}
            style={[
              s.key,
              { backgroundColor: cellBg },
              k === 'back' || k === 'more' ? s.keyAlt : null,
            ]}
          >
            <Text style={[s.keyNum, { color: ink }]}>
              {k === 'back' ? '⌫' : k === 'more' ? `${shape.padTo}+` : k}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  headRow: { flexDirection: 'row', gap: 6, alignItems: 'flex-end', marginBottom: 5 },
  // MISSING TOKEN: 8.5pt eyebrow — `theme.type.eyebrow` is 9.5. Same gap #11 recorded.
  legLabel: {
    fontFamily: theme.font.sans[700],
    fontSize: 8.5,
    letterSpacing: 1.28,
    lineHeight: 11,
    width: 44,
    textTransform: 'uppercase',
  },
  sideLabel: { ...theme.type.rlValue, flex: 1, textAlign: 'center' },
  legRow: { flexDirection: 'row', gap: 6, alignItems: 'center', marginBottom: 6 },
  cell: {
    flex: 1,
    height: 44,
    borderRadius: theme.radius.btn,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  cellNum: { ...theme.num.l, ...theme.tabular },
  shapeNote: { ...theme.type.tiny, marginTop: 2, marginBottom: theme.space.md },
  pad: { flexDirection: 'row', flexWrap: 'wrap', gap: 5 },
  key: {
    width: 44,
    height: 44,
    borderRadius: theme.radius.btn,
    alignItems: 'center',
    justifyContent: 'center',
  },
  keyAlt: { opacity: 0.75 },
  keyNum: { ...theme.num.s, ...theme.tabular },
});
