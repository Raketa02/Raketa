/**
 * The row, per design-system 5.5 — the key-value line.
 *
 * ```
 * flexDirection row   alignItems center   justifyContent space-between
 * gap 9               paddingVertical 6   fontSize 11.5
 * ```
 *
 * **The divider is drawn from the second row onward, never as a bottom border on every
 * row** — that way the first row has no rule above it and the last none below it, without
 * anyone counting. The caller passes `divided={index > 0}`, which is 5.5's own rule.
 *
 * `value` takes a node as well as a string, because a row's value is sometimes more than
 * a word: the evidence trail puts a direction mark and a level in one, and a mark drawn
 * beside a word is what keeps a direction from being carried by colour alone.
 *
 * **A row is one thing to a screen reader, or it is two halves read a screen apart.**
 * Where the label and the value only mean something together — and on a key-value line
 * they always do — the caller gives an `accessibilityLabel` and the row becomes a single
 * element.
 */

import { StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export type RowVariant = 'base' | 'onDark';

export interface RowProps {
  readonly label: string;
  readonly value: ReactNode;
  /** 5.5's `index > 0`. The first row in a list is undivided. */
  readonly divided?: boolean;
  /** 5.2's repaint: a row inside a dark card takes the on-dark ink and hairline. */
  readonly variant?: RowVariant;
  /** Makes the row one accessibility element, read as a whole. */
  readonly accessibilityLabel?: string;
}

export function Row({
  label,
  value,
  divided = false,
  variant = 'base',
  accessibilityLabel,
}: RowProps) {
  return (
    <View
      style={[s.row, divided ? DIVIDER[variant] : undefined]}
      accessible={accessibilityLabel !== undefined ? true : undefined}
      accessibilityLabel={accessibilityLabel}
    >
      <Text style={[s.label, LABEL[variant]]}>{label}</Text>
      {typeof value === 'string' ? (
        <Text style={[s.value, VALUE[variant]]} numberOfLines={1}>
          {value}
        </Text>
      ) : (
        value
      )}
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
    paddingVertical: theme.space.xs,
  },
  // `flexShrink`, so a long server-authored label wraps rather than pushing the value
  // off the row: the label is copy this client does not control.
  label: { ...theme.type.rlLabel, flexShrink: 1 },
  value: { ...theme.type.rlValue },
});

const DIVIDER = StyleSheet.create({
  base: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  onDark: { borderTopWidth: 1, borderTopColor: theme.color.onDarkHair },
});

const LABEL = StyleSheet.create({
  base: { color: theme.color.muted },
  onDark: { color: theme.color.onDarkTiny },
});

const VALUE = StyleSheet.create({
  base: { color: theme.color.ink },
  onDark: { color: theme.color.surface },
});
