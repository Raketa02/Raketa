/**
 * **Where one day stops and the next starts** — the only time-shaped thing this stream draws.
 *
 * There is **no per-message timestamp**: a room lives at most a few days, so a clock beside every
 * bubble is noise, and the fact worth having is *was this today*
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.3).
 *
 * The weekday is `domain/entry.ts`' answer over the **platform zone**, and that placement is the
 * whole of what this component is trusted with: a device zone would put two people in one room on
 * two different days.
 *
 * `header` is its role, per §24.4 — it labels the run of entries under it, which is what a
 * listener moving by heading is looking for.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';
import { dayName } from '@/shared/vocabulary/availabilityPresentation';
import type { Weekday } from '@/shared/vocabulary/week';

export interface DaySeparatorProps {
  readonly day: Weekday;
}

export function DaySeparator({ day }: DaySeparatorProps) {
  return (
    <View style={s.separator}>
      <View style={s.rule} />
      <Text accessibilityRole="header" style={s.day}>
        {dayName(day)}
      </Text>
      <View style={s.rule} />
    </View>
  );
}

const s = StyleSheet.create({
  separator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.xs,
  },
  // `line2` and not `line`: this is a FOLD inside one thing — the stream is one surface and the
  // separator marks a place in it — where `line` bounds a thing. Drawn here rather than through
  // `Hairline`, which is a section wrapper with a fold above it and has no children to hold.
  rule: { flex: 1, height: 1, backgroundColor: theme.color.line2 },
  day: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
});
